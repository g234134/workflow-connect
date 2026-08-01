#!/usr/bin/env python3
"""Read-only workflow event inspector (P8.9-T1 CLI).

Merges notification_events.jsonl, checkpoint_events.jsonl, and downstream ack
files into a per-case read model. No writes to outbox or feedback sinks.

Usage:
    python scripts/inspect_workflow_events.py --case-ref demo_phase --format json
    python scripts/inspect_workflow_events.py --case-ref demo_phase --event-type run.completed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.workflow_event_consumer_v1 import load_workflow_events


def _format_text(result: dict) -> str:
    lines = [
        "Workflow Event Inspector (P8.9-T1 · read-only)",
        f"case_ref: {result.get('case_ref')}",
        f"ok: {result.get('ok')}",
        f"read_only: {result.get('read_only')}",
        f"schema_version: {result.get('schema_version')}",
        f"count: {result.get('count', 0)}",
        f"streams_read: {', '.join(result.get('streams_read') or []) or '(none)'}",
        "",
    ]

    counts = result.get("count_by_event_type") or {}
    if counts:
        lines.append("── count_by_event_type ──")
        for event_type, count in sorted(counts.items()):
            lines.append(f"  {event_type}: {count}")
        lines.append("")

    timeline = result.get("timeline") or []
    if not timeline:
        lines.append("(no workflow events for this case / filter)")
    else:
        lines.append("── timeline ──")
        for row in timeline:
            tracking = row.get("tracking_status", "")
            stream = row.get("source_stream", "")
            lines.append(
                f"  {row.get('emitted_at')}  [{stream}]  {row.get('event_type')}  "
                f"tracking={tracking}  id={row.get('native_id')}"
            )
            if row.get("last_error"):
                lines.append(f"    last_error: {row.get('last_error')}")
            if row.get("ack_path"):
                lines.append(f"    ack_path: {row.get('ack_path')}")

    lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect merged workflow notification + checkpoint timeline (read-only)."
    )
    parser.add_argument("--case-ref", required=True, help="Case slug under cases/")
    parser.add_argument("--event-type", default=None, help="Optional event_type filter")
    parser.add_argument("--event-id", default=None, help="Optional notification event_id filter")
    parser.add_argument(
        "--since",
        default=None,
        help="Optional ISO timestamp lower bound (emitted_at >= since)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument("--outbox-root", default=None, help="Optional outbox root override")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    result = load_workflow_events(
        args.case_ref,
        event_type=args.event_type,
        event_id=args.event_id,
        since=args.since,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
