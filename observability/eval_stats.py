"""
Distribution analysis for eval_export/v1 JSONL artifacts.

Reads one or more export files (not raw ibridge records), computes
needs_review ratio and tag histograms, and suggests CI threshold ranges.

Usage:
    python -m observability.eval_stats artifacts/eval/eval_results.latest.jsonl
    python -m observability.eval_stats path/a.jsonl path/b.jsonl --group-by date
    python -m observability.eval_stats path/to.jsonl --format text --min-samples 10
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Iterator, Literal

SCHEMA_VERSION: Final[str] = "eval_export/v1"

KNOWN_GATE_TAGS: Final[frozenset[str]] = frozenset(
    {
        "high_retry",
        "context_heavy",
        "many_handoffs",
        "infra_risk",
        "observability_gap",
    }
)

DEFAULT_MIN_SAMPLES_FOR_RECOMMENDATIONS: Final[int] = 10
DATE_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"^(\d{4}-\d{2}-\d{2})")

GroupBy = Literal["none", "date", "exported_date", "file"]


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
    return obj


def iter_export_lines(path: Path) -> Iterator[tuple[dict[str, Any], int, str]]:
    """
    Yield ``(export_line, line_no, source_label)`` from a single JSONL file.

    Skips blank lines. Warns on schema_version mismatch via ``warnings`` list
    attached to the caller through ``load_export_files`` instead.
    """
    if not path.exists():
        raise FileNotFoundError(str(path))
    if not path.is_file():
        raise ValueError(f"expected a file, got directory: {path}")
    if path.suffix.lower() != ".jsonl":
        raise ValueError(f"expected .jsonl export file: {path.name}")

    source = str(path)
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = _parse_json_line(raw, source=source, line_no=line_no)
        if line is not None:
            yield line, line_no, path.name


def _date_prefix(iso_ts: str | None) -> str:
    if not iso_ts:
        return "unknown"
    match = DATE_PREFIX_RE.match(str(iso_ts).strip())
    return match.group(1) if match else "unknown"


def _group_key(line: dict[str, Any], *, group_by: GroupBy, source_file: str) -> str:
    if group_by == "none":
        return "all"
    if group_by == "file":
        return source_file
    if group_by == "exported_date":
        return _date_prefix(line.get("exported_at"))
    if group_by == "date":
        return _date_prefix(line.get("timestamp"))
    raise ValueError(f"unsupported group_by: {group_by}")


def _accumulate_row(
    acc: dict[str, Any],
    line: dict[str, Any],
    *,
    schema_warnings: list[str],
    source_file: str,
    line_no: int,
) -> None:
    version = line.get("schema_version")
    if version != SCHEMA_VERSION:
        schema_warnings.append(
            f"{source_file}:{line_no}: schema_version={version!r} (expected {SCHEMA_VERSION})"
        )

    acc["total"] += 1
    gate_result = line.get("gate_result")
    if gate_result == "needs_review":
        acc["needs_review_count"] += 1
    elif gate_result == "pass":
        acc["pass_count"] += 1
    else:
        acc["unknown_gate_result_count"] += 1

    tags = line.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    if tags:
        acc["rows_with_tags"] += 1
    for tag in tags:
        tag_str = str(tag)
        acc["tag_counts"][tag_str] = acc["tag_counts"].get(tag_str, 0) + 1
        if tag_str not in KNOWN_GATE_TAGS:
            acc["other_tag_counts"][tag_str] = acc["other_tag_counts"].get(tag_str, 0) + 1


def _finalize_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    total = bucket["total"]
    needs = bucket["needs_review_count"]
    ratio = (needs / total) if total else 0.0
    tag_counts: dict[str, int] = bucket["tag_counts"]
    tag_rates = {tag: round(count / total, 4) for tag, count in sorted(tag_counts.items())}
    tag_shares = {
        tag: round(count / max(bucket["rows_with_tags"], 1), 4)
        for tag, count in sorted(tag_counts.items())
    }
    return {
        "total": total,
        "pass_count": bucket["pass_count"],
        "needs_review_count": needs,
        "needs_review_ratio": round(ratio, 4),
        "unknown_gate_result_count": bucket["unknown_gate_result_count"],
        "rows_with_tags": bucket["rows_with_tags"],
        "tag_counts": tag_counts,
        "tag_rates": tag_rates,
        "tag_shares_of_tagged_rows": tag_shares,
        "other_tags": sorted(bucket["other_tag_counts"].keys()),
    }


def _empty_bucket() -> dict[str, Any]:
    return {
        "total": 0,
        "pass_count": 0,
        "needs_review_count": 0,
        "unknown_gate_result_count": 0,
        "rows_with_tags": 0,
        "tag_counts": {},
        "other_tag_counts": {},
    }


def analyze_export_files(
    paths: list[Path],
    *,
    group_by: GroupBy = "none",
    min_samples_for_recommendations: int = DEFAULT_MIN_SAMPLES_FOR_RECOMMENDATIONS,
) -> dict[str, Any]:
    """
    Analyze eval_export/v1 JSONL file(s).

    Returns a structured dict suitable for CLI JSON output and reports.
    """
    if not paths:
        return {
            "ok": False,
            "message": "no input paths provided",
            "stats": {},
            "recommendations": {},
        }

    schema_warnings: list[str] = []
    groups: dict[str, dict[str, Any]] = {}
    input_files: list[str] = []

    for path in paths:
        if not path.exists():
            return {
                "ok": False,
                "message": f"file not found: {path.name}",
                "stats": {"input_files": input_files},
                "recommendations": {},
            }
        input_files.append(path.name)
        try:
            for line, line_no, source_file in iter_export_lines(path):
                key = _group_key(line, group_by=group_by, source_file=source_file)
                if key not in groups:
                    groups[key] = _empty_bucket()
                _accumulate_row(
                    groups[key],
                    line,
                    schema_warnings=schema_warnings,
                    source_file=source_file,
                    line_no=line_no,
                )
        except (OSError, ValueError) as exc:
            return {
                "ok": False,
                "message": f"failed to read {path.name}: {exc}",
                "stats": {"input_files": input_files},
                "recommendations": {},
            }

    if "all" not in groups and groups:
        merged = _empty_bucket()
        for bucket in groups.values():
            merged["total"] += bucket["total"]
            merged["pass_count"] += bucket["pass_count"]
            merged["needs_review_count"] += bucket["needs_review_count"]
            merged["unknown_gate_result_count"] += bucket["unknown_gate_result_count"]
            merged["rows_with_tags"] += bucket["rows_with_tags"]
            for tag, count in bucket["tag_counts"].items():
                merged["tag_counts"][tag] = merged["tag_counts"].get(tag, 0) + count
            for tag, count in bucket["other_tag_counts"].items():
                merged["other_tag_counts"][tag] = merged["other_tag_counts"].get(tag, 0) + count
        groups["all"] = merged

    overall_key = "all" if "all" in groups else next(iter(groups), "all")
    overall = _finalize_bucket(groups.get(overall_key, _empty_bucket()))
    grouped = {key: _finalize_bucket(bucket) for key, bucket in sorted(groups.items())}

    total = overall["total"]
    sufficient = total >= min_samples_for_recommendations
    recommendations = suggest_ci_thresholds(
        overall,
        min_samples_for_recommendations=min_samples_for_recommendations,
    )

    if total == 0:
        message = "no eval_export lines found; cannot compute distribution"
        ok = False
    elif not sufficient:
        message = (
            f"analyzed {total} sample(s) from {len(input_files)} file(s); "
            f"below min_samples={min_samples_for_recommendations} for high-confidence "
            "CI threshold recommendations (provisional values included)"
        )
        ok = True
    else:
        message = (
            f"analyzed {total} sample(s); needs_review {overall['needs_review_ratio']:.2%}"
        )
        ok = True

    return {
        "ok": ok,
        "message": message,
        "stats": {
            "input_files": input_files,
            "group_by": group_by,
            "analyzed_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "overall": overall,
            "groups": grouped if group_by != "none" else {},
            "schema_warnings": schema_warnings[:50],
            "min_samples_for_recommendations": min_samples_for_recommendations,
            "sufficient_for_recommendations": sufficient,
        },
        "recommendations": recommendations,
    }


def suggest_ci_thresholds(
    overall: dict[str, Any],
    *,
    min_samples_for_recommendations: int = DEFAULT_MIN_SAMPLES_FOR_RECOMMENDATIONS,
) -> dict[str, Any]:
    """
    Derive provisional CI settings from observed distribution.

    Does not modify CI; returns suggested ranges and tag policies only.
    """
    total = overall.get("total", 0)
    ratio = float(overall.get("needs_review_ratio", 0.0))
    tag_rates: dict[str, float] = overall.get("tag_rates") or {}
    tag_counts: dict[str, int] = overall.get("tag_counts") or {}

    if total == 0:
        return {
            "confidence": "none",
            "notes": ["No samples — run export on dev/staging artifacts first."],
            "max_needs_review_ratio": None,
            "fail_on_tags": [],
        }

    confidence = "high" if total >= min_samples_for_recommendations else "low"

    # Headroom above observed ratio for normal batch noise (~5–25 pp).
    margin_low = 0.05
    margin_high = max(0.20, ratio * 0.25)
    suggested_low = round(min(0.95, ratio + margin_low), 2)
    suggested_high = round(min(0.95, ratio + margin_high), 2)
    if suggested_high < suggested_low:
        suggested_high = suggested_low

    ratio_notes = [
        f"Observed needs_review ratio: {ratio:.2%} ({overall.get('needs_review_count', 0)}/{total}).",
        (
            f"Suggest --max-needs-review-ratio in [{suggested_low:.2f}, {suggested_high:.2f}]: "
            "ceiling above typical batch with room for small regressions; "
            "tighten toward the low end once staging baseline stabilizes."
        ),
    ]
    if confidence == "low":
        ratio_notes.append(
            f"Sample size {total} < {min_samples_for_recommendations}: "
            "re-run after Chat A nightly export accumulates more rows."
        )

    fail_on_tags: list[dict[str, str]] = []
    warn_tags: list[dict[str, str]] = []

    infra_count = tag_counts.get("infra_risk", 0)
    fail_on_tags.append(
        {
            "tag": "infra_risk",
            "action": "fail",
            "reason": (
                "Infrastructure failures (timeout, context_overflow) should block CI "
                "even when overall needs_review ratio is within range."
            ),
        }
    )
    if infra_count:
        ratio_notes.append(
            f"Observed infra_risk in {infra_count}/{total} rows "
            f"({tag_rates.get('infra_risk', 0):.2%}) — any occurrence should fail CI."
        )

    obs_rate = tag_rates.get("observability_gap", 0.0)
    if obs_rate >= 0.10 or tag_counts.get("observability_gap", 0) >= max(3, total // 10):
        warn_tags.append(
            {
                "tag": "observability_gap",
                "action": "warn",
                "reason": (
                    f"observability_gap appears in {tag_counts.get('observability_gap', 0)} rows "
                    f"({obs_rate:.2%}); use dashboard alert first, add --fail-on-tags once "
                    "trace instrumentation improves."
                ),
            }
        )
    else:
        fail_on_tags.append(
            {
                "tag": "observability_gap",
                "action": "optional_fail",
                "reason": (
                    "Low frequency in current sample; enable --fail-on-tags observability_gap "
                    "on nightly/production paths when baseline is near zero."
                ),
            }
        )

    for noisy_tag in ("high_retry", "context_heavy", "many_handoffs"):
        count = tag_counts.get(noisy_tag, 0)
        if count:
            warn_tags.append(
                {
                    "tag": noisy_tag,
                    "action": "monitor",
                    "reason": (
                        f"{noisy_tag} seen {count} time(s) ({tag_rates.get(noisy_tag, 0):.2%}); "
                        "ratio gate usually sufficient — fail-on-tags only if policy requires."
                    ),
                }
            )

    other_tags = overall.get("other_tags") or []
    if other_tags:
        warn_tags.append(
            {
                "tag": ",".join(other_tags),
                "action": "investigate",
                "reason": "Unknown tags outside eval_gate v0.1 set — verify exporter version.",
            }
        )

    return {
        "confidence": confidence,
        "notes": ratio_notes,
        "max_needs_review_ratio": {
            "observed": ratio,
            "suggested_range": [suggested_low, suggested_high],
            "ci_fixture_baseline": 0.8,
            "ci_fixture_note": (
                "Current workflow uses 0.8 on unit-test fixture (~67% needs_review); "
                "replace with suggested_range once real dev/staging export N≥30."
            ),
        },
        "fail_on_tags": fail_on_tags,
        "warn_tags": warn_tags,
        "suggested_cli": {
            "max_needs_review_ratio": suggested_high,
            "fail_on_tags": [item["tag"] for item in fail_on_tags if item["action"] == "fail"],
        },
    }


_KB_INDEX_BUCKET_ORDER: Final[tuple[str, ...]] = ("ready", "stale", "missing", "null", "not_set")


def _kb_index_bucket_key(line: dict[str, Any]) -> str:
    if "kb_index_status" not in line:
        return "not_set"
    raw = line.get("kb_index_status")
    if raw is None:
        return "null"
    status = str(raw).strip().lower()
    if status in {"ready", "stale", "missing"}:
        return status
    return "not_set"


def compute_index_context_breakdown(paths: list[Path]) -> dict[str, Any]:
    """
    Bucket eval_export lines by ``kb_index_status`` for report observability.

    Rows without the field use bucket ``not_set``; explicit JSON null uses ``null``.
    """
    buckets: dict[str, dict[str, int]] = {
        key: {"sample_count": 0, "needs_review_count": 0, "pass_count": 0}
        for key in _KB_INDEX_BUCKET_ORDER
    }
    rows_with_field = 0

    for path in paths:
        if not path.exists():
            continue
        for line, _, _ in iter_export_lines(path):
            bucket = _kb_index_bucket_key(line)
            if bucket not in buckets:
                buckets[bucket] = {"sample_count": 0, "needs_review_count": 0, "pass_count": 0}
            if "kb_index_status" in line:
                rows_with_field += 1
            buckets[bucket]["sample_count"] += 1
            gate_result = line.get("gate_result")
            if gate_result == "needs_review":
                buckets[bucket]["needs_review_count"] += 1
            elif gate_result == "pass":
                buckets[bucket]["pass_count"] += 1

    breakdown: list[dict[str, Any]] = []
    for key in _KB_INDEX_BUCKET_ORDER:
        row = buckets.get(key)
        if not row or row["sample_count"] == 0:
            continue
        total = row["sample_count"]
        needs = row["needs_review_count"]
        breakdown.append(
            {
                "kb_index_status": None if key == "null" else key,
                "sample_count": total,
                "needs_review_count": needs,
                "needs_review_ratio": round(needs / total, 4) if total else 0.0,
                "pass_count": row["pass_count"],
            }
        )

    return {
        "buckets": breakdown,
        "rows_with_kb_index_status": rows_with_field,
        "observability_only": True,
        "note": "Index context is observability-only; does not affect eval_gate or selector hook.",
    }


def build_stats_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Flat summary dict for automation (CI, eval_report, JSON consumers)."""
    stats = result.get("stats") or {}
    overall = stats.get("overall") or {}
    rec = result.get("recommendations") or {}
    ratio_rec = rec.get("max_needs_review_ratio") or {}
    suggested_cli = rec.get("suggested_cli") or {}

    fail_tags = [
        item["tag"]
        for item in (rec.get("fail_on_tags") or [])
        if isinstance(item, dict) and item.get("action") == "fail" and item.get("tag")
    ]

    return {
        "ok": bool(result.get("ok")),
        "message": result.get("message", ""),
        "sample_count": int(overall.get("total", 0)),
        "needs_review_count": int(overall.get("needs_review_count", 0)),
        "needs_review_ratio": float(overall.get("needs_review_ratio", 0.0)),
        "tag_counts": dict(overall.get("tag_counts") or {}),
        "suggested_thresholds": {
            "max_needs_review_ratio_range": ratio_rec.get("suggested_range"),
            "max_needs_review_ratio_observed": ratio_rec.get("observed"),
            "fail_on_tags": fail_tags,
            "confidence": rec.get("confidence"),
            "suggested_cli": suggested_cli,
        },
        "analyzed_at": stats.get("analyzed_at"),
        "input_files": list(stats.get("input_files") or []),
    }


