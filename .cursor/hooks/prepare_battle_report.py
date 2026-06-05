#!/usr/bin/env python3
"""stop hook — prepare lightweight battle report draft (fail-open, no append)."""
from __future__ import annotations

import sys

from _lib import (
    build_battle_report_draft,
    get_session_context,
    load_lifecycle_config,
    load_scope_ledger,
    load_subagent_artifact,
    read_stdin_json,
    rebuild_by_ticket,
    save_scope_ledger,
    ticket_is_eligible,
    utc_now_iso,
    write_battle_report_drafts,
)


def main() -> int:
    try:
        payload = read_stdin_json()
        cfg = load_lifecycle_config()
        conversation_id = str(payload.get("conversation_id") or payload.get("session_id") or "unknown")
        stop_status = str(payload.get("status") or "completed")

        session_ctx = get_session_context(cfg)
        ledger = load_scope_ledger(cfg)
        session = (ledger.get("sessions") or {}).get(conversation_id) or {}
        ticket_id = session.get("ticket_id") or session_ctx.get("ticket_id")

        if session:
            session["stop_status"] = stop_status
            session["last_event_at"] = utc_now_iso()
            ledger.setdefault("sessions", {})[conversation_id] = session
            rebuild_by_ticket(ledger)
            save_scope_ledger(cfg, ledger)

        if not ticket_is_eligible(ticket_id, cfg):
            print(
                f"[prepare_battle_report] skip: ticket_id={ticket_id!r} not eligible",
                file=sys.stderr,
            )
            return 0

        ledger_files = [
            e.get("path")
            for e in (session.get("files_changed") or [])
            if e.get("path") and not e.get("skipped")
        ]

        implementation = load_subagent_artifact(cfg, str(ticket_id), "implementation")
        checker = load_subagent_artifact(cfg, str(ticket_id), "checker")

        draft = build_battle_report_draft(
            cfg=cfg,
            ticket_id=str(ticket_id),
            conversation_id=conversation_id,
            stop_status=stop_status,
            ledger_files=ledger_files,
            implementation=implementation,
            checker=checker,
        )
        write_battle_report_drafts(cfg, str(ticket_id), conversation_id, draft)
    except Exception as exc:  # noqa: BLE001 — fail-open by design
        print(f"[prepare_battle_report] warning: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
