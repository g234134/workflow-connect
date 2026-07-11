"""
Wave 6 manifest writer for the first coding sprint.

This module builds a deduplicated, job-level manifest document from envelope-like
payloads and computes the billing units defined in the Wave 6 frozen specs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from core.schemas.wave6_manifest import (
    ManifestBillingUnits,
    ManifestRow,
    ManifestV20,
    ProductSku,
    WAVE6_BILLING_TABLE_VERSION_DEFAULT,
    WAVE6_ENVELOPE_SCHEMA_VERSION,
    Wave6ManifestJobRecord,
)


def _resolve_billing_table_version(billing_table: Mapping[str, Any] | str | None) -> str:
    if isinstance(billing_table, str):
        text = billing_table.strip()
        return text or WAVE6_BILLING_TABLE_VERSION_DEFAULT
    if billing_table is None:
        return WAVE6_BILLING_TABLE_VERSION_DEFAULT
    value = str(billing_table.get("billing_table_version") or "").strip()
    if value:
        return value
    return WAVE6_BILLING_TABLE_VERSION_DEFAULT


def _normalize_job_record(job_record: Wave6ManifestJobRecord | Mapping[str, Any]) -> Wave6ManifestJobRecord:
    if isinstance(job_record, Wave6ManifestJobRecord):
        return job_record
    return Wave6ManifestJobRecord.model_validate(job_record)


def _normalize_content_summary(source: Any) -> Any:
    if not isinstance(source, Mapping):
        return source
    return {
        "char_count": source.get("char_count"),
        "line_count": source.get("line_count"),
        "imports": source.get("imports", []),
    }


def _row_payload_from_source(source: Mapping[str, Any], product_sku: ProductSku) -> dict[str, Any]:
    enrichment = source.get("enrichment")
    payload = {
        "file_id": source.get("file_id"),
        "name": source.get("name"),
        "extension": source.get("extension"),
        "original_type": source.get("original_type"),
        "size_bytes": source.get("size_bytes"),
        "encoding": source.get("encoding"),
        "content_sha256": source.get("content_sha256"),
        "schema_version": source.get("schema_version", WAVE6_ENVELOPE_SCHEMA_VERSION),
        "clean_status": source.get("clean_status"),
        "stored_logical_path": source.get("stored_logical_path"),
        "parse_strategy": source.get("parse_strategy"),
        "warnings": source.get("warnings", []),
        "content_summary": _normalize_content_summary(source.get("content_summary")),
        "groq_used": bool(source.get("groq_used", False)),
        "groq_reason": source.get("groq_reason"),
    }
    if product_sku == "CLEAN-ENRICH" and enrichment is not None:
        payload["enrichment"] = enrichment
    return payload


def _normalize_row(source: ManifestRow | Mapping[str, Any], product_sku: ProductSku) -> ManifestRow:
    if isinstance(source, ManifestRow):
        row = source
        if product_sku == "CLEAN-BASIC" and row.enrichment is not None:
            payload = row.to_contract_dict()
            payload.pop("enrichment", None)
            payload["has_enrichment"] = False
            return ManifestRow.model_validate(payload)
        return row
    return ManifestRow.model_validate(_row_payload_from_source(source, product_sku))


def _row_is_billable_u(row: ManifestRow, product_sku: ProductSku) -> bool:
    if row.clean_status != "ok":
        return False
    if row.schema_version != WAVE6_ENVELOPE_SCHEMA_VERSION:
        return False
    if product_sku == "CLEAN-BASIC":
        if row.enrichment is not None:
            return False
        return row.groq_used is False
    if row.enrichment is None:
        return False
    return True


def _row_is_billable_l(row: ManifestRow, product_sku: ProductSku) -> bool:
    if product_sku != "CLEAN-ENRICH":
        return False
    if not _row_is_billable_u(row, product_sku):
        return False
    return row.groq_used and bool(str(row.groq_reason or "").strip())


def _row_rank(row: ManifestRow, product_sku: ProductSku) -> tuple[int, int, int, int]:
    return (
        int(_row_is_billable_u(row, product_sku)),
        int(row.clean_status == "ok"),
        int(row.schema_version == WAVE6_ENVELOPE_SCHEMA_VERSION),
        int(row.enrichment is not None),
    )


def _dedupe_rows(rows: Sequence[ManifestRow], product_sku: ProductSku) -> list[ManifestRow]:
    selected: dict[str, tuple[tuple[int, int, int, int], int, ManifestRow]] = {}
    for index, row in enumerate(rows):
        rank = _row_rank(row, product_sku)
        current = selected.get(row.content_sha256)
        if current is None or rank > current[0]:
            selected[row.content_sha256] = (rank, index, row)
    return [item[2] for item in sorted(selected.values(), key=lambda item: item[1])]


def compute_billing_units(rows: Sequence[ManifestRow], product_sku: ProductSku) -> ManifestBillingUnits:
    billable_u = 0
    billable_l = 0
    for row in rows:
        if _row_is_billable_u(row, product_sku):
            billable_u += 1
        if _row_is_billable_l(row, product_sku):
            billable_l += 1
    return ManifestBillingUnits(U=billable_u, L=billable_l)


def write_manifest(
    job_record: Wave6ManifestJobRecord | Mapping[str, Any],
    envelopes: Sequence[ManifestRow | Mapping[str, Any]],
    billing_table: Mapping[str, Any] | str | None = None,
) -> ManifestV20:
    """
    Build a Wave 6 manifest document from envelope-like rows.

    Rules implemented here:
    - accepted_units = final manifest rows where clean_status == "ok"
    - billing_units.U follows Wave 6 U definition
    - billing_units.L follows ENRICH-only Groq billing rule
    - duplicates are collapsed by content_sha256 with a deterministic best-row pick
    """

    job = _normalize_job_record(job_record)
    normalized_rows = [_normalize_row(item, job.sku) for item in envelopes]
    deduped_rows = _dedupe_rows(normalized_rows, job.sku)
    accepted_units = sum(1 for row in deduped_rows if row.clean_status == "ok")
    billing_units = compute_billing_units(deduped_rows, job.sku)
    return ManifestV20(
        job_id=job.job_id,
        product_sku=job.sku,
        billing_table_version=_resolve_billing_table_version(billing_table),
        accepted_units=accepted_units,
        billing_units=billing_units,
        rows=deduped_rows,
    )


__all__ = [
    "compute_billing_units",
    "write_manifest",
]
