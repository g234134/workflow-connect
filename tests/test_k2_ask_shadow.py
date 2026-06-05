"""
K-2 ↔ ask shadow comparison tests (dev/test only).

Runs legacy ``run_ask_flow`` and ``run_k2_flow`` on the same logical input with
gov_core mocks (no live RAG/health). Prints a short diff report per case for
manual review.

See ``docs/k2_behavior_profile.md`` for scenario baselines and governance notes.
"""

from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOV_ROOT = _REPO_ROOT / "01_Environments" / "python_venvs" / "gov_core_system"

try:
    from langgraph.graph import StateGraph  # noqa: F401

    _LANGGRAPH_INSTALLED = True
except ImportError:
    _LANGGRAPH_INSTALLED = False


def _purge_core_modules() -> None:
    for key in list(sys.modules):
        if key == "core" or key.startswith("core."):
            del sys.modules[key]


def _with_path_first(path: Path) -> None:
    path_s = str(path)
    while path_s in sys.path:
        sys.path.remove(path_s)
    sys.path.insert(0, path_s)


def _import_ask_runner(*, reload: bool = False) -> tuple[Any, Any]:
    """Load gov_core ask flow. Reuse cached module unless ``reload=True`` (keeps mocks)."""
    _with_path_first(_GOV_ROOT)
    if not reload and "core.langgraph_flow" in sys.modules:
        mod = sys.modules["core.langgraph_flow"]
        return mod.run_ask_flow, mod
    if reload:
        _purge_core_modules()
        _with_path_first(_GOV_ROOT)
    mod = importlib.import_module("core.langgraph_flow")
    return mod.run_ask_flow, mod


def _import_k2_runner() -> tuple[Any, Any]:
    """Load repo-root K-2 flow and shadow helpers."""
    _purge_core_modules()
    _with_path_first(_REPO_ROOT)
    for extra in (_REPO_ROOT / "02_Agents_Core", _REPO_ROOT / "04_Workflows"):
        extra_s = str(extra)
        if extra_s not in sys.path:
            sys.path.append(extra_s)
    k2_mod = importlib.import_module("core.langgraph_flow_k2")
    shadow_mod = importlib.import_module("core.k2_ask_shadow")
    return k2_mod.run_k2_flow, shadow_mod


def _hline_with_kb() -> dict[str, object]:
    return {
        "ok": True,
        "message": "ok",
        "root_context": {"rules": []},
        "working_context": {"task_input": {"context_refs": ["doc://internal/runbook"]}},
        "long_term_memory": {"semantic": [{"id": "m1"}], "structured": []},
        "token_usage": {"total_tokens": 32, "total": 32},
        "metadata": {"entry": "context_entry", "entry_mode": "ask_pipeline", "tags": ["knowledge"]},
        "task_input": {"task_id": "task-s1", "context_refs": ["doc://internal/runbook"]},
    }


def _mock_health_ok(*_a: object, **_k: object) -> dict[str, object]:
    return {"ok": True, "all_ok": True, "message": "mock health ok"}


def _mock_rag_answer(query: str, top_k: int) -> dict[str, object]:
    return {
        "ok": True,
        "message": "mock answer",
        "query": query,
        "top_k": top_k,
        "answer": f"rag:{query}",
        "sources": [{"rank": 1}],
    }


def _mock_direct_answer(
    question: str,
    *,
    retrieve_error: str | None = None,
    retrieve_error_type: str | None = None,
) -> dict[str, object]:
    out: dict[str, object] = {
        "ok": True,
        "message": "ok",
        "question": question,
        "answer": f"direct:{question}",
        "sources": [],
        "answer_mode": "direct",
    }
    if retrieve_error:
        out["retrieve_fallback"] = True
        out["retrieve_error"] = retrieve_error
    if retrieve_error_type:
        out["retrieve_error_type"] = retrieve_error_type
    return out


def _mock_stub_retrieve(query: str, top_k: int) -> dict[str, object]:
    return {
        "ok": True,
        "message": "stub retrieve ok",
        "query": query,
        "top_k": top_k,
        "hits": [{"id": "stub-1"}],
    }


