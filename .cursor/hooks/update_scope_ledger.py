#!/usr/bin/env python3
"""afterFileEdit hook — merge edited files into scope ledger (fail-open)."""
from __future__ import annotations

import sys

from _lib import (
    compile_patterns,
    get_session_context,
    load_lifecycle_config,
    load_scope_ledger,
    merge_file_change,
    path_matches_any,
    read_stdin_json,
    rebuild_by_ticket,
    repo_relative_path,
    resolve_repo_root,
    save_scope_ledger,
    utc_now_iso,
)


def main() -> int:
    try:
        payload = read_stdin_json()
        cfg = load_lifecycle_config()
        repo_root = resolve_repo_root(payload)
        conversation_id = payload.get("conversation_id") or payload.get("session_id") or "unknown"
        generation_id = payload.get("generation_id")
        file_path = str(payload.get("file_path") or "")
        now = utc_now_iso()

        rel_path = repo_relative_path(file_path, repo_root) if file_path else ""
        skip_patterns = compile_patterns(cfg.get("skip_path_patterns") or [])
        skipped = bool(rel_path and path_matches_any(rel_path, skip_patterns))

        session_ctx = get_session_context(cfg)
        ticket_id = session_ctx.get("ticket_id")
        ticket_source = session_ctx.get("ticket_source", "unknown")

        ledger = load_scope_ledger(cfg)
        ledger["current_conversation_id"] = conversation_id
        sessions = ledger.setdefault("sessions", {})
        session = sessions.setdefault(
            conversation_id,
            {
                "ticket_id": ticket_id,
                "ticket_source": ticket_source,
                "started_at": now,
                "last_event_at": now,
                "stop_status": None,
                "files_changed": [],
                "generation_ids": [],
            },
        )

        if ticket_id:
            session["ticket_id"] = ticket_id
            session["ticket_source"] = ticket_source
        session["last_event_at"] = now

        if generation_id:
            gen_ids = session.setdefault("generation_ids", [])
            gen_str = str(generation_id)
            if gen_str not in gen_ids:
                gen_ids.append(gen_str)

        if rel_path:
            merge_file_change(
                session,
                rel_path,
                skipped=skipped,
                hook_name="afterFileEdit",
                now=now,
            )

        rebuild_by_ticket(ledger)
        save_scope_ledger(cfg, ledger)
    except Exception as exc:  # noqa: BLE001 — fail-open by design
        print(f"[update_scope_ledger] warning: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
