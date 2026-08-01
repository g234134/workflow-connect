"""Sprint 1 · C-1: context-driven subagent routing v0.1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.context_entry import build_rooted_context
from subagents.context_routing import (
    DEFAULT_AGENT_ID,
    MONITORING_AGENT_ID,
    attach_subagent_route_to_context,
    build_route_decision,
    route_task_by_context,
)


class TestContextSubagentRouting(unittest.TestCase):
    def test_monitoring_context_routes_to_monitoring_subagent(self) -> None:
        root: dict = {}
        working = {
            "task_input": {
                "task_type": "monitoring",
                "goal": "Check GET /monitoring/overview KPI drift",
                "tags": ["monitoring"],
            }
        }
        ltm: dict = {}
        self.assertEqual(
            route_task_by_context(root, working, ltm),
            MONITORING_AGENT_ID,
        )
        decision = build_route_decision(root, working, ltm)
        self.assertEqual(decision["rule_id"], "ROUTE-MON-1")
        self.assertTrue(decision.get("signal_only"))

    def test_general_context_routes_to_default_subagent(self) -> None:
        root = {"version": "v0.1"}
        working = {
            "task_input": {"goal": "你好，今天天气如何？", "query": "你好"},
            "goal": "你好",
        }
        ltm = {"semantic": {"hits": []}, "structured": {"rows": []}}
        self.assertEqual(
            route_task_by_context(root, working, ltm),
            DEFAULT_AGENT_ID,
        )

    def test_kpi_only_keyword_routes_to_monitoring_subagent(self) -> None:
        """TEST-SUB-001 follow-up: bare KPI keyword (no /monitoring/ path) → ROUTE-MON-1."""
        working = {
            "task_input": {
                "goal": "Review quarterly KPI trends for ops board",
            }
        }
        decision = build_route_decision({}, working, {})
        self.assertEqual(decision["target_agent_id"], MONITORING_AGENT_ID)
        self.assertEqual(decision["rule_id"], "ROUTE-MON-1")
        self.assertTrue(decision.get("signal_only"))

    def test_attach_writes_metadata_on_context_entry_output(self) -> None:
        built = build_rooted_context(
            {
                "query": "wave1 monitoring acceptance",
                "task_type": "monitoring",
                "tags": ["monitoring"],
            },
            mode="ask_pipeline",
        )
        self.assertTrue(built.get("ok"), built.get("message"))
        enriched = attach_subagent_route_to_context(built)
        route = (enriched.get("metadata") or {}).get("subagent_route") or {}
        self.assertEqual(route.get("target_agent_id"), MONITORING_AGENT_ID)

    def test_selector_unchanged_when_subagent_route_present(self) -> None:
        """RAG selector (S2) must not be overridden by subagent routing."""
        import core.ask_rag_selector as selector_mod

        decide_use_rag = selector_mod.decide_use_rag

        built = attach_subagent_route_to_context(
            build_rooted_context({"query": "你好"}, mode="ask_pipeline")
        )
        decision = decide_use_rag("你好", context_payload=built)
        self.assertFalse(decision.get("use_rag"))
        self.assertEqual(
            (built.get("metadata") or {}).get("subagent_route", {}).get("target_agent_id"),
            DEFAULT_AGENT_ID,
        )


if __name__ == "__main__":
    unittest.main()
