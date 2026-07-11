"""
Phase 6.5 event envelope and typed payloads.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from core.contracts.phase6_5_data_contract import (
    EventType,
    EntityType,
    PHASE6_5_EVENTS_SCHEMA_VERSION_CONST,
    is_event_allowed,
)
from core.schemas.phase6_5_common import Phase65BaseModel, _parse_iso_datetime
from shared.naming import (
    FIELD_ENTITY_ID,
    FIELD_ENTITY_TYPE,
    FIELD_EVENT_ID,
    FIELD_EVENT_TYPE,
    FIELD_METADATA,
    FIELD_OCCURRED_AT,
    FIELD_PAYLOAD,
    FIELD_SCHEMA_VERSION,
)


class EventMetadata(Phase65BaseModel):
    source: str | None = Field(default=None, max_length=64)
    trace_id: str | None = Field(default=None, max_length=200)
    actor_ref: str | None = Field(default=None, max_length=200)


class GenericEntityPayload(Phase65BaseModel):
    changes: dict[str, str | float | bool | None] = Field(default_factory=dict)


class LeadCreatedPayload(Phase65BaseModel):
    source: str = Field(max_length=64)


class OrderPlacedPayload(Phase65BaseModel):
    order_id: str
    lead_id: str

    @field_validator("order_id", "lead_id")
    @classmethod
    def _uuid_fields(cls, v: str) -> str:
        UUID(v)
        return v


class JobStartedPayload(Phase65BaseModel):
    job_id: str
    order_id: str

    @field_validator("job_id", "order_id")
    @classmethod
    def _uuid_fields(cls, v: str) -> str:
        UUID(v)
        return v


class RunCompletedPayload(Phase65BaseModel):
    run_id: str
    job_id: str
    duration_ms: int | None = Field(default=None, ge=0)

    @field_validator("run_id", "job_id")
    @classmethod
    def _uuid_fields(cls, v: str) -> str:
        UUID(v)
        return v


class PaymentCapturedPayload(Phase65BaseModel):
    payment_id: str
    invoice_id: str
    amount: float = Field(ge=0)

    @field_validator("payment_id", "invoice_id")
    @classmethod
    def _uuid_fields(cls, v: str) -> str:
        UUID(v)
        return v


class SkillRunStartedPayload(Phase65BaseModel):
    skill_run_id: str
    skill_card_id: str
    run_id: str | None = None

    @field_validator("skill_run_id", "skill_card_id", "run_id")
    @classmethod
    def _uuid_fields(cls, v: str | None) -> str | None:
        if v is None:
            return None
        UUID(v)
        return v


class ReplayRecordedPayload(Phase65BaseModel):
    replay_event_id: str
    target_entity_type: EntityType
    target_entity_id: str
    causation_event_id: str | None = None

    @field_validator("replay_event_id", "target_entity_id", "causation_event_id")
    @classmethod
    def _uuid_fields(cls, v: str | None) -> str | None:
        if v is None:
            return None
        UUID(v)
        return v


PAYLOAD_MODEL_BY_EVENT_TYPE: dict[str, type[Phase65BaseModel]] = {
    EventType.LEAD_CREATED.value: LeadCreatedPayload,
    EventType.ORDER_PLACED.value: OrderPlacedPayload,
    EventType.JOB_STARTED.value: JobStartedPayload,
    EventType.RUN_COMPLETED.value: RunCompletedPayload,
    EventType.PAYMENT_CAPTURED.value: PaymentCapturedPayload,
    EventType.SKILL_RUN_STARTED.value: SkillRunStartedPayload,
    EventType.REPLAY_EVENT_RECORDED.value: ReplayRecordedPayload,
}


class EventEnvelope(Phase65BaseModel):
    event_id: str
    event_type: EventType
    entity_type: EntityType
    entity_id: str
    occurred_at: str
    schema_version: str = Field(default=PHASE6_5_EVENTS_SCHEMA_VERSION_CONST)
    payload: dict[str, Any]
    metadata: EventMetadata

    @field_validator(FIELD_EVENT_ID, FIELD_ENTITY_ID)
    @classmethod
    def _uuid_fields(cls, v: str) -> str:
        UUID(v)
        return v

    @field_validator(FIELD_SCHEMA_VERSION)
    @classmethod
    def _events_schema_version(cls, v: str) -> str:
        if v != PHASE6_5_EVENTS_SCHEMA_VERSION_CONST:
            raise ValueError(f"schema_version must be {PHASE6_5_EVENTS_SCHEMA_VERSION_CONST!r}")
        return v

    @field_validator(FIELD_OCCURRED_AT)
    @classmethod
    def _occurred_at_iso(cls, v: Any) -> str:
        return _parse_iso_datetime(v)

    @model_validator(mode="after")
    def _event_allowed_for_entity(self) -> EventEnvelope:
        if not is_event_allowed(self.entity_type.value, self.event_type.value):
            raise ValueError(
                f"event_type {self.event_type.value!r} not allowed for "
                f"entity_type {self.entity_type.value!r}"
            )
        return self

    def validate_payload_typed(self) -> Phase65BaseModel:
        model_cls = PAYLOAD_MODEL_BY_EVENT_TYPE.get(self.event_type.value)
        if model_cls is None:
            return GenericEntityPayload.model_validate(self.payload)
        return model_cls.model_validate(self.payload)

    def to_contract_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data[FIELD_EVENT_TYPE] = self.event_type.value
        data[FIELD_ENTITY_TYPE] = self.entity_type.value
        return data


def build_event(
    event_type: str | EventType,
    entity_type: str | EntityType,
    entity_id: str,
    payload: dict[str, Any] | Phase65BaseModel,
    *,
    event_id: str | None = None,
    occurred_at: str | None = None,
    metadata: EventMetadata | dict[str, Any] | None = None,
    schema_version: str = PHASE6_5_EVENTS_SCHEMA_VERSION_CONST,
) -> dict[str, Any]:
    """
    Build and validate an event envelope; returns stable contract dict.
    """
    et = event_type.value if isinstance(event_type, EventType) else str(event_type)
    ent = entity_type.value if isinstance(entity_type, EntityType) else str(entity_type)
    if not is_event_allowed(ent, et):
        return {
            "ok": False,
            "message": f"event_type {et!r} not allowed for entity_type {ent!r}",
        }

    if isinstance(payload, Phase65BaseModel):
        payload_dict = payload.model_dump(mode="json")
    else:
        payload_dict = dict(payload)

    typed_model = PAYLOAD_MODEL_BY_EVENT_TYPE.get(et)
    try:
        if typed_model is not None:
            typed_model.model_validate(payload_dict)
        else:
            GenericEntityPayload.model_validate(payload_dict)
    except Exception as exc:  # noqa: BLE001 — contract boundary returns dict
        return {"ok": False, "message": str(exc)}

    if metadata is None:
        meta = EventMetadata()
    elif isinstance(metadata, EventMetadata):
        meta = metadata
    else:
        meta = EventMetadata.model_validate(metadata)

    if occurred_at is None:
        occurred_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if event_id is None:
        event_id = str(uuid4())

    try:
        envelope = EventEnvelope(
            event_id=event_id,
            event_type=EventType(et),
            entity_type=EntityType(ent),
            entity_id=entity_id,
            occurred_at=occurred_at,
            schema_version=schema_version,
            payload=payload_dict,
            metadata=meta,
        )
    except Exception as exc:  # noqa: BLE001 — contract boundary returns dict
        return {"ok": False, "message": str(exc)}

    return {"ok": True, "message": "event envelope valid", "event": envelope.to_contract_dict()}
