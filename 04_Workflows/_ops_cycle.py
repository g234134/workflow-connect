"""_ops_cycle.py — 副官營運週期 CLI（HQ-P4-OPS-CYCLE）"""
from __future__ import annotations

import argparse
import json
import os
import sys

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from ops_cycle import (  # type: ignore  # noqa: E402
    append_battle_report,
    get_archive_checklist,
    get_cycle_artifact_paths,
    render_battle_report_markdown,
    validate_archive,
    validate_battle_report,
    write_review_template,
)


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def _emit(result: dict, pretty: bool) -> None:
    if pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="HQ Phase 4 ops cycle (battle report / archive / review).")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate-report", parents=[common], help="Validate battle report JSON")
    p_val.add_argument("--json", dest="json_path", required=True, help="Path to report JSON")

    p_render = sub.add_parser("render-report", parents=[common], help="Render battle report markdown to stdout")
    p_render.add_argument("--json", dest="json_path", required=True)

    p_append = sub.add_parser("append-report", parents=[common], help="Append battle report to Progress")
    p_append.add_argument("--json", dest="json_path", required=True)
    p_append.add_argument("--dry-run", action="store_true")

    p_list = sub.add_parser("checklist", parents=[common], help="Evaluate archive checklist")
    p_list.add_argument("--mode", choices=["minimal", "full"], default="full")

    p_arch = sub.add_parser("validate-archive", parents=[common], help="Validate archive readiness")
    p_arch.add_argument("--mode", choices=["minimal", "full"], default="full")

    p_rev = sub.add_parser("new-review", parents=[common], help="Create review template under project_status/reviews")
    p_rev.add_argument("--type", dest="review_type", required=True)
    p_rev.add_argument("--project", dest="project_id", required=True)
    p_rev.add_argument("--ticket", default=None)
    p_rev.add_argument("--dry-run", action="store_true")

    sub.add_parser("paths", parents=[common], help="Print ops cycle artifact paths")

    args = parser.parse_args()

    if args.command == "paths":
        _emit(get_cycle_artifact_paths(), args.pretty)
        return 0

    if args.command == "validate-report":
        data = _load_json(args.json_path)
        result = validate_battle_report(data)
        _emit(result, args.pretty)
        return 0 if result.get("ok") else 2

    if args.command == "render-report":
        data = _load_json(args.json_path)
        validation = validate_battle_report(data)
        if not validation.get("ok"):
            _emit({"ok": False, "validation": validation}, args.pretty)
            return 2
        print(render_battle_report_markdown(data))
        return 0

    if args.command == "append-report":
        data = _load_json(args.json_path)
        result = append_battle_report(data, dry_run=args.dry_run)
        _emit(result, args.pretty)
        return 0 if result.get("ok") else 2

    if args.command == "checklist":
        result = get_archive_checklist(args.mode)
        _emit(result, args.pretty)
        return 0 if result.get("ok") else 1

    if args.command == "validate-archive":
        result = validate_archive(args.mode)
        _emit(result, args.pretty)
        return 0 if result.get("ready_for_archive") else 1

    if args.command == "new-review":
        result = write_review_template(
            args.review_type,
            args.project_id,
            ticket=args.ticket,
            dry_run=args.dry_run,
        )
        _emit(result, args.pretty)
        return 0 if result.get("ok") else 2

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
