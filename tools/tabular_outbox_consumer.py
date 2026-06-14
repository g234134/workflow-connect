"""Tabular Outbox Consumer v1 (W3-TL-T4).

Read-only access to tabular MVP outbox records under outbox/<case_ref>/.
Separate from Phase 8.8 orchestration_bridge_outbox replay tooling.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.tabular_outbox_writer import (
    OUTBOX_SCHEMA_VERSION,
    outbox_root as resolve_outbox_root,
    validate_record,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

_REQUIRED_OUTBOX_KEYS = frozenset(
    {
        "schema_version",
        "case_ref",
        "run_id",
        "tool_id",
        "started_at",
        "finished_at",
        "ok",
        "exit_code",
        "message",
        "artifacts",
        "outbox_path",
    }
)

_SUMMARY_KEYS = (
    "case_ref",
    "run_id",
    "tool_id",
    "started_at",
    "finished_at",
    "ok",
    "exit_code",
    "message",
    "outbox_path",
)


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return repo_root.resolve() if repo_root is not None else _REPO_ROOT


def _normalize_case_ref(case_ref: str) -> str:
    return case_ref.replace("\\", "/").strip("/")


def _case_dir_from_ref(case_ref: str) -> str:
    return f"cases/{_normalize_case_ref(case_ref)}"


def _parse_iso8601(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _run_summary(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: record.get(key) for key in _SUMMARY_KEYS}


def _iter_run_files(
    root: Path,
    case_ref: Optional[str] = None,
) -> List[Path]:
    if not root.is_dir():
        return []

    if case_ref is not None:
        case_dir = root / _normalize_case_ref(case_ref)
        if not case_dir.is_dir():
            return []
        return sorted(case_dir.glob("*.json"))

    paths: List[Path] = []
    for path in sorted(root.rglob("*.json")):
        if path.parent == root:
            continue
        paths.append(path)
    return paths


def _load_run_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _matches_time_window(
    record: Dict[str, Any],
    *,
    started_after: Optional[str] = None,
    started_before: Optional[str] = None,
) -> bool:
    started_at = record.get("started_at")
    if not isinstance(started_at, str):
        return True

    started_dt = _parse_iso8601(started_at)
    if started_dt is None:
        return True

    if started_after:
        after_dt = _parse_iso8601(started_after)
        if after_dt is not None and started_dt < after_dt:
            return False

    if started_before:
        before_dt = _parse_iso8601(started_before)
        if before_dt is not None and started_dt > before_dt:
            return False

    return True


def list_outbox_runs(
    case_ref: Optional[str] = None,
    tool_id: Optional[str] = None,
    *,
    started_after: Optional[str] = None,
    started_before: Optional[str] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Scan outbox/ and return matching run summaries (newest first)."""
    root = resolve_outbox_root(_repo_root(repo_root), outbox_root_override)
    summaries: List[Dict[str, Any]] = []

    for path in _iter_run_files(root, case_ref):
        record = _load_run_file(path)
        if record is None:
            continue
        if tool_id is not None and record.get("tool_id") != tool_id:
            continue
        if not _matches_time_window(
            record,
            started_after=started_after,
            started_before=started_before,
        ):
            continue
        summaries.append(_run_summary(record))

    summaries.sort(
        key=lambda item: str(item.get("started_at") or ""),
        reverse=True,
    )
    return summaries


