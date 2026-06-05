"""Unit tests for observability/eval_gate (P+ v0.1)."""

from __future__ import annotations

import unittest

from observability.eval_gate import (
    CONTEXT_HEAVY_TOKEN_THRESHOLD,
    evaluate_task_record,
)


def _healthy_record() -> dict:
    return {
        "success": True,
        "error_type": None,
        "retry_count": 0,
        "handoff_count": 0,
        "context_token_usage": {"total_tokens": 1_000},
        "trace_completeness": {"score": 0.95},
    }


class TestEvalGate(unittest.TestCase):
    def test_healthy_record_passes(self) -> None:
        out = evaluate_task_record(_healthy_record())
        self.assertTrue(out["pass"])
        self.assertEqual(out["tags"], [])
        self.assertEqual(out["reasons"], [])

    def test_high_retry(self) -> None:
        record = _healthy_record()
        record["retry_count"] = 2
        out = evaluate_task_record(record)
        self.assertFalse(out["pass"])
        self.assertIn("high_retry", out["tags"])
        self.assertTrue(any("retry_count" in r for r in out["reasons"]))

    def test_context_heavy(self) -> None:
        record = _healthy_record()
        record["context_token_usage"] = {
            "total_tokens": CONTEXT_HEAVY_TOKEN_THRESHOLD + 1,
        }
        out = evaluate_task_record(record)
        self.assertFalse(out["pass"])
        self.assertIn("context_heavy", out["tags"])

    def test_many_handoffs(self) -> None:
        record = _healthy_record()
        record["handoff_count"] = 3
        out = evaluate_task_record(record)
        self.assertFalse(out["pass"])
        self.assertIn("many_handoffs", out["tags"])

    def test_infra_risk_context_overflow(self) -> None:
        record = _healthy_record()
        record["error_type"] = "context_overflow"
        out = evaluate_task_record(record)
        self.assertFalse(out["pass"])
        self.assertIn("infra_risk", out["tags"])

    def test_infra_risk_timeout(self) -> None:
        record = _healthy_record()
        record["error_type"] = "timeout"
        out = evaluate_task_record(record)
        self.assertFalse(out["pass"])
        self.assertIn("infra_risk", out["tags"])

    def test_observability_gap(self) -> None:
        record = _healthy_record()
        record["trace_completeness"] = {"score": 0.75}
        out = evaluate_task_record(record)
        self.assertFalse(out["pass"])
        self.assertIn("observability_gap", out["tags"])

    def test_multiple_tags(self) -> None:
        record = _healthy_record()
        record["retry_count"] = 3
        record["handoff_count"] = 5
        out = evaluate_task_record(record)
        self.assertFalse(out["pass"])
        self.assertIn("high_retry", out["tags"])
        self.assertIn("many_handoffs", out["tags"])
        self.assertEqual(len(out["tags"]), len(out["reasons"]))

    def test_invalid_record_type(self) -> None:
        out = evaluate_task_record([])  # type: ignore[arg-type]
        self.assertFalse(out["pass"])
        self.assertIn("invalid_record", out["tags"])


if __name__ == "__main__":
    unittest.main()
