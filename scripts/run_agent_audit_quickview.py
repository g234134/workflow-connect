#!/usr/bin/env python3
"""Agent-lines audit quickview CLI v1 (W10-T3 · WB-T5 spec).

Read-only aggregator for Reviewer / auditors: surfaces the latest agent-run
decision, route, checkpoint state, and human decisions for a case_ref.

Contract SSOT: docs/audit-quickview-and-case-history-spec-v1.md
  - Wire JSON: schema_version agent_audit_quickview_v1 (--format json)
  - Investigation view (sections/timeline/gaps): spec §2.4 projection

Sources (read-only, no writes; priority per spec §3):
  - outbox/agent_ci/
  - outbox/agent_experiment_regression/
  - outbox/non_tabular_experiment/
  - outbox/<case_ref>/checkpoint_A|B-*.json
  - outbox/sandbox_delivery/ (optional)

Usage:
    python scripts/run_agent_audit_quickview.py --case-ref demo_phase
    python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json
    python scripts/run_agent_audit_quickview.py --case-ref demo_phase --view investigation --format json
    python scripts/run_agent_audit_quickview.py --case-ref sampleco/2026-0001
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from audit.audit_investigation_projection_v1 import project_audit_investigation_view
from delivery.sandbox_delivery_bundle_v1 import find_latest_sandbox_bundle
from delivery.workflow_event_consumer_v1 import load_workflow_events

_RUN_ARTIFACT_DIRS: Tuple[Tuple[str, str], ...] = (
    ("agent_experiment_regression", "agent_experiment_regression"),
    ("agent_ci", "agent_ci"),
    ("non_tabular_experiment", "non_tabular_experiment"),
)

_CHECKPOINT_A_PREFIX = "checkpoint_A-intake-confirmation_"
_CHECKPOINT_B_PREFIX = "checkpoint_B-delivery-confirmation_"

_ARTIFACT_TS_RE = re.compile(r"^(\d{8}T\d{6}Z)_")
_CHECKPOINT_TS_RE = re.compile(
    r"checkpoint_[AB]-[a-z-]+_(\d{4}-\d{2}-\d{2}T[\d:+-]+Z|\d{8}T\d{6}Z)"
)


def case_ref_to_slug(case_ref: str) -> str:
    """Sanitize case_ref for regression artifact filenames."""
    return case_ref.replace("/", "_").replace("\\", "_")


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _artifact_timestamp_from_filename(filename: str) -> str:
    match = _ARTIFACT_TS_RE.match(filename)
    return match.group(1) if match else ""


def _checkpoint_timestamp_from_filename(filename: str) -> str:
    match = _CHECKPOINT_TS_RE.search(filename)
    return match.group(1) if match else ""


def _extract_case_ref_from_artifact(
    data: Dict[str, Any],
    source_kind: str,
) -> Optional[str]:
    if source_kind == "agent_experiment_regression":
        case_summary = data.get("case_summary") or {}
        if case_summary.get("case_ref"):
            return str(case_summary["case_ref"])
        experiment = data.get("experiment") or {}
        if experiment.get("case_ref"):
            return str(experiment["case_ref"])
        return None
    case_ref = data.get("case_ref")
    return str(case_ref) if case_ref else None


def _artifact_matches_case_ref(
    *,
    filename: str,
    case_ref: str,
    data: Optional[Dict[str, Any]],
    source_kind: str,
) -> bool:
    slug = case_ref_to_slug(case_ref)
    if filename == f"{slug}.json" or filename.endswith(f"_{slug}.json"):
        return True
    if data is None:
        return False
    extracted = _extract_case_ref_from_artifact(data, source_kind)
    return extracted == case_ref


def case_outbox_dir(case_ref: str, repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / "outbox" / Path(case_ref)


def find_latest_run_artifact(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Return metadata for the newest matching run artifact, or None."""
    root = repo_root or _REPO_ROOT
    candidates: List[Tuple[str, Path, Dict[str, Any], str]] = []

    for dir_name, source_kind in _RUN_ARTIFACT_DIRS:
        scan_root = root / "outbox" / dir_name
        if not scan_root.is_dir():
            continue
        for path in sorted(scan_root.glob("*.json")):
            data = _load_json(path)
            if not _artifact_matches_case_ref(
                filename=path.name,
                case_ref=case_ref,
                data=data,
                source_kind=source_kind,
            ):
                continue
            if data is None:
                continue
            ts = _artifact_timestamp_from_filename(path.name)
            candidates.append((ts, path, data, source_kind))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    ts, path, data, source_kind = candidates[0]
    try:
        rel_path = path.relative_to(root).as_posix()
    except ValueError:
        rel_path = path.as_posix()

    return {
        "source_kind": source_kind,
        "artifact_path": rel_path,
        "artifact_timestamp": ts or None,
        "written_at": data.get("written_at"),
        "payload": data,
    }


