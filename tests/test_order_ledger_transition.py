"""Unit tests for order status transitions (WC-M3 sandbox)."""

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

from dispatch_executor import parse_ticket_state_markdown  # noqa: E402
from order_ledger.models import (  # noqa: E402
    ORDER_STATUS_DRAFT,
    ORDER_STATUS_PAID,
    ORDER_STATUS_PENDING_PAYMENT,
)
from order_ledger.service import create_order_for_ticket, lookup_order, transition_order  # noqa: E402
from order_ledger.store import InMemoryOrderLedgerStore, JsonlFileStore  # noqa: E402

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "order_ledger"


def _load_ready_ticket():
    path = _FIXTURES / "ticket_ready_for_order.md"
    text = path.read_text(encoding="utf-8")
    return parse_ticket_state_markdown(text, path, repo_root=_REPO_ROOT)


def _create_draft_order(store) -> str:
    ticket = _load_ready_ticket()
    created = create_order_for_ticket(store, ticket, 10000, "TWD")
    assert created["ok"]
    return created["order"]["order_id"]


class TestOrderStatusTransition(unittest.TestCase):
    def test_draft_to_pending_payment_ok(self) -> None:
        store = InMemoryOrderLedgerStore()
        order_id = _create_draft_order(store)
        result = transition_order(store, order_id, "pending_payment", actor="test", reason="unit")
        self.assertTrue(result["ok"])
        self.assertEqual(result["message"], "order_transitioned")
        self.assertEqual(result["from_status"], ORDER_STATUS_DRAFT)
        self.assertEqual(result["to_status"], ORDER_STATUS_PENDING_PAYMENT)
        order = result["order"]
        self.assertEqual(order["order_status"], ORDER_STATUS_PENDING_PAYMENT)
        self.assertTrue(order["transitioned_at"])
        self.assertEqual(order["actor"], "test")
        self.assertEqual(order["reason"], "unit")

    def test_pending_to_paid_ok(self) -> None:
        store = InMemoryOrderLedgerStore()
        order_id = _create_draft_order(store)
        transition_order(store, order_id, "pending_payment")
        result = transition_order(store, order_id, "paid", actor="cli", reason="pay")
        self.assertTrue(result["ok"])
        self.assertEqual(result["to_status"], ORDER_STATUS_PAID)
        self.assertEqual(result["order"]["order_status"], ORDER_STATUS_PAID)

    def test_draft_to_paid_invalid(self) -> None:
        store = InMemoryOrderLedgerStore()
        order_id = _create_draft_order(store)
        result = transition_order(store, order_id, "paid")
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "invalid_transition")
        self.assertEqual(result["from_status"], ORDER_STATUS_DRAFT)
        self.assertEqual(result["to_status"], ORDER_STATUS_PAID)

    def test_paid_to_pending_invalid(self) -> None:
        store = InMemoryOrderLedgerStore()
        order_id = _create_draft_order(store)
        transition_order(store, order_id, "pending_payment")
        transition_order(store, order_id, "paid")
        result = transition_order(store, order_id, "pending_payment")
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "invalid_transition")

    def test_order_not_found(self) -> None:
        store = InMemoryOrderLedgerStore()
        result = transition_order(store, "ORD-MISSING", "pending_payment")
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "order_not_found")

    def test_jsonl_audit_fields_on_transition(self) -> None:
        ticket = _load_ready_ticket()
        with tempfile.TemporaryDirectory() as tmp:
            jsonl_path = Path(tmp) / "orders.jsonl"
            store = JsonlFileStore(jsonl_path)
            create_order_for_ticket(store, ticket, 5000, "USD")
            order_id = "ORD-WC-T4"
            transition_order(store, order_id, "pending_payment", actor="jsonl-test", reason="audit")

            reloaded = JsonlFileStore(jsonl_path)
            found = lookup_order(reloaded, order_id=order_id)
            self.assertTrue(found["ok"])
            self.assertEqual(found["order"]["order_status"], ORDER_STATUS_PENDING_PAYMENT)
            self.assertEqual(found["order"]["actor"], "jsonl-test")
            self.assertEqual(found["order"]["reason"], "audit")
            self.assertTrue(found["order"]["transitioned_at"])

            lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            latest = json.loads(lines[-1])
            self.assertEqual(latest["order_status"], ORDER_STATUS_PENDING_PAYMENT)
            self.assertIn("transitioned_at", latest)
            self.assertIn("actor", latest)
            self.assertIn("reason", latest)


if __name__ == "__main__":
    unittest.main()
