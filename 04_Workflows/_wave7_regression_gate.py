"""Wave 6/7/8 integration regression gate CLI (INT-REGRESSION-GATE v0.1)."""

from __future__ import annotations

import argparse
import json
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

    from core.wave7_regression_gate import (  # noqa: PLC0415
        format_first_failure_line,
        run_regression_gate,
    )

    parser = argparse.ArgumentParser(
        description="Wave 6/7/8 integration regression gate (Tier-A / Tier-B / ALL).",
    )
    parser.add_argument(
        "--tier",
        default="A",
        choices=["A", "B", "ALL", "a", "b", "all"],
        help="A=Tier-A modules; B=Tier-B only; ALL=Tier-A + Tier-B",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase unittest verbosity (repeat for more)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON result to stdout",
    )
    args = parser.parse_args(argv)

    verbosity = 1 + min(args.verbose, 2)
    try:
        result = run_regression_gate(tier=args.tier, verbosity=verbosity)
    except (ValueError, RuntimeError) as exc:
        payload = {
            "ok": False,
            "suite": str(args.tier).upper(),
            "failed_tests": [],
            "message": str(exc),
        }
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 2

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))

    if not result.get("ok"):
        line = format_first_failure_line(result)
        if line:
            print(line, file=sys.stderr)

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
