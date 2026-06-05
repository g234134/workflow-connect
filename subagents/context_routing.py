"""
Context-driven subagent routing v0.1 (Sprint 1 · C-1).

Uses H-line context layers as an **additional signal** for downstream subagent choice.
Does not replace ask RAG selector (S1–S3) or HQ ``task_routing`` workers.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

DEFAULT_AGENT_ID = "default_subagent"
MONITORING_AGENT_ID = "monitoring_subagent"
ROUTING_VERSION = "context_routing_v0.1"

_RULE_MONITORING = "ROUTE-MON-1"
_RULE_DEFAULT = "ROUTE-DEF-0"

_MONITORING_TAG = frozenset({"monitoring", "observability", "alerting", "wave1_monitoring"})
_MONITORING_TEXT_RE = re.compile(
    r"(?:\bmonitoring\b|/monitoring/|alert[_\s-]?events?|dashboard|"
    r"监控|監控|可观测|可觀測|\bkpi?s?\b)",
    re.I,
)


def _normalize_tags(raw: Any) -> set[str]:
    if not isinstance(raw, list):
        return set()
    return {str(t).strip().lower() for t in raw if str(t or "").strip()}


def _task_input_from_working(working_context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(working_context, dict):
        return {}
    ti = working_context.get("task_input")
    return ti if isinstance(ti, dict) else {}


def _collect_text_blobs(
    root_context: dict[str, Any] | None,
    working_context: dict[str, Any] | None,
    long_term_memory: dict[str, Any] | None,
) -> list[str]:
    blobs: list[str] = []
    ti = _task_input_from_working(working_context)
    for key in ("goal", "query", "task_type", "domain", "description"):
        val = ti.get(key) or (working_context or {}).get(key)
        if val is not None and str(val).strip():
            blobs.append(str(val))
    if isinstance(root_context, dict):
        nav = root_context.get("navigation")
        if isinstance(nav, dict):
            blobs.extend(str(v) for v in nav.values() if v)
    if isinstance(long_term_memory, dict):
        structured = long_term_memory.get("structured")
        if isinstance(structured, dict):
            for row in structured.get("rows") or []:
                if isinstance(row, dict) and row.get("request_type"):
                    blobs.append(str(row["request_type"]))
    return blobs


def _explicit_target(task_input: dict[str, Any]) -> str | None:
    for key in ("subagent_target", "target_agent_id", "subagent_route"):
        raw = task_input.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def _is_monitoring_task(
    *,
    task_input: dict[str, Any],
    tags: set[str],
    text_blobs: list[str],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    explicit = _explicit_target(task_input)
    if explicit in (MONITORING_AGENT_ID, "monitoring"):
        reasons.append("explicit subagent_target=monitoring")
        return True, reasons

    task_type = str(task_input.get("task_type") or "").strip().lower()
    if task_type in {"monitoring", "observability", "alerting"}:
        reasons.append(f"task_type={task_type}")
        return True, reasons

    domain = str(task_input.get("domain") or "").strip().lower()
    if domain in {"monitoring", "observability"}:
        reasons.append(f"domain={domain}")
        return True, reasons

    overlap = tags.intersection(_MONITORING_TAG)
    if overlap:
        reasons.append(f"tags={sorted(overlap)}")
        return True, reasons

    joined = " ".join(text_blobs)
    if _MONITORING_TEXT_RE.search(joined):
        reasons.append("monitoring keyword in goal/query/context")
        return True, reasons

    return False, reasons


def route_task_by_context(
    root_context: dict[str, Any] | None,
    working_context: dict[str, Any] | None,
    long_term_memory: dict[str, Any] | None,
) -> str:
    """
    Minimal v0.1 route: monitoring signals → ``monitoring_subagent``, else default.

    Returns a stable ``target_agent_id`` string only; use ``build_route_decision`` for audit fields.
    """
    return str(build_route_decision(root_context, working_context, long_term_memory)["target_agent_id"])


def build_route_decision(
    root_context: dict[str, Any] | None,
    working_context: dict[str, Any] | None,
    long_term_memory: dict[str, Any] | None,
) -> dict[str, Any]:
    """Structured routing decision for metadata / LangGraph state attachment."""
    task_input = _task_input_from_working(working_context)
    tags = _normalize_tags(task_input.get("tags"))
    tags.update(_normalize_tags((working_context or {}).get("tags")))
    text_blobs = _collect_text_blobs(root_context, working_context, long_term_memory)

    explicit = _explicit_target(task_input)
    if explicit and explicit not in (MONITORING_AGENT_ID, "monitoring", DEFAULT_AGENT_ID):
        return {
            "ok": True,
            "target_agent_id": explicit,
            "routing_version": ROUTING_VERSION,
            "rule_id": "ROUTE-EXPLICIT",
            "reasons": [f"explicit subagent_target={explicit}"],
            "signal_only": True,
        }

    is_mon, mon_reasons = _is_monitoring_task(
        task_input=task_input,
        tags=tags,
        text_blobs=text_blobs,
    )
    if is_mon:
        return {
            "ok": True,
            "target_agent_id": MONITORING_AGENT_ID,
            "routing_version": ROUTING_VERSION,
            "rule_id": _RULE_MONITORING,
            "reasons": mon_reasons,
            "signal_only": True,
        }

    return {
        "ok": True,
        "target_agent_id": DEFAULT_AGENT_ID,
        "routing_version": ROUTING_VERSION,
        "rule_id": _RULE_DEFAULT,
        "reasons": ["no monitoring signals; default subagent"],
        "signal_only": True,
    }


def attach_subagent_route_to_context(context_built: dict[str, Any]) -> dict[str, Any]:
    """
    Copy *context_built* and write ``metadata.subagent_route`` (non-destructive to layers).

    Safe to call on ``build_rooted_context`` output before ask graph init.
    """
    out = deepcopy(context_built)
    decision = build_route_decision(
        out.get("root_context"),
        out.get("working_context"),
        out.get("long_term_memory"),
    )
    meta = out.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
        out["metadata"] = meta
    meta["subagent_route"] = decision
    return out


def enrich_init_with_subagent_route(
    init: dict[str, Any],
    *,
    task_id: str,
    context_built: dict[str, Any],
) -> dict[str, Any]:
    """Attach H-line payload + flat subagent route keys to LangGraph initial state."""
    payload = attach_subagent_route_to_context(context_built)
    route = (payload.get("metadata") or {}).get("subagent_route") or {}
    out = dict(init)
    out["_context_entry_task_id"] = task_id
    out["_context_entry_payload"] = payload
    out["_subagent_route"] = route
    out["_subagent_target_agent_id"] = route.get("target_agent_id", DEFAULT_AGENT_ID)
    return out
