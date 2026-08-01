"""P8.6–8.8 runtime inspect v1 (Wave 2 thin wiring).

Read-only chain: catalog collision check → selector plan_only → executor dry_run.
Does not spawn subprocess, write outbox, touch DarkOps, or open UI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tools.tabular_tool_executor import execute_tabular_tool
from tools.tabular_tool_selector import select_tabular_tools
from tools.non_tabular_tool_selector_v1 import select_non_tabular_tools

SCHEMA_VERSION = "p868_runtime_inspect_v1"
TABULAR_CATALOG_REL = Path("tools") / "tabular_tool_catalog_v1.json"
NT_CATALOG_REL = Path("tools") / "non_tabular_tool_catalog_v1.json"

# WB-T2 contract §2.2 — read-only allowlist summary (not live orchestrator import).
ALLOWLIST_MATRIX: Dict[str, Dict[str, bool]] = {
    "demo_phase": {
        "dry_run": True,
        "plan_only": True,
        "execute": True,
        "sandbox_end_to_end": False,
    },
    "sampleco/2026-0001": {
        "dry_run": True,
        "plan_only": True,
        "execute": True,
        "sandbox_end_to_end": False,
    },
    "additional_demo": {
        "dry_run": True,
        "plan_only": True,
        "execute": True,
        "sandbox_end_to_end": True,
    },
    "sandbox_client": {
        "dry_run": True,
        "plan_only": True,
        "execute": True,
        "sandbox_end_to_end": False,
    },
}

NON_CLAIMS = (
    "neq_prod_browser",
    "neq_wave4_ui",
    "neq_phase_closure",
    "neq_darkops_executor",
    "neq_execute_subprocess",
    "neq_dashboard_authorize",
)


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    return Path(__file__).resolve().parents[1]


def _normalize_case_ref(case_ref: str) -> str:
    return str(case_ref or "").strip().replace("\\", "/").strip("/")


def _load_tool_ids(catalog_path: Path) -> Set[str]:
    if not catalog_path.is_file():
        return set()
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    tools = data.get("tools") if isinstance(data, dict) else None
    if not isinstance(tools, list):
        return set()
    out: Set[str] = set()
    for row in tools:
        if isinstance(row, dict):
            tid = str(row.get("tool_id") or "").strip()
            if tid:
                out.add(tid)
    return out


def _catalog_summary(repo_root: Path) -> Dict[str, Any]:
    tab_path = repo_root / TABULAR_CATALOG_REL
    nt_path = repo_root / NT_CATALOG_REL
    tab_ids = _load_tool_ids(tab_path)
    nt_ids = _load_tool_ids(nt_path)
    collision = sorted(tab_ids & nt_ids)
    return {
        "ok": bool(tab_ids) and bool(nt_ids) and not collision,
        "tabular_path": TABULAR_CATALOG_REL.as_posix(),
        "non_tabular_path": NT_CATALOG_REL.as_posix(),
        "tabular_count": len(tab_ids),
        "non_tabular_count": len(nt_ids),
        "collision_tool_ids": collision,
        "message": (
            "catalogs loaded; tool_id namespaces disjoint"
            if not collision and tab_ids and nt_ids
            else (
                "tool_id collision across Tabular/NT catalogs"
                if collision
                else "catalog missing or empty"
            )
        ),
    }


def _allowlist_for(case_ref: str) -> Dict[str, Any]:
    modes = ALLOWLIST_MATRIX.get(case_ref)
    if modes is None:
        return {
            "ok": False,
            "case_ref": case_ref,
            "allowlisted": False,
            "modes": {},
            "message": "case_ref_not_in_wb_t2_allowlist_matrix",
        }
    return {
        "ok": True,
        "case_ref": case_ref,
        "allowlisted": True,
        "modes": dict(modes),
        "message": "wb_t2_allowlist_matrix_hit",
    }


def inspect_p868_runtime(
    case_ref: str,
    *,
    task_type: str = "gate_only",
    repo_root: Optional[Path] = None,
    include_nt_selector: bool = True,
    nt_task_type: str = "non_tabular.document.extract",
    nt_case_profile: str = "docu-corp",
) -> Dict[str, Any]:
    """Inspect P8.6–8.8 runtime wiring (read-only / dry_run)."""
    root = _repo_root(repo_root)
    norm = _normalize_case_ref(case_ref)
    base: Dict[str, Any] = {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "read_only": True,
        "case_ref": norm,
        "task_type": task_type,
        "catalog": {},
        "selector": {},
        "executor": {},
        "allowlist": {},
        "nt_selector": None,
        "non_claims": list(NON_CLAIMS),
        "message": "",
    }

    if not norm:
        base["message"] = "case_ref required"
        base["catalog"] = _catalog_summary(root)
        base["allowlist"] = _allowlist_for(norm)
        return base

    catalog = _catalog_summary(root)
    base["catalog"] = catalog
    allowlist = _allowlist_for(norm)
    base["allowlist"] = allowlist

    case_dir = root / "cases" / norm
    selector = select_tabular_tools(str(case_dir), task_type)
    # Contract semantics: selector is always plan_only.
    if isinstance(selector, dict) and "plan_only" not in selector:
        selector = dict(selector)
        selector["plan_only"] = True
    base["selector"] = {
        "ok": bool(selector.get("ok")),
        "plan_only": bool(selector.get("plan_only", True)),
        "selector_rule_id": selector.get("selector_rule_id"),
        "message": selector.get("message"),
        "candidate_tools": selector.get("candidate_tools") or [],
        "candidate_count": len(selector.get("candidate_tools") or []),
    }

    if include_nt_selector:
        nt = select_non_tabular_tools(nt_task_type, nt_case_profile)
        planned = nt.get("planned_tools") or []
        base["nt_selector"] = {
            "ok": bool(nt.get("ok")),
            "plan_only": True,
            "selector_rule_id": nt.get("selector_rule_id"),
            "message": nt.get("message"),
            "planned_tools": planned,
            "planned_count": len(planned),
        }

    candidates: List[Dict[str, Any]] = list(selector.get("candidate_tools") or [])
    if not selector.get("ok") or not candidates:
        base["executor"] = {
            "ok": False,
            "execution_mode": "dry_run",
            "message": "skipped: selector has no candidates",
            "dry_run": True,
        }
        base["message"] = "selector failed or empty; executor skipped"
        base["ok"] = False
        return base

    tool_id = str(candidates[0].get("tool_id") or "").strip()
    exec_result = execute_tabular_tool(
        norm,
        tool_id,
        dry_run=True,
        extra_args={"repo_root": str(root)},
    )
    base["executor"] = {
        "ok": bool(exec_result.get("ok")),
        "execution_mode": "dry_run",
        "tool_id": exec_result.get("tool_id") or tool_id,
        "dry_run": bool(exec_result.get("dry_run", True)),
        "message": exec_result.get("message"),
        "exit_code": exec_result.get("exit_code"),
        "artifacts": exec_result.get("artifacts") or [],
    }

    ok = (
        bool(catalog.get("ok"))
        and bool(selector.get("ok"))
        and bool(base["executor"].get("ok"))
        and bool(base["selector"].get("plan_only"))
        and bool(base["executor"].get("dry_run"))
    )
    base["ok"] = ok
    base["message"] = (
        "catalog + selector plan_only + executor dry_run wired"
        if ok
        else "runtime inspect incomplete"
    )
    return base
