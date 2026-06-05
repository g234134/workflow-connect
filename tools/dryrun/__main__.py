"""CLI entry: python -m tools.dryrun [--input-dir PATH] [artefact ...]"""

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

DEFAULT_INPUT_DIR = Path("artifacts/eval")
DEFAULT_OUTPUT_DIR = Path("observability/dryrun")
DEFAULT_MIN_SCORE = 0.875


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only dry-run: compare gate artefacts vs simplified ideal verdicts.",
    )
    parser.add_argument(
        "artefacts",
        nargs="*",
        type=Path,
        help="Optional explicit artefact file(s) or directory(ies).",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help=f"Directory to scan for shadow eval / ibridge JSONL (default: {DEFAULT_INPUT_DIR}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Write reports here (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_SCORE,
        help="Trace completeness threshold for gate_ok_score_high (default: 0.875).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-record lines to stdout.",
    )
    return parser


def _collect_paths(args: argparse.Namespace) -> list[Path]:
    paths: list[Path] = []
    if args.artefacts:
        for artefact in args.artefacts:
            if artefact.is_dir():
                paths.extend(discover_input_paths(artefact))
            else:
                paths.append(artefact)
    input_dir = args.input_dir or (DEFAULT_INPUT_DIR if not args.artefacts else None)
    if input_dir is not None:
        paths.extend(discover_input_paths(input_dir))
    # stable dedupe
    seen: set[str] = set()
    unique: list[Path] = []
    for p in paths:
        key = str(p.resolve()) if p.exists() else str(p)
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_paths = _collect_paths(args)
    if not input_paths:
        print(f"{DISCLAIMER}", file=sys.stderr)
        print("error: no input artefacts found; pass paths or --input-dir", file=sys.stderr)
        return 2

    records, aggregate_gate = load_records_from_paths(input_paths)
    if not records:
        print(f"{DISCLAIMER}", file=sys.stderr)
        print("error: no per-task records loaded from inputs", file=sys.stderr)
        return 2

    rows = build_comparison_rows(records, min_score=args.min_score)
    jsonl_path, md_path, stamp = emit_reports(
        rows,
        args.output_dir,
        input_paths=input_paths,
        min_score=args.min_score,
        aggregate_gate=aggregate_gate,
    )

    total = len(rows)
    matches = sum(1 for r in rows if r.get("verdict_match"))
    ratio = (matches / total) if total else 0.0
    mismatches = total - matches

    print(DISCLAIMER)
    print(f"records={total} matches={matches} match_ratio={ratio:.1%} mismatches={mismatches}")
    print(f"min_score={args.min_score}")
    print(f"inputs={len(input_paths)} files")
    for p in input_paths:
        print(f"  - {p.as_posix()}")
    print(f"per_record={jsonl_path.as_posix()}")
    print(f"summary={md_path.as_posix()}")

    if args.verbose:
        for row in rows:
            mark = "OK" if row.get("verdict_match") else "DIFF"
            print(
                f"  [{mark}] {row.get('task_id')}: actual={row.get('actual_verdict')} "
                f"ideal={row.get('ideal_verdict')} rule={row.get('dryrun_rule')}"
            )

    if aggregate_gate:
        print(
            f"aggregate_gate: ok={aggregate_gate.get('ok')} "
            f"verdict={aggregate_gate.get('verdict')} "
            f"source={aggregate_gate.get('source_file')}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
