"""Unit tests for observability/ibridge_exporter (P-line real data export)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from metrics import get_collector, reset_collector
from observability.eval_exporter import export_eval_jsonl, iter_records
from observability.ibridge_exporter import (
    export_allowed,
    export_ibridge_jsonl,
    normalize_ibridge_record,
    normalize_shadow_record,
    validate_normalized_record,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "eval"


def _sample_metrics_record(task_id: str = "task-export-1") -> dict:
    return {
        "task_id": task_id,
        "trace_id": f"trace-{task_id}",
        "agent_name": "ask_pipeline",
        "start_time": "2026-05-23T09:00:00Z",
        "end_time": "2026-05-23T10:00:00Z",
        "success": True,
        "retry_count": 1,
        "handoff_count": 0,
        "error_type": None,
        "context_token_usage": {"total_tokens": 1500},
        "trace_completeness": {"score": 0.92},
        "step_count": 2,
    }


class TestIbridgeExporter(unittest.TestCase):
    def setUp(self) -> None:
        reset_collector()

    def tearDown(self) -> None:
        reset_collector()

    def test_normalize_unwraps_ibridge_record(self) -> None:
        inner = _sample_metrics_record()
        wrapped = {"ok": True, "ibridge_record": inner}
        out = normalize_ibridge_record(wrapped)
        self.assertEqual(out["task_id"], inner["task_id"])
        self.assertEqual(out["trace_id"], inner["trace_id"])
        self.assertEqual(out["context_token_usage"]["total_tokens"], 1500)

    def test_validate_normalized_record(self) -> None:
        rec = normalize_ibridge_record(_sample_metrics_record())
        self.assertTrue(validate_normalized_record(rec)["ok"])

    def test_export_blocked_in_production(self) -> None:
        gate = export_allowed(deploy_env="production")
        self.assertFalse(gate["allowed"])

    def test_export_from_file_matches_fixture_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "exported.jsonl"
            result = export_ibridge_jsonl(
                source="file",
                input_path=_FIXTURES / "ibridge_records.jsonl",
                output_path=out,
                force=True,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["written"], 3)

            for record, _idx in iter_records(out):
                self.assertTrue(validate_normalized_record(record)["ok"])
                eval_out = Path(tmp) / "eval.jsonl"
                export_result = export_eval_jsonl(out, eval_out)
                self.assertTrue(export_result["ok"])
                self.assertEqual(export_result["written"], 3)

    def test_export_from_collector(self) -> None:
        col = get_collector()
        col.start_task("task-export-1", "ask_pipeline")
        col.end_task("task-export-1", success=True)
        record = col.get_task("task-export-1")["record"]
        record["retry_count"] = 2
        record["context_token_usage"] = {"total_tokens": 2000}
        record["trace_completeness"] = {"score": 0.9}

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "from_collector.jsonl"
            result = export_ibridge_jsonl(
                source="collector",
                output_path=out,
                limit=10,
                force=True,
            )
            self.assertTrue(result["ok"])
            self.assertGreaterEqual(result["written"], 1)

            lines = [json.loads(ln) for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertTrue(any(row.get("task_id") == "task-export-1" for row in lines))

    def test_normalize_shadow_k2_flow_record(self) -> None:
        raw = {
            "ok": True,
            "record": {
                "task_id": "shadow-k2-flow-1",
                "trace_id": "tr-sk-1",
                "end_time": "2026-05-24T10:00:00Z",
                "success": True,
                "retry_count": 0,
                "handoff_count": 0,
                "error_type": None,
                "context_token_usage": {"total_tokens": 800},
                "trace_completeness": {"score": 0.95},
            },
        }
        out = normalize_shadow_record(raw)
        self.assertTrue(validate_normalized_record(out)["ok"])
        self.assertEqual(out["task_id"], "shadow-k2-flow-1")

    def test_normalize_shadow_k2_summary(self) -> None:
        raw = {
            "case_name": "shadow-retry",
            "end_time": "2026-05-24T10:03:00Z",
            "k2_summary": {
                "pipeline": "k2",
                "ok": True,
                "retry_count": 2,
                "handoff_count": 0,
                "error_type": None,
            },
        }
        out = normalize_shadow_record(raw)
        self.assertEqual(out["task_id"], "shadow-retry")
        self.assertEqual(out["retry_count"], 2)

    def test_k2_summary_tags_preserved_in_ibridge_record(self) -> None:
        raw = {
            "case_name": "shadow-tagged",
            "end_time": "2026-05-30T10:00:00Z",
            "k2_summary": {
                "pipeline": "k2",
                "ok": True,
                "retry_count": 0,
                "handoff_count": 0,
                "error_type": None,
                "tags": ["infra_risk", "foo"],
            },
        }
        out = normalize_shadow_record(raw)
        self.assertEqual(out["tags"], ["infra_risk", "foo"])

    def test_k2_summary_missing_tags_defaults_to_empty_list(self) -> None:
        raw = {
            "case_name": "shadow-no-tags",
            "end_time": "2026-05-30T10:01:00Z",
            "k2_summary": {
                "pipeline": "k2",
                "ok": True,
                "retry_count": 0,
                "handoff_count": 0,
                "error_type": None,
            },
        }
        out = normalize_shadow_record(raw)
        self.assertEqual(out["tags"], [])

    def test_export_shadow_source_writes_profile_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "shadow_ibridge_records.latest.jsonl"
            result = export_ibridge_jsonl(
                source="shadow",
                input_path=_FIXTURES / "shadow_raw_records.jsonl",
                output_path=out,
                profile="shadow",
                force=True,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["written"], 4)
            self.assertEqual(result["profile"], "shadow")

            for record, _idx in iter_records(out):
                self.assertTrue(validate_normalized_record(record)["ok"])
                eval_out = Path(tmp) / "eval.jsonl"
                export_result = export_eval_jsonl(out, eval_out)
                self.assertTrue(export_result["ok"])
                lines = eval_out.read_text(encoding="utf-8").strip().splitlines()
                for line in lines:
                    row = json.loads(line)
                    self.assertIn(row["gate_result"], ("pass", "needs_review"))


if __name__ == "__main__":
    unittest.main()
