#!/usr/bin/env python3
"""CLI: low-risk eligibility check for a single on-disk case directory (Wave 2 P2).

Usage:
    python scripts/check_case_eligibility.py --case-dir cases/demo_phase
    python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json
    python scripts/check_case_eligibility.py --case-dir cases/sampleco/2026-0001 --json

JSON ``dimensions.schema`` (Wave 4B header probe):
    status — accepted | review_needed | rejected | unknown (field-count rules)
    field_count — column count when readable
    column_names — raw CSV header list
    notes — probe tags, e.g. phase_demo, phase_like, multi_row_export, schema_ambiguous
    warnings — human-facing warning tokens for downstream guards / manual review

Exit codes:
    0 — accepted
    1 — rejected
    2 — review_needed
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

from case_eligibility import check_case_eligibility  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Low-risk tabular case eligibility gate (manual MVP · Wave 2 P2). "
            "dimensions.schema.notes carries Wave 4B header/schema probe tags "
            "(phase_like, multi_row_export, etc.) without changing cleaning logic."
        )
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        type=Path,
        help="Path to case directory containing intake.json and raw data file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full structured result JSON to stdout",
    )
    args = parser.parse_args(argv)

    result = check_case_eligibility(args.case_dir)
    eligibility = result.get("eligibility", "review_needed")
    summary = f"eligibility={eligibility} case={result.get('case_id', args.case_dir.name)}"
    if result.get("reason_code"):
        summary += f" reason={result['reason_code']}"
    print(summary)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return int(result.get("exit_code", 2))


if __name__ == "__main__":
    sys.exit(main())
