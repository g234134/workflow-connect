"""Delivery approval one-click CLI v1 (W8-T3).

Integrates delivery signoff review, output_guard summary, Checkpoint B human
decision recording, and optional controlled notify experiment. Preview by default;
requires explicit confirm before persisting decisions (HITL).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from delivery.controlled_notify_experiment_v1 import run_controlled_notify_experiment
# F3: Import notification gateway for human approval event emission
from delivery.notification_gateway_v1 import (
    build_notification_event,
    send_notification,
)
from hitl.checkpoint_b_integration_v1 import (
    CHECKPOINT_B_ID,
    delivery_plan_from_checkpoint_b,
)
from hitl.checkpoints_v1 import (
    CHECKPOINT_B_ACTIONS,
    get_checkpoint,
    record_human_decision,
)
from tools.tabular_tool_executor import resolve_case_ref

CLI_VERSION = "v1"

CLI_ACTION_ALIASES: Dict[str, str] = {
    "approve": "approve_delivery",
    "request_changes": "request_changes",
    "hold": "hold",
}

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return repo_root.resolve() if repo_root is not None else _REPO_ROOT


def _case_dir_rel(case_path: Path, root: Path, case_ref: str) -> str:
    try:
        return case_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return case_ref


def _normalize_case_dir(
    case_dir: Union[str, Path],
    repo_root: Optional[Path] = None,
) -> Path:
    root = _repo_root(repo_root)
    path = Path(case_dir)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _parse_signoff_fields(signoff_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in signoff_text.splitlines():
        match = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line.strip())
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip().strip("_")
        if key in {"field", "-------"}:
            continue
        fields[key] = value
    return fields


def normalize_cli_action(action: str) -> str:
    """Map CLI shorthand (approve) to checkpoint action (approve_delivery)."""
    key = str(action or "").strip().lower()
    if key in CLI_ACTION_ALIASES:
        return CLI_ACTION_ALIASES[key]
    if key in CHECKPOINT_B_ACTIONS:
        return key
    allowed = sorted(set(CLI_ACTION_ALIASES) | set(CLI_ACTION_ALIASES.values()))
    raise ValueError(f"invalid action {action!r}; allowed: {allowed}")


def _emit_checkpoint_approved_for_human(
    checkpoint_id: str,
    case_ref: str,
    operator_id: str,
    decision_time: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    enabled: bool = True,
) -> Optional[Dict[str, Any]]:
    """F3: Emit checkpoint.approved event when human approves delivery.
    
    This is separate from auto_approved events from the orchestrator.
    Returns notification result dict or None if disabled/failed.
    """
    if not enabled:
        return None
    
    try:
        event = build_notification_event(
            "checkpoint.approved",
            case_ref=case_ref,
            checkpoint_id=checkpoint_id,
            checkpoint_status="approved",
            approval_source="human",
            artifacts={
                "approver": operator_id,
                "decision_time": decision_time,
            },
            status_summary={
                "final_status": "approved_by_human",
                "mode": "run",
            },
            source={
                "step_id": "CLI",
                "module": "delivery.delivery_approval_cli_v1",
            },
        )
        return send_notification(
            event,
            enabled=True,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
        )
    except Exception:
        # Best-effort: never raise, failures don't block main flow
        return None


def build_approval_review_summary(
    case_dir: Union[str, Path],
    *,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Load signoff, output_guard, and row metrics for human review display."""
    root = _repo_root(repo_root)
    case_path = _normalize_case_dir(case_dir, root)
    case_ref = resolve_case_ref(case_path)

    if not case_path.is_dir():
        return {
            "ok": False,
            "message": f"case directory not found: {case_dir}",
            "case_ref": case_ref,
        }

    signoff_path = case_path / "delivery_signoff.md"
    report_path = case_path / "reports" / "report.json"
    cleaning_stats_path = case_path / "reports" / "cleaning_stats.json"

    missing: list[str] = []
    if not signoff_path.is_file():
        missing.append("delivery_signoff.md")
    if not report_path.is_file():
        missing.append("reports/report.json")

    if missing:
        return {
            "ok": False,
            "message": "missing required delivery review inputs",
            "case_ref": case_ref,
            "missing": missing,
        }

    report = _load_json(report_path) or {}
    cleaning_stats = _load_json(cleaning_stats_path) or {}
    signoff_text = signoff_path.read_text(encoding="utf-8")
    signoff_fields = _parse_signoff_fields(signoff_text)

    output_guard = report.get("output_guard") if isinstance(report.get("output_guard"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    row_counts = cleaning_stats.get("row_counts") if isinstance(cleaning_stats.get("row_counts"), dict) else {}

    input_rows = output_guard.get("input_rows") or row_counts.get("intake") or summary.get("total_rows")
    output_rows = output_guard.get("output_rows") or row_counts.get("ok") or summary.get("accepted_rows")
    removal_ratio = output_guard.get("ratio") or output_guard.get("removal_ratio")
    if removal_ratio is None and isinstance(input_rows, int) and isinstance(output_rows, int) and input_rows > 0:
        removal_ratio = round((input_rows - output_rows) / input_rows, 4)

    return {
        "ok": True,
        "message": "delivery approval review summary loaded",
        "case_ref": case_ref,
        "case_dir": _case_dir_rel(case_path, root, case_ref),
        "delivery_signoff": {
            "path": "delivery_signoff.md",
            "fields": signoff_fields,
            "preview_lines": signoff_text.strip().splitlines()[:8],
        },
        "output_guard": {
            "status": output_guard.get("status"),
            "checks": output_guard.get("checks"),
            "ratio": output_guard.get("ratio"),
            "threshold": output_guard.get("threshold"),
        },
        "metrics": {
            "input_rows": input_rows,
            "output_rows": output_rows,
            "removed_rows": max(int(input_rows) - int(output_rows), 0)
            if isinstance(input_rows, int) and isinstance(output_rows, int)
            else None,
            "removal_ratio": removal_ratio,
            "qa_status": summary.get("qa_status"),
            "accepted_rows": summary.get("accepted_rows"),
            "rejected_rows": summary.get("rejected_rows"),
            "total_rows": summary.get("total_rows"),
        },
    }


def _patch_checkpoint_resume_context(
    checkpoint_id: str,
    resume_context: dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> None:
    """Persist resume_context patches (e.g. revise_target=bundle) on checkpoint file."""
    checkpoint = get_checkpoint(
        checkpoint_id,
        pending_only=False,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    if checkpoint is None:
        return

    checkpoint_path = checkpoint.get("checkpoint_path")
    if not checkpoint_path:
        return

    path = _repo_root(repo_root) / checkpoint_path
    if not path.is_file():
        return

    updated = dict(checkpoint)
    updated["resume_context"] = dict(resume_context)
    human = dict(updated.get("human_decision") or {})
    if resume_context.get("revise_target"):
        human["revise_target"] = resume_context["revise_target"]
    if resume_context.get("change_request"):
        human["change_request"] = resume_context["change_request"]
    updated["human_decision"] = human

    path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_delivery_approval(
    case_dir: Union[str, Path],
    checkpoint_id: str,
    action: str,
    notes: str = "",
    *,
    confirm: bool = False,
    revise_target: Optional[str] = None,
    operator_id: str = "operator_cli",
    run_notify_experiment: bool = False,
    notify_dry_run: bool = True,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> dict[str, Any]:
    """One-click delivery approval flow: review → optional confirm → optional notify."""
    root = _repo_root(repo_root)
    case_path = _normalize_case_dir(case_dir, root)
    case_ref = resolve_case_ref(case_path)

    try:
        internal_action = normalize_cli_action(action)
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "case_ref": case_ref}

    if checkpoint_id != CHECKPOINT_B_ID:
        return {
            "ok": False,
            "message": f"W8-T3 CLI supports {CHECKPOINT_B_ID!r} only; got {checkpoint_id!r}",
            "case_ref": case_ref,
        }

    review = build_approval_review_summary(case_path, repo_root=root)
    if not review.get("ok"):
        return {
            "ok": False,
            "message": str(review.get("message") or "review summary failed"),
            "case_ref": case_ref,
            "review_summary": review,
        }

    if review.get("case_ref") != case_ref:
        return {
            "ok": False,
            "message": f"case_ref mismatch: dir resolves to {case_ref!r}, review has {review.get('case_ref')!r}",
            "case_ref": case_ref,
            "review_summary": review,
        }

    extra = {}
    if outbox_root_override:
        extra["outbox_root_override"] = outbox_root_override
    if repo_root is not None:
        extra["repo_root"] = root

    checkpoint = get_checkpoint(checkpoint_id, pending_only=True, **extra)
    checkpoint_status = "not_found"
    if checkpoint is not None:
        checkpoint_status = str(checkpoint.get("status") or "unknown")
        cp_ref = str(checkpoint.get("case_ref") or "")
        if cp_ref and cp_ref != case_ref:
            return {
                "ok": False,
                "message": f"checkpoint case_ref {cp_ref!r} does not match {case_ref!r}",
                "case_ref": case_ref,
                "review_summary": review,
                "checkpoint_status": checkpoint_status,
            }

    result: dict[str, Any] = {
        "ok": True,
        "message": "preview only; pass confirm=True to record decision"
        if not confirm
        else "delivery approval recorded",
        "cli_version": CLI_VERSION,
        "case_ref": case_ref,
        "checkpoint_id": checkpoint_id,
        "action": action,
        "internal_action": internal_action,
        "confirmed": confirm,
        "external_dispatch": False,
        "review_summary": review,
        "checkpoint_status": checkpoint_status,
        "resume_context": None,
        "delivery_plan": None,
        "notify_experiment": None,
    }

    if not confirm:
        return result

    if checkpoint is None:
        return {
            "ok": False,
            "message": f"no pending checkpoint found for id: {checkpoint_id}",
            "case_ref": case_ref,
            "review_summary": review,
            "confirmed": False,
        }

    if internal_action == "request_changes" and revise_target in ("cleaning", "bundle"):
        pass
    elif internal_action == "request_changes" and revise_target is not None:
        return {
            "ok": False,
            "message": f"invalid revise_target {revise_target!r}; allowed: cleaning, bundle",
            "case_ref": case_ref,
            "review_summary": review,
        }

    try:
        resume_context = record_human_decision(
            checkpoint_id,
            internal_action,
            notes,
            operator_id=operator_id,
            **extra,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "case_ref": case_ref,
            "review_summary": review,
            "confirmed": False,
        }

    if internal_action == "request_changes":
        target = revise_target or "cleaning"
        resume_context["revise_target"] = target
        resume_context["resume_from"] = target
        if notes:
            resume_context["change_request"] = notes
        _patch_checkpoint_resume_context(
            checkpoint_id,
            resume_context,
            repo_root=root,
            outbox_root_override=outbox_root_override,
        )

    delivery_plan = delivery_plan_from_checkpoint_b(resume_context)
    result["resume_context"] = resume_context
    result["delivery_plan"] = delivery_plan
    result["message"] = str(delivery_plan.get("message") or result["message"])

    # F3: Emit checkpoint.approved notification when human approves
    notification_result: Optional[Dict[str, Any]] = None
    if internal_action == "approve_delivery":
        decision_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        notification_result = _emit_checkpoint_approved_for_human(
            checkpoint_id,
            case_ref,
            operator_id,
            decision_time,
            repo_root=root,
            outbox_root_override=outbox_root_override,
            enabled=True,  # Always emit when human approves (can be made configurable)
        )
        if notification_result:
            result["notification_event"] = {
                "ok": notification_result.get("ok"),
                "event_id": notification_result.get("event_id"),
                "path": (notification_result.get("sink_result") or {}).get("path"),
            }

    if not delivery_plan.get("ok"):
        result["ok"] = False

    if run_notify_experiment and internal_action == "approve_delivery":
        notify_result = run_controlled_notify_experiment(
            case_path,
            dry_run=notify_dry_run,
            repo_root=root,
            outbox_root_override=outbox_root_override,
        )
        result["notify_experiment"] = {
            "ok": notify_result.get("ok"),
            "message": notify_result.get("message"),
            "dry_run": notify_result.get("dry_run"),
            "simulated": notify_result.get("simulated"),
            "external_dispatch": notify_result.get("external_dispatch"),
            "outbox_path": notify_result.get("outbox_path"),
            "skipped": False,
        }
        result["external_dispatch"] = False
    elif run_notify_experiment:
        result["notify_experiment"] = {
            "ok": True,
            "skipped": True,
            "message": "notify experiment skipped for non-approve actions",
            "external_dispatch": False,
        }
    else:
        result["notify_experiment"] = {
            "ok": True,
            "skipped": True,
            "message": "notify experiment not requested",
            "external_dispatch": False,
        }

    return result
