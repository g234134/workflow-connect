#!/usr/bin/env python3
"""Local toolchain gaps quickview CLI (WC-C1-01).

Read-only aggregation of WC-PRE-02～05 capabilities and optional WB-T4 health
dashboard embed. Developer-facing; not a PR gate or CI required check.

Usage:
    python scripts/run_toolchain_local_gaps_quickview.py --format json
    python scripts/run_toolchain_local_gaps_quickview.py --case-ref demo_phase --format text
    python scripts/run_toolchain_local_gaps_quickview.py --include-health-dashboard --write
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SCHEMA_VERSION = "toolchain_local_gaps_v1"
_GATE_CLASS = "optional"
_BLOCKS_MAINLINE = False
_DEFAULT_OUTPUT_DIR = "artifacts/toolchain"

SectionStatus = Literal["ok", "degraded", "missing", "skipped"]

SelectorProbeFn = Callable[[], Dict[str, Any]]
ExecutorProbeFn = Callable[[], Dict[str, Any]]
AuditProbeFn = Callable[[Optional[str]], Dict[str, Any]]
SmokeProbeFn = Callable[[], Dict[str, Any]]
HealthEmbedFn = Callable[[], Dict[str, Any]]


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _section_base(
    *,
    status: SectionStatus,
    ok: bool,
    message: str,
) -> Dict[str, Any]:
    return {"status": status, "ok": ok, "message": message}


def probe_selector_plan_only(
    *,
    tabular_probe: Optional[SelectorProbeFn] = None,
    non_tabular_probe: Optional[SelectorProbeFn] = None,
) -> Dict[str, Any]:
    """In-process plan-only probe for tabular and non-tabular selectors (WC-PRE-02)."""
    if tabular_probe is None:
        from tools.tabular_tool_selector import select_tabular_tools

        case_dir = _REPO_ROOT / "cases" / "demo_phase"
        tabular_probe = lambda: select_tabular_tools(  # noqa: E731
            str(case_dir),
            "gate_only",
        )

    if non_tabular_probe is None:
        from tools.non_tabular_tool_selector_v1 import select_non_tabular_tools

        non_tabular_probe = lambda: select_non_tabular_tools(  # noqa: E731
            "non_tabular.document.extract",
            "docu-corp",
        )

    tabular_result = tabular_probe()
    non_tabular_result = non_tabular_probe()

    tabular_plan = tabular_result.get("plan_only") is True
    non_tabular_plan = non_tabular_result.get("plan_only") is True

    details = {
        "tabular": {
            "plan_only": tabular_result.get("plan_only"),
            "ok": tabular_result.get("ok"),
            "selector_rule_id": tabular_result.get("selector_rule_id"),
        },
        "non_tabular": {
            "plan_only": non_tabular_result.get("plan_only"),
            "ok": non_tabular_result.get("ok"),
            "selector_rule_id": non_tabular_result.get("selector_rule_id"),
        },
    }

    if tabular_plan and non_tabular_plan:
        return {
            **_section_base(
                status="ok",
                ok=True,
                message="tabular and non-tabular selectors report plan_only=True",
            ),
            **details,
        }

    reasons: List[str] = []
    if not tabular_plan:
        if "plan_only" not in tabular_result:
            reasons.append("tabular missing plan_only key")
        else:
            reasons.append(f"tabular plan_only={tabular_result.get('plan_only')!r}")
    if not non_tabular_plan:
        if "plan_only" not in non_tabular_result:
            reasons.append("non-tabular missing plan_only key")
        else:
            reasons.append(f"non-tabular plan_only={non_tabular_result.get('plan_only')!r}")

    return {
        **_section_base(
            status="degraded",
            ok=False,
            message="; ".join(reasons) or "plan_only contract not satisfied",
        ),
        **details,
    }


def probe_executor_timeout_contract(
    *,
    executor_probe: Optional[ExecutorProbeFn] = None,
) -> Dict[str, Any]:
    """Verify executor subprocess timeout=600 and subprocess_timeout message (WC-PRE-03)."""
    if executor_probe is not None:
        return executor_probe()

    from tools import tabular_tool_executor as executor_mod
    from tools.tabular_tool_executor import execute_tabular_tool

    expected_timeout = executor_mod._SUBPROCESS_TIMEOUT_SECONDS
    if expected_timeout != 600:
        return {
            **_section_base(
                status="degraded",
                ok=False,
                message=f"expected timeout=600, found {expected_timeout}",
            ),
            "timeout_seconds": expected_timeout,
            "subprocess_timeout_message_ok": False,
        }

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        outbox_root = Path(tmp) / "outbox"
        extra = {"outbox_root_override": str(outbox_root)}

        with patch("tools.tabular_tool_executor.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["python", "scripts/fake.py"],
                timeout=600,
                stderr="timed out",
            )
            result = execute_tabular_tool(
                "demo_phase",
                "validate.eligibility",
                dry_run=False,
                extra_args=extra,
            )
            call_kwargs = mock_run.call_args.kwargs if mock_run.call_args else {}

    timeout_ok = call_kwargs.get("timeout") == 600
    message_ok = "subprocess_timeout" in str(result.get("message", ""))
    exit_code_ok = result.get("exit_code") is None
    contract_ok = timeout_ok and message_ok and exit_code_ok and not result.get("ok")

    if contract_ok:
        return {
            **_section_base(
                status="ok",
                ok=True,
                message="subprocess timeout=600 and subprocess_timeout message verified (mocked)",
            ),
            "timeout_seconds": expected_timeout,
            "subprocess_timeout_message_ok": True,
            "mocked_probe": True,
        }

    issues: List[str] = []
    if not timeout_ok:
        issues.append(f"subprocess.run timeout={call_kwargs.get('timeout')!r}, expected 600")
    if not message_ok:
        issues.append("result message missing subprocess_timeout")
    if not exit_code_ok:
        issues.append(f"expected exit_code=null, got {result.get('exit_code')!r}")
    if result.get("ok"):
        issues.append("expected ok=false on timeout")

    return {
        **_section_base(
            status="degraded",
            ok=False,
            message="; ".join(issues) or "executor timeout contract mismatch",
        ),
        "timeout_seconds": expected_timeout,
        "subprocess_timeout_message_ok": message_ok,
        "mocked_probe": True,
    }


def probe_audit_investigation(
    case_ref: Optional[str],
    *,
    audit_probe: Optional[AuditProbeFn] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Optional audit investigation gaps summary (WC-PRE-04)."""
    if not case_ref:
        return {
            **_section_base(
                status="skipped",
                ok=True,
                message="no case-ref provided; audit investigation skipped",
            ),
            "case_ref": None,
            "gaps_count": None,
            "top_gaps": [],
        }

    if audit_probe is not None:
        return audit_probe(case_ref)

    from audit.audit_investigation_projection_v1 import project_audit_investigation_view
    from scripts.run_agent_audit_quickview import run_agent_audit_quickview

    root = repo_root or _REPO_ROOT
    wire = run_agent_audit_quickview(case_ref, repo_root=root)
    investigation = project_audit_investigation_view(wire)
    gaps = investigation.get("gaps") or []
    top_gaps = [
        {
            "gap_id": g.get("gap_id"),
            "severity": g.get("severity"),
            "reason": g.get("reason"),
        }
        for g in gaps[:5]
    ]

    return {
        **_section_base(
            status="ok" if investigation.get("ok") else "degraded",
            ok=True,
            message=(
                f"audit investigation projected {len(gaps)} gap(s) for case_ref={case_ref}"
            ),
        ),
        "case_ref": case_ref,
        "gaps_count": len(gaps),
        "audit_gaps_count": investigation.get("audit_gaps_count", len(gaps)),
        "audit_sections_found": investigation.get("audit_sections_found"),
        "top_gaps": top_gaps,
        "investigation_ok": investigation.get("ok"),
    }


