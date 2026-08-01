"""Unit tests for observability/eval_stats (P-line distribution analysis)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from observability.eval_stats import (
    analyze_export_files,
    build_stats_summary,
    format_text_report,
    iter_export_lines,
    suggest_ci_thresholds,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "eval"
_SAMPLE = _FIXTURES / "eval_export_sample.jsonl"


class TestEvalStats(unittest.TestCase):
    def test_sample_counts_match_hand_calculation(self) -> None:
        result = analyze_export_files([_SAMPLE], min_samples_for_recommendations=1)
        self.assertTrue(result["ok"])
        overall = result["stats"]["overall"]
        self.assertEqual(overall["total"], 3)
        self.assertEqual(overall["needs_review_count"], 2)
        self.assertAlmostEqual(overall["needs_review_ratio"], 2 / 3, places=4)
        self.assertEqual(overall["tag_counts"]["infra_risk"], 1)
        self.assertEqual(overall["tag_counts"]["high_retry"], 1)

    def test_empty_file_insufficient_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.jsonl"
            empty.write_text("", encoding="utf-8")
            result = analyze_export_files([empty])
        self.assertFalse(result["ok"])
        self.assertEqual(result["stats"]["overall"]["total"], 0)
        self.assertEqual(result["recommendations"]["confidence"], "none")

    def test_small_sample_provisional_recommendations(self) -> None:
        result = analyze_export_files([_SAMPLE], min_samples_for_recommendations=10)
        self.assertTrue(result["ok"])
        self.assertFalse(result["stats"]["sufficient_for_recommendations"])
        self.assertEqual(result["recommendations"]["confidence"], "low")
        sr = result["recommendations"]["max_needs_review_ratio"]["suggested_range"]
        self.assertEqual(len(sr), 2)
        self.assertGreaterEqual(sr[1], sr[0])

    def test_missing_file_fails(self) -> None:
        result = analyze_export_files([Path("nonexistent_eval.jsonl")])
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["message"])

    def test_group_by_date(self) -> None:
        result = analyze_export_files([_SAMPLE], group_by="date")
        groups = result["stats"]["groups"]
        self.assertIn("2026-05-23", groups)
        self.assertEqual(groups["2026-05-23"]["total"], 3)

    def test_suggest_ci_infra_risk_fail(self) -> None:
        overall = {
            "total": 3,
            "needs_review_count": 2,
            "needs_review_ratio": 0.6667,
            "tag_counts": {"infra_risk": 1, "high_retry": 1},
            "tag_rates": {"infra_risk": 0.3333, "high_retry": 0.3333},
            "other_tags": [],
        }
        rec = suggest_ci_thresholds(overall, min_samples_for_recommendations=1)
        fail_tags = [x["tag"] for x in rec["fail_on_tags"] if x["action"] == "fail"]
        self.assertIn("infra_risk", fail_tags)

    def test_build_stats_summary_flat_schema(self) -> None:
        result = analyze_export_files([_SAMPLE], min_samples_for_recommendations=1)
        summary = build_stats_summary(result)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["sample_count"], 3)
        self.assertAlmostEqual(summary["needs_review_ratio"], 2 / 3, places=4)
        self.assertIn("infra_risk", summary["tag_counts"])
        st = summary["suggested_thresholds"]
        self.assertIn("max_needs_review_ratio_range", st)
        self.assertIn("fail_on_tags", st)
        self.assertIn("infra_risk", st["fail_on_tags"])

    def test_format_text_report_serializable(self) -> None:
        result = analyze_export_files([_SAMPLE], min_samples_for_recommendations=1)
        text = format_text_report(result)
        self.assertIn("needs_review", text)
        json.dumps(result)

    def test_iter_export_lines(self) -> None:
        rows = list(iter_export_lines(_SAMPLE))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0][0]["schema_version"], "eval_export/v1")


if __name__ == "__main__":
    unittest.main()
