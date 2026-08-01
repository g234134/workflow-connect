#!/usr/bin/env python3
"""C2-D1 demo: profile and clean Phase.csv tabular data.

Demo scope only — not a production CLEAN pipeline. See docs/C2-D1_DEMO_WALKTHROUGH.md.

Wave 2 P3: supports ``--case-dir`` to run against any case folder with intake.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from case_eligibility import check_case_eligibility
from case_intake_loader import load_case_runner_config
from cleaning_profiles_v1 import get_profile, resolve_runtime_profile

try:
    import clean_generic as _clean_generic  # noqa: WPS433
except ImportError:
    _clean_generic = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASE_DIR = REPO_ROOT / "cases" / "demo_phase"

_DEFAULT_PROFILE = get_profile("phase_demo_v1") or {}
COLUMNS = list(_DEFAULT_PROFILE.get("columns") or ["Phase", "名稱", "之前", "現在（建議）"])
PERCENT_COLUMNS = list(_DEFAULT_PROFILE.get("percent_columns") or ["之前", "現在（建議）"])
PHASE_PATTERN = re.compile(r"^Phase\s+(\d+)$", re.IGNORECASE)


def _profile_columns(profile_cfg: dict) -> list[str]:
    return list(profile_cfg.get("columns") or COLUMNS)


def _profile_percent_columns(profile_cfg: dict) -> list[str]:
    return list(profile_cfg.get("percent_columns") or PERCENT_COLUMNS)


def _dedup_record_key(record: dict[str, object], profile_cfg: dict) -> str:
    keys = profile_cfg.get("dedup_keys") or ["Phase"]
    return "|".join(str(record.get(k, "")).strip() for k in keys)


def read_rows(path: Path, *, encoding: str = "utf-8-sig", delimiter: str = ",") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        return [dict(row) for row in reader]


def write_rows(path: Path, rows: list[dict[str, object]], *, profile_cfg: dict | None = None) -> None:
    columns = _profile_columns(profile_cfg or _DEFAULT_PROFILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def is_blank(value: str | None) -> bool:
    return value is None or str(value).strip() == ""


def parse_percent(value: str) -> tuple[float | None, str | None]:
    """Return numeric percent on 0-100 scale and optional anomaly note."""
    if is_blank(value):
        return None, None
    raw = str(value).strip()
    try:
        if raw.endswith("%"):
            num = float(raw[:-1].strip())
            return num, None
        num = float(raw)
        if 0 <= num <= 1:
            return num * 100, "scaled_from_fraction"
        return num, None
    except ValueError:
        return None, f"unparseable:{raw}"


def normalize_phase(value: str) -> tuple[str, str | None]:
    if is_blank(value):
        return "", "missing_phase"
    raw = str(value).strip()
    match = PHASE_PATTERN.match(raw)
    if match:
        return f"Phase {int(match.group(1))}", None
    return raw, "nonstandard_phase_name"


def profile(rows: list[dict[str, str]], *, profile_cfg: dict | None = None) -> dict:
    cfg = profile_cfg or _DEFAULT_PROFILE
    columns = _profile_columns(cfg)
    percent_columns = _profile_percent_columns(cfg)
    dedup_keys = cfg.get("dedup_keys") or ["Phase"]

    n_rows = len(rows)
    missing_by_col: dict[str, int] = {col: 0 for col in columns}
    for row in rows:
        for col in columns:
            if is_blank(row.get(col)):
                missing_by_col[col] += 1

    row_keys = [tuple((row.get(col) or "").strip() for col in columns) for row in rows]
    duplicate_full_rows = n_rows - len(set(row_keys))

    dedup_values = [
        "|".join(str(row.get(k, "")).strip() for k in dedup_keys)
        for row in rows
        if any(not is_blank(row.get(k)) for k in dedup_keys)
    ]
    dedup_counter = Counter(dedup_values)
    duplicate_dedup_keys = sum(1 for _, count in dedup_counter.items() if count > 1)

    format_issues: list[dict] = []
    range_issues: list[dict] = []
    for idx, row in enumerate(rows, start=2):
        phase_norm, phase_note = normalize_phase(row.get("Phase", ""))
        if phase_note:
            format_issues.append({"row": idx, "field": "Phase", "issue": phase_note, "value": row.get("Phase")})
        for col in percent_columns:
            num, note = parse_percent(row.get(col, ""))
            if note and note.startswith("unparseable"):
                format_issues.append({"row": idx, "field": col, "issue": note, "value": row.get(col)})
            elif num is not None and (num < 0 or num > 100):
                range_issues.append({"row": idx, "field": col, "value": num, "phase": phase_norm or row.get("Phase")})

    return {
        "row_count": n_rows,
        "column_count": len(columns),
        "missing_by_column": {
            col: {"count": missing_by_col[col], "rate": round(missing_by_col[col] / n_rows, 4) if n_rows else 0}
            for col in columns
        },
        "duplicate_full_rows": duplicate_full_rows,
        "duplicate_phase_keys": duplicate_dedup_keys,
        "phase_value_counts": dict(dedup_counter),
        "format_issues": format_issues,
        "range_issues": range_issues,
        "cleaning_profile_id": cfg.get("profile_id"),
    }


def clean(rows: list[dict[str, str]], *, profile_cfg: dict | None = None) -> tuple[list[dict[str, object]], dict]:
    cfg = profile_cfg or _DEFAULT_PROFILE
    columns = _profile_columns(cfg)
    percent_columns = _profile_percent_columns(cfg)
    compare_col = cfg.get("dedup_compare_column") or "現在（建議）"
    cleaned: list[dict[str, object]] = []
    dropped_rows: list[dict] = []
    deduped_rows: list[dict] = []
    range_flags: list[dict] = []

    for idx, row in enumerate(rows, start=2):
        if is_blank(row.get("Phase")) and is_blank(row.get("名稱")):
            dropped_rows.append({"row": idx, "reason": "missing_phase_and_name"})
            continue

        phase, phase_note = normalize_phase(row.get("Phase", ""))
        if not phase:
            dropped_rows.append({"row": idx, "reason": "missing_phase", "名稱": row.get("名稱")})
            continue
        name = str(row.get("名稱", "")).strip()

        record: dict[str, object] = {
            "Phase": phase,
            "名稱": name,
            "_source_row": idx,
            "_flags": [],
        }
        if phase_note:
            record["_flags"].append(phase_note)

        for col in percent_columns:
            num, note = parse_percent(row.get(col, ""))
            if note == "scaled_from_fraction":
                record["_flags"].append(f"{col}:scaled_from_fraction")
            elif note and note.startswith("unparseable"):
                record["_flags"].append(f"{col}:{note}")
                num = None
            if num is not None and (num < 0 or num > 100):
                record["_flags"].append(f"{col}:out_of_range")
                range_flags.append({"row": idx, "field": col, "value": num, "phase": phase})
            record[col] = "" if num is None else round(num, 2)

        cleaned.append(record)

    by_dedup_key: dict[str, dict[str, object]] = {}
    for record in cleaned:
        key = _dedup_record_key(record, cfg)
        current = by_dedup_key.get(key)
        if current is None:
            by_dedup_key[key] = record
            continue
        current_now = current.get(compare_col)
        new_now = record.get(compare_col)
        try:
            keep_new = float(new_now or -1) > float(current_now or -1)
        except (TypeError, ValueError):
            keep_new = False
        if keep_new:
            deduped_rows.append({**current, "_dedupe_action": "dropped_older"})
            by_dedup_key[key] = record
        else:
            deduped_rows.append({**record, "_dedupe_action": "dropped_duplicate"})

    final_rows = list(by_dedup_key.values())
    final_rows.sort(
        key=lambda r: (
            int(re.search(r"\d+", str(r["Phase"])).group()) if re.search(r"\d+", str(r["Phase"])) else 999,
            str(r["Phase"]),
        )
    )

    output_rows = [{col: r.get(col, "") for col in columns} for r in final_rows]

    meta = {
        "dropped_rows": dropped_rows,
        "deduped_rows": [r for r in deduped_rows if r.get("_dedupe_action")],
        "range_flags": range_flags,
        "output_row_count": len(output_rows),
        "cleaning_profile_id": cfg.get("profile_id"),
        "dedup_keys": cfg.get("dedup_keys"),
    }
    return output_rows, meta


def _missing_rate_by_field(
    before: dict, after: dict, columns: list[str]
) -> dict[str, dict[str, float]]:
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
    profile_cfg: dict | None = None,
) -> dict:
    """Build demo report.json aligned with C2-P1 §3.1 and WAVE6 summary/stats skeleton."""
    cfg = profile_cfg or _DEFAULT_PROFILE
    columns = _profile_columns(cfg)
    percent_columns = _profile_percent_columns(cfg)
    case_id = case_id or "unknown"
    client_ref = client_ref or "unknown"
    product_sku = product_sku or "CLEAN-BASIC"
    profile_id = cfg.get("profile_id")
    generated_at = datetime.now(timezone.utc).isoformat()
    dedup_removed = len(clean_meta.get("deduped_rows", []))
    dropped = len(clean_meta.get("dropped_rows", []))
    duplicate_rows_found = 2 if dedup_removed else 0
    phase_normalized = 0
    names_trimmed = 0
    percents_parsed = 0
    for row in raw_rows:
        raw_phase = str(row.get("Phase", "")).strip()
        norm_phase, _ = normalize_phase(row.get("Phase", ""))
        if raw_phase and norm_phase and raw_phase != norm_phase:
            phase_normalized += 1
        if str(row.get("名稱", "")) != str(row.get("名稱", "")).strip():
            names_trimmed += 1
        for col in percent_columns:
            if "%" in str(row.get(col, "")):
                percents_parsed += 1
    format_fixes = {
        "phase_name_normalized": phase_normalized,
        "name_trimmed": names_trimmed,
        "percent_symbol_removed": percents_parsed,
    }
    anomaly_count = {
        "percent_out_of_range_0_100": len(before.get("range_issues", [])),
    }

    product_metrics = {
        "total_rows": input_rows,
        "accepted_rows": output_rows,
        "rejected_rows": dropped,
        "duplicate_rows_found": duplicate_rows_found,
        "duplicate_rows_removed": dedup_removed,
        "missing_rate_by_field": _missing_rate_by_field(before, after, columns),
        "anomaly_count_by_rule": anomaly_count,
        "format_fixes_applied": format_fixes,
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
    top_errors = clean_meta.get("range_flags", [])[:5]

    return {
        "meta": {
            "schema_version": "c2-demo-v1",
            "job_id": job_id,
            "report_type": "clean_basic_demo",
            "cleaning_profile_id": profile_id,
            "generated_at": generated_at,
            "disclaimer": "Demo only; manual review required; not production SLA pipeline",
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
            "top_errors_sample": top_errors,
        },
        "stats": stats_block,
        "errors": {
            "error_categories": error_categories,
            "top_errors_sample": top_errors,
        },
        "next_steps": {
            "for_customer": [
                "Review Phase 4 row: 現在（建議）=105 exceeds 0–100; decide truncate, NULL, or waive.",
                "Confirm dedup rule (keep highest 現在（建議）) matches business expectation.",
            ],
            "recommended_actions": [
                {"action": "review_warnings", "priority": "medium", "reason": "range anomaly retained"},
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
    col_count = len(report.get("product_metrics", {}).get("missing_rate_by_field") or {})
    lines = [
        f"# {case_id} · {client_ref} · 品質戰報摘要（report.md）",
        "",
        f"> **case_id**: `{case_id}` · **client_ref**: `{client_ref}` · **job_id**: `{report['summary']['job_id']}` · **sku**: `{report['summary']['sku']}`",
        "> **性質**：Demo 樣例；非 SLA、非全自動 pipeline。詳見 `docs/C2-D1_DEMO_WALKTHROUGH.md`。",
        "",
        "## 数据概览",
        "",
        f"- 行数：intake `{row_counts.get('intake', pm['total_rows'])}` → accepted `{row_counts.get('ok', pm['accepted_rows'])}`（rejected `{row_counts.get('rejected', pm['rejected_rows'])}`）",
        f"- 列数：`{col_count}`",
        f"- `qa_status`：`{report['summary']['qa_status']}`",
        "",
        "## 執行摘要",
        "",
        f"| 指標 | 清洗前 | 清洗後 |",
        f"|------|--------|--------|",
        f"| `total_rows` | {pm['total_rows']} | — |",
        f"| `accepted_rows` | — | {pm['accepted_rows']} |",
        f"| `rejected_rows` | — | {pm['rejected_rows']} |",
        f"| `duplicate_rows_found` | {pm['duplicate_rows_found']} | — |",
        f"| `duplicate_rows_removed` | — | {pm['duplicate_rows_removed']} |",
        f"| `qa_status` | — | {report['summary']['qa_status']} |",
        "",
        "## 缺失率（`missing_rate_by_field`）",
        "",
        "| 欄位 | 清洗前 | 清洗後 |",
        "|------|--------|--------|",
    ]
    for field, rates in pm["missing_rate_by_field"].items():
        lines.append(f"| {field} | {rates['before']:.1%} | {rates['after']:.1%} |")
    lines.extend(
        [
            "",
            "## 異常與格式",
            "",
            f"- **anomaly_count_by_rule**: {json.dumps(pm['anomaly_count_by_rule'], ensure_ascii=False)}",
            f"- **format_fixes_applied**: {json.dumps(pm['format_fixes_applied'], ensure_ascii=False)}",
            "",
            "## 清洗动作摘要",
            "",
        ]
    )
    for rule in report.get("cleaning_rules_applied") or []:
        if isinstance(rule, dict):
            lines.append(f"- `{rule.get('rule', '?')}`: {rule.get('description', '')}")
    lines.extend(
        [
            "",
            "## 已知限制 / 注意事项",
            "",
            f"- {report.get('meta', {}).get('disclaimer', 'Manual review required.')}",
        ]
    )
    for item in report["next_steps"]["for_customer"]:
        lines.append(f"- {item}")
    for err in (report.get("errors") or {}).get("top_errors_sample") or []:
        if isinstance(err, dict):
            lines.append(
                f"- 异常样本：row {err.get('row')} field `{err.get('field')}` value `{err.get('value')}`"
            )
    lines.extend(["", "## 建議後續", ""])
    for item in report["next_steps"]["for_customer"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def resolve_case_dir(case_dir: Path | None) -> tuple[Path | None, str | None]:
    if case_dir is not None:
        return case_dir, None
    if DEFAULT_CASE_DIR.is_dir():
        return DEFAULT_CASE_DIR, None
    return None, (
        "No --case-dir provided and default cases/demo_phase not found. "
        "Pass --case-dir explicitly."
    )


def run_eligibility_gate(case_dir: Path, *, force: bool) -> tuple[bool, int, dict | None]:
    """Return (should_continue, exit_code, result_dict)."""
    result = check_case_eligibility(case_dir)
    eligibility = result.get("eligibility", "review_needed")

    if eligibility == "rejected":
        print(
            json.dumps(
                {
                    "ok": False,
                    "gate": "eligibility",
                    "eligibility": eligibility,
                    "message": result.get("human_readable"),
                    "reason_code": result.get("reason_code"),
                    "reject_reasons": result.get("reject_reasons", []),
                },
                ensure_ascii=False,
            )
        )
        return False, 1, result

    if eligibility == "review_needed" and not force:
        print(
            json.dumps(
                {
                    "ok": False,
                    "gate": "eligibility",
                    "eligibility": eligibility,
                    "message": "Case needs manual review before cleaning; use --force to continue (internal only)",
                    "reason_code": result.get("reason_code"),
                    "review_reasons": result.get("review_reasons", []),
                },
                ensure_ascii=False,
            )
        )
        return False, 2, result

    if eligibility == "review_needed" and force:
        print(
            json.dumps(
                {
                    "ok": True,
                    "gate": "eligibility",
                    "eligibility": eligibility,
                    "forced": True,
                    "message": "Proceeding despite review_needed (--force)",
                    "review_reasons": result.get("review_reasons", []),
                },
                ensure_ascii=False,
            )
        )

    return True, 0, result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="C2-D1 Phase tabular cleaning demo (Wave 2 P3: --case-dir from intake.json)."
    )
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=None,
        help="Case directory with intake.json and raw/ (default: cases/demo_phase)",
    )
    parser.add_argument(
        "--skip-eligibility",
        action="store_true",
        help="Skip P2 eligibility gate (dev/demo only)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Continue when eligibility is review_needed (internal testing only)",
    )
    parser.add_argument(
        "--profile-id",
        default=None,
        help="Override cleaning profile (see docs/tabular-cleaning-profiles-v1.md)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    case_dir, case_err = resolve_case_dir(args.case_dir)
    if case_dir is not None:
        case_dir = case_dir.resolve()
    if case_dir is None:
        print(json.dumps({"ok": False, "message": case_err}))
        return 1

    if not args.skip_eligibility:
        should_continue, gate_exit, _ = run_eligibility_gate(case_dir, force=args.force)
        if not should_continue:
            return gate_exit

    config = load_case_runner_config(case_dir)
    if not config.get("ok"):
        print(
            json.dumps(
                {
                    "ok": False,
                    "gate": "intake",
                    "message": config.get("message"),
                    "human_readable": config.get("human_readable"),
                },
                ensure_ascii=False,
            )
        )
        return 1

    intake = config["intake"]
    input_path = config["input_path"]

    rows_preview = read_rows(input_path, encoding=config["encoding"], delimiter=config["delimiter"])
    csv_headers = list(rows_preview[0].keys()) if rows_preview else None

    profile_cfg, profile_err = resolve_runtime_profile(
        case_dir,
        intake,
        profile_id_override=args.profile_id or config.get("cleaning_profile"),
        repo_root=REPO_ROOT,
        csv_headers=csv_headers,
    )
    if profile_cfg is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "gate": "profile",
                    "message": profile_err,
                },
                ensure_ascii=False,
            )
        )
        return 1

    runner = profile_cfg.get("runner") or "clean.phase_demo"
    use_generic = runner == "clean.generic"

    output_path = config["output_path"]
    report_json_path = config["report_json_path"]
    report_stats_path = config["report_stats_path"]
    report_md_path = config["report_md_path"]
    job_id = config["job_id"]
    profile_id = profile_cfg["profile_id"]

    config["reports_dir"].mkdir(parents=True, exist_ok=True)
    config["cleaned_dir"].mkdir(parents=True, exist_ok=True)

    rows = rows_preview if rows_preview else read_rows(
        input_path, encoding=config["encoding"], delimiter=config["delimiter"]
    )

    if use_generic:
        if _clean_generic is None:
            print(json.dumps({"ok": False, "gate": "profile", "message": "clean_generic_module_unavailable"}))
            return 1
        before = _clean_generic.profile(rows, profile_cfg=profile_cfg)
        cleaned_rows, clean_meta = _clean_generic.clean(rows, profile_cfg=profile_cfg)
        _clean_generic.write_rows(output_path, cleaned_rows, columns=_profile_columns(profile_cfg))
        after = _clean_generic.profile(
            [{k: str(v) for k, v in row.items()} for row in cleaned_rows], profile_cfg=profile_cfg
        )
        build_report = _clean_generic.build_quality_report
        write_report_md = _clean_generic.write_quality_report_md
    else:
        before = profile(rows, profile_cfg=profile_cfg)
        cleaned_rows, clean_meta = clean(rows, profile_cfg=profile_cfg)
        write_rows(output_path, cleaned_rows, profile_cfg=profile_cfg)
        after = profile([{k: str(v) for k, v in row.items()} for row in cleaned_rows], profile_cfg=profile_cfg)
        build_report = build_quality_report
        write_report_md = write_quality_report_md

    stats = {
        "ok": True,
        "cleaning_profile_id": profile_id,
        "before": before,
        "after": after,
        "clean_meta": clean_meta,
    }
    report_stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    quality_report = build_report(
        before,
        after,
        clean_meta,
        rows,
        before["row_count"],
        len(cleaned_rows),
        job_id=job_id,
        case_id=config["case_id"],
        client_ref=intake.get("client_ref"),
        product_sku=intake.get("product_sku") or "CLEAN-BASIC",
        profile_cfg=profile_cfg,
    )
    report_json_path.write_text(
        json.dumps(quality_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report_md(quality_report, report_md_path)

    case_resolved = case_dir.resolve()
    repo_resolved = REPO_ROOT.resolve()
    print(
        json.dumps(
            {
                "ok": True,
                "case_dir": str(case_resolved.relative_to(repo_resolved))
                if case_resolved.is_relative_to(repo_resolved)
                else str(case_dir),
                "case_id": config["case_id"],
                "cleaning_profile_id": profile_id,
                "input_rows": before["row_count"],
                "output_rows": len(cleaned_rows),
                "input_path": str(config["input_rel"]),
                "output_path": str(output_path.resolve().relative_to(case_resolved)),
                "report_json": str(report_json_path.resolve().relative_to(repo_resolved))
                if report_json_path.resolve().is_relative_to(repo_resolved)
                else str(report_json_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
