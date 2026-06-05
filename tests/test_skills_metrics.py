"""J-line skill metrics seed tests (M/P/O via skill_runner)."""

from __future__ import annotations

import unittest

from metrics.metrics_collector import ERROR_TYPES, MetricsCollector, reset_collector
from observability.logging_adapter import reset_active_trace, start_trace
from skills.example_skill_pg_query import run_skill_pg_query
from skills.example_skill_retrieve import run_skill_retrieve


class TestSkillsMetrics(unittest.TestCase):
    def setUp(self) -> None:
        reset_collector()
        reset_active_trace()

    def tearDown(self) -> None:
        reset_active_trace()

    def test_retrieve_success_no_retry(self) -> None:
        col = MetricsCollector()
        out = run_skill_retrieve(
            "skill-t-retrieve-ok",
            query="大唐律令",
            top_k=3,
            collector=col,
            agent_name="test_agent",
            call_site="unittest.retrieve",
        )
        self.assertTrue(out["ok"])
        self.assertIsNone(out["error_type"])
        self.assertEqual(out["retry_count"], 0)

        result = out["result"]
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("ok"))
        self.assertEqual(len(result.get("hits") or []), 3)

        self.assertEqual(out["metadata"]["skill_name"], "example_skill_retrieve")
        self.assertEqual(out["metadata"]["agent_name"], "test_agent")
        self.assertEqual(out["metadata"]["call_site"], "unittest.retrieve")

        task = col.get_task("skill-t-retrieve-ok")
        self.assertTrue(task["ok"])
        record = task["record"]
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 1)

    def test_retrieve_simulated_retry(self) -> None:
        col = MetricsCollector()
        out = run_skill_retrieve(
            "skill-t-retrieve-retry",
            query="retry-me",
            top_k=2,
            collector=col,
            simulate_first_failure=True,
        )
        self.assertTrue(out["ok"])
        self.assertIsNone(out["error_type"])
        self.assertGreaterEqual(out["retry_count"], 1)

        task = col.get_task("skill-t-retrieve-retry")
        record = task["record"]
        self.assertGreaterEqual(int(record.get("retry_count", 0)), 1)
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 2)

        errors = record.get("errors") or []
        self.assertTrue(errors)
        self.assertIn(errors[0].get("error_type"), ERROR_TYPES)

    def test_pg_query_success(self) -> None:
        col = MetricsCollector()
        out = run_skill_pg_query(
            "skill-t-pg-ok",
            table="orders",
            filters={"status": "open"},
            collector=col,
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["retry_count"], 0)
        self.assertEqual(out["metadata"]["skill_name"], "example_skill_pg_query")

        rows = (out["result"] or {}).get("rows") or []
        self.assertEqual(len(rows), 1)

        record = col.get_task("skill-t-pg-ok")["record"]
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 1)

    def test_pg_query_with_active_trace(self) -> None:
        col = MetricsCollector()
        started = start_trace("skill_test_agent", task_id="skill-t-trace", collector=col)
        self.assertTrue(started["ok"])
        ctx = started["trace_ctx"]

        out = run_skill_pg_query(
            "skill-t-trace",
            table="leads",
            collector=col,
            trace_ctx=ctx,
            call_site="unittest.with_trace",
        )
        self.assertTrue(out["ok"])

        record = col.get_task("skill-t-trace")["record"]
        step_names = [s.get("name") for s in record.get("steps") or []]
        self.assertIn("pg_query", step_names)

    def test_return_shape_keys(self) -> None:
        out = run_skill_retrieve("skill-t-shape", query="x", collector=MetricsCollector())
        for key in ("ok", "result", "error_type", "retry_count", "metadata"):
            self.assertIn(key, out)


if __name__ == "__main__":
    unittest.main()
