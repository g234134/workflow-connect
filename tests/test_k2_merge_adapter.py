"""
Unit tests for K-2 ↔ ask merge adapter (dev/test only).

See ``docs/k2_merge_strategy.md`` for scenario table (S1–S7).
"""

from __future__ import annotations

import unittest

from core.k2_merge_adapter import (
    SEVERE_EVAL_TAGS,
    merge_ask_and_k2,
)


def _ask_stub(
    *,
    ok: bool = True,
    answer: str = "rag:hello",
    errors: list | None = None,
    retrieve_error_type: str | None = None,
) -> dict:
    answer_block: dict = {
        "ok": ok,
        "message": "ask done",
        "query": "hello",
        "top_k": 3,
        "answer": answer,
    }
    if retrieve_error_type:
        answer_block["retrieve_fallback"] = True
        answer_block["retrieve_error_type"] = retrieve_error_type
    return {
        "mode": "ask",
        "query": "hello",
        "top_k": 3,
        "ok": ok,
        "message": "ask pipeline completed",
        "answer": answer_block,
        "retrieve": {"ok": True, "hits": []},
        "errors": errors or ([] if ok else ["ask_fail"]),
        "executed_nodes": ["health_node", "selector_node", "answer_node"],
    }


def _k2_stub(
    *,
    ok: bool = True,
    summary: str = "agent succeeded",
    tags: list | None = None,
    error_type: str | None = None,
) -> dict:
    eval_meta: dict = {}
    if tags is not None:
        eval_meta = {"eval_gate": {"pass": not tags, "tags": tags, "reasons": tags}}
    state: dict = {
        "final_result": {
            "ok": ok,
            "status": "success" if ok else "fail",
            "message": summary,
            "result": {"summary": summary},
        },
        "skill_results": {"retrieve": {"ok": True, "hits": []}},
    }
    if error_type:
        state["error_type"] = error_type
    record = {"retry_count": 1, "handoff_count": 2, "success": ok, "trace_completeness": {"score": 0.9}}
    return {
        "ok": ok,
        "message": summary,
        "state": state,
        "record": record,
        "eval_metadata": eval_meta,
    }


class TestMergeAskAndK2(unittest.TestCase):
    def test_s1_both_ok_pass(self) -> None:
        merged = merge_ask_and_k2(
            _ask_stub(),
            _k2_stub(tags=[]),
            query="hello",
            top_k=3,
        )
        self.assertTrue(merged["ok"])
        self.assertEqual((merged["answer"] or {}).get("answer"), "rag:hello")
        merge = merged["k2_merge"]
        self.assertEqual(merge["primary_source"], "ask")
        self.assertEqual(merge["gate_result"], "pass")
        self.assertFalse(merge["ci_fail"])
        self.assertIn("k2_eval_metadata", merged)

    def test_s2_both_ok_review_tags(self) -> None:
        merged = merge_ask_and_k2(
            _ask_stub(),
            _k2_stub(tags=["high_retry", "retrieve_retry"]),
            query="hello",
            top_k=3,
        )
        self.assertTrue(merged["ok"])
        merge = merged["k2_merge"]
        self.assertEqual(merge["gate_result"], "needs_review")
        self.assertFalse(merge["ci_fail"])
        self.assertIn("high_retry", merge["k2_eval_tags"])

    def test_s3_both_ok_infra_risk_fails(self) -> None:
        merged = merge_ask_and_k2(
            _ask_stub(),
            _k2_stub(tags=["infra_risk"]),
            query="hello",
            top_k=3,
        )
        self.assertFalse(merged["ok"])
        self.assertEqual((merged["answer"] or {}).get("answer"), "rag:hello")
        merge = merged["k2_merge"]
        self.assertEqual(merge["gate_result"], "fail")
        self.assertTrue(merge["ci_fail"])
        self.assertIn("infra_risk", merge["k2_severe_tags"])
        errors = merged.get("errors") or []
        self.assertTrue(any("severe_eval" in str(e) for e in errors))

    def test_s4_ask_ok_k2_fail(self) -> None:
        merged = merge_ask_and_k2(
            _ask_stub(),
            _k2_stub(ok=False, summary="k2 failed", error_type="tool_error"),
            query="hello",
            top_k=3,
        )
        self.assertTrue(merged["ok"])
        merge = merged["k2_merge"]
        self.assertEqual(merge["decision"], "ask_ok_k2_fail_use_ask")
        self.assertEqual(merge["gate_result"], "needs_review")
        self.assertFalse(merged.get("k2_eval_metadata"))

    def test_s5_ask_fail_k2_ok_conservative(self) -> None:
        merged = merge_ask_and_k2(
            _ask_stub(ok=False, answer="", errors=["timeout"]),
            _k2_stub(ok=True, summary="k2 recovered"),
            query="hello",
            top_k=3,
        )
        self.assertFalse(merged["ok"])
        merge = merged["k2_merge"]
        self.assertTrue(merge["k2_recovered"])
        self.assertEqual(merge["decision"], "ask_fail_k2_ok_keep_ask_failure")
        self.assertEqual(merge["k2_answer_preview"], "k2 recovered")

    def test_s6_both_fail(self) -> None:
        merged = merge_ask_and_k2(
            _ask_stub(ok=False, errors=["timeout"]),
            _k2_stub(ok=False, error_type="timeout"),
            query="hello",
            top_k=3,
        )
        self.assertFalse(merged["ok"])
        merge = merged["k2_merge"]
        self.assertEqual(merge["gate_result"], "fail")
        self.assertTrue(merge["ci_fail"])
        self.assertEqual(merge["k2_error_type"], "timeout")
        errors = merged.get("errors") or []
        self.assertIn("timeout", errors)

    def test_s7_answer_mismatch_preview_in_meta(self) -> None:
        merged = merge_ask_and_k2(
            _ask_stub(answer="rag:query"),
            _k2_stub(summary="agent succeeded"),
            query="hello",
            top_k=3,
        )
        self.assertEqual((merged["answer"] or {}).get("answer"), "rag:query")
        self.assertEqual(merged["k2_merge"]["k2_answer_preview"], "agent succeeded")

    def test_include_eval_false_omits_eval_metadata(self) -> None:
        merged = merge_ask_and_k2(
            _ask_stub(),
            _k2_stub(tags=["high_retry"]),
            query="hello",
            top_k=3,
            include_eval_in_envelope=False,
        )
        self.assertNotIn("k2_eval_metadata", merged)
        self.assertIn("k2_merge", merged)

    def test_ask_envelope_shape_preserved(self) -> None:
        merged = merge_ask_and_k2(_ask_stub(), _k2_stub(), query="hello", top_k=3)
        for key in ("mode", "query", "top_k", "ok", "message", "answer", "errors", "executed_nodes"):
            self.assertIn(key, merged)
        self.assertEqual(merged["mode"], "ask")

    def test_severe_tags_constant(self) -> None:
        self.assertIn("infra_risk", SEVERE_EVAL_TAGS)


class TestMergeShadowIntegration(unittest.TestCase):
    """Synthetic shadow path: ask + k2 stubs → merge (no LangGraph)."""

    def test_shadow_merge_pipeline(self) -> None:
        ask_out = _ask_stub(answer="direct:你好")
        k2_out = _k2_stub(summary="agent succeeded", tags=["infra_risk"])
        merged = merge_ask_and_k2(ask_out, k2_out, query="你好", top_k=2)
        self.assertFalse(merged["ok"])
        self.assertEqual(merged["k2_merge"]["primary_source"], "ask")
        self.assertIn("k2_metrics_record", merged)


if __name__ == "__main__":
    unittest.main()
