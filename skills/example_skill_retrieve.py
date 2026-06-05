"""
Example skill: mock vector retrieve (Qdrant-shaped, no real backend).

Mirrors ask_pipeline ``retrieve`` semantics for J-line instrumentation seed.
"""

from __future__ import annotations

from typing import Any

from observability.logging_adapter import TraceContext
from metrics.metrics_collector import MetricsCollector

from skills.skill_runner import SkillResult, run_metrics_aware_skill

SKILL_NAME = "example_skill_retrieve"


def _mock_qdrant_search(query: str, top_k: int) -> dict[str, Any]:
    """Placeholder Qdrant search — deterministic mock hits."""
    q = (query or "").strip() or "(empty)"
    k = max(1, min(int(top_k), 20))
    hits = [
        {
            "id": f"vec-{i}",
            "score": round(0.95 - i * 0.05, 3),
            "payload": {"text": f"chunk for {q!r} #{i}"},
        }
        for i in range(k)
    ]
    return {
        "ok": True,
        "message": "mock retrieve ok",
        "query": q,
        "top_k": k,
        "hits": hits,
        "source": "mock_qdrant",
    }


def run_skill_retrieve(
    task_id: str,
    *,
    query: str,
    top_k: int = 5,
    collector: MetricsCollector | None = None,
    trace_ctx: TraceContext | None = None,
    agent_name: str | None = None,
    call_site: str | None = None,
    simulate_first_failure: bool = False,
) -> SkillResult:
    """
    Metrics-aware mock retrieve.

    When ``simulate_first_failure`` is True, the first attempt raises
    ``timeout`` (policy allows one retry), then succeeds on the second attempt.
    """
    return run_metrics_aware_skill(
        skill_name=SKILL_NAME,
        task_id=task_id,
        core_fn=lambda: _mock_qdrant_search(query, top_k),
        collector=collector,
        trace_ctx=trace_ctx,
        agent_name=agent_name,
        call_site=call_site,
        step_name="retrieve",
        simulate_first_failure=simulate_first_failure,
        failure_error_type="timeout",
        record_external=True,
    )
