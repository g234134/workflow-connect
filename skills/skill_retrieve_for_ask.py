"""
Ask-mainline retrieve skill: metrics-aware wrapper around real RAG retrieve core.

Unlike ``example_skill_retrieve`` (mock Qdrant), callers supply ``core_fn`` that
runs ``document_chunks_smoke_retrieve_and_verify`` or stub fallback unchanged.
"""

from __future__ import annotations

from typing import Any, Callable

from observability.logging_adapter import TraceContext
from metrics.metrics_collector import MetricsCollector

from skills.skill_runner import SkillResult, run_metrics_aware_skill

SKILL_NAME = "skill_retrieve_for_ask"
CALL_SITE_DEFAULT = "langgraph_flow.retrieve_node"


def run_skill_retrieve_for_ask(
    task_id: str,
    *,
    core_fn: Callable[[], dict[str, Any]],
    collector: MetricsCollector | None = None,
    trace_ctx: TraceContext | None = None,
    agent_name: str | None = "ask_pipeline",
    call_site: str | None = CALL_SITE_DEFAULT,
    simulate_first_failure: bool = False,
) -> SkillResult:
    """
    Execute ask retrieve ``core_fn`` with retry, M-line metrics, and optional D4 span.

    ``result`` is the retrieve dict (``ok``, ``message``, ``hits``, …) from the core.
    """
    return run_metrics_aware_skill(
        skill_name=SKILL_NAME,
        task_id=task_id,
        core_fn=core_fn,
        collector=collector,
        trace_ctx=trace_ctx,
        agent_name=agent_name,
        call_site=call_site,
        step_name="retrieve",
        simulate_first_failure=simulate_first_failure,
        failure_error_type="timeout",
        record_external=True,
    )
