"""
Wave B eval gate report bootstrap — export JSONL → Markdown + JSON summary.

Wraps ``observability.eval_stats.analyze_export_files`` with stable report
artifacts for CI upload and local inspection.

Usage::

    python -m observability.eval_report artifacts/eval/eval_export_v1_shadow_nightly.latest.jsonl
    python -m observability.eval_report path/to.jsonl --out-dir artifacts/eval
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final

from observability.eval_stats import analyze_export_files, format_text_report

REPORT_JSON_NAME: Final[str] = "eval_report.latest.json"
REPORT_MD_NAME: Final[str] = "eval_report.latest.md"


def build_report_summary(analysis: dict[str, Any]) -> dict[str, Any]:
    """Stable summary dict for automation and CI artifact consumers."""
    stats = analysis.get("stats") or {}
    overall = stats.get("overall") or {}
    rec = analysis.get("recommendations") or {}
    ratio_rec = rec.get("max_needs_review_ratio") or {}
    suggested_cli = rec.get("suggested_cli") or {}

    fail_tags = [
        item["tag"]
        for item in (rec.get("fail_on_tags") or [])
        if isinstance(item, dict) and item.get("action") == "fail" and item.get("tag")
    ]

    tag_counts = dict(overall.get("tag_counts") or {})
    top_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))[:10]

    return {
        "ok": bool(analysis.get("ok")),
        "message": analysis.get("message", ""),
        "sample_count": int(overall.get("total", 0)),
        "needs_review_count": int(overall.get("needs_review_count", 0)),
        "needs_review_ratio": float(overall.get("needs_review_ratio", 0.0)),
        "tag_counts": tag_counts,
        "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
        "suggested_thresholds": {
            "max_needs_review_ratio_range": ratio_rec.get("suggested_range"),
            "max_needs_review_ratio_observed": ratio_rec.get("observed"),
            "fail_on_tags": fail_tags,
            "confidence": rec.get("confidence"),
        },
        "analyzed_at": stats.get("analyzed_at"),
        "input_files": list(stats.get("input_files") or []),
        "reproduce_command": (
            "python -m observability.eval_report "
            + " ".join(f'"{p}"' for p in (stats.get("input_files") or []))
        ),
        "suggested_cli": suggested_cli,
    }


def format_markdown_report(summary: dict[str, Any], analysis: dict[str, Any]) -> str:
    """Human-readable Markdown report with reproduce block."""
    inputs = ", ".join(f"`{p}`" for p in (summary.get("input_files") or [])) or "(none)"
    top_tags = summary.get("top_tags") or []
    tag_lines = "\n".join(f"| `{t['tag']}` | {t['count']} |" for t in top_tags) or "| *(none)* | 0 |"

    ratio = summary.get("needs_review_ratio", 0.0)
    st = summary.get("suggested_thresholds") or {}
    ratio_range = st.get("max_needs_review_ratio_range")
    if isinstance(ratio_range, (list, tuple)) and len(ratio_range) == 2:
        ratio_range_text = f"{float(ratio_range[0]):.2f}–{float(ratio_range[1]):.2f}"
    else:
        ratio_range_text = "n/a"
    fail_tags = st.get("fail_on_tags") or []

    lines = [
        "# Eval gate report (Wave B bootstrap)",
        "",
        f"> Generated: `{summary.get('analyzed_at', '')}`",
        "",
        "## Executive summary",
        "",
        f"- **Samples (N)**: {summary.get('sample_count', 0)}",
        f"- **Source files**: {inputs}",
        f"- **needs_review**: {summary.get('needs_review_count', 0)} ({ratio:.1%})",
        f"- **Confidence**: {st.get('confidence', 'n/a')}",
        f"- **Suggested max-needs-review-ratio range**: {ratio_range_text}",
        f"- **Suggested fail-on-tags**: {', '.join(fail_tags) if fail_tags else '(none)'}",
        "",
        "## Tag histogram (top)",
        "",
        "| Tag | Count |",
        "|-----|-------|",
        tag_lines,
        "",
        "## Reproduce",
        "",
        "```bash",
        summary.get("reproduce_command", "python -m observability.eval_report <export.jsonl>"),
        "```",
        "",
        "## Full text stats",
        "",
        "```text",
        format_text_report(analysis),
        "```",
        "",
    ]
    return "\n".join(lines)


def write_eval_report(
    export_paths: list[Path],
    out_dir: Path,
    *,
    min_samples: int = 1,
) -> dict[str, Any]:
    """Analyze export file(s) and write ``eval_report.latest.{json,md}``."""
    analysis = analyze_export_files(export_paths, min_samples_for_recommendations=min_samples)
    summary = build_report_summary(analysis)

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON_NAME
    md_path = out_dir / REPORT_MD_NAME

    payload = {"summary": summary, "analysis": analysis}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown_report(summary, analysis), encoding="utf-8")

    return {
        "ok": summary["ok"],
        "message": "eval report written" if summary["ok"] else summary.get("message", "report failed"),
        "sample_count": summary["sample_count"],
        "needs_review_ratio": summary["needs_review_ratio"],
        "tag_counts": summary["tag_counts"],
        "suggested_thresholds": summary["suggested_thresholds"],
        "json_path": str(json_path),
        "md_path": str(md_path),
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate eval gate Markdown + JSON report")
    parser.add_argument("paths", nargs="+", type=Path, help="eval_export/v1 JSONL input(s)")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("artifacts/eval"),
        help="Output directory (default: artifacts/eval)",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=1,
        help="Minimum samples for threshold recommendations (default: 1)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = write_eval_report(args.paths, args.out_dir, min_samples=args.min_samples)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
