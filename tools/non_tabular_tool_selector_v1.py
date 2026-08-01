"""Non-Tabular Tool Selector v1 stub (W9-T3).

Pure mapping from non-tabular task_type and case_profile to symbolic planned_tools.
Does not invoke tools, external APIs, or heavy processors.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_PATH = _REPO_ROOT / "tools" / "non_tabular_tool_catalog_v1.json"
_ROUTING_CATALOG_PATH = _REPO_ROOT / "routing" / "non_tabular_routing_catalog_v1.yaml"

_NT_A_PROFILE_HINTS = frozenset({"docu-corp", "docu_corp", "docu-corp/2026-0001"})
_NT_B_PROFILE_HINTS = frozenset({"log-analytics-co", "log_analytics_co", "log-analytics-co/2026-0001"})

_NT_A_TASK_TYPES = frozenset(
    {
        "non_tabular.document.extract",
        "non-tabular.document.extract",
        "non-tabular.document.clean_and_annotate",
    }
)
_NT_B_TASK_TYPES = frozenset(
    {
        "non_tabular.log.analyze",
        "non-tabular.log.analyze",
        "non-tabular.log.parse_and_summarize",
    }
)

# Fallback when routing YAML is absent (W9-T1 skeleton); aligns with
# docs/non-tabular-routing-catalog-v1.md default_tools → W9-T3 catalog tool_ids.
_DEFAULT_TOOLS_BY_TASK_TYPE: Dict[str, List[str]] = {
    "non_tabular.document.extract": ["text_extractor", "doc_classifier"],
    "non_tabular.document.clean_and_annotate": ["text_extractor", "doc_classifier"],
    "non_tabular.log.analyze": ["log_parser", "anomaly_summarizer"],
    "non_tabular.log.parse_and_summarize": ["log_parser", "anomaly_summarizer"],
}

_INPUT_KIND_BY_TOOL: Dict[str, str] = {
    "text_extractor": "document",
    "doc_classifier": "document",
    "log_parser": "log",
    "anomaly_summarizer": "log",
}

# W9-T1 routing catalog symbolic names → W9-T3 catalog tool_ids (stub mapping).
_SYMBOLIC_TO_CATALOG_TOOL: Dict[str, Optional[str]] = {
    "validate.content_accessible": None,
    "extract.text_content": "text_extractor",
    "extract.metadata": "doc_classifier",
    "parse.log_structure": "log_parser",
    "analyze.anomaly_patterns": "anomaly_summarizer",
    "transform.normalize": None,
    "analyze.content_stats": None,
    "bundle.multi_format": None,
}


def _load_catalog() -> Dict[str, Any]:
    with _CATALOG_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise RuntimeError("non-tabular catalog root must be a mapping")
    return data


def _catalog_tools_by_id(catalog: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    cat = catalog if catalog is not None else _load_catalog()
    return {
        str(tool["tool_id"]): tool
        for tool in cat.get("tools", [])
        if isinstance(tool, dict) and tool.get("tool_id")
    }


def _is_non_tabular_family(task_type: str) -> bool:
    return task_type.startswith("non_tabular.") or task_type.startswith("non-tabular.")


def _normalize_task_type(task_type: str) -> str:
    if task_type.startswith("non-tabular."):
        return "non_tabular." + task_type[len("non-tabular.") :]
    return task_type


def _error(message: str, selector_rule_id: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "message": message,
        "selector_rule_id": selector_rule_id,
        "plan_only": True,
        "flow_family": "non_tabular",
        "profile_tier": None,
        "planned_tools": [],
    }


def _success(
    message: str,
    selector_rule_id: str,
    profile_tier: str,
    planned_tools: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "ok": True,
        "message": message,
        "selector_rule_id": selector_rule_id,
        "plan_only": True,
        "flow_family": "non_tabular",
        "profile_tier": profile_tier,
        "planned_tools": planned_tools,
    }


def _resolve_profile_tier(task_type: str, case_profile: str) -> str:
    normalized_tt = _normalize_task_type(task_type)
    profile_lower = case_profile.strip().lower()

    if (
        task_type in _NT_A_TASK_TYPES
        or normalized_tt.startswith("non_tabular.document.")
    ):
        return "NT-A"
    if (
        task_type in _NT_B_TASK_TYPES
        or normalized_tt.startswith("non_tabular.log.")
    ):
        return "NT-B"

    if any(hint in profile_lower for hint in _NT_A_PROFILE_HINTS):
        return "NT-A"
    if any(hint in profile_lower for hint in _NT_B_PROFILE_HINTS):
        return "NT-B"
    return "unknown"


def _translate_routing_tool_ids(tool_ids: List[str]) -> List[str]:
    translated: List[str] = []
    for tool_id in tool_ids:
        mapped = _SYMBOLIC_TO_CATALOG_TOOL.get(tool_id, tool_id)
        if mapped:
            translated.append(mapped)
    return translated


def _load_routing_default_tools(task_type: str) -> Optional[List[str]]:
    normalized_tt = _normalize_task_type(task_type)
    if not _ROUTING_CATALOG_PATH.is_file():
        return _DEFAULT_TOOLS_BY_TASK_TYPE.get(normalized_tt) or _DEFAULT_TOOLS_BY_TASK_TYPE.get(
            task_type
        )

    try:
        import yaml  # type: ignore
    except ImportError:
        return _DEFAULT_TOOLS_BY_TASK_TYPE.get(normalized_tt)

    try:
        data = yaml.safe_load(_ROUTING_CATALOG_PATH.read_text(encoding="utf-8"))
    except OSError:
        return _DEFAULT_TOOLS_BY_TASK_TYPE.get(normalized_tt)

    if not isinstance(data, dict):
        return _DEFAULT_TOOLS_BY_TASK_TYPE.get(normalized_tt)

    for entry in data.get("task_types") or []:
        if not isinstance(entry, dict):
            continue
        entry_tt = str(entry.get("task_type") or "")
        if entry_tt == task_type or _normalize_task_type(entry_tt) == normalized_tt:
            tools = entry.get("default_tools")
            if isinstance(tools, list) and tools:
                translated = _translate_routing_tool_ids([str(t) for t in tools])
                if translated:
                    return translated
    return _DEFAULT_TOOLS_BY_TASK_TYPE.get(normalized_tt)


def _tools_for_profile_tier(profile_tier: str) -> List[str]:
    if profile_tier == "NT-A":
        return ["text_extractor", "doc_classifier"]
    if profile_tier == "NT-B":
        return ["log_parser", "anomaly_summarizer"]
    return []


def _resolve_tool_ids(task_type: str, profile_tier: str) -> Tuple[List[str], str]:
    routing_tools = _load_routing_default_tools(task_type)
    if routing_tools:
        return routing_tools, "routing_catalog.default_tools"

    tier_tools = _tools_for_profile_tier(profile_tier)
    if tier_tools:
        return tier_tools, f"{profile_tier.lower()}.profile_tier_tools"

    return [], "error.no_tool_mapping"


def _planned_tool_entry(tool: Dict[str, Any], reason: str) -> Dict[str, Any]:
    tool_id = str(tool["tool_id"])
    return {
        "tool_id": tool_id,
        "reason": reason,
        "input_kind": str(tool.get("input_kind") or _INPUT_KIND_BY_TOOL.get(tool_id, "unknown")),
        "output_kind": str(tool.get("output_kind") or "unknown"),
        "maturity": str(tool.get("maturity") or "experimental"),
        "symbolic_only": True,
    }


def select_non_tabular_tools(
    task_type: str,
    case_profile: str,
    *,
    max_tools: int = 3,
) -> Dict[str, Any]:
    """Recommend symbolic non-tabular tools for a task_type and case_profile.

    Returns a stable dict with ok, message, selector_rule_id, flow_family,
    profile_tier, and planned_tools (symbolic only; no execution).
    """
    if not _is_non_tabular_family(task_type):
        return _error(
            f"unsupported task_type: {task_type} (not non_tabular family)",
            "error.not_non_tabular_family",
        )

    if max_tools < 1:
        return _error("max_tools must be >= 1", "error.invalid_max_tools")

    profile_tier = _resolve_profile_tier(task_type, case_profile)
    if profile_tier == "unknown":
        return _error(
            f"unknown non_tabular profile for task_type={task_type}, case_profile={case_profile}",
            "error.unknown_non_tabular_profile",
        )

    tool_ids, mapping_source = _resolve_tool_ids(task_type, profile_tier)
    if not tool_ids:
        return _error(
            f"no tool mapping for task_type={task_type}, profile_tier={profile_tier}",
            "error.no_tool_mapping",
        )

    catalog_by_id = _catalog_tools_by_id()
    planned: List[Dict[str, Any]] = []
    input_kind_filter: Optional[str] = "document" if profile_tier == "NT-A" else "log"

    for tool_id in tool_ids:
        if len(planned) >= max_tools:
            break
        tool = catalog_by_id.get(tool_id)
        if tool is None:
            return _error(
                f"catalog missing tool_id: {tool_id}",
                "error.catalog_tool_id",
            )
        if input_kind_filter and str(tool.get("input_kind")) != input_kind_filter:
            continue
        planned.append(
            _planned_tool_entry(
                tool,
                reason=f"{mapping_source}; profile_tier={profile_tier}; case_profile={case_profile}",
            )
        )

    if not planned:
        return _error(
            f"no catalog tools matched input_kind={input_kind_filter} for profile_tier={profile_tier}",
            "error.no_matching_tools",
        )

    rule_id = f"{profile_tier.lower()}.{task_type.split('.')[-1]}"
    return _success(
        f"non-tabular shadow selection for {profile_tier} ({len(planned)} symbolic tools)",
        rule_id,
        profile_tier,
        planned,
    )
