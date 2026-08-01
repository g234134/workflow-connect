#!/usr/bin/env python3
"""Agent experiment lines CI suite v1 (W10-T1 / W12-T2).

Unified CI helper for Tabular Agent Standard Line and Non-Tabular Experiment
Preview. Independent from MVP mainline regression — pipeline may call this
optionally on PR / manual / nightly triggers.

Non-Tabular fixtures (W9-T5/T6 real fixtures; fallback to stub via env):
    NT-A: cases/docu-corp/2026-0001 (docu-corp, mixed_documents)
    NT-B: cases/log-analytics-co/2026-0001 (log-analytics-co, server_logs)

Environment:
    AGENT_LINES_CI_USE_STUB_FIXTURES=1  # Use stub fixtures instead of real

Usage:
    python scripts/run_agent_lines_ci_suite.py
    python scripts/run_agent_lines_ci_suite.py --scope all --format json
    python scripts/run_agent_lines_ci_suite.py --scope tabular --include-extended-fixtures
    python scripts/run_agent_lines_ci_suite.py --scope non_tabular --format text
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_TABULAR_REGRESSION_SCRIPT = _REPO_ROOT / "scripts" / "run_agent_standard_case_regression.py"
_NON_TABULAR_PREVIEW_SCRIPT = _REPO_ROOT / "scripts" / "run_non_tabular_experiment_preview.py"

Scope = Literal["tabular", "non_tabular", "all"]
Format = Literal["text", "json"]

_MATURITY_TIER_ORDER = (
    "stable",
    "controlled_experimental",
    "experimental",
    "unknown",
)
_EXPERIMENT_SCRIPT = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
_fixture_maturity_resolver: Any = None

# Real fixtures from W9-T5 (NT-A) and W9-T6 (NT-B)
_NT_REAL_FIXTURES: List[Dict[str, str]] = [
    {
        "fixture_id": "NT-A",
        "task_type": "non_tabular.document.extract",
        "case_dir": "cases/docu-corp/2026-0001",
    },
    {
        "fixture_id": "NT-B",
        "task_type": "non_tabular.log.analyze",
        "case_dir": "cases/log-analytics-co/2026-0001",
    },
]

# Stub fixtures for local dev fallback or CI isolation modes
_NT_STUB_FIXTURES: List[Dict[str, str]] = [
    {
        "fixture_id": "NT-A-stub",
        "task_type": "non_tabular.document.extract",
        "case_dir": "cases/_experiment_samples/nt_docu_stub",
    },
    {
        "fixture_id": "NT-B-stub",
        "task_type": "non_tabular.log.analyze",
        "case_dir": "cases/_experiment_samples/nt_log_stub",
    },
]


def _get_nt_fixtures() -> List[Dict[str, str]]:
    """Return NT fixtures: real by default, stub if AGENT_LINES_CI_USE_STUB_FIXTURES=1."""
    if os.getenv("AGENT_LINES_CI_USE_STUB_FIXTURES") == "1":
        return _NT_STUB_FIXTURES
    return _NT_REAL_FIXTURES


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_fixture_maturity_resolver():
    global _fixture_maturity_resolver
    if _fixture_maturity_resolver is not None:
        return _fixture_maturity_resolver
    if not _EXPERIMENT_SCRIPT.is_file():
        _fixture_maturity_resolver = False
        return _fixture_maturity_resolver
    mod = _load_module(
        _EXPERIMENT_SCRIPT,
        "run_agent_standard_case_experiment_ci",
    )
    _fixture_maturity_resolver = getattr(mod, "get_fixture_maturity", False)
    return _fixture_maturity_resolver


def resolve_tabular_case_fixture_maturity(case: Dict[str, Any]) -> str:
    """Resolve fixture maturity for a tabular CI case summary."""
    value = case.get("fixture_maturity")
    if isinstance(value, str) and value.strip():
        return value.strip()
    case_ref = case.get("case_ref")
    if case_ref:
        resolver = _load_fixture_maturity_resolver()
        if resolver:
            return str(resolver(str(case_ref)))
    return "unknown"


def enrich_tabular_cases_with_fixture_maturity(
    cases: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for case in cases:
        item = dict(case)
        item["fixture_maturity"] = resolve_tabular_case_fixture_maturity(item)
        enriched.append(item)
    return enriched


def summarize_tabular_by_fixture_maturity(
    cases: List[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """Aggregate tabular CI case pass/fail counts by fixture maturity tier."""
    by_maturity: Dict[str, Dict[str, int]] = {}
    for case in cases:
        maturity = resolve_tabular_case_fixture_maturity(case)
        bucket = by_maturity.setdefault(
            maturity,
            {"total": 0, "passed": 0, "failed": 0},
        )
        bucket["total"] += 1
        if case.get("ok"):
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    return by_maturity


def format_tabular_maturity_summary_text(
    by_maturity: Dict[str, Dict[str, int]],
) -> List[str]:
    if not by_maturity:
        return []
    order = {tier: idx for idx, tier in enumerate(_MATURITY_TIER_ORDER)}
    lines = ["  by_fixture_maturity:"]
    for tier in sorted(
        by_maturity.keys(),
        key=lambda item: (order.get(item, len(_MATURITY_TIER_ORDER)), item),
    ):
        bucket = by_maturity[tier]
        lines.append(
            f"    {tier}: passed={bucket.get('passed', 0)}/"
            f"{bucket.get('total', 0)}"
        )
    return lines


def _load_module(script_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def default_ci_outbox_root(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / "outbox" / "agent_ci"


def ci_summary_artifact_path(
    *,
    outbox_root: Path,
    timestamp: str,
) -> Path:
    return outbox_root / f"{timestamp}_ci_summary.json"


def _relative_repo_path(path: Path) -> str:
    try:
        return path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _summarize_non_tabular_preview(result: Dict[str, Any], *, fixture_id: str) -> Dict[str, Any]:
    decision = result.get("decision") or {}
    return {
        "fixture_id": fixture_id,
        "case_ref": result.get("case_ref"),
        "case_dir": result.get("case_dir"),
        "task_type": result.get("task_type"),
        "ok": result.get("ok"),
        "final_status": result.get("final_status"),
        "decision": decision.get("decision"),
        "risk_level": decision.get("risk_level"),
        "experiment_id": result.get("experiment_id"),
        "outbox_path": result.get("outbox_path"),
        "message": result.get("message"),
    }


def run_tabular_ci_scope(
    *,
    include_extended_fixtures: bool = False,
    tabular_outbox_root: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Tabular Agent Standard Line via run-all-allowed regression hook."""
    tabular_mod = _load_module(_TABULAR_REGRESSION_SCRIPT, "run_agent_standard_case_regression")
    ts = timestamp or _utc_timestamp()
    result = tabular_mod.run_agent_standard_case_regression(
        run_mode="run-all-allowed",
        auto_approve_intake=True,
        include_extended_fixtures=include_extended_fixtures,
        outbox_root=tabular_outbox_root,
        timestamp=ts,
    )
    cases = enrich_tabular_cases_with_fixture_maturity(result.get("cases") or [])
    by_fixture_maturity = summarize_tabular_by_fixture_maturity(cases)
    summary = dict(result.get("summary") or {})
    summary["by_fixture_maturity"] = by_fixture_maturity
    return {
        "line": "tabular_agent_standard",
        "ok": bool(result.get("ok")),
        "timestamp": result.get("timestamp"),
        "run_mode": result.get("run_mode"),
        "include_extended_fixtures": include_extended_fixtures,
        "task_type": result.get("task_type"),
        "summary": summary,
        "cases": cases,
        "outbox_root": result.get("outbox_root"),
        "regression_id": result.get("regression_id"),
        "message": result.get("message"),
    }


