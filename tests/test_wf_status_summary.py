"""Unit tests for observability/wf_status_summary (WAVE-B-P3-WF-STATUS-SUMMARY-CLI)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from observability.wf_status_summary import (  # noqa: E402
    WF_STATUS_JSON_NAME,
    WF_STATUS_MD_NAME,
    build_gate_block,
    build_trace_join_stats,
    build_wf_status_summary,
    load_index_case,
    write_wf_status_summary,
)

_FIXTURE_EVAL = _REPO_ROOT / "tests/fixtures/eval/eval_export_sample.jsonl"
_FIXTURE_TRACE = _REPO_ROOT / "tests/fixtures/trace/sample_traces.jsonl"
_PILOT_INDEX = _REPO_ROOT / "workflow_v2/20_pilot/W3-B/index_status_W2-1.json"
_PILOT_CASE = _REPO_ROOT / "workflow_v2/20_pilot/W2-1_case/W2-1_case.md"


class TestWfStatusSummary(unittest.TestCase):
    def test_empty_export_gate_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.jsonl"
            empty.write_text("", encoding="utf-8")
            gate = build_gate_block(empty, min_samples=1)
            self.assertFalse(gate["ok"])
            self.assertEqual(gate["sample_count"], 0)

    def test_all_pass_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pass_only.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "eval_export/v1",
                        "trace_id": "tr-pass",
                        "task_id": "t-pass",
                        "gate_result": "pass",
                        "tags": [],
                        "reasons": [],
                        "metrics": {},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            summary = build_wf_status_summary(
                eval_path=path,
                index_status_paths=[_PILOT_INDEX],
                trace_path=_FIXTURE_TRACE,
            )
            self.assertTrue(summary["ok"])
            self.assertEqual(summary["gate"]["needs_review_count"], 0)
            self.assertEqual(summary["trace_join_stats"]["row_count"], 0)

    def test_fixture_has_needs_review(self) -> None:
        summary = build_wf_status_summary(
            eval_path=_FIXTURE_EVAL,
            index_status_paths=[_PILOT_INDEX],
            trace_path=_FIXTURE_TRACE,
            case_md=_PILOT_CASE,
        )
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["gate"]["sample_count"], 3)
        self.assertEqual(summary["gate"]["needs_review_count"], 2)
        self.assertAlmostEqual(summary["gate"]["needs_review_ratio"], 2 / 3, places=4)
        self.assertTrue(any(t["tag"] == "infra_risk" for t in summary["gate"]["top_tags"]))

    def test_index_missing_stub(self) -> None:
        missing = _REPO_ROOT / "nonexistent/index_status.json"
        row = load_index_case(missing)
        self.assertEqual(row["kb_index_status"], "unknown")
        self.assertEqual(row["index_file_status"], "missing")

    def test_trace_join_skipped_when_trace_missing(self) -> None:
        stats = build_trace_join_stats(
            _FIXTURE_EVAL,
            _REPO_ROOT / "nonexistent/trace.jsonl",
        )
        self.assertEqual(stats["status"], "skipped")
        self.assertEqual(stats["hit_rate"], "n/a")

    def test_full_fixture_stable_keys_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = write_wf_status_summary(
                eval_path=_FIXTURE_EVAL,
                index_status_paths=[_PILOT_INDEX],
                out_dir=out,
                trace_path=_FIXTURE_TRACE,
                case_md=_PILOT_CASE,
            )
            self.assertTrue(result["ok"])
            json_path = out / WF_STATUS_JSON_NAME
            md_path = out / WF_STATUS_MD_NAME
            self.assertTrue(json_path.is_file())
            self.assertTrue(md_path.is_file())

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            for key in ("ok", "gate", "index_cases", "trace_join_stats", "generated_at"):
                self.assertIn(key, payload)

            self.assertEqual(payload["index_cases"][0]["case_id"], "W2-1")
            self.assertEqual(payload["index_cases"][0]["kb_index_status"], "ready")
            self.assertEqual(payload["trace_join_stats"]["row_count"], 2)
            self.assertEqual(payload["trace_join_stats"]["trace_found_count"], 1)
            self.assertAlmostEqual(payload["trace_join_stats"]["hit_rate"], 0.5, places=4)

            md = md_path.read_text(encoding="utf-8")
            self.assertIn("Gate health", md)
            self.assertIn("Index readiness", md)
            self.assertIn("Trace join", md)
            self.assertIn("Reviewer shortcuts", md)
            self.assertIn("infra_risk", md)
            self.assertIn("ready", md)


if __name__ == "__main__":
    unittest.main()
