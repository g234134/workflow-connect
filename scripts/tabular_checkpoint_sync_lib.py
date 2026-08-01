"""Sync CP-B checkpoint fields between automation_run_log and automation_state.

Eliminates drift after CP-B approve, delivery approve, and driver checkpoint_b completion.

Read/query helpers for checkpoint admin CLI (TAB-W4-H1) are append-only; they do not
change existing sync behaviour.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from tabular_automation_state_lib import load_state, read_intake_case_id, save_state, utc_now_iso  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

RUN_LOG_FILENAME = "automation_run_log.json"

# Checkpoint admin query constants (TAB-W4-H1)
CHECKPOINT_ID_CP_A = "A-intake-confirmation"
CHECKPOINT_ID_CP_B = "B-delivery-confirmation"
PENDING_CP_STATUSES = frozenset({"pending", "awaiting_human", "awaiting_decision"})
EXPIRED_CP_STATUS = "expired"
REQUEUEABLE_CP_STATUSES = frozenset({EXPIRED_CP_STATUS})

_CP_TYPE_TO_FIELD = {
    "cp_a": "checkpoint_a_status",
    "checkpoint_a": "checkpoint_a_status",
    "cp_b": "checkpoint_b_status",
    "checkpoint_b": "checkpoint_b_status",
}

_CP_TYPE_TO_CHECKPOINT_ID = {
    "cp_a": CHECKPOINT_ID_CP_A,
    "checkpoint_a": CHECKPOINT_ID_CP_A,
    "cp_b": CHECKPOINT_ID_CP_B,
    "checkpoint_b": CHECKPOINT_ID_CP_B,
}

_CHECKPOINT_ID_TO_CP_TYPE = {
    CHECKPOINT_ID_CP_A: "cp_a",
    CHECKPOINT_ID_CP_B: "cp_b",
}

_SKIP_CASE_PREFIXES = ("_",)


def run_log_path(case_dir: Path) -> Path:
    return case_dir / "reports" / RUN_LOG_FILENAME


def _load_run_log(case_dir: Path) -> dict[str, Any] | None:
    path = run_log_path(case_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _save_run_log(case_dir: Path, run_log: dict[str, Any]) -> Path:
    path = run_log_path(case_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def sync_checkpoint_b_run_log_step(
    case_dir: Path,
    *,
    step_status: str,
    checkpoint_b_status: str,
    updated_by: str = "tabular_checkpoint_sync",
) -> dict[str, Any]:
    """Upsert checkpoint_b step in automation_run_log with aligned status fields."""
    run_log = _load_run_log(case_dir)
    if run_log is None:
        return {"ok": False, "message": "automation_run_log.json missing or unreadable"}

    steps = run_log.get("steps")
    if not isinstance(steps, list):
        steps = []
        run_log["steps"] = steps

    ended_at = utc_now_iso()
    found = False
    for step in reversed(steps):
        if isinstance(step, dict) and step.get("step_name") == "checkpoint_b":
            step["step_status"] = step_status
            detail = dict(step.get("detail") or {})
            detail["checkpoint_b_status"] = checkpoint_b_status
            detail["synced_by"] = updated_by
            step["detail"] = detail
            step["ended_at"] = ended_at
            artifacts = dict(step.get("artifacts") or {})
            artifacts["checkpoint_b_status"] = checkpoint_b_status
            step["artifacts"] = artifacts
            found = True
            break

    if not found:
        steps.append(
            {
                "step_name": "checkpoint_b",
                "step_status": step_status,
                "started_at": ended_at,
                "ended_at": ended_at,
                "artifacts": {"checkpoint_b_status": checkpoint_b_status},
                "detail": {
                    "checkpoint_b_status": checkpoint_b_status,
                    "synced_by": updated_by,
                },
            }
        )

    path = _save_run_log(case_dir, run_log)
    return {
        "ok": True,
        "updated": True,
        "found_existing_step": found,
        "run_log_path": str(path),
        "step_status": step_status,
        "checkpoint_b_status": checkpoint_b_status,
    }


def sync_checkpoint_b_state_and_readiness(
    case_dir: Path,
    *,
    checkpoint_b_status: str,
    step_status: str | None = None,
    current_step: str | None = None,
    updated_by: str = "tabular_checkpoint_sync",
    skip_readiness_eval: bool = False,
) -> dict[str, Any]:
    """Mirror CP-B status onto automation_state, run-log, and delivery readiness."""
    state = load_state(case_dir)
    if state.get("ok") is False:
        return state

    state["checkpoint_b_status"] = checkpoint_b_status
    if current_step is not None:
        state["current_step"] = current_step
    state["last_transition_ts"] = utc_now_iso()
    save_state(case_dir, state)

    run_log_result: dict[str, Any] = {"ok": True, "updated": False}
    if step_status is not None:
        run_log_result = sync_checkpoint_b_run_log_step(
            case_dir,
            step_status=step_status,
            checkpoint_b_status=checkpoint_b_status,
            updated_by=updated_by,
        )

    readiness: dict[str, Any] = {"ok": True, "skipped": True}
    if not skip_readiness_eval:
        from tabular_delivery_approval_lib import (  # noqa: WPS433
            load_approval,
            maybe_update_delivery_readiness,
            sync_automation_state_delivery,
        )

        approval = load_approval(case_dir)
        if approval.get("delivery_approval_status") != "rejected":
            readiness = maybe_update_delivery_readiness(case_dir, updated_by=updated_by)
            approval = load_approval(case_dir)
            if isinstance(approval, dict) and approval.get("ok") is not False:
                sync_automation_state_delivery(case_dir, approval)

    return {
        "ok": True,
        "checkpoint_b_status": checkpoint_b_status,
        "step_status": step_status,
        "current_step": state.get("current_step"),
        "run_log": run_log_result,
        "readiness": readiness,
        "state": state,
    }


def repo_root() -> Path:
    return _REPO_ROOT


def normalize_cp_type(cp_type: str | None) -> str | None:
    if not cp_type:
        return None
    key = cp_type.strip().lower().replace("-", "_")
    if key in ("cp_a", "checkpoint_a"):
        return "cp_a"
    if key in ("cp_b", "checkpoint_b"):
        return "cp_b"
    return None


def checkpoint_id_for_cp_type(cp_type: str) -> str | None:
    return _CP_TYPE_TO_CHECKPOINT_ID.get(cp_type)


def cp_type_for_checkpoint_id(checkpoint_id: str) -> str | None:
    return _CHECKPOINT_ID_TO_CP_TYPE.get(checkpoint_id)


def status_field_for_cp_type(cp_type: str) -> str | None:
    return _CP_TYPE_TO_FIELD.get(cp_type)


def is_pending_checkpoint_status(status: str | None) -> bool:
    return str(status or "").strip().lower() in PENDING_CP_STATUSES


def normalize_list_status(status: str | None) -> str:
    raw = str(status or "").strip().lower()
    if raw in {"pending", "awaiting_human"}:
        return "awaiting_decision"
    return raw or "unknown"


def _should_skip_case_dir(case_dir: Path, cases_root: Path) -> bool:
    try:
        rel = case_dir.relative_to(cases_root)
    except ValueError:
        return True
    if not rel.parts:
        return True
    return rel.parts[0].startswith(_SKIP_CASE_PREFIXES)


def discover_admin_case_dirs(*, root: Path | None = None) -> list[Path]:
    """Return all non-template case directories under cases/."""
    base = root or repo_root()
    cases_root = base / "cases"
    matches: list[Path] = []
    if not cases_root.is_dir():
        return matches
    for intake_path in sorted(cases_root.rglob("intake.json")):
        parent = intake_path.parent
        if _should_skip_case_dir(parent, cases_root):
            continue
        matches.append(parent.resolve())
    return matches


def pending_entries_from_automation_state(case_dir: Path) -> list[dict[str, Any]]:
    """Read pending CP-A/CP-B rows from automation_state.json (read-only)."""
    state = load_state(case_dir)
    if state.get("ok") is False:
        return []

    case_id = str(state.get("case_id") or read_intake_case_id(case_dir) or case_dir.name)
    updated_at = state.get("last_transition_ts")
    pause_reason = state.get("pause_reason")
    entries: list[dict[str, Any]] = []

    for cp_type, field in (("cp_a", "checkpoint_a_status"), ("cp_b", "checkpoint_b_status")):
        status = str(state.get(field) or "")
        if not is_pending_checkpoint_status(status):
            continue
        entries.append(
            {
                "case_id": case_id,
                "checkpoint_id": checkpoint_id_for_cp_type(cp_type),
                "cp_type": cp_type,
                "status": normalize_list_status(status),
                "created_at": updated_at,
                "updated_at": updated_at,
                "pause_reason": pause_reason,
                "source": "automation_state",
                "case_dir": str(case_dir),
            }
        )
    return entries


def merge_pending_checkpoint_items(
    automation_items: list[dict[str, Any]],
    outbox_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge automation_state and outbox pending rows by (case_id, cp_type)."""
    merged: dict[tuple[str, str], dict[str, Any]] = {}

    for item in automation_items:
        case_id = str(item.get("case_id") or "")
        cp_type = str(item.get("cp_type") or "")
        if case_id and cp_type:
            merged[(case_id, cp_type)] = dict(item)

    for item in outbox_items:
        checkpoint_id = str(item.get("checkpoint_id") or "")
        cp_type = cp_type_for_checkpoint_id(checkpoint_id) or ""
        case_id = str(item.get("case_id") or item.get("case_ref") or "")
        if not case_id or not cp_type:
            continue
        row = merged.get((case_id, cp_type), {})
        merged[(case_id, cp_type)] = {
            "case_id": case_id,
            "checkpoint_id": checkpoint_id,
            "cp_type": cp_type,
            "status": normalize_list_status(str(item.get("status") or row.get("status"))),
            "created_at": item.get("created_at") or row.get("created_at"),
            "updated_at": item.get("updated_at") or row.get("updated_at") or row.get("created_at"),
            "pause_reason": row.get("pause_reason") or item.get("pause_reason"),
            "source": "outbox" if item else row.get("source", "automation_state"),
            "checkpoint_path": item.get("checkpoint_path"),
            "case_dir": row.get("case_dir") or item.get("case_dir"),
        }

    items = list(merged.values())
    items.sort(key=lambda row: (str(row.get("case_id", "")), str(row.get("cp_type", ""))))
    return items


