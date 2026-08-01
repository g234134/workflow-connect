"""Unit tests for HITL Checkpoints v1 (W5-T2B)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hitl.checkpoints_v1 import (
    CHECKPOINT_A_ID,
    CHECKPOINT_B_ID,
    CHECKPOINT_SCHEMA_VERSION,
    append_checkpoint_event,
    build_resume_context,
    list_pending_checkpoints,
    record_human_decision,
    validate_checkpoint,
    write_checkpoint,
)
from tools.tabular_outbox_writer import outbox_root

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _sample_checkpoint_a() -> dict:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_A_ID,
        "case_ref": "demo_phase",
        "run_id": "2026-06-10T08-30-00Z_intake_confirm",
        "status": "awaiting_human",
        "created_at": "2026-06-10T08:30:00Z",
        "expires_at": "2026-06-10T08:35:00Z",
        "task_type": "tabular.cleaning.mvp",
        "agent_output": {
            "task_type": "tabular.cleaning.mvp",
            "intake_decision": {
                "decision": "needs_review",
                "risk_level": "medium",
                "rationale": [
                    "task_type=tabular.cleaning.mvp",
                    "manual_review_required",
                ],
                "suggested_route": {
                    "selector_task_type": "e2e",
                    "planned_tools": [
                        "validate.eligibility",
                        "clean.phase_demo",
                        "export.delivery_bundle",
                    ],
                    "orchestration_tool_id": "orchestrate.e2e",
                },
            },
            "case_summary": {
                "client_ref": "internal-demo",
                "case_id": "demo_phase",
                "input_file": "raw/Phase.csv",
            },
            "gate_preview": {
                "eligibility": "review_needed",
                "exit_code": 2,
                "reason_code": "rows<100",
            },
        },
    }


def _sample_checkpoint_b() -> dict:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_B_ID,
        "case_ref": "demo_phase",
        "run_id": "2026-06-10T08-31-30Z_delivery_confirm",
        "status": "awaiting_human",
        "created_at": "2026-06-10T08:31:30Z",
        "expires_at": "2026-06-10T08:36:30Z",
        "task_type": "tabular.cleaning.mvp",
        "agent_output": {
            "task_type": "tabular.cleaning.mvp",
            "execution_summary": {
                "tools_executed": [
                    {"tool_id": "validate.eligibility", "ok": True, "exit_code": 2},
                    {"tool_id": "clean.phase_demo", "ok": True, "forced": True},
                    {"tool_id": "export.delivery_bundle", "ok": True},
                ],
            },
            "cleaning_results": {
                "input_rows": 7,
                "output_rows": 5,
                "removed_rows": 2,
                "removal_ratio": 0.286,
                "qa_status": "pass_with_warnings",
            },
            "artifacts": {
                "eligibility_report": "reports/eligibility_result.json",
                "cleaned_csv": "cleaned/Phase_cleaned.csv",
                "delivery_bundle": "reports/delivery_bundle.zip",
                "signoff": "delivery_signoff.md",
            },
            "output_guard": {
                "status": "ok",
                "checks": {
                    "ratio_check": "ok",
                    "schema_check": "ok",
                    "completeness_check": "ok",
                },
            },
            "delivery_draft": {
                "summary_text": "已清洗 7→5 rows",
                "confidence_score": 0.92,
            },
        },
    }


class TestHitlCheckpointsV1(unittest.TestCase):
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

    def test_write_checkpoint_creates_file_under_outbox(self) -> None:
        path = write_checkpoint(_sample_checkpoint_a(), **self.extra)
        self.assertTrue(path.is_file())
        self.assertIn("outbox", str(path))
        self.assertIn("demo_phase", str(path))
        with path.open(encoding="utf-8") as fh:
            saved = json.load(fh)
        self.assertEqual(saved["status"], "awaiting_human")
        self.assertTrue(saved["checkpoint_path"].startswith("outbox/demo_phase/"))

    def test_list_pending_checkpoints(self) -> None:
        write_checkpoint(_sample_checkpoint_a(), **self.extra)
        write_checkpoint(_sample_checkpoint_b(), **self.extra)

        pending = list_pending_checkpoints(**self.extra)
        self.assertEqual(len(pending), 2)
        ids = {row["checkpoint_id"] for row in pending}
        self.assertEqual(ids, {CHECKPOINT_A_ID, CHECKPOINT_B_ID})
        for row in pending:
            self.assertEqual(row["case_ref"], "demo_phase")
            self.assertIn("created_at", row)

    def test_record_human_decision_checkpoint_a_approve(self) -> None:
        write_checkpoint(_sample_checkpoint_a(), **self.extra)
        resume = record_human_decision(
            CHECKPOINT_A_ID,
            "approve",
            "approved by test",
            operator_id="operator_001",
            **self.extra,
        )

        self.assertEqual(resume["checkpoint_id"], CHECKPOINT_A_ID)
        self.assertEqual(resume["case_ref"], "demo_phase")
        self.assertEqual(resume["resume_from"], "selector")
        self.assertEqual(resume["human_decision"]["action"], "approve")
        self.assertEqual(resume["human_decision"]["by"], "operator_001")
        self.assertEqual(
            resume["original_decision"],
            {"decision": "needs_review", "risk_level": "medium"},
        )
        self.assertEqual(
            resume["planned_tools"],
            [
                "validate.eligibility",
                "clean.phase_demo",
                "export.delivery_bundle",
            ],
        )
        self.assertEqual(resume["selector_task_type"], "e2e")

        pending = list_pending_checkpoints(**self.extra)
        self.assertEqual(pending, [])

    def test_record_human_decision_checkpoint_b_approve_delivery(self) -> None:
        write_checkpoint(_sample_checkpoint_b(), **self.extra)
        resume = record_human_decision(
            CHECKPOINT_B_ID,
            "approve_delivery",
            notes="ship it",
            operator_id="operator_002",
            **self.extra,
        )

        self.assertEqual(resume["checkpoint_id"], CHECKPOINT_B_ID)
        self.assertEqual(resume["resume_from"], "delivery")
        self.assertEqual(resume["human_decision"]["action"], "approve_delivery")
        self.assertIn("artifacts", resume)
        self.assertEqual(
            resume["original_decision"]["output_guard_status"],
            "ok",
        )

    def test_resume_context_revise_plan_uses_gate(self) -> None:
        checkpoint = _sample_checkpoint_a()
        human = {
            "action": "revise_plan",
            "by": "operator_001",
            "at": "2026-06-10T08:32:00Z",
        }
        resume = build_resume_context(checkpoint, human)
        self.assertEqual(resume["resume_from"], "gate")

    def test_resume_context_hold_has_no_resume_from(self) -> None:
        checkpoint = _sample_checkpoint_b()
        human = {
            "action": "hold",
            "by": "operator_002",
            "at": "2026-06-10T08:33:00Z",
        }
        resume = build_resume_context(checkpoint, human)
        self.assertIsNone(resume["resume_from"])

    def test_reject_writes_only_under_outbox(self) -> None:
        root = outbox_root(self.repo_root)
        outside = self.repo_root / "cases" / "evil.json"
        outside.parent.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(ValueError):
            from hitl.checkpoints_v1 import _assert_under_outbox

            _assert_under_outbox(outside, root)

    def test_append_checkpoint_event_rejects_outside_outbox(self) -> None:
        outside = self.repo_root / "checkpoint_events.jsonl"
        with self.assertRaises(ValueError):
            append_checkpoint_event(
                {"event": "bad"},
                repo_root=self.repo_root,
                outbox_root_override=str(self.repo_root),
            )

    def test_validate_checkpoint_requires_schema(self) -> None:
        bad = dict(_sample_checkpoint_a())
        bad.pop("schema_version")
        with self.assertRaises(ValueError):
            validate_checkpoint(bad)


if __name__ == "__main__":
    unittest.main()
