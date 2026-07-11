"""
Wave 7 formal ``report.json`` producer (REPORT-SUMMARY-PRODUCER).

Builds ``report.summary.*`` from post-dedup manifest truth and embeds QA-M1 output.
Wave 8 (W8-M2-REPORT-INTEGRATION) merges optional M2 execution results into ``qa`` /
``summary.qa_status`` without changing the report schema. Does not run M2 checks,
Markdown rendering, or financial pricing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from core.schemas.wave6_manifest import (
    ManifestV20,
    WAVE6_BILLING_TABLE_VERSION_DEFAULT,
    Wave6ManifestJobRecord,
)

WAVE7_REPORT_SCHEMA_VERSION = "wave7_report_v0.1"

QA_STATUS_PASS = "pass"
QA_STATUS_PASS_WITH_WARNINGS = "pass_with_warnings"
QA_STATUS_FAIL = "fail"

M2_SAMPLE_VALIDATION_SKIPPED: dict[str, Any] = {
    "status": "skipped",
    "ok": True,
    "reason": "Wave 7: M2 sample_validation deferred to Wave 8",
    "N": None,
    "sample_size": None,
    "seed": None,
    "failed_checks": 0,
    "failures": [],
}

SUMMARY_FIELDS_COMPUTED = (
    "job_id",
    "sku",
    "accepted_units",
    "rejected_units",
    "total_rows",
    "billing_units",
    "qa_status",
    "cost",
    "chargeable_hint",
)


def _normalize_job_record(job_record: Wave6ManifestJobRecord | Mapping[str, Any]) -> Wave6ManifestJobRecord:
    if isinstance(job_record, Wave6ManifestJobRecord):
        return job_record
    return Wave6ManifestJobRecord.model_validate(job_record)


def _normalize_manifest(manifest: ManifestV20 | Mapping[str, Any]) -> ManifestV20:
    if isinstance(manifest, ManifestV20):
        return manifest
    return ManifestV20.model_validate(manifest)


def _manifest_contract_dict(manifest: ManifestV20 | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(manifest, ManifestV20):
        return manifest.to_contract_dict()
    return dict(manifest)


def _count_rejected_units(rows: Sequence[Any]) -> int:
    count = 0
    for row in rows:
        if isinstance(row, Mapping):
            status = row.get("clean_status")
        else:
            status = getattr(row, "clean_status", None)
        if status != "ok":
            count += 1
    return count


def _resolve_billing_table_version(billing_table: Mapping[str, Any] | str | None) -> str:
    if isinstance(billing_table, str):
        text = billing_table.strip()
        return text or WAVE6_BILLING_TABLE_VERSION_DEFAULT
    if billing_table is None:
        return WAVE6_BILLING_TABLE_VERSION_DEFAULT
    value = str(billing_table.get("billing_table_version") or "").strip()
    return value or WAVE6_BILLING_TABLE_VERSION_DEFAULT


def _normalize_failure_list(failures: Any) -> list[dict[str, Any]]:
    if not isinstance(failures, Sequence) or isinstance(failures, (str, bytes)):
        return []
    out: list[dict[str, Any]] = []
    for item in failures:
        if isinstance(item, Mapping):
            out.append(dict(item))
    return out


def _failure_severities(failures: Sequence[Any]) -> set[str]:
    return {
        str(item.get("severity", "P0")).upper()
        for item in failures
        if isinstance(item, Mapping)
    }


def _map_qa_status_from_failures(
    *,
    manifest_integrity_ok: bool,
    failures: Sequence[Any],
) -> str:
    """
    Map combined M1+M2 failures to R3 §G.6–G.7 ``qa_status``.
    """

    if not manifest_integrity_ok:
        return QA_STATUS_FAIL

    severities = _failure_severities(failures)
    if "P0" in severities:
        return QA_STATUS_FAIL
    if "P1" in severities:
        return QA_STATUS_PASS_WITH_WARNINGS
    return QA_STATUS_PASS


def _map_qa_status(qa_m1_result: Mapping[str, Any]) -> str:
    """Map QA-M1-only result to ``qa_status`` (M2 absent / skipped)."""

    qa = qa_m1_result.get("qa")
    if not isinstance(qa, Mapping):
        return QA_STATUS_FAIL

    integrity = qa.get("manifest_integrity")
    manifest_ok = bool(isinstance(integrity, Mapping) and integrity.get("ok"))
    failures = _normalize_failure_list(qa.get("failures"))
    return _map_qa_status_from_failures(manifest_integrity_ok=manifest_ok, failures=failures)


def merge_m1_m2_results(
    m1_result: Mapping[str, Any],
    m2_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Merge QA-M1 and optional M2 execution output into the report ``qa`` block.

    ``m2_result`` shape (from ``run_m2_checks``): ``{ok, sample_validation, failures[]}``.
    When ``m2_result`` is omitted, ``sample_validation`` is the Wave 7 skipped skeleton.
    """

    qa_m1 = m1_result.get("qa")
    if not isinstance(qa_m1, Mapping):
        integrity = {
            "ok": False,
            "checked_rows": 0,
            "failed_rows": 0,
            "failed_checks": 0,
        }
        m1_failures: list[dict[str, Any]] = []
        m1_ok = False
    else:
        integrity_raw = qa_m1.get("manifest_integrity")
        if isinstance(integrity_raw, Mapping):
            integrity = dict(integrity_raw)
        else:
            integrity = {
                "ok": False,
                "checked_rows": 0,
                "failed_rows": 0,
                "failed_checks": 0,
            }
        m1_failures = _normalize_failure_list(qa_m1.get("failures"))
        m1_ok = bool(integrity.get("ok"))

    if m2_result is None:
        sample = dict(M2_SAMPLE_VALIDATION_SKIPPED)
        combined_failures = list(m1_failures)
    else:
        sample_raw = m2_result.get("sample_validation")
        sample = dict(sample_raw) if isinstance(sample_raw, Mapping) else {
            "status": "completed",
            "ok": bool(m2_result.get("ok")),
            "N": None,
            "sample_size": None,
            "seed": None,
            "failed_checks": 0,
            "failures": [],
        }
        m2_failures = _normalize_failure_list(m2_result.get("failures"))
        combined_failures = list(m1_failures) + m2_failures

    sample_ok = bool(sample.get("ok"))
    overall_ok = m1_ok and sample_ok

    return {
        "manifest_integrity": integrity,
        "failures": combined_failures,
        "sample_validation": sample,
        "overall_ok": overall_ok,
    }


