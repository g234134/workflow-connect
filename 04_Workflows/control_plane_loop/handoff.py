"""Order handoff loop: eligibility → dispatch context → order intake → comms (WC-T6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dispatch_executor import (
    TicketRecord,
    classify_ticket,
    parse_ticket_state_markdown,
    recommend_role,
)
from order_ledger.service import create_order_for_ticket
from order_ledger.store import JsonlFileStore
from ticket_comms.message_generator import snapshot_from_ticket_record
from ticket_comms.order_events import emit_order_comms
from ticket_eligibility import (
    EligibilityContext,
    build_done_ids,
    evaluate_ticket_eligibility,
)


def _load_ticket_record(
    ticket_id: str,
    ticket_path: Path,
    repo_root: Path,
) -> TicketRecord:
    if not ticket_path.is_file():
        raise FileNotFoundError(f"ticket_state_not_found:{ticket_path.as_posix()}")
    text = ticket_path.read_text(encoding="utf-8")
    return parse_ticket_state_markdown(text, ticket_path, repo_root=repo_root)


def _build_dispatch_context(
    ticket: TicketRecord,
    *,
    done_ids: set[str],
) -> dict[str, Any]:
    bucket = classify_ticket(ticket, done_ids=done_ids)
    role, reason = recommend_role(ticket, bucket)
    return {
        "bucket": bucket,
        "recommended_role": role,
        "reason": reason,
        "blockers": list(ticket.blockers),
        "dependencies": list(ticket.dependencies),
    }


def execute_order_handoff(
    repo_root: Path,
    ticket_id: str,
    amount_minor: int,
    currency: str,
    *,
    ticket_path: Path | None = None,
    orders_jsonl: Path | None = None,
    comms_outbox: Path | None = None,
    dry_run: bool = False,
    skip_eligibility: bool = False,
    requested_role: str = "orchestrator",
    emit_comms: bool = True,
) -> dict[str, Any]:
    """Run minimal 接单→开单→回报 loop for one ticket.

    Does not write live ``*_state.md``. Returns structured dict with
    eligibility, dispatch_context, order, and comms sections.
    """
    workflows = repo_root / "04_Workflows"
    resolved_ticket_path = ticket_path or (workflows / "tickets" / f"{ticket_id}_state.md")
    ledger_path = orders_jsonl or (repo_root / "artifacts" / "order_ledger" / "orders.jsonl")
    outbox = str(comms_outbox or (repo_root / "artifacts" / "ticket_comms"))

    try:
        ticket = _load_ticket_record(ticket_id, resolved_ticket_path, repo_root)
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "ticket_id": ticket_id,
            "eligibility": None,
            "dispatch_context": None,
            "order": None,
            "comms": None,
        }

    done_ids = build_done_ids(repo_root)
    eligibility = evaluate_ticket_eligibility(
        ticket,
        done_ids=done_ids,
        context=EligibilityContext(requested_role=requested_role),
    )
    dispatch_context = _build_dispatch_context(ticket, done_ids=done_ids)

    if not skip_eligibility and eligibility.get("eligible") == "ineligible":
        return {
            "ok": False,
            "message": "ineligible_for_handoff",
            "ticket_id": ticket.ticket_id,
            "eligibility": eligibility,
            "dispatch_context": dispatch_context,
            "order": None,
            "comms": None,
            "reasons": eligibility.get("reasons") or [],
        }

    store = JsonlFileStore(ledger_path)
    order_result = create_order_for_ticket(
        store,
        ticket,
        amount_minor,
        currency,
        dry_run=dry_run,
    )

    comms_result: dict[str, Any] | None = None
    if emit_comms:
        snapshot = snapshot_from_ticket_record(ticket)
        comms_result = emit_order_comms(
            snapshot,
            order_result,
            dry_run=dry_run,
            outbox_dir=outbox,
        )

    loop_ok = bool(order_result.get("ok"))
    return {
        "ok": loop_ok,
        "message": "order_handoff_complete" if loop_ok else str(order_result.get("message")),
        "ticket_id": ticket.ticket_id,
        "dry_run": dry_run,
        "eligibility": eligibility,
        "dispatch_context": dispatch_context,
        "order": order_result,
        "comms": comms_result,
    }
