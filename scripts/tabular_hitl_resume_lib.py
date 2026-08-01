"""Tabular HITL checkpoint resume integration (v1).

Bridges outbox checkpoint decisions with ``automation_state.json`` and the
unified tabular driver. CP-A approve resumes at ``cleaning``; CP-B approve
marks ``approved_for_delivery`` (chain complete).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hitl.checkpoint_a_integration_v1 import case_ref_from_case_dir  # noqa: E402
from hitl.checkpoints_v1 import (  # noqa: E402
    CHECKPOINT_A_ID,
    CHECKPOINT_B_ID,
    list_pending_checkpoints,
    record_human_decision,
)
from tabular_automation_driver_lib import resolve_case_dir, run_tabular_automation  # noqa: E402
from tabular_automation_state_lib import (  # noqa: E402
    PAUSE_REASON_CHECKPOINT_A,
    PAUSE_REASON_CHECKPOINT_B,
    load_state,
    resume_automation,
    save_state,
    utc_now_iso,
    validate_case_dir,
)
from tabular_checkpoint_sync_lib import sync_checkpoint_b_state_and_readiness  # noqa: E402
from tabular_internal_notify_lib import (  # noqa: E402
    EVENT_CHECKPOINT_REJECTED,
    notify_internal,
)

CheckpointLetter = Literal["a", "b"]

_CP_A_HITL_ACTIONS = {"approve-a": "approve", "reject-a": "reject"}
_CP_B_HITL_ACTIONS = {"approve-b": "approve_delivery", "reject-b": "hold"}


def driver_resume_step_from_context(resume_context: dict[str, Any]) -> str | None:
    """Map HITL resume_context to unified driver step names."""
    checkpoint_id = str(resume_context.get("checkpoint_id", ""))
    human = resume_context.get("human_decision") or {}
    action = str(human.get("action", ""))
    resume_from = resume_context.get("resume_from")

    if checkpoint_id == CHECKPOINT_A_ID:
        if action == "approve":
            return "cleaning"
        if action == "revise_plan":
            return "eligibility"
        if action == "reject":
            return None

    if checkpoint_id == CHECKPOINT_B_ID:
        if action == "approve_delivery":
            return "approved_for_delivery"
        if action == "request_changes":
            target = resume_from or "cleaning"
            return target if target in ("cleaning", "bundle") else "cleaning"
        if action == "hold":
            return None

    return None


def _checkpoint_status_for_action(checkpoint: CheckpointLetter, hitl_action: str) -> str:
    if checkpoint == "a":
        return "approved" if hitl_action == "approve-a" else "rejected"
    return "approved" if hitl_action == "approve-b" else "rejected"


def _find_pending_checkpoint_id(
    case_ref: str,
    checkpoint_id: str,
    *,
    outbox_root_override: str | None = None,
) -> str | None:
    extra: dict[str, Any] = {"case_ref": case_ref}
    if outbox_root_override:
        extra["outbox_root_override"] = outbox_root_override
    pending = list_pending_checkpoints(**extra)
    matches = [row for row in pending if row.get("checkpoint_id") == checkpoint_id]
    if not matches:
        return None
    matches.sort(key=lambda row: str(row.get("created_at", "")))
    return str(matches[-1]["checkpoint_id"])


def apply_tabular_checkpoint_decision(
    case_dir: Path,
    *,
    command: str,
    operator_id: str = "operator_cli",
    notes: str = "",
    outbox_root_override: str | None = None,
) -> dict[str, Any]:
    """Record CP-A/B human decision and update automation_state.json."""
    err = validate_case_dir(case_dir)
    if err:
        return {**err, "command": command}

    case_dir = case_dir.resolve()
    state = load_state(case_dir)
    if state.get("ok") is False:
        return {**state, "command": command}

    try:
        rel = case_dir.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        rel = str(case_dir)
    case_ref = case_ref_from_case_dir(rel)
    extra: dict[str, Any] = {}
    if outbox_root_override:
        extra["outbox_root_override"] = outbox_root_override

    if command in _CP_A_HITL_ACTIONS:
        checkpoint: CheckpointLetter = "a"
        checkpoint_id = CHECKPOINT_A_ID
        hitl_decision = _CP_A_HITL_ACTIONS[command]
        status_field = "checkpoint_a_status"
        by_field = "checkpoint_a_decided_by"
        at_field = "checkpoint_a_decided_at"
        expected_pause = PAUSE_REASON_CHECKPOINT_A
    elif command in _CP_B_HITL_ACTIONS:
        checkpoint = "b"
        checkpoint_id = CHECKPOINT_B_ID
        hitl_decision = _CP_B_HITL_ACTIONS[command]
        status_field = "checkpoint_b_status"
        by_field = "checkpoint_b_decided_by"
        at_field = "checkpoint_b_decided_at"
        expected_pause = PAUSE_REASON_CHECKPOINT_B
    else:
        return {
            "ok": False,
            "command": command,
            "message": f"unsupported tabular checkpoint command: {command!r}",
        }

    if state.get(status_field) != "pending":
        return {
            "ok": False,
            "command": command,
            "case_dir": str(case_dir),
            "message": (
                f"{status_field}={state.get(status_field)!r}; expected pending "
                f"(pause_reason={state.get('pause_reason')!r})"
            ),
            "state": state,
        }

    if state.get("pause_reason") not in (expected_pause, None):
        return {
            "ok": False,
            "command": command,
            "case_dir": str(case_dir),
            "message": (
                f"pause_reason={state.get('pause_reason')!r}; expected {expected_pause!r}"
            ),
            "state": state,
        }

    resolved_id = _find_pending_checkpoint_id(
        case_ref, checkpoint_id, outbox_root_override=outbox_root_override
    )
    if resolved_id is None:
        return {
            "ok": False,
            "command": command,
            "case_dir": str(case_dir),
            "case_ref": case_ref,
            "message": f"no pending outbox checkpoint for {checkpoint_id} / {case_ref}",
            "state": state,
        }

    try:
        resume_context = record_human_decision(
            resolved_id,
            hitl_decision,
            notes,
            operator_id=operator_id,
            **extra,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "command": command,
            "case_dir": str(case_dir),
            "message": str(exc),
            "state": state,
        }

    decided_at = utc_now_iso()
    cp_status = _checkpoint_status_for_action(checkpoint, command)
    resume_step = driver_resume_step_from_context(resume_context)

    state[status_field] = cp_status
    state[by_field] = operator_id
    state[at_field] = decided_at
    state["requires_hitl_checkpoint"] = False
    state["last_transition_ts"] = decided_at

    if cp_status == "approved" and resume_step:
        state["checkpoint_resume_step"] = resume_step
        state["allowed_to_auto_proceed"] = True
        state["last_error"] = None
        if resume_step == "approved_for_delivery":
            state["automation_status"] = "completed"
            state["pause_reason"] = None
            state["current_step"] = "approved_for_delivery"
        else:
            state["pause_reason"] = f"checkpoint_{checkpoint}_approved_awaiting_resume"
    else:
        state["checkpoint_resume_step"] = None
        state["allowed_to_auto_proceed"] = False
        state["automation_status"] = "stopped" if cp_status == "rejected" else "paused"
        state["pause_reason"] = (
            f"checkpoint_{checkpoint}_rejected"
            if cp_status == "rejected"
            else f"checkpoint_{checkpoint}_held"
        )
        state["last_error"] = notes or f"{command} recorded; no auto resume"

    save_state(case_dir, state)

    if checkpoint == "b" and cp_status == "approved":
        sync_checkpoint_b_state_and_readiness(
            case_dir,
            checkpoint_b_status="approved",
            step_status="completed",
            current_step=state.get("current_step"),
            updated_by=operator_id,
        )

    if cp_status == "rejected":
        notify_internal(
            case_dir,
            EVENT_CHECKPOINT_REJECTED,
            {
                "checkpoint": checkpoint,
                "checkpoint_id": checkpoint_id,
                "checkpoint_status": cp_status,
                "command": command,
                "operator_id": operator_id,
                "notes": notes,
            },
            case_id=state.get("case_id"),
        )

    return {
        "ok": True,
        "command": command,
        "case_dir": str(case_dir),
        "case_ref": case_ref,
        "checkpoint_id": checkpoint_id,
        "checkpoint_status": cp_status,
        "resume_context": resume_context,
        "checkpoint_resume_step": state.get("checkpoint_resume_step"),
        "automation_status": state.get("automation_status"),
        "message": (
            f"{command} recorded; resume_step={state.get('checkpoint_resume_step')!r}"
        ),
        "state": state,
    }


def resume_after_checkpoint(
    case_dir: Path,
    *,
    requested_by: str = "operator_cli",
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Resume unified driver from ``checkpoint_resume_step`` after human approval."""
    err = validate_case_dir(case_dir)
    if err:
        return {**err, "command": "resume-after-checkpoint"}

    case_dir = case_dir.resolve()
    state = load_state(case_dir)
    if state.get("ok") is False:
        return {**state, "command": "resume-after-checkpoint"}

    resume_step = state.get("checkpoint_resume_step")
    if not resume_step:
        return {
            "ok": False,
            "command": "resume-after-checkpoint",
            "case_dir": str(case_dir),
            "message": "checkpoint_resume_step is unset; run approve-a/b first",
            "state": state,
        }

    if resume_step == "approved_for_delivery":
        if state.get("automation_status") != "completed":
            state["automation_status"] = "completed"
            state["current_step"] = "approved_for_delivery"
            state["pause_reason"] = None
            state["allowed_to_auto_proceed"] = False
            state["last_transition_ts"] = utc_now_iso()
            save_state(case_dir, state)
        return {
            "ok": True,
            "command": "resume-after-checkpoint",
            "case_dir": str(case_dir),
            "checkpoint_resume_step": resume_step,
            "automation_status": "completed",
            "message": "CP-B approved; case marked approved_for_delivery",
            "state": state,
        }

    if state.get("automation_status") == "paused":
        resume_ctl = resume_automation(case_dir, requested_by=requested_by)
        if not resume_ctl.get("ok"):
            return {
                **resume_ctl,
                "command": "resume-after-checkpoint",
                "message": resume_ctl.get("message", "control plane resume failed"),
            }
        state = resume_ctl.get("state") or load_state(case_dir)

    if not dry_run and state.get("automation_status") != "running" and not force:
        return {
            "ok": False,
            "command": "resume-after-checkpoint",
            "case_dir": str(case_dir),
            "automation_status": state.get("automation_status"),
            "message": "automation_status must be running before driver resume",
            "state": state,
        }

    if dry_run:
        return {
            "ok": True,
            "command": "resume-after-checkpoint",
            "dry_run": True,
            "case_dir": str(case_dir),
            "checkpoint_resume_step": resume_step,
            "planned_start_from": resume_step,
            "message": f"would resume driver from {resume_step}",
            "state": state,
        }

    run_result = run_tabular_automation(
        case_dir,
        start_from=resume_step,
        resume=False,
        force=force,
    )

    final_state = load_state(case_dir)
    if run_result.get("ok"):
        final_state["checkpoint_resume_step"] = None
        save_state(case_dir, final_state)

    return {
        "ok": run_result.get("ok", False),
        "command": "resume-after-checkpoint",
        "case_dir": str(case_dir),
        "checkpoint_resume_step": resume_step,
        "driver_result": run_result,
        "automation_status": final_state.get("automation_status"),
        "message": run_result.get("message", ""),
        "state": final_state,
    }


def resolve_case_dir_from_args(
    *,
    case_id: str | None = None,
    case_dir: Path | None = None,
) -> Path | None:
    return resolve_case_dir(case_id=case_id, case_dir=case_dir)
