"""
Structured error builders for gov_core (Package C + D).

Do not duplicate ERR_* keys — import from ``core.gov_core_contracts``.
"""

from __future__ import annotations

from typing import Any

from core.gov_core_contracts import (
    ERR_KEY_CODE,
    ERR_KEY_DETAILS,
    ERR_KEY_MESSAGE,
    ERR_KEY_NODE,
    ERR_KEY_RETRYABLE,
    ERR_KEY_SCHEMA_VERSION,
    ERROR_SCHEMA_VERSION,
)


class ErrorCode:
    HEALTH_FAILED = "HEALTH_FAILED"
    INGEST_FAILED = "INGEST_FAILED"
    VERIFY_FAILED = "VERIFY_FAILED"
    RETRIEVE_FAILED = "RETRIEVE_FAILED"
    ANSWER_FAILED = "ANSWER_FAILED"
    PIPELINE_FAILED = "PIPELINE_FAILED"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    BUSINESS_VALIDATION_FAILED = "BUSINESS_VALIDATION_FAILED"
    MALFORMED_JSON = "MALFORMED_JSON"
    EMPTY_PAYLOAD = "EMPTY_PAYLOAD"
    HUMAN_REJECTED = "HUMAN_REJECTED"
    UNKNOWN = "UNKNOWN"


NODE_ERROR_CODES: dict[str, str] = {
    "health_node": ErrorCode.HEALTH_FAILED,
    "ingest_node": ErrorCode.INGEST_FAILED,
    "verify_node": ErrorCode.VERIFY_FAILED,
    "retrieve_node": ErrorCode.RETRIEVE_FAILED,
    "answer_node": ErrorCode.ANSWER_FAILED,
    "human_confirm": ErrorCode.HUMAN_REJECTED,
    "start": ErrorCode.UNKNOWN,
    "retrieve_context": ErrorCode.RETRIEVE_FAILED,
    "decide": ErrorCode.UNKNOWN,
    "finish": ErrorCode.UNKNOWN,
}


def code_for_node(node: str, *, explicit_code: str | None = None) -> str:
    if explicit_code:
        return explicit_code
    return NODE_ERROR_CODES.get(node, ErrorCode.UNKNOWN)


def build_structured_error(
    node: str,
    code: str,
    message: str,
    *,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from core.error_taxonomy import META_KEY_ERROR_CATEGORY, taxonomy_from_structured_error

    merged_details = dict(details) if details else {}
    out: dict[str, Any] = {
        ERR_KEY_SCHEMA_VERSION: ERROR_SCHEMA_VERSION,
        ERR_KEY_CODE: code,
        ERR_KEY_MESSAGE: str(message),
        ERR_KEY_NODE: node,
        ERR_KEY_RETRYABLE: bool(retryable),
    }
    tags = taxonomy_from_structured_error(
        {
            "code": code,
            "message": message,
            "retryable": retryable,
            "details": merged_details or None,
        }
    )
    merged_details.setdefault(META_KEY_ERROR_CATEGORY, tags[META_KEY_ERROR_CATEGORY])
    merged_details.setdefault("error_code", tags["error_code"])
    out[ERR_KEY_DETAILS] = merged_details
    return out


class GovCoreError(Exception):
    """Raised when a node fails with a contract-shaped structured error."""

    def __init__(self, structured_error: dict[str, Any]) -> None:
        self.structured_error = dict(structured_error)
        self.retryable = bool(structured_error.get(ERR_KEY_RETRYABLE, False))
        super().__init__(str(structured_error.get(ERR_KEY_MESSAGE, "")))

    def as_dict(self) -> dict[str, Any]:
        return dict(self.structured_error)


def raise_node_error(
    node: str,
    message: str,
    *,
    code: str | None = None,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> None:
    err = build_structured_error(
        node,
        code_for_node(node, explicit_code=code),
        message,
        retryable=retryable,
        details=details,
    )
    raise GovCoreError(err)
