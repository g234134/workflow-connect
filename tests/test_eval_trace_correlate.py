"""Unit tests for observability/eval_trace_correlate (Wave B correlate CLI)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from observability.eval_trace_correlate import (
    build_triage_object,
    correlate_exports,
    extract_join_keys,
    extract_kb_index_status_from_eval_row,
    format_triage_markdown,
    is_flagged_row,
    is_needs_review_row,
    lookup_trace_events,
    build_trace_index,
)
from observability.trace_query import query_traces

_EVAL_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "eval" / "eval_export_sample.jsonl"
_TRACE_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "trace" / "sample_traces.jsonl"


class TestEvalTraceCorrelate(unittest.TestCase):
    def test_extract_join_keys_from_source_ref(self) -> None:
        row = {
            "trace_id": None,
            "task_id": "t-1",
            "source_ref": {"trace_id": "tr-from-ref", "task_id": "t-ref"},
        }
        keys = extract_join_keys(row)
        self.assertEqual(keys["trace_id"], "tr-from-ref")
        self.assertEqual(keys["task_id"], "t-1")

    def test_is_flagged_needs_review(self) -> None:
        self.assertTrue(is_flagged_row({"gate_result": "needs_review", "tags": []}))

    def test_is_flagged_fail_on_tag(self) -> None:
        self.assertTrue(
            is_flagged_row({"gate_result": "pass", "tags": ["infra_risk"]})
        )
        self.assertFalse(
            is_flagged_row({"gate_result": "pass", "tags": ["high_retry"]})
        )

    def test_correlate_flagged_with_trace_match(self) -> None:
        result = correlate_exports(_EVAL_FIXTURE, _TRACE_FIXTURE, only_flagged=True)
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["row_count"], 1)

        infra = next(
            (r for r in result["rows"] if r.get("task_id") == "t-infra"),
            None,
        )
        self.assertIsNotNone(infra)
        assert infra is not None
        self.assertTrue(infra["trace_found"])
        self.assertEqual(infra["join_key"], "trace_id")
        self.assertEqual(infra["join_value"], "tr-3")
        summary = infra["trace_summary"]
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertGreaterEqual(summary["event_count"], 2)
        self.assertEqual(summary["first_event"]["event"], "trace_start")
        self.assertEqual(summary["last_event"]["event"], "trace_end")
        self.assertEqual(summary["last_event"]["error_type"], "timeout")
        self.assertIsNotNone(summary.get("trace_completeness"))

    def test_correlate_missing_trace_no_crash(self) -> None:
        result = correlate_exports(_EVAL_FIXTURE, _TRACE_FIXTURE, only_flagged=True)
        self.assertTrue(result["ok"])

        retry = next(
            (r for r in result["rows"] if r.get("task_id") == "t-retry"),
            None,
        )
        self.assertIsNotNone(retry)
        assert retry is not None
        self.assertFalse(retry["trace_found"])
        self.assertIsNone(retry["trace_summary"])
        self.assertIn("no trace events", retry["message"])

    def test_only_flagged_excludes_pass_row(self) -> None:
        result = correlate_exports(_EVAL_FIXTURE, _TRACE_FIXTURE, only_flagged=True)
        task_ids = {r.get("task_id") for r in result["rows"]}
        self.assertNotIn("t-healthy", task_ids)

    def test_all_rows_when_only_flagged_off(self) -> None:
        result = correlate_exports(
            _EVAL_FIXTURE,
            _TRACE_FIXTURE,
            only_flagged=False,
            only_needs_review=False,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["row_count"], 3)

    def test_missing_trace_file_ok_false(self) -> None:
        result = correlate_exports(
            _EVAL_FIXTURE,
            Path("nonexistent_traces.jsonl"),
            only_flagged=True,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["rows"], [])

    def test_join_priority_trace_over_task(self) -> None:
        index = build_trace_index(_TRACE_FIXTURE)
        keys = {"trace_id": "tr-3", "task_id": "task-wb-002", "session_id": None}
        join_key, join_value, events = lookup_trace_events(index, keys)
        self.assertEqual(join_key, "trace_id")
        self.assertEqual(join_value, "tr-3")
        self.assertTrue(events)
        self.assertTrue(all(e.get("trace_id") == "tr-3" for e in events))

    def test_end_to_end_trace_query_verifies_match(self) -> None:
        result = correlate_exports(_EVAL_FIXTURE, _TRACE_FIXTURE, only_flagged=True)
        infra = next(r for r in result["rows"] if r.get("task_id") == "t-infra")
        trace_id = infra.get("trace_id")
        self.assertEqual(trace_id, "tr-3")

        trace_result = query_traces(_TRACE_FIXTURE, trace_id=trace_id)
        self.assertTrue(trace_result["ok"])
        self.assertGreater(trace_result["matches"], 0)
        self.assertEqual(
            trace_result["summary"]["event_counts"].get("trace_end"),
            infra["trace_summary"]["event_counts"].get("trace_end"),
        )

    def test_result_json_serializable(self) -> None:
        result = correlate_exports(_EVAL_FIXTURE, _TRACE_FIXTURE)
        json.dumps(result)

    def test_invalid_trace_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.jsonl"
            bad.write_text("{not json\n", encoding="utf-8")
            result = correlate_exports(_EVAL_FIXTURE, bad)
            self.assertFalse(result["ok"])

    def test_triage_subobject_stable_keys(self) -> None:
        result = correlate_exports(_EVAL_FIXTURE, _TRACE_FIXTURE)
        infra = next(r for r in result["rows"] if r.get("task_id") == "t-infra")
        triage = infra["triage"]
        self.assertEqual(set(triage.keys()), {"why_flagged", "primary_tags", "trace_ref", "kb_index_status"})
        self.assertEqual(triage["kb_index_status"], "ready")
        self.assertEqual(triage["why_flagged"], "error_type=timeout")
        self.assertTrue(triage["trace_ref"]["trace_found"])

    def test_triage_md_format_shows_gate_and_index(self) -> None:
        result = correlate_exports(_EVAL_FIXTURE, _TRACE_FIXTURE)
        md = format_triage_markdown(result)
        self.assertIn("eval flagged triage", md)
        self.assertIn("infra_risk", md)
        self.assertIn("error_type=timeout", md)
        self.assertIn("kb_index_status", md)
        self.assertIn("ready", md)
        self.assertIn("trace_id=tr-3", md)

    def test_kb_index_status_unknown_when_missing(self) -> None:
        row = {"gate_result": "needs_review", "tags": ["high_retry"]}
        self.assertEqual(extract_kb_index_status_from_eval_row(row), "unknown")
        triage = build_triage_object({**row, "join_key": None, "join_value": None, "trace_found": False})
        self.assertEqual(triage["kb_index_status"], "unknown")

    def test_only_needs_review_default_excludes_pass_infra_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "eval.jsonl"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": "eval_export/v1",
                        "gate_result": "pass",
                        "tags": ["infra_risk"],
                        "reasons": [],
                        "metrics": {},
                        "exported_at": "2026-06-05T00:00:00Z",
                        "trace_id": "tr-pass-infra",
                        "task_id": "t-pass-infra",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = correlate_exports(eval_path, _TRACE_FIXTURE)
            self.assertTrue(result["ok"])
            self.assertEqual(result["row_count"], 0)

    def test_no_only_needs_review_uses_only_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "eval.jsonl"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": "eval_export/v1",
                        "gate_result": "pass",
                        "tags": ["infra_risk"],
                        "reasons": [],
                        "metrics": {},
                        "exported_at": "2026-06-05T00:00:00Z",
                        "trace_id": "tr-pass-infra",
                        "task_id": "t-pass-infra",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = correlate_exports(
                eval_path,
                _TRACE_FIXTURE,
                only_needs_review=False,
                only_flagged=True,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["row_count"], 1)

    def test_is_needs_review_row(self) -> None:
        self.assertTrue(is_needs_review_row({"gate_result": "needs_review"}))
        self.assertFalse(is_needs_review_row({"gate_result": "pass", "tags": ["infra_risk"]}))

    def test_exporter_kb_index_sidecar_matches_eval_row(self) -> None:
        from observability.eval_exporter import build_export_line

        record = {
            "task_id": "t-infra",
            "trace_id": "tr-3",
            "metadata": {"kb_index_status": "ready"},
        }
        line = build_export_line(record, include_kb_index=True)
        self.assertEqual(line["kb_index_status"], "ready")
        self.assertEqual(line["source_ref"]["kb_index_status"], "ready")
        self.assertEqual(line["trace_metadata_sidecar"]["kb_index_status"], "ready")

        result = correlate_exports(_EVAL_FIXTURE, _TRACE_FIXTURE)
        infra = next(r for r in result["rows"] if r.get("task_id") == "t-infra")
        self.assertEqual(infra["triage"]["kb_index_status"], "ready")


if __name__ == "__main__":
    unittest.main()
