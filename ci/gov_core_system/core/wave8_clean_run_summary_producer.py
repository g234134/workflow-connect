"""
Wave 8 CLEAN-RUN-SUMMARY Outbox producer (derived view only).

Assembles ``clean_run_summary_v0.1`` from existing truth layers (``job_record``,
``report.json``, optional lifecycle ``run_result`` / M2 output). Does not modify
report schema, job_record, or lifecycle behavior; does not write to databases.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.wave7_artifact_storage import w6_logical_ref
from core.wave7_orch_job_lifecycle import WAVE7_LIFECYCLE_SCHEMA_VERSION
from core.wave7_report_summary_producer import M2_SAMPLE_VALIDATION_SKIPPED

CLEAN_RUN_SUMMARY_SCHEMA_VERSION = "clean_run_summary_v0.1"

COMPLETION_COMPLETED = "completed"
COMPLETION_COMPLETED_WITH_FAILURES = "completed_with_failures"

JOB_STATUS_TO_ORCH: dict[str, str] = {
    "pending": "PENDING",
    "running": "RUNNING",
    "done": "DONE",
    "failed": "FAILED",
    "blocked": "BLOCKED",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _normalize_failure_list(failures: Any) -> list[dict[str, Any]]:
    if not isinstance(failures, Sequence) or isinstance(failures, (str, bytes)):
        return []
    return [dict(item) for item in failures if isinstance(item, Mapping)]


def _count_failures_by_layer_severity(
    failures: Sequence[Any],
    *,
    layer: str | None,
    severity: str,
) -> int:
    count = 0
    layer_upper = layer.upper() if layer else None
    sev_upper = severity.upper()
    for item in failures:
        if not isinstance(item, Mapping):
            continue
        item_layer = str(item.get("layer", "")).upper()
        item_sev = str(item.get("severity", "P0")).upper()
        if layer_upper is not None and item_layer != layer_upper:
            continue
        if layer_upper is None and item_layer == "M2":
            continue
        if item_sev == sev_upper:
            count += 1
    return count


def _map_orch_status(job_status: str) -> str:
    return JOB_STATUS_TO_ORCH.get(str(job_status or "").strip().lower(), "FAILED")


def _resolve_completion_variant(
    *,
    job_status: str,
    job_record: Mapping[str, Any],
    run_result: Mapping[str, Any] | None,
) -> str | None:
    status = str(job_status or "").strip().lower()
    if status != "done":
        return None
    for source in (job_record, run_result or {}):
        variant = source.get("completion_variant")
        if variant == COMPLETION_COMPLETED_WITH_FAILURES:
            return COMPLETION_COMPLETED_WITH_FAILURES
    return COMPLETION_COMPLETED


def _resolve_product_sku(
    *,
    job_record: Mapping[str, Any],
    report_dict: Mapping[str, Any] | None,
) -> str:
    job_sku = str(job_record.get("sku") or job_record.get("product_sku") or "").strip()
    report_summary = _as_mapping(report_dict.get("summary")) if report_dict else {}
    report_sku = str(report_summary.get("sku") or "").strip()
    if job_sku and report_sku and job_sku != report_sku:
        raise ValueError(
            f"product_sku mismatch: job_record={job_sku!r} report.summary={report_sku!r}"
        )
    return job_sku or report_sku


def _coerce_w6_ref(job_id: str, kind: str, ref: Any) -> str | None:
    if ref is None:
        return None
    text = str(ref).strip()
    if not text:
        return None
    if text.startswith("w6://"):
        return text
    return w6_logical_ref(job_id, kind)


def _build_artifacts_section(
    *,
    job_id: str,
    artifacts: Mapping[str, Any] | None,
    run_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    refs = _as_mapping(artifacts)
    if not refs and run_result is not None:
        refs = _as_mapping(run_result.get("artifacts"))

    report_json_ref = _coerce_w6_ref(
        job_id,
        "report_json",
        refs.get("report_ref") or refs.get("report_json_ref"),
    )
    report_md_ref = _coerce_w6_ref(job_id, "report_md", refs.get("report_md_ref"))
    manifest_ref = _coerce_w6_ref(job_id, "manifest", refs.get("manifest_ref"))
    if manifest_ref is None and job_id:
        manifest_ref = w6_logical_ref(job_id, "manifest")

    deliverable_refs: list[str] = []
    deliverables_ref = refs.get("deliverables_ref")
    if isinstance(deliverables_ref, str) and deliverables_ref.strip():
        deliverable_refs.append(_coerce_w6_ref(job_id, "deliverables", deliverables_ref) or "")
    extra = refs.get("deliverable_refs")
    if isinstance(extra, Sequence) and not isinstance(extra, (str, bytes)):
        for item in extra:
            coerced = _coerce_w6_ref(job_id, "deliverables", item)
            if coerced:
                deliverable_refs.append(coerced)
    deliverable_refs = [ref for ref in deliverable_refs if ref]

    report_md_rendered = bool(report_md_ref)

    return {
        "report_json_ref": report_json_ref,
        "report_md_ref": report_md_ref,
        "manifest_ref": manifest_ref,
        "deliverable_refs": deliverable_refs,
        "report_md_rendered": report_md_rendered,
    }


def _build_m1_summary(qa: Mapping[str, Any]) -> dict[str, Any]:
    integrity = _as_mapping(qa.get("manifest_integrity"))
    failures = _normalize_failure_list(qa.get("failures"))
    return {
        "ok": bool(integrity.get("ok")),
        "checked_rows": int(integrity.get("checked_rows") or 0),
        "failed_rows": int(integrity.get("failed_rows") or 0),
        "failed_checks": int(integrity.get("failed_checks") or 0),
        "p0_failure_count": _count_failures_by_layer_severity(failures, layer=None, severity="P0"),
        "p1_failure_count": _count_failures_by_layer_severity(failures, layer=None, severity="P1"),
    }


def _build_m2_summary(
    *,
    qa: Mapping[str, Any],
    m2_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    sample_raw = qa.get("sample_validation")
    if not isinstance(sample_raw, Mapping) and m2_result is not None:
        sample_raw = m2_result.get("sample_validation")
    if not isinstance(sample_raw, Mapping):
        sample_raw = M2_SAMPLE_VALIDATION_SKIPPED

    failures = _normalize_failure_list(qa.get("failures"))
    if not failures and m2_result is not None:
        failures = _normalize_failure_list(m2_result.get("failures"))

    return {
        "status": str(sample_raw.get("status") or "skipped"),
        "ok": bool(sample_raw.get("ok")),
        "N": sample_raw.get("N"),
        "sample_size": sample_raw.get("sample_size"),
        "seed": sample_raw.get("seed"),
        "failed_checks": int(sample_raw.get("failed_checks") or 0),
        "p0_failure_count": _count_failures_by_layer_severity(failures, layer="M2", severity="P0"),
        "p1_failure_count": _count_failures_by_layer_severity(failures, layer="M2", severity="P1"),
        "reason": sample_raw.get("reason"),
    }


def _build_input_volume(
    *,
    report_dict: Mapping[str, Any] | None,
    input_volume_hint: Mapping[str, Any] | None,
    intake_record: Mapping[str, Any] | None,
) -> dict[str, Any]:
    hint = _as_mapping(input_volume_hint)
    intake = _as_mapping(intake_record)
    data_profile = _as_mapping(intake.get("data_profile"))

    file_count = hint.get("file_count")
    if file_count is None and hint.get("input_count") is not None:
        file_count = hint.get("input_count")

    row_count = hint.get("row_count")
    if row_count is None:
        row_count = data_profile.get("row_count_estimate")
    if row_count is None and report_dict is not None:
        summary = _as_mapping(report_dict.get("summary"))
        row_count = summary.get("total_rows")

    size_bytes = hint.get("size_bytes")
    skipped_file_count = hint.get("skipped_file_count")
    if skipped_file_count is None:
        skipped = hint.get("skipped")
        if isinstance(skipped, Sequence) and not isinstance(skipped, (str, bytes)):
            skipped_file_count = len(skipped)
        else:
            skipped_file_count = 0

    return {
        "file_count": file_count,
        "row_count": row_count,
        "size_bytes": size_bytes,
        "skipped_file_count": int(skipped_file_count or 0),
    }


def _build_costs_section(
    *,
    report_dict: Mapping[str, Any] | None,
    order_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    summary = _as_mapping(report_dict.get("summary")) if report_dict else {}
    cost = _as_mapping(summary.get("cost"))
    order = _as_mapping(order_context)
    cost_estimate = _as_mapping(order.get("cost_estimate"))

    billing_units = summary.get("billing_units")
    if billing_units is not None and not isinstance(billing_units, Mapping):
        billing_units = None

    chargeable_hint = summary.get("chargeable_hint")
    if chargeable_hint is None:
        chargeable_hint = cost.get("chargeable_hint")

    currency = cost.get("currency")
    if currency is None:
        currency = "USD" if cost or summary.get("billing_units") else None

    return {
        "billing_table_version": cost.get("billing_table_version"),
        "billing_units": dict(billing_units) if isinstance(billing_units, Mapping) else None,
        "chargeable_hint": chargeable_hint,
        "tool_cost_estimate": cost_estimate.get("tool_cost_estimate"),
        "human_hours_estimate": cost_estimate.get("human_hours_estimate"),
        "currency": currency,
    }


def _build_runtime_stats(
    *,
    job_record: Mapping[str, Any],
    run_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    lifecycle = run_result or {}
    storage_retry_count = lifecycle.get("storage_attempts")
    if storage_retry_count is None:
        storage_retry_count = job_record.get("storage_attempts", 0)

    checkpoint = str(lifecycle.get("checkpoint") or job_record.get("checkpoint") or "none")
    envelope_compute_count = int(
        lifecycle.get("envelope_compute_count") or job_record.get("envelope_compute_count") or 0
    )
    storage_retry_count_int = int(storage_retry_count or 0)
    checkpoint_hit = checkpoint == "manifest" and storage_retry_count_int > 1

    started_at = job_record.get("started_at")
    completed_at = job_record.get("completed_at")
    duration_ms = None
    if started_at and completed_at:
        try:
            start = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
            end = datetime.fromisoformat(str(completed_at).replace("Z", "+00:00"))
            duration_ms = int((end - start).total_seconds() * 1000)
        except (TypeError, ValueError):
            duration_ms = None

    return {
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": duration_ms,
        "lifecycle_schema_version": str(
            lifecycle.get("schema_version") or WAVE7_LIFECYCLE_SCHEMA_VERSION
        ),
        "final_stage": str(lifecycle.get("stage") or job_record.get("stage") or ""),
        "storage_retry_count": storage_retry_count_int,
        "envelope_compute_count": envelope_compute_count,
        "checkpoint": checkpoint,
        "checkpoint_hit": checkpoint_hit,
        "error_code": lifecycle.get("error_code") or job_record.get("error_code"),
        "message": str(lifecycle.get("message") or job_record.get("message") or ""),
    }


def _source_event_for_status(job_status: str) -> str:
    status = str(job_status or "").strip().lower()
    if status == "done":
        return "wave7.job.finalized"
    if status == "failed":
        return "wave7.job.failed"
    if status == "blocked":
        return "wave7.job.blocked"
    return "wave7.job.in_progress"


def _build_provenance(
    *,
    report_dict: Mapping[str, Any] | None,
    run_result: Mapping[str, Any] | None,
    artifacts_section: Mapping[str, Any],
    job_status: str,
) -> dict[str, Any]:
    lifecycle = run_result or {}
    return {
        "report_schema_version": (
            str(report_dict.get("schema_version")) if report_dict else None
        ),
        "lifecycle_schema_version": str(
            lifecycle.get("schema_version") or WAVE7_LIFECYCLE_SCHEMA_VERSION
        ),
        "source_event": _source_event_for_status(job_status),
        "truth_refs": {
            "report_json": artifacts_section.get("report_json_ref"),
            "manifest": artifacts_section.get("manifest_ref"),
        },
    }


def build_clean_run_summary(
    *,
    job_record: Mapping[str, Any],
    report_dict: Mapping[str, Any] | None,
    m2_result: Mapping[str, Any] | None = None,
    artifacts: Mapping[str, Any] | None = None,
    run_result: Mapping[str, Any] | None = None,
    intake_record: Mapping[str, Any] | None = None,
    order_context: Mapping[str, Any] | None = None,
    input_volume_hint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a ``CLEAN-RUN-SUMMARY`` document from truth-layer inputs.

    Pure derivation only — no re-judgment of QA outcomes. Optional ``run_result``
    supplies lifecycle fields for ``runtime_stats`` / ``artifacts`` when not passed
    explicitly via ``artifacts``.
    """

    job = _as_mapping(job_record)
    job_id = str(job.get("job_id") or (report_dict or {}).get("job_id") or "").strip()
    if not job_id:
        raise ValueError("job_id required in job_record or report_dict")

    product_sku = _resolve_product_sku(job_record=job, report_dict=report_dict)

    job_status = str(
        job.get("status") or (run_result or {}).get("status") or "failed"
    ).strip().lower()
    orch_status = _map_orch_status(job_status)
    completion_variant = _resolve_completion_variant(
        job_status=job_status,
        job_record=job,
        run_result=run_result,
    )

    report_summary = _as_mapping(report_dict.get("summary")) if report_dict else {}
    qa = _as_mapping(report_dict.get("qa")) if report_dict else {}

    billing_units = report_summary.get("billing_units")
    if billing_units is not None and not isinstance(billing_units, Mapping):
        billing_units = {"U": 0, "L": 0}

    qa_status = report_summary.get("qa_status")
    overall_ok = bool(qa.get("overall_ok")) if qa else False

    order = _as_mapping(order_context)
    identity: dict[str, Any] = {
        "job_id": job_id,
        "product_sku": product_sku,
        "intake_id": (_as_mapping(intake_record).get("intake_id") if intake_record else None),
        "order_id": order.get("order_id"),
        "client_ref": str(job.get("client_ref") or order.get("client_ref") or ""),
        "batch_tag": order.get("batch_tag"),
    }

    outcome: dict[str, Any] = {
        "accepted_units": int(report_summary.get("accepted_units") or 0),
        "rejected_units": int(report_summary.get("rejected_units") or 0),
        "billing_units": dict(billing_units) if isinstance(billing_units, Mapping) else {"U": 0, "L": 0},
        "qa_status": qa_status,
        "completion_variant": completion_variant,
        "overall_ok": overall_ok,
        "orch_status": orch_status,
        "job_status": job_status,
    }

    qa_layers = {
        "m1_summary": _build_m1_summary(qa),
        "m2_summary": _build_m2_summary(qa=qa, m2_result=m2_result),
    }

    artifacts_section = _build_artifacts_section(
        job_id=job_id,
        artifacts=artifacts,
        run_result=run_result,
    )

    return {
        "schema_version": CLEAN_RUN_SUMMARY_SCHEMA_VERSION,
        "generated_at": _utc_now_iso(),
        "identity": identity,
        "input_volume": _build_input_volume(
            report_dict=report_dict,
            input_volume_hint=input_volume_hint,
            intake_record=intake_record,
        ),
        "outcome": outcome,
        "qa_layers": qa_layers,
        "runtime_stats": _build_runtime_stats(job_record=job, run_result=run_result),
        "artifacts": artifacts_section,
        "costs": _build_costs_section(report_dict=report_dict, order_context=order_context),
        "provenance": _build_provenance(
            report_dict=report_dict,
            run_result=run_result,
            artifacts_section=artifacts_section,
            job_status=job_status,
        ),
    }


def write_clean_run_summary_to_file(
    summary: Mapping[str, Any],
    *,
    out_dir: str | Path,
    job_id: str,
) -> dict[str, Any]:
    """
    Persist ``summary`` as ``{out_dir}/{job_id}/run_summary.json`` (relative layout).
    """

    jid = str(job_id or summary.get("identity", {}).get("job_id") or "").strip()
    if not jid:
        return {"ok": False, "path": None, "message": "job_id required"}

    root = Path(out_dir)
    target = root / jid / "run_summary.json"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(dict(summary), indent=2, ensure_ascii=False) + "\n"
        target.write_text(payload, encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "path": None, "message": str(exc)}

    rel_path = f"{jid}/run_summary.json"
    return {"ok": True, "path": rel_path, "message": "clean_run_summary_written"}


__all__ = [
    "CLEAN_RUN_SUMMARY_SCHEMA_VERSION",
    "COMPLETION_COMPLETED",
    "COMPLETION_COMPLETED_WITH_FAILURES",
    "JOB_STATUS_TO_ORCH",
    "build_clean_run_summary",
    "write_clean_run_summary_to_file",
]
