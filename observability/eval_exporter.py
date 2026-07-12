"""
Export P+ eval_gate results to JSONL for analysis and CI.

Each output line is a compact eval export record (schema ``eval_export/v1``);
full ``ibridge_record`` / metrics blobs are not duplicated.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Iterator, Literal

from observability.eval_gate import evaluate_task_record

SCHEMA_VERSION: Final[str] = "eval_export/v1"
KB_INDEX_EXPORT_ENV: Final[str] = "GOV_EVAL_EXPORT_KB_INDEX_STATUS"
_VALID_KB_INDEX_STATUS: Final[frozenset[str]] = frozenset({"ready", "stale", "missing"})
GateResult = Literal["pass", "needs_review"]
GateFilter = Literal["all", "pass", "needs_review"]


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _record_timestamp(record: dict[str, Any]) -> str | None:
    for key in ("end_time", "start_time", "timestamp"):
        raw = record.get(key)
        if raw is not None and str(raw).strip():
            return str(raw)
    return None


def _context_tokens_total(record: dict[str, Any]) -> int:
    usage = record.get("context_token_usage")
    if not isinstance(usage, dict):
        return 0
    raw = usage.get("total_tokens", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _trace_completeness_score(record: dict[str, Any]) -> float | None:
    tc = record.get("trace_completeness")
    if not isinstance(tc, dict):
        return None
    raw = tc.get("score")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def summarize_metrics(record: dict[str, Any]) -> dict[str, Any]:
    """Extract gate-relevant metrics only (no full record copy)."""
    summary: dict[str, Any] = {
        "success": record.get("success"),
        "retry_count": record.get("retry_count", 0),
        "handoff_count": record.get("handoff_count", 0),
        "error_type": record.get("error_type"),
        "context_tokens_total": _context_tokens_total(record),
        "trace_completeness_score": _trace_completeness_score(record),
    }
    if record.get("agent_name") is not None:
        summary["agent_name"] = record.get("agent_name")
    if record.get("step_count") is not None:
        summary["step_count"] = record.get("step_count")
    return summary


def gate_result_label(gate: dict[str, Any]) -> GateResult:
    return "pass" if gate.get("pass") else "needs_review"


def kb_index_export_enabled() -> bool:
    """True when ``GOV_EVAL_EXPORT_KB_INDEX_STATUS`` is explicitly on (default off)."""
    return os.environ.get(KB_INDEX_EXPORT_ENV, "0").strip().lower() in {"1", "true", "yes"}


def load_case_index_map(path: Path | None) -> dict[str, Any]:
    """
    Load ``case_id → kb_index_status`` (or nested dict with ``kb_index_status`` / ``kb_index_job_id``).

    Returns empty dict when ``path`` is None or missing.
    """
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: case-index-map root must be object")
    return data


def _record_case_id(record: dict[str, Any]) -> str | None:
    for container in (record, record.get("metadata") if isinstance(record.get("metadata"), dict) else {}):
        if not isinstance(container, dict):
            continue
        raw = container.get("case_id")
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    return None


def _normalize_kb_index_status(raw: Any) -> str | None:
    if raw is None:
        return None
    status = str(raw).strip().lower()
    if not status or status == "null":
        return None
    if status in _VALID_KB_INDEX_STATUS:
        return status
    return None


def _case_map_entry(entry: Any) -> tuple[str | None, str | None]:
    if isinstance(entry, dict):
        status = _normalize_kb_index_status(entry.get("kb_index_status"))
        job_id = entry.get("kb_index_job_id")
        job_str = str(job_id).strip() if job_id is not None and str(job_id).strip() else None
        return status, job_str
    return _normalize_kb_index_status(entry), None


def resolve_kb_index_context(
    record: dict[str, Any],
    *,
    case_index_map: dict[str, Any] | None = None,
) -> dict[str, str | None]:
    """
    Resolve optional kb index fields for export sidecar.

    Priority (frozen):
    1. ``metadata.kb_index_status`` / ``metadata.kb_index_job_id``
    2. ``selector_hints.kb_index_status`` / ``selector_hints.kb_index_job_id``
    3. ``--case-index-map`` entry for ``case_id`` (status and optional job_id)
    """
    status: str | None = None
    job_id: str | None = None

    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        status = _normalize_kb_index_status(metadata.get("kb_index_status"))
        raw_job = metadata.get("kb_index_job_id")
        if raw_job is not None and str(raw_job).strip():
            job_id = str(raw_job).strip()

    hints = record.get("selector_hints")
    if isinstance(hints, dict):
        if status is None:
            status = _normalize_kb_index_status(hints.get("kb_index_status"))
        if job_id is None:
            raw_job = hints.get("kb_index_job_id")
            if raw_job is not None and str(raw_job).strip():
                job_id = str(raw_job).strip()

    if case_index_map:
        case_id = _record_case_id(record)
        if case_id and case_id in case_index_map:
            mapped_status, mapped_job = _case_map_entry(case_index_map[case_id])
            if status is None:
                status = mapped_status
            if job_id is None:
                job_id = mapped_job

    return {"kb_index_status": status, "kb_index_job_id": job_id}


def attach_kb_index_to_trace_metadata(
    export_line: dict[str, Any],
    kb_index_status: str | None,
) -> dict[str, Any]:
    """
    Mirror ``kb_index_status`` onto export line sidecar fields (observability only).

    Does not modify gov-trace-v2 middleware or default trace JSONL writes.
    """
    if kb_index_status is None or not str(kb_index_status).strip():
        return export_line
    line = dict(export_line)
    status = str(kb_index_status).strip()
    source_ref = dict(line.get("source_ref") or {})
    source_ref["kb_index_status"] = status
    line["source_ref"] = source_ref
    line["trace_metadata_sidecar"] = {"kb_index_status": status}
    return line


def build_export_line(
    record: dict[str, Any],
    *,
    gate: dict[str, Any] | None = None,
    line_index: int | None = None,
    exported_at: str | None = None,
    include_kb_index: bool = False,
    case_index_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build one JSONL export object (eval_export/v1).

    ``gate`` defaults to ``evaluate_task_record(record)`` when omitted.
    """
    evaluated = gate if gate is not None else evaluate_task_record(record)
    result = gate_result_label(evaluated)
    task_id = record.get("task_id")
    trace_id = record.get("trace_id")

    line: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "trace_id": trace_id,
        "task_id": task_id,
        "timestamp": _record_timestamp(record),
        "exported_at": exported_at or _iso_now(),
        "gate_result": result,
        "tags": list(evaluated.get("tags") or []),
        "reasons": list(evaluated.get("reasons") or []),
        "metrics": summarize_metrics(record),
    }

    source_ref: dict[str, Any] = {}
    if task_id is not None:
        source_ref["task_id"] = task_id
    if trace_id is not None:
        source_ref["trace_id"] = trace_id
    if line_index is not None:
        source_ref["line_index"] = line_index
    if source_ref:
        line["source_ref"] = source_ref

    if include_kb_index:
        kb_ctx = resolve_kb_index_context(record, case_index_map=case_index_map)
        line["kb_index_status"] = kb_ctx["kb_index_status"]
        if kb_ctx["kb_index_job_id"]:
            line["kb_index_job_id"] = kb_ctx["kb_index_job_id"]
        if kb_ctx["kb_index_status"]:
            line = attach_kb_index_to_trace_metadata(line, kb_ctx["kb_index_status"])

    return line


