#!/usr/bin/env python3
"""Inspect P8.9 operator fields projection (Wave 2 · read-only).

Usage:
  python scripts/inspect_p89_operator_fields_v1.py --case-ref demo_phase --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.p89_operator_fields_v1 import project_operator_fields


def _format_text(result: dict) -> str:
    lines = [
        "P8.9 Operator Fields (read-only projection)",
        f"ok: {result.get('ok')}",
        f"case_ref: {result.get('case_ref')}",
        f"count: {result.get('count', 0)}",
        f"schema_version: {result.get('schema_version')}",
        f"t4: {result.get('t4_alignment')}",
        "",
    ]
    for row in result.get("rows") or []:
        lines.append(
            "  "
            f"event_id={row.get('event_id')} "
            f"ack={row.get('ack_status')} "
            f"handler={row.get('handler_id')} "
            f"registry_hit={row.get('dispatch_registry_hit')} "
            f"dlq={row.get('dlq_flag')}"
        )
    if result.get("message"):
        lines.append("")
        lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P8.9 operator fields projection (read-only)")
    parser.add_argument("--case-ref", required=True)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--outbox-root", default=None, help="optional outbox root override")
    parser.add_argument("--dlq-path", default=None, help="optional DLQ jsonl override")
    args = parser.parse_args(argv)

    result = project_operator_fields(
        args.case_ref,
        repo_root=_REPO_ROOT,
        outbox_root_override=args.outbox_root,
        dlq_path_override=args.dlq_path,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_text(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
