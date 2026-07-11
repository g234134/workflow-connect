"""Checkpoint B integration v1 — delivery gate for Agent-run experiment line (W6-T6).

Bridges output_guard / delivery_draft / execution_summary into HITL checkpoint B
state under outbox/. Tool-layer only; does not notify clients or resume main chain.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from hitl.checkpoints_v1 import (
    CHECKPOINT_B_ID,
    CHECKPOINT_SCHEMA_VERSION,
    build_resume_context,
    suggested_actions,
    write_checkpoint,
)
from tools.tabular_tool_executor import resolve_case_ref

CHECKPOINT_B_VERSION = "v1"
DEFAULT_TASK_TYPE = "tabular.cleaning.mvp"
CHECKPOINT_B_EXPIRY_MINUTES = 5

_REPO_ROOT = Path(__file__).resolve().parents[1]

_TRIGGER_STATUSES = frozenset({"warning", "blocked"})
_SKIP_OK_STATUSES = frozenset({"ok"})
_TERMINAL_STATUSES = frozenset({"error"})


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return repo_root.resolve() if repo_root is not None else _REPO_ROOT


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_expires_iso(minutes: int = CHECKPOINT_B_EXPIRY_MINUTES) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return expires.strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _guard_status(output_guard: Dict[str, Any]) -> str:
    return str(output_guard.get("status") or "").strip().lower()


def _derive_cleaning_results(
    execution_summary: Dict[str, Any],
    output_guard: Dict[str, Any],
) -> Dict[str, Any]:
    explicit = execution_summary.get("cleaning_results")
    if isinstance(explicit, dict) and explicit:
        return dict(explicit)

    ratio = output_guard.get("removal_ratio")
    if ratio is None:
        ratio = execution_summary.get("removal_ratio")

    input_rows = output_guard.get("input_rows") or execution_summary.get("input_rows")
    output_rows = output_guard.get("output_rows") or execution_summary.get("output_rows")
    removed_rows = None
    if isinstance(input_rows, int) and isinstance(output_rows, int):
        removed_rows = max(input_rows - output_rows, 0)

    qa_status = "pass"
    status = _guard_status(output_guard)
    if status == "warning":
        qa_status = "pass_with_warnings"
    elif status in ("blocked", "error"):
        qa_status = "fail"

    return {
        "input_rows": input_rows,
        "output_rows": output_rows,
        "removed_rows": removed_rows,
        "removal_ratio": ratio,
        "qa_status": qa_status,
    }


def _derive_delivery_draft(
    output_guard: Dict[str, Any],
    cleaning_results: Dict[str, Any],
    artifacts: Dict[str, Any],
) -> Dict[str, Any]:
    explicit = output_guard.get("delivery_draft")
    if isinstance(explicit, dict) and explicit.get("summary_text"):
        return dict(explicit)

    input_rows = cleaning_results.get("input_rows")
    output_rows = cleaning_results.get("output_rows")
    removed_rows = cleaning_results.get("removed_rows")
    status = _guard_status(output_guard)

    parts: List[str] = []
    if input_rows is not None and output_rows is not None:
        parts.append(f"已清洗 {input_rows}→{output_rows} rows")
    if removed_rows is not None:
        parts.append(f"移除 {removed_rows} 行")
    if status:
        parts.append(f"output_guard.status={status}")
    if artifacts.get("signoff"):
        parts.append(f"signoff={artifacts['signoff']}")

    confidence = 0.85 if status == "ok" else 0.6 if status == "warning" else 0.4
    return {
        "summary_text": "；".join(parts) if parts else "Delivery draft (auto-generated)",
        "confidence_score": confidence,
    }


def should_create_checkpoint_b(
    output_guard: Dict[str, Any],
    *,
    auto_approve: bool = False,
) -> bool:
    """Return True when v1 rules require a human Checkpoint B."""
    status = _guard_status(output_guard)
    if status in _TERMINAL_STATUSES:
        return False
    if status in _TRIGGER_STATUSES:
        return True
    if status in _SKIP_OK_STATUSES and auto_approve:
        return False
    return False


def build_checkpoint_b_payload(
    case_dir: Union[str, Path],
    execution_summary: Dict[str, Any],
    output_guard: Dict[str, Any],
    artifacts: Dict[str, Any],
    *,
    task_type: str = DEFAULT_TASK_TYPE,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build checkpoint B state dict (not yet persisted)."""
    root = _repo_root(repo_root)
    case_path = _normalize_case_dir(case_dir, repo_root=root)
    case_ref = resolve_case_ref(case_path, {"case_ref": execution_summary.get("case_ref")})

    created_at = _utc_now_iso()
    cleaning_results = _derive_cleaning_results(execution_summary, output_guard)
    delivery_draft = _derive_delivery_draft(output_guard, cleaning_results, artifacts)

    tools_executed = execution_summary.get("tools_executed") or []
    outbox_runs = execution_summary.get("outbox_runs") or []

    agent_output: Dict[str, Any] = {
        "task_type": task_type,
        "execution_summary": {
            "tools_executed": list(tools_executed),
            "outbox_runs": list(outbox_runs),
        },
        "cleaning_results": cleaning_results,
        "artifacts": dict(artifacts),
        "output_guard": dict(output_guard),
        "delivery_draft": delivery_draft,
    }

    run_id = execution_summary.get("run_id") or (
        f"{created_at.replace(':', '-').replace('.', '-')}_delivery_confirm"
    )

    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_B_ID,
        "case_ref": case_ref,
        "run_id": run_id,
        "status": "awaiting_human",
        "created_at": created_at,
        "expires_at": _utc_expires_iso(),
        "task_type": task_type,
        "agent_output": agent_output,
        "checkpoint": {
            "id": CHECKPOINT_B_ID,
            "version": CHECKPOINT_B_VERSION,
            "triggered_at": created_at,
            "case_ref": case_ref,
            "task_type": task_type,
        },
        "human_decision": None,
        "resume_context": None,
        "case_dir": _case_dir_rel(case_path, root, case_ref),
    }


