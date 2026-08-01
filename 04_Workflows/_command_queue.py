#!/usr/bin/env python3
"""Command Queue CLI — 總指揮官讀取/摘要隊列。

Usage:
  python 04_Workflows/_command_queue.py --pretty
  python 04_Workflows/_command_queue.py --mode arrange --pretty
  python 04_Workflows/_command_queue.py --mode execute --pretty
  python 04_Workflows/_command_queue.py --status READY --pretty
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _queue_path() -> Path:
    return _repo_root() / "04_Workflows" / "command_queue" / "QUEUE.yaml"


def _archive_path() -> Path:
    return _repo_root() / "04_Workflows" / "command_queue" / "QUEUE.archive.yaml"


def _load_archive_items() -> list[dict[str, Any]]:
    """DONE / DONE_WITH_GAPS live in QUEUE.archive.yaml (optional)."""
    path = _archive_path()
    if yaml is None or not path.is_file():
        return []
    arch = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(arch, dict):
        return []
    items = arch.get("queue") or []
    return [i for i in items if isinstance(i, dict)]


def load_queue() -> dict[str, Any]:
    path = _queue_path()
    if not path.is_file():
        return {
            "ok": False,
            "message": f"queue file missing: {path.relative_to(_repo_root()).as_posix()}",
        }
    if yaml is None:
        return {"ok": False, "message": "PyYAML required: pip install pyyaml"}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"ok": False, "message": "invalid QUEUE.yaml root"}
    data["ok"] = True
    data["queue_path"] = path.relative_to(_repo_root()).as_posix()
    archived = _load_archive_items()
    data["_archived_queue"] = archived
    data["archive_path"] = (
        _archive_path().relative_to(_repo_root()).as_posix() if archived else None
    )
    data["archive_count"] = len(archived)
    # stats.done reflects archive when live queue has been slimmed
    stats = data.get("stats")
    if isinstance(stats, dict) and archived:
        done_n = sum(
            1 for i in archived if str(i.get("status", "")).upper() == "DONE"
        )
        gaps_n = sum(
            1
            for i in archived
            if str(i.get("status", "")).upper() == "DONE_WITH_GAPS"
        )
        stats = dict(stats)
        stats["done"] = done_n + gaps_n
        stats["archived_done"] = done_n
        stats["archived_done_with_gaps"] = gaps_n
        data["stats"] = stats
    return data


def _filter_queue(data: dict[str, Any], status: str | None) -> list[dict[str, Any]]:
    items = list(data.get("queue") or [])
    status_u = (status or "").upper()
    # DONE* may live only in archive after slim
    if status_u in ("DONE", "DONE_WITH_GAPS") or status_u == "":
        items = items + list(data.get("_archived_queue") or [])
    if not status:
        return items
    return [i for i in items if str(i.get("status", "")).upper() == status_u]


def _mode_summary(data: dict[str, Any], mode: str | None) -> dict[str, Any]:
    mode = (mode or "status").lower()
    priority = data.get("priority_next") or []
    blocked = data.get("global_blocked") or []
    stats = data.get("stats") or {}
    backlog = data.get("unplanned_backlog") or []

    if mode == "arrange":
        planned = _filter_queue(data, "PLANNED") + _filter_queue(data, "NOT_PLANNED")
        return {
            "mode": "arrange",
            "hint": "排後續：開 FRAME / 補 W-MASTER / 更新 priority_next",
            "candidates": [
                {"id": i.get("id"), "title": i.get("title"), "status": i.get("status")}
                for i in planned[:12]
            ],
            "unplanned_backlog": [
                {"id": i.get("id"), "title": i.get("title"), "group": i.get("group")}
                for i in backlog
            ],
            "global_blocked": [{"id": b.get("id"), "reason": b.get("reason")} for b in blocked],
        }

    if mode == "execute":
        return {
            "mode": "execute",
            "hint": "接著做：從 priority_next 或 READY/DOING 派 Implementer/Reviewer",
            "priority_next": priority,
            "ready": [
                {"id": i.get("id"), "title": i.get("title"), "state_file": i.get("state_file")}
                for i in _filter_queue(data, "READY")
            ],
            "doing": [
                {
                    "id": i.get("id"),
                    "title": i.get("title"),
                    "next_action": i.get("next_action"),
                    "state_file": i.get("state_file"),
                }
                for i in _filter_queue(data, "DOING")
            ],
        }

    return {
        "mode": "status",
        "stats": stats,
        "global_phase_avg_pct": data.get("global_phase_avg_pct"),
        "priority_next": priority,
        "global_blocked_count": len(blocked),
    }


def build_result(
    *,
    mode: str | None,
    status: str | None,
    pretty: bool,
) -> dict[str, Any]:
    data = load_queue()
    if not data.get("ok"):
        return data

    result: dict[str, Any] = {
        "ok": True,
        "queue_path": data.get("queue_path"),
        "archive_path": data.get("archive_path"),
        "archive_count": data.get("archive_count", 0),
        "schema_version": data.get("schema_version"),
        "last_sync": data.get("last_sync"),
        "ssot": data.get("ssot"),
        "summary": _mode_summary(data, mode),
    }

    if status:
        status_u = status.upper()
        items = _filter_queue(data, status_u)
        # --status DONE also surfaces DONE_WITH_GAPS for ops follow-up
        if status_u == "DONE":
            items = items + _filter_queue(data, "DONE_WITH_GAPS")
        result["filtered"] = {
            "status": status_u,
            "items": items,
        }
    elif mode in (None, "status"):
        result["queue_by_status"] = {}
        for st in ("READY", "DOING", "PLANNED", "BLOCKED", "DONE", "DONE_WITH_GAPS"):
            items = _filter_queue(data, st)
            if items:
                result["queue_by_status"][st] = [
                    {
                        "id": i.get("id"),
                        "title": i.get("title"),
                        "next_action": i.get("next_action"),
                    }
                    for i in items
                ]

    if pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Command Queue reader for HQ Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["status", "arrange", "execute"],
        default="status",
        help="arrange=排後續 · execute=接著做 · status=全覽",
    )
    parser.add_argument(
        "--status",
        help="Filter queue items by status (READY/DOING/PLANNED/BLOCKED/DONE)",
    )
    parser.add_argument("--pretty", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args(argv)

    result = build_result(mode=args.mode, status=args.status, pretty=args.pretty)
    if not args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
