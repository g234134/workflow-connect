"""
Pydantic schemas for core LangGraph node / backend outputs.

Models use ``extra='ignore'`` so legacy fields from backends are preserved
when dumping validated payloads back into graph state.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _ExtraIgnore(BaseModel):
    model_config = ConfigDict(extra="ignore")


class SubCheckResult(_ExtraIgnore):
    ok: bool
    message: str = ""


class HealthCheckResult(_ExtraIgnore):
    """``run_full_healthcheck`` / ``health_node`` payload."""

    postgres: SubCheckResult | dict[str, Any] | None = None
    qdrant: SubCheckResult | dict[str, Any] | None = None
    verify: SubCheckResult | dict[str, Any] | None = None
    all_ok: bool | None = None
    ok: bool | None = None
    message: str | None = None

    @field_validator("postgres", "qdrant", "verify", mode="before")
    @classmethod
    def _coerce_subcheck(cls, v: Any) -> Any:
        if v is None or isinstance(v, dict):
            return v
        return None


class IngestBatchResult(_ExtraIgnore):
    """``ingest_batch`` / ``ingest_node`` payload."""

    ok: bool
    message: str = ""
    input_path: str | None = None
    chunks: int | None = Field(default=None, ge=0)
    files_total: int | None = Field(default=None, ge=0)
    files_ok: int | None = Field(default=None, ge=0)
    files_skipped: int | None = Field(default=None, ge=0)
    document_id: str | None = None
    doc_key: str | None = None


class VerifyBatchResult(_ExtraIgnore):
    """``verify_batch`` / ``verify_node`` payload."""

    ok: bool
    message: str = ""
    result: dict[str, Any] | list[Any] | str | int | bool | None = None


class RagSourceItem(_ExtraIgnore):
    rank: int = Field(..., ge=1)
    document_id: str | None = None
    doc_key: str | None = None
    score: float | None = None
    snippet: str | None = None

    @field_validator("score", mode="before")
    @classmethod
    def _non_negative_score(cls, v: Any) -> Any:
        if v is None:
            return v
        return v


class RetrieveSmokeResult(_ExtraIgnore):
    """``document_chunks_smoke_retrieve_and_verify`` / ``retrieve_node``."""

    ok: bool
    message: str = ""
    query: str = ""
    top_k: int = Field(1, ge=1)
    collection: str | None = None
    hits: list[dict[str, Any]] = Field(default_factory=list)


class RagAnswerResult(_ExtraIgnore):
    """``rag_answer`` / ``answer_node``."""

    ok: bool
    question: str = ""
    answer: str | None = None
    message: str = ""
    sources: list[RagSourceItem | dict[str, Any]] = Field(default_factory=list)
    llm_model: str | None = None
    answer_mode: str | None = None
    retrieve_fallback: bool | None = None
    retrieve_error: str | None = None
    retrieve_error_type: str | None = None


class LGStateEnvelope(_ExtraIgnore):
    """Whole-flow API payload after LangGraph (subset validated at boundary)."""

    mode: Literal["ask", "ingest_verify"] | str
    ok: bool | None = None
    query: str | None = None
    input_path: str | None = None
    top_k: int | None = Field(default=None, ge=1)
    health: dict[str, Any] | None = None
    ingest: dict[str, Any] | None = None
    verify: dict[str, Any] | None = None
    retrieve: dict[str, Any] | None = None
    answer: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)
    executed_nodes: list[str] = Field(default_factory=list)
    message: str | None = None
    semantic_success: bool | None = None
    business_failure: bool | None = None
    structured_errors: list[dict[str, Any]] | None = None
    validation_errors: list[dict[str, Any]] | None = None
