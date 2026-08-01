#!/usr/bin/env python3
"""Order intake CLI (WC-T4).

Usage:
    # Default: read STATE from 04_Workflows/tickets/<ticket_id>_state.md
    python scripts/run_order_intake.py create --ticket WC-T4-INT --amount-minor 10000 --currency TWD

    # Override ticket state path (fixtures / local experiments)
    python scripts/run_order_intake.py create --ticket WC-T4 --amount-minor 10000 --currency TWD \\
        --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md

    python scripts/run_order_intake.py create ... --dry-run
    python scripts/run_order_intake.py lookup --order-id ORD-WC-T4
    python scripts/run_order_intake.py lookup --ticket-id WC-T4
    python scripts/run_order_intake.py list
    python scripts/run_order_intake.py transition --order-id ORD-WC-DEMO-1 --to pending_payment
    GOV_PAYMENT_SANDBOX_ENABLED=1 python scripts/run_order_intake.py pay --order-id ORD-WC-DEMO-1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from dispatch_executor import parse_ticket_state_markdown  # noqa: E402
from order_ledger.payment_adapter import charge  # noqa: E402
from order_ledger.service import (  # noqa: E402
    create_order_for_ticket,
    list_orders,
    lookup_order,
    transition_order,
)
from order_ledger.store import JsonlFileStore  # noqa: E402

DEFAULT_JSONL = _REPO_ROOT / "artifacts" / "order_ledger" / "orders.jsonl"


def _default_ticket_path(ticket_id: str) -> Path:
    return _WORKFLOWS / "tickets" / f"{ticket_id}_state.md"


def _load_ticket(ticket_id: str, ticket_path: Path | None) -> Any:
    path = ticket_path or _default_ticket_path(ticket_id)
    if not path.is_file():
        raise FileNotFoundError(f"ticket_state_not_found:{path.as_posix()}")
    text = path.read_text(encoding="utf-8")
    return parse_ticket_state_markdown(text, path, repo_root=_REPO_ROOT)


def _build_store(jsonl_path: Path) -> JsonlFileStore:
    return JsonlFileStore(jsonl_path)


def cmd_create(args: argparse.Namespace) -> dict[str, Any]:
    ticket = _load_ticket(args.ticket, args.ticket_path)
    store = _build_store(args.jsonl_path)
    return create_order_for_ticket(
        store,
        ticket,
        args.amount_minor,
        args.currency,
        dry_run=args.dry_run,
        idempotency_key=args.idempotency_key,
    )


def cmd_lookup(args: argparse.Namespace) -> dict[str, Any]:
    store = _build_store(args.jsonl_path)
    return lookup_order(
        store,
        order_id=args.order_id,
        ticket_id=args.ticket_id,
    )


def cmd_list(args: argparse.Namespace) -> dict[str, Any]:
    store = _build_store(args.jsonl_path)
    return list_orders(store)


def cmd_transition(args: argparse.Namespace) -> dict[str, Any]:
    store = _build_store(args.jsonl_path)
    return transition_order(
        store,
        args.order_id,
        args.to,
        actor=args.actor,
        reason=args.reason,
    )


def cmd_pay(args: argparse.Namespace) -> dict[str, Any]:
    store = _build_store(args.jsonl_path)
    return charge(
        store,
        args.order_id,
        amount_minor=args.amount_minor,
        simulate=args.simulate,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WC-T4 order intake CLI")
    parser.add_argument(
        "--jsonl-path",
        type=Path,
        default=DEFAULT_JSONL,
        help="JSONL ledger path (default: artifacts/order_ledger/orders.jsonl)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    create_p = sub.add_parser("create", help="Create order for ticket")
    create_p.add_argument("--ticket", required=True, help="Ticket id")
    create_p.add_argument("--amount-minor", type=int, required=True)
    create_p.add_argument("--currency", required=True)
    create_p.add_argument(
        "--ticket-path",
        type=Path,
        default=None,
        help="Optional override; default: 04_Workflows/tickets/<ticket_id>_state.md",
    )
    create_p.add_argument("--idempotency-key", default=None)
    create_p.add_argument("--dry-run", action="store_true")

    lookup_p = sub.add_parser("lookup", help="Lookup order by id or ticket")
    lookup_p.add_argument("--order-id", default=None)
    lookup_p.add_argument("--ticket-id", default=None)

    transition_p = sub.add_parser("transition", help="Transition order status (sandbox state machine)")
    transition_p.add_argument("--order-id", required=True)
    transition_p.add_argument(
        "--to",
        required=True,
        help="Target status: pending_payment | paid | refunded",
    )
    transition_p.add_argument("--actor", default="cli")
    transition_p.add_argument("--reason", default="manual_transition")

    pay_p = sub.add_parser("pay", help="Sandbox mock charge (requires GOV_PAYMENT_SANDBOX_ENABLED=1)")
    pay_p.add_argument("--order-id", required=True)
    pay_p.add_argument("--amount-minor", type=int, default=None)
    pay_p.add_argument(
        "--simulate",
        default=None,
        help="Optional failure inject: decline | timeout",
    )

    sub.add_parser("list", help="List all orders")

    return parser


def _print_result(result: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("ok"):
        order = result.get("order")
        if order:
            print(
                f"order_id={order.get('order_id')} ticket_id={order.get('ticket_id')} "
                f"amount_minor={order.get('amount_minor')} currency={order.get('currency')}"
            )
        elif result.get("orders") is not None:
            print(f"count={result.get('count')}")
            for item in result.get("orders") or []:
                print(f"  {item.get('order_id')} {item.get('ticket_id')}")
        else:
            print(result.get("message"))
    else:
        print(f"ERROR: {result.get('message')}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            result = cmd_create(args)
        elif args.command == "lookup":
            result = cmd_lookup(args)
        elif args.command == "transition":
            result = cmd_transition(args)
        elif args.command == "pay":
            result = cmd_pay(args)
        else:
            result = cmd_list(args)
    except FileNotFoundError as exc:
        result = {"ok": False, "message": str(exc)}
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        result = {"ok": False, "message": f"cli_error:{exc}"}

    _print_result(result, args.format)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
