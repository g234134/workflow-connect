"""
Error taxonomy for gov_core monitoring (Wave 3 / Chat A).

Maps structured error codes, exception types, and Langfuse payloads into stable
``error_category`` values stored in ``task_runs.metadata`` / ``step_runs.metadata``.

Categories (primary cause):
  - system_error: connectivity, timeout, dependency / infra
  - llm_error: model invocation, rate limit, token/context limits
  - validation_error: schema / business rule failures
  - config_error: missing or invalid configuration / environment
  - unknown: unclassified
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from core.errors import ErrorCode
from core.retry_policy import _NON_RETRYABLE_ERROR_CODES  # noqa: PLC2701

# Metadata keys (monitoring + DLQ extras)
META_KEY_ERROR_CATEGORY = "error_category"
META_KEY_ERROR_CODE = "error_code"
META_KEY_NON_RETRYABLE = "non_retryable"

# Stable category literals
CATEGORY_SYSTEM = "system_error"
CATEGORY_LLM = "llm_error"
CATEGORY_VALIDATION = "validation_error"
CATEGORY_CONFIG = "config_error"
CATEGORY_UNKNOWN = "unknown"

_ALL_CATEGORIES = frozenset(
    {
        CATEGORY_SYSTEM,
        CATEGORY_LLM,
        CATEGORY_VALIDATION,
        CATEGORY_CONFIG,
        CATEGORY_UNKNOWN,
    }
)

_VALIDATION_CODES = frozenset(
    {
        ErrorCode.SCHEMA_VALIDATION_FAILED,
        ErrorCode.BUSINESS_VALIDATION_FAILED,
        ErrorCode.MALFORMED_JSON,
        ErrorCode.EMPTY_PAYLOAD,
        ErrorCode.HUMAN_REJECTED,
        ErrorCode.VERIFY_FAILED,
    }
)

_LLM_NODE_CODES = frozenset(
    {
        ErrorCode.RETRIEVE_FAILED,
        ErrorCode.ANSWER_FAILED,
    }
)

_SYSTEM_NODE_CODES = frozenset(
    {
        ErrorCode.HEALTH_FAILED,
        ErrorCode.INGEST_FAILED,
        ErrorCode.PIPELINE_FAILED,
    }
)

_LLM_MESSAGE_RE = re.compile(
    r"(rate\s*limit|token|context\s*length|max\s*tokens|model\s*not\s*found|"
    r"openai|anthropic|completion|chat\s*completion|embedding)",
    re.IGNORECASE,
)

_SYSTEM_MESSAGE_RE = re.compile(
    r"(timeout|timed\s*out|connection|connect|unreachable|503|502|504|"
    r"service\s*unavailable|network|socket|dns|refused)",
    re.IGNORECASE,
)

_CONFIG_MESSAGE_RE = re.compile(
    r"(not\s*configured|missing\s*env|environment\s*variable|"
    r"database_url|credentials\s*missing|api\s*key|langfuse|config)",
    re.IGNORECASE,
)

_LLM_EXCEPTION_TYPES = frozenset(
    {
        "RateLimitError",
        "ContextLengthExceededError",
        "BadRequestError",
        "APIStatusError",
    }
)

_SYSTEM_EXCEPTION_TYPES = frozenset(
    {
        "TimeoutError",
        "ConnectionError",
        "ConnectTimeout",
        "ReadTimeout",
        "HTTPError",
        "URLError",
        "OSError",
        "BrokenPipeError",
    }
)


def normalize_error_code(
    *,
    error_code: str | None = None,
    error_type: str | None = None,
    langfuse_meta: Mapping[str, Any] | None = None,
) -> str | None:
    """Prefer explicit code; fall back to Langfuse metadata or error_type alias."""
    for candidate in (
        error_code,
        (langfuse_meta or {}).get("code") if langfuse_meta else None,
        (langfuse_meta or {}).get("error_type") if langfuse_meta else None,
        error_type,
    ):
        if candidate is not None and str(candidate).strip():
            return str(candidate).strip()
    return None


def classify_error(
    *,
    error_code: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    retryable: bool | None = None,
    exception_type: str | None = None,
    langfuse_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Classify a failure into taxonomy fields.

    Returns dict with keys: error_category, error_code, error_type, non_retryable.
    ``error_type`` mirrors machine code (same as error_code) for DLQ/monitoring alignment.
    """
    meta = langfuse_meta or {}
    if meta.get(META_KEY_ERROR_CATEGORY) in _ALL_CATEGORIES:
        code = normalize_error_code(
            error_code=error_code or meta.get(META_KEY_ERROR_CODE),
            error_type=error_type,
            langfuse_meta=meta,
        )
        non_retryable = meta.get(META_KEY_NON_RETRYABLE)
        if non_retryable is None and retryable is not None:
            non_retryable = not retryable
        elif non_retryable is None and code in _NON_RETRYABLE_ERROR_CODES:
            non_retryable = True
        return {
            META_KEY_ERROR_CATEGORY: str(meta[META_KEY_ERROR_CATEGORY]),
            META_KEY_ERROR_CODE: code or "UNKNOWN",
            "error_type": code or str(error_type or "UNKNOWN"),
            META_KEY_NON_RETRYABLE: bool(non_retryable) if non_retryable is not None else False,
        }

    code = normalize_error_code(
        error_code=error_code,
        error_type=error_type,
        langfuse_meta=meta,
    )
    msg = (error_message or "").strip()
    exc = (exception_type or error_type or "").strip()

    category = _category_from_signals(code=code, message=msg, exception_type=exc)
    non_retryable = _infer_non_retryable(code=code, retryable=retryable, category=category)

    resolved_code = code or exc or "UNKNOWN"
    return {
        META_KEY_ERROR_CATEGORY: category,
        META_KEY_ERROR_CODE: resolved_code,
        "error_type": resolved_code,
        META_KEY_NON_RETRYABLE: non_retryable,
    }