def list_pending_checkpoints_admin(*, root: Path | None = None) -> dict[str, Any]:
    """Aggregate pending CP-A/CP-B checkpoints from automation_state and outbox."""
    base = root or repo_root()
    automation_items: list[dict[str, Any]] = []
    for case_dir in discover_admin_case_dirs(root=base):
        automation_items.extend(pending_entries_from_automation_state(case_dir))

    outbox_items: list[dict[str, Any]] = []
    try:
        from hitl.checkpoints_v1 import list_pending_checkpoints  # noqa: WPS433

        for row in list_pending_checkpoints(repo_root=base):
            checkpoint_id = str(row.get("checkpoint_id") or "")
            cp_type = cp_type_for_checkpoint_id(checkpoint_id)
            if not cp_type:
                continue
            outbox_items.append(
                {
                    "case_id": row.get("case_ref"),
                    "checkpoint_id": checkpoint_id,
                    "cp_type": cp_type,
                    "status": normalize_list_status(str(row.get("status") or "awaiting_human")),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("created_at"),
                    "pause_reason": None,
                    "checkpoint_path": row.get("checkpoint_path"),
                    "source": "outbox",
                }
            )
    except ImportError:
        pass

    items = merge_pending_checkpoint_items(automation_items, outbox_items)
    return {"ok": True, "action": "list", "items": items, "count": len(items)}


