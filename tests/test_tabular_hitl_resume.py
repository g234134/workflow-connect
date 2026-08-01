"""Unit tests for tabular HITL checkpoint resume integration."""

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

from tabular_automation_state_lib import (  # noqa: E402
    PAUSE_REASON_CHECKPOINT_A,
    load_state,
    save_state,
    start_automation,
)
from tabular_hitl_resume_lib import (  # noqa: E402
    apply_tabular_checkpoint_decision,
    driver_resume_step_from_context,
    resume_after_checkpoint,
)


class TestDriverResumeStepMapping(unittest.TestCase):
    def test_cp_a_approve_maps_to_cleaning(self) -> None:
        ctx = {
            "checkpoint_id": "A-intake-confirmation",
            "human_decision": {"action": "approve"},
            "resume_from": "selector",
        }
        self.assertEqual(driver_resume_step_from_context(ctx), "cleaning")

    def test_cp_b_approve_maps_to_approved_for_delivery(self) -> None:
        ctx = {
            "checkpoint_id": "B-delivery-confirmation",
            "human_decision": {"action": "approve_delivery"},
            "resume_from": "delivery",
        }
        self.assertEqual(driver_resume_step_from_context(ctx), "approved_for_delivery")

    def test_cp_a_reject_has_no_resume_step(self) -> None:
        ctx = {
            "checkpoint_id": "A-intake-confirmation",
            "human_decision": {"action": "reject"},
            "resume_from": None,
        }
        self.assertIsNone(driver_resume_step_from_context(ctx))


class TestTabularHitlResumeState(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.case_dir = self.tmp / "cases" / "demo_phase"
        self.case_dir.mkdir(parents=True)
        shutil.copy2(
            _REPO_ROOT / "cases" / "demo_phase" / "intake.json",
            self.case_dir / "intake.json",
        )
        (self.case_dir / "raw").mkdir()
        shutil.copy2(
            _REPO_ROOT / "cases" / "demo_phase" / "raw" / "Phase.csv",
            self.case_dir / "raw" / "Phase.csv",
        )
        start_automation(self.case_dir, requested_by="test")
        state = load_state(self.case_dir)
        state.update(
            {
                "automation_status": "paused",
                "pause_reason": PAUSE_REASON_CHECKPOINT_A,
                "current_step": "checkpoint_a",
                "requires_hitl_checkpoint": True,
                "checkpoint_a_status": "pending",
                "checkpoint_b_status": "not_required",
            }
        )
        save_state(self.case_dir, state)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    @patch("tabular_hitl_resume_lib.record_human_decision")
    def test_approve_a_sets_resume_step(self, mock_record: unittest.mock.MagicMock) -> None:
        mock_record.return_value = {
            "checkpoint_id": "A-intake-confirmation",
            "case_ref": "demo_phase",
            "human_decision": {"action": "approve"},
            "resume_from": "selector",
        }
        with patch(
            "tabular_hitl_resume_lib._find_pending_checkpoint_id",
            return_value="A-intake-confirmation",
        ):
            result = apply_tabular_checkpoint_decision(
                self.case_dir,
                command="approve-a",
                operator_id="op1",
                notes="LGTM",
            )
        self.assertTrue(result["ok"])
        state = load_state(self.case_dir)
        self.assertEqual(state["checkpoint_a_status"], "approved")
        self.assertEqual(state["checkpoint_a_decided_by"], "op1")
        self.assertEqual(state["checkpoint_resume_step"], "cleaning")
        self.assertFalse(state["requires_hitl_checkpoint"])

    @patch("tabular_hitl_resume_lib.record_human_decision")
    def test_reject_a_stops_case(self, mock_record: unittest.mock.MagicMock) -> None:
        mock_record.return_value = {
            "checkpoint_id": "A-intake-confirmation",
            "case_ref": "demo_phase",
            "human_decision": {"action": "reject"},
            "resume_from": None,
        }
        with patch(
            "tabular_hitl_resume_lib._find_pending_checkpoint_id",
            return_value="A-intake-confirmation",
        ):
            result = apply_tabular_checkpoint_decision(
                self.case_dir,
                command="reject-a",
                operator_id="op1",
            )
        self.assertTrue(result["ok"])
        state = load_state(self.case_dir)
        self.assertEqual(state["checkpoint_a_status"], "rejected")
        self.assertEqual(state["automation_status"], "stopped")
        self.assertIsNone(state["checkpoint_resume_step"])

    @patch("tabular_hitl_resume_lib.run_tabular_automation")
    def test_resume_after_checkpoint_invokes_driver(
        self, mock_run: unittest.mock.MagicMock
    ) -> None:
        mock_run.return_value = {"ok": True, "message": "completed"}
        state = load_state(self.case_dir)
        state.update(
            {
                "checkpoint_a_status": "approved",
                "requires_hitl_checkpoint": False,
                "checkpoint_resume_step": "cleaning",
                "pause_reason": "checkpoint_a_approved_awaiting_resume",
            }
        )
        save_state(self.case_dir, state)

        result = resume_after_checkpoint(self.case_dir, requested_by="op1")
        self.assertTrue(result["ok"])
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get("start_from"), "cleaning")


if __name__ == "__main__":
    unittest.main()
