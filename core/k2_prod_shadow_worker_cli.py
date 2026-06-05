"""
CLI for K-2 prod shadow worker (subprocess entry from gov_core ``/api/ask`` hook).

Usage::

    python -m core.k2_prod_shadow_worker_cli /path/to/payload.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_payload(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="K-2 prod shadow worker (Phase 1)")
    parser.add_argument(
        "payload_path",
        type=str,
        help="JSON file path, or '-' to read payload from stdin",
    )
    args = parser.parse_args(argv)

    if args.payload_path == "-":
        raw = sys.stdin.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
    else:
        payload = _load_payload(Path(args.payload_path))
    ask_snapshot = payload.get("ask_snapshot")
    if not isinstance(ask_snapshot, dict):
        print(json.dumps({"ok": False, "message": "missing ask_snapshot object"}))
        return 1

    query = str(payload.get("query") or "")
    top_k = int(payload.get("top_k") or 3)
    thread_id = payload.get("thread_id")
    session_id = payload.get("session_id")
    spool_path_raw = payload.get("spool_path")
    spool_path = Path(spool_path_raw) if spool_path_raw else None

    from core.k2_prod_shadow_worker import execute_prod_shadow_from_ask

    try:
        result = execute_prod_shadow_from_ask(
            ask_snapshot,
            query=query,
            top_k=top_k,
            thread_id=str(thread_id) if thread_id else None,
            session_id=str(session_id) if session_id else None,
            spool_path=spool_path,
        )
    except Exception as exc:  # noqa: BLE001 — worker boundary
        print(json.dumps({"ok": False, "message": f"shadow worker failed: {exc}"}))
        return 1

    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
