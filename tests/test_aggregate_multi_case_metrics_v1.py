"""Unit tests for multi-case metrics aggregator v1 (MC-METRICS)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from delivery import feedback_ingest_v1 as ingest
from delivery import notification_gateway_v1 as gw
from hitl.checkpoints_v1 import CHECKPOINT_A_ID, write_checkpoint
from scripts.aggregate_multi_case_metrics_v1 import aggregate_multi_case_metrics
from tools.tabular_outbox_writer import outbox_root


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


class TestAggregateMultiCaseMetricsV1(unittest.TestCase):
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

    def test_aggregator_sums_pending_blocked_completed_across_cases(self) -> None:
        pending_ref = "fleet_pending_case"
        blocked_ref = "fleet_blocked_case"
        completed_ref = "fleet_completed_case"

        write_checkpoint(
            {
                "schema_version": "hitl_checkpoint_v1",
                "checkpoint_id": CHECKPOINT_A_ID,
                "case_ref": pending_ref,
                "status": "awaiting_human",
                "created_at": "2026-06-19T12:00:00Z",
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
            emitted_at="2026-06-19T12:05:00Z",
        )
        write_checkpoint(
            {
                "schema_version": "hitl_checkpoint_v1",
                "checkpoint_id": CHECKPOINT_A_ID,
                "case_ref": completed_ref,
                "status": "approved",
                "created_at": "2026-06-19T12:10:00Z",
                "task_type": "tabular.cleaning.mvp",
                "agent_output": {
                    "task_type": "tabular.cleaning.mvp",
                    "intake_gate": {"decision": "accept"},
                },
                "human_decision": {"action": "approve", "by": "operator", "at": "2026-06-19T12:11:00Z"},
                "resume_context": None,
            },
            **self.extra,
        )
        _append_notification(
            self.outbox,
            case_ref=completed_ref,
            event_type="run.completed",
            emitted_at="2026-06-19T12:15:00Z",
        )

        result = aggregate_multi_case_metrics(
            [pending_ref, blocked_ref, completed_ref],
            **self.extra,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["schema_version"], "multi_case_metrics_v1")
        self.assertEqual(result["case_count"], 3)
        metrics = result["metrics"]
        self.assertEqual(metrics["total_pending_cases"], 1)
        self.assertEqual(metrics["total_blocked_cases"], 1)
        self.assertEqual(metrics["total_completed_cases"], 1)
        self.assertEqual(len(result["per_case"]), 3)

    def test_aggregator_sums_ack_metrics_across_cases(self) -> None:
        case_a = "fleet_ack_case_a"
        case_b = "fleet_ack_case_b"

        pending_a = _append_notification(
            self.outbox,
            case_ref=case_a,
            event_type="checkpoint.awaiting_human",
        )
        failed_b = _append_notification(
            self.outbox,
            case_ref=case_b,
            event_type="run.blocked",
        )
        acked_b = _append_notification(
            self.outbox,
            case_ref=case_b,
            event_type="run.completed",
        )

        ingest.record_downstream_ack(
            failed_b["event_id"],
            "handler_a",
            "failed",
            message="timeout",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        ingest.record_downstream_ack(
            acked_b["event_id"],
            "handler_a",
            "received",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )

        result = aggregate_multi_case_metrics([case_a, case_b], **self.extra)
        metrics = result["metrics"]

        self.assertEqual(metrics["total_notifications_emitted"], 3)
        self.assertEqual(metrics["total_notifications_pending_ack"], 1)
        self.assertEqual(metrics["total_notifications_failed_ack"], 1)
        pending_ids = {
            item["event_id"]
            for item in ingest.ingest_pending_events(
                case_a,
                repo_root=self.repo_root,
                outbox_root_override=str(self.outbox),
            )["pending"]
        }
        self.assertEqual(pending_ids, {pending_a["event_id"]})

    def test_aggregator_handles_empty_case_list(self) -> None:
        result = aggregate_multi_case_metrics([], **self.extra)

        self.assertTrue(result["ok"])
        self.assertEqual(result["case_count"], 0)
        self.assertEqual(result["cases"], [])
        metrics = result["metrics"]
        self.assertEqual(metrics["total_pending_cases"], 0)
        self.assertEqual(metrics["total_blocked_cases"], 0)
        self.assertEqual(metrics["total_completed_cases"], 0)
        self.assertEqual(metrics["total_notifications_emitted"], 0)
        self.assertEqual(metrics["total_notifications_failed_ack"], 0)
        self.assertEqual(metrics["total_notifications_pending_ack"], 0)
        self.assertEqual(result["per_case"], [])


if __name__ == "__main__":
    unittest.main()
