"""Test-compatible shim for direct (no-RAG) ask answer."""

from __future__ import annotations

from typing import Any


def perform_direct_answer(
    question: str,
    *,
    retrieve_error: str | None = None,
    retrieve_error_type: str | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": True,
        "message": "ok",
        "question": question,
        "answer": f"direct:{question}",
        "sources": [],
        "answer_mode": "direct",
    }
    if retrieve_error:
        out["retrieve_fallback"] = True
        out["retrieve_error"] = retrieve_error
        out["answer_mode"] = "direct_fallback"
    if retrieve_error_type:
        out["retrieve_error_type"] = retrieve_error_type
    return out
