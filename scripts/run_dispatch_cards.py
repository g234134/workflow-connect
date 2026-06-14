#!/usr/bin/env python
"""CLI entry for dispatch instruction card generator (read-only on ticket state)."""



from __future__ import annotations



import argparse

import json

import sys

from pathlib import Path



_REPO_ROOT = Path(__file__).resolve().parents[1]

_WORKFLOWS = _REPO_ROOT / "04_Workflows"

if str(_WORKFLOWS) not in sys.path:

    sys.path.insert(0, str(_WORKFLOWS))



from _dispatch_cards import (  # noqa: E402

    VALID_ROLES,

    generate_cards,

    refresh_dispatch_plan,

    write_run_summary,

)





def main() -> int:

    parser = argparse.ArgumentParser(

        description="Generate Cursor instruction cards from dispatch plan + ticket FRAME (read-only).",

    )

    parser.add_argument(

        "--plan",

        default="artifacts/control_plane/dispatch_plan.latest.json",

        help="dispatch_plan JSON path (relative to repo root)",

    )

    parser.add_argument(

        "--out-dir",

        default="artifacts/control_plane/cards/",

        help="Output directory for *.cursor.md cards",

    )

    parser.add_argument(

        "--role",

        default="all",

        choices=sorted(VALID_ROLES),

        help="Filter by recommended role",

    )

    parser.add_argument(

        "--limit",

        type=int,

        default=5,

        help="Max suggested_next supplement tickets (runnable_now always included)",

    )

    parser.add_argument(

        "--ticket",

        help="Generate card for a single ticket id only",

    )

    parser.add_argument(

        "--refresh-plan",

        action="store_true",

        help="Run dispatch_executor before generating cards",

    )

    parser.add_argument(

        "--dry-run",

        action="store_true",

        help="Do not write card files; emit JSON summary only",

    )

    parser.add_argument(

        "--json-summary",

        default="artifacts/control_plane/dispatch_cards_run.latest.json",

        help="Optional path for run summary JSON (skipped when --dry-run)",

    )

    parser.add_argument(

        "--pretty",

        action="store_true",

        help="Pretty-print JSON summary to stdout",

    )

    parser.add_argument(

        "--eligibility-gate",

        choices=("off", "warn", "block"),

        default="block",

        help="off=skip gate; warn=write card with warning; block=skip ineligible tickets",

    )

    parser.add_argument(

        "--force-eligibility",

        action="store_true",

        help="Orchestrator override: generate cards even when ineligible (logged in summary)",

    )

    args = parser.parse_args()



    if args.refresh_plan:

        refresh_result = refresh_dispatch_plan(_REPO_ROOT)

        if not refresh_result["ok"]:

            print(

                json.dumps({"ok": False, "error": "refresh_plan_failed", **refresh_result}),

                file=sys.stderr,

            )

            return 1



    plan_path = _REPO_ROOT / args.plan

    if not plan_path.is_file():

        print(

            json.dumps({"ok": False, "error": f"plan_not_found:{args.plan}"}),

            file=sys.stderr,

        )

        return 1



    out_dir = _REPO_ROOT / args.out_dir

    summary = generate_cards(

        _REPO_ROOT,

        plan_path=plan_path,

        out_dir=out_dir,

        role=args.role,

        limit=args.limit,

        ticket_id=args.ticket,

        dry_run=args.dry_run,

        eligibility_gate=args.eligibility_gate,

        force_eligibility=args.force_eligibility,

    )



    if not args.dry_run and args.json_summary:

        write_run_summary(summary, _REPO_ROOT / args.json_summary)



    if args.pretty:

        print(json.dumps(summary, ensure_ascii=False, indent=2))

    else:

        print(

            json.dumps(

                {

                    "ok": summary.get("ok"),

                    "cards_generated": summary.get("cards_generated"),

                    "cards_skipped": summary.get("cards_skipped"),

                    "warnings_count": len(summary.get("warnings", [])),

                    "eligibility_gate": summary.get("eligibility_gate"),

                    "eligibility_blocked_count": len(summary.get("eligibility_blocked", [])),

                },

                ensure_ascii=False,

            )

        )



    return 0 if summary.get("ok") else 1





if __name__ == "__main__":

    raise SystemExit(main())


