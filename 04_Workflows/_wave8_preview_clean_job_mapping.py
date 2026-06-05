#!/usr/bin/env python3
"""
Wave 8 — Preview CleanJob mapping CLI (v0.1)

本地驗證 intake JSON → CleanJob → Wave7 inputs 映射鏈路，不執行實際作業。

Usage:
    python 04_Workflows/_wave8_preview_clean_job_mapping.py --intake-json path/to/intake.json

Output (stdout):
    {
        "ok": true,
        "clean_job": {...},
        "job_record": {...},
        "raw_files": [...],
        "message": "...",
        "error_code": null,
        "schema_version": "wave8_preview_v0.1"
    }

Exit codes:
    0 — 映射成功
    1 — 映射失敗（驗證錯誤或異常）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _resolve_core_path() -> Path | None:
    """Resolve gov_core_system core path relative to this script."""
    script_dir = Path(__file__).parent.resolve()
    # Look for core in expected venv location
    candidate = (
        script_dir.parent
        / "01_Environments"
        / "python_venvs"
        / "gov_core_system"
    )
    if (candidate / "core").is_dir():
        return candidate
    return None


def _import_mappers(core_root: Path) -> tuple[Any, Any]:
    """Import mapping functions from core with sys.path bootstrap."""
    if str(core_root) not in sys.path:
        sys.path.insert(0, str(core_root))

    try:
        from core.wave8_clean_intake_mapper import map_intake_to_clean_job
        from core.wave8_clean_job_bridge import build_wave7_inputs_from_clean_job

        return map_intake_to_clean_job, build_wave7_inputs_from_clean_job
    except ImportError as e:
        raise ImportError(f"Failed to import core mappers from {core_root}: {e}") from e


def _load_intake_json(path: Path) -> dict[str, Any]:
    """Load and validate intake JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Intake JSON not found: {path}")
    if not path.is_file():
        raise ValueError(f"Intake JSON path is not a file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        if not content.strip():
            raise ValueError(f"Intake JSON file is empty: {path}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Intake JSON root must be an object, got {type(data).__name__}")

    return data


def run_preview(intake_json_path: Path) -> dict[str, Any]:
    """
    Run the full mapping chain: intake → CleanJob → Wave7 inputs.

    Returns structured result with ok, clean_job, job_record, raw_files.
    """
    schema_version = "wave8_preview_v0.1"

    # Step 0: Load intake JSON
    try:
        intake_record = _load_intake_json(intake_json_path)
    except (FileNotFoundError, ValueError) as e:
        return {
            "ok": False,
            "clean_job": None,
            "job_record": None,
            "raw_files": None,
            "message": f"Failed to load intake JSON: {e}",
            "error_code": "intake_load_failed",
            "schema_version": schema_version,
        }

    # Step 1: Import mappers
    core_root = _resolve_core_path()
    if core_root is None:
        return {
            "ok": False,
            "clean_job": None,
            "job_record": None,
            "raw_files": None,
            "message": "Could not locate gov_core_system core path",
            "error_code": "core_path_not_found",
            "schema_version": schema_version,
        }

    try:
        map_intake_to_clean_job, build_wave7_inputs_from_clean_job = _import_mappers(core_root)
    except ImportError as e:
        return {
            "ok": False,
            "clean_job": None,
            "job_record": None,
            "raw_files": None,
            "message": f"Failed to import mappers: {e}",
            "error_code": "import_error",
            "schema_version": schema_version,
        }

    # Step 2: Map intake → CleanJob
    clean_result = map_intake_to_clean_job(intake_record)
    if not clean_result.get("ok"):
        return {
            "ok": False,
            "clean_job": clean_result.get("clean_job"),
            "job_record": None,
            "raw_files": None,
            "message": clean_result.get("message", "CleanJob mapping failed"),
            "error_code": clean_result.get("error_code", "clean_job_mapping_failed"),
            "validation_errors": clean_result.get("validation_errors", []),
            "schema_version": schema_version,
        }

    clean_job = clean_result.get("clean_job")
    if clean_job is None:
        return {
            "ok": False,
            "clean_job": None,
            "job_record": None,
            "raw_files": None,
            "message": "CleanJob mapping returned ok=true but clean_job is None",
            "error_code": "clean_job_missing",
            "schema_version": schema_version,
        }

    # Step 3: Map CleanJob → Wave7 inputs
    wave7_result = build_wave7_inputs_from_clean_job(clean_job)
    if not wave7_result.get("ok"):
        return {
            "ok": False,
            "clean_job": clean_job,
            "job_record": wave7_result.get("job_record"),
            "raw_files": wave7_result.get("raw_files"),
            "message": wave7_result.get("message", "Wave7 inputs mapping failed"),
            "error_code": wave7_result.get("error_code", "wave7_mapping_failed"),
            "schema_version": schema_version,
        }

    # Success
    return {
        "ok": True,
        "clean_job": clean_job,
        "job_record": wave7_result.get("job_record"),
        "raw_files": wave7_result.get("raw_files"),
        "sidecar": wave7_result.get("sidecar"),
        "message": "Mapping chain completed successfully",
        "error_code": None,
        "schema_version": schema_version,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview CleanJob mapping: intake JSON → CleanJob → Wave7 inputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python %(prog)s --intake-json fixtures/intake_basic_sample.json
    python %(prog)s --intake-json fixtures/intake_enrich_sample.json

Exit codes:
    0 — Success (mapping completed)
    1 — Failure (validation error or exception)
        """,
    )
    parser.add_argument(
        "--intake-json",
        required=True,
        metavar="PATH",
        help="Path to intake JSON file to validate",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print additional diagnostic info to stderr",
    )

    args = parser.parse_args()
    intake_path = Path(args.intake_json).expanduser().resolve()

    if args.verbose:
        print(f"[verbose] Loading intake from: {intake_path}", file=sys.stderr)

    result = run_preview(intake_path)

    # Output result as JSON to stdout
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))

    # Return appropriate exit code
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
