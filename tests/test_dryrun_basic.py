"""Unit tests for tools.dryrun (read-only CLI; mock inputs only)."""

from __future__ import annotations

import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

from tools.dryrun import (
    build_comparison_rows,
    compute_ideal_verdict,
    map_actual_verdict,
    verdicts_match,
)
from tools.dryrun.__main__ import main
from tools.dryrun.core import (
    DISCLAIMER,
    _normalize_export_row,
    discover_input_paths,
    load_records_from_paths,
)
from tools.dryrun.output import emit_reports


class TestDryrunRules(unittest.TestCase):
    def test_gate_ok_score_high(self) -> None:
        record = {
            "task_id": "t-high",
            "gate_result": "pass",
            "tags": [],
            "metrics": {"success": True, "trace_completeness_score": 0.95},
        }
        ideal, rule = compute_ideal_verdict(record, min_score=0.875)
        self.assertEqual(ideal, "allow")
        self.assertEqual(rule, "gate_ok_score_high")
        self.assertEqual(map_actual_verdict(record), "allow")
        self.assertTrue(verdicts_match("allow", "allow"))

    def test_gate_ok_score_low(self) -> None:
        record = {
            "task_id": "t-low",
            "gate_result": "pass",
            "tags": [],
            "metrics": {"success": True, "trace_completeness_score": 0.85},
        }
        ideal, rule = compute_ideal_verdict(record, min_score=0.875)
        self.assertEqual(ideal, "warn")
        self.assertEqual(rule, "gate_ok_score_low")
        self.assertEqual(map_actual_verdict(record), "allow")
        self.assertFalse(verdicts_match("allow", "warn"))

    def test_gate_fail_deny(self) -> None:
        record = {
            "task_id": "t-deny",
            "gate_result": "needs_review",
            "tags": ["infra_risk"],
            "metrics": {"success": False, "error_type": "timeout"},
        }
        ideal, rule = compute_ideal_verdict(record)
        self.assertEqual(ideal, "deny")
        self.assertEqual(rule, "gate_fail_deny")
        self.assertEqual(map_actual_verdict(record), "fail")
        self.assertTrue(verdicts_match("fail", "deny"))

    def test_gate_fail_needs_review(self) -> None:
        record = {
            "task_id": "t-review",
            "gate_result": "needs_review",
            "tags": ["high_retry"],
            "metrics": {"success": True, "retry_count": 2, "trace_completeness_score": 0.9},
        }
        ideal, rule = compute_ideal_verdict(record)
        self.assertEqual(ideal, "warn")
        self.assertEqual(rule, "gate_fail_needs_review")
        self.assertEqual(map_actual_verdict(record), "warn")

    def test_edge_unknown(self) -> None:
        record = {"gate_result": "pass", "metrics": {}}
        ideal, rule = compute_ideal_verdict(record)
        self.assertEqual(ideal, "unknown")
        self.assertEqual(rule, "edge_unknown")


class TestNormalizeExportRowTags(unittest.TestCase):
    def _ibridge_row(self, **overrides: object) -> dict:
        base = {
            "task_id": "t-merge",
            "trace_id": "tr-merge",
            "success": True,
            "retry_count": 0,
            "handoff_count": 0,
            "error_type": None,
            "context_token_usage": {"total_tokens": 0},
            "trace_completeness": {"score": 1.0},
        }
        base.update(overrides)
        return base

    def test_case_a_original_tags_only(self) -> None:
        row = self._ibridge_row(tags=["infra_risk"])
        normalized = _normalize_export_row(row, source_file="ibridge.jsonl")
        self.assertEqual(normalized["tags"], ["infra_risk"])
        self.assertEqual(normalized["_synthetic_tags"], [])

    def test_case_b_synthetic_tags_only(self) -> None:
        row = self._ibridge_row(tags=[], retry_count=2)
        normalized = _normalize_export_row(row, source_file="ibridge.jsonl")
        self.assertEqual(normalized["tags"], ["high_retry"])
        self.assertEqual(normalized["_synthetic_tags"], ["high_retry"])

    def test_case_c_merge_original_and_synthetic_tags(self) -> None:
        row = self._ibridge_row(tags=["infra_risk"], retry_count=2)
        normalized = _normalize_export_row(row, source_file="ibridge.jsonl")
        self.assertEqual(normalized["tags"], ["high_retry", "infra_risk"])
        self.assertEqual(normalized["_synthetic_tags"], ["high_retry"])

    def test_merge_preserves_ideal_verdict(self) -> None:
        """Merged observability tags must not change ideal verdict vs synthetic-only."""
        row = self._ibridge_row(tags=["infra_risk"])
        normalized = _normalize_export_row(row, source_file="ibridge.jsonl")
        rows = build_comparison_rows([normalized])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tags"], ["infra_risk"])
        self.assertEqual(rows[0]["ideal_verdict"], "allow")
        self.assertEqual(rows[0]["dryrun_rule"], "gate_ok_score_high")


class TestDryrunCli(unittest.TestCase):
    def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8",
        )

    def test_cli_emits_required_fields(self) -> None:
        rows_data = [
            {
                "schema_version": "eval_export/v1",
                "task_id": "t-healthy",
                "trace_id": "tr-1",
                "gate_result": "pass",
                "tags": [],
                "reasons": [],
                "metrics": {
                    "success": True,
                    "retry_count": 0,
                    "handoff_count": 0,
                    "trace_completeness_score": 0.95,
                },
            },
            {
                "schema_version": "eval_export/v1",
                "task_id": "t-infra",
                "trace_id": "tr-3",
                "gate_result": "needs_review",
                "tags": ["infra_risk"],
                "reasons": ["error_type=timeout"],
                "metrics": {
                    "success": False,
                    "retry_count": 0,
                    "handoff_count": 0,
                    "error_type": "timeout",
                    "trace_completeness_score": 0.95,
                },
            },
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "eval"
            output_dir = root / "out"
            input_dir.mkdir()
            self._write_jsonl(input_dir / "shadow_eval_results.latest.jsonl", rows_data)

            stdout = StringIO()
            with mock.patch("sys.stdout", stdout):
                code = main(
                    [
                        "--input-dir",
                        str(input_dir),
                        "--output-dir",
                        str(output_dir),
                        "--min-score",
                        "0.875",
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn(DISCLAIMER, stdout.getvalue())

            jsonl_files = list(output_dir.glob("*_per_record.jsonl"))
            md_files = list(output_dir.glob("*_summary.md"))
            self.assertEqual(len(jsonl_files), 1)
            self.assertEqual(len(md_files), 1)

            loaded = [
                json.loads(line)
                for line in jsonl_files[0].read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(loaded), 2)
            for row in loaded:
                for key in (
                    "task_id",
                    "actual_verdict",
                    "ideal_verdict",
                    "verdict_match",
                    "dryrun_rule",
                ):
                    self.assertIn(key, row)

            summary = md_files[0].read_text(encoding="utf-8")
            self.assertIn(DISCLAIMER, summary)
            self.assertIn("Total records", summary)

    def test_discover_and_build_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "shadow_eval_results.latest.jsonl"
            self._write_jsonl(
                path,
                [
                    {
                        "schema_version": "eval_export/v1",
                        "task_id": "only-one",
                        "gate_result": "pass",
                        "tags": [],
                        "metrics": {"success": True, "trace_completeness_score": 0.99},
                    }
                ],
            )
            discovered = discover_input_paths(root)
            self.assertIn(path, discovered)
            records, _agg = load_records_from_paths(discovered)
            rows = build_comparison_rows(records)
            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0]["verdict_match"])


if __name__ == "__main__":
    unittest.main()
