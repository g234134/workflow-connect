"""
Phase 6.5 domain entity Pydantic models (11 entities).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from core.contracts.phase6_5_data_contract import (
    DeliveryStatus,
    InvoiceStatus,
    JobPriority,
    JobStatus,
    LeadStatus,
    OrderStatus,
    PaymentStatus,
    ReplayEventStatus,
    RequirementProfileStatus,
    RunStatus,
    SkillCardStatus,
    SkillRunStatus,
    EntityType,
)
from core.schemas.phase6_5_common import EntityRecordBase, Phase65BaseModel
from shared.naming import (
    FIELD_CONTACT_REF,
    FIELD_JOB_ID,
    FIELD_LEAD_ID,
    FIELD_ORDER_ID,
    FIELD_OWNER_REF,
    FIELD_REQUIREMENT_PROFILE_ID,
    FIELD_RUN_ID,
    FIELD_SKILL_CARD_ID,
    FIELD_SOURCE,
    FIELD_INVOICE_ID,
    FIELD_TARGET_ENTITY_ID,
    FIELD_TARGET_ENTITY_TYPE,
    FIELD_REPLAY_KIND,
    FIELD_SNAPSHOT_REF,
    FIELD_CAUSATION_EVENT_ID,
)


class RequirementConstraints(Phase65BaseModel):
    budget_usd_max: float | None = Field(default=None, ge=0)
    deadline_at: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=32)


class OrderLineItem(Phase65BaseModel):
    sku: str = Field(max_length=64)
    quantity: int = Field(ge=1)
    unit_price: float | None = Field(default=None, ge=0)


class SkillCardSpec(Phase65BaseModel):
    description: str | None = Field(default=None, max_length=500)
    input_schema_ref: str | None = Field(default=None, max_length=200)
    output_schema_ref: str | None = Field(default=None, max_length=200)


def _validate_uuid_fk(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    UUID(value)
    return value


class Lead(EntityRecordBase):
    status: LeadStatus
    source: str = Field(max_length=64)
    contact_ref: str = Field(max_length=200)
    owner_ref: str = Field(max_length=200)


class RequirementProfile(EntityRecordBase):
    status: RequirementProfileStatus
    lead_id: str
    summary: str = Field(max_length=2000)
    constraints: RequirementConstraints

    @field_validator(FIELD_LEAD_ID)
    @classmethod
    def _lead_id_uuid(cls, v: str) -> str:
        UUID(v)
        return v


class Order(EntityRecordBase):
    status: OrderStatus
    lead_id: str
    requirement_profile_id: str | None = None
    line_items: list[OrderLineItem] = Field(min_length=1)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator(FIELD_LEAD_ID, FIELD_REQUIREMENT_PROFILE_ID)
    @classmethod
    def _fk_uuids(cls, v: str | None) -> str | None:
        return _validate_uuid_fk(v, "fk")


class Job(EntityRecordBase):
    status: JobStatus
    order_id: str
    job_type: str = Field(max_length=64)
    priority: JobPriority

    @field_validator(FIELD_ORDER_ID)
    @classmethod
    def _order_id_uuid(cls, v: str) -> str:
        UUID(v)
        return v


class Run(EntityRecordBase):
    status: RunStatus
    job_id: str
    run_kind: str = Field(max_length=64)
    started_at: str | None = None
    ended_at: str | None = None

    @field_validator(FIELD_JOB_ID)
    @classmethod
    def _job_id_uuid(cls, v: str) -> str:
        UUID(v)
        return v


class Delivery(EntityRecordBase):
    status: DeliveryStatus
    job_id: str
    artifact_refs: list[str] = Field(default_factory=list, max_length=64)
    accepted_at: str | None = None

    @field_validator(FIELD_JOB_ID)
    @classmethod
    def _job_id_uuid(cls, v: str) -> str:
        UUID(v)
        return v


class Invoice(EntityRecordBase):
    status: InvoiceStatus
    order_id: str
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    issued_at: str

    @field_validator(FIELD_ORDER_ID)
    @classmethod
    def _order_id_uuid(cls, v: str) -> str:
        UUID(v)
        return v


class Payment(EntityRecordBase):
    status: PaymentStatus
    invoice_id: str
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    method: str = Field(max_length=32)
    paid_at: str | None = None

    @field_validator(FIELD_INVOICE_ID)
    @classmethod
    def _invoice_id_uuid(cls, v: str) -> str:
        UUID(v)
        return v


class SkillCard(EntityRecordBase):
    status: SkillCardStatus
    skill_key: str = Field(max_length=128)
    version: str = Field(max_length=32)
    spec: SkillCardSpec


class SkillRun(EntityRecordBase):
    status: SkillRunStatus
    skill_card_id: str
    run_id: str | None = None
    job_id: str | None = None
    input_ref: str = Field(max_length=200)
    output_ref: str | None = Field(default=None, max_length=200)

    @field_validator(FIELD_SKILL_CARD_ID, FIELD_RUN_ID, FIELD_JOB_ID)
    @classmethod
    def _fk_uuids(cls, v: str | None) -> str | None:
        return _validate_uuid_fk(v, "fk")


class ReplayEvent(EntityRecordBase):
    status: ReplayEventStatus
    target_entity_type: EntityType
    target_entity_id: str
    replay_kind: str = Field(max_length=64)
    snapshot_ref: str = Field(max_length=200)
    causation_event_id: str | None = None

    @field_validator(FIELD_TARGET_ENTITY_ID, FIELD_CAUSATION_EVENT_ID)
    @classmethod
    def _uuid_fields(cls, v: str | None) -> str | None:
        return _validate_uuid_fk(v, "fk")


ENTITY_MODEL_BY_TYPE: dict[str, type[EntityRecordBase]] = {
    EntityType.LEAD.value: Lead,
    EntityType.REQUIREMENT_PROFILE.value: RequirementProfile,
    EntityType.ORDER.value: Order,
    EntityType.JOB.value: Job,
    EntityType.RUN.value: Run,
    EntityType.DELIVERY.value: Delivery,
    EntityType.INVOICE.value: Invoice,
    EntityType.PAYMENT.value: Payment,
    EntityType.SKILL_CARD.value: SkillCard,
    EntityType.SKILL_RUN.value: SkillRun,
    EntityType.REPLAY_EVENT.value: ReplayEvent,
}


def entity_model_for_type(entity_type: str) -> type[EntityRecordBase]:
    model = ENTITY_MODEL_BY_TYPE.get(entity_type)
    if model is None:
        raise KeyError(f"unknown entity_type: {entity_type!r}")
    return model