def _category_from_signals(
    *,
    code: str | None,
    message: str,
    exception_type: str,
) -> str:
    if code in _VALIDATION_CODES:
        return CATEGORY_VALIDATION
    if code in _LLM_NODE_CODES:
        if _LLM_MESSAGE_RE.search(message) or exception_type in _LLM_EXCEPTION_TYPES:
            return CATEGORY_LLM
        if _SYSTEM_MESSAGE_RE.search(message) or exception_type in _SYSTEM_EXCEPTION_TYPES:
            return CATEGORY_SYSTEM
        return CATEGORY_LLM
    if code in _SYSTEM_NODE_CODES:
        if _CONFIG_MESSAGE_RE.search(message):
            return CATEGORY_CONFIG
        return CATEGORY_SYSTEM
    if code == ErrorCode.PIPELINE_FAILED:
        if _CONFIG_MESSAGE_RE.search(message):
            return CATEGORY_CONFIG
        if _LLM_MESSAGE_RE.search(message):
            return CATEGORY_LLM
        if _SYSTEM_MESSAGE_RE.search(message):
            return CATEGORY_SYSTEM
        return CATEGORY_UNKNOWN
    if exception_type in _LLM_EXCEPTION_TYPES or _LLM_MESSAGE_RE.search(message):
        return CATEGORY_LLM
    if exception_type in _SYSTEM_EXCEPTION_TYPES or _SYSTEM_MESSAGE_RE.search(message):
        return CATEGORY_SYSTEM
    if _CONFIG_MESSAGE_RE.search(message):
        return CATEGORY_CONFIG
    if code in _NON_RETRYABLE_ERROR_CODES:
        return CATEGORY_VALIDATION
    return CATEGORY_UNKNOWN


def _infer_non_retryable(*, code: str | None, retryable: bool | None, category: str) -> bool:
    if retryable is False:
        return True
    if code and code in _NON_RETRYABLE_ERROR_CODES:
        return True
    if category == CATEGORY_VALIDATION:
        return True
    if category == CATEGORY_CONFIG:
        return True
    return False


def enrich_metadata_with_taxonomy(
    metadata: dict[str, Any],
    *,
    failed: bool,
    error_code: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    retryable: bool | None = None,
    exception_type: str | None = None,
    langfuse_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach flat taxonomy keys to metadata; no-op on success paths."""
    if not failed:
        return metadata
    tags = classify_error(
        error_code=error_code,
        error_type=error_type,
        error_message=error_message,
        retryable=retryable,
        exception_type=exception_type,
        langfuse_meta=langfuse_meta or metadata,
    )
    out = dict(metadata)
    out.update(tags)
    out["error_taxonomy"] = {
        META_KEY_ERROR_CATEGORY: tags[META_KEY_ERROR_CATEGORY],
        META_KEY_ERROR_CODE: tags[META_KEY_ERROR_CODE],
        META_KEY_NON_RETRYABLE: tags[META_KEY_NON_RETRYABLE],
    }
    return out


def taxonomy_from_structured_error(structured: Mapping[str, Any]) -> dict[str, Any]:
    """Build taxonomy dict from a contract-shaped structured error."""
    details = structured.get("details") if isinstance(structured.get("details"), dict) else {}
    return classify_error(
        error_code=str(structured.get("code") or ""),
        error_type=str(structured.get("code") or ""),
        error_message=str(structured.get("message") or ""),
        retryable=bool(structured.get("retryable", False)),
        exception_type=str(details.get("exception_type") or "") or None,
    )
