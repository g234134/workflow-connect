"""Tabular cleaning automation control-plane state (v1).

Persists per-case ``automation_state.json`` at the case root (sibling to ``intake.json``).
Human operators use start / pause / resume / stop; a future unified driver reads the same file.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tabular_internal_notify_lib import (  # noqa: E402
    EVENT_CASE_IDLE_TO_RUNNING,
    notify_internal,
)

SCHEMA_VERSION = "tabular-automation-state-v1"
STATE_FILENAME = "automation_state.json"

VALID_STATUSES = frozenset(
    {"idle", "running", "paused", "stopped", "completed", "failed"}
)

VALID_STEPS = frozenset(
    {
        None,
        "intake",
        "eligibility",
        "checkpoint_a",
        "cleaning",
        "report",
        "bundle",
        "e2e",
        "checkpoint_b",
        "delivery",
        "approved_for_delivery",
    }
)

VALID_CHECKPOINT_STATUSES = frozenset(
    {"not_required", "pending", "approved", "rejected"}
)

PAUSE_REASON_CHECKPOINT_A = "awaiting_checkpoint_a"
PAUSE_REASON_CHECKPOINT_B = "awaiting_checkpoint_b"

VALID_DLQ_STATUSES = frozenset({"none", "queued", "handled"})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def state_path(case_dir: Path) -> Path:
    return case_dir / STATE_FILENAME


def read_intake_case_id(case_dir: Path) -> str | None:
    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return None
    try:
        data = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    case_id = data.get("case_id")
    return str(case_id) if case_id else None


def default_state(*, case_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "automation_status": "idle",
        "start_requested_by": None,
        "stop_requested_by": None,
        "pause_reason": None,
        "resume_requested_by": None,
        "last_transition_ts": None,
        "current_step": None,
        "allowed_to_auto_proceed": False,
        "requires_hitl_checkpoint": False,
        "checkpoint_a_status": "not_required",
        "checkpoint_b_status": "not_required",
        "checkpoint_a_decided_by": None,
        "checkpoint_b_decided_by": None,
        "checkpoint_a_decided_at": None,
        "checkpoint_b_decided_at": None,
        "checkpoint_resume_step": None,
        "last_error": None,
        "last_error_at": None,
        "retry_count": 0,
        "dlq_status": "none",
    }


def ensure_checkpoint_fields(state: dict[str, Any]) -> dict[str, Any]:
    """Backfill checkpoint columns for state files written before HITL resume v1."""
    defaults = default_state(case_id=str(state.get("case_id") or ""))
    for key in (
        "checkpoint_a_status",
        "checkpoint_b_status",
        "checkpoint_a_decided_by",
        "checkpoint_b_decided_by",
        "checkpoint_a_decided_at",
        "checkpoint_b_decided_at",
        "checkpoint_resume_step",
        "last_error_at",
        "retry_count",
        "dlq_status",
    ):
        state.setdefault(key, defaults[key])
    dlq = state.get("dlq_status")
    if dlq not in VALID_DLQ_STATUSES:
        state["dlq_status"] = "none"
    return state


def load_state(case_dir: Path) -> dict[str, Any]:
    path = state_path(case_dir)
    if not path.is_file():
        case_id = read_intake_case_id(case_dir) or case_dir.name
        return default_state(case_id=case_id)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": f"failed to read automation state: {exc}",
            "path": str(path),
        }

    if not isinstance(data, dict):
        return {
            "ok": False,
            "message": "automation_state.json must be a JSON object",
            "path": str(path),
        }

    status = data.get("automation_status")
    if status not in VALID_STATUSES:
        return {
            "ok": False,
            "message": f"invalid automation_status: {status!r}",
            "path": str(path),
        }

    return ensure_checkpoint_fields(data)


def save_state(case_dir: Path, state: dict[str, Any]) -> None:
    path = state_path(case_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_case_dir(case_dir: Path) -> dict[str, Any] | None:
    if not case_dir.is_dir():
        return {
            "ok": False,
            "message": f"case directory not found: {case_dir}",
            "case_dir": str(case_dir),
        }
    if not (case_dir / "intake.json").is_file():
        return {
            "ok": False,
            "message": "missing intake.json; automation state requires a valid case directory",
            "case_dir": str(case_dir),
        }
    return None


def _result(
    *,
    ok: bool,
    command: str,
    case_dir: Path,
    previous_status: str | None,
    state: dict[str, Any] | None = None,
    message: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": ok,
        "command": command,
        "case_dir": str(case_dir),
        "state_path": str(state_path(case_dir)),
        "previous_status": previous_status,
        "message": message,
    }
    if state is not None:
        payload["automation_status"] = state.get("automation_status")
        payload["state"] = state
    return payload


def get_status(case_dir: Path) -> dict[str, Any]:
    err = validate_case_dir(case_dir)
    if err:
        err["command"] = "status"
        return err

    state = load_state(case_dir)
    if state.get("ok") is False:
        state["command"] = "status"
        return state

    exists = state_path(case_dir).is_file()
    return _result(
        ok=True,
        command="status",
        case_dir=case_dir,
        previous_status=state.get("automation_status"),
        state=state,
        message="state file present" if exists else "no state file; reporting synthetic idle defaults",
    )


def start_automation(
    case_dir: Path,
    *,
    requested_by: str,
    restart: bool = False,
) -> dict[str, Any]:
    err = validate_case_dir(case_dir)
    if err:
        err["command"] = "start"
        return err

    state = load_state(case_dir)
    if state.get("ok") is False:
        state["command"] = "start"
        return state

    previous = state.get("automation_status", "idle")

    if previous in {"stopped", "completed", "failed"}:
        if not restart:
            return _result(
                ok=False,
                command="start",
                case_dir=case_dir,
                previous_status=previous,
                state=state,
                message=(
                    f"cannot start from {previous}; use start --restart for an explicit new run "
                    "(in-place resume is not allowed)"
                ),
            )
        state["last_error"] = None
        state["last_error_at"] = None
        state["retry_count"] = 0
        state["dlq_status"] = "none"
        state["current_step"] = None
        state["requires_hitl_checkpoint"] = False
        state["checkpoint_a_status"] = "not_required"
        state["checkpoint_b_status"] = "not_required"
        state["checkpoint_a_decided_by"] = None
        state["checkpoint_b_decided_by"] = None
        state["checkpoint_a_decided_at"] = None
        state["checkpoint_b_decided_at"] = None
        state["checkpoint_resume_step"] = None

    if previous == "running":
        return _result(
            ok=False,
            command="start",
            case_dir=case_dir,
            previous_status=previous,
            state=state,
            message="already running",
        )

    if previous not in {"idle", "paused", "stopped", "completed", "failed"}:
        return _result(
            ok=False,
            command="start",
            case_dir=case_dir,
            previous_status=previous,
            state=state,
            message=f"start not allowed from automation_status={previous}",
        )

    intake_case_id = read_intake_case_id(case_dir)
    if intake_case_id:
        state["case_id"] = intake_case_id

    state["automation_status"] = "running"
    state["start_requested_by"] = requested_by
    state["pause_reason"] = None
    state["allowed_to_auto_proceed"] = True
    state["last_transition_ts"] = utc_now_iso()
    if restart:
        state["stop_requested_by"] = None
        state["resume_requested_by"] = None

    save_state(case_dir, state)
    if previous == "idle":
        notify_internal(
            case_dir,
            EVENT_CASE_IDLE_TO_RUNNING,
            {
                "previous_status": previous,
                "requested_by": requested_by,
                "restart": restart,
            },
            case_id=state.get("case_id"),
        )
    return _result(
        ok=True,
        command="start",
        case_dir=case_dir,
        previous_status=previous,
        state=state,
        message="restart accepted" if restart else "automation running",
    )


def pause_automation(
    case_dir: Path,
    *,
    requested_by: str,
    reason: str | None = None,
) -> dict[str, Any]:
    err = validate_case_dir(case_dir)
    if err:
        err["command"] = "pause"
        return err

    state = load_state(case_dir)
    if state.get("ok") is False:
        state["command"] = "pause"
        return state

    previous = state.get("automation_status", "idle")
    if previous != "running":
        return _result(
            ok=False,
            command="pause",
            case_dir=case_dir,
            previous_status=previous,
            state=state,
            message="pause only allowed when automation_status=running",
        )

    state["automation_status"] = "paused"
    state["pause_reason"] = reason or f"paused by {requested_by}"
    state["allowed_to_auto_proceed"] = False
    state["last_transition_ts"] = utc_now_iso()

    save_state(case_dir, state)
    return _result(
        ok=True,
        command="pause",
        case_dir=case_dir,
        previous_status=previous,
        state=state,
        message="automation paused; current step preserved",
    )


def resume_automation(case_dir: Path, *, requested_by: str) -> dict[str, Any]:
    err = validate_case_dir(case_dir)
    if err:
        err["command"] = "resume"
        return err

    state = load_state(case_dir)
    if state.get("ok") is False:
        state["command"] = "resume"
        return state

    previous = state.get("automation_status", "idle")
    if previous != "paused":
        return _result(
            ok=False,
            command="resume",
            case_dir=case_dir,
            previous_status=previous,
            state=state,
            message="resume only allowed when automation_status=paused",
        )

    state["automation_status"] = "running"
    state["resume_requested_by"] = requested_by
    state["allowed_to_auto_proceed"] = True
    state["last_transition_ts"] = utc_now_iso()

    save_state(case_dir, state)
    return _result(
        ok=True,
        command="resume",
        case_dir=case_dir,
        previous_status=previous,
        state=state,
        message="automation resumed",
    )


def stop_automation(case_dir: Path, *, requested_by: str) -> dict[str, Any]:
    err = validate_case_dir(case_dir)
    if err:
        err["command"] = "stop"
        return err

    state = load_state(case_dir)
    if state.get("ok") is False:
        state["command"] = "stop"
        return state

    previous = state.get("automation_status", "idle")
    if previous == "stopped":
        return _result(
            ok=True,
            command="stop",
            case_dir=case_dir,
            previous_status=previous,
            state=state,
            message="already stopped",
        )

    if previous in {"completed", "failed"}:
        return _result(
            ok=False,
            command="stop",
            case_dir=case_dir,
            previous_status=previous,
            state=state,
            message=f"stop not applicable when automation_status={previous}",
        )

    state["automation_status"] = "stopped"
    state["stop_requested_by"] = requested_by
    state["allowed_to_auto_proceed"] = False
    state["last_transition_ts"] = utc_now_iso()

    save_state(case_dir, state)
    return _result(
        ok=True,
        command="stop",
        case_dir=case_dir,
        previous_status=previous,
        state=state,
        message="automation stopped; no further auto steps until explicit restart",
    )
