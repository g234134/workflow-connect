"""Integration tests for WC-T4 order intake (real ticket state → ledger)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dispatch_executor import parse_ticket_state_markdown  # noqa: E402
from order_ledger.service import create_order_for_ticket, lookup_order  # noqa: E402
from order_ledger.store import JsonlFileStore  # noqa: E402

import run_order_intake  # noqa: E402

_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "order_ledger" / "WC-T4-INT_state.md"
_TICKET_ID = "WC-T4-INT"


def _load_real_fixture():
    text = _FIXTURE.read_text(encoding="utf-8")
    return parse_ticket_state_markdown(text, _FIXTURE, repo_root=_REPO_ROOT)


class TestOrderLedgerIntegration(unittest.TestCase):
    def test_real_ticket_fixture_ready_gate_and_create(self) -> None:
        ticket = _load_real_fixture()
        self.assertEqual(ticket.ticket_id, _TICKET_ID)
        self.assertIn("ready_for_order", (ticket.next_action or "").lower())

        with tempfile.TemporaryDirectory() as tmp:
            jsonl_path = Path(tmp) / "orders.jsonl"
            store = JsonlFileStore(jsonl_path)

            created = create_order_for_ticket(store, ticket, 15000, "TWD")
            self.assertTrue(created["ok"])
            self.assertFalse(created["replay"])
            self.assertEqual(created["message"], "order_created")
            order = created["order"]
            self.assertEqual(order["order_id"], f"ORD-{_TICKET_ID}")
            self.assertEqual(order["ticket_id"], _TICKET_ID)
            self.assertEqual(order["amount_minor"], 15000)
            self.assertEqual(order["currency"], "TWD")

            lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["order_id"], f"ORD-{_TICKET_ID}")

            reloaded = JsonlFileStore(jsonl_path)
            by_order = lookup_order(reloaded, order_id=f"ORD-{_TICKET_ID}")
            self.assertTrue(by_order["ok"])
            self.assertEqual(by_order["order"]["amount_minor"], 15000)

            by_ticket = lookup_order(reloaded, ticket_id=_TICKET_ID)
            self.assertTrue(by_ticket["ok"])
            self.assertEqual(by_ticket["order"]["order_id"], f"ORD-{_TICKET_ID}")

    def test_not_ready_rejected_on_real_shape_fixture(self) -> None:
        ticket = _load_real_fixture()
        ticket = type(ticket)(
            **{
                **ticket.__dict__,
                "next_action": "assign implementer for next slice",
                "overall_status": "draft",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = JsonlFileStore(Path(tmp) / "orders.jsonl")
            result = create_order_for_ticket(store, ticket, 10000, "TWD")
            self.assertFalse(result["ok"])
            self.assertEqual(result["message"], "not_ready_for_order")

    def test_load_ticket_default_path_without_ticket_path_arg(self) -> None:
        with mock.patch.object(
            run_order_intake,
            "_default_ticket_path",
            return_value=_FIXTURE,
        ):
            ticket = run_order_intake._load_ticket(_TICKET_ID, None)
        self.assertEqual(ticket.ticket_id, _TICKET_ID)

    def test_cli_create_lookup_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jsonl_path = Path(tmp) / "orders.jsonl"
            create_cmd = [
                sys.executable,
                str(_SCRIPTS / "run_order_intake.py"),
                "--jsonl-path",
                str(jsonl_path),
                "--format",
                "json",
                "create",
                "--ticket",
                _TICKET_ID,
                "--amount-minor",
                "22000",
                "--currency",
                "USD",
                "--ticket-path",
                str(_FIXTURE),
            ]
            create_proc = subprocess.run(
                create_cmd,
                capture_output=True,
                text=True,
                cwd=_REPO_ROOT,
                check=False,
            )
            self.assertEqual(create_proc.returncode, 0, create_proc.stderr or create_proc.stdout)
            created = json.loads(create_proc.stdout)
            self.assertTrue(created["ok"])
            self.assertEqual(created["order"]["order_id"], f"ORD-{_TICKET_ID}")

            lookup_cmd = [
                sys.executable,
                str(_SCRIPTS / "run_order_intake.py"),
                "--jsonl-path",
                str(jsonl_path),
                "--format",
                "json",
                "lookup",
                "--ticket-id",
                _TICKET_ID,
            ]
            lookup_proc = subprocess.run(
                lookup_cmd,
                capture_output=True,
                text=True,
                cwd=_REPO_ROOT,
                check=False,
            )
            self.assertEqual(lookup_proc.returncode, 0, lookup_proc.stderr or lookup_proc.stdout)
            found = json.loads(lookup_proc.stdout)
            self.assertTrue(found["ok"])
            self.assertEqual(found["order"]["amount_minor"], 22000)
            self.assertEqual(found["order"]["currency"], "USD")


if __name__ == "__main__":
    unittest.main()