def format_text_report(result: dict[str, Any]) -> str:
    """Human-readable table for pasting into battle reports."""
    lines: list[str] = []
    lines.append(f"ok: {result.get('ok')}")
    lines.append(f"message: {result.get('message')}")
    stats = result.get("stats") or {}
    overall = stats.get("overall") or {}
    total = overall.get("total", 0)
    lines.append("")
    lines.append("=== Overall ===")
    lines.append(f"N={total}  needs_review={overall.get('needs_review_count', 0)}  "
                 f"ratio={overall.get('needs_review_ratio', 0):.2%}")
    lines.append(f"pass={overall.get('pass_count', 0)}  rows_with_tags={overall.get('rows_with_tags', 0)}")

    tag_counts = overall.get("tag_counts") or {}
    if tag_counts:
        lines.append("")
        lines.append("=== Tags (row-level appearances) ===")
        for tag, count in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0])):
            rate = overall.get("tag_rates", {}).get(tag, 0)
            lines.append(f"  {tag}: {count} ({rate:.2%} of N)")
    else:
        lines.append("")
        lines.append("=== Tags ===")
        lines.append("  (none)")

    groups = stats.get("groups") or {}
    if groups:
        lines.append("")
        lines.append("=== Groups ===")
        for key, bucket in groups.items():
            lines.append(
                f"  [{key}] N={bucket.get('total')} needs_review={bucket.get('needs_review_ratio', 0):.2%}"
            )

    rec = result.get("recommendations") or {}
    ratio_rec = rec.get("max_needs_review_ratio")
    if ratio_rec:
        lines.append("")
        lines.append("=== CI: max-needs-review-ratio ===")
        sr = ratio_rec.get("suggested_range")
        if sr:
            lines.append(f"  suggested range: {sr[0]:.2f} – {sr[1]:.2f}")
        lines.append(f"  observed: {ratio_rec.get('observed', 0):.2%}")
    for note in rec.get("notes") or []:
        lines.append(f"  note: {note}")

    fail_tags = rec.get("fail_on_tags") or []
    if fail_tags:
        lines.append("")
        lines.append("=== CI: fail-on-tags ===")
        for item in fail_tags:
            lines.append(f"  {item.get('tag')}: {item.get('action')} — {item.get('reason')}")

    warn_tags = rec.get("warn_tags") or []
    if warn_tags:
        lines.append("")
        lines.append("=== CI: monitor / warn ===")
        for item in warn_tags:
            lines.append(f"  {item.get('tag')}: {item.get('action')} — {item.get('reason')}")

    cli = rec.get("suggested_cli") or {}
    if cli:
        lines.append("")
        lines.append("=== Suggested CLI (provisional) ===")
        fot = cli.get("fail_on_tags") or []
        fot_s = ",".join(fot) if fot else "(none)"
        lines.append(
            f"  --max-needs-review-ratio {cli.get('max_needs_review_ratio')} "
            f"--fail-on-tags {fot_s}"
        )

    warnings = stats.get("schema_warnings") or []
    if warnings:
        lines.append("")
        lines.append("=== Schema warnings ===")
        for w in warnings[:10]:
            lines.append(f"  {w}")

    return "\n".join(lines)


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze eval_export/v1 JSONL distribution and suggest CI thresholds.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="One or more eval_export/v1 .jsonl files",
    )
    parser.add_argument(
        "--group-by",
        choices=("none", "date", "exported_date", "file"),
        default="none",
        help="Optional bucket key (default: none)",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=DEFAULT_MIN_SAMPLES_FOR_RECOMMENDATIONS,
        help=(
            "Minimum N for high-confidence recommendations "
            f"(default: {DEFAULT_MIN_SAMPLES_FOR_RECOMMENDATIONS})"
        ),
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="stdout format (default: json)",
    )
    parser.add_argument(
        "--write-report",
        type=Path,
        default=None,
        help="Optional path to write a markdown summary (append-style section)",
    )
    return parser


