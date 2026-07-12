"""
Wave B P3 — Gate / Index / Trace one-page status summary CLI.

Assembles existing eval_report, index_status, and eval_trace_correlate
artifacts into a single Markdown + JSON overview (read-only; no gate logic).

Usage::

    python -m observability.wf_status_summary \\
        --eval tests/fixtures/eval/eval_export_sample.jsonl \\
        --index-status workflow_v2/20_pilot/W3-B/index_status_W2-1.json \\
        --trace-jsonl tests/fixtures/trace/sample_traces.jsonl \\
        --out-dir artifacts/wf
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

from observability.eval_report import build_report_summary
from observability.eval_stats import analyze_export_files
from observability.eval_trace_correlate import correlate_exports

WF_STATUS_JSON_NAME: Final[str] = "wf_status_summary.latest.json"
WF_STATUS_MD_NAME: Final[str] = "wf_status_summary.latest.md"

DEFAULT_EVAL_EXPORT: Final[Path] = Path("tests/fixtures/eval/eval_export_sample.jsonl")
DEFAULT_TRACE_JSONL: Final[Path] = Path("tests/fixtures/trace/sample_traces.jsonl")
DEFAULT_INDEX_STATUS: Final[Path] = Path("workflow_v2/20_pilot/W3-B/index_status_W2-1.json")
DEFAULT_CASE_MD: Final[Path] = Path("workflow_v2/20_pilot/W2-1_case/W2-1_case.md")
DEFAULT_OUT_DIR: Final[Path] = Path("artifacts/wf")

_CASE_FIELD_RE: Final[re.Pattern[str]] = re.compile(
    r"\*\*`(?P<key>kb_index_status|kb_index_job_id)`\*\*\s*\|\s*`(?P<value>[^`]+)`"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_case_kb_fields(case_md: Path) -> dict[str, str]:
    """Extract kb_index_status / kb_index_job_id from case front-matter table."""
    if not case_md.is_file():
        return {}
    fields: dict[str, str] = {}
    for match in _CASE_FIELD_RE.finditer(case_md.read_text(encoding="utf-8")):
        fields[match.group("key")] = match.group("value").strip()
    return fields


def _fields_from_status_fallback(status: dict[str, Any], *, status_rel: str) -> str | None:
    try:
        from workflow_v2.kb.repo_index_bootstrap import fields_from_status

        mapped = fields_from_status(status, status_rel=status_rel)
        if mapped.get("ok"):
            fields = mapped.get("fields") or {}
            value = fields.get("kb_index_status")
            return str(value) if value else None
    except Exception:
        return None
    return None


def load_index_case(
    status_path: Path,
    *,
    case_md: Path | None = None,
) -> dict[str, Any]:
    """Build one index_cases row from index_status JSON and optional case markdown."""
    if not status_path.is_file():
        return {
            "case_id": "unknown",
            "kb_index_status": "unknown",
            "job_id": None,
            "file_count": None,
            "chunk_count": None,
            "last_updated": None,
            "index_file_status": "missing",
            "source": status_path.as_posix(),
        }

    status = json.loads(status_path.read_text(encoding="utf-8"))
    if not isinstance(status, dict):
        return {
            "case_id": "unknown",
            "kb_index_status": "unknown",
            "job_id": None,
            "file_count": None,
            "chunk_count": None,
            "last_updated": None,
            "index_file_status": "invalid",
            "source": status_path.as_posix(),
        }

    result_summary = status.get("result_summary") if isinstance(status.get("result_summary"), dict) else {}
    case_id = str(status.get("case_id") or "unknown")
    job_id = status.get("job_id")
    kb_index_status = "unknown"

    if case_md is not None:
        case_fields = parse_case_kb_fields(case_md)
        if case_fields.get("kb_index_status"):
            kb_index_status = case_fields["kb_index_status"]
        if case_fields.get("kb_index_job_id"):
            job_id = case_fields["kb_index_job_id"]

    if kb_index_status == "unknown":
        mapped = _fields_from_status_fallback(status, status_rel=status_path.as_posix())
        if mapped:
            kb_index_status = mapped

    return {
        "case_id": case_id,
        "kb_index_status": kb_index_status,
        "job_id": job_id,
        "file_count": result_summary.get("file_count"),
        "chunk_count": result_summary.get("chunk_count"),
        "last_updated": status.get("last_updated"),
        "index_file_status": "ok",
        "source": status_path.as_posix(),
    }


def build_gate_block(eval_path: Path, *, min_samples: int = 1) -> dict[str, Any]:
    """Reuse eval_report / eval_stats for gate health summary."""
    if not eval_path.is_file():
        return {
            "ok": False,
            "message": f"eval export not found: {eval_path.as_posix()}",
            "sample_count": 0,
            "needs_review_count": 0,
            "needs_review_ratio": 0.0,
            "tag_counts": {},
            "top_tags": [],
            "suggested_thresholds": {},
            "suggested_cli": {},
            "reproduce_command": "",
            "input_files": [eval_path.as_posix()],
        }

    analysis = analyze_export_files([eval_path], min_samples_for_recommendations=min_samples)
    return build_report_summary(analysis, export_paths=[eval_path])


def build_trace_join_stats(eval_path: Path, trace_path: Path | None) -> dict[str, Any]:
    """Summary-level trace join stats for flagged eval rows (no per-row detail)."""
    if trace_path is None or not trace_path.is_file():
        return {
            "row_count": 0,
            "trace_found_count": 0,
            "hit_rate": "n/a",
            "status": "skipped",
            "message": (
                f"trace file not found: {trace_path.as_posix()}"
                if trace_path is not None
                else "trace file not provided"
            ),
        }

    result = correlate_exports(eval_path, trace_path, only_flagged=True)
    if not result.get("ok"):
        return {
            "row_count": 0,
            "trace_found_count": 0,
            "hit_rate": "n/a",
            "status": "skipped",
            "message": result.get("message", "trace join skipped"),
        }

    row_count = int(result.get("row_count") or 0)
    found = int(result.get("trace_found_count") or 0)
    if row_count == 0:
        hit_rate: float | str = "n/a"
    else:
        hit_rate = round(found / row_count, 4)

    return {
        "row_count": row_count,
        "trace_found_count": found,
        "hit_rate": hit_rate,
        "status": "ok",
        "message": result.get("message", ""),
    }


def build_wf_status_summary(
    *,
    eval_path: Path,
    index_status_paths: list[Path],
    trace_path: Path | None = None,
    case_md: Path | None = None,
    min_samples: int = 1,
) -> dict[str, Any]:
    """Assemble stable summary dict for JSON/Markdown consumers."""
    gate = build_gate_block(eval_path, min_samples=min_samples)
    index_cases = [load_index_case(path, case_md=case_md) for path in index_status_paths]
    trace_join_stats = build_trace_join_stats(eval_path, trace_path)

    ok = eval_path.is_file()
    message = "wf status summary assembled" if ok else gate.get("message", "eval export missing")

    return {
        "ok": ok,
        "message": message,
        "gate": gate,
        "index_cases": index_cases,
        "trace_join_stats": trace_join_stats,
        "generated_at": _utc_now_iso(),
        "inputs": {
            "eval_export": eval_path.as_posix(),
            "trace_jsonl": trace_path.as_posix() if trace_path else None,
            "index_status": [p.as_posix() for p in index_status_paths],
            "case_md": case_md.as_posix() if case_md else None,
        },
    }


def format_markdown_report(summary: dict[str, Any]) -> str:
    """One-page Markdown answering gate health, index readiness, and trace join rate."""
    gate = summary.get("gate") or {}
    trace_stats = summary.get("trace_join_stats") or {}
    index_cases = summary.get("index_cases") or []
    inputs = summary.get("inputs") or {}

    eval_path = inputs.get("eval_export") or "<eval.jsonl>"
    trace_path = inputs.get("trace_jsonl") or "<trace.jsonl>"

    ratio = float(gate.get("needs_review_ratio") or 0.0)
    top_tags = gate.get("top_tags") or []
    tag_lines = "\n".join(f"| `{t['tag']}` | {t['count']} |" for t in top_tags) or "| *(none)* | 0 |"

    index_lines = "\n".join(
        f"| {row.get('case_id')} | {row.get('kb_index_status')} | "
        f"{row.get('job_id') or '—'} | {row.get('file_count', '—')} | "
        f"{row.get('chunk_count', '—')} | {row.get('last_updated') or '—'} |"
        for row in index_cases
    ) or "| — | unknown | — | — | — | — |"

    hit_rate = trace_stats.get("hit_rate")
    if isinstance(hit_rate, (int, float)):
        hit_rate_text = f"{hit_rate:.1%}" if hit_rate <= 1 else str(hit_rate)
    else:
        hit_rate_text = str(hit_rate)

    st = gate.get("suggested_thresholds") or {}
    confidence = st.get("confidence", "n/a")

    lines = [
        "# WF status summary (Gate / Index / Trace)",
        "",
        f"> Generated: `{summary.get('generated_at', '')}`",
        "",
        "## 1. Gate health",
        "",
        f"- **Samples (N)**: {gate.get('sample_count', 0)}",
        f"- **needs_review**: {gate.get('needs_review_count', 0)} ({ratio:.1%})",
        f"- **Confidence**: {confidence}",
        "",
        "### Top tags",
        "",
        "| Tag | Count |",
        "|-----|-------|",
        tag_lines,
        "",
        "## 2. Index readiness",
        "",
        "| case_id | kb_index_status | job_id | file_count | chunk_count | last_updated |",
        "|---------|-----------------|--------|------------|-------------|--------------|",
        index_lines,
        "",
        "## 3. Trace join (flagged rows)",
        "",
        f"- **Status**: {trace_stats.get('status', 'n/a')}",
        f"- **Flagged rows**: {trace_stats.get('row_count', 0)}",
        f"- **Trace hits**: {trace_stats.get('trace_found_count', 0)}",
        f"- **Hit rate**: {hit_rate_text}",
        "",
        "## Reviewer shortcuts",
        "",
        "```bash",
        f"python -m observability.eval_trace_correlate --eval {eval_path} --trace {trace_path} --format markdown",
        f"python -m observability.trace_query --file {trace_path} --trace-id <id> --format json",
        "```",
        "",
    ]
    return "\n".join(lines)


def write_wf_status_summary(
    *,
    eval_path: Path,
    index_status_paths: list[Path],
    out_dir: Path,
    trace_path: Path | None = None,
    case_md: Path | None = None,
    min_samples: int = 1,
) -> dict[str, Any]:
    """Write ``wf_status_summary.latest.{json,md}`` and return CLI result dict."""
    summary = build_wf_status_summary(
        eval_path=eval_path,
        index_status_paths=index_status_paths,
        trace_path=trace_path,
        case_md=case_md,
        min_samples=min_samples,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / WF_STATUS_JSON_NAME
    md_path = out_dir / WF_STATUS_MD_NAME

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown_report(summary), encoding="utf-8")

    return {
        "ok": summary["ok"],
        "message": summary.get("message", ""),
        "json_path": str(json_path),
        "md_path": str(md_path),
        "gate": summary.get("gate"),
        "index_cases": summary.get("index_cases"),
        "trace_join_stats": summary.get("trace_join_stats"),
        "generated_at": summary.get("generated_at"),
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Gate / Index / Trace one-page WF status summary"
    )
    parser.add_argument(
        "--eval",
        "--eval-export",
        dest="eval_export",
        type=Path,
        default=DEFAULT_EVAL_EXPORT,
        help="eval_export/v1 JSONL (default: tests/fixtures/eval/eval_export_sample.jsonl)",
    )
    parser.add_argument(
        "--trace-jsonl",
        type=Path,
        default=DEFAULT_TRACE_JSONL,
        help="gov-trace-v2 JSONL (default: tests/fixtures/trace/sample_traces.jsonl)",
    )
    parser.add_argument(
        "--index-status",
        action="append",
        type=Path,
        default=None,
        help="index_status JSON (repeatable; default: workflow_v2/20_pilot/W3-B/index_status_W2-1.json)",
    )
    parser.add_argument(
        "--case-md",
        type=Path,
        default=DEFAULT_CASE_MD,
        help="Optional case markdown for kb_index_status front-matter",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory (default: artifacts/wf)",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=1,
        help="Minimum samples for gate threshold recommendations (default: 1)",
    )
    parser.add_argument(
        "--no-trace",
        action="store_true",
        help="Skip trace join stats (soft degrade)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    index_paths = args.index_status if args.index_status else [DEFAULT_INDEX_STATUS]
    trace_path = None if args.no_trace else args.trace_jsonl
    case_md = args.case_md if args.case_md.is_file() else None

    result = write_wf_status_summary(
        eval_path=args.eval_export,
        index_status_paths=index_paths,
        out_dir=args.out_dir,
        trace_path=trace_path,
        case_md=case_md,
        min_samples=args.min_samples,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
