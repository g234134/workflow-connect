"""
H-line context entry contract — unified wrapper over ``context.build_context``.

New ask-like pipelines MUST call ``build_rooted_context`` instead of hand-assembling
root/working/long-term layers at the entry point. See ``context/context_entry_contract.md``.
"""

from __future__ import annotations

import copy
import json
import uuid
from typing import Any

from context.context_builder import build_context
from context.deny_rules import GateRunner, attach_deny_observability, merge_subtree_deny_union

_ENTRY_MODES = frozenset({"ask_pipeline", "k1_pipeline", "k2_pipeline", "api_entry", "long_task"})
_MOUNT_TYPES = frozenset({"line", "dept", "module", "theme"})
_MAX_ACTIVE_SUBTREES = 2
_MAX_ENTRY_REFS_PER_SUBTREE = 3
_SUBTREE_LAYER_MAX_TOKENS = 8_000
_CHARS_PER_TOKEN = 4
_TRIM_METADATA_VERSION = "p0.5-v0.1"

# v0.1 minimal deny gates (A'-2 / R-3a; R-3b GateRunner); rules in context/deny_rules.py.
_DENY_RUNNER = GateRunner()
_NAV_MAP_TEMPLATE_REF = "workflow_upgrade/01_context-entry/40_navigation_map_template.md"

# v0.1 mock aligned with A-2 + nav map §8 (`line.a.context-entry`).
_DEFAULT_SUBTREE_V01: dict[str, Any] = {
    "subtree_id": "line.a.context-entry",
    "mount_type": "line",
    "scope_label": "Sprint 0 · A 線 Context Entry 規格層",
    "active": True,
    "inherits_entry": True,
    "subtree_version": "sprint0-a2-v0.1",
    "subtree_priority": 10,
    "entry_refs": [
        "workflow_upgrade/01_context-entry/A0_context_entry_overview.md",
        "workflow_upgrade/01_context-entry/A1_root_context_spec.md",
        "workflow_upgrade/01_context-entry/A2_subtree_context_spec.md",
        "context/context_entry_contract.md",
    ],
    "nav_map_ref": _NAV_MAP_TEMPLATE_REF,
    "runbook_digest": [
        "一次只接一票；狀態 TODO→DOING→DONE",
        "執行期合同以 context_entry_contract 為準",
    ],
    "source": "context_entry_v0.1_mock",
}

# A-4 §8 minimal template nodes (nav auto v0.1; governance spec unchanged).
_NAV_TEMPLATE_ROOT_V01: dict[str, Any] = {
    "node_id": "root",
    "type": "root",
    "scope_label": "戰車全局接戰與 H 線入口",
    "parent_node_id": None,
    "entry_refs": [
        "AGENTS.md",
        "context/context_entry_contract.md",
        "04_Workflows/HARNESS_CONSTITUTION.md",
        "workflow_upgrade/00_master_plan.md",
        "workflow_upgrade/90_run_queue.md",
    ],
    "nav_map_ref": _NAV_MAP_TEMPLATE_REF,
}

