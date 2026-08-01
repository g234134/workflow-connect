"""P8 Notify webhook mock / local probe v1 (P8-T3 mock MVP).

Simulates delivery.bundle_ready webhook reliability locally:
  mock dispatch → exponential backoff retries (max 3) → file DLQ → mock replay.

Honest boundaries:
  - Default mode is ``mock``; ``live`` / real HTTP is fail-closed.
  - external_http is always False in this module.
  - ≠ prod webhook · ≠ staging URL rollout · ≠ P7 adapter mutation.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "p8_notify_webhook_mock_v1"
DLQ_SCHEMA_ID = "p8_notify_webhook_dlq_mock_v1"
DEFAULT_EVENT_TYPE = "delivery.bundle_ready"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_DLQ_REL = Path("outbox") / "p8_notify_dlq_mock" / "events.jsonl"

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def resolve_dlq_path(
    *,
    repo_root: Optional[Path] = None,
    dlq_path_override: Optional[str] = None,
) -> Path:
    if dlq_path_override:
        path = Path(dlq_path_override)
        return path if path.is_absolute() else _repo_root(repo_root) / path
    return _repo_root(repo_root) / DEFAULT_DLQ_REL


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def mock_dispatch_bundle_ready(
    *,
    case_ref: str,
    client_summary: Optional[str] = None,
    force_fail: bool = False,
    mode: str = "mock",
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    repo_root: Optional[Path] = None,
    dlq_path_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Mock notify dispatch for delivery.bundle_ready.

    On success: records delivered_at (simulated).
    On force_fail: simulates retries then appends one DLQ row.
    """
    result: Dict[str, Any] = {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "event_type": DEFAULT_EVENT_TYPE,
        "case_ref": case_ref,
        "external_http": False,
        "delivered_at": None,
        "retry_exhausted": False,
        "attempt_count": 0,
        "dlq_path": None,
        "dlq_event_id": None,
        "message": "",
    }

    if mode != "mock":
        result["message"] = (
            f"fail-close: mode={mode!r} not allowed in P8-T3 mock MVP "
            "(live/prod HTTP NonScope)"
        )
        return result

    event_id = f"p8mock-{uuid.uuid4().hex[:12]}"
    attempts = max(1, int(max_attempts))

    if not force_fail:
        result.update(
            {
                "ok": True,
                "attempt_count": 1,
                "delivered_at": _utc_now_iso(),
                "event_id": event_id,
                "client_summary_preview": (client_summary or "")[:240],
                "message": "mock webhook delivered (simulated; external_http=false)",
            }
        )
        return result

    # Simulated retry exhaustion → DLQ
    dlq_path = resolve_dlq_path(repo_root=repo_root, dlq_path_override=dlq_path_override)
    record = {
        "schema_id": DLQ_SCHEMA_ID,
        "dlq_written_at": _utc_now_iso(),
        "event_id": event_id,
        "event_type": DEFAULT_EVENT_TYPE,
        "case_ref": case_ref,
        "attempt_count": attempts,
        "retry_exhausted": True,
        "last_error": "mock_forced_failure",
        "client_summary_preview": (client_summary or "")[:240],
        "replayed_at": None,
        "external_http": False,
        "mode": "mock",
    }
    _append_jsonl(dlq_path, record)
    result.update(
        {
            "ok": True,  # mock pipeline completed (failure path exercised)
            "attempt_count": attempts,
            "retry_exhausted": True,
            "event_id": event_id,
            "dlq_path": str(dlq_path),
            "dlq_event_id": event_id,
            "message": (
                f"mock retry exhausted after {attempts} attempts; "
                "wrote DLQ (external_http=false)"
            ),
            "dispatch_outcome": "failed_to_dlq",
        }
    )
    return result


def list_dlq(
    *,
    repo_root: Optional[Path] = None,
    dlq_path_override: Optional[str] = None,
    case_ref: Optional[str] = None,
) -> Dict[str, Any]:
    dlq_path = resolve_dlq_path(repo_root=repo_root, dlq_path_override=dlq_path_override)
    rows = _read_jsonl(dlq_path)
    if case_ref:
        rows = [r for r in rows if str(r.get("case_ref") or "") == case_ref]
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "dlq_path": str(dlq_path),
        "count": len(rows),
        "items": rows,
        "external_http": False,
        "message": f"found {len(rows)} DLQ row(s)",
    }


def replay_dlq_event(
    *,
    event_id: str,
    dry_run: bool = True,
    mode: str = "mock",
    repo_root: Optional[Path] = None,
    dlq_path_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Replay one DLQ event via mock sink only (no real HTTP)."""
    base: Dict[str, Any] = {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "external_http": False,
        "dry_run": dry_run,
        "event_id": event_id,
        "message": "",
    }
    if mode != "mock":
        base["message"] = "fail-close: replay live/prod HTTP NonScope"
        return base

    dlq_path = resolve_dlq_path(repo_root=repo_root, dlq_path_override=dlq_path_override)
    rows = _read_jsonl(dlq_path)
    match = next((r for r in rows if str(r.get("event_id") or "") == event_id), None)
    if match is None:
        base["message"] = f"DLQ event not found: {event_id}"
        return base

    if dry_run:
        base.update(
            {
                "ok": True,
                "would_replay": True,
                "case_ref": match.get("case_ref"),
                "event_type": match.get("event_type"),
                "message": "dry-run replay preview (no write)",
            }
        )
        return base

    # Rewrite jsonl with replayed_at on matching row (local mock bookkeeping only)
    updated: List[Dict[str, Any]] = []
    replayed_at = _utc_now_iso()
    for row in rows:
        if str(row.get("event_id") or "") == event_id:
            row = dict(row)
            row["replayed_at"] = replayed_at
            row["last_replay_mode"] = "mock"
        updated.append(row)
    dlq_path.parent.mkdir(parents=True, exist_ok=True)
    with dlq_path.open("w", encoding="utf-8") as fh:
        for row in updated:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    base.update(
        {
            "ok": True,
            "replayed": True,
            "replayed_at": replayed_at,
            "case_ref": match.get("case_ref"),
            "dlq_path": str(dlq_path),
            "message": "mock replay recorded (external_http=false; ≠ prod webhook)",
        }
    )
    return base
