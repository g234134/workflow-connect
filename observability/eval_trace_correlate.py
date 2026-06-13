"""
Join eval_export/v1 rows with gov-trace-v2 JSONL for ops triage.

Correlates flagged eval rows (``needs_review`` or fail-on-tags) to local trace
events so reviewers can see trace summaries without copy-pasting IDs into
``trace_query``.

Join key priority (documented in ``observability/eval_export.md``):
``trace_id`` > ``task_id`` > ``session_id``.

Usage::

    python -m observability.eval_trace_correlate \\
        --eval tests/fixtures/eval/eval_export_sample.jsonl \\
        --trace tests/fixtures/trace/sample_traces.jsonl \\
        --format json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Iterator, Literal

from observability.eval_stats import iter_export_lines
from observability.trace_query import _build_summary, iter_trace_events
from observability.trace_schema import trace_completeness_score

DEFAULT_FAIL_ON_TAGS: Final[frozenset[str]] = frozenset({"infra_risk"})
JOIN_KEY_ORDER: Final[tuple[str, ...]] = ("trace_id", "task_id", "session_id")

OutputFormat = Literal["json", "jsonl", "markdown", "triage-md"]


def extract_kb_index_status_from_eval_row(row: dict[str, Any]) -> str:
    """Resolve kb_index_status from eval export row; ``unknown`` when absent."""
    raw = row.get("kb_index_status")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    source_ref = row.get("source_ref")
    if isinstance(source_ref, dict):
        ref_status = source_ref.get("kb_index_status")
        if ref_status is not None and str(ref_status).strip():
            return str(ref_status).strip()
    sidecar = row.get("trace_metadata_sidecar")
    if isinstance(sidecar, dict):
        side_status = sidecar.get("kb_index_status")
        if side_status is not None and str(side_status).strip():
            return str(side_status).strip()
    return "unknown"


def is_needs_review_row(row: dict[str, Any]) -> bool:
    return row.get("gate_result") == "needs_review"


def build_triage_object(row: dict[str, Any]) -> dict[str, Any]:
    """Stable triage sidecar for correlate JSON/JSONL output."""
    reasons = list(row.get("reasons") or [])
    tags = list(row.get("tags") or [])
    if reasons:
        why_flagged = "; ".join(str(r) for r in reasons)
    elif tags:
        why_flagged = ", ".join(str(t) for t in tags)
    else:
        why_flagged = str(row.get("gate_result") or "needs_review")

    return {
        "why_flagged": why_flagged,
        "primary_tags": tags[:3] if len(tags) > 3 else tags,
        "trace_ref": {
            "join_key": row.get("join_key"),
            "join_value": row.get("join_value"),
            "trace_found": row.get("trace_found"),
        },
        "kb_index_status": extract_kb_index_status_from_eval_row(row),
    }


def _normalize_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def extract_join_keys(row: dict[str, Any]) -> dict[str, str | None]:
    """Return join candidates from an eval_export row (incl. ``source_ref``)."""
    source_ref = row.get("source_ref") if isinstance(row.get("source_ref"), dict) else {}
    return {
        "trace_id": _normalize_id(row.get("trace_id") or source_ref.get("trace_id")),
        "task_id": _normalize_id(row.get("task_id") or source_ref.get("task_id")),
        "session_id": _normalize_id(row.get("session_id") or source_ref.get("session_id")),
    }


def is_flagged_row(
    row: dict[str, Any],
    *,
    fail_on_tags: frozenset[str] = DEFAULT_FAIL_ON_TAGS,
) -> bool:
    if row.get("gate_result") == "needs_review":
        return True
    tags = row.get("tags")
    if not isinstance(tags, list):
        return False
    tag_set = {str(t) for t in tags if t}
    return bool(tag_set & fail_on_tags)


def _event_sort_key(event: dict[str, Any]) -> tuple[str, int]:
    return (str(event.get("timestamp") or ""), int(event.get("_source_line") or 0))


def _compact_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event": event.get("event"),
        "timestamp": event.get("timestamp"),
        "trace_id": event.get("trace_id"),
        "task_id": event.get("task_id"),
        "session_id": event.get("session_id"),
        "status": event.get("status"),
        "error_type": event.get("error_type"),
        "agent_name": event.get("agent_name"),
        "workflow_name": event.get("workflow_name"),
        "tool_name": event.get("tool_name"),
    }


def _trace_completeness_from_events(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not events:
        return None
    for evt in reversed(sorted(events, key=_event_sort_key)):
        if evt.get("event") == "trace_end":
            return trace_completeness_score(evt)
    return trace_completeness_score(events[-1])


def build_trace_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize matched gov-trace-v2 events for correlate output."""
    ordered = sorted(events, key=_event_sort_key)
    summary = _build_summary(ordered)
    return {
        "event_count": len(ordered),
        "event_counts": summary.get("event_counts") or {},
        "first_event": _compact_event(ordered[0]) if ordered else None,
        "last_event": _compact_event(ordered[-1]) if ordered else None,
        "first_timestamp": summary.get("first_timestamp"),
        "last_timestamp": summary.get("last_timestamp"),
        "trace_ids": summary.get("trace_ids") or [],
        "task_ids": summary.get("task_ids") or [],
        "trace_completeness": _trace_completeness_from_events(ordered),
    }


