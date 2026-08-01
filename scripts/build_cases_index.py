#!/usr/bin/env python3
"""Refresh cases/index.json from registered case directories (Wave 4A MEMO).

Usage:
    python scripts/build_cases_index.py
    python scripts/build_cases_index.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from cases_index_lib import discover_case_dirs, refresh_cases_index  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Discover case dirs (anchors + glob) and write cases/index.json."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured refresh result JSON to stdout",
    )
    args = parser.parse_args(argv)

    result = refresh_cases_index()
    discovered = len(discover_case_dirs())
    summary = (
        f"cases_index refreshed: {result['cases_written']} entries "
        f"from {discovered} discovered dirs -> {result['index_path']}"
    )
    print(summary)
    if result.get("skipped"):
        print(f"skipped: {', '.join(result['skipped'])}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
