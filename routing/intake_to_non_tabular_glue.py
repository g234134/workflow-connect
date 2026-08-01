"""Routing → Non-Tabular Tool Layer glue v1 (W9-T4 preview).

Pure mapping from non_tabular routing catalog task_type to selector intent
and symbolic planned tool_ids. Does not invoke Selector, Executor, or main chain.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROUTING_CATALOG_PATH = _REPO_ROOT / "routing" / "non_tabular_routing_catalog_v1.yaml"

# Orchestrator-facing aliases → W9-T1 catalog task_type keys
_TASK_TYPE_ALIASES: Dict[str, str] = {
    "non_tabular.document.extract": "non-tabular.document.clean_and_annotate",
    "non_tabular.log.analyze": "non-tabular.log.parse_and_summarize",
    "non-tabular.document.extract": "non-tabular.document.clean_and_annotate",
    "non-tabular.log.analyze": "non-tabular.log.parse_and_summarize",
}

_SKILL_CARD_BY_PREFIX: Dict[str, str] = {
    "non_tabular.document.": "NT-A",
    "non_tabular.log.": "NT-B",
    "non-tabular.document.": "NT-A",
    "non-tabular.log.": "NT-B",
}


def _load_routing_catalog() -> Dict[str, Any]:
    text = _ROUTING_CATALOG_PATH.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ImportError as exc:
        raise RuntimeError("pyyaml required to load non-tabular routing catalog") from exc
    if not isinstance(data, dict):
        raise RuntimeError("non-tabular routing catalog root must be a mapping")
    return data


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


def _entry_by_task_type(catalog: Dict[str, Any], task_type: str) -> Optional[Dict[str, Any]]:
    for entry in catalog.get("task_types") or []:
        if not isinstance(entry, dict):
            continue
        entry_tt = str(entry.get("task_type") or "")
        if entry_tt == task_type:
            return entry
    return None


def _resolve_catalog_task_type(task_type: str) -> Tuple[Optional[str], Optional[str]]:
    if task_type in _TASK_TYPE_ALIASES:
        return _TASK_TYPE_ALIASES[task_type], None
    for prefix in _SKILL_CARD_BY_PREFIX:
        if task_type.startswith(prefix):
            return None, f"unsupported_non_tabular_task_type: {task_type}"
    return None, "not_non_tabular_family"


def _skill_card_for(task_type: str) -> Optional[str]:
    for prefix, card in _SKILL_CARD_BY_PREFIX.items():
        if task_type.startswith(prefix):
            return card
    return None


def _detect_case_profile(
    case_path: Path,
    intake: Optional[Dict[str, Any]],
    catalog_entry: Dict[str, Any],
) -> Tuple[str, List[str], List[str]]:
    notes: List[str] = []
    gate_notes: List[str] = []

    client_ref = str((intake or {}).get("client_ref") or "")
    case_id = str((intake or {}).get("case_id") or case_path.name)
    default_profile = str(catalog_entry.get("case_profile") or case_id)
    profile = client_ref or default_profile

    schema_hint = str((intake or {}).get("schema_hint") or catalog_entry.get("intake_schema") or "")
    content_type = str((intake or {}).get("content_type") or catalog_entry.get("content_type") or "")

    if schema_hint in ("schema-free", "semi-structured"):
        gate_notes.append("schema_flexibility")
    if not schema_hint:
        gate_notes.append("no_schema_hint")
    if content_type:
        gate_notes.append(content_type)

    risk_tier = str(catalog_entry.get("risk_tier") or "medium")
    notes.append(f"routing risk_tier={risk_tier}")
    notes.append(f"catalog case_profile={default_profile}")

    return profile, gate_notes, notes


def is_non_tabular_task_type(task_type: str) -> bool:
    if task_type.startswith("non_tabular.") or task_type.startswith("non-tabular."):
        return True
    return task_type in _TASK_TYPE_ALIASES


def plan_non_tabular_route(task_type: str, case_dir: str) -> Dict[str, Any]:
    """Build a Non-Tabular shadow routing plan from task_type and case_dir metadata."""
    normalized_case = _normalize_case_dir(case_dir)
    try:
        rel_case_dir = normalized_case.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        rel_case_dir = normalized_case.as_posix()

    base: Dict[str, Any] = {
        "ok": False,
        "task_type": task_type,
        "case_dir": rel_case_dir,
        "flow_family": "non_tabular",
        "preview_only": True,
    }

    if not is_non_tabular_task_type(task_type):
        base["message"] = "not_non_tabular_family"
        base["notes"] = ["task_type must start with non_tabular. or non-tabular."]
        return base

    catalog_task_type, alias_error = _resolve_catalog_task_type(task_type)
    if alias_error:
        base["message"] = alias_error.split(": ", 1)[0] if ": " in alias_error else alias_error
        base["notes"] = [alias_error]
        return base

    routing_catalog = _load_routing_catalog()
    entry = _entry_by_task_type(routing_catalog, str(catalog_task_type))
    if entry is None:
        base["message"] = "route_not_found_in_non_tabular_catalog"
        base["notes"] = [f"catalog_task_type={catalog_task_type}"]
        return base

    default_tools = [str(t) for t in entry.get("default_tools") or []]
    if not default_tools:
        base["message"] = "planned_tools empty"
        return base

    intake = _load_intake(normalized_case)
    profile_id, gate_notes, profile_notes = _detect_case_profile(normalized_case, intake, entry)

    notes: List[str] = [
        "plan-only non-tabular glue; does not invoke Selector or Executor",
        f"routing catalog entry: {catalog_task_type}",
        f"orchestrator task_type alias: {task_type}",
        "preview-only orchestrator (W9-T4); heavy tools not executed",
    ]
    notes.extend(profile_notes)
    entry_note = entry.get("notes")
    if entry_note:
        notes.append(str(entry_note).strip())

    selector_task_type = "document_extract" if _skill_card_for(task_type) == "NT-A" else "log_analyze"

    result: Dict[str, Any] = {
        "ok": True,
        "message": f"planned {len(default_tools)} symbolic routing tool(s) for {task_type}",
        "task_type": task_type,
        "catalog_task_type": catalog_task_type,
        "case_dir": rel_case_dir,
        "case_profile": profile_id,
        "selector_task_type": selector_task_type,
        "planned_tools": default_tools,
        "routing_catalog_tool_ids": default_tools,
        "flow_family": "non_tabular",
        "preview_only": True,
        "skill_card": _skill_card_for(task_type),
        "risk_tier": entry.get("risk_tier"),
        "notes": notes,
    }

    if gate_notes:
        result["inferred_gate_notes"] = list(gate_notes)

    if intake is None:
        result["notes"].append("warning: intake.json missing; profile inference limited")

    return result
