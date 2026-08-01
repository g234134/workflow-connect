#!/usr/bin/env python3
"""Multi-phase smoke runner v1 — orchestrates P7.5 / P8 / P8.9 CLIs without changing them.

Contract: docs/smoke-and-regression-contract-v1.md (MP-SMOKE · L-local recommended).
Does NOT replace INT Tier-A or PR mandatory CI.

Runs a fixed seven-step sequence for a single case (default ``demo_phase``):
gate preview → gate run + notify → standard-case experiment → workflow events inspect
→ feedback ingest dry-run → P8.9 verification bundle (collect-only) → operator backlog.

Usage:
    python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json
    python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --enable-dispatch --format json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.feedback_ingest_v1 import ingest_pending_events
from delivery.notification_gateway_v1 import emit_intake_gate_decision_notification
from delivery.workflow_event_consumer_v1 import load_workflow_events
from routing.intake_gate_layer_v1 import evaluate_intake_gate

_EXPERIMENT_SCRIPT = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
_P89_BUNDLE_SCRIPT = _REPO_ROOT / "scripts" / "run_p8_9_verification_bundle_v1.py"
_BACKLOG_SCRIPT = _REPO_ROOT / "scripts" / "list_operator_backlog_v1.py"

SUMMARY_SCHEMA = "multi_phase_smoke_v1"
DEFAULT_CASE_REF = "demo_phase"
DEFAULT_TASK_TYPE = "tabular.cleaning.mvp"

_CASE_REF_TO_DIR: Dict[str, str] = {
    "demo_phase": "cases/demo_phase",
    "sampleco/2026-0001": "cases/sampleco/2026-0001",
    "additional_demo": "cases/additional_demo",
    "sandbox_client": "cases/sandbox_client",
}

STEP_IDS: tuple[str, ...] = (
    "gate_preview",
    "gate_run_notify",
    "std_case_experiment",
    "workflow_events_inspect",
    "feedback_ingest_dry_run",
    "p89_verification_bundle",
    "operator_backlog",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def case_ref_to_slug(case_ref: str) -> str:
    return case_ref.replace("/", "_").replace("\\", "_")


def case_dir_for_ref(case_ref: str) -> str:
    if case_ref in _CASE_REF_TO_DIR:
        return _CASE_REF_TO_DIR[case_ref]
    return f"cases/{case_ref}"


def default_verification_dir(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
) -> Path:
    root = repo_root or _REPO_ROOT
    return root / "outbox" / "verification" / case_ref_to_slug(case_ref)


def resolve_outbox_root(
    *,
    repo_root: Path,
    outbox_root_override: Optional[str],
) -> Path:
    if outbox_root_override:
        return Path(outbox_root_override).resolve()
    return repo_root / "outbox"


def _load_module(script_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _gate_step_detail(
    gate_result: Dict[str, Any],
    gate_notify: Optional[Dict[str, Any]] = None,
    *,
    include_notify: bool = False,
) -> Dict[str, Any]:
    """Build MP-SMOKE step detail aligned with p75 gate trace SSOT join keys."""
    decision = gate_result.get("decision")
    detail: Dict[str, Any] = {
        "case_ref": gate_result.get("case_ref"),
        "intake_decision_id": gate_result.get("intake_decision_id"),
        "decision": decision,
        "gate_decision": decision,
        "reason_codes": gate_result.get("reason_codes"),
        "mode": gate_result.get("mode"),
        "p75_policy_decision": gate_result.get("p75_policy_decision"),
        "deny_reason": gate_result.get("deny_reason"),
    }
    if include_notify:
        detail["notification_ok"] = (gate_notify or {}).get("ok")
        detail["event_type"] = (
            "intake.gate_decision" if gate_notify is not None else None
        )
    return detail


def _step_result(
    step_id: str,
    *,
    ok: bool,
    message: str,
    artifact_paths: Optional[Dict[str, str]] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "step_id": step_id,
        "ok": ok,
        "message": message,
        "artifact_paths": artifact_paths or {},
    }
    if detail is not None:
        row["detail"] = detail
    return row


def run_multi_phase_smoke_v1(
    case_ref: str = DEFAULT_CASE_REF,
    *,
    task_type: str = DEFAULT_TASK_TYPE,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    enable_dispatch: bool = False,
    write_summary: bool = True,
) -> Dict[str, Any]:
    """Execute the seven-step multi-phase smoke sequence; returns summary dict."""
    root = Path(repo_root).resolve() if repo_root else _REPO_ROOT
    outbox_root = resolve_outbox_root(
        repo_root=root,
        outbox_root_override=outbox_root_override,
    )
    outbox_root.mkdir(parents=True, exist_ok=True)
    outbox_str = outbox_root.as_posix()
    case_dir = case_dir_for_ref(case_ref)
    verification_dir = default_verification_dir(case_ref, repo_root=root)

    steps: List[Dict[str, Any]] = []
    prior_dispatch_env = os.environ.get("GOV_NOTIFICATION_DISPATCH_ENABLED")

    def _append(step: Dict[str, Any]) -> None:
        steps.append(step)

    # 1 — Gate preview (no outbox write)
    preview = evaluate_intake_gate(
        task_type,
        case_dir,
        mode="preview",
        repo_root=root,
        outbox_root_override=outbox_str,
    )
    _append(
        _step_result(
            "gate_preview",
            ok=bool(preview.get("ok")),
            message=str(preview.get("message") or "gate preview completed"),
            detail=_gate_step_detail(preview),
        )
    )

    # 2 — Gate run + notifications
    gate_run = evaluate_intake_gate(
        task_type,
        case_dir,
        mode="run",
        repo_root=root,
        outbox_root_override=outbox_str,
    )
    gate_notify: Optional[Dict[str, Any]] = None
    gate_artifacts: Dict[str, str] = {}
    if gate_run.get("outbox_record_path"):
        gate_artifacts["outbox_record_path"] = str(gate_run["outbox_record_path"])
    if gate_run.get("ok"):
        gate_notify = emit_intake_gate_decision_notification(
            gate_run,
            enabled=True,
            repo_root=root,
            outbox_root_override=outbox_str,
        )
        if gate_notify and (gate_notify.get("sink_result") or {}).get("path"):
            gate_artifacts["notification_path"] = str(
                (gate_notify.get("sink_result") or {}).get("path")
            )
    _append(
        _step_result(
            "gate_run_notify",
            ok=bool(gate_run.get("ok")),
            message=str(gate_run.get("message") or "gate run completed"),
            artifact_paths=gate_artifacts,
            detail=_gate_step_detail(
                gate_run,
                gate_notify,
                include_notify=True,
            ),
        )
    )

    # 3 — Standard-case experiment (HITL auto path)
    if enable_dispatch:
        os.environ["GOV_NOTIFICATION_DISPATCH_ENABLED"] = "1"
    else:
        os.environ.pop("GOV_NOTIFICATION_DISPATCH_ENABLED", None)

    experiment_mod = _load_module(_EXPERIMENT_SCRIPT, "run_agent_standard_case_experiment")
    experiment = experiment_mod.run_agent_standard_case_experiment(
        task_type,
        case_dir,
        mode="run",
        auto_approve_intake=True,
        notifications_enabled=True,
        outbox_root_override=outbox_str,
    )
    exp_artifacts: Dict[str, str] = {}
    if experiment.get("experiment_id"):
        exp_artifacts["experiment_id"] = str(experiment["experiment_id"])
    delivery = experiment.get("delivery") or {}
    if isinstance(delivery, dict) and delivery.get("bundle_path"):
        exp_artifacts["bundle_path"] = str(delivery["bundle_path"])
    _append(
        _step_result(
            "std_case_experiment",
            ok=bool(experiment.get("ok")),
            message=str(experiment.get("message") or "standard-case experiment completed"),
            artifact_paths=exp_artifacts,
            detail={"steps_run": experiment.get("steps_run") or []},
        )
    )

    # 4 — Workflow events inspect (read-only)
    events = load_workflow_events(
        case_ref,
        repo_root=root,
        outbox_root_override=outbox_str,
    )
    _append(
        _step_result(
            "workflow_events_inspect",
            ok=bool(events.get("ok")),
            message=str(events.get("message") or "workflow events loaded"),
            detail={
                "count": events.get("count", 0),
                "streams_read": events.get("streams_read") or [],
            },
        )
    )

    # 5 — Feedback ingest dry-run
    feedback = ingest_pending_events(
        case_ref,
        repo_root=root,
        outbox_root_override=outbox_str,
    )
    feedback["dry_run"] = True
    _append(
        _step_result(
            "feedback_ingest_dry_run",
            ok=bool(feedback.get("ok")),
            message=str(feedback.get("message") or "feedback ingest dry-run completed"),
            detail={"pending_count": feedback.get("pending_count", 0)},
        )
    )

    # 6 — P8.9 verification bundle (collect-only; experiment already ran in step 3)
    bundle_mod = _load_module(_P89_BUNDLE_SCRIPT, "run_p8_9_verification_bundle_v1")
    bundle = bundle_mod.run_p8_9_verification_bundle(
        case_ref,
        task_type=task_type,
        repo_root=root,
        output_dir=verification_dir,
        outbox_root_override=outbox_str,
        enable_notifications=True,
        enable_dispatch=enable_dispatch,
        skip_experiment=True,
        auto_approve_intake=True,
    )
    p89_artifacts = dict(bundle.get("artifact_paths") or {})
    _append(
        _step_result(
            "p89_verification_bundle",
            ok=bool(bundle.get("ok")),
            message=str(bundle.get("message") or "P8.9 verification bundle assembled"),
            artifact_paths=p89_artifacts,
            detail={
                "events_summary": bundle.get("events_summary"),
                "acks_summary": bundle.get("acks_summary"),
            },
        )
    )

    # 7 — Operator backlog view
    backlog_mod = _load_module(_BACKLOG_SCRIPT, "list_operator_backlog_v1")
    backlog = backlog_mod.list_operator_backlog(
        case_ref=case_ref,
        repo_root=root,
        outbox_root_override=outbox_str,
    )
    _append(
        _step_result(
            "operator_backlog",
            ok=bool(backlog.get("ok")),
            message=str(backlog.get("message") or "operator backlog listed"),
            detail={"count": backlog.get("count", 0), "items": backlog.get("items") or []},
        )
    )

    if prior_dispatch_env is None:
        os.environ.pop("GOV_NOTIFICATION_DISPATCH_ENABLED", None)
    else:
        os.environ["GOV_NOTIFICATION_DISPATCH_ENABLED"] = prior_dispatch_env

    all_ok = all(bool(s.get("ok")) for s in steps)
    summary_path = verification_dir / "multi_phase_smoke_run.json"
    artifact_paths: Dict[str, str] = {}
    if write_summary:
        verification_dir.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(
                {
                    "schema_version": SUMMARY_SCHEMA,
                    "ok": all_ok,
                    "case_ref": case_ref,
                    "task_type": task_type,
                    "run_at": _utc_now_iso(),
                    "outbox_root": outbox_str,
                    "enable_dispatch": enable_dispatch,
                    "steps": steps,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        artifact_paths["multi_phase_smoke_run.json"] = summary_path.as_posix()

    return {
        "schema_version": SUMMARY_SCHEMA,
        "ok": all_ok,
        "read_only": False,
        "case_ref": case_ref,
        "task_type": task_type,
        "run_at": _utc_now_iso(),
        "outbox_root": outbox_str,
        "enable_dispatch": enable_dispatch,
        "steps": steps,
        "step_ids": list(STEP_IDS),
        "artifact_paths": artifact_paths,
        "message": "multi-phase smoke v1 completed" if all_ok else "multi-phase smoke v1 completed with failures",
    }


def _format_text(result: Dict[str, Any]) -> str:
    lines = [
        "Multi-Phase Smoke v1",
        f"case_ref: {result.get('case_ref')}",
        f"ok: {result.get('ok')}",
        f"outbox_root: {result.get('outbox_root')}",
        f"enable_dispatch: {result.get('enable_dispatch')}",
        "",
        "── steps ──",
    ]
    for step in result.get("steps") or []:
        status = "OK" if step.get("ok") else "FAIL"
        lines.append(f"  [{status}] {step.get('step_id')}: {step.get('message')}")
        paths = step.get("artifact_paths") or {}
        for key, path in paths.items():
            lines.append(f"      {key}: {path}")
    lines.append("")
    paths = result.get("artifact_paths") or {}
    if paths:
        lines.append("── summary artifacts ──")
        for key, path in paths.items():
            lines.append(f"  {key}: {path}")
        lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run multi-phase smoke (P7.5 gate → experiment → P8.9 consumer → operator backlog)."
    )
    parser.add_argument(
        "--case-ref",
        default=DEFAULT_CASE_REF,
        help=f"Case slug under cases/ (default: {DEFAULT_CASE_REF})",
    )
    parser.add_argument(
        "--task-type",
        default=DEFAULT_TASK_TYPE,
        help=f"Routing task_type (default: {DEFAULT_TASK_TYPE})",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional isolated outbox root (default: <repo>/outbox/)",
    )
    parser.add_argument(
        "--enable-dispatch",
        action="store_true",
        help="Enable post-emit notification dispatch during experiment / bundle collect",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument(
        "--no-write-summary",
        action="store_true",
        help="Skip writing outbox/verification/<case>/multi_phase_smoke_run.json",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    result = run_multi_phase_smoke_v1(
        args.case_ref,
        task_type=args.task_type,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
        enable_dispatch=args.enable_dispatch,
        write_summary=not args.no_write_summary,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