def _auto_delivery_plan(
    *,
    case_ref: str,
    output_guard: Dict[str, Any],
    artifacts: Dict[str, Any],
    skip_reason: str,
) -> Dict[str, Any]:
    return {
        "ok": True,
        "checkpoint_id": CHECKPOINT_B_ID,
        "case_ref": case_ref,
        "action": "auto_approve",
        "skip_reason": skip_reason,
        "resume_from": "delivery",
        "proceed_to_delivery": True,
        "update_case_status": "delivered",
        "notify_client": False,
        "artifacts": dict(artifacts),
        "output_guard_status": _guard_status(output_guard),
        "next_steps": ["S13_delivery_approval", "S14_ledger_update"],
        "message": "Checkpoint B skipped; proceed to delivery gate (no client notify in v1).",
    }


def _await_human_delivery_plan(
    *,
    case_ref: str,
    checkpoint: Dict[str, Any],
    checkpoint_path: Optional[str],
) -> Dict[str, Any]:
    return {
        "ok": True,
        "checkpoint_id": CHECKPOINT_B_ID,
        "case_ref": case_ref,
        "action": "await_human",
        "resume_from": None,
        "proceed_to_delivery": False,
        "update_case_status": None,
        "notify_client": False,
        "checkpoint_path": checkpoint_path,
        "suggested_actions": suggested_actions(CHECKPOINT_B_ID),
        "delivery_draft": (checkpoint.get("agent_output") or {}).get("delivery_draft"),
        "output_guard": (checkpoint.get("agent_output") or {}).get("output_guard"),
        "next_steps": ["human_review", "apply_decision_via_cli_or_experiment"],
        "message": "Checkpoint B created; awaiting human decision.",
    }


def _terminal_delivery_plan(
    *,
    case_ref: str,
    output_guard: Dict[str, Any],
    message: str,
) -> Dict[str, Any]:
    return {
        "ok": False,
        "checkpoint_id": CHECKPOINT_B_ID,
        "case_ref": case_ref,
        "action": "blocked",
        "resume_from": None,
        "proceed_to_delivery": False,
        "update_case_status": None,
        "notify_client": False,
        "output_guard_status": _guard_status(output_guard),
        "next_steps": [],
        "message": message,
    }


def maybe_create_checkpoint_b(
    case_dir: Union[str, Path],
    execution_summary: Dict[str, Any],
    output_guard: Dict[str, Any],
    artifacts: Dict[str, Any],
    auto_approve: bool = False,
    *,
    task_type: str = DEFAULT_TASK_TYPE,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    write_state: bool = True,
) -> Dict[str, Any]:
    """Create Checkpoint B when v1 rules require human review; else return skip plan."""
    root = _repo_root(repo_root)
    case_path = _normalize_case_dir(case_dir, repo_root=root)
    case_ref = resolve_case_ref(case_path, {"case_ref": execution_summary.get("case_ref")})
    status = _guard_status(output_guard)

    if status in _TERMINAL_STATUSES:
        plan = _terminal_delivery_plan(
            case_ref=case_ref,
            output_guard=output_guard,
            message=f"output_guard.status={status}; checkpoint B not created (flow terminates).",
        )
        return {
            "ok": False,
            "checkpoint_created": False,
            "skipped": True,
            "skip_reason": f"terminal_status:{status}",
            "checkpoint": None,
            "checkpoint_path": None,
            "delivery_plan": plan,
        }

    if not should_create_checkpoint_b(output_guard, auto_approve=auto_approve):
        reason = "ok_with_auto_approve" if status == "ok" and auto_approve else "ok_no_human_gate"
        plan = _auto_delivery_plan(
            case_ref=case_ref,
            output_guard=output_guard,
            artifacts=artifacts,
            skip_reason=reason,
        )
        return {
            "ok": True,
            "checkpoint_created": False,
            "skipped": True,
            "skip_reason": reason,
            "checkpoint": None,
            "checkpoint_path": None,
            "delivery_plan": plan,
        }

    checkpoint = build_checkpoint_b_payload(
        case_path,
        execution_summary,
        output_guard,
        artifacts,
        task_type=task_type,
        repo_root=root,
    )

    checkpoint_path: Optional[str] = None
    if write_state:
        dest = write_checkpoint(
            checkpoint,
            repo_root=root,
            outbox_root_override=outbox_root_override,
        )
        # FIX (W6-T5/W6-T6-fix-outbox-root-override): Support custom outbox outside repo.
        # Try repo_root first (backward compat), then outbox_root, then absolute.
        try:
            checkpoint_path = str(dest.relative_to(root))
        except ValueError:
            # outbox is outside repo; compute relative to outbox_root instead
            from tools.tabular_outbox_writer import outbox_root as get_outbox_root
            outbox_base = Path(outbox_root_override) if outbox_root_override else get_outbox_root(root)
            try:
                checkpoint_path = str(dest.relative_to(outbox_base))
            except ValueError:
                # Final fallback: absolute path
                checkpoint_path = str(dest.resolve())

    plan = _await_human_delivery_plan(
        case_ref=case_ref,
        checkpoint=checkpoint,
        checkpoint_path=checkpoint_path,
    )
    return {
        "ok": True,
        "checkpoint_created": True,
        "skipped": False,
        "skip_reason": None,
        "checkpoint": checkpoint,
        "checkpoint_path": checkpoint_path,
        "delivery_plan": plan,
    }