def build_trace_index(path: Path) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """
    Index trace events by ``trace_id``, ``task_id``, and ``session_id``.

    Uses ``iter_trace_events`` from ``trace_query`` (single JSONL pass).
    """
    index: dict[str, dict[str, list[dict[str, Any]]]] = {
        key: {} for key in JOIN_KEY_ORDER
    }
    for event, line_no in iter_trace_events(path):
        row = dict(event)
        row["_source_line"] = line_no
        for key in JOIN_KEY_ORDER:
            value = _normalize_id(event.get(key))
            if value:
                index[key].setdefault(value, []).append(row)
    return index


def lookup_trace_events(
    index: dict[str, dict[str, list[dict[str, Any]]]],
    keys: dict[str, str | None],
) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    """
    Resolve trace events using join priority: trace_id > task_id > session_id.
    """
    for key in JOIN_KEY_ORDER:
        value = keys.get(key)
        if not value:
            continue
        events = index.get(key, {}).get(value) or []
        if events:
            return key, value, list(events)
    return None, None, []


def correlate_eval_row(
    row: dict[str, Any],
    *,
    index: dict[str, dict[str, list[dict[str, Any]]]],
    eval_line_index: int,
) -> dict[str, Any]:
    keys = extract_join_keys(row)
    join_key, join_value, events = lookup_trace_events(index, keys)
    trace_found = bool(events)

    if trace_found:
        message = f"matched {len(events)} trace event(s) via {join_key}={join_value}"
    else:
        attempted = [f"{k}={v}" for k, v in keys.items() if v]
        if attempted:
            message = f"no trace events for join keys ({', '.join(attempted)})"
        else:
            message = "no join keys on eval row"

    return {
        "eval_line_index": eval_line_index,
        "trace_id": keys.get("trace_id"),
        "task_id": keys.get("task_id"),
        "session_id": keys.get("session_id"),
        "gate_result": row.get("gate_result"),
        "tags": list(row.get("tags") or []),
        "reasons": list(row.get("reasons") or []),
        "metrics": dict(row.get("metrics") or {}),
        "kb_index_status": extract_kb_index_status_from_eval_row(row),
        "join_key": join_key,
        "join_value": join_value,
        "trace_found": trace_found,
        "message": message,
        "trace_summary": build_trace_summary(events) if trace_found else None,
    }


def _finalize_correlate_row(row: dict[str, Any]) -> dict[str, Any]:
    """Attach stable ``triage`` sub-object to a correlate row."""
    finalized = dict(row)
    finalized["triage"] = build_triage_object(finalized)
    return finalized


