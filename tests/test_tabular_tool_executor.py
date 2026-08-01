"""Unit tests for Tabular Tool Executor + Outbox v1 (W3-TL-T3)."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.tabular_outbox_writer import OUTBOX_SCHEMA_VERSION
from tools.tabular_tool_executor import execute_tabular_tool

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEMO_PHASE_DIR = _REPO_ROOT / "cases" / "demo_phase"

_REQUIRED_EXECUTE_KEYS = frozenset(
    {
        "ok",
        "message",
        "tool_id",
        "case_ref",
        "run_id",
        "schema_version",
        "exit_code",
        "started_at",
        "finished_at",
        "artifacts",
        "outbox_path",
        "dry_run",
    }
)

_REQUIRED_OUTBOX_KEYS = frozenset(
    {
        "schema_version",
        "case_ref",
        "run_id",
        "tool_id",
        "started_at",
        "finished_at",
        "ok",
        "exit_code",
        "message",
        "artifacts",
        "outbox_path",
    }
)


def _assert_execute_shape(result: dict) -> None:
    missing = _REQUIRED_EXECUTE_KEYS - set(result)
    assert not missing, f"missing execute keys: {sorted(missing)}"


def _assert_outbox_shape(record: dict) -> None:
    missing = _REQUIRED_OUTBOX_KEYS - set(record)
    assert not missing, f"missing outbox keys: {sorted(missing)}"


class TestTabularToolExecutor(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.outbox_root = str(Path(self._tmpdir.name) / "outbox")
        self.extra = {"outbox_root": self.outbox_root}

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_ac1_dry_run_no_subprocess_no_outbox_file(self) -> None:
        with patch("tools.tabular_tool_executor.subprocess.run") as mock_run:
            result = execute_tabular_tool(
                "demo_phase",
                "validate.eligibility",
                dry_run=True,
                extra_args=self.extra,
            )

        mock_run.assert_not_called()
        _assert_execute_shape(result)
        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["tool_id"], "validate.eligibility")
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertIn("outbox/demo_phase/", result["outbox_path"])
        self.assertTrue(result["outbox_path"].endswith(".json"))

        outbox_file = _REPO_ROOT / result["outbox_path"]
        self.assertFalse(outbox_file.exists())

        events_path = Path(self.outbox_root) / "events.jsonl"
        self.assertFalse(events_path.exists())

    def test_ac2_demo_phase_eligibility_real_execute(self) -> None:
        result = execute_tabular_tool(
            "demo_phase",
            "validate.eligibility",
            dry_run=False,
            extra_args=self.extra,
        )

        _assert_execute_shape(result)
        self.assertEqual(result["tool_id"], "validate.eligibility")
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertIsNotNone(result["exit_code"])
        self.assertIn(result["exit_code"], (0, 1, 2))
        self.assertTrue(result["ok"])
        self.assertFalse(result["dry_run"])

        outbox_path = Path(self.outbox_root) / "demo_phase" / f"{result['run_id']}.json"
        self.assertTrue(outbox_path.is_file(), f"missing outbox file: {outbox_path}")

        with outbox_path.open(encoding="utf-8") as fh:
            record = json.load(fh)
        _assert_outbox_shape(record)
        self.assertEqual(record["schema_version"], OUTBOX_SCHEMA_VERSION)
        self.assertEqual(record["tool_id"], "validate.eligibility")
        self.assertIsInstance(record["artifacts"], list)
        self.assertGreaterEqual(len(record["artifacts"]), 1)
        self.assertIn("path", record["artifacts"][0])

        events_path = Path(self.outbox_root) / "events.jsonl"
        self.assertTrue(events_path.is_file())
        lines = events_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreaterEqual(len(lines), 1)
        event = json.loads(lines[-1])
        self.assertEqual(event["tool_id"], "validate.eligibility")
        self.assertEqual(event["case_ref"], "demo_phase")

    def test_ac3_missing_intake_failure_still_writes_outbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty_case = Path(tmp) / "empty_case"
            empty_case.mkdir()
            (empty_case / "raw").mkdir()
            (empty_case / "raw" / "dummy.csv").write_text("a,b\n1,2\n", encoding="utf-8")

            outbox_root = str(Path(tmp) / "outbox")
            result = execute_tabular_tool(
                "empty_case",
                "validate.eligibility",
                dry_run=False,
                extra_args={
                    "case_dir": str(empty_case),
                    "outbox_root": outbox_root,
                },
            )

            _assert_execute_shape(result)
            self.assertFalse(result["ok"])
            self.assertEqual(result["exit_code"], 2)
            self.assertIn("missing intake", result["message"].lower())

            outbox_file = Path(outbox_root) / "empty_case" / f"{result['run_id']}.json"
            self.assertTrue(outbox_file.is_file())
            with outbox_file.open(encoding="utf-8") as fh:
                record = json.load(fh)
            _assert_outbox_shape(record)
            self.assertFalse(record["ok"])
            self.assertEqual(record["exit_code"], 2)

    def test_unknown_tool_id_failure(self) -> None:
        result = execute_tabular_tool(
            "demo_phase",
            "nonexistent.tool",
            dry_run=False,
            extra_args=self.extra,
        )

        _assert_execute_shape(result)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["exit_code"])
        self.assertIn("unknown tool_id", result["message"])

        outbox_file = Path(self.outbox_root) / "demo_phase" / f"{result['run_id']}.json"
        self.assertTrue(outbox_file.is_file())

    def test_lightweight_index_cases_execute(self) -> None:
        result = execute_tabular_tool(
            "_global",
            "index.cases",
            dry_run=False,
            extra_args=self.extra,
        )

        _assert_execute_shape(result)
        self.assertEqual(result["tool_id"], "index.cases")
        self.assertIsNotNone(result["exit_code"])
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(len(result["artifacts"]), 1)
        self.assertEqual(result["artifacts"][0].get("logical_key"), "cases_index")

    def test_subprocess_timeout_returns_failure_with_null_exit_code(self) -> None:
        with patch("tools.tabular_tool_executor.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["python", "scripts/fake.py"],
                timeout=600,
                stderr="timed out",
            )
            result = execute_tabular_tool(
                "demo_phase",
                "validate.eligibility",
                dry_run=False,
                extra_args=self.extra,
            )

        _assert_execute_shape(result)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["exit_code"])
        self.assertIn("subprocess_timeout", result["message"])
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args.kwargs
        self.assertEqual(call_kwargs.get("timeout"), 600)

        outbox_file = Path(self.outbox_root) / "demo_phase" / f"{result['run_id']}.json"
        self.assertTrue(outbox_file.is_file())
        with outbox_file.open(encoding="utf-8") as fh:
            record = json.load(fh)
        self.assertFalse(record["ok"])
        self.assertIsNone(record["exit_code"])
        self.assertIn("subprocess_timeout", record["message"])

    def test_dry_run_planned_command_contains_case_dir(self) -> None:
        result = execute_tabular_tool(
            "demo_phase",
            "validate.eligibility",
            dry_run=True,
            extra_args=self.extra,
        )
        self.assertTrue(result["ok"])
        outbox_file = Path(self.outbox_root) / "demo_phase" / f"{result['run_id']}.json"
        self.assertFalse(outbox_file.exists())


if __name__ == "__main__":
    unittest.main()
