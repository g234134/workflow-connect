"""
Retry policy helpers (feature-flagged via GOV_CORE_RETRY_POLICY_ENABLED).

When the flag is off, config readers still return defaults for snapshots; invoke
retry behavior is gated in ``core.retry_invoke``.

Public API:
- ``is_retryable_error`` — transient / contract retryable only
- ``compute_backoff_delay_ms`` — exponential backoff, capped, optional jitter
- ``execute_with_retry`` — retry loop for callables (no DLQ; use ``retry_invoke`` for workflow)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
from typing import Any, Callable, Mapping, TypeVar

from core.gov_core_contracts import (
    CHECKPOINT_CONFIG_SCHEMA_VERSION,
    CP_KEY_ATTEMPT,
    CP_KEY_BACKOFF_MS,
    CP_KEY_MAX_ATTEMPTS,
    CP_KEY_RUN_ID,
    CP_KEY_SCHEMA_VERSION,
    ERR_KEY_CODE,
    ERR_KEY_RETRYABLE,
    LOG_LOGGER_RETRY,
)
from shared.naming import (
    DEFAULT_RETRY_BASE_DELAY_MS,
    DEFAULT_RETRY_MAX_ATTEMPTS,
    DEFAULT_RETRY_MAX_DELAY_MS,
    ENV_FEATURE_RETRY_POLICY,
    ENV_RETRY_BACKOFF_MS,
    ENV_RETRY_BACKOFF_MULTIPLIER,
    ENV_RETRY_BASE_DELAY_MS,
    ENV_RETRY_MAX_ATTEMPTS,
    ENV_RETRY_MAX_DELAY_MS,
)

_TRUTHY = frozenset({"1", "true", "yes", "on"})

_DEFAULT_BACKOFF_MULTIPLIER = 2.0

T = TypeVar("T")

# Fail-fast error codes (business / schema / malformed — never retry).
_NON_RETRYABLE_ERROR_CODES: frozenset[str] = frozenset(
    {
        "SCHEMA_VALIDATION_FAILED",
        "BUSINESS_VALIDATION_FAILED",
        "MALFORMED_JSON",
        "EMPTY_PAYLOAD",
        "HUMAN_REJECTED",
    }
)

_NON_RETRYABLE_EXCEPTION_TYPES: tuple[type[BaseException], ...] = (
    ValueError,
    TypeError,
    KeyError,
    json.JSONDecodeError,
)


def is_retry_policy_enabled() -> bool:
    raw = (os.environ.get(ENV_FEATURE_RETRY_POLICY) or "").strip().lower()
    return raw in _TRUTHY


def get_retry_logger() -> logging.Logger:
    return logging.getLogger(LOG_LOGGER_RETRY)


def _parse_positive_int(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        get_retry_logger().warning("invalid %s=%r; using default %s", name, raw, default)
        return default
    if value < 1:
        get_retry_logger().warning("%s=%s < 1; using default %s", name, value, default)
        return default
    return value


def _parse_positive_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        get_retry_logger().warning("invalid %s=%r; using default %s", name, raw, default)
        return default
    if value < 1.0:
        get_retry_logger().warning("%s=%s < 1; using default %s", name, value, default)
        return default
    return value


def max_attempts() -> int:
    return _parse_positive_int(ENV_RETRY_MAX_ATTEMPTS, DEFAULT_RETRY_MAX_ATTEMPTS)


def base_delay_ms() -> int:
    raw = (os.environ.get(ENV_RETRY_BASE_DELAY_MS) or "").strip()
    if raw:
        return _parse_positive_int(ENV_RETRY_BASE_DELAY_MS, DEFAULT_RETRY_BASE_DELAY_MS)
    return _parse_positive_int(ENV_RETRY_BACKOFF_MS, DEFAULT_RETRY_BASE_DELAY_MS)


def max_delay_ms() -> int:
    return _parse_positive_int(ENV_RETRY_MAX_DELAY_MS, DEFAULT_RETRY_MAX_DELAY_MS)


def backoff_ms_base() -> int:
    """Alias for ``base_delay_ms`` (legacy name)."""
    return base_delay_ms()


def backoff_multiplier() -> float:
    return _parse_positive_float(ENV_RETRY_BACKOFF_MULTIPLIER, _DEFAULT_BACKOFF_MULTIPLIER)


def compute_backoff_delay_ms(
    attempt: int,
    *,
    base_delay_ms: int = DEFAULT_RETRY_BASE_DELAY_MS,
    max_delay_ms: int = DEFAULT_RETRY_MAX_DELAY_MS,
    jitter: bool = True,
) -> int:
    """
    Exponential backoff for 1-based ``attempt`` (first retry delay uses 2^0 * base).

    Capped at ``max_delay_ms``. When ``jitter`` is True, returns a value in
    ``[0, capped]`` (full jitter) for thundering-herd mitigation.
    """
    if attempt < 1:
        attempt = 1
    exp = int(base_delay_ms * (2 ** (attempt - 1)))
    capped = min(max(0, exp), max_delay_ms)
    if not jitter or capped <= 0:
        return capped
    return random.randint(0, capped)


def compute_backoff_ms(attempt: int) -> int:
    """Legacy exponential backoff (no jitter); used in checkpoint snapshots."""
    if attempt < 1:
        attempt = 1
    base = backoff_ms_base()
    mult = backoff_multiplier()
    delay = int(base * (mult ** (attempt - 1)))
    return min(max(0, delay), max_delay_ms())


def checkpoint_config_fields(
    *,
    run_id: str = "",
    attempt: int = 1,
) -> dict[str, Any]:
    """Contract-shaped checkpoint/retry metadata (read-only)."""
    return {
        CP_KEY_SCHEMA_VERSION: CHECKPOINT_CONFIG_SCHEMA_VERSION,
        CP_KEY_RUN_ID: (run_id or "").strip(),
        CP_KEY_ATTEMPT: max(1, int(attempt)),
        CP_KEY_MAX_ATTEMPTS: max_attempts(),
        CP_KEY_BACKOFF_MS: compute_backoff_delay_ms(
            max(1, int(attempt)),
            base_delay_ms=base_delay_ms(),
            max_delay_ms=max_delay_ms(),
            jitter=False,
        ),
    }


def make_idempotency_key(
    run_id: str,
    operation: str,
    *parts: str,
) -> str:
    """Stable idempotency key for a logical operation within a run."""
    payload = {
        "run_id": (run_id or "").strip() or "unknown",
        "operation": (operation or "").strip() or "invoke",
        "parts": [str(p) for p in parts],
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"),
    ).hexdigest()
    return f"gov_core:{digest[:32]}"


def _error_code_from_mapping(value: Mapping[str, Any]) -> str | None:
    code = value.get(ERR_KEY_CODE)
    if code is not None and str(code).strip():
        return str(code).strip()
    return None


def _retryable_from_mapping(value: Mapping[str, Any]) -> bool | None:
    if ERR_KEY_RETRYABLE in value:
        return bool(value[ERR_KEY_RETRYABLE])
    return None


def _structured_from_exc(exc: BaseException) -> Mapping[str, Any] | None:
    for attr in ("structured_error", "error_dict", "as_dict"):
        candidate = getattr(exc, attr, None)
        if callable(candidate):
            try:
                candidate = candidate()
            except Exception:  # noqa: BLE001
                candidate = None
        if isinstance(candidate, Mapping):
            return candidate
    return None


def _is_non_retryable_code(code: str | None) -> bool:
    return bool(code and code in _NON_RETRYABLE_ERROR_CODES)


def is_retryable_error(
    error: BaseException,
    *,
    node_id: str | None = None,
) -> bool:
    """
    Decide whether ``error`` should be retried.

    Fail-fast: business validation, schema validation, malformed input, and
    explicit ``retryable=False``. Retries transient network/timeouts and errors
    marked retryable in structured payloads or node policy.
    """
    if isinstance(error, _NON_RETRYABLE_EXCEPTION_TYPES):
        return False

    detail = getattr(error, "detail", None)
    if isinstance(detail, Mapping):
        code = _error_code_from_mapping(detail)
        if _is_non_retryable_code(code):
            return False

    structured = _structured_from_exc(error)
    if structured is not None:
        code = _error_code_from_mapping(structured)
        if _is_non_retryable_code(code):
            return False

    retryable = getattr(error, ERR_KEY_RETRYABLE, None)
    if retryable is not None:
        return bool(retryable)

    if isinstance(detail, Mapping):
        found = _retryable_from_mapping(detail)
        if found is not None:
            return found

    if structured is not None:
        found = _retryable_from_mapping(structured)
        if found is not None:
            return found

    try:
        from core.errors import GovCoreError
    except ImportError:
        GovCoreError = ()  # type: ignore[misc, assignment]

    if GovCoreError and isinstance(error, GovCoreError):
        if structured is None:
            structured = error.as_dict()
        if node_id:
            from core.node_policy import merge_retryable_from_node

            return merge_retryable_from_node(
                error,
                node_id=node_id,
                structured=error.as_dict(),
            )
        return bool(getattr(error, ERR_KEY_RETRYABLE, False))

    from core.node_policy import RETRYABLE_EXCEPTION_TYPES, merge_retryable_from_node

    if isinstance(error, RETRYABLE_EXCEPTION_TYPES):
        return True

    if node_id:
        return merge_retryable_from_node(error, node_id=node_id, structured=structured)

    return False


def execute_with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int,
    base_delay_ms: int,
    max_delay_ms: int,
    node_id: str | None = None,
) -> T:
    """
    Invoke ``fn`` with retries on transient / retryable errors only.

    Does not enqueue DLQ or emit retry logs — use ``retry_invoke`` for workflow paths.
    """
    attempts_limit = max(1, int(max_attempts))
    last_exc: BaseException | None = None

    for attempt in range(1, attempts_limit + 1):
        try:
            return fn()
        except BaseException as exc:  # noqa: BLE001
            last_exc = exc
            if not is_retryable_error(exc, node_id=node_id):
                raise
            if attempt >= attempts_limit:
                raise
            delay = compute_backoff_delay_ms(
                attempt,
                base_delay_ms=base_delay_ms,
                max_delay_ms=max_delay_ms,
            )
            if delay > 0:
                time.sleep(delay / 1000.0)

    assert last_exc is not None  # pragma: no cover
    raise last_exc


def sleep_backoff(attempt: int) -> None:
    """Block for the backoff interval of ``attempt`` (1-based), using env defaults."""
    delay_ms = compute_backoff_delay_ms(
        attempt,
        base_delay_ms=base_delay_ms(),
        max_delay_ms=max_delay_ms(),
    )
    if delay_ms > 0:
        time.sleep(delay_ms / 1000.0)
