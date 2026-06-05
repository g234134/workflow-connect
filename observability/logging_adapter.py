"""
D4 logging adapter: trace / span model over M-line ``metrics_collector``.

Model
-----
- **trace** — one agent task (maps to ``MetricsCollector.start_task`` / ``end_task``).
- **span** — one step or sub-agent (maps to ``log_step``; optional nested via ``start_span``).

Every agent run should use ``agent_run_trace()`` or explicit ``start_trace`` … ``end_trace``.
All public helpers return a structured ``dict`` with ``ok`` and ``message``.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Final, Iterator, Literal

from metrics.metrics_collector import (
    ERROR_TYPES,
    MetricsCollector,
    get_collector,
)
from observability.trace_schema import (
    GOV_TRACE_SCHEMA_VERSION,
    build_trace_event,
    estimate_token_cost_usd,
)

TRACE_SCHEMA_VERSION: Final[str] = "agent-metrics-v1"
LOG_LOGGER: Final[str] = "gov_core.observability"

EventKind = Literal["event", "span", "metric", "error"]
ErrorType = Literal["llm_error", "tool_error", "context_overflow", "timeout", "unknown"]

# Canonical metric names routed to collector helpers (M-line schema fields).
_COLLECTOR_METRIC_ROUTES: Final[dict[str, str]] = {
    "handoff_count": "record_handoff",
    "external_call_count": "record_external_call",
    "memory_hit_rate": "memory_hit_rate",
    "retry_count": "retry_count",
}

_thread_local = threading.local()
_logger = logging.getLogger(LOG_LOGGER)
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


@dataclass
class TraceContext:
    """In-flight trace (one task)."""

    task_id: str
    agent_name: str
    trace_id: str
    schema_version: str = TRACE_SCHEMA_VERSION
    session_id: str | None = None
    workflow_name: str | None = None
    user_id: str | None = None
    token_input: int = 0
    token_output: int = 0
    token_cost: float | None = None
    spans: list[dict[str, Any]] = field(default_factory=list)
    custom_metrics: dict[str, Any] = field(default_factory=dict)
    _active_span: dict[str, Any] | None = field(default=None, repr=False)
    _collector: MetricsCollector | None = field(default=None, repr=False)

    def collector(self) -> MetricsCollector:
        return self._collector or get_collector()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "trace_id": self.trace_id,
            "trace_schema_version": self.schema_version,
            "active_span": (
                self._active_span.get("name") if self._active_span else None
            ),
        }


def _set_active_trace(ctx: TraceContext | None) -> None:
    _thread_local.trace = ctx


def get_active_trace() -> TraceContext | None:
    return getattr(_thread_local, "trace", None)


def reset_active_trace() -> None:
    _set_active_trace(None)


def _emit_structured(
    event: str,
    payload: dict[str, Any],
    *,
    trace_ctx: TraceContext | None = None,
) -> None:
    ctx = trace_ctx
    _reserved = {
        "session_id",
        "task_id",
        "trace_id",
        "span_id",
        "agent_name",
        "workflow_name",
        "tool_name",
        "span_name",
        "latency_ms",
        "status",
        "success",
        "error_type",
        "token_input",
        "token_output",
        "token_cost",
        "user_id",
    }
    extra = {
        "agent_metrics_version": TRACE_SCHEMA_VERSION,
        "gov_trace_version": GOV_TRACE_SCHEMA_VERSION,
        **{k: v for k, v in payload.items() if k not in _reserved},
    }
    body = build_trace_event(
        event=event,
        session_id=(payload.get("session_id") or (ctx.session_id if ctx else None)),
        task_id=payload.get("task_id") or (ctx.task_id if ctx else None),
        trace_id=payload.get("trace_id") or (ctx.trace_id if ctx else None),
        span_id=payload.get("span_id"),
        agent_name=payload.get("agent_name") or (ctx.agent_name if ctx else None),
        workflow_name=payload.get("workflow_name")
        or (ctx.workflow_name if ctx else None),
        tool_name=payload.get("tool_name") or payload.get("span_name"),
        latency_ms=payload.get("latency_ms"),
        status=payload.get("status"),
        success=payload.get("success"),
        error_type=payload.get("error_type"),
        token_input=payload.get("token_input"),
        token_output=payload.get("token_output"),
        token_cost=payload.get("token_cost"),
        user_id=payload.get("user_id") or (ctx.user_id if ctx else None),
        **extra,
    )
    _logger.info("%s", json.dumps(body, default=str, ensure_ascii=False))


def _resolve_trace(trace_ctx: TraceContext | None) -> TraceContext | None:
    return trace_ctx or get_active_trace()


def start_trace(
    agent_name: str,
    *,
    task_id: str | None = None,
    trace_id: str | None = None,
    session_id: str | None = None,
    workflow_name: str | None = None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    collector: MetricsCollector | None = None,
) -> dict[str, Any]:
    """
    Begin a trace (one agent task). Registers the trace as thread-active.

    Returns ``{ok, message, trace_ctx, task_id, trace_id, record?}``.
    """
    col = collector or get_collector()
    tid = (task_id or "").strip() or uuid.uuid4().hex
    lf_trace_id = (trace_id or "").strip() or uuid.uuid4().hex

    started = col.start_task(
        tid,
        agent_name,
        trace_id=lf_trace_id,
        metadata=metadata,
    )
    if not started.get("ok"):
        return {
            "ok": False,
            "message": started.get("message", "start_task failed"),
            "task_id": tid,
            "trace_id": lf_trace_id,
        }

    meta = dict(metadata or {})
    ctx = TraceContext(
        task_id=tid,
        agent_name=agent_name,
        trace_id=lf_trace_id,
        session_id=(session_id or meta.get("session_id")),
        workflow_name=(workflow_name or meta.get("workflow_name") or agent_name),
        user_id=(user_id or meta.get("user_id")),
        _collector=col,
    )
    _set_active_trace(ctx)

    _emit_structured(
        "trace_start",
        {
            "task_id": tid,
            "trace_id": lf_trace_id,
            "session_id": ctx.session_id,
            "workflow_name": ctx.workflow_name,
            "user_id": ctx.user_id,
            "agent_name": agent_name,
            "status": "running",
            "agent_run": True,
        },
        trace_ctx=ctx,
    )

    return {
        "ok": True,
        "message": "trace started",
        "trace_ctx": ctx,
        "task_id": tid,
        "trace_id": lf_trace_id,
        "record": started.get("record"),
    }


def end_trace(
    trace_ctx: TraceContext | None = None,
    *,
    success: bool,
    error_type: ErrorType | None = None,
    retry_count: int | None = None,
    handoff_count: int | None = None,
    external_call_count: int | None = None,
    memory_hit_rate: float | None = None,
    collector: MetricsCollector | None = None,
) -> dict[str, Any]:
    """End a trace and finalize the M-line task record."""
    ctx = _resolve_trace(trace_ctx)
    if ctx is None:
        return {"ok": False, "message": "no active trace; call start_trace first"}

    col = collector or ctx.collector()

    if ctx._active_span is not None:
        end_span(ctx, success=success)

    flush_memory = memory_hit_rate
    flush_retry = retry_count

    if ctx.custom_metrics:
        col.log_step(
            ctx.task_id,
            "trace_metrics_flush",
            metadata={"custom_metrics": dict(ctx.custom_metrics)},
        )

    ended = col.end_task(
        ctx.task_id,
        success=success,
        error_type=error_type,
        retry_count=flush_retry,
        handoff_count=handoff_count,
        external_call_count=external_call_count,
        memory_hit_rate=flush_memory,
        trace_id=ctx.trace_id,
    )

    if get_active_trace() is ctx:
        reset_active_trace()

    record = ended.get("record") if ended.get("ok") else None
    completeness = (record or {}).get("trace_completeness", {})

    usage = (record or {}).get("context_token_usage") or {}
    ctx.token_input = int(usage.get("prompt_tokens") or ctx.token_input or 0)
    ctx.token_output = int(usage.get("completion_tokens") or ctx.token_output or 0)
    ctx.token_cost = estimate_token_cost_usd(
        token_input=ctx.token_input,
        token_output=ctx.token_output,
    )

    _emit_structured(
        "trace_end",
        {
            "task_id": ctx.task_id,
            "trace_id": ctx.trace_id,
            "session_id": ctx.session_id,
            "workflow_name": ctx.workflow_name,
            "user_id": ctx.user_id,
            "agent_name": ctx.agent_name,
            "success": success,
            "status": "success" if success else "failed",
            "error_type": error_type,
            "token_input": ctx.token_input,
            "token_output": ctx.token_output,
            "token_cost": ctx.token_cost,
            "agent_run": True,
            "trace_completeness_score": completeness.get("score"),
            "ok_collector": ended.get("ok"),
        },
        trace_ctx=ctx,
    )

    if not ended.get("ok"):
        return {
            "ok": False,
            "message": ended.get("message", "end_task failed"),
            "task_id": ctx.task_id,
            "trace_id": ctx.trace_id,
        }

    return {
        "ok": True,
        "message": "trace ended",
        "task_id": ctx.task_id,
        "trace_id": ctx.trace_id,
        "record": record,
        "trace_completeness": completeness,
    }


def start_span(
    trace_ctx: TraceContext | None,
    span_name: str,
    *,
    agent: str | None = None,
    tool_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Open a span (step / sub-agent). Nested spans must be closed with ``end_span``.
    """
    ctx = _resolve_trace(trace_ctx)
    if ctx is None:
        return {"ok": False, "message": "no active trace for span"}

    if ctx._active_span is not None:
        return {
            "ok": False,
            "message": f"span already active: {ctx._active_span.get('name')}",
            "task_id": ctx.task_id,
        }

    span_agent = agent or ctx.agent_name
    span_id = uuid.uuid4().hex[:12]
    ctx._active_span = {
        "span_id": span_id,
        "name": span_name,
        "agent": span_agent,
        "tool_name": tool_name or span_name,
        "started_at": time.perf_counter(),
        "metadata": dict(metadata or {}),
    }

    _emit_structured(
        "span_start",
        {
            "task_id": ctx.task_id,
            "trace_id": ctx.trace_id,
            "session_id": ctx.session_id,
            "span_id": span_id,
            "span_name": span_name,
            "tool_name": tool_name or span_name,
            "agent": span_agent,
            "agent_name": span_agent,
            "workflow_name": ctx.workflow_name,
            "status": "running",
        },
        trace_ctx=ctx,
    )

    return {
        "ok": True,
        "message": "span started",
        "task_id": ctx.task_id,
        "span_id": span_id,
        "span_name": span_name,
        "agent": span_agent,
    }


