"""
W3-B-SELECTOR-HOOK — kb_index_status read-only tool gate (Wave B minimal).

Pure decision logic only; does not read case files, ENG-CTX, or external storage.
Contract: ``workflow_v2/20_pilot/W3-B_kb_contract.md`` §5.4.
"""

from __future__ import annotations

import os
import re
from typing import Any

# Wave C: set GOV_KB_INDEX_SELECTOR_HOOK_ENABLED=1 after runtime wiring from case/ENG-CTX.
KB_INDEX_SELECTOR_HOOK_ENV = "GOV_KB_INDEX_SELECTOR_HOOK_ENABLED"

_VALID_KB_INDEX_STATUS = frozenset({"ready", "stale", "missing"})

# repo_* tools whose names indicate retrieve / graph read (not index/embed jobs).
_REPO_RETRIEVE_GRAPH_PATTERN = re.compile(
    r"^repo_.*(retrieve|graph|rag_query)",
    re.IGNORECASE,
)

_HOOK_RULE_ID = "W3-B-SELECTOR-HOOK"


def is_repo_index_gated_tool(tool_name: str) -> bool:
    """Return True when ``tool_name`` is a repo retrieve/graph class tool."""
    name = str(tool_name or "").strip()
    if not name:
        return False
    return bool(_REPO_RETRIEVE_GRAPH_PATTERN.match(name))


def kb_index_selector_hook_enabled() -> bool:
    """Feature flag for prod wiring (default OFF until Wave C)."""
    return os.environ.get(KB_INDEX_SELECTOR_HOOK_ENV, "0").strip() in {"1", "true", "yes"}


def decide_kb_index_tool_gate(kb_index_status: str, tool_name: str) -> dict[str, Any]:
    """
    Decide allow / degrade / block for a tool given ``kb_index_status``.

    Returns a stable dict with ``ok``, ``decision``, ``message``, and ``audit_tags``.
    """
    status = str(kb_index_status or "").strip().lower()
    tool = str(tool_name or "").strip()

    base_tags: list[str] = [f"hook:{_HOOK_RULE_ID}"]
    if tool:
        base_tags.append(f"tool:{tool}")

    if not is_repo_index_gated_tool(tool):
        return {
            "ok": True,
            "decision": "allow",
            "message": "non-repo retrieve/graph tool; kb_index gate not applied",
            "audit_tags": base_tags + ["gate:skipped_non_repo_tool"],
        }

    base_tags.append("gate:repo_retrieve_graph")

    if status not in _VALID_KB_INDEX_STATUS:
        return {
            "ok": False,
            "decision": "block",
            "message": f"unknown kb_index_status={kb_index_status!r}; blocking repo retrieve/graph tool",
            "audit_tags": base_tags + ["kb_index:unknown", "decision:block"],
        }

    base_tags.append(f"kb_index:{status}")

    if status == "missing":
        return {
            "ok": True,
            "decision": "block",
            "message": "kb_index_status=missing blocks repo retrieve/graph tools",
            "audit_tags": base_tags + ["decision:block"],
        }

    if status == "stale":
        return {
            "ok": True,
            "decision": "degrade",
            "message": "kb_index_status=stale degrades repo retrieve/graph tools (audit cost_class=high)",
            "audit_tags": base_tags + ["decision:degrade", "cost_class:high"],
        }

    # ready
    return {
        "ok": True,
        "decision": "allow",
        "message": "kb_index_status=ready allows repo retrieve/graph tools",
        "audit_tags": base_tags + ["decision:allow"],
    }
