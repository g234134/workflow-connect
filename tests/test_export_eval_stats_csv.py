"""Tests for tools.export_eval_stats_csv (W5-D-ARTEFACT-CSV-EXPORTER-01)."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.export_eval_stats_csv import UNIFIED_COLUMNS, export_eval_stats_csv

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "eval"
_EVAL_SAMPLE = _FIXTURES / "eval_export_sample.jsonl"


class TestExportEvalStatsCsv(unittest.TestCase):
    def _write_dryrun_jsonl(self, path: Path) -> None:
        rows = [
            {
                "task_id": "t-dry-1",
                "trace_id": "tr-dry-1",
                "actual_verdict": "allow",
                "ideal_verdict": "allow",
                "verdict_match": True,
                "dryrun_rule": "gate_ok_score_high",
                "gate_result": "pass",
                "tags": ["high_retry"],
                "metrics": {
                    "success": True,
                    "retry_count": 2,
                    "trace_completeness_score": 0.91,
                },
            },
        ]
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8",
        )

    def test_csv_headers_and_row_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dryrun_path = root / "20260531T120000Z_per_record.jsonl"
            self._write_dryrun_jsonl(dryrun_path)
            out_path = root / "eval_stats.csv"

            result = export_eval_stats_csv(
                [_EVAL_SAMPLE, dryrun_path],
                out_path,
            )
            self.assertTrue(result["ok"])
            self.assertGreaterEqual(result["written"], 4)

            with out_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, list(UNIFIED_COLUMNS))
                rows = list(reader)

        eval_rows = [r for r in rows if r["source_kind"] == "eval_export"]
        dry_rows = [r for r in rows if r["source_kind"] == "dryrun"]
        self.assertEqual(len(eval_rows), 3)
        self.assertEqual(len(dry_rows), 1)

        infra = next(r for r in eval_rows if r["task_id"] == "t-infra")
        self.assertEqual(infra["tags"], "infra_risk")
        self.assertEqual(infra["gate_result"], "needs_review")
        self.assertEqual(infra["actual_verdict"], "fail")
        self.assertEqual(infra["score"], "0.95")

        healthy = next(r for r in eval_rows if r["task_id"] == "t-healthy")
        self.assertEqual(healthy["tags"], "")
        self.assertEqual(healthy["actual_verdict"], "allow")

        dry = dry_rows[0]
        self.assertEqual(dry["task_id"], "t-dry-1")
        self.assertEqual(dry["ideal_verdict"], "allow")
        self.assertEqual(dry["actual_verdict"], "allow")
        self.assertEqual(dry["tags"], "high_retry")
        self.assertEqual(dry["dryrun_rule"], "gate_ok_score_high")
        self.assertEqual(dry["score"], "0.91")
        self.assertEqual(dry["enf_rule_hits"], "")


if __name__ == "__main__":
    unittest.main()
