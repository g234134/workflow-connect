"""
Shared metrics-aware skill runner (J-line seed).

Wraps core logic with ``run_with_retry``, ``MetricsCollector``, and optional
observability spans. No external HTTP/DB/Qdrant — callers supply mock cores.
"""

from __future__ import annotations

from typing import Any, Callable, TypedDict, cast

from metrics.metrics_collector import ERROR_TYPES, ErrorType, MetricsCollector, get_collector
from observability.logging_adapter import (
    TraceContext,
    end_span,
    get_active_trace,
    log_event,
    log_metric,
    start_span,
)
from reliability.retry_handler import ReliabilityError, run_with_retry


class SkillResult(TypedDict, total=False):
    ok: bool
    result: Any
    error_type: str | None
    retry_count: int
    metadata: dict[str, Any]


def _ensure_task(
    col: MetricsCollector,
    task_id: str,
    *,
    agent_name: str,
    trace_ctx: TraceContext | None,
) -> None:
    """Start M-line task record when skill runs outside an active agent trace."""
    existing = col.get_task(task_id)
    if existing.get("ok"):
        return
    trace_id = trace_ctx.trace_id if trace_ctx else None
    col.start_task(
        task_id,
        agent_name,
        trace_id=trace_id,
        metadata={"source": "skill_runner"},
    )


def run_metrics_aware_skill(
    *,
    skill_name: str,
    task_id: str,
    core_fn: Callable[[], Any],
    collector: MetricsCollector | None = None,
    trace_ctx: TraceContext | None = None,
    agent_name: str | None = None,
    call_site: str | None = None,
    step_name: str | None = None,
    simulate_first_failure: bool = False,
    failure_error_type: ErrorType = "timeout",
    record_external: bool = True,
) -> SkillResult:
    """
    Execute a skill core with retry + metrics + optional D4 span.

    Returns ``{ok, result, error_type, retry_count, metadata}`` aligned with
    ``metrics/metrics_schema.json`` and J-line ``skills_contract.md``.
    """
    col = collector if collector is not None else get_collector()
    tid = (task_id or "").strip()
    if not tid:
        return {
            "ok": False,
            "result": None,
            "error_type": "unknown",
            "retry_count": 0,
            "metadata": {"skill_name": skill_name, "message": "task_id required"},
        }

    ctx = trace_ctx or get_active_trace()
    span_agent = agent_name or (ctx.agent_name if ctx else "skill_runner")
    span_step = step_name or skill_name

    _ensure_task(col, tid, agent_name=span_agent, trace_ctx=ctx)

    attempt_box = {"n": 0}
    external_calls = 0

    if ctx is not None:
        start_span(ctx, span_step, agent=span_agent, metadata={"skill_name": skill_name})
        log_event(
            f"{skill_name}_start",
            {"task_id": tid, "call_site": call_site},
            trace_ctx=ctx,
        )

    def _core() -> Any:
        nonlocal external_calls
        if record_external:
            external_calls += 1
            col.record_external_call(tid, count=1)
            if ctx is not None:
                log_metric("external_call_count", 1, trace_ctx=ctx, collector=col)

        if simulate_first_failure:
            attempt_box["n"] = attempt_box.get("n", 0) + 1
            if attempt_box["n"] == 1:
                err = failure_error_type if failure_error_type in ERROR_TYPES else "timeout"
                col.log_error(
                    tid,
                    err,
                    f"{skill_name} simulated fault (first attempt)",
                    increment_retry=False,
                )
                raise ReliabilityError(
                    f"{skill_name} simulated fault (retry policy)",
                    error_type=err,
                )
        return core_fn()

    retry_out = run_with_retry(
        _core,
        task_id=tid,
        step_name=span_step,
        collector=col,
    )

    retry_count = int(retry_out.get("retry_count") or 0)
    error_type = cast(str | None, retry_out.get("error_type"))

    if ctx is not None:
        end_span(
            ctx,
            success=bool(retry_out.get("ok")),
            metadata={
                "skill_name": skill_name,
                "retry_count": retry_count,
                "external_call_count": external_calls,
            },
        )
        log_event(
            f"{skill_name}_end",
            {"ok": retry_out.get("ok"), "retry_count": retry_count},
            trace_ctx=ctx,
        )

    metadata: dict[str, Any] = {
        "skill_name": skill_name,
        "step_name": span_step,
        "attempts": int(retry_out.get("attempts") or 0),
        "external_call_count": external_calls,
    }
    if agent_name:
        metadata["agent_name"] = agent_name
    if call_site:
        metadata["call_site"] = call_site

    if not retry_out.get("ok"):
        metadata["message"] = retry_out.get("message", "skill failed")
        return {
            "ok": False,
            "result": None,
            "error_type": error_type,
            "retry_count": retry_count,
            "metadata": metadata,
        }

    return {
        "ok": True,
        "result": retry_out.get("result"),
        "error_type": None,
        "retry_count": retry_count,
        "metadata": metadata,
    }
