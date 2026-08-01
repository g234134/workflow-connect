#!/usr/bin/env python3
"""P4 dispatch replay min v1 — same_chat dispatch suggestion + O→B→C→D checklist.

Ticket: P4-DISPATCH-REPLAY-MIN-v1
Design: docs/p4-dispatch-replay-min-v1.md

Reuses existing read-only `dispatch_executor` (no prod crew / no chat spawn).

Usage:
    python scripts/run_p4_dispatch_replay_min_v1.py --ticket-id P4-MULTI-CHAT-SMOKE-PACK-v1 --pretty
    python scripts/run_p4_dispatch_replay_min_v1.py --ticket-id P4-MULTI-CHAT-SMOKE-PACK-v1 --format text
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from dispatch_executor import build_dispatch_plan  # noqa: E402

_SCHEMA_VERSION = "p4_dispatch_replay_min_v1"
_DOC_REL = "docs/p4-dispatch-replay-min-v1.md"
_REPLAY_SEQUENCE = (
    {"step": 1, "role": "orchestrator", "code": "O", "action": "freeze FRAME + STATE"},
    {"step": 2, "role": "implementer", "code": "B", "action": "implement + B_REPORT"},
    {"step": 3, "role": "reviewer", "code": "C", "action": "read-only AC + C_REPORT"},
    {"step": 4, "role": "scribe", "code": "D", "action": "D_REPORT + Progress append"},
)
_NON_CLAIMS = (
    "≠ prod multi-agent runtime",
    "≠ crewai / langchain in gov_main",
    "≠ auto-spawn Cursor chats",
    "≠ Dashboard Phase% apply",
)


def _find_suggestion(plan: dict[str, Any], ticket_id: str) -> dict[str, Any] | None:
    tid = ticket_id.strip()
    for row in plan.get("suggested_next") or []:
        if str(row.get("ticket_id", "")).strip() == tid:
            return row
    for bucket in ("runnable_now", "in_review", "blocked", "done", "draft"):
        for row in plan.get(bucket) or []:
            if str(row.get("ticket_id", "")).strip() == tid:
                return {
                    "ticket_id": tid,
                    "recommended_role": row.get("current_owner"),
                    "reason": f"bucket={bucket}; no role suggestion row",
                    "bucket": bucket,
                    "commands": [],
                    "blocked_by": row.get("blockers") or [],
                    "can_parallelize": False,
                }
    return None


def _find_ticket_row(plan: dict[str, Any], ticket_id: str) -> dict[str, Any] | None:
    tid = ticket_id.strip()
    for bucket in ("runnable_now", "in_review", "blocked", "done", "draft"):
        for row in plan.get(bucket) or []:
            if str(row.get("ticket_id", "")).strip() == tid:
                out = dict(row)
                out["bucket"] = bucket
                return out
    return None


def build_dispatch_replay_min(
    *,
    ticket_id: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Return structured dispatch+replay dict for one ticket (read-only)."""
    root = repo_root or _REPO_ROOT
    tid = (ticket_id or "").strip()
    if not tid:
        return {
            "ok": False,
            "schema_version": _SCHEMA_VERSION,
            "message": "ticket_id required",
            "non_claims": list(_NON_CLAIMS),
            "doc": _DOC_REL,
        }

    plan = build_dispatch_plan(root, ticket_filter=tid)
    suggestion = _find_suggestion(plan, tid)
    ticket_row = _find_ticket_row(plan, tid)

    if suggestion is None and ticket_row is None:
        return {
            "ok": False,
            "schema_version": _SCHEMA_VERSION,
            "ticket_id": tid,
            "message": f"ticket not found under filter={tid!r}",
            "dispatch_ok": bool(plan.get("ok")),
            "tickets_scanned": plan.get("tickets_scanned", 0),
            "warnings": plan.get("warnings") or [],
            "non_claims": list(_NON_CLAIMS),
            "doc": _DOC_REL,
        }

    recommended_role = (suggestion or {}).get("recommended_role")
    overall_status = (ticket_row or {}).get("overall_status")
    next_action = (ticket_row or {}).get("next_action")
    current_owner = (ticket_row or {}).get("current_owner")
    bucket = (suggestion or ticket_row or {}).get("bucket")

    return {
        "ok": True,
        "schema_version": _SCHEMA_VERSION,
        "mode": "dispatch_replay_min",
        "ticket_id": tid,
        "overall_status": overall_status,
        "current_owner": current_owner,
        "next_action": next_action,
        "bucket": bucket,
        "recommended_role": recommended_role,
        "reason": (suggestion or {}).get("reason"),
        "commands": (suggestion or {}).get("commands") or [],
        "blocked_by": (suggestion or {}).get("blocked_by") or [],
        "replay_sequence": list(_REPLAY_SEQUENCE),
        "dispatch_ok": bool(plan.get("ok")),
        "tickets_scanned": plan.get("tickets_scanned", 0),
        "warnings": plan.get("warnings") or [],
        "message": (
            f"replay min ready · recommended_role={recommended_role} · "
            f"status={overall_status}"
        ),
        "non_claims": list(_NON_CLAIMS),
        "doc": _DOC_REL,
        "apply_phase_pct": False,
    }


def _format_text(result: dict[str, Any]) -> str:
    lines = [
        f"ok: {result.get('ok')}",
        f"ticket_id: {result.get('ticket_id')}",
        f"overall_status: {result.get('overall_status')}",
        f"recommended_role: {result.get('recommended_role')}",
        f"next_action: {result.get('next_action')}",
        f"message: {result.get('message')}",
        "replay_sequence: O → B → C → D",
    ]
    for step in result.get("replay_sequence") or []:
        lines.append(
            f"  {step.get('step')}. [{step.get('code')}] {step.get('role')}: {step.get('action')}"
        )
    lines.append("non_claims:")
    for claim in result.get("non_claims") or []:
        lines.append(f"  - {claim}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P4 dispatch replay min — read-only role suggestion + O→B→C→D checklist",
    )
    parser.add_argument(
        "--ticket-id",
        required=True,
        help="Ticket id substring / exact id (passed to dispatch filter)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="stdout format (default json)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON",
    )
    args = parser.parse_args(argv)

    result = build_dispatch_replay_min(ticket_id=args.ticket_id)
    if args.format == "text":
        sys.stdout.write(_format_text(result))
    else:
        indent = 2 if args.pretty else None
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=indent) + "\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
