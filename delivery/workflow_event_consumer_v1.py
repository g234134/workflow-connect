"""Read-only workflow event consumer (P8.9-T1 + T2 ack merge).

Merges notification_events.jsonl, checkpoint_events.jsonl, and downstream ack
files into a normalized per-case ledger projection. No writes to raw sinks.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

LEDGER_SCHEMA_VERSION = "workflow_event_ledger_v1"
CONSUMER_SCHEMA_VERSION = "workflow_event_consumer_v1"

NOTIFICATION_EVENTS_FILENAME = "notification_events.jsonl"
CHECKPOINT_EVENTS_FILENAME = "checkpoint_events.jsonl"

_CHECKPOINT_EVENT_MAP = {
    "checkpoint_created": "checkpoint.created",
    "checkpoint_decision": "checkpoint.human_decision",
    "human_decision": "checkpoint.human_decision",
}


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


def _parse_iso_ts(value: Optional[str]) -> str:
    if not value:
        return ""
    return str(value)


def _read_jsonl(path: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if not path.is_file():
        return [], None
    rows: List[Dict[str, Any]] = []
    try:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                return rows, f"{path.name}:{line_no}: {exc}"
            if isinstance(obj, dict):
                rows.append(obj)
    except OSError as exc:
        return [], str(exc)
    return rows, None


def _notification_ledger_row(
    event: Dict[str, Any],
    *,
    repo_root: Path,
    outbox_root: Path,
) -> Dict[str, Any]:
    event_id = str(event.get("event_id", ""))
    case_ref = _normalize_case_ref(str(event.get("case_ref", "")))
    emitted_at = _parse_iso_ts(event.get("emitted_at"))
    event_type = str(event.get("event_type", "unknown"))
    source = event.get("source") if isinstance(event.get("source"), dict) else {}
    ledger_row_id = f"notification:{event_id}"

    source_path: Optional[str] = None
    notif_dir = outbox_root / "notifications" / case_ref
    if notif_dir.is_dir() and event_id:
        for path in notif_dir.glob("*.json"):
            data = _load_json_file(path)
            if data and str(data.get("event_id")) == event_id:
                try:
                    source_path = path.relative_to(repo_root).as_posix()
                except ValueError:
                    source_path = path.as_posix()
                break

    return {
        "ledger_schema_version": LEDGER_SCHEMA_VERSION,
        "ledger_row_id": ledger_row_id,
        "source_stream": "notification",
        "native_id": event_id,
        "event_type": event_type,
        "case_ref": case_ref,
        "emitted_at": emitted_at,
        "source_step": source.get("step_id"),
        "checkpoint_id": event.get("checkpoint_id"),
        "status": event.get("checkpoint_status"),
        "tracking_status": "recorded",
        "attempts": 0,
        "last_error": None,
        "idempotency_key": event.get("idempotency_key"),
        "source_path": source_path,
        "payload_ref": {
            "schema_version": event.get("schema_version"),
            "event_id": event_id,
        },
        "downstream_ack": None,
        "ack_path": None,
    }


def _checkpoint_ledger_row(event: Dict[str, Any]) -> Dict[str, Any]:
    raw_event = str(event.get("event", "checkpoint_event"))
    event_type = _CHECKPOINT_EVENT_MAP.get(raw_event, f"checkpoint.{raw_event}")
    checkpoint_id = str(event.get("checkpoint_id", "unknown"))
    case_ref = _normalize_case_ref(str(event.get("case_ref", "")))
    emitted_at = _parse_iso_ts(
        event.get("timestamp") or event.get("created_at") or event.get("emitted_at")
    )
    ledger_row_id = f"checkpoint:{checkpoint_id}:{raw_event}:{emitted_at}"

    return {
        "ledger_schema_version": LEDGER_SCHEMA_VERSION,
        "ledger_row_id": ledger_row_id,
        "source_stream": "checkpoint",
        "native_id": ledger_row_id,
        "event_type": event_type,
        "case_ref": case_ref,
        "emitted_at": emitted_at,
        "source_step": None,
        "checkpoint_id": checkpoint_id,
        "status": event.get("status"),
        "tracking_status": "recorded",
        "attempts": 0,
        "last_error": None,
        "idempotency_key": None,
        "source_path": event.get("checkpoint_path"),
        "payload_ref": {"schema_version": event.get("schema_version"), "event": raw_event},
        "downstream_ack": None,
        "ack_path": None,
    }


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _load_ack_index(
    case_ref: str,
    outbox_root: Path,
    repo_root: Path,
) -> Dict[str, Dict[str, Any]]:
    """Map event_id -> first matching ack record (any handler)."""
    acks_dir = outbox_root / "feedback" / _normalize_case_ref(case_ref) / "acks"
    index: Dict[str, Dict[str, Any]] = {}
    if not acks_dir.is_dir():
        return index

    for path in sorted(acks_dir.glob("*.json")):
        data = _load_json_file(path)
        if not data:
            continue
        event_id = str(data.get("event_id", ""))
        if not event_id or event_id in index:
            continue
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            rel = path.as_posix()
        data = dict(data)
        data["ack_path"] = rel
        index[event_id] = data
    return index


def _apply_ack_to_row(row: Dict[str, Any], ack: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if row.get("source_stream") != "notification":
        return row

    merged = dict(row)
    if not ack:
        merged["tracking_status"] = "pending_ack"
        merged["downstream_ack"] = None
        merged["ack_path"] = None
        return merged

    status = str(ack.get("status", "")).lower()
    merged["downstream_ack"] = {
        k: ack.get(k)
        for k in (
            "schema_version",
            "feedback_kind",
            "event_id",
            "handler_id",
            "status",
            "message",
            "recorded_at",
        )
        if k in ack
    }
    merged["ack_path"] = ack.get("ack_path")

    if status == "received":
        merged["tracking_status"] = "acked"
        merged["last_error"] = None
    elif status == "failed":
        merged["tracking_status"] = "failed"
        merged["last_error"] = ack.get("message")
    else:
        merged["tracking_status"] = "pending_ack"
    return merged


def _merge_tracking(rows: List[Dict[str, Any]], ack_index: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_apply_ack_to_row(row, ack_index.get(str(row.get("native_id", "")))) for row in rows]


def _filter_rows(
    rows: List[Dict[str, Any]],
    *,
    case_ref: str,
    event_type: Optional[str],
    event_id: Optional[str],
    since: Optional[str],
) -> List[Dict[str, Any]]:
    norm_case = _normalize_case_ref(case_ref)
    filtered: List[Dict[str, Any]] = []
    for row in rows:
        if _normalize_case_ref(str(row.get("case_ref", ""))) != norm_case:
            continue
        if event_type and row.get("event_type") != event_type:
            continue
        if event_id and str(row.get("native_id")) != event_id:
            continue
        if since:
            emitted = str(row.get("emitted_at", ""))
            if emitted and emitted < since:
                continue
        filtered.append(row)
    return filtered


def _dedupe_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[str] = set()
    out: List[Dict[str, Any]] = []
    for row in rows:
        key = str(row.get("ledger_row_id", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _count_by_event_type(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        et = str(row.get("event_type", "unknown"))
        counts[et] = counts.get(et, 0) + 1
    return counts


def load_workflow_events(
    case_ref: str,
    *,
    event_type: str | None = None,
    event_id: str | None = None,
    since: str | None = None,
    repo_root: Path | None = None,
    outbox_root_override: str | None = None,
) -> dict:
    """Load merged workflow event ledger rows for a case (read-only)."""
    root = _repo_root(repo_root)
    outbox = _outbox_root(repo_root, outbox_root_override)
    norm_case = _normalize_case_ref(case_ref)

    streams_read: List[str] = []
    parse_errors: List[str] = []

    notif_path = outbox / NOTIFICATION_EVENTS_FILENAME
    notif_rows, notif_err = _read_jsonl(notif_path)
    if notif_path.is_file():
        streams_read.append(f"outbox/{NOTIFICATION_EVENTS_FILENAME}")
    if notif_err:
        parse_errors.append(notif_err)

    cp_path = outbox / CHECKPOINT_EVENTS_FILENAME
    cp_rows, cp_err = _read_jsonl(cp_path)
    if cp_path.is_file():
        streams_read.append(f"outbox/{CHECKPOINT_EVENTS_FILENAME}")
    if cp_err:
        parse_errors.append(cp_err)

    if parse_errors:
        return {
            "ok": False,
            "read_only": True,
            "schema_version": CONSUMER_SCHEMA_VERSION,
            "case_ref": norm_case,
            "message": "; ".join(parse_errors),
            "streams_read": streams_read,
            "count": 0,
            "count_by_event_type": {},
            "events": [],
            "timeline": [],
            "hints": [],
        }

    ledger_rows: List[Dict[str, Any]] = []
    for event in notif_rows:
        if _normalize_case_ref(str(event.get("case_ref", ""))) != norm_case:
            continue
        ledger_rows.append(
            _notification_ledger_row(event, repo_root=root, outbox_root=outbox)
        )

    for event in cp_rows:
        if _normalize_case_ref(str(event.get("case_ref", ""))) != norm_case:
            continue
        ledger_rows.append(_checkpoint_ledger_row(event))

    ledger_rows = _dedupe_rows(ledger_rows)
    ack_index = _load_ack_index(norm_case, outbox, root)
    ledger_rows = _merge_tracking(ledger_rows, ack_index)

    filtered = _filter_rows(
        ledger_rows,
        case_ref=norm_case,
        event_type=event_type,
        event_id=event_id,
        since=since,
    )
    timeline = sorted(filtered, key=lambda r: (str(r.get("emitted_at", "")), str(r.get("ledger_row_id", ""))))

    return {
        "ok": True,
        "read_only": True,
        "schema_version": CONSUMER_SCHEMA_VERSION,
        "case_ref": norm_case,
        "message": f"found {len(filtered)} ledger rows from {len(streams_read)} streams",
        "streams_read": streams_read,
        "count": len(filtered),
        "count_by_event_type": _count_by_event_type(filtered),
        "events": filtered,
        "timeline": timeline,
        "hints": [],
    }


def find_notification_event(
    event_id: str,
    *,
    case_ref: str | None = None,
    repo_root: Path | None = None,
    outbox_root_override: str | None = None,
) -> Optional[Dict[str, Any]]:
    """Lookup a single notification event by event_id (optionally scoped to case_ref)."""
    outbox = _outbox_root(repo_root, outbox_root_override)
    notif_rows, err = _read_jsonl(outbox / NOTIFICATION_EVENTS_FILENAME)
    if err:
        return None
    for event in notif_rows:
        if str(event.get("event_id")) != event_id:
            continue
        if case_ref and _normalize_case_ref(str(event.get("case_ref", ""))) != _normalize_case_ref(case_ref):
            continue
        return event
    return None
