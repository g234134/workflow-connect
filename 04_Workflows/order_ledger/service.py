"""Order intake service layer (WC-T4 v0.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from dispatch_executor import TicketRecord

from order_ledger.gates import is_ready_for_order, validate_amount_minor, validate_currency
from order_ledger.models import OrderRecord, build_order_id
from order_ledger.store import OrderLedgerStore


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_order_for_ticket(
    store: OrderLedgerStore,
    ticket: TicketRecord,
    amount_minor: int,
    currency: str,
    *,
    dry_run: bool = False,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Create order for ticket after gates; idempotent per ticket_id."""
    existing = store.get_by_ticket_id(ticket.ticket_id)
    if existing is not None:
        return {
            "ok": True,
            "message": "order_exists",
            "replay": True,
            "order": existing.to_dict(),
        }

    gate = is_ready_for_order(ticket)
    if not gate["ready"]:
        return {
            "ok": False,
            "message": "not_ready_for_order",
            "replay": False,
            "gate": gate,
        }

    amount_check = validate_amount_minor(amount_minor)
    if not amount_check["ok"]:
        return {
            "ok": False,
            "message": amount_check["message"],
            "replay": False,
            "amount_minor": amount_check.get("amount_minor"),
        }

    currency_check = validate_currency(currency)
    if not currency_check["ok"]:
        return {
            "ok": False,
            "message": currency_check["message"],
            "replay": False,
            "currency": currency_check.get("currency"),
        }

    key = (idempotency_key or ticket.ticket_id).strip()
    order = OrderRecord(
        order_id=build_order_id(ticket.ticket_id),
        ticket_id=ticket.ticket_id,
        ticket_ref=ticket.source_path or f"04_Workflows/tickets/{ticket.ticket_id}_state.md",
        amount_minor=amount_check["amount_minor"],
        currency=currency_check["currency"],
        created_at=_utc_now_iso(),
        idempotency_key=key,
    )

    if dry_run:
        return {
            "ok": True,
            "message": "dry_run",
            "replay": False,
            "dry_run": True,
            "gate": gate,
            "order": order.to_dict(),
        }

    store.put(order)
    return {
        "ok": True,
        "message": "order_created",
        "replay": False,
        "order": order.to_dict(),
    }


def lookup_order(
    store: OrderLedgerStore,
    *,
    order_id: str | None = None,
    ticket_id: str | None = None,
) -> dict[str, Any]:
    if order_id:
        found = store.get_by_order_id(order_id)
        if found is None:
            return {"ok": False, "message": "order_not_found", "order_id": order_id}
        return {"ok": True, "message": "order_found", "order": found.to_dict()}

    if ticket_id:
        found = store.get_by_ticket_id(ticket_id)
        if found is None:
            return {"ok": False, "message": "order_not_found", "ticket_id": ticket_id}
        return {"ok": True, "message": "order_found", "order": found.to_dict()}

    return {"ok": False, "message": "lookup_requires_order_id_or_ticket_id"}


def list_orders(store: OrderLedgerStore) -> dict[str, Any]:
    orders = [o.to_dict() for o in store.list_orders()]
    return {
        "ok": True,
        "message": "orders_listed",
        "count": len(orders),
        "orders": orders,
    }
