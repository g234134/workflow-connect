#!/usr/bin/env python3
"""Delivery approval one-click CLI v1 (W8-T3).

Integrates signoff / output_guard review with Checkpoint B human decision and
optional controlled notify experiment. Preview by default; --confirm required
to persist decisions. Never calls external notification gateways.

Usage:
    python scripts/run_delivery_approval_cli.py \\
        --case-dir cases/demo_phase \\
        --checkpoint-id B-delivery-confirmation \\
        --action approve \\
        --notes "LGTM"

    python scripts/run_delivery_approval_cli.py \\
        --case-dir cases/demo_phase \\
        --action approve --confirm \\
        --with-notify-experiment --no-notify-dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.delivery_approval_cli_v1 import run_delivery_approval
from hitl.checkpoints_v1 import CHECKPOINT_B_ID


def _format_review_text(result: Dict[str, Any]) -> str:
    review = result.get("review_summary") or {}
    signoff = review.get("delivery_signoff") or {}
    guard = review.get("output_guard") or {}
    metrics = review.get("metrics") or {}

    lines = [
        "Delivery Approval Review (W8-T3 one-click CLI)",
        f"case_ref: {review.get('case_ref')}",
        f"case_dir: {review.get('case_dir')}",
        "",
        "--- delivery_signoff ---",
        f"path: {signoff.get('path')}",
    ]
    fields = signoff.get("fields") or {}
    for key in ("case_id", "client_ref", "job_id", "lead_approval"):
        if key in fields:
            lines.append(f"  {key}: {fields[key]}")

    lines.extend(
        [
            "",
            "--- output_guard ---",
            f"status: {guard.get('status')}",
        ]
    )
    if guard.get("ratio") is not None:
        lines.append(f"ratio: {guard.get('ratio')}")
    if guard.get("threshold") is not None:
        lines.append(f"threshold: {guard.get('threshold')}")

    lines.extend(
        [
            "",
            "--- metrics ---",
            f"input_rows: {metrics.get('input_rows')}",
            f"output_rows: {metrics.get('output_rows')}",
            f"removed_rows: {metrics.get('removed_rows')}",
            f"removal_ratio: {metrics.get('removal_ratio')}",
            f"qa_status: {metrics.get('qa_status')}",
            "",
            f"checkpoint_id: {result.get('checkpoint_id')}",
            f"checkpoint_status: {result.get('checkpoint_status')}",
            f"action: {result.get('action')} -> {result.get('internal_action')}",
            f"confirmed: {result.get('confirmed')}",
        ]
    )

    if not result.get("confirmed"):
        lines.append("")
        lines.append("PREVIEW ONLY — re-run with --confirm to record human decision.")

    delivery_plan = result.get("delivery_plan")
    if delivery_plan:
        lines.extend(
            [
                "",
                "--- delivery_plan ---",
                f"action: {delivery_plan.get('action')}",
                f"resume_from: {delivery_plan.get('resume_from')}",
                f"proceed_to_delivery: {delivery_plan.get('proceed_to_delivery')}",
                f"update_case_status: {delivery_plan.get('update_case_status')}",
            ]
        )

    notify = result.get("notify_experiment")
    if notify and not notify.get("skipped"):
        lines.extend(
            [
                "",
                "--- notify_experiment (simulated) ---",
                f"dry_run: {notify.get('dry_run')}",
                f"external_dispatch: {notify.get('external_dispatch')}",
                f"outbox_path: {notify.get('outbox_path')}",
            ]
        )

    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One-click delivery approval CLI (Checkpoint B + optional notify experiment)",
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        help="Case directory under cases/ (e.g. cases/demo_phase)",
    )
    parser.add_argument(
        "--checkpoint-id",
        default=CHECKPOINT_B_ID,
        help=f"Checkpoint id (default: {CHECKPOINT_B_ID})",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=("approve", "request_changes", "hold"),
        help="Human decision shorthand",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Operator notes recorded on human_decision",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Persist human decision (default: preview only)",
    )
    parser.add_argument(
        "--revise-target",
        choices=("cleaning", "bundle"),
        default=None,
        help="For request_changes: re-run from cleaning or bundle (default: cleaning)",
    )
    parser.add_argument(
        "--with-notify-experiment",
        action="store_true",
        help="After approve, call controlled notify experiment (simulated only)",
    )
    parser.add_argument(
        "--notify-dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="When notify experiment runs, skip outbox write (default: true)",
    )
    parser.add_argument(
        "--operator-id",
        default="operator_cli",
        help="Operator id on human_decision",
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
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    extra: Dict[str, Any] = {"repo_root": _REPO_ROOT}
    if args.outbox_root:
        extra["outbox_root_override"] = args.outbox_root

    result = run_delivery_approval(
        args.case_dir,
        args.checkpoint_id,
        args.action,
        args.notes,
        confirm=args.confirm,
        revise_target=args.revise_target,
        operator_id=args.operator_id,
        run_notify_experiment=args.with_notify_experiment,
        notify_dry_run=args.notify_dry_run,
        **extra,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_review_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