@unittest.skipUnless(_LANGGRAPH_INSTALLED, "langgraph package required")
class TestK2AskShadowHelpers(unittest.TestCase):
    def test_map_task_input_for_k2(self) -> None:
        _, shadow = _import_k2_runner()
        ti = shadow.map_task_input_for_k2({"task_id": "t1", "query": "hello"})
        self.assertEqual(ti["task_id"], "t1")
        self.assertEqual(ti["goal"], "hello")

    def test_compare_shadow_profiles_layers(self) -> None:
        _, shadow = _import_k2_runner()
        ask_s = {
            "ok": True,
            "status": "success",
            "answer_preview": "rag:hello",
            "handoff_count": 0,
            "executed_node_count": 4,
            "retry_count": 0,
            "selector_use_rag": True,
            "selector_rule_id": "ASK-R5",
            "retrieve_fallback": False,
            "has_eval_metadata": False,
            "error_type": None,
            "tags": [],
            "context_entry_mode": "ask_pipeline",
            "message_preview": "ask pipeline completed",
        }
        k2_s = {
            "ok": True,
            "status": "success",
            "answer_preview": "agent succeeded",
            "handoff_count": 2,
            "executed_node_count": 0,
            "retry_count": 1,
            "selector_use_rag": None,
            "selector_rule_id": "K2-N/A",
            "retrieve_fallback": False,
            "has_eval_metadata": True,
            "error_type": None,
            "tags": ["infra_risk"],
            "context_entry_mode": "k2_pipeline",
            "message_preview": "agent succeeded",
        }
        profile = shadow.compare_shadow_profiles(ask_s, k2_s, case_name="unit")
        self.assertIn("layers", profile)
        self.assertIn("classification", profile)
        self.assertTrue(profile.get("functional_ok"))
        self.assertIn("message_preview", profile["classification"]["expected"])
        self.assertIn("handoff_count", profile["classification"]["uncertain"])

    def test_merge_hook_envelope_shape(self) -> None:
        _, shadow = _import_k2_runner()
        k2_stub = {
            "ok": True,
            "message": "done",
            "state": {"final_result": {"ok": True, "message": "done", "result": {"summary": "x"}}},
            "record": {"retry_count": 1, "handoff_count": 2, "success": True},
            "eval_metadata": {"eval_gate": {"pass": True}},
        }
        env = shadow.k2_result_to_ask_response_envelope(k2_stub, query="q", top_k=2)
        self.assertEqual(env.get("mode"), "ask")
        self.assertTrue(env.get("ok"))
        self.assertIn("k2_eval_metadata", env)

    def test_ask_merge_interface_shadow_ready(self) -> None:
        _, shadow = _import_k2_runner()
        from core.langgraph_flow_k2 import ASK_MERGE_INTERFACE

        self.assertEqual(ASK_MERGE_INTERFACE.get("status"), "shadow_ready")
        self.assertIn("shadow", ASK_MERGE_INTERFACE)

    def test_merge_adapter_importable(self) -> None:
        from core.k2_merge_adapter import merge_ask_and_k2

        self.assertTrue(callable(merge_ask_and_k2))


@unittest.skipUnless(_LANGGRAPH_INSTALLED, "langgraph package required")
class TestK2AskShadowMerge(unittest.TestCase):
    """Shadow + merge adapter: synthetic envelopes (no full e2e required)."""

    def test_shadow_merge_both_ok_infra_risk(self) -> None:
        from core.k2_merge_adapter import merge_ask_and_k2

        ask_out = {
            "mode": "ask",
            "query": "q",
            "top_k": 2,
            "ok": True,
            "message": "ok",
            "answer": {"answer": "rag:q", "ok": True},
            "errors": [],
            "executed_nodes": ["answer_node"],
        }
        k2_out = {
            "ok": True,
            "message": "done",
            "state": {
                "final_result": {
                    "ok": True,
                    "result": {"summary": "agent succeeded"},
                },
            },
            "record": {"retry_count": 1, "handoff_count": 1, "success": True},
            "eval_metadata": {"eval_gate": {"pass": False, "tags": ["infra_risk"]}},
        }
        merged = merge_ask_and_k2(ask_out, k2_out, query="q", top_k=2)
        self.assertFalse(merged["ok"])
        self.assertEqual((merged["answer"] or {}).get("answer"), "rag:q")
        self.assertEqual(merged["k2_merge"]["gate_result"], "fail")
        self.assertTrue(merged["k2_merge"]["ci_fail"])


