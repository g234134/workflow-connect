#!/usr/bin/env python3
"""Read-only historical case lookup against cases/index.json (Wave 4A MEMO).

Usage:
    python scripts/lookup_case_history.py --list-all
    python scripts/lookup_case_history.py --client-ref sampleco
    python scripts/lookup_case_history.py --product-sku CLEAN-BASIC
    python scripts/lookup_case_history.py --schema-headers Phase,名稱
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from cases_index_lib import _parse_header_list, lookup_cases  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lookup registered cases from cases/index.json (structured filters only)."
    )
    parser.add_argument("--client-ref", help="Exact client_ref match (case-insensitive)")
    parser.add_argument("--product-sku", help="Exact product_sku match (case-insensitive)")
    parser.add_argument(
        "--schema-headers",
        help="Comma-separated header names; matches subset or exact set against indexed schema_headers",
    )
    parser.add_argument("--list-all", action="store_true", help="Return all indexed entries")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include schema_headers, cleaning_rules, delivery_template_ref, qa fields",
    )
    args = parser.parse_args(argv)

    if not args.list_all and not any([args.client_ref, args.product_sku, args.schema_headers]):
        parser.error("specify at least one filter or --list-all")

    result = lookup_cases(
        client_ref=args.client_ref,
        product_sku=args.product_sku,
        schema_headers=_parse_header_list(args.schema_headers),
        list_all=args.list_all,
        verbose=args.verbose,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