def end_span(
    trace_ctx: TraceContext | None,
    *,
    success: bool = True,
    duration_ms: float | None = None,
    token_delta: dict[str, int] | None = None,
    metadata: dict[str, Any] | None = None,
    collector: MetricsCollector | None = None,
) -> dict[str, Any]:
    """Close the active span and append a step to the M-line record."""
    ctx = _resolve_trace(trace_ctx)
    if ctx is None:
        return {"ok": False, "message": "no active trace for span end"}

    span = ctx._active_span
    if span is None:
        return {"ok": False, "message": "no active span", "task_id": ctx.task_id}

    col = collector or ctx.collector()
    step_meta = {
        "span_id": span["span_id"],
        "agent": span.get("agent"),
        "success": success,
        **(span.get("metadata") or {}),
        **(metadata or {}),
    }

    if duration_ms is None and span.get("started_at") is not None:
        duration_ms = round((time.perf_counter() - float(span["started_at"])) * 1000.0, 3)

    step_result = col.log_step(
        ctx.task_id,
        span["name"],
        duration_ms=duration_ms,
        token_delta=token_delta,
        metadata=step_meta,
    )

    if token_delta:
        ctx.token_input += int(token_delta.get("prompt_tokens") or 0)
        ctx.token_output += int(token_delta.get("completion_tokens") or 0)

    ctx.spans.append(
        {
            "span_id": span["span_id"],
            "name": span["name"],
            "agent": span.get("agent"),
            "success": success,
            "step_index": step_result.get("step_index"),
        }
    )
    ctx._active_span = None

    _emit_structured(
        "span_end",
        {
            "task_id": ctx.task_id,
            "trace_id": ctx.trace_id,
            "session_id": ctx.session_id,
            "span_id": span["span_id"],
            "span_name": span["name"],
            "tool_name": span.get("tool_name") or span["name"],
            "agent_name": span.get("agent"),
            "workflow_name": ctx.workflow_name,
            "latency_ms": duration_ms,
            "success": success,
            "status": "success" if success else "failed",
            "token_input": (token_delta or {}).get("prompt_tokens"),
            "token_output": (token_delta or {}).get("completion_tokens"),
        },
        trace_ctx=ctx,
    )

    return {
        "ok": step_result.get("ok", False),
        "message": step_result.get("message", "span ended"),
        "task_id": ctx.task_id,
        "step_index": step_result.get("step_index"),
        "record": step_result.get("record"),
    }


