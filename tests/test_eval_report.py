"""Unit tests for observability/eval_report (Wave B eval gate report bootstrap)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from observability.eval_report import (
    REPORT_JSON_NAME,
    REPORT_MD_NAME,
    build_report_summary,
    format_markdown_report,
    write_eval_report,
)
from observability.eval_stats import analyze_export_files, compute_index_context_breakdown

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "eval" / "eval_export_sample.jsonl"


class TestEvalReport(unittest.TestCase):
    def test_build_report_summary_shape(self) -> None:
        analysis = analyze_export_files([_FIXTURE], min_samples_for_recommendations=1)
        summary = build_report_summary(analysis)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["sample_count"], 3)
        self.assertAlmostEqual(summary["needs_review_ratio"], 2 / 3, places=4)
        self.assertIn("infra_risk", summary["tag_counts"])
        self.assertIn("suggested_thresholds", summary)
        self.assertIn("reproduce_command", summary)

    def test_write_eval_report_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = write_eval_report([_FIXTURE], out, min_samples=1)
            self.assertTrue(result["ok"])
            self.assertEqual(result["sample_count"], 3)
            json_path = out / REPORT_JSON_NAME
            md_path = out / REPORT_MD_NAME
            self.assertTrue(json_path.is_file())
            self.assertTrue(md_path.is_file())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("summary", payload)
            self.assertIn("analysis", payload)
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Executive summary", md_text)
            self.assertIn("Reproduce", md_text)
            self.assertIn("needs_review", md_text)

    def test_markdown_includes_top_tags(self) -> None:
        analysis = analyze_export_files([_FIXTURE], min_samples_for_recommendations=1)
        summary = build_report_summary(analysis)
        md = format_markdown_report(summary, analysis)
        self.assertIn("infra_risk", md)
        self.assertIn("high_retry", md)

    def test_empty_export_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.jsonl"
            empty.write_text("", encoding="utf-8")
            out = Path(tmp) / "out"
            result = write_eval_report([empty], out)
            self.assertFalse(result["ok"])
            self.assertEqual(result["sample_count"], 0)

    def test_index_context_breakdown_on_fixture(self) -> None:
        breakdown = compute_index_context_breakdown([_FIXTURE])
        self.assertEqual(breakdown["rows_with_kb_index_status"], 1)
        buckets = {b["kb_index_status"]: b for b in breakdown["buckets"]}
        self.assertIn("ready", buckets)
        self.assertEqual(buckets["ready"]["sample_count"], 1)
        self.assertEqual(buckets["ready"]["needs_review_count"], 1)
        self.assertIn("not_set", {b["kb_index_status"] for b in breakdown["buckets"]})

    def test_report_summary_includes_index_context(self) -> None:
        analysis = analyze_export_files([_FIXTURE], min_samples_for_recommendations=1)
        summary = build_report_summary(analysis, export_paths=[_FIXTURE])
        self.assertIn("index_context_breakdown", summary)
        self.assertTrue(summary["index_context_breakdown"]["observability_only"])

    def test_markdown_includes_index_context_section(self) -> None:
        analysis = analyze_export_files([_FIXTURE], min_samples_for_recommendations=1)
        summary = build_report_summary(analysis, export_paths=[_FIXTURE])
        md = format_markdown_report(summary, analysis)
        self.assertIn("### Index context", md)
        self.assertIn("Observability only", md)
        self.assertIn("`ready`", md)


if __name__ == "__main__":
    unittest.main()