def _unwrap_record(raw: dict[str, Any]) -> dict[str, Any]:
    for key in ("ibridge_record", "record", "metrics_record"):
        nested = raw.get(key)
        if isinstance(nested, dict):
            return nested
    return raw


def _parse_json_line(raw: str, *, source: str, line_no: int) -> dict[str, Any] | None:
    text = raw.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source}:{line_no}: invalid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError(f"{source}:{line_no}: expected JSON object, got {type(obj).__name__}")
    return _unwrap_record(obj)


def _records_from_json_file(path: Path) -> Iterator[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return
    data = json.loads(text)
    if isinstance(data, list):
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"{path}: array[{i}] must be object")
            yield _unwrap_record(item)
    elif isinstance(data, dict):
        yield _unwrap_record(data)
    else:
        raise ValueError(f"{path}: root must be object or array of objects")


def iter_records(path: Path) -> Iterator[tuple[dict[str, Any], int | None]]:
    """
    Yield ``(record, line_index)`` from a file or directory of JSON/JSONL.

    ``line_index`` is set for JSONL sources; ``None`` for single JSON objects.
    """
    if not path.exists():
        raise FileNotFoundError(str(path))

    if path.is_dir():
        files = sorted(
            p
            for p in path.rglob("*")
            if p.suffix.lower() in {".jsonl", ".json"} and p.is_file()
        )
        for file_path in files:
            yield from iter_records(file_path)
        return

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            rec = _parse_json_line(raw, source=str(path), line_no=line_no)
            if rec is not None:
                yield rec, line_no
    elif suffix == ".json":
        for rec in _records_from_json_file(path):
            yield rec, None
    else:
        raise ValueError(f"unsupported input extension: {path.suffix} (use .json or .jsonl)")


