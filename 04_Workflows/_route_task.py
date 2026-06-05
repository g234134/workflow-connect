"""_route_task.py — 副官任務路由 CLI（HQ-P3-TASK-ROUTING）"""
from __future__ import annotations

import argparse
import json
import os
import sys

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from task_routing import enrich_route_with_runners, route_task  # type: ignore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve HQ task routing (worker/cabin/runners).")
    parser.add_argument("--type", dest="task_type", help="Canonical task_type (e.g. chariot.factory)")
    parser.add_argument("--text", dest="text", help="Task description for keyword matching")
    parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        default=[],
        help="Optional tag (repeatable); combined with --text",
    )
    parser.add_argument(
        "--paths",
        action="store_true",
        help="Include runner_paths from Master_Map.json",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON to stdout",
    )
    args = parser.parse_args()

    if not args.task_type and not args.text and not args.tags:
        parser.error("Provide --type and/or --text/--tag")

    result = route_task(
        task_type=args.task_type,
        description=args.text,
        tags=args.tags or None,
    )
    if args.paths:
        result = enrich_route_with_runners(result)

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))

    if not result.get("ok"):
        return 2
    if result.get("blocked") and not result.get("assignable"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
