"""Phase 6 core agent workflow smoke CLI (P6 / A-P0-4)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    workflows_dir = Path(__file__).resolve().parent
    repo_root = workflows_dir.parent

    # Repo root on path before importing core.*
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from core.agent_workflow_smoke import (  # noqa: PLC0415
        format_first_failure_line,
        gov_core_root_from_master_map,
        run_agent_workflow_smoke,
    )

    parser = argparse.ArgumentParser(
        description="Core agent workflow smoke (ROOT / DARK / HQ / PR / ALL).",
    )
    parser.add_argument(
        "--tier",
        default="PR",
        choices=[
            "ROOT",
            "DARK",
            "DARK_FULL",
            "HQ",
            "PR",
            "ALL",
            "root",
            "dark",
            "dark_full",
            "hq",
            "pr",
            "all",
        ],
        help="PR=fast PR gate; DARK=gov_core subset; DARK_FULL=full dark modules; ALL=ROOT+HQ+DARK",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase unittest verbosity (repeat for more)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON result to stdout",
    )
    args = parser.parse_args(argv)

    verbosity = 1 + min(args.verbose, 2)
    gov_core = None
    tier_u = str(args.tier).upper()
    if tier_u in ("DARK", "DARK_FULL", "ALL"):
        try:
            gov_core = gov_core_root_from_master_map(workflows_dir)
        except RuntimeError as exc:
            payload = {
                "ok": False,
                "suite": "agent_workflow_smoke",
                "tier": tier_u,
                "message": str(exc),
            }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
            return 2

    try:
        result = run_agent_workflow_smoke(
            tier=args.tier,
            verbosity=verbosity,
            repo_root=repo_root,
            workflows_dir=workflows_dir,
            gov_core_root=gov_core,
        )
    except (ValueError, RuntimeError) as exc:
        payload = {
            "ok": False,
            "suite": "agent_workflow_smoke",
            "tier": tier_u,
            "failed_tests": [],
            "message": str(exc),
        }
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 2

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))

    if not result.get("ok"):
        hint = format_first_failure_line(result)
        if hint:
            print(hint, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
