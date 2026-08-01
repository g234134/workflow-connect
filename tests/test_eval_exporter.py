"""Unit tests for observability/eval_exporter (P+ export)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from observability.eval_exporter import (
    KB_INDEX_EXPORT_ENV,
    SCHEMA_VERSION,
    build_export_line,
    export_eval_jsonl,
    iter_records,
    load_case_index_map,
    resolve_kb_index_context,
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

    def test_kb_index_flag_off_omits_fields(self) -> None:
        record = _healthy_record()
        record["metadata"] = {"kb_index_status": "ready"}
        line = build_export_line(record, include_kb_index=False)
        self.assertNotIn("kb_index_status", line)
        self.assertNotIn("kb_index_job_id", line)

    def test_kb_index_flag_on_from_metadata(self) -> None:
        record = _healthy_record()
        record["metadata"] = {
            "kb_index_status": "ready",
            "kb_index_job_id": "job-abc",
        }
        line = build_export_line(record, include_kb_index=True)
        self.assertEqual(line["kb_index_status"], "ready")
        self.assertEqual(line["kb_index_job_id"], "job-abc")

    def test_kb_index_priority_selector_hints_after_metadata(self) -> None:
        record = _healthy_record()
        record["metadata"] = {"kb_index_status": "ready"}
        record["selector_hints"] = {"kb_index_status": "stale"}
        ctx = resolve_kb_index_context(record)
        self.assertEqual(ctx["kb_index_status"], "ready")

    def test_kb_index_case_index_map_fallback(self) -> None:
        record = _healthy_record()
        record["case_id"] = "W2-1"
        case_map = load_case_index_map(_FIXTURES / "case_index_map_W2-1.json")
        ctx = resolve_kb_index_context(record, case_index_map=case_map)
        self.assertEqual(ctx["kb_index_status"], "ready")
        self.assertEqual(ctx["kb_index_job_id"], "repo_index_v1_job__W2-1__wave_b_gov_scope")

    def test_export_jsonl_kb_index_env_on(self) -> None:
        with mock.patch.dict(os.environ, {KB_INDEX_EXPORT_ENV: "1"}, clear=False):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "eval_kb.jsonl"
                result = export_eval_jsonl(_FIXTURES / "ibridge_records.jsonl", out)
                self.assertTrue(result["ok"])
                self.assertTrue(result["kb_index_export_enabled"])
                lines = [json.loads(ln) for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
        infra_line = next(row for row in lines if row["task_id"] == "t-infra")
        self.assertEqual(infra_line["kb_index_status"], "ready")
        self.assertEqual(infra_line["kb_index_job_id"], "repo_index_v1_job__W2-1__wave_b_gov_scope")
        healthy_line = next(row for row in lines if row["task_id"] == "t-healthy")
        self.assertIn("kb_index_status", healthy_line)
        self.assertIsNone(healthy_line["kb_index_status"])

    def test_export_jsonl_kb_index_env_off_unchanged(self) -> None:
        with mock.patch.dict(os.environ, {KB_INDEX_EXPORT_ENV: "0"}, clear=False):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "eval_plain.jsonl"
                export_eval_jsonl(_FIXTURES / "ibridge_records.jsonl", out)
                lines = [json.loads(ln) for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
        for row in lines:
            self.assertNotIn("kb_index_status", row)
            self.assertNotIn("kb_index_job_id", row)


if __name__ == "__main__":
    unittest.main()
