#!/usr/bin/env python3
"""Validate intake.json structure before starting automation.

Usage:
    python scripts/validate_intake.py --case-dir cases/demo_phase
    python scripts/validate_intake.py --case-dir cases/demo_phase --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]


def validate_intake(case_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    case_dir = case_dir.resolve()

    if not case_dir.is_dir():
        return {"ok": False, "errors": ["case_dir_missing"], "message": "case directory not found"}

    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        errors.append("missing_intake_json")
    else:
        try:
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"intake_json_invalid:{exc}")
            intake = {}
        if not isinstance(intake, dict):
            errors.append("intake_json_not_object")
            intake = {}
        else:
            if not intake.get("provenance"):
                errors.append("missing_provenance")
            if not intake.get("sensitivity"):
                errors.append("missing_sensitivity")
            data_file = intake.get("data_file")
            if not isinstance(data_file, str) or not data_file.strip():
                errors.append("missing_data_file")
            elif not (case_dir / data_file).is_file():
                errors.append(f"raw_file_missing:{data_file}")

    if not (case_dir / "raw").is_dir():
        errors.append("missing_raw_directory")

    ok = not errors
    return {
        "ok": ok,
        "case_dir": str(case_dir),
        "errors": errors,
        "message": "intake valid" if ok else f"intake invalid: {', '.join(errors)}",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate case intake.json structure.")
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    case_dir = args.case_dir
    if not case_dir.is_absolute():
        case_dir = _REPO_ROOT / case_dir

    result = validate_intake(case_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result.get("message", ""))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
