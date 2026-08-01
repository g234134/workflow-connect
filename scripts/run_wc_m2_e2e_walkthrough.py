#!/usr/bin/env python3
"""Control Plane M2 E2E walkthrough runner (WC-T7 skeleton).

Orchestrates CLI steps from docs/wave_c/WC_T7_e2e_walkthrough_runbook.md.
Manual STATE edits (§1 setup, §3/§4 HITL) are printed, not automated.

Usage:
    python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run
    python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute
    python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures
    python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures --include-payment
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ALLOWED_TICKET_PREFIX = "WC-DEMO-"
_REQUIRED_ARTIFACTS_PREFIX = "artifacts/e2e"
_HITL_FIXTURES_DIR = _REPO_ROOT / "tests" / "fixtures" / "e2e_walkthrough"
_HITL_FIXTURE_MAP = {
    "before_review.md": "{ticket_id}_before_review.md",
    "state_review.md": "{ticket_id}_state_review.md",
    "state_ready_for_order.md": "{ticket_id}_state_ready_for_order.md",
}


@dataclass(frozen=True)
class CommandSpec:
    cmd: list[str]
    env_patch: dict[str, str] | None = None


@dataclass(frozen=True)
class Step:
    step_id: str
    title: str
    commands: tuple[CommandSpec, ...]
    hitl_note: str | None = None
    skip_unless: str | None = None  # path relative to repo root; step skipped if missing
    skip_unless_only_execute: bool = True  # when False, dry-run still previews step


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


def materialize_hitl_fixtures(ticket_id: str, artifact_dir: Path) -> dict[str, str]:
    """Copy pre-recorded HITL snapshots from tests/fixtures into artifact_dir."""
    materialized: dict[str, str] = {}
    for dest_name, src_pattern in _HITL_FIXTURE_MAP.items():
        src_name = src_pattern.format(ticket_id=ticket_id)
        src = _HITL_FIXTURES_DIR / src_name
        if not src.is_file():
            raise ValueError(
                f"missing HITL fixture {src_name!r} under "
                f"{_rel(_HITL_FIXTURES_DIR)}/; cannot use --use-hitl-fixtures"
            )
        dest = artifact_dir / dest_name
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        materialized[dest_name] = _rel(dest)
    return materialized


def build_steps(
    ticket_id: str,
    artifact_dir: Path,
    *,
    use_hitl_fixtures: bool = False,
    include_payment: bool = False,
) -> list[Step]:
    cards_dir = artifact_dir / "cards"
    comms_dir = artifact_dir / "comms"
    orders_jsonl = artifact_dir / "orders.jsonl"
    before_review = artifact_dir / "before_review.md"
    ticket_state = _REPO_ROOT / "04_Workflows" / "tickets" / f"{ticket_id}_state.md"
    state_review = artifact_dir / "state_review.md"
    state_ready_for_order = artifact_dir / "state_ready_for_order.md"
    comms_after = state_review if use_hitl_fixtures else ticket_state
    order_ticket_path = state_ready_for_order if use_hitl_fixtures else None
    order_id = f"ORD-{ticket_id}"
    py = sys.executable
    order_intake = _REPO_ROOT / "scripts" / "run_order_intake.py"

    order_create_cmd = [
        py, str(order_intake),
        "--jsonl-path", _rel(orders_jsonl),
        "create", "--ticket", ticket_id,
        "--amount-minor", "10000", "--currency", "TWD",
    ]
    if order_ticket_path is not None:
        order_create_cmd.extend(["--ticket-path", _rel(order_ticket_path)])

    steps: list[Step] = [
        Step(
            "0",
            "Environment check",
            (
                CommandSpec(
                    cmd=[
                        py, str(_REPO_ROOT / "scripts" / "run_ticket_eligibility.py"),
                        "--ticket", ticket_id, "--requested-role", "implementer", "--format", "json",
                    ],
                ),
            ),
            skip_unless=_rel(ticket_state),
        ),
        Step(
            "2",
            "Dispatch cards + eligibility gate",
            (
                CommandSpec(
                    cmd=[
                        py, str(_REPO_ROOT / "scripts" / "run_dispatch_cards.py"),
                        "--refresh-plan", "--ticket", ticket_id, "--role", "implementer",
                        "--eligibility-gate", "block",
                        "--out-dir", _rel(cards_dir) + "/",
                        "--json-summary", _rel(artifact_dir / "dispatch_cards_run.json"),
                        "--pretty",
                    ],
                ),
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
                CommandSpec(
                    cmd=[
                        py, str(_REPO_ROOT / "scripts" / "run_ticket_state_update_with_comms.py"),
                        "--before", _rel(before_review),
                        "--after", _rel(comms_after),
                        "--outbox-dir", _rel(comms_dir),
                    ],
                ),
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
                CommandSpec(cmd=order_create_cmd),
                CommandSpec(
                    cmd=[
                        py, str(order_intake),
                        "--jsonl-path", _rel(orders_jsonl),
                        "lookup", "--ticket-id", ticket_id,
                    ],
                ),
                CommandSpec(cmd=list(order_create_cmd)),
            ),
            skip_unless=_rel(state_ready_for_order if use_hitl_fixtures else ticket_state),
        ),
    ]

    if include_payment:
        steps.append(
            Step(
                "6-payment",
                "Sandbox payment: transition → pay → PAID lookup (WC-M3 §4.2 · demo only)",
                (
                    CommandSpec(
                        cmd=[
                            py, str(order_intake),
                            "--jsonl-path", _rel(orders_jsonl),
                            "transition", "--order-id", order_id,
                            "--to", "pending_payment",
                            "--actor", "m2-walkthrough",
                            "--reason", "sandbox_execute",
                        ],
                    ),
                    CommandSpec(
                        cmd=[
                            py, str(order_intake),
                            "--jsonl-path", _rel(orders_jsonl),
                            "pay", "--order-id", order_id,
                        ],
                        env_patch={"GOV_PAYMENT_SANDBOX_ENABLED": "1"},
                    ),
                    CommandSpec(
                        cmd=[
                            py, str(order_intake),
                            "--jsonl-path", _rel(orders_jsonl),
                            "lookup", "--order-id", order_id,
                        ],
                    ),
                ),
                skip_unless=_rel(orders_jsonl),
                skip_unless_only_execute=False,
            ),
        )

    steps.append(
        Step(
            "5",
            "Module unittest cross-check",
            (
                CommandSpec(
                    cmd=[
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
        ),
    )
    return steps


def _format_cmd(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def _run_cmd(cmd: list[str], *, env_patch: dict[str, str] | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    if env_patch:
        env.update(env_patch)
    proc = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
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
    use_hitl_fixtures: bool = False,
    include_payment: bool = False,
) -> dict[str, Any]:
    _validate_ticket(ticket_id)
    root = _validate_artifacts_root(artifacts_root)
    artifact_dir = root / ticket_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    hitl_fixtures: dict[str, str] | None = None
    if use_hitl_fixtures:
        if dry_run:
            raise ValueError(
                "--use-hitl-fixtures requires --execute (fixture materialization writes "
                "to artifacts/e2e/<ticket>/ only; does not modify live *_state.md)"
            )
        hitl_fixtures = materialize_hitl_fixtures(ticket_id, artifact_dir)

    steps_out: list[dict[str, Any]] = []
    all_ok = True
    final_order_status: str | None = None

    for step in build_steps(
        ticket_id,
        artifact_dir,
        use_hitl_fixtures=use_hitl_fixtures,
        include_payment=include_payment,
    ):
        entry: dict[str, Any] = {
            "step_id": step.step_id,
            "title": step.title,
            "status": "pending",
        }

        if step.skip_unless:
            check_path = _REPO_ROOT / step.skip_unless
            missing_prereq = not check_path.is_file()
            if missing_prereq and (not dry_run or step.skip_unless_only_execute):
                entry["status"] = "skipped"
                entry["reason"] = f"missing prerequisite: {step.skip_unless}"
                steps_out.append(entry)
                continue

        if step.hitl_note:
            if use_hitl_fixtures:
                entry["status"] = "fixture"
                entry["note"] = (
                    "Skipped manual HITL; pre-recorded snapshots materialized from "
                    f"{_rel(_HITL_FIXTURES_DIR)}/"
                )
            else:
                entry["status"] = "hitl"
                entry["note"] = step.hitl_note
            steps_out.append(entry)
            continue

        cmd_results: list[dict[str, Any]] = []
        step_ok = True
        for spec in step.commands:
            formatted = _format_cmd(spec.cmd)
            cmd_entry: dict[str, Any] = {"command": formatted, "ran": False}
            if spec.env_patch:
                cmd_entry["env"] = dict(spec.env_patch)
            if dry_run:
                cmd_results.append(cmd_entry)
            else:
                result = _run_cmd(spec.cmd, env_patch=spec.env_patch)
                result["command"] = formatted
                result["ran"] = True
                if spec.env_patch:
                    result["env"] = dict(spec.env_patch)
                cmd_results.append(result)
                if not result["ok"]:
                    step_ok = False
                    all_ok = False
                elif (
                    step.step_id == "6-payment"
                    and "lookup" in spec.cmd
                    and result.get("stdout")
                ):
                    try:
                        lookup_payload = json.loads(result["stdout"])
                        order = lookup_payload.get("order") or {}
                        final_order_status = order.get("order_status")
                    except json.JSONDecodeError:
                        pass

        entry["commands"] = cmd_results
        if dry_run:
            entry["status"] = "dry_run"
        elif step_ok:
            entry["status"] = "ok"
        else:
            entry["status"] = "failed"
        steps_out.append(entry)
        if not dry_run and not all_ok:
            break

    result: dict[str, Any] = {
        "ok": dry_run or all_ok,
        "mode": "dry_run" if dry_run else "execute",
        "ticket_id": ticket_id,
        "artifact_dir": _rel(artifact_dir),
        "runbook": "docs/wave_c/WC_T7_e2e_walkthrough_runbook.md",
        "steps": steps_out,
    }
    if include_payment:
        result["include_payment"] = True
    if final_order_status is not None:
        result["order_status"] = final_order_status
    if hitl_fixtures is not None:
        result["hitl_fixtures"] = hitl_fixtures
        result["use_hitl_fixtures"] = True
    return result


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
    parser.add_argument(
        "--use-hitl-fixtures",
        action="store_true",
        help=(
            "With --execute: materialize pre-recorded HITL snapshots from "
            "tests/fixtures/e2e_walkthrough/ into artifact_dir; skip manual STATE edits"
        ),
    )
    parser.add_argument(
        "--include-payment",
        action="store_true",
        help=(
            "Append step 6-payment (transition → sandbox pay → PAID lookup) after order "
            "create; demo/sandbox only (WC-DEMO-* + artifacts/e2e); injects "
            "GOV_PAYMENT_SANDBOX_ENABLED=1 for pay subprocess only"
        ),
    )
    args = parser.parse_args(argv)

    if args.use_hitl_fixtures and args.dry_run:
        print(
            json.dumps(
                {
                    "ok": False,
                    "message": "--use-hitl-fixtures requires --execute",
                }
            ),
            file=sys.stderr,
        )
        return 2

    try:
        result = run_walkthrough(
            args.ticket,
            args.artifacts_root,
            dry_run=args.dry_run,
            use_hitl_fixtures=args.use_hitl_fixtures,
            include_payment=args.include_payment,
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
