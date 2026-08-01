"""Tabular internal notification hook (v1 placeholder).

Appends noteworthy automation transitions to ``internal_notify_log.json`` at the
case root and emits a single INFO log line. Does **not** dispatch to external
chat, email, or alert systems — see ``docs/tabular-cleaning-automation-manifest-v1.md``
§1.11 for the event catalog and future extension notes.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

INTERNAL_NOTIFY_SCHEMA = "tabular-internal-notify-v1"
INTERNAL_NOTIFY_LOG_FILENAME = "internal_notify_log.json"

EVENT_CASE_IDLE_TO_RUNNING = "case.idle_to_running"
EVENT_CHECKPOINT_PENDING = "checkpoint.pending"
EVENT_CHECKPOINT_REJECTED = "checkpoint.rejected"
EVENT_CASE_COMPLETED_DELIVERY_READY = "case.completed_delivery_ready"
EVENT_CASE_DLQ_ENQUEUED = "case.dlq_enqueued"

INTERNAL_NOTIFY_EVENTS = frozenset(
    {
        EVENT_CASE_IDLE_TO_RUNNING,
        EVENT_CHECKPOINT_PENDING,
        EVENT_CHECKPOINT_REJECTED,
        EVENT_CASE_COMPLETED_DELIVERY_READY,
        EVENT_CASE_DLQ_ENQUEUED,
    }
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_intake_case_id(case_dir: Path) -> str | None:
    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return None
    try:
        data = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    case_id = data.get("case_id")
    return str(case_id) if case_id else None


def notify_log_path(case_dir: Path) -> Path:
    return case_dir / INTERNAL_NOTIFY_LOG_FILENAME


def _load_notify_log(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": INTERNAL_NOTIFY_SCHEMA, "entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": INTERNAL_NOTIFY_SCHEMA, "entries": []}
    if not isinstance(data, dict):
        return {"schema_version": INTERNAL_NOTIFY_SCHEMA, "entries": []}
    data.setdefault("schema_version", INTERNAL_NOTIFY_SCHEMA)
    data.setdefault("entries", [])
    return data


def notify_internal(
    case_dir: Path,
    event: str,
    payload: dict[str, Any] | None = None,
    *,
    case_id: str | None = None,
) -> dict[str, Any]:
    """Record an internal-only notify event. Returns structured ``dict`` (never raises)."""
    if event not in INTERNAL_NOTIFY_EVENTS:
        return {
            "ok": False,
            "event": event,
            "message": f"unknown internal notify event: {event!r}",
        }

    resolved_case_id = case_id or _read_intake_case_id(case_dir) or case_dir.name
    entry: dict[str, Any] = {
        "event": event,
        "ts": _utc_now_iso(),
        "case_id": resolved_case_id,
        "payload": payload or {},
    }

    path = notify_log_path(case_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        log_doc = _load_notify_log(path)
        log_doc["case_id"] = resolved_case_id
        log_doc["last_event_at"] = entry["ts"]
        log_doc["entries"].append(entry)
        path.write_text(
            json.dumps(log_doc, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        return {
            "ok": False,
            "event": event,
            "case_id": resolved_case_id,
            "message": f"failed to append internal notify log: {exc}",
        }

    logger.info(
        "tabular_internal_notify event=%s case_id=%s path=%s",
        event,
        resolved_case_id,
        path,
    )

    return {
        "ok": True,
        "event": event,
        "case_id": resolved_case_id,
        "logged": True,
        "path": str(path),
        "entry": entry,
        "message": "internal notify recorded (no external dispatch)",
    }


def maybe_notify_completed_delivery_ready(
    case_dir: Path,
    *,
    previous_delivery_ready: bool,
    delivery_ready: bool,
    automation_status: str,
    previous_automation_status: str | None = None,
    case_id: str | None = None,
    source: str = "unknown",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Emit ``case.completed_delivery_ready`` when both gates newly satisfied."""
    newly_completed = (
        previous_automation_status is not None
        and previous_automation_status != "completed"
        and automation_status == "completed"
    )
    newly_ready = delivery_ready and not previous_delivery_ready
    if automation_status != "completed" or not delivery_ready:
        return None
    if not newly_completed and not newly_ready:
        return None

    payload: dict[str, Any] = {
        "automation_status": automation_status,
        "delivery_ready": True,
        "source": source,
        "previous_automation_status": previous_automation_status,
        "previous_delivery_ready": previous_delivery_ready,
    }
    if extra:
        payload.update(extra)

    return notify_internal(
        case_dir,
        EVENT_CASE_COMPLETED_DELIVERY_READY,
        payload,
        case_id=case_id,
    )
