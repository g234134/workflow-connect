"""Unit tests for WC-T6 Control Plane order handoff loop."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from control_plane_loop.handoff import execute_order_handoff  # noqa: E402
from dispatch_executor import parse_ticket_state_markdown  # noqa: E402
from ticket_comms.message_generator import snapshot_from_ticket_record  # noqa: E402
from ticket_comms.order_events import (  # noqa: E402
    build_order_comms_payload,
    emit_order_comms,
)

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "order_ledger"


def _load_fixture(name: str):
    path = _FIXTURES / name
    text = path.read_text(encoding="utf-8")
    return parse_ticket_state_markdown(text, path, repo_root=_REPO_ROOT)


class TestOrderCommsPayload(unittest.TestCase):
    def test_order_created_payload(self) -> None:
        ticket = _load_fixture("ticket_ready_for_order.md")
        snapshot = snapshot_from_ticket_record(ticket)
        order_result = {
            "ok": True,
            "message": "order_created",
            "replay": False,
            "order": {
                "order_id": "ORD-WC-T4",
                "ticket_id": "WC-T4",
                "amount_minor": 10000,
                "currency": "TWD",
                "order_status": "DRAFT",
            },
        }
        payload = build_order_comms_payload(snapshot, order_result, generated_at="2026-06-13T00:00:00Z")
        self.assertEqual(payload["event_type"], "order_created")
        self.assertIn("ORD-WC-T4", payload["summary"])
        self.assertEqual(payload["order"]["order_id"], "ORD-WC-T4")

    def test_order_rejected_payload(self) -> None:
        ticket = _load_fixture("ticket_not_ready.md")
        snapshot = snapshot_from_ticket_record(ticket)
        order_result = {
            "ok": False,
            "message": "not_ready_for_order",
            "gate": {"ready": False, "gate": "not_ready", "reasons": ["next_action missing keyword"]},
        }
        payload = build_order_comms_payload(snapshot, order_result)
        self.assertEqual(payload["event_type"], "order_rejected")
        self.assertIn("rejected", payload["summary"].lower())


class TestOrderHandoffLoop(unittest.TestCase):
    def test_full_loop_create_and_comms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "orders.jsonl"
            outbox = tmp_path / "comms"
            result = execute_order_handoff(
                _REPO_ROOT,
                "WC-T4",
                10000,
                "TWD",
                ticket_path=_FIXTURES / "ticket_ready_for_order.md",
                orders_jsonl=ledger,
                comms_outbox=outbox,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["message"], "order_handoff_complete")
            self.assertEqual(result["eligibility"]["eligible"], "eligible")
            self.assertIn("bucket", result["dispatch_context"])
            self.assertTrue(result["order"]["ok"])
            self.assertEqual(result["comms"]["event_type"], "order_created")
            self.assertTrue(result["comms"]["sent"])

            comms_log = outbox / "ticket_comms.jsonl"
            self.assertTrue(comms_log.is_file())
            line = json.loads(comms_log.read_text(encoding="utf-8").strip())
            self.assertEqual(line["payload"]["event_type"], "order_created")

    def test_not_ready_with_skip_eligibility_emits_rejection_comms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = execute_order_handoff(
                _REPO_ROOT,
                "WC-T4",
                5000,
                "TWD",
                ticket_path=_FIXTURES / "ticket_not_ready.md",
                orders_jsonl=tmp_path / "orders.jsonl",
                comms_outbox=tmp_path / "comms",
                skip_eligibility=True,
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["order"]["message"], "not_ready_for_order")
            self.assertEqual(result["comms"]["event_type"], "order_rejected")

    def test_ineligible_blocks_without_override(self) -> None:
        result = execute_order_handoff(
            _REPO_ROOT,
            "WC-NOT-READY",
            10000,
            "TWD",
            ticket_path=_FIXTURES / "ticket_not_ready.md",
            requested_role="reviewer",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "ineligible_for_handoff")
        self.assertIsNone(result["order"])

    def test_dry_run_no_ledger_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "orders.jsonl"
            result = execute_order_handoff(
                _REPO_ROOT,
                "WC-T4",
                10000,
                "TWD",
                ticket_path=_FIXTURES / "ticket_ready_for_order.md",
                orders_jsonl=ledger,
                comms_outbox=tmp_path / "comms",
                dry_run=True,
                skip_eligibility=True,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["order"]["message"], "dry_run")
            self.assertEqual(result["comms"]["event_type"], "order_dry_run")
            self.assertFalse(ledger.exists())

    def test_idempotent_replay_comms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "orders.jsonl"
            kwargs = {
                "repo_root": _REPO_ROOT,
                "ticket_id": "WC-T4",
                "amount_minor": 10000,
                "currency": "TWD",
                "ticket_path": _FIXTURES / "ticket_ready_for_order.md",
                "orders_jsonl": ledger,
                "comms_outbox": tmp_path / "comms",
                "skip_eligibility": True,
            }
            first = execute_order_handoff(**kwargs)
            second = execute_order_handoff(**kwargs)
            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            self.assertFalse(first["order"]["replay"])
            self.assertTrue(second["order"]["replay"])
            self.assertEqual(second["comms"]["event_type"], "order_replay")


class TestEmitOrderComms(unittest.TestCase):
    def test_emit_writes_jsonl(self) -> None:
        ticket = _load_fixture("ticket_ready_for_order.md")
        snapshot = snapshot_from_ticket_record(ticket)
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp)
            result = emit_order_comms(
                snapshot,
                {"ok": True, "message": "order_created", "order": {"order_id": "ORD-WC-T4"}},
                outbox_dir=str(outbox),
            )
            self.assertTrue(result["sent"])
            log_path = outbox / "ticket_comms.jsonl"
            self.assertTrue(log_path.is_file())


if __name__ == "__main__":
    unittest.main()
