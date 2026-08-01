#!/usr/bin/env python3

"""One-command Tabular intake → delivery orchestration.



Usage:

    python scripts/run_tabular_new_case_to_delivery.py --dry-run --json \\

        --case-dir cases/internal/generic-low-risk

    python scripts/run_tabular_new_case_to_delivery.py --case-dir cases/internal/generic-low-risk \\

        --start --json

    python scripts/run_tabular_new_case_to_delivery.py \\

        --client-ref internal --product-sku CLEAN-BASIC --source-file cases/internal/generic-low-risk/raw/simple_orders.csv \\

        --dry-run --json

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



from tabular_new_case_to_delivery_lib import (  # noqa: E402

    DEFAULT_OPERATOR,

    resolve_case_dir_from_args,

    run_new_case_to_delivery,

)





def main(argv: list[str] | None = None) -> int:

    parser = argparse.ArgumentParser(

        description="Orchestrate Tabular case from intake through delivery (operator CLI)."

    )

    parser.add_argument("--case-dir", type=Path, help="Existing case directory")

    parser.add_argument("--client-ref", help="Create new case under cases/<client-ref>/")

    parser.add_argument("--product-sku", help="Product SKU for new case intake")

    parser.add_argument("--source-file", type=Path, help="Raw CSV/Excel source for new case")

    parser.add_argument("--start", action="store_true", help="Start automation and run driver")

    parser.add_argument("--force", action="store_true", help="Pass --force to driver (review_needed)")

    parser.add_argument("--no-export-zip", action="store_true")

    parser.add_argument("--dry-run", action="store_true")

    parser.add_argument("--requested-by", default=DEFAULT_OPERATOR)

    parser.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)



    case_dir, create_result = resolve_case_dir_from_args(

        case_dir=args.case_dir,

        client_ref=args.client_ref,

        product_sku=args.product_sku,

        source_file=args.source_file,

        repo_root=_REPO_ROOT,

    )

    if case_dir is None:

        err = create_result or {"ok": False, "message": "case resolution failed"}

        if args.json:

            print(json.dumps(err, ensure_ascii=False, indent=2))

        else:

            print(err.get("message", "error"))

        return 1



    result = run_new_case_to_delivery(

        case_dir,

        repo_root=_REPO_ROOT,

        start=args.start,

        requested_by=args.requested_by,

        force_driver=args.force,

        export_zip=not args.no_export_zip,

        dry_run=args.dry_run,

    )

    if create_result and create_result.get("ok"):

        result = {**result, "create_case": create_result}



    if args.json:

        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:

        print(

            f"ok={result.get('ok')} delivery_ready={result.get('delivery_ready')} "

            f"will_pause_at={result.get('will_pause_at')} message={result.get('message')}"

        )



    return 0 if result.get("ok") else 1





if __name__ == "__main__":

    sys.exit(main())

