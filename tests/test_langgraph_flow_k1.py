"""Smoke tests for K-1 LangGraph e2e (M/N/O/P/Q integration)."""

from __future__ import annotations

import unittest

from metrics.metrics_collector import reset_collector
from observability.logging_adapter import reset_active_trace

try:
    from core.langgraph_flow_k1 import run_k1_flow

    _LANGGRAPH_AVAILABLE = True
except ImportError:
    _LANGGRAPH_AVAILABLE = False

try:
    from langgraph.graph import StateGraph  # noqa: F401

    _LANGGRAPH_INSTALLED = True
except ImportError:
    _LANGGRAPH_INSTALLED = False


@unittest.skipUnless(
    _LANGGRAPH_AVAILABLE and _LANGGRAPH_INSTALLED,
    "langgraph package required for K-1 e2e",
)
class TestLangGraphFlowK1(unittest.TestCase):
    def setUp(self) -> None:
        reset_collector()
        reset_active_trace()

    def tearDown(self) -> None:
        reset_active_trace()

    def test_k1_invoke_meets_dod_metrics(self) -> None:
        out = run_k1_flow(task_id="k1-test-001", goal="unittest K-1 e2e")
        self.assertTrue(out.get("ok"), out.get("message"))

        state = out.get("state") or {}
        final_result = state.get("final_result") or {}
        self.assertTrue(final_result.get("ok"))
        self.assertIn("result", final_result)

        record = out.get("record") or {}
        self.assertTrue(record.get("success"))
        self.assertGreaterEqual(int(record.get("retry_count", 0)), 1)
        self.assertGreaterEqual(int(record.get("handoff_count", 0)), 2)

        token_usage = record.get("context_token_usage") or {}
        self.assertGreater(int(token_usage.get("total_tokens", 0)), 0)

        completeness = record.get("trace_completeness") or out.get("trace_completeness") or {}
        self.assertGreater(float(completeness.get("score", 0)), 0.9)

        ctx_payload = state.get("context_payload") or {}
        self.assertTrue(ctx_payload.get("ok"))
        result_layers = ctx_payload.get("result") or {}
        self.assertIn("root_context", result_layers)
        self.assertIn("working_context", result_layers)


if __name__ == "__main__":
    unittest.main()
