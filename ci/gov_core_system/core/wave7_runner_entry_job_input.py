"""
Wave 7 runner entry — construct ``job_record`` and ``raw_files[]`` from real inputs.

Sources: cleaned_full batch manifest / directory scan, queue JSON payload, CLI args.
Optional Wave 6 intake gate: only ``decision=accept`` proceeds to job construction.

Does not write envelopes/manifests, persist jobs, or run cleaning pipelines.
"""

from __future__ import annotations

import argparse
import json
import re
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.envelope_writer import (
    FORBIDDEN_DELIVERY_PATH_KEYS,
    SKU_BASIC,
    SKU_ENRICH,
    SUPPORTED_SKUS,
    EnvelopeWriterError,
    build_envelope,
)
from core.schemas.envelope_v2 import ENRICHMENT_V0_1_SCHEMA_VERSION, _HEX64_RE, _LEAKY_PATH_RE
from core.wave6_intake_gate import run_intake_gate

WAVE7_RUNNER_ENTRY_SCHEMA_VERSION = "wave7_runner_entry_v1"

ERR_EMPTY_BATCH = "empty_batch"
ERR_UNKNOWN_SKU = "unknown_sku"
ERR_SKU_INTAKE_MISMATCH = "sku_intake_mismatch"
ERR_INTAKE_DEFER = "intake_deferred"
ERR_INTAKE_REJECT = "intake_rejected"
ERR_INVALID_JSON = "invalid_cleaned_json"
ERR_MISSING_SHA256 = "missing_content_sha256"
ERR_MISSING_REQUIRED = "missing_required_field"
ERR_MANIFEST_EMPTY = "manifest_empty"
ERR_NO_INPUT_SOURCE = "no_input_source"

_LOGICAL_MARKERS = ("cleaned_full/", "raw_inbound/", "staging/wave7/")

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_job_id(*, sku: str, client_ref: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", client_ref).strip("-")[:24] or "job"
    sku_tag = "basic" if sku == SKU_BASIC else "enrich"
    return f"w7-{sku_tag}-{slug}-{uuid.uuid4().hex[:8]}"


def _fail(
    *,
    code: str,
    message: str,
    skipped: list[dict[str, Any]] | None = None,
    input_count: int = 0,
) -> dict[str, Any]:
    return {
        "ok": False,
        "message": message,
        "error_code": code,
        "job_record": None,
        "input_count": input_count,
        "skipped": skipped or [],
        "schema_version": WAVE7_RUNNER_ENTRY_SCHEMA_VERSION,
    }


def _ok(
    *,
    job_record: dict[str, Any],
    raw_files: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    message: str = "job_input_ready",
) -> dict[str, Any]:
    return {
        "ok": True,
        "message": message,
        "error_code": None,
        "job_record": job_record,
        "raw_files": raw_files,
        "input_count": len(raw_files),
        "skipped": skipped,
        "schema_version": WAVE7_RUNNER_ENTRY_SCHEMA_VERSION,
    }


def normalize_sku(sku: str) -> str | None:
    normalized = str(sku or "").strip().upper()
    if normalized in SUPPORTED_SKUS:
        return normalized
    return None


def to_logical_path(
    *values: str | None,
    default_prefix: str = "cleaned_full",
    fallback_name: str | None = None,
) -> str | None:
    """Map legacy ``source_path`` / ``stored_path`` / hints to a logical delivery path."""

    candidates = [
        str(raw).strip().replace("\\", "/")
        for raw in values
        if raw and str(raw).strip()
    ]
    if not candidates and fallback_name:
        return f"{default_prefix}/{fallback_name}"
    if not candidates:
        return None

    for marker in _LOGICAL_MARKERS:
        for candidate in candidates:
            lowered = candidate.lower()
            idx = lowered.find(marker)
            if idx >= 0:
                return candidate[idx:].lstrip("/")

    for candidate in candidates:
        if _LEAKY_PATH_RE.search(candidate):
            name = candidate.rsplit("/", 1)[-1]
            if name:
                return f"{default_prefix}/{name}"
        if candidate.startswith("/"):
            name = candidate.rsplit("/", 1)[-1]
            if name:
                return f"{default_prefix}/{name}"
        if not _LEAKY_PATH_RE.search(candidate):
            return candidate

    if fallback_name:
        return f"{default_prefix}/{fallback_name}"
    return None


def _strip_legacy_path_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in record.items() if k not in FORBIDDEN_DELIVERY_PATH_KEYS}
    return out


