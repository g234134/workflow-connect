"""Unit tests for workflow event consumer v1 (P8.9-T1 + T2 ack merge)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery import feedback_ingest_v1 as ingest
from delivery import notification_gateway_v1 as gw
from delivery import workflow_event_consumer_v1 as consumer


def _append_notification(outbox: Path, *, case_ref: str, event_type: str) -> dict:
    event = gw.build_notification_event(
        event_type,
        case_ref=case_ref,
        source={"step_id": "S4"},
    )
    jsonl = outbox / "notification_events.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
    return event


class TestWorkflowEventConsumerV1(unittest.TestCase):
    def test_load_workflow_events_returns_stable_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            _append_notification(outbox, case_ref="demo_phase", event_type="run.completed")
            result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertTrue(result["ok"])
            self.assertTrue(result["read_only"])
            self.assertEqual(result["schema_version"], "workflow_event_consumer_v1")
            self.assertEqual(result["case_ref"], "demo_phase")
            self.assertGreaterEqual(result["count"], 1)
            self.assertIn("events", result)
            self.assertIn("timeline", result)
            self.assertIn("count_by_event_type", result)

    def test_consumer_merges_downstream_ack_into_tracking_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = _append_notification(outbox, case_ref="demo_phase", event_type="run.completed")
            ingest.record_downstream_ack(
                event["event_id"],
                "local_handler_v1",
                "received",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            row = next(r for r in result["events"] if r["native_id"] == event["event_id"])
            self.assertEqual(row["tracking_status"], "acked")
            self.assertIsNone(row["last_error"])
            self.assertIsNotNone(row.get("downstream_ack"))
            self.assertIsNotNone(row.get("ack_path"))

    def test_consumer_pending_ack_when_notification_without_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = _append_notification(
                outbox, case_ref="demo_phase", event_type="checkpoint.awaiting_human"
            )
            result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            row = next(r for r in result["events"] if r["native_id"] == event["event_id"])
            self.assertEqual(row["tracking_status"], "pending_ack")
            self.assertIsNone(row.get("downstream_ack"))

    def test_consumer_failed_ack_surfaces_last_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = _append_notification(outbox, case_ref="demo_phase", event_type="run.blocked")
            ingest.record_downstream_ack(
                event["event_id"],
                "local_handler_v1",
                "failed",
                message="dispatch rejected",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            row = next(r for r in result["events"] if r["native_id"] == event["event_id"])
            self.assertEqual(row["tracking_status"], "failed")
            self.assertEqual(row["last_error"], "dispatch rejected")

    def test_filter_by_event_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            e1 = _append_notification(outbox, case_ref="demo_phase", event_type="run.completed")
            _append_notification(outbox, case_ref="demo_phase", event_type="run.blocked")
            result = consumer.load_workflow_events(
                "demo_phase",
                event_id=e1["event_id"],
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["events"][0]["native_id"], e1["event_id"])

    def test_checkpoint_stream_stays_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            outbox.mkdir(parents=True)
            cp_line = {
                "event": "checkpoint_created",
                "checkpoint_id": "A-intake-confirmation",
                "case_ref": "demo_phase",
                "timestamp": "2026-06-16T12:00:00Z",
            }
            (outbox / "checkpoint_events.jsonl").write_text(json.dumps(cp_line) + "\n", encoding="utf-8")
            result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            cp_rows = [r for r in result["events"] if r["source_stream"] == "checkpoint"]
            self.assertEqual(len(cp_rows), 1)
            self.assertEqual(cp_rows[0]["tracking_status"], "recorded")

    def test_inspect_cli_json_output_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            _append_notification(outbox, case_ref="demo_phase", event_type="run.completed")
            script = _REPO_ROOT / "scripts" / "inspect_workflow_events.py"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--case-ref",
                    "demo_phase",
                    "--format",
                    "json",
                    "--repo-root",
                    tmp,
                    "--outbox-root",
                    str(outbox),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["ok"])
            self.assertIn("events", payload)
            self.assertIn("timeline", payload)
            self.assertGreaterEqual(payload["count"], 1)


if __name__ == "__main__":
    unittest.main()
