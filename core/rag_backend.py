"""Test-compatible shim for RAG answer backend."""

from __future__ import annotations

from typing import Any


def rag_answer(query: str, top_k: int, **_kwargs: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "message": "shim rag answer",
        "query": query,
        "top_k": top_k,
        "answer": f"rag:{query}",
        "sources": [],
    }