def _normalize_sha256(value: Any) -> str | None:
    if value is None:
        return None
    vv = str(value).strip().lower()
    if _HEX64_RE.fullmatch(vv):
        return vv
    return None


def _minimal_content_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    existing = record.get("content_summary")
    if isinstance(existing, Mapping) and existing:
        return {
            "line_count": int(existing.get("line_count") or 0),
            "char_count": int(existing.get("char_count") or 0),
            "imports": list(existing.get("imports") or []),
            "preview_lines": list(existing.get("preview_lines") or [])[:10],
        }
    return {"line_count": 0, "char_count": 0, "imports": [], "preview_lines": []}


def _default_enrichment_present() -> dict[str, Any]:
    return {
        "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
        "present": True,
        "detected_language": "unknown",
        "domain_tags": [],
        "content_kind": "unknown",
        "quality_score": 50,
        "review_priority": "medium",
        "enrichment_provenance": "rules",
        "signals": {
            "has_parse_warnings": False,
            "used_llm": False,
            "line_count": 0,
            "import_count": 0,
        },
    }


def map_cleaned_record_to_raw_file(
    record: Mapping[str, Any],
    *,
    sku: str,
    source_hint: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Convert an on-disk cleaned JSON row to an envelope-writer ``raw_file`` dict.

    Returns ``(raw_file, skip_info)``; exactly one is non-None.
    """

    base = _strip_legacy_path_fields(record)
    file_id = str(base.get("file_id") or "").strip()
    if not file_id and source_hint:
        stem = Path(source_hint).stem
        file_id = stem or ""
    if not file_id:
        return None, {
            "source": source_hint,
            "error_code": ERR_MISSING_REQUIRED,
            "reason": "missing file_id",
        }

    sha = _normalize_sha256(base.get("content_sha256"))
    if not sha:
        return None, {
            "source": source_hint or file_id,
            "error_code": ERR_MISSING_SHA256,
            "reason": "missing or invalid content_sha256",
        }

    logical = to_logical_path(
        str(base.get("stored_logical_path") or ""),
        str(record.get("stored_path") or ""),
        str(record.get("source_path") or ""),
        fallback_name=Path(source_hint).name if source_hint else f"{file_id}.json",
    )
    if not logical:
        return None, {
            "source": source_hint or file_id,
            "error_code": ERR_MISSING_REQUIRED,
            "reason": "could not derive stored_logical_path",
        }
    if _LEAKY_PATH_RE.search(logical):
        return None, {
            "source": source_hint or file_id,
            "error_code": ERR_MISSING_REQUIRED,
            "reason": "stored_logical_path still looks absolute",
        }

    name = str(base.get("name") or file_id).strip() or file_id
    extension = str(base.get("extension") or Path(name).suffix or ".json").strip()
    if extension and not extension.startswith("."):
        extension = f".{extension}"

    raw: dict[str, Any] = {
        "file_id": file_id,
        "content_sha256": sha,
        "clean_status": str(base.get("clean_status") or "ok").strip() or "ok",
        "name": name,
        "extension": extension,
        "original_type": str(base.get("original_type") or "unknown").strip() or "unknown",
        "size_bytes": int(base.get("size_bytes") or 0),
        "encoding": base.get("encoding"),
        "stored_logical_path": logical,
        "content_summary": _minimal_content_summary(base),
        "groq_used": bool(base.get("groq_used")),
        "groq_reason": base.get("groq_reason"),
        "parse_strategy": base.get("parse_strategy"),
        "warnings": list(base.get("warnings") or []),
    }

    enrichment = base.get("enrichment")
    if sku == SKU_ENRICH:
        if isinstance(enrichment, Mapping) and enrichment:
            raw["enrichment"] = dict(enrichment)
        elif raw["clean_status"] == "ok":
            raw["enrichment"] = _default_enrichment_present()
    elif enrichment is not None:
        pass  # dropped for BASIC

    try:
        build_envelope({"sku": sku}, raw)
    except (EnvelopeWriterError, ValueError) as exc:
        return None, {
            "source": source_hint or file_id,
            "error_code": ERR_MISSING_REQUIRED,
            "reason": str(exc),
        }

    return raw, None


def _load_json_file(path: Path) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, str(exc)
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, str(exc)


def _resolve_manifest_entries(
    manifest_data: Any,
    *,
    base_dir: Path,
) -> list[tuple[Path | None, Mapping[str, Any] | None, str]]:
    """
    Return list of (disk_path | None, inline_record | None, hint).
    """

    entries: list[tuple[Path | None, Mapping[str, Any] | None, str]] = []

    if isinstance(manifest_data, list):
        items = manifest_data
    elif isinstance(manifest_data, Mapping):
        files = manifest_data.get("files") or manifest_data.get("paths") or manifest_data.get("entries")
        if isinstance(files, list):
            items = files
        else:
            return entries
    else:
        return entries

    for item in items:
        if isinstance(item, str):
            hint = item
            p = Path(item)
            if not p.is_absolute():
                p = base_dir / item
            entries.append((p, None, hint))
        elif isinstance(item, Mapping):
            hint = str(item.get("file_id") or item.get("stored_logical_path") or "inline")
            path_val = item.get("path") or item.get("json_path")
            if path_val:
                p = Path(str(path_val))
                if not p.is_absolute():
                    p = base_dir / p
                entries.append((p, item, str(path_val)))
            else:
                entries.append((None, item, hint))
    return entries


def _ingest_disk_path(
    path: Path,
    *,
    sku: str,
    inline: Mapping[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    hint = str(path)
    if inline is not None and not path.is_file():
        return map_cleaned_record_to_raw_file(inline, sku=sku, source_hint=hint)

    if not path.is_file():
        return None, {
            "source": hint,
            "error_code": ERR_INVALID_JSON,
            "reason": "file not found",
        }

    data, err = _load_json_file(path)
    if err or not isinstance(data, Mapping):
        return None, {
            "source": hint,
            "error_code": ERR_INVALID_JSON,
            "reason": err or "expected JSON object",
        }

    merged: dict[str, Any] = dict(data)
    if inline:
        merged.update({k: v for k, v in inline.items() if k not in FORBIDDEN_DELIVERY_PATH_KEYS})
    return map_cleaned_record_to_raw_file(merged, sku=sku, source_hint=hint)


def _scan_cleaned_directory(cleaned_dir: Path) -> list[Path]:
    if not cleaned_dir.is_dir():
        return []
    return sorted(cleaned_dir.glob("*.json"))


def _evaluate_intake(
    intake_request: Mapping[str, Any] | None,
    *,
    sku: str,
) -> dict[str, Any] | None:
    if intake_request is None:
        return None

    gate = run_intake_gate(dict(intake_request))
    decision = gate.decision

    if decision == "defer":
        return _fail(
            code=ERR_INTAKE_DEFER,
            message=f"intake deferred: {gate.message}",
        )
    if decision == "reject":
        return _fail(
            code=ERR_INTAKE_REJECT,
            message=f"intake rejected: {gate.message}",
        )
    if decision != "accept":
        return _fail(
            code=ERR_INTAKE_REJECT,
            message=f"intake blocked: decision={decision}",
        )

    intake_sku = (
        getattr(gate, "suggested_product_sku", None)
        or str(intake_request.get("product_sku") or "").strip()
        or None
    )
    intake_sku_norm = normalize_sku(intake_sku or "")
    if intake_sku_norm and intake_sku_norm != sku:
        return _fail(
            code=ERR_SKU_INTAKE_MISMATCH,
            message=(
                f"runner sku {sku!r} does not match intake product_sku {intake_sku_norm!r}"
            ),
        )
    return None


def build_runner_job_input(
    *,
    sku: str,
    client_ref: str,
    cleaned_dir: str | Path | None = None,
    manifest_path: str | Path | None = None,
    queue_payload: Mapping[str, Any] | None = None,
    job_id: str | None = None,
    intake_request: Mapping[str, Any] | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Build ``job_record`` and ``raw_files`` from batch manifest, directory scan, and/or queue payload.

    Returns ``{ok, message, error_code?, job_record, raw_files?, input_count, skipped[]}``.
    """

    client_ref_s = str(client_ref or "").strip()
    if not client_ref_s:
        return _fail(code=ERR_MISSING_REQUIRED, message="client_ref is required")

    sku_norm = normalize_sku(sku)
    if sku_norm is None:
        return _fail(
            code=ERR_UNKNOWN_SKU,
            message=f"unsupported sku {sku!r}; expected CLEAN-BASIC or CLEAN-ENRICH",
        )

    intake_block = _evaluate_intake(intake_request, sku=sku_norm)
    if intake_block is not None:
        return intake_block

    resolved_base = (base_dir or Path(".")).resolve()
    work: list[tuple[Path | None, Mapping[str, Any] | None, str]] = []
    queue_skipped: list[dict[str, Any]] = []

    if queue_payload is not None:
        q_files = (
            queue_payload.get("files")
            or queue_payload.get("entries")
            or queue_payload.get("raw_files")
        )
        if isinstance(q_files, list):
            for idx, item in enumerate(q_files):
                hint = f"queue[{idx}]"
                if isinstance(item, Mapping):
                    work.append((None, item, hint))
                elif isinstance(item, str):
                    p = Path(item)
                    if not p.is_absolute():
                        p = resolved_base / item
                    work.append((p, None, hint))
                else:
                    queue_skipped.append(
                        {
                            "source": hint,
                            "error_code": ERR_INVALID_JSON,
                            "reason": "queue entry must be object or path string",
                        }
                    )

    if manifest_path is not None:
        mpath = Path(manifest_path)
        if not mpath.is_file():
            return _fail(
                code=ERR_INVALID_JSON,
                message=f"manifest not found: {mpath.name}",
            )
        manifest_data, err = _load_json_file(mpath)
        if err:
            return _fail(code=ERR_INVALID_JSON, message=f"manifest parse error: {err}")
        if manifest_data is None:
            return _fail(code=ERR_MANIFEST_EMPTY, message="manifest is empty")
        entries = _resolve_manifest_entries(manifest_data, base_dir=resolved_base)
        if not entries:
            return _fail(code=ERR_MANIFEST_EMPTY, message="manifest contains no file entries")
        work.extend(entries)

    if cleaned_dir is not None:
        cdir = Path(cleaned_dir)
        scanned = _scan_cleaned_directory(cdir)
        if not scanned:
            if not work:
                return _fail(
                    code=ERR_EMPTY_BATCH,
                    message="cleaned_dir has no *.json files",
                )
        for p in scanned:
            work.append((p, None, str(p)))

    if not work:
        return _fail(
            code=ERR_NO_INPUT_SOURCE,
            message="provide cleaned_dir, manifest_path, or queue_payload with files",
        )

    raw_files: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = list(queue_skipped)

    for path, inline, hint in work:
        if path is not None:
            raw, skip = _ingest_disk_path(path, sku=sku_norm, inline=inline)
        elif inline is not None:
            raw, skip = map_cleaned_record_to_raw_file(inline, sku=sku_norm, source_hint=hint)
        else:
            skip = {
                "source": hint,
                "error_code": ERR_MISSING_REQUIRED,
                "reason": "empty work item",
            }
            raw = None
        if skip:
            skipped.append(skip)
            continue
        if raw:
            raw_files.append(raw)

    if not raw_files:
        return _fail(
            code=ERR_EMPTY_BATCH,
            message="no valid raw files after intake and validation",
            skipped=skipped,
            input_count=0,
        )

    job_record = {
        "job_id": (str(job_id).strip() if job_id else _default_job_id(sku=sku_norm, client_ref=client_ref_s)),
        "sku": sku_norm,
        "client_ref": client_ref_s,
        "created_at": _utc_now_iso(),
    }

    result = _ok(job_record=job_record, raw_files=raw_files, skipped=skipped)
    return result


def build_runner_job_from_queue_file(
    queue_path: str | Path,
    *,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Load a minimal queue JSON fixture and build job input."""

    path = Path(queue_path)
    data, err = _load_json_file(path)
    if err or not isinstance(data, Mapping):
        return _fail(
            code=ERR_INVALID_JSON,
            message=err or "queue payload must be a JSON object",
        )

    sku = str(data.get("sku") or data.get("product_sku") or "").strip()
    client_ref = str(data.get("client_ref") or "").strip()
    job_id = str(data.get("job_id") or "").strip() or None
    intake_request = data.get("intake_request") if isinstance(data.get("intake_request"), Mapping) else None

    return build_runner_job_input(
        sku=sku,
        client_ref=client_ref,
        queue_payload=data,
        job_id=job_id,
        intake_request=intake_request,
        base_dir=base_dir or path.parent,
    )


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wave 7 runner entry: construct job_record and raw_files from batch/CLI",
    )
    parser.add_argument("--sku", required=True, help="CLEAN-BASIC or CLEAN-ENRICH")
    parser.add_argument("--client-ref", required=True, dest="client_ref")
    parser.add_argument("--cleaned-dir", dest="cleaned_dir", default=None)
    parser.add_argument("--manifest", dest="manifest_path", default=None)
    parser.add_argument("--queue-json", dest="queue_json", default=None)
    parser.add_argument("--job-id", dest="job_id", default=None)
    parser.add_argument("--intake-json", dest="intake_json", default=None)
    parser.add_argument("--base-dir", dest="base_dir", default=".")
    return parser


def build_runner_job_from_cli(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = build_cli_parser().parse_args(list(argv) if argv is not None else None)

    intake_request: dict[str, Any] | None = None
    if args.intake_json:
        ipath = Path(args.intake_json)
        data, err = _load_json_file(ipath)
        if err or not isinstance(data, Mapping):
            return _fail(code=ERR_INVALID_JSON, message=err or "intake JSON must be an object")
        intake_request = dict(data)

    queue_payload: dict[str, Any] | None = None
    if args.queue_json:
        qpath = Path(args.queue_json)
        data, err = _load_json_file(qpath)
        if err or not isinstance(data, Mapping):
            return _fail(code=ERR_INVALID_JSON, message=err or "queue JSON must be an object")
        queue_payload = dict(data)

    return build_runner_job_input(
        sku=args.sku,
        client_ref=args.client_ref,
        cleaned_dir=args.cleaned_dir,
        manifest_path=args.manifest_path,
        queue_payload=queue_payload,
        job_id=args.job_id,
        intake_request=intake_request,
        base_dir=Path(args.base_dir),
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = build_runner_job_from_cli(argv)
    print(json.dumps({k: v for k, v in result.items() if k != "raw_files"}, ensure_ascii=False))
    if result.get("ok") and result.get("raw_files"):
        print(json.dumps({"raw_files_count": len(result["raw_files"])}, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
