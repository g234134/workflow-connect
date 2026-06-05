"""Unit tests for observability/trace_schema (gov-trace-v2)."""

from __future__ import annotations

import unittest

from observability.trace_schema import (
    GOV_TRACE_SCHEMA_VERSION,
    build_trace_event,
    estimate_token_cost_usd,
    trace_completeness_score,
    validate_trace_event,
)


class TestTraceSchema(unittest.TestCase):
    def test_build_trace_event_required_fields(self) -> None:
        evt = build_trace_event(
            event="span_end",
            task_id="task-1",
            trace_id="trace-abc",
            span_id="span-1",
            agent_name="ask_pipeline",
            workflow_name="ask",
            tool_name="retrieve",
            latency_ms=42.5,
            status="success",
            token_input=100,
            token_output=50,
            session_id="sess-1",
            user_id="user-9",
        )
        self.assertEqual(evt["trace_schema_version"], GOV_TRACE_SCHEMA_VERSION)
        self.assertEqual(evt["task_id"], "task-1")
        self.assertEqual(evt["trace_id"], "trace-abc")
        self.assertEqual(evt["status"], "success")
        self.assertIsNotNone(evt["token_cost"])
        self.assertTrue(validate_trace_event(evt)["ok"])

    def test_estimate_token_cost(self) -> None:
        cost = estimate_token_cost_usd(token_input=1000, token_output=500)
        self.assertIsNotNone(cost)
        self.assertGreater(cost, 0)

    def test_trace_completeness_score(self) -> None:
        evt = build_trace_event(
            event="trace_end",
            task_id="t",
            trace_id="tr",
            session_id="s",
            span_id="sp",
            agent_name="ask_pipeline",
            workflow_name="ask",
            tool_name="retrieve",
            latency_ms=10.0,
            status="success",
            token_input=1,
            token_output=2,
            user_id="u1",
        )
        score = trace_completeness_score(evt)
        self.assertGreaterEqual(score["score"], 0.8)
        self.assertIn("timestamp", score["present"])

    def test_validate_rejects_missing_required(self) -> None:
        out = validate_trace_event({"event": "orphan"})
        self.assertFalse(out["ok"])


if __name__ == "__main__":
    unittest.main()
