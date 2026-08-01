"""Generic low-risk tabular cleaning (profile: generic_low_risk_profile).

Supports simple tables with primary key + numeric / category / text columns.
Schema roles are resolved from intake.json via cleaning_profiles_v1.build_runtime_profile.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_COLUMN_TYPES = frozenset({"primary_key", "numeric", "category", "text"})


def is_blank(value: str | None) -> bool:
    return value is None or str(value).strip() == ""


def read_rows(path: Path, *, encoding: str = "utf-8-sig", delimiter: str = ",") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        return [dict(row) for row in reader]


def write_rows(path: Path, rows: list[dict[str, object]], *, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def parse_numeric(value: str) -> tuple[float | None, str | None]:
    if is_blank(value):
        return None, None
    raw = str(value).strip().replace(",", "")
    try:
        return float(raw), None
    except ValueError:
        return None, f"unparseable:{raw}"


def _columns_from_profile(profile_cfg: dict[str, Any]) -> list[str]:
    return list(profile_cfg.get("columns") or [])


def _role_map(profile_cfg: dict[str, Any]) -> dict[str, str]:
    return dict(profile_cfg.get("field_roles") or {})


def _primary_key(profile_cfg: dict[str, Any]) -> str | None:
    pk = profile_cfg.get("primary_key")
    if isinstance(pk, str) and pk.strip():
        return pk.strip()
    roles = _role_map(profile_cfg)
    for col, role in roles.items():
        if role == "primary_key":
            return col
    return None


def _columns_by_role(profile_cfg: dict[str, Any], role: str) -> list[str]:
    roles = _role_map(profile_cfg)
    return [col for col, r in roles.items() if r == role]


def profile(rows: list[dict[str, str]], *, profile_cfg: dict[str, Any]) -> dict[str, Any]:
    columns = _columns_from_profile(profile_cfg)
    pk = _primary_key(profile_cfg)
    numeric_cols = _columns_by_role(profile_cfg, "numeric")

    n_rows = len(rows)
    missing_by_col: dict[str, int] = {col: 0 for col in columns}
    for row in rows:
        for col in columns:
            if is_blank(row.get(col)):
                missing_by_col[col] += 1

    row_keys = [tuple((row.get(col) or "").strip() for col in columns) for row in rows]
    duplicate_full_rows = n_rows - len(set(row_keys))

    pk_values = [(row.get(pk) or "").strip() for row in rows if pk and not is_blank(row.get(pk))]
    pk_counter = Counter(pk_values)
    duplicate_pk_keys = sum(1 for _, count in pk_counter.items() if count > 1)

    format_issues: list[dict[str, Any]] = []
    range_issues: list[dict[str, Any]] = []
    numeric_range = profile_cfg.get("numeric_range") or {}

    for idx, row in enumerate(rows, start=2):
        for col in numeric_cols:
            num, note = parse_numeric(row.get(col, ""))
            if note and note.startswith("unparseable"):
                format_issues.append({"row": idx, "field": col, "issue": note, "value": row.get(col)})
            elif num is not None:
                col_range = numeric_range.get(col) if isinstance(numeric_range, dict) else None
                lo = col_range.get("min") if isinstance(col_range, dict) else profile_cfg.get("numeric_min")
                hi = col_range.get("max") if isinstance(col_range, dict) else profile_cfg.get("numeric_max")
                if lo is not None and num < float(lo):
                    range_issues.append({"row": idx, "field": col, "value": num, "issue": "below_min"})
                elif hi is not None and num > float(hi):
                    range_issues.append({"row": idx, "field": col, "value": num, "issue": "above_max"})

    return {
        "row_count": n_rows,
        "column_count": len(columns),
        "missing_by_column": {
            col: {"count": missing_by_col[col], "rate": round(missing_by_col[col] / n_rows, 4) if n_rows else 0}
            for col in columns
        },
        "duplicate_full_rows": duplicate_full_rows,
        "duplicate_primary_keys": duplicate_pk_keys,
        "primary_key_value_counts": dict(pk_counter),
        "format_issues": format_issues,
        "range_issues": range_issues,
        "cleaning_profile_id": profile_cfg.get("profile_id"),
    }


def clean(rows: list[dict[str, str]], *, profile_cfg: dict[str, Any]) -> tuple[list[dict[str, object]], dict[str, Any]]:
    columns = _columns_from_profile(profile_cfg)
    pk = _primary_key(profile_cfg)
    numeric_cols = _columns_by_role(profile_cfg, "numeric")
    category_cols = _columns_by_role(profile_cfg, "category")
    text_cols = _columns_by_role(profile_cfg, "text")
    compare_col = profile_cfg.get("dedup_compare_column") or (numeric_cols[0] if numeric_cols else None)
    drop_blank_pk = profile_cfg.get("drop_if_blank") or ([pk] if pk else [])

    cleaned: list[dict[str, object]] = []
    dropped_rows: list[dict[str, Any]] = []
    deduped_rows: list[dict[str, Any]] = []
    range_flags: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=2):
        skip = False
        for col in drop_blank_pk:
            if col and is_blank(row.get(col)):
                dropped_rows.append({"row": idx, "reason": f"missing_{col}", "field": col})
                skip = True
                break
        if skip:
            continue

        record: dict[str, object] = {"_source_row": idx, "_flags": []}

        for col in columns:
            raw = row.get(col, "")
            role = _role_map(profile_cfg).get(col, "text")

            if role == "primary_key":
                record[col] = str(raw).strip()
            elif role == "numeric":
                num, note = parse_numeric(str(raw))
                if note and note.startswith("unparseable"):
                    record["_flags"].append(f"{col}:{note}")
                    record[col] = ""
                elif num is not None:
                    numeric_range = profile_cfg.get("numeric_range") or {}
                    col_range = numeric_range.get(col) if isinstance(numeric_range, dict) else {}
                    lo = col_range.get("min") if isinstance(col_range, dict) else profile_cfg.get("numeric_min")
                    hi = col_range.get("max") if isinstance(col_range, dict) else profile_cfg.get("numeric_max")
                    if lo is not None and num < float(lo):
                        record["_flags"].append(f"{col}:below_min")
                        range_flags.append({"row": idx, "field": col, "value": num})
                    elif hi is not None and num > float(hi):
                        record["_flags"].append(f"{col}:above_max")
                        range_flags.append({"row": idx, "field": col, "value": num})
                    record[col] = round(num, 4) if num is not None else ""
                else:
                    record[col] = ""
            elif role == "category":
                val = str(raw).strip()
                record[col] = val
                if is_blank(val):
                    record["_flags"].append(f"{col}:missing_category")
            else:
                record[col] = str(raw).strip()

        cleaned.append(record)

    dedup_keys = profile_cfg.get("dedup_keys") or ([pk] if pk else [])
    by_key: dict[str, dict[str, object]] = {}
    for record in cleaned:
        key = "|".join(str(record.get(k, "")).strip() for k in dedup_keys)
        current = by_key.get(key)
        if current is None:
            by_key[key] = record
            continue
        if compare_col:
            try:
                keep_new = float(record.get(compare_col) or -1) > float(current.get(compare_col) or -1)
            except (TypeError, ValueError):
                keep_new = False
        else:
            keep_new = False
        if keep_new:
            deduped_rows.append({**current, "_dedupe_action": "dropped_older"})
            by_key[key] = record
        else:
            deduped_rows.append({**record, "_dedupe_action": "dropped_duplicate"})

    final_rows = list(by_key.values())
    if pk:
        final_rows.sort(key=lambda r: str(r.get(pk, "")))

    output_rows = [{col: r.get(col, "") for col in columns} for r in final_rows]
    meta = {
        "dropped_rows": dropped_rows,
        "deduped_rows": [r for r in deduped_rows if r.get("_dedupe_action")],
        "range_flags": range_flags,
        "output_row_count": len(output_rows),
        "cleaning_profile_id": profile_cfg.get("profile_id"),
        "dedup_keys": dedup_keys,
    }
    return output_rows, meta


def _missing_rate_by_field(before: dict, after: dict, columns: list[str]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for col in columns:
        before_rate = before["missing_by_column"][col]["rate"]
        after_rate = after["missing_by_column"][col]["rate"]
        result[col] = {"before": before_rate, "after": after_rate}
    return result


def build_quality_report(
    before: dict,
    after: dict,
    clean_meta: dict,
    raw_rows: list[dict[str, str]],
    input_rows: int,
    output_rows: int,
    *,
    job_id: str,
    case_id: str | None = None,
    client_ref: str | None = None,
    product_sku: str | None = None,
    profile_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = profile_cfg or {}
    columns = _columns_from_profile(cfg)
    case_id = case_id or "unknown"
    client_ref = client_ref or "unknown"
    product_sku = product_sku or "CLEAN-BASIC"
    profile_id = cfg.get("profile_id")
    generated_at = datetime.now(timezone.utc).isoformat()
    dedup_removed = len(clean_meta.get("deduped_rows", []))
    dropped = len(clean_meta.get("dropped_rows", []))

    product_metrics = {
        "total_rows": input_rows,
        "accepted_rows": output_rows,
        "rejected_rows": dropped,
        "duplicate_rows_found": dedup_removed,
        "duplicate_rows_removed": dedup_removed,
        "missing_rate_by_field": _missing_rate_by_field(before, after, columns),
        "anomaly_count_by_rule": {
            "numeric_out_of_range": len(before.get("range_issues", [])),
            "format_unparseable": len(before.get("format_issues", [])),
        },
        "format_fixes_applied": {
            "text_trimmed": sum(
                1 for row in raw_rows for col in columns if str(row.get(col, "")) != str(row.get(col, "")).strip()
            ),
            "numeric_parsed": sum(
                1
                for row in raw_rows
                for col in _columns_by_role(cfg, "numeric")
                if not is_blank(row.get(col)) and parse_numeric(str(row.get(col)))[0] is not None
            ),
        },
    }

    stats_block = {
        "row_counts": {
            "intake": input_rows,
            "after_dedup": input_rows - dropped,
            "ok": output_rows,
            "rejected": dropped,
        },
        "missing_value_stats": [
            {
                "field": col,
                "missing_before": before["missing_by_column"][col]["count"],
                "missing_after": after["missing_by_column"][col]["count"],
                "rate_before": before["missing_by_column"][col]["rate"],
                "rate_after": after["missing_by_column"][col]["rate"],
            }
            for col in columns
        ],
        "processing_time_ms": 0,
    }

    error_categories = [
        {"code": "MISSING-KEY", "count": dropped, "severity": "P1"},
        {"code": "RANGE-ANOMALY", "count": len(clean_meta.get("range_flags", [])), "severity": "P2"},
    ]

    return {
        "meta": {
            "schema_version": "c2-demo-v1",
            "job_id": job_id,
            "report_type": "clean_basic_generic",
            "cleaning_profile_id": profile_id,
            "generated_at": generated_at,
            "disclaimer": "Generic low-risk profile; manual review recommended for first use",
            "product_spec_ref": "docs/PRODUCT_TABULAR_CLEANING.md",
            "template_ref": "04_Workflows/WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md",
            "cleaning_profile_ref": "docs/tabular-cleaning-profiles-v1.md",
        },
        "case_id": case_id,
        "client_ref": client_ref,
        "product_sku": product_sku,
        "generated_at": generated_at,
        "summary": {
            "job_id": job_id,
            "sku": product_sku,
            "total_rows": input_rows,
            "accepted_rows": output_rows,
            "accepted_units": output_rows,
            "rejected_rows": dropped,
            "rejected_units": dropped,
            "qa_status": "pass_with_warnings",
            "completion_variant": "completed_with_failures",
            "chargeable_hint": False,
        },
        "product_metrics": product_metrics,
        "cleaning_stats": {
            "row_counts": stats_block["row_counts"],
            "missing_value_stats": stats_block["missing_value_stats"],
            "product_metrics": product_metrics,
        },
        "issues_summary": {
            "qa_status": "pass_with_warnings",
            "completion_variant": "completed_with_failures",
            "error_categories": error_categories,
            "top_errors_sample": clean_meta.get("range_flags", [])[:5],
        },
        "stats": stats_block,
        "errors": {
            "error_categories": error_categories,
            "top_errors_sample": clean_meta.get("range_flags", [])[:5],
        },
        "next_steps": {
            "for_customer": [
                "Review flagged numeric anomalies and unparseable values.",
                "Confirm dedup rule (keep highest numeric compare column) matches business expectation.",
            ],
            "recommended_actions": [
                {"action": "review_warnings", "priority": "medium", "reason": "generic profile first-run review"},
            ],
        },
        "cleaning_rules_applied": [
            {"rule": rule_id, "description": rule_id.replace("_", " ")}
            for rule_id in (cfg.get("cleaning_rules_applied") or [])
        ],
        "cleaning_profile_id": profile_id,
    }


def write_quality_report_md(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pm = report["product_metrics"]
    case_id = report.get("case_id") or "unknown"
    client_ref = report.get("client_ref") or "unknown"
    stats = report.get("stats") or {}
    row_counts = stats.get("row_counts") or {}
    profile_id = report.get("cleaning_profile_id") or report.get("meta", {}).get("cleaning_profile_id")
    col_count = len(pm.get("missing_rate_by_field") or {})
    lines = [
        f"# {case_id} · {client_ref} · 品質戰報摘要（report.md）",
        "",
        f"> **case_id**: `{case_id}` · **client_ref**: `{client_ref}` · **profile**: `{profile_id}`",
        "",
        "## 数据概览",
        "",
        f"- 行数：intake `{row_counts.get('intake', pm['total_rows'])}` → accepted `{row_counts.get('ok', pm['accepted_rows'])}`",
        f"- 列数：`{col_count}` · `cleaning_profile_id`: `{profile_id}`",
        f"- `qa_status`：`{report['summary']['qa_status']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
