"""
CI entry for P+ eval_gate: sample recent records and fail on review-rate signal.

Usage:
    python -m observability.eval_ci_check path/to/records.jsonl
    python -m observability.eval_ci_check path/to/dir --limit 50 --max-needs-review-ratio 0.5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final

from observability.enf_config import load_enf_config, log_enf_config
from observability.eval_exporter import build_export_line, iter_records
from observability.eval_gate import evaluate_task_record

DEFAULT_LIMIT: Final[int] = 100
DEFAULT_MAX_NEEDS_REVIEW_RATIO: Final[float] = 0.5
DEFAULT_MIN_SAMPLES: Final[int] = 1


def _load_tail_records(path: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record, _line_index in iter_records(path):
        records.append(record)
    if limit > 0 and len(records) > limit:
        records = records[-limit:]
    return records


def run_ci_check(
    input_path: Path,
    *,
    limit: int = DEFAULT_LIMIT,
    max_needs_review_ratio: float = DEFAULT_MAX_NEEDS_REVIEW_RATIO,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    fail_on_tags: frozenset[str] | None = None,
) -> dict[str, Any]:
    """
    Evaluate the last ``limit`` records and return a structured CI verdict.

    ``ok`` is False when:
    - sampled count < ``min_samples``
    - needs_review ratio > ``max_needs_review_ratio`` (and samples >= min_samples)
    - any sampled row has a tag in ``fail_on_tags`` (when set)
    """
    if max_needs_review_ratio < 0 or max_needs_review_ratio > 1:
        return {
            "ok": False,
            "message": "max_needs_review_ratio must be between 0 and 1",
            "stats": {},
        }

    try:
        records = _load_tail_records(input_path, limit)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": f"failed to load records: {exc}",
            "stats": {},
        }

    sampled = len(records)
    needs_review_count = 0
    tag_hits: dict[str, int] = {}
    fail_tag_rows: list[dict[str, Any]] = []

    for record in records:
        gate = evaluate_task_record(record)
        export_line = build_export_line(record, gate=gate)
        if export_line["gate_result"] == "needs_review":
            needs_review_count += 1
        for tag in export_line.get("tags") or []:
            tag_hits[tag] = tag_hits.get(tag, 0) + 1
            if fail_on_tags and tag in fail_on_tags:
                fail_tag_rows.append(
                    {
                        "task_id": export_line.get("task_id"),
                        "tag": tag,
                    }
                )

    ratio = (needs_review_count / sampled) if sampled else 0.0
    ratio_triggered = sampled >= min_samples and ratio > max_needs_review_ratio
    tag_triggered = bool(fail_tag_rows)

    stats: dict[str, Any] = {
        "sampled": sampled,
        "needs_review_count": needs_review_count,
        "needs_review_ratio": round(ratio, 4),
        "max_needs_review_ratio": max_needs_review_ratio,
        "min_samples": min_samples,
        "ratio_triggered": ratio_triggered,
        "tag_triggered": tag_triggered,
        "tag_counts": tag_hits,
        "fail_on_tags": sorted(fail_on_tags) if fail_on_tags else [],
    }
    if fail_tag_rows:
        stats["fail_tag_rows"] = fail_tag_rows[:20]

    if sampled < min_samples:
        return {
            "ok": False,
            "message": f"insufficient samples: {sampled} < {min_samples}",
            "stats": stats,
        }

    if ratio_triggered:
        return {
            "ok": False,
            "message": (
                f"needs_review ratio {ratio:.2%} exceeds threshold "
                f"{max_needs_review_ratio:.2%} ({needs_review_count}/{sampled})"
            ),
            "stats": stats,
        }

    if tag_triggered:
        return {
            "ok": False,
            "message": f"fail_on_tags matched in sample: {fail_tag_rows[:5]}",
            "stats": stats,
        }

    return {
        "ok": True,
        "message": (
            f"CI check passed: needs_review {needs_review_count}/{sampled} "
            f"({ratio:.2%}), threshold {max_needs_review_ratio:.2%}"
        ),
        "stats": stats,
    }


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CI signal: eval_gate on recent ibridge/metrics records.",
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Input .json / .jsonl file or directory",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Evaluate only the last N records (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--max-needs-review-ratio",
        type=float,
        default=DEFAULT_MAX_NEEDS_REVIEW_RATIO,
        help=(
            f"Fail when needs_review ratio exceeds this value "
            f"(default: {DEFAULT_MAX_NEEDS_REVIEW_RATIO})"
        ),
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=DEFAULT_MIN_SAMPLES,
        help=f"Fail when fewer than N records are available (default: {DEFAULT_MIN_SAMPLES})",
    )
    parser.add_argument(
        "--fail-on-tags",
        default="",
        help="Comma-separated tags that fail CI if present (e.g. infra_risk)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    log_enf_config(load_enf_config())

    args = _build_cli().parse_args(argv)
    tags_raw = (args.fail_on_tags or "").strip()
    fail_on_tags = frozenset(t.strip() for t in tags_raw.split(",") if t.strip()) or None

    result = run_ci_check(
        args.input_path,
        limit=args.limit,
        max_needs_review_ratio=args.max_needs_review_ratio,
        min_samples=args.min_samples,
        fail_on_tags=fail_on_tags,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
