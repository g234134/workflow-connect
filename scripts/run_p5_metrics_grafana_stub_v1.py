#!/usr/bin/env python3
"""CLI for P5 local Grafana/JSON对照 stub (P5-metrics-grafana-stub-v1).

Design SSOT: docs/p5-metrics-grafana-stub-contract-v1.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from observability.p5_metrics_grafana_stub_v1 import (  # noqa: E402
    DEFAULT_CASE_REF,
    DOC_REL,
    build_grafana_stub,
)


def _format_text(result: dict) -> str:
    health = result.get("health") or {}
    metrics = result.get("metrics") or {}
    alerts = result.get("alert_budget_summary") or {}
    lines = [
        "P5 Metrics Grafana Stub v1 (local only)",
        f"doc: {result.get('doc') or DOC_REL}",
        f"ok: {result.get('ok')}",
        f"case_ref: {result.get('case_ref')}",
        f"health.ok: {health.get('ok')} (source={health.get('source')})",
        f"metrics.scrape_ok: {metrics.get('scrape_ok')} (source={metrics.get('source')})",
        (
            f"alert_budget: warn={alerts.get('warn_count')} "
            f"critical={alerts.get('critical_count')} "
            f"total={alerts.get('total_events')} "
            f"(source={alerts.get('source')})"
        ),
        f"message: {result.get('message')}",
    ]
    if result.get("artifact_path"):
        lines.append(f"artifact_path: {result.get('artifact_path')}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="P5 local Grafana/JSON对照 stub (≠ live Grafana / PG soak).",
    )
    parser.add_argument(
        "--case-ref",
        default=DEFAULT_CASE_REF,
        help=f"Case for metrics scrape (default: {DEFAULT_CASE_REF})",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write artifacts/p5_metrics/grafana_stub.latest.json",
    )
    parser.add_argument(
        "--artifact-path",
        default=None,
        help="Optional repo-relative artifact override",
    )
    parser.add_argument(
        "--alert-sink",
        default=None,
        help="Optional P75 alert sink JSONL path (repo-relative)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument("--outbox-root", default=None, help="Optional outbox root override")
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    result = build_grafana_stub(
        case_ref=args.case_ref,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
        alert_sink_override=args.alert_sink,
        write_artifact=bool(args.write),
        artifact_path_override=args.artifact_path,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
