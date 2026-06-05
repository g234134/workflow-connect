"""Unit tests for observability/eval_exporter (P+ export)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from observability.eval_exporter import (
    SCHEMA_VERSION,
    build_export_line,
    export_eval_jsonl,
    iter_records,
)
from observability.eval_gate import CONTEXT_HEAVY_TOKEN_THRESHOLD

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "eval"


def _healthy_record() -> dict:
    return {
        "task_id": "t-1",
        "trace_id": "tr-1",
        "end_time": "2026-05-23T12:00:00Z",
        "success": True,
        "retry_count": 0,
        "handoff_count": 0,
        "error_type": None,
        "context_token_usage": {"total_tokens": 1000},
        "trace_completeness": {"score": 0.95},
    }


class TestEvalExporter(unittest.TestCase):
    def test_build_export_line_pass(self) -> None:
        line = build_export_line(_healthy_record(), line_index=1)
        self.assertEqual(line["schema_version"], SCHEMA_VERSION)
        self.assertEqual(line["gate_result"], "pass")
        self.assertEqual(line["tags"], [])
        self.assertEqual(line["task_id"], "t-1")
        self.assertEqual(line["metrics"]["retry_count"], 0)
        self.assertEqual(line["metrics"]["context_tokens_total"], 1000)
        self.assertEqual(line["source_ref"]["line_index"], 1)

    def test_build_export_line_needs_review(self) -> None:
        record = _healthy_record()
        record["retry_count"] = 2
        line = build_export_line(record)
        self.assertEqual(line["gate_result"], "needs_review")
        self.assertIn("high_retry", line["tags"])
        self.assertTrue(line["reasons"])

    def test_unwrap_ibridge_record_key(self) -> None:
        wrapped = {"ibridge_record": _healthy_record(), "ok": True}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapped.jsonl"
            path.write_text(json.dumps(wrapped) + "\n", encoding="utf-8")
            records = list(iter_records(path))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][0]["task_id"], "t-1")

    def test_export_jsonl_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "eval_results.jsonl"
            result = export_eval_jsonl(_FIXTURES / "ibridge_records.jsonl", out)
            self.assertTrue(result["ok"])
            self.assertEqual(result["total_read"], 3)
            self.assertEqual(result["written"], 3)

            lines = [json.loads(ln) for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0]["gate_result"], "pass")
        self.assertEqual(lines[1]["gate_result"], "needs_review")
        self.assertIn("infra_risk", lines[2]["tags"])
        for row in lines:
            self.assertEqual(row["schema_version"], SCHEMA_VERSION)
            self.assertIn("metrics", row)

    def test_export_filter_needs_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "filtered.jsonl"
            result = export_eval_jsonl(
                _FIXTURES / "ibridge_records.jsonl",
                out,
                gate_filter="needs_review",
            )
            self.assertEqual(result["written"], 2)
            self.assertEqual(result["skipped_filter"], 1)
            lines = out.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        for ln in lines:
            row = json.loads(ln)
            self.assertEqual(row["gate_result"], "needs_review")

    def test_context_heavy_summary(self) -> None:
        record = _healthy_record()
        record["context_token_usage"] = {
            "total_tokens": CONTEXT_HEAVY_TOKEN_THRESHOLD + 1,
        }
        line = build_export_line(record)
        self.assertEqual(line["gate_result"], "needs_review")
        self.assertIn("context_heavy", line["tags"])
        self.assertGreater(
            line["metrics"]["context_tokens_total"],
            CONTEXT_HEAVY_TOKEN_THRESHOLD,
        )


if __name__ == "__main__":
    unittest.main()
