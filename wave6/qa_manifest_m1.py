"""Wave 6 manifest-only QA gate (M1)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, Final

_HEX64_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-fA-F]{64}$")
_FAILURE_LAYER: Final[str] = "M1"
_FAILURE_SEVERITY: Final[str] = "P0"
_REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "file_id",
    "content_sha256",
    "clean_status",
    "extension",
    "stored_logical_path",
    "schema_version",
)
_SKU_BASIC: Final[str] = "CLEAN-BASIC"
_SKU_ENRICH: Final[str] = "CLEAN-ENRICH"


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _is_hex64(value: Any) -> bool:
    return isinstance(value, str) and bool(_HEX64_RE.fullmatch(value))


def _row_key(row: Mapping[str, Any], row_index: int) -> str:
    file_id = _string_or_none(row.get("file_id"))
    if file_id:
        return f"file_id:{file_id}"

    content_sha256 = _string_or_none(row.get("content_sha256"))
    if content_sha256:
        return f"content_sha256:{content_sha256}"

    return f"row_index:{row_index}"


def _accepted_units(report: Mapping[str, Any]) -> int:
    summary = report.get("summary")
    if not isinstance(summary, Mapping):
        return 0

    raw_value = summary.get("accepted_units", 0)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return 0


def _make_failure(
    *,
    check_id: str,
    message: str,
    file_id: Any,
    content_sha256: Any,
    stored_logical_path: Any,
    remediation_hint: str,
) -> dict[str, Any]:
    return {
        "layer": _FAILURE_LAYER,
        "check_id": check_id,
        "severity": _FAILURE_SEVERITY,
        "file_id": _string_or_none(file_id),
        "content_sha256": _string_or_none(content_sha256),
        "stored_logical_path": _string_or_none(stored_logical_path),
        "message": message[:200],
        "remediation_hint": remediation_hint,
    }


def run_m1_checks(
    manifest_rows: Sequence[Mapping[str, Any]] | Sequence[object],
    job_record: Mapping[str, Any] | object,
    report: Mapping[str, Any] | object,
) -> dict[str, Any]:
    """Run the manifest-integrity gate for Wave 6 M1.

    This function is intentionally pure: it only consumes the provided
    manifest rows, job record, and report summary, and it never reads files,
    envelopes, or external state.
    """

    normalized_rows = [_as_dict(row) for row in manifest_rows]
    normalized_job_record = _as_dict(job_record)
    normalized_report = _as_dict(report)

    sku = normalized_job_record.get("sku")
    failures: list[dict[str, Any]] = []
    failed_row_keys: set[str] = set()
    seen_sha_by_lowercase: set[str] = set()
    ok_row_count = 0

    for row_index, row in enumerate(normalized_rows):
        row_key = _row_key(row, row_index)
        file_id = row.get("file_id")
        content_sha256 = row.get("content_sha256")
        stored_logical_path = row.get("stored_logical_path")
        clean_status = row.get("clean_status")

        missing_keys = [key for key in _REQUIRED_KEYS if key not in row]
        if missing_keys:
            failures.append(
                _make_failure(
                    check_id="M1-KEYS",
                    message=f"missing required manifest keys: {', '.join(missing_keys)}",
                    file_id=file_id,
                    content_sha256=content_sha256,
                    stored_logical_path=stored_logical_path,
                    remediation_hint="fix_manifest",
                )
            )
            failed_row_keys.add(row_key)

        sha_is_valid = _is_hex64(content_sha256)
        if not sha_is_valid:
            failures.append(
                _make_failure(
                    check_id="M1-SHA",
                    message="content_sha256 must be a 64-character hex string",
                    file_id=file_id,
                    content_sha256=content_sha256,
                    stored_logical_path=stored_logical_path,
                    remediation_hint="fix_manifest",
                )
            )
            failed_row_keys.add(row_key)

        if clean_status == "ok":
            ok_row_count += 1

        if sku == _SKU_BASIC and "enrichment" in row:
            failures.append(
                _make_failure(
                    check_id="M1-SKU-BASIC",
                    message="CLEAN-BASIC rows must not declare the enrichment key",
                    file_id=file_id,
                    content_sha256=content_sha256,
                    stored_logical_path=stored_logical_path,
                    remediation_hint="fix_manifest",
                )
            )
            failed_row_keys.add(row_key)

        if sku == _SKU_ENRICH and clean_status == "ok" and row.get("has_enrichment") is not True:
            failures.append(
                _make_failure(
                    check_id="M1-SKU-ENRICH",
                    message="CLEAN-ENRICH ok rows must set has_enrichment=true",
                    file_id=file_id,
                    content_sha256=content_sha256,
                    stored_logical_path=stored_logical_path,
                    remediation_hint="fix_manifest",
                )
            )
            failed_row_keys.add(row_key)

        if sha_is_valid:
            normalized_sha = str(content_sha256).lower()
            if normalized_sha in seen_sha_by_lowercase:
                failures.append(
                    _make_failure(
                        check_id="M1-DEDUP",
                        message="duplicate content_sha256 detected within the manifest",
                        file_id=file_id,
                        content_sha256=content_sha256,
                        stored_logical_path=stored_logical_path,
                        remediation_hint="fix_manifest",
                    )
                )
                failed_row_keys.add(row_key)
            else:
                seen_sha_by_lowercase.add(normalized_sha)

    accepted_units = _accepted_units(normalized_report)

    # M1-OK-ONLY is intentionally enforced through the M1-COUNT reconciliation:
    # only rows with clean_status == "ok" contribute to ok_row_count. If an
    # upstream caller wrongly treats non-ok rows as accepted, the discrepancy
    # surfaces as a single aggregate M1-COUNT failure instead of a second,
    # redundant row-scoped failure shape for M1-OK-ONLY.
    if ok_row_count != accepted_units:
        failures.append(
            _make_failure(
                check_id="M1-COUNT",
                message=(
                    "manifest ok-row count does not match "
                    f"report.summary.accepted_units ({ok_row_count} != {accepted_units})"
                ),
                file_id=None,
                content_sha256=None,
                stored_logical_path=None,
                remediation_hint="reconcile_manifest_and_report_summary",
            )
        )

    manifest_integrity = {
        "ok": len(failures) == 0,
        "checked_rows": len(normalized_rows),
        "failed_rows": len(failed_row_keys),
        "failed_checks": len(failures),
    }

    return {
        "qa": {
            "manifest_integrity": manifest_integrity,
            "failures": failures,
        }
    }
