"""
Wave 6 intake gate request/result models (DATA-CLEANING · R2 appendix B).

Pure structured input only; no manifest/envelope/QA fields.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from core.schemas.intake import (
    GateCheckItem,
    GateDecisionLiteral,
    INTAKE_GATE_SCHEMA_VERSION,
    IntakeGateRequest as Phase75IntakeGateRequest,
    SourceChannelLiteral,
    WorkCategoryLiteral,
)

WAVE6_INTAKE_GATE_SCHEMA_VERSION = "wave6_intake_gate_v1"

VALID_PRODUCT_SKUS = frozenset({"CLEAN-BASIC", "CLEAN-ENRICH"})
SUGGESTED_PIPELINE_HINT = "code_cleaning_pipeline_v2"

_ISO639_1_RE = re.compile(r"^[a-z]{2}$", re.IGNORECASE)
_RISK_SCAN_LEVELS = frozenset({"none", "metadata_only"})
_LLM_ASSIST_LEVELS = frozenset({"off", "on_failures_only"})

SKU_TAG_ALIASES: dict[str, str] = {
    "sku:clean-basic": "CLEAN-BASIC",
    "sku:clean-enrich": "CLEAN-ENRICH",
    "sku:CLEAN-BASIC": "CLEAN-BASIC",
    "sku:CLEAN-ENRICH": "CLEAN-ENRICH",
}

SIZE_POLICY_ACK_TAGS = frozenset(
    {
        "size_policy:acknowledged",
        "size_policy_ack",
        "enterprise",
        "enterprise:w6",
    }
)


class _Wave6IntakeBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IntakeGateRequest(_Wave6IntakeBase):
    """Wave 6 inbound gate payload (Phase 7.5 fields + R2 SKU fields)."""

    description: str = ""
    tags: list[str] = Field(default_factory=list)
    explicit_task_type: str = ""
    source_channel: SourceChannelLiteral = "unknown"
    file_extension_hints: list[str] = Field(default_factory=list)
    inbound_path_hint: str = ""
    batch_size_hint: int | None = None
    product_sku: str = ""
    enrichment_profile: dict[str, Any] | None = None
    client_ref: str = ""

    @field_validator(
        "description",
        "explicit_task_type",
        "inbound_path_hint",
        "product_sku",
        "client_ref",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, v: Any) -> Any:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("tags", "file_extension_hints", mode="before")
    @classmethod
    def _normalize_str_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        out: list[str] = []
        for item in v:
            s = str(item).strip()
            if s:
                out.append(s)
        return out

    @field_validator("enrichment_profile", mode="before")
    @classmethod
    def _empty_profile_to_none(cls, v: Any) -> dict[str, Any] | None:
        if v is None:
            return None
        if isinstance(v, dict) and not v:
            return None
        if not isinstance(v, dict):
            raise ValueError("enrichment_profile must be an object")
        return v

    @model_validator(mode="after")
    def _require_some_signal(self) -> IntakeGateRequest:
        if self.description or self.tags or self.explicit_task_type:
            return self
        raise ValueError("at least one of description, tags, or explicit_task_type is required")

    def combined_text(self) -> str:
        parts = [
            self.description,
            self.explicit_task_type,
            self.client_ref,
            self.product_sku,
            *self.tags,
        ]
        if self.inbound_path_hint:
            parts.append(self.inbound_path_hint)
        for ext in self.file_extension_hints:
            parts.append(ext)
        return " ".join(p for p in parts if p).strip()

    def to_phase75_request(self) -> Phase75IntakeGateRequest:
        return Phase75IntakeGateRequest(
            description=self.description,
            tags=self.tags,
            explicit_task_type=self.explicit_task_type,
            source_channel=self.source_channel,
            file_extension_hints=self.file_extension_hints,
            inbound_path_hint=self.inbound_path_hint,
            batch_size_hint=self.batch_size_hint,
        )


class IntakeGateResult(_Wave6IntakeBase):
    """Wave 6 gate decision (intake-only; no manifest/envelope/QA artifacts)."""

    ok: Literal[True] = True
    decision: GateDecisionLiteral
    work_category: WorkCategoryLiteral
    confidence: float = Field(ge=0.0, le=1.0)
    message: str
    suggested_task_type: str | None = None
    suggested_pipeline: str | None = None
    suggested_product_sku: str | None = None
    gate_checks: list[GateCheckItem] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    defer_fields_needed: list[str] = Field(default_factory=list)
    schema_version: str = WAVE6_INTAKE_GATE_SCHEMA_VERSION
    intake_gate_schema_version: str = INTAKE_GATE_SCHEMA_VERSION
    phase6_5_pre_state: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class IntakeGateFailure(_Wave6IntakeBase):
    ok: Literal[False] = False
    decision: GateDecisionLiteral = "reject"
    work_category: WorkCategoryLiteral = "unknown"
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    message: str
    suggested_task_type: str | None = None
    suggested_pipeline: str | None = None
    suggested_product_sku: str | None = None
    gate_checks: list[GateCheckItem] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    defer_fields_needed: list[str] = Field(default_factory=list)
    schema_version: str = WAVE6_INTAKE_GATE_SCHEMA_VERSION
    intake_gate_schema_version: str = INTAKE_GATE_SCHEMA_VERSION
    phase6_5_pre_state: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
