#!/usr/bin/env python3
"""CLI inspector for tabular MVP outbox records (W3-TL-T4).

Examples:
    python tools/inspect_tabular_outbox.py --case-ref demo_phase
    python tools/inspect_tabular_outbox.py --case-ref demo_phase --tool-id validate.eligibility
    python tools/inspect_tabular_outbox.py --case-ref demo_phase --join-history --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.tabular_outbox_consumer import (  # noqa: E402
    get_outbox_run,
    join_with_case_history,
    list_outbox_runs,
)


def _format_table(rows: list[dict]) -> str:
    if not rows:
        return "(no runs)"

    columns = [
        ("run_id", 36),
        ("tool_id", 24),
        ("ok", 5),
        ("exit_code", 9),
        ("started_at", 24),
    ]
    header = "  ".join(name.ljust(width) for name, width in columns)
    lines = [header, "-" * len(header)]
    for row in rows:
        parts = []
        for name, width in columns:
            value = row.get(name, "")
            if value is None:
                text = "null"
            else:
                text = str(value)
            if len(text) > width:
                text = text[: width - 1] + "…"
            parts.append(text.ljust(width))
        lines.append("  ".join(parts))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect tabular MVP outbox runs under outbox/<case_ref>/."
    )
    parser.add_argument("--case-ref", help="Case slug (e.g. demo_phase, sampleco/2026-0001)")
    parser.add_argument("--tool-id", help="Filter by catalog tool_id")
    parser.add_argument("--run-id", help="Fetch a single run record")
    parser.add_argument(
        "--started-after",
        help="ISO-8601 lower bound on started_at (inclusive)",
    )
    parser.add_argument(
        "--started-before",
        help="ISO-8601 upper bound on started_at (inclusive)",
    )
    parser.add_argument(
        "--join-history",
        action="store_true",
        help="Join outbox runs with cases/index.json and lookup_case_history view",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON on stdout",
    )
    parser.add_argument(
        "--outbox-root",
        help="Override outbox root (repo-relative or absolute); default: outbox/",
    )
    args = parser.parse_args(argv)

    extra = {"outbox_root_override": args.outbox_root} if args.outbox_root else {}

    if args.run_id:
        if not args.case_ref:
            parser.error("--run-id requires --case-ref")
        result = get_outbox_run(args.case_ref, args.run_id, **extra)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result.get("ok"):
            print(json.dumps(result["record"], ensure_ascii=False, indent=2))
        else:
            print(result.get("message", "error"), file=sys.stderr)
        return 0 if result.get("ok") else 1

    if args.join_history:
        if not args.case_ref:
            parser.error("--join-history requires --case-ref")
        result = join_with_case_history(args.case_ref, **extra)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            case = result.get("case") or {}
            print(f"case_ref: {result.get('case_ref')}")
            print(
                f"client_ref: {case.get('client_ref')}  "
                f"product_sku: {case.get('product_sku')}  "
                f"gate_status: {case.get('gate_status')}"
            )
            print(f"run_count: {result.get('run_count', 0)}")
            print()
            print("runs (chronological):")
            print(_format_table(result.get("runs") or []))
            last = result.get("last_by_tool_id") or {}
            if last:
                print()
                print("last_by_tool_id:")
                for tool_id, row in sorted(last.items()):
                    print(
                        f"  {tool_id}: ok={row.get('ok')} "
                        f"exit_code={row.get('exit_code')} "
                        f"run_id={row.get('run_id')}"
                    )
        return 0 if result.get("ok") else 1

    runs = list_outbox_runs(
        case_ref=args.case_ref,
        tool_id=args.tool_id,
        started_after=args.started_after,
        started_before=args.started_before,
        **extra,
    )
    payload = {
        "ok": True,
        "case_ref": args.case_ref,
        "tool_id": args.tool_id,
        "count": len(runs),
        "runs": runs,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        scope = args.case_ref or "*"
        tool = args.tool_id or "*"
        print(f"outbox runs for case_ref={scope} tool_id={tool} count={len(runs)}")
        print(_format_table(runs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
