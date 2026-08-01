"""Tests for P8-T2c checkpoint preview CLI (read-only)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hitl.checkpoints_v1 import CHECKPOINT_A_ID, write_checkpoint
from scripts.preview_checkpoint_v1 import preview_checkpoint
from tools.tabular_outbox_writer import outbox_root


class TestPreviewCheckpointV1(unittest.TestCase):
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

    def _write_pending(self, case_ref: str = "demo_phase") -> Path:
        write_checkpoint(
            {
                "schema_version": "hitl_checkpoint_v1",
                "checkpoint_id": CHECKPOINT_A_ID,
                "case_ref": case_ref,
                "status": "awaiting_human",
                "created_at": "2026-07-13T12:00:00Z",
                "task_type": "tabular.cleaning.mvp",
                "agent_output": {
                    "task_type": "tabular.cleaning.mvp",
                    "intake_decision": {
                        "decision": "review_needed",
                        "risk_level": "medium",
                        "rationale": ["needs human"],
                        "suggested_route": {"planned_tools": ["validate.eligibility"]},
                    },
                    "gate_preview": {
                        "eligibility": "ok",
                        "exit_code": 0,
                        "reason_code": None,
                    },
                },
                "human_decision": None,
                "resume_context": None,
            },
            **self.extra,
        )
        matches = list((self.outbox / case_ref).glob("*.json"))
        self.assertTrue(matches)
        return matches[0]

    def test_preview_by_path_ok(self) -> None:
        path = self._write_pending()
        result = preview_checkpoint(checkpoint_path=str(path), **self.extra)
        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["mutated"])
        self.assertEqual(result["schema_version"], "checkpoint_preview_v1")
        preview = result["preview"]
        self.assertEqual(preview["checkpoint_id"], CHECKPOINT_A_ID)
        self.assertEqual(preview["case_ref"], "demo_phase")
        self.assertEqual(preview["status"], "awaiting_human")
        self.assertTrue(preview.get("suggested_actions"))

    def test_path_outside_outbox_fail_close(self) -> None:
        outside = self.repo_root / "not_outbox" / "cp.json"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_text("{}", encoding="utf-8")
        result = preview_checkpoint(checkpoint_path=str(outside), **self.extra)
        self.assertFalse(result["ok"])
        self.assertIn("outbox", result["message"].lower())

    def test_preview_by_id_and_case_ref(self) -> None:
        self._write_pending("case_a")
        self._write_pending("case_b")
        result = preview_checkpoint(
            checkpoint_id=CHECKPOINT_A_ID,
            case_ref="case_b",
            **self.extra,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["preview"]["case_ref"], "case_b")

    def test_missing_id_fail(self) -> None:
        result = preview_checkpoint(
            checkpoint_id="Z-does-not-exist",
            **self.extra,
        )
        self.assertFalse(result["ok"])

    def test_no_mutation_side_effect(self) -> None:
        path = self._write_pending()
        before = path.read_text(encoding="utf-8")
        preview_checkpoint(checkpoint_path=str(path), **self.extra)
        after = path.read_text(encoding="utf-8")
        self.assertEqual(before, after)
        self.assertEqual(json.loads(before)["status"], "awaiting_human")


if __name__ == "__main__":
    unittest.main()
