"""Feedback ingest v1 — downstream ack persistence (P8.9-T2).

Records handler acknowledgements for workflow notification events under
outbox/feedback/<case_ref>/acks/. Read-only with respect to gateway emit paths.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from delivery.workflow_event_consumer_v1 import find_notification_event, load_workflow_events

DOWNSTREAM_ACK_SCHEMA_VERSION = "downstream_ack_v1"
FEEDBACK_KIND = "downstream_ack"
INGEST_SCHEMA_VERSION = "feedback_ingest_v1"

VALID_ACK_STATUSES = frozenset({"received", "failed"})


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    return Path(__file__).resolve().parents[1]


def _outbox_root(
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    if outbox_root_override:
        return Path(outbox_root_override).resolve()
    return _repo_root(repo_root) / "outbox"


def _normalize_case_ref(case_ref: str) -> str:
    return case_ref.replace("\\", "/").strip("/")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ack_path(
    outbox_root: Path,
    case_ref: str,
    event_id: str,
    handler_id: str,
) -> Path:
    safe_handler = handler_id.replace("/", "_").replace("\\", "_")
    filename = f"{event_id}_{safe_handler}.json"
    return outbox_root / "feedback" / _normalize_case_ref(case_ref) / "acks" / filename


def _build_ack_record(
    *,
    event_id: str,
    handler_id: str,
    case_ref: str,
    status: str,
    message: Optional[str],
    source_event_type: str,
    ledger_row_id: str,
    recorded_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": DOWNSTREAM_ACK_SCHEMA_VERSION,
        "feedback_kind": FEEDBACK_KIND,
        "event_id": event_id,
        "handler_id": handler_id,
        "case_ref": _normalize_case_ref(case_ref),
        "status": status,
        "message": message,
        "recorded_at": recorded_at or _utc_now_iso(),
        "source_event_type": source_event_type,
        "ledger_row_id": ledger_row_id,
    }


def _records_equal(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    keys = (
        "schema_version",
        "feedback_kind",
        "event_id",
        "handler_id",
        "case_ref",
        "status",
        "message",
        "source_event_type",
        "ledger_row_id",
    )
    return all(a.get(k) == b.get(k) for k in keys)


def record_downstream_ack(
    event_id: str,
    handler_id: str,
    status: str,
    message: str | None = None,
    *,
    case_ref: str | None = None,
    repo_root: Path | None = None,
    outbox_root_override: str | None = None,
) -> dict:
    """Persist downstream ack for a workflow notification event (idempotent)."""
    if status not in VALID_ACK_STATUSES:
        return {
            "ok": False,
            "schema_version": INGEST_SCHEMA_VERSION,
            "message": f"invalid ack status: {status}",
            "event_id": event_id,
            "handler_id": handler_id,
            "ack_path": None,
            "idempotent_skip": False,
        }

    event = find_notification_event(
        event_id,
        case_ref=case_ref,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    if event is None:
        return {
            "ok": False,
            "schema_version": INGEST_SCHEMA_VERSION,
            "message": f"unknown event_id: {event_id}",
            "event_id": event_id,
            "handler_id": handler_id,
            "ack_path": None,
            "idempotent_skip": False,
        }

    resolved_case = _normalize_case_ref(str(case_ref or event.get("case_ref", "")))
    if not resolved_case:
        return {
            "ok": False,
            "schema_version": INGEST_SCHEMA_VERSION,
            "message": "case_ref could not be resolved",
            "event_id": event_id,
            "handler_id": handler_id,
            "ack_path": None,
            "idempotent_skip": False,
        }

    root = _repo_root(repo_root)
    outbox = _outbox_root(repo_root, outbox_root_override)
    ledger_row_id = f"notification:{event_id}"
    record = _build_ack_record(
        event_id=event_id,
        handler_id=handler_id,
        case_ref=resolved_case,
        status=status,
        message=message,
        source_event_type=str(event.get("event_type", "")),
        ledger_row_id=ledger_row_id,
    )

    path = _ack_path(outbox, resolved_case, event_id, handler_id)
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(existing, dict) and _records_equal(existing, record):
                try:
                    rel = path.relative_to(root).as_posix()
                except ValueError:
                    rel = path.as_posix()
                return {
                    "ok": True,
                    "schema_version": INGEST_SCHEMA_VERSION,
                    "message": "ack already recorded (idempotent skip)",
                    "event_id": event_id,
                    "handler_id": handler_id,
                    "ack_path": rel,
                    "idempotent_skip": True,
                    "ack": existing,
                }
        except (OSError, json.JSONDecodeError):
            pass

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "schema_version": INGEST_SCHEMA_VERSION,
            "message": f"ack write failed: {exc}",
            "event_id": event_id,
            "handler_id": handler_id,
            "ack_path": None,
            "idempotent_skip": False,
        }

    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()

    return {
        "ok": True,
        "schema_version": INGEST_SCHEMA_VERSION,
        "message": "downstream ack recorded",
        "event_id": event_id,
        "handler_id": handler_id,
        "ack_path": rel,
        "idempotent_skip": False,
        "ack": record,
    }


def ingest_pending_events(
    case_ref: str,
    *,
    repo_root: Path | None = None,
    outbox_root_override: str | None = None,
) -> dict:
    """List notification events for case_ref that have no downstream ack yet."""
    norm_case = _normalize_case_ref(case_ref)
    consumer = load_workflow_events(
        norm_case,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    if not consumer.get("ok"):
        return {
            "ok": False,
            "schema_version": INGEST_SCHEMA_VERSION,
            "case_ref": norm_case,
            "message": consumer.get("message", "consumer failed"),
            "pending": [],
            "pending_count": 0,
        }

    pending: List[Dict[str, Any]] = []
    for row in consumer.get("events") or []:
        if row.get("source_stream") != "notification":
            continue
        if row.get("tracking_status") != "pending_ack":
            continue
        pending.append(
            {
                "event_id": row.get("native_id"),
                "event_type": row.get("event_type"),
                "emitted_at": row.get("emitted_at"),
                "case_ref": row.get("case_ref"),
                "ledger_row_id": row.get("ledger_row_id"),
                "tracking_status": row.get("tracking_status"),
            }
        )

    return {
        "ok": True,
        "schema_version": INGEST_SCHEMA_VERSION,
        "case_ref": norm_case,
        "message": f"found {len(pending)} pending notification event(s)",
        "pending": pending,
        "pending_count": len(pending),
    }
