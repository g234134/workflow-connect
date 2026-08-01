#!/usr/bin/env python3
"""Build standard case delivery bundle (Wave 2 P4 · manual MVP).

Reads existing cleaned CSV, reports, and P2 eligibility; writes
reports/eligibility_result.json and ensures delivery_signoff.md exists.
Does not run cleaning or send email/UI.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from case_eligibility import check_case_eligibility
from output_guard import apply_output_guard_to_report

ELIGIBILITY_RESULT_SCHEMA = "case-eligibility-result-v0.1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SIGNOFF_TEMPLATE = REPO_ROOT / "cases" / "_TEMPLATE_case" / "delivery_signoff.md"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _load_intake(case_dir: Path) -> dict[str, Any]:
    for name in ("intake.json", "intake_record.json"):
        data = _load_json(case_dir / name)
        if data is not None:
            return data
    return {}


def _find_cleaned_csvs(case_dir: Path) -> list[Path]:
    cleaned_dir = case_dir / "cleaned"
    if not cleaned_dir.is_dir():
        return []
    return sorted(p for p in cleaned_dir.glob("*.csv") if p.is_file())


def _eligibility_to_result(raw: dict[str, Any], checked_at: str) -> dict[str, Any]:
    dimensions = raw.get("dimensions") or {}
    dimensions_summary = {
        name: dim.get("status") if isinstance(dim, dict) else dim
        for name, dim in dimensions.items()
    }
    reasons: list[str] = []
    for key in ("reject_reasons", "review_reasons", "notes"):
        items = raw.get(key)
        if isinstance(items, list):
            reasons.extend(str(x) for x in items if str(x).strip())
    # dedupe preserving order
    seen: set[str] = set()
    unique_reasons: list[str] = []
    for item in reasons:
        if item not in seen:
            seen.add(item)
            unique_reasons.append(item)

    status = raw.get("eligibility") or raw.get("status") or "review_needed"
    if status not in ("accepted", "rejected", "review_needed"):
        status = "review_needed"

    return {
        "schema_version": ELIGIBILITY_RESULT_SCHEMA,
        "status": status,
        "checked_at": checked_at,
        "case_id": raw.get("case_id"),
        "client_ref": raw.get("client_ref"),
        "dimensions_summary": dimensions_summary,
        "reasons": unique_reasons,
        "human_readable": raw.get("human_readable"),
        "reason_code": raw.get("reason_code"),
        "source": "p2_case_eligibility",
    }


def ensure_eligibility_result(
    case_dir: Path,
    *,
    intake: dict[str, Any] | None = None,
    refresh: bool = False,
) -> tuple[dict[str, Any], Path]:
    """Run or load P2 eligibility and write reports/eligibility_result.json."""
    reports_dir = case_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "eligibility_result.json"

    if out_path.is_file() and not refresh:
        existing = _load_json(out_path)
        if existing and existing.get("status"):
            return existing, out_path

    checked_at = _utc_now_iso()
    raw = check_case_eligibility(case_dir)
    result = _eligibility_to_result(raw, checked_at)
    if intake is None:
        intake = _load_intake(case_dir)
    if not result.get("case_id"):
        result["case_id"] = intake.get("case_id") or case_dir.name
    if not result.get("client_ref"):
        result["client_ref"] = intake.get("client_ref")

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result, out_path


def _issues_summary_from_report(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary") or {}
    errors = report.get("errors") or {}
    return {
        "qa_status": summary.get("qa_status"),
        "completion_variant": summary.get("completion_variant"),
        "error_categories": errors.get("error_categories") or [],
        "top_errors_sample": (errors.get("top_errors_sample") or [])[:5],
    }


def enrich_report_json_v1(
    case_dir: Path,
    intake: dict[str, Any],
    *,
    write: bool = True,
) -> dict[str, Any] | None:
    """Add v1 contract fields to report.json without removing existing keys."""
    report_path = case_dir / "reports" / "report.json"
    report = _load_json(report_path)
    if report is None:
        return None

    meta = report.setdefault("meta", {})
    summary = report.get("summary") or {}
    stats = report.get("stats") or {}

    case_id = intake.get("case_id") or case_dir.name
    client_ref = intake.get("client_ref") or "unknown"
    product_sku = (
        intake.get("product_sku")
        or summary.get("sku")
        or report.get("product_sku")
        or "CLEAN-BASIC"
    )

    report["case_id"] = case_id
    report["client_ref"] = client_ref
    report["product_sku"] = product_sku
    report["generated_at"] = meta.get("generated_at") or _utc_now_iso()
    report["cleaning_stats"] = {
        "row_counts": stats.get("row_counts") or {},
        "missing_value_stats": stats.get("missing_value_stats") or [],
        "product_metrics": report.get("product_metrics") or {},
    }
    report["issues_summary"] = _issues_summary_from_report(report)

    if write:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _render_signoff_from_template(
    template_path: Path,
    *,
    case_id: str,
    client_ref: str,
    product_sku: str,
    job_id: str,
    eligibility: dict[str, Any],
    report: dict[str, Any] | None,
    bundle_built_at: str,
) -> str:
    template = template_path.read_text(encoding="utf-8") if template_path.is_file() else ""
    if not template.strip():
        template = (
            "# Delivery Signoff · `{case_id}`\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| case_id | `{case_id}` |\n"
            "| client_ref | `{client_ref}` |\n"
        )

    status = eligibility.get("status", "review_needed")
    reasons = eligibility.get("reasons") or []
    reasons_text = "; ".join(reasons[:5]) if reasons else "none"

    row_counts: dict[str, Any] = {}
    cleaning_rules: list[Any] = []
    qa_status = "unknown"
    if report:
        cleaning_stats = report.get("cleaning_stats") or {}
        row_counts = cleaning_stats.get("row_counts") or report.get("stats", {}).get("row_counts") or {}
        cleaning_rules = report.get("cleaning_rules_applied") or []
        issues = report.get("issues_summary") or {}
        qa_status = issues.get("qa_status") or (report.get("summary") or {}).get("qa_status") or "unknown"

    rules_lines = []
    for rule in cleaning_rules[:8]:
        if isinstance(rule, dict):
            rules_lines.append(f"- `{rule.get('rule', '?')}`: {rule.get('description', '')}")
    rules_block = "\n".join(rules_lines) if rules_lines else "- _pending manual entry_"

    intake_rows = row_counts.get("intake", "—")
    accepted_rows = row_counts.get("ok", row_counts.get("accepted", "—"))
    rejected_rows = row_counts.get("rejected", "—")
    checked_at = eligibility.get("checked_at", bundle_built_at)

    content = template
    simple_replacements = {
        "<case_id>": case_id,
        "<client_ref>": client_ref,
        "<product_sku>": product_sku,
        "<job_id>": job_id,
        "`{case_id}`": f"`{case_id}`",
        "`{client_ref}`": f"`{client_ref}`",
        "`{product_sku}`": f"`{product_sku}`",
        "`{job_id}`": f"`{job_id}`",
    }
    for old, new in simple_replacements.items():
        content = content.replace(old, new)

    # Fill metric table placeholders when template includes P4 sections
    content = content.replace("| intake rows | _pending_ |", f"| intake rows | {intake_rows} |")
    content = content.replace("| accepted rows | _pending_ |", f"| accepted rows | {accepted_rows} |")
    content = content.replace("| rejected rows | _pending_ |", f"| rejected rows | {rejected_rows} |")
    content = content.replace("| qa_status | _pending_ |", f"| qa_status | `{qa_status}` |")
    content = content.replace("| status | _pending_ |", f"| status | `{status}` |")
    content = content.replace("| checked_at | _pending_ |", f"| checked_at | `{checked_at}` |")
    content = content.replace("| reasons | _pending_ |", f"| reasons | {reasons_text} |")
    content = content.replace("| bundle_built_at | _pending_ |", f"| bundle_built_at | `{bundle_built_at}` |")

    if "### Rules applied" in content and "_pending manual entry_" in content:
        content = content.replace("- _pending manual entry_", rules_block, 1)

    if "## Cleaning summary" not in content:
        content += f"""

