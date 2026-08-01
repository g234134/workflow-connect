"""_boot_context.py — 三層接戰 bootstrap CLI（讀檔計畫 + 路由 + Progress 末段）

Examples:
  # 完整接戰（預設）
  python 04_Workflows/_boot_context.py --text "<尚書省指令>" --pretty

  # 續棒輕量：只讀票 state + multi_chat_roles 對應角色小節
  python 04_Workflows/_boot_context.py --mode light --ticket-id W5-T6-ticket-schema-relay-ops-ssot-v1 --role implementer --pretty

  # 等價：ops_cycle bootstrap
  python 04_Workflows/_ops_cycle.py bootstrap --mode light --ticket-id <ID> --role reviewer --pretty
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from boot_context import build_boot_context  # type: ignore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "HQ boot bootstrap: route task and emit read_plan JSON. "
            "Default mode=full（三層接戰）；mode=light 為 Multi-Chat 續棒輕量讀檔。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "modes:\n"
            "  full   預設。Tier2/3/4 read_plan + Progress tail。\n"
            "  light  續棒。只讀 --ticket-id／--ticket-state 與 "
            ".cursor/rules/multi_chat_roles.mdc 對應 §角色；跳過 Progress／憲法全文。\n"
            "\n"
            "light 範例:\n"
            "  python 04_Workflows/_boot_context.py --mode light "
            "--ticket-id BATCH-MVP-01 --role implementer --pretty\n"
        ),
    )
    parser.add_argument("--type", dest="task_type", help="Canonical task_type (e.g. hq.governance)")
    parser.add_argument("--text", dest="text", help="Task description for keyword matching")
    parser.add_argument(
        "--mode",
        choices=["full", "light"],
        default="full",
        help="full=完整接戰（預設）；light=續棒輕量（票 state + roles 小節）",
    )
    parser.add_argument(
        "--ticket-id",
        help="light：票號（解析為 04_Workflows/tickets/<id>_state.md）",
    )
    parser.add_argument(
        "--ticket-state",
        help="light：票 state 相對路徑（優先於 --ticket-id）",
    )
    parser.add_argument(
        "--role",
        default="orchestrator",
        help="light：orchestrator|implementer|reviewer|scribe（或 O/B/C/D）；預設 orchestrator",
    )
    parser.add_argument(
        "--progress-tail",
        type=int,
        default=80,
        help="Lines to include from Progress tail (default: 80；light 忽略）",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    result = build_boot_context(
        task_type=args.task_type,
        text=args.text,
        progress_tail_lines=args.progress_tail,
        mode=args.mode,
        ticket_id=args.ticket_id,
        ticket_state=args.ticket_state,
        role=args.role,
    )

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
