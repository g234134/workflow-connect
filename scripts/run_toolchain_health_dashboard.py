#!/usr/bin/env python3
"""Toolchain health dashboard v1 (WB-T4).

Read-only aggregation of agent CI summaries, offline metrics, monthly report
headlines, fixture maturity tiers, catalog health, and optional wf_status_summary.

Gate defaults (Phase 5 skeleton):
  - dry_run=True (default): read outbox only; no agent CI suite side effect
  - gate_class=optional, blocks_mainline=false — not a PR required check
  - Use --no-dry-run to optionally invoke run_agent_lines_ci_suite before assembly
  - Phase% is NOT emitted; see docs/wave-progress-dashboard-skeleton-v1.md

Spec: docs/toolchain-health-dashboard-v1.md

Usage:
    python scripts/run_toolchain_health_dashboard.py --format json
    python scripts/run_toolchain_health_dashboard.py --dry-run
    python scripts/run_toolchain_health_dashboard.py --include-wf-status
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SCHEMA_VERSION = "toolchain_health_v1"
_GATE_CLASS = "optional"
_BLOCKS_MAINLINE = False

_DEFAULT_CI_OUTBOX = "outbox/agent_ci"
_DEFAULT_METRICS_JSON = "outbox/agent_metrics/metrics_summary.json"
_DEFAULT_METRICS_DIR = "outbox/agent_metrics"
_DEFAULT_OUTPUT_DIR = "artifacts/toolchain"
_DEFAULT_WF_STATUS_JSON = "artifacts/wf/wf_status_summary.latest.json"

_TABULAR_CATALOG = "tools/tabular_tool_catalog_v1.json"
_NT_CATALOG = "tools/non_tabular_tool_catalog_v1.json"
_EXPECTED_CATALOG_REVISION = "2026-06-10"

_MATURITY_TIER_ORDER = (
    "stable",
    "controlled_experimental",
    "experimental",
    "unknown",
)

SectionStatus = Literal["ok", "degraded", "missing"]


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _rel_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _parse_revision_date(revision: Any) -> Optional[datetime]:
    if not isinstance(revision, str) or not revision.strip():
        return None
    text = revision.strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _find_latest_glob(root: Path, pattern: str) -> Optional[Path]:
    if not root.is_dir():
        return None
    matches = sorted(root.glob(pattern), key=lambda p: p.name, reverse=True)
    return matches[0] if matches else None


def _section_meta(
    *,
    status: SectionStatus,
    ok: bool,
    message: str,
    source_path: Optional[str] = None,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {
        "status": status,
        "ok": ok,
        "message": message,
    }
    if source_path:
        meta["source_path"] = source_path
    return meta


def load_agent_ci_section(
    repo_root: Path,
    *,
    ci_outbox: Path,
) -> Dict[str, Any]:
    latest = _find_latest_glob(ci_outbox, "*_ci_summary.json")
    if latest is None:
        return {
            **_section_meta(
                status="degraded",
                ok=False,
                message=f"no CI summary artifacts under {ci_outbox.as_posix()}",
            ),
            "suite_id": None,
            "scope": None,
            "scopes_run": [],
            "tabular_ok": None,
            "non_tabular_ok": None,
            "by_fixture_maturity": {},
            "written_at": None,
        }

    payload = _load_json(latest)
    if payload is None:
        return {
            **_section_meta(
                status="degraded",
                ok=False,
                message=f"failed to parse CI summary: {latest.as_posix()}",
                source_path=_rel_path(latest, repo_root),
            ),
            "suite_id": None,
            "scope": None,
            "scopes_run": [],
            "tabular_ok": None,
            "non_tabular_ok": None,
            "by_fixture_maturity": {},
            "written_at": None,
        }

    tabular = payload.get("tabular") or {}
    tabular_summary = tabular.get("summary") or {}
    by_maturity = tabular_summary.get("by_fixture_maturity") or {}
    suite_ok = bool(payload.get("ok"))

    return {
        **_section_meta(
            status="ok" if suite_ok else "degraded",
            ok=suite_ok,
            message=payload.get("message") or "agent CI summary loaded",
            source_path=_rel_path(latest, repo_root),
        ),
        "suite_id": payload.get("suite_id"),
        "scope": payload.get("scope"),
        "scopes_run": payload.get("scopes_run") or [],
        "tabular_ok": tabular.get("ok"),
        "non_tabular_ok": (payload.get("non_tabular") or {}).get("ok"),
        "by_fixture_maturity": by_maturity,
        "written_at": payload.get("written_at"),
        "schema_version": payload.get("schema_version"),
    }


def load_metrics_summary_section(
    repo_root: Path,
    *,
    metrics_path: Path,
) -> Dict[str, Any]:
    payload = _load_json(metrics_path)
    if payload is None:
        return {
            **_section_meta(
                status="degraded",
                ok=False,
                message=f"metrics summary not found or invalid: {metrics_path.as_posix()}",
            ),
            "schema_version": None,
            "generated_at": None,
            "aggregate": {},
            "by_source": {},
            "by_fixture_maturity": {},
            "runs_parsed": 0,
        }

    aggregate = payload.get("aggregate") or {}
    runs = payload.get("runs") or []
    runs_count = len(runs) if isinstance(runs, list) else 0
    has_runs = runs_count > 0

    return {
        **_section_meta(
            status="ok" if has_runs else "degraded",
            ok=has_runs,
            message=payload.get("message") or f"metrics summary loaded ({runs_count} runs)",
            source_path=_rel_path(metrics_path, repo_root),
        ),
        "schema_version": payload.get("schema_version"),
        "generated_at": payload.get("generated_at"),
        "aggregate": {
            "total_runs": aggregate.get("total_runs", 0),
            "successful_runs": aggregate.get("successful_runs", 0),
            "failed_runs": aggregate.get("failed_runs", 0),
            "error_rate": aggregate.get("error_rate", 0.0),
            "checkpoint_a_trigger_rate": aggregate.get("checkpoint_a_trigger_rate", 0.0),
            "checkpoint_b_trigger_rate": aggregate.get("checkpoint_b_trigger_rate", 0.0),
        },
        "by_source": payload.get("by_source") or {},
        "by_fixture_maturity": payload.get("by_fixture_maturity") or {},
        "runs_parsed": runs_count,
    }


def _extract_monthly_report_head(text: str, *, max_lines: int = 12) -> List[str]:
    lines: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(">"):
            lines.append(line.lstrip("> ").strip())
        elif line.startswith("|") and "---" not in line:
            lines.append(line)
        elif line.startswith("- "):
            lines.append(line)
        if len(lines) >= max_lines:
            break
    return lines


def load_monthly_report_head_section(
    repo_root: Path,
    *,
    metrics_dir: Path,
    metrics_section: Dict[str, Any],
) -> Dict[str, Any]:
    latest_report = _find_latest_glob(metrics_dir, "monthly_report_*.md")
    if latest_report is not None:
        try:
            text = latest_report.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if text.strip():
            month_match = re.search(r"Monthly Report — (\d{4}-\d{2})", text)
            return {
                **_section_meta(
                    status="ok",
                    ok=True,
                    message="monthly report headline extracted",
                    source_path=_rel_path(latest_report, repo_root),
                ),
                "month": month_match.group(1) if month_match else None,
                "headlines": _extract_monthly_report_head(text),
                "report_path": _rel_path(latest_report, repo_root),
            }

    aggregate = metrics_section.get("aggregate") or {}
    if metrics_section.get("status") == "ok" and aggregate.get("total_runs", 0) > 0:
        return {
            **_section_meta(
                status="ok",
                ok=True,
                message="synthetic monthly head from metrics_summary aggregate",
            ),
            "month": None,
            "headlines": [
                f"total_runs={aggregate.get('total_runs', 0)}",
                f"error_rate={aggregate.get('error_rate', 0.0)}",
                f"cp_a_rate={aggregate.get('checkpoint_a_trigger_rate', 0.0)}",
                f"cp_b_rate={aggregate.get('checkpoint_b_trigger_rate', 0.0)}",
            ],
            "report_path": None,
        }

    return {
        **_section_meta(
            status="degraded",
            ok=False,
            message="no monthly report file and metrics aggregate empty",
        ),
        "month": None,
        "headlines": [],
        "report_path": None,
    }


def merge_fixture_maturity_tiers(
    *,
    metrics_section: Dict[str, Any],
    agent_ci_section: Dict[str, Any],
) -> Dict[str, Any]:
    merged: Dict[str, Dict[str, Any]] = {}

    def _ensure(tier: str) -> Dict[str, Any]:
        return merged.setdefault(
            tier,
            {
                "tier": tier,
                "metrics_total_runs": 0,
                "metrics_error_rate": 0.0,
                "ci_passed": 0,
                "ci_total": 0,
            },
        )

    for tier, bucket in (metrics_section.get("by_fixture_maturity") or {}).items():
        entry = _ensure(str(tier))
        entry["metrics_total_runs"] = bucket.get("total_runs", 0)
        entry["metrics_error_rate"] = bucket.get("error_rate", 0.0)

    for tier, bucket in (agent_ci_section.get("by_fixture_maturity") or {}).items():
        entry = _ensure(str(tier))
        entry["ci_passed"] = bucket.get("passed", 0)
        entry["ci_total"] = bucket.get("total", 0)

    ordered = [
        merged[tier]
        for tier in _MATURITY_TIER_ORDER
        if tier in merged
    ]
    for tier in sorted(merged.keys()):
        if tier not in _MATURITY_TIER_ORDER:
            ordered.append(merged[tier])

    populated = len(ordered)
    status: SectionStatus = "ok" if populated else "degraded"
    return {
        **_section_meta(
            status=status,
            ok=populated > 0,
            message=f"{populated} fixture maturity tier(s) aggregated",
        ),
        "tiers": ordered,
        "tier_count": populated,
    }


def load_catalog_health_section(repo_root: Path) -> Dict[str, Any]:
    tabular_path = repo_root / _TABULAR_CATALOG
    nt_path = repo_root / _NT_CATALOG

    tabular = _load_json(tabular_path)
    nt = _load_json(nt_path)

    if tabular is None or nt is None:
        missing = []
        if tabular is None:
            missing.append(_TABULAR_CATALOG)
        if nt is None:
            missing.append(_NT_CATALOG)
        return {
            **_section_meta(
                status="degraded",
                ok=False,
                message=f"catalog JSON missing: {', '.join(missing)}",
            ),
            "tabular_tool_count": 0,
            "non_tabular_tool_count": 0,
            "total_tool_count": 0,
            "tabular_catalog_revision": None,
            "non_tabular_catalog_revision": None,
            "stale_revision": True,
            "revision_aligned": False,
        }

    tabular_tools = tabular.get("tools") or []
    nt_tools = nt.get("tools") or []
    tabular_count = len(tabular_tools) if isinstance(tabular_tools, list) else 0
    nt_count = len(nt_tools) if isinstance(nt_tools, list) else 0

    tab_rev = tabular.get("catalog_revision")
    nt_rev = nt.get("catalog_revision")
    revision_aligned = tab_rev == nt_rev == _EXPECTED_CATALOG_REVISION

    stale_flags: List[bool] = []
    for rev in (tab_rev, nt_rev):
        parsed = _parse_revision_date(rev)
        if parsed is None:
            stale_flags.append(True)
        else:
            age_days = (datetime.now(timezone.utc) - parsed).days
            stale_flags.append(age_days > 365)
    stale_revision = any(stale_flags) or not revision_aligned

    return {
        **_section_meta(
            status="ok" if not stale_revision else "degraded",
            ok=not stale_revision,
            message=(
                "catalog revisions current"
                if not stale_revision
                else "catalog revision stale or misaligned"
            ),
        ),
        "tabular_tool_count": tabular_count,
        "non_tabular_tool_count": nt_count,
        "total_tool_count": tabular_count + nt_count,
        "tabular_catalog_revision": tab_rev,
        "non_tabular_catalog_revision": nt_rev,
        "expected_catalog_revision": _EXPECTED_CATALOG_REVISION,
        "stale_revision": stale_revision,
        "revision_aligned": revision_aligned,
        "tabular_catalog_path": _TABULAR_CATALOG,
        "non_tabular_catalog_path": _NT_CATALOG,
    }


def load_wf_status_summary_section(
    repo_root: Path,
    *,
    wf_status_path: Path,
    include_wf_status: bool,
) -> Dict[str, Any]:
    if not include_wf_status:
        return {
            **_section_meta(
                status="missing",
                ok=False,
                message="wf_status_summary not requested (--include-wf-status to enable)",
            ),
            "gate_sample_count": None,
            "needs_review_ratio": None,
            "index_cases_count": None,
            "trace_hit_rate": None,
        }

    if not wf_status_path.is_file():
        return {
            **_section_meta(
                status="degraded",
                ok=False,
                message=f"wf_status_summary artifact missing: {wf_status_path.as_posix()}",
            ),
            "gate_sample_count": None,
            "needs_review_ratio": None,
            "index_cases_count": None,
            "trace_hit_rate": None,
        }

    payload = _load_json(wf_status_path)
    if payload is None:
        return {
            **_section_meta(
                status="degraded",
                ok=False,
                message=f"wf_status_summary invalid: {wf_status_path.as_posix()}",
            ),
            "gate_sample_count": None,
            "needs_review_ratio": None,
            "index_cases_count": None,
            "trace_hit_rate": None,
        }

    gate = payload.get("gate") or {}
    trace_stats = payload.get("trace_join_stats") or {}
    index_cases = payload.get("index_cases") or []

    return {
        **_section_meta(
            status="ok" if payload.get("ok") else "degraded",
            ok=bool(payload.get("ok")),
            message=payload.get("message") or "wf_status_summary loaded (read-only)",
            source_path=_rel_path(wf_status_path, repo_root),
        ),
        "gate_sample_count": gate.get("sample_count"),
        "needs_review_ratio": gate.get("needs_review_ratio"),
        "index_cases_count": len(index_cases) if isinstance(index_cases, list) else 0,
        "trace_hit_rate": trace_stats.get("hit_rate"),
        "generated_at": payload.get("generated_at"),
    }


def compute_aggregated_health_score(sections: Dict[str, Dict[str, Any]]) -> int:
    """Heuristic 0–100 score; not an SLA."""
    weights = {
        "agent_ci": 20,
        "metrics_summary": 25,
        "monthly_report_head": 10,
        "fixture_maturity_tiers": 15,
        "catalog_health": 20,
        "wf_status_summary": 10,
    }
    score = 0.0
    for name, weight in weights.items():
        section = sections.get(name) or {}
        status = section.get("status")
        if status == "ok":
            score += weight
        elif status == "degraded":
            score += weight * 0.4
        elif status == "missing" and name == "wf_status_summary":
            score += weight * 0.5
    return max(0, min(100, int(round(score))))


_CORE_SECTIONS = (
    "agent_ci",
    "metrics_summary",
    "monthly_report_head",
    "fixture_maturity_tiers",
    "catalog_health",
)


def count_sections_populated(sections: Dict[str, Dict[str, Any]]) -> int:
    count = 0
    for name in _CORE_SECTIONS:
        status = (sections.get(name) or {}).get("status")
        if status in {"ok", "degraded"}:
            count += 1
    return count


def count_sections_ok(sections: Dict[str, Dict[str, Any]]) -> int:
    return sum(
        1
        for name in _CORE_SECTIONS
        if (sections.get(name) or {}).get("status") == "ok"
    )


def build_toolchain_health(
    *,
    repo_root: Path,
    dry_run: bool = True,
    include_wf_status: bool = False,
    ci_outbox: Optional[Path] = None,
    metrics_path: Optional[Path] = None,
    metrics_dir: Optional[Path] = None,
    wf_status_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Assemble toolchain_health_v1 dashboard dict (read-only by default)."""
    root = repo_root.resolve()
    ci_root = (ci_outbox or (root / _DEFAULT_CI_OUTBOX)).resolve()
    metrics_json = (metrics_path or (root / _DEFAULT_METRICS_JSON)).resolve()
    metrics_root = (metrics_dir or (root / _DEFAULT_METRICS_DIR)).resolve()
    wf_path = (wf_status_path or (root / _DEFAULT_WF_STATUS_JSON)).resolve()

    agent_ci = load_agent_ci_section(root, ci_outbox=ci_root)
    metrics_summary = load_metrics_summary_section(root, metrics_path=metrics_json)
    monthly_report_head = load_monthly_report_head_section(
        root,
        metrics_dir=metrics_root,
        metrics_section=metrics_summary,
    )
    fixture_maturity_tiers = merge_fixture_maturity_tiers(
        metrics_section=metrics_summary,
        agent_ci_section=agent_ci,
    )
    catalog_health = load_catalog_health_section(root)
    wf_status_summary = load_wf_status_summary_section(
        root,
        wf_status_path=wf_path,
        include_wf_status=include_wf_status,
    )

    sections = {
        "agent_ci": agent_ci,
        "metrics_summary": metrics_summary,
        "monthly_report_head": monthly_report_head,
        "fixture_maturity_tiers": fixture_maturity_tiers,
        "catalog_health": catalog_health,
        "wf_status_summary": wf_status_summary,
    }

    sections_populated = count_sections_populated(sections)
    sections_ok = count_sections_ok(sections)
    aggregated_health_score = compute_aggregated_health_score(sections)

    overall_ok = sections_ok >= 3

    return {
        "ok": overall_ok,
        "schema_version": _SCHEMA_VERSION,
        "generated_at": _utc_now_iso(),
        "dry_run": dry_run,
        "gate_class": _GATE_CLASS,
        "blocks_mainline": _BLOCKS_MAINLINE,
        "aggregated_health_score": aggregated_health_score,
        "sections_populated": sections_populated,
        "sections_ok": sections_ok,
        "sections": sections,
        "message": (
            f"toolchain health dashboard assembled "
            f"({sections_populated}/5 core sections populated; "
            f"score={aggregated_health_score})"
        ),
        "output_paths": {},
    }


