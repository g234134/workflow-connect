"""
Canonical gov trace event schema (Phase 3 / Phase 5 baseline).

Structured logs and span records use ``gov-trace-v2``. Agent task aggregates
remain on ``agent-metrics-v1`` (``metrics/metrics_schema.json``); field names
align for dashboard / Langfuse / PG ingest.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Final, Literal, Mapping

GOV_TRACE_SCHEMA_VERSION: Final[str] = "gov-trace-v2"

TraceStatus = Literal["success", "failed", "running", "unknown"]

# Required keys on every emitted trace *event* (span_end / trace_end / http_request).
TRACE_EVENT_REQUIRED: Final[tuple[str, ...]] = (
    "trace_schema_version",
    "event",
    "timestamp",
    "trace_id",
    "task_id",
    "status",
)

# Full contract surface (documentation + completeness scoring).
TRACE_CONTRACT_FIELDS: Final[tuple[str, ...]] = (
    "session_id",
    "task_id",
    "trace_id",
    "span_id",
    "agent_name",
    "workflow_name",
    "tool_name",
    "latency_ms",
    "status",
    "error_type",
    "token_input",
    "token_output",
    "token_cost",
    "user_id",
    "timestamp",
)

# Default USD per 1K tokens when providers do not return cost (override via env in middleware).
_DEFAULT_INPUT_USD_PER_1K: Final[float] = 0.00015
_DEFAULT_OUTPUT_USD_PER_1K: Final[float] = 0.0006


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_trace_id() -> str:
    return uuid.uuid4().hex


def new_span_id() -> str:
    return uuid.uuid4().hex[:12]


def estimate_token_cost_usd(
    *,
    token_input: int | None = None,
    token_output: int | None = None,
    input_rate_per_1k: float | None = None,
    output_rate_per_1k: float | None = None,
) -> float | None:
    """Heuristic cost when billing metadata is absent (never blocks callers)."""
    if token_input is None and token_output is None:
        return None
    inp = max(0, int(token_input or 0))
    out = max(0, int(token_output or 0))
    if inp == 0 and out == 0:
        return 0.0
    in_rate = input_rate_per_1k if input_rate_per_1k is not None else _DEFAULT_INPUT_USD_PER_1K
    out_rate = output_rate_per_1k if output_rate_per_1k is not None else _DEFAULT_OUTPUT_USD_PER_1K
    return round((inp / 1000.0) * in_rate + (out / 1000.0) * out_rate, 8)


def normalize_status(
    *,
    success: bool | None = None,
    status: str | None = None,
    http_status: int | None = None,
) -> TraceStatus:
    if status in ("success", "failed", "running"):
        return status  # type: ignore[return-value]
    if success is True:
        return "success"
    if success is False:
        return "failed"
    if http_status is not None:
        return "success" if 200 <= http_status < 400 else "failed"
    return "unknown"


def build_trace_event(
    *,
    event: str,
    session_id: str | None = None,
    task_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    agent_name: str | None = None,
    workflow_name: str | None = None,
    tool_name: str | None = None,
    latency_ms: float | None = None,
    status: TraceStatus | str | None = None,
    success: bool | None = None,
    error_type: str | None = None,
    token_input: int | None = None,
    token_output: int | None = None,
    token_cost: float | None = None,
    user_id: str | None = None,
    timestamp: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """
    Build a single JSON-serializable trace event dict.

    ``token_cost`` is estimated from token counts when omitted.
    """
    resolved_status = normalize_status(success=success, status=status)
    cost = token_cost
    if cost is None and (token_input is not None or token_output is not None):
        cost = estimate_token_cost_usd(
            token_input=token_input,
            token_output=token_output,
        )

    body: dict[str, Any] = {
        "trace_schema_version": GOV_TRACE_SCHEMA_VERSION,
        "event": event,
        "timestamp": timestamp or utc_now_iso(),
        "session_id": session_id,
        "task_id": task_id,
        "trace_id": trace_id or new_trace_id(),
        "span_id": span_id,
        "agent_name": agent_name,
        "workflow_name": workflow_name,
        "tool_name": tool_name,
        "latency_ms": latency_ms,
        "status": resolved_status,
        "error_type": error_type,
        "token_input": token_input,
        "token_output": token_output,
        "token_cost": cost,
        "user_id": user_id,
    }
    if extra:
        body.update(extra)
    return body


def trace_completeness_score(record: Mapping[str, Any]) -> dict[str, Any]:
    """Score how many contract fields are present (0–1), for D4-style checks."""
    present: list[str] = []
    missing: list[str] = []
    for field in TRACE_CONTRACT_FIELDS:
        val = record.get(field)
        ok = val is not None and (not isinstance(val, str) or val.strip())
        if ok:
            present.append(field)
        else:
            missing.append(field)
    score = len(present) / len(TRACE_CONTRACT_FIELDS) if TRACE_CONTRACT_FIELDS else 1.0
    return {
        "score": round(score, 4),
        "present": present,
        "missing": missing,
        "required_fields": list(TRACE_CONTRACT_FIELDS),
    }


def validate_trace_event(record: Mapping[str, Any]) -> dict[str, Any]:
    """Light validation for tests; returns ``{ok, message, missing?}``."""
    missing = [k for k in TRACE_EVENT_REQUIRED if not record.get(k)]
    if missing:
        return {
            "ok": False,
            "message": f"missing required keys: {', '.join(missing)}",
            "missing": missing,
        }
    if record.get("trace_schema_version") != GOV_TRACE_SCHEMA_VERSION:
        return {
            "ok": False,
            "message": "unexpected trace_schema_version",
        }
    return {"ok": True, "message": "valid trace event"}
