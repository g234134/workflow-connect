"""Unit tests for feedback ingest v1 (P8.9-T2)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery import feedback_ingest_v1 as ingest
from delivery import notification_gateway_v1 as gw


def _write_notification(
    outbox: Path,
    *,
    case_ref: str = "demo_phase",
    event_type: str = "run.completed",
) -> dict:
    event = gw.build_notification_event(event_type, case_ref=case_ref, source={"step_id": "S14"})
    gw.send_notification(event, enabled=True, outbox_root_override=str(outbox))
    return event


class TestFeedbackIngestV1(unittest.TestCase):
    def test_record_downstream_ack_received_writes_ack_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = _write_notification(outbox)
            result = ingest.record_downstream_ack(
                event["event_id"],
                "local_handler_v1",
                "received",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertTrue(result["ok"])
            self.assertFalse(result["idempotent_skip"])
            self.assertIn("outbox/feedback/demo_phase/acks/", result["ack_path"])
            ack_path = Path(tmp) / result["ack_path"]
            self.assertTrue(ack_path.is_file())
            data = json.loads(ack_path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "downstream_ack_v1")
            self.assertEqual(data["feedback_kind"], "downstream_ack")
            self.assertEqual(data["status"], "received")

    def test_record_downstream_ack_failed_sets_message_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = _write_notification(outbox)
            result = ingest.record_downstream_ack(
                event["event_id"],
                "local_handler_v1",
                "failed",
                message="handler timeout",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertTrue(result["ok"])
            data = json.loads((Path(tmp) / result["ack_path"]).read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "failed")
            self.assertEqual(data["message"], "handler timeout")

    def test_duplicate_ack_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = _write_notification(outbox)
            first = ingest.record_downstream_ack(
                event["event_id"],
                "local_handler_v1",
                "received",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            second = ingest.record_downstream_ack(
                event["event_id"],
                "local_handler_v1",
                "received",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            self.assertFalse(first["idempotent_skip"])
            self.assertTrue(second["idempotent_skip"])

    def test_ingest_pending_events_lists_unacked_notifications(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            e1 = _write_notification(outbox, event_type="checkpoint.awaiting_human")
            e2 = _write_notification(outbox, event_type="run.completed")
            result = ingest.ingest_pending_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["pending_count"], 2)
            ids = {p["event_id"] for p in result["pending"]}
            self.assertEqual(ids, {e1["event_id"], e2["event_id"]})
            for item in result["pending"]:
                self.assertEqual(item["case_ref"], "demo_phase")
                self.assertIn("event_type", item)
                self.assertIn("emitted_at", item)

    def test_ingest_dry_run_does_not_write_ack_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            _write_notification(outbox)
            ingest.ingest_pending_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            acks_dir = outbox / "feedback" / "demo_phase" / "acks"
            ack_files = list(acks_dir.glob("*.json")) if acks_dir.is_dir() else []
            self.assertEqual(ack_files, [])

    def test_ingest_after_ack_reduces_pending_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = _write_notification(outbox)
            before = ingest.ingest_pending_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            ingest.record_downstream_ack(
                event["event_id"],
                "local_handler_v1",
                "received",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            after = ingest.ingest_pending_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertEqual(before["pending_count"], 1)
            self.assertEqual(after["pending_count"], 0)

    def test_record_ack_unknown_event_id_returns_ok_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = ingest.record_downstream_ack(
                str(uuid.uuid4()),
                "local_handler_v1",
                "received",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertFalse(result["ok"])
            self.assertIn("unknown event_id", result["message"])


if __name__ == "__main__":
    unittest.main()
