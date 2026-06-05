"""D2 context / memory layer (v0.1 mock)."""

from contract.constants import MAX_TOTAL_TOKEN_BUDGET

from .context_builder import (
    ROOT_MIN_TOKENS,
    ROOT_RESERVED_TOKENS,
    TRIM_PRIORITY,
    build_context,
    estimate_tokens,
)

__all__ = [
    "MAX_TOTAL_TOKEN_BUDGET",
    "ROOT_MIN_TOKENS",
    "ROOT_RESERVED_TOKENS",
    "TRIM_PRIORITY",
    "build_context",
    "estimate_tokens",
]
