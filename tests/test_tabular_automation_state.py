"""Unit tests for tabular automation control plane (v1)."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_automation_state_lib import (  # noqa: E402
    get_status,
    pause_automation,
    resume_automation,
    start_automation,
    state_path,
    stop_automation,
)


class TestTabularAutomationState(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.case_dir = self.tmp / "cases" / "demo_client" / "2026-0001"
        self.case_dir.mkdir(parents=True)
        shutil.copy2(
            _REPO_ROOT / "cases" / "demo_phase" / "intake.json",
            self.case_dir / "intake.json",
        )
        intake = json.loads((self.case_dir / "intake.json").read_text(encoding="utf-8"))
        intake["case_id"] = "2026-0001"
        intake["client_ref"] = "demo_client"
        (self.case_dir / "intake.json").write_text(
            json.dumps(intake, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_status_without_state_file(self) -> None:
        result = get_status(self.case_dir)
        self.assertTrue(result["ok"])
        self.assertEqual(result["state"]["automation_status"], "idle")
        self.assertFalse(state_path(self.case_dir).is_file())

    def test_start_pause_resume_stop_cycle(self) -> None:
        start = start_automation(self.case_dir, requested_by="op1")
        self.assertTrue(start["ok"])
        self.assertEqual(start["previous_status"], "idle")
        self.assertEqual(start["state"]["automation_status"], "running")
        self.assertTrue(start["state"]["allowed_to_auto_proceed"])

        duplicate_start = start_automation(self.case_dir, requested_by="op1")
        self.assertFalse(duplicate_start["ok"])
        self.assertIn("already running", duplicate_start["message"])

        pause = pause_automation(
            self.case_dir, requested_by="op1", reason="manual hold"
        )
        self.assertTrue(pause["ok"])
        self.assertEqual(pause["previous_status"], "running")
        self.assertEqual(pause["state"]["automation_status"], "paused")
        self.assertFalse(pause["state"]["allowed_to_auto_proceed"])

        resume = resume_automation(self.case_dir, requested_by="op2")
        self.assertTrue(resume["ok"])
        self.assertEqual(resume["state"]["automation_status"], "running")
        self.assertEqual(resume["state"]["resume_requested_by"], "op2")

        stop = stop_automation(self.case_dir, requested_by="op3")
        self.assertTrue(stop["ok"])
        self.assertEqual(stop["state"]["automation_status"], "stopped")
        self.assertFalse(stop["state"]["allowed_to_auto_proceed"])

    def test_start_from_stopped_requires_restart(self) -> None:
        stop_automation(self.case_dir, requested_by="op")
        blocked = start_automation(self.case_dir, requested_by="op")
        self.assertFalse(blocked["ok"])
        self.assertIn("restart", blocked["message"])

        restarted = start_automation(
            self.case_dir, requested_by="op", restart=True
        )
        self.assertTrue(restarted["ok"])
        self.assertEqual(restarted["state"]["automation_status"], "running")
        self.assertEqual(restarted["state"]["retry_count"], 0)

    def test_start_from_paused(self) -> None:
        start_automation(self.case_dir, requested_by="op")
        pause_automation(self.case_dir, requested_by="op")
        again = start_automation(self.case_dir, requested_by="op")
        self.assertTrue(again["ok"])
        self.assertEqual(again["previous_status"], "paused")
        self.assertEqual(again["state"]["automation_status"], "running")

    def test_resume_only_from_paused(self) -> None:
        result = resume_automation(self.case_dir, requested_by="op")
        self.assertFalse(result["ok"])
        self.assertIn("paused", result["message"])

    def test_pause_only_from_running(self) -> None:
        result = pause_automation(self.case_dir, requested_by="op")
        self.assertFalse(result["ok"])
        self.assertIn("running", result["message"])


if __name__ == "__main__":
    unittest.main()
