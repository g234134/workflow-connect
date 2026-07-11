"""Sandbox-only mock payment provider adapter (WC-M3 · P9).

Env gate: GOV_PAYMENT_SANDBOX_ENABLED=1 (default 0).
Failure inject: GOV_PAYMENT_SANDBOX_SIMULATE=decline|timeout or simulate= param.
Never reads real payment API keys.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from order_ledger.models import ORDER_STATUS_PAID, ORDER_STATUS_PENDING_PAYMENT, normalize_order_status
from order_ledger.service import transition_order
from order_ledger.store import OrderLedgerStore


def is_sandbox_enabled() -> bool:
    return os.environ.get("GOV_PAYMENT_SANDBOX_ENABLED", "0").strip() == "1"


def _resolve_simulate(simulate: str | None) -> str:
    raw = (simulate or os.environ.get("GOV_PAYMENT_SANDBOX_SIMULATE") or "").strip().lower()
    return raw


def _mock_provider_ref(order_id: str) -> str:
    suffix = uuid.uuid4().hex[:8]
    return f"SANDBOX-REF-{order_id}-{suffix}"


def charge(
    store: OrderLedgerStore,
    order_id: str,
    amount_minor: int | None = None,
    *,
    simulate: str | None = None,
    actor: str = "sandbox-adapter",
) -> dict[str, Any]:
    """Mock charge: happy path transitions order to PAID; decline/timeout leaves PENDING_PAYMENT."""
    if not is_sandbox_enabled():
        return {"ok": False, "message": "sandbox_disabled"}

    found = store.get_by_order_id(order_id)
    if found is None:
        return {"ok": False, "message": "order_not_found", "order_id": order_id}

    if amount_minor is not None and int(amount_minor) != int(found.amount_minor):
        return {
            "ok": False,
            "message": "amount_mismatch",
            "order_id": order_id,
            "expected_amount_minor": found.amount_minor,
            "provided_amount_minor": amount_minor,
        }

    current = normalize_order_status(found.order_status)
    if current == ORDER_STATUS_PAID:
        return {
            "ok": True,
            "message": "already_paid",
            "replay": True,
            "payment_result": {
                "status": "paid",
                "provider_ref": found.provider_ref or _mock_provider_ref(order_id),
                "simulated": True,
            },
            "order": found.to_dict(),
        }

    if current != ORDER_STATUS_PENDING_PAYMENT:
        return {
            "ok": False,
            "message": "invalid_status_for_charge",
            "order_id": order_id,
            "order_status": current,
        }

    mode = _resolve_simulate(simulate)
    if mode == "decline":
        return {
            "ok": False,
            "message": "charge_declined",
            "payment_result": {"status": "declined", "simulated": True},
            "order": found.to_dict(),
        }
    if mode == "timeout":
        return {
            "ok": False,
            "message": "charge_timeout",
            "payment_result": {"status": "timeout", "simulated": True},
            "order": found.to_dict(),
        }

    provider_ref = _mock_provider_ref(order_id)
    transitioned = transition_order(
        store,
        order_id,
        ORDER_STATUS_PAID,
        actor=actor,
        reason="sandbox_charge_ok",
        provider_ref=provider_ref,
    )
    if not transitioned.get("ok"):
        return transitioned

    return {
        "ok": True,
        "message": "charge_succeeded",
        "payment_result": {
            "status": "paid",
            "provider_ref": provider_ref,
            "simulated": True,
        },
        "order": transitioned.get("order"),
    }


def refund(
    store: OrderLedgerStore,
    order_id: str,
    *,
    dry_run: bool = False,
    actor: str = "sandbox-adapter",
) -> dict[str, Any]:
    """Mock refund: dry-run previews; execute transitions PAID → REFUNDED."""
    if not is_sandbox_enabled():
        return {"ok": False, "message": "sandbox_disabled"}

    found = store.get_by_order_id(order_id)
    if found is None:
        return {"ok": False, "message": "order_not_found", "order_id": order_id}

    current = normalize_order_status(found.order_status)
    if current != ORDER_STATUS_PAID:
        return {
            "ok": False,
            "message": "invalid_status_for_refund",
            "order_id": order_id,
            "order_status": current,
        }

    if dry_run:
        return {
            "ok": True,
            "message": "refund_dry_run",
            "dry_run": True,
            "payment_result": {"status": "refund_preview", "simulated": True},
            "order": found.to_dict(),
        }

    from order_ledger.models import ORDER_STATUS_REFUNDED

    transitioned = transition_order(
        store,
        order_id,
        ORDER_STATUS_REFUNDED,
        actor=actor,
        reason="sandbox_refund_ok",
    )
    if not transitioned.get("ok"):
        return transitioned

    return {
        "ok": True,
        "message": "refund_succeeded",
        "payment_result": {"status": "refunded", "simulated": True},
        "order": transitioned.get("order"),
    }
