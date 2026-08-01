"""Unit tests for Checkpoint B integration v1 (W6-T6)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hitl.checkpoint_b_integration_v1 import (
    CHECKPOINT_B_ID,
    build_checkpoint_b_payload,
    delivery_plan_from_checkpoint_b,
    delivery_plan_from_human_decision,
    maybe_create_checkpoint_b,
    should_create_checkpoint_b,
)
from hitl.checkpoints_v1 import CHECKPOINT_SCHEMA_VERSION
from tools.tabular_outbox_writer import outbox_root

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _sample_execution_summary() -> dict:
    return {
        "tools_executed": [
            {"tool_id": "validate.eligibility", "ok": True, "exit_code": 2},
            {"tool_id": "clean.phase_demo", "ok": True, "forced": True},
            {"tool_id": "export.delivery_bundle", "ok": True},
        ],
        "outbox_runs": [
            "2026-06-10T08-30-15Z_eligibility",
            "2026-06-10T08-30-45Z_phase_demo",
            "2026-06-10T08-31-15Z_delivery_bundle",
        ],
        "cleaning_results": {
            "input_rows": 7,
            "output_rows": 5,
            "removed_rows": 2,
            "removal_ratio": 0.286,
            "qa_status": "pass_with_warnings",
        },
    }


def _sample_artifacts() -> dict:
    return {
        "eligibility_report": "reports/eligibility_result.json",
        "cleaned_csv": "cleaned/Phase_cleaned.csv",
        "delivery_bundle": "reports/delivery_bundle.zip",
        "signoff": "delivery_signoff.md",
    }


def _sample_output_guard_ok() -> dict:
    return {
        "status": "ok",
        "checks": {
            "ratio_check": "ok",
            "schema_check": "ok",
            "completeness_check": "ok",
        },
    }


def _sample_output_guard_warning() -> dict:
    return {
        "status": "warning",
        "checks": {
            "ratio_check": "warning",
            "schema_check": "ok",
            "completeness_check": "ok",
        },
        "removal_ratio": 0.93,
    }


class TestCheckpointBIntegrationV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.outbox = outbox_root(self.repo_root)
        self.case_dir = self.repo_root / "cases" / "demo_phase"
        self.case_dir.mkdir(parents=True)
        (self.case_dir / "intake.json").write_text(
            json.dumps({"client_ref": "internal-demo", "case_id": "demo_phase"}),
            encoding="utf-8",
        )
        self.extra = {
            "repo_root": self.repo_root,
            "outbox_root_override": str(self.outbox),
        }

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_ok_auto_approve_skips_checkpoint(self) -> None:
        result = maybe_create_checkpoint_b(
            self.case_dir,
            _sample_execution_summary(),
            _sample_output_guard_ok(),
            _sample_artifacts(),
            auto_approve=True,
            **self.extra,
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["checkpoint_created"])
        self.assertTrue(result["skipped"])
        self.assertEqual(result["skip_reason"], "ok_with_auto_approve")
        self.assertIsNone(result["checkpoint_path"])

        plan = result["delivery_plan"]
        self.assertEqual(plan["action"], "auto_approve")
        self.assertEqual(plan["resume_from"], "delivery")
        self.assertTrue(plan["proceed_to_delivery"])
        self.assertFalse(plan["notify_client"])

        checkpoint_files = list((self.outbox / "demo_phase").glob("checkpoint_*.json"))
        self.assertEqual(checkpoint_files, [])

    def test_warning_creates_checkpoint_b(self) -> None:
        result = maybe_create_checkpoint_b(
            self.case_dir,
            _sample_execution_summary(),
            _sample_output_guard_warning(),
            _sample_artifacts(),
            auto_approve=False,
            **self.extra,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["checkpoint_created"])
        self.assertFalse(result["skipped"])
        self.assertIsNotNone(result["checkpoint_path"])
        norm_path = str(result["checkpoint_path"]).replace("\\", "/")
        self.assertTrue(norm_path.startswith("outbox/demo_phase/"))

        checkpoint = result["checkpoint"]
        self.assertEqual(checkpoint["checkpoint_id"], CHECKPOINT_B_ID)
        self.assertEqual(checkpoint["schema_version"], CHECKPOINT_SCHEMA_VERSION)
        self.assertEqual(checkpoint["status"], "awaiting_human")
        self.assertIn("delivery_draft", checkpoint["agent_output"])
        self.assertEqual(
            checkpoint["agent_output"]["output_guard"]["status"],
            "warning",
        )

        plan = result["delivery_plan"]
        self.assertEqual(plan["action"], "await_human")
        self.assertFalse(plan["proceed_to_delivery"])
        self.assertEqual(
            plan["suggested_actions"],
            ["approve_delivery", "hold", "request_changes"],
        )

        saved = self.outbox / "demo_phase"
        files = list(saved.glob("checkpoint_B-delivery-confirmation_*.json"))
        self.assertEqual(len(files), 1)

    def test_build_checkpoint_b_payload_structure(self) -> None:
        payload = build_checkpoint_b_payload(
            self.case_dir,
            _sample_execution_summary(),
            _sample_output_guard_warning(),
            _sample_artifacts(),
            repo_root=self.repo_root,
        )

        self.assertEqual(payload["checkpoint_id"], CHECKPOINT_B_ID)
        self.assertEqual(payload["case_ref"], "demo_phase")
        self.assertIn("execution_summary", payload["agent_output"])
        self.assertIn("artifacts", payload["agent_output"])
        self.assertIn("checkpoint", payload)
        self.assertEqual(payload["checkpoint"]["version"], "v1")

    def test_delivery_plan_approve_delivery(self) -> None:
        resume_context = {
            "checkpoint_id": CHECKPOINT_B_ID,
            "case_ref": "demo_phase",
            "original_decision": {"output_guard_status": "warning"},
            "human_decision": {
                "action": "approve_delivery",
                "by": "operator_002",
                "at": "2026-06-10T08:33:00Z",
            },
            "resume_from": "delivery",
            "artifacts": _sample_artifacts(),
        }
        plan = delivery_plan_from_checkpoint_b(resume_context)

        self.assertTrue(plan["ok"])
        self.assertEqual(plan["action"], "approve_delivery")
        self.assertEqual(plan["resume_from"], "delivery")
        self.assertTrue(plan["proceed_to_delivery"])
        self.assertEqual(plan["update_case_status"], "delivered")
        self.assertFalse(plan["notify_client"])
        self.assertIn("S13_delivery_approval", plan["next_steps"])

    def test_delivery_plan_request_changes_defaults_cleaning(self) -> None:
        resume_context = {
            "checkpoint_id": CHECKPOINT_B_ID,
            "case_ref": "sampleco/2026-0001",
            "human_decision": {
                "action": "request_changes",
                "comment": "re-clean with stricter null handling",
            },
            "resume_from": "cleaning",
            "change_request": "re-clean with stricter null handling",
            "artifacts": _sample_artifacts(),
        }
        plan = delivery_plan_from_checkpoint_b(resume_context)

        self.assertTrue(plan["ok"])
        self.assertEqual(plan["action"], "request_changes")
        self.assertEqual(plan["revise_target"], "cleaning")
        self.assertEqual(plan["resume_from"], "cleaning")
        self.assertFalse(plan["proceed_to_delivery"])
        self.assertEqual(plan["update_case_status"], "changes_requested")
        self.assertIn("re_run_cleaning", plan["next_steps"])

    def test_delivery_plan_request_changes_bundle_target(self) -> None:
        resume_context = {
            "checkpoint_id": CHECKPOINT_B_ID,
            "case_ref": "demo_phase",
            "human_decision": {
                "action": "request_changes",
                "revise_target": "bundle",
            },
            "resume_from": "bundle",
            "revise_target": "bundle",
            "artifacts": _sample_artifacts(),
        }
        plan = delivery_plan_from_checkpoint_b(resume_context)

        self.assertEqual(plan["revise_target"], "bundle")
        self.assertEqual(plan["resume_from"], "bundle")
        self.assertIn("re_run_bundle", plan["next_steps"])

    def test_delivery_plan_hold(self) -> None:
        resume_context = {
            "checkpoint_id": CHECKPOINT_B_ID,
            "case_ref": "demo_phase",
            "human_decision": {"action": "hold", "by": "operator_003"},
            "resume_from": None,
        }
        plan = delivery_plan_from_checkpoint_b(resume_context)

        self.assertTrue(plan["ok"])
        self.assertEqual(plan["action"], "hold")
        self.assertIsNone(plan["resume_from"])
        self.assertFalse(plan["proceed_to_delivery"])
        self.assertEqual(plan["update_case_status"], "on_hold")
        self.assertIn("await_manual_resume", plan["next_steps"])

    def test_delivery_plan_from_human_decision_helper(self) -> None:
        checkpoint = build_checkpoint_b_payload(
            self.case_dir,
            _sample_execution_summary(),
            _sample_output_guard_warning(),
            _sample_artifacts(),
            repo_root=self.repo_root,
        )
        human = {
            "action": "approve_delivery",
            "operator_id": "operator_002",
            "comment": "ship",
            "timestamp": "2026-06-10T08:33:00Z",
            "by": "operator_002",
            "at": "2026-06-10T08:33:00Z",
        }
        plan = delivery_plan_from_human_decision(checkpoint, human)
        self.assertEqual(plan["action"], "approve_delivery")
        self.assertEqual(plan["human_action"], "approve_delivery")

    def test_writes_only_under_outbox(self) -> None:
        outside = self.repo_root / "cases" / "evil_checkpoint.json"
        with self.assertRaises(ValueError):
            maybe_create_checkpoint_b(
                self.case_dir,
                _sample_execution_summary(),
                _sample_output_guard_warning(),
                _sample_artifacts(),
                outbox_root_override=str(self.repo_root / "cases"),
                **{"repo_root": self.repo_root},
            )

    def test_should_create_checkpoint_b_rules(self) -> None:
        self.assertFalse(
            should_create_checkpoint_b(_sample_output_guard_ok(), auto_approve=True)
        )
        self.assertTrue(should_create_checkpoint_b(_sample_output_guard_warning()))
        self.assertTrue(
            should_create_checkpoint_b({"status": "blocked"}, auto_approve=False)
        )
        self.assertFalse(should_create_checkpoint_b({"status": "error"}))

    def test_custom_outbox_root_outside_repo_writes_checkpoint_b(self) -> None:
        """Test that custom outbox_root outside repo_root works for checkpoint B.

        Regression test for W6-T5/W6-T6-fix-outbox-root-override-relative-path-v1.
        Previously, dest.relative_to(repo_root) would raise ValueError when
        outbox_root was outside the repo directory.
        """
        # Must be named 'outbox' per checkpoints_v1.py validation
        with tempfile.TemporaryDirectory() as external_dir:
            external_outbox = Path(external_dir) / "outbox"
            external_outbox.mkdir(parents=True, exist_ok=True)

            # This should NOT raise ValueError
            result = maybe_create_checkpoint_b(
                self.case_dir,
                _sample_execution_summary(),
                _sample_output_guard_warning(),
                _sample_artifacts(),
                auto_approve=False,
                repo_root=self.repo_root,
                outbox_root_override=str(external_outbox),
            )

            # Verify checkpoint was created
            self.assertTrue(result["ok"])
            self.assertTrue(result["checkpoint_created"])
            self.assertFalse(result["skipped"])
            self.assertIsNotNone(result["checkpoint_path"])

            # Verify file was written to external outbox
            case_outbox = external_outbox / "demo_phase"
            checkpoint_files = list(case_outbox.glob("checkpoint_B-delivery-confirmation_*.json"))
            self.assertEqual(len(checkpoint_files), 1)

            # Verify checkpoint content
            with checkpoint_files[0].open(encoding="utf-8") as fh:
                saved = json.load(fh)
            self.assertEqual(saved["checkpoint_id"], CHECKPOINT_B_ID)
            self.assertEqual(saved["status"], "awaiting_human")


if __name__ == "__main__":
    unittest.main()
