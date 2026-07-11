"""Routing → Tabular Tool Layer glue v1 (W4-T1).

Pure mapping from W2 intake routing catalog task_type to W3-TL selector intent
and planned tool_ids. Does not invoke Selector, Executor, or E2E drivers.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROUTING_CATALOG_PATH = _REPO_ROOT / "routing" / "intake_routing_catalog_v1.yaml"
_TABULAR_CATALOG_PATH = _REPO_ROOT / "tools" / "tabular_tool_catalog_v1.json"
_CASES_INDEX_PATH = _REPO_ROOT / "cases" / "index.json"

# Feature flag (default off). This ticket does not wire into main-chain CLIs.
TABULAR_ROUTING_GLUE_ENABLED = os.environ.get("TABULAR_ROUTING_GLUE_ENABLED", "0") == "1"

_SUPPORTED_TASK_TYPES = frozenset(
    {
        "tabular.cleaning.mvp",
        "tabular.cleaning.regression",
        "tabular.intake.new_case",
    }
)

_SELECTOR_TASK_TYPE_BY_ROUTE: Dict[str, str] = {
    "tabular.cleaning.mvp": "e2e",
    "tabular.cleaning.regression": "e2e",
    "tabular.intake.new_case": "gate_only",
}

_DEMO_PHASE_GATE_NOTES = ("phase_like", "phase_demo")
_SAMPLECO_GATE_NOTES = ("phase_like", "multi_row_export", "schema_ambiguous")


def _load_routing_catalog() -> Dict[str, Any]:
    text = _ROUTING_CATALOG_PATH.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ImportError as exc:
        raise RuntimeError("pyyaml required to load intake routing catalog") from exc
    if not isinstance(data, dict):
        raise RuntimeError("routing catalog root must be a mapping")
    return data


def _load_tabular_catalog() -> Dict[str, Any]:
    with _TABULAR_CATALOG_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise RuntimeError("tabular catalog root must be a mapping")
    return data


def _tabular_tool_ids(catalog: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    cat = catalog if catalog is not None else _load_tabular_catalog()
    return {
        str(tool["tool_id"]): bool(tool.get("enabled", False))
        for tool in cat.get("tools", [])
    }


def _route_by_task_type(catalog: Dict[str, Any], task_type: str) -> Optional[Dict[str, Any]]:
    for route in catalog.get("routes", []):
        if isinstance(route, dict) and route.get("task_type") == task_type:
            return route
    return None


def _normalize_case_dir(case_dir: str) -> Path:
    path = Path(case_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path.resolve()


def _load_intake(case_path: Path) -> Optional[Dict[str, Any]]:
    intake_path = case_path / "intake.json"
    if not intake_path.is_file():
        return None
    with intake_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_cases_index_entry(case_path: Path) -> Optional[Dict[str, Any]]:
    if not _CASES_INDEX_PATH.is_file():
        return None
    with _CASES_INDEX_PATH.open(encoding="utf-8") as fh:
        index = json.load(fh)
    rel = case_path.relative_to(_REPO_ROOT).as_posix()
    for entry in index.get("cases", []):
        if not isinstance(entry, dict):
            continue
        entry_dir = str(entry.get("case_dir", "")).replace("\\", "/")
        if entry_dir == rel:
            return entry
    return None


def _detect_case_profile(
    case_path: Path,
    intake: Optional[Dict[str, Any]],
    index_entry: Optional[Dict[str, Any]],
) -> Tuple[str, List[str], List[str]]:
    """Return (profile_id, gate_notes, notes)."""
    notes: List[str] = []
    gate_notes: List[str] = []

    case_id = str((intake or {}).get("case_id") or case_path.name)
    client_ref = str((intake or {}).get("client_ref") or "")

    if case_id == "demo_phase" or client_ref == "internal-demo" or case_path.name == "demo_phase":
        profile = "demo_phase"
        gate_notes = list(_DEMO_PHASE_GATE_NOTES)
        notes.append("demo_phase fixture; clean.phase_demo requires --force for review_needed gate")
        if index_entry:
            if index_entry.get("gate_status") == "review_needed":
                notes.append("gate_status=review_needed per cases/index.json")
            for limit in index_entry.get("known_limits") or []:
                if limit == "manual_review_required":
                    notes.append("manual_review_required")
        return profile, gate_notes, notes

    if client_ref == "sampleco" or (
        case_path.parent.name == "sampleco" and case_path.name == "2026-0001"
    ):
        profile = "sampleco"
        gate_notes = list(_SAMPLECO_GATE_NOTES)
        notes.append("human_review_required for clean.phase_demo")
        notes.append("schema notes: multi_row_export, schema_ambiguous")
        return profile, gate_notes, notes

    rel = case_path.relative_to(_REPO_ROOT).as_posix()
    cleaning_profile = str((intake or {}).get("cleaning_profile") or "")
    if rel == "cases/internal/generic-low-risk" or cleaning_profile == "generic_low_risk_profile":
        profile = "generic-low-risk"
        notes.append("generic_low_risk_profile")
        notes.append("owned_provenance_low_risk_schema")
        return profile, gate_notes, notes

    profile = case_id or case_path.name
    notes.append("unknown fixture profile; planned_tools from routing catalog only")
    return profile, gate_notes, notes


def _validate_planned_tools(
    planned_tools: List[str],
    routing_tool_ids: List[str],
    enabled_tools: Dict[str, bool],
) -> Optional[str]:
    if not planned_tools:
        return "planned_tools empty"
    routing_set = set(routing_tool_ids)
    for tool_id in planned_tools:
        if tool_id not in enabled_tools:
            return f"tabular catalog missing or unknown tool_id: {tool_id}"
        if not enabled_tools[tool_id]:
            return f"tabular catalog tool disabled: {tool_id}"
        if routing_set and tool_id not in routing_set:
            return f"tool_id {tool_id} not in routing catalog route tool_ids"
    return None


def plan_tabular_route(task_type: str, case_dir: str) -> Dict[str, Any]:
    """Build a Tabular MVP routing plan from W2 task_type and case_dir metadata.

    Returns a stable dict with at least ``ok``, ``task_type``, ``case_dir``;
    on success also ``selector_task_type``, ``planned_tools``, ``notes``.
    """
    normalized_case = _normalize_case_dir(case_dir)
    rel_case_dir = normalized_case.relative_to(_REPO_ROOT).as_posix()

    base: Dict[str, Any] = {
        "ok": False,
        "task_type": task_type,
        "case_dir": rel_case_dir,
        "glue_enabled": TABULAR_ROUTING_GLUE_ENABLED,
    }

    if task_type not in _SUPPORTED_TASK_TYPES:
        base["message"] = "unsupported_task_type"
        base["notes"] = [f"supported: {sorted(_SUPPORTED_TASK_TYPES)}"]
        return base

    routing_catalog = _load_routing_catalog()
    route = _route_by_task_type(routing_catalog, task_type)
    if route is None:
        base["message"] = "route_not_found_in_routing_catalog"
        return base

    routing_tool_ids = [str(tid) for tid in route.get("tool_ids") or []]
    planned_tools = list(routing_tool_ids)
    selector_task_type = _SELECTOR_TASK_TYPE_BY_ROUTE[task_type]

    tabular_catalog = _load_tabular_catalog()
    enabled_tools = _tabular_tool_ids(tabular_catalog)
    validation_error = _validate_planned_tools(planned_tools, routing_tool_ids, enabled_tools)
    if validation_error:
        base["message"] = validation_error
        base["planned_tools"] = planned_tools
        return base

    intake = _load_intake(normalized_case)
    index_entry = _load_cases_index_entry(normalized_case)
    profile_id, gate_notes, profile_notes = _detect_case_profile(
        normalized_case, intake, index_entry
    )

    notes: List[str] = [
        "plan-only glue; does not invoke Selector or Executor",
        f"routing catalog route: {task_type}",
    ]
    notes.extend(profile_notes)

    orchestration_tool_id = route.get("orchestration_tool_id")
    if orchestration_tool_id:
        notes.append(f"orchestration_tool_id={orchestration_tool_id} (one-shot alternative)")

    result: Dict[str, Any] = {
        "ok": True,
        "message": f"planned {len(planned_tools)} tool(s) for {task_type}",
        "task_type": task_type,
        "case_dir": rel_case_dir,
        "case_profile": profile_id,
        "selector_task_type": selector_task_type,
        "planned_tools": planned_tools,
        "routing_catalog_tool_ids": routing_tool_ids,
        "glue_enabled": TABULAR_ROUTING_GLUE_ENABLED,
        "notes": notes,
    }

    if orchestration_tool_id:
        result["orchestration_tool_id"] = str(orchestration_tool_id)

    if gate_notes:
        result["inferred_gate_notes"] = list(gate_notes)

    if intake is None:
        result["notes"].append("warning: intake.json missing; profile inference limited")

    return result
