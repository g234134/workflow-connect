#!/usr/bin/env python3
"""Control Plane M2 E2E walkthrough runner (WC-T7 skeleton).

Orchestrates CLI steps from docs/wave_c/WC_T7_e2e_walkthrough_runbook.md.
Manual STATE edits (§1 setup, §3/§4 HITL) are printed, not automated.

Usage:
    python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run
    python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ALLOWED_TICKET_PREFIX = "WC-DEMO-"
_REQUIRED_ARTIFACTS_PREFIX = "artifacts/e2e"


@dataclass(frozen=True)
class Step:
    step_id: str
    title: str
    commands: tuple[list[str], ...]
    hitl_note: str | None = None
    skip_unless: str | None = None  # path relative to repo root; step skipped if missing


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _validate_ticket(ticket_id: str) -> None:
    if not ticket_id.startswith(_ALLOWED_TICKET_PREFIX):
        raise ValueError(
            f"ticket_id must start with {_ALLOWED_TICKET_PREFIX!r} (got {ticket_id!r}); "
            "refusing to run on production tickets"
        )


def _validate_artifacts_root(artifacts_root: Path) -> Path:
    rel = _rel(artifacts_root)
    norm = rel.replace("\\", "/")
    if not norm.startswith(_REQUIRED_ARTIFACTS_PREFIX):
        raise ValueError(
            f"artifacts-root must be under {_REQUIRED_ARTIFACTS_PREFIX}/ "
            f"(got {norm!r})"
        )
    return artifacts_root


def build_steps(ticket_id: str, artifact_dir: Path) -> list[Step]:
    cards_dir = artifact_dir / "cards"
    comms_dir = artifact_dir / "comms"
    orders_jsonl = artifact_dir / "orders.jsonl"
    before_review = artifact_dir / "before_review.md"
    ticket_state = _REPO_ROOT / "04_Workflows" / "tickets" / f"{ticket_id}_state.md"
    py = sys.executable

    return [
        Step(
            "0",
            "Environment check",
            (
                [py, str(_REPO_ROOT / "scripts" / "run_ticket_eligibility.py"),
                 "--ticket", ticket_id, "--requested-role", "implementer", "--format", "json"],
            ),
            skip_unless=_rel(ticket_state),
        ),
        Step(
            "2",
            "Dispatch cards + eligibility gate",
            (
                [
                    py, str(_REPO_ROOT / "scripts" / "run_dispatch_cards.py"),
                    "--refresh-plan", "--ticket", ticket_id, "--role", "implementer",
                    "--eligibility-gate", "block",
                    "--out-dir", _rel(cards_dir) + "/",
                    "--json-summary", _rel(artifact_dir / "dispatch_cards_run.json"),
                    "--pretty",
                ],
            ),
        ),
        Step(
            "3-hitl",
            "HITL: edit STATE to review/reviewer (see runbook §3)",
            (),
            hitl_note=(
                f"Manually edit {_rel(ticket_state)} STATE to review/reviewer, then save "
                f"snapshot: cp {_rel(ticket_state)} {_rel(before_review)} BEFORE editing, "
                "or copy pre-edit state to before_review.md first per runbook."
            ),
        ),
        Step(
            "3",
            "Comms JSONL (after before_review + live state differ)",
            (
                [
                    py, str(_REPO_ROOT / "scripts" / "run_ticket_state_update_with_comms.py"),
                    "--before", _rel(before_review),
                    "--after", _rel(ticket_state),
                    "--outbox-dir", _rel(comms_dir),
                ],
            ),
            skip_unless=_rel(before_review),
        ),
        Step(
            "4-hitl",
            "HITL: edit STATE to ready_for_order (see runbook §4)",
            (),
            hitl_note=(
                f"Manually edit {_rel(ticket_state)} STATE: next_action must contain "
                "'ready_for_order' before order create."
            ),
        ),
        Step(
            "4",
            "Order create + lookup + replay",
            (
                [
                    py, str(_REPO_ROOT / "scripts" / "run_order_intake.py"),
                    "--jsonl-path", _rel(orders_jsonl),
                    "create", "--ticket", ticket_id,
                    "--amount-minor", "10000", "--currency", "TWD",
                ],
                [
                    py, str(_REPO_ROOT / "scripts" / "run_order_intake.py"),
                    "--jsonl-path", _rel(orders_jsonl),
                    "lookup", "--ticket-id", ticket_id,
                ],
                [
                    py, str(_REPO_ROOT / "scripts" / "run_order_intake.py"),
                    "--jsonl-path", _rel(orders_jsonl),
                    "create", "--ticket", ticket_id,
                    "--amount-minor", "10000", "--currency", "TWD",
                ],
            ),
            skip_unless=_rel(ticket_state),
        ),
        Step(
            "5",
            "Module unittest cross-check",
            (
                [
                    py, "-m", "unittest",
                    "tests.test_ticket_eligibility",
                    "tests.test_dispatch_cards",
                    "tests.test_ticket_comms",
                    "tests.test_ticket_state_update_cli",
                    "tests.test_order_ledger",
                    "tests.test_order_ledger_integration",
                    "-v",
                ],
            ),
        ),
    ]


def _format_cmd(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def _run_cmd(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
    }


def run_walkthrough(
    ticket_id: str,
    artifacts_root: Path,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    _validate_ticket(ticket_id)
    root = _validate_artifacts_root(artifacts_root)
    artifact_dir = root / ticket_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    steps_out: list[dict[str, Any]] = []
    all_ok = True

    for step in build_steps(ticket_id, artifact_dir):
        entry: dict[str, Any] = {
            "step_id": step.step_id,
            "title": step.title,
            "status": "pending",
        }

        if step.skip_unless:
            check_path = _REPO_ROOT / step.skip_unless
            if not check_path.is_file():
                entry["status"] = "skipped"
                entry["reason"] = f"missing prerequisite: {step.skip_unless}"
                steps_out.append(entry)
                continue

        if step.hitl_note:
            entry["status"] = "hitl"
            entry["note"] = step.hitl_note
            steps_out.append(entry)
            continue

        cmd_results: list[dict[str, Any]] = []
        for cmd in step.commands:
            formatted = _format_cmd(cmd)
            if dry_run:
                cmd_results.append({"command": formatted, "ran": False})
            else:
                result = _run_cmd(cmd)
                result["command"] = formatted
                result["ran"] = True
                cmd_results.append(result)
                if not result["ok"]:
                    all_ok = False

        entry["commands"] = cmd_results
        entry["status"] = "dry_run" if dry_run else ("ok" if all_ok else "failed")
        steps_out.append(entry)
        if not dry_run and not all_ok:
            break

    return {
        "ok": dry_run or all_ok,
        "mode": "dry_run" if dry_run else "execute",
        "ticket_id": ticket_id,
        "artifact_dir": _rel(artifact_dir),
        "runbook": "docs/wave_c/WC_T7_e2e_walkthrough_runbook.md",
        "steps": steps_out,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="WC-T7 Control Plane M2 E2E walkthrough runner (demo tickets only).",
    )
    parser.add_argument(
        "--ticket",
        default="WC-DEMO-1",
        help="Demo ticket id (must start with WC-DEMO-)",
    )
    parser.add_argument(
        "--artifacts-root",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "e2e",
        help="Isolated artifacts root (must be under artifacts/e2e)",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands only; do not execute or write via subprocess",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Execute CLI steps (demo ticket + artifacts/e2e only)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured result JSON",
    )
    args = parser.parse_args(argv)

    try:
        result = run_walkthrough(
            args.ticket,
            args.artifacts_root,
            dry_run=args.dry_run,
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "message": str(exc)}), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"=== WC-T7 M2 E2E Walkthrough ({result['mode']}) ===")
        print(f"ticket:       {result['ticket_id']}")
        print(f"artifact_dir: {result['artifact_dir']}")
        for step in result["steps"]:
            print(f"\n[{step['step_id']}] {step['title']} — {step['status']}")
            if step.get("note"):
                print(f"  HITL: {step['note']}")
            if step.get("reason"):
                print(f"  skip: {step['reason']}")
            for cmd_entry in step.get("commands") or []:
                print(f"  $ {cmd_entry['command']}")
                if cmd_entry.get("ran") and not cmd_entry.get("ok"):
                    err = (cmd_entry.get("stderr") or "")[:300]
                    if err:
                        print(f"    stderr: {err}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