def probe_smoke_matrix_dry_run(
    *,
    smoke_probe: Optional[SmokeProbeFn] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Read-only smoke matrix list dry-run summary (WC-PRE-05)."""
    if smoke_probe is not None:
        return smoke_probe()

    from scripts.run_toolchain_smoke_matrix import run_toolchain_smoke_matrix

    report = run_toolchain_smoke_matrix(
        tier="all",
        dry_run=True,
        repo_root=repo_root or _REPO_ROOT,
    )

    tier_counts: Dict[str, int] = {}
    for item in report.get("results") or []:
        tier = str(item.get("tier") or "unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    dry_run = report.get("dry_run") is True
    entries_requested = report.get("entries_requested", 0)
    section_ok = dry_run and entries_requested > 0 and report.get("ok")

    return {
        **_section_base(
            status="ok" if section_ok else "degraded",
            ok=bool(section_ok),
            message=report.get("message") or "smoke matrix dry-run summary",
        ),
        "dry_run": dry_run,
        "entries_requested": entries_requested,
        "tier_counts": tier_counts,
        "matrix_schema_version": report.get("matrix_schema_version"),
        "matrix_revision": report.get("matrix_revision"),
    }


def probe_toolchain_health_embed(
    *,
    health_probe: Optional[HealthEmbedFn] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Optional WB-T4 health dashboard embed (read-only dry-run summary)."""
    if health_probe is not None:
        return health_probe()

    from scripts.run_toolchain_health_dashboard import build_toolchain_health

    payload = build_toolchain_health(repo_root=repo_root or _REPO_ROOT, dry_run=True)
    return {
        "ok": payload.get("ok"),
        "gate_class": payload.get("gate_class"),
        "blocks_mainline": payload.get("blocks_mainline"),
        "dry_run": payload.get("dry_run"),
        "schema_version": payload.get("schema_version"),
        "sections_populated": payload.get("sections_populated"),
        "sections_ok": payload.get("sections_ok"),
        "aggregated_health_score": payload.get("aggregated_health_score"),
        "message": payload.get("message"),
    }


def build_toolchain_local_gaps_report(
    *,
    case_ref: Optional[str] = None,
    dry_run: bool = True,
    include_health_dashboard: bool = False,
    repo_root: Optional[Path] = None,
    tabular_probe: Optional[SelectorProbeFn] = None,
    non_tabular_probe: Optional[SelectorProbeFn] = None,
    executor_probe: Optional[ExecutorProbeFn] = None,
    audit_probe: Optional[AuditProbeFn] = None,
    smoke_probe: Optional[SmokeProbeFn] = None,
    health_probe: Optional[HealthEmbedFn] = None,
) -> Dict[str, Any]:
    """Assemble toolchain_local_gaps_v1 report dict."""
    root = repo_root or _REPO_ROOT

    sections: Dict[str, Dict[str, Any]] = {
        "selector_plan_only": probe_selector_plan_only(
            tabular_probe=tabular_probe,
            non_tabular_probe=non_tabular_probe,
        ),
        "executor_timeout_contract": probe_executor_timeout_contract(
            executor_probe=executor_probe,
        ),
        "audit_investigation": probe_audit_investigation(
            case_ref,
            audit_probe=audit_probe,
            repo_root=root,
        ),
        "smoke_matrix_dry_run": probe_smoke_matrix_dry_run(
            smoke_probe=smoke_probe,
            repo_root=root,
        ),
    }

    report: Dict[str, Any] = {
        "ok": all(section.get("ok") for section in sections.values()),
        "schema_version": _SCHEMA_VERSION,
        "generated_at": _utc_now_iso(),
        "gate_class": _GATE_CLASS,
        "blocks_mainline": _BLOCKS_MAINLINE,
        "dry_run": dry_run,
        "case_ref": case_ref,
        "sections": sections,
        "message": (
            "local toolchain gaps quickview assembled "
            f"({sum(1 for s in sections.values() if s.get('ok'))}/{len(sections)} sections ok)"
        ),
    }

    if include_health_dashboard:
        report["toolchain_health_embed"] = probe_toolchain_health_embed(
            health_probe=health_probe,
            repo_root=root,
        )

    return report


def format_toolchain_local_gaps_text(report: Dict[str, Any]) -> str:
    """Render human-readable summary projected from JSON report."""
    lines = [
        "Toolchain Local Gaps Quickview (WC-C1-01 · read-only · optional gate)",
        f"schema_version: {report.get('schema_version')}",
        f"ok: {report.get('ok')}",
        f"gate_class: {report.get('gate_class')} · blocks_mainline: {report.get('blocks_mainline')}",
        f"dry_run: {report.get('dry_run')}",
        f"case_ref: {report.get('case_ref') or '(none)'}",
        "",
    ]

    sections = report.get("sections") or {}
    for name, section in sections.items():
        ok_flag = "ok" if section.get("ok") else "!ok"
        lines.append(f"── {name} [{ok_flag}] ──")
        lines.append(f"status: {section.get('status')}")
        lines.append(f"message: {section.get('message')}")
        if name == "selector_plan_only":
            tab = section.get("tabular") or {}
            nt = section.get("non_tabular") or {}
            lines.append(
                f"tabular plan_only={tab.get('plan_only')} · "
                f"non_tabular plan_only={nt.get('plan_only')}"
            )
        elif name == "audit_investigation" and section.get("gaps_count") is not None:
            lines.append(f"gaps_count: {section.get('gaps_count')}")
            for gap in section.get("top_gaps") or []:
                lines.append(
                    f"  - {gap.get('gap_id')}: {gap.get('reason')} ({gap.get('severity')})"
                )
        elif name == "smoke_matrix_dry_run":
            lines.append(f"entries_requested: {section.get('entries_requested')}")
            lines.append(f"dry_run: {section.get('dry_run')}")
            tier_counts = section.get("tier_counts") or {}
            if tier_counts:
                tiers = ", ".join(f"{k}={v}" for k, v in sorted(tier_counts.items()))
                lines.append(f"tier_counts: {tiers}")
        elif name == "executor_timeout_contract":
            lines.append(f"timeout_seconds: {section.get('timeout_seconds')}")
        lines.append("")

    embed = report.get("toolchain_health_embed")
    if embed:
        lines.append("── toolchain_health_embed ──")
        lines.append(f"ok: {embed.get('ok')} · gate_class: {embed.get('gate_class')}")
        lines.append(f"sections_populated: {embed.get('sections_populated')}")
        lines.append("")

    lines.append(f"message: {report.get('message')}")
    return "\n".join(lines)


def write_gaps_artifacts(
    report: Dict[str, Any],
    *,
    repo_root: Path,
    output_dir: Path,
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "toolchain_local_gaps.latest.json"
    md_path = output_dir / "toolchain_local_gaps.latest.md"

    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(format_toolchain_local_gaps_text(report) + "\n", encoding="utf-8")

    def _rel(path: Path) -> str:
        try:
            return path.relative_to(repo_root).as_posix()
        except ValueError:
            return path.as_posix()

    return {"json": _rel(json_path), "markdown": _rel(md_path)}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Local toolchain gaps quickview (WC-C1-01) — read-only optional report. "
            "Not a PR gate or CI required check."
        ),
    )
    parser.add_argument(
        "--case-ref",
        default=None,
        help="Optional case_ref for audit investigation projection",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Read-only probes only; no long subprocess (default: true)",
    )
    parser.add_argument(
        "--include-health-dashboard",
        action="store_true",
        help="Embed WB-T4 toolchain health dashboard dry-run summary",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write artifacts/toolchain/toolchain_local_gaps.latest.{json,md}",
    )
    parser.add_argument(
        "--output-dir",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Artifact output directory (default: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional repo root override",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT

    report = build_toolchain_local_gaps_report(
        case_ref=args.case_ref,
        dry_run=args.dry_run,
        include_health_dashboard=args.include_health_dashboard,
        repo_root=repo_root,
    )

    if args.write:
        out_dir = (
            Path(args.output_dir)
            if Path(args.output_dir).is_absolute()
            else repo_root / args.output_dir
        )
        report["output_paths"] = write_gaps_artifacts(
            report,
            repo_root=repo_root,
            output_dir=out_dir.resolve(),
        )

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_toolchain_local_gaps_text(report))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
