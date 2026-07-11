"""
Manifest-only Wave 6 QA M1 checker.

This module validates the manifest layer only. It does not read envelopes,
does not touch the filesystem, and does not emit any overall QA verdict.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from core.schemas.wave6_manifest import ManifestV20, Wave6ManifestJobRecord

_REQUIRED_ROW_KEYS = (
    "file_id",
    "content_sha256",
    "clean_status",
    "extension",
    "stored_logical_path",
    "schema_version",
)
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _normalize_job_record(job_record: Wave6ManifestJobRecord | Mapping[str, Any]) -> Wave6ManifestJobRecord:
    if isinstance(job_record, Wave6ManifestJobRecord):
        return job_record
    return Wave6ManifestJobRecord.model_validate(job_record)


def _normalize_manifest_row(row: Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    to_contract_dict = getattr(row, "to_contract_dict", None)
    if callable(to_contract_dict):
        data = to_contract_dict()
        if isinstance(data, Mapping):
            return dict(data)
    return {}


def _extract_rows(manifest: ManifestV20 | Mapping[str, Any]) -> list[dict[str, Any]]:
    if isinstance(manifest, ManifestV20):
        return manifest.rows_for_qa()
    raw_rows = manifest.get("rows", []) if isinstance(manifest, Mapping) else []
    if not isinstance(raw_rows, Sequence) or isinstance(raw_rows, (str, bytes, bytearray)):
        return []
    return [_normalize_manifest_row(row) for row in raw_rows]


def _normalize_accepted_units(report_summary: Mapping[str, Any]) -> int:
    return int(report_summary.get("accepted_units", 0))


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalized_sha_or_none(value: Any) -> str | None:
    text = _clean_text(value)
    if text is None or _SHA256_RE.fullmatch(text) is None:
        return None
    return text.lower()


def _row_failure_key(row: Mapping[str, Any], row_index: int) -> str:
    file_id = _clean_text(row.get("file_id"))
    if file_id is not None:
        return f"file_id:{file_id}"
    sha = _normalized_sha_or_none(row.get("content_sha256"))
    if sha is not None:
        return f"sha:{sha}"
    return f"row_index:{row_index}"


def _make_failure(
    *,
    check_id: str,
    message: str,
    row: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "layer": "M1",
        "check_id": check_id,
        "severity": "P0",
        "file_id": None,
        "content_sha256": None,
        "stored_logical_path": None,
        "message": message[:200],
        "remediation_hint": "fix_manifest",
    }
    if row is None:
        return payload
    payload["file_id"] = _clean_text(row.get("file_id"))
    payload["content_sha256"] = _normalized_sha_or_none(row.get("content_sha256"))
    payload["stored_logical_path"] = _clean_text(row.get("stored_logical_path"))
    return payload


def _is_ok_row(row: Mapping[str, Any]) -> bool:
    return row.get("clean_status") == "ok"


def run_m1_checks(
    manifest: ManifestV20 | Mapping[str, Any],
    job_record: Wave6ManifestJobRecord | Mapping[str, Any],
    report_summary: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Run manifest-only M1 integrity checks.

    Inputs consumed:
    - manifest.rows
    - job_record.sku
    - report_summary.accepted_units

    Outputs emitted:
    - qa.manifest_integrity
    - qa.failures
    """

    job = _normalize_job_record(job_record)
    rows = _extract_rows(manifest)
    accepted_units = _normalize_accepted_units(report_summary)

    failures: list[dict[str, Any]] = []
    failed_row_keys: set[str] = set()
    strict_ok_count = 0
    seen_shas: set[str] = set()

    def add_row_failure(check_id: str, message: str, row: Mapping[str, Any], row_index: int) -> None:
        failures.append(_make_failure(check_id=check_id, message=message, row=row))
        failed_row_keys.add(_row_failure_key(row, row_index))

    for row_index, row in enumerate(rows):
        if _is_ok_row(row):
            strict_ok_count += 1

        missing_keys = [key for key in _REQUIRED_ROW_KEYS if key not in row]
        if missing_keys:
            add_row_failure(
                "M1-KEYS",
                f"missing required manifest keys: {', '.join(missing_keys)}",
                row,
                row_index,
            )

        normalized_sha = _normalized_sha_or_none(row.get("content_sha256"))
        if normalized_sha is None:
            add_row_failure(
                "M1-SHA",
                "content_sha256 must be a 64-char hex string",
                row,
                row_index,
            )

        if job.sku == "CLEAN-BASIC" and "enrichment" in row:
            add_row_failure(
                "M1-SKU-BASIC",
                "CLEAN-BASIC rows must not include the enrichment key",
                row,
                row_index,
            )

        if job.sku == "CLEAN-ENRICH" and _is_ok_row(row):
            if row.get("has_enrichment") is not True:
                add_row_failure(
                    "M1-SKU-ENRICH",
                    "CLEAN-ENRICH ok rows require has_enrichment=true",
                    row,
                    row_index,
                )

        if normalized_sha is not None:
            if normalized_sha in seen_shas:
                add_row_failure(
                    "M1-DEDUP",
                    "duplicate content_sha256 within manifest job",
                    row,
                    row_index,
                )
            else:
                seen_shas.add(normalized_sha)

    if accepted_units > strict_ok_count:
        failures.append(
            _make_failure(
                check_id="M1-OK-ONLY",
                message=(
                    f"accepted_units={accepted_units} exceeds strict ok row count={strict_ok_count}; "
                    "non-ok rows must not be counted as accepted"
                ),
            )
        )

    if accepted_units != strict_ok_count:
        failures.append(
            _make_failure(
                check_id="M1-COUNT",
                message=f"accepted_units={accepted_units} does not match manifest ok row count={strict_ok_count}",
            )
        )

    return {
        "qa": {
            "manifest_integrity": {
                "ok": len(failures) == 0,
                "checked_rows": len(rows),
                "failed_rows": len(failed_row_keys),
                "failed_checks": len(failures),
            },
            "failures": failures,
        }
    }


__all__ = ["run_m1_checks"]
