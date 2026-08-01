#!/usr/bin/env python3
"""Load case intake.json and resolve runner paths (Wave 2 P3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUPPORTED_FORMATS = frozenset({"csv", "tsv", "txt"})

_REQUIRED_PATH_KEYS = ("data_file",)


def _first_source(intake: dict[str, Any]) -> dict[str, Any]:
    sources = intake.get("data_sources")
    if isinstance(sources, list) and sources and isinstance(sources[0], dict):
        return sources[0]
    source = intake.get("source")
    if isinstance(source, dict):
        return source
    return {}


def _require_str(intake: dict[str, Any], source: dict[str, Any], *keys: str) -> tuple[str | None, str | None]:
    for key in keys:
        for container in (source, intake):
            val = container.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip(), None
    return None, f"missing_required_field:{keys[0]}"


def load_case_runner_config(case_dir: Path) -> dict[str, Any]:
    """Resolve paths and parse settings from case_dir/intake.json.

    Returns dict with ok=True and paths on success; ok=False + message on failure.
    Supports legacy flat intake (data_file, encoding) and nested source.* (P1 README).
    """
    case_dir = case_dir.resolve()
    if not case_dir.is_dir():
        return {
            "ok": False,
            "message": f"case_dir_not_found:{case_dir.name}",
            "human_readable": f"Case directory not found: {case_dir}",
        }

    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return {
            "ok": False,
            "message": "missing_intake_json",
            "human_readable": f"Missing intake.json in {case_dir.name}",
        }

    try:
        intake = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": f"invalid_intake_json:{exc}",
            "human_readable": f"Cannot parse intake.json: {exc}",
        }

    if not isinstance(intake, dict):
        return {
            "ok": False,
            "message": "invalid_intake_json:root_not_object",
            "human_readable": "intake.json root must be a JSON object",
        }

    source = _first_source(intake)
    data_rel, err = _require_str(intake, source, "source_file", "data_file", "raw_data_file", "primary_data_file")
    if err:
        return {
            "ok": False,
            "message": err,
            "human_readable": "intake.json must specify source.source_file or data_file (relative to case_dir)",
        }

    input_path = (case_dir / data_rel).resolve()
    try:
        input_path.relative_to(case_dir.resolve())
    except ValueError:
        return {
            "ok": False,
            "message": "data_file_outside_case_dir",
            "human_readable": f"Data file must live under case_dir: {data_rel}",
        }

    if not input_path.is_file():
        return {
            "ok": False,
            "message": f"missing_input_file:{data_rel}",
            "human_readable": f"Raw data file not found: {data_rel}",
        }

    file_format, fmt_err = _require_str(intake, source, "file_format")
    if fmt_err:
        suffix = input_path.suffix.lstrip(".").lower()
        file_format = "tsv" if suffix == "tsv" else "csv" if suffix in ("csv", "txt") else suffix

    file_format = (file_format or "").lower()
    if file_format not in SUPPORTED_FORMATS:
        return {
            "ok": False,
            "message": f"unsupported_file_format:{file_format}",
            "human_readable": (
                f"Unsupported file_format '{file_format}'; P3 runner supports csv/tsv only (xlsx deferred)"
            ),
        }

    encoding, enc_err = _require_str(intake, source, "encoding")
    if enc_err:
        encoding = "utf-8-sig"

    delimiter = source.get("delimiter") or intake.get("delimiter")
    if delimiter is None:
        delimiter = "\t" if file_format == "tsv" else ","
    if not isinstance(delimiter, str) or not delimiter:
        return {
            "ok": False,
            "message": "invalid_delimiter",
            "human_readable": "delimiter must be a non-empty string",
        }

    schema = intake.get("schema")
    if not isinstance(schema, dict):
        schema = intake.get("schema_definition")
    if not isinstance(schema, dict):
        schema = {}

    case_id = intake.get("case_id") or case_dir.name
    stem = input_path.stem
    cleaned_name = f"{stem}_cleaned.csv"
    cleaned_dir = case_dir / "cleaned"
    reports_dir = case_dir / "reports"

    return {
        "ok": True,
        "case_dir": case_dir,
        "case_id": case_id,
        "intake": intake,
        "intake_path": intake_path,
        "input_path": input_path,
        "input_rel": data_rel,
        "file_format": file_format,
        "encoding": encoding,
        "delimiter": delimiter,
        "schema": schema,
        "id_column": schema.get("id_column") or schema.get("primary_key"),
        "required_columns": schema.get("required_columns") or [],
        "nullable_columns": schema.get("nullable_columns") or [],
        "date_columns": schema.get("date_columns") or [],
        "percent_columns": schema.get("percent_columns") or [],
        "cleaned_dir": cleaned_dir,
        "reports_dir": reports_dir,
        "output_path": cleaned_dir / cleaned_name,
        "report_stats_path": reports_dir / "cleaning_stats.json",
        "report_json_path": reports_dir / "report.json",
        "report_md_path": reports_dir / "report.md",
        "job_id": intake.get("job_id") or f"case-{case_id}",
        "cleaning_profile": intake.get("cleaning_profile"),
    }
