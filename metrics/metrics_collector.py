"""
In-memory agent metrics collector (stub).

Records per-task metrics aligned with ``metrics_schema.json`` and D1–D5 dimension
mapping. No database; safe for unit tests and local instrumentation.

Usage::

    from metrics import get_collector

    col = get_collector()
    col.start_task("task-1", "ask_pipeline")
    col.log_step("task-1", "retrieve", token_delta={"prompt_tokens": 100, "completion_tokens": 0, "total_tokens": 100})
    col.end_task("task-1", success=True)
"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Literal

ErrorType = Literal[
    "llm_error",
    "tool_error",
    "context_overflow",
    "timeout",
    "unknown",
]

ERROR_TYPES: Final[frozenset[str]] = frozenset(
    {"llm_error", "tool_error", "context_overflow", "timeout", "unknown"}
)

# D4: fields that must be present for a "complete" trace (see metrics_schema.json).
TRACE_COMPLETENESS_REQUIRED: Final[tuple[str, ...]] = (
    "task_id",
    "agent_name",
    "start_time",
    "end_time",
    "success",
    "step_count",
    "context_token_usage",
    "trace_id",
)

# Default memory hit rate until the memory layer reports real stats.
DEFAULT_MEMORY_HIT_RATE: Final[float] = 0.0

_SCHEMA_PATH = Path(__file__).resolve().parent / "metrics_schema.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_token_usage() -> dict[str, int]:
    return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def _merge_token_usage(
    base: dict[str, int],
    delta: dict[str, int] | None,
) -> dict[str, int]:
    if not delta:
        return base
    out = dict(base)
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        out[key] = int(out.get(key, 0)) + int(delta.get(key, 0))
    out["total_tokens"] = int(
        out.get("total_tokens", 0)
        or out["prompt_tokens"] + out["completion_tokens"]
    )
    return out


def compute_trace_completeness(
    record: dict[str, Any],
    *,
    required_fields: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """D4: score trace completeness by required field presence (0–1)."""
    required = required_fields or TRACE_COMPLETENESS_REQUIRED
    present: list[str] = []
    missing: list[str] = []
    for field in required:
        val = record.get(field)
        if field == "context_token_usage":
            ok = isinstance(val, dict) and val.get("total_tokens", 0) >= 0
        elif val is None:
            ok = False
        elif isinstance(val, str) and not val.strip():
            ok = False
        else:
            ok = True
        if ok:
            present.append(field)
        else:
            missing.append(field)
    score = len(present) / len(required) if required else 1.0
    return {
        "score": round(score, 4),
        "present": present,
        "missing": missing,
        "required_fields": list(required),
    }


def load_schema() -> dict[str, Any]:
    """Load ``metrics_schema.json`` from disk."""
    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


class MetricsCollector:
    """In-memory per-task metrics store."""

    def __init__(self, *, memory_hit_rate_default: float = DEFAULT_MEMORY_HIT_RATE) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}
        self._memory_hit_rate_default = memory_hit_rate_default

    def start_task(
        self,
        task_id: str,
        agent_name: str,
        *,
        trace_id: str | None = None,
        memory_hit_rate: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Begin tracking a task. Returns ``{ok, message, task_id, record}``.

        If ``task_id`` is empty, a UUID is generated.
        """
        tid = (task_id or "").strip() or uuid.uuid4().hex
        if tid in self._tasks and self._tasks[tid].get("end_time") is None:
            return {
                "ok": False,
                "message": f"task already active: {tid}",
                "task_id": tid,
            }
        record: dict[str, Any] = {
            "task_id": tid,
            "agent_name": agent_name,
            "start_time": _utc_now_iso(),
            "end_time": None,
            "success": False,
            "retry_count": 0,
            "step_count": 0,
            "context_token_usage": _empty_token_usage(),
            "error_type": None,
            "handoff_count": 0,
            "memory_hit_rate": (
                memory_hit_rate
                if memory_hit_rate is not None
                else self._memory_hit_rate_default
            ),
            "external_call_count": 0,
            "trace_id": trace_id,
            "steps": [],
            "errors": [],
            "success_rate": 0.0,
            "trace_completeness": compute_trace_completeness(
                {
                    "task_id": tid,
                    "agent_name": agent_name,
                    "start_time": _utc_now_iso(),
                    "end_time": None,
                    "success": False,
                    "step_count": 0,
                    "context_token_usage": _empty_token_usage(),
                    "trace_id": trace_id,
                }
            ),
        }
        if metadata:
            record["metadata"] = dict(metadata)
        self._tasks[tid] = record
        return {"ok": True, "message": "task started", "task_id": tid, "record": deepcopy(record)}

    def end_task(
        self,
        task_id: str,
        *,
        success: bool,
        error_type: ErrorType | None = None,
        retry_count: int | None = None,
        handoff_count: int | None = None,
        external_call_count: int | None = None,
        memory_hit_rate: float | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Finalize a task and compute derived fields (success_rate, trace_completeness)."""
        tid = (task_id or "").strip()
        record = self._tasks.get(tid)
        if not record:
            return {"ok": False, "message": f"unknown task_id: {tid}", "task_id": tid}

        record["end_time"] = _utc_now_iso()
        record["success"] = bool(success)
        record["success_rate"] = 1.0 if success else 0.0
        if retry_count is not None:
            record["retry_count"] = max(0, int(retry_count))
        if handoff_count is not None:
            record["handoff_count"] = max(0, int(handoff_count))
        if external_call_count is not None:
            record["external_call_count"] = max(0, int(external_call_count))
        if memory_hit_rate is not None:
            record["memory_hit_rate"] = max(0.0, min(1.0, float(memory_hit_rate)))
        if trace_id is not None:
            record["trace_id"] = trace_id

        if not success:
            if error_type is None and record.get("errors"):
                error_type = record["errors"][-1].get("error_type", "unknown")
            record["error_type"] = error_type if error_type in ERROR_TYPES else "unknown"
        else:
            record["error_type"] = None

        record["trace_completeness"] = compute_trace_completeness(record)
        return {
            "ok": True,
            "message": "task ended",
            "task_id": tid,
            "record": deepcopy(record),
        }

    def log_step(
        self,
        task_id: str,
        step_name: str,
        *,
        duration_ms: float | None = None,
        token_delta: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append a step event and bump ``step_count`` / token totals."""
        tid = (task_id or "").strip()
        record = self._tasks.get(tid)
        if not record:
            return {"ok": False, "message": f"unknown task_id: {tid}", "task_id": tid}

        step_index = len(record["steps"])
        step: dict[str, Any] = {
            "step_index": step_index,
            "name": step_name,
            "timestamp": _utc_now_iso(),
            "duration_ms": duration_ms,
            "token_delta": token_delta or _empty_token_usage(),
        }
        if metadata:
            step["metadata"] = dict(metadata)
        record["steps"].append(step)
        record["step_count"] = len(record["steps"])
        record["context_token_usage"] = _merge_token_usage(
            record["context_token_usage"],
            token_delta,
        )
        record["trace_completeness"] = compute_trace_completeness(record)
        return {
            "ok": True,
            "message": "step logged",
            "task_id": tid,
            "step_index": step_index,
            "record": deepcopy(record),
        }

    def log_error(
        self,
        task_id: str,
        error_type: ErrorType,
        message: str = "",
        *,
        step_index: int | None = None,
        retryable: bool = False,
        increment_retry: bool = False,
    ) -> dict[str, Any]:
        """Record an error event; optionally increment ``retry_count``."""
        tid = (task_id or "").strip()
        if error_type not in ERROR_TYPES:
            return {
                "ok": False,
                "message": f"invalid error_type: {error_type}",
                "task_id": tid,
            }
        record = self._tasks.get(tid)
        if not record:
            return {"ok": False, "message": f"unknown task_id: {tid}", "task_id": tid}

        err: dict[str, Any] = {
            "timestamp": _utc_now_iso(),
            "error_type": error_type,
            "message": message,
            "step_index": step_index,
            "retryable": retryable,
        }
        record["errors"].append(err)
        record["error_type"] = error_type
        if increment_retry:
            record["retry_count"] = int(record.get("retry_count", 0)) + 1
        return {
            "ok": True,
            "message": "error logged",
            "task_id": tid,
            "error": deepcopy(err),
            "record": deepcopy(record),
        }

    def record_handoff(self, task_id: str, *, count: int = 1) -> dict[str, Any]:
        """Increment ``handoff_count`` (D3)."""
        tid = (task_id or "").strip()
        record = self._tasks.get(tid)
        if not record:
            return {"ok": False, "message": f"unknown task_id: {tid}", "task_id": tid}
        record["handoff_count"] = int(record.get("handoff_count", 0)) + max(1, count)
        return {"ok": True, "message": "handoff recorded", "task_id": tid, "record": deepcopy(record)}

    def record_retry_count(
        self, task_id: str, *, count: int = 1
    ) -> dict[str, Any]:
        """Add ``count`` to ``retry_count`` (D4).  Like record_handoff, no flush needed."""
        tid = (task_id or "").strip()
        record = self._tasks.get(tid)
        if not record:
            return {"ok": False, "message": f"unknown task_id: {tid}", "task_id": tid}
        current = int(record.get("retry_count", 0))
        record["retry_count"] = current + max(1, int(count))
        return {"ok": True, "message": "retry_count recorded", "task_id": tid, "record": deepcopy(record)}

    def record_memory_hit_rate(
        self, task_id: str, *, value: float
    ) -> dict[str, Any]:
        """Set ``memory_hit_rate`` (D4).  Direct write, no flush needed."""
        tid = (task_id or "").strip()
        record = self._tasks.get(tid)
        if not record:
            return {"ok": False, "message": f"unknown task_id: {tid}", "task_id": tid}
        record["memory_hit_rate"] = max(0.0, min(1.0, float(value)))
        return {"ok": True, "message": "memory_hit_rate recorded", "task_id": tid, "record": deepcopy(record)}

    def record_external_call(self, task_id: str, *, count: int = 1) -> dict[str, Any]:
        """Increment ``external_call_count`` (D5 reserved)."""
        tid = (task_id or "").strip()
        record = self._tasks.get(tid)
        if not record:
            return {"ok": False, "message": f"unknown task_id: {tid}", "task_id": tid}
        record["external_call_count"] = int(record.get("external_call_count", 0)) + max(
            1, count
        )
        return {
            "ok": True,
            "message": "external call recorded",
            "task_id": tid,
            "record": deepcopy(record),
        }

    def get_task(self, task_id: str) -> dict[str, Any]:
        """Return a task record or ``{ok: false, message}``."""
        tid = (task_id or "").strip()
        record = self._tasks.get(tid)
        if not record:
            return {"ok": False, "message": f"unknown task_id: {tid}", "task_id": tid}
        return {"ok": True, "message": "ok", "task_id": tid, "record": deepcopy(record)}

    def list_tasks(self) -> dict[str, Any]:
        """Return all task records (shallow copy of keys)."""
        return {
            "ok": True,
            "message": "ok",
            "task_ids": list(self._tasks.keys()),
            "records": deepcopy(list(self._tasks.values())),
        }

    def aggregate_success_rate(self) -> dict[str, Any]:
        """D1 rollup: mean ``success_rate`` over ended tasks."""
        ended = [r for r in self._tasks.values() if r.get("end_time")]
        if not ended:
            return {"ok": True, "message": "no ended tasks", "success_rate": 0.0, "n": 0}
        rate = sum(float(r.get("success_rate", 0)) for r in ended) / len(ended)
        return {
            "ok": True,
            "message": "ok",
            "success_rate": round(rate, 4),
            "n": len(ended),
        }


_default_collector: MetricsCollector | None = None


def get_collector() -> MetricsCollector:
    """Process-wide singleton collector."""
    global _default_collector
    if _default_collector is None:
        _default_collector = MetricsCollector()
    return _default_collector


def reset_collector() -> None:
    """Reset singleton (tests)."""
    global _default_collector
    _default_collector = MetricsCollector()
