"""
Wave 7 in-memory orchestrator pipeline wire for frozen Wave 6 modules.

Stages (fixed order):
  raw_files → write_envelopes
  envelopes → normalize_manifest_inputs (ENRICH present gate only here)
  normalized → write_manifest
  manifest summary → run_m1_checks → build_wave7_report

Does not write disk, lifecycle, or checkpoints.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from core.envelope_writer import EnvelopeWriterError, write_envelopes
from core.wave6_manifest_writer import write_manifest
from core.wave6_qa_manifest_m1 import run_m1_checks
from core.schemas.wave6_manifest import ManifestV20, WAVE6_BILLING_TABLE_VERSION_DEFAULT
from core.wave7_report_summary_producer import (
    build_summary_for_m1_checks,
    build_wave7_report,
)
from core.wave8_m2_execution_engine import EnvelopeLoader, run_m2_checks
from core.wave8_m2_sampling_design import SamplingPlan, build_sampling_plan

WAVE7_QA_REPORT_STUB_BRIDGE_VERSION = "wave7_qa_report_stub_bridge_v0"
WAVE7_QA_REPORT_STUB_BRIDGE_NOTICE = (
    "NOT Wave 7 formal report.summary producer — temporary M1-COUNT bridge only"
)

STAGE_ENVELOPE = "envelope"
STAGE_MANIFEST = "manifest"
STAGE_QA = "qa"

ERR_ENVELOPE = "envelope_stage_failed"
ERR_MANIFEST = "manifest_stage_failed"
ERR_QA = "qa_stage_failed"


def build_qa_report_stub_bridge(*, accepted_units: int) -> dict[str, Any]:
    """
    Deprecated stand-in for QA-M1 ``M1-COUNT`` during early Wave 7 wiring.

    **Superseded by** ``core.wave7_report_summary_producer.build_summary_for_m1_checks``
    and ``build_wave7_report``. Kept for tests that intentionally inject a wrong count.
    """

    return {
        "_wave7_bridge": True,
        "_bridge_version": WAVE7_QA_REPORT_STUB_BRIDGE_VERSION,
        "_bridge_notice": WAVE7_QA_REPORT_STUB_BRIDGE_NOTICE,
        "_superseded_by": "wave7_report_summary_producer",
        "accepted_units": int(accepted_units),
    }


def normalize_envelope_for_manifest(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """
    Convert delivery envelope rows to manifest-writer input shape.

    ENRICH delivery envelopes carry ``enrichment.present``; manifest rows use
    ``ManifestEnrichment`` without that delivery-only gate:

    - ``present=true``: strip ``present``; keep enrichment block for manifest.
    - ``present=false``: drop entire ``enrichment`` key (align with rejected rows).
    """

    out = deepcopy(dict(envelope))
    enrichment = out.get("enrichment")
    if not isinstance(enrichment, dict):
        return out
    if enrichment.get("present") is True:
        out["enrichment"] = {key: value for key, value in enrichment.items() if key != "present"}
        return out
    out.pop("enrichment", None)
    return out


def normalize_manifest_inputs(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    sku: str,
) -> list[dict[str, Any]]:
    """Apply manifest input normalization for all envelope rows."""

    if sku == "CLEAN-BASIC":
        return [dict(item) for item in envelopes]
    return [normalize_envelope_for_manifest(item) for item in envelopes]


def _fail(
    *,
    stage: str,
    error_code: str,
    message: str,
    envelopes: list[dict[str, Any]] | None = None,
    manifest: ManifestV20 | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "stage": stage,
        "error_code": error_code,
        "message": message,
        "envelopes": envelopes,
        "manifest": manifest,
        "qa": None,
    }


def _billing_table_version_for_sampling(
    billing_table: Mapping[str, Any] | str | None,
) -> str:
    if isinstance(billing_table, str):
        text = billing_table.strip()
        return text or WAVE6_BILLING_TABLE_VERSION_DEFAULT
    if billing_table is None:
        return WAVE6_BILLING_TABLE_VERSION_DEFAULT
    value = str(billing_table.get("billing_table_version") or "").strip()
    return value or WAVE6_BILLING_TABLE_VERSION_DEFAULT


def _m1_manifest_integrity_ok(qa_m1_result: Mapping[str, Any]) -> bool:
    qa = qa_m1_result.get("qa")
    if not isinstance(qa, Mapping):
        return False
    integrity = qa.get("manifest_integrity")
    return bool(isinstance(integrity, Mapping) and integrity.get("ok"))


def sorted_ok_manifest_rows(manifest: ManifestV20) -> list[dict[str, Any]]:
    """Ok-only manifest rows sorted by ``content_sha256`` (M2 contract)."""

    rows: list[dict[str, Any]] = []
    for row in manifest.rows:
        if row.clean_status != "ok":
            continue
        to_dict = getattr(row, "to_contract_dict", None)
        if callable(to_dict):
            rows.append(dict(to_dict()))
        elif isinstance(row, Mapping):
            rows.append(dict(row))
    rows.sort(key=lambda item: str(item.get("content_sha256") or "").lower())
    return rows


def envelope_loader_from_envelopes(
    envelopes: Sequence[Mapping[str, Any]] | None,
) -> EnvelopeLoader:
    by_path: dict[str, Mapping[str, Any]] = {}
    for envelope in envelopes or []:
        if not isinstance(envelope, Mapping):
            continue
        path = str(envelope.get("stored_logical_path") or "").strip()
        if path:
            by_path[path] = envelope

    def _load(ref: str) -> Mapping[str, Any] | dict[str, Any] | None:
        return by_path.get(ref)

    return _load


def m2_checks_error_result(
    manifest: ManifestV20,
    exc: BaseException,
    *,
    billing_table: Mapping[str, Any] | str | None = None,
) -> dict[str, Any]:
    """Build a non-strict M2 failure payload after an unexpected error."""

    ok_rows = sorted_ok_manifest_rows(manifest)
    version = _billing_table_version_for_sampling(billing_table)
    plan = build_sampling_plan(len(ok_rows), billing_table_version=version)
    return _m2_error_result(plan=plan, message=f"m2_checks_failed: {exc}")


def _m2_error_result(*, plan: SamplingPlan, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "sample_validation": {
            "status": "error",
            "ok": False,
            "reason": message,
            "N": plan.N,
            "sample_size": plan.sample_size,
            "seed": plan.seed,
            "failed_checks": 0,
            "failures": [],
        },
        "failures": [],
    }


def execute_m2_checks(
    manifest: ManifestV20,
    *,
    job_record: Mapping[str, Any],
    envelopes: Sequence[Mapping[str, Any]] | None,
    qa_m1_result: Mapping[str, Any],
    billing_table: Mapping[str, Any] | str | None = None,
    strict_m2: bool = False,
) -> dict[str, Any]:
    """
    Build sampling plan and run M2 checks (Wave 8).

    When M1 integrity failed, ``run_m2_checks`` skips envelope I/O via
    ``manifest_integrity_ok=False``. On unexpected errors: raises if ``strict_m2``,
    otherwise returns an M2 result with ``sample_validation.status=error``.
    """

    ok_rows = sorted_ok_manifest_rows(manifest)
    version = _billing_table_version_for_sampling(billing_table)
    plan = build_sampling_plan(len(ok_rows), billing_table_version=version)
    manifest_integrity_ok = _m1_manifest_integrity_ok(qa_m1_result)
    loader = envelope_loader_from_envelopes(envelopes)

    try:
        return run_m2_checks(
            ok_rows,
            plan,
            job_record=job_record,
            envelope_loader=loader,
            manifest_integrity_ok=manifest_integrity_ok,
        )
    except Exception as exc:
        if strict_m2:
            raise
        return _m2_error_result(plan=plan, message=f"m2_checks_failed: {exc}")


def _resolve_report_summary(
    manifest: ManifestV20,
    job_record: Mapping[str, Any],
    qa_report_stub: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if qa_report_stub is not None:
        return dict(qa_report_stub)
    return build_summary_for_m1_checks(manifest, job_record)


def run_wave6_pipeline(
    job_record: Mapping[str, Any],
    raw_files: Sequence[Mapping[str, Any]],
    *,
    qa_report_stub: Mapping[str, Any] | None = None,
    billing_table: Mapping[str, Any] | str | None = None,
    enable_m2: bool = False,
    strict_m2: bool = False,
) -> dict[str, Any]:
    """
    Run the frozen Wave 6 in-memory chain for one job.

    Returns ``{ok, envelopes, manifest, qa, message, error_code}``; on failure also
    ``stage`` in ``{envelope, manifest, qa}``.
    """

    sku = str(job_record.get("sku") or "").strip()

    try:
        envelopes = write_envelopes(job_record, raw_files)
    except (EnvelopeWriterError, ValueError, TypeError) as exc:
        return _fail(
            stage=STAGE_ENVELOPE,
            error_code=ERR_ENVELOPE,
            message=str(exc),
        )

    try:
        manifest_inputs = normalize_manifest_inputs(envelopes, sku=sku)
        manifest = write_manifest(job_record, manifest_inputs, billing_table=billing_table)
    except (ValueError, TypeError) as exc:
        return _fail(
            stage=STAGE_MANIFEST,
            error_code=ERR_MANIFEST,
            message=str(exc),
            envelopes=envelopes,
        )

    try:
        report_summary = _resolve_report_summary(manifest, job_record, qa_report_stub)
        qa_out = run_m1_checks(manifest, job_record, report_summary)
        m2_result: dict[str, Any] | None = None
        if enable_m2:
            m2_result = execute_m2_checks(
                manifest,
                job_record=job_record,
                envelopes=envelopes,
                qa_m1_result=qa_out,
                billing_table=billing_table,
                strict_m2=strict_m2,
            )
        report_build = build_wave7_report(
            job_record,
            manifest.to_contract_dict(),
            qa_out,
            billing_table=billing_table,
            m2_result=m2_result,
        )
        if not report_build.get("ok"):
            return _fail(
                stage=STAGE_QA,
                error_code=ERR_QA,
                message=str(report_build.get("message") or "report_build_failed"),
                envelopes=envelopes,
                manifest=manifest,
            )
    except (ValueError, TypeError) as exc:
        return _fail(
            stage=STAGE_MANIFEST,
            error_code=ERR_QA,
            message=str(exc),
            envelopes=envelopes,
            manifest=manifest,
        )

    return {
        "ok": True,
        "stage": None,
        "error_code": None,
        "message": "wave6_pipeline_ok",
        "envelopes": envelopes,
        "manifest": manifest,
        "qa": qa_out,
        "report": report_build["report"],
    }


__all__ = [
    "STAGE_ENVELOPE",
    "STAGE_MANIFEST",
    "STAGE_QA",
    "ERR_ENVELOPE",
    "ERR_MANIFEST",
    "ERR_QA",
    "WAVE7_QA_REPORT_STUB_BRIDGE_VERSION",
    "WAVE7_QA_REPORT_STUB_BRIDGE_NOTICE",
    "build_qa_report_stub_bridge",
    "normalize_envelope_for_manifest",
    "normalize_manifest_inputs",
    "execute_m2_checks",
    "envelope_loader_from_envelopes",
    "m2_checks_error_result",
    "run_wave6_pipeline",
    "sorted_ok_manifest_rows",
]
