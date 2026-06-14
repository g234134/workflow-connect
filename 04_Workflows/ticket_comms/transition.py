"""Hook for ticket STATE transitions → comms generation + send (WC-T2)."""

from __future__ import annotations

from typing import Any

from ticket_comms.message_generator import (
    TicketStateSnapshot,
    build_comms_payload,
    compute_state_diff,
)
from ticket_comms.sender import CommsSender, FileLogSender, NullSender


def emit_ticket_comms_on_change(
    before: TicketStateSnapshot,
    after: TicketStateSnapshot,
    *,
    sender: CommsSender | None = None,
    dry_run: bool = False,
    outbox_dir: str | None = None,
) -> dict[str, Any]:
    """Generate and optionally send a comms payload when ticket STATE changes.

    This is the integration hook for future writers (Orchestrator tooling,
    event bus, or file watchers). Returns stable dict with ok / message.
    """
    if before.ticket_id != after.ticket_id:
        return {
            "ok": False,
            "message": "ticket_id_mismatch",
            "ticket_id": after.ticket_id,
            "sent": False,
            "payload": None,
            "send_result": None,
        }

    diff = compute_state_diff(before, after)
    if not diff.has_changes():
        return {
            "ok": True,
            "message": "no_state_change",
            "ticket_id": after.ticket_id,
            "sent": False,
            "payload": None,
            "send_result": None,
        }

    payload = build_comms_payload(after, diff)

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
        "ticket_id": after.ticket_id,
        "sent": bool(send_result.get("ok")),
        "payload": payload,
        "send_result": send_result,
    }
