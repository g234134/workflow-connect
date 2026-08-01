#!/usr/bin/env python3
"""P8-T3 notify webhook mock CLI — local probe only (≠ prod HTTP).

Usage:
    python scripts/run_p8_notify_webhook_mock_v1.py dispatch --case-ref demo_phase
    python scripts/run_p8_notify_webhook_mock_v1.py dispatch --case-ref demo_phase --force-fail
    python scripts/run_p8_notify_webhook_mock_v1.py list-dlq --format json
    python scripts/run_p8_notify_webhook_mock_v1.py replay --event-id <id> --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.p8_notify_webhook_mock_v1 import (  # noqa: E402
    list_dlq,
    mock_dispatch_bundle_ready,
    replay_dlq_event,
)


def _print(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"ok={result.get('ok')} message={result.get('message', '')} "
            f"external_http={result.get('external_http')}"
        )


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
    )
    p.add_argument("--repo-root", default=None)
    p.add_argument("--dlq-path", default=None, help="Override DLQ jsonl path")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="P8 notify webhook mock / DLQ replay (local probe · ≠ prod)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_dispatch = sub.add_parser("dispatch", help="Mock delivery.bundle_ready dispatch")
    _add_common(p_dispatch)
    p_dispatch.add_argument("--case-ref", required=True)
    p_dispatch.add_argument("--client-summary", default="")
    p_dispatch.add_argument(
        "--force-fail",
        action="store_true",
        help="Force retry exhaustion → DLQ",
    )
    p_dispatch.add_argument(
        "--mode",
        default="mock",
        help="Only 'mock' allowed (live fail-closes)",
    )

    p_list = sub.add_parser("list-dlq", help="List mock DLQ rows")
    _add_common(p_list)
    p_list.add_argument("--case-ref", default=None)

    p_replay = sub.add_parser("replay", help="Replay one DLQ event (mock sink)")
    _add_common(p_replay)
    p_replay.add_argument("--event-id", required=True)
    p_replay.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Preview only (default: true)",
    )
    p_replay.add_argument("--mode", default="mock")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root) if args.repo_root else None
    as_json = args.format == "json"
    common = {
        "repo_root": repo_root,
        "dlq_path_override": args.dlq_path,
    }

    if args.command == "dispatch":
        result = mock_dispatch_bundle_ready(
            case_ref=args.case_ref,
            client_summary=args.client_summary,
            force_fail=args.force_fail,
            mode=args.mode,
            **common,
        )
    elif args.command == "list-dlq":
        result = list_dlq(case_ref=args.case_ref, **common)
    elif args.command == "replay":
        result = replay_dlq_event(
            event_id=args.event_id,
            dry_run=args.dry_run,
            mode=args.mode,
            **common,
        )
    else:
        result = {"ok": False, "message": f"unknown command: {args.command}"}

    _print(result, as_json=as_json)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
