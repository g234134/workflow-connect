"""
Test-compatible shim for ask RAG selector (ASK-R1–R6).

Minimal rule-based ``decide_use_rag`` so CI / unit tests can import and run
without the full ``gov_core_system`` ask pipeline. Replace with production
selector when the dark-side module is available.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from core.kb_index_selector_hook import decide_kb_index_tool_gate

_GREETING_PATTERNS = (
    r"^你好[！!。.?？\s]*$",
    r"^您好[！!。.?？\s]*$",
    r"^hi[!.?\s]*$",
    r"^hello[!.?\s]*$",
    r"^hey[!.?\s]*$",
    r"^好的[！!。.?？\s]*$",
    r"^ok[!.?\s]*$",
    r"^okay[!.?\s]*$",
    r"^谢谢[！!。.?？\s]*$",
    r"^thanks[!.?\s]*$",
)

_KNOWLEDGE_PATTERNS = (
    r"\bwhat\b",
    r"\bhow\b",
    r"\bwhy\b",
    r"\bexplain\b",
    r"\bpipeline\b",
    r"\bpolicy\b",
    r"\bdocument\b",
    r"\bkb\b",
    r"\bknowledge\s*base\b",
    r"\bcontext\b",
    r"\bfrom\s+docs?\b",
    r"\baccording\s+to\b",
    r"如何",
    r"什麼",
    r"什麼是",
    r"為什麼",
    r"怎麼",
    r"文檔",
    r"文件",
    r"知識庫",
)


def _norm_query(query: Any) -> str:
    if query is None:
        return ""
    return str(query).strip()


def _get_hints(payload: Mapping[str, Any] | None, task_input: Mapping[str, Any] | None) -> dict[str, Any]:
    hints: dict[str, Any] = {}
    if isinstance(task_input, Mapping):
        raw = task_input.get("selector_hints")
        if isinstance(raw, Mapping):
            hints.update(raw)
    if isinstance(payload, Mapping):
        ti = payload.get("task_input")
        if isinstance(ti, Mapping):
            raw = ti.get("selector_hints")
            if isinstance(raw, Mapping):
                hints.update(raw)
    return hints


def _has_kb_context(payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(payload, Mapping):
        return False

    task_input = payload.get("task_input")
    if isinstance(task_input, Mapping):
        refs = task_input.get("context_refs")
        if isinstance(refs, (list, tuple)) and len(refs) > 0:
            return True

    working = payload.get("working_context")
    if isinstance(working, Mapping):
        ti = working.get("task_input")
        if isinstance(ti, Mapping):
            refs = ti.get("context_refs")
            if isinstance(refs, (list, tuple)) and len(refs) > 0:
                return True

    metadata = payload.get("metadata")
    if isinstance(metadata, Mapping):
        tags = metadata.get("tags")
        if isinstance(tags, (list, tuple)):
            lowered = {str(t).lower() for t in tags}
            if lowered & {"rag", "knowledge", "kb"}:
                return True

    ltm = payload.get("long_term_memory")
    if isinstance(ltm, Mapping):
        semantic = ltm.get("semantic")
        if isinstance(semantic, (list, tuple)) and len(semantic) > 0:
            return True
        if isinstance(semantic, Mapping) and semantic:
            return True

    return False


def _is_greeting_or_chitchat(query: str) -> bool:
    if not query:
        return True
    lowered = query.lower()
    for pattern in _GREETING_PATTERNS:
        if re.match(pattern, lowered, flags=re.IGNORECASE):
            return True
    return False


def _has_knowledge_pattern(query: str) -> bool:
    lowered = query.lower()
    for pattern in _KNOWLEDGE_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return True
    return False


def decide_use_rag(
    query: Any,
    *,
    context_payload: Mapping[str, Any] | None = None,
    task_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Decide whether the ask flow should run retrieve + RAG answer.

    Returns ``use_rag``, ``skip_rag``, ``selector_rule_id``, and ``answer_mode``.
    """
    q = _norm_query(query)
    hints = _get_hints(context_payload, task_input)

    if hints.get("force_no_rag"):
        return {
            "use_rag": False,
            "skip_rag": True,
            "selector_rule_id": "ASK-R1",
            "answer_mode": "direct",
        }
    if hints.get("force_rag"):
        return {
            "use_rag": True,
            "skip_rag": False,
            "selector_rule_id": "ASK-R1",
            "answer_mode": "rag",
        }

    if not q or _is_greeting_or_chitchat(q):
        return {
            "use_rag": False,
            "skip_rag": True,
            "selector_rule_id": "ASK-R2",
            "answer_mode": "direct",
        }

    if _has_kb_context(context_payload):
        return {
            "use_rag": True,
            "skip_rag": False,
            "selector_rule_id": "ASK-R4",
            "answer_mode": "rag",
        }

    if _has_knowledge_pattern(q):
        return {
            "use_rag": True,
            "skip_rag": False,
            "selector_rule_id": "ASK-R5",
            "answer_mode": "rag",
        }

    if len(q) < 10:
        return {
            "use_rag": False,
            "skip_rag": True,
            "selector_rule_id": "ASK-R3",
            "answer_mode": "direct",
        }

    return {
        "use_rag": True,
        "skip_rag": False,
        "selector_rule_id": "ASK-R6",
        "answer_mode": "rag",
    }


def apply_kb_index_tool_gate_from_hints(
    tool_name: str,
    *,
    selector_hints: Mapping[str, Any] | None = None,
    task_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Test harness entry for W3-B kb_index tool gate.

    Reads ``kb_index_status`` from ``selector_hints`` or ``task_input.selector_hints``.
    When absent, returns allow with ``gate:skipped_no_kb_index_status`` (no prod effect).
    """
    hints: dict[str, Any] = {}
    if isinstance(task_input, Mapping):
        raw = task_input.get("selector_hints")
        if isinstance(raw, Mapping):
            hints.update(raw)
    if isinstance(selector_hints, Mapping):
        hints.update(selector_hints)

    status = hints.get("kb_index_status")
    if status is None or str(status).strip() == "":
        return {
            "ok": True,
            "decision": "allow",
            "message": "kb_index_status not injected; gate skipped (test harness only)",
            "audit_tags": ["gate:skipped_no_kb_index_status"],
        }

    return decide_kb_index_tool_gate(str(status), tool_name)
