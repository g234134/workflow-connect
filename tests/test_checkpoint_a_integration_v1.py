"""Unit tests for Checkpoint A integration v1 (W6-T5)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hitl.checkpoint_a_integration_v1 import (
    apply_human_decision_to_checkpoint_a,
    build_checkpoint_a_payload,
    maybe_create_checkpoint_a,
    resume_plan_from_checkpoint_a,
    should_trigger_checkpoint_a,
)
from hitl.checkpoints_v1 import CHECKPOINT_A_ID, CHECKPOINT_SCHEMA_VERSION
from routing.intake_decision_rules_v1 import evaluate_intake_decision
from tools.tabular_outbox_writer import outbox_root

_REPO_ROOT = Path(__file__).resolve().parents[1]


class TestCheckpointAIntegrationV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.outbox = outbox_root(self.repo_root)
        self.extra = {
            "repo_root": self.repo_root,
            "outbox_root_override": str(self.outbox),
        }

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _decision(self, task_type: str, case_dir: str) -> dict:
        return evaluate_intake_decision(task_type, case_dir)

    def test_demo_phase_cleaning_creates_checkpoint_a(self) -> None:
        decision = self._decision("tabular.cleaning.mvp", "cases/demo_phase")
        self.assertEqual(decision["decision"], "needs_review")
        self.assertTrue(should_trigger_checkpoint_a(decision))

        result = maybe_create_checkpoint_a(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            decision,
            **self.extra,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "awaiting_human")
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertIn("checkpoint_path", result)

        checkpoint_path = self.repo_root / result["checkpoint_path"]
        self.assertTrue(checkpoint_path.is_file())
        self.assertIn("outbox", str(checkpoint_path))
        with checkpoint_path.open(encoding="utf-8") as fh:
            saved = json.load(fh)
        self.assertEqual(saved["checkpoint_id"], CHECKPOINT_A_ID)
        self.assertEqual(saved["status"], "awaiting_human")
        intake = saved["agent_output"]["intake_decision"]
        self.assertEqual(intake["decision"], "needs_review")
        self.assertIn("suggested_route", intake)

    def test_gate_adapter_embeds_intake_gate_in_checkpoint_payload(self) -> None:
        from routing.intake_gate_layer_v1 import evaluate_intake_gate
        from routing.intake_gate_mapping_v1 import decision_result_from_gate

        gate = evaluate_intake_gate(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            mode="preview",
        )
        adapted = decision_result_from_gate(gate)
        payload = build_checkpoint_a_payload(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            adapted,
        )
        intake_gate = payload["agent_output"].get("intake_gate") or {}
        self.assertEqual(intake_gate.get("intake_decision_id"), gate["intake_decision_id"])
        self.assertEqual(intake_gate.get("decision"), "review_needed")
        self.assertEqual(
            payload["agent_output"]["intake_decision"]["decision"],
            "needs_review",
        )

    def test_gate_reject_via_adapter_skips_checkpoint_a(self) -> None:
        from routing.intake_gate_layer_v1 import evaluate_intake_gate
        from routing.intake_gate_mapping_v1 import decision_result_from_gate

        gate = evaluate_intake_gate(
            "tabular.unsupported.mvp",
            "cases/demo_phase",
            mode="preview",
        )
        self.assertEqual(gate["decision"], "reject")
        adapted = decision_result_from_gate(gate)
        self.assertEqual(adapted["decision"], "reject")
        self.assertFalse(should_trigger_checkpoint_a(adapted))

        result = maybe_create_checkpoint_a(
            "tabular.unsupported.mvp",
            "cases/demo_phase",
            adapted,
            **self.extra,
        )
        self.assertEqual(result["status"], "rejected_intake")
        self.assertNotIn("checkpoint_path", result)
        pending = list(self.outbox.rglob("checkpoint_*.json"))
        self.assertEqual(pending, [])

    def test_gate_review_needed_via_adapter_triggers_checkpoint_a(self) -> None:
        from routing.intake_gate_layer_v1 import evaluate_intake_gate
        from routing.intake_gate_mapping_v1 import decision_result_from_gate

        gate = evaluate_intake_gate(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            mode="preview",
        )
        self.assertEqual(gate["decision"], "review_needed")
        adapted = decision_result_from_gate(gate)
        self.assertEqual(adapted["decision"], "needs_review")
        self.assertTrue(should_trigger_checkpoint_a(adapted))

        result = maybe_create_checkpoint_a(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            adapted,
            **self.extra,
        )
        self.assertEqual(result["status"], "awaiting_human")
        self.assertIn("checkpoint_path", result)

    def test_demo_phase_intake_new_case_auto_approve(self) -> None:
        decision = self._decision("tabular.intake.new_case", "cases/demo_phase")
        self.assertEqual(decision["decision"], "auto_accept")
        self.assertEqual(decision["risk_level"], "low")

        result = maybe_create_checkpoint_a(
            "tabular.intake.new_case",
            "cases/demo_phase",
            decision,
            auto_approve=True,
            **self.extra,
        )

        self.assertEqual(result["status"], "approved_auto")
        plan = result["resume_plan"]
        self.assertEqual(plan["final_status"], "approved")
        self.assertEqual(plan["resume_from"], "selector")
        self.assertIn("planned_tools", plan)

        pending = list(self.repo_root.glob("outbox/**/checkpoint_*.json"))
        self.assertEqual(pending, [])

    def test_auto_approve_needs_review_skips_checkpoint_file(self) -> None:
        decision = self._decision("tabular.cleaning.mvp", "cases/demo_phase")
        self.assertEqual(decision["decision"], "needs_review")

        result = maybe_create_checkpoint_a(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            decision,
            auto_approve=True,
            **self.extra,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "auto_approved")
        self.assertEqual(result["decision"], "needs_review")
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertEqual(result["reason"], "auto_approve_skip")
        self.assertNotIn("checkpoint_path", result)
        self.assertIn("resume_plan", result)

        plan = result["resume_plan"]
        self.assertEqual(plan["final_status"], "approved")
        self.assertEqual(plan["resume_from"], "selector")
        self.assertIn("planned_tools", plan)

        pending = list(self.repo_root.glob("outbox/**/checkpoint_*.json"))
        self.assertEqual(pending, [], "No checkpoint file should be written when needs_review + auto_approve=True")

    def test_needs_review_without_auto_approve_still_writes_checkpoint_file(self) -> None:
        """Baseline regression guard: needs_review + auto_approve=False must write checkpoint.

        This test explicitly verifies the contrast with test_auto_approve_needs_review_skips_checkpoint_file.
        When auto_approve is False (default), needs_review must create a checkpoint file and return
        status='awaiting_human', not 'auto_approved'.
        """
        decision = self._decision("tabular.cleaning.mvp", "cases/demo_phase")
        self.assertEqual(decision["decision"], "needs_review")

        # Explicitly pass auto_approve=False to contrast with auto_approve=True test
        result = maybe_create_checkpoint_a(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            decision,
            auto_approve=False,
            **self.extra,
        )

        # Must create checkpoint, not skip
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "awaiting_human")
        self.assertEqual(result["decision"], "needs_review")
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertIn("checkpoint_path", result)
        self.assertNotIn("resume_plan", result)  # No resume_plan when awaiting_human
        self.assertNotIn("reason", result)  # No reason field in normal flow

        # Verify checkpoint file was actually written
        checkpoint_path = self.repo_root / result["checkpoint_path"]
        self.assertTrue(checkpoint_path.is_file(), "checkpoint file must exist when auto_approve=False")
        self.assertIn("outbox", str(checkpoint_path))

        with checkpoint_path.open(encoding="utf-8") as fh:
            saved = json.load(fh)
        self.assertEqual(saved["checkpoint_id"], CHECKPOINT_A_ID)
        self.assertEqual(saved["status"], "awaiting_human")

    def test_sampleco_cleaning_creates_checkpoint_a(self) -> None:
        case_dir = "cases/sampleco/2026-0001"
        decision = self._decision("tabular.cleaning.mvp", case_dir)
        self.assertEqual(decision["decision"], "needs_review")

        result = maybe_create_checkpoint_a(
            "tabular.cleaning.mvp",
            case_dir,
            decision,
            **self.extra,
        )

        self.assertEqual(result["status"], "awaiting_human")
        self.assertEqual(result["case_ref"], "sampleco/2026-0001")

        payload = build_checkpoint_a_payload(
            "tabular.cleaning.mvp",
            case_dir,
            decision,
        )
        self.assertEqual(payload["schema_version"], CHECKPOINT_SCHEMA_VERSION)
        self.assertEqual(payload["case_ref"], "sampleco/2026-0001")

    def test_human_decision_resume_plans(self) -> None:
        decision = self._decision("tabular.cleaning.mvp", "cases/demo_phase")
        payload = build_checkpoint_a_payload(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            decision,
        )

        for action, expected_resume, expected_final in (
            ("approve", "selector", "approved"),
            ("revise_plan", "gate", "revise_needed"),
            ("reject", None, "rejected"),
        ):
            with self.subTest(action=action):
                applied = apply_human_decision_to_checkpoint_a(action, payload)
                self.assertTrue(applied["ok"])
                resume_context = applied["resume_context"]
                plan = applied["resume_plan"]
                self.assertEqual(resume_context["resume_from"], expected_resume)
                self.assertEqual(plan["resume_from"], expected_resume)
                self.assertEqual(plan["final_status"], expected_final)
                if action == "approve":
                    self.assertEqual(plan["selector_task_type"], "e2e")
                    self.assertIn("validate.eligibility", plan["planned_tools"])

    def test_resume_plan_from_checkpoint_a_reject(self) -> None:
        resume_context = {
            "checkpoint_id": CHECKPOINT_A_ID,
            "case_ref": "demo_phase",
            "original_decision": {"decision": "needs_review", "risk_level": "medium"},
            "human_decision": {"action": "reject", "by": "op1", "at": "2026-06-10T08:32:00Z"},
            "resume_from": None,
        }
        plan = resume_plan_from_checkpoint_a(resume_context)
        self.assertTrue(plan["ok"])
        self.assertIsNone(plan["resume_from"])
        self.assertEqual(plan["final_status"], "rejected")

    def test_writes_only_under_outbox(self) -> None:
        decision = self._decision("tabular.cleaning.mvp", "cases/demo_phase")
        maybe_create_checkpoint_a(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            decision,
            **self.extra,
        )
        outside_cases = list(self.repo_root.glob("cases/**/*.json"))
        self.assertEqual(outside_cases, [])
        checkpoint_files = list(self.outbox.rglob("checkpoint_*.json"))
        self.assertEqual(len(checkpoint_files), 1)
        self.assertTrue(str(checkpoint_files[0]).replace("\\", "/").startswith(
            str(self.outbox).replace("\\", "/")
        ))

    def test_custom_outbox_root_outside_repo_writes_checkpoint(self) -> None:
        """Test that custom outbox_root outside repo_root works without ValueError.

        Regression test for W6-T5/W6-T6-fix-outbox-root-override-relative-path-v1.
        Previously, dest.relative_to(repo_root) would raise ValueError when
        outbox_root was outside the repo directory.
        """
        # Create a truly external outbox directory (not under repo_root)
        # Must be named 'outbox' per checkpoints_v1.py validation
        with tempfile.TemporaryDirectory() as external_dir:
            external_outbox = Path(external_dir) / "outbox"
            external_outbox.mkdir(parents=True, exist_ok=True)

            decision = self._decision("tabular.cleaning.mvp", "cases/demo_phase")
            self.assertEqual(decision["decision"], "needs_review")

            # This should NOT raise ValueError
            result = maybe_create_checkpoint_a(
                "tabular.cleaning.mvp",
                "cases/demo_phase",
                decision,
                repo_root=self.repo_root,
                outbox_root_override=str(external_outbox),
            )

            # Verify checkpoint was created
            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "awaiting_human")
            self.assertIn("checkpoint_path", result)

            # Verify file was written to external outbox
            case_outbox = external_outbox / "demo_phase"
            checkpoint_files = list(case_outbox.glob("checkpoint_*.json"))
            self.assertEqual(len(checkpoint_files), 1)

            # Verify checkpoint content
            with checkpoint_files[0].open(encoding="utf-8") as fh:
                saved = json.load(fh)
            self.assertEqual(saved["checkpoint_id"], CHECKPOINT_A_ID)
            self.assertEqual(saved["status"], "awaiting_human")

            # checkpoint_path should be absolute path or relative to external outbox
            checkpoint_path = result["checkpoint_path"]
            self.assertTrue(
                Path(checkpoint_path).is_absolute() or "demo_phase" in checkpoint_path
            )


if __name__ == "__main__":
    unittest.main()
