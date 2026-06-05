"""
Export P+ eval_gate results to JSONL for analysis and CI.

Each output line is a compact eval export record (schema ``eval_export/v1``);
full ``ibridge_record`` / metrics blobs are not duplicated.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Iterator, Literal

from observability.eval_gate import evaluate_task_record

SCHEMA_VERSION: Final[str] = "eval_export/v1"
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


def build_export_line(
    record: dict[str, Any],
    *,
    gate: dict[str, Any] | None = None,
    line_index: int | None = None,
    exported_at: str | None = None,
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

    with output_path.open("w", encoding="utf-8", newline="\n") as out_f:
        for record, line_index in iter_records(input_path):
            total_read += 1
            export_line = build_export_line(record, line_index=line_index)
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_cli().parse_args(argv)
    result = export_eval_jsonl(
        args.input_path,
        args.output,
        gate_filter=args.gate_filter,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
