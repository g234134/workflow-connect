"""
Pydantic models for unified structured errors (Task Package C).

Contract wire keys (``code``, ``message``, ``node``, …) are canonical;
``to_unified_dict()`` adds Task C aliases (``success``, ``error_type``, …).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.errors import build_structured_error
from core.gov_core_contracts import (
    ERR_KEY_CODE,
    ERR_KEY_DETAILS,
    ERR_KEY_ERROR_CONTEXT,
    ERR_KEY_ERROR_MESSAGE,
    ERR_KEY_ERROR_TYPE,
    ERR_KEY_MESSAGE,
    ERR_KEY_NODE,
    ERR_KEY_RETRYABLE,
    ERR_KEY_SCHEMA_VERSION,
    ERR_KEY_SOURCE_AGENT,
    ERR_KEY_SUCCESS,
    ERROR_SCHEMA_VERSION,
)


class StructuredError(BaseModel):
    """Contract-shaped structured error (maps to ``structured_errors[]``)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    error_schema_version: str = Field(default=ERROR_SCHEMA_VERSION)
    code: str
    message: str
    node: str
    retryable: bool = False
    details: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> StructuredError:
        return cls.model_validate(raw)

    def to_contract_dict(self) -> dict[str, Any]:
        return build_structured_error(
            self.node,
            self.code,
            self.message,
            retryable=self.retryable,
            details=self.details,
        )

    def to_unified_dict(self) -> dict[str, Any]:
        """Task C unified view: canonical keys + human-oriented aliases."""
        base = self.to_contract_dict()
        base[ERR_KEY_SUCCESS] = False
        base[ERR_KEY_ERROR_TYPE] = self.code
        base[ERR_KEY_ERROR_MESSAGE] = self.message
        base[ERR_KEY_SOURCE_AGENT] = self.node
        if self.details is not None:
            base[ERR_KEY_ERROR_CONTEXT] = self.details
        return base


class UnifiedErrorEnvelope(BaseModel):
    """
    Top-level API error envelope when a flow fails validation or business rules.

    ``semantic_success=True`` + ``business_failure=True`` means the graph ran
    but the output is not usable (schema / business assertion failure).
    """

    model_config = ConfigDict(extra="forbid")

    success: bool = False
    ok: bool = False
    semantic_success: bool = False
    business_failure: bool = False
    errors: list[str] = Field(default_factory=list)
    structured_errors: list[dict[str, Any]] = Field(default_factory=list)
    validation_errors: list[dict[str, Any]] = Field(default_factory=list)
    message: str | None = None

    def to_api_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "ok": self.ok,
            "success": self.success,
            "semantic_success": self.semantic_success,
            "business_failure": self.business_failure,
            "errors": list(self.errors),
        }
        if self.message is not None:
            out["message"] = self.message
        if self.structured_errors:
            out["structured_errors"] = self.structured_errors
        if self.validation_errors:
            out["validation_errors"] = self.validation_errors
        return out
