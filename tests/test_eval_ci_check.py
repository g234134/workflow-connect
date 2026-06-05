"""Unit tests for observability/eval_ci_check (P+ CI hook)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from observability.eval_ci_check import run_ci_check

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "eval"


class TestEvalCiCheck(unittest.TestCase):
    def test_within_threshold_on_fixture(self) -> None:
        report = run_ci_check(
            _FIXTURES / "ibridge_records.jsonl",
            limit=3,
            max_needs_review_ratio=0.9,
            min_samples=1,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["stats"]["sampled"], 3)
        self.assertEqual(report["stats"]["needs_review_count"], 2)

    def test_ratio_exceeded_fails(self) -> None:
        report = run_ci_check(
            _FIXTURES / "ibridge_records.jsonl",
            limit=3,
            max_needs_review_ratio=0.3,
            min_samples=1,
        )
        self.assertFalse(report["ok"])
        self.assertTrue(report["stats"]["ratio_triggered"])

    def test_fail_on_tags(self) -> None:
        report = run_ci_check(
            _FIXTURES / "ibridge_records.jsonl",
            limit=3,
            max_needs_review_ratio=1.0,
            min_samples=1,
            fail_on_tags=frozenset({"infra_risk"}),
        )
        self.assertFalse(report["ok"])
        self.assertTrue(report["stats"]["tag_triggered"])

    def test_limit_takes_last_n(self) -> None:
        report = run_ci_check(
            _FIXTURES / "ibridge_records.jsonl",
            limit=1,
            max_needs_review_ratio=1.0,
            min_samples=1,
        )
        self.assertEqual(report["stats"]["sampled"], 1)
        self.assertEqual(report["stats"]["needs_review_count"], 1)
        self.assertIn("infra_risk", report["stats"]["tag_counts"])

    def test_insufficient_samples_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.jsonl"
            empty.write_text("", encoding="utf-8")
            report = run_ci_check(empty, limit=10, min_samples=1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["stats"]["sampled"], 0)

    def test_report_json_serializable(self) -> None:
        report = run_ci_check(_FIXTURES / "ibridge_records.jsonl", limit=2, min_samples=1)
        encoded = json.dumps(report)
        self.assertIn("ok", encoded)


if __name__ == "__main__":
    unittest.main()
