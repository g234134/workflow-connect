"""
Wave 7 single-job orchestrator and lifecycle state machine (ORCH-JOB-LIFECYCLE).

Stages (fixed order):
  intake (optional, via runner entry) → entry → pipeline (envelope + manifest)
  → report summary → QA-M1 → artifact finalize

State transitions (documented):
  PENDING → RUNNING → DONE | FAILED | BLOCKED
  DONE may carry completion_variant=completed_with_failures (R3 §G.7).

Checkpoint: after manifest (+ envelopes) persist to staging, report/QA/storage
may retry without recomputing envelopes.

Does not implement multi-job scheduling, BASIC→ENRICH upgrade, Phase 6.5
delivery.status, or distributed locks.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from core.envelope_writer import EnvelopeWriterError, write_envelopes
from core.schemas.wave6_manifest import ManifestV20
from core.wave6_qa_manifest_m1 import run_m1_checks
from core.wave7_artifact_storage import ERR_IO, store_wave7_artifacts, w6_logical_ref
from core.wave7_orch_pipeline_wire import (
    ERR_ENVELOPE,
    ERR_MANIFEST,
    execute_m2_checks,
    m2_checks_error_result,
    normalize_manifest_inputs,
)
from core.wave7_report_summary_producer import build_summary_for_m1_checks, build_wave7_report
from core.wave7_runner_entry_job_input import build_runner_job_input
from core.wave6_manifest_writer import write_manifest
from core.wave8_report_md_renderer import render_data_clean_report

WAVE7_LIFECYCLE_SCHEMA_VERSION = "wave7_orch_job_lifecycle_v0.1"

# --- Job lifecycle status (ticket §2.2) ---
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_BLOCKED = "blocked"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

COMPLETION_COMPLETED_WITH_FAILURES = "completed_with_failures"

# --- Stages ---
STAGE_INTAKE = "intake"
STAGE_ENTRY = "entry"
STAGE_PIPELINE = "pipeline"
STAGE_REPORT = "report"
STAGE_QA = "qa"
STAGE_STORAGE = "storage"

CHECKPOINT_NONE = "none"
CHECKPOINT_MANIFEST = "manifest"

# --- Policies ---
P0_POLICY_FAILED = "failed"
P0_POLICY_BLOCKED = "blocked"

DEFAULT_MAX_RETRIES = 3

ERR_ENTRY = "entry_failed"
ERR_PIPELINE = "pipeline_stage_failed"
ERR_REPORT = "report_build_failed"
ERR_M2 = "m2_checks_failed"
ERR_QA_P0 = "qa_m1_p0_failed"
ERR_STORAGE = "storage_failed"
ERR_INVALID_INPUT = "invalid_job_input"

NON_RETRYABLE_CODES = frozenset(
    {
        ERR_ENTRY,
        ERR_ENVELOPE,
        ERR_MANIFEST,
        ERR_PIPELINE,
        ERR_REPORT,
        ERR_M2,
        ERR_QA_P0,
        ERR_INVALID_INPUT,
        "intake_deferred",
        "intake_rejected",
        "unknown_sku",
        "sku_intake_mismatch",
        "empty_batch",
        "invalid_cleaned_json",
    }
)

# State transition table (META documentation):
# | from     | event                    | to       | notes                          |
# |----------|--------------------------|----------|--------------------------------|
# | pending  | run started              | running  |                                |
# | running  | all stages ok            | done     | may set completed_with_failures|
# | running  | P0 QA + policy failed    | failed   | default; no finalize           |
# | running  | P0 QA + policy blocked   | blocked  | configurable                   |
# | running  | non-retryable stage err  | failed   | retryable=False                |
# | running  | retryable IO exhausted   | failed   | after max_retries              |


LifecycleHook = Callable[["JobRunContext"], None]


@dataclass
class JobRunContext:
    """In-memory checkpoint for a single job run."""

    status: str = STATUS_PENDING
    stage: str = STAGE_ENTRY
    checkpoint: str = CHECKPOINT_NONE
    job_record: dict[str, Any] | None = None
    raw_files: list[dict[str, Any]] = field(default_factory=list)
    envelopes: list[dict[str, Any]] | None = None
    manifest: ManifestV20 | None = None
    qa: dict[str, Any] | None = None
    report: dict[str, Any] | None = None
    manifest_stored: bool = False
    envelope_compute_count: int = 0
    message: str = ""
    error_code: str | None = None
    retryable: bool = False
    completion_variant: str | None = None
    storage_attempts: int = 0
    m2_result: dict[str, Any] | None = None


def _job_record_for_manifest(job_record: Mapping[str, Any]) -> dict[str, Any]:
    """Manifest writer accepts only ``job_id`` + ``sku`` (strict schema)."""
    return {
        "job_id": str(job_record["job_id"]),
        "sku": str(job_record["sku"]),
    }


def _has_p0_failures(qa_m1: Mapping[str, Any]) -> bool:
    qa = qa_m1.get("qa")
    if not isinstance(qa, Mapping):
        return True
    failures = qa.get("failures")
    if not isinstance(failures, list):
        return True
    for item in failures:
        if isinstance(item, Mapping) and str(item.get("severity", "P0")).upper() == "P0":
            return True
    return False


def _manifest_has_rejected_rows(manifest: ManifestV20) -> bool:
    return any(row.clean_status != "ok" for row in manifest.rows)


def _is_retryable_error(code: str | None) -> bool:
    if not code:
        return False
    return code not in NON_RETRYABLE_CODES and code == ERR_IO


def _result_from_context(
    ctx: JobRunContext,
    *,
    ok: bool,
    artifacts: dict[str, str] | None = None,
) -> dict[str, Any]:
    job_record = dict(ctx.job_record or {})
    job_record["status"] = ctx.status
    if ctx.completion_variant:
        job_record["completion_variant"] = ctx.completion_variant

    refs = artifacts or {}
    if ctx.job_record and "job_id" in ctx.job_record:
        jid = str(ctx.job_record["job_id"])
        refs = {
            "manifest_ref": refs.get("manifest_ref") or w6_logical_ref(jid, "manifest"),
            "report_ref": refs.get("report_ref") or w6_logical_ref(jid, "report_json"),
            "report_md_ref": refs.get("report_md_ref") or w6_logical_ref(jid, "report_md"),
            "deliverables_ref": refs.get("deliverables_ref") or w6_logical_ref(jid, "deliverables"),
            **{k: v for k, v in refs.items() if k not in ("manifest_ref", "report_ref", "report_md_ref", "deliverables_ref")},
        }

    return {
        "ok": ok,
        "status": ctx.status,
        "stage": ctx.stage,
        "completion_variant": ctx.completion_variant,
        "artifacts": refs,
        "qa": ctx.qa,
        "retryable": ctx.retryable,
        "message": ctx.message,
        "error_code": ctx.error_code,
        "job_record": job_record,
        "checkpoint": ctx.checkpoint,
        "storage_attempts": ctx.storage_attempts,
        "envelope_compute_count": ctx.envelope_compute_count,
        "schema_version": WAVE7_LIFECYCLE_SCHEMA_VERSION,
    }


def _resolve_entry(
    job_input: Mapping[str, Any],
    *,
    hooks: Mapping[str, LifecycleHook] | None,
) -> tuple[JobRunContext | None, dict[str, Any] | None]:
    ctx = JobRunContext(status=STATUS_RUNNING, stage=STAGE_ENTRY)

    if "job_record" in job_input and "raw_files" in job_input:
        job_record = job_input.get("job_record")
        raw_files = job_input.get("raw_files")
        if not isinstance(job_record, Mapping) or not isinstance(raw_files, list):
            ctx.status = STATUS_FAILED
            ctx.error_code = ERR_INVALID_INPUT
            ctx.message = "job_record and raw_files required when provided together"
            ctx.retryable = False
            return ctx, _result_from_context(ctx, ok=False)
        ctx.job_record = dict(job_record)
        ctx.raw_files = [dict(r) for r in raw_files if isinstance(r, Mapping)]
        if not ctx.raw_files:
            ctx.status = STATUS_FAILED
            ctx.error_code = ERR_ENTRY
            ctx.message = "raw_files empty"
            ctx.retryable = False
            return ctx, _result_from_context(ctx, ok=False)
        return ctx, None

    sku = str(job_input.get("sku") or "").strip()
    client_ref = str(job_input.get("client_ref") or "").strip()
    if not sku or not client_ref:
        ctx.status = STATUS_FAILED
        ctx.error_code = ERR_INVALID_INPUT
        ctx.message = "provide job_record+raw_files or sku+client_ref"
        ctx.retryable = False
        return ctx, _result_from_context(ctx, ok=False)

    intake_request = job_input.get("intake_request")
    entry = build_runner_job_input(
        sku=sku,
        client_ref=client_ref,
        cleaned_dir=job_input.get("cleaned_dir"),
        manifest_path=job_input.get("manifest_path"),
        queue_payload=job_input.get("queue_payload")
        if isinstance(job_input.get("queue_payload"), Mapping)
        else None,
        job_id=job_input.get("job_id"),
        intake_request=intake_request if isinstance(intake_request, Mapping) else None,
        base_dir=job_input.get("base_dir"),
    )
    if not entry.get("ok"):
        ctx.status = STATUS_FAILED
        ctx.stage = STAGE_INTAKE if entry.get("error_code", "").startswith("intake") else STAGE_ENTRY
        ctx.error_code = str(entry.get("error_code") or ERR_ENTRY)
        ctx.message = str(entry.get("message") or "entry failed")
        ctx.retryable = _is_retryable_error(ctx.error_code)
        return ctx, _result_from_context(ctx, ok=False)

    ctx.job_record = dict(entry["job_record"])
    ctx.raw_files = [dict(r) for r in entry.get("raw_files") or []]
    if hooks and "after_entry" in hooks:
        hooks["after_entry"](ctx)
    return ctx, None


def _run_pipeline_memory(ctx: JobRunContext) -> dict[str, Any] | None:
    """Envelope + manifest in memory; increments envelope_compute_count."""

    assert ctx.job_record is not None
    ctx.stage = STAGE_PIPELINE

    try:
        ctx.envelope_compute_count += 1
        manifest_job = _job_record_for_manifest(ctx.job_record)
        envelopes = write_envelopes(manifest_job, ctx.raw_files)
    except (EnvelopeWriterError, ValueError, TypeError) as exc:
        ctx.status = STATUS_FAILED
        ctx.stage = STAGE_PIPELINE
        ctx.error_code = ERR_ENVELOPE
        ctx.message = str(exc)
        ctx.retryable = False
        return _result_from_context(ctx, ok=False)

    sku = str(ctx.job_record.get("sku") or "")
    try:
        manifest_inputs = normalize_manifest_inputs(envelopes, sku=sku)
        manifest = write_manifest(manifest_job, manifest_inputs)
    except (ValueError, TypeError) as exc:
        ctx.status = STATUS_FAILED
        ctx.stage = STAGE_PIPELINE
        ctx.error_code = ERR_MANIFEST
        ctx.message = str(exc)
        ctx.retryable = False
        return _result_from_context(ctx, ok=False)

    ctx.envelopes = envelopes
    ctx.manifest = manifest
    ctx.checkpoint = CHECKPOINT_MANIFEST
    return None


def _persist_manifest_checkpoint(
    ctx: JobRunContext,
    *,
    paths_resolved: dict[str, str] | None,
    repo_root: Any,
    start: Any,
    json_writer: Callable[[Any, str], None] | None,
) -> dict[str, Any] | None:
    if ctx.manifest_stored or ctx.manifest is None or ctx.job_record is None:
        return None

    ctx.stage = STAGE_STORAGE
    manifest_dict = ctx.manifest.to_contract_dict()
    store = store_wave7_artifacts(
        str(ctx.job_record["job_id"]),
        str(ctx.job_record.get("sku") or ""),
        envelopes=ctx.envelopes,
        manifest=manifest_dict,
        report=None,
        mode="overwrite_stage",
        paths_resolved=paths_resolved,
        repo_root=repo_root,
        start=start,
        json_writer=None,
    )
    if not store.get("ok"):
        ctx.status = STATUS_FAILED
        ctx.error_code = str(store.get("error_code") or ERR_STORAGE)
        ctx.message = str(store.get("message") or "manifest checkpoint store failed")
        ctx.retryable = _is_retryable_error(ctx.error_code)
        return _result_from_context(
            ctx,
            ok=False,
            artifacts=store.get("artifact_refs") or {},
        )

    ctx.manifest_stored = True
    ctx.checkpoint = CHECKPOINT_MANIFEST
    return None


def _run_qa_and_report(
    ctx: JobRunContext,
    *,
    billing_table: Mapping[str, Any] | str | None,
    p0_failure_policy: str,
    hooks: Mapping[str, LifecycleHook] | None,
    enable_m2: bool = False,
    strict_m2: bool = False,
) -> dict[str, Any] | None:
    assert ctx.job_record is not None and ctx.manifest is not None

    if hooks and "after_manifest" in hooks:
        hooks["after_manifest"](ctx)

    manifest_job = _job_record_for_manifest(ctx.job_record)
    ctx.stage = STAGE_QA
    summary_slice = build_summary_for_m1_checks(ctx.manifest, manifest_job)
    ctx.qa = run_m1_checks(ctx.manifest, manifest_job, summary_slice)

    if _has_p0_failures(ctx.qa):
        policy = p0_failure_policy if p0_failure_policy in (P0_POLICY_FAILED, P0_POLICY_BLOCKED) else P0_POLICY_FAILED
        ctx.status = STATUS_BLOCKED if policy == P0_POLICY_BLOCKED else STATUS_FAILED
        ctx.error_code = ERR_QA_P0
        ctx.message = "QA-M1 P0 failure"
        ctx.retryable = False
        return _result_from_context(ctx, ok=False)

    m2_result: dict[str, Any] | None = None
    if enable_m2:
        try:
            m2_result = execute_m2_checks(
                ctx.manifest,
                job_record=manifest_job,
                envelopes=ctx.envelopes,
                qa_m1_result=ctx.qa,
                billing_table=billing_table,
                strict_m2=strict_m2,
            )
        except Exception as exc:
            if strict_m2:
                ctx.status = STATUS_FAILED
                ctx.stage = STAGE_QA
                ctx.error_code = ERR_M2
                ctx.message = f"m2_checks_failed: {exc}"
                ctx.retryable = False
                return _result_from_context(ctx, ok=False)
            m2_result = m2_checks_error_result(
                ctx.manifest,
                exc,
                billing_table=billing_table,
            )
        if m2_result is not None:
            sample = m2_result.get("sample_validation")
            if isinstance(sample, Mapping) and sample.get("status") == "error":
                ctx.message = str(sample.get("reason") or "m2_checks_failed")

    ctx.stage = STAGE_REPORT
    report_out = build_wave7_report(
        manifest_job,
        ctx.manifest,
        ctx.qa,
        billing_table=billing_table,
        m2_result=m2_result,
    )
    if not report_out.get("ok") or report_out.get("report") is None:
        ctx.status = STATUS_FAILED
        ctx.error_code = ERR_REPORT
        ctx.message = str(report_out.get("message") or "report build failed")
        ctx.retryable = False
        return _result_from_context(ctx, ok=False)

    ctx.report = dict(report_out["report"])
    ctx.m2_result = m2_result
    return None


def _logical_run_summary_ref(
    *,
    paths_resolved: dict[str, str] | None,
    job_id: str,
    relative_file: str,
) -> str:
    """Repo-relative logical path for run_summary (never absolute)."""
    rel = relative_file.strip().lstrip("/")
    if paths_resolved and paths_resolved.get("delivery_root"):
        base = str(paths_resolved["delivery_root"]).strip().rstrip("/\\")
        return f"{base}/{rel}"
    return rel


def _attach_clean_run_summary(
    ctx: JobRunContext,
    result: dict[str, Any],
    *,
    paths_resolved: dict[str, str] | None,
    repo_root: Any,
) -> dict[str, Any]:
    """
    Outbox sidecar: derive and write run_summary.json without mutating job ok/status.
    """
    from pathlib import Path

    from core.wave8_clean_run_summary_producer import (
        build_clean_run_summary,
        write_clean_run_summary_to_file,
    )

    if ctx.job_record is None:
        return result

    job_id = str(ctx.job_record["job_id"])
    out: dict[str, Any] = dict(result)
    outbox: dict[str, Any] = {"ok": False, "message": ""}

    job_record = dict(ctx.job_record)
    job_record["status"] = str(out.get("status") or ctx.status)
    if out.get("completion_variant"):
        job_record["completion_variant"] = out["completion_variant"]
    elif ctx.completion_variant:
        job_record["completion_variant"] = ctx.completion_variant

    try:
        summary = build_clean_run_summary(
            job_record=job_record,
            report_dict=ctx.report,
            m2_result=ctx.m2_result,
            artifacts=out.get("artifacts"),
            run_result=out,
        )
    except Exception as exc:
        outbox["message"] = f"clean_run_summary_build_failed: {exc}"
        out["clean_run_summary_outbox"] = outbox
        return out

    try:
        root = Path(repo_root) if repo_root is not None else Path.cwd()
        if paths_resolved and paths_resolved.get("delivery_root"):
            out_dir = root / str(paths_resolved["delivery_root"])
        else:
            out_dir = root / "delivery"
        write_result = write_clean_run_summary_to_file(
            summary, out_dir=out_dir, job_id=job_id
        )
    except Exception as exc:
        write_result = {"ok": False, "path": None, "message": str(exc)}

    artifacts = dict(out.get("artifacts") or {})
    if write_result.get("ok"):
        rel_path = str(write_result.get("path") or f"{job_id}/run_summary.json")
        ref = _logical_run_summary_ref(
            paths_resolved=paths_resolved,
            job_id=job_id,
            relative_file=rel_path,
        )
        artifacts["run_summary_ref"] = ref
        out["run_summary_ref"] = ref
        outbox = {
            "ok": True,
            "message": str(write_result.get("message") or "clean_run_summary_written"),
            "path": ref,
        }
    else:
        outbox["message"] = str(
            write_result.get("message") or "clean_run_summary_write_failed"
        )

    out["artifacts"] = artifacts
    out["clean_run_summary_outbox"] = outbox
    return out


def _finalize_storage(
    ctx: JobRunContext,
    *,
    paths_resolved: dict[str, str] | None,
    repo_root: Any,
    start: Any,
    json_writer: Callable[[Any, str], None] | None,
    render_report_md: bool = False,
    strict_report_md: bool = False,
) -> dict[str, Any]:
    assert ctx.job_record is not None and ctx.manifest is not None and ctx.report is not None

    ctx.stage = STAGE_STORAGE
    store = store_wave7_artifacts(
        str(ctx.job_record["job_id"]),
        str(ctx.job_record.get("sku") or ""),
        envelopes=ctx.envelopes,
        manifest=ctx.manifest.to_contract_dict(),
        report=ctx.report,
        mode="create",
        paths_resolved=paths_resolved,
        repo_root=repo_root,
        start=start,
        json_writer=json_writer,
    )

    # Wave 8: optional Markdown report rendering
    if render_report_md and store.get("ok"):
        _render_and_write_report_md(
            ctx,
            store=store,
            paths_resolved=paths_resolved,
            repo_root=repo_root,
            strict=strict_report_md,
        )

    return store


def _render_and_write_report_md(
    ctx: JobRunContext,
    *,
    store: dict[str, Any],
    paths_resolved: dict[str, str] | None,
    repo_root: Any,
    strict: bool = False,
) -> None:
    """
    Render report.json to Markdown and write to delivery/job/report.md.
    Failure is isolated: logs warning, does not rollback report.json.
    """
    from pathlib import Path

    assert ctx.job_record is not None and ctx.report is not None
    job_id = str(ctx.job_record["job_id"])

    # Build display_context for renderer
    display_context: dict[str, Any] = {
        "job_id": job_id,
        "generated_at": ctx.job_record.get("completed_at") or ctx.job_record.get("started_at"),
    }
    if ctx.completion_variant:
        display_context["completion_variant"] = ctx.completion_variant
        display_context["run_status"] = ctx.status

    # Render Markdown
    try:
        render_out = render_data_clean_report(
            ctx.report,
            config={"audience": "external"},
            display_context=display_context,
        )
    except Exception as exc:
        ctx.message = f"report_md_render_failed: {exc}"
        if strict:
            store["report_md_render"] = {"ok": False, "message": str(exc)}
        return

    if not render_out.get("ok"):
        ctx.message = f"report_md_render_failed: {render_out.get('message')}"
        if strict:
            store["report_md_render"] = {"ok": False, "message": render_out.get("message")}
        return

    markdown = str(render_out.get("markdown", ""))
    if not markdown:
        ctx.message = "report_md_render_failed: empty markdown"
        if strict:
            store["report_md_render"] = {"ok": False, "message": "empty markdown"}
        return

    # Resolve delivery path and write report.md
    try:
        root = Path(repo_root) if repo_root is not None else Path.cwd()
        if paths_resolved and paths_resolved.get("delivery_root"):
            delivery_root = paths_resolved["delivery_root"]
            report_md_path = root / delivery_root / job_id / "report.md"
        else:
            # Fallback: use paths_logical from store
            paths_logical = store.get("paths_logical") or {}
            report_md_rel = paths_logical.get("report_md", f"{job_id}/report.md")
            report_md_path = root / report_md_rel

        report_md_path.parent.mkdir(parents=True, exist_ok=True)
        report_md_path.write_text(markdown, encoding="utf-8")
    except Exception as exc:
        ctx.message = f"report_md_write_failed: {exc}"
        if strict:
            store["report_md_render"] = {"ok": False, "message": f"write failed: {exc}"}
        return

    # Success sidecar info
    store["report_md_render"] = {"ok": True, "message": "report_md_rendered"}
    store["_report_md_written"] = True  # Internal marker for idempotency checks


def run_wave7_job(
    job_input_params_or_record: Mapping[str, Any],
    *,
    max_retries: int | None = None,
    p0_failure_policy: str = P0_POLICY_FAILED,
    paths_resolved: dict[str, str] | None = None,
    repo_root: Any = None,
    start: Any = None,
    billing_table: Mapping[str, Any] | str | None = None,
    json_writer: Callable[[Any, str], None] | None = None,
    hooks: Mapping[str, LifecycleHook] | None = None,
    resume_context: JobRunContext | None = None,
    enable_m2: bool = False,
    strict_m2: bool = False,
    render_report_md: bool = False,
    strict_report_md: bool = False,
) -> dict[str, Any]:
    """
    Run the Wave 7 single-job lifecycle.

    ``job_input_params_or_record`` may be:
    - ``{job_record, raw_files}`` — skip runner entry
    - ``{sku, client_ref, queue_payload?, intake_request?, ...}`` — runner entry

    ``resume_context``: optional checkpoint from a prior partial run (tests / retry).

    ``enable_m2``: if True, run Wave 8 sampling + envelope checks before report build.
    ``strict_m2``: if True, unexpected M2 errors fail the job (default False).
    ``render_report_md``: if True, render report.json to report.md after storage.
    ``strict_report_md``: if True, render failure affects ok/artifacts (default False).

    Returns structured dict with ``status``, ``stage``, ``artifacts``, ``qa``,
    ``retryable``, ``message``, ``error_code``, ``completion_variant``.
    """

    limit = DEFAULT_MAX_RETRIES if max_retries is None else max(0, int(max_retries))

    ctx, early = _resolve_entry(job_input_params_or_record, hooks=hooks)
    if early is not None:
        return _attach_clean_run_summary(
            ctx, early, paths_resolved=paths_resolved, repo_root=repo_root
        )

    if resume_context is not None:
        ctx.envelopes = resume_context.envelopes
        ctx.manifest = resume_context.manifest
        ctx.manifest_stored = resume_context.manifest_stored
        ctx.checkpoint = resume_context.checkpoint
        ctx.envelope_compute_count = resume_context.envelope_compute_count

    ctx.status = STATUS_RUNNING

    if ctx.checkpoint != CHECKPOINT_MANIFEST or ctx.manifest is None:
        fail = _run_pipeline_memory(ctx)
        if fail is not None:
            return _attach_clean_run_summary(
                ctx, fail, paths_resolved=paths_resolved, repo_root=repo_root
            )

        ckpt_fail = _persist_manifest_checkpoint(
            ctx,
            paths_resolved=paths_resolved,
            repo_root=repo_root,
            start=start,
            json_writer=json_writer,
        )
        if ckpt_fail is not None:
            return _attach_clean_run_summary(
                ctx, ckpt_fail, paths_resolved=paths_resolved, repo_root=repo_root
            )

    qa_fail = _run_qa_and_report(
        ctx,
        billing_table=billing_table,
        p0_failure_policy=p0_failure_policy,
        hooks=hooks,
        enable_m2=enable_m2,
        strict_m2=strict_m2,
    )
    if qa_fail is not None:
        return _attach_clean_run_summary(
            ctx, qa_fail, paths_resolved=paths_resolved, repo_root=repo_root
        )

    last_store: dict[str, Any] = {}
    for attempt in range(limit + 1):
        ctx.storage_attempts = attempt + 1
        last_store = _finalize_storage(
            ctx,
            paths_resolved=paths_resolved,
            repo_root=repo_root,
            start=start,
            json_writer=json_writer,
            render_report_md=render_report_md,
            strict_report_md=strict_report_md,
        )
        if last_store.get("ok"):
            break
        code = str(last_store.get("error_code") or ERR_STORAGE)
        if not _is_retryable_error(code) or attempt >= limit:
            ctx.status = STATUS_FAILED
            ctx.stage = STAGE_STORAGE
            ctx.error_code = code
            ctx.message = str(last_store.get("message") or "artifact finalize failed")
            ctx.retryable = _is_retryable_error(code) and attempt < limit
            return _attach_clean_run_summary(
                ctx,
                _result_from_context(
                    ctx,
                    ok=False,
                    artifacts=last_store.get("artifact_refs") or {},
                ),
                paths_resolved=paths_resolved,
                repo_root=repo_root,
            )

    assert ctx.manifest is not None
    ctx.status = STATUS_DONE
    ctx.stage = STAGE_STORAGE
    prior_message = str(ctx.message or "").strip()
    if prior_message and "m2_checks_failed" in prior_message:
        ctx.message = f"wave7_job_done; {prior_message}"
    else:
        ctx.message = "wave7_job_done"
    ctx.error_code = None
    ctx.retryable = False

    if _manifest_has_rejected_rows(ctx.manifest) and not _has_p0_failures(ctx.qa or {}):
        ctx.completion_variant = COMPLETION_COMPLETED_WITH_FAILURES

    return _attach_clean_run_summary(
        ctx,
        _result_from_context(
            ctx,
            ok=True,
            artifacts=last_store.get("artifact_refs") or {},
        ),
        paths_resolved=paths_resolved,
        repo_root=repo_root,
    )


__all__ = [
    "CHECKPOINT_MANIFEST",
    "CHECKPOINT_NONE",
    "COMPLETION_COMPLETED_WITH_FAILURES",
    "DEFAULT_MAX_RETRIES",
    "ERR_ENTRY",
    "ERR_M2",
    "ERR_QA_P0",
    "ERR_STORAGE",
    "NON_RETRYABLE_CODES",
    "P0_POLICY_BLOCKED",
    "P0_POLICY_FAILED",
    "STAGE_ENTRY",
    "STAGE_PIPELINE",
    "STAGE_QA",
    "STAGE_REPORT",
    "STAGE_STORAGE",
    "STATUS_BLOCKED",
    "STATUS_DONE",
    "STATUS_FAILED",
    "STATUS_PENDING",
    "STATUS_RUNNING",
    "WAVE7_LIFECYCLE_SCHEMA_VERSION",
    "JobRunContext",
    "run_wave7_job",
]
