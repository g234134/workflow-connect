#!/usr/bin/env python3
"""HITL Checkpoint CLI v1 (W5-T2B) + tabular driver resume (v1.1).

List/review/apply outbox checkpoint decisions, or wire tabular automation
state + unified driver resume for CP-A / CP-B.

Usage:
    python scripts/run_hitl_checkpoint_cli.py --list
    python scripts/run_hitl_checkpoint_cli.py --review --checkpoint-id A-intake-confirmation
    python scripts/run_hitl_checkpoint_cli.py \\
        --apply-decision approve \\
        --checkpoint-id A-intake-confirmation \\
        --notes "LGTM"

    # Tabular unified driver (reads/writes automation_state.json):
    python scripts/run_hitl_checkpoint_cli.py approve-a --case-id demo_phase --json
    python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint \\
        --case-id demo_phase --json
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
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hitl.checkpoints_v1 import (  # noqa: E402
    get_checkpoint,
    list_pending_checkpoints,
    record_human_decision,
    review_summary,
)
from tabular_hitl_resume_lib import (  # noqa: E402
    apply_tabular_checkpoint_decision,
    resolve_case_dir_from_args,
    resume_after_checkpoint,
)

_TABULAR_COMMANDS = frozenset(
    {"approve-a", "reject-a", "approve-b", "reject-b", "resume-after-checkpoint"}
)


def _format_list_text(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No pending checkpoints."
    lines = ["Pending checkpoints:"]
    for row in rows:
        lines.append(
            "  - case_ref={case_ref} checkpoint_id={checkpoint_id} "
            "type={type} created_at={created_at}".format(**row)
        )
    return "\n".join(lines)


def _format_review_text(summary: dict[str, Any]) -> str:
    lines = [
        "HITL Checkpoint Review (W5-T2B)",
        f"checkpoint_id: {summary.get('checkpoint_id')}",
        f"case_ref: {summary.get('case_ref')}",
        f"status: {summary.get('status')}",
        f"task_type: {summary.get('task_type', '')}",
    ]

    if summary.get("decision") is not None:
        lines.append(f"decision: {summary.get('decision')}")
    if summary.get("risk_level") is not None:
        lines.append(f"risk_level: {summary.get('risk_level')}")

    risk_signals = summary.get("risk_signals") or []
    if risk_signals:
        lines.append("risk_signals:")
        for sig in risk_signals:
            lines.append(f"  - {sig}")

    output_guard = summary.get("output_guard") or {}
    if output_guard:
        lines.append("output_guard:")
        for key, value in output_guard.items():
            lines.append(f"  {key}: {value}")

    planned = summary.get("planned_tools") or []
    if planned:
        lines.append("planned_tools:")
        for tool_id in planned:
            lines.append(f"  - {tool_id}")

    draft = summary.get("delivery_draft") or {}
    if draft:
        lines.append(f"delivery_draft.summary_text: {draft.get('summary_text', '')}")

    actions = summary.get("suggested_actions") or []
    lines.append("suggested_actions:")
    for action in actions:
        lines.append(f"  - {action}")

    return "\n".join(lines)


def _print_result(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"ok={result.get('ok')} command={result.get('command')} "
            f"message={result.get('message', '')}"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))


def _run_tabular_command(args: argparse.Namespace, command: str) -> int:
    case_dir = resolve_case_dir_from_args(case_id=args.case_id, case_dir=args.case_dir)
    if case_dir is None:
        result = {
            "ok": False,
            "command": command,
            "message": f"case not found for case_id={args.case_id!r}",
        }
        _print_result(result, as_json=args.json)
        return 1

    if command == "resume-after-checkpoint":
        result = resume_after_checkpoint(
            case_dir,
            requested_by=args.operator_id,
            force=args.force,
            dry_run=args.dry_run,
        )
    else:
        result = apply_tabular_checkpoint_decision(
            case_dir,
            command=command,
            operator_id=args.operator_id,
            notes=args.notes,
            outbox_root_override=args.outbox_root,
        )

    _print_result(result, as_json=args.json)
    return 0 if result.get("ok") else 1


def _main_tabular(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Tabular HITL checkpoint resume CLI.")
    parser.add_argument(
        "command",
        choices=sorted(_TABULAR_COMMANDS),
        help="Tabular checkpoint action",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--case-id", help="Case id (e.g. demo_phase)")
    target.add_argument("--case-dir", type=Path, help="Explicit case directory")
    parser.add_argument("--notes", default="", help="Operator notes")
    parser.add_argument(
        "--operator-id",
        default="operator_cli",
        help="Operator id for approve/reject",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional outbox root override",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Pass --force to unified driver on resume",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="resume-after-checkpoint: plan only",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args(argv)
    return _run_tabular_command(args, args.command)


def _main_outbox(argv: list[str] | None) -> int:
    parser = argparse.ArgumentParser(
        description="HITL checkpoint admin CLI (W5-T2B outbox layer).",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional outbox root override (repo-relative or absolute)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List pending checkpoints")
    group.add_argument(
        "--review",
        action="store_true",
        help="Load and display checkpoint summary",
    )
    group.add_argument(
        "--apply-decision",
        metavar="ACTION",
        help="Record human decision and emit resume_context (outbox only)",
    )

    parser.add_argument(
        "--checkpoint-id",
        help="Checkpoint id (required for --review and --apply-decision)",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional operator notes for --apply-decision",
    )
    parser.add_argument(
        "--operator-id",
        default="operator_cli",
        help="Operator id recorded on human_decision",
    )

    args = parser.parse_args(argv)
    extra = {"outbox_root_override": args.outbox_root} if args.outbox_root else {}

    if args.list:
        rows = list_pending_checkpoints(**extra)
        if args.format == "json":
            print(json.dumps({"ok": True, "pending": rows}, ensure_ascii=False, indent=2))
        else:
            print(_format_list_text(rows))
        return 0

    if not args.checkpoint_id:
        print("error: --checkpoint-id is required", file=sys.stderr)
        return 2

    if args.review:
        checkpoint = get_checkpoint(args.checkpoint_id, pending_only=False, **extra)
        if checkpoint is None:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "message": f"checkpoint not found: {args.checkpoint_id}",
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 1
        summary = review_summary(checkpoint)
        if args.format == "json":
            print(json.dumps({"ok": True, "summary": summary}, ensure_ascii=False, indent=2))
        else:
            print(_format_review_text(summary))
        return 0

    if args.apply_decision:
        try:
            resume_context = record_human_decision(
                args.checkpoint_id,
                args.apply_decision,
                args.notes,
                operator_id=args.operator_id,
                **extra,
            )
        except ValueError as exc:
            print(
                json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False),
                file=sys.stderr,
            )
            return 1
        payload = {"ok": True, "resume_context": resume_context}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    return 2


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in _TABULAR_COMMANDS:
        return _main_tabular(argv)
    return _main_outbox(argv)


if __name__ == "__main__":
    raise SystemExit(main())
