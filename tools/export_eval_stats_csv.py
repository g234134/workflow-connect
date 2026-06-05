"""
W5-D-ARTEFACT-CSV-EXPORTER-01 — merge eval / dryrun / ENF JSONL artefacts into one CSV.

Usage (repo root, stdlib only):

  python -m tools.export_eval_stats_csv \\
    --input artifacts/eval/eval_export_v1_shadow_nightly.20260531.jsonl \\
    --input observability/dryrun/20260530T222742Z_per_record.jsonl \\
    --output output/eval_stats_20260531.csv

Multiple ``--input`` paths are concatenated in order; each JSONL line becomes one CSV row.
Source kind is inferred from filename (eval_export / dryrun / enf) or row shape.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Iterable, Iterator, Literal

from tools.dryrun.core import map_actual_verdict

SourceKind = Literal["eval_export", "dryrun", "enf", "unknown"]

UNIFIED_COLUMNS: Final[tuple[str, ...]] = (
    "date",
    "job_name",
    "task_id",
    "trace_id",
    "tags",
    "score",
    "ideal_verdict",
    "actual_verdict",
    "gate_result",
    "dryrun_rule",
    "enf_rule_hits",
    "source_kind",
    "source_file",
)

_DATE_IN_FILENAME = re.compile(r"(?<!\d)(20\d{6})(?!\d)")
_ISO_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _empty_row() -> dict[str, str]:
    return {col: "" for col in UNIFIED_COLUMNS}


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if isinstance(row, dict):
                yield row


def _serialize_tags(tags: Any) -> str:
    if not tags:
        return ""
    if isinstance(tags, str):
        return tags.strip()
    if isinstance(tags, (list, tuple, set)):
        parts = [str(t).strip() for t in tags if str(t).strip()]
        return ";".join(parts)
    return str(tags)


def _serialize_enf_hits(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        parts = [str(v).strip() for v in value if str(v).strip()]
        return ";".join(parts)
    if isinstance(value, dict):
        hits = value.get("hits") or value.get("rules") or value.get("enf_rules")
        if hits is not None:
            return _serialize_enf_hits(hits)
    return str(value)


def _parse_iso_date(value: Any) -> str:
    if not value or not isinstance(value, str):
        return ""
    text = value.strip()
    match = _ISO_DATE_PREFIX.match(text)
    if match:
        return match.group(1)
    if len(text) >= 8 and text[:8].isdigit():
        try:
            return datetime.strptime(text[:8], "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            return ""
    return ""


def _date_from_filename(path: Path) -> str:
    match = _DATE_IN_FILENAME.search(path.stem)
    if not match:
        return ""
    raw = match.group(1)
    try:
        return datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _extract_score(record: dict[str, Any]) -> str:
    metrics = record.get("metrics") or {}
    score = metrics.get("trace_completeness_score")
    if score is None:
        tc = record.get("trace_completeness")
        if isinstance(tc, dict):
            score = tc.get("score")
    if score is None:
        return ""
    try:
        return f"{float(score):.6g}"
    except (TypeError, ValueError):
        return str(score)


def _job_name_from_path(path: Path, *, kind: SourceKind) -> str:
    stem = path.stem
    if kind == "dryrun" and stem.endswith("_per_record"):
        return stem[: -len("_per_record")] or "dryrun"
    if kind == "eval_export":
        for suffix in (".latest",):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
        parts = stem.split(".")
        if len(parts) > 1 and parts[-1].isdigit() and len(parts[-1]) == 8:
            stem = ".".join(parts[:-1])
        return stem or "eval_export"
    if kind == "enf":
        return stem or "enf"
    return stem or path.name


def _job_name_from_row(record: dict[str, Any], fallback: str) -> str:
    metrics = record.get("metrics") or {}
    agent = metrics.get("agent_name") or record.get("job_name") or record.get("agent_name")
    if isinstance(agent, str) and agent.strip():
        return agent.strip()
    return fallback


def detect_source_kind(path: Path, row: dict[str, Any]) -> SourceKind:
    name_lower = path.name.lower()
    if "enf" in name_lower or row.get("enf_rule_hits") or row.get("preview_rule"):
        return "enf"
    if row.get("schema_version") == "eval_export/v1":
        return "eval_export"
    if "ideal_verdict" in row and "actual_verdict" in row:
        return "dryrun"
    if "per_record" in name_lower or "dryrun" in name_lower:
        return "dryrun"
    if "eval_export" in name_lower or "eval_results" in name_lower:
        return "eval_export"
    if "gate_result" in row and "metrics" in row:
        return "eval_export"
    return "unknown"


def row_from_eval_export(
    record: dict[str, Any],
    *,
    path: Path,
    kind: SourceKind,
) -> dict[str, str]:
    out = _empty_row()
    job_fallback = _job_name_from_path(path, kind=kind)
    out["date"] = (
        _parse_iso_date(record.get("timestamp"))
        or _parse_iso_date(record.get("exported_at"))
        or _date_from_filename(path)
    )
    out["job_name"] = _job_name_from_row(record, job_fallback)
    out["task_id"] = str(record.get("task_id") or "")
    out["trace_id"] = str(record.get("trace_id") or "")
    out["tags"] = _serialize_tags(record.get("tags"))
    out["score"] = _extract_score(record)
    out["actual_verdict"] = map_actual_verdict(record)
    out["gate_result"] = str(record.get("gate_result") or "")
    out["source_kind"] = kind
    out["source_file"] = path.as_posix()
    return out


def row_from_dryrun(
    record: dict[str, Any],
    *,
    path: Path,
    kind: SourceKind,
) -> dict[str, str]:
    out = _empty_row()
    job_fallback = _job_name_from_path(path, kind=kind)
    out["date"] = _date_from_filename(path)
    out["job_name"] = _job_name_from_row(record, job_fallback)
    out["task_id"] = str(record.get("task_id") or "")
    out["trace_id"] = str(record.get("trace_id") or "")
    out["tags"] = _serialize_tags(record.get("tags"))
    out["score"] = _extract_score(record)
    out["ideal_verdict"] = str(record.get("ideal_verdict") or "")
    out["actual_verdict"] = str(record.get("actual_verdict") or "")
    out["gate_result"] = str(record.get("gate_result") or "")
    out["dryrun_rule"] = str(record.get("dryrun_rule") or "")
    out["source_kind"] = kind
    out["source_file"] = path.as_posix()
    return out


def row_from_enf(
    record: dict[str, Any],
    *,
    path: Path,
    kind: SourceKind,
) -> dict[str, str]:
    out = _empty_row()
    job_fallback = _job_name_from_path(path, kind=kind)
    out["date"] = (
        _parse_iso_date(record.get("timestamp"))
        or _date_from_filename(path)
    )
    out["job_name"] = _job_name_from_row(record, job_fallback)
    out["task_id"] = str(record.get("task_id") or "")
    out["trace_id"] = str(record.get("trace_id") or "")
    out["tags"] = _serialize_tags(record.get("tags"))
    out["score"] = _extract_score(record)
    out["ideal_verdict"] = str(record.get("ideal_verdict") or "")
    out["actual_verdict"] = str(record.get("actual_verdict") or "")
    out["gate_result"] = str(record.get("gate_result") or "")
    out["dryrun_rule"] = str(record.get("dryrun_rule") or "")
    hits = record.get("enf_rule_hits")
    if hits is None and record.get("preview_rule"):
        hits = [record["preview_rule"]]
    out["enf_rule_hits"] = _serialize_enf_hits(hits)
    out["source_kind"] = kind
    out["source_file"] = path.as_posix()
    return out


def normalize_record_row(record: dict[str, Any], path: Path) -> dict[str, str]:
    kind = detect_source_kind(path, record)
    if kind == "eval_export":
        return row_from_eval_export(record, path=path, kind=kind)
    if kind == "dryrun":
        return row_from_dryrun(record, path=path, kind=kind)
    if kind == "enf":
        return row_from_enf(record, path=path, kind=kind)
    out = row_from_eval_export(record, path=path, kind="unknown")
    out["source_kind"] = "unknown"
    return out


def collect_rows(input_paths: Iterable[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in input_paths:
        if not path.is_file():
            raise FileNotFoundError(f"input not found: {path.as_posix()}")
        for record in _iter_jsonl(path):
            rows.append(normalize_record_row(record, path))
    return rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(UNIFIED_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export_eval_stats_csv(
    input_paths: list[Path],
    output_path: Path,
) -> dict[str, Any]:
    """Merge JSONL artefacts into a unified-schema CSV. Returns structured result dict."""
    if not input_paths:
        return {
            "ok": False,
            "message": "at least one --input path is required",
            "written": 0,
            "inputs": [],
            "output": output_path.as_posix(),
        }
    try:
        rows = collect_rows(input_paths)
        write_csv(rows, output_path)
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "message": str(exc),
            "written": 0,
            "inputs": [p.as_posix() for p in input_paths],
            "output": output_path.as_posix(),
        }
    return {
        "ok": True,
        "message": f"wrote {len(rows)} row(s)",
        "written": len(rows),
        "inputs": [p.as_posix() for p in input_paths],
        "output": output_path.as_posix(),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export eval / dryrun / ENF JSONL artefacts to a unified-schema CSV.",
    )
    parser.add_argument(
        "--input",
        dest="inputs",
        action="append",
        type=Path,
        required=True,
        help="JSONL input path (repeat for multiple files).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output CSV path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = export_eval_stats_csv(list(args.inputs), args.output)
    if result["ok"]:
        print(
            f"[export-eval-stats-csv] ok written={result['written']} "
            f"output={result['output']}",
            flush=True,
        )
        return 0
    print(f"[export-eval-stats-csv] error {result['message']}", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
