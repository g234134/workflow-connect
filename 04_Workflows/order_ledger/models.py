"""Order ledger datamodels (WC-T4 v0.1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = "order_ledger_v1"
DEFAULT_ORDER_STATUS = "DRAFT"


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
        )


def build_order_id(ticket_id: str) -> str:
    """One-ticket-one-order: deterministic order id."""
    return f"ORD-{ticket_id.strip()}"
