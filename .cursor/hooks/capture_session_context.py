#!/usr/bin/env python3
"""beforeSubmitPrompt hook — capture ticket_id from user prompt (fail-open)."""
from __future__ import annotations

import json
import sys

from _lib import (
    get_session_context,
    infer_ticket_id,
    load_lifecycle_config,
    read_stdin_json,
    save_session_context,
    utc_now_iso,
)


def main() -> int:
    try:
        payload = read_stdin_json()
        cfg = load_lifecycle_config()
        prompt = str(payload.get("prompt") or "")
        conversation_id = payload.get("conversation_id") or payload.get("session_id")

        ticket_id, ticket_source = infer_ticket_id(prompt, cfg)
        existing = get_session_context(cfg)

        context = {
            "conversation_id": conversation_id or existing.get("conversation_id"),
            "ticket_id": ticket_id or existing.get("ticket_id"),
            "ticket_source": ticket_source if ticket_id else existing.get("ticket_source", "unknown"),
            "prompt_snippet": prompt[:200],
            "captured_at": utc_now_iso(),
            "hook_event_name": payload.get("hook_event_name") or "beforeSubmitPrompt",
        }
        save_session_context(cfg, context)
    except Exception as exc:  # noqa: BLE001 — fail-open by design
        print(f"[capture_session_context] warning: {exc}", file=sys.stderr)

    print(json.dumps({"continue": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
