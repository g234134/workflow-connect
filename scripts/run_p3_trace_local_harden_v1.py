#!/usr/bin/env python3
"""P3 local trace harden v1 — fixture schema + trace_query smoke.

Ticket: P3-TRACE-LOCAL-HARDEN-v1
Design: docs/p3-trace-local-harden-v1.md

Read-only against fixture JSONL (default sample_traces). Does **not**
talk to Langfuse / PG / dark observability.

Usage:
    python scripts/run_p3_trace_local_harden_v1.py --format text
    python scripts/run_p3_trace_local_harden_v1.py --pretty
    python scripts/run_p3_trace_local_harden_v1.py --file tests/fixtures/trace/sample_traces.jsonl --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from observability.trace_query import query_traces  # noqa: E402
from observability.trace_schema import (  # noqa: E402
    GOV_TRACE_SCHEMA_VERSION,
    validate_trace_event,
)

_SCHEMA_VERSION = "p3_trace_local_harden_v1"
_DOC_REL = "docs/p3-trace-local-harden-v1.md"
_DEFAULT_FIXTURE_REL = "tests/fixtures/trace/sample_traces.jsonl"
_SMOKE_TRACE_ID = "trace-wb-fixture-001"
_SMOKE_TASK_ID = "task-wb-002"
_NON_CLAIMS = (
    "≠ prod Langfuse upgrade / live Langfuse connect",
    "≠ Langfuse↔PG alignment complete",
    "≠ mandatory CI / Dashboard Phase% apply",
    "≠ rewrite live runtime/checkpoints or dark core",
)


def _repo_root() -> Path:
    return _REPO_ROOT


def _check_schema_fixture(path: Path) -> dict[str, Any]:
    """Validate every non-empty JSONL line against gov-trace-v2 required keys."""
    if not path.is_file():
        return {
            "name": "schema_fixture",
            "ok": False,
            "message": f"file not found: {path.as_posix()}",
            "lines_checked": 0,
            "invalid": [],
        }

    lines_checked = 0
    invalid: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                text = raw.strip()
                if not text:
                    continue
                lines_checked += 1
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError as exc:
                    invalid.append(
                        {
                            "line": line_no,
                            "reason": f"invalid JSON: {exc}",
                        }
                    )
                    continue
                if not isinstance(obj, dict):
                    invalid.append({"line": line_no, "reason": "expected JSON object"})
                    continue
                verdict = validate_trace_event(obj)
                if not verdict.get("ok"):
                    invalid.append(
                        {
                            "line": line_no,
                            "reason": verdict.get("message") or "validation failed",
                            "missing": verdict.get("missing"),
                        }
                    )
    except OSError as exc:
        return {
            "name": "schema_fixture",
            "ok": False,
            "message": str(exc),
            "lines_checked": lines_checked,
            "invalid": invalid,
        }

    ok = not invalid and lines_checked > 0
    if lines_checked == 0:
        message = "no events in file"
    elif invalid:
        message = f"{len(invalid)} invalid event(s) of {lines_checked}"
    else:
        message = f"all {lines_checked} event(s) match {GOV_TRACE_SCHEMA_VERSION}"
    return {
        "name": "schema_fixture",
        "ok": ok,
        "message": message,
        "lines_checked": lines_checked,
        "invalid": invalid,
        "schema_version_expected": GOV_TRACE_SCHEMA_VERSION,
    }


def _check_query_by_trace_id(path: Path) -> dict[str, Any]:
    result = query_traces(path, trace_id=_SMOKE_TRACE_ID)
    matches = int(result.get("matches") or 0)
    ok = bool(result.get("ok")) and matches >= 3
    return {
        "name": "query_by_trace_id",
        "ok": ok,
        "message": result.get("message") or "",
        "trace_id": _SMOKE_TRACE_ID,
        "matches": matches,
        "query_ok": bool(result.get("ok")),
    }


def _check_query_by_task_id(path: Path) -> dict[str, Any]:
    result = query_traces(path, task_id=_SMOKE_TASK_ID)
    matches = int(result.get("matches") or 0)
    event_counts = (result.get("summary") or {}).get("event_counts") or {}
    has_end = int(event_counts.get("trace_end") or 0) >= 1
    ok = bool(result.get("ok")) and matches >= 1 and has_end
    return {
        "name": "query_by_task_id",
        "ok": ok,
        "message": result.get("message") or "",
        "task_id": _SMOKE_TASK_ID,
        "matches": matches,
        "event_counts": event_counts,
        "query_ok": bool(result.get("ok")),
    }


def _display_path(path: Path, root: Path) -> str:
    """Prefer repo-relative posix; never invent drive-letter constants."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run_p3_trace_local_harden(
    *,
    file: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Return structured harden result for local gov-trace-v2 JSONL."""
    root = repo_root or _repo_root()
    path = file if file is not None else root / _DEFAULT_FIXTURE_REL
    if not path.is_absolute():
        candidate = root / path
        path = candidate if candidate.exists() else path
    path = path.resolve()

    checks = [
        _check_schema_fixture(path),
        _check_query_by_trace_id(path),
        _check_query_by_task_id(path),
    ]
    all_ok = all(bool(c.get("ok")) for c in checks)
    failed = [c["name"] for c in checks if not c.get("ok")]

    return {
        "ok": all_ok,
        "schema_version": _SCHEMA_VERSION,
        "mode": "trace_local_harden",
        "source_file": _display_path(path, root),
        "checks": checks,
        "failed_checks": failed,
        "message": (
            "local trace harden passed"
            if all_ok
            else f"local trace harden failed: {', '.join(failed) or 'unknown'}"
        ),
        "non_claims": list(_NON_CLAIMS),
        "doc": _DOC_REL,
        "apply_phase_pct": False,
        "phase_targets": ["P3"],
        "baseline_pct": 82,
        "proposed_delta_pct": "+1～+3",
    }


def _format_text(result: dict[str, Any]) -> str:
    lines = [
        f"ok: {result.get('ok')}",
        f"schema_version: {result.get('schema_version')}",
        f"source_file: {result.get('source_file')}",
        f"message: {result.get('message')}",
        f"apply_phase_pct: {result.get('apply_phase_pct')}",
        "checks:",
    ]
    for check in result.get("checks") or []:
        lines.append(
            f"  - {check.get('name')}: ok={check.get('ok')} — {check.get('message')}"
        )
    lines.append("non_claims:")
    for claim in result.get("non_claims") or []:
        lines.append(f"  - {claim}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P3 local trace harden — fixture schema + trace_query smoke",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help=f"JSONL path (default: {_DEFAULT_FIXTURE_REL})",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="stdout format (default json)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write artifacts/p3_trace/harden.latest.json",
    )
    args = parser.parse_args(argv)

    result = run_p3_trace_local_harden(file=args.file)

    if args.write:
        out_dir = _repo_root() / "artifacts" / "p3_trace"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "harden.latest.json"
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result = dict(result)
        result["artifact"] = _display_path(out_path, _repo_root())

    if args.format == "text":
        sys.stdout.write(_format_text(result))
    else:
        indent = 2 if args.pretty else None
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=indent) + "\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