def _prices_are_null(billing_table: Mapping[str, Any] | None) -> bool:
    if billing_table is None:
        return True
    for section in ("list", "floor"):
        block = billing_table.get(section)
        if not isinstance(block, Mapping):
            continue
        for value in block.values():
            if value is not None:
                return False
    return True


def _build_cost_block(
    *,
    sku: str,
    billing_units: Mapping[str, Any],
    billing_table: Mapping[str, Any] | str | None,
) -> dict[str, Any]:
    """
    R2 §A.4.2–A.4.3 structure; amounts null until finance fills list prices.
    """

    table = billing_table if isinstance(billing_table, Mapping) else None
    currency = "USD"
    if table is not None:
        currency = str(table.get("currency_default") or "USD")

    u_qty = int(billing_units.get("U", 0))
    l_qty = int(billing_units.get("L", 0))

    line_items: list[dict[str, Any]] = [
        {
            "sku": sku,
            "unit": "U",
            "quantity": u_qty,
            "unit_price": None,
            "amount": None,
            "formula_ref": "R2_A4_3_amount_basic_or_enrich_u",
        },
    ]
    if sku == "CLEAN-ENRICH" and l_qty > 0:
        line_items.append(
            {
                "sku": sku,
                "unit": "L",
                "quantity": l_qty,
                "unit_price": None,
                "amount": None,
                "formula_ref": "R2_A4_3_amount_enrich_l",
            }
        )

    prices_null = _prices_are_null(table)
    chargeable_hint = not prices_null

    return {
        "billing_table_version": _resolve_billing_table_version(billing_table),
        "currency": currency,
        "line_items": line_items,
        "amount_basic": None,
        "amount_enrich": None,
        "amount_total": None,
        "minimum_fee_adjustment": None,
        "chargeable_hint": chargeable_hint,
    }