def _matches_filter(gate_result: GateResult, gate_filter: GateFilter) -> bool:
    if gate_filter == "all":
        return True
    return gate_result == gate_filter


def export_eval_jsonl(
    input_path: Path,
    output_path: Path,
    *,
    gate_filter: GateFilter = "all",
    include_kb_index: bool | None = None,
    case_index_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run eval_gate on all records under ``input_path`` and write JSONL.

    Returns:
        ok: True when export completed (including zero matching rows).
        message: human-readable summary.
        written: number of lines written.
        skipped_filter: records evaluated but omitted by filter.
        total_read: records read from input.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped_filter = 0
    total_read = 0
    kb_enabled = kb_index_export_enabled() if include_kb_index is None else include_kb_index

    with output_path.open("w", encoding="utf-8", newline="\n") as out_f:
        for record, line_index in iter_records(input_path):
            total_read += 1
            export_line = build_export_line(
                record,
                line_index=line_index,
                include_kb_index=kb_enabled,
                case_index_map=case_index_map,
            )
            if not _matches_filter(export_line["gate_result"], gate_filter):
                skipped_filter += 1
                continue
            out_f.write(json.dumps(export_line, ensure_ascii=False) + "\n")
            written += 1

    return {
        "ok": True,
        "message": (
            f"exported {written} line(s) from {total_read} record(s) "
            f"(filter={gate_filter}) to {output_path.name}"
        ),
        "written": written,
        "skipped_filter": skipped_filter,
        "total_read": total_read,
        "output_path": str(output_path),
        "gate_filter": gate_filter,
        "kb_index_export_enabled": kb_enabled,
    }


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export eval_gate results from ibridge/metrics JSON(L) to JSONL.",
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Input .json / .jsonl file or directory of record files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("eval_results.jsonl"),
        help="Output JSONL path (default: eval_results.jsonl)",
    )
    parser.add_argument(
        "--filter",
        choices=("all", "pass", "needs_review"),
        default="all",
        dest="gate_filter",
        help="Only write rows matching gate_result (default: all)",
    )
    parser.add_argument(
        "--case-index-map",
        type=Path,
        default=None,
        help="Optional JSON map case_id → kb_index_status (Wave B P3 sidecar)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_cli().parse_args(argv)
    case_map = load_case_index_map(args.case_index_map) if args.case_index_map else None
    result = export_eval_jsonl(
        args.input_path,
        args.output,
        gate_filter=args.gate_filter,
        case_index_map=case_map,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
