"""Unit tests for 04_Workflows/order_ledger (WC-T4)."""

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
from order_ledger.gates import (  # noqa: E402
    is_ready_for_order,
    validate_amount_minor,
    validate_currency,
)
from order_ledger.service import create_order_for_ticket, lookup_order  # noqa: E402
from order_ledger.store import InMemoryOrderLedgerStore, JsonlFileStore  # noqa: E402

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "order_ledger"


def _load_fixture(name: str):
    path = _FIXTURES / name
    text = path.read_text(encoding="utf-8")
    return parse_ticket_state_markdown(text, path, repo_root=_REPO_ROOT)


class TestReadyForOrderGate(unittest.TestCase):
    def test_ready_keyword(self) -> None:
        ticket = _load_fixture("ticket_ready_for_order.md")
        gate = is_ready_for_order(ticket)
        self.assertTrue(gate["ready"])
        self.assertEqual(gate["gate"], "keyword")

    def test_not_ready_ticket(self) -> None:
        ticket = _load_fixture("ticket_not_ready.md")
        gate = is_ready_for_order(ticket)
        self.assertFalse(gate["ready"])
        self.assertEqual(gate["gate"], "not_ready")

    def test_status_alt_review(self) -> None:
        ticket = _load_fixture("ticket_not_ready.md")
        ticket.overall_status = "review"
        gate = is_ready_for_order(ticket)
        self.assertTrue(gate["ready"])
        self.assertEqual(gate["gate"], "status_alt")


class TestValidation(unittest.TestCase):
    def test_invalid_currency(self) -> None:
        bad = validate_currency("INVALID")
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["message"], "invalid_currency")

        short = validate_currency("TW")
        self.assertFalse(short["ok"])

    def test_amount_minor_not_positive(self) -> None:
        zero = validate_amount_minor(0)
        self.assertFalse(zero["ok"])
        self.assertEqual(zero["message"], "invalid_amount_minor")

        negative = validate_amount_minor(-100)
        self.assertFalse(negative["ok"])


class TestCreateOrder(unittest.TestCase):
    def test_normal_create(self) -> None:
        ticket = _load_fixture("ticket_ready_for_order.md")
        store = InMemoryOrderLedgerStore()
        result = create_order_for_ticket(store, ticket, 10000, "TWD")
        self.assertTrue(result["ok"])
        self.assertFalse(result["replay"])
        self.assertEqual(result["message"], "order_created")
        order = result["order"]
        self.assertEqual(order["order_id"], "ORD-WC-T4")
        self.assertEqual(order["ticket_id"], "WC-T4")
        self.assertEqual(order["amount_minor"], 10000)
        self.assertEqual(order["currency"], "TWD")
        self.assertEqual(order["order_status"], "DRAFT")

    def test_not_ready_rejected(self) -> None:
        ticket = _load_fixture("ticket_not_ready.md")
        store = InMemoryOrderLedgerStore()
        result = create_order_for_ticket(store, ticket, 5000, "TWD")
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "not_ready_for_order")

    def test_idempotent_replay(self) -> None:
        ticket = _load_fixture("ticket_ready_for_order.md")
        store = InMemoryOrderLedgerStore()
        first = create_order_for_ticket(store, ticket, 10000, "TWD")
        second = create_order_for_ticket(store, ticket, 20000, "USD")
        self.assertTrue(first["ok"])
        self.assertFalse(first["replay"])
        self.assertTrue(second["ok"])
        self.assertTrue(second["replay"])
        self.assertEqual(second["order"]["amount_minor"], 10000)
        self.assertEqual(second["order"]["currency"], "TWD")

    def test_jsonl_round_trip(self) -> None:
        ticket = _load_fixture("ticket_ready_for_order.md")
        with tempfile.TemporaryDirectory() as tmp:
            jsonl_path = Path(tmp) / "orders.jsonl"
            store = JsonlFileStore(jsonl_path)
            created = create_order_for_ticket(store, ticket, 7500, "USD")
            self.assertTrue(created["ok"])

            lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["order_id"], "ORD-WC-T4")

            reloaded = JsonlFileStore(jsonl_path)
            found = lookup_order(reloaded, order_id="ORD-WC-T4")
            self.assertTrue(found["ok"])
            self.assertEqual(found["order"]["amount_minor"], 7500)
            self.assertEqual(found["order"]["currency"], "USD")


if __name__ == "__main__":
    unittest.main()
