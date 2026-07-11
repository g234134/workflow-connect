#!/usr/bin/env python3
"""Tabular intake tool path dry-run CLI v1 (W4-T3-A).

Chains W4-T1 glue plan → W3-TL Selector view → local executor plan (no subprocess,
no outbox writes). Does not modify new_cleaning_case, Local UI, or main-chain E2E.

Usage:
    python scripts/run_tabular_intake_tool_path.py \\
        --task-type tabular.cleaning.mvp --case-dir cases/demo_phase
    python scripts/run_tabular_intake_tool_path.py \\
        --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_CATALOG_PATH = _REPO_ROOT / "tools" / "tabular_tool_catalog_v1.json"

_TABULAR_TASK_TYPES = frozenset(
    {
        "tabular.cleaning.mvp",
        "tabular.cleaning.regression",
        "tabular.intake.new_case",
    }
)

_SELECTOR_INTENT_BY_TOOL: Dict[str, str] = {
    "validate.eligibility": "gate_only",
    "clean.phase_demo": "clean",
    "export.delivery_bundle": "bundle",
    "intake.new_case": "gate_only",
    "orchestrate.mainline_regression": "e2e",
    "orchestrate.e2e": "e2e",
}

_EXPECTED_ARTIFACTS: Dict[str, List[Dict[str, str]]] = {
    "validate.eligibility": [
        {"kind": "report", "path": "{case_dir}/reports/eligibility_result.json", "logical_key": "eligibility_result"},
    ],
    "clean.phase_demo": [
        {"kind": "cleaned_csv", "path": "{case_dir}/cleaned/Phase_cleaned.csv", "logical_key": "cleaned_csv"},
        {"kind": "report", "path": "{case_dir}/reports/report.json", "logical_key": "report"},
        {"kind": "report", "path": "{case_dir}/reports/cleaning_stats.json", "logical_key": "cleaning_stats"},
    ],
    "export.delivery_bundle": [
        {"kind": "report", "path": "{case_dir}/reports/report.json", "logical_key": "report"},
        {"kind": "signoff", "path": "{case_dir}/delivery_signoff.md", "logical_key": "delivery_signoff"},
    ],
    "intake.new_case": [],
    "orchestrate.mainline_regression": [],
    "orchestrate.e2e": [
        {"kind": "report", "path": "{case_dir}/reports/eligibility_result.json", "logical_key": "eligibility_result"},
        {"kind": "report", "path": "{case_dir}/reports/report.json", "logical_key": "report"},
    ],
}


def _normalize_case_dir(case_dir: str) -> tuple[Path, str]:
    path = Path(case_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    resolved = path.resolve()
    rel = resolved.relative_to(_REPO_ROOT.resolve()).as_posix()
    return resolved, rel


def _is_tabular_family(task_type: str) -> bool:
    return task_type.startswith("tabular.")


def _load_catalog() -> Dict[str, Any]:
    with _CATALOG_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise RuntimeError("tabular catalog root must be a mapping")
    return data


def _find_tool(catalog: Dict[str, Any], tool_id: str) -> Optional[Dict[str, Any]]:
    for tool in catalog.get("tools", []):
        if isinstance(tool, dict) and str(tool.get("tool_id")) == tool_id:
            return tool
    return None


def _build_cli_command(
    tool: Dict[str, Any],
    case_dir_rel: str,
    *,
    force: bool = False,
    skip_eligibility: bool = True,
    json_flag: bool = True,
) -> str:
    cli = tool.get("cli_invocation")
    if not cli or not isinstance(cli, str):
        return ""

    cmd = re.sub(r"\[[^\]]*\]", "", cli)
    cmd = re.sub(r"\s*\|\s*", " ", cmd)
    cmd = " ".join(cmd.split())
    cmd = cmd.replace("<case_dir>", case_dir_rel)

    tool_id = str(tool.get("tool_id", ""))
    suffix: List[str] = []
    if tool_id == "clean.phase_demo":
        if skip_eligibility:
            suffix.append("--skip-eligibility")
        if force:
            suffix.append("--force")
    if tool_id in {"validate.eligibility", "export.delivery_bundle"} and json_flag:
        if "--json" not in cmd:
            suffix.append("--json")
    if suffix:
        cmd = f"{cmd} {' '.join(suffix)}"

    argv = shlex.split(cmd, posix=(sys.platform != "win32"))
    if argv and argv[0] == "python":
        argv[0] = sys.executable
    return " ".join(argv)


def _expected_artifacts_for(tool_id: str, case_dir_rel: str) -> List[Dict[str, str]]:
    templates = _EXPECTED_ARTIFACTS.get(tool_id, [])
    out: List[Dict[str, str]] = []
    for item in templates:
        entry = dict(item)
        entry["path"] = entry["path"].replace("{case_dir}", case_dir_rel)
        out.append(entry)
    return out


def _glue_plan_view(glue: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "selector_task_type": glue.get("selector_task_type"),
        "planned_tools": glue.get("planned_tools") or [],
        "case_profile": glue.get("case_profile"),
        "inferred_gate_notes": glue.get("inferred_gate_notes") or [],
        "notes": glue.get("notes") or [],
    }


def _selector_flags_for_tool(
    candidate_tools: List[Dict[str, Any]],
    tool_id: str,
) -> Dict[str, bool]:
    for item in candidate_tools:
        if str(item.get("tool_id")) == tool_id:
            return {
                "requires_force": bool(item.get("requires_force")),
                "human_review_required": bool(item.get("human_review_required")),
            }
    return {"requires_force": False, "human_review_required": False}


def _build_selector_view(
    case_dir_rel: str,
    glue: Dict[str, Any],
) -> Dict[str, Any]:
    from tools.tabular_tool_selector import select_tabular_tools

    gate_notes = glue.get("inferred_gate_notes") or None
    selector_task_type = str(glue.get("selector_task_type") or "e2e")
    overall = select_tabular_tools(case_dir_rel, selector_task_type, gate_notes=gate_notes)

    per_step: List[Dict[str, Any]] = []
    notes: List[str] = []
    for tool_id in glue.get("planned_tools") or []:
        intent = _SELECTOR_INTENT_BY_TOOL.get(str(tool_id), selector_task_type)
        step = select_tabular_tools(case_dir_rel, intent, gate_notes=gate_notes)
        per_step.append(
            {
                "tool_id": tool_id,
                "selector_task_type": intent,
                "ok": step.get("ok"),
                "selector_rule_id": step.get("selector_rule_id"),
                "candidate_tools": step.get("candidate_tools") or [],
            }
        )
        if not step.get("ok"):
            notes.append(f"step selector warning for {tool_id}: {step.get('message')}")

    candidates = overall.get("candidate_tools") or []
    if overall.get("ok"):
        notes.append(f"overall selector ({selector_task_type}): {overall.get('message')}")
    else:
        notes.append(f"overall selector failed: {overall.get('message')}")

    return {
        "selector_task_type": selector_task_type,
        "ok": overall.get("ok"),
        "selector_rule_id": overall.get("selector_rule_id"),
        "candidates": candidates,
        "per_step": per_step,
        "notes": notes,
    }


def _build_executor_plan(
    glue: Dict[str, Any],
    case_dir_rel: str,
    selector_view: Dict[str, Any],
) -> List[Dict[str, Any]]:
    catalog = _load_catalog()
    plan: List[Dict[str, Any]] = []

    candidate_pool: List[Dict[str, Any]] = []
    for step in selector_view.get("per_step") or []:
        candidate_pool.extend(step.get("candidate_tools") or [])
    candidate_pool.extend(selector_view.get("candidates") or [])

    for tool_id in glue.get("planned_tools") or []:
        tool = _find_tool(catalog, str(tool_id))
        flags = _selector_flags_for_tool(candidate_pool, str(tool_id))
        force = flags["requires_force"]
        human_review = flags["human_review_required"]

        planned_command = ""
        if tool:
            planned_command = _build_cli_command(
                tool,
                case_dir_rel,
                force=force,
                skip_eligibility=True,
            )

        entry: Dict[str, Any] = {
            "tool_id": tool_id,
            "dry_run": True,
            "planned_command": planned_command,
            "expected_artifacts": _expected_artifacts_for(str(tool_id), case_dir_rel),
        }
        if force:
            entry["requires_force"] = True
        if human_review:
            entry["human_review_required"] = True
        if not tool:
            entry["message"] = f"tool_id not found in catalog: {tool_id}"
        plan.append(entry)

    return plan


def run_tabular_intake_tool_path(task_type: str, case_dir: str) -> Dict[str, Any]:
    """Build dry-run tabular intake tool path preview dict."""
    _, case_dir_rel = _normalize_case_dir(case_dir)

    base: Dict[str, Any] = {
        "ok": False,
        "task_type": task_type,
        "case_dir": case_dir_rel,
        "mode": "dry_run_preview",
    }

    if not _is_tabular_family(task_type):
        base["message"] = "unsupported_family"
        base["notes"] = [f"supported families: tabular.* ({sorted(_TABULAR_TASK_TYPES)})"]
        return base

    from routing.intake_to_tabular_glue import plan_tabular_route

    glue = plan_tabular_route(task_type, case_dir_rel)
    if not glue.get("ok"):
        base["message"] = glue.get("message", "glue_plan_failed")
        base["glue_plan"] = _glue_plan_view(glue)
        base["notes"] = glue.get("notes") or []
        return base

    selector_view = _build_selector_view(case_dir_rel, glue)
    executor_plan = _build_executor_plan(glue, case_dir_rel, selector_view)

    return {
        "ok": True,
        "message": f"dry-run preview for {task_type}",
        "task_type": task_type,
        "case_dir": case_dir_rel,
        "mode": "dry_run_preview",
        "glue_plan": _glue_plan_view(glue),
        "selector_view": selector_view,
        "executor_plan": executor_plan,
        "notes": [
            "path preview only; no subprocess, no outbox writes",
            "does not modify cases/*/reports or invoke Executor module",
        ],
    }


def _format_table(result: Dict[str, Any]) -> str:
    lines = [
        f"ok: {result.get('ok')}",
        f"task_type: {result.get('task_type')}",
        f"case_dir: {result.get('case_dir')}",
        f"message: {result.get('message', '')}",
    ]
    glue = result.get("glue_plan") or {}
    if glue:
        lines.append(f"selector_task_type: {glue.get('selector_task_type')}")
        lines.append(f"planned_tools: {', '.join(glue.get('planned_tools') or [])}")
    for step in result.get("executor_plan") or []:
        lines.append(f"  - {step.get('tool_id')}: {step.get('planned_command', '')[:80]}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Tabular intake tool path dry-run preview (W4-T3-A)",
    )
    parser.add_argument(
        "--task-type",
        required=True,
        help="W2 routing task_type (tabular.* family)",
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        help="Case directory (e.g. cases/demo_phase)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON result on stdout",
    )
    args = parser.parse_args(argv)

    result = run_tabular_intake_tool_path(args.task_type, args.case_dir)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_table(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
