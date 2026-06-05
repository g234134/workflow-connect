"""Unit tests: ask-mainline skill wrappers (I-ask-skills-wire)."""

from __future__ import annotations

import unittest

from metrics.metrics_collector import MetricsCollector, reset_collector
from observability.logging_adapter import reset_active_trace
from reliability.retry_handler import ReliabilityError
from skills.skill_answer_for_ask import run_skill_answer_for_ask
from skills.skill_retrieve_for_ask import run_skill_retrieve_for_ask


def _mock_retrieve_core() -> dict[str, object]:
    return {
        "ok": True,
        "message": "unit retrieve ok",
        "hits": [{"id": "h1"}],
        "source": "test_core",
    }


def _mock_answer_core() -> dict[str, object]:
    return {
        "ok": True,
        "message": "unit answer ok",
        "answer": "hello from core",
    }


class TestSkillsAskWireUnit(unittest.TestCase):
    def setUp(self) -> None:
        reset_collector()
        reset_active_trace()

    def tearDown(self) -> None:
        reset_active_trace()

    def test_retrieve_skill_matches_core_shape(self) -> None:
        col = MetricsCollector()
        out = run_skill_retrieve_for_ask(
            "ask-unit-retrieve",
            core_fn=_mock_retrieve_core,
            collector=col,
            call_site="unittest.ask_wire",
        )
        self.assertTrue(out["ok"])
        result = out["result"]
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("message"), "unit retrieve ok")
        self.assertEqual(len(result.get("hits") or []), 1)
        self.assertEqual(out["metadata"]["skill_name"], "skill_retrieve_for_ask")
        self.assertEqual(out["metadata"]["call_site"], "unittest.ask_wire")

        record = col.get_task("ask-unit-retrieve")["record"]
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 1)

    def test_retrieve_skill_simulated_retry(self) -> None:
        col = MetricsCollector()
        out = run_skill_retrieve_for_ask(
            "ask-unit-retrieve-retry",
            core_fn=_mock_retrieve_core,
            collector=col,
            simulate_first_failure=True,
        )
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(int(out["retry_count"] or 0), 1)
        record = col.get_task("ask-unit-retrieve-retry")["record"]
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 2)

    def test_answer_skill_matches_core_shape(self) -> None:
        col = MetricsCollector()
        out = run_skill_answer_for_ask(
            "ask-unit-answer",
            core_fn=_mock_answer_core,
            collector=col,
            call_site="unittest.answer_wire",
        )
        self.assertTrue(out["ok"])
        result = out["result"]
        self.assertEqual((result or {}).get("answer"), "hello from core")
        self.assertEqual(out["metadata"]["step_name"], "execute")
        self.assertEqual(out["metadata"]["skill_name"], "skill_answer_for_ask")
        self.assertEqual(out["metadata"]["call_site"], "unittest.answer_wire")

        record = col.get_task("ask-unit-answer")["record"]
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 1)

    def test_answer_skill_simulated_retry(self) -> None:
        col = MetricsCollector()
        out = run_skill_answer_for_ask(
            "ask-unit-answer-retry",
            core_fn=_mock_answer_core,
            collector=col,
            simulate_first_failure=True,
        )
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(int(out["retry_count"] or 0), 1)
        self.assertEqual(out["metadata"]["skill_name"], "skill_answer_for_ask")
        record = col.get_task("ask-unit-answer-retry")["record"]
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 2)

    def test_answer_skill_llm_error_failure(self) -> None:
        col = MetricsCollector()

        def _always_fail() -> dict[str, object]:
            raise ReliabilityError("mock llm unavailable", error_type="llm_error")

        out = run_skill_answer_for_ask(
            "ask-unit-answer-fail",
            core_fn=_always_fail,
            collector=col,
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error_type"], "llm_error")
        self.assertGreaterEqual(int(out["retry_count"] or 0), 1)
        self.assertEqual(out["metadata"]["skill_name"], "skill_answer_for_ask")
        record = col.get_task("ask-unit-answer-fail")["record"]
        self.assertGreaterEqual(int(record.get("external_call_count", 0)), 1)


if __name__ == "__main__":
    unittest.main()
