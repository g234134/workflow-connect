"""Tabular Tool Outbox writer v1 (W3-TL-T3).

Writes per-run JSON records under outbox/<case_ref>/<run_id>.json and optionally
appends to outbox/events.jsonl. Separate from Phase 8.8 orchestration_bridge_outbox.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

OUTBOX_SCHEMA_VERSION = "tabular_outbox_v1"
DEFAULT_OUTBOX_DIRNAME = "outbox"
EVENTS_FILENAME = "events.jsonl"

_REQUIRED_RECORD_KEYS = frozenset(
    {
        "schema_version",
        "case_ref",
        "run_id",
        "tool_id",
        "started_at",
        "finished_at",
        "ok",
        "exit_code",
        "message",
        "artifacts",
    }
)


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[1]


def format_run_timestamp(when: Optional[datetime] = None) -> str:
    """Compact UTC timestamp for run_id prefix (no colons)."""
    dt = when or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H-%M-%SZ")


def tool_slug(tool_id: str) -> str:
    """Short slug from catalog tool_id (last segment)."""
    return tool_id.rsplit(".", 1)[-1]


def generate_run_id(tool_id: str, started_at: Optional[str] = None) -> str:
    """Build run_id: ``{timestamp}_{tool_slug}``."""
    if started_at:
        # Accept full ISO8601 and normalize to compact prefix.
        try:
            parsed = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            ts = format_run_timestamp(parsed.astimezone(timezone.utc))
        except ValueError:
            ts = format_run_timestamp()
    else:
        ts = format_run_timestamp()
    return f"{ts}_{tool_slug(tool_id)}"


def outbox_root(repo_root: Optional[Path] = None, outbox_root_override: Optional[str] = None) -> Path:
    root = _repo_root(repo_root)
    if outbox_root_override:
        override = Path(outbox_root_override)
        if not override.is_absolute():
            override = root / override
        return override.resolve()
    return root / DEFAULT_OUTBOX_DIRNAME


def build_outbox_rel_path(case_ref: str, run_id: str) -> str:
    """Repo-relative path to per-run outbox JSON."""
    safe_case = case_ref.replace("\\", "/").strip("/")
    return f"{DEFAULT_OUTBOX_DIRNAME}/{safe_case}/{run_id}.json"


def validate_record(record: Dict[str, Any]) -> None:
    missing = _REQUIRED_RECORD_KEYS - set(record)
    if missing:
        raise ValueError(f"outbox record missing required keys: {sorted(missing)}")
    if not isinstance(record["artifacts"], list):
        raise ValueError("artifacts must be a list")


def write_run_record(
    record: Dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    """Write per-run outbox JSON; returns absolute path written."""
    validate_record(record)
    root = outbox_root(repo_root, outbox_root_override)
    case_ref = str(record["case_ref"])
    run_id = str(record["run_id"])
    safe_case = case_ref.replace("\\", "/").strip("/")
    dest_dir = root / safe_case
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{run_id}.json"
    payload = dict(record)
    payload["outbox_path"] = build_outbox_rel_path(case_ref, run_id)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return dest


def append_event_line(
    event: Dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    """Append one JSON line to outbox/events.jsonl."""
    root = outbox_root(repo_root, outbox_root_override)
    root.mkdir(parents=True, exist_ok=True)
    events_path = root / EVENTS_FILENAME
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return events_path


def build_event_line(record: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal append-only event from a full run record."""
    return {
        "case_ref": record.get("case_ref"),
        "run_id": record.get("run_id"),
        "tool_id": record.get("tool_id"),
        "ok": record.get("ok"),
        "exit_code": record.get("exit_code"),
        "started_at": record.get("started_at"),
        "finished_at": record.get("finished_at"),
        "dry_run": record.get("dry_run", False),
    }
