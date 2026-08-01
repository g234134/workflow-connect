#!/usr/bin/env python3
"""Read-only inspect CLI for notification webhook DLQ jsonl (P7 · §4.6.4.4).

Examples:
    python tools/inspect_notification_dlq_v1.py list --limit 20
    python tools/inspect_notification_dlq_v1.py stats --tier prod --json
    python tools/inspect_notification_dlq_v1.py list --dlq-path tests/fixtures/notification_dlq/events.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_DLQ_PATH = "outbox/notification_dlq/events.jsonl"
DEFAULT_LIMIT = 50

LIST_ENTRY_FIELDS = (
    "dlq_written_at",
    "timestamp",
    "event_id",
    "event_type",
    "endpoint",
    "tier",
    "attempt_count",
    "retry_exhausted",
    "last_error",
    "http_status",
    "payload_digest",
)


def _parse_iso8601(value: str) -> datetime:
    text = value.strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        text = f"{text}T00:00:00+00:00"
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _record_time(record: Dict[str, Any], time_field: str) -> Optional[datetime]:
    raw = record.get(time_field)
    if not raw or not isinstance(raw, str):
        return None
    try:
        return _parse_iso8601(raw)
    except ValueError:
        return None


def _resolve_dlq_path(dlq_path: Optional[str], dlq_root: Optional[str]) -> Path:
    if dlq_path:
        return Path(dlq_path)
    if dlq_root:
        return Path(dlq_root) / "events.jsonl"
    return Path(DEFAULT_DLQ_PATH)


def _iter_dlq_records(
    dlq_file: Path,
) -> Iterable[Dict[str, Any]]:
    if not dlq_file.is_file():
        return
    with dlq_file.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: skip line {line_no}: invalid JSON ({exc.msg})",
                    file=sys.stderr,
                )
                continue
            if not isinstance(parsed, dict):
                print(
                    f"warning: skip line {line_no}: expected JSON object",
                    file=sys.stderr,
                )
                continue
            yield parsed


def _http_status_key(status: Any) -> str:
    if status is None:
        return "null"
    return str(status)


def _matches_filters(
    record: Dict[str, Any],
    *,
    since: Optional[datetime],
    until: Optional[datetime],
    time_field: str,
    tier: Optional[str],
    endpoint: Optional[str],
    event_id: Optional[str],
    http_status: Optional[Any],
) -> bool:
    if tier is not None and record.get("tier") != tier:
        return False
    if endpoint is not None:
        endpoint_value = record.get("endpoint") or ""
        if endpoint not in str(endpoint_value):
            return False
    if event_id is not None and record.get("event_id") != event_id:
        return False
    if http_status is not None:
        if http_status == "null":
            if record.get("http_status") is not None:
                return False
        elif record.get("http_status") != http_status:
            return False

    record_dt = _record_time(record, time_field)
    if since is not None:
        if record_dt is None or record_dt < since:
            return False
    if until is not None:
        if record_dt is None or record_dt > until:
            return False
    return True


def _project_entry(
    record: Dict[str, Any],
    *,
    include_webhook_result: bool,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {}
    for field in LIST_ENTRY_FIELDS:
        if field in record:
            entry[field] = record[field]
    if include_webhook_result and "webhook_result" in record:
        entry["webhook_result"] = record["webhook_result"]
    return entry


def _format_table(entries: List[Dict[str, Any]]) -> str:
    if not entries:
        return "(no entries)"

    columns = [
        ("dlq_written_at", 24),
        ("tier", 8),
        ("event_id", 20),
        ("endpoint", 28),
        ("http_status", 11),
        ("last_error", 32),
    ]
    header = "  ".join(name.ljust(width) for name, width in columns)
    lines = [header, "-" * len(header)]
    for row in entries:
        parts = []
        for name, width in columns:
            value = row.get(name, "")
            if value is None:
                text = "null"
            else:
                text = str(value)
            if len(text) > width:
                text = text[: width - 1] + "…"
            parts.append(text.ljust(width))
        lines.append("  ".join(parts))
    return "\n".join(lines)


def _load_filtered_records(
    dlq_file: Path,
    *,
    since: Optional[datetime],
    until: Optional[datetime],
    time_field: str,
    tier: Optional[str],
    endpoint: Optional[str],
    event_id: Optional[str],
    http_status: Optional[Any],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for record in _iter_dlq_records(dlq_file) or []:
        if _matches_filters(
            record,
            since=since,
            until=until,
            time_field=time_field,
            tier=tier,
            endpoint=endpoint,
            event_id=event_id,
            http_status=http_status,
        ):
            records.append(record)

    records.sort(
        key=lambda item: _record_time(item, "dlq_written_at")
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return records


def _parse_code_arg(raw: Optional[str]) -> Optional[Any]:
    if raw is None:
        return None
    if raw.lower() == "null":
        return "null"
    try:
        return int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"--code must be an integer or 'null', got {raw!r}"
        ) from exc


def inspect_list(
    dlq_file: Path,
    *,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    time_field: str = "dlq_written_at",
    tier: Optional[str] = None,
    endpoint: Optional[str] = None,
    event_id: Optional[str] = None,
    http_status: Optional[Any] = None,
    limit: int = DEFAULT_LIMIT,
    include_webhook_result: bool = False,
) -> Dict[str, Any]:
    records = _load_filtered_records(
        dlq_file,
        since=since,
        until=until,
        time_field=time_field,
        tier=tier,
        endpoint=endpoint,
        event_id=event_id,
        http_status=http_status,
    )
    limited = records[:limit]
    entries = [
        _project_entry(record, include_webhook_result=include_webhook_result)
        for record in limited
    ]
    return {"ok": True, "count": len(entries), "entries": entries}


def inspect_stats(
    dlq_file: Path,
    *,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    time_field: str = "dlq_written_at",
    tier: Optional[str] = None,
    endpoint: Optional[str] = None,
    event_id: Optional[str] = None,
    http_status: Optional[Any] = None,
) -> Dict[str, Any]:
    records = _load_filtered_records(
        dlq_file,
        since=since,
        until=until,
        time_field=time_field,
        tier=tier,
        endpoint=endpoint,
        event_id=event_id,
        http_status=http_status,
    )
    by_endpoint = Counter(str(record.get("endpoint") or "unknown") for record in records)
    by_tier = Counter(str(record.get("tier") or "unknown") for record in records)
    by_http_status = Counter(
        _http_status_key(record.get("http_status")) for record in records
    )
    return {
        "ok": True,
        "total_count": len(records),
        "by_endpoint": dict(sorted(by_endpoint.items())),
        "by_tier": dict(sorted(by_tier.items())),
        "by_http_status": dict(sorted(by_http_status.items())),
    }


def _assert_no_sensitive_leak(payload: Dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    banned_fragments = (
        "authorization:",
        "hmac_secret",
        "x-gov-signature-256",
        '"raw_body"',
        '"webhook_body"',
    )
    for fragment in banned_fragments:
        if fragment in encoded:
            raise ValueError(f"output may contain sensitive data ({fragment})")


def main(argv: Optional[List[str]] = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    command = "list"
    if raw_argv and raw_argv[0] in ("list", "stats"):
        command = raw_argv[0]
        raw_argv = raw_argv[1:]

    parser = argparse.ArgumentParser(
        description="Read-only inspect CLI for notification webhook DLQ jsonl."
    )
    parser.add_argument(
        "--dlq-path",
        help=f"Path to DLQ jsonl (default: {DEFAULT_DLQ_PATH})",
    )
    parser.add_argument(
        "--dlq-root",
        help="Directory shortcut; resolves to <root>/events.jsonl",
    )
    parser.add_argument("--since", help="Lower bound (ISO8601 or YYYY-MM-DD)")
    parser.add_argument("--until", help="Upper bound (ISO8601 or YYYY-MM-DD)")
    parser.add_argument(
        "--time-field",
        choices=("dlq_written_at", "timestamp"),
        default="dlq_written_at",
        help="Time field for --since/--until (default: dlq_written_at)",
    )
    parser.add_argument("--tier", choices=("sandbox", "staging", "prod"))
    parser.add_argument("--endpoint", help="Endpoint substring filter")
    parser.add_argument("--event-id", help="Exact event_id filter")
    parser.add_argument(
        "--code",
        type=_parse_code_arg,
        help="Filter http_status (integer or 'null' for connection failures)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON on stdout",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum entries to list (default: {DEFAULT_LIMIT}; list only)",
    )
    parser.add_argument(
        "--include-webhook-result",
        action="store_true",
        help="Include embed webhook_result in list output",
    )

    args = parser.parse_args(raw_argv)

    since = _parse_iso8601(args.since) if args.since else None
    until = _parse_iso8601(args.until) if args.until else None
    dlq_file = _resolve_dlq_path(args.dlq_path, args.dlq_root)

    filter_kwargs = {
        "since": since,
        "until": until,
        "time_field": args.time_field,
        "tier": args.tier,
        "endpoint": args.endpoint,
        "event_id": args.event_id,
        "http_status": args.code,
    }

    if command == "list":
        result = inspect_list(
            dlq_file,
            limit=args.limit,
            include_webhook_result=args.include_webhook_result,
            **filter_kwargs,
        )
        if args.json:
            _assert_no_sensitive_leak(result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(
                f"notification DLQ list path={dlq_file} count={result['count']}"
            )
            print(_format_table(result["entries"]))
        return 0

    if command == "stats":
        result = inspect_stats(dlq_file, **filter_kwargs)
        if args.json:
            _assert_no_sensitive_leak(result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(
                f"notification DLQ stats path={dlq_file} "
                f"total_count={result['total_count']}"
            )
            print("by_http_status:")
            for key, count in result["by_http_status"].items():
                print(f"  {key}: {count}")
            print("by_endpoint:")
            for key, count in result["by_endpoint"].items():
                print(f"  {key}: {count}")
            print("by_tier:")
            for key, count in result["by_tier"].items():
                print(f"  {key}: {count}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