def build_summary_for_m1_checks(
    manifest: ManifestV20 | Mapping[str, Any],
    job_record: Wave6ManifestJobRecord | Mapping[str, Any],
) -> dict[str, Any]:
    """
    Summary slice consumed by ``run_m1_checks`` (``accepted_units`` truth from manifest).
    """

    doc = _normalize_manifest(manifest)
    job = _normalize_job_record(job_record)
    billing = doc.billing_units.model_dump(mode="json")
    return {
        "job_id": job.job_id,
        "sku": job.sku,
        "accepted_units": doc.accepted_units,
        "rejected_units": _count_rejected_units(doc.rows),
        "total_rows": len(doc.rows),
        "billing_units": billing,
    }


def build_wave7_report(
    job_record: Wave6ManifestJobRecord | Mapping[str, Any],
    manifest_contract_dict: ManifestV20 | Mapping[str, Any],
    qa_m1_result: Mapping[str, Any],
    billing_table: Mapping[str, Any] | str | None = None,
    m2_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a Wave 7 ``report.json`` document.

    Optional ``m2_result`` (Wave 8): output of ``run_m2_checks`` with
    ``{ok, sample_validation, failures[]}``. When omitted, M2 is recorded as skipped.

    Returns ``{ok, report, summary_fields_computed, message}``.
    """

    try:
        job = _normalize_job_record(job_record)
        manifest = _normalize_manifest(manifest_contract_dict)
    except (ValueError, TypeError) as exc:
        return {
            "ok": False,
            "report": None,
            "summary_fields_computed": [],
            "message": str(exc),
        }

    billing_units = manifest.billing_units.model_dump(mode="json")
    cost = _build_cost_block(
        sku=job.sku,
        billing_units=billing_units,
        billing_table=billing_table if isinstance(billing_table, Mapping) else None,
    )
    qa_section = merge_m1_m2_results(qa_m1_result, m2_result)
    qa_status = _map_qa_status_from_failures(
        manifest_integrity_ok=bool(qa_section["manifest_integrity"].get("ok")),
        failures=qa_section["failures"],
    )

    summary: dict[str, Any] = {
        "job_id": job.job_id,
        "sku": job.sku,
        "accepted_units": manifest.accepted_units,
        "rejected_units": _count_rejected_units(manifest.rows),
        "total_rows": len(manifest.rows),
        "billing_units": billing_units,
        "qa_status": qa_status,
        "cost": cost,
        "chargeable_hint": cost["chargeable_hint"],
    }

    report: dict[str, Any] = {
        "schema_version": WAVE7_REPORT_SCHEMA_VERSION,
        "job_id": job.job_id,
        "summary": summary,
        "qa": qa_section,
    }

    return {
        "ok": True,
        "report": report,
        "summary_fields_computed": list(SUMMARY_FIELDS_COMPUTED),
        "message": "wave7_report_built",
    }


__all__ = [
    "M2_SAMPLE_VALIDATION_SKIPPED",
    "QA_STATUS_FAIL",
    "QA_STATUS_PASS",
    "QA_STATUS_PASS_WITH_WARNINGS",
    "SUMMARY_FIELDS_COMPUTED",
    "WAVE7_REPORT_SCHEMA_VERSION",
    "build_summary_for_m1_checks",
    "build_wave7_report",
    "merge_m1_m2_results",
]
