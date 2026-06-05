# task_routing.py — HQ Phase 3 任務路由解析（機器讀表 + dict 契約）
from __future__ import annotations

import json
import re
from copy import deepcopy
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from gov_paths import get_artifact_path, load_master_map

_ROUTING_ARTIFACT_KEY = "task_routing_table"
_DARK_OPS_WORKER = "DarkOps-Worker"


@lru_cache(maxsize=1)
def load_routing_table() -> Dict[str, Any]:
    path = get_artifact_path(_ROUTING_ARTIFACT_KEY)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "routes" not in data or "default_route" not in data:
        raise ValueError("task_routing_table.json: missing routes or default_route")
    return data


def invalidate_routing_cache() -> None:
    load_routing_table.cache_clear()


def _normalize_text(text: str) -> str:
    return text.strip().lower()


def _find_route_by_type(table: Dict[str, Any], task_type: str) -> Optional[Dict[str, Any]]:
    want = _normalize_text(task_type)
    for route in table.get("routes") or []:
        if _normalize_text(str(route.get("task_type", ""))) == want:
            return route
    return None


def _score_keywords(text: str, keywords: List[str]) -> int:
    hay = _normalize_text(text)
    score = 0
    for kw in keywords or []:
        token = _normalize_text(str(kw))
        if not token:
            continue
        if token in hay:
            score += 2
        elif re.search(re.escape(token), hay):
            score += 1
    return score


def _pick_keyword_route(table: Dict[str, Any], text: str) -> Tuple[Optional[Dict[str, Any]], int]:
    best: Optional[Dict[str, Any]] = None
    best_score = 0
    for route in table.get("routes") or []:
        score = _score_keywords(text, list(route.get("keywords") or []))
        if score > best_score:
            best_score = score
            best = route
    return best, best_score


def _is_dark_ops_blocked(table: Dict[str, Any], worker: str) -> bool:
    if worker != _DARK_OPS_WORKER:
        return False
    gates = table.get("phase_gates") or {}
    return str(gates.get("dark_ops_worker", "")).strip().lower() == "blocked"


def _build_result(
    route: Dict[str, Any],
    match_method: str,
    table: Dict[str, Any],
) -> Dict[str, Any]:
    worker = str(route.get("worker", ""))
    blocked = _is_dark_ops_blocked(table, worker)
    assignable = not blocked
    block_reason: Optional[str] = None
    if blocked:
        block_reason = (
            "DarkOps-Worker is phase-gated blocked; "
            "routing identifies target only — open a separate ticket to ungate."
        )

    task_type = str(route.get("task_type", ""))
    message = f"Routed {task_type} → {worker}"
    if route.get("cabin"):
        message += f" @ {route['cabin']}"
    if route.get("dark_agent"):
        message += f" (agent {route['dark_agent']})"
    if blocked:
        message += " [NOT ASSIGNABLE: DarkOps blocked]"

    return {
        "ok": True,
        "assignable": assignable,
        "task_type": task_type,
        "worker": worker,
        "cabin": route.get("cabin"),
        "domain": route.get("domain"),
        "dark_agent": route.get("dark_agent"),
        "runners": list(route.get("runners") or []),
        "enter_runner": route.get("enter_runner"),
        "match_method": match_method,
        "blocked": blocked,
        "block_reason": block_reason,
        "message": message,
        "routing_schema_version": table.get("routing_schema_version"),
        "ticket": table.get("ticket"),
    }


def route_task(
    task_type: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    依 task_type 或描述／標籤解析任務路由。
    優先：explicit task_type > keyword(text+tags) > default_route。
    """
    table = load_routing_table()

    if task_type and str(task_type).strip():
        route = _find_route_by_type(table, str(task_type))
        if route is not None:
            return _build_result(route, "explicit", table)
        return {
            "ok": False,
            "assignable": False,
            "task_type": str(task_type).strip(),
            "worker": None,
            "cabin": None,
            "domain": None,
            "dark_agent": None,
            "runners": [],
            "enter_runner": None,
            "match_method": "explicit",
            "blocked": True,
            "block_reason": f"Unknown task_type: {task_type}",
            "message": f"No route for task_type={task_type!r}",
            "routing_schema_version": table.get("routing_schema_version"),
            "ticket": table.get("ticket"),
        }

    parts: List[str] = []
    if description:
        parts.append(str(description))
    if tags:
        parts.extend(str(t) for t in tags)
    combined = " ".join(parts).strip()

    if combined:
        route, score = _pick_keyword_route(table, combined)
        if route is not None and score > 0:
            return _build_result(route, "keyword", table)

    default = deepcopy(table.get("default_route") or {})
    if "task_type" not in default:
        default["task_type"] = "hq.coordination"
        default.setdefault("worker", "HQ-Coordinator")
        default.setdefault("domain", "HQ")
    return _build_result(default, "default", table)


def resolve_runner_paths(runner_keys: List[str]) -> Dict[str, str]:
    """將 runner 邏輯名解析為相對路徑（供副官交接包）。"""
    m = load_master_map()
    runners = m.get("runners") or {}
    out: Dict[str, str] = {}
    for key in runner_keys:
        rel = runners.get(key)
        if rel:
            out[key] = str(rel).replace("/", "\\") if "\\" in str(m.get("tang_gov_root", "")) else str(rel)
        else:
            out[key] = ""
    return out


def enrich_route_with_runners(result: Dict[str, Any]) -> Dict[str, Any]:
    """附加 runner_paths 欄位（不改變路由決策）。"""
    enriched = dict(result)
    keys = list(result.get("runners") or [])
    enter = result.get("enter_runner")
    if enter:
        keys = [str(enter)] + keys
    enriched["runner_paths"] = resolve_runner_paths(keys)
    return enriched
