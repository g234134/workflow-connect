#!/usr/bin/env python3
"""Routing eval runner v1 (W4-T2).

Reads routing/routing_eval_cases_v1.yaml and cross-checks each case against
the intake routing catalog, Tabular glue plan, and Gov routing policy (read-only).
Does not execute routing engines, LLM judges, or Langfuse queries.

Usage:
    python scripts/run_routing_eval.py
    python scripts/run_routing_eval.py --dry-run --format json
    python scripts/run_routing_eval.py --case-id tabular_demo_phase_clean
    python scripts/run_routing_eval.py --execute --case-id tabular_mainline_regression
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_EVAL_CASES_PATH = _REPO_ROOT / "routing" / "routing_eval_cases_v1.yaml"
_ROUTING_CATALOG_PATH = _REPO_ROOT / "routing" / "intake_routing_catalog_v1.yaml"
_TABULAR_CATALOG_PATH = _REPO_ROOT / "tools" / "tabular_tool_catalog_v1.json"

_TABULAR_FAMILIES = frozenset({"tabular_mvp"})
_GOV_FAMILIES = frozenset({"gov_registry"})
_EXECUTABLE_CASE_IDS = frozenset({"tabular_mainline_regression"})
_DEFAULT_CASE_DIRS: Dict[str, str] = {
    "tabular_mainline_regression": "cases/demo_phase",
}


def _load_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load routing eval inputs") from exc
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} root must be a mapping")
    return data


def load_eval_cases(cases_path: Path | None = None) -> Dict[str, Any]:
    path = cases_path or _EVAL_CASES_PATH
    return _load_yaml(path)


def load_routing_catalog(catalog_path: Path | None = None) -> Dict[str, Any]:
    path = catalog_path or _ROUTING_CATALOG_PATH
    return _load_yaml(path)


def _routes_by_task_type(catalog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    routes: Dict[str, Dict[str, Any]] = {}
    for route in catalog.get("routes") or []:
        if isinstance(route, dict) and route.get("task_type"):
            routes[str(route["task_type"])] = route
    return routes


def _tabular_catalog_tool_ids() -> Dict[str, bool]:
    with _TABULAR_CATALOG_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return {
        str(tool["tool_id"]): bool(tool.get("enabled", False))
        for tool in (data.get("tools") or [])
        if isinstance(tool, dict) and tool.get("tool_id")
    }


def _case_dir_for(case: Dict[str, Any]) -> Optional[str]:
    ctx = case.get("input_context") or {}
    case_dir = ctx.get("case_dir")
    if case_dir:
        return str(case_dir)
    return _DEFAULT_CASE_DIRS.get(str(case.get("id", "")))


def _mismatched_expected(planned: Sequence[str], expected: Sequence[str]) -> List[str]:
    planned_set = set(planned)
    return [tid for tid in expected if tid not in planned_set]


def _resolve_gov_planned_tools(
    route: Dict[str, Any],
    case: Dict[str, Any],
    *,
    repo_root: Path,
) -> Dict[str, Any]:
    from core.routing_policy_loader import load_routing_policy, resolve_route_tool_ids

    ctx = case.get("input_context") or {}
    route_id = str(
        ctx.get("policy_route_id") or route.get("policy_route_id") or ""
    ).strip()
    if not route_id:
        return {
            "ok": False,
            "message": "gov case missing policy_route_id",
            "planned_tools": [],
        }

    policy = load_routing_policy(repo_root=repo_root)
    resolved = resolve_route_tool_ids(policy, route_id)
    return {
        "ok": bool(resolved.get("ok")),
        "message": str(resolved.get("message", "")),
        "planned_tools": list(resolved.get("tool_ids") or []),
        "policy_route_id": route_id,
    }


def _run_mainline_regression_subprocess(*, repo_root: Path) -> Dict[str, Any]:
    script = repo_root / "scripts" / "run_mvp_mainline_regression.py"
    proc = subprocess.run(
        [sys.executable, str(script), "-v"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "command": f"{sys.executable} {script.relative_to(repo_root)} -v",
    }


def evaluate_case(
    case: Dict[str, Any],
    *,
    catalog: Dict[str, Any],
    dry_run: bool = True,
    execute: bool = False,
    repo_root: Path | None = None,
) -> Dict[str, Any]:
    """Evaluate one routing eval case; returns a stable per-case result dict."""
    root = repo_root or _REPO_ROOT
    case_id = str(case.get("id", ""))
    task_type = str(case.get("task_type", ""))
    expected_tool_ids = [str(t) for t in (case.get("expected_tool_ids") or [])]
    expected_families = [str(f) for f in (case.get("expected_families") or [])]
    expected_entrypoint = str(case.get("expected_entrypoint") or "")

    result: Dict[str, Any] = {
        "id": case_id,
        "ok": False,
        "task_type": task_type,
        "family": expected_families[0] if expected_families else "",
        "expected_tool_ids": expected_tool_ids,
        "planned_tools": [],
        "mismatched_tools": [],
        "notes": [],
        "dry_run": dry_run,
    }

    routes = _routes_by_task_type(catalog)
    route = routes.get(task_type)
    if route is None:
        result["message"] = f"task_type {task_type!r} not found in intake routing catalog"
        return result

    catalog_family = str(route.get("preferred_tool_family", ""))
    if catalog_family and catalog_family not in expected_families:
        result["notes"].append(
            f"warning: catalog family {catalog_family!r} not in expected_families"
        )

    catalog_entrypoint = str(route.get("entrypoint") or "")
    result["catalog_entrypoint"] = catalog_entrypoint
    result["expected_entrypoint"] = expected_entrypoint
    policy_based_route = bool(route.get("policy_route_id") or route.get("policy_ssot"))
    if policy_based_route and not catalog_entrypoint:
        result["entrypoint_match"] = True
        if expected_entrypoint:
            result["notes"].append(
                f"policy-based route; case expected_entrypoint={expected_entrypoint!r} "
                "(not in intake catalog entrypoint field)"
            )
    else:
        result["entrypoint_match"] = (
            not expected_entrypoint or catalog_entrypoint == expected_entrypoint
        )
        if expected_entrypoint and not result["entrypoint_match"]:
            result["notes"].append(
                f"entrypoint mismatch: catalog={catalog_entrypoint!r} "
                f"expected={expected_entrypoint!r}"
            )

    family = catalog_family or (expected_families[0] if expected_families else "")
    result["family"] = family

    if family in _TABULAR_FAMILIES:
        from routing.intake_to_tabular_glue import plan_tabular_route

        case_dir = _case_dir_for(case)
        if not case_dir:
            result["message"] = "tabular case missing case_dir in input_context"
            return result

        plan = plan_tabular_route(task_type, case_dir)
        if not plan.get("ok"):
            result["message"] = str(plan.get("message", "plan_tabular_route failed"))
            result["planned_tools"] = list(plan.get("planned_tools") or [])
            result["notes"].extend(plan.get("notes") or [])
            return result

        planned_tools = [str(t) for t in plan.get("planned_tools") or []]
        result["planned_tools"] = planned_tools
        result["case_dir"] = plan.get("case_dir")
        result["notes"].extend(plan.get("notes") or [])

        enabled_tools = _tabular_catalog_tool_ids()
        unknown = [t for t in planned_tools if t not in enabled_tools]
        disabled = [t for t in planned_tools if enabled_tools.get(t) is False]
        if unknown:
            result["notes"].append(f"planned_tools not in tabular catalog: {unknown}")
        if disabled:
            result["notes"].append(f"planned_tools disabled in tabular catalog: {disabled}")

        mismatched = _mismatched_expected(planned_tools, expected_tool_ids)
        result["mismatched_tools"] = mismatched

        acceptable_orch = set(case.get("acceptable_orchestration_tool_ids") or [])
        if mismatched and acceptable_orch:
            orch_id = plan.get("orchestration_tool_id")
            if orch_id and str(orch_id) in acceptable_orch:
                result["notes"].append(
                    f"acceptable orchestration alternative: {orch_id} (stepwise tools not required)"
                )
                mismatched = _mismatched_expected([str(orch_id)], expected_tool_ids)
                if not mismatched:
                    result["mismatched_tools"] = []

        result["ok"] = (
            not mismatched
            and not unknown
            and not disabled
            and result["entrypoint_match"]
        )
        if mismatched:
            result["message"] = f"planned_tools missing expected: {mismatched}"
        elif result["ok"]:
            result["message"] = f"tabular plan aligned for {case_id}"

    elif family in _GOV_FAMILIES:
        gov = _resolve_gov_planned_tools(route, case, repo_root=root)
        planned_tools = list(gov.get("planned_tools") or [])
        result["planned_tools"] = planned_tools
        result["policy_route_id"] = gov.get("policy_route_id")
        if not gov.get("ok"):
            result["message"] = str(gov.get("message", "gov policy resolve failed"))
            return result

        mismatched = _mismatched_expected(planned_tools, expected_tool_ids)
        result["mismatched_tools"] = mismatched
        optional = set(case.get("optional_tool_ids") or [])
        if mismatched:
            only_optional = all(t in optional for t in mismatched)
            if only_optional:
                result["notes"].append("mismatched ids are optional_tool_ids only")
                mismatched = []

        result["ok"] = not mismatched and result["entrypoint_match"]
        if mismatched:
            result["message"] = f"policy steps missing expected: {mismatched}"
        elif result["ok"]:
            result["message"] = f"gov policy aligned for {case_id}"
        result["notes"].append("gov check: read-only policy resolve; no tools executed")

    else:
        route_tool_ids = [str(t) for t in (route.get("tool_ids") or [])]
        result["planned_tools"] = route_tool_ids
        mismatched = _mismatched_expected(route_tool_ids, expected_tool_ids)
        result["mismatched_tools"] = mismatched
        result["ok"] = not mismatched and result["entrypoint_match"]
        result["message"] = (
            f"catalog tool_ids aligned for {case_id}"
            if result["ok"]
            else f"catalog tool_ids missing expected: {mismatched}"
        )
        result["notes"].append(f"family {family!r}: catalog-level check only")

    if execute and not dry_run and case_id in _EXECUTABLE_CASE_IDS:
        smoke = _run_mainline_regression_subprocess(repo_root=root)
        result["execute"] = smoke
        result["notes"].append(
            f"execute smoke exit_code={smoke.get('exit_code')} ok={smoke.get('ok')}"
        )
        if not smoke.get("ok"):
            result["ok"] = False
            result["message"] = "execute smoke failed (mainline regression)"
    elif execute and not dry_run and case_id not in _EXECUTABLE_CASE_IDS:
        result["notes"].append("execute skipped: case not in executable allowlist")

    return result


def run_eval(
    *,
    case_id: str | None = None,
    dry_run: bool = True,
    execute: bool = False,
    cases_path: Path | None = None,
    catalog_path: Path | None = None,
    repo_root: Path | None = None,
) -> Dict[str, Any]:
    """Run routing eval for all cases or one case by id."""
    root = repo_root or _REPO_ROOT
    cases_doc = load_eval_cases(cases_path)
    catalog = load_routing_catalog(catalog_path)
    all_cases = cases_doc.get("cases") or []

    if case_id:
        selected = [c for c in all_cases if isinstance(c, dict) and c.get("id") == case_id]
        if not selected:
            return {
                "ok": False,
                "message": f"case id not found: {case_id}",
                "dry_run": dry_run,
                "execute": execute,
                "cases_run": 0,
                "cases_ok": 0,
                "results": [],
            }
    else:
        selected = [c for c in all_cases if isinstance(c, dict)]

    results: List[Dict[str, Any]] = []
    for case in selected:
        results.append(
            evaluate_case(
                case,
                catalog=catalog,
                dry_run=dry_run,
                execute=execute and not dry_run,
                repo_root=root,
            )
        )

    cases_ok = sum(1 for r in results if r.get("ok"))
    return {
        "ok": cases_ok == len(results) and len(results) > 0,
        "message": f"{cases_ok}/{len(results)} case(s) aligned",
        "schema_version": cases_doc.get("schema_version"),
        "catalog_ref": cases_doc.get("catalog_ref"),
        "dry_run": dry_run,
        "execute": execute and not dry_run,
        "cases_run": len(results),
        "cases_ok": cases_ok,
        "results": results,
    }


def _format_table(report: Dict[str, Any]) -> str:
    lines = [
        "routing eval report",
        f"  dry_run={report.get('dry_run')} execute={report.get('execute')} "
        f"cases_ok={report.get('cases_ok')}/{report.get('cases_run')}",
        "",
        f"{'id':<32} {'ok':<6} {'family':<16} {'mismatch':<8} message",
        "-" * 96,
    ]
    for item in report.get("results") or []:
        mismatch_count = len(item.get("mismatched_tools") or [])
        msg = str(item.get("message", ""))[:40]
        lines.append(
            f"{str(item.get('id', '')):<32} "
            f"{str(item.get('ok', False)):<6} "
            f"{str(item.get('family', '')):<16} "
            f"{mismatch_count:<8} {msg}"
        )
    return "\n".join(lines)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Routing eval runner v1 — plan/catalog/policy cross-check (W4-T2)"
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Plan/compare only; no subprocess execution (default: true)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run allowed smoke subprocesses (implies not dry-run for those cases)",
    )
    parser.add_argument("--case-id", default=None, help="Evaluate a single case id")
    parser.add_argument(
        "--format",
        choices=("json", "table"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--cases-path",
        type=Path,
        default=None,
        help="Override routing eval cases YAML path",
    )
    parser.add_argument(
        "--catalog-path",
        type=Path,
        default=None,
        help="Override intake routing catalog YAML path",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    dry_run = args.dry_run and not args.execute

    try:
        report = run_eval(
            case_id=args.case_id,
            dry_run=dry_run,
            execute=args.execute,
            cases_path=args.cases_path,
            catalog_path=args.catalog_path,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        err = {"ok": False, "message": str(exc), "results": []}
        if args.format == "json":
            print(json.dumps(err, ensure_ascii=False, indent=2))
        else:
            print(f"ok=False message={exc}")
        return 1

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_format_table(report))

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