def _resolve_revise_target(resume_context: Dict[str, Any]) -> str:
    explicit = resume_context.get("revise_target") or resume_context.get("resume_target")
    if explicit in ("cleaning", "bundle"):
        return str(explicit)

    human = resume_context.get("human_decision") or {}
    target = human.get("revise_target")
    if target in ("cleaning", "bundle"):
        return str(target)

    resume_from = resume_context.get("resume_from")
    if resume_from in ("cleaning", "bundle"):
        return str(resume_from)

    return "cleaning"


def delivery_plan_from_checkpoint_b(resume_context: Dict[str, Any]) -> Dict[str, Any]:
    """Translate post-decision resume_context into a delivery plan for experiment consumers."""
    checkpoint_id = str(resume_context.get("checkpoint_id", ""))
    if checkpoint_id != CHECKPOINT_B_ID:
        return {
            "ok": False,
            "message": f"expected checkpoint_id={CHECKPOINT_B_ID}; got {checkpoint_id!r}",
        }

    case_ref = str(resume_context.get("case_ref", ""))
    human = resume_context.get("human_decision") or {}
    action = str(human.get("action", ""))
    resume_from = resume_context.get("resume_from")
    artifacts = resume_context.get("artifacts") or {}
    original = resume_context.get("original_decision") or {}

    base: Dict[str, Any] = {
        "ok": True,
        "checkpoint_id": CHECKPOINT_B_ID,
        "case_ref": case_ref,
        "human_action": action,
        "resume_from": resume_from,
        "original_decision": dict(original),
        "artifacts": dict(artifacts),
        "notify_client": False,
    }

    if action == "approve_delivery":
        base.update(
            {
                "action": "approve_delivery",
                "proceed_to_delivery": True,
                "update_case_status": "delivered",
                "next_steps": ["S13_delivery_approval", "S14_ledger_update"],
                "message": "Human approved delivery; proceed without re-running tools.",
            }
        )
        return base

    if action == "request_changes":
        revise_target = _resolve_revise_target(resume_context)
        base.update(
            {
                "action": "request_changes",
                "proceed_to_delivery": False,
                "update_case_status": "changes_requested",
                "revise_target": revise_target,
                "resume_from": revise_target,
                "change_request": resume_context.get("change_request")
                or human.get("comment")
                or "",
                "next_steps": [f"re_run_{revise_target}", "return_to_checkpoint_b"],
                "message": f"Human requested changes; re-run from {revise_target}.",
            }
        )
        return base

    if action == "hold":
        base.update(
            {
                "action": "hold",
                "proceed_to_delivery": False,
                "update_case_status": "on_hold",
                "resume_from": None,
                "next_steps": ["await_manual_resume"],
                "message": "Case on hold; no delivery or tool re-run until resumed.",
            }
        )
        return base

    return {
        "ok": False,
        "checkpoint_id": CHECKPOINT_B_ID,
        "case_ref": case_ref,
        "message": f"unsupported human action for checkpoint B: {action!r}",
        "suggested_actions": suggested_actions(CHECKPOINT_B_ID),
    }


def delivery_plan_from_human_decision(
    checkpoint: Dict[str, Any],
    human_decision: Dict[str, Any],
) -> Dict[str, Any]:
    """Build delivery plan from checkpoint state + human decision (no file I/O)."""
    resume_context = build_resume_context(checkpoint, human_decision)
    if human_decision.get("revise_target") in ("cleaning", "bundle"):
        resume_context["revise_target"] = human_decision["revise_target"]
        resume_context["resume_from"] = human_decision["revise_target"]
    if human_decision.get("change_request"):
        resume_context["change_request"] = human_decision["change_request"]
    return delivery_plan_from_checkpoint_b(resume_context)