def resolve_case_dir_for_admin(
    *,
    case_id: str | None = None,
    case_dir: Path | None = None,
    root: Path | None = None,
) -> Path | None:
    if case_dir is not None:
        return case_dir.resolve()

    if not case_id:
        return None

    base = root or repo_root()
    cases_root = base / "cases"
    direct = cases_root / case_id
    if direct.is_dir() and (direct / "intake.json").is_file():
        return direct.resolve()

    if "/" in case_id or "\\" in case_id:
        nested = cases_root / Path(case_id.replace("\\", "/"))
        if nested.is_dir() and (nested / "intake.json").is_file():
            return nested.resolve()

    for intake_path in cases_root.rglob("intake.json"):
        parent = intake_path.parent
        if parent.name == case_id:
            return parent.resolve()
        try:
            data = json.loads(intake_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("case_id", "")) == case_id:
            return parent.resolve()
    return None


def read_automation_checkpoint_status(
    case_dir: Path,
    cp_type: str,
) -> dict[str, Any]:
    """Return automation_state checkpoint row for admin mutations."""
    field = status_field_for_cp_type(cp_type)
    if field is None:
        return {
            "ok": False,
            "error_code": "invalid_cp_type",
            "message": f"unsupported cp_type: {cp_type!r}",
        }

    state = load_state(case_dir)
    if state.get("ok") is False:
        return {
            "ok": False,
            "error_code": "state_unreadable",
            "message": state.get("message", "failed to load automation state"),
        }

    case_id = str(state.get("case_id") or read_intake_case_id(case_dir) or case_dir.name)
    return {
        "ok": True,
        "case_id": case_id,
        "cp_type": cp_type,
        "status_field": field,
        "status": str(state.get(field) or ""),
        "state": state,
        "pause_reason": state.get("pause_reason"),
        "updated_at": state.get("last_transition_ts"),
    }

