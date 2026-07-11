"""
Wave 6 minimal envelope v2 writer.

This writer only materializes per-file envelopes for a single job. It does not:
- compute billing truth
- aggregate manifest counters
- generate enrichment semantics
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from core.schemas.envelope_v2 import BasicEnvelopeV2, EnrichEnvelopeV2, EnvelopeV2

SKU_BASIC = "CLEAN-BASIC"
SKU_ENRICH = "CLEAN-ENRICH"
SUPPORTED_SKUS = frozenset({SKU_BASIC, SKU_ENRICH})
FORBIDDEN_KEYS = frozenset({"billable_u", "billable_l"})
FORBIDDEN_DELIVERY_PATH_KEYS = frozenset({"source_path", "stored_path"})


class EnvelopeWriterError(ValueError):
    """Raised when a raw row cannot be emitted as a valid delivery envelope."""


def _walk_keys(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            out.append(str(key))
            out.extend(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            out.extend(_walk_keys(item))
    return out


def _assert_no_forbidden_fields(raw_file: Mapping[str, Any]) -> None:
    all_keys = set(_walk_keys(raw_file))
    bad_billing = sorted(FORBIDDEN_KEYS & all_keys)
    if bad_billing:
        raise EnvelopeWriterError(
            f"envelope v2 must not carry billing truth fields: {', '.join(bad_billing)}"
        )

    bad_paths = sorted(FORBIDDEN_DELIVERY_PATH_KEYS & set(raw_file.keys()))
    if bad_paths:
        raise EnvelopeWriterError(
            f"delivery envelope must not expose raw path fields: {', '.join(bad_paths)}"
        )


def _normalize_job_sku(job_record: Mapping[str, Any]) -> str:
    sku = str(job_record.get("sku") or "").strip()
    if sku not in SUPPORTED_SKUS:
        supported = ", ".join(sorted(SUPPORTED_SKUS))
        raise EnvelopeWriterError(f"unsupported sku {sku!r}; expected one of: {supported}")
    return sku


def build_envelope(job_record: Mapping[str, Any], raw_file: Mapping[str, Any]) -> EnvelopeV2:
    """
    Validate and build a single envelope model from a job + raw file row.

    ``job_record`` must carry ``sku``.
    ``raw_file`` is the per-file payload candidate for envelope v2.0.
    """

    sku = _normalize_job_sku(job_record)
    _assert_no_forbidden_fields(raw_file)

    payload = dict(raw_file)
    payload.setdefault("schema_version", "2.0")

    if sku == SKU_BASIC:
        if "enrichment" in payload:
            raise EnvelopeWriterError("BASIC envelope must not include enrichment")
        if payload.get("groq_used") is True:
            raise EnvelopeWriterError("BASIC envelope must not set groq_used=true")
        return BasicEnvelopeV2.model_validate(payload)

    if "enrichment" not in payload:
        raise EnvelopeWriterError("ENRICH envelope requires enrichment block")
    return EnrichEnvelopeV2.model_validate(payload)


def write_envelopes(
    job_record: Mapping[str, Any],
    raw_files: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build validated envelope v2 payloads for one job."""

    return [build_envelope(job_record, raw_file).to_dict() for raw_file in raw_files]