_NAV_TEMPLATE_SUBTREES_V01: dict[str, dict[str, Any]] = {
    "line.a.context-entry": {
        "node_id": "line.a.context-entry",
        "type": "subtree",
        "line": "A",
        "mount_type": "line",
        "theme": "sprint0-f-a",
        "scope_label": "Sprint 0 · Context Entry 規格層",
        "parent_node_id": "root",
        "entry_refs": [
            "workflow_upgrade/01_context-entry/A0_context_entry_overview.md",
            "workflow_upgrade/01_context-entry/A1_root_context_spec.md",
            "workflow_upgrade/01_context-entry/A2_subtree_context_spec.md",
            "context/context_entry_contract.md",
        ],
        "nav_map_ref": _NAV_MAP_TEMPLATE_REF,
        "active_default": True,
    },
    "line.f.workflow-upgrade": {
        "node_id": "line.f.workflow-upgrade",
        "type": "subtree",
        "line": "F",
        "mount_type": "line",
        "theme": "sprint0",
        "scope_label": "Sprint 0 總控（F 線）",
        "parent_node_id": "root",
        "entry_refs": [
            "workflow_upgrade/00_master_plan.md",
            "workflow_upgrade/90_run_queue.md",
            "workflow_upgrade/01_context-entry/A0_context_entry_overview.md",
        ],
        "nav_map_ref": _NAV_MAP_TEMPLATE_REF,
        "active_default": False,
    },
}


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _normalize_task_input(task_input: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(task_input, dict):
        return {}
    out = copy.deepcopy(task_input)
    if not str(out.get("task_id") or "").strip():
        out["task_id"] = _new_id("task")
    if not str(out.get("work_order_id") or "").strip():
        out["work_order_id"] = _new_id("wo")
    return out


def _normalize_entry_refs(refs: Any) -> list[str]:
    if not isinstance(refs, list):
        return []
    out: list[str] = []
    for item in refs:
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def _entry_refs_from_root(root_context: dict[str, Any]) -> list[str]:
    """Aggregate logical navigation names from root mock (no disk paths)."""
    navigation = root_context.get("navigation")
    if not isinstance(navigation, dict):
        return []
    refs: list[str] = []
    for value in navigation.values():
        text = str(value or "").strip()
        if text and text not in refs:
            refs.append(text)
    return refs


def _normalize_subtree_record(
    raw: dict[str, Any],
    *,
    root_context: dict[str, Any],
) -> dict[str, Any]:
    base = copy.deepcopy(_DEFAULT_SUBTREE_V01)
    if isinstance(raw, dict):
        for key, value in raw.items():
            if value is not None:
                base[key] = value

    mount_type = str(base.get("mount_type") or "line").strip().lower()
    if mount_type not in _MOUNT_TYPES:
        mount_type = "line"
    base["mount_type"] = mount_type

    subtree_id = str(base.get("subtree_id") or "").strip()
    if not subtree_id:
        base["subtree_id"] = f"{mount_type}.context-entry"
    else:
        base["subtree_id"] = subtree_id

    base["scope_label"] = str(
        base.get("scope_label") or _DEFAULT_SUBTREE_V01["scope_label"]
    ).strip()
    base["active"] = bool(base.get("active", True))
    base["inherits_entry"] = bool(base.get("inherits_entry", True))

    explicit_refs = _normalize_entry_refs(base.get("entry_refs"))
    if explicit_refs:
        base["entry_refs"] = explicit_refs
    else:
        merged = _normalize_entry_refs(_DEFAULT_SUBTREE_V01.get("entry_refs"))
        for ref in _entry_refs_from_root(root_context):
            if ref not in merged:
                merged.append(ref)
        base["entry_refs"] = merged[:7]

    base.setdefault("subtree_version", "sprint0-a2-v0.1")
    base.setdefault("source", "context_entry_v0.1")
    return base


def _build_subtree_context_v01(
    task_input: dict[str, Any],
    root_context: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Minimal P0.5 subtree layer (A-2 v0.1).

    Uses task_input overrides when present; otherwise emits one active mock subtree.
    """
    raw_subtrees = task_input.get("subtrees")
    if isinstance(raw_subtrees, list) and raw_subtrees:
        records = [
            _normalize_subtree_record(item, root_context=root_context)
            for item in raw_subtrees
            if isinstance(item, dict)
        ]
    else:
        override: dict[str, Any] = {}
        if str(task_input.get("subtree_id") or "").strip():
            override["subtree_id"] = task_input.get("subtree_id")
        if str(task_input.get("subtree_mount_type") or "").strip():
            override["mount_type"] = task_input.get("subtree_mount_type")
        if str(task_input.get("subtree_scope_label") or "").strip():
            override["scope_label"] = task_input.get("subtree_scope_label")
        if task_input.get("subtree_active") is not None:
            override["active"] = task_input.get("subtree_active")
        refs = task_input.get("subtree_entry_refs")
        if refs is not None:
            override["entry_refs"] = refs
        records = [_normalize_subtree_record(override, root_context=root_context)]

    if not records:
        records = [_normalize_subtree_record({}, root_context=root_context)]

    return records


def _estimate_tokens_text(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _estimate_subtree_record_tokens(rec: dict[str, Any]) -> int:
    blob = json.dumps(
        {
            "scope_label": rec.get("scope_label"),
            "entry_refs": rec.get("entry_refs"),
            "runbook_digest": rec.get("runbook_digest"),
            "handoff_digest": rec.get("handoff_digest"),
        },
        ensure_ascii=False,
        default=str,
    )
    return _estimate_tokens_text(blob)


def _record_trim(
    trims: list[dict[str, Any]],
    *,
    subtree_id: str,
    trimmed_entries: list[str],
    reason: str,
    detail: str = "",
) -> None:
    trims.append(
        {
            "subtree_id": subtree_id,
            "trimmed_entries": trimmed_entries,
            "reason": reason,
            "detail": detail,
        }
    )


def _apply_subtree_trimming_v01(
    records: list[dict[str, Any]],
    *,
    max_active: int = _MAX_ACTIVE_SUBTREES,
    max_entry_refs: int = _MAX_ENTRY_REFS_PER_SUBTREE,
    layer_max_tokens: int = _SUBTREE_LAYER_MAX_TOKENS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    P0.5 subtree trimming (R-2 v0.1): active cap, entry_refs cap, token heuristic.

    Does not mutate ``subtree_id`` or other identity metadata; only ``active``,
    list lengths, and digest contents may change. Audit trail in returned trim meta.
    """
    trimmed = copy.deepcopy(records)
    trims: list[dict[str, Any]] = []
    tokens_before = sum(_estimate_subtree_record_tokens(r) for r in trimmed if r.get("active"))

    active_indices = [i for i, rec in enumerate(trimmed) if rec.get("active")]
    ranked_active = sorted(
        active_indices,
        key=lambda i: (-int(trimmed[i].get("subtree_priority") or 0), i),
    )
    keep_active = set(ranked_active[:max_active])
    for idx in active_indices:
        if idx in keep_active:
            continue
        rec = trimmed[idx]
        sid = str(rec.get("subtree_id") or "")
        rec["active"] = False
        _record_trim(
            trims,
            subtree_id=sid,
            trimmed_entries=[],
            reason="active_subtree_cap",
            detail=f"max_active={max_active}",
        )

    for rec in trimmed:
        refs = _normalize_entry_refs(rec.get("entry_refs"))
        if len(refs) <= max_entry_refs:
            continue
        dropped = refs[max_entry_refs:]
        rec["entry_refs"] = refs[:max_entry_refs]
        _record_trim(
            trims,
            subtree_id=str(rec.get("subtree_id") or ""),
            trimmed_entries=dropped,
            reason="entry_refs_cap",
            detail=f"max_entry_refs={max_entry_refs}",
        )

    def active_layer_tokens() -> int:
        return sum(_estimate_subtree_record_tokens(r) for r in trimmed if r.get("active"))

    while active_layer_tokens() > layer_max_tokens:
        active_idxs = [i for i, rec in enumerate(trimmed) if rec.get("active")]
        if not active_idxs:
            break

        budget_reduced = False
        by_tokens = sorted(
            active_idxs,
            key=lambda i: _estimate_subtree_record_tokens(trimmed[i]),
            reverse=True,
        )
        for idx in by_tokens:
            rec = trimmed[idx]
            sid = str(rec.get("subtree_id") or "")
            handoff = list(rec.get("handoff_digest") or [])
            if handoff:
                dropped = str(handoff.pop())
                rec["handoff_digest"] = handoff
                _record_trim(
                    trims,
                    subtree_id=sid,
                    trimmed_entries=[dropped],
                    reason="handoff_digest_cap",
                    detail="subtree_token_budget",
                )
                budget_reduced = True
                break
            runbook = list(rec.get("runbook_digest") or [])
            if len(runbook) > 1:
                dropped = str(runbook.pop())
                rec["runbook_digest"] = runbook
                _record_trim(
                    trims,
                    subtree_id=sid,
                    trimmed_entries=[dropped],
                    reason="runbook_digest_cap",
                    detail="subtree_token_budget",
                )
                budget_reduced = True
                break

        if budget_reduced:
            continue

        victim = min(
            active_idxs,
            key=lambda i: (int(trimmed[i].get("subtree_priority") or 0), i),
        )
        rec = trimmed[victim]
        sid = str(rec.get("subtree_id") or "")
        rec["active"] = False
        _record_trim(
            trims,
            subtree_id=sid,
            trimmed_entries=[],
            reason="subtree_token_budget",
            detail=f"layer_max_tokens={layer_max_tokens}",
        )

    tokens_after = sum(_estimate_subtree_record_tokens(r) for r in trimmed if r.get("active"))
    return trimmed, {
        "version": _TRIM_METADATA_VERSION,
        "applied": bool(trims),
        "trims": trims,
        "token_estimate": {
            "before": tokens_before,
            "after": tokens_after,
            "budget": layer_max_tokens,
        },
    }


def _nav_node_from_subtree_record(subtree: dict[str, Any]) -> dict[str, Any]:
    """Synthesize a minimal nav node from an A-2 subtree record."""
    subtree_id = str(subtree.get("subtree_id") or "").strip()
    if not subtree_id:
        return {}
    template = copy.deepcopy(_NAV_TEMPLATE_SUBTREES_V01.get(subtree_id, {}))
    node: dict[str, Any] = {
        "node_id": subtree_id,
        "type": "subtree",
        "subtree_id": subtree_id,
        "mount_type": str(subtree.get("mount_type") or template.get("mount_type") or "line"),
        "scope_label": str(
            subtree.get("scope_label") or template.get("scope_label") or subtree_id
        ),
        "parent_node_id": "root",
        "entry_refs": _normalize_entry_refs(
            subtree.get("entry_refs") or template.get("entry_refs")
        ),
        "nav_map_ref": str(
            subtree.get("nav_map_ref") or template.get("nav_map_ref") or _NAV_MAP_TEMPLATE_REF
        ),
        "active_default": bool(subtree.get("active", template.get("active_default", False))),
    }
    for key in ("line", "dept", "module", "theme"):
        val = subtree.get(key) if subtree.get(key) is not None else template.get(key)
        if val is not None and str(val).strip() and str(val).strip() != "-":
            node[key] = val
    return node


def _merge_nav_nodes(base: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    """Merge nav node fields: user-provided keys win; auto fills missing only."""
    out = copy.deepcopy(base)
    for key, value in user.items():
        if value is None:
            continue
        if key == "entry_refs":
            refs = _normalize_entry_refs(value)
            if refs:
                out[key] = refs
            continue
        out[key] = value
    return out


def _merge_navigation_map_v01(auto_map: dict[str, Any], user_map: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge navigation_map: user override > auto fill-missing (R-1)."""
    if not user_map:
        return auto_map
    merged = copy.deepcopy(auto_map)
    for key, value in user_map.items():
        if value is None:
            continue
        if key == "nodes" and isinstance(value, dict):
            merged_nodes = merged.setdefault("nodes", {})
            for node_id, user_node in value.items():
                if not isinstance(user_node, dict):
                    continue
                base_node = merged_nodes.get(node_id)
                if isinstance(base_node, dict):
                    merged_nodes[node_id] = _merge_nav_nodes(base_node, user_node)
                else:
                    merged_nodes[node_id] = copy.deepcopy(user_node)
            continue
        if key == "subtree_to_node" and isinstance(value, dict):
            merged.setdefault("subtree_to_node", {}).update(value)
            continue
        if key == "active_path" and isinstance(value, list) and value:
            merged["active_path"] = [str(x).strip() for x in value if str(x).strip()]
            continue
        merged[key] = value
    if "active_path" not in user_map:
        merged["active_path"] = auto_map.get("active_path", [])
    if "subtree_to_node" not in user_map:
        merged["subtree_to_node"] = auto_map.get("subtree_to_node", {})
    return merged


def _auto_navigation_map_v01(
    *,
    task_input: dict[str, Any],
    root_context: dict[str, Any],
    subtree_context: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Nav auto v0.1 (R-1): minimal navigation_map from A-4 template + subtree_context.

    Produces one primary path (active_path), node entry_refs, and subtree_id → node_id links.
    """
    _ = root_context  # reserved for future root.navigation enrichment
    nodes: dict[str, Any] = {"root": copy.deepcopy(_NAV_TEMPLATE_ROOT_V01)}
    subtree_to_node: dict[str, str] = {}
    active_path: list[str] = ["root"]

    active_subtrees = [s for s in subtree_context if isinstance(s, dict) and s.get("active")]
    if not active_subtrees:
        active_subtrees = [s for s in subtree_context if isinstance(s, dict)]

    for subtree in active_subtrees:
        node = _nav_node_from_subtree_record(subtree)
        if not node:
            continue
        node_id = str(node.get("node_id") or "")
        if not node_id:
            continue
        template_node = _NAV_TEMPLATE_SUBTREES_V01.get(node_id, {})
        if template_node:
            # Nav index uses A-4 template entry_refs; subtree supplies identity only.
            merged = copy.deepcopy(template_node)
            for key in (
                "scope_label",
                "mount_type",
                "line",
                "dept",
                "module",
                "theme",
                "active_default",
            ):
                val = node.get(key)
                if val is not None and str(val).strip():
                    merged[key] = val
            merged["subtree_id"] = str(subtree.get("subtree_id") or node_id)
            node = merged
        nodes[node_id] = node
        sid = str(subtree.get("subtree_id") or node_id)
        subtree_to_node[sid] = node_id
        if node_id not in active_path:
            active_path.append(node_id)

    if len(active_path) == 1 and "line.a.context-entry" in nodes:
        active_path.append("line.a.context-entry")
        subtree_to_node.setdefault("line.a.context-entry", "line.a.context-entry")

    auto_map: dict[str, Any] = {
        "version": "nav-auto-v0.1",
        "nav_map_ref": _NAV_MAP_TEMPLATE_REF,
        "active_path": active_path,
        "nodes": nodes,
        "subtree_to_node": subtree_to_node,
        "source": "nav_auto_v0.1",
    }

    user_map = task_input.get("navigation_map")
    if not isinstance(user_map, dict):
        user_map = {}
    return _merge_navigation_map_v01(auto_map, user_map)


def _attach_navigation_map_v01(
    *,
    task_input: dict[str, Any],
    root_context: dict[str, Any],
    subtree_context: list[dict[str, Any]],
    result: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build navigation_map and attach to metadata + result (single hook)."""
    nav_map = _auto_navigation_map_v01(
        task_input=task_input,
        root_context=root_context,
        subtree_context=subtree_context,
    )
    metadata["navigation_map"] = nav_map
    metadata["navigation_map_version"] = "v0.1"
    result["navigation_map"] = nav_map
    return nav_map


def _deny_gate_pre_injection(task_input: dict[str, Any]) -> dict[str, Any] | None:
    """Gate-1: deny before ``build_context`` (A-3 step ①, P0 on task_input)."""
    return _DENY_RUNNER.run_hit("pre_injection", {"task_input": task_input})


def _deny_gate_post_assembly(
    *,
    result: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any] | None:
    """Gate-2: deny after ``build_context`` (A-3 step ⑤, P1 on assembled layers)."""
    return _DENY_RUNNER.run_hit(
        "post_assembly",
        {"result": result, "metadata": metadata},
    )


def _deny_gate_subtree(
    *,
    result: dict[str, Any],
    subtree_context: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Gate-3: subtree deny union scan (A-3 step ③, P0.5 on active subtree layer)."""
    root_context = result.get("root_context")
    if not isinstance(root_context, dict):
        root_context = {}
    deny_union = merge_subtree_deny_union(
        root_context=root_context,
        subtree_context=subtree_context,
    )
    return _DENY_RUNNER.run_hit(
        "subtree",
        {
            "result": result,
            "subtree_context": subtree_context,
            "deny_union": deny_union,
        },
        extra={
            "subtree": {
                "active_subtree_ids": deny_union.get("active_subtree_ids") or [],
                "deny_union": deny_union,
            }
        },
    )


def _build_deny_response(
    *,
    entry_mode: str,
    normalized_input: dict[str, Any],
    deny: dict[str, Any],
) -> dict[str, Any]:
    deny_types = deny.get("deny_types") or []
    gate = str(deny.get("gate") or "deny")
    message = f"context denied ({gate}): {', '.join(deny_types)}"
    meta = {
        "source": entry_mode,
        "entry_mode": entry_mode,
        "entry": "context_entry",
        "task_id": normalized_input.get("task_id"),
        "work_order_id": normalized_input.get("work_order_id"),
        "deny": deny,
    }
    return {
        "ok": False,
        "message": message,
        "root_context": {},
        "subtree_context": [],
        "working_context": {},
        "long_term_memory": {},
        "token_usage": _normalize_token_usage({}),
        "result": {},
        "metadata": meta,
        "task_input": normalized_input,
    }


def _apply_pre_context_entry_hooks(
    normalized_input: dict[str, Any],
    *,
    entry_mode: str,
) -> dict[str, Any]:
    """Optional B-1 pre-hook; no-op when hooks disabled."""
    try:
        from hooks.context_entry_hooks import apply_pre_context_entry_hooks
    except ImportError:
        return normalized_input
    payload = apply_pre_context_entry_hooks(
        {"task_input": normalized_input, "entry_mode": entry_mode}
    )
    ti = payload.get("task_input")
    return ti if isinstance(ti, dict) else normalized_input


def _apply_post_context_entry_hooks(response: dict[str, Any]) -> dict[str, Any]:
    """Optional B-1 post-hook; no-op when hooks disabled."""
    try:
        from hooks.context_entry_hooks import apply_post_context_entry_hooks
    except ImportError:
        return response
    return apply_post_context_entry_hooks(response)


def _normalize_token_usage(raw: dict[str, Any] | None) -> dict[str, int]:
    usage = dict(raw) if isinstance(raw, dict) else {}
    total = int(usage.get("total_tokens") or usage.get("total") or 0)
    return {
        "root": int(usage.get("root", 0)),
        "working": int(usage.get("working", 0)),
        "memory": int(usage.get("memory", 0)),
        "total": total,
        "total_tokens": total,
    }


def build_rooted_context(
    task_input: dict[str, Any] | None,
    *,
    mode: str = "ask_pipeline",
) -> dict[str, Any]:
    """
    Context entry contract for ask-like and long-task pipelines.

    Parameters
    ----------
    task_input:
        Passed to ``build_context`` after ``task_id`` / ``work_order_id`` defaults.
    mode:
        Trace label stored in ``metadata.entry_mode`` and ``metadata.source``.

    Returns
    -------
    dict
        ``build_context`` contract plus promoted layers:
        ``root_context``, ``subtree_context``, ``working_context``, ``long_term_memory``,
        ``token_usage``, and normalized ``task_input``.
    """
    entry_mode = mode if mode in _ENTRY_MODES else "ask_pipeline"
    normalized_input = _normalize_task_input(task_input)
    normalized_input = _apply_pre_context_entry_hooks(
        normalized_input,
        entry_mode=entry_mode,
    )

    pre_deny = _deny_gate_pre_injection(normalized_input)
    if pre_deny is not None:
        return _apply_post_context_entry_hooks(
            _build_deny_response(
                entry_mode=entry_mode,
                normalized_input=normalized_input,
                deny=pre_deny,
            )
        )

    if not normalized_input and task_input is not None and not isinstance(task_input, dict):
        return _apply_post_context_entry_hooks(
            {
                "ok": False,
                "message": "task_input must be a dict",
                "root_context": {},
                "subtree_context": [],
                "working_context": {},
                "long_term_memory": {},
                "token_usage": _normalize_token_usage({}),
                "result": {},
                "metadata": {
                    "source": entry_mode,
                    "entry_mode": entry_mode,
                    "entry": "context_entry",
                },
                "task_input": {},
            }
        )

    built = build_context(normalized_input)
    result = (
        copy.deepcopy(built.get("result"))
        if isinstance(built.get("result"), dict)
        else {}
    )
    meta = copy.deepcopy(built.get("metadata")) if isinstance(built.get("metadata"), dict) else {}

    post_deny = _deny_gate_post_assembly(result=result, metadata=meta)
    if post_deny is not None:
        return _apply_post_context_entry_hooks(
            _build_deny_response(
                entry_mode=entry_mode,
                normalized_input=normalized_input,
                deny=post_deny,
            )
        )

    root_context = result.get("root_context") or {}
    subtree_context, trim_meta = _apply_subtree_trimming_v01(
        _build_subtree_context_v01(normalized_input, root_context)
    )
    result["subtree_context"] = subtree_context
    _attach_navigation_map_v01(
        task_input=normalized_input,
        root_context=root_context,
        subtree_context=subtree_context,
        result=result,
        metadata=meta,
    )

    subtree_deny = _deny_gate_subtree(result=result, subtree_context=subtree_context)
    if subtree_deny is not None:
        return _apply_post_context_entry_hooks(
            _build_deny_response(
                entry_mode=entry_mode,
                normalized_input=normalized_input,
                deny=subtree_deny,
            )
        )

    raw_usage = meta.get("token_usage") if isinstance(meta.get("token_usage"), dict) else {}
    token_usage = _normalize_token_usage(raw_usage)

    meta["token_usage"] = token_usage
    meta["source"] = entry_mode
    meta["entry_mode"] = entry_mode
    meta["entry"] = "context_entry"
    meta["task_id"] = normalized_input.get("task_id")
    meta["work_order_id"] = normalized_input.get("work_order_id")
    meta["subtree_context_version"] = "v0.1"
    meta["subtree_active_count"] = sum(1 for s in subtree_context if s.get("active"))
    meta["trim"] = trim_meta
    meta["deny"] = attach_deny_observability(
        {"denied": False, "gate": None, "deny_types": []}
    )

    return _apply_post_context_entry_hooks(
        {
            "ok": bool(built.get("ok")),
            "message": str(built.get("message") or ""),
            "root_context": root_context,
            "subtree_context": subtree_context,
            "working_context": result.get("working_context") or {},
            "long_term_memory": result.get("long_term_memory") or {},
            "token_usage": token_usage,
            "result": result,
            "metadata": meta,
            "task_input": normalized_input,
        }
    )
