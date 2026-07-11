"""
Phase 6.5 shared Pydantic bases (strict extra=forbid on all models).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.contracts.phase6_5_data_contract import PHASE6_5_ENTITIES_SCHEMA_VERSION_CONST
from shared.naming import (
    FIELD_CREATED_AT,
    FIELD_RECORD_ID,
    FIELD_SCHEMA_VERSION,
    FIELD_TRACE_ID,
    FIELD_UPDATED_AT,
)


class Phase65BaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


def _parse_iso_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        datetime.fromisoformat(text)
        return value.strip()
    raise ValueError("expected ISO-8601 date-time string or datetime")


class EntityRecordBase(Phase65BaseModel):
    schema_version: str = Field(default=PHASE6_5_ENTITIES_SCHEMA_VERSION_CONST)
    id: str = Field(alias=FIELD_RECORD_ID, validation_alias=FIELD_RECORD_ID)
    status: str
    created_at: str = Field(alias=FIELD_CREATED_AT, validation_alias=FIELD_CREATED_AT)
    updated_at: str = Field(alias=FIELD_UPDATED_AT, validation_alias=FIELD_UPDATED_AT)
    trace_id: str | None = Field(default=None, alias=FIELD_TRACE_ID, validation_alias=FIELD_TRACE_ID)

    @field_validator(FIELD_SCHEMA_VERSION)
    @classmethod
    def _schema_version_must_be_v1(cls, v: str) -> str:
        if v != PHASE6_5_ENTITIES_SCHEMA_VERSION_CONST:
            raise ValueError(f"schema_version must be {PHASE6_5_ENTITIES_SCHEMA_VERSION_CONST!r}")
        return v

    @field_validator(FIELD_RECORD_ID)
    @classmethod
    def _id_must_be_uuid(cls, v: str) -> str:
        UUID(v)
        return v

    @field_validator(FIELD_CREATED_AT, FIELD_UPDATED_AT)
    @classmethod
    def _normalize_timestamps(cls, v: Any) -> str:
        return _parse_iso_datetime(v)

    def to_contract_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=False)
