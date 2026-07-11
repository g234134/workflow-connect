"""
Pydantic contract models for Wave 6 manifest v2.0.

This is the minimal typed schema for the first coding sprint:
- one job-level manifest document
- one deduplicated row per content_sha256
- top-level accepted_units + billing_units
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WAVE6_MANIFEST_VERSION = "manifest_v2.0"
WAVE6_ENVELOPE_SCHEMA_VERSION = "2.0"
WAVE6_ENRICHMENT_SCHEMA_VERSION = "enrichment_v0.1"
WAVE6_BILLING_TABLE_VERSION_DEFAULT = "w6_billing_v0.1"

ProductSku = Literal["CLEAN-BASIC", "CLEAN-ENRICH"]
ReviewPriority = Literal["low", "medium", "high"]
ContentKind = Literal["code", "doc", "config", "binary_like", "unknown"]
EnrichmentProvenance = Literal["rules", "llm", "mixed"]

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ManifestContentSummary(_StrictModel):
    char_count: int = Field(ge=0)
    line_count: int = Field(ge=0)
    imports: list[str] = Field(default_factory=list)

    @field_validator("imports", mode="before")
    @classmethod
    def _normalize_imports(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("imports must be a list")
        out: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return out


class ManifestEnrichmentSignals(_StrictModel):
    has_parse_warnings: bool
    used_llm: bool
    line_count: int = Field(ge=0)
    import_count: int = Field(ge=0)


class ManifestEnrichment(_StrictModel):
    schema_version: Literal["enrichment_v0.1"] = WAVE6_ENRICHMENT_SCHEMA_VERSION
    detected_language: str = Field(min_length=1)
    domain_tags: list[str] = Field(default_factory=list, max_length=8)
    content_kind: ContentKind
    quality_score: int = Field(ge=0, le=100)
    review_priority: ReviewPriority
    enrichment_provenance: EnrichmentProvenance
    signals: ManifestEnrichmentSignals

    @field_validator("domain_tags", mode="before")
    @classmethod
    def _normalize_domain_tags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("domain_tags must be a list")
        out: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return out


class ManifestRow(_StrictModel):
    file_id: str = Field(min_length=1)
    name: str | None = None
    extension: str = Field(min_length=1)
    original_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    encoding: str | None = None
    content_sha256: str
    schema_version: str = WAVE6_ENVELOPE_SCHEMA_VERSION
    clean_status: str = Field(min_length=1)
    stored_logical_path: str = Field(min_length=1)
    parse_strategy: str | None = None
    warnings: list[str] = Field(default_factory=list)
    content_summary: ManifestContentSummary
    groq_used: bool = False
    groq_reason: str | None = None
    has_enrichment: bool = False
    enrichment: ManifestEnrichment | None = None

    @field_validator("content_sha256")
    @classmethod
    def _validate_sha256(cls, value: str) -> str:
        text = str(value).strip()
        if not _SHA256_RE.fullmatch(text):
            raise ValueError("content_sha256 must be a 64-char hex string")
        return text.lower()

    @field_validator("warnings", mode="before")
    @classmethod
    def _normalize_warnings(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("warnings must be a list")
        out: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return out

    @model_validator(mode="after")
    def _derive_has_enrichment(self) -> ManifestRow:
        self.has_enrichment = self.enrichment is not None
        return self

    def to_contract_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class Wave6ManifestJobRecord(_StrictModel):
    job_id: str = Field(min_length=1)
    sku: ProductSku


class ManifestBillingUnits(_StrictModel):
    U: int = Field(ge=0)
    L: int = Field(ge=0)


class ManifestV20(_StrictModel):
    schema_version: Literal["manifest_v2.0"] = WAVE6_MANIFEST_VERSION
    job_id: str = Field(min_length=1)
    product_sku: ProductSku
    billing_table_version: str = Field(min_length=1)
    accepted_units: int = Field(ge=0)
    billing_units: ManifestBillingUnits
    rows: list[ManifestRow] = Field(default_factory=list)

    def rows_for_qa(self) -> list[dict[str, Any]]:
        return [row.to_contract_dict() for row in self.rows]

    def to_contract_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


__all__ = [
    "ManifestBillingUnits",
    "ManifestContentSummary",
    "ManifestEnrichment",
    "ManifestEnrichmentSignals",
    "ManifestRow",
    "ManifestV20",
    "ProductSku",
    "WAVE6_BILLING_TABLE_VERSION_DEFAULT",
    "WAVE6_ENRICHMENT_SCHEMA_VERSION",
    "WAVE6_ENVELOPE_SCHEMA_VERSION",
    "WAVE6_MANIFEST_VERSION",
    "Wave6ManifestJobRecord",
]
