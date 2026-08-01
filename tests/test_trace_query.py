"""Unit tests for observability/trace_query (Wave B trace lookup CLI)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from observability.trace_query import format_text_result, format_triage_result, query_traces

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "trace" / "sample_traces.jsonl"


class TestTraceQuery(unittest.TestCase):
    def test_query_by_trace_id(self) -> None:
        result = query_traces(_FIXTURE, trace_id="trace-wb-fixture-001")
        self.assertTrue(result["ok"])
        self.assertEqual(result["matches"], 3)
        events = result["events"]
        self.assertEqual(events[0]["event"], "trace_start")
        self.assertEqual(events[-1]["event"], "trace_end")

    def test_query_by_task_id(self) -> None:
        result = query_traces(_FIXTURE, task_id="task-wb-002", limit=10)
        self.assertTrue(result["ok"])
        self.assertEqual(result["matches"], 2)
        self.assertEqual(result["summary"]["event_counts"]["trace_end"], 1)

    def test_query_by_session_id(self) -> None:
        result = query_traces(_FIXTURE, session_id="sess-wb-001")
        self.assertTrue(result["ok"])
        self.assertEqual(result["matches"], 3)
        self.assertEqual(result["events"][0]["session_id"], "sess-wb-001")
        self.assertEqual(result["summary"]["trace_ids"], ["trace-wb-fixture-001"])

    def test_missing_id_zero_matches(self) -> None:
        result = query_traces(_FIXTURE, trace_id="does-not-exist")
        self.assertTrue(result["ok"])
        self.assertEqual(result["matches"], 0)
        self.assertIn("no matching", result["message"])

    def test_missing_file_ok_false(self) -> None:
        result = query_traces(Path("nonexistent_traces.jsonl"), trace_id="x")
        self.assertFalse(result["ok"])
        self.assertEqual(result["matches"], 0)

    def test_no_filter_ok_false(self) -> None:
        result = query_traces(_FIXTURE)
        self.assertFalse(result["ok"])

    def test_event_filter(self) -> None:
        result = query_traces(_FIXTURE, event="span_end", limit=5)
        self.assertTrue(result["ok"])
        self.assertEqual(result["matches"], 1)
        self.assertEqual(result["events"][0]["tool_name"], "retrieve")

    def test_format_text_serializable(self) -> None:
        result = query_traces(_FIXTURE, trace_id="trace-wb-fixture-001")
        text = format_text_result(result)
        self.assertIn("trace_start", text)
        json.dumps(result)

    def test_invalid_json_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.jsonl"
            bad.write_text("{not json\n", encoding="utf-8")
            result = query_traces(bad, trace_id="x")
            self.assertFalse(result["ok"])
            self.assertIn("invalid JSON", result["message"])

    def test_summary_kb_index_status_from_metadata(self) -> None:
        result = query_traces(_FIXTURE, trace_id="tr-3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"].get("kb_index_status"), "ready")

    def test_format_triage_result(self) -> None:
        result = query_traces(_FIXTURE, trace_id="tr-3")
        text = format_triage_result(result)
        self.assertIn("trace_id=tr-3", text)
        self.assertIn("audit_tags=", text)
        self.assertIn("hook:W3-B-SELECTOR-HOOK", text)

    def test_triage_format_omits_kb_index_when_absent(self) -> None:
        result = query_traces(_FIXTURE, trace_id="trace-wb-fixture-001")
        self.assertTrue(result["ok"])
        self.assertNotIn("kb_index_status", result["summary"])


if __name__ == "__main__":
    unittest.main()
