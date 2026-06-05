"""
CI logging-only wrapper for tools.dryrun.

Emits structured [DRYRUN-LOG] lines for nightly observability.
Always exits 0 — never influences pipeline pass/fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.dryrun.core import (
    DISCLAIMER,
    build_comparison_rows,
    discover_input_paths,
    load_records_from_paths,
)
from tools.dryrun.output import emit_reports

LOG_PREFIX = "[DRYRUN-LOG]"


def _emit(event: str, **fields: object) -> None:
    parts = [LOG_PREFIX, f"event={event}"]
    for key, value in fields.items():
        if value is None:
            continue
        text = str(value).replace("\n", " ")
        parts.append(f"{key}={text}")
    print(" ".join(parts), flush=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Logging-only CI wrapper for tools.dryrun (always exit 0).",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Primary artefact file or directory (repo-relative).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("observability/dryrun"),
        help="Write dry-run reports here (default: observability/dryrun).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.875,
        help="Trace completeness threshold for gate_ok_score_high (default: 0.875).",
    )
    return parser


def run_logging_only(
    *,
    input_path: Path,
    output_dir: Path,
    min_score: float,
) -> None:
    _emit("start", disclaimer=DISCLAIMER, input=input_path.as_posix(), min_score=min_score)

    if input_path.is_dir():
        input_paths = discover_input_paths(input_path)
    elif input_path.is_file():
        input_paths = [input_path]
    else:
        _emit("skip", reason="input_not_found", input=input_path.as_posix())
        _emit("complete", status="skipped", exit_policy="logging_only")
        return

    if not input_paths:
        _emit("skip", reason="no_discoverable_artefacts", input=input_path.as_posix())
        _emit("complete", status="skipped", exit_policy="logging_only")
        return

    records, aggregate_gate = load_records_from_paths(input_paths)
    if not records:
        _emit("skip", reason="no_records_loaded", inputs=len(input_paths))
        _emit("complete", status="skipped", exit_policy="logging_only")
        return

    rows = build_comparison_rows(records, min_score=min_score)
    jsonl_path, md_path, stamp = emit_reports(
        rows,
        output_dir,
        input_paths=input_paths,
        min_score=min_score,
        aggregate_gate=aggregate_gate,
    )

    total = len(rows)
    matches = sum(1 for row in rows if row.get("verdict_match"))
    mismatches = total - matches
    ratio = (matches / total) if total else 0.0

    _emit(
        "inputs",
        count=len(input_paths),
        files="|".join(p.as_posix() for p in input_paths),
    )
    _emit(
        "summary",
        records=total,
        matches=matches,
        mismatches=mismatches,
        match_ratio=f"{ratio:.1%}",
        min_score=min_score,
    )
    _emit("artefact", per_record=jsonl_path.as_posix(), summary=md_path.as_posix(), stamp=stamp)

    if aggregate_gate:
        _emit(
            "aggregate_gate",
            ok=aggregate_gate.get("ok"),
            verdict=aggregate_gate.get("verdict"),
            source=aggregate_gate.get("source_file"),
        )

    mismatch_rows = [row for row in rows if not row.get("verdict_match")]
    if mismatch_rows:
        sample = mismatch_rows[:5]
        for row in sample:
            _emit(
                "mismatch",
                task_id=row.get("task_id"),
                actual=row.get("actual_verdict"),
                ideal=row.get("ideal_verdict"),
                rule=row.get("dryrun_rule"),
            )
        if len(mismatch_rows) > len(sample):
            _emit("mismatch_truncated", shown=len(sample), total=len(mismatch_rows))

    _emit("complete", status="ok", exit_policy="logging_only")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        run_logging_only(
            input_path=args.input,
            output_dir=args.output_dir,
            min_score=args.min_score,
        )
    except Exception as exc:  # noqa: BLE001 — CI logging-only must never fail the job
        _emit("error", type=type(exc).__name__, message=str(exc))
        _emit("complete", status="error_logged", exit_policy="logging_only")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
