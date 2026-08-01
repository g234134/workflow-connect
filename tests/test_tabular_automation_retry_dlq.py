"""Unit tests for tabular automation retry / DLQ (v1)."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_automation_driver_lib import run_tabular_automation  # noqa: E402
from tabular_automation_retry_dlq_lib import (  # noqa: E402
    BACKOFF_SECONDS,
    MAX_TRANSIENT_RETRIES,
    backoff_seconds,
    classify_step_failure,
    dlq_index_path,
    enqueue_dlq,
    is_transient_error,
)
from tabular_automation_state_lib import start_automation  # noqa: E402


def _make_temp_case() -> Path:
    tmp = Path(tempfile.mkdtemp())
    case_dir = tmp / "cases" / "retry_client" / "retry_case"
    case_dir.mkdir(parents=True)
    shutil.copytree(
        _REPO_ROOT / "cases" / "demo_phase" / "raw",
        case_dir / "raw",
    )
    intake = json.loads(
        (_REPO_ROOT / "cases" / "demo_phase" / "intake.json").read_text(encoding="utf-8")
    )
    intake["case_id"] = "retry_case"
    intake["client_ref"] = "retry_client"
    (case_dir / "intake.json").write_text(
        json.dumps(intake, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return case_dir


class TestRetryDlqLib(unittest.TestCase):
    def test_is_transient_error(self) -> None:
        self.assertTrue(is_transient_error("I/O error: resource temporarily unavailable"))
        self.assertFalse(is_transient_error("eligibility rejected"))

    def test_classify_step_failure(self) -> None:
        self.assertEqual(
            classify_step_failure({"ok": False, "hitl_blocked": True}),
            "permanent_stop",
        )
        self.assertEqual(
            classify_step_failure(
                {"ok": False, "error": "Connection reset by peer", "terminal": False}
            ),
            "transient",
        )
        self.assertEqual(
            classify_step_failure({"ok": False, "error": "clean exit 1"}),
            "immediate_dlq",
        )

    def test_backoff_sequence(self) -> None:
        self.assertEqual(backoff_seconds(1), BACKOFF_SECONDS[0])
        self.assertEqual(backoff_seconds(2), BACKOFF_SECONDS[1])
        self.assertEqual(backoff_seconds(3), BACKOFF_SECONDS[2])

    def test_enqueue_dlq_writes_index_and_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp)
            result = enqueue_dlq(
                case_dir,
                case_id="demo",
                case_dir_rel="cases/demo",
                run_id="run123",
                step_name="cleaning",
                error="I/O error after retries",
                failure_class="transient",
                retry_count=3,
                last_error_at="2026-06-27T12:00:00+00:00",
            )
            self.assertTrue(result["ok"])
            index = json.loads(dlq_index_path(case_dir).read_text(encoding="utf-8"))
            self.assertEqual(len(index["entries"]), 1)
            self.assertEqual(index["entries"][0]["status"], "queued")
            entry_path = case_dir / "dlq" / f"{result['entry_id']}.json"
            self.assertTrue(entry_path.is_file())


class TestDriverTransientRetry(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = _make_temp_case()

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir.parents[2], ignore_errors=True)

    def test_transient_intake_retries_then_dlq(self) -> None:
        case_dir = self.case_dir
        calls = {"n": 0}

        def flaky_intake(_cd: Path) -> dict:
            calls["n"] += 1
            return {
                "ok": False,
                "artifacts": {},
                "error": "OSError: resource temporarily unavailable",
            }

        start_automation(case_dir, requested_by="retry_test", restart=True)

        with patch(
            "tabular_automation_driver_lib._step_intake",
            side_effect=flaky_intake,
        ), patch("tabular_automation_driver_lib.time.sleep"):
            result = run_tabular_automation(
                case_dir,
                force=True,
                skip_control_check=True,
                stop_after="intake",
            )

        self.assertFalse(result["ok"])
        self.assertEqual(calls["n"], MAX_TRANSIENT_RETRIES + 1)
        step = result["run_log"]["steps"][0]
        self.assertEqual(step["retry_count"], MAX_TRANSIENT_RETRIES)
        self.assertEqual(step["dlq_status"], "queued")
        self.assertEqual(len(step["retry_attempts"]), MAX_TRANSIENT_RETRIES + 1)

        state = json.loads((case_dir / "automation_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["dlq_status"], "queued")
        self.assertEqual(state["retry_count"], MAX_TRANSIENT_RETRIES)
        self.assertIsNotNone(state["last_error_at"])

        index_path = dlq_index_path(case_dir)
        self.assertTrue(index_path.is_file())


class TestDriverPersistentDlq(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = _make_temp_case()

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir.parents[2], ignore_errors=True)

    def test_persistent_report_error_immediate_dlq(self) -> None:
        case_dir = self.case_dir
        calls = {"n": 0}

        def bad_report(_cd: Path) -> dict:
            calls["n"] += 1
            return {
                "ok": False,
                "artifacts": {},
                "error": "missing report artifacts: report.json",
            }

        start_automation(case_dir, requested_by="dlq_test", restart=True)

        with patch(
            "tabular_automation_driver_lib._step_report",
            side_effect=bad_report,
        ):
            result = run_tabular_automation(
                case_dir,
                force=True,
                skip_control_check=True,
                start_from="report",
                stop_after="report",
            )

        self.assertFalse(result["ok"])
        self.assertEqual(calls["n"], 1)
        step = result["run_log"]["steps"][0]
        self.assertEqual(step["step_name"], "report")
        self.assertEqual(step["retry_count"], 0)
        self.assertEqual(step["attempt"], 1)
        self.assertEqual(step["dlq_status"], "queued")
        self.assertIn("missing report artifacts", step["error_if_any"] or "")
        self.assertIsNotNone(step["dlq_if_any"])
        self.assertEqual(step["dlq_if_any"]["failure_class"], "immediate_dlq")

        state = json.loads((case_dir / "automation_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["dlq_status"], "queued")

        entry = json.loads(
            (case_dir / "dlq" / f"{step['dlq_if_any']['entry_id']}.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(entry["failure_class"], "immediate_dlq")
        self.assertEqual(entry["retry_count"], 0)


class TestDriverTransientRecovery(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = _make_temp_case()

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir.parents[2], ignore_errors=True)

    def test_transient_recovers_without_dlq(self) -> None:
        case_dir = self.case_dir
        calls = {"n": 0}

        def flaky_then_ok(_cd: Path) -> dict:
            calls["n"] += 1
            if calls["n"] == 1:
                return {
                    "ok": False,
                    "artifacts": {},
                    "error": "OSError: resource temporarily unavailable",
                }
            return {"ok": True, "artifacts": {"intake_json": "ok"}, "error": None}

        start_automation(case_dir, requested_by="retry_test", restart=True)

        with patch(
            "tabular_automation_driver_lib._step_intake",
            side_effect=flaky_then_ok,
        ), patch("tabular_automation_driver_lib.time.sleep"):
            result = run_tabular_automation(
                case_dir,
                force=True,
                skip_control_check=True,
                stop_after="intake",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(calls["n"], 2)
        step = result["run_log"]["steps"][0]
        self.assertEqual(step["attempt"], 2)
        self.assertEqual(step["dlq_status"], "none")
        self.assertIsNone(step["error_if_any"])
        self.assertIsNone(step["dlq_if_any"])
        self.assertEqual(len(step["retry_attempts"]), 1)


if __name__ == "__main__":
    unittest.main()
