"""Order intake gates (WC-T4 v0.1)."""

from __future__ import annotations

import re
from typing import Any

from dispatch_executor import TicketRecord

READY_FOR_ORDER_KEYWORDS: tuple[str, ...] = (
    "ready_for_order",
    "ready for order",
    "order intake",
    "create order",
    "开单",
    "開單",
)

ALT_READY_STATUSES = frozenset({"review", "done"})

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")

# v0.1 subset — format + membership; extend in later tickets.
KNOWN_CURRENCIES = frozenset(
    {
        "TWD",
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CNY",
        "HKD",
        "SGD",
        "AUD",
        "CAD",
        "CHF",
        "KRW",
    }
)


def _normalize_next_action(ticket: TicketRecord | dict[str, Any]) -> str:
    if isinstance(ticket, TicketRecord):
        raw = ticket.next_action
    else:
        raw = ticket.get("next_action")
    return (raw or "").strip().lower()


def _overall_status(ticket: TicketRecord | dict[str, Any]) -> str:
    if isinstance(ticket, TicketRecord):
        raw = ticket.overall_status
    else:
        raw = ticket.get("overall_status")
    return (raw or "unknown").strip().lower()


def is_ready_for_order(ticket: TicketRecord | dict[str, Any]) -> dict[str, Any]:
    """Return structured ready gate: keyword primary, status alt fallback."""
    reasons: list[str] = []
    next_action = _normalize_next_action(ticket)

    for keyword in READY_FOR_ORDER_KEYWORDS:
        if keyword.lower() in next_action:
            return {
                "ready": True,
                "gate": "keyword",
                "reasons": [f"next_action_matches:{keyword}"],
            }

    status = _overall_status(ticket)
    if status in ALT_READY_STATUSES:
        return {
            "ready": True,
            "gate": "status_alt",
            "reasons": [f"overall_status_alt:{status}"],
        }

    if not next_action:
        reasons.append("next_action_missing")
    else:
        reasons.append("next_action_no_ready_keyword")
    reasons.append(f"overall_status_not_alt:{status}")
    return {"ready": False, "gate": "not_ready", "reasons": reasons}


def validate_currency(currency: str) -> dict[str, Any]:
    code = (currency or "").strip().upper()
    if not _CURRENCY_RE.match(code):
        return {"ok": False, "message": "invalid_currency", "currency": code}
    if code not in KNOWN_CURRENCIES:
        return {"ok": False, "message": "invalid_currency", "currency": code}
    return {"ok": True, "message": "valid_currency", "currency": code}


def validate_amount_minor(amount_minor: int) -> dict[str, Any]:
    try:
        value = int(amount_minor)
    except (TypeError, ValueError):
        return {"ok": False, "message": "invalid_amount_minor", "amount_minor": amount_minor}
    if value <= 0:
        return {"ok": False, "message": "invalid_amount_minor", "amount_minor": value}
    return {"ok": True, "message": "valid_amount_minor", "amount_minor": value}
