"""
Wave 8 M2 execution engine — sample envelope validation (R3 §G.4).

Reads envelopes only for ``sampling_plan.row_indexes`` positions within the
pre-sorted ok-row ``manifest_rows`` list. Does not write manifest/report files.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from core.envelope_writer import SKU_BASIC, SKU_ENRICH
from core.schemas.envelope_v2 import ENRICHMENT_V0_1_SCHEMA_VERSION, ENVELOPE_V2_SCHEMA_VERSION, _LEAKY_PATH_RE
from core.schemas.wave6_manifest import Wave6ManifestJobRecord
from core.wave8_m2_sampling_design import SamplingPlan

EnvelopeLoader = Callable[[str], Mapping[str, Any] | dict[str, Any] | None]

_BINARY_EXTENSIONS = frozenset({".bin", ".exe", ".dll", ".so"})

_CHECK_REMEDIATION: dict[str, str] = {
    "M2-SCHEMA-20": "reject_row",
    "M2-GROQ-BASIC": "rerun_basic",
    "M2-ENRICH-BLOCK": "rerun_enrich",
    "M2-QUALITY": "rerun_enrich",
    "M2-PATH-LEAK": "rerun_basic",
    "M2-PREVIEW-LEN": "fix_manifest",
}


def _normalize_job_record(job_record: Wave6ManifestJobRecord | Mapping[str, Any]) -> Wave6ManifestJobRecord:
    if isinstance(job_record, Wave6ManifestJobRecord):
        return job_record
    return Wave6ManifestJobRecord.model_validate(job_record)


def _normalize_row(row: Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    to_contract_dict = getattr(row, "to_contract_dict", None)
    if callable(to_contract_dict):
        data = to_contract_dict()
        if isinstance(data, Mapping):
            return dict(data)
    return {}


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_extension(ext: Any) -> str:
    text = _clean_text(ext) or ""
    if not text:
        return ""
    return text if text.startswith(".") else f".{text}"


def _make_failure(
    *,
    check_id: str,
    severity: str,
    message: str,
    row: Mapping[str, Any] | None = None,
    remediation_hint: str | None = None,
) -> dict[str, Any]:
    hint = remediation_hint or _CHECK_REMEDIATION.get(check_id, "reject_row")
    payload: dict[str, Any] = {
        "layer": "M2",
        "check_id": check_id,
        "severity": severity,
        "file_id": None,
        "content_sha256": None,
        "stored_logical_path": None,
        "message": message[:200],
        "remediation_hint": hint,
    }
    if row is not None:
        sha = _clean_text(row.get("content_sha256"))
        payload["file_id"] = _clean_text(row.get("file_id"))
        payload["content_sha256"] = sha.lower() if sha else None
        payload["stored_logical_path"] = _clean_text(row.get("stored_logical_path"))
    return payload


def recompute_quality_score(envelope: Mapping[str, Any]) -> int:
    """
    R2 §C.4 deterministic ``quality_score`` from envelope v2 fields.
    """

    if envelope.get("clean_status") != "ok":
        return 0

    score = 100
    warnings = envelope.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)):
        if len(warnings) > 0:
            score -= 10

    parse_strategy = envelope.get("parse_strategy")
    original_type = str(envelope.get("original_type") or "").lower()
    if parse_strategy is None and "python" in original_type:
        score -= 5

    content_summary = envelope.get("content_summary")
    if isinstance(content_summary, Mapping):
        line_count = int(content_summary.get("line_count") or 0)
        char_count = int(content_summary.get("char_count") or 0)
        if line_count == 0:
            score -= 40
        if char_count < 50:
            score -= 15

    groq_used = bool(envelope.get("groq_used"))
    groq_reason = str(envelope.get("groq_reason") or "")
    if groq_used and "failure" in groq_reason.lower():
        score -= 20

    extension = _normalize_extension(envelope.get("extension"))
    if extension in _BINARY_EXTENSIONS:
        score -= 30

    return max(0, min(100, score))


def _envelope_ref(row: Mapping[str, Any]) -> str | None:
    return _clean_text(row.get("stored_logical_path"))


def _load_envelope(
    row: Mapping[str, Any],
    envelope_loader: EnvelopeLoader,
) -> tuple[Mapping[str, Any] | None, list[dict[str, Any]]]:
    ref = _envelope_ref(row)
    if ref is None:
        return None, [
            _make_failure(
                check_id="M2-SCHEMA-20",
                severity="P0",
                message="missing stored_logical_path for envelope load",
                row=row,
            )
        ]

    try:
        loaded = envelope_loader(ref)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return None, [
            _make_failure(
                check_id="M2-SCHEMA-20",
                severity="P0",
                message=f"envelope load failed: {exc}",
                row=row,
            )
        ]

    if loaded is None:
        return None, [
            _make_failure(
                check_id="M2-SCHEMA-20",
                severity="P0",
                message=f"envelope not found for ref {ref}",
                row=row,
            )
        ]

    if not isinstance(loaded, Mapping):
        return None, [
            _make_failure(
                check_id="M2-SCHEMA-20",
                severity="P0",
                message="envelope loader returned non-object payload",
                row=row,
            )
        ]

    return loaded, []


def _check_m2_schema_20(envelope: Mapping[str, Any], row: Mapping[str, Any]) -> list[dict[str, Any]]:
    if envelope.get("schema_version") != ENVELOPE_V2_SCHEMA_VERSION:
        return [
            _make_failure(
                check_id="M2-SCHEMA-20",
                severity="P0",
                message="schema_version must be 2.0",
                row=row,
            )
        ]
    return []


def _check_m2_groq_basic(envelope: Mapping[str, Any], row: Mapping[str, Any], sku: str) -> list[dict[str, Any]]:
    if sku != SKU_BASIC:
        return []
    if envelope.get("groq_used") is not False:
        return [
            _make_failure(
                check_id="M2-GROQ-BASIC",
                severity="P0",
                message="CLEAN-BASIC envelope must have groq_used=false",
                row=row,
            )
        ]
    return []


def _check_m2_enrich_block(envelope: Mapping[str, Any], row: Mapping[str, Any], sku: str) -> list[dict[str, Any]]:
    if sku != SKU_ENRICH:
        return []

    enrichment = envelope.get("enrichment")
    if not isinstance(enrichment, Mapping):
        return [
            _make_failure(
                check_id="M2-ENRICH-BLOCK",
                severity="P0",
                message="CLEAN-ENRICH envelope requires enrichment block",
                row=row,
            )
        ]

    if enrichment.get("schema_version") != ENRICHMENT_V0_1_SCHEMA_VERSION:
        return [
            _make_failure(
                check_id="M2-ENRICH-BLOCK",
                severity="P0",
                message="enrichment.schema_version must be enrichment_v0.1",
                row=row,
            )
        ]

    return []


def _check_m2_quality(envelope: Mapping[str, Any], row: Mapping[str, Any], sku: str) -> list[dict[str, Any]]:
    if sku != SKU_ENRICH:
        return []

    enrichment = envelope.get("enrichment")
    if not isinstance(enrichment, Mapping) or not enrichment.get("present"):
        return []

    declared = enrichment.get("quality_score")
    if not isinstance(declared, int):
        return [
            _make_failure(
                check_id="M2-QUALITY",
                severity="P1",
                message="enrichment.present=true requires integer quality_score",
                row=row,
            )
        ]

    expected = recompute_quality_score(envelope)
    if declared != expected:
        return [
            _make_failure(
                check_id="M2-QUALITY",
                severity="P1",
                message=f"quality_score mismatch: declared={declared} recomputed={expected}",
                row=row,
            )
        ]
    return []


def _check_m2_path_leak(envelope: Mapping[str, Any], row: Mapping[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for key in ("source_path", "stored_path"):
        value = envelope.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        if _LEAKY_PATH_RE.search(text):
            failures.append(
                _make_failure(
                    check_id="M2-PATH-LEAK",
                    severity="P1",
                    message=f"{key} must not contain disk or URL path markers",
                    row=row,
                )
            )
    return failures


def _check_m2_preview_len(envelope: Mapping[str, Any], row: Mapping[str, Any]) -> list[dict[str, Any]]:
    content_summary = envelope.get("content_summary")
    if not isinstance(content_summary, Mapping):
        return []

    preview_lines = content_summary.get("preview_lines")
    if preview_lines is None:
        return []

    if isinstance(preview_lines, Sequence) and not isinstance(preview_lines, (str, bytes)):
        count = len(preview_lines)
    else:
        return [
            _make_failure(
                check_id="M2-PREVIEW-LEN",
                severity="P2",
                message="content_summary.preview_lines must be a list",
                row=row,
            )
        ]

    if count > 10:
        return [
            _make_failure(
                check_id="M2-PREVIEW-LEN",
                severity="P2",
                message=f"preview_lines length {count} exceeds maximum 10",
                row=row,
            )
        ]
    return []


def _run_row_checks(
    envelope: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    sku: str,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    failures.extend(_check_m2_schema_20(envelope, row))
    if any(f["check_id"] == "M2-SCHEMA-20" for f in failures):
        return failures

    failures.extend(_check_m2_groq_basic(envelope, row, sku))
    failures.extend(_check_m2_enrich_block(envelope, row, sku))
    failures.extend(_check_m2_quality(envelope, row, sku))
    failures.extend(_check_m2_path_leak(envelope, row))
    failures.extend(_check_m2_preview_len(envelope, row))
    return failures


def _m2_ok_from_failures(failures: Sequence[Mapping[str, Any]]) -> bool:
    for item in failures:
        severity = str(item.get("severity", "P0")).upper()
        if severity in {"P0", "P1"}:
            return False
    return True


def _skipped_sample_validation(
    *,
    plan: SamplingPlan,
    reason: str,
    ok: bool = True,
) -> dict[str, Any]:
    return {
        "status": "skipped",
        "ok": ok,
        "reason": reason,
        "N": plan.N,
        "sample_size": plan.sample_size,
        "seed": plan.seed,
        "failed_checks": 0,
        "failures": [],
    }


def _completed_sample_validation(
    *,
    plan: SamplingPlan,
    failures: list[dict[str, Any]],
    ok: bool,
) -> dict[str, Any]:
    return {
        "status": "completed",
        "ok": ok,
        "N": plan.N,
        "sample_size": plan.sample_size,
        "seed": plan.seed,
        "failed_checks": len(failures),
        "failures": list(failures),
    }


def run_m2_checks(
    manifest_rows: Sequence[Any],
    sampling_plan: SamplingPlan,
    *,
    job_record: Wave6ManifestJobRecord | Mapping[str, Any],
    envelope_loader: EnvelopeLoader,
    manifest_integrity_ok: bool = True,
) -> dict[str, Any]:
    """
    Execute M2 checks on sampled ok manifest rows.

    ``manifest_rows`` must already be ok-only rows sorted by ``content_sha256``.
    ``envelope_loader`` receives ``stored_logical_path`` and returns an envelope dict.
    """

    job = _normalize_job_record(job_record)
    rows = [_normalize_row(row) for row in manifest_rows]

    if not manifest_integrity_ok:
        sample_validation = _skipped_sample_validation(
            plan=sampling_plan,
            reason="m1_failed",
            ok=True,
        )
        return {
            "ok": True,
            "sample_validation": sample_validation,
            "failures": [],
        }

    if sampling_plan.N <= 0 or sampling_plan.sample_size <= 0:
        sample_validation = _skipped_sample_validation(
            plan=sampling_plan,
            reason="no_sample",
            ok=True,
        )
        return {
            "ok": True,
            "sample_validation": sample_validation,
            "failures": [],
        }

    failures: list[dict[str, Any]] = []
    for index in sampling_plan.row_indexes:
        if index < 0 or index >= len(rows):
            failures.append(
                _make_failure(
                    check_id="M2-SCHEMA-20",
                    severity="P0",
                    message=f"sampling index {index} out of range for {len(rows)} ok rows",
                )
            )
            continue

        row = rows[index]
        envelope, load_failures = _load_envelope(row, envelope_loader)
        failures.extend(load_failures)
        if envelope is None:
            continue

        failures.extend(_run_row_checks(envelope, row, sku=job.sku))

    ok = _m2_ok_from_failures(failures)
    sample_validation = _completed_sample_validation(
        plan=sampling_plan,
        failures=failures,
        ok=ok,
    )

    return {
        "ok": ok,
        "sample_validation": sample_validation,
        "failures": failures,
    }


__all__ = [
    "EnvelopeLoader",
    "recompute_quality_score",
    "run_m2_checks",
]
