#!/usr/bin/env python3
"""Operator CLI for feedback ingest / pending notification scan (P8.9-T2).

Usage:
    python scripts/run_feedback_ingest.py --case-ref demo_phase --dry-run
    python scripts/run_feedback_ingest.py --case-ref demo_phase --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.feedback_ingest_v1 import ingest_pending_events


def _format_text(result: dict) -> str:
    lines = [
        "Feedback Ingest (P8.9-T2 · read-only dry-run)",
        f"case_ref: {result.get('case_ref')}",
        f"ok: {result.get('ok')}",
        f"pending_count: {result.get('pending_count', 0)}",
        "",
    ]
    pending = result.get("pending") or []
    if not pending:
        lines.append("(no pending notification events without downstream ack)")
    else:
        lines.append("── Pending events ──")
        for item in pending:
            lines.append(
                f"  {item.get('event_id')}  {item.get('event_type')}  "
                f"emitted_at={item.get('emitted_at')}"
            )
    lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List pending workflow notifications (dry-run).")
    parser.add_argument("--case-ref", required=True, help="Case slug under cases/")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List pending events only; never write ack files (default behavior)",
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
    result = ingest_pending_events(
        args.case_ref,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
    )
    if args.dry_run:
        result["dry_run"] = True

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_text(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
