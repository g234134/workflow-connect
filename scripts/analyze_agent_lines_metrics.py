#!/usr/bin/env python3
"""Offline agent-lines metrics extractor v1 (W10-T2 / W12-T2).

Read-only scan of local outbox / regression JSON artifacts for Tabular agent
standard line and non-tabular preview. Emits aggregate metrics as JSON + CSV.

Usage:
    python scripts/analyze_agent_lines_metrics.py
    python scripts/analyze_agent_lines_metrics.py --format json
    python scripts/analyze_agent_lines_metrics.py --repo-root /path/to/repo
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

Format = Literal["text", "json"]

_SCHEMA_VERSION = "agent_lines_metrics_v1"
_FILENAME_TS_RE = re.compile(r"^(\d{8}T\d{6}Z)_")

_DEFAULT_SCAN_DIRS = (
    "outbox/agent_experiment_regression",
    "outbox/agent_ci",
    "outbox/non_tabular_experiment",
)

_DEFAULT_OUTPUT_DIR = "outbox/agent_metrics"

_CP_A_TRIGGER_STATUSES = frozenset(
    {
        "would_pause",
        "auto_approved",
        "written",
        "awaiting_human",
        "paused",
        "triggered",
    }
)
_CP_B_TRIGGER_STATUSES = frozenset(
    {
        "would_trigger",
        "written",
        "stopped_before_delivery",
        "triggered",
        "stopped_at_checkpoint_b",
    }
)

_SKIP_DIR_NAMES = frozenset({"_checkpoint_scratch"})

_TABULAR_SOURCES = frozenset({"agent_experiment_regression", "agent_ci"})
_MATURITY_TIER_ORDER = (
    "stable",
    "controlled_experimental",
    "experimental",
    "unknown",
)
_EXPERIMENT_SCRIPT = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
_fixture_maturity_resolver: Optional[Any] = None



def default_scan_roots(repo_root: Optional[Path] = None) -> List[Path]:
    root = repo_root or _REPO_ROOT
    return [root / rel for rel in _DEFAULT_SCAN_DIRS]


def default_output_dir(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / _DEFAULT_OUTPUT_DIR


def _parse_compact_timestamp(value: str) -> Optional[datetime]:
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).astimezone(timezone.utc)
    except ValueError:
        return None


def _parse_iso_timestamp(value: str) -> Optional[datetime]:
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).astimezone(timezone.utc)
    except ValueError:
        return None


def _infer_source_name(path: Path, repo_root: Path) -> str:
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        rel = path.as_posix()
    if rel.startswith("outbox/"):
        return rel[len("outbox/") :]
    return rel


def _iter_json_files(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return
    for item in sorted(root.rglob("*.json")):
        if any(part in _SKIP_DIR_NAMES for part in item.parts):
            continue
        if item.name.startswith("."):
            continue
        yield item


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def is_checkpoint_a_triggered(payload: Dict[str, Any]) -> bool:
    summary = payload.get("case_summary") or {}
    status = summary.get("checkpoint_a_status")
    if isinstance(status, str) and status in _CP_A_TRIGGER_STATUSES:
        return True
    experiment = payload.get("experiment") or {}
    cp_a = experiment.get("checkpoint_a_status") or {}
    if cp_a.get("would_trigger") is True:
        return True
    cp_status = cp_a.get("status")
    if isinstance(cp_status, str) and cp_status in _CP_A_TRIGGER_STATUSES:
        return True
    return False


def is_checkpoint_b_triggered(payload: Dict[str, Any]) -> bool:
    summary = payload.get("case_summary") or {}
    if summary.get("checkpoint_b_would_trigger") is True:
        return True
    status = summary.get("checkpoint_b_status")
    if isinstance(status, str) and status in _CP_B_TRIGGER_STATUSES:
        return True
    experiment = payload.get("experiment") or {}
    cp_b = experiment.get("checkpoint_b_status") or {}
    if cp_b.get("would_trigger") is True:
        return True
    cp_status = cp_b.get("status")
    if isinstance(cp_status, str) and cp_status in _CP_B_TRIGGER_STATUSES:
        return True
    integration = cp_b.get("integration") or {}
    if integration.get("checkpoint_created") is True:
        return True
    return False


def infer_run_success(payload: Dict[str, Any], source: str) -> bool:
    summary = payload.get("case_summary") or {}
    if "ok" in summary:
        return bool(summary.get("ok"))
    if "ok" in payload:
        return bool(payload.get("ok"))
    experiment = payload.get("experiment") or {}
    if "ok" in experiment:
        return bool(experiment.get("ok"))
    final_status = (
        summary.get("final_status")
        or payload.get("final_status")
        or experiment.get("final_status")
    )
    if isinstance(final_status, str):
        if final_status in {"blocked", "error", "failed"}:
            return False
        if final_status in {
            "preview_ready",
            "waiting_for_human",
            "run_complete",
            "stopped_at_checkpoint_b",
            "stopped_at_cleaning_preview",
        }:
            return True
    if source == "non_tabular_experiment":
        return final_status == "preview_ready"
    return False


def _load_fixture_maturity_resolver():
    global _fixture_maturity_resolver
    if _fixture_maturity_resolver is not None:
        return _fixture_maturity_resolver
    if not _EXPERIMENT_SCRIPT.is_file():
        _fixture_maturity_resolver = False
        return _fixture_maturity_resolver
    spec = importlib.util.spec_from_file_location(
        "run_agent_standard_case_experiment_metrics",
        _EXPERIMENT_SCRIPT,
    )
    if spec is None or spec.loader is None:
        _fixture_maturity_resolver = False
        return _fixture_maturity_resolver
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _fixture_maturity_resolver = getattr(mod, "get_fixture_maturity", False)
    return _fixture_maturity_resolver


def extract_fixture_maturity(
    payload: Dict[str, Any],
    *,
    source: str,
    case_ref: str,
) -> Optional[str]:
    """Return fixture maturity tier for tabular runs; None for non-tabular."""
    if source not in _TABULAR_SOURCES:
        return None
    summary = payload.get("case_summary") or {}
    experiment = payload.get("experiment") or {}
    for container in (summary, experiment):
        value = container.get("fixture_maturity")
        if isinstance(value, str) and value.strip():
            return value.strip()
    if case_ref and case_ref != "unknown":
        resolver = _load_fixture_maturity_resolver()
        if resolver:
            return str(resolver(case_ref))
    return "unknown"


def _sorted_maturity_tiers(keys: Iterable[str]) -> List[str]:
    order = {tier: idx for idx, tier in enumerate(_MATURITY_TIER_ORDER)}
    return sorted(keys, key=lambda item: (order.get(item, len(_MATURITY_TIER_ORDER)), item))


def extract_case_ref(payload: Dict[str, Any]) -> str:
    summary = payload.get("case_summary") or {}
    for key in ("case_ref",):
        value = summary.get(key) or payload.get(key)
        if value:
            return str(value)
    experiment = payload.get("experiment") or {}
    if experiment.get("case_ref"):
        return str(experiment["case_ref"])
    return "unknown"


def infer_duration_seconds(payload: Dict[str, Any], filepath: Path) -> Optional[float]:
    end_ts = _parse_iso_timestamp(str(payload.get("written_at") or ""))
    meta = payload.get("regression_meta") or {}
    start_ts = _parse_compact_timestamp(str(meta.get("timestamp") or ""))
    if start_ts is None:
        match = _FILENAME_TS_RE.match(filepath.name)
        if match:
            start_ts = _parse_compact_timestamp(match.group(1))
    if start_ts is None or end_ts is None:
        return None
    delta = (end_ts - start_ts).total_seconds()
    if delta < 0:
        return None
    return round(delta, 3)


def _empty_bucket() -> Dict[str, Any]:
    return {
        "total_runs": 0,
        "successful_runs": 0,
        "failed_runs": 0,
        "error_rate": 0.0,
        "checkpoint_a_triggered": 0,
        "checkpoint_a_trigger_rate": 0.0,
        "checkpoint_b_triggered": 0,
        "checkpoint_b_trigger_rate": 0.0,
        "duration_samples": 0,
        "duration_seconds_mean": None,
        "duration_seconds_median": None,
        "duration_seconds_min": None,
        "duration_seconds_max": None,
    }


def _finalize_bucket(bucket: Dict[str, Any], durations: List[float]) -> Dict[str, Any]:
    total = bucket["total_runs"]
    failed = bucket["failed_runs"]
    bucket["error_rate"] = round(failed / total, 4) if total else 0.0
    cp_a = bucket["checkpoint_a_triggered"]
    cp_b = bucket["checkpoint_b_triggered"]
    bucket["checkpoint_a_trigger_rate"] = round(cp_a / total, 4) if total else 0.0
    bucket["checkpoint_b_trigger_rate"] = round(cp_b / total, 4) if total else 0.0
    bucket["duration_samples"] = len(durations)
    if durations:
        bucket["duration_seconds_mean"] = round(statistics.mean(durations), 3)
        bucket["duration_seconds_median"] = round(statistics.median(durations), 3)
        bucket["duration_seconds_min"] = round(min(durations), 3)
        bucket["duration_seconds_max"] = round(max(durations), 3)
    return bucket


def _record_from_payload(
    *,
    payload: Dict[str, Any],
    source: str,
    filepath: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    try:
        rel_path = filepath.relative_to(repo_root).as_posix()
    except ValueError:
        rel_path = filepath.as_posix()
    duration = infer_duration_seconds(payload, filepath)
    cp_applicable = source != "non_tabular_experiment"
    case_ref = extract_case_ref(payload)
    return {
        "source": source,
        "path": rel_path,
        "schema_version": payload.get("schema_version"),
        "case_ref": case_ref,
        "fixture_maturity": extract_fixture_maturity(
            payload, source=source, case_ref=case_ref
        ),
        "ok": infer_run_success(payload, source),
        "final_status": (
            (payload.get("case_summary") or {}).get("final_status")
            or payload.get("final_status")
            or (payload.get("experiment") or {}).get("final_status")
        ),
        "checkpoint_a_triggered": is_checkpoint_a_triggered(payload)
        if cp_applicable
        else None,
        "checkpoint_b_triggered": is_checkpoint_b_triggered(payload)
        if cp_applicable
        else None,
        "duration_seconds": duration,
        "written_at": payload.get("written_at"),
    }


def analyze_agent_lines_metrics(
    *,
    repo_root: Optional[Path] = None,
    scan_roots: Optional[List[Path]] = None,
    write_outputs: bool = True,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Scan agent-line outbox dirs and return structured metrics summary."""
    root = (repo_root or _REPO_ROOT).resolve()
    roots = scan_roots or default_scan_roots(root)
    out_dir = (output_dir or default_output_dir(root)).resolve()

    runs: List[Dict[str, Any]] = []
    sources_meta: List[Dict[str, Any]] = []
    by_source: Dict[str, Dict[str, Any]] = {}
    by_case_ref: Dict[str, Dict[str, Any]] = {}
    by_fixture_maturity: Dict[str, Dict[str, Any]] = {}

    for scan_root in roots:
        source_name = _infer_source_name(scan_root, root)
        exists = scan_root.is_dir()
        file_count = 0
        if exists:
            for json_path in _iter_json_files(scan_root):
                payload = _load_json(json_path)
                if payload is None:
                    continue
                file_count += 1
                record = _record_from_payload(
                    payload=payload,
                    source=source_name,
                    filepath=json_path,
                    repo_root=root,
                )
                runs.append(record)

                src_bucket = by_source.setdefault(source_name, _empty_bucket())
                case_bucket = by_case_ref.setdefault(
                    record["case_ref"], _empty_bucket()
                )
                buckets = [src_bucket, case_bucket]
                maturity = record.get("fixture_maturity")
                if isinstance(maturity, str) and maturity:
                    maturity_bucket = by_fixture_maturity.setdefault(
                        maturity, _empty_bucket()
                    )
                    buckets.append(maturity_bucket)
                for bucket in buckets:
                    bucket["total_runs"] += 1
                    if record["ok"]:
                        bucket["successful_runs"] += 1
                    else:
                        bucket["failed_runs"] += 1
                    if record["checkpoint_a_triggered"] is True:
                        bucket["checkpoint_a_triggered"] += 1
                    if record["checkpoint_b_triggered"] is True:
                        bucket["checkpoint_b_triggered"] += 1

        sources_meta.append(
            {
                "source": source_name,
                "path": scan_root.relative_to(root).as_posix()
                if scan_root.is_relative_to(root)
                else scan_root.as_posix(),
                "exists": exists,
                "json_files_parsed": file_count,
            }
        )

    source_durations: Dict[str, List[float]] = {name: [] for name in by_source}
    case_durations: Dict[str, List[float]] = {name: [] for name in by_case_ref}
    maturity_durations: Dict[str, List[float]] = {
        name: [] for name in by_fixture_maturity
    }
    for record in runs:
        duration = record.get("duration_seconds")
        if duration is None:
            continue
        source_durations.setdefault(record["source"], []).append(duration)
        case_durations.setdefault(record["case_ref"], []).append(duration)
        maturity = record.get("fixture_maturity")
        if isinstance(maturity, str) and maturity:
            maturity_durations.setdefault(maturity, []).append(duration)

    for name, bucket in by_source.items():
        _finalize_bucket(bucket, source_durations.get(name, []))
    for name, bucket in by_case_ref.items():
        _finalize_bucket(bucket, case_durations.get(name, []))
    for name, bucket in by_fixture_maturity.items():
        _finalize_bucket(bucket, maturity_durations.get(name, []))

    aggregate = _empty_bucket()
    all_durations: List[float] = []
    for record in runs:
        aggregate["total_runs"] += 1
        if record["ok"]:
            aggregate["successful_runs"] += 1
        else:
            aggregate["failed_runs"] += 1
        if record["checkpoint_a_triggered"] is True:
            aggregate["checkpoint_a_triggered"] += 1
        if record["checkpoint_b_triggered"] is True:
            aggregate["checkpoint_b_triggered"] += 1
        if record.get("duration_seconds") is not None:
            all_durations.append(float(record["duration_seconds"]))
    _finalize_bucket(aggregate, all_durations)

    summary: Dict[str, Any] = {
        "ok": True,
        "schema_version": _SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "repo_root": root.as_posix(),
        "sources_scanned": sources_meta,
        "aggregate": aggregate,
        "by_source": by_source,
        "by_case_ref": by_case_ref,
        "by_fixture_maturity": by_fixture_maturity,
        "runs": runs,
        "output_paths": {},
        "message": f"parsed {len(runs)} run artifact(s) from {len(roots)} scan root(s)",
    }

    if write_outputs:
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / "metrics_summary.json"
        csv_path = out_dir / "metrics_summary.csv"
        try:
            summary["output_paths"] = {
                "json": json_path.relative_to(root).as_posix(),
                "csv": csv_path.relative_to(root).as_posix(),
            }
        except ValueError:
            summary["output_paths"] = {
                "json": json_path.as_posix(),
                "csv": csv_path.as_posix(),
            }
        with json_path.open("w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        write_metrics_csv(summary, csv_path)

    return summary


def _csv_num(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _bucket_to_csv_row(
    section: str,
    *,
    source: str = "",
    case_ref: str = "",
    fixture_maturity: str = "",
    bucket: Dict[str, Any],
) -> Dict[str, str]:
    return {
        "section": section,
        "source": source,
        "case_ref": case_ref,
        "fixture_maturity": fixture_maturity,
        "total_runs": str(bucket.get("total_runs", 0)),
        "successful_runs": str(bucket.get("successful_runs", 0)),
        "failed_runs": str(bucket.get("failed_runs", 0)),
        "error_rate": str(bucket.get("error_rate", 0.0)),
        "checkpoint_a_triggered": str(bucket.get("checkpoint_a_triggered", 0)),
        "checkpoint_a_trigger_rate": str(bucket.get("checkpoint_a_trigger_rate", 0.0)),
        "checkpoint_b_triggered": str(bucket.get("checkpoint_b_triggered", 0)),
        "checkpoint_b_trigger_rate": str(bucket.get("checkpoint_b_trigger_rate", 0.0)),
        "duration_samples": str(bucket.get("duration_samples", 0)),
        "duration_seconds_mean": _csv_num(bucket.get("duration_seconds_mean")),
        "duration_seconds_median": _csv_num(bucket.get("duration_seconds_median")),
        "duration_seconds_min": _csv_num(bucket.get("duration_seconds_min")),
        "duration_seconds_max": _csv_num(bucket.get("duration_seconds_max")),
    }


CSV_FIELDNAMES = [
    "section",
    "source",
    "case_ref",
    "fixture_maturity",
    "total_runs",
    "successful_runs",
    "failed_runs",
    "error_rate",
    "checkpoint_a_triggered",
    "checkpoint_a_trigger_rate",
    "checkpoint_b_triggered",
    "checkpoint_b_trigger_rate",
    "duration_samples",
    "duration_seconds_mean",
    "duration_seconds_median",
    "duration_seconds_min",
    "duration_seconds_max",
]


def write_metrics_csv(summary: Dict[str, Any], csv_path: Path) -> None:
    rows: List[Dict[str, str]] = []
    rows.append(
        _bucket_to_csv_row("aggregate", bucket=summary.get("aggregate") or {})
    )
    for source, bucket in sorted((summary.get("by_source") or {}).items()):
        rows.append(
            _bucket_to_csv_row("by_source", source=source, bucket=bucket)
        )
    for case_ref, bucket in sorted((summary.get("by_case_ref") or {}).items()):
        rows.append(
            _bucket_to_csv_row("by_case_ref", case_ref=case_ref, bucket=bucket)
        )
    by_fixture_maturity = summary.get("by_fixture_maturity") or {}
    for maturity in _sorted_maturity_tiers(by_fixture_maturity.keys()):
        rows.append(
            _bucket_to_csv_row(
                "by_fixture_maturity",
                fixture_maturity=maturity,
                bucket=by_fixture_maturity[maturity],
            )
        )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def format_fixture_maturity_summary_text(
    by_fixture_maturity: Dict[str, Dict[str, Any]],
) -> List[str]:
    if not by_fixture_maturity:
        return []
    lines = ["by_fixture_maturity (tabular tiers):"]
    for tier in _sorted_maturity_tiers(by_fixture_maturity.keys()):
        bucket = by_fixture_maturity[tier]
        lines.append(
            f"  {tier}: runs={bucket.get('total_runs', 0)} "
            f"error_rate={bucket.get('error_rate', 0.0)} "
            f"cp_a={bucket.get('checkpoint_a_trigger_rate', 0.0)} "
            f"cp_b={bucket.get('checkpoint_b_trigger_rate', 0.0)}"
        )
    return lines


def format_metrics_summary_text(summary: Dict[str, Any]) -> str:
    agg = summary.get("aggregate") or {}
    lines = [
        "Agent Lines Metrics Summary (W10-T2 / W12-T2)",
        f"schema_version: {summary.get('schema_version')}",
        f"generated_at: {summary.get('generated_at')}",
        f"runs parsed: {agg.get('total_runs', 0)}",
        f"successful_runs: {agg.get('successful_runs', 0)}",
        f"failed_runs: {agg.get('failed_runs', 0)}",
        f"error_rate: {agg.get('error_rate', 0.0)}",
        f"checkpoint_a_trigger_rate: {agg.get('checkpoint_a_trigger_rate', 0.0)}",
        f"checkpoint_b_trigger_rate: {agg.get('checkpoint_b_trigger_rate', 0.0)}",
        f"duration_seconds_mean: {agg.get('duration_seconds_mean')}",
        "",
    ]
    lines.extend(
        format_fixture_maturity_summary_text(
            summary.get("by_fixture_maturity") or {}
        )
    )
    if lines and lines[-1] == "":
        lines.pop()
    outputs = summary.get("output_paths") or {}
    if outputs.get("json"):
        lines.append(f"json: {outputs['json']}")
    if outputs.get("csv"):
        lines.append(f"csv: {outputs['csv']}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline metrics extractor for Tabular + non-tabular agent lines.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(_REPO_ROOT),
        help="Repository root (default: script parent directory)",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help=f"Output directory (default: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Analyze only; do not write metrics_summary files",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else default_output_dir(repo_root)
    )
    summary = analyze_agent_lines_metrics(
        repo_root=repo_root,
        write_outputs=not args.no_write,
        output_dir=output_dir,
    )

    if args.format == "json":
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(format_metrics_summary_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
