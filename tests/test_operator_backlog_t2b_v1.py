"""Tests for P8-T2b batch-approve + resume-latest-approved."""

from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from hitl.checkpoints_v1 import CHECKPOINT_A_ID, write_checkpoint
from scripts.list_operator_backlog_v1 import (
    batch_approve_pending,
    resume_latest_approved,
)
from tools.tabular_outbox_writer import outbox_root


class TestOperatorBacklogT2b(unittest.TestCase):
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

    def _write_pending(self, case_ref: str, task_type: str, created_at: str) -> None:
        write_checkpoint(
            {
                "schema_version": "hitl_checkpoint_v1",
                "checkpoint_id": CHECKPOINT_A_ID,
                "case_ref": case_ref,
                "status": "awaiting_human",
                "created_at": created_at,
                "task_type": task_type,
                "agent_output": {"task_type": task_type},
                "human_decision": None,
                "resume_context": None,
            },
            **self.extra,
        )

    def _write_approved(self, case_ref: str, task_type: str, created_at: str) -> None:
        write_checkpoint(
            {
                "schema_version": "hitl_checkpoint_v1",
                "checkpoint_id": CHECKPOINT_A_ID,
                "case_ref": case_ref,
                "status": "approved",
                "created_at": created_at,
                "resolved_at": created_at,
                "task_type": task_type,
                "agent_output": {"task_type": task_type},
                "human_decision": {
                    "action": "approve",
                    "by": "op",
                    "at": created_at,
                },
                "resume_context": {
                    "checkpoint_id": CHECKPOINT_A_ID,
                    "case_ref": case_ref,
                    "resume_from": "selector",
                    "human_decision": {"action": "approve"},
                    "original_decision": {},
                },
            },
            **self.extra,
        )

    def test_batch_approve_same_task_type(self) -> None:
        self._write_pending("case_a", "tabular.cleaning.mvp", "2026-07-13T10:00:00Z")
        self._write_pending("case_b", "tabular.cleaning.mvp", "2026-07-13T10:01:00Z")
        self._write_pending("case_other", "other.task", "2026-07-13T10:02:00Z")

        dry = batch_approve_pending(
            task_type="tabular.cleaning.mvp",
            dry_run=True,
            **self.extra,
        )
        self.assertTrue(dry["ok"])
        self.assertEqual(dry["count_would_approve"], 2)

        result = batch_approve_pending(
            task_type="tabular.cleaning.mvp",
            dry_run=False,
            **self.extra,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["count_approved"], 2)
        approved_refs = {row["case_ref"] for row in result["approved"]}
        self.assertEqual(approved_refs, {"case_a", "case_b"})
        # other task_type untouched
        skipped_other = [
            row for row in result["skipped"] if row.get("case_ref") == "case_other"
        ]
        self.assertTrue(skipped_other)

    def test_batch_approve_requires_task_type(self) -> None:
        result = batch_approve_pending(task_type="", **self.extra)
        self.assertFalse(result["ok"])
        self.assertIn("task_type", result["message"])

    def test_resume_latest_fail_close_multiple(self) -> None:
        self._write_approved("case_a", "tabular.cleaning.mvp", "2026-07-13T11:00:00Z")
        self._write_approved("case_b", "tabular.cleaning.mvp", "2026-07-13T11:01:00Z")

        multi = resume_latest_approved(
            task_type="tabular.cleaning.mvp",
            **self.extra,
        )
        self.assertFalse(multi["ok"])
        self.assertTrue(multi.get("fail_close"))
        self.assertEqual(multi["count_options"], 2)

        single = resume_latest_approved(
            task_type="tabular.cleaning.mvp",
            case_ref="case_b",
            **self.extra,
        )
        self.assertTrue(single["ok"])
        self.assertEqual(single["selected"]["case_ref"], "case_b")
        self.assertFalse(single.get("executed_resume"))

    def test_resume_latest_single_ok(self) -> None:
        self._write_approved("only_one", "tabular.cleaning.mvp", "2026-07-13T12:00:00Z")
        result = resume_latest_approved(
            task_type="tabular.cleaning.mvp",
            **self.extra,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["selected"]["case_ref"], "only_one")
        self.assertIn("resume-checkpoint", result.get("resume_hint", ""))


if __name__ == "__main__":
    unittest.main()