def run_non_tabular_ci_scope(
    *,
    non_tabular_outbox_root: Optional[str] = None,
    write_outbox: bool = True,
) -> Dict[str, Any]:
    """Run Non-Tabular NT-A / NT-B preview fixtures (real or stub per env)."""
    nt_mod = _load_module(_NON_TABULAR_PREVIEW_SCRIPT, "run_non_tabular_experiment_preview")
    fixtures_out: List[Dict[str, Any]] = []
    all_ok = True

    nt_fixtures = _get_nt_fixtures()
    for spec in nt_fixtures:
        preview = nt_mod.run_non_tabular_experiment_preview(
            spec["task_type"],
            spec["case_dir"],
            write_outbox=write_outbox,
            outbox_root=non_tabular_outbox_root,
        )
        summary = _summarize_non_tabular_preview(preview, fixture_id=spec["fixture_id"])
        fixtures_out.append(summary)
        if not preview.get("ok"):
            all_ok = False

    passed = sum(1 for item in fixtures_out if item.get("ok"))
    using_stub = os.getenv("AGENT_LINES_CI_USE_STUB_FIXTURES") == "1"
    return {
        "line": "non_tabular_experiment_preview",
        "ok": all_ok,
        "fixture_source": "stub" if using_stub else "real",
        "fixtures": fixtures_out,
        "summary": {
            "total": len(fixtures_out),
            "passed": passed,
            "failed": len(fixtures_out) - passed,
        },
        "outbox_root": non_tabular_outbox_root or _relative_repo_path(
            nt_mod._DEFAULT_OUTBOX_ROOT  # type: ignore[attr-defined]
        ),
        "message": "non-tabular preview CI scope complete"
        if all_ok
        else "non-tabular preview CI scope completed with failures",
    }


