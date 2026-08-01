#!/usr/bin/env python3
"""P8 notify webhook v1 CLI — sandbox / staging / prod via P7 adapter.

Usage:
    python scripts/run_p8_notify_webhook_v1.py readiness --tier staging
    python scripts/run_p8_notify_webhook_v1.py dispatch --case-ref demo_phase --tier sandbox
    python scripts/run_p8_notify_webhook_v1.py list-dlq --format json

Does not print secret values. Staging/prod require env gates (see docs).
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

from delivery.p8_notify_webhook_v1 import (  # noqa: E402
    dispatch_bundle_ready,
    list_dlq,
    staging_prod_readiness_check,
)


def _print(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"ok={result.get('ok')} message={result.get('message', '')} "
            f"external_http={result.get('external_http')} tier={result.get('tier')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P8 notify webhook (sandbox/staging/prod · P7 adapter)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ready = sub.add_parser("readiness", help="Check staging/prod env gates (booleans)")
    p_ready.add_argument("--tier", choices=("staging", "prod"), default="staging")
    p_ready.add_argument("--format", choices=("json", "text"), default="json")

    p_dispatch = sub.add_parser("dispatch", help="Dispatch delivery.bundle_ready")
    p_dispatch.add_argument("--case-ref", required=True)
    p_dispatch.add_argument("--client-summary", default="")
    p_dispatch.add_argument(
        "--tier",
        choices=("sandbox", "staging", "prod"),
        default="sandbox",
    )
    p_dispatch.add_argument("--endpoint-url", default=None)
    p_dispatch.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    p_dispatch.add_argument("--format", choices=("json", "text"), default="json")

    p_list = sub.add_parser("list-dlq", help="List P7 notification DLQ rows")
    p_list.add_argument("--case-ref", default=None)
    p_list.add_argument("--dlq-path", default=None)
    p_list.add_argument("--repo-root", default=None)
    p_list.add_argument("--format", choices=("json", "text"), default="json")

    args = parser.parse_args(argv)
    as_json = args.format == "json"

    if args.command == "readiness":
        result = staging_prod_readiness_check(tier=args.tier)
    elif args.command == "dispatch":
        result = dispatch_bundle_ready(
            case_ref=args.case_ref,
            client_summary=args.client_summary,
            tier=args.tier,
            dry_run=args.dry_run,
            endpoint_url=args.endpoint_url,
        )
    elif args.command == "list-dlq":
        repo_root = Path(args.repo_root) if args.repo_root else None
        result = list_dlq(
            case_ref=args.case_ref,
            repo_root=repo_root,
            dlq_path_override=args.dlq_path,
        )
    else:
        result = {"ok": False, "message": f"unknown command: {args.command}"}

    _print(result, as_json=as_json)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
