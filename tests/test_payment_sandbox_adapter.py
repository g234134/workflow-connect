"""Unit tests for sandbox payment adapter (WC-M3 · P9)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from dispatch_executor import parse_ticket_state_markdown  # noqa: E402
from order_ledger.models import ORDER_STATUS_PAID, ORDER_STATUS_PENDING_PAYMENT  # noqa: E402
from order_ledger.payment_adapter import charge, is_sandbox_enabled, refund  # noqa: E402
from order_ledger.service import create_order_for_ticket, transition_order  # noqa: E402
from order_ledger.store import InMemoryOrderLedgerStore  # noqa: E402

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "order_ledger"


def _load_ready_ticket():
    path = _FIXTURES / "ticket_ready_for_order.md"
    text = path.read_text(encoding="utf-8")
    return parse_ticket_state_markdown(text, path, repo_root=_REPO_ROOT)


def _pending_order(store) -> str:
    ticket = _load_ready_ticket()
    created = create_order_for_ticket(store, ticket, 12000, "TWD")
    order_id = created["order"]["order_id"]
    transition_order(store, order_id, "pending_payment")
    return order_id


class TestPaymentSandboxAdapter(unittest.TestCase):
    def test_sandbox_disabled_by_default(self) -> None:
        with mock.patch.dict(os.environ, {"GOV_PAYMENT_SANDBOX_ENABLED": "0"}, clear=False):
            self.assertFalse(is_sandbox_enabled())
            store = InMemoryOrderLedgerStore()
            order_id = _pending_order(store)
            result = charge(store, order_id)
            self.assertFalse(result["ok"])
            self.assertEqual(result["message"], "sandbox_disabled")

    def test_happy_path_charge_to_paid(self) -> None:
        with mock.patch.dict(os.environ, {"GOV_PAYMENT_SANDBOX_ENABLED": "1"}, clear=False):
            store = InMemoryOrderLedgerStore()
            order_id = _pending_order(store)
            result = charge(store, order_id)
            self.assertTrue(result["ok"])
            self.assertEqual(result["message"], "charge_succeeded")
            self.assertEqual(result["payment_result"]["status"], "paid")
            self.assertTrue(str(result["payment_result"]["provider_ref"]).startswith("SANDBOX-REF-"))
            self.assertEqual(result["order"]["order_status"], ORDER_STATUS_PAID)
            self.assertEqual(result["order"]["actor"], "sandbox-adapter")
            self.assertEqual(result["order"]["reason"], "sandbox_charge_ok")

    def test_decline_leaves_pending_payment(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"GOV_PAYMENT_SANDBOX_ENABLED": "1", "GOV_PAYMENT_SANDBOX_SIMULATE": "decline"},
            clear=False,
        ):
            store = InMemoryOrderLedgerStore()
            order_id = _pending_order(store)
            result = charge(store, order_id)
            self.assertFalse(result["ok"])
            self.assertEqual(result["message"], "charge_declined")
            found = store.get_by_order_id(order_id)
            assert found is not None
            self.assertEqual(found.order_status, ORDER_STATUS_PENDING_PAYMENT)

    def test_timeout_leaves_pending_payment(self) -> None:
        with mock.patch.dict(os.environ, {"GOV_PAYMENT_SANDBOX_ENABLED": "1"}, clear=False):
            store = InMemoryOrderLedgerStore()
            order_id = _pending_order(store)
            result = charge(store, order_id, simulate="timeout")
            self.assertFalse(result["ok"])
            self.assertEqual(result["message"], "charge_timeout")
            found = store.get_by_order_id(order_id)
            assert found is not None
            self.assertEqual(found.order_status, ORDER_STATUS_PENDING_PAYMENT)

    def test_charge_from_draft_rejected(self) -> None:
        with mock.patch.dict(os.environ, {"GOV_PAYMENT_SANDBOX_ENABLED": "1"}, clear=False):
            store = InMemoryOrderLedgerStore()
            ticket = _load_ready_ticket()
            created = create_order_for_ticket(store, ticket, 8000, "TWD")
            order_id = created["order"]["order_id"]
            result = charge(store, order_id)
            self.assertFalse(result["ok"])
            self.assertEqual(result["message"], "invalid_status_for_charge")

    def test_integration_transition_and_charge(self) -> None:
        with mock.patch.dict(os.environ, {"GOV_PAYMENT_SANDBOX_ENABLED": "1"}, clear=False):
            store = InMemoryOrderLedgerStore()
            order_id = _pending_order(store)
            paid = charge(store, order_id, amount_minor=12000)
            self.assertTrue(paid["ok"])
            replay = charge(store, order_id)
            self.assertTrue(replay["ok"])
            self.assertEqual(replay["message"], "already_paid")
            refund_dry = refund(store, order_id, dry_run=True)
            self.assertTrue(refund_dry["ok"])
            self.assertEqual(refund_dry["message"], "refund_dry_run")
            refund_exec = refund(store, order_id, dry_run=False)
            self.assertTrue(refund_exec["ok"])
            self.assertEqual(refund_exec["order"]["order_status"], "REFUNDED")


if __name__ == "__main__":
    unittest.main()
