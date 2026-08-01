#!/usr/bin/env python3
"""CLI for P7.5 Intake Gate local HTTP stub (P75-G7).

Design SSOT: docs/p75-intake-gate-http-stub-v1.md

Modes:
  --once   Evaluate one request without binding a port (default)
  --serve  Loopback HTTP server (POST /api/intake/gate)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from routing.intake_gate_http_stub_v1 import (  # noqa: E402
    DOC_REL,
    GATE_PATH,
    handle_gate_request,
    serve,
)


def _load_body(args: argparse.Namespace) -> Dict[str, Any]:
    if args.request_json:
        path = Path(args.request_json)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("request JSON must be an object")
        return data

    if args.stdin_json:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("stdin JSON must be an object")
        return data

    body: Dict[str, Any] = {
        "task_type": args.task_type,
        "case_dir": args.case_dir,
        "mode": args.mode,
    }
    if args.policy_path:
        body["policy_path"] = args.policy_path
    if args.outbox_root:
        body["outbox_root"] = args.outbox_root
    if args.enable_notifications:
        body["enable_notifications"] = True
    if args.include_extended_fixtures:
        body["include_extended_fixtures"] = True
    if args.no_v1_fallback:
        body["no_v1_fallback"] = True
    return body


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="P75-G7 Intake Gate local HTTP stub (loopback / once).",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start loopback HTTP server (blocks)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="One-shot evaluate without binding a port (default)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Loopback host only")
    parser.add_argument("--port", type=int, default=8765, help="Listen port for --serve")
    parser.add_argument("--task-type", default=None, help="Gate task_type (once mode)")
    parser.add_argument("--case-dir", default=None, help="Gate case_dir (once mode)")
    parser.add_argument(
        "--mode",
        choices=("preview", "run"),
        default="preview",
        help="Gate mode (default: preview)",
    )
    parser.add_argument("--policy-path", default=None)
    parser.add_argument("--outbox-root", default=None)
    parser.add_argument("--enable-notifications", action="store_true")
    parser.add_argument("--include-extended-fixtures", action="store_true")
    parser.add_argument("--no-v1-fallback", action="store_true")
    parser.add_argument("--request-json", default=None, help="Path to request JSON object")
    parser.add_argument(
        "--stdin-json",
        action="store_true",
        help="Read request body from stdin",
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT

    if args.serve:
        serve(
            args.port,
            host=args.host,
            repo_root=repo_root,
            outbox_root_override=args.outbox_root,
        )
        return 0

    # --once (default)
    try:
        if args.request_json or args.stdin_json:
            body = _load_body(args)
        else:
            if not args.task_type or not args.case_dir:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "message": "provide --task-type/--case-dir, --request-json, or --stdin-json",
                            "contract_ref": DOC_REL,
                            "path": GATE_PATH,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 2
            body = _load_body(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "message": str(exc),
                    "contract_ref": DOC_REL,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    _status, payload = handle_gate_request(
        body,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root or body.get("outbox_root"),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
