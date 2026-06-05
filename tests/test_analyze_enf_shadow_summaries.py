"""Unit tests for tools.analyze_enf_shadow_summaries."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import mock

from tools.analyze_enf_shadow_summaries import (
    PREFIX,
    ShadowSummaryRow,
    generate_report,
    parse_line,
    parse_stream,
)

# ── helpers ────────────────────────────────────────────────────────────────

_SAMPLE_COMPLETE = {
    "mode": "shadow",
    "status": "ok",
    "exit_policy": "preview_only",
    "total": 120,
    "would_block": 3,
    "would_warn": 2,
    "would_noop": 115,
    "input": "nightly/2025-01-15_per_record.jsonl",
    "min_score": 0.7,
    "rules": {
        "ENF-RULE-1": {"would_block": 3},
        "ENF-RULE-2": {"would_warn": 2, "shadow_retries": 2},
        "C3-05-L1-INFRA-RISK-SUCCESS": {"would_warn": 0},
    },
    "samples": {
        "would_block": [
            {
                "task_id": "task-abc",
                "dryrun_rule": "gate_fail_deny",
                "gate_result": "deny",
                "error_type": "timeout",
                "tags": ["infra_risk"],
            },
            {
                "task_id": "task-def",
                "dryrun_rule": "gate_fail_deny",
                "gate_result": "deny",
                "error_type": "crash",
                "tags": ["security:critical"],
            },
        ],
    },
}

_SAMPLE_WARN_ONLY = {
    "mode": "shadow",
    "status": "ok",
    "exit_policy": "preview_only",
    "total": 50,
    "would_block": 0,
    "would_warn": 1,
    "would_noop": 49,
    "input": "nightly/2025-01-16_per_record.jsonl",
    "min_score": 0.7,
    "rules": {
        "ENF-RULE-1": {"would_block": 0},
        "ENF-RULE-2": {"would_warn": 1, "shadow_retries": 1},
        "C3-05-L1-INFRA-RISK-SUCCESS": {"would_warn": 0},
    },
}

_SAMPLE_SKIPPED = {
    "mode": "shadow",
    "status": "skipped",
    "exit_policy": "preview_only",
    "total": 0,
    "would_block": 0,
    "would_warn": 0,
    "would_noop": 0,
    "reason": "input_not_found",
}

_SAMPLE_WITH_BAD_LINE = """\
some garbage line
[GOV-ENF-SHADOW-SUMMARY] {"mode":"shadow","status":"ok","total":10,"would_block":1,"would_warn":0,"would_noop":9,"rules":{"ENF-RULE-1":{"would_block":1},"ENF-RULE-2":{"would_warn":0,"shadow_retries":0},"C3-05-L1-INFRA-RISK-SUCCESS":{"would_warn":0}}}
[GOV-ENF-SHADOW-SUMMARY] this is not json
[GOV-ENF-SHADOW-SUMMARY] {"mode":"shadow","status":"ok","total":20,"would_block":2,"would_warn":1,"would_noop":17,"rules":{"ENF-RULE-1":{"would_block":2},"ENF-RULE-2":{"would_warn":1,"shadow_retries":1},"C3-05-L1-INFRA-RISK-SUCCESS":{"would_warn":0}}}
invalid trailing
"""


def _prefix_line(payload: dict) -> str:
    return f"{PREFIX} {json.dumps(payload, separators=(',', ':'))}\n"


# ── parse_line ─────────────────────────────────────────────────────────────


class TestParseLine(unittest.TestCase):
    def test_valid_json_line(self) -> None:
        line = _prefix_line(_SAMPLE_COMPLETE)
        result = parse_line(line)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.total, 120)
        self.assertEqual(result.would_block, 3)
        self.assertEqual(result.rule1_block, 3)

    def test_non_prefix_line_returns_none(self) -> None:
        line = "some random log line\n"
        self.assertIsNone(parse_line(line))

    def test_bad_json_after_prefix_returns_none(self) -> None:
        line = f"{PREFIX} this is not json\n"
        self.assertIsNone(parse_line(line))

    def test_empty_line_returns_none(self) -> None:
        self.assertIsNone(parse_line(""))
        self.assertIsNone(parse_line("  \n"))


class TestParseStream(unittest.TestCase):
    def test_multiple_valid_lines(self) -> None:
        lines = _prefix_line(_SAMPLE_COMPLETE) + _prefix_line(_SAMPLE_WARN_ONLY)
        results = parse_stream(io.StringIO(lines))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].total, 120)

    def test_mixed_lines_skips_invalid(self) -> None:
        stream = io.StringIO(_SAMPLE_WITH_BAD_LINE)
        results = parse_stream(stream)
        self.assertEqual(len(results), 2)

    def test_no_valid_lines(self) -> None:
        stream = io.StringIO("line one\nline two\n")
        results = parse_stream(stream)
        self.assertEqual(results, [])

    def test_empty_stream(self) -> None:
        results = parse_stream(io.StringIO(""))
        self.assertEqual(results, [])


# ── generate_report ────────────────────────────────────────────────────────


class TestGenerateReport(unittest.TestCase):
    def test_normal_report_contains_sections(self) -> None:
        rows = [
            ShadowSummaryRow.from_dict(_SAMPLE_COMPLETE),
            ShadowSummaryRow.from_dict(_SAMPLE_WARN_ONLY),
        ]
        buf = io.StringIO()
        generate_report(rows, out=buf)
        output = buf.getvalue()

        self.assertIn("ENF Shadow Summary Report", output)
        self.assertIn("Overall", output)
        self.assertIn("Per-Rule", output)
        self.assertIn("Samples", output)
        self.assertIn("170", output)  # total records (120 + 50)
        self.assertIn("3", output)    # would_block
        self.assertIn("3", output)    # would_warn

    def test_skipped_only_rows_counts_as_run(self) -> None:
        rows = [ShadowSummaryRow.from_dict(_SAMPLE_SKIPPED)]
        buf = io.StringIO()
        generate_report(rows, out=buf)
        output = buf.getvalue()
        self.assertIn("runs loaded", output)

    def test_no_rows_prints_empty_message(self) -> None:
        buf = io.StringIO()
        generate_report([], out=buf)
        self.assertIn("no data", buf.getvalue().lower())

    def test_samples_section_shows_samples(self) -> None:
        rows = [ShadowSummaryRow.from_dict(_SAMPLE_COMPLETE)]
        buf = io.StringIO()
        generate_report(rows, out=buf)
        output = buf.getvalue()
        self.assertIn("task-abc", output)
        self.assertIn("task-def", output)
        self.assertIn("infra_risk", output)
        self.assertIn("timeout", output)


# ── CLI entry points ───────────────────────────────────────────────────────


class TestCliLogFlag(unittest.TestCase):
    def test_log_flag_parses_file(self) -> None:
        content = _prefix_line(_SAMPLE_COMPLETE) + _prefix_line(_SAMPLE_WARN_ONLY)
        with NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmppath = tmp.name
        try:
            buf = io.StringIO()
            with mock.patch("sys.argv", ["analyze_enf", "--log", tmppath]):
                with redirect_stdout(buf):
                    from tools.analyze_enf_shadow_summaries import main
                    exit_code = main()
            self.assertEqual(exit_code, 0)
            output = buf.getvalue()
            self.assertIn("runs loaded", output)
            self.assertIn("Overall", output)
        finally:
            Path(tmppath).unlink(missing_ok=True)

    def test_stdin_flag_parses_piped_input(self) -> None:
        content = _prefix_line(_SAMPLE_COMPLETE) + _prefix_line(_SAMPLE_WARN_ONLY)
        buf = io.StringIO()
        with mock.patch("sys.argv", ["analyze_enf", "--stdin"]):
            with mock.patch("sys.stdin", io.StringIO(content)):
                with redirect_stdout(buf):
                    from tools.analyze_enf_shadow_summaries import main
                    exit_code = main()
        self.assertEqual(exit_code, 0)
        output = buf.getvalue()
        self.assertIn("runs loaded", output)

    def test_no_flag_prints_usage_and_exits(self) -> None:
        buf = io.StringIO()
        with mock.patch("sys.argv", ["analyze_enf"]):
            with redirect_stderr(buf):
                from tools.analyze_enf_shadow_summaries import main

                with self.assertRaises(SystemExit) as cm:
                    main()
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("usage", buf.getvalue().lower())