def get_outbox_run(
    case_ref: str,
    run_id: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Read a single outbox/<case_ref>/<run_id>.json record."""
    safe_case = _normalize_case_ref(case_ref)
    safe_run = str(run_id).strip()
    if not safe_case or not safe_run:
        return {
            "ok": False,
            "message": "invalid_case_ref_or_run_id",
            "case_ref": case_ref,
            "run_id": run_id,
        }

    root = resolve_outbox_root(_repo_root(repo_root), outbox_root_override)
    path = root / safe_case / f"{safe_run}.json"
    if not path.is_file():
        return {
            "ok": False,
            "message": "run_not_found",
            "case_ref": safe_case,
            "run_id": safe_run,
            "outbox_path": f"outbox/{safe_case}/{safe_run}.json",
        }

    record = _load_run_file(path)
    if record is None:
        return {
            "ok": False,
            "message": "invalid_run_json",
            "case_ref": safe_case,
            "run_id": safe_run,
            "outbox_path": f"outbox/{safe_case}/{safe_run}.json",
        }

    missing = _REQUIRED_OUTBOX_KEYS - set(record)
    if missing:
        return {
            "ok": False,
            "message": f"missing_required_keys:{sorted(missing)}",
            "case_ref": safe_case,
            "run_id": safe_run,
            "record": record,
        }

    if record.get("schema_version") != OUTBOX_SCHEMA_VERSION:
        return {
            "ok": False,
            "message": "unsupported_schema_version",
            "case_ref": safe_case,
            "run_id": safe_run,
            "schema_version": record.get("schema_version"),
            "record": record,
        }

    try:
        validate_record(record)
    except ValueError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "case_ref": safe_case,
            "run_id": safe_run,
            "record": record,
        }

    return {"ok": True, "record": record}


def _load_index_entry(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    index_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    root = _repo_root(repo_root)
    path = index_path or (root / "cases" / "index.json")
    if not path.is_file():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    cases = data.get("cases")
    if not isinstance(cases, list):
        return None

    target_dir = _case_dir_from_ref(case_ref)
    for item in cases:
        if not isinstance(item, dict):
            continue
        case_dir = str(item.get("case_dir", "")).replace("\\", "/")
        if case_dir == target_dir:
            return dict(item)
    return None


def _lookup_history_for_case(
    index_entry: Optional[Dict[str, Any]],
    *,
    repo_root: Optional[Path] = None,
    index_path: Optional[Path] = None,
) -> Dict[str, Any]:
    if index_entry is None:
        return {"ok": False, "matches": [], "notes": ["case_not_in_index"]}

    import sys

    scripts_dir = _repo_root(repo_root) / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from cases_index_lib import lookup_cases  # noqa: WPS433

    client_ref = index_entry.get("client_ref")
    if not isinstance(client_ref, str) or not client_ref.strip():
        return {"ok": False, "matches": [], "notes": ["missing_client_ref"]}

    return lookup_cases(
        client_ref=client_ref,
        index_path=index_path,
        repo_root=_repo_root(repo_root),
    )


def _last_by_tool_id(runs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for run in sorted(runs, key=lambda item: str(item.get("started_at") or "")):
        tool = run.get("tool_id")
        if isinstance(tool, str) and tool:
            latest[tool] = run
    return latest


def join_with_case_history(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    index_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Join outbox runs with cases/index.json and lookup_case_history view."""
    safe_case = _normalize_case_ref(case_ref)
    if not safe_case:
        return {
            "ok": False,
            "message": "invalid_case_ref",
            "case_ref": case_ref,
        }

    index_entry = _load_index_entry(
        safe_case,
        repo_root=repo_root,
        index_path=index_path,
    )
    history = _lookup_history_for_case(
        index_entry,
        repo_root=repo_root,
        index_path=index_path,
    )

    runs = list_outbox_runs(
        case_ref=safe_case,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    runs_chronological = sorted(
        runs,
        key=lambda item: str(item.get("started_at") or ""),
    )

    case_info: Optional[Dict[str, Any]] = None
    if index_entry is not None:
        case_info = {
            "case_dir": index_entry.get("case_dir"),
            "client_ref": index_entry.get("client_ref"),
            "case_id": index_entry.get("case_id"),
            "product_sku": index_entry.get("product_sku"),
            "gate_status": index_entry.get("gate_status"),
            "schema_headers": index_entry.get("schema_headers"),
            "known_limits": index_entry.get("known_limits"),
        }

    return {
        "ok": True,
        "case_ref": safe_case,
        "case": case_info,
        "history": history,
        "runs": runs_chronological,
        "last_by_tool_id": _last_by_tool_id(runs_chronological),
        "run_count": len(runs_chronological),
    }
