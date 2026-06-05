"""Test-compatible shim for ask I-bridge / H-line context wiring."""

from __future__ import annotations

from typing import Any, Callable


def ensure_k1_packages_on_path() -> None:
    """No-op in shim; real implementation adjusts sys.path for K-1 packages."""


def _import_build_rooted_context() -> Callable[..., dict[str, Any]]:
    from core.context_entry import build_rooted_context

    return build_rooted_context
