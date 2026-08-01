#!/usr/bin/env python3
"""P8.9 verification bundle v1 — repeatable regression smoke for consumer / feedback / dispatch.

Runs a standard-case experiment with notifications (and optional dispatch), then aggregates
existing CLI read models into a fixed artifact bundle under outbox/verification/<case_slug>/.

Usage:
    python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json
    python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --outbox-root /tmp/p89_outbox
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
from delivery.workflow_event_consumer_v1 import load_workflow_events

_EXPERIMENT_SCRIPT = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
_AUDIT_SCRIPT = _REPO_ROOT / "scripts" / "run_agent_audit_quickview.py"

VERIFICATION_RUN_SCHEMA = "p8_9_verification_run_v1"
VERIFICATION_ACKS_SCHEMA = "p8_9_verification_acks_v1"
DEFAULT_TASK_TYPE = "tabular.cleaning.mvp"

_CASE_REF_TO_DIR: Dict[str, str] = {
    "demo_phase": "cases/demo_phase",
    "sampleco/2026-0001": "cases/sampleco/2026-0001",
    "additional_demo": "cases/additional_demo",
    "sandbox_client": "cases/sandbox_client",
}

_BUNDLE_FILENAMES = (
    "p8.9_verification_run.json",
    "events.json",
    "audit_quickview.json",
    "acks.json",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def case_ref_to_slug(case_ref: str) -> str:
    return case_ref.replace("/", "_").replace("\\", "_")


def case_dir_for_ref(case_ref: str) -> str:
    if case_ref in _CASE_REF_TO_DIR:
        return _CASE_REF_TO_DIR[case_ref]
    return f"cases/{case_ref}"


def default_output_dir(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
) -> Path:
    root = repo_root or _REPO_ROOT
    return root / "outbox" / "verification" / case_ref_to_slug(case_ref)


def resolve_outbox_root(
    *,
    output_dir: Path,
    outbox_root_override: Optional[str],
) -> Path:
    if outbox_root_override:
        return Path(outbox_root_override).resolve()
    return output_dir / "outbox"


def resolve_consumer_repo_root(outbox_root: Path) -> Path:
    """Repo root for load_workflow_events when outbox lives at <root>/outbox/."""
    if outbox_root.name == "outbox":
        return outbox_root.parent
    return outbox_root.parent


def _load_experiment_runner():
    spec = importlib.util.spec_from_file_location(
        "run_agent_standard_case_experiment", _EXPERIMENT_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load experiment script: {_EXPERIMENT_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_audit_runner():
    spec = importlib.util.spec_from_file_location(
        "run_agent_audit_quickview", _AUDIT_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load audit quickview script: {_AUDIT_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _count_by_event_type(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        et = str(row.get("event_type", "unknown"))
        counts[et] = counts.get(et, 0) + 1
    return counts


def _merge_workflow_notifications_into_audit(
    audit_quickview: Dict[str, Any],
    wf: Dict[str, Any],
) -> None:
    if not wf.get("ok"):
        return
    notif_rows = [r for r in wf.get("events") or [] if r.get("source_stream") == "notification"]
    audit_quickview["workflow_notifications"] = {
        "found": bool(notif_rows),
        "count": len(notif_rows),
        "pending_ack_count": sum(
            1 for r in notif_rows if r.get("tracking_status") == "pending_ack"
        ),
        "failed_ack_count": sum(
            1 for r in notif_rows if r.get("tracking_status") == "failed"
        ),
        "count_by_event_type": _count_by_event_type(notif_rows),
        "streams_read": wf.get("streams_read") or [],
        "events": wf.get("events") or [],
        "consumer_ok": True,
    }
    if notif_rows:
        audit_quickview["ok"] = True


def collect_ack_records(
    case_ref: str,
    *,
    consumer_repo: Path,
    outbox_root: Path,
) -> Dict[str, Any]:
    """Aggregate feedback ingest pending scan + on-disk ack files."""
    ingest = ingest_pending_events(
        case_ref,
        repo_root=consumer_repo,
        outbox_root_override=str(outbox_root),
    )
    norm_case = case_ref.replace("\\", "/").strip("/")
    ack_dir = outbox_root / "feedback" / norm_case / "acks"
    ack_records: List[Dict[str, Any]] = []
    if ack_dir.is_dir():
        for path in sorted(ack_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                ack_records.append(data)

    return {
        "schema_version": VERIFICATION_ACKS_SCHEMA,
        "case_ref": case_ref,
        "ok": bool(ingest.get("ok")),
        "ingest": ingest,
        "ack_records": ack_records,
        "ack_count": len(ack_records),
        "pending_count": ingest.get("pending_count", 0),
    }


def write_bundle_artifacts(
    output_dir: Path,
    *,
    summary: Dict[str, Any],
    events: Dict[str, Any],
    audit_quickview: Dict[str, Any],
    acks: Dict[str, Any],
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, str] = {}
    payloads = {
        "p8.9_verification_run.json": summary,
        "events.json": events,
        "audit_quickview.json": audit_quickview,
        "acks.json": acks,
    }
    for filename, payload in payloads.items():
        path = output_dir / filename
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        paths[filename] = path.as_posix()
    return paths


def run_p8_9_verification_bundle(
    case_ref: str,
    *,
    task_type: str = DEFAULT_TASK_TYPE,
    repo_root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    enable_notifications: bool = True,
    enable_dispatch: bool = True,
    skip_experiment: bool = False,
    auto_approve_intake: bool = True,
) -> Dict[str, Any]:
    """Execute verification run and write bundle artifacts; returns summary dict."""
    root = Path(repo_root).resolve() if repo_root else _REPO_ROOT
    out_dir = Path(output_dir).resolve() if output_dir else default_output_dir(case_ref, repo_root=root)
    outbox_root = resolve_outbox_root(output_dir=out_dir, outbox_root_override=outbox_root_override)
    outbox_root.mkdir(parents=True, exist_ok=True)
    consumer_repo = resolve_consumer_repo_root(outbox_root)

    experiment_result: Optional[Dict[str, Any]] = None
    prior_dispatch_env = os.environ.get("GOV_NOTIFICATION_DISPATCH_ENABLED")

    if not skip_experiment:
        if enable_dispatch:
            os.environ["GOV_NOTIFICATION_DISPATCH_ENABLED"] = "1"
        else:
            os.environ.pop("GOV_NOTIFICATION_DISPATCH_ENABLED", None)
        experiment_mod = _load_experiment_runner()
        experiment_result = experiment_mod.run_agent_standard_case_experiment(
            task_type,
            case_dir_for_ref(case_ref),
            mode="run",
            auto_approve_intake=auto_approve_intake,
            notifications_enabled=enable_notifications,
            outbox_root_override=str(outbox_root),
        )

    events = load_workflow_events(
        case_ref,
        repo_root=consumer_repo,
        outbox_root_override=str(outbox_root),
    )

    audit_mod = _load_audit_runner()
    audit_quickview = audit_mod.run_agent_audit_quickview(
        case_ref,
        repo_root=consumer_repo,
    )
    _merge_workflow_notifications_into_audit(audit_quickview, events)

    acks = collect_ack_records(
        case_ref,
        consumer_repo=consumer_repo,
        outbox_root=outbox_root,
    )

    notification_rows = [
        r for r in (events.get("events") or []) if r.get("source_stream") == "notification"
    ]
    event_types = sorted({str(r.get("event_type")) for r in notification_rows if r.get("event_type")})
    tracking_statuses = sorted(
        {str(r.get("tracking_status")) for r in notification_rows if r.get("tracking_status")}
    )

    bundle_ok = bool(events.get("ok")) and bool(acks.get("ok"))
    if experiment_result is not None:
        bundle_ok = bundle_ok and bool(experiment_result.get("ok"))

    summary: Dict[str, Any] = {
        "schema_version": VERIFICATION_RUN_SCHEMA,
        "ok": bundle_ok,
        "read_only": False,
        "case_ref": case_ref,
        "task_type": task_type,
        "run_at": _utc_now_iso(),
        "output_dir": out_dir.as_posix(),
        "outbox_root": outbox_root.as_posix(),
        "enable_notifications": enable_notifications,
        "enable_dispatch": enable_dispatch,
        "skip_experiment": skip_experiment,
        "experiment": experiment_result,
        "events_summary": {
            "ok": events.get("ok"),
            "count": events.get("count", 0),
            "event_types": event_types,
            "tracking_statuses": tracking_statuses,
            "streams_read": events.get("streams_read") or [],
        },
        "audit_quickview_ok": audit_quickview.get("ok"),
        "acks_summary": {
            "ack_count": acks.get("ack_count", 0),
            "pending_count": acks.get("pending_count", 0),
        },
        "artifact_files": list(_BUNDLE_FILENAMES),
        "artifact_paths": {name: (out_dir / name).as_posix() for name in _BUNDLE_FILENAMES},
        "message": "P8.9 verification bundle assembled",
    }

    write_bundle_artifacts(
        out_dir,
        summary=summary,
        events=events,
        audit_quickview=audit_quickview,
        acks=acks,
    )

    if prior_dispatch_env is None:
        os.environ.pop("GOV_NOTIFICATION_DISPATCH_ENABLED", None)
    else:
        os.environ["GOV_NOTIFICATION_DISPATCH_ENABLED"] = prior_dispatch_env

    return summary


def _format_text(result: Dict[str, Any]) -> str:
    lines = [
        "P8.9 Verification Bundle v1",
        f"case_ref: {result.get('case_ref')}",
        f"ok: {result.get('ok')}",
        f"output_dir: {result.get('output_dir')}",
        f"outbox_root: {result.get('outbox_root')}",
        "",
        "── events_summary ──",
    ]
    es = result.get("events_summary") or {}
    lines.append(f"  count: {es.get('count', 0)}")
    lines.append(f"  event_types: {', '.join(es.get('event_types') or [])}")
    lines.append(f"  tracking_statuses: {', '.join(es.get('tracking_statuses') or [])}")
    lines.append("")
    lines.append("── acks_summary ──")
    aks = result.get("acks_summary") or {}
    lines.append(f"  ack_count: {aks.get('ack_count', 0)}")
    lines.append(f"  pending_count: {aks.get('pending_count', 0)}")
    lines.append("")
    paths = result.get("artifact_paths") or {}
    lines.append("── artifacts ──")
    for name in _BUNDLE_FILENAMES:
        lines.append(f"  {name}: {paths.get(name, '(missing)')}")
    lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run P8.9 verification bundle (experiment + consumer + audit + acks)."
    )
    parser.add_argument("--case-ref", required=True, help="Case slug (e.g. demo_phase)")
    parser.add_argument(
        "--task-type",
        default=DEFAULT_TASK_TYPE,
        help=f"Routing task_type (default: {DEFAULT_TASK_TYPE})",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Bundle output directory (default: outbox/verification/<case_slug>/)",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional isolated outbox root (default: <output-dir>/outbox/)",
    )
    parser.add_argument(
        "--disable-notifications",
        action="store_true",
        help="Suppress notification emit during experiment",
    )
    parser.add_argument(
        "--disable-dispatch",
        action="store_true",
        help="Do not enable post-emit dispatch during experiment",
    )
    parser.add_argument(
        "--skip-experiment",
        action="store_true",
        help="Only collect consumer/audit/acks from existing outbox (testing)",
    )
    parser.add_argument(
        "--no-auto-approve-intake",
        action="store_true",
        help="Do not auto-approve intake during experiment",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else default_output_dir(args.case_ref, repo_root=repo_root)
    )

    result = run_p8_9_verification_bundle(
        args.case_ref,
        task_type=args.task_type,
        repo_root=repo_root,
        output_dir=output_dir,
        outbox_root_override=args.outbox_root,
        enable_notifications=not args.disable_notifications,
        enable_dispatch=not args.disable_dispatch,
        skip_experiment=args.skip_experiment,
        auto_approve_intake=not args.no_auto_approve_intake,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
