"""P8.9 operator fields projection v1 (Wave 2 narrative / obs thin gap).

Read-only projection of Wave-4 UI draft fields from existing consumer +
handler registry + optional webhook DLQ jsonl.

Non-claims:
  - ≠ prod webhook / allowlist SLA
  - ≠ UI rendering
  - ≠ rewriting emit / ack / webhook adapter
  - ≠ Phase% uplift authorization
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from delivery.workflow_event_consumer_v1 import load_workflow_events

SCHEMA_VERSION = "p89_operator_fields_v1"
HANDLERS_CONFIG_REL = Path("routing") / "notification_handlers_v1.yaml"
DEFAULT_DLQ_PATH = "outbox/notification_dlq/events.jsonl"
ENV_DLQ_PATH = "GOV_NOTIFICATION_WEBHOOK_DLQ_PATH"

UI_FIELD_KEYS = (
    "event_id",
    "ack_status",
    "handler_id",
    "dispatch_registry_hit",
    "dlq_flag",
)


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    return Path(__file__).resolve().parents[1]


def _normalize_case_ref(case_ref: str) -> str:
    return str(case_ref or "").strip().replace("\\", "/").strip("/")


def _resolve_dlq_path(repo_root: Path, dlq_path_override: Optional[str] = None) -> Path:
    raw = (dlq_path_override or os.getenv(ENV_DLQ_PATH, "") or DEFAULT_DLQ_PATH).strip()
    path = Path(raw)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def load_handler_event_index(
    *,
    repo_root: Optional[Path] = None,
    handlers_path: Optional[Path] = None,
) -> Dict[str, List[str]]:
    """Map event_type → registered handler_id list (from YAML registry)."""
    root = _repo_root(repo_root)
    path = handlers_path or (root / HANDLERS_CONFIG_REL)
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    index: Dict[str, List[str]] = {}
    for handler in data.get("handlers") or []:
        if not isinstance(handler, dict):
            continue
        hid = str(handler.get("handler_id") or "").strip()
        if not hid:
            continue
        for et in handler.get("event_types") or []:
            key = str(et)
            index.setdefault(key, [])
            if hid not in index[key]:
                index[key].append(hid)
    return index


def _load_dlq_event_ids(
    *,
    repo_root: Path,
    case_ref: str,
    dlq_path_override: Optional[str] = None,
) -> Set[str]:
    """Return event_ids present in webhook DLQ for this case (read-only)."""
    path = _resolve_dlq_path(repo_root, dlq_path_override)
    if not path.is_file():
        return set()
    norm = _normalize_case_ref(case_ref)
    found: Set[str] = set()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        row_case = _normalize_case_ref(str(row.get("case_ref") or ""))
        if row_case and row_case != norm:
            continue
        eid = str(row.get("event_id") or "").strip()
        if eid:
            found.add(eid)
    return found


def _ack_status_from_row(row: Dict[str, Any]) -> str:
    if row.get("source_stream") != "notification":
        return "recorded"
    tracking = str(row.get("tracking_status") or "").strip().lower()
    if tracking in ("acked", "failed", "pending_ack"):
        return tracking
    return "pending_ack"


def project_operator_fields(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    dlq_path_override: Optional[str] = None,
    handlers_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Project UI draft fields for a case from existing P8.9 sinks (read-only)."""
    root = _repo_root(repo_root)
    norm = _normalize_case_ref(case_ref)
    if not norm:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "read_only": True,
            "case_ref": "",
            "message": "case_ref is required",
            "count": 0,
            "fields": list(UI_FIELD_KEYS),
            "rows": [],
            "t4_alignment": {
                "ticket": "WD-P7-T2",
                "alias": "P8.9-T4",
                "status": "landed",
                "adapter": "delivery/notification_webhook_adapter_v1.py",
            },
            "non_claims": [
                "≠ prod webhook / allowlist SLA",
                "≠ UI",
                "≠ Phase% authorize",
                "≠ rewrite webhook adapter",
            ],
        }

    consumer = load_workflow_events(
        norm,
        repo_root=root,
        outbox_root_override=outbox_root_override,
    )
    if not consumer.get("ok", False):
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "read_only": True,
            "case_ref": norm,
            "message": consumer.get("message") or "workflow event consumer failed",
            "count": 0,
            "fields": list(UI_FIELD_KEYS),
            "rows": [],
            "streams_read": consumer.get("streams_read") or [],
            "t4_alignment": {
                "ticket": "WD-P7-T2",
                "alias": "P8.9-T4",
                "status": "landed",
                "adapter": "delivery/notification_webhook_adapter_v1.py",
            },
            "non_claims": [
                "≠ prod webhook / allowlist SLA",
                "≠ UI",
                "≠ Phase% authorize",
                "≠ rewrite webhook adapter",
            ],
        }

    handler_index = load_handler_event_index(repo_root=root, handlers_path=handlers_path)
    dlq_ids = _load_dlq_event_ids(
        repo_root=root, case_ref=norm, dlq_path_override=dlq_path_override
    )

    rows_out: List[Dict[str, Any]] = []
    for row in consumer.get("timeline") or []:
        if not isinstance(row, dict):
            continue
        if row.get("source_stream") != "notification":
            continue
        event_id = str(row.get("native_id") or row.get("event_id") or "").strip()
        event_type = str(row.get("event_type") or "")
        ack = row.get("downstream_ack") if isinstance(row.get("downstream_ack"), dict) else {}
        handler_id = str(ack.get("handler_id") or "") or None
        registered = handler_index.get(event_type) or []
        rows_out.append(
            {
                "event_id": event_id or None,
                "event_type": event_type or None,
                "ack_status": _ack_status_from_row(row),
                "handler_id": handler_id,
                "dispatch_registry_hit": bool(registered),
                "registered_handler_ids": list(registered),
                "dlq_flag": bool(event_id and event_id in dlq_ids),
            }
        )

    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "read_only": True,
        "case_ref": norm,
        "message": "operator fields projected (read-only)",
        "count": len(rows_out),
        "fields": list(UI_FIELD_KEYS),
        "rows": rows_out,
        "streams_read": consumer.get("streams_read") or [],
        "registry_handlers_path": HANDLERS_CONFIG_REL.as_posix(),
        "t4_alignment": {
            "ticket": "WD-P7-T2",
            "alias": "P8.9-T4",
            "status": "landed",
            "adapter": "delivery/notification_webhook_adapter_v1.py",
            "handler_id": "webhook_dispatch_v1",
        },
        "non_claims": [
            "≠ prod webhook / allowlist SLA",
            "≠ UI",
            "≠ Phase% authorize",
            "≠ rewrite webhook adapter",
        ],
    }
