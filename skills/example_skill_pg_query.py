"""
Example skill: mock PG business lookup (no real database).
"""

from __future__ import annotations

from typing import Any

from observability.logging_adapter import TraceContext
from metrics.metrics_collector import MetricsCollector

from skills.skill_runner import SkillResult, run_metrics_aware_skill

SKILL_NAME = "example_skill_pg_query"


def _mock_pg_lookup(table: str, filters: dict[str, Any] | None) -> dict[str, Any]:
    """Placeholder SQL read — returns a single row dict."""
    tbl = (table or "records").strip()
    filt = dict(filters or {})
    return {
        "ok": True,
        "message": "mock pg query ok",
        "table": tbl,
        "filters": filt,
        "rows": [
            {
                "id": "row-001",
                "status": "active",
                "label": f"{tbl}:sample",
            }
        ],
        "row_count": 1,
        "source": "mock_pg",
    }


def run_skill_pg_query(
    task_id: str,
    *,
    table: str,
    filters: dict[str, Any] | None = None,
    collector: MetricsCollector | None = None,
    trace_ctx: TraceContext | None = None,
    agent_name: str | None = None,
    call_site: str | None = None,
    simulate_first_failure: bool = False,
) -> SkillResult:
    """
    Metrics-aware mock PG query.

    Default path: single external call, no retry.
    Optional ``simulate_first_failure`` uses ``timeout`` for one policy retry.
    """
    return run_metrics_aware_skill(
        skill_name=SKILL_NAME,
        task_id=task_id,
        core_fn=lambda: _mock_pg_lookup(table, filters),
        collector=collector,
        trace_ctx=trace_ctx,
        agent_name=agent_name,
        call_site=call_site,
        step_name="pg_query",
        simulate_first_failure=simulate_first_failure,
        failure_error_type="timeout",
        record_external=True,
    )
