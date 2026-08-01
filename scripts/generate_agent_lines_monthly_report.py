#!/usr/bin/env python3
"""Offline agent-lines monthly metrics report generator v1 (W11-T3 / W12-T2).

Reads an existing metrics_summary.json (W10-T2 output) and produces human-readable
Markdown monthly reports. No external services, notifications, or outbox writes.

Usage:
    python scripts/generate_agent_lines_monthly_report.py
    python scripts/generate_agent_lines_monthly_report.py --input outbox/agent_metrics/metrics_summary.json
    python scripts/generate_agent_lines_monthly_report.py --month 2026-06
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SCHEMA_VERSION = "agent_lines_monthly_report_v1"
_DEFAULT_INPUT = "outbox/agent_metrics/metrics_summary.json"
_DEFAULT_OUTPUT_DIR = "outbox/agent_metrics"

LineType = Literal["tabular", "non_tabular", "other"]

_MATURITY_TIER_ORDER = (
    "stable",
    "controlled_experimental",
    "experimental",
    "unknown",
)


def default_input_path(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / _DEFAULT_INPUT


def default_output_dir(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / _DEFAULT_OUTPUT_DIR


def _parse_written_at_month(written_at: Any) -> Optional[str]:
    if not written_at or not isinstance(written_at, str):
        return None
    text = written_at.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text).astimezone(timezone.utc)
    except ValueError:
        return None
    return f"{dt.year:04d}-{dt.month:02d}"


def classify_line_type(source: str) -> LineType:
    if source == "non_tabular_experiment":
        return "non_tabular"
    if source in {"agent_experiment_regression", "agent_ci"}:
        return "tabular"
    return "other"


def _empty_bucket() -> Dict[str, Any]:
    return {
        "total_runs": 0,
        "successful_runs": 0,
        "failed_runs": 0,
        "error_rate": 0.0,
        "checkpoint_a_triggered": 0,
        "checkpoint_a_trigger_rate": 0.0,
        "checkpoint_b_triggered": 0,
        "checkpoint_b_trigger_rate": 0.0,
        "non_tabular_preview_count": 0,
    }


def _finalize_bucket(bucket: Dict[str, Any]) -> Dict[str, Any]:
    total = bucket["total_runs"]
    failed = bucket["failed_runs"]
    bucket["error_rate"] = round(failed / total, 4) if total else 0.0
    cp_a = bucket["checkpoint_a_triggered"]
    cp_b = bucket["checkpoint_b_triggered"]
    bucket["checkpoint_a_trigger_rate"] = round(cp_a / total, 4) if total else 0.0
    bucket["checkpoint_b_trigger_rate"] = round(cp_b / total, 4) if total else 0.0
    return bucket


def _accumulate_run(bucket: Dict[str, Any], run: Dict[str, Any]) -> None:
    bucket["total_runs"] += 1
    if run.get("ok"):
        bucket["successful_runs"] += 1
    else:
        bucket["failed_runs"] += 1
    if run.get("checkpoint_a_triggered") is True:
        bucket["checkpoint_a_triggered"] += 1
    if run.get("checkpoint_b_triggered") is True:
        bucket["checkpoint_b_triggered"] += 1


def aggregate_runs_by_month(
    runs: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Group runs into per-month buckets: overall, tabular, non_tabular."""
    by_month: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for run in runs:
        month = _parse_written_at_month(run.get("written_at"))
        if month is None:
            continue
        month_buckets = by_month.setdefault(
            month,
            {
                "overall": _empty_bucket(),
                "tabular": _empty_bucket(),
                "non_tabular": _empty_bucket(),
            },
        )
        line_type = classify_line_type(str(run.get("source") or ""))
        _accumulate_run(month_buckets["overall"], run)
        if line_type == "tabular":
            _accumulate_run(month_buckets["tabular"], run)
        elif line_type == "non_tabular":
            _accumulate_run(month_buckets["non_tabular"], run)
            month_buckets["non_tabular"]["non_tabular_preview_count"] += 1
            month_buckets["overall"]["non_tabular_preview_count"] += 1

    for month_buckets in by_month.values():
        for bucket in month_buckets.values():
            _finalize_bucket(bucket)
    return by_month