def find_latest_checkpoint(
    case_ref: str,
    checkpoint_id: Literal["A", "B"],
    *,
    repo_root: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Return the newest on-disk checkpoint A or B record for case_ref."""
    root = repo_root or _REPO_ROOT
    outbox = case_outbox_dir(case_ref, root)
    if not outbox.is_dir():
        return None

    prefix = _CHECKPOINT_A_PREFIX if checkpoint_id == "A" else _CHECKPOINT_B_PREFIX
    candidates: List[Tuple[str, Path, Dict[str, Any]]] = []
    for path in outbox.glob(f"{prefix}*.json"):
        data = _load_json(path)
        if data is None:
            continue
        ts = _checkpoint_timestamp_from_filename(path.name)
        candidates.append((ts, path, data))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    ts, path, data = candidates[0]
    try:
        rel_path = path.relative_to(root).as_posix()
    except ValueError:
        rel_path = path.as_posix()

    return {
        "checkpoint_id": data.get("checkpoint_id")
        or ("A-intake-confirmation" if checkpoint_id == "A" else "B-delivery-confirmation"),
        "checkpoint_path": rel_path,
        "checkpoint_timestamp": ts or None,
        "status": data.get("status"),
        "human_decision": data.get("human_decision"),
        "payload": data,
    }


def _normalize_decision_block(
    artifact: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not artifact:
        return {"decision": None, "risk_level": None}

    payload = artifact["payload"]
    source_kind = artifact["source_kind"]

    if source_kind == "agent_experiment_regression":
        experiment = payload.get("experiment") or {}
        decision = experiment.get("decision") or {}
        case_summary = payload.get("case_summary") or {}
        return {
            "decision": decision.get("decision") or case_summary.get("decision"),
            "risk_level": decision.get("risk_level"),
            "message": decision.get("message"),
        }

    decision = payload.get("decision")
    if isinstance(decision, dict):
        return {
            "decision": decision.get("decision"),
            "risk_level": decision.get("risk_level") or (payload.get("risk") or {}).get("level"),
            "message": decision.get("message"),
        }

    risk = payload.get("risk") or {}
    return {
        "decision": decision if isinstance(decision, str) else None,
        "risk_level": risk.get("level") if isinstance(risk, dict) else None,
        "message": None,
    }


def _normalize_route_block(
    artifact: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not artifact:
        return {
            "selector_task_type": None,
            "planned_tools": [],
            "orchestration_tool_id": None,
        }

    payload = artifact["payload"]
    source_kind = artifact["source_kind"]

    if source_kind == "agent_experiment_regression":
        experiment = payload.get("experiment") or {}
        route = experiment.get("planned_route") or {}
        decision = experiment.get("decision") or {}
        suggested = decision.get("suggested_route") or {}
        planned_tools = route.get("planned_tools") or suggested.get("planned_tools") or []
        return {
            "selector_task_type": route.get("selector_task_type")
            or suggested.get("selector_task_type"),
            "planned_tools": list(planned_tools),
            "orchestration_tool_id": suggested.get("orchestration_tool_id"),
            "case_profile": route.get("case_profile"),
        }

    route = payload.get("planned_route") or {}
    planned_tools = payload.get("planned_tools") or route.get("planned_tools") or []
    return {
        "selector_task_type": route.get("selector_task_type"),
        "planned_tools": list(planned_tools),
        "orchestration_tool_id": route.get("orchestration_tool_id"),
        "case_profile": route.get("case_profile"),
        "flow_family": payload.get("flow_family"),
    }


def _normalize_checkpoint_view(
    *,
    checkpoint_id: Literal["A", "B"],
    artifact: Optional[Dict[str, Any]],
    on_disk: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    inline: Dict[str, Any] = {}
    if artifact:
        payload = artifact["payload"]
        source_kind = artifact["source_kind"]
        if source_kind == "agent_experiment_regression":
            experiment = payload.get("experiment") or {}
            key = "checkpoint_a_status" if checkpoint_id == "A" else "checkpoint_b_status"
            inline = experiment.get(key) or {}
            case_summary = payload.get("case_summary") or {}
            summary_key = (
                "checkpoint_a_status" if checkpoint_id == "A" else "checkpoint_b_status"
            )
            if not inline.get("status") and case_summary.get(summary_key):
                inline = {**inline, "status": case_summary.get(summary_key)}
            if checkpoint_id == "B" and "would_trigger" not in inline:
                inline["would_trigger"] = case_summary.get("checkpoint_b_would_trigger")

    human_decision = None
    if on_disk and on_disk.get("human_decision"):
        human_decision = on_disk["human_decision"]
    elif inline.get("human_decision"):
        human_decision = inline["human_decision"]

    return {
        "checkpoint_id": (
            on_disk.get("checkpoint_id")
            if on_disk
            else inline.get("checkpoint_id")
            or (
                "A-intake-confirmation"
                if checkpoint_id == "A"
                else "B-delivery-confirmation"
            )
        ),
        "would_trigger": inline.get("would_trigger"),
        "status": (on_disk or {}).get("status") or inline.get("status"),
        "message": inline.get("message"),
        "on_disk": bool(on_disk),
        "checkpoint_path": (on_disk or {}).get("checkpoint_path"),
        "human_decision": human_decision,
    }


def _normalize_delivery_approval(
    checkpoint_b_on_disk: Optional[Dict[str, Any]],
    artifact: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if checkpoint_b_on_disk and checkpoint_b_on_disk.get("human_decision"):
        hd = checkpoint_b_on_disk["human_decision"]
        return {
            "source": "checkpoint_B_on_disk",
            "action": hd.get("action"),
            "operator_id": hd.get("operator_id") or hd.get("by"),
            "comment": hd.get("comment"),
            "timestamp": hd.get("timestamp") or hd.get("at"),
            "status": checkpoint_b_on_disk.get("status"),
        }

    if not artifact or artifact["source_kind"] != "agent_experiment_regression":
        return None

    experiment = artifact["payload"].get("experiment") or {}
    cp_b = experiment.get("checkpoint_b_status") or {}
    if cp_b.get("delivery_plan_action"):
        return {
            "source": "experiment_checkpoint_b_status",
            "action": cp_b.get("delivery_plan_action"),
            "status": cp_b.get("status"),
            "message": cp_b.get("message"),
        }
    return None


def run_agent_audit_quickview(
    case_ref: str,
    *,
    repo_root: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Build read-only audit quickview dict for case_ref."""
    root = Path(repo_root).resolve() if repo_root is not None else _REPO_ROOT

    artifact = find_latest_run_artifact(case_ref, repo_root=root)
    cp_a_disk = find_latest_checkpoint(case_ref, "A", repo_root=root)
    cp_b_disk = find_latest_checkpoint(case_ref, "B", repo_root=root)

    decision = _normalize_decision_block(artifact)
    route = _normalize_route_block(artifact)
    checkpoint_a = _normalize_checkpoint_view(
        checkpoint_id="A",
        artifact=artifact,
        on_disk=cp_a_disk,
    )
    checkpoint_b = _normalize_checkpoint_view(
        checkpoint_id="B",
        artifact=artifact,
        on_disk=cp_b_disk,
    )
    delivery_approval = _normalize_delivery_approval(cp_b_disk, artifact)
    sandbox_artifact = find_latest_sandbox_bundle(case_ref, repo_root=root)
    sandbox_delivery: Optional[Dict[str, Any]] = None
    if sandbox_artifact:
        payload = sandbox_artifact.get("payload") or {}
        sandbox_delivery = {
            "found": True,
            "sandbox": True,
            "source_kind": sandbox_artifact.get("source_kind"),
            "artifact_path": sandbox_artifact.get("artifact_path"),
            "artifact_timestamp": sandbox_artifact.get("artifact_timestamp"),
            "bundle_dir": payload.get("bundle_dir"),
            "output_guard": payload.get("output_guard"),
            "checkpoint_trace": payload.get("checkpoint_trace"),
            "notify_triggered": payload.get("notify_triggered", False),
            "production_contract": payload.get("production_contract", False),
        }

    run_meta: Dict[str, Any] = {
        "found": artifact is not None,
        "source_kind": artifact["source_kind"] if artifact else None,
        "artifact_path": artifact["artifact_path"] if artifact else None,
        "artifact_timestamp": artifact["artifact_timestamp"] if artifact else None,
    }
    if artifact and artifact["source_kind"] == "agent_experiment_regression":
        case_summary = artifact["payload"].get("case_summary") or {}
        experiment = artifact["payload"].get("experiment") or {}
        run_meta.update(
            {
                "mode": case_summary.get("mode") or experiment.get("mode"),
                "final_status": case_summary.get("final_status")
                or experiment.get("final_status"),
                "experiment_id": case_summary.get("experiment_id")
                or experiment.get("experiment_id"),
                "task_type": experiment.get("task_type"),
                "flow_family": "tabular",
            }
        )
    elif artifact:
        payload = artifact["payload"]
        run_meta.update(
            {
                "mode": payload.get("mode"),
                "final_status": payload.get("final_status"),
                "experiment_id": payload.get("experiment_id"),
                "task_type": payload.get("task_type"),
                "flow_family": payload.get("flow_family") or "non_tabular",
            }
        )

    wf_consumer = load_workflow_events(case_ref, repo_root=root)
    wf_events = wf_consumer.get("events") or [] if wf_consumer.get("ok") else []
    notif_rows = [r for r in wf_events if r.get("source_stream") == "notification"]
    pending_ack_count = sum(1 for r in notif_rows if r.get("tracking_status") == "pending_ack")
    failed_ack_count = sum(1 for r in notif_rows if r.get("tracking_status") == "failed")
    notif_count_by_type: Dict[str, int] = {}
    for row in notif_rows:
        et = str(row.get("event_type", "unknown"))
        notif_count_by_type[et] = notif_count_by_type.get(et, 0) + 1
    workflow_notifications: Dict[str, Any] = {
        "found": bool(notif_rows),
        "count": len(notif_rows),
        "pending_ack_count": pending_ack_count,
        "failed_ack_count": failed_ack_count,
        "count_by_event_type": notif_count_by_type,
        "streams_read": wf_consumer.get("streams_read") or [],
        "events": wf_events,
        "consumer_ok": wf_consumer.get("ok", False),
    }

    ok = (
        artifact is not None
        or cp_a_disk is not None
        or cp_b_disk is not None
        or sandbox_artifact is not None
        or workflow_notifications["found"]
    )
    message = (
        "audit quickview assembled from on-disk artifacts"
        if ok
        else f"no agent-run or checkpoint artifacts found for case_ref={case_ref}"
    )

    result: Dict[str, Any] = {
        "ok": ok,
        "read_only": True,
        "schema_version": "agent_audit_quickview_v1",
        "case_ref": case_ref,
        "message": message,
        "latest_run": run_meta,
        "decision": decision,
        "planned_route": route,
        "checkpoint_a": checkpoint_a,
        "checkpoint_b": checkpoint_b,
        "delivery_approval": delivery_approval,
        "workflow_notifications": workflow_notifications,
    }
    if sandbox_delivery:
        result["sandbox_delivery"] = sandbox_delivery
    return result


def _relative_repo_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def collect_read_paths(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
) -> List[str]:
    """List filesystem paths consulted by a quickview run (for audit attestation)."""
    root = repo_root or _REPO_ROOT
    paths: List[str] = []

    for dir_name, _ in _RUN_ARTIFACT_DIRS:
        scan_root = root / "outbox" / dir_name
        if scan_root.is_dir():
            for path in scan_root.glob("*.json"):
                data = _load_json(path)
                if _artifact_matches_case_ref(
                    filename=path.name,
                    case_ref=case_ref,
                    data=data,
                    source_kind=dir_name,
                ):
                    paths.append(_relative_repo_path(path, root))

    outbox = case_outbox_dir(case_ref, root)
    if outbox.is_dir():
        for path in outbox.glob("checkpoint_*.json"):
            paths.append(_relative_repo_path(path, root))

    sandbox_root = root / "outbox" / "sandbox_delivery" / case_ref
    if sandbox_root.is_dir():
        for path in sandbox_root.rglob("manifest.json"):
            paths.append(_relative_repo_path(path, root))

    for rel in ("outbox/notification_events.jsonl", "outbox/checkpoint_events.jsonl"):
        p = root / Path(*rel.split("/"))
        if p.is_file():
            paths.append(rel)

    feedback_acks = root / "outbox" / "feedback" / case_ref / "acks"
    if feedback_acks.is_dir():
        for path in feedback_acks.glob("*.json"):
            paths.append(_relative_repo_path(path, root))

    return sorted(set(paths))


def format_audit_quickview_text(view: Dict[str, Any]) -> str:
    """Render human-readable audit quickview."""
    lines = [
        "Agent-Lines Audit Quickview (W10-T3 · read-only)",
        f"case_ref: {view.get('case_ref')}",
        f"ok: {view.get('ok')}",
        "",
    ]

    run = view.get("latest_run") or {}
    lines.append("── Latest Agent Run ──")
    lines.append(f"found: {run.get('found')}")
    if run.get("found"):
        lines.append(f"source: {run.get('source_kind')}")
        lines.append(f"artifact: {run.get('artifact_path')}")
        lines.append(f"timestamp: {run.get('artifact_timestamp')}")
        lines.append(f"mode: {run.get('mode')}")
        lines.append(f"final_status: {run.get('final_status')}")
        lines.append(f"task_type: {run.get('task_type')}")
        lines.append(f"experiment_id: {run.get('experiment_id')}")
    lines.append("")

    decision = view.get("decision") or {}
    lines.append("── Decision ──")
    lines.append(f"decision: {decision.get('decision')}")
    lines.append(f"risk_level: {decision.get('risk_level')}")
    if decision.get("message"):
        lines.append(f"message: {decision.get('message')}")
    lines.append("")

    route = view.get("planned_route") or {}
    lines.append("── Planned Route ──")
    lines.append(f"selector_task_type: {route.get('selector_task_type')}")
    tools = route.get("planned_tools") or []
    lines.append(f"planned_tools: {', '.join(tools) if tools else '(none)'}")
    if route.get("orchestration_tool_id"):
        lines.append(f"orchestration_tool_id: {route.get('orchestration_tool_id')}")
    lines.append("")

    cp_a = view.get("checkpoint_a") or {}
    lines.append("── Checkpoint A (Intake) ──")
    lines.append(f"would_trigger: {cp_a.get('would_trigger')}")
    lines.append(f"status: {cp_a.get('status')}")
    lines.append(f"on_disk: {cp_a.get('on_disk')}")
    if cp_a.get("checkpoint_path"):
        lines.append(f"path: {cp_a.get('checkpoint_path')}")
    hd_a = cp_a.get("human_decision") or {}
    if hd_a:
        lines.append(
            f"human_decision: action={hd_a.get('action')} "
            f"by={hd_a.get('operator_id') or hd_a.get('by')}"
        )
    lines.append("")

    cp_b = view.get("checkpoint_b") or {}
    lines.append("── Checkpoint B (Delivery) ──")
    lines.append(f"would_trigger: {cp_b.get('would_trigger')}")
    lines.append(f"status: {cp_b.get('status')}")
    lines.append(f"on_disk: {cp_b.get('on_disk')}")
    if cp_b.get("checkpoint_path"):
        lines.append(f"path: {cp_b.get('checkpoint_path')}")
    hd_b = cp_b.get("human_decision") or {}
    if hd_b:
        lines.append(
            f"human_decision: action={hd_b.get('action')} "
            f"by={hd_b.get('operator_id') or hd_b.get('by')}"
        )
    lines.append("")

    delivery = view.get("delivery_approval")
    lines.append("── Delivery Approval ──")
    if delivery:
        lines.append(f"source: {delivery.get('source')}")
        lines.append(f"action: {delivery.get('action')}")
        lines.append(f"status: {delivery.get('status')}")
        if delivery.get("operator_id"):
            lines.append(f"operator_id: {delivery.get('operator_id')}")
        if delivery.get("comment"):
            lines.append(f"comment: {delivery.get('comment')}")
        if delivery.get("timestamp"):
            lines.append(f"timestamp: {delivery.get('timestamp')}")
    else:
        lines.append("(none recorded)")

    lines.append("")
    lines.append(f"message: {view.get('message')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only agent-lines audit quickview (W10-T3). "
            "Spec: docs/audit-quickview-and-case-history-spec-v1.md"
        ),
    )
    parser.add_argument(
        "--case-ref",
        required=True,
        help="Case slug under cases/ (e.g. demo_phase, sampleco/2026-0001)",
    )
    parser.add_argument(
        "--view",
        choices=("wire", "investigation"),
        default="wire",
        help="Output view: wire quickview (default) or investigation projection (spec §2.4)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional repo root override (default: parent of scripts/)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    wire = run_agent_audit_quickview(args.case_ref, repo_root=repo_root)
    wire["sources_read"] = collect_read_paths(args.case_ref, repo_root=repo_root)

    if args.view == "investigation":
        output = project_audit_investigation_view(wire)
        output["sources_read"] = wire.get("sources_read", [])
    else:
        output = wire

    if args.format == "json":
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        if args.view == "investigation":
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print(format_audit_quickview_text(output))

    return 0 if output.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