def log_event(
    event_name: str,
    payload: dict[str, Any] | None = None,
    *,
    trace_ctx: TraceContext | None = None,
    kind: EventKind = "event",
    as_step: bool = False,
    collector: MetricsCollector | None = None,
) -> dict[str, Any]:
    """
    Log a structured event. When ``as_step`` or ``kind=='span'``, also writes an M-line step.

    Requires an active trace for agent-run compliance (returns ``ok: false`` otherwise).
    """
    ctx = _resolve_trace(trace_ctx)
    if ctx is None:
        _emit_structured(
            "event_orphan",
            {"event_name": event_name, "warning": "no_active_trace", "task_id": None},
        )
        return {
            "ok": False,
            "message": "no active trace; every agent run must call start_trace",
            "event_name": event_name,
        }

    body = {
        "task_id": ctx.task_id,
        "trace_id": ctx.trace_id,
        "agent_name": ctx.agent_name,
        "event_name": event_name,
        "kind": kind,
        **(payload or {}),
    }
    _emit_structured("log_event", body, trace_ctx=ctx)

    write_step = as_step or kind == "span"
    if not write_step:
        return {"ok": True, "message": "event logged", "task_id": ctx.task_id}

    col = collector or ctx.collector()
    step = col.log_step(
        ctx.task_id,
        event_name,
        metadata={"kind": kind, **(payload or {})},
    )
    return {
        "ok": step.get("ok", False),
        "message": step.get("message", "event logged as step"),
        "task_id": ctx.task_id,
        "step_index": step.get("step_index"),
    }


