"""Unit tests for Tabular Outbox Consumer v1 (W3-TL-T4)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.tabular_outbox_consumer import (
    get_outbox_run,
    join_with_case_history,
    list_outbox_runs,
)
from tools.tabular_outbox_writer import OUTBOX_SCHEMA_VERSION

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_OUTBOX = _REPO_ROOT / "tests" / "fixtures" / "outbox"

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


def _assert_outbox_shape(record: dict) -> None:
    missing = _REQUIRED_OUTBOX_KEYS - set(record)
    assert not missing, f"missing outbox keys: {sorted(missing)}"


class TestTabularOutboxConsumer(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.outbox_root = Path(self._tmpdir.name) / "outbox"
        shutil.copytree(_FIXTURE_OUTBOX, self.outbox_root)
        self.extra = {"outbox_root_override": str(self.outbox_root)}

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_ac1_list_outbox_runs_demo_phase(self) -> None:
        runs = list_outbox_runs("demo_phase", **self.extra)
        self.assertGreaterEqual(len(runs), 1)
        for run in runs:
            self.assertEqual(run["case_ref"], "demo_phase")
            self.assertIn("run_id", run)
            self.assertIn("tool_id", run)
            self.assertIn("started_at", run)

    def test_ac1_list_outbox_runs_sampleco(self) -> None:
        runs = list_outbox_runs("sampleco/2026-0001", **self.extra)
        self.assertGreaterEqual(len(runs), 1)
        self.assertEqual(runs[0]["case_ref"], "sampleco/2026-0001")

    def test_ac2_filter_by_tool_id(self) -> None:
        runs = list_outbox_runs(
            "demo_phase",
            "validate.eligibility",
            **self.extra,
        )
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["tool_id"], "validate.eligibility")

    def test_ac2_time_filter(self) -> None:
        runs = list_outbox_runs(
            "demo_phase",
            started_after="2026-06-10T02:00:00Z",
            **self.extra,
        )
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["tool_id"], "clean.phase_demo")

    def test_get_outbox_run_success(self) -> None:
        result = get_outbox_run(
            "demo_phase",
            "2026-06-10T01-52-00Z_eligibility",
            **self.extra,
        )
        self.assertTrue(result["ok"])
        record = result["record"]
        _assert_outbox_shape(record)
        self.assertEqual(record["schema_version"], OUTBOX_SCHEMA_VERSION)
        self.assertEqual(record["tool_id"], "validate.eligibility")

    def test_get_outbox_run_not_found(self) -> None:
        result = get_outbox_run(
            "demo_phase",
            "nonexistent-run-id",
            **self.extra,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "run_not_found")
        self.assertEqual(result["case_ref"], "demo_phase")

    def test_get_outbox_run_missing_case(self) -> None:
        result = get_outbox_run(
            "no_such_case",
            "2026-06-10T01-52-00Z_eligibility",
            **self.extra,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "run_not_found")

    def test_join_with_case_history_demo_phase(self) -> None:
        result = join_with_case_history("demo_phase", **self.extra)
        self.assertTrue(result["ok"])
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertIn("case", result)
        self.assertIn("history", result)
        self.assertIn("runs", result)
        self.assertIn("last_by_tool_id", result)

        case = result["case"]
        self.assertIsNotNone(case)
        assert case is not None
        self.assertEqual(case.get("client_ref"), "internal-demo")
        self.assertEqual(case.get("product_sku"), "CLEAN-BASIC")

        runs = result["runs"]
        self.assertGreaterEqual(len(runs), 2)
        started = [r["started_at"] for r in runs]
        self.assertEqual(started, sorted(started))

        last = result["last_by_tool_id"]
        self.assertIn("validate.eligibility", last)
        self.assertIn("clean.phase_demo", last)
        self.assertEqual(last["clean.phase_demo"]["tool_id"], "clean.phase_demo")

        history = result["history"]
        self.assertTrue(history.get("ok"))
        self.assertGreaterEqual(len(history.get("matches", [])), 1)

    def test_join_with_case_history_sampleco(self) -> None:
        result = join_with_case_history("sampleco/2026-0001", **self.extra)
        self.assertTrue(result["ok"])
        case = result["case"]
        self.assertIsNotNone(case)
        assert case is not None
        self.assertEqual(case.get("client_ref"), "sampleco")
        self.assertGreaterEqual(result["run_count"], 1)

    def test_join_empty_outbox_still_ok(self) -> None:
        empty_root = Path(self._tmpdir.name) / "empty_outbox"
        empty_root.mkdir()
        result = join_with_case_history(
            "demo_phase",
            outbox_root_override=str(empty_root),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["runs"], [])
        self.assertEqual(result["run_count"], 0)

    def test_join_invalid_case_ref(self) -> None:
        result = join_with_case_history("", **self.extra)
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "invalid_case_ref")

    def test_list_all_cases_when_no_case_ref(self) -> None:
        runs = list_outbox_runs(**self.extra)
        self.assertGreaterEqual(len(runs), 3)
        case_refs = {r["case_ref"] for r in runs}
        self.assertIn("demo_phase", case_refs)
        self.assertIn("sampleco/2026-0001", case_refs)


class TestInspectTabularOutboxCli(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.outbox_root = Path(self._tmpdir.name) / "outbox"
        shutil.copytree(_FIXTURE_OUTBOX, self.outbox_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_cli_list_json(self) -> None:
        import io
        from contextlib import redirect_stdout

        from tools.inspect_tabular_outbox import main

        captured = io.StringIO()
        with redirect_stdout(captured):
            code = main(
                [
                    "--case-ref",
                    "demo_phase",
                    "--json",
                    "--outbox-root",
                    str(self.outbox_root),
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(captured.getvalue())
        self.assertTrue(payload["ok"])
        self.assertGreaterEqual(payload["count"], 1)

    def test_cli_join_history_json(self) -> None:
        import io
        from contextlib import redirect_stdout

        from tools.inspect_tabular_outbox import main

        captured = io.StringIO()
        with redirect_stdout(captured):
            code = main(
                [
                    "--case-ref",
                    "demo_phase",
                    "--join-history",
                    "--json",
                    "--outbox-root",
                    str(self.outbox_root),
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(captured.getvalue())
        self.assertTrue(payload["ok"])
        self.assertIn("last_by_tool_id", payload)


if __name__ == "__main__":
    unittest.main()
