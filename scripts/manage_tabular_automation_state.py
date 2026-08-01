#!/usr/bin/env python3
"""CLI: tabular cleaning automation control plane (start / pause / resume / stop / status).

Persists per-case ``cases/<case>/automation_state.json``. Machine-readable JSON on stdout
when ``--json`` is set; otherwise a short human summary plus JSON block.

Usage:
    python scripts/manage_tabular_automation_state.py status \\
        --case-dir cases/demo_phase --json

    python scripts/manage_tabular_automation_state.py start \\
        --case-dir cases/demo_phase --requested-by operator --json

    python scripts/manage_tabular_automation_state.py pause \\
        --case-dir cases/demo_phase --requested-by operator --reason "awaiting review" --json

    python scripts/manage_tabular_automation_state.py resume \\
        --case-dir cases/demo_phase --requested-by operator --json

    python scripts/manage_tabular_automation_state.py stop \\
        --case-dir cases/demo_phase --requested-by operator --json

    python scripts/manage_tabular_automation_state.py start \\
        --case-dir cases/demo_phase --requested-by operator --restart --json
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

from tabular_automation_state_lib import (  # noqa: E402
    get_status,
    pause_automation,
    resume_automation,
    start_automation,
    stop_automation,
)


def _dispatch(args: argparse.Namespace) -> dict:
    case_dir = args.case_dir.resolve()
    command = args.command

    if command == "status":
        return get_status(case_dir)
    if command == "start":
        return start_automation(
            case_dir,
            requested_by=args.requested_by,
            restart=args.restart,
        )
    if command == "pause":
        return pause_automation(
            case_dir,
            requested_by=args.requested_by,
            reason=args.reason,
        )
    if command == "resume":
        return resume_automation(case_dir, requested_by=args.requested_by)
    if command == "stop":
        return stop_automation(case_dir, requested_by=args.requested_by)
    raise ValueError(f"unknown command: {command}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Tabular cleaning automation control plane v1. "
            "Writes automation_state.json at the case root."
        )
    )
    parser.add_argument(
        "command",
        choices=("start", "pause", "resume", "stop", "status"),
        help="Control action",
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        type=Path,
        help="Case directory containing intake.json",
    )
    parser.add_argument(
        "--requested-by",
        default="operator",
        help="Actor id recorded on start/pause/resume/stop (default: operator)",
    )
    parser.add_argument(
        "--reason",
        default=None,
        help="Pause reason (pause command only)",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help=(
            "Required to start after stopped/completed/failed; "
            "clears retry_count and last_error for a new run"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full structured result JSON to stdout",
    )
    args = parser.parse_args(argv)

    result = _dispatch(args)
    status = result.get("automation_status") or (result.get("state") or {}).get(
        "automation_status"
    )
    summary = (
        f"command={result.get('command')} ok={result.get('ok')} "
        f"status={status} message={result.get('message', '')}"
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(summary)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