def correlate_exports(
    eval_path: Path,
    trace_path: Path,
    *,
    only_flagged: bool = True,
    only_needs_review: bool = True,
    fail_on_tags: frozenset[str] = DEFAULT_FAIL_ON_TAGS,
) -> dict[str, Any]:
    try:
        trace_index = build_trace_index(trace_path)
    except FileNotFoundError:
        return {
            "ok": False,
            "message": f"trace file not found: {trace_path.as_posix()}",
            "rows": [],
            "eval_file": eval_path.as_posix(),
            "trace_file": trace_path.as_posix(),
            "only_flagged": only_flagged,
            "only_needs_review": only_needs_review,
            "fail_on_tags": sorted(fail_on_tags),
        }
    except ValueError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "rows": [],
            "eval_file": eval_path.as_posix(),
            "trace_file": trace_path.as_posix(),
            "only_flagged": only_flagged,
            "only_needs_review": only_needs_review,
            "fail_on_tags": sorted(fail_on_tags),
        }

    correlated: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        for row, line_no, _source in iter_export_lines(eval_path):
            if only_needs_review:
                if not is_needs_review_row(row):
                    continue
            elif only_flagged and not is_flagged_row(row, fail_on_tags=fail_on_tags):
                continue
            correlated.append(
                _finalize_correlate_row(
                    correlate_eval_row(row, index=trace_index, eval_line_index=line_no)
                )
            )
    except (FileNotFoundError, ValueError) as exc:
        return {
            "ok": False,
            "message": str(exc),
            "rows": [],
            "eval_file": eval_path.as_posix(),
            "trace_file": trace_path.as_posix(),
            "only_flagged": only_flagged,
            "only_needs_review": only_needs_review,
            "fail_on_tags": sorted(fail_on_tags),
        }

    found = sum(1 for r in correlated if r.get("trace_found"))
    total = len(correlated)
    if total == 0:
        msg = "no eval rows selected (check --only-flagged / input file)"
    else:
        msg = f"correlated {total} eval row(s); trace_found={found}"

    return {
        "ok": True,
        "message": msg,
        "rows": correlated,
        "row_count": total,
        "trace_found_count": found,
        "eval_file": eval_path.as_posix(),
        "trace_file": trace_path.as_posix(),
        "only_flagged": only_flagged,
        "only_needs_review": only_needs_review,
        "fail_on_tags": sorted(fail_on_tags),
        "join_key_priority": list(JOIN_KEY_ORDER),
        "warnings": warnings,
    }


def _top_event_types(trace_summary: dict[str, Any] | None, *, limit: int = 5) -> str:
    if not trace_summary:
        return "—"
    counts = trace_summary.get("event_counts") or {}
    if not counts:
        return "—"
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{name}×{count}" for name, count in ordered[:limit])


def format_triage_markdown_row(row: dict[str, Any]) -> str:
    """One flagged eval row as a fixed triage block."""
    lines = [
        f"## eval line {row.get('eval_line_index')} · {row.get('task_id') or '—'}",
        "",
        f"- **gate_result**: `{row.get('gate_result')}`",
        f"- **tags**: {', '.join(row.get('tags') or []) or '—'}",
        f"- **reasons**: {', '.join(row.get('reasons') or []) or '—'}",
        f"- **kb_index_status**: `{row.get('kb_index_status', 'unknown')}`",
    ]
    join_key = row.get("join_key")
    join_value = row.get("join_value")
    if join_key and join_value:
        lines.append(f"- **join**: `{join_key}={join_value}`")
    else:
        lines.append("- **join**: —")

    summary = row.get("trace_summary")
    if summary:
        tc = summary.get("trace_completeness") or {}
        score = tc.get("score") if isinstance(tc, dict) else None
        lines.extend(
            [
                f"- **trace events**: {summary.get('event_count', 0)}",
                f"- **event types**: {_top_event_types(summary)}",
                f"- **trace_completeness**: {score if score is not None else '—'}",
            ]
        )
        if summary.get("first_timestamp") and summary.get("last_timestamp"):
            lines.append(
                f"- **span**: {summary['first_timestamp']} → {summary['last_timestamp']}"
            )
    else:
        lines.append(f"- **trace**: not found ({row.get('message', '—')})")

    triage = row.get("triage") or build_triage_object(row)
    lines.append(f"- **why_flagged**: {triage.get('why_flagged', '—')}")
    lines.append("")
    return "\n".join(lines)


def format_triage_markdown(result: dict[str, Any]) -> str:
    """Reviewer one-page triage view for flagged eval rows."""
    header = [
        "# eval flagged triage",
        "",
        f"- **ok**: {result.get('ok')}",
        f"- **message**: {result.get('message')}",
        f"- **eval**: `{result.get('eval_file')}`",
        f"- **trace**: `{result.get('trace_file')}`",
        f"- **only_needs_review**: {result.get('only_needs_review')}",
        f"- **join priority**: {' > '.join(result.get('join_key_priority') or JOIN_KEY_ORDER)}",
        "",
    ]
    body: list[str] = []
    for row in result.get("rows") or []:
        body.append(format_triage_markdown_row(row))
    if not body:
        body.append("_No rows selected (check --only-needs-review / input file)._")
        body.append("")
    return "\n".join(header + body)


