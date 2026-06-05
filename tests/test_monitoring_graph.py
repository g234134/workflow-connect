"""Sprint 5 · A-line: monitoring LangGraph (read-only observability)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.monitoring_graph import (
    MONITORING_GRAPH_VERSION,
    build_monitoring_graph,
    extract_monitoring_graph_public_summary,
    run_monitoring_graph,
)

try:
    from langgraph.graph import StateGraph  # noqa: F401

    _LANGGRAPH_INSTALLED = True
except ImportError:
    _LANGGRAPH_INSTALLED = False


@unittest.skipUnless(_LANGGRAPH_INSTALLED, "langgraph package required")
class TestMonitoringGraphLangGraph(unittest.TestCase):
    def test_build_monitoring_graph_compiles(self) -> None:
        compiled = build_monitoring_graph()
        self.assertTrue(callable(getattr(compiled, "invoke", None)))

    def test_run_graph_happy_path_recommendations(self) -> None:
        result = run_monitoring_graph(
            {
                "task_id": "g-1",
                "service_query": "get_overview",
                "subagent_route": {"rule_id": "ROUTE-MON-1"},
                "service_summary": {
                    "task_count": 2,
                    "success_rate": 0.9,
                    "dlq_backlog": 1,
                    "p95_latency_ms": 6000,
                },
            }
        )
        self.assertTrue(result.get("ok"))
        analysis = result.get("analysis") or {}
        self.assertEqual(analysis.get("graph_version"), MONITORING_GRAPH_VERSION)
        self.assertEqual(analysis.get("routing_rule_id"), "ROUTE-MON-1")
        self.assertIn("signals", analysis)
        self.assertGreaterEqual(analysis.get("signal_count", 0), 1)
        nodes = analysis.get("nodes_executed") or []
        self.assertEqual(
            nodes,
            ["summarize", "analyze", "recommend", "finalize"],
        )
        kinds = {r.get("kind") for r in result.get("recommendations") or []}
        self.assertTrue({"health", "dlq", "latency"}.issubset(kinds))

    def test_missing_service_summary(self) -> None:
        result = run_monitoring_graph({"service_summary": {}})
        self.assertFalse(result.get("ok"))
        self.assertIn("service_summary", str(result.get("reason", "")))
        analysis = result.get("analysis") or {}
        nodes = analysis.get("nodes_executed") or []
        self.assertEqual(nodes, ["summarize", "finalize"])

    def test_public_summary_includes_nodes_executed(self) -> None:
        result = run_monitoring_graph(
            {
                "service_summary": {"success_rate": 1.0},
                "service_query": "get_overview",
            }
        )
        pub = extract_monitoring_graph_public_summary(result)
        self.assertIsNotNone(pub)
        assert pub is not None
        summary = pub.get("analysis_summary") or {}
        self.assertEqual(summary.get("graph_version"), MONITORING_GRAPH_VERSION)
        self.assertIn("nodes_executed", summary)


class TestMonitoringGraphContract(unittest.TestCase):
    def test_healthy_summary_no_recommendations(self) -> None:
        result = run_monitoring_graph(
            {
                "service_summary": {
                    "success_rate": 1.0,
                    "dlq_backlog": 0,
                    "p95_latency_ms": 100,
                },
            }
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("recommendations"), [])


if __name__ == "__main__":
    unittest.main()
