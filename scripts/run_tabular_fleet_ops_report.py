#!/usr/bin/env python3
"""Fleet-level Tabular ops report (read-only rollup).

Usage:
    python scripts/run_tabular_fleet_ops_report.py
    python scripts/run_tabular_fleet_ops_report.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_ops_summary_lib import (  # noqa: E402
    build_ops_summary,
    format_fleet_blockers,
    format_ops_table,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fleet-level Tabular ops summary (read-only; all cases)."
    )
    parser.add_argument("--format", choices=("table", "json"), default="json")
    parser.add_argument("--json", action="store_true", help="Alias for --format json")
    args = parser.parse_args(argv)

    result = build_ops_summary(list_all=True, fleet=True)
    output_format = "json" if args.json else args.format

    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_fleet_blockers(result))
        print("")
        print(format_ops_table(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
