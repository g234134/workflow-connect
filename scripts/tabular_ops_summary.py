#!/usr/bin/env python3
"""Tabular ops summary CLI — operator-friendly case status at a glance.

Read-only aggregation over automation_state.json, delivery approval, HITL
checkpoints, output_guard policy, and per-case DLQ index. Does not mutate case files.

Usage:
    python scripts/tabular_ops_summary.py --case-id demo_phase
    python scripts/tabular_ops_summary.py --case-id demo_phase --json
    python scripts/tabular_ops_summary.py --client-ref sampleco
    python scripts/tabular_ops_summary.py --all
    python scripts/tabular_ops_summary.py --all --fleet --json
    python scripts/tabular_ops_summary.py --all --format table
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_ops_summary_lib import (  # noqa: E402
    build_ops_summary,
    format_fleet_blockers,
    format_ops_table,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize Tabular case automation status for operators (read-only)."
        )
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--case-id",
        help="Single case id (e.g. demo_phase, 2026-0001)",
    )
    scope.add_argument(
        "--client-ref",
        help="Filter cases by intake.json client_ref (case-insensitive)",
    )
    scope.add_argument(
        "--all",
        action="store_true",
        help="Summarize all cases under cases/ (excluding _TEMPLATE_case etc.)",
    )
    parser.add_argument(
        "--fleet",
        action="store_true",
        help="Emit fleet ops rollup (tabular-fleet-ops-v1 schema with blocker lists)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format: human table (default) or JSON",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Alias for --format json",
    )
    args = parser.parse_args(argv)

    output_format = "json" if args.json else args.format

    result = build_ops_summary(
        case_id=args.case_id,
        client_ref=args.client_ref,
        list_all=args.all,
        fleet=args.fleet,
    )

    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.fleet:
        print(format_fleet_blockers(result))
        print("")
        print(format_ops_table(result))
    else:
        print(format_ops_table(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