def _pct(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def _sorted_maturity_tiers(keys: List[str]) -> List[str]:
    order = {tier: idx for idx, tier in enumerate(_MATURITY_TIER_ORDER)}
    return sorted(keys, key=lambda item: (order.get(item, len(_MATURITY_TIER_ORDER)), item))


def aggregate_tabular_runs_by_fixture_maturity(
    runs: List[Dict[str, Any]],
    *,
    month: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Bucket tabular runs by fixture_maturity tier (W12-T2)."""
    by_maturity: Dict[str, Dict[str, Any]] = {}
    for run in runs:
        if classify_line_type(str(run.get("source") or "")) != "tabular":
            continue
        if month is not None and _parse_written_at_month(run.get("written_at")) != month:
            continue
        maturity = run.get("fixture_maturity")
        if not isinstance(maturity, str) or not maturity.strip():
            maturity = "unknown"
        else:
            maturity = maturity.strip()
        bucket = by_maturity.setdefault(maturity, _empty_bucket())
        _accumulate_run(bucket, run)
    for bucket in by_maturity.values():
        _finalize_bucket(bucket)
    return by_maturity


def render_fixture_maturity_table(
    by_maturity: Dict[str, Dict[str, Any]],
) -> List[str]:
    if not by_maturity:
        return []
    lines = [
        "## Tabular fixture maturity (tier rollup)",
        "",
        "| Tier | Runs | Error rate | CP-A rate | CP-B rate |",
        "|------|------|------------|-----------|-----------|",
    ]
    for tier in _sorted_maturity_tiers(list(by_maturity.keys())):
        bucket = by_maturity[tier]
        lines.append(
            f"| `{tier}` | {bucket['total_runs']} | {_pct(bucket['error_rate'])} | "
            f"{_pct(bucket['checkpoint_a_trigger_rate'])} | "
            f"{_pct(bucket['checkpoint_b_trigger_rate'])} |"
        )
    lines.extend(
        [
            "",
            "- Tiers come from `fixture_maturity` on tabular run records; missing values roll up as `unknown`.",
            "- Non-tabular preview runs are excluded from this table.",
            "",
        ]
    )
    return lines


def render_monthly_markdown(
    month: str,
    buckets: Dict[str, Dict[str, Any]],
    *,
    source_summary: Optional[Dict[str, Any]] = None,
    by_fixture_maturity: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    overall = buckets["overall"]
    tabular = buckets["tabular"]
    non_tabular = buckets["non_tabular"]
    generated_at = (source_summary or {}).get("generated_at", "unknown")
    lines = [
        f"# Agent Lines Monthly Report — {month}",
        "",
        f"> Generated from `metrics_summary.json` · source snapshot: `{generated_at}`",
        f"> Schema: `{_SCHEMA_VERSION}` · **offline only** — no external monitoring",
        "",
        "## Summary",
        "",
        "| Metric | All lines | Tabular | Non-tabular preview |",
        "|--------|-----------|---------|---------------------|",
        f"| Total runs | {overall['total_runs']} | {tabular['total_runs']} | {non_tabular['total_runs']} |",
        f"| Successful | {overall['successful_runs']} | {tabular['successful_runs']} | {non_tabular['successful_runs']} |",
        f"| Failed | {overall['failed_runs']} | {tabular['failed_runs']} | {non_tabular['failed_runs']} |",
        f"| Error rate | {_pct(overall['error_rate'])} | {_pct(tabular['error_rate'])} | {_pct(non_tabular['error_rate'])} |",
        f"| CP-A trigger rate | {_pct(overall['checkpoint_a_trigger_rate'])} | {_pct(tabular['checkpoint_a_trigger_rate'])} | — |",
        f"| CP-B trigger rate | {_pct(overall['checkpoint_b_trigger_rate'])} | {_pct(tabular['checkpoint_b_trigger_rate'])} | — |",
        f"| Non-tabular previews | {overall['non_tabular_preview_count']} | — | {non_tabular['non_tabular_preview_count']} |",
        "",
    ]
    if by_fixture_maturity:
        lines.extend(render_fixture_maturity_table(by_fixture_maturity))
    lines.extend(
        [
        "## Notes",
        "",
        "- **Tabular** sources: `agent_experiment_regression`, `agent_ci` (HITL CP-A/B applicable).",
        "- **Non-tabular** source: `non_tabular_experiment` (preview artifacts; CP-A/B not integrated in v1).",
        "- Runs without `written_at` are excluded from monthly buckets.",
        "- This report does **not** send notifications or connect to external services.",
        "",
        ]
    )
    return "\n".join(lines)


def load_metrics_summary(input_path: Path) -> Dict[str, Any]:
    if not input_path.is_file():
        return {
            "ok": False,
            "message": f"metrics summary not found: {input_path.as_posix()}",
            "runs": [],
        }
    try:
        with input_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": f"failed to read metrics summary: {exc}",
            "runs": [],
        }
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "metrics summary root must be a JSON object",
            "runs": [],
        }
    return payload


def generate_agent_lines_monthly_report(
    *,
    metrics_summary: Dict[str, Any],
    repo_root: Optional[Path] = None,
    write_outputs: bool = True,
    output_dir: Optional[Path] = None,
    months_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build monthly Markdown reports from a W10-T2 metrics_summary payload."""
    root = (repo_root or _REPO_ROOT).resolve()
    out_dir = (output_dir or default_output_dir(root)).resolve()
    runs = metrics_summary.get("runs") or []
    if not isinstance(runs, list):
        runs = []

    by_month = aggregate_runs_by_month(runs)
    selected_months = sorted(by_month.keys())
    if months_filter:
        allowed = {m.strip() for m in months_filter if m.strip()}
        selected_months = [m for m in selected_months if m in allowed]

    report_paths: Dict[str, str] = {}
    reports: Dict[str, str] = {}
    runs_by_maturity_month = {
        month: aggregate_tabular_runs_by_fixture_maturity(runs, month=month)
        for month in selected_months
    }

    for month in selected_months:
        markdown = render_monthly_markdown(
            month,
            by_month[month],
            source_summary=metrics_summary,
            by_fixture_maturity=runs_by_maturity_month.get(month) or {},
        )
        reports[month] = markdown
        rel_name = f"monthly_report_{month}.md"
        if write_outputs:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / rel_name
            out_path.write_text(markdown, encoding="utf-8")
            try:
                report_paths[month] = out_path.relative_to(root).as_posix()
            except ValueError:
                report_paths[month] = out_path.as_posix()

    skipped_no_timestamp = sum(
        1 for run in runs if _parse_written_at_month(run.get("written_at")) is None
    )

    result: Dict[str, Any] = {
        "ok": bool(metrics_summary.get("ok", True)) and bool(runs) is not False,
        "schema_version": _SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "source_schema_version": metrics_summary.get("schema_version"),
        "source_generated_at": metrics_summary.get("generated_at"),
        "months": selected_months,
        "by_month": {m: by_month[m] for m in selected_months},
        "by_fixture_maturity": {
            m: runs_by_maturity_month.get(m, {}) for m in selected_months
        },
        "report_paths": report_paths,
        "skipped_runs_without_timestamp": skipped_no_timestamp,
        "message": (
            f"generated {len(selected_months)} monthly report(s) "
            f"from {len(runs)} run record(s)"
        ),
    }
    if not runs:
        result["ok"] = False
        result["message"] = "no runs in metrics summary"
    return result


def format_report_result_text(result: Dict[str, Any]) -> str:
    lines = [
        "Agent Lines Monthly Report (W11-T3)",
        f"schema_version: {result.get('schema_version')}",
        f"generated_at: {result.get('generated_at')}",
        f"months: {', '.join(result.get('months') or []) or '(none)'}",
        f"message: {result.get('message')}",
    ]
    for month, path in sorted((result.get("report_paths") or {}).items()):
        lines.append(f"report[{month}]: {path}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate offline monthly Markdown reports from metrics_summary.json.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(_REPO_ROOT),
        help="Repository root (default: script parent directory)",
    )
    parser.add_argument(
        "--input",
        default="",
        help=f"Path to metrics_summary.json (default: {_DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help=f"Output directory for monthly reports (default: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--month",
        action="append",
        default=[],
        help="Generate only specific month(s), e.g. 2026-06 (repeatable)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Build reports in memory only; do not write Markdown files",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    input_path = (
        Path(args.input).resolve()
        if args.input
        else default_input_path(repo_root)
    )
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else default_output_dir(repo_root)
    )

    summary = load_metrics_summary(input_path)
    if summary.get("ok") is False and not summary.get("runs"):
        print(
            json.dumps(
                {
                    "ok": False,
                    "message": summary.get("message"),
                },
                indent=2,
                ensure_ascii=False,
            )
            if args.format == "json"
            else summary.get("message"),
            file=sys.stderr,
        )
        return 1

    result = generate_agent_lines_monthly_report(
        metrics_summary=summary,
        repo_root=repo_root,
        write_outputs=not args.no_write,
        output_dir=output_dir,
        months_filter=args.month or None,
    )
    result["input_path"] = (
        input_path.relative_to(repo_root).as_posix()
        if input_path.is_relative_to(repo_root)
        else input_path.as_posix()
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_report_result_text(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