def format_toolchain_health_markdown(payload: Dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    lines = [
        "# Toolchain Health Dashboard",
        "",
        f"> Schema: `{payload.get('schema_version')}` · "
        f"Generated: `{payload.get('generated_at')}` · "
        f"Score: **{payload.get('aggregated_health_score')}**/100 (heuristic, not SLA)",
        "",
        f"- **Overall ok**: `{payload.get('ok')}`",
        f"- **Gate class**: `{payload.get('gate_class')}` · "
        f"**blocks_mainline**: `{payload.get('blocks_mainline')}`",
        f"- **Sections populated**: {payload.get('sections_populated')}/5",
        f"- **Mode**: `{'dry-run (read-only)' if payload.get('dry_run') else 'live'}`",
        "",
        "## agent_ci",
        "",
    ]
    agent_ci = sections.get("agent_ci") or {}
    lines.extend(
        [
            f"- status: `{agent_ci.get('status')}` · ok: `{agent_ci.get('ok')}`",
            f"- scope: `{agent_ci.get('scope')}` · tabular_ok: `{agent_ci.get('tabular_ok')}`",
            f"- source: `{agent_ci.get('source_path', 'n/a')}`",
            "",
            "## metrics_summary",
            "",
        ]
    )
    metrics = sections.get("metrics_summary") or {}
    agg = metrics.get("aggregate") or {}
    lines.extend(
        [
            f"- status: `{metrics.get('status')}` · runs: `{metrics.get('runs_parsed', 0)}`",
            f"- error_rate: `{agg.get('error_rate', 0.0)}` · "
            f"cp_a: `{agg.get('checkpoint_a_trigger_rate', 0.0)}`",
            "",
            "## monthly_report_head",
            "",
        ]
    )
    monthly = sections.get("monthly_report_head") or {}
    for headline in monthly.get("headlines") or []:
        lines.append(f"- {headline}")
    lines.extend(["", "## fixture_maturity_tiers", ""])
    tiers = (sections.get("fixture_maturity_tiers") or {}).get("tiers") or []
    if tiers:
        lines.append("| tier | metrics_runs | ci_passed/ci_total |")
        lines.append("|------|--------------|-------------------|")
        for row in tiers:
            lines.append(
                f"| {row.get('tier')} | {row.get('metrics_total_runs', 0)} | "
                f"{row.get('ci_passed', 0)}/{row.get('ci_total', 0)} |"
            )
    else:
        lines.append("- *(no tiers aggregated)*")
    lines.extend(["", "## catalog_health", ""])
    catalog = sections.get("catalog_health") or {}
    lines.extend(
        [
            f"- tabular tools: `{catalog.get('tabular_tool_count', 0)}` · "
            f"non-tabular: `{catalog.get('non_tabular_tool_count', 0)}`",
            f"- revisions: tabular=`{catalog.get('tabular_catalog_revision')}` · "
            f"nt=`{catalog.get('non_tabular_catalog_revision')}`",
            f"- stale_revision: `{catalog.get('stale_revision')}`",
            "",
            "## wf_status_summary (optional)",
            "",
        ]
    )
    wf = sections.get("wf_status_summary") or {}
    lines.append(
        f"- status: `{wf.get('status')}` · samples: `{wf.get('gate_sample_count')}` · "
        f"needs_review_ratio: `{wf.get('needs_review_ratio')}`"
    )
    lines.append("")
    return "\n".join(lines)


def write_toolchain_health_artifacts(
    payload: Dict[str, Any],
    *,
    repo_root: Path,
    output_dir: Path,
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "toolchain_health.latest.json"
    md_path = output_dir / "toolchain_health.latest.md"

    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(format_toolchain_health_markdown(payload), encoding="utf-8")

    return {
        "json": _rel_path(json_path, repo_root),
        "markdown": _rel_path(md_path, repo_root),
    }


def maybe_run_agent_ci_suite(*, dry_run: bool) -> None:
    """Optional hook: only when dry_run is False."""
    if dry_run:
        return
    ci_script = _REPO_ROOT / "scripts" / "run_agent_lines_ci_suite.py"
    if not ci_script.is_file():
        return
    mod_spec = __import__("importlib.util", fromlist=["spec_from_file_location"])
    spec = mod_spec.spec_from_file_location("run_agent_lines_ci_suite", ci_script)
    if spec is None or spec.loader is None:
        return
    mod = mod_spec.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run_agent_lines_ci_suite(scope="all", write_ci_summary=True)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Toolchain health dashboard (WB-T4) — read-only aggregation.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(_REPO_ROOT),
        help="Repository root",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Read existing outbox only; do not trigger agent CI suite (default: true)",
    )
    parser.add_argument(
        "--include-wf-status",
        action="store_true",
        help="Include read-only wf_status_summary section when artifact exists",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing artifacts/toolchain/toolchain_health.latest.*",
    )
    parser.add_argument(
        "--output-dir",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Artifact output directory (default: {_DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not args.dry_run:
        maybe_run_agent_ci_suite(dry_run=False)

    payload = build_toolchain_health(
        repo_root=repo_root,
        dry_run=args.dry_run,
        include_wf_status=args.include_wf_status,
    )

    if not args.no_write:
        out_dir = (
            Path(args.output_dir)
            if Path(args.output_dir).is_absolute()
            else repo_root / args.output_dir
        )
        payload["output_paths"] = write_toolchain_health_artifacts(
            payload,
            repo_root=repo_root,
            output_dir=out_dir.resolve(),
        )

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_toolchain_health_markdown(payload))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
