#!/usr/bin/env python3
"""Tabular delivery approval CLI (post CP-B).

Updates ``delivery_approval.json``, ``delivery_signoff.md``, ``cases/index.json``,
and mirrors fields onto ``automation_state.json``. Does not touch workflow /
governance / Dashboard.

Usage:
    python scripts/approve_tabular_delivery.py --case-id demo_phase --approve --by lead --json
    python scripts/approve_tabular_delivery.py --case-id demo_phase --reject --by lead \\
        --reason "output_guard warning" --json
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

from tabular_automation_driver_lib import resolve_case_dir  # noqa: E402
from tabular_delivery_approval_lib import (  # noqa: E402
    approve_tabular_delivery,
    evaluate_delivery_readiness,
    reject_tabular_delivery,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record tabular delivery approval or rejection after CP-B."
    )
    parser.add_argument(
        "--case-id",
        required=True,
        help="Case id (e.g. demo_phase) or nested id resolved via cases/",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--approve", action="store_true", help="Approve delivery")
    action.add_argument("--reject", action="store_true", help="Reject delivery")
    parser.add_argument(
        "--by",
        default="operator_cli",
        help="Operator id recorded in audit fields (default: operator_cli)",
    )
    parser.add_argument(
        "--reason",
        default="",
        help="Optional approval note or required rejection rationale",
    )
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        help="Only evaluate readiness gates; do not persist approve/reject",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON result")
    args = parser.parse_args(argv)

    case_dir = resolve_case_dir(case_id=args.case_id)
    if case_dir is None:
        result = {"ok": False, "message": f"case not found for case_id={args.case_id!r}"}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["message"], file=sys.stderr)
        return 1

    if args.evaluate_only:
        result = evaluate_delivery_readiness(case_dir)
    elif args.approve:
        result = approve_tabular_delivery(case_dir, approved_by=args.by, reason=args.reason)
    else:
        if not args.reason.strip():
            result = {
                "ok": False,
                "message": "--reason is required when using --reject",
                "case_dir": str(case_dir),
            }
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(result["message"], file=sys.stderr)
            return 1
        result = reject_tabular_delivery(case_dir, rejected_by=args.by, reason=args.reason)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok={result.get('ok')} message={result.get('message')}")
        if result.get("readiness_gaps"):
            print(f"gaps: {', '.join(result['readiness_gaps'])}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
