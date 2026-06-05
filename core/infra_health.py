"""Test-compatible shim for ask flow health gate."""

from __future__ import annotations

from typing import Any


def run_full_healthcheck(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    return {"ok": True, "all_ok": True, "message": "shim health ok"}
