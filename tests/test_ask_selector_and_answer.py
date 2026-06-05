"""Ask RAG selector + no-context / fallback answer path (Chat B)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOV_ROOT = _REPO_ROOT / "01_Environments" / "python_venvs" / "gov_core_system"

if str(_GOV_ROOT) not in sys.path:
    sys.path.insert(0, str(_GOV_ROOT))


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


def _mock_stub_retrieve(query: str, top_k: int) -> dict[str, object]:
    return {
        "ok": True,
        "message": "stub retrieve ok",
        "query": query,
        "top_k": top_k,
        "hits": [{"id": "stub-1"}],
    }


def _mock_rag_answer(query: str, top_k: int) -> dict[str, object]:
    return {
        "ok": True,
        "message": "mock rag answer",
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


class TestAskRagSelectorUnit(unittest.TestCase):
    def test_s1_kb_context_uses_rag(self) -> None:
        from core.ask_rag_selector import decide_use_rag

        out = decide_use_rag(
            "document_chunks pipeline 如何運作？",
            context_payload=_hline_with_kb(),
        )
        self.assertTrue(out["use_rag"])
        self.assertFalse(out["skip_rag"])
        self.assertEqual(out["selector_rule_id"], "ASK-R4")

    def test_s2_greeting_skips_rag(self) -> None:
        from core.ask_rag_selector import decide_use_rag

        out = decide_use_rag("你好", context_payload=None)
        self.assertFalse(out["use_rag"])
        self.assertTrue(out["skip_rag"])
        self.assertEqual(out["selector_rule_id"], "ASK-R2")

    def test_s2_short_chitchat_skips_rag(self) -> None:
        from core.ask_rag_selector import decide_use_rag

        out = decide_use_rag("好的", context_payload=None)
        self.assertFalse(out["use_rag"])
        self.assertEqual(out["selector_rule_id"], "ASK-R2")

    def test_knowledge_pattern_without_context_uses_rag(self) -> None:
        from core.ask_rag_selector import decide_use_rag

        out = decide_use_rag("explain ask_pipeline retrieve flow", context_payload=None)
        self.assertTrue(out["use_rag"])
        self.assertEqual(out["selector_rule_id"], "ASK-R5")


class TestAskSelectorFlowIntegration(unittest.TestCase):
    def setUp(self) -> None:
        import core.langgraph_flow as langgraph_flow_mod

        langgraph_flow_mod._COMPILED_ASK = None
        os.environ.pop("GOV_CORE_ASK_IBRIDGE_V0", None)
        from core.ask_pipeline_ibridge_v0 import ensure_k1_packages_on_path

        ensure_k1_packages_on_path()
        from metrics.metrics_collector import reset_collector
        from observability.logging_adapter import reset_active_trace

        reset_collector()
        reset_active_trace()

    def tearDown(self) -> None:
        os.environ.pop("GOV_CORE_ASK_IBRIDGE_V0", None)
        try:
            from metrics.metrics_collector import reset_collector
            from observability.logging_adapter import reset_active_trace

            reset_collector()
            reset_active_trace()
        except ImportError:
            pass

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.fallback.should_use_retrieve_stub", return_value=True)
    @mock.patch("core.fallback.retrieve_stub_fallback", side_effect=_mock_stub_retrieve)
    @mock.patch("core.rag_backend.rag_answer", side_effect=_mock_rag_answer)
    @mock.patch("core.ask_pipeline_ibridge_v0._import_build_rooted_context")
    def test_s1_flow_with_context_runs_retrieve_and_answer_skills(
        self,
        mock_import_brc: mock.MagicMock,
        _rag: mock.MagicMock,
        _retrieve: mock.MagicMock,
        _stub: mock.MagicMock,
        _health: mock.MagicMock,
    ) -> None:
        from core.langgraph_flow import run_ask_flow

        mock_brc = mock.MagicMock(return_value=_hline_with_kb())
        mock_import_brc.return_value = mock_brc

        out = run_ask_flow(
            "document_chunks pipeline 如何運作？",
            top_k=2,
            ibridge_v0=False,
            thread_id="selector-s1",
        )
        self.assertTrue(out.get("ok"), out.get("message"))
        nodes = out.get("executed_nodes") or []
        self.assertIn("selector_node", nodes)
        self.assertIn("retrieve_node", nodes)
        selector = out.get("ask_selector") or {}
        self.assertTrue(selector.get("use_rag"))

        from metrics.metrics_collector import get_collector

        record = get_collector().get_task("selector-s1").get("record") or {}
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 2)

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.ask_direct_answer.perform_direct_answer", side_effect=_mock_direct_answer)
    def test_s2_greeting_skips_retrieve_answer_skill_still_runs(
        self,
        _direct: mock.MagicMock,
        _health: mock.MagicMock,
    ) -> None:
        from core.langgraph_flow import run_ask_flow
        import skills.skill_answer_for_ask as answer_mod

        with mock.patch.object(
            answer_mod,
            "run_skill_answer_for_ask",
            wraps=answer_mod.run_skill_answer_for_ask,
        ) as answer_skill:
            out = run_ask_flow("你好", top_k=2, ibridge_v0=False, thread_id="selector-s2")

        self.assertTrue(out.get("ok"), out.get("message"))
        nodes = out.get("executed_nodes") or []
        self.assertIn("selector_node", nodes)
        self.assertNotIn("retrieve_node", nodes)
        selector = out.get("ask_selector") or {}
        self.assertFalse(selector.get("use_rag"))
        answer_skill.assert_called_once()

        from metrics.metrics_collector import get_collector

        record = get_collector().get_task("selector-s2").get("record") or {}
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 1)
        self.assertEqual((out.get("answer") or {}).get("answer"), "direct:你好")

    @mock.patch("core.infra_health.run_full_healthcheck", side_effect=_mock_health_ok)
    @mock.patch("core.langgraph_flow._perform_retrieve_query")
    @mock.patch("core.ask_direct_answer.perform_direct_answer", side_effect=_mock_direct_answer)
    def test_s3_retrieve_failure_falls_back_to_direct_answer_with_tags(
        self,
        _direct: mock.MagicMock,
        mock_perform_retrieve: mock.MagicMock,
        _health: mock.MagicMock,
    ) -> None:
        from core.langgraph_flow import run_ask_flow

        mock_perform_retrieve.return_value = {
            "ok": False,
            "message": "retrieve timed out",
            "error_type": "timeout",
            "hits": [],
        }

        out = run_ask_flow(
            "explain ask_pipeline retrieve flow",
            top_k=2,
            ibridge_v0=True,
            thread_id="selector-s3",
        )
        self.assertTrue(out.get("ok"), out.get("message"))
        nodes = out.get("executed_nodes") or []
        self.assertIn("retrieve_node", nodes)
        self.assertIn("answer_node", nodes)

        answer = out.get("answer") or {}
        self.assertEqual(answer.get("answer"), "direct:explain ask_pipeline retrieve flow")
        self.assertTrue(answer.get("retrieve_fallback"))
        self.assertEqual(answer.get("retrieve_error_type"), "timeout")

        ibridge = out.get("ibridge_v0") or {}
        decision = ibridge.get("selector_decision") or {}
        self.assertTrue(decision.get("retrieve_fallback"))
        self.assertTrue(decision.get("use_rag"))

        record = out.get("ibridge_record") or {}
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 1)


class TestAskSelectorK2Optional(unittest.TestCase):
    """Optional: K-2 uses separate prefetch; selector contract is ask-mainline only."""

    def test_k2_merge_interface_documents_shadow_tests(self) -> None:
        k2_path = _REPO_ROOT / "core" / "langgraph_flow_k2.py"
        self.assertTrue(k2_path.is_file(), "K-2 module expected at repo core/")
        text = k2_path.read_text(encoding="utf-8")
        self.assertIn("tests/test_k2_ask_shadow.py", text)
        self.assertIn("ASK_MERGE_INTERFACE", text)


if __name__ == "__main__":
    unittest.main()