def log_metric(
    name: str,
    value: float | int | bool,
    *,
    trace_ctx: TraceContext | None = None,
    unit: str | None = None,
    labels: dict[str, Any] | None = None,
    collector: MetricsCollector | None = None,
) -> dict[str, Any]:
    """
    Record a metric on the active trace.

    Known names are routed to M-line collector helpers; others are stored under
    ``custom_metrics`` and flushed at ``end_trace``.
    """
    ctx = _resolve_trace(trace_ctx)
    if ctx is None:
        return {
            "ok": False,
            "message": "no active trace; cannot log metric",
            "metric": name,
        }

    col = collector or ctx.collector()
    route = _COLLECTOR_METRIC_ROUTES.get(name)

    if route == "record_handoff":
        result = col.record_handoff(ctx.task_id, count=max(1, int(value)))
    elif route == "record_external_call":
        result = col.record_external_call(ctx.task_id, count=max(1, int(value)))
    elif name == "retry_count":
        result = col.record_retry_count(ctx.task_id, count=max(1, int(value)))
    elif name == "memory_hit_rate":
        result = col.record_memory_hit_rate(ctx.task_id, value=float(value))
    else:
        ctx.custom_metrics[name] = {
            "value": value,
            "unit": unit,
            "labels": labels or {},
        }
        result = {"ok": True, "message": "custom metric buffered"}

    col.log_step(
        ctx.task_id,
        f"metric:{name}",
        metadata={
            "metric": name,
            "value": value,
            "unit": unit,
            "labels": labels or {},
        },
    )

    _emit_structured(
        "log_metric",
        {
            "task_id": ctx.task_id,
            "trace_id": ctx.trace_id,
            "session_id": ctx.session_id,
            "metric": name,
            "value": value,
            "unit": unit,
        },
        trace_ctx=ctx,
    )

    return {
        "ok": result.get("ok", True),
        "message": result.get("message", "metric logged"),
        "task_id": ctx.task_id,
        "metric": name,
        "value": value,
    }


def log_error(
    error_type: ErrorType,
    message: str = "",
    *,
    trace_ctx: TraceContext | None = None,
    increment_retry: bool = False,
    collector: MetricsCollector | None = None,
) -> dict[str, Any]:
    """Record an error on the active trace (M-line ``log_error`` + structured log)."""
    if error_type not in ERROR_TYPES:
        return {"ok": False, "message": f"invalid error_type: {error_type}"}

    ctx = _resolve_trace(trace_ctx)
    if ctx is None:
        return {"ok": False, "message": "no active trace"}

    col = collector or ctx.collector()
    err = col.log_error(
        ctx.task_id,
        error_type,
        message,
        increment_retry=increment_retry,
    )
    log_event(
        "error",
        {"error_type": error_type, "message": message},
        trace_ctx=ctx,
        kind="error",
    )
    return {
        "ok": err.get("ok", False),
        "message": err.get("message", "error logged"),
        "task_id": ctx.task_id,
        "error": err.get("error"),
    }


@contextmanager
def agent_run_trace(
    agent_name: str,
    *,
    task_id: str | None = None,
    trace_id: str | None = None,
    session_id: str | None = None,
    workflow_name: str | None = None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    collector: MetricsCollector | None = None,
) -> Iterator[TraceContext]:
    """
    Context manager enforcing trace + structured logs for one agent run.

    Usage::

        with agent_run_trace("ask_pipeline") as ctx:
            log_event("retrieve_start", {"query_id": "q1"})
            ...
    """
    started = start_trace(
        agent_name,
        task_id=task_id,
        trace_id=trace_id,
        session_id=session_id,
        workflow_name=workflow_name,
        user_id=user_id,
        metadata=metadata,
        collector=collector,
    )
    if not started.get("ok"):
        raise RuntimeError(started.get("message", "start_trace failed"))

    ctx: TraceContext = started["trace_ctx"]
    success = False
    error_type: ErrorType | None = None
    try:
        log_event("agent_run_start", {"agent_name": agent_name}, trace_ctx=ctx)
        yield ctx
        success = True
    except Exception as exc:
        error_type = "unknown"
        log_error("unknown", str(exc), trace_ctx=ctx, increment_retry=False)
        raise
    finally:
        log_event(
            "agent_run_end",
            {"agent_name": agent_name, "success": success},
            trace_ctx=ctx,
        )
        end_trace(
            ctx,
            success=success,
            error_type=error_type if not success else None,
            collector=collector,
        )
