#!/usr/bin/env python3
"""Hermes → Cursor task dispatcher.

Writes a structured task card to .cursor/hooks_state/hermes_task.json,
then optionally opens Cursor at the target file.

Usage:
    python .cursor/hooks/hermes_dispatch.py \
        --ticket-id HQ-XXX \
        --goal "Fix the broken import in core/module.py" \
        --primary-target core/module.py \
        --allowed core/module.py tests/test_module.py \
        --forbidden .env runtime/checkpoints \
        --accept "python -m pytest tests/test_module.py -v" \
        --context 04_Workflows/tickets/HQ-XXX_state.md \
        --open-cursor
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # .cursor/hooks -> repo root
TASK_PATH = REPO_ROOT / ".cursor" / "hooks_state" / "hermes_task.json"
RESULT_PATH = REPO_ROOT / ".cursor" / "hooks_state" / "hermes_task_result.json"
SNAPSHOT_PATH = REPO_ROOT / ".cursor" / "hooks_state" / "hermes_dispatch_snapshot.txt"


def get_git_snapshot() -> list[str]:
    """Record list of currently dirty files (git status --porcelain)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
        )
        files = []
        for line in result.stdout.strip().splitlines():
            # Format: "XY filename" — take everything after the 3-char status prefix
            if len(line) > 3:
                files.append(line[3:].strip())
        return sorted(files)
    except Exception:
        return []


def get_git_head() -> str | None:
    """Get current git HEAD commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_task_card(args: argparse.Namespace) -> dict:
    """Build and write the task card JSON."""
    # Save snapshot of dirty files at dispatch time (for scope delta check)
    snapshot = get_git_snapshot()
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(snapshot))
        f.write("\n") if snapshot else None

    task = {
        "ticket_id": args.ticket_id,
        "dispatched_at": utc_now_iso(),
        "dispatcher": "hermes",
        "goal": args.goal,
        "primary_target": args.primary_target,
        "allowed_paths": args.allowed or [],
        "forbidden_paths": args.forbidden or [],
        "acceptance_commands": args.accept or [],
        "context_files": args.context or [],
        "priority": args.priority or "normal",
        "notes": args.notes or "",
        "gate_files": args.gate_files or [],
        "dispatch_head": get_git_head(),
    }
    TASK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TASK_PATH, "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return task


def open_cursor(target: str | None = None) -> bool:
    """Try to open Cursor at the repo root or a specific file:line."""
    cursor_cmd = _find_cursor()
    if not cursor_cmd:
        print("[hermes_dispatch] cursor CLI not found in PATH", file=sys.stderr)
        return False

    cmd = [cursor_cmd, str(REPO_ROOT)]
    if target:
        # cursor -g file:line opens at specific location
        cmd = [cursor_cmd, "-g", target]

    try:
        subprocess.Popen(cmd, cwd=str(REPO_ROOT))
        return True
    except FileNotFoundError:
        print(f"[hermes_dispatch] failed to launch: {cmd[0]}", file=sys.stderr)
        return False


def _find_cursor() -> str | None:
    """Locate cursor CLI."""
    import shutil

    # Check PATH first
    found = shutil.which("cursor")
    if found:
        return found

    # Windows fallback: common install location
    candidates = [
        Path.home() / "AppData/Local/Programs/cursor/resources/app/bin/cursor.cmd",
        Path.home() / "AppData/Local/Programs/cursor/resources/app/bin/cursor",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def read_result() -> dict | None:
    """Read the existing task result (if any)."""
    if RESULT_PATH.is_file():
        try:
            with open(RESULT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def clear_task():
    """Remove the task card, result, and snapshot after successful dispatch."""
    for p in (TASK_PATH, RESULT_PATH, SNAPSHOT_PATH):
        if p.is_file():
            p.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes → Cursor task dispatcher")
    sub = parser.add_subparsers(dest="command")

    # dispatch: write task card and optionally open Cursor
    dispatch = sub.add_parser("dispatch", help="Write task card + open Cursor")
    dispatch.add_argument("--ticket-id", required=True, help="Ticket ID (e.g. HQ-XXX)")
    dispatch.add_argument("--goal", required=True, help="Task goal description")
    dispatch.add_argument("--primary-target", required=True, help="Primary file/module to change")
    dispatch.add_argument("--allowed", nargs="*", default=[], help="Allowed file paths")
    dispatch.add_argument("--forbidden", nargs="*", default=[], help="Forbidden file paths")
    dispatch.add_argument("--accept", nargs="*", default=[], help="Acceptance commands")
    dispatch.add_argument("--context", nargs="*", default=[], help="Context files to read")
    dispatch.add_argument("--priority", default="normal", choices=["low", "normal", "high", "urgent"])
    dispatch.add_argument("--notes", default="", help="Extra notes for Cursor")
    dispatch.add_argument("--gate-files", nargs="*", default=[], help="Governance files to read first")
    dispatch.add_argument("--open-cursor", action="store_true", help="Open Cursor after writing task card")

    # check: see if there's a pending or completed task
    sub.add_parser("check", help="Check task status")

    # result: read the result JSON
    sub.add_parser("result", help="Read task result")

    # clear: remove task card + result
    sub.add_parser("clear", help="Clear task card and result")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "dispatch":
        task = write_task_card(args)
        print(json.dumps({
            "ok": True,
            "ticket_id": task["ticket_id"],
            "task_path": str(TASK_PATH),
            "message": f"Task card written. Open Cursor and run /hermes-dispatch",
        }, ensure_ascii=False, indent=2))

        if args.open_cursor:
            opened = open_cursor(args.primary_target)
            if opened:
                print(f"  Cursor opened at {args.primary_target}")
            else:
                print("  Could not open Cursor automatically; please open manually")

        return 0

    elif args.command == "check":
        result = read_result()
        task_exists = TASK_PATH.is_file()
        if result:
            print(json.dumps({
                "status": result.get("status", "unknown"),
                "ticket_id": result.get("ticket_id"),
                "message": result.get("message"),
                "files_changed": result.get("files_changed", []),
            }, ensure_ascii=False, indent=2))
        elif task_exists:
            print(json.dumps({
                "status": "pending",
                "message": "Task card exists, waiting for Cursor to complete",
            }, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({
                "status": "idle",
                "message": "No active task",
            }, ensure_ascii=False, indent=2))
        return 0

    elif args.command == "result":
        result = read_result()
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"ok": False, "message": "No result found"}, ensure_ascii=False))
        return 0

    elif args.command == "clear":
        clear_task()
        print(json.dumps({"ok": True, "message": "Task card and result cleared"}, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
