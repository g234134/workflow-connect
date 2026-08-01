#!/usr/bin/env python
"""CLI entry for control-plane dispatch executor (read-only suggestions)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from dispatch_executor import (  # noqa: E402
    build_dispatch_plan,
    write_dispatch_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan ticket state files and emit dispatch suggestions (read-only).",
    )
    parser.add_argument(
        "--ticket",
        help="Filter to tickets whose id/path contains this substring (e.g. W1-T2)",
    )
    parser.add_argument(
        "--json-out",
        default="artifacts/control_plane/dispatch_plan.latest.json",
        help="JSON artifact path (relative to repo root)",
    )
    parser.add_argument(
        "--md-out",
        default="artifacts/control_plane/dispatch_plan.latest.md",
        help="Markdown artifact path (relative to repo root)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing artifact files; stdout only",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON plan to stdout",
    )
    args = parser.parse_args()

    plan = build_dispatch_plan(_REPO_ROOT, ticket_filter=args.ticket)

    if not args.no_write:
        write_dispatch_artifacts(
            plan,
            json_out=_REPO_ROOT / args.json_out,
            md_out=_REPO_ROOT / args.md_out,
        )

    if args.pretty:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    elif not args.no_write:
        print(json.dumps({"ok": plan.get("ok"), "tickets_scanned": plan.get("tickets_scanned")}, ensure_ascii=False))

    return 0 if plan.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
