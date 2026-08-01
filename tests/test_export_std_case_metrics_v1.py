"""Unit tests for standard-case metrics exporter v1 (MP-METRICS)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from delivery import feedback_ingest_v1 as ingest
from delivery import notification_gateway_v1 as gw
from hitl.checkpoints_v1 import CHECKPOINT_A_ID, write_checkpoint
from scripts.export_std_case_metrics_v1 import export_std_case_metrics
from scripts.list_operator_backlog_v1 import build_backlog_entry
from tools.tabular_outbox_writer import outbox_root

_METRIC_KEYS = (
    "pending_cases_count",
    "blocked_cases_count",
    "completed_cases_count",
    "notifications_emitted_count",
    "notifications_with_pending_ack_count",
    "notifications_failed_ack_count",
)


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


class TestExportStdCaseMetricsV1(unittest.TestCase):
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

    def test_metrics_exporter_returns_expected_keys(self) -> None:
        result = export_std_case_metrics("demo_phase", **self.extra)
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema_version"], "std_case_metrics_v1")
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertTrue(result["read_only"])

        metrics = result["std_case_metrics_v1"]
        for key in _METRIC_KEYS:
            self.assertIn(key, metrics)
            self.assertIsInstance(metrics[key], int)

    def test_metrics_exporter_counts_pending_blocked_completed_consistently_with_backlog(
        self,
    ) -> None:
        pending_ref = "pending_metrics_case"
        blocked_ref = "blocked_metrics_case"
        completed_ref = "completed_metrics_case"

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

        for case_ref, expected_status, expected_field in (
            (pending_ref, "pending", "pending_cases_count"),
            (blocked_ref, "blocked", "blocked_cases_count"),
            (completed_ref, "completed", "completed_cases_count"),
        ):
            backlog = build_backlog_entry(case_ref, **self.extra)
            self.assertEqual(backlog["status"], expected_status)

            exported = export_std_case_metrics(case_ref, **self.extra)
            metrics = exported["std_case_metrics_v1"]
            self.assertEqual(metrics[expected_field], 1)
            self.assertEqual(metrics["pending_cases_count"], 1 if expected_status == "pending" else 0)
            self.assertEqual(metrics["blocked_cases_count"], 1 if expected_status == "blocked" else 0)
            self.assertEqual(metrics["completed_cases_count"], 1 if expected_status == "completed" else 0)

    def test_metrics_exporter_counts_ack_status_consistently_with_consumer(self) -> None:
        case_ref = "ack_metrics_case"
        e_pending = _append_notification(
            self.outbox,
            case_ref=case_ref,
            event_type="checkpoint.awaiting_human",
        )
        e_failed = _append_notification(
            self.outbox,
            case_ref=case_ref,
            event_type="run.blocked",
        )
        e_acked = _append_notification(
            self.outbox,
            case_ref=case_ref,
            event_type="run.completed",
        )

        ingest.record_downstream_ack(
            e_failed["event_id"],
            "handler_a",
            "failed",
            message="timeout",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        ingest.record_downstream_ack(
            e_acked["event_id"],
            "handler_a",
            "received",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )

        ingest_result = ingest.ingest_pending_events(
            case_ref,
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        exported = export_std_case_metrics(case_ref, **self.extra)
        metrics = exported["std_case_metrics_v1"]

        self.assertEqual(metrics["notifications_emitted_count"], 3)
        self.assertEqual(metrics["notifications_with_pending_ack_count"], 1)
        self.assertEqual(metrics["notifications_failed_ack_count"], 1)
        self.assertEqual(
            metrics["notifications_with_pending_ack_count"],
            ingest_result["pending_count"],
        )
        self.assertEqual(exported["sources"]["ingest_pending_count"], ingest_result["pending_count"])

        pending_ids = {item["event_id"] for item in ingest_result["pending"]}
        self.assertEqual(pending_ids, {e_pending["event_id"]})


if __name__ == "__main__":
    unittest.main()
