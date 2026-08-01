#!/usr/bin/env python3
"""Unified tabular cleaning automation driver (v1).

Chains intake readiness → gate → CP-A → clean → report → bundle → e2e → CP-B
for low-risk allowlist cases. Reads ``automation_state.json``; writes
``reports/automation_run_log.json``.

Prerequisite: control plane start (unless ``--dry-run``):

    python scripts/manage_tabular_automation_state.py start \\
        --case-dir cases/demo_phase --requested-by operator --json

Usage:
    python scripts/run_tabular_automation.py --case-id demo_phase --dry-run --json

    python scripts/run_tabular_automation.py --case-dir cases/demo_phase \\
        --start-from gate --stop-after bundle --json

    python scripts/run_tabular_automation.py --case-id demo_phase \\
        --force --json
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

from tabular_automation_driver_lib import (  # noqa: E402
    STEP_ORDER,
    normalize_step_name,
    resolve_case_dir,
    run_tabular_automation,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Unified tabular cleaning automation driver (low-risk allowlist). "
            "Requires automation_status=running unless --dry-run."
        )
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--case-id",
        help="Case id (e.g. demo_phase, 2026-0001); resolved under cases/",
    )
    target.add_argument(
        "--case-dir",
        type=Path,
        help="Explicit case directory path",
    )
    parser.add_argument(
        "--start-from",
        default="intake",
        help=(
            "First step to run: intake | gate | checkpoint_a | clean | "
            "report | bundle | e2e | checkpoint_b (default: intake)"
        ),
    )
    parser.add_argument(
        "--stop-after",
        default=None,
        help="Last step to run (inclusive); same names as --start-from",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue from automation_state.current_step (next step after pause/HITL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan steps only; do not execute subprocesses or mutate artifacts",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Internal demo bypass: non-allowlist cases, review_needed cleaning, "
            "and CP-A/B auto-approve when rules permit"
        ),
    )
    parser.add_argument(
        "--use-tool-executor",
        action="store_true",
        help=(
            "Placeholder: log tool-executor routing intent for cleaning step; "
            "default remains local subprocess CLIs"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full structured result JSON to stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    case_dir = resolve_case_dir(case_id=args.case_id, case_dir=args.case_dir)
    if case_dir is None:
        result = {
            "ok": False,
            "message": f"case not found for case_id={args.case_id!r}",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    start_from = normalize_step_name(args.start_from)
    if start_from is None:
        result = {
            "ok": False,
            "message": f"invalid --start-from: {args.start_from!r}; valid: {STEP_ORDER}",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    stop_after = None
    if args.stop_after:
        stop_after = normalize_step_name(args.stop_after)
        if stop_after is None:
            result = {
                "ok": False,
                "message": f"invalid --stop-after: {args.stop_after!r}; valid: {STEP_ORDER}",
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1

    result = run_tabular_automation(
        case_dir,
        start_from=start_from,
        stop_after=stop_after,
        resume=args.resume,
        dry_run=args.dry_run,
        force=args.force,
        use_tool_executor=args.use_tool_executor,
    )

    summary = (
        f"ok={result.get('ok')} case={result.get('case_id')} "
        f"status={result.get('automation_status')} message={result.get('message', '')}"
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(summary)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
