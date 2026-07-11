"""Order ledger datamodels (WC-T4 v0.1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = "order_ledger_v1"
DEFAULT_ORDER_STATUS = "DRAFT"

ORDER_STATUS_DRAFT = "DRAFT"
ORDER_STATUS_PENDING_PAYMENT = "PENDING_PAYMENT"
ORDER_STATUS_PAID = "PAID"
ORDER_STATUS_REFUNDED = "REFUNDED"

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    ORDER_STATUS_DRAFT: frozenset({ORDER_STATUS_PENDING_PAYMENT}),
    ORDER_STATUS_PENDING_PAYMENT: frozenset({ORDER_STATUS_PAID}),
    ORDER_STATUS_PAID: frozenset({ORDER_STATUS_REFUNDED}),
    ORDER_STATUS_REFUNDED: frozenset(),
}

CLI_STATUS_ALIASES: dict[str, str] = {
    "draft": ORDER_STATUS_DRAFT,
    "pending_payment": ORDER_STATUS_PENDING_PAYMENT,
    "paid": ORDER_STATUS_PAID,
    "refunded": ORDER_STATUS_REFUNDED,
}


def normalize_order_status(raw: str) -> str:
    key = (raw or "").strip().lower()
    if key in CLI_STATUS_ALIASES:
        return CLI_STATUS_ALIASES[key]
    return (raw or "").strip().upper()


def is_valid_transition(from_status: str, to_status: str) -> bool:
    current = normalize_order_status(from_status)
    target = normalize_order_status(to_status)
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    return target in allowed


@dataclass
class OrderRecord:
    """Minimal order intake record — one ticket maps to one order."""

    order_id: str
    ticket_id: str
    ticket_ref: str
    amount_minor: int
    currency: str
    order_status: str = DEFAULT_ORDER_STATUS
    created_at: str = ""
    idempotency_key: str = ""
    schema_version: str = SCHEMA_VERSION
    transitioned_at: str = ""
    actor: str = ""
    reason: str = ""
    provider_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema_version"] = SCHEMA_VERSION
        return data

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> OrderRecord:
        return cls(
            order_id=str(raw["order_id"]),
            ticket_id=str(raw["ticket_id"]),
            ticket_ref=str(raw["ticket_ref"]),
            amount_minor=int(raw["amount_minor"]),
            currency=str(raw["currency"]),
            order_status=str(raw.get("order_status") or DEFAULT_ORDER_STATUS),
            created_at=str(raw.get("created_at") or ""),
            idempotency_key=str(raw.get("idempotency_key") or raw["ticket_id"]),
            schema_version=str(raw.get("schema_version") or SCHEMA_VERSION),
            transitioned_at=str(raw.get("transitioned_at") or ""),
            actor=str(raw.get("actor") or ""),
            reason=str(raw.get("reason") or ""),
            provider_ref=str(raw.get("provider_ref") or ""),
        )


def build_order_id(ticket_id: str) -> str:
    """One-ticket-one-order: deterministic order id."""
    return f"ORD-{ticket_id.strip()}"