## Cleaning summary

| Metric | Value |
|--------|-------|
| intake rows | {intake_rows} |
| accepted rows | {accepted_rows} |
| rejected rows | {rejected_rows} |
| qa_status | `{qa_status}` |

### Rules applied

{rules_block}

## Eligibility summary

| Field | Value |
|-------|-------|
| status | `{status}` |
| checked_at | `{checked_at}` |
| reasons | {reasons_text} |

## Signoff

| Field | Value |
|-------|-------|
| reviewer | _pending — manual entry_ |
| signer (Lead) | _pending — manual entry_ |
| signed_at | _pending — manual entry_ |
| bundle_built_at | `{bundle_built_at}` |

## Exceptions / notes

<!-- Manual: record known limits, waivers, and customer-facing caveats (C2-P2 §19). -->

- Non-SLA demo pipeline; manual review required before external delivery.
"""
    return content


def ensure_delivery_signoff(
    case_dir: Path,
    *,
    intake: dict[str, Any],
    eligibility: dict[str, Any],
    report: dict[str, Any] | None,
    template_path: Path | None = None,
    refresh: bool = False,
) -> Path:
    signoff_path = case_dir / "delivery_signoff.md"
    if signoff_path.is_file() and not refresh:
        return signoff_path

    tpl = template_path or DEFAULT_SIGNOFF_TEMPLATE
    case_id = str(intake.get("case_id") or case_dir.name)
    client_ref = str(intake.get("client_ref") or "unknown")
    product_sku = str(
        intake.get("product_sku")
        or (report or {}).get("product_sku")
        or ((report or {}).get("summary") or {}).get("sku")
        or "CLEAN-BASIC"
    )
    job_id = str(((report or {}).get("summary") or {}).get("job_id") or case_id)
    built_at = _utc_now_iso()

    content = _render_signoff_from_template(
        tpl,
        case_id=case_id,
        client_ref=client_ref,
        product_sku=product_sku,
        job_id=job_id,
        eligibility=eligibility,
        report=report,
        bundle_built_at=built_at,
    )
    signoff_path.write_text(content, encoding="utf-8")
    return signoff_path


def build_case_delivery_bundle(
    case_dir: Path,
    *,
    refresh_eligibility: bool = False,
    refresh_signoff: bool = False,
    enrich_report: bool = True,
    signoff_template: Path | None = None,
) -> dict[str, Any]:
    """Validate case artifacts and materialize P4 delivery bundle files."""
    case_dir = case_dir.resolve()
    missing: list[str] = []
    warnings: list[str] = []

    if not case_dir.is_dir():
        return {
            "ok": False,
            "message": f"case directory not found: {case_dir.name}",
            "case_dir": str(case_dir),
        }

    intake = _load_intake(case_dir)
    cleaned_csvs = _find_cleaned_csvs(case_dir)
    if not cleaned_csvs:
        missing.append("cleaned/*.csv")

    reports_dir = case_dir / "reports"
    report_json_path = reports_dir / "report.json"
    report_md_path = reports_dir / "report.md"
    cleaning_stats_path = reports_dir / "cleaning_stats.json"

    if not report_json_path.is_file():
        missing.append("reports/report.json")
    if not report_md_path.is_file():
        warnings.append("reports/report.md missing")

    if missing:
        return {
            "ok": False,
            "message": "missing required bundle inputs",
            "case_dir": str(case_dir),
            "missing": missing,
            "warnings": warnings,
        }

    report = enrich_report_json_v1(case_dir, intake, write=enrich_report) if enrich_report else _load_json(report_json_path)

    eligibility, eligibility_path = ensure_eligibility_result(
        case_dir, intake=intake, refresh=refresh_eligibility
    )

    output_guard: dict[str, Any] | None = None
    if report is not None:
        eligibility_raw = check_case_eligibility(case_dir)
        _, output_guard = apply_output_guard_to_report(
            case_dir,
            report,
            eligibility_raw=eligibility_raw,
            write=enrich_report,
        )

    signoff_path = ensure_delivery_signoff(
        case_dir,
        intake=intake,
        eligibility=eligibility,
        report=report,
        template_path=signoff_template,
        refresh=refresh_signoff,
    )

    artifacts = {
        "cleaned_csv": [str(p.relative_to(case_dir)).replace("\\", "/") for p in cleaned_csvs],
        "report_json": "reports/report.json",
        "report_md": "reports/report.md" if report_md_path.is_file() else None,
        "cleaning_stats_json": "reports/cleaning_stats.json" if cleaning_stats_path.is_file() else None,
        "eligibility_result_json": str(eligibility_path.relative_to(case_dir)).replace("\\", "/"),
        "delivery_signoff_md": signoff_path.name,
    }

    return {
        "ok": True,
        "message": "delivery bundle ready",
        "case_dir": str(case_dir),
        "case_id": intake.get("case_id") or case_dir.name,
        "client_ref": intake.get("client_ref"),
        "product_sku": (report or {}).get("product_sku") if report else intake.get("product_sku"),
        "eligibility_status": eligibility.get("status"),
        "output_guard": output_guard,
        "artifacts": artifacts,
        "warnings": warnings,
    }