def format_markdown_appendix(result: dict[str, Any]) -> str:
    lines = [
        "# eval / trace correlate appendix",
        "",
        f"- **ok**: {result.get('ok')}",
        f"- **message**: {result.get('message')}",
        f"- **eval**: `{result.get('eval_file')}`",
        f"- **trace**: `{result.get('trace_file')}`",
        f"- **only_flagged**: {result.get('only_flagged')}",
        f"- **join priority**: {' > '.join(result.get('join_key_priority') or JOIN_KEY_ORDER)}",
        "",
        "| line | gate | tags | join | trace_found | events | first → last |",
        "|------|------|------|------|-------------|--------|--------------|",
    ]
    for row in result.get("rows") or []:
        summary = row.get("trace_summary") or {}
        join_text = (
            f"{row.get('join_key')}={row.get('join_value')}"
            if row.get("join_key")
            else "—"
        )
        tags = ", ".join(row.get("tags") or []) or "—"
        first_last = "—"
        if summary.get("first_timestamp") and summary.get("last_timestamp"):
            first_last = f"{summary['first_timestamp']} → {summary['last_timestamp']}"
        lines.append(
            f"| {row.get('eval_line_index')} | {row.get('gate_result')} | {tags} | "
            f"{join_text} | {row.get('trace_found')} | {summary.get('event_count', 0)} | "
            f"{first_last} |"
        )
    lines.append("")
    for row in result.get("rows") or []:
        lines.append(f"## eval line {row.get('eval_line_index')}")
        lines.append("")
        lines.append(f"- **message**: {row.get('message')}")
        summary = row.get("trace_summary")
        if summary:
            lines.append(f"- **event_count**: {summary.get('event_count')}")
            if summary.get("first_event"):
                fe = summary["first_event"]
                lines.append(
                    f"- **first_event**: `{fe.get('event')}` @ {fe.get('timestamp')} "
                    f"status={fe.get('status')}"
                )
            if summary.get("last_event"):
                le = summary["last_event"]
                lines.append(
                    f"- **last_event**: `{le.get('event')}` @ {le.get('timestamp')} "
                    f"status={le.get('status')} error={le.get('error_type')}"
                )
            tc = summary.get("trace_completeness")
            if isinstance(tc, dict) and tc.get("score") is not None:
                lines.append(f"- **trace_completeness.score**: {tc.get('score')}")
        lines.append("")
    return "\n".join(lines)


def iter_correlated_jsonl(result: dict[str, Any]) -> Iterator[str]:
    for row in result.get("rows") or []:
        yield json.dumps(row, ensure_ascii=False)


def _parse_fail_on_tags(raw: str) -> frozenset[str]:
    if not raw.strip():
        return frozenset()
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Correlate eval_export/v1 rows with gov-trace-v2 JSONL"
    )
    parser.add_argument("--eval", type=Path, required=True, help="eval_export/v1 JSONL")
    parser.add_argument("--trace", type=Path, required=True, help="gov-trace-v2 JSONL")
    parser.add_argument(
        "--format",
        choices=("json", "jsonl", "markdown", "triage-md"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--only-needs-review",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Process only gate_result=needs_review rows (default: true; overrides tag-only flagged)",
    )
    parser.add_argument(
        "--only-flagged",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="When --no-only-needs-review: needs_review or fail-on-tags rows (default: true)",
    )
    parser.add_argument(
        "--fail-on-tags",
        default="infra_risk",
        help="Comma-separated tags that count as flagged (default: infra_risk)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write output to file (stdout when omitted)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    fail_on_tags = _parse_fail_on_tags(args.fail_on_tags) or DEFAULT_FAIL_ON_TAGS
    result = correlate_exports(
        args.eval,
        args.trace,
        only_flagged=args.only_flagged,
        only_needs_review=args.only_needs_review,
        fail_on_tags=fail_on_tags,
    )

    if args.format == "json":
        payload = json.dumps(result, ensure_ascii=False, indent=2)
    elif args.format == "jsonl":
        payload = "\n".join(iter_correlated_jsonl(result))
        if payload:
            payload += "\n"
    elif args.format == "triage-md":
        payload = format_triage_markdown(result)
    else:
        payload = format_markdown_appendix(result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="" if args.format == "jsonl" and not payload else "\n")

    if not result.get("ok"):
        return 1
    if not result.get("rows"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
