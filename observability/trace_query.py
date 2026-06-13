"""
Local gov-trace-v2 JSONL query CLI (Wave B bootstrap).

Read-only lookup by ``trace_id`` / ``task_id`` / ``session_id`` against a
JSONL file (default logical path: ``runtime/task_traces.jsonl``).

Usage::

    python -m observability.trace_query --file tests/fixtures/trace/sample_traces.jsonl --trace-id trace-wb-fixture-001
    python -m observability.trace_query --task-id task-wb-001 --format text
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Iterator

from observability.trace_schema import GOV_TRACE_SCHEMA_VERSION, trace_completeness_score

DEFAULT_TRACE_JSONL: Final[str] = "runtime/task_traces.jsonl"


def _parse_trace_line(raw: str, *, source: str, line_no: int) -> dict[str, Any] | None:
    text = raw.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source}:{line_no}: invalid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError(f"{source}:{line_no}: expected JSON object")
    return obj


def iter_trace_events(path: Path) -> Iterator[tuple[dict[str, Any], int]]:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    with path.open(encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            obj = _parse_trace_line(raw, source=path.name, line_no=line_no)
            if obj is not None:
                yield obj, line_no


def _event_matches(
    event: dict[str, Any],
    *,
    trace_id: str | None,
    task_id: str | None,
    session_id: str | None,
    event_name: str | None,
) -> bool:
    if event.get("trace_schema_version") != GOV_TRACE_SCHEMA_VERSION:
        return False
    if trace_id and str(event.get("trace_id", "")) != trace_id:
        return False
    if task_id and str(event.get("task_id", "")) != task_id:
        return False
    if session_id and str(event.get("session_id", "")) != session_id:
        return False
    if event_name and str(event.get("event", "")) != event_name:
        return False
    return bool(trace_id or task_id or session_id or event_name)


def _extract_kb_index_status_from_event(event: dict[str, Any]) -> str | None:
    metadata = event.get("metadata")
    if isinstance(metadata, dict):
        raw = metadata.get("kb_index_status")
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    hints = event.get("selector_hints")
    if isinstance(hints, dict):
        raw = hints.get("kb_index_status")
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    return None


def _collect_audit_tags(events: list[dict[str, Any]]) -> list[str]:
    tags: list[str] = []
    for evt in events:
        metadata = evt.get("metadata")
        if isinstance(metadata, dict):
            audit = metadata.get("audit_tags")
            if isinstance(audit, list):
                tags.extend(str(t) for t in audit if t)
        hints = evt.get("selector_hints")
        if isinstance(hints, dict):
            audit = hints.get("audit_tags")
            if isinstance(audit, list):
                tags.extend(str(t) for t in audit if t)
    return tags


def _trace_completeness_from_events(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not events:
        return None
    ordered = sorted(events, key=lambda e: str(e.get("timestamp") or ""))
    for evt in reversed(ordered):
        if evt.get("event") == "trace_end":
            return trace_completeness_score(evt)
    return trace_completeness_score(ordered[-1])


def _build_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {
            "event_counts": {},
            "trace_ids": [],
            "task_ids": [],
            "first_timestamp": None,
            "last_timestamp": None,
        }
    event_counts: dict[str, int] = {}
    trace_ids: set[str] = set()
    task_ids: set[str] = set()
    timestamps: list[str] = []
    kb_index_status: str | None = None
    for evt in events:
        name = str(evt.get("event", "unknown"))
        event_counts[name] = event_counts.get(name, 0) + 1
        if evt.get("trace_id"):
            trace_ids.add(str(evt["trace_id"]))
        if evt.get("task_id"):
            task_ids.add(str(evt["task_id"]))
        if evt.get("timestamp"):
            timestamps.append(str(evt["timestamp"]))
        status = _extract_kb_index_status_from_event(evt)
        if status:
            kb_index_status = status
    timestamps.sort()
    summary: dict[str, Any] = {
        "event_counts": event_counts,
        "trace_ids": sorted(trace_ids),
        "task_ids": sorted(task_ids),
        "first_timestamp": timestamps[0] if timestamps else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
    }
    if kb_index_status:
        summary["kb_index_status"] = kb_index_status
    return summary


def query_traces(
    path: Path,
    *,
    trace_id: str | None = None,
    task_id: str | None = None,
    session_id: str | None = None,
    event: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    if not (trace_id or task_id or session_id or event):
        return {
            "ok": False,
            "message": "at least one filter required: trace_id, task_id, session_id, or event",
            "matches": 0,
            "events": [],
            "summary": _build_summary([]),
        }

    try:
        matched: list[dict[str, Any]] = []
        for evt, line_no in iter_trace_events(path):
            if _event_matches(
                evt,
                trace_id=trace_id,
                task_id=task_id,
                session_id=session_id,
                event_name=event,
            ):
                row = dict(evt)
                row["_source_line"] = line_no
                matched.append(row)
                if len(matched) >= limit:
                    break
    except FileNotFoundError:
        return {
            "ok": False,
            "message": f"trace file not found: {path.as_posix()}",
            "matches": 0,
            "events": [],
            "summary": _build_summary([]),
        }
    except ValueError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "matches": 0,
            "events": [],
            "summary": _build_summary([]),
        }

    summary = _build_summary(matched)
    if matched:
        message = f"found {len(matched)} event(s)"
    else:
        message = "no matching trace events"

    return {
        "ok": True,
        "message": message,
        "matches": len(matched),
        "events": matched,
        "summary": summary,
        "source_file": path.as_posix(),
    }


def format_text_result(result: dict[str, Any]) -> str:
    lines = [
        f"ok={result.get('ok')} matches={result.get('matches')} — {result.get('message')}",
        f"source: {result.get('source_file', '')}",
    ]
    summary = result.get("summary") or {}
    if summary.get("event_counts"):
        lines.append(f"events: {summary['event_counts']}")
    for evt in result.get("events") or []:
        lines.append(
            f"  [{evt.get('timestamp')}] {evt.get('event')} "
            f"trace={evt.get('trace_id')} task={evt.get('task_id')} status={evt.get('status')}"
        )
    return "\n".join(lines)


def format_triage_result(result: dict[str, Any], *, audit_tag_limit: int = 5) -> str:
    """Short human-readable triage line: trace_id + completeness + recent audit_tags."""
    events = result.get("events") or []
    summary = result.get("summary") or {}
    trace_id = summary.get("trace_ids", [None])[0] if summary.get("trace_ids") else None
    if not trace_id and events:
        trace_id = events[0].get("trace_id")

    completeness = _trace_completeness_from_events(events)
    score = completeness.get("score") if isinstance(completeness, dict) else None
    audit_tags = _collect_audit_tags(events)[-audit_tag_limit:]

    lines = [
        f"trace_id={trace_id or '—'} completeness={score if score is not None else '—'}",
        f"audit_tags={', '.join(audit_tags) if audit_tags else '—'}",
        f"events={result.get('matches', 0)} ok={result.get('ok')}",
    ]
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query gov-trace-v2 JSONL (read-only)")
    parser.add_argument("--file", type=Path, default=Path(DEFAULT_TRACE_JSONL), help="JSONL trace file")
    parser.add_argument("--trace-id", default="", help="Filter by trace_id")
    parser.add_argument("--task-id", default="", help="Filter by task_id")
    parser.add_argument("--session-id", default="", help="Filter by session_id")
    parser.add_argument("--event", default="", help="Filter by event name")
    parser.add_argument("--limit", type=int, default=100, help="Max events (default: 100)")
    parser.add_argument("--format", choices=("json", "text", "triage"), default="json", help="Output format")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = query_traces(
        args.file,
        trace_id=args.trace_id or None,
        task_id=args.task_id or None,
        session_id=args.session_id or None,
        event=args.event or None,
        limit=args.limit,
    )
    if args.format == "text":
        print(format_text_result(result))
    elif args.format == "triage":
        print(format_triage_result(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
