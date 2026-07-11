"""
Phase 6.5 shared contracts — **mvp_v0.1 · NOT production-ready**.

Authority for entity/event enums and allowed (entity_type, event_type) pairs.
Pydantic models live in ``core.schemas.phase6_5_*``.
JSON schemas live in ``shared/schemas/phase6_5_*_v1.json``.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from shared.naming import (
    PHASE6_5_ENTITIES_SCHEMA_VERSION,
    PHASE6_5_EVENTS_SCHEMA_VERSION,
)

CONTRACT_TIER: Final[str] = "mvp_v0.1"
CONTRACT_DOC_TIER_LINE: Final[str] = "**Tier**: mvp_v0.1 · **NOT production-ready**"
PRODUCTION_READY: Final[bool] = False

PHASE6_5_ENTITIES_SCHEMA_VERSION_CONST: Final[str] = PHASE6_5_ENTITIES_SCHEMA_VERSION
PHASE6_5_EVENTS_SCHEMA_VERSION_CONST: Final[str] = PHASE6_5_EVENTS_SCHEMA_VERSION


def is_production_ready() -> bool:
    return False


class EntityType(str, Enum):
    LEAD = "lead"
    REQUIREMENT_PROFILE = "requirement_profile"
    ORDER = "order"
    JOB = "job"
    RUN = "run"
    DELIVERY = "delivery"
    INVOICE = "invoice"
    PAYMENT = "payment"
    SKILL_CARD = "skill_card"
    SKILL_RUN = "skill_run"
    REPLAY_EVENT = "replay_event"


ENTITY_TYPES: Final[tuple[str, ...]] = tuple(e.value for e in EntityType)


class EventType(str, Enum):
    LEAD_CREATED = "lead.created"
    LEAD_QUALIFIED = "lead.qualified"
    LEAD_ARCHIVED = "lead.archived"
    REQUIREMENT_PROFILE_CREATED = "requirement_profile.created"
    REQUIREMENT_PROFILE_UPDATED = "requirement_profile.updated"
    ORDER_PLACED = "order.placed"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_CANCELLED = "order.cancelled"
    JOB_CREATED = "job.created"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    DELIVERY_SUBMITTED = "delivery.submitted"
    DELIVERY_ACCEPTED = "delivery.accepted"
    INVOICE_ISSUED = "invoice.issued"
    INVOICE_VOIDED = "invoice.voided"
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    SKILL_CARD_PUBLISHED = "skill_card.published"
    SKILL_CARD_DEPRECATED = "skill_card.deprecated"
    SKILL_RUN_STARTED = "skill_run.started"
    SKILL_RUN_COMPLETED = "skill_run.completed"
    SKILL_RUN_FAILED = "skill_run.failed"
    REPLAY_EVENT_RECORDED = "replay_event.recorded"


EVENT_TYPES: Final[tuple[str, ...]] = tuple(e.value for e in EventType)


class LeadStatus(str, Enum):
    DRAFT = "draft"
    QUALIFIED = "qualified"
    ARCHIVED = "archived"


class RequirementProfileStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    PLACED = "placed"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class JobStatus(str, Enum):
    CREATED = "created"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    VOIDED = "voided"


class PaymentStatus(str, Enum):
    INITIATED = "initiated"
    CAPTURED = "captured"
    FAILED = "failed"


class SkillCardStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class SkillRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReplayEventStatus(str, Enum):
    RECORDED = "recorded"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


ENTITY_EVENT_ALLOWED: Final[dict[str, frozenset[str]]] = {
    EntityType.LEAD.value: frozenset(
        {
            EventType.LEAD_CREATED.value,
            EventType.LEAD_QUALIFIED.value,
            EventType.LEAD_ARCHIVED.value,
        }
    ),
    EntityType.REQUIREMENT_PROFILE.value: frozenset(
        {
            EventType.REQUIREMENT_PROFILE_CREATED.value,
            EventType.REQUIREMENT_PROFILE_UPDATED.value,
        }
    ),
    EntityType.ORDER.value: frozenset(
        {
            EventType.ORDER_PLACED.value,
            EventType.ORDER_CONFIRMED.value,
            EventType.ORDER_CANCELLED.value,
        }
    ),
    EntityType.JOB.value: frozenset(
        {
            EventType.JOB_CREATED.value,
            EventType.JOB_STARTED.value,
            EventType.JOB_COMPLETED.value,
        }
    ),
    EntityType.RUN.value: frozenset(
        {
            EventType.RUN_STARTED.value,
            EventType.RUN_COMPLETED.value,
            EventType.RUN_FAILED.value,
        }
    ),
    EntityType.DELIVERY.value: frozenset(
        {
            EventType.DELIVERY_SUBMITTED.value,
            EventType.DELIVERY_ACCEPTED.value,
        }
    ),
    EntityType.INVOICE.value: frozenset(
        {
            EventType.INVOICE_ISSUED.value,
            EventType.INVOICE_VOIDED.value,
        }
    ),
    EntityType.PAYMENT.value: frozenset(
        {
            EventType.PAYMENT_INITIATED.value,
            EventType.PAYMENT_CAPTURED.value,
            EventType.PAYMENT_FAILED.value,
        }
    ),
    EntityType.SKILL_CARD.value: frozenset(
        {
            EventType.SKILL_CARD_PUBLISHED.value,
            EventType.SKILL_CARD_DEPRECATED.value,
        }
    ),
    EntityType.SKILL_RUN.value: frozenset(
        {
            EventType.SKILL_RUN_STARTED.value,
            EventType.SKILL_RUN_COMPLETED.value,
            EventType.SKILL_RUN_FAILED.value,
        }
    ),
    EntityType.REPLAY_EVENT.value: frozenset({EventType.REPLAY_EVENT_RECORDED.value}),
}


def is_event_allowed(entity_type: str, event_type: str) -> bool:
    allowed = ENTITY_EVENT_ALLOWED.get(entity_type)
    if allowed is None:
        return False
    return event_type in allowed
