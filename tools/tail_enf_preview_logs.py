"""
Read-only control-plane helper: tail ENF preview log markers or dry-run summaries.

Usage:
  python -m tools.tail_enf_preview_logs --input observability/enf-preview/*.log --limit 20
  python -m tools.tail_enf_preview_logs --from-dryrun observability/dryrun --runs 5
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from tools.enf_preview_wrapper import (
    DECISION_SUMMARY_PREFIX,
    ENF_RULE_1_DEFAULT_MIN_SCORE,
    ENF_RULE_1_NAME,
    ENF_RULE_2_NAME,
    LOG_PREFIX,
    classify_preview_outcome,
)

DEFAULT_MARKERS: tuple[str, ...] = (LOG_PREFIX, DECISION_SUMMARY_PREFIX, "[ENF-WARN]")
DEFAULT_LOG_GLOB = "observability/enf-preview/*.log"
DEFAULT_DRYRUN_DIR = Path("observability/dryrun")


@dataclass(frozen=True)
class MatchedLine:
    source: str
    line_no: int
    text: str
    sort_key: tuple[float, int, int]


def _expand_inputs(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        expanded = sorted(Path().glob(pattern))
        if expanded:
            paths.extend(expanded)
            continue
        candidate = Path(pattern)
        if candidate.is_file():
            paths.append(candidate)
    # stable dedupe, oldest-first read order; tail reverses at end
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _line_matches(line: str, markers: tuple[str, ...]) -> bool:
    return any(marker in line for marker in markers)


def _collect_log_matches(
    files: Iterable[Path],
    *,
    markers: tuple[str, ...],
) -> list[MatchedLine]:
    matches: list[MatchedLine] = []
    for path in files:
        if not path.is_file():
            continue
        mtime = path.stat().st_mtime
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_no, raw in enumerate(handle, start=1):
                text = raw.rstrip("\n")
                if _line_matches(text, markers):
                    matches.append(
                        MatchedLine(
                            source=path.as_posix(),
                            line_no=line_no,
                            text=text,
                            sort_key=(mtime, line_no, len(matches)),
                        )
                    )
    return matches


def _load_per_record_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _summarize_dryrun_file(path: Path, *, min_score: float) -> str:
    rows = _load_per_record_rows(path)
    would_block = 0
    would_warn = 0
    would_noop = 0
    rule1_blocks = 0
    rule2_warns = 0

    for row in rows:
        outcome, rule_name = classify_preview_outcome(row, min_score=min_score)
        if outcome == "block":
            would_block += 1
            rule1_blocks += 1
        elif outcome == "warn":
            would_warn += 1
            rule2_warns += 1
        else:
            would_noop += 1

    total = len(rows)
    return (
        f"{LOG_PREFIX} event=summary total={total} would_block={would_block} "
        f"would_warn={would_warn} would_noop={would_noop} input={path.as_posix()} "
        f"source=dryrun_artefact min_score={min_score} "
        f"rule1={ENF_RULE_1_NAME}:{rule1_blocks} rule2={ENF_RULE_2_NAME}:{rule2_warns}"
    )


def _collect_dryrun_summaries(
    dryrun_dir: Path,
    *,
    runs: int,
    min_score: float,
) -> list[MatchedLine]:
    if not dryrun_dir.is_dir():
        return []

    per_record_files = sorted(dryrun_dir.glob("*_per_record.jsonl"), key=lambda p: p.name)
    selected = per_record_files[-runs:] if runs > 0 else per_record_files

    lines: list[MatchedLine] = []
    for index, path in enumerate(selected):
        try:
            text = _summarize_dryrun_file(path, min_score=min_score)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            text = (
                f"{LOG_PREFIX} [WARN] event=skip reason=artefact_error "
                f"input={path.as_posix()} message={exc}"
            )
        mtime = path.stat().st_mtime
        lines.append(
            MatchedLine(
                source=path.as_posix(),
                line_no=0,
                text=text,
                sort_key=(mtime, index, 0),
            )
        )
    return lines


def _emit_matches(matches: list[MatchedLine], *, limit: int) -> None:
    if not matches:
        print(
            f"{LOG_PREFIX} [WARN] event=empty reason=no_matching_lines "
            "hint=pass --from-dryrun or capture CI stdout to *.log",
            flush=True,
        )
        return

    tail = matches[-limit:] if limit > 0 else matches
    for item in tail:
        prefix = f"{item.source}:{item.line_no}: " if item.line_no else f"{item.source}: "
        print(prefix + item.text, flush=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Show recent ENF preview log lines (grep) or summaries from dry-run artefacts "
            "(read-only)."
        ),
    )
    parser.add_argument(
        "--input",
        nargs="*",
        default=None,
        help=f"Log file path(s) or glob(s) (default: {DEFAULT_LOG_GLOB}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of matching lines to print (default: 20).",
    )
    parser.add_argument(
        "--marker",
        action="append",
        dest="markers",
        help=f"Substring marker to match (default: {', '.join(DEFAULT_MARKERS)}).",
    )
    parser.add_argument(
        "--from-dryrun",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Also synthesize summary lines from the latest *_per_record.jsonl files "
            f"(default dir when flag alone: {DEFAULT_DRYRUN_DIR.as_posix()})."
        ),
        nargs="?",
        const=DEFAULT_DRYRUN_DIR,
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="With --from-dryrun, number of latest per-record artefacts (default: 5).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=ENF_RULE_1_DEFAULT_MIN_SCORE,
        help=f"ENF-RULE-1 threshold for --from-dryrun (default: {ENF_RULE_1_DEFAULT_MIN_SCORE}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    markers = tuple(args.markers) if args.markers else DEFAULT_MARKERS
    matches: list[MatchedLine] = []

    patterns = args.input if args.input is not None else [DEFAULT_LOG_GLOB]
    log_files = _expand_inputs(patterns)
    matches.extend(_collect_log_matches(log_files, markers=markers))

    if args.from_dryrun is not None:
        matches.extend(
            _collect_dryrun_summaries(
                args.from_dryrun,
                runs=args.runs,
                min_score=args.min_score,
            )
        )

    matches.sort(key=lambda item: item.sort_key)
    _emit_matches(matches, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
