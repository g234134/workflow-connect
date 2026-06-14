#!/usr/bin/env python3
"""Control Plane order handoff loop CLI (WC-T6).

Chains eligibility check, dispatch context, order intake, and order-event comms.
Does not write live *_state.md or call payment gateways.

Usage:
    python scripts/run_control_plane_order_handoff.py \\
        --ticket WC-T4 \\
        --amount-minor 10000 \\
        --currency TWD \\
        --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md

    python scripts/run_control_plane_order_handoff.py \\
        --ticket WC-T4 --amount-minor 10000 --currency TWD \\
        --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md \\
        --dry-run

    python scripts/run_control_plane_order_handoff.py \\
        --ticket WC-T4 --amount-minor 10000 --currency TWD \\
        --ticket-path tests/fixtures/order_ledger/ticket_not_ready.md \\
        --skip-eligibility --comms-outbox artifacts/e2e/WC-T4/comms
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

from control_plane_loop.handoff import execute_order_handoff  # noqa: E402


def _default_ticket_path(ticket_id: str) -> Path:
    return _WORKFLOWS / "tickets" / f"{ticket_id}_state.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="WC-T6 Control Plane order handoff loop (eligibility → order → comms)",
    )
    parser.add_argument("--ticket", required=True, help="Ticket id")
    parser.add_argument("--amount-minor", type=int, required=True)
    parser.add_argument("--currency", required=True)
    parser.add_argument(
        "--ticket-path",
        type=Path,
        default=None,
        help="Override ticket state path (default: 04_Workflows/tickets/<id>_state.md)",
    )
    parser.add_argument(
        "--jsonl-path",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "order_ledger" / "orders.jsonl",
        help="Order ledger JSONL path",
    )
    parser.add_argument(
        "--comms-outbox",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "ticket_comms",
        help="Comms JSONL outbox directory",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview order; no ledger/comms write")
    parser.add_argument(
        "--skip-eligibility",
        action="store_true",
        help="Proceed even when eligibility is ineligible (Orchestrator override)",
    )
    parser.add_argument(
        "--requested-role",
        default="orchestrator",
        choices=("implementer", "reviewer", "scribe", "orchestrator"),
    )
    parser.add_argument(
        "--no-comms",
        action="store_true",
        help="Skip order-event comms emission",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
    )
    args = parser.parse_args(argv)

    ticket_path = args.ticket_path or _default_ticket_path(args.ticket)
    result = execute_order_handoff(
        _REPO_ROOT,
        args.ticket,
        args.amount_minor,
        args.currency,
        ticket_path=ticket_path,
        orders_jsonl=args.jsonl_path,
        comms_outbox=args.comms_outbox,
        dry_run=args.dry_run,
        skip_eligibility=args.skip_eligibility,
        requested_role=args.requested_role,
        emit_comms=not args.no_comms,
    )

    if args.format == "text":
        _print_text(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result.get("ok") else 1


def _print_text(result: dict[str, Any]) -> None:
    lines = [
        "Control Plane Order Handoff (WC-T6)",
        f"ticket_id: {result.get('ticket_id')}",
        f"ok: {result.get('ok')}",
        f"message: {result.get('message')}",
    ]
    elig = result.get("eligibility") or {}
    lines.append(f"eligible: {elig.get('eligible')}")
    dispatch = result.get("dispatch_context") or {}
    lines.append(f"dispatch_bucket: {dispatch.get('bucket')}")
    lines.append(f"recommended_role: {dispatch.get('recommended_role')}")
    order = result.get("order") or {}
    if order.get("order"):
        o = order["order"]
        lines.append(f"order_id: {o.get('order_id')} status: {o.get('order_status')}")
    comms = result.get("comms") or {}
    if comms.get("event_type"):
        lines.append(f"comms_event: {comms.get('event_type')} sent: {comms.get('sent')}")
    print("\n".join(lines))


if __name__ == "__main__":
    raise SystemExit(main())
