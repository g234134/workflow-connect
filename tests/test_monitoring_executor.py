"""Sprint 4 · O-2a: monitoring subagent executor (service adapter + stub fallback)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.context_entry import build_rooted_context
from subagents.context_routing import (
    MONITORING_AGENT_ID,
    enrich_init_with_subagent_route,
)
from subagents.monitoring_executor import (
    ENV_MONITORING_GRAPH_ENABLED,
    EXECUTOR_ADAPTER_ID,
    EXECUTOR_VERSION,
    FALLBACK_STUB,
    MONITORING_SUBAGENT_ID,
    attach_executor_result_to_init,
    extract_monitoring_graph_summary_from_init,
    extract_monitoring_summary_from_init,
    get_monitoring_task_log,
    maybe_run_monitoring_executor,
    reset_monitoring_task_log,
    resolve_monitoring_service_query,
    run_monitoring_subagent,
)


class TestMonitoringExecutor(unittest.TestCase):
    def setUp(self) -> None:
        reset_monitoring_task_log()
        self._adapter_patcher = mock.patch(
            "subagents.monitoring_executor._invoke_monitoring_service_adapter",
            return_value={"ok": False, "message": "test: force stub path"},
        )
        self._adapter_patcher.start()

    def tearDown(self) -> None:
        self._adapter_patcher.stop()
        os.environ.pop(ENV_MONITORING_GRAPH_ENABLED, None)

    def test_extract_monitoring_summary_from_init(self) -> None:
        noop_mon = extract_monitoring_summary_from_init(
            {
                "_monitoring_executor_result": {
                    "ok": True,
                    "noop": True,
                    "monitoring": False,
                    "executed": False,
                    "executor": None,
                    "message": "subagent executor skipped (not monitoring route)",
                }
            }
        )
        self.assertFalse(noop_mon.get("monitoring"))
        self.assertTrue(noop_mon.get("noop"))

        stub_mon = extract_monitoring_summary_from_init(
            {
                "_monitoring_executor_result": {
                    "ok": True,
                    "monitoring": True,
                    "executed": True,
                    "executor": EXECUTOR_VERSION,
                    "fallback": FALLBACK_STUB,
                    "message": "monitoring stub executed",
                }
            }
        )
        self.assertTrue(stub_mon.get("monitoring"))
        self.assertEqual(stub_mon.get("executor"), EXECUTOR_VERSION)

    def test_run_monitoring_subagent_returns_stub_markers(self) -> None:
        result = run_monitoring_subagent(
            {"task_id": "mon-1", "task_type": "monitoring", "goal": "KPI drift"},
            {"ok": True, "metadata": {}},
            routing={"subagent_id": MONITORING_SUBAGENT_ID},
        )
        self.assertTrue(result.get("ok"))
        self.assertTrue(result.get("monitoring"))
        self.assertEqual(result.get("executor"), EXECUTOR_VERSION)
        self.assertEqual(result.get("fallback"), FALLBACK_STUB)
        self.assertEqual(result.get("message"), "monitoring stub executed")
        self.assertIn("adapter_error", result)
        self.assertEqual(len(get_monitoring_task_log()), 1)

    def test_maybe_run_noop_for_default_route(self) -> None:
        result = maybe_run_monitoring_executor(
            {"query": "你好"},
            {"ok": True},
            init={
                "_subagent_route": {"target_agent_id": "default_subagent"},
                "_subagent_target_agent_id": "default_subagent",
            },
        )
        self.assertTrue(result.get("noop"))
        self.assertFalse(result.get("monitoring"))
        self.assertFalse(result.get("executed"))
        self.assertEqual(len(get_monitoring_task_log()), 0)

    def test_maybe_run_for_monitoring_subagent_id_hyphen(self) -> None:
        result = maybe_run_monitoring_executor(
            {"task_type": "monitoring"},
            {"ok": True},
            init={"_subagent_route": {"subagent_id": MONITORING_SUBAGENT_ID}},
        )
        self.assertTrue(result.get("monitoring"))
        self.assertEqual(result.get("executor"), EXECUTOR_VERSION)
        self.assertEqual(result.get("fallback"), FALLBACK_STUB)

    def test_maybe_run_for_c1_target_agent_id(self) -> None:
        result = maybe_run_monitoring_executor(
            {"task_type": "monitoring"},
            {"ok": True},
            init={"_subagent_target_agent_id": MONITORING_AGENT_ID},
        )
        self.assertTrue(result.get("executed"))
        self.assertTrue(result.get("monitoring"))

    def test_attach_executor_on_enriched_init_monitoring_only(self) -> None:
        built = build_rooted_context(
            {
                "query": "wave1 monitoring acceptance",
                "task_type": "monitoring",
                "tags": ["monitoring"],
            },
            mode="ask_pipeline",
        )
        self.assertTrue(built.get("ok"), built.get("message"))
        init = enrich_init_with_subagent_route(
            {"query": "wave1 monitoring acceptance", "top_k": 3},
            task_id="mon-attach",
            context_built=built,
        )
        self.assertEqual(init.get("_subagent_target_agent_id"), MONITORING_AGENT_ID)

        with_exec = attach_executor_result_to_init(init, context_built=built)
        mon = with_exec.get("_monitoring_executor_result") or {}
        self.assertTrue(mon.get("monitoring"))
        self.assertEqual(mon.get("executor"), EXECUTOR_VERSION)

        general_built = build_rooted_context({"query": "你好"}, mode="ask_pipeline")
        general_init = enrich_init_with_subagent_route(
            {"query": "你好", "top_k": 3},
            task_id="gen-attach",
            context_built=general_built,
        )
        general_exec = attach_executor_result_to_init(general_init, context_built=general_built)
        gen_mon = general_exec.get("_monitoring_executor_result") or {}
        self.assertTrue(gen_mon.get("noop"))
        self.assertFalse(gen_mon.get("monitoring"))

    def test_hline_routing_plus_executor_integration(self) -> None:
        """build_rooted_context → C-1 route → O-1 executor (ask init shape, no graph)."""
        built = build_rooted_context(
            {
                "query": "Check /monitoring/overview KPI",
                "task_type": "monitoring",
                "tags": ["monitoring"],
            },
            mode="ask_pipeline",
        )
        init = enrich_init_with_subagent_route(
            {"query": "Check /monitoring/overview KPI", "top_k": 3},
            task_id="hline-mon",
            context_built=built,
        )
        final_init = attach_executor_result_to_init(init, context_built=built)
        mon = final_init.get("_monitoring_executor_result") or {}
        self.assertTrue(mon.get("monitoring"))
        self.assertEqual(mon.get("executor"), EXECUTOR_VERSION)
        self.assertEqual(
            (final_init.get("_subagent_route") or {}).get("target_agent_id"),
            MONITORING_AGENT_ID,
        )

    def test_resolve_query_dashboard_summary_from_text(self) -> None:
        name, kwargs = resolve_monitoring_service_query(
            {"query": "GET /monitoring/dashboard-summary bundle"}
        )
        self.assertEqual(name, "get_dashboard_summary")
        self.assertEqual(kwargs.get("cost_days"), 7)

    def test_service_adapter_success(self) -> None:
        self._adapter_patcher.stop()
        with mock.patch(
            "subagents.monitoring_executor._invoke_monitoring_service_adapter",
            return_value={
                "ok": True,
                "service_query": "get_overview",
                "service_summary": {"task_count": 3, "success_rate": 1.0},
            },
        ):
            result = run_monitoring_subagent(
                {"task_id": "mon-adapt", "query": "monitoring overview"},
                {"ok": True},
                routing={"subagent_id": MONITORING_SUBAGENT_ID},
            )
        self.assertEqual(result.get("executor"), EXECUTOR_ADAPTER_ID)
        self.assertNotIn("fallback", result)
        self.assertEqual(result.get("service_query"), "get_overview")
        self.assertEqual(result.get("service_summary", {}).get("task_count"), 3)

    def test_service_adapter_fallback_on_failure(self) -> None:
        self._adapter_patcher.stop()
        with mock.patch(
            "subagents.monitoring_executor._invoke_monitoring_service_adapter",
            return_value={"ok": False, "message": "DATABASE_URL not configured"},
        ):
            result = run_monitoring_subagent(
                {"task_id": "mon-fb"},
                {"ok": True},
                routing={"target_agent_id": MONITORING_AGENT_ID},
            )
        self.assertEqual(result.get("executor"), EXECUTOR_VERSION)
        self.assertEqual(result.get("fallback"), FALLBACK_STUB)
        self.assertIn("DATABASE_URL", result.get("adapter_error", ""))

    def test_graph_flag_off_no_graph_result(self) -> None:
        os.environ.pop(ENV_MONITORING_GRAPH_ENABLED, None)
        self._adapter_patcher.stop()
        with mock.patch(
            "subagents.monitoring_executor._invoke_monitoring_service_adapter",
            return_value={
                "ok": True,
                "service_query": "get_overview",
                "service_summary": {"task_count": 1, "success_rate": 1.0},
            },
        ):
            result = run_monitoring_subagent(
                {"task_id": "mon-g-off"},
                {"ok": True},
                routing={"subagent_id": MONITORING_SUBAGENT_ID},
            )
        self.assertNotIn("_monitoring_graph_result", result)

    def test_graph_flag_on_adapter_success_sets_graph_result(self) -> None:
        os.environ[ENV_MONITORING_GRAPH_ENABLED] = "1"
        self._adapter_patcher.stop()
        with mock.patch(
            "subagents.monitoring_executor._invoke_monitoring_service_adapter",
            return_value={
                "ok": True,
                "service_query": "get_overview",
                "service_summary": {"task_count": 2, "success_rate": 0.9, "dlq_backlog": 1},
            },
        ):
            result = run_monitoring_subagent(
                {"task_id": "mon-g-on"},
                {"ok": True},
                routing={"subagent_id": MONITORING_SUBAGENT_ID, "rule_id": "ROUTE-MON-1"},
            )
        graph = result.get("_monitoring_graph_result") or {}
        self.assertTrue(graph.get("ok"))
        self.assertIsInstance(graph.get("recommendations"), list)
        analysis = graph.get("analysis") or {}
        self.assertEqual(analysis.get("graph_version"), "v0.2-langgraph-min")
        pub = extract_monitoring_graph_summary_from_init(
            {"_monitoring_graph_result": graph}
        )
        self.assertIsNotNone(pub)
        assert pub is not None
        self.assertTrue(pub.get("ok"))
        self.assertGreaterEqual(pub.get("recommendation_count", 0), 1)

    def test_graph_error_does_not_break_executor(self) -> None:
        os.environ[ENV_MONITORING_GRAPH_ENABLED] = "1"
        self._adapter_patcher.stop()
        with mock.patch(
            "subagents.monitoring_executor._invoke_monitoring_service_adapter",
            return_value={
                "ok": True,
                "service_query": "get_overview",
                "service_summary": {"task_count": 1},
            },
        ), mock.patch(
            "subagents.monitoring_executor.run_monitoring_graph",
            side_effect=RuntimeError("graph boom"),
        ):
            result = run_monitoring_subagent(
                {"task_id": "mon-g-err"},
                {"ok": True},
                routing={"target_agent_id": MONITORING_AGENT_ID},
            )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("executor"), EXECUTOR_ADAPTER_ID)
        graph = result.get("_monitoring_graph_result") or {}
        self.assertFalse(graph.get("ok"))
        self.assertIn("graph boom", str(graph.get("reason", "")))

    def test_attach_executor_propagates_graph_to_init(self) -> None:
        os.environ[ENV_MONITORING_GRAPH_ENABLED] = "1"
        self._adapter_patcher.stop()
        with mock.patch(
            "subagents.monitoring_executor._invoke_monitoring_service_adapter",
            return_value={
                "ok": True,
                "service_query": "get_overview",
                "service_summary": {"success_rate": 1.0},
            },
        ):
            init = attach_executor_result_to_init(
                {
                    "_subagent_route": {"target_agent_id": MONITORING_AGENT_ID},
                    "query": "monitoring overview",
                },
                context_built={"ok": True},
            )
        self.assertIn("_monitoring_graph_result", init)
        self.assertTrue((init.get("_monitoring_graph_result") or {}).get("ok"))


if __name__ == "__main__":
    unittest.main()
