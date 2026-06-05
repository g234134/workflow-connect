"""Wave 7 runner environment bootstrap CLI (RUNNER-ENV-BOOTSTRAP)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _insert_gov_core_from_master_map(workflows_dir: Path) -> Path:
    repo_root = workflows_dir.parent
    mp_path = workflows_dir / "Master_Map.json"
    with mp_path.open(encoding="utf-8") as f:
        master_map = json.load(f)
    cabins = master_map.get("cabins") or {}
    entry = cabins.get("gov_core_system") if isinstance(cabins, dict) else None
    if not isinstance(entry, dict):
        raise RuntimeError("Master_Map.cabins.gov_core_system missing")
    venv_rel = entry.get("venv_dir")
    if not venv_rel:
        raise RuntimeError("Master_Map.cabins.gov_core_system.venv_dir missing")
    gov_core = (repo_root / str(venv_rel).replace("\\", "/")).resolve()
    gov_s = str(gov_core)
    if gov_s not in sys.path:
        sys.path.insert(0, gov_s)
    return gov_core


def main(argv: list[str] | None = None) -> int:
    workflows_dir = Path(__file__).resolve().parent
    _insert_gov_core_from_master_map(workflows_dir)

    from core.wave7_runner_env_bootstrap import bootstrap_runner_env  # noqa: PLC0415

    parser = argparse.ArgumentParser(
        description="Wave 7 runner/orchestrator environment bootstrap (single entry).",
    )
    parser.add_argument(
        "--cabin",
        default=None,
        help="Cabin id (default: Master_Map.wave7_bootstrap.cabin_default)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Import core modules and verify JSON schemas are readable",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve paths only; skip venv/schema checks unless --check is also set",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON result",
    )
    args = parser.parse_args(argv)

    result = bootstrap_runner_env(
        cabin=args.cabin,
        check=args.check,
        dry_run=args.dry_run,
        start=workflows_dir,
    )

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))

    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
