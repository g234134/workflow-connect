"""Unit tests for operator backlog v1 (P8-T2)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hitl.checkpoint_a_integration_v1 import maybe_create_checkpoint_a
from hitl.checkpoints_v1 import CHECKPOINT_A_ID, write_checkpoint
from routing.intake_decision_rules_v1 import evaluate_intake_decision
from scripts.list_operator_backlog_v1 import (
    build_backlog_entry,
    classify_operator_status,
    list_operator_backlog,
)
from delivery import notification_gateway_v1 as gw
from tools.tabular_outbox_writer import outbox_root

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _append_notification(
    outbox: Path,
    *,
    case_ref: str,
    event_type: str,
    emitted_at: str | None = None,
) -> dict:
    event = gw.build_notification_event(
        event_type,
        case_ref=case_ref,
        source={"step_id": "S14"},
    )
    if emitted_at:
        event["emitted_at"] = emitted_at
    jsonl = outbox / "notification_events.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
    return event


class TestOperatorBacklogV1(unittest.TestCase):
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

    def test_backlog_lists_case_with_open_checkpoint_a(self) -> None:
        decision = evaluate_intake_decision("tabular.cleaning.mvp", "cases/demo_phase")
        result = maybe_create_checkpoint_a(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            decision,
            **self.extra,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "awaiting_human")

        _append_notification(
            self.outbox,
            case_ref="demo_phase",
            event_type="checkpoint.awaiting_human",
        )

        backlog = list_operator_backlog(
            status="pending",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        items = backlog["items"]
        self.assertGreaterEqual(len(items), 1)
        row = next(item for item in items if item["case_ref"] == "demo_phase")
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["checkpoint_a_status"], "awaiting_human")
        self.assertIn(row["last_event_type"], ("checkpoint.awaiting_human", "checkpoint.created"))

    def test_backlog_does_not_list_completed_case(self) -> None:
        case_ref = "completed_case"
        checkpoint = {
            "schema_version": "hitl_checkpoint_v1",
            "checkpoint_id": CHECKPOINT_A_ID,
            "case_ref": case_ref,
            "status": "approved",
            "created_at": "2026-06-19T10:00:00Z",
            "task_type": "tabular.cleaning.mvp",
            "agent_output": {
                "task_type": "tabular.cleaning.mvp",
                "intake_gate": {"decision": "accept"},
            },
            "human_decision": {"action": "approve", "by": "operator", "at": "2026-06-19T10:05:00Z"},
            "resume_context": None,
        }
        write_checkpoint(checkpoint, **self.extra)
        _append_notification(
            self.outbox,
            case_ref=case_ref,
            event_type="run.completed",
            emitted_at="2026-06-19T10:10:00Z",
        )

        pending = list_operator_backlog(
            status="pending",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        self.assertNotIn(
            case_ref,
            [item["case_ref"] for item in pending["items"]],
        )

        completed = list_operator_backlog(
            status="completed",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        row = next(item for item in completed["items"] if item["case_ref"] == case_ref)
        self.assertEqual(row["status"], "completed")
        self.assertEqual(row["checkpoint_a_status"], "approved")

    def test_backlog_filters_by_status(self) -> None:
        pending_ref = "pending_case"
        blocked_ref = "blocked_case"

        write_checkpoint(
            {
                "schema_version": "hitl_checkpoint_v1",
                "checkpoint_id": CHECKPOINT_A_ID,
                "case_ref": pending_ref,
                "status": "awaiting_human",
                "created_at": "2026-06-19T11:00:00Z",
                "task_type": "tabular.cleaning.mvp",
                "agent_output": {"task_type": "tabular.cleaning.mvp"},
                "human_decision": None,
                "resume_context": None,
            },
            **self.extra,
        )
        _append_notification(
            self.outbox,
            case_ref=blocked_ref,
            event_type="run.blocked",
            emitted_at="2026-06-19T11:05:00Z",
        )

        pending = list_operator_backlog(
            status="pending",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        pending_refs = {item["case_ref"] for item in pending["items"]}
        self.assertIn(pending_ref, pending_refs)
        self.assertNotIn(blocked_ref, pending_refs)

        blocked = list_operator_backlog(
            status="blocked",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        blocked_refs = {item["case_ref"] for item in blocked["items"]}
        self.assertIn(blocked_ref, blocked_refs)
        self.assertNotIn(pending_ref, blocked_refs)

    def test_classify_operator_status_rules(self) -> None:
        self.assertEqual(
            classify_operator_status(
                checkpoint_a_status="awaiting_human",
                intake_decision="needs_review",
                last_terminal_event_type=None,
            ),
            "pending",
        )
        self.assertEqual(
            classify_operator_status(
                checkpoint_a_status="approved",
                intake_decision="accept",
                last_terminal_event_type="run.completed",
            ),
            "completed",
        )
        self.assertEqual(
            classify_operator_status(
                checkpoint_a_status="none",
                intake_decision="accept",
                last_terminal_event_type="run.blocked",
            ),
            "blocked",
        )
        self.assertEqual(
            classify_operator_status(
                checkpoint_a_status="none",
                intake_decision=None,
                last_terminal_event_type=None,
                has_timeline=False,
            ),
            "inactive",
        )

    def test_build_backlog_entry_shape(self) -> None:
        row = build_backlog_entry(
            "empty_case",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        for key in (
            "case_ref",
            "task_type",
            "status",
            "last_event_type",
            "last_updated_at",
            "intake_decision",
            "checkpoint_a_status",
        ):
            self.assertIn(key, row)


if __name__ == "__main__":
    unittest.main()