def write_ci_summary_artifact(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def run_agent_lines_ci_suite(
    *,
    scope: Scope = "all",
    include_extended_fixtures: bool = False,
    tabular_outbox_root: Optional[str] = None,
    non_tabular_outbox_root: Optional[str] = None,
    ci_outbox_root: Optional[str] = None,
    write_ci_summary: bool = True,
    write_non_tabular_outbox: bool = True,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Run selected agent-line CI scopes and optionally write merged summary JSON."""
    ts = timestamp or _utc_timestamp()
    suite_id = str(uuid.uuid4())
    scopes_run: List[str] = []
    tabular_result: Optional[Dict[str, Any]] = None
    non_tabular_result: Optional[Dict[str, Any]] = None
    all_ok = True

    if scope in ("tabular", "all"):
        scopes_run.append("tabular")
        tabular_result = run_tabular_ci_scope(
            include_extended_fixtures=include_extended_fixtures,
            tabular_outbox_root=tabular_outbox_root,
            timestamp=ts,
        )
        if not tabular_result.get("ok"):
            all_ok = False

    if scope in ("non_tabular", "all"):
        scopes_run.append("non_tabular")
        non_tabular_result = run_non_tabular_ci_scope(
            non_tabular_outbox_root=non_tabular_outbox_root,
            write_outbox=write_non_tabular_outbox,
        )
        if not non_tabular_result.get("ok"):
            all_ok = False

    ci_outbox = Path(ci_outbox_root) if ci_outbox_root else default_ci_outbox_root()
    summary_path = ci_summary_artifact_path(outbox_root=ci_outbox, timestamp=ts)
    rel_summary_path = _relative_repo_path(summary_path)

    payload: Dict[str, Any] = {
        "schema_version": "agent_lines_ci_suite_v1",
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "suite_id": suite_id,
        "timestamp": ts,
        "scope": scope,
        "scopes_run": scopes_run,
        "ok": all_ok,
        "include_extended_fixtures": include_extended_fixtures,
        "tabular": tabular_result,
        "non_tabular": non_tabular_result,
        "ci_summary_path": rel_summary_path,
        "message": "agent lines CI suite complete" if all_ok else "agent lines CI suite completed with failures",
    }

    if write_ci_summary:
        write_ci_summary_artifact(summary_path, payload)

    return payload


def format_ci_suite_summary_text(result: Dict[str, Any]) -> str:
    lines = [
        "Agent Lines CI Suite (W10-T1 / W12-T2)",
        f"suite_id: {result.get('suite_id')}",
        f"timestamp: {result.get('timestamp')}",
        f"scope: {result.get('scope')}",
        f"ok: {result.get('ok')}",
        f"ci_summary_path: {result.get('ci_summary_path')}",
        "",
    ]

    tabular = result.get("tabular")
    if tabular:
        sm = tabular.get("summary") or {}
        lines.append("tabular (run-all-allowed):")
        lines.append(f"  ok: {tabular.get('ok')}")
        lines.append(f"  passed: {sm.get('passed')}/{sm.get('total')}")
        for case in tabular.get("cases") or []:
            maturity = case.get("fixture_maturity") or "unknown"
            lines.append(
                f"  - {case.get('case_ref')} [{maturity}] ({case.get('mode')}): "
                f"final_status={case.get('final_status')} ok={case.get('ok')}"
            )
        lines.extend(
            format_tabular_maturity_summary_text(
                (tabular.get("summary") or {}).get("by_fixture_maturity") or {}
            )
        )
        lines.append("")

    non_tabular = result.get("non_tabular")
    if non_tabular:
        sm = non_tabular.get("summary") or {}
        lines.append("non_tabular (NT-A / NT-B preview):")
        lines.append(f"  ok: {non_tabular.get('ok')}")
        lines.append(f"  passed: {sm.get('passed')}/{sm.get('total')}")
        for fixture in non_tabular.get("fixtures") or []:
            lines.append(
                f"  - {fixture.get('fixture_id')} ({fixture.get('task_type')}): "
                f"final_status={fixture.get('final_status')} ok={fixture.get('ok')}"
            )
        lines.append("")

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Agent experiment lines CI suite (W10-T1).",
    )
    parser.add_argument(
        "--scope",
        choices=("tabular", "non_tabular", "all"),
        default="all",
        help="Which agent line(s) to run (default: all)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text summary)",
    )
    parser.add_argument(
        "--include-extended-fixtures",
        action="store_true",
        help="Tabular scope: also run additional_demo and sandbox_client fixtures",
    )
    parser.add_argument(
        "--tabular-outbox-root",
        default=None,
        help="Override tabular regression artifact root",
    )
    parser.add_argument(
        "--non-tabular-outbox-root",
        default=None,
        help="Override non-tabular preview sandbox outbox root",
    )
    parser.add_argument(
        "--ci-outbox-root",
        default=None,
        help="Override merged CI summary root (default: outbox/agent_ci)",
    )
    parser.add_argument(
        "--no-ci-summary",
        action="store_true",
        help="Skip writing outbox/agent_ci/<timestamp>_ci_summary.json",
    )
    args = parser.parse_args(argv)

    result = run_agent_lines_ci_suite(
        scope=args.scope,  # type: ignore[arg-type]
        include_extended_fixtures=args.include_extended_fixtures,
        tabular_outbox_root=args.tabular_outbox_root,
        non_tabular_outbox_root=args.non_tabular_outbox_root,
        ci_outbox_root=args.ci_outbox_root,
        write_ci_summary=not args.no_ci_summary,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_ci_suite_summary_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
