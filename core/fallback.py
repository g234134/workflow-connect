"""Test-compatible shim for retrieve fallback helpers."""

from __future__ import annotations

from typing import Any


def should_use_retrieve_stub(*_args: Any, **_kwargs: Any) -> bool:
    return False


def retrieve_stub_fallback(query: str, top_k: int, **_kwargs: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "message": "shim retrieve ok",
        "query": query,
        "top_k": top_k,
        "hits": [],
    }
