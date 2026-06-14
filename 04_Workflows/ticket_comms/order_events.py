"""Order-event comms payloads for Control Plane handoff loop (WC-T6)."""

from __future__ import annotations

from typing import Any

from ticket_comms.message_generator import SCHEMA_VERSION, TicketStateSnapshot, _utc_now_iso
from ticket_comms.sender import CommsSender, FileLogSender, NullSender

ORDER_EVENT_TYPES = frozenset(
    {"order_created", "order_replay", "order_rejected", "order_dry_run"}
)


def _resolve_event_type(order_result: dict[str, Any]) -> str:
    if order_result.get("dry_run"):
        return "order_dry_run"
    if not order_result.get("ok"):
        return "order_rejected"
    if order_result.get("replay"):
        return "order_replay"
    return "order_created"


def _build_order_summary(
    snapshot: TicketStateSnapshot,
    order_result: dict[str, Any],
    event_type: str,
) -> str:
    ticket_id = snapshot.ticket_id
    if event_type == "order_created":
        order = order_result.get("order") or {}
        return (
            f"Ticket {ticket_id}: order {order.get('order_id')} created "
            f"({order.get('amount_minor')} {order.get('currency')}, status DRAFT)."
        )
    if event_type == "order_replay":
        order = order_result.get("order") or {}
        return (
            f"Ticket {ticket_id}: order {order.get('order_id')} already exists "
            f"(idempotent replay)."
        )
    if event_type == "order_dry_run":
        order = order_result.get("order") or {}
        return (
            f"Ticket {ticket_id}: order dry-run preview "
            f"({order.get('order_id', 'pending')}, no ledger write)."
        )
    message = str(order_result.get("message") or "order_rejected")
    gate = order_result.get("gate")
    if gate and not gate.get("ready"):
        reasons = gate.get("reasons") or []
        if reasons:
            return f"Ticket {ticket_id}: order rejected — {message}; {reasons[0]}"
    return f"Ticket {ticket_id}: order rejected — {message}."


def _build_order_title(snapshot: TicketStateSnapshot, event_type: str) -> str:
    labels = {
        "order_created": "Order Created",
        "order_replay": "Order Replay",
        "order_rejected": "Order Rejected",
        "order_dry_run": "Order Dry Run",
    }
    return f"[{snapshot.ticket_id}] {labels.get(event_type, 'Order Update')}"


def build_order_comms_payload(
    snapshot: TicketStateSnapshot,
    order_result: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build structured comms payload for an order intake outcome."""
    event_type = _resolve_event_type(order_result)
    ticket_ref = snapshot.source_path or f"04_Workflows/tickets/{snapshot.ticket_id}_state.md"

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_type": event_type,
        "ticket_id": snapshot.ticket_id,
        "title": _build_order_title(snapshot, event_type),
        "summary": _build_order_summary(snapshot, order_result, event_type),
        "ticket_ref": ticket_ref,
        "order_result": {
            "ok": bool(order_result.get("ok")),
            "message": str(order_result.get("message") or ""),
            "replay": bool(order_result.get("replay")),
        },
        "generated_at": generated_at or _utc_now_iso(),
    }

    if order_result.get("order"):
        payload["order"] = dict(order_result["order"])
    if order_result.get("gate"):
        payload["gate"] = dict(order_result["gate"])

    return payload


def emit_order_comms(
    snapshot: TicketStateSnapshot,
    order_result: dict[str, Any],
    *,
    sender: CommsSender | None = None,
    dry_run: bool = False,
    outbox_dir: str | None = None,
) -> dict[str, Any]:
    """Generate and optionally send comms for an order intake outcome."""
    payload = build_order_comms_payload(snapshot, order_result)

    if dry_run:
        adapter: CommsSender = NullSender()
    elif sender is not None:
        adapter = sender
    elif outbox_dir:
        adapter = FileLogSender(outbox_dir)
    else:
        adapter = FileLogSender("artifacts/ticket_comms")

    send_result = adapter.send(payload)
    return {
        "ok": bool(send_result.get("ok")),
        "message": str(send_result.get("message") or "sent"),
        "ticket_id": snapshot.ticket_id,
        "event_type": payload["event_type"],
        "sent": bool(send_result.get("ok")),
        "payload": payload,
        "send_result": send_result,
    }
