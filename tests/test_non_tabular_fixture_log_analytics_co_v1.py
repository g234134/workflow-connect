"""Unit tests for NT-B log-analytics-co fixture (W9-T6)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CASE_DIR = "cases/log-analytics-co/2026-0001"
_CASE_PATH = _REPO_ROOT / _CASE_DIR
_INTAKE_PATH = _CASE_PATH / "intake.json"
_RAW_SERVER_LOGS = _CASE_PATH / "raw" / "server_logs"

_REQUIRED_INTAKE_KEYS = (
    "client_ref",
    "case_id",
    "content_type",
    "schema_hint",
    "sensitivity",
)

_NT_B_TASK_TYPES = (
    "non_tabular.log.analyze",
    "non-tabular.log.parse_and_summarize",
)

_LOG_SAMPLE_SUFFIXES = {".log", ".jsonl"}


def _load_intake() -> dict:
    return json.loads(_INTAKE_PATH.read_text(encoding="utf-8"))


class TestNonTabularFixtureLogAnalyticsCoV1(unittest.TestCase):
    def test_case_directory_structure(self) -> None:
        self.assertTrue(_CASE_PATH.is_dir(), f"missing case dir: {_CASE_DIR}")
        self.assertTrue(_INTAKE_PATH.is_file(), "intake.json must exist")
        self.assertTrue(_RAW_SERVER_LOGS.is_dir(), "raw/server_logs/ must exist")

    def test_raw_server_logs_has_parseable_sample(self) -> None:
        samples = [
            p
            for p in _RAW_SERVER_LOGS.iterdir()
            if p.is_file() and p.suffix.lower() in _LOG_SAMPLE_SUFFIXES
        ]
        self.assertGreaterEqual(len(samples), 1, "need >=1 .log or .jsonl sample")
        content = samples[0].read_text(encoding="utf-8")
        self.assertGreater(len(content.strip()), 20)

    def test_intake_required_keys_and_values(self) -> None:
        intake = _load_intake()
        for key in _REQUIRED_INTAKE_KEYS:
            self.assertIn(key, intake, f"missing intake key: {key}")

        self.assertEqual(intake["client_ref"], "log-analytics-co")
        self.assertEqual(intake["case_id"], "logs-2026-0001")
        self.assertEqual(intake["content_type"], "server_logs")
        self.assertEqual(intake["schema_hint"], "semi-structured")
        self.assertIn(intake["sensitivity"], {"public", "internal", "confidential"})

        time_hint = intake.get("time_range") or intake.get("time_range_hint")
        self.assertTrue(
            time_hint,
            "time_range or time_range_hint required for NT-B intake",
        )

        data_source = intake.get("data_source", "")
        self.assertTrue(
            data_source.startswith("raw/server_logs"),
            f"data_source should follow catalog convention, got {data_source!r}",
        )

    def test_v2_decision_nt_b_shadow_needs_review(self) -> None:
        for task_type in _NT_B_TASK_TYPES:
            with self.subTest(task_type=task_type):
                result = evaluate_intake_decision_v2(task_type, _CASE_DIR)
                self.assertTrue(result["ok"], result.get("message"))
                self.assertEqual(result["flow_family"], "non_tabular")
                self.assertEqual(result["fixture_profile_tier"], "NT-B")
                self.assertEqual(result["case_profile_tier"], "NT-B")
                self.assertEqual(result["decision"], "needs_review")
                self.assertEqual(result["risk_level"], "medium")
                self.assertIn(
                    "log_analysis_profile",
                    result["signals"]["medium"],
                )
                hook = result.get("shadow_flow_hook") or {}
                self.assertTrue(hook.get("eligible"))


if __name__ == "__main__":
    unittest.main()
