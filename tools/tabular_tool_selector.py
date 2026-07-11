"""Tabular Tool Selector v1 (W3-TL-T2).

Pure-function recommendations from case metadata and gate schema notes.
Does not invoke tools or modify E2E driver behavior.

W10-T2: optional read-only consumption of ``skills/approved_registry.json``
when ``TABULAR_APPROVED_REGISTRY_ENABLED=1`` (default off for backward compat).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_PATH = _REPO_ROOT / "tools" / "tabular_tool_catalog_v1.json"
_REGISTRY_PATH = _REPO_ROOT / "skills" / "approved_registry.json"
_ENV_REGISTRY_ENABLED = "TABULAR_APPROVED_REGISTRY_ENABLED"
_ENV_REGISTRY_STRICT = "TABULAR_APPROVED_REGISTRY_STRICT"

TOOL_VALIDATE_ELIGIBILITY = "validate.eligibility"
TOOL_CLEAN_PHASE_DEMO = "clean.phase_demo"
TOOL_EXPORT_DELIVERY_BUNDLE = "export.delivery_bundle"

# v1 static mapping for registry entries that only carry skill_id (W5-T1 schema).
# Entries may also include optional ``tool_ids`` on the registry row (preferred).
_SKILL_ID_TO_TOOL_IDS: Dict[str, List[str]] = {
    "draft-clean-basic-job-001": [TOOL_CLEAN_PHASE_DEMO],
    "skill-tabular-validate-eligibility": [TOOL_VALIDATE_ELIGIBILITY],
    "skill-tabular-export-delivery": [TOOL_EXPORT_DELIVERY_BUNDLE],
}

_VALID_TASK_TYPES = frozenset({"gate_only", "clean", "bundle", "e2e"})

# Known fixture gate notes (docs/mvp-standard-trace-path.md §3–§5)
_DEMO_PHASE_GATE_NOTES = ("phase_like", "phase_demo")
_SAMPLECO_GATE_NOTES = ("phase_like", "multi_row_export", "schema_ambiguous")


def _load_catalog() -> Dict[str, Any]:
    with _CATALOG_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _catalog_tool_ids() -> Dict[str, bool]:
    catalog = _load_catalog()
    return {
        str(tool["tool_id"]): bool(tool.get("enabled", False))
        for tool in catalog.get("tools", [])
    }


def _error(
    message: str,
    selector_rule_id: str,
) -> Dict[str, Any]:
    return {
        "ok": False,
        "message": message,
        "selector_rule_id": selector_rule_id,
        "plan_only": True,
        "candidate_tools": [],
    }


def _registry_filter_enabled() -> bool:
    return os.environ.get(_ENV_REGISTRY_ENABLED, "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _registry_filter_strict() -> bool:
    """Return True if fail-closed policy should apply when registry is bad/missing."""
    return os.environ.get(_ENV_REGISTRY_STRICT, "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _resolve_approved_tool_ids(entries: List[Any]) -> FrozenSet[str]:
    """Map approved registry rows to tabular catalog tool_ids."""
    result: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("selector_eligible") is False:
            continue
        tool_ids = entry.get("tool_ids")
        if isinstance(tool_ids, list) and tool_ids:
            for tool_id in tool_ids:
                if tool_id:
                    result.add(str(tool_id))
            continue
        skill_id = entry.get("skill_id")
        if skill_id:
            result.update(_SKILL_ID_TO_TOOL_IDS.get(str(skill_id), []))
    return frozenset(result)


def _load_approved_registry(
    registry_path: Optional[Path] = None,
    *,
    strict: bool = False,
) -> Dict[str, Any]:
    """Read-only load of approved skill registry.

    When strict=False (default): graceful degrade on missing/malformed/empty registry.
    When strict=True: return error dict with ok=False for missing/malformed/empty registry.
    """
    path = registry_path if registry_path is not None else _REGISTRY_PATH

    def _fail_closed_result(message: str) -> Dict[str, Any]:
        return {
            "ok": False,
            "degraded": False,
            "message": message,
            "approved_tool_ids": frozenset(),
            "error_rule_id": "error.registry_fail_closed",
        }

    def _degrade_result(message: str) -> Dict[str, Any]:
        return {
            "ok": True,
            "degraded": True,
            "message": message,
            "approved_tool_ids": frozenset(),
        }

    if not path.is_file():
        msg = "approved registry missing"
        return _fail_closed_result(msg) if strict else _degrade_result(f"{msg}; skipping approval filter")
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        msg = f"approved registry unreadable ({exc})"
        return _fail_closed_result(msg) if strict else _degrade_result(f"{msg}; skipping approval filter")
    if not isinstance(data, dict):
        msg = "approved registry malformed (not a dict)"
        return _fail_closed_result(msg) if strict else _degrade_result(f"{msg}; skipping approval filter")
    approved = data.get("approved")
    if not isinstance(approved, list):
        msg = "approved registry malformed (approved field missing or not a list)"
        return _fail_closed_result(msg) if strict else _degrade_result(f"{msg}; skipping approval filter")
    if not approved:
        msg = "approved registry empty"
        return _fail_closed_result(msg) if strict else _degrade_result(f"{msg}; skipping approval filter")
    tool_ids = _resolve_approved_tool_ids(approved)
    if not tool_ids:
        msg = "approved registry has no resolvable tool_id mappings"
        return _fail_closed_result(msg) if strict else _degrade_result(f"{msg}; skipping approval filter")
    return {
        "ok": True,
        "degraded": False,
        "message": f"approved registry loaded ({len(tool_ids)} tool_id(s))",
        "approved_tool_ids": tool_ids,
    }


def _apply_approved_registry(result: Dict[str, Any]) -> Dict[str, Any]:
    """Filter candidate_tools against approved registry when feature is enabled."""
    if not _registry_filter_enabled():
        return result
    if not result.get("ok"):
        return result

    strict = _registry_filter_strict()
    reg = _load_approved_registry(strict=strict)

    # Fail-closed: registry load error in strict mode blocks the selector
    if strict and not reg.get("ok", True):
        return _error(
            f"approved registry fail-closed: {reg['message']}",
            reg.get("error_rule_id", "error.registry_fail_closed"),
        )

    sidecar = {
        "enabled": True,
        "degraded": reg["degraded"],
        "message": reg["message"],
    }
    if reg["degraded"]:
        out = dict(result)
        out["approved_registry"] = sidecar
        out["message"] = f"{result['message']}; {reg['message']}"
        return out

    approved_ids = reg["approved_tool_ids"]
    sidecar["approved_tool_count"] = len(approved_ids)
    filtered: List[Dict[str, Any]] = []
    for item in result["candidate_tools"]:
        tool_id = str(item["tool_id"])
        if tool_id not in approved_ids:
            continue
        enriched = dict(item)
        enriched["approval_status"] = "approved"
        filtered.append(enriched)

    if not filtered and result["candidate_tools"]:
        return _error(
            "no candidates pass approved registry filter",
            "error.registry_not_approved",
        )

    out = dict(result)
    out["candidate_tools"] = filtered
    out["approved_registry"] = sidecar
    out["message"] = f"{result['message']}; {reg['message']}"
    return out


def _success(
    message: str,
    selector_rule_id: str,
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    enabled = _catalog_tool_ids()
    validated: List[Dict[str, Any]] = []
    for item in candidates:
        tool_id = str(item["tool_id"])
        if tool_id not in enabled:
            return _error(
                f"catalog missing or unknown tool_id: {tool_id}",
                "error.catalog_tool_id",
            )
        if not enabled[tool_id]:
            return _error(
                f"catalog tool disabled: {tool_id}",
                "error.catalog_disabled",
            )
        validated.append(item)
    base = {
        "ok": True,
        "message": message,
        "selector_rule_id": selector_rule_id,
        "plan_only": True,
        "candidate_tools": validated,
    }
    return _apply_approved_registry(base)


def _candidate(
    tool_id: str,
    reason: str,
    *,
    requires_force: bool = False,
    human_review_required: bool = False,
) -> Dict[str, Any]:
    return {
        "tool_id": tool_id,
        "reason": reason,
        "requires_force": requires_force,
        "human_review_required": human_review_required,
    }


def _resolve_intake(case_dir: Path, intake: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if intake is not None:
        return intake
    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return None
    with intake_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _raw_exists(case_dir: Path, intake: Dict[str, Any]) -> bool:
    data_file = intake.get("data_file")
    if not data_file or not isinstance(data_file, str):
        return False
    return (case_dir / data_file).is_file()


def _has_cleaned_artifact(case_dir: Path) -> bool:
    cleaned_dir = case_dir / "cleaned"
    if not cleaned_dir.is_dir():
        return False
    return any(cleaned_dir.glob("*_cleaned.csv"))


def _normalize_gate_notes(gate_notes: Optional[List[str]]) -> List[str]:
    if not gate_notes:
        return []
    return [str(note).strip() for note in gate_notes if str(note).strip()]


def _infer_gate_notes(case_dir: Path, intake: Dict[str, Any]) -> List[str]:
    case_id = str(intake.get("case_id") or "")
    client_ref = str(intake.get("client_ref") or "")
    scale = intake.get("scale") if isinstance(intake.get("scale"), dict) else {}
    row_count = scale.get("row_count")

    dir_name = case_dir.name
    if case_id == "demo_phase" or dir_name == "demo_phase" or client_ref == "internal-demo":
        return list(_DEMO_PHASE_GATE_NOTES)

    if client_ref == "sampleco" or (isinstance(row_count, int) and row_count >= 100):
        return list(_SAMPLECO_GATE_NOTES)

    parent = case_dir.parent.name
    if parent == "sampleco" and dir_name == "2026-0001":
        return list(_SAMPLECO_GATE_NOTES)

    return []


def _phase_like_cleanable(notes: List[str]) -> bool:
    return "phase_like" in notes or "phase_demo" in notes


def _requires_force(notes: List[str], intake: Dict[str, Any]) -> bool:
    if "multi_row_export" in notes or "schema_ambiguous" in notes:
        return False
    if "phase_demo" in notes:
        return True
    case_id = str(intake.get("case_id") or "")
    if case_id == "demo_phase":
        return True
    scale = intake.get("scale") if isinstance(intake.get("scale"), dict) else {}
    row_count = scale.get("row_count")
    if "phase_like" in notes and isinstance(row_count, int) and row_count < 100:
        return True
    return False


def _human_review_required(notes: List[str]) -> bool:
    return "multi_row_export" in notes or "schema_ambiguous" in notes


def select_tabular_tools(
    case_dir: str,
    task_type: str,
    intake: Optional[Dict[str, Any]] = None,
    gate_notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Recommend tabular MVP tools for a case directory and task intent.

    Returns a stable dict with ok, message, selector_rule_id, candidate_tools[].
    """
    if task_type not in _VALID_TASK_TYPES:
        return _error(
            f"unsupported task_type: {task_type}",
            "error.invalid_task_type",
        )

    case_path = Path(case_dir)
    resolved_intake = _resolve_intake(case_path, intake)
    if resolved_intake is None:
        return _error(
            "missing intake: intake.json not provided and not found under case_dir",
            "error.missing_intake",
        )

    if not _raw_exists(case_path, resolved_intake):
        return _error(
            "missing raw data_file referenced by intake",
            "error.missing_raw",
        )

    if task_type == "gate_only":
        return _success(
            "gate-only: recommend eligibility validation",
            "gate_only.eligibility",
            [
                _candidate(
                    TOOL_VALIDATE_ELIGIBILITY,
                    "task_type=gate_only requires P2 eligibility gate",
                )
            ],
        )

    notes = _normalize_gate_notes(gate_notes)
    if not notes:
        notes = _infer_gate_notes(case_path, resolved_intake)

    if task_type in {"clean", "e2e"}:
        if not _normalize_gate_notes(gate_notes) and not notes:
            return _error(
                "missing gate schema notes for clean/e2e selection",
                "error.missing_gate_notes",
            )
        if gate_notes is not None and not _normalize_gate_notes(gate_notes):
            return _error(
                "missing gate schema notes for clean/e2e selection",
                "error.missing_gate_notes",
            )

        if not _phase_like_cleanable(notes):
            return _error(
                "no phase_like schema signal; cannot recommend cleaner",
                "error.unknown_schema",
            )

        requires_force = _requires_force(notes, resolved_intake)
        human_review = _human_review_required(notes)

        if human_review:
            rule_id = "sampleco.clean.review"
            message = "using phase_demo cleaner with human review for ambiguous schema"
            reason = "phase_like schema with multi_row_export or schema_ambiguous"
        elif requires_force:
            rule_id = "phase_demo.clean.force"
            message = "using phase_demo cleaner with force"
            reason = "phase_like schema with review_needed gate"
        else:
            rule_id = "phase_demo.clean"
            message = "using phase_demo cleaner"
            reason = "phase_like schema eligible for cleaning"

        return _success(
            message,
            rule_id,
            [
                _candidate(
                    TOOL_CLEAN_PHASE_DEMO,
                    reason,
                    requires_force=requires_force,
                    human_review_required=human_review,
                )
            ],
        )

    if task_type == "bundle":
        if not _has_cleaned_artifact(case_path):
            return _error(
                "missing cleaned artifact; run cleaning before bundle",
                "error.missing_cleaned",
            )
        return _success(
            "bundle: recommend delivery bundle export",
            "bundle.delivery",
            [
                _candidate(
                    TOOL_EXPORT_DELIVERY_BUNDLE,
                    "cleaned CSV present; ready for P4 delivery bundle",
                )
            ],
        )

    return _error(
        f"unhandled task_type: {task_type}",
        "error.unhandled_task_type",
    )
