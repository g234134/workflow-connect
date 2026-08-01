#!/usr/bin/env python3
"""Multi-case standard-case metrics aggregator v1 (MC-METRICS · read-only).

Rolls up per-case metrics from ``export_std_case_metrics`` into fleet-level
pending/blocked/completed and notification ack totals.

Usage:
    python scripts/aggregate_multi_case_metrics_v1.py --format json
    python scripts/aggregate_multi_case_metrics_v1.py --cases demo_phase,sampleco/2026-0001 --format text
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.export_std_case_metrics_v1 import export_std_case_metrics

SCHEMA_VERSION = "multi_case_metrics_v1"

# Representative fleet cases (A1 / MVP mainline regression alignment).
DEFAULT_CASE_REFS: tuple[str, ...] = (
    "demo_phase",
    "sampleco/2026-0001",
)

_PER_CASE_TO_TOTAL = (
    ("pending_cases_count", "total_pending_cases"),
    ("blocked_cases_count", "total_blocked_cases"),
    ("completed_cases_count", "total_completed_cases"),
    ("notifications_emitted_count", "total_notifications_emitted"),
    ("notifications_failed_ack_count", "total_notifications_failed_ack"),
    ("notifications_with_pending_ack_count", "total_notifications_pending_ack"),
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_case_ref(case_ref: str) -> str:
    return case_ref.replace("\\", "/").strip("/")


def parse_case_refs(raw: Optional[str]) -> List[str]:
    """Parse comma-separated case refs; dedupe while preserving order."""
    if not raw:
        return list(DEFAULT_CASE_REFS)
    refs: List[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        norm = _normalize_case_ref(part.strip())
        if not norm or norm in seen:
            continue
        seen.add(norm)
        refs.append(norm)
    return refs


def _empty_metrics() -> Dict[str, int]:
    return {total_key: 0 for _, total_key in _PER_CASE_TO_TOTAL}


def _aggregate_metrics(per_case_exports: List[Dict[str, Any]]) -> Dict[str, int]:
    totals = _empty_metrics()
    for export in per_case_exports:
        metrics = export.get("std_case_metrics_v1") or {}
        for per_key, total_key in _PER_CASE_TO_TOTAL:
            totals[total_key] += int(metrics.get(per_key, 0) or 0)
    return totals


def _build_per_case_row(export: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "case_ref": export.get("case_ref"),
        "ok": bool(export.get("ok")),
        "operator_status": export.get("operator_status"),
        "message": export.get("message"),
        "std_case_metrics_v1": export.get("std_case_metrics_v1") or {},
    }


def aggregate_multi_case_metrics(
    case_refs: Optional[List[str]] = None,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    include_per_case: bool = True,
) -> Dict[str, Any]:
    """Aggregate fleet metrics across multiple case_ref slugs (read-only)."""
    if case_refs is None:
        refs = list(DEFAULT_CASE_REFS)
    else:
        refs = list(case_refs)
    root = (repo_root or _REPO_ROOT).resolve()

    per_case_exports: List[Dict[str, Any]] = []
    for case_ref in refs:
        per_case_exports.append(
            export_std_case_metrics(
                case_ref,
                repo_root=root,
                outbox_root_override=outbox_root_override,
            )
        )

    failed = [row for row in per_case_exports if not row.get("ok")]
    aggregated = _aggregate_metrics(per_case_exports)

    result: Dict[str, Any] = {
        "ok": len(failed) == 0,
        "read_only": True,
        "schema_version": SCHEMA_VERSION,
        "case_count": len(refs),
        "cases": refs,
        "exported_at": _utc_now_iso(),
        "metrics": aggregated,
        "message": (
            f"aggregated metrics for {len(refs)} case(s)"
            if not failed
            else f"aggregated metrics for {len(refs)} case(s); {len(failed)} export(s) failed"
        ),
    }

    if include_per_case:
        result["per_case"] = [_build_per_case_row(row) for row in per_case_exports]

    return result


def _format_text(result: dict) -> str:
    metrics = result.get("metrics") or {}
    lines = [
        "Multi-Case Standard Case Metrics Aggregator v1 (read-only)",
        f"schema_version: {result.get('schema_version')}",
        f"ok: {result.get('ok')}",
        f"case_count: {result.get('case_count')}",
        f"cases: {', '.join(result.get('cases') or [])}",
        f"exported_at: {result.get('exported_at')}",
        "",
        "── fleet metrics ──",
    ]
    for _, total_key in _PER_CASE_TO_TOTAL:
        lines.append(f"  {total_key}: {metrics.get(total_key, 0)}")
    lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate standard-case metrics across multiple cases (read-only).",
    )
    parser.add_argument(
        "--cases",
        default=None,
        help=(
            "Comma-separated case slugs (default: representative fleet set: "
            + ", ".join(DEFAULT_CASE_REFS)
            + ")"
        ),
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--no-per-case",
        action="store_true",
        help="Omit per_case drill-down array from JSON output",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument("--outbox-root", default=None, help="Optional outbox root override")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    case_refs = parse_case_refs(args.cases)
    result = aggregate_multi_case_metrics(
        case_refs,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
        include_per_case=not args.no_per_case,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