@unittest.skipUnless(_LANGGRAPH_INSTALLED, "langgraph package required")
class TestK2AskShadowE2E(unittest.TestCase):
    """Shadow-run ask vs K-2; field mismatches expected — assert no crashes."""

    def setUp(self) -> None:
        os.environ.pop("GOV_CORE_ASK_IBRIDGE_V0", None)
        _import_ask_runner(reload=True)
        try:
            from core.ask_pipeline_ibridge_v0 import ensure_k1_packages_on_path

            ensure_k1_packages_on_path()
        except ImportError:
            pass
        _lg_mod = importlib.import_module("core.langgraph_flow")
        _lg_mod._COMPILED_ASK = None
        try:
            from metrics.metrics_collector import reset_collector
            from observability.logging_adapter import reset_active_trace

            reset_collector()
            reset_active_trace()
        except ImportError:
            pass

    def tearDown(self) -> None:
        os.environ.pop("GOV_CORE_ASK_IBRIDGE_V0", None)
        _purge_core_modules()

    def _run_case(
        self,
        case_name: str,
        query: str,
        *,
        top_k: int = 2,
        ask_kwargs: dict | None = None,
        k2_kwargs: dict | None = None,
    ) -> dict[str, Any]:
        # Run ask before loading K-2: ``_import_k2_runner`` purges ``core`` from sys.modules.
        run_ask_flow, _lg_mod = _import_ask_runner(reload=False)
        base_id = f"k2-shadow-{case_name}"
        ask_kw = {"top_k": top_k, "thread_id": base_id, "ibridge_v0": False}
        ask_kw.update(ask_kwargs or {})
        ask_out = run_ask_flow(query, **ask_kw)

        run_k2_flow, shadow = _import_k2_runner()
        task_input = shadow.build_shadow_task_input(
            task_id=f"{base_id}-shared",
            query=query,
            top_k=top_k,
            thread_id=base_id,
        )
        k2_out = run_k2_flow(
            task_id=f"{base_id}-k2",
            goal=query,
            task_input=shadow.map_task_input_for_k2(task_input, default_goal=query),
            **(k2_kwargs or {}),
        )

        comparison = shadow.compare_shadow_profiles(
            shadow.summarize_ask_output(ask_out),
            shadow.summarize_k2_output(k2_out),
            case_name=case_name,
        )
        comparison["report"] = shadow.format_shadow_report(case_name, comparison)
        comparison["ask_raw_ok"] = ask_out.get("ok")
        comparison["k2_raw_ok"] = k2_out.get("ok")
        comparison["ask_out"] = ask_out
        comparison["k2_out"] = k2_out
        print(comparison.get("report", ""))
        self.assertIsNotNone(comparison.get("ask_raw_ok"))
        self.assertIsNotNone(comparison.get("k2_raw_ok"))
        return comparison

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.fallback.should_use_retrieve_stub", return_value=True)
    @mock.patch("core.rag_backend.rag_answer", side_effect=_mock_rag_answer)
    def test_shadow_simple_happy(self, *_mocks: mock.MagicMock) -> None:
        """Legacy happy path: knowledge-shaped query, selector uses RAG, both succeed."""
        comp = self._run_case("simple_happy", "explain ask_pipeline retrieve flow")
        self.assertTrue(comp.get("ask_raw_ok"))
        self.assertTrue(comp.get("k2_raw_ok"))
        ask_s = comp.get("ask_summary") or {}
        self.assertTrue(ask_s.get("selector_use_rag"))
        mismatched = comp.get("mismatched") or {}
        self.assertIn("context_entry_mode", mismatched)
        self.assertIn("has_eval_metadata", mismatched)
        classification = comp.get("classification") or {}
        self.assertFalse(classification.get("unacceptable"))

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.ask_direct_answer.perform_direct_answer", side_effect=_mock_direct_answer)
    def test_shadow_greeting_selector_skip(self, *_mocks: mock.MagicMock) -> None:
        """S2-style: greeting skips retrieve on ask; K-2 still runs prefetch skill."""
        comp = self._run_case("greeting_skip", "你好")
        self.assertTrue(comp.get("ask_raw_ok"))
        self.assertTrue(comp.get("k2_raw_ok"))
        ask_out = comp.get("ask_out") or {}
        nodes = ask_out.get("executed_nodes") or []
        self.assertIn("selector_node", nodes)
        self.assertNotIn("retrieve_node", nodes)
        ask_s = comp.get("ask_summary") or {}
        self.assertFalse(ask_s.get("selector_use_rag"))
        self.assertEqual(ask_s.get("selector_rule_id"), "ASK-R2")

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.fallback.should_use_retrieve_stub", return_value=True)
    @mock.patch("core.fallback.retrieve_stub_fallback", side_effect=_mock_stub_retrieve)
    @mock.patch("core.rag_backend.rag_answer", side_effect=_mock_rag_answer)
    @mock.patch("core.ask_pipeline_ibridge_v0._import_build_rooted_context")
    def test_shadow_rag_with_kb_context(
        self,
        mock_import_brc: mock.MagicMock,
        *_mocks: mock.MagicMock,
    ) -> None:
        """S1-style: KB context + knowledge question → ask selector uses RAG."""
        mock_import_brc.return_value = mock.MagicMock(return_value=_hline_with_kb())
        comp = self._run_case(
            "rag_kb_context",
            "document_chunks pipeline 如何運作？",
            ask_kwargs={"ibridge_v0": False},
        )
        self.assertTrue(comp.get("ask_raw_ok"))
        self.assertTrue(comp.get("k2_raw_ok"))
        ask_out = comp.get("ask_out") or {}
        self.assertIn("retrieve_node", ask_out.get("executed_nodes") or [])
        ask_s = comp.get("ask_summary") or {}
        self.assertTrue(ask_s.get("selector_use_rag"))
        self.assertEqual(ask_s.get("selector_rule_id"), "ASK-R4")

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.langgraph_flow._perform_retrieve_query")
    @mock.patch("core.ask_direct_answer.perform_direct_answer", side_effect=_mock_direct_answer)
    def test_shadow_retrieve_timeout_fallback(
        self,
        _direct: mock.MagicMock,
        mock_perform_retrieve: mock.MagicMock,
        _health: mock.MagicMock,
    ) -> None:
        """S3-style: retrieve timeout → ask direct fallback; K-2 may still succeed via agents."""
        mock_perform_retrieve.return_value = {
            "ok": False,
            "message": "retrieve timed out",
            "error_type": "timeout",
            "hits": [],
        }
        comp = self._run_case(
            "retrieve_timeout",
            "explain ask_pipeline retrieve flow",
            ask_kwargs={"ibridge_v0": True},
            k2_kwargs={"simulate_skill_failure": True},
        )
        self.assertTrue(comp.get("ask_raw_ok"))
        self.assertTrue(comp.get("k2_raw_ok"))
        ask_s = comp.get("ask_summary") or {}
        self.assertTrue(ask_s.get("retrieve_fallback"))
        self.assertTrue(ask_s.get("selector_use_rag"))
        k2_out = comp.get("k2_out") or {}
        retrieve = (k2_out.get("state") or {}).get("skill_results", {}).get("retrieve") or {}
        self.assertGreaterEqual(int(retrieve.get("retry_count", 0)), 1)

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.fallback.should_use_retrieve_stub", return_value=True)
    @mock.patch("core.rag_backend.rag_answer", side_effect=_mock_rag_answer)
    def test_shadow_ibridge_v0_hline_alignment(self, *_mocks: mock.MagicMock) -> None:
        """I-bridge v0=True: ask exposes selector_decision + ibridge_record; compare profiles."""
        comp = self._run_case(
            "ibridge_v0",
            "explain ask_pipeline retrieve flow",
            ask_kwargs={"ibridge_v0": True},
        )
        self.assertTrue(comp.get("ask_raw_ok"))
        self.assertTrue(comp.get("k2_raw_ok"))
        ask_out = comp.get("ask_out") or {}
        ibridge = ask_out.get("ibridge_v0") or {}
        self.assertTrue(ibridge.get("context_payload_ok"))
        decision = ibridge.get("selector_decision") or {}
        self.assertIn("use_rag", decision)
        ask_s = comp.get("ask_summary") or {}
        self.assertEqual(ask_s.get("context_entry_mode"), "ask_pipeline")
        k2_s = comp.get("k2_summary") or {}
        self.assertEqual(k2_s.get("context_entry_mode"), "k2_pipeline")

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.fallback.should_use_retrieve_stub", return_value=True)
    @mock.patch("core.rag_backend.rag_answer", side_effect=_mock_rag_answer)
    def test_shadow_k2_skill_retry_still_succeeds(self, *_mocks: mock.MagicMock) -> None:
        comp = self._run_case(
            "k2_skill_retry",
            "shadow k2 skill retry path",
            k2_kwargs={"simulate_skill_failure": True},
        )
        self.assertTrue(comp.get("k2_raw_ok"))
        k2_out = comp.get("k2_out") or {}
        state = k2_out.get("state") or {}
        retrieve = (state.get("skill_results") or {}).get("retrieve") or {}
        self.assertGreaterEqual(int(retrieve.get("retry_count", 0)), 1)
        k2_s = comp.get("k2_summary") or {}
        self.assertTrue(k2_s.get("has_eval_metadata"))
        self.assertIn("retrieve_retry", k2_s.get("tags") or [])

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.fallback.should_use_retrieve_stub", return_value=True)
    @mock.patch("core.rag_backend.rag_answer", side_effect=_mock_rag_answer)
    def test_shadow_summaries_printable(self, *_mocks: mock.MagicMock) -> None:
        run_ask_flow, _ = _import_ask_runner()
        ask_out = run_ask_flow("shadow summary probe", top_k=2, ibridge_v0=False)
        run_k2_flow, shadow = _import_k2_runner()
        k2_out = run_k2_flow(task_id="k2-shadow-summary", goal="shadow summary probe")
        comp = shadow.compare_shadow_profiles(
            shadow.summarize_ask_output(ask_out),
            shadow.summarize_k2_output(k2_out),
            case_name="summary_probe",
        )
        print(shadow.format_shadow_report("summary_probe", comp))
        self.assertIn("ask_summary", comp)
        self.assertIn("k2_summary", comp)
        self.assertIn("layers", comp)


if __name__ == "__main__":
    unittest.main()
