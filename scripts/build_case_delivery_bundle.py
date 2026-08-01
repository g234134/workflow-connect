#!/usr/bin/env python3
"""CLI: build standard case delivery bundle (Wave 2 P4).

Usage:
    python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase
    python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json
    python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --refresh-eligibility
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"
if str(_CSV_CLEANING) not in sys.path:
    sys.path.insert(0, str(_CSV_CLEANING))

from case_delivery_bundle import build_case_delivery_bundle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build case delivery bundle: cleaned + reports + eligibility + signoff."
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        type=Path,
        help="Path to case directory (e.g. cases/demo_phase)",
    )
    parser.add_argument(
        "--refresh-eligibility",
        action="store_true",
        help="Re-run P2 eligibility even if eligibility_result.json exists",
    )
    parser.add_argument(
        "--refresh-signoff",
        action="store_true",
        help="Overwrite delivery_signoff.md from template",
    )
    parser.add_argument(
        "--no-enrich-report",
        action="store_true",
        help="Skip v1 contract enrichment on report.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full structured result JSON to stdout",
    )
    args = parser.parse_args(argv)

    result = build_case_delivery_bundle(
        args.case_dir,
        refresh_eligibility=args.refresh_eligibility,
        refresh_signoff=args.refresh_signoff,
        enrich_report=not args.no_enrich_report,
    )

    if result.get("ok"):
        arts = result.get("artifacts") or {}
        print(
            f"bundle ok case={result.get('case_id')} "
            f"eligibility={result.get('eligibility_status')} "
            f"signoff={arts.get('delivery_signoff_md')}"
        )
        for key in ("cleaned_csv", "report_json", "eligibility_result_json"):
            val = arts.get(key)
            if val:
                display = val if isinstance(val, str) else ", ".join(val)
                print(f"  {key}: {display}")
    else:
        print(f"bundle failed: {result.get('message')}")
        missing = result.get("missing")
        if missing:
            print("  missing: " + ", ".join(missing))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
