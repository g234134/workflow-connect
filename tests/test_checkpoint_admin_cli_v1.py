"""Unit tests for Checkpoint Admin CLI v1 (TAB-W4-H1)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from checkpoint_admin import cmd_expire, cmd_list, cmd_requeue  # noqa: E402
from hitl.checkpoints_v1 import CHECKPOINT_A_ID, CHECKPOINT_SCHEMA_VERSION, write_checkpoint  # noqa: E402
from tabular_automation_state_lib import load_state  # noqa: E402
from tabular_checkpoint_sync_lib import EXPIRED_CP_STATUS  # noqa: E402

_ANCHOR_CASE_IDS = frozenset({"demo_phase", "2026-0001", "generic-low-risk"})
_REQUIRED_LIST_KEYS = frozenset(
    {
        "case_id",
        "checkpoint_id",
        "cp_type",
        "status",
    }
)


def _seed_pending_case(root: Path, *, case_id: str = "admin_test_case") -> Path:
    case_dir = root / "cases" / case_id
    case_dir.mkdir(parents=True)
    (case_dir / "intake.json").write_text(
        json.dumps({"case_id": case_id, "client_ref": "internal-test"}),
        encoding="utf-8",
    )
    (case_dir / "automation_state.json").write_text(
        json.dumps(
            {
                "schema_version": "tabular-automation-state-v1",
                "case_id": case_id,
                "automation_status": "paused",
                "pause_reason": "awaiting_checkpoint_a",
                "checkpoint_a_status": "pending",
                "checkpoint_b_status": "not_required",
                "last_transition_ts": "2026-07-01T10:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    return case_dir


def _sample_outbox_checkpoint(case_ref: str) -> dict:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_A_ID,
        "case_ref": case_ref,
        "run_id": "2026-07-01T10-00-00Z_intake_confirm",
        "status": "awaiting_human",
        "created_at": "2026-07-01T10:00:00Z",
        "expires_at": "2026-07-01T10:05:00Z",
        "task_type": "tabular.cleaning.mvp",
        "agent_output": {
            "task_type": "tabular.cleaning.mvp",
            "intake_decision": {
                "decision": "needs_review",
                "risk_level": "medium",
                "rationale": ["manual_review_required"],
                "suggested_route": {
                    "selector_task_type": "e2e",
                    "planned_tools": ["validate.eligibility"],
                },
            },
        },
    }


class TestCheckpointAdminCliV1(unittest.TestCase):
    def test_list_pending_checkpoints_returns_known_demo_cases(self) -> None:
        result = cmd_list(root=_REPO_ROOT)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("action"), "list")
        self.assertIn("items", result)
        self.assertIn("count", result)
        self.assertIsInstance(result["items"], list)

        for item in result["items"]:
            for key in _REQUIRED_LIST_KEYS:
                self.assertIn(key, item)
            self.assertNotIn(
                item.get("status"),
                {"approved", "rejected", EXPIRED_CP_STATUS},
            )

        listed_case_ids = {row.get("case_id") for row in result["items"]}
        for anchor in _ANCHOR_CASE_IDS:
            if anchor in listed_case_ids:
                row = next(r for r in result["items"] if r.get("case_id") == anchor)
                self.assertIn(row.get("cp_type"), {"cp_a", "cp_b"})
                self.assertIn(row.get("status"), {"awaiting_decision", "pending", "awaiting_human"})

    def test_expire_checkpoint_marks_status_expired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_id = "expire_case"
            case_dir = _seed_pending_case(root, case_id=case_id)
            write_checkpoint(
                _sample_outbox_checkpoint(case_id),
                repo_root=root,
            )

            result = cmd_expire(
                root=root,
                checkpoint_id=CHECKPOINT_A_ID,
                cp_type=None,
                case_id=case_id,
                case_dir=None,
                reason="operator triage SLA",
            )
            self.assertTrue(result.get("ok"), result)
            checkpoint = result.get("checkpoint") or {}
            self.assertEqual(checkpoint.get("status"), EXPIRED_CP_STATUS)
            self.assertEqual(checkpoint.get("expire_reason"), "operator triage SLA")

            state = load_state(case_dir)
            self.assertEqual(state.get("checkpoint_a_status"), EXPIRED_CP_STATUS)

            outbox_files = list((root / "outbox" / case_id).glob("checkpoint_*.json"))
            self.assertTrue(outbox_files)
            payload = json.loads(outbox_files[0].read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), EXPIRED_CP_STATUS)

            list_after = cmd_list(root=root)
            self.assertEqual(list_after.get("count"), 0)

    def test_requeue_checkpoint_restores_pending_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_id = "requeue_case"
            case_dir = _seed_pending_case(root, case_id=case_id)
            write_checkpoint(
                _sample_outbox_checkpoint(case_id),
                repo_root=root,
            )

            expired = cmd_expire(
                root=root,
                checkpoint_id=CHECKPOINT_A_ID,
                cp_type=None,
                case_id=case_id,
                case_dir=None,
                reason="test expire",
            )
            self.assertTrue(expired.get("ok"), expired)

            result = cmd_requeue(
                root=root,
                checkpoint_id=CHECKPOINT_A_ID,
                cp_type=None,
                case_id=case_id,
                case_dir=None,
            )
            self.assertTrue(result.get("ok"), result)
            checkpoint = result.get("checkpoint") or {}
            self.assertEqual(checkpoint.get("status"), "awaiting_decision")

            state = load_state(case_dir)
            self.assertEqual(state.get("checkpoint_a_status"), "pending")
            self.assertEqual(state.get("pause_reason"), "awaiting_checkpoint_a")

            outbox_files = list((root / "outbox" / case_id).glob("checkpoint_*.json"))
            payload = json.loads(outbox_files[0].read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "awaiting_human")
            self.assertIsNone(payload.get("human_decision"))

            list_after = cmd_list(root=root)
            self.assertEqual(list_after.get("count"), 1)


if __name__ == "__main__":
    unittest.main()
