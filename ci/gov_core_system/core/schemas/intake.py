"""
Pydantic models for Phase 7.5 intake / gate (data-cleaning work only).

Wire shape is consumed by ``core.intake_decider``; public functions return plain ``dict``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

INTAKE_GATE_SCHEMA_VERSION = "intake_gate_v1"
INTAKE_GATE_JSON_SCHEMA_REF = "shared/schemas/intake_gate_v1.json"

GateDecisionLiteral = Literal["accept", "reject", "defer"]
WorkCategoryLiteral = Literal["data_cleaning", "other", "unknown"]

SourceChannelLiteral = Literal[
    "telegram",
    "cli",
    "watchdog",
    "api",
    "unknown",
]


class _IntakeBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IntakeGateRequest(_IntakeBase):
    """Inbound work order signals before routing to factory / dark.data runners."""

    description: str = ""
    tags: list[str] = Field(default_factory=list)
    explicit_task_type: str = ""
    source_channel: SourceChannelLiteral = "unknown"
    file_extension_hints: list[str] = Field(default_factory=list)
    inbound_path_hint: str = ""
    batch_size_hint: int | None = None

    @field_validator("description", "explicit_task_type", "inbound_path_hint", mode="before")
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

    @model_validator(mode="after")
    def _require_some_signal(self) -> IntakeGateRequest:
        if self.description or self.tags or self.explicit_task_type:
            return self
        raise ValueError("at least one of description, tags, or explicit_task_type is required")

    def combined_text(self) -> str:
        parts = [self.description, self.explicit_task_type, *self.tags]
        if self.inbound_path_hint:
            parts.append(self.inbound_path_hint)
        for ext in self.file_extension_hints:
            parts.append(ext)
        return " ".join(p for p in parts if p).strip()


class GateCheckItem(_IntakeBase):
    id: str
    passed: bool
    detail: str = ""


class EntityPreStateHint(_IntakeBase):
    """Phase 6.5 entity row expected before/after gate (see phase6_5_entities_v1.json)."""

    entity_type: Literal["lead", "requirement_profile", "order"]
    pre_status: str
    next_status: str | None = None
    next_event_type: str | None = None
    field_mapping: dict[str, str] = Field(default_factory=dict)
    notes: str = ""


class Phase65PreStateBundle(_IntakeBase):
    """Aligns gate decision with lead / requirement_profile / order pre-states."""

    contract_tier: str = "mvp_v0.1"
    entities_schema_version: str = "v1"
    events_schema_version: str = "v1"
    decision: GateDecisionLiteral
    lead: EntityPreStateHint | None = None
    requirement_profile: EntityPreStateHint | None = None
    order: EntityPreStateHint | None = None
    authority: dict[str, str] | None = None


class IntakeGateResult(_IntakeBase):
    """Canonical success envelope (also returned as dict from decider)."""

    ok: Literal[True] = True
    decision: GateDecisionLiteral
    work_category: WorkCategoryLiteral
    confidence: float = Field(ge=0.0, le=1.0)
    message: str
    suggested_task_type: str | None = None
    suggested_pipeline: str | None = None
    gate_checks: list[GateCheckItem] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    schema_version: str = INTAKE_GATE_SCHEMA_VERSION
    phase6_5_pre_state: Phase65PreStateBundle | dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class IntakeGateFailure(_IntakeBase):
    ok: Literal[False] = False
    decision: GateDecisionLiteral = "reject"
    work_category: WorkCategoryLiteral = "unknown"
    confidence: float = 0.0
    message: str
    suggested_task_type: str | None = None
    suggested_pipeline: str | None = None
    gate_checks: list[GateCheckItem] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    schema_version: str = INTAKE_GATE_SCHEMA_VERSION
    phase6_5_pre_state: Phase65PreStateBundle | dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