def _markdown_summary(result: dict[str, Any]) -> str:
    """Short markdown block for eval_stats_report.md."""
    stats = result.get("stats") or {}
    overall = stats.get("overall") or {}
    rec = result.get("recommendations") or {}
    ratio_rec = rec.get("max_needs_review_ratio") or {}
    sr = ratio_rec.get("suggested_range") or ["?", "?"]
    lines = [
        f"<!-- generated {stats.get('analyzed_at', '')} -->",
        "",
        f"- **Samples**: N={overall.get('total', 0)} from `{', '.join(stats.get('input_files') or [])}`",
        f"- **needs_review**: {overall.get('needs_review_count', 0)} "
        f"({overall.get('needs_review_ratio', 0):.2%})",
        f"- **Confidence**: {rec.get('confidence', 'n/a')}",
        f"- **Suggested max-needs-review-ratio**: {sr[0]:.2f}–{sr[1]:.2f}",
        f"- **Suggested fail-on-tags**: "
        f"{', '.join(rec.get('suggested_cli', {}).get('fail_on_tags') or []) or '(none)'}",
        "",
        "```text",
        format_text_report(result),
        "```",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _build_cli().parse_args(argv)
    result = analyze_export_files(
        args.paths,
        group_by=args.group_by,
        min_samples_for_recommendations=args.min_samples,
    )

    if args.format == "text":
        print(format_text_report(result))
    else:
        summary = build_stats_summary(result)
        payload = {**summary, "stats": result.get("stats"), "recommendations": result.get("recommendations")}
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.write_report is not None:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        header = f"\n## Analysis run ({result.get('stats', {}).get('analyzed_at', '')})\n\n"
        args.write_report.write_text(
            header + _markdown_summary(result),
            encoding="utf-8",
        )

    # Exit 0 when analysis ran; exit 1 only on hard read/parse failure or zero rows.
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
