"""
Pydantic models for Wave 6 data-cleaning envelope v2.0.

Scope of this module is intentionally narrow:
- per-file truth only
- no billable_u / billable_l
- no manifest-level aggregation logic
"""

from __future__ import annotations

import re
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ENVELOPE_V2_SCHEMA_VERSION = "2.0"
ENRICHMENT_V0_1_SCHEMA_VERSION = "enrichment_v0.1"
ENVELOPE_V2_JSON_SCHEMA_REF = "shared/schemas/envelope_v2.json"

CleanStatusLiteral = Literal["ok", "rejected", "parse_failed", "skipped"]
ContentKindLiteral = Literal["code", "doc", "config", "binary_like", "unknown"]
ReviewPriorityLiteral = Literal["low", "medium", "high"]
EnrichmentProvenanceLiteral = Literal["rules", "llm", "mixed"]

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_LEAKY_PATH_RE = re.compile(r"(?:^[a-zA-Z]:[\\/])|(?:://)|(?:^\\\\)")


class _EnvelopeBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContentSummary(_EnvelopeBase):
    line_count: int = Field(ge=0)
    char_count: int = Field(ge=0)
    imports: list[str] = Field(default_factory=list)
    preview_lines: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("imports", "preview_lines", mode="before")
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


class EnrichmentSignals(_EnvelopeBase):
    has_parse_warnings: bool
    used_llm: bool
    line_count: int = Field(ge=0)
    import_count: int = Field(ge=0)


class EnrichmentBlock(_EnvelopeBase):
    schema_version: Literal["enrichment_v0.1"] = ENRICHMENT_V0_1_SCHEMA_VERSION
    present: bool
    detected_language: str | None = None
    domain_tags: list[str] = Field(default_factory=list, max_length=8)
    content_kind: ContentKindLiteral | None = None
    quality_score: int | None = Field(default=None, ge=0, le=100)
    review_priority: ReviewPriorityLiteral | None = None
    enrichment_provenance: EnrichmentProvenanceLiteral | None = None
    signals: EnrichmentSignals | None = None

    @field_validator("detected_language", mode="before")
    @classmethod
    def _normalize_language(cls, v: Any) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @field_validator("domain_tags", mode="before")
    @classmethod
    def _normalize_tags(cls, v: Any) -> list[str]:
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
    def _validate_present_shape(self) -> EnrichmentBlock:
        if self.present:
            missing = [
                name
                for name, value in (
                    ("detected_language", self.detected_language),
                    ("content_kind", self.content_kind),
                    ("quality_score", self.quality_score),
                    ("review_priority", self.review_priority),
                    ("enrichment_provenance", self.enrichment_provenance),
                    ("signals", self.signals),
                )
                if value is None
            ]
            if missing:
                raise ValueError(f"enrichment.present=true requires: {', '.join(missing)}")
            return self

        forbidden_when_absent = {
            "detected_language": self.detected_language,
            "content_kind": self.content_kind,
            "quality_score": self.quality_score,
            "review_priority": self.review_priority,
            "enrichment_provenance": self.enrichment_provenance,
            "signals": self.signals,
        }
        dirty = [name for name, value in forbidden_when_absent.items() if value is not None]
        if dirty:
            raise ValueError(
                f"enrichment.present=false must not carry populated fields: {', '.join(dirty)}"
            )
        return self


class EnvelopeBaseV2(_EnvelopeBase):
    schema_version: Literal["2.0"] = ENVELOPE_V2_SCHEMA_VERSION
    file_id: str = Field(min_length=1, max_length=128)
    content_sha256: str
    clean_status: CleanStatusLiteral
    name: str = Field(min_length=1, max_length=512)
    extension: str = Field(min_length=1, max_length=32)
    original_type: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(ge=0)
    encoding: str | None = None
    stored_logical_path: str = Field(min_length=1, max_length=512)
    content_summary: ContentSummary
    groq_used: bool = False
    groq_reason: str | None = None
    parse_strategy: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @field_validator(
        "file_id",
        "name",
        "extension",
        "original_type",
        "encoding",
        "stored_logical_path",
        "groq_reason",
        "parse_strategy",
        mode="before",
    )
    @classmethod
    def _strip_text(cls, v: Any) -> Any:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("warnings", mode="before")
    @classmethod
    def _normalize_warnings(cls, v: Any) -> list[str]:
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

    @field_validator("content_sha256")
    @classmethod
    def _validate_sha256(cls, v: str) -> str:
        vv = v.strip().lower()
        if not _HEX64_RE.fullmatch(vv):
            raise ValueError("content_sha256 must be lowercase hex64")
        return vv

    @field_validator("stored_logical_path")
    @classmethod
    def _forbid_path_leak(cls, v: str) -> str:
        if _LEAKY_PATH_RE.search(v):
            raise ValueError("stored_logical_path must be logical only, not disk or URL path")
        return v

    @model_validator(mode="after")
    def _normalize_groq_reason(self) -> EnvelopeBaseV2:
        if self.groq_used:
            return self
        self.groq_reason = None
        return self

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class BasicEnvelopeV2(EnvelopeBaseV2):
    groq_used: Literal[False] = False


class EnrichEnvelopeV2(EnvelopeBaseV2):
    enrichment: EnrichmentBlock

    @model_validator(mode="after")
    def _validate_enrichment_for_status(self) -> EnrichEnvelopeV2:
        if self.clean_status == "ok" and not self.enrichment.present:
            raise ValueError("clean_status=ok requires enrichment.present=true")
        return self


EnvelopeV2: TypeAlias = BasicEnvelopeV2 | EnrichEnvelopeV2
