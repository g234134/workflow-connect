#!/usr/bin/env python3
"""Low-risk tabular case eligibility gate (Wave 2 P2 · manual MVP).

Rules source: WAVE6_CLEAN_INTAKE_ELIGIBILITY_v0.1 (ACCEPT/REVIEW/REJECT intervals)
and C2-P1 §2.4 (2D tabular, scale, encoding). Does not run cleaning or prod pipeline.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Literal

EligibilityVerdict = Literal["accepted", "rejected", "review_needed"]
DimensionStatus = Literal["accepted", "rejected", "review_needed", "unknown"]

# Wave 6 scale thresholds (bytes / rows)
MIN_ROWS = 100
ACCEPT_MAX_ROWS = 1_000_000
REVIEW_MAX_ROWS = 10_000_000
MIN_BYTES = 1024
ACCEPT_MAX_BYTES = 1_000_000_000
REVIEW_MAX_BYTES = 10_000_000_000
ACCEPT_MAX_FIELDS = 100
REJECT_MAX_FIELDS = 500

ENCODING_WHITELIST = frozenset(
    {
        "utf-8",
        "utf-8-sig",
        "utf_8",
        "utf_8_sig",
        "gbk",
        "gb2312",
        "gb18030",
        "cp936",
    }
)
TABULAR_FORMATS = frozenset({"csv", "tsv", "txt"})
EXCEL_FORMATS = frozenset({"xlsx", "xls"})
SUPPORTED_FORMATS = TABULAR_FORMATS | EXCEL_FORMATS

REJECT_PROVENANCE = frozenset({"web_scraping", "web_scrape", "unknown"})
REJECT_SENSITIVITY = frozenset({"phi", "hipaa", "protected_health"})
REVIEW_SENSITIVITY = frozenset({"pii", "financial", "trade_secret", "restricted"})
REJECT_STRUCTURE = frozenset({"audio_video", "binary_unknown", "binary", "unknown"})
REVIEW_STRUCTURE = frozenset({"image", "mixed_document", "pdf", "ocr", "rich_markup"})

PII_NAME_PATTERN = re.compile(
    r"(email|e-mail|phone|mobile|tel|ssn|social.?security|passport|"
    r"身份证|手機|电话|邮箱|姓名|name)",
    re.IGNORECASE,
)

# CLEAN-BASIC / Phase demo expected header (C2-D1 · clean_phase_demo.COLUMNS)
PHASE_DEMO_COLUMNS = ("Phase", "名稱", "之前", "現在（建議）")
PHASE_DEMO_COLUMN_SET = frozenset(PHASE_DEMO_COLUMNS)
PHASE_DEMO_REQUIRED = ("Phase", "名稱")
SPRINT_PATTERN = re.compile(r"Sprint\s*\d+", re.IGNORECASE)
MULTI_ROW_MIN_ROWS = 20

EXIT_CODES = {"accepted": 0, "rejected": 1, "review_needed": 2}


def _norm_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _norm_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_norm_str(value)] if value.strip() else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            token = _norm_str(item)
            if token:
                out.append(token)
        return out
    return [_norm_str(value)] if str(value).strip() else []


def _load_intake(case_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    for name in ("intake.json", "intake_record.json"):
        path = case_dir / name
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                return None, f"invalid_intake_json:{exc}"
            if not isinstance(data, dict):
                return None, "invalid_intake_json:root_not_object"
            return data, None
    return None, "missing_intake_json"


def _first_source(intake: dict[str, Any]) -> dict[str, Any]:
    sources = intake.get("data_sources")
    if isinstance(sources, list) and sources and isinstance(sources[0], dict):
        return sources[0]
    return {}


def _resolve_data_file(case_dir: Path, intake: dict[str, Any]) -> Path | None:
    for key in ("data_file", "raw_data_file", "primary_data_file"):
        rel = intake.get(key)
        if isinstance(rel, str) and rel.strip():
            candidate = case_dir / rel.strip()
            if candidate.is_file():
                return candidate
    source = _first_source(intake)
    for key in ("stored_logical_path", "path", "file_name"):
        rel = source.get(key)
        if isinstance(rel, str) and rel.strip():
            candidate = case_dir / Path(rel.strip()).name
            if candidate.is_file():
                return candidate
            nested = case_dir / "raw" / Path(rel.strip()).name
            if nested.is_file():
                return nested
    search_roots = [case_dir, case_dir / "raw"]
    for root in search_roots:
        if not root.is_dir():
            continue
        for pattern in ("*.csv", "*.tsv", "*.txt", "*.xlsx", "*.xls"):
            matches = sorted(root.glob(pattern))
            if matches:
                return matches[0]
    return None


def _resolve_encoding(intake: dict[str, Any], source: dict[str, Any]) -> str:
    profile = intake.get("data_profile")
    if not isinstance(profile, dict):
        profile = {}
    for container in (intake, source, profile):
        enc = container.get("encoding")
        if isinstance(enc, str) and enc.strip():
            return enc.strip()
    return "utf-8"


def _resolve_format(intake: dict[str, Any], source: dict[str, Any], data_file: Path | None) -> str:
    profile = intake.get("data_profile")
    if not isinstance(profile, dict):
        profile = {}
    for container in (intake, source, profile):
        fmt = container.get("file_format")
        if isinstance(fmt, str) and fmt.strip():
            return _norm_str(fmt)
    if data_file is not None:
        return _norm_str(data_file.suffix.lstrip("."))
    return ""


def _resolve_scale(
    intake: dict[str, Any],
    source: dict[str, Any],
    data_file: Path | None,
) -> tuple[int | None, int | None]:
    profile = intake.get("data_profile")
    if not isinstance(profile, dict):
        profile = {}
    scale = intake.get("scale")
    if not isinstance(scale, dict):
        scale = {}

    row_count: int | None = None
    for container in (scale, intake, source, profile):
        for key in ("row_count", "row_count_estimate", "rows"):
            val = container.get(key)
            if isinstance(val, int) and val >= 0:
                row_count = val
                break
        if row_count is not None:
            break

    size_bytes: int | None = None
    for container in (scale, intake, source, profile):
        for key in ("file_size_bytes", "size_bytes", "total_size_bytes"):
            val = container.get(key)
            if isinstance(val, int) and val >= 0:
                size_bytes = val
                break
        if size_bytes is not None:
            break

    if data_file is not None:
        if size_bytes is None:
            size_bytes = data_file.stat().st_size
        if row_count is None and _norm_str(_resolve_format(intake, source, data_file)) in TABULAR_FORMATS:
            row_count = _count_csv_rows(data_file, _resolve_encoding(intake, source))

    return row_count, size_bytes


def _count_csv_rows(path: Path, encoding: str) -> int | None:
    try:
        with path.open(encoding=encoding, newline="") as fh:
            reader = csv.reader(fh)
            total = sum(1 for _ in reader)
            return max(total - 1, 0)
    except (OSError, UnicodeDecodeError, csv.Error):
        for fallback in ("utf-8-sig", "utf-8", "gbk"):
            try:
                with path.open(encoding=fallback, newline="") as fh:
                    reader = csv.reader(fh)
                    total = sum(1 for _ in reader)
                    return max(total - 1, 0)
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
    return None


def _read_csv_header(data_file: Path, encoding: str) -> list[str] | None:
    for enc in (encoding, "utf-8-sig", "utf-8", "gbk"):
        try:
            with data_file.open(encoding=enc, newline="") as fh:
                reader = csv.reader(fh)
                header = next(reader, None)
                if header:
                    return [col.strip() for col in header if col is not None]
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    return None


def _read_tabular_sample_rows(
    data_file: Path,
    encoding: str,
    *,
    max_rows: int = 500,
) -> list[dict[str, str]]:
    for enc in (encoding, "utf-8-sig", "utf-8", "gbk"):
        try:
            with data_file.open(encoding=enc, newline="") as fh:
                reader = csv.DictReader(fh)
                return [dict(row) for idx, row in enumerate(reader) if idx < max_rows]
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    return []


def _normalize_phase_key(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _probe_schema_dimension(
    data_file: Path | None,
    encoding: str,
    file_format: str,
    row_count: int | None,
    case_id: str | None,
    product_sku: str | None,
) -> dict[str, Any]:
    """Light header/content probe for CLEAN-BASIC Phase-like tables (observation only)."""
    clean_basic = _norm_str(product_sku) == "clean-basic"
    notes: list[str] = []
    column_names: list[str] | None = None
    warnings: list[str] = []

    if data_file is None or file_format not in TABULAR_FORMATS:
        return {
            "column_names": column_names,
            "notes": notes,
            "warnings": warnings,
            "probe_status": "unknown",
        }

    column_names = _read_csv_header(data_file, encoding)
    if not column_names:
        return {
            "column_names": None,
            "notes": ["header_unreadable"],
            "warnings": ["header_unreadable"],
            "probe_status": "unknown",
        }

    header_set = frozenset(column_names)
    missing_required = [col for col in PHASE_DEMO_REQUIRED if col not in header_set]
    if missing_required:
        notes.append("schema_mismatch")
        notes.append("missing_required_columns")
        warnings.append("missing_required_columns:" + ",".join(missing_required))
        return {
            "column_names": column_names,
            "notes": notes,
            "warnings": warnings,
            "probe_status": "mismatch" if clean_basic else "non_phase",
        }

    if header_set == PHASE_DEMO_COLUMN_SET:
        notes.append("phase_like")
        if _norm_str(case_id) == "demo_phase":
            notes.append("phase_demo")
    elif PHASE_DEMO_COLUMN_SET.issubset(header_set):
        notes.append("phase_like")
        notes.append("extra_columns")
        warnings.append("extra_columns")
    elif header_set.issubset(PHASE_DEMO_COLUMN_SET):
        notes.append("phase_like_partial")
        missing_optional = [col for col in PHASE_DEMO_COLUMNS if col not in header_set]
        if missing_optional:
            warnings.append("missing_optional_columns:" + ",".join(missing_optional))
    else:
        notes.append("non_phase_schema")
        if clean_basic:
            notes.append("schema_mismatch")
            warnings.append("header_set_differs_from_phase_demo")
        return {
            "column_names": column_names,
            "notes": notes,
            "warnings": warnings,
            "probe_status": "mismatch" if clean_basic else "non_phase",
        }

    effective_rows = row_count
    sample_rows = _read_tabular_sample_rows(data_file, encoding)
    if effective_rows is None and sample_rows:
        effective_rows = len(sample_rows)

    if effective_rows is not None and effective_rows >= MULTI_ROW_MIN_ROWS and "phase_like" in notes:
        phase_values = [_normalize_phase_key(row.get("Phase")) for row in sample_rows if row.get("Phase")]
        unique_phases = len({v for v in phase_values if v})
        sprint_hits = sum(
            1 for row in sample_rows if SPRINT_PATTERN.search(str(row.get("名稱") or ""))
        )
        duplicate_ratio = 0.0
        if phase_values:
            duplicate_ratio = 1.0 - (unique_phases / len(phase_values))

        multi_row = sprint_hits > 0 or (
            unique_phases > 0 and effective_rows > max(MULTI_ROW_MIN_ROWS, unique_phases * 2)
        )
        if multi_row:
            notes.append("multi_row_export")
            notes.append("schema_ambiguous")
            warnings.append("phase_like_headers_but_multi_row_or_sprint_pattern")

    return {
        "column_names": column_names,
        "notes": notes,
        "warnings": warnings,
        "probe_status": "phase_like" if "phase_like" in notes else "partial",
    }


def _resolve_field_count(
    intake: dict[str, Any],
    data_file: Path | None,
    encoding: str,
    file_format: str,
) -> int | None:
    schema = intake.get("schema")
    if not isinstance(schema, dict):
        schema = intake.get("schema_definition")
    if not isinstance(schema, dict):
        schema = {}
    for key in ("field_count", "column_count", "fields"):
        val = schema.get(key)
        if isinstance(val, int) and val >= 0:
            return val
        if isinstance(val, list):
            return len(val)

    if data_file is None or file_format not in TABULAR_FORMATS:
        return None

    for enc in (encoding, "utf-8-sig", "utf-8", "gbk"):
        try:
            with data_file.open(encoding=enc, newline="") as fh:
                reader = csv.reader(fh)
                header = next(reader, None)
                if header:
                    return len(header)
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    return None


def _collect_sensitivity_flags(intake: dict[str, Any]) -> list[str]:
    flags = _norm_list(intake.get("sensitivity"))
    security = intake.get("security_compliance")
    if isinstance(security, dict) and security.get("contains_pii") is True:
        if "pii" not in flags:
            flags.append("pii")
    schema = intake.get("schema")
    if not isinstance(schema, dict):
        schema = intake.get("schema_definition")
    if isinstance(schema, dict):
        pii_fields = schema.get("pii_fields")
        if isinstance(pii_fields, list) and pii_fields and "pii" not in flags:
            flags.append("pii")
    return flags


def _collect_pii_field_names(intake: dict[str, Any], data_file: Path | None, encoding: str, file_format: str) -> list[str]:
    names: list[str] = []
    schema = intake.get("schema")
    if not isinstance(schema, dict):
        schema = intake.get("schema_definition")
    if isinstance(schema, dict):
        pii_fields = schema.get("pii_fields")
        if isinstance(pii_fields, list):
            names.extend(str(x) for x in pii_fields if str(x).strip())

    if data_file is not None and file_format in TABULAR_FORMATS:
        for enc in (encoding, "utf-8-sig", "utf-8", "gbk"):
            try:
                with data_file.open(encoding=enc, newline="") as fh:
                    reader = csv.reader(fh)
                    header = next(reader, None)
                    if header:
                        for col in header:
                            if PII_NAME_PATTERN.search(col):
                                names.append(col)
                break
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
    return sorted(set(names))


def _scale_status(row_count: int | None, size_bytes: int | None) -> tuple[DimensionStatus, list[str]]:
    reasons: list[str] = []
    worst: DimensionStatus = "accepted"

    def bump(status: DimensionStatus) -> None:
        nonlocal worst
        order = {"accepted": 0, "unknown": 1, "review_needed": 2, "rejected": 3}
        if order[status] > order[worst]:
            worst = status

    if row_count is not None:
        if row_count > REVIEW_MAX_ROWS:
            reasons.append(f"rows>{REVIEW_MAX_ROWS}")
            bump("rejected")
        elif row_count > ACCEPT_MAX_ROWS:
            reasons.append(f"rows>{ACCEPT_MAX_ROWS}")
            bump("review_needed")
        elif row_count < MIN_ROWS:
            reasons.append(f"rows<{MIN_ROWS}")
            bump("review_needed")
    else:
        bump("unknown")
        reasons.append("row_count_unknown")

    if size_bytes is not None:
        if size_bytes > REVIEW_MAX_BYTES:
            reasons.append(f"size>{REVIEW_MAX_BYTES}")
            bump("rejected")
        elif size_bytes > ACCEPT_MAX_BYTES:
            reasons.append(f"size>{ACCEPT_MAX_BYTES}")
            bump("review_needed")
        elif size_bytes < MIN_BYTES:
            reasons.append(f"size<{MIN_BYTES}")
            bump("review_needed")
    else:
        bump("unknown")
        reasons.append("file_size_unknown")

    if worst == "accepted" and "unknown" in reasons:
        worst = "unknown"
    return worst, reasons


def _aggregate_verdict(*statuses: DimensionStatus) -> EligibilityVerdict:
    if "rejected" in statuses:
        return "rejected"
    if "review_needed" in statuses or "unknown" in statuses:
        return "review_needed"
    return "accepted"


def check_case_eligibility(case_dir: Path) -> dict[str, Any]:
    """Evaluate low-risk eligibility for a single on-disk case directory."""
    case_dir = case_dir.resolve()
    reasons: list[str] = []
    review_reasons: list[str] = []
    reason_code: str | None = None

    if not case_dir.is_dir():
        return {
            "ok": False,
            "eligibility": "rejected",
            "reason_code": "case_dir_missing",
            "human_readable": f"Case directory not found: {case_dir.name}",
            "case_dir": str(case_dir),
            "dimensions": {},
            "exit_code": EXIT_CODES["rejected"],
        }

    intake, intake_err = _load_intake(case_dir)
    if intake is None:
        return {
            "ok": False,
            "eligibility": "review_needed",
            "reason_code": intake_err,
            "human_readable": "Missing or invalid intake.json; cannot run eligibility gate",
            "case_dir": str(case_dir),
            "dimensions": {"intake": {"status": "unknown", "details": intake_err or ""}},
            "exit_code": EXIT_CODES["review_needed"],
        }

    source = _first_source(intake)
    data_file = _resolve_data_file(case_dir, intake)
    encoding = _resolve_encoding(intake, source)
    file_format = _resolve_format(intake, source, data_file)
    row_count, size_bytes = _resolve_scale(intake, source, data_file)
    field_count = _resolve_field_count(intake, data_file, encoding, file_format)

    provenance = intake.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    source_type = _norm_str(provenance.get("source_type") or provenance.get("type") or intake.get("source_type"))
    structure = _norm_str(intake.get("structure") or provenance.get("structure") or "text_only")
    sensitivity_flags = _collect_sensitivity_flags(intake)
    pii_field_names = _collect_pii_field_names(intake, data_file, encoding, file_format)

    dimensions: dict[str, Any] = {}

    # --- provenance (hard reject first) ---
    prov_status: DimensionStatus = "accepted"
    if source_type in REJECT_PROVENANCE:
        prov_status = "rejected"
        reason_code = "provenance_web_scrape" if "web" in source_type else "provenance_unverifiable"
        reasons.append(reason_code)
    elif not source_type:
        prov_status = "review_needed"
        review_reasons.append("provenance_unspecified")
    expiry = provenance.get("license_expiry_days")
    if isinstance(expiry, int) and expiry < 30:
        prov_status = "review_needed" if prov_status == "accepted" else prov_status
        review_reasons.append("license_expiry_risk")
    dimensions["provenance"] = {"status": prov_status, "source_type": source_type or None}

    # --- sensitivity ---
    sens_status: DimensionStatus = "accepted"
    if any(flag in REJECT_SENSITIVITY for flag in sensitivity_flags):
        sens_status = "rejected"
        reason_code = reason_code or "phi_not_supported"
        reasons.append("phi_not_supported")
    elif any(flag in REVIEW_SENSITIVITY for flag in sensitivity_flags):
        sens_status = "review_needed"
        review_reasons.append("sensitivity_review:" + ",".join(sensitivity_flags))
    elif pii_field_names and "pii" not in sensitivity_flags:
        sens_status = "review_needed"
        review_reasons.append("possible_pii_columns")
    dimensions["sensitivity"] = {
        "status": sens_status,
        "flags": sensitivity_flags,
        "pii_field_names": pii_field_names,
    }

    # --- structure / format ---
    struct_status: DimensionStatus = "accepted"
    if structure in REJECT_STRUCTURE:
        struct_status = "rejected"
        reason_code = reason_code or (
            "format_av_unsupported" if structure == "audio_video" else "format_unsupported"
        )
        reasons.append(reason_code)
    elif structure in REVIEW_STRUCTURE:
        struct_status = "review_needed"
        review_reasons.append(f"structure:{structure}")
    if file_format and file_format not in SUPPORTED_FORMATS:
        struct_status = "rejected" if struct_status != "rejected" else struct_status
        if struct_status != "rejected":
            struct_status = "review_needed"
        review_reasons.append(f"unsupported_format:{file_format}")
    if data_file is None:
        struct_status = "review_needed" if struct_status == "accepted" else struct_status
        review_reasons.append("data_file_missing")
    elif file_format in TABULAR_FORMATS:
        # C2-P1 §2.4: must parse as 2D table
        if field_count is None or field_count < 1:
            struct_status = "review_needed" if struct_status != "rejected" else struct_status
            review_reasons.append("not_2d_tabular")
    if file_format in EXCEL_FORMATS:
        sheet = intake.get("excel_sheet") or intake.get("target_sheet")
        if not sheet:
            struct_status = "review_needed" if struct_status == "accepted" else struct_status
            review_reasons.append("excel_sheet_unspecified")
    dimensions["structure"] = {
        "status": struct_status,
        "structure": structure or None,
        "file_format": file_format or None,
        "data_file": data_file.name if data_file else None,
    }

    # --- scale ---
    scale_status, scale_reasons = _scale_status(row_count, size_bytes)
    if scale_status == "rejected":
        reason_code = reason_code or "scale_exceeds_capacity"
        reasons.extend(scale_reasons)
    elif scale_status in ("review_needed", "unknown"):
        review_reasons.extend(scale_reasons)
    dimensions["scale"] = {
        "status": scale_status,
        "row_count": row_count,
        "file_size_bytes": size_bytes,
        "details": ", ".join(scale_reasons) if scale_reasons else "within_accept",
    }

    # --- schema / fields + header probe (Wave 4B · observation only) ---
    field_status: DimensionStatus = "accepted"
    if field_count is not None:
        if field_count > REJECT_MAX_FIELDS:
            field_status = "rejected"
            reason_code = reason_code or "field_count_exceeds_capacity"
            reasons.append(f"fields>{REJECT_MAX_FIELDS}")
        elif field_count > ACCEPT_MAX_FIELDS:
            field_status = "review_needed"
            review_reasons.append(f"fields>{ACCEPT_MAX_FIELDS}")
    else:
        field_status = "unknown"
        review_reasons.append("field_count_unknown")

    case_id = intake.get("case_id") or case_dir.name
    product_sku = intake.get("product_sku")
    schema_probe = _probe_schema_dimension(
        data_file,
        encoding,
        file_format,
        row_count,
        str(case_id) if case_id else None,
        str(product_sku) if product_sku else None,
    )
    schema_notes: list[str] = list(schema_probe.get("notes") or [])
    schema_warnings: list[str] = list(schema_probe.get("warnings") or [])

    if _norm_str(product_sku) == "clean-basic":
        if schema_probe.get("probe_status") == "mismatch":
            if field_status == "accepted":
                field_status = "review_needed"
            review_reasons.append("schema_header_mismatch")
        elif schema_probe.get("probe_status") == "unknown" and schema_notes:
            if field_status == "accepted":
                field_status = "review_needed"
            review_reasons.append(schema_notes[0])

    # phase_like + multi_row_export: keep dimension accepted; warnings in notes only
    dimensions["schema"] = {
        "status": field_status,
        "field_count": field_count,
        "column_names": schema_probe.get("column_names"),
        "notes": schema_notes,
        "warnings": schema_warnings,
    }

    # --- encoding / delimiter (C2-P1 §2.4) ---
    enc_status: DimensionStatus = "accepted"
    enc_norm = _norm_str(encoding).replace("utf8", "utf-8")
    if enc_norm not in ENCODING_WHITELIST:
        enc_status = "review_needed"
        review_reasons.append(f"encoding_not_whitelisted:{encoding}")
    delimiter = intake.get("delimiter") or source.get("delimiter") or ","
    if delimiter not in {",", ";", "\t", "|"}:
        enc_status = "review_needed" if enc_status == "accepted" else enc_status
        review_reasons.append(f"delimiter_unusual:{delimiter!r}")
    dimensions["encoding"] = {"status": enc_status, "encoding": encoding, "delimiter": delimiter}

    verdict = _aggregate_verdict(
        prov_status,
        sens_status,
        struct_status,
        scale_status,
        field_status,
        enc_status,
    )

    if verdict == "accepted":
        human = "Case matches low-risk tabular profile; eligible for manual cleaning pipeline"
    elif verdict == "rejected":
        human = "Case fails low-risk eligibility; do not auto-accept"
    else:
        human = "Case needs manual review before cleaning"

    all_notes = reasons + review_reasons
    return {
        "ok": True,
        "eligibility": verdict,
        "reason_code": reason_code or (review_reasons[0] if review_reasons else None),
        "human_readable": human,
        "case_dir": str(case_dir),
        "case_id": intake.get("case_id") or case_dir.name,
        "dimensions": dimensions,
        "review_reasons": review_reasons,
        "reject_reasons": reasons,
        "notes": all_notes,
        "exit_code": EXIT_CODES[verdict],
        "spec_refs": [
            "04_Workflows/WAVE6_CLEAN_INTAKE_ELIGIBILITY_v0.1.md",
            "docs/PRODUCT_TABULAR_CLEANING.md §2.4",
        ],
    }
