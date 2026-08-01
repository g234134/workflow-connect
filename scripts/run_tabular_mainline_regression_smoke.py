#!/usr/bin/env python3

"""Tri-case Tabular main-chain regression smoke (demo_phase + sampleco + generic-low-risk).



Usage:

    python scripts/run_tabular_mainline_regression_smoke.py

    python scripts/run_tabular_mainline_regression_smoke.py --json

"""



from __future__ import annotations



import argparse

import json

import sys

from pathlib import Path

from typing import Any



_REPO_ROOT = Path(__file__).resolve().parents[1]

_SCRIPTS = _REPO_ROOT / "scripts"

if str(_SCRIPTS) not in sys.path:

    sys.path.insert(0, str(_SCRIPTS))



from tabular_regression_smoke_lib import (  # noqa: E402

    DEFAULT_OPERATOR,

    run_case_regression_smoke,

)



SMOKE_CASES: list[dict[str, Any]] = [

    {

        "case_dir": "cases/demo_phase",

        "case_id": "demo_phase",

        "force_driver": True,

        "expected_delivery_ready": True,

    },

    {

        "case_dir": "cases/sampleco/2026-0001",

        "case_id": "2026-0001",

        "force_driver": False,

        "expected_delivery_ready": False,

    },

    {

        "case_dir": "cases/internal/generic-low-risk",

        "case_id": "generic-low-risk",

        "force_driver": False,

        "expected_delivery_ready": True,

    },

]





def run_tabular_mainline_regression_smoke(

    *,

    requested_by: str = DEFAULT_OPERATOR,

    dry_run: bool = False,

) -> dict[str, Any]:

    results: list[dict[str, Any]] = []

    all_ok = True



    for spec in SMOKE_CASES:

        case_dir = (_REPO_ROOT / spec["case_dir"]).resolve()

        result = run_case_regression_smoke(

            case_dir,

            repo_root=_REPO_ROOT,

            case_id=spec.get("case_id"),

            requested_by=requested_by,

            dry_run=dry_run,

            force_driver=bool(spec.get("force_driver")),

            expected_delivery_ready=spec.get("expected_delivery_ready"),

        )

        results.append(result)

        if not result.get("ok"):

            all_ok = False



    return {

        "ok": all_ok,

        "dry_run": dry_run,

        "cases": results,

        "case_count": len(results),

        "passed": sum(1 for r in results if r.get("ok")),

        "message": (

            "tabular mainline regression smoke passed"

            if all_ok

            else "tabular mainline regression smoke failed — see cases[].verification.failures"

        ),

    }





def main(argv: list[str] | None = None) -> int:

    parser = argparse.ArgumentParser(

        description=(

            "Run Tabular main-chain regression smoke for demo_phase, sampleco, "

            "and generic-low-risk."

        )

    )

    parser.add_argument("--operator", default=DEFAULT_OPERATOR)

    parser.add_argument("--dry-run", action="store_true")

    parser.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)



    result = run_tabular_mainline_regression_smoke(

        requested_by=args.operator,

        dry_run=args.dry_run,

    )



    if args.json:

        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:

        print(f"ok={result.get('ok')} passed={result.get('passed')}/{result.get('case_count')}")

        for case in result.get("cases") or []:

            ver = case.get("verification") or {}

            print(

                f"  {case.get('case_id')}: ok={case.get('ok')} "

                f"delivery_ready={ver.get('delivery_ready')} "

                f"{case.get('message', '')}"

            )



    return 0 if result.get("ok") else 1





if __name__ == "__main__":

    sys.exit(main())

