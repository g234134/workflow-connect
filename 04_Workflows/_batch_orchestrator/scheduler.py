"""Batch subtask scheduler MVP — waves / order / eligibility (BATCH-MVP-02).

Consumes loader ``data.subtasks`` lists. Does not execute workers or touch
ticket state / Progress.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping, Sequence


def _normalize_subtasks(subtasks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in subtasks:
        if not isinstance(item, Mapping):
            continue
        sid = str(item.get("subtask_id", "")).strip()
        if not sid:
            continue
        deps_raw = item.get("dependencies") or []
        deps = [str(d).strip() for d in deps_raw if str(d).strip()]
        try:
            priority = int(item.get("priority", 100))
        except (TypeError, ValueError):
            priority = 100
        out.append(
            {
                "subtask_id": sid,
                "priority": priority,
                "dependencies": deps,
                "status": str(item.get("status", "pending")),
            }
        )
    return out


def _detect_cycle(ids: set[str], deps_map: dict[str, list[str]]) -> list[str]:
    """Return one cycle path (node ids) if a dependency cycle exists, else []."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in ids}
    parent: dict[str, str | None] = {n: None for n in ids}

    def dfs(u: str) -> list[str] | None:
        color[u] = GRAY
        for v in deps_map.get(u, []):
            if v not in ids:
                continue
            if color[v] == GRAY:
                # reconstruct cycle u → … → v → u
                cycle = [v, u]
                cur = u
                while cur != v and parent[cur] is not None:
                    cur = parent[cur]  # type: ignore[assignment]
                    cycle.append(cur)
                cycle.reverse()
                return cycle
            if color[v] == WHITE:
                parent[v] = u
                found = dfs(v)
                if found is not None:
                    return found
        color[u] = BLACK
        return None

    for node in sorted(ids):
        if color[node] == WHITE:
            found = dfs(node)
            if found:
                return found
    return []


def plan_from_subtasks(subtasks: list[dict]) -> dict:
    """Plan execution waves from a subtask list.

    Returns dict with at least:
      ok, waves, order, eligibility, message
    """
    normalized = _normalize_subtasks(subtasks)
    if not normalized:
        return {
            "ok": False,
            "waves": [],
            "order": [],
            "eligibility": {
                "parallel_ok": [],
                "blocked": [],
                "errors": ["no valid subtasks (missing subtask_id)"],
            },
            "message": "scheduler refused: empty or invalid subtask list",
        }

    ids = {s["subtask_id"] for s in normalized}
    by_id = {s["subtask_id"]: s for s in normalized}
    deps_map: dict[str, list[str]] = {
        s["subtask_id"]: [d for d in s["dependencies"] if d in ids] for s in normalized
    }

    errors: list[str] = []
    blocked: list[dict[str, str]] = []

    # Unknown deps (outside batch) — note but do not hard-fail topology
    for s in normalized:
        for d in s["dependencies"]:
            if d not in ids:
                errors.append(f"{s['subtask_id']}: unknown dependency '{d}'")
                blocked.append(
                    {
                        "subtask_id": s["subtask_id"],
                        "reason": f"unknown_dependency:{d}",
                    }
                )

    cycle = _detect_cycle(ids, deps_map)
    if cycle:
        cycle_msg = " → ".join(cycle + [cycle[0]])
        return {
            "ok": False,
            "waves": [],
            "order": [],
            "eligibility": {
                "parallel_ok": [],
                "blocked": [{"subtask_id": n, "reason": "dependency_cycle"} for n in cycle],
                "errors": [f"dependency cycle detected: {cycle_msg}"],
            },
            "message": "scheduler refused: dependency cycle",
        }

    # Kahn topological levels = waves; within wave sort by priority asc then id
    indegree: dict[str, int] = {n: 0 for n in ids}
    children: dict[str, list[str]] = defaultdict(list)
    for sid, deps in deps_map.items():
        for d in deps:
            children[d].append(sid)
            indegree[sid] += 1

    ready = [n for n, deg in indegree.items() if deg == 0]
    ready.sort(key=lambda n: (by_id[n]["priority"], n))

    waves: list[list[str]] = []
    order: list[str] = []
    remaining = set(ids)

    while ready:
        wave = list(ready)
        waves.append(wave)
        order.extend(wave)
        for n in wave:
            remaining.discard(n)
        next_ready: list[str] = []
        for n in wave:
            for child in children[n]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    next_ready.append(child)
        next_ready.sort(key=lambda n: (by_id[n]["priority"], n))
        ready = next_ready

    if remaining:
        # Should not happen without cycle; treat as error
        errors.append(f"incomplete schedule; leftover: {sorted(remaining)}")
        return {
            "ok": False,
            "waves": waves,
            "order": order,
            "eligibility": {
                "parallel_ok": [],
                "blocked": [{"subtask_id": n, "reason": "unscheduled"} for n in sorted(remaining)],
                "errors": errors,
            },
            "message": "scheduler refused: incomplete topological schedule",
        }

    parallel_ok = [sid for wave in waves for sid in wave if len(wave) > 1]
    # Also mark singletons as eligible (no parallel peers)
    eligibility = {
        "parallel_ok": parallel_ok,
        "blocked": blocked,
        "errors": errors,
        "wave_sizes": [len(w) for w in waves],
    }

    return {
        "ok": True,
        "waves": waves,
        "order": order,
        "eligibility": eligibility,
        "message": f"planned {len(order)} subtasks in {len(waves)} wave(s)",
    }


def plan_from_loader_data(data: Mapping[str, Any]) -> dict:
    """Convenience: accept loader ``data`` mapping with ``subtasks`` key."""
    subtasks = data.get("subtasks") if isinstance(data, Mapping) else None
    if not isinstance(subtasks, list):
        return {
            "ok": False,
            "waves": [],
            "order": [],
            "eligibility": {"parallel_ok": [], "blocked": [], "errors": ["data.subtasks missing"]},
            "message": "scheduler refused: loader data.subtasks required",
        }
    return plan_from_subtasks(subtasks)
