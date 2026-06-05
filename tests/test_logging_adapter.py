"""Unit tests for observability/logging_adapter (D4)."""

from __future__ import annotations

import unittest

from metrics.metrics_collector import MetricsCollector, reset_collector
from observability.logging_adapter import (
    agent_run_trace,
    end_span,
    end_trace,
    log_event,
    log_metric,
    reset_active_trace,
    start_span,
    start_trace,
)


class TestLoggingAdapter(unittest.TestCase):
    def setUp(self) -> None:
        reset_collector()
        reset_active_trace()

    def tearDown(self) -> None:
        reset_active_trace()

    def test_trace_lifecycle_maps_to_collector(self) -> None:
        col = MetricsCollector()
        started = start_trace("ask_pipeline", task_id="t-1", collector=col)
        self.assertTrue(started["ok"])
        ctx = started["trace_ctx"]

        log_event("retrieve_start", {"k": 1}, trace_ctx=ctx)
        start_span(ctx, "retrieve")
        end_span(ctx, duration_ms=12.5, token_delta={"prompt_tokens": 10, "completion_tokens": 0, "total_tokens": 10})

        log_metric("handoff_count", 1, trace_ctx=ctx, collector=col)
        ended = end_trace(ctx, success=True, collector=col)
        self.assertTrue(ended["ok"])
        record = ended["record"]
        self.assertEqual(record["task_id"], "t-1")
        self.assertEqual(record["agent_name"], "ask_pipeline")
        self.assertTrue(record["success"])
        self.assertGreaterEqual(record["step_count"], 1)
        self.assertEqual(record["handoff_count"], 1)
        self.assertGreaterEqual(record["trace_completeness"]["score"], 0.875)

    def test_log_event_without_trace_fails(self) -> None:
        out = log_event("orphan")
        self.assertFalse(out["ok"])

    def test_agent_run_trace_context_manager(self) -> None:
        col = MetricsCollector()
        with agent_run_trace("data_agent", task_id="t-2", collector=col) as ctx:
            log_event("step_a", trace_ctx=ctx, as_step=True)
        task = col.get_task("t-2")
        self.assertTrue(task["ok"])
        self.assertTrue(task["record"]["success"])
        self.assertGreaterEqual(task["record"]["step_count"], 1)

    def test_end_trace_without_active_fails(self) -> None:
        out = end_trace(success=True)
        self.assertFalse(out["ok"])

    def test_metric_retry_count_direct_writes_collector(self) -> None:
        """log_metric('retry_count', ...) writes directly to collector, not through end_trace."""
        col = MetricsCollector()
        started = start_trace("agent", task_id="ctr-retry-dw", collector=col)
        self.assertTrue(started["ok"])
        ctx = started["trace_ctx"]

        # Write retry_count multiple times without calling end_trace
        log_metric("retry_count", 1, trace_ctx=ctx, collector=col)
        log_metric("retry_count", 2, trace_ctx=ctx, collector=col)

        # Read record directly from collector — end_trace was NOT called yet
        task = col.get_task("ctr-retry-dw")
        self.assertTrue(task["ok"])
        record = task["record"]
        # 1 + max(1,2) = 1 + 2 = 3  (each call uses max(1, int(value)))
        self.assertEqual(record["retry_count"], 3)

    def test_retry_count_survives_exception_before_end_trace(self) -> None:
        """If exception prevents end_trace, retry_count data is not lost."""
        col = MetricsCollector()
        started = start_trace("agent", task_id="ctr-retry-exc", collector=col)
        self.assertTrue(started["ok"])
        ctx = started["trace_ctx"]

        log_metric("retry_count", 3, trace_ctx=ctx, collector=col)

        # Simulate exception before end_trace — never call end_trace
        # Record should already have the updated retry_count from log_metric
        task = col.get_task("ctr-retry-exc")
        self.assertTrue(task["ok"])
        self.assertEqual(task["record"]["retry_count"], 3)

        # Verify end_trace's explicit parameter still overrides
        col2 = MetricsCollector()
        started2 = start_trace("agent", task_id="ctr-override", collector=col2)
        self.assertTrue(started2["ok"])
        ctx2 = started2["trace_ctx"]

        log_metric("retry_count", 1, trace_ctx=ctx2, collector=col2)  # direct write -> 1

        # end_trace with explicit retry_count=99 should override
        ended = end_trace(ctx2, success=True, retry_count=99, collector=col2)
        self.assertTrue(ended["ok"])
        self.assertEqual(ended["record"]["retry_count"], 99)


        if __name__ == "__main__":
            unittest.main()
