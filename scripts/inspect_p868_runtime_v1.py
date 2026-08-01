#!/usr/bin/env python3
"""Inspect P8.6–8.8 runtime wiring (catalog → selector → executor dry_run).

Usage:
  python scripts/inspect_p868_runtime_v1.py --case-ref demo_phase --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.p868_runtime_inspect_v1 import inspect_p868_runtime


def _format_text(result: dict) -> str:
    lines = [
        "P8.6–8.8 Runtime Inspect (read-only / dry_run)",
        f"ok: {result.get('ok')}",
        f"case_ref: {result.get('case_ref')}",
        f"schema_version: {result.get('schema_version')}",
        f"catalog: {result.get('catalog')}",
        f"selector: plan_only={result.get('selector', {}).get('plan_only')} "
        f"candidates={result.get('selector', {}).get('candidate_count')}",
        f"executor: mode={result.get('executor', {}).get('execution_mode')} "
        f"ok={result.get('executor', {}).get('ok')} "
        f"tool={result.get('executor', {}).get('tool_id')}",
        f"allowlist: {result.get('allowlist')}",
        f"message: {result.get('message')}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P8.6–8.8 runtime inspect (catalog/selector/executor dry_run)"
    )
    parser.add_argument("--case-ref", required=True)
    parser.add_argument("--task-type", default="gate_only")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--skip-nt", action="store_true", help="skip NT selector stub")
    args = parser.parse_args(argv)

    result = inspect_p868_runtime(
        args.case_ref,
        task_type=args.task_type,
        repo_root=_REPO_ROOT,
        include_nt_selector=not args.skip_nt,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_text(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
