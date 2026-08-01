#!/usr/bin/env python3
"""CLI entry for Intake Gate preview/run (P75-G2/G3/G4).

Preview mode computes gate result without writing outbox records.
Run mode writes durable outbox record; with ``--enable-notifications`` emits
``intake.gate_decision`` (best-effort, fail-open).

Upstream entry for PM / integrators — orchestrator S3 also calls the same gate layer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.notification_gateway_v1 import (
    emit_intake_gate_decision_notification,
    is_enabled_via_env,
)
from routing.intake_gate_layer_v1 import evaluate_intake_gate


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Intake Gate (preview/run).")
    parser.add_argument("--task-type", required=True, help="W2 routing catalog task_type")
    parser.add_argument("--case-dir", required=True, help="Repo-relative or absolute case path")
    parser.add_argument(
        "--mode",
        choices=("preview", "run"),
        default="preview",
        help="preview: no outbox write; run: write outbox record (+ optional notify)",
    )
    parser.add_argument(
        "--policy-path",
        default=None,
        help="Optional override path to intake_gate_policy_v1.yaml",
    )
    parser.add_argument(
        "--include-extended-fixtures",
        action="store_true",
        help="Set include_extended_fixtures policy flag (W4-GUARD-01 alignment)",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Print matched policy rules and reason_codes; does not write outbox",
    )
    parser.add_argument(
        "--enable-notifications",
        action="store_true",
        help="Run mode only: emit intake.gate_decision after outbox record (best-effort)",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional outbox root override (gate record + notification sinks)",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--no-v1-fallback", action="store_true")
    return parser


def _explain_text(result: dict) -> str:
    lines = [
        f"decision: {result.get('decision')}",
        f"policy_version: {result.get('policy_version')}",
        f"reason_codes: {result.get('reason_codes')}",
        "matched_policy_rules:",
    ]
    for check in result.get("gate_checks") or []:
        if not isinstance(check, dict):
            continue
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(
            f"  - [{status}] {check.get('rule_id')}: {check.get('detail')}"
        )
    return "\n".join(lines)


def _maybe_emit_gate_notification(
    result: dict,
    *,
    mode: str,
    notifications_enabled: bool,
    outbox_root: str | None,
) -> dict | None:
    if mode != "run" or not notifications_enabled:
        return None
    if not result.get("ok") or not result.get("outbox_record_path"):
        return None

    notify_result = emit_intake_gate_decision_notification(
        result,
        enabled=True,
        repo_root=_REPO_ROOT,
        outbox_root_override=outbox_root,
    )
    if notify_result is None:
        return None
    return {
        "event_type": "intake.gate_decision",
        "ok": notify_result.get("ok"),
        "event_id": notify_result.get("event_id"),
        "path": (notify_result.get("sink_result") or {}).get("path"),
        "message": notify_result.get("message"),
    }


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    flags = {"include_extended_fixtures": bool(args.include_extended_fixtures)}
    notifications_enabled = bool(args.enable_notifications or is_enabled_via_env())

    result = evaluate_intake_gate(
        args.task_type,
        args.case_dir,
        mode=args.mode,
        policy_path=args.policy_path,
        flags=flags,
        use_v1_fallback=not args.no_v1_fallback,
        repo_root=_REPO_ROOT,
        outbox_root_override=args.outbox_root,
    )

    notification = _maybe_emit_gate_notification(
        result,
        mode=args.mode,
        notifications_enabled=notifications_enabled,
        outbox_root=args.outbox_root,
    )

    if args.explain or args.format == "json":
        payload = dict(result)
        if notification is not None:
            payload["notification"] = notification
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(_explain_text(result))
        return 0 if result.get("ok") else 1

    if not result.get("ok"):
        print(result.get("message", "gate evaluation failed"))
        return 1

    print(f"decision: {result.get('decision')}")
    print(f"risk_level: {result.get('risk_level')}")
    print(f"policy_version: {result.get('policy_version')}")
    print(f"reason_codes: {result.get('reason_codes')}")
    if result.get("outbox_record_path"):
        print(f"outbox_record_path: {result.get('outbox_record_path')}")
    if notification is not None:
        print(f"notification: {notification.get('event_type')} ok={notification.get('ok')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
