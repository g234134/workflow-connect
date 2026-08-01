#!/usr/bin/env python3
"""CLI for Wave 3 smoke chain (G7 → gate → notify → sink → MP-SMOKE).

Design SSOT: docs/wave3-smoke-g7-gate-notify-mp-chain-v1.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.wave3_smoke_chain_v1 import (  # noqa: E402
    DEFAULT_CASE_REF,
    DEFAULT_TASK_TYPE,
    DOC_REL,
    run_wave3_smoke_chain_v1,
)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Wave 3 smoke chain: G7 + gate + notify + alert sink + MP-SMOKE",
    )
    parser.add_argument("--case-ref", default=DEFAULT_CASE_REF)
    parser.add_argument("--task-type", default=DEFAULT_TASK_TYPE)
    parser.add_argument("--case-dir", default=None, help="Override case dir")
    parser.add_argument("--outbox-root", default=None)
    parser.add_argument(
        "--skip-mp-smoke",
        action="store_true",
        help="Skip full MP-SMOKE step (steps 1–4 only)",
    )
    parser.add_argument(
        "--enable-dispatch",
        action="store_true",
        help="Pass enable_dispatch to MP-SMOKE",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = run_wave3_smoke_chain_v1(
        args.case_ref,
        task_type=args.task_type,
        case_dir=args.case_dir,
        repo_root=_REPO_ROOT,
        outbox_root_override=args.outbox_root,
        include_mp_smoke=not args.skip_mp_smoke,
        enable_dispatch=args.enable_dispatch,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok={result.get('ok')} schema={result.get('schema_version')}")
        print(f"message={result.get('message')}")
        print(f"contract={DOC_REL}")
        for step in result.get("steps") or []:
            flag = "PASS" if step.get("ok") else "FAIL"
            print(f"  [{flag}] {step.get('step_id')}: {step.get('message')}")
        if result.get("failed_steps"):
            print(f"failed_steps={result.get('failed_steps')}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
