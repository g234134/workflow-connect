#!/usr/bin/env python3
"""Replay failed Tabular automation steps from DLQ.

Usage:
    python scripts/replay_tabular_dlq.py --case-dir cases/demo_phase --list
    python scripts/replay_tabular_dlq.py --case-dir cases/demo_phase --entry-id <id> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_automation_driver_lib import run_tabular_automation  # noqa: E402
from tabular_automation_retry_dlq_lib import (  # noqa: E402
    dlq_index_path,
    mark_dlq_handled,
)
from tabular_automation_state_lib import (  # noqa: E402
    load_state,
    resume_automation,
    start_automation,
)


def list_dlq_entries(case_dir: Path) -> dict[str, Any]:
    path = dlq_index_path(case_dir)
    if not path.is_file():
        return {"ok": True, "entries": [], "message": "no DLQ index"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": f"dlq unreadable: {exc}"}
    entries = data.get("entries") or []
    queued = [e for e in entries if isinstance(e, dict) and e.get("status") == "queued"]
    return {"ok": True, "entries": queued, "all_entries": entries}


def replay_dlq_entry(
    case_dir: Path,
    entry_id: str,
    *,
    requested_by: str = "dlq_replay_cli",
    inject_transient: bool = False,
) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    listing = list_dlq_entries(case_dir)
    if not listing.get("ok"):
        return listing

    match = None
    for row in listing.get("entries") or []:
        if row.get("entry_id") == entry_id:
            match = row
            break
    if match is None:
        return {"ok": False, "message": f"queued DLQ entry not found: {entry_id}"}

    step_name = str(match.get("step_name") or "")
    if not step_name:
        return {"ok": False, "message": "DLQ entry missing step_name"}

    state = load_state(case_dir)
    status = state.get("automation_status", "idle")
    if status in {"idle", "stopped", "completed", "failed"}:
        ctl = start_automation(case_dir, requested_by=requested_by, restart=True)
        if not ctl.get("ok"):
            return ctl
    elif status == "paused":
        ctl = resume_automation(case_dir, requested_by=requested_by)
        if not ctl.get("ok"):
            return ctl

    driver = run_tabular_automation(
        case_dir,
        start_from=step_name,
        force=inject_transient,
    )
    handled = mark_dlq_handled(case_dir, entry_id)
    final_state = load_state(case_dir)

    return {
        "ok": driver.get("ok") is True,
        "entry_id": entry_id,
        "step_name": step_name,
        "driver_result": driver,
        "dlq_handled": handled,
        "automation_status": final_state.get("automation_status"),
        "message": driver.get("message", ""),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List or replay Tabular automation DLQ entries.")
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--list", action="store_true", help="List queued DLQ entries")
    parser.add_argument("--entry-id", default=None, help="Replay a specific DLQ entry")
    parser.add_argument(
        "--inject-transient",
        action="store_true",
        help="Pass --force to driver replay (testing hook)",
    )
    parser.add_argument("--requested-by", default="dlq_replay_cli")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    case_dir = args.case_dir
    if not case_dir.is_absolute():
        case_dir = _REPO_ROOT / case_dir

    if args.list:
        result = list_dlq_entries(case_dir)
    elif args.entry_id:
        result = replay_dlq_entry(
            case_dir,
            args.entry_id,
            requested_by=args.requested_by,
            inject_transient=args.inject_transient,
        )
    else:
        result = {"ok": False, "message": "specify --list or --entry-id"}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result.get("message", ""))
        if args.list and result.get("entries"):
            for row in result["entries"]:
                print(f"  {row.get('entry_id')} step={row.get('step_name')}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
