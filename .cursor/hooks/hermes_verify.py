#!/usr/bin/env python3
"""Hermes-side verification for Cursor-dispatched tasks.

Reads hermes_task.json + hermes_task_result.json, runs acceptance commands,
checks git diff for scope compliance, and outputs a verdict JSON.

Usage:
    python .cursor/hooks/hermes_verify.py [--ticket-id HQ-XXX] [--clean]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TASK_PATH = REPO_ROOT / ".cursor" / "hooks_state" / "hermes_task.json"
RESULT_PATH = REPO_ROOT / ".cursor" / "hooks_state" / "hermes_task_result.json"
SNAPSHOT_PATH = REPO_ROOT / ".cursor" / "hooks_state" / "hermes_dispatch_snapshot.txt"
LEDGER_PATH = REPO_ROOT / "04_Workflows" / "cross_agent_fix_ledger.yaml"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(cmd: str, timeout: int = 60) -> dict:
    """Run a shell command and return structured result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=str(REPO_ROOT), timeout=timeout,
        )
        return {
            "command": cmd,
            "exit_code": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
            "ok": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"command": cmd, "exit_code": -1, "ok": False, "error": "timeout"}
    except Exception as e:
        return {"command": cmd, "exit_code": -1, "ok": False, "error": str(e)}


def get_git_diff_files() -> list[str]:
    """Get list of NEW dirty files since dispatch via snapshot delta.

    Compares current git status against the snapshot taken at dispatch time.
    Only files that became dirty (or changed status) AFTER dispatch are
    considered — pre-existing dirty files are ignored.
    """
    try:
        # Load pre-dispatch snapshot
        pre_files = set()
        if SNAPSHOT_PATH.is_file():
            with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        pre_files.add(line)

        # Get current dirty files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
        )
        cur_files = set()
        for line in result.stdout.strip().splitlines():
            if len(line) > 3:
                cur_files.add(line[3:].strip())

        # Delta: files that are dirty NOW but weren't at dispatch time
        new_files = sorted(cur_files - pre_files)
        return new_files
    except Exception:
        return []


def check_scope_compliance(changed_files: list[str], allowed: list[str], forbidden: list[str]) -> dict:
    """Check if changed files are within allowed scope and outside forbidden scope."""
    violations = []

    # Check forbidden paths
    for f in changed_files:
        for fp in forbidden:
            if f.startswith(fp) or fp in f:
                violations.append(f"FORBIDDEN: {f} matches forbidden path {fp}")

    # Check allowed paths (if specified; empty means any is allowed)
    if allowed:
        for f in changed_files:
            in_scope = any(f.startswith(a) or a in f for a in allowed)
            if not in_scope:
                violations.append(f"OUT_OF_SCOPE: {f} not in allowed_paths")

    return {
        "compliant": len(violations) == 0,
        "violations": violations,
        "files_checked": changed_files,
    }


def read_task() -> dict | None:
    if TASK_PATH.is_file():
        try:
            with open(TASK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def read_result() -> dict | None:
    if RESULT_PATH.is_file():
        try:
            with open(RESULT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes-side verification")
    parser.add_argument("--ticket-id", help="Verify specific ticket (matches task card)")
    parser.add_argument("--clean", action="store_true", help="Clear task + result after verification")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per acceptance command")
    args = parser.parse_args()

    task = read_task()
    result = read_result()

    # Build verdict
    verdict = {
        "verified_at": utc_now_iso(),
        "ticket_id": args.ticket_id or (task or {}).get("ticket_id", "unknown"),
        "checks": {},
        "overall_ok": False,
    }

    # Check 1: Task card exists
    if not task:
        verdict["checks"]["task_card"] = {"ok": False, "message": "No task card found"}
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
        return 1
    verdict["checks"]["task_card"] = {"ok": True}

    # Check 2: Result exists
    if not result:
        verdict["checks"]["result"] = {"ok": False, "message": "No result from Cursor yet"}
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
        return 1
    verdict["checks"]["result"] = {
        "ok": result.get("status") == "completed",
        "status": result.get("status"),
        "message": result.get("message"),
    }

    # Check 3: Scope compliance (git diff)
    changed_files = get_git_diff_files()
    scope = check_scope_compliance(
        changed_files,
        task.get("allowed_paths", []),
        task.get("forbidden_paths", []),
    )
    verdict["checks"]["scope"] = scope

    # Check 4: Acceptance commands
    acceptance_results = []
    all_commands_ok = True
    for cmd in (task.get("acceptance_commands") or []):
        res = run_command(cmd, timeout=args.timeout)
        acceptance_results.append(res)
        if not res["ok"]:
            all_commands_ok = False
    verdict["checks"]["acceptance"] = {
        "ok": all_commands_ok,
        "commands": acceptance_results,
    }

    # Check 5: Skeleton/placeholder honesty
    skeleton_items = result.get("skeleton", [])
    blockers = result.get("blockers", [])
    verdict["checks"]["completeness"] = {
        "ok": len(blockers) == 0,
        "skeleton_items": skeleton_items,
        "blockers": blockers,
    }

    # Overall verdict
    verdict["overall_ok"] = all([
        verdict["checks"]["task_card"]["ok"],
        verdict["checks"]["result"]["ok"],
        verdict["checks"]["scope"]["compliant"],
        verdict["checks"]["acceptance"]["ok"],
        verdict["checks"]["completeness"]["ok"],
    ])

    # Summary
    verdict["summary"] = {
        "files_changed": changed_files,
        "cursor_files_changed": result.get("files_changed", []),
        "commands_run": [r.get("command") for r in acceptance_results],
        "all_passing": verdict["overall_ok"],
    }

    print(json.dumps(verdict, ensure_ascii=False, indent=2))

    # Clean up if requested
    if args.clean and verdict["overall_ok"]:
        for p in (TASK_PATH, RESULT_PATH):
            if p.is_file():
                p.unlink()
        print(f"\n[hermes_verify] Task card and result cleared.", file=sys.stderr)

    return 0 if verdict["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
