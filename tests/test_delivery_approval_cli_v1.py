"""Unit tests for delivery approval one-click CLI v1 (W8-T3)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from delivery.delivery_approval_cli_v1 import (
    build_approval_review_summary,
    normalize_cli_action,
    run_delivery_approval,
)
from hitl.checkpoint_b_integration_v1 import (
    CHECKPOINT_B_ID,
    build_checkpoint_b_payload,
    maybe_create_checkpoint_b,
)
from hitl.checkpoints_v1 import get_checkpoint
from tools.tabular_outbox_writer import outbox_root

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEMO_PHASE = _REPO_ROOT / "cases" / "demo_phase"


def _sample_execution_summary() -> dict:
    return {
        "tools_executed": [
            {"tool_id": "validate.eligibility", "ok": True, "exit_code": 2},
            {"tool_id": "clean.phase_demo", "ok": True, "forced": True},
            {"tool_id": "export.delivery_bundle", "ok": True},
        ],
        "outbox_runs": ["2026-06-10T08-30-15Z_eligibility"],
    }


def _sample_artifacts() -> dict:
    return {
        "eligibility_report": "reports/eligibility_result.json",
        "cleaned_csv": "cleaned/Phase_cleaned.csv",
        "signoff": "delivery_signoff.md",
    }


def _sample_output_guard_warning() -> dict:
    return {
        "status": "warning",
        "input_rows": 7,
        "output_rows": 5,
        "ratio": 0.286,
    }


class TestDeliveryApprovalCliV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.outbox = outbox_root(self.repo_root)
        self.case_dir = self.repo_root / "cases" / "demo_phase"
        self.case_dir.mkdir(parents=True)
        (self.case_dir / "intake.json").write_text(
            json.dumps({"client_ref": "internal-demo", "case_id": "demo_phase", "sensitivity": "internal"}),
            encoding="utf-8",
        )
        (self.case_dir / "delivery_signoff.md").write_text(
            "| Field | Value |\n| case_id | demo_phase |\n| client_ref | demo |\n",
            encoding="utf-8",
        )
        reports = self.case_dir / "reports"
        reports.mkdir()
        (reports / "report.json").write_text(
            json.dumps(
                {
                    "summary": {"total_rows": 7, "accepted_rows": 5, "qa_status": "pass_with_warnings"},
                    "output_guard": {
                        "status": "warning",
                        "input_rows": 7,
                        "output_rows": 5,
                        "ratio": 0.286,
                    },
                }
            ),
            encoding="utf-8",
        )
        (reports / "cleaning_stats.json").write_text(
            json.dumps({"row_counts": {"intake": 7, "ok": 5}}),
            encoding="utf-8",
        )
        self.extra = {
            "repo_root": self.repo_root,
            "outbox_root_override": str(self.outbox),
        }

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _seed_pending_checkpoint_b(self) -> None:
        maybe_create_checkpoint_b(
            self.case_dir,
            _sample_execution_summary(),
            _sample_output_guard_warning(),
            _sample_artifacts(),
            **self.extra,
        )

    def test_normalize_cli_action_aliases(self) -> None:
        self.assertEqual(normalize_cli_action("approve"), "approve_delivery")
        self.assertEqual(normalize_cli_action("request_changes"), "request_changes")
        self.assertEqual(normalize_cli_action("hold"), "hold")

    def test_build_approval_review_summary(self) -> None:
        summary = build_approval_review_summary(self.case_dir, repo_root=self.repo_root)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["case_ref"], "demo_phase")
        self.assertEqual(summary["output_guard"]["status"], "warning")
        self.assertEqual(summary["metrics"]["input_rows"], 7)
        self.assertEqual(summary["metrics"]["output_rows"], 5)

    def test_preview_without_confirm(self) -> None:
        self._seed_pending_checkpoint_b()
        result = run_delivery_approval(
            self.case_dir,
            CHECKPOINT_B_ID,
            "approve",
            notes="preview",
            confirm=False,
            **self.extra,
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["confirmed"])
        self.assertIsNone(result["resume_context"])
        checkpoint = get_checkpoint(CHECKPOINT_B_ID, pending_only=True, **self.extra)
        self.assertEqual(checkpoint.get("status"), "awaiting_human")

    def test_approve_delivery_writes_decision(self) -> None:
        self._seed_pending_checkpoint_b()
        result = run_delivery_approval(
            self.case_dir,
            CHECKPOINT_B_ID,
            "approve",
            notes="ship it",
            confirm=True,
            **self.extra,
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["confirmed"])
        resume = result["resume_context"]
        self.assertIsNotNone(resume)
        self.assertEqual(resume["resume_from"], "delivery")
        self.assertEqual(resume["human_decision"]["action"], "approve_delivery")

        plan = result["delivery_plan"]
        self.assertTrue(plan["ok"])
        self.assertEqual(plan["action"], "approve_delivery")
        self.assertTrue(plan["proceed_to_delivery"])
        self.assertEqual(plan["update_case_status"], "delivered")
        self.assertFalse(plan["notify_client"])

        notify = result["notify_experiment"]
        self.assertTrue(notify["skipped"])

    def test_request_changes_defaults_cleaning(self) -> None:
        self._seed_pending_checkpoint_b()
        result = run_delivery_approval(
            self.case_dir,
            CHECKPOINT_B_ID,
            "request_changes",
            notes="fix nulls",
            confirm=True,
            **self.extra,
        )
        self.assertTrue(result["ok"])
        resume = result["resume_context"]
        self.assertEqual(resume["resume_from"], "cleaning")
        self.assertEqual(resume["revise_target"], "cleaning")
        self.assertEqual(resume["change_request"], "fix nulls")

        plan = result["delivery_plan"]
        self.assertEqual(plan["action"], "request_changes")
        self.assertEqual(plan["update_case_status"], "changes_requested")
        self.assertFalse(plan["proceed_to_delivery"])

    def test_request_changes_bundle_target(self) -> None:
        self._seed_pending_checkpoint_b()
        result = run_delivery_approval(
            self.case_dir,
            CHECKPOINT_B_ID,
            "request_changes",
            notes="rebuild bundle",
            confirm=True,
            revise_target="bundle",
            **self.extra,
        )
        self.assertTrue(result["ok"])
        resume = result["resume_context"]
        self.assertEqual(resume["resume_from"], "bundle")
        self.assertEqual(resume["revise_target"], "bundle")

        plan = result["delivery_plan"]
        self.assertEqual(plan["revise_target"], "bundle")
        self.assertIn("re_run_bundle", plan["next_steps"])

    def test_hold_on_hold(self) -> None:
        self._seed_pending_checkpoint_b()
        result = run_delivery_approval(
            self.case_dir,
            CHECKPOINT_B_ID,
            "hold",
            notes="waiting for client",
            confirm=True,
            **self.extra,
        )
        self.assertTrue(result["ok"])
        resume = result["resume_context"]
        self.assertIsNone(resume["resume_from"])
        self.assertEqual(resume["human_decision"]["action"], "hold")

        plan = result["delivery_plan"]
        self.assertEqual(plan["action"], "hold")
        self.assertEqual(plan["update_case_status"], "on_hold")

    def test_notify_experiment_skipped_by_default(self) -> None:
        self._seed_pending_checkpoint_b()
        with patch("delivery.delivery_approval_cli_v1.run_controlled_notify_experiment") as mock_notify:
            result = run_delivery_approval(
                self.case_dir,
                CHECKPOINT_B_ID,
                "approve",
                confirm=True,
                run_notify_experiment=False,
                **self.extra,
            )
            mock_notify.assert_not_called()
        self.assertTrue(result["notify_experiment"]["skipped"])

    def test_notify_experiment_called_on_approve(self) -> None:
        self._seed_pending_checkpoint_b()
        with patch("delivery.delivery_approval_cli_v1.run_controlled_notify_experiment") as mock_notify:
            mock_notify.return_value = {
                "ok": True,
                "dry_run": True,
                "simulated": True,
                "external_dispatch": False,
                "message": "simulated",
            }
            result = run_delivery_approval(
                self.case_dir,
                CHECKPOINT_B_ID,
                "approve",
                confirm=True,
                run_notify_experiment=True,
                notify_dry_run=True,
                **self.extra,
            )
            mock_notify.assert_called_once()
        self.assertFalse(result["notify_experiment"]["skipped"])
        self.assertFalse(result["notify_experiment"]["external_dispatch"])
        self.assertFalse(result["external_dispatch"])

    def test_notify_experiment_skipped_for_request_changes(self) -> None:
        self._seed_pending_checkpoint_b()
        with patch("delivery.delivery_approval_cli_v1.run_controlled_notify_experiment") as mock_notify:
            result = run_delivery_approval(
                self.case_dir,
                CHECKPOINT_B_ID,
                "request_changes",
                confirm=True,
                run_notify_experiment=True,
                **self.extra,
            )
            mock_notify.assert_not_called()
        self.assertTrue(result["notify_experiment"]["skipped"])

    def test_demo_phase_review_against_repo_fixture(self) -> None:
        if not _DEMO_PHASE.is_dir():
            self.skipTest("demo_phase fixture missing")
        summary = build_approval_review_summary(_DEMO_PHASE, repo_root=_REPO_ROOT)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["case_ref"], "demo_phase")
        self.assertIn(summary["output_guard"]["status"], ("ok", "warning", "blocked"))


if __name__ == "__main__":
    unittest.main()
