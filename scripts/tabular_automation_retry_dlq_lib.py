"""Tabular automation retry classification and dead-letter queue (DLQ) v1.

Transient step failures are retried up to ``MAX_TRANSIENT_RETRIES`` with simple
exponential backoff. Exhausted retries or immediate-DLQ failures are appended
to ``cases/<case>/dlq/dlq.json`` (index) and ``cases/<case>/dlq/<entry_id>.json``.

DLQ records are **collect-only**: they do not trigger re-run, cleaning, or delivery.
Operators/engineering review and clear entries manually.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Literal

DLQ_SCHEMA = "tabular-automation-dlq-v1"
DLQ_DIRNAME = "dlq"
DLQ_INDEX_FILENAME = "dlq.json"

MAX_TRANSIENT_RETRIES = 3
BACKOFF_SECONDS = (1, 2, 4)

VALID_DLQ_STATUSES = frozenset({"none", "queued", "handled"})

FailureClass = Literal["transient", "permanent_stop", "immediate_dlq"]

_TRANSIENT_MARKERS = (
    "temporary",
    "temporarily unavailable",
    "resource temporarily unavailable",
    "timed out",
    "timeout",
    "connection reset",
    "connection aborted",
    "file locked",
    "device or resource busy",
    "i/o error",
    "ioerror",
    "oserror",
    "errno 11",
    "errno 35",
    "broken pipe",
    "too many open files",
)

_PERMANENT_STOP_MARKERS = (
    "rejected",
    "awaiting human",
    "checkpoint",
    "intake decision reject",
    "eligibility rejected",
    "needs_review",
)

_IMMEDIATE_DLQ_MARKERS = (
    "schema mismatch",
    "missing report artifacts",
    "clean exit",
    "bundle exit",
    "gate exit",
    "e2e validation failed",
)


def dlq_dir(case_dir: Path) -> Path:
    return case_dir / DLQ_DIRNAME


def dlq_index_path(case_dir: Path) -> Path:
    return dlq_dir(case_dir) / DLQ_INDEX_FILENAME


def backoff_seconds(retry_attempt: int) -> float:
    """Return sleep seconds before retry attempt *retry_attempt* (1-based)."""
    idx = min(max(retry_attempt - 1, 0), len(BACKOFF_SECONDS) - 1)
    return float(BACKOFF_SECONDS[idx])


def is_transient_error(error: str | None) -> bool:
    if not error:
        return False
    lower = error.lower()
    return any(marker in lower for marker in _TRANSIENT_MARKERS)


def classify_step_failure(step_result: dict[str, Any]) -> FailureClass:
    """Classify a failed step result for retry / DLQ policy."""
    if step_result.get("ok") is True:
        return "transient"  # unused when ok

    if step_result.get("hitl_blocked") or step_result.get("terminal"):
        return "permanent_stop"

    explicit = step_result.get("failure_class")
    if explicit in ("transient", "permanent_stop", "immediate_dlq"):
        return explicit

    if step_result.get("transient") is True:
        return "transient"
    if step_result.get("transient") is False:
        return "immediate_dlq"

    error = (step_result.get("error") or "").lower()
    if any(m in error for m in _PERMANENT_STOP_MARKERS):
        return "permanent_stop"
    if is_transient_error(error):
        return "transient"
    if any(m in error for m in _IMMEDIATE_DLQ_MARKERS):
        return "immediate_dlq"

    return "immediate_dlq"


def _new_entry_id(*, step_name: str) -> str:
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"{ts}_{uuid.uuid4().hex[:8]}_{step_name}"


def _load_dlq_index(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": DLQ_SCHEMA, "entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": DLQ_SCHEMA, "entries": []}
    if not isinstance(data, dict):
        return {"schema_version": DLQ_SCHEMA, "entries": []}
    data.setdefault("schema_version", DLQ_SCHEMA)
    data.setdefault("entries", [])
    return data


def enqueue_dlq(
    case_dir: Path,
    *,
    case_id: str,
    case_dir_rel: str,
    run_id: str,
    step_name: str,
    error: str | None,
    failure_class: FailureClass,
    retry_count: int,
    last_error_at: str,
    run_log_path: str | None = None,
    cleaning_profile_id: str | None = None,
) -> dict[str, Any]:
    """Append a DLQ entry. Does not re-run automation or trigger delivery."""
    entry_id = _new_entry_id(step_name=step_name)
    entry: dict[str, Any] = {
        "entry_id": entry_id,
        "status": "queued",
        "case_id": case_id,
        "case_dir": case_dir_rel,
        "run_id": run_id,
        "step_name": step_name,
        "error": error,
        "failure_class": failure_class,
        "retry_count": retry_count,
        "last_error_at": last_error_at,
        "queued_at": last_error_at,
        "run_log_path": run_log_path,
        "cleaning_profile_id": cleaning_profile_id,
        "note": "collect-only; operator must triage and mark handled — no auto re-run",
    }

    ddir = dlq_dir(case_dir)
    ddir.mkdir(parents=True, exist_ok=True)

    entry_path = ddir / f"{entry_id}.json"
    entry_path.write_text(
        json.dumps(entry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    index_path = dlq_index_path(case_dir)
    index = _load_dlq_index(index_path)
    index["case_id"] = case_id
    index["entries"].append(
        {
            "entry_id": entry_id,
            "status": "queued",
            "step_name": step_name,
            "run_id": run_id,
            "queued_at": last_error_at,
            "error": error,
            "entry_path": f"{DLQ_DIRNAME}/{entry_id}.json",
        }
    )
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "entry_id": entry_id,
        "dlq_index_path": str(index_path),
        "entry_path": str(entry_path),
        "entry": entry,
    }


def mark_dlq_handled(case_dir: Path, entry_id: str) -> dict[str, Any]:
    """Mark a DLQ entry and index row as handled (operator cleanup)."""
    entry_path = dlq_dir(case_dir) / f"{entry_id}.json"
    if not entry_path.is_file():
        return {"ok": False, "message": f"DLQ entry not found: {entry_id}"}

    try:
        entry = json.loads(entry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": f"failed to read DLQ entry: {exc}"}

    entry["status"] = "handled"
    entry_path.write_text(
        json.dumps(entry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    index_path = dlq_index_path(case_dir)
    index = _load_dlq_index(index_path)
    for row in index.get("entries", []):
        if row.get("entry_id") == entry_id:
            row["status"] = "handled"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {"ok": True, "entry_id": entry_id, "status": "handled"}
