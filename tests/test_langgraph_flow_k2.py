"""Smoke and routing tests for K-2 LangGraph orchestration."""

from __future__ import annotations

import unittest

from metrics.metrics_collector import reset_collector
from observability.logging_adapter import reset_active_trace

try:
    from core.langgraph_flow_k2 import (
        ASK_MERGE_INTERFACE,
        _route_after_executor,
        _route_after_planner,
        _route_after_prefetch,
        initial_k2_state,
        run_k2_flow,
    )

    _K2_IMPORTABLE = True
except ImportError:
    _K2_IMPORTABLE = False

try:
    from langgraph.graph import StateGraph  # noqa: F401

    _LANGGRAPH_INSTALLED = True
except ImportError:
    _LANGGRAPH_INSTALLED = False


@unittest.skipUnless(_K2_IMPORTABLE, "core.langgraph_flow_k2 not importable")
class TestK2RoutingIsolation(unittest.TestCase):
    """Routing helpers work without invoking the compiled graph."""

    def test_planner_handoff_routes_to_explicit_node(self) -> None:
        state = initial_k2_state()
        state["agent_output"] = {
            "status": "need_handoff",
            "next_agent": "executor_agent",
        }
        self.assertEqual(_route_after_planner(state), "handoff_planner")

    def test_executor_retry_on_timeout(self) -> None:
        state = initial_k2_state()
        state["agent_output"] = {"status": "fail"}
        state["error_type"] = "timeout"
        state["executor_attempts"] = 0
        state["max_executor_retries"] = 2
        self.assertEqual(_route_after_executor(state), "executor_retry")

    def test_prefetch_fail_routes_fail_end(self) -> None:
        state = initial_k2_state()
        state["agent_output"] = {"status": "fail"}
        self.assertEqual(_route_after_prefetch(state), "fail_end")


@unittest.skipUnless(
    _K2_IMPORTABLE and _LANGGRAPH_INSTALLED,
    "langgraph package required for K-2 e2e",
)
class TestLangGraphFlowK2E2E(unittest.TestCase):
    def setUp(self) -> None:
        reset_collector()
        reset_active_trace()

    def tearDown(self) -> None:
        reset_active_trace()

    def test_k2_happy_path_with_skills_and_eval(self) -> None:
        out = run_k2_flow(task_id="k2-test-happy", goal="unittest K-2 e2e")
        self.assertTrue(out.get("ok"), out.get("message"))

        state = out.get("state") or {}
        skills = state.get("skill_results") or {}
        retrieve = skills.get("retrieve") or {}
        self.assertTrue(retrieve.get("ok"), retrieve)

        eval_meta = out.get("eval_metadata") or {}
        self.assertIn("eval_gate", eval_meta)
        self.assertIsInstance(eval_meta.get("handoff_edges"), list)
        self.assertGreaterEqual(len(eval_meta.get("handoff_edges") or []), 2)

        record = out.get("record") or {}
        self.assertTrue(record.get("success"))
        self.assertGreaterEqual(int(record.get("handoff_count", 0)), 2)
        self.assertGreater(int((record.get("context_token_usage") or {}).get("total_tokens", 0)), 0)

        ctx = state.get("context_payload") or {}
        meta = ctx.get("metadata") or {}
        self.assertEqual(meta.get("entry_mode"), "k2_pipeline")

    def test_k2_executor_retry_path(self) -> None:
        out = run_k2_flow(task_id="k2-test-retry", goal="unittest K-2 retry")
        record = out.get("record") or {}
        self.assertGreaterEqual(int(record.get("retry_count", 0)), 1)

    def test_k2_skill_simulated_retry(self) -> None:
        out = run_k2_flow(
            task_id="k2-test-skill-retry",
            goal="skill simulated retry path",
            simulate_skill_failure=True,
        )
        state = out.get("state") or {}
        retrieve = (state.get("skill_results") or {}).get("retrieve") or {}
        self.assertTrue(retrieve.get("ok"))
        self.assertGreaterEqual(int(retrieve.get("retry_count", 0)), 1)
        self.assertTrue(out.get("ok"))


@unittest.skipUnless(_K2_IMPORTABLE, "core.langgraph_flow_k2 not importable")
class TestK2AskMergeDesign(unittest.TestCase):
    def test_ask_merge_interface_documented(self) -> None:
        self.assertEqual(ASK_MERGE_INTERFACE.get("status"), "shadow_ready")
        self.assertIn("shadow", ASK_MERGE_INTERFACE)
        self.assertIn("entry", ASK_MERGE_INTERFACE)
        self.assertIn("why_not_hardwired_yet", ASK_MERGE_INTERFACE)
        reasons = ASK_MERGE_INTERFACE.get("why_not_hardwired_yet")
        self.assertIsInstance(reasons, list)
        self.assertGreaterEqual(len(reasons), 2)


if __name__ == "__main__":
    unittest.main()
