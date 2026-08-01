#!/usr/bin/env python3
"""Standard-case metrics exporter v1 (MP-METRICS · read-only).

Aggregates per-case operator backlog status and workflow notification ack
metrics from existing read models (backlog CLI, workflow event consumer,
feedback ingest). Does not write to outbox or emit events.

Usage:
    python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json
    python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format text
    python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format prometheus
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

from delivery.feedback_ingest_v1 import ingest_pending_events
from delivery.workflow_event_consumer_v1 import load_workflow_events
from scripts.list_operator_backlog_v1 import build_backlog_entry

SCHEMA_VERSION = "std_case_metrics_v1"

_METRIC_KEYS = (
    "pending_cases_count",
    "blocked_cases_count",
    "completed_cases_count",
    "notifications_emitted_count",
    "notifications_with_pending_ack_count",
    "notifications_failed_ack_count",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _status_to_case_counts(status: str) -> Dict[str, int]:
    return {
        "pending_cases_count": 1 if status == "pending" else 0,
        "blocked_cases_count": 1 if status == "blocked" else 0,
        "completed_cases_count": 1 if status == "completed" else 0,
    }


def _notification_metrics(
    events: List[Dict[str, Any]],
) -> Dict[str, int]:
    notif_rows = [row for row in events if row.get("source_stream") == "notification"]
    pending_ack = sum(1 for row in notif_rows if row.get("tracking_status") == "pending_ack")
    failed_ack = sum(1 for row in notif_rows if row.get("tracking_status") == "failed")
    return {
        "notifications_emitted_count": len(notif_rows),
        "notifications_with_pending_ack_count": pending_ack,
        "notifications_failed_ack_count": failed_ack,
    }


def export_std_case_metrics(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Export lightweight per-case metrics (read-only)."""
    root = (repo_root or _REPO_ROOT).resolve()
    norm_case = case_ref.replace("\\", "/").strip("/")

    backlog_entry = build_backlog_entry(
        norm_case,
        repo_root=root,
        outbox_root_override=outbox_root_override,
    )
    operator_status = str(backlog_entry.get("status") or "inactive")
    if backlog_entry.get("skipped"):
        operator_status = "inactive"

    consumer = load_workflow_events(
        norm_case,
        repo_root=root,
        outbox_root_override=outbox_root_override,
    )
    if not consumer.get("ok"):
        return {
            "ok": False,
            "read_only": True,
            "schema_version": SCHEMA_VERSION,
            "case_ref": norm_case,
            "exported_at": _utc_now_iso(),
            "message": consumer.get("message", "workflow consumer failed"),
            "std_case_metrics_v1": {key: 0 for key in _METRIC_KEYS},
            "operator_status": operator_status,
        }

    ingest = ingest_pending_events(
        norm_case,
        repo_root=root,
        outbox_root_override=outbox_root_override,
    )
    if not ingest.get("ok"):
        return {
            "ok": False,
            "read_only": True,
            "schema_version": SCHEMA_VERSION,
            "case_ref": norm_case,
            "exported_at": _utc_now_iso(),
            "message": ingest.get("message", "feedback ingest failed"),
            "std_case_metrics_v1": {key: 0 for key in _METRIC_KEYS},
            "operator_status": operator_status,
        }

    events = consumer.get("events") or []
    metrics: Dict[str, int] = {}
    metrics.update(_status_to_case_counts(operator_status))
    metrics.update(_notification_metrics(events))

    return {
        "ok": True,
        "read_only": True,
        "schema_version": SCHEMA_VERSION,
        "case_ref": norm_case,
        "exported_at": _utc_now_iso(),
        "message": f"exported metrics for case_ref={norm_case}",
        "operator_status": operator_status,
        "std_case_metrics_v1": metrics,
        "sources": {
            "backlog_status": operator_status,
            "consumer_event_count": consumer.get("count", 0),
            "ingest_pending_count": ingest.get("pending_count", 0),
        },
    }


def _format_text(result: dict) -> str:
    metrics = result.get("std_case_metrics_v1") or {}
    lines = [
        "Standard Case Metrics Exporter v1 (read-only)",
        f"case_ref: {result.get('case_ref')}",
        f"ok: {result.get('ok')}",
        f"operator_status: {result.get('operator_status')}",
        f"exported_at: {result.get('exported_at')}",
        "",
        "── std_case_metrics_v1 ──",
    ]
    for key in _METRIC_KEYS:
        lines.append(f"  {key}: {metrics.get(key, 0)}")
    lines.append("")
    sources = result.get("sources") or {}
    if sources:
        lines.append("── sources ──")
        for key, value in sources.items():
            lines.append(f"  {key}: {value}")
        lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def format_std_case_metrics_prometheus(result: dict) -> str:
    """Render exporter result as Prometheus text exposition format."""
    case_ref = str(result.get("case_ref") or "unknown")
    metrics = result.get("std_case_metrics_v1") or {}
    lines: List[str] = []
    if not result.get("ok"):
        message = str(result.get("message") or "export failed")
        lines.append(f"# error: {message}")
    for key in _METRIC_KEYS:
        lines.append(f"# HELP {key} Standard-case metric {key}")
        lines.append(f"# TYPE {key} gauge")
        lines.append(f'{key}{{case_ref="{case_ref}"}} {metrics.get(key, 0)}')
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export per-case standard-case metrics (read-only)."
    )
    parser.add_argument("--case-ref", required=True, help="Case slug under cases/")
    parser.add_argument(
        "--format",
        choices=("json", "text", "prometheus"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument("--outbox-root", default=None, help="Optional outbox root override")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    result = export_std_case_metrics(
        args.case_ref,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.format == "prometheus":
        print(format_std_case_metrics_prometheus(result), end="")
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
