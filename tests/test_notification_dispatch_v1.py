"""Unit tests for notification dispatch v1 (P8.9-T3)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery import feedback_ingest_v1 as ingest
from delivery import notification_dispatch_v1 as dispatch
from delivery import notification_gateway_v1 as gw
from delivery import workflow_event_consumer_v1 as consumer


def _failing_handler(
    notification_event: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    ack = context["record_ack"]("failed", message="simulated handler failure")
    return {"ok": False, "message": "simulated handler failure", "ack": ack}


def _exploding_handler(
    notification_event: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    raise RuntimeError("handler exploded")


class TestNotificationDispatchV1(unittest.TestCase):
    def test_registry_can_register_and_find_handler_for_event_type(self) -> None:
        registry = dispatch.HandlerRegistry()

        def _noop(_event: dict, _ctx: dict) -> dict:
            return {"ok": True}

        registry.register_handler("test_handler", ["delivery.bundle_ready"], _noop)
        found = registry.find_handlers("delivery.bundle_ready")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], "test_handler")
        self.assertEqual(registry.find_handlers("unknown.event"), [])

    def test_load_default_handler_registry_from_yaml(self) -> None:
        registry = dispatch.load_default_handler_registry(repo_root=_REPO_ROOT)
        handlers = registry.list_handlers()
        handler_ids = {h["handler_id"] for h in handlers}
        self.assertIn("bundle_ready_log_v1", handler_ids)
        self.assertIn("run_terminal_log_v1", handler_ids)
        bundle_handlers = registry.find_handlers("delivery.bundle_ready")
        self.assertGreaterEqual(len(bundle_handlers), 1)

    def test_dispatch_calls_handler_and_records_ack_received(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = gw.build_notification_event(
                "delivery.bundle_ready",
                case_ref="demo_phase",
                case_dir="cases/demo_phase",
            )
            gw.send_notification(
                event,
                enabled=True,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            registry = dispatch.load_default_handler_registry(repo_root=_REPO_ROOT)
            result = dispatch.dispatch_event(
                event,
                handler_registry=registry,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertTrue(result["ok"])
            self.assertIn("bundle_ready_log_v1", result["handlers_invoked"])

            consumer_result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            row = next(r for r in consumer_result["events"] if r["native_id"] == event["event_id"])
            self.assertEqual(row["tracking_status"], "acked")
            self.assertIsNone(row["last_error"])

    def test_dispatch_handles_handler_failure_and_records_ack_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = gw.build_notification_event("run.completed", case_ref="demo_phase")
            gw.send_notification(
                event,
                enabled=True,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            registry = dispatch.HandlerRegistry()
            registry.register_handler("fail_handler_v1", ["run.completed"], _failing_handler)
            result = dispatch.dispatch_event(
                event,
                handler_registry=registry,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertFalse(result["ok"])
            handler_result = result["handler_results"][0]
            self.assertFalse(handler_result["ok"])
            self.assertTrue(handler_result["ack"]["ok"])

            consumer_result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            row = next(r for r in consumer_result["events"] if r["native_id"] == event["event_id"])
            self.assertEqual(row["tracking_status"], "failed")
            self.assertEqual(row["last_error"], "simulated handler failure")

    def test_dispatch_unknown_event_type_noop_and_does_not_raise(self) -> None:
        registry = dispatch.HandlerRegistry()
        result = dispatch.dispatch_event(
            {"event_id": "x", "event_type": "does.not.exist", "case_ref": "demo_phase"},
            handler_registry=registry,
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result.get("noop"))
        self.assertEqual(result["handlers_invoked"], [])

    def test_dispatch_handler_exception_records_failed_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = gw.build_notification_event("run.blocked", case_ref="demo_phase")
            gw.send_notification(
                event,
                enabled=True,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            registry = dispatch.HandlerRegistry()
            registry.register_handler("boom_handler_v1", ["run.blocked"], _exploding_handler)
            result = dispatch.dispatch_event(
                event,
                handler_registry=registry,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertFalse(result["ok"])
            self.assertIn("handler exploded", result["handler_results"][0]["message"])

            consumer_result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            row = next(r for r in consumer_result["events"] if r["native_id"] == event["event_id"])
            self.assertEqual(row["tracking_status"], "failed")
            self.assertIn("handler exploded", row["last_error"])

    def test_gateway_post_emit_dispatch_fail_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = gw.build_notification_event("delivery.bundle_ready", case_ref="demo_phase")
            result = gw.send_notification(
                event,
                enabled=True,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
                dispatch_enabled=True,
            )
            self.assertTrue(result["ok"])
            self.assertIn("dispatch_result", result)
            dispatch_result = result["dispatch_result"]
            self.assertIsNotNone(dispatch_result)
            self.assertIn("bundle_ready_log_v1", dispatch_result.get("handlers_invoked", []))

    def test_gateway_emit_without_dispatch_leaves_pending_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = gw.build_notification_event("delivery.bundle_ready", case_ref="demo_phase")
            result = gw.send_notification(
                event,
                enabled=True,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
                dispatch_enabled=False,
            )
            self.assertTrue(result["ok"])
            self.assertNotIn("dispatch_result", result)

            consumer_result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            row = next(r for r in consumer_result["events"] if r["native_id"] == event["event_id"])
            self.assertEqual(row["tracking_status"], "pending_ack")

    def test_emit_dispatch_ack_e2e_consumer_shows_acked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            event = gw.build_notification_event(
                "delivery.bundle_ready",
                case_ref="demo_phase",
                case_dir="cases/demo_phase",
            )
            emit_result = gw.send_notification(
                event,
                enabled=True,
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
                dispatch_enabled=True,
            )
            self.assertTrue(emit_result["ok"])

            pending = ingest.ingest_pending_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            self.assertEqual(pending["pending_count"], 0)

            consumer_result = consumer.load_workflow_events(
                "demo_phase",
                repo_root=Path(tmp),
                outbox_root_override=str(outbox),
            )
            row = next(r for r in consumer_result["events"] if r["native_id"] == event["event_id"])
            self.assertEqual(row["tracking_status"], "acked")
            ack_path = Path(tmp) / str(row["ack_path"])
            self.assertTrue(ack_path.is_file())
            ack_data = json.loads(ack_path.read_text(encoding="utf-8"))
            self.assertEqual(ack_data["handler_id"], "bundle_ready_log_v1")
            self.assertEqual(ack_data["status"], "received")


if __name__ == "__main__":
    unittest.main()
