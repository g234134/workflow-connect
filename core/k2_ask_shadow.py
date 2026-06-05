"""
K-2 ↔ ask mainline shadow comparison (dev/test only).

Runs the legacy ``run_ask_flow`` and ``run_k2_flow`` against the same logical
task_input, normalizes outputs, and emits a structured diff report. Does not
wire into ``/api/ask`` or production routes.

See ``tests/test_k2_ask_shadow.py`` and ``ASK_MERGE_INTERFACE`` in
``core.langgraph_flow_k2``.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Callable, Mapping, Sequence

# Fields compared in shadow reports (normalized summaries).
SHADOW_COMPARE_FIELDS: tuple[str, ...] = (
    "ok",
    "status",
    "message_preview",
    "answer_preview",
    "retry_count",
    "handoff_count",
    "error_type",
    "context_entry_mode",
    "has_eval_metadata",
    "executed_node_count",
    "selector_use_rag",
    "selector_rule_id",
    "retrieve_fallback",
    "tags",
)

# Layered profile fields for governance diff (compare_shadow_profiles).
SHADOW_PROFILE_LAYERS: dict[str, tuple[str, ...]] = {
    "functional": ("ok", "status", "answer_preview"),
    "orchestration": ("handoff_count", "executed_node_count", "retry_count"),
    "strategy": ("selector_use_rag", "selector_rule_id", "retrieve_fallback"),
    "observability": ("has_eval_metadata", "error_type", "tags", "context_entry_mode"),
}

# Fields that are expected to differ until merge adapter lands (not merge blockers).
EXPECTED_DIFF_FIELDS: frozenset[str] = frozenset(
    {
        "message_preview",
        "answer_preview",
        "context_entry_mode",
        "has_eval_metadata",
        "executed_node_count",
        "selector_use_rag",
        "selector_rule_id",
        "tags",
    }
)

# Fields requiring governance decision before partial traffic merge.
UNCERTAIN_DIFF_FIELDS: frozenset[str] = frozenset(
    {
        "handoff_count",
        "retry_count",
        "retrieve_fallback",
    }
)

# Fields that must align for safe merge (hard gate).
INVARIANT_DIFF_FIELDS: frozenset[str] = frozenset({"ok", "status", "error_type"})

_TRUNC = 120


def _trunc(value: Any, *, limit: int = _TRUNC) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_tags(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return sorted({str(t) for t in raw if t is not None})


def _extract_ask_tags(out: Mapping[str, Any]) -> list[str]:
    tags: set[str] = set()
    ibridge = out.get("ibridge_v0") if isinstance(out.get("ibridge_v0"), dict) else {}
    selector = ibridge.get("selector_decision") if isinstance(ibridge.get("selector_decision"), dict) else {}
    for key in ("tags", "selector_tags"):
        tags.update(_normalize_tags(selector.get(key)))
    answer = out.get("answer") if isinstance(out.get("answer"), dict) else {}
    if answer.get("retrieve_fallback"):
        tags.add("retrieve_fallback")
    if answer.get("retrieve_error_type"):
        tags.add(str(answer.get("retrieve_error_type")))
    return sorted(tags)


def _answer_similarity(left: str, right: str) -> float:
    """Coarse answer alignment score in [0, 1]; not byte-identical equality."""
    a = (left or "").strip().lower()
    b = (right or "").strip().lower()
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return round(SequenceMatcher(None, a, b).ratio(), 3)


def map_task_input_for_k2(
    task_input: Mapping[str, Any],
    *,
    default_goal: str = "",
) -> dict[str, Any]:
    """
    ASK_MERGE_INTERFACE entry adapter: ask-shaped task_input → K-2 initial state input.

    Preserves ``task_id``, ``goal``, ``query``; passes through optional thread/session hints.
    """
    ti = dict(task_input)
    goal = str(ti.get("goal") or ti.get("query") or default_goal or "")
    ti.setdefault("task_id", "k2-shadow")
    ti.setdefault("goal", goal)
    ti.setdefault("query", goal)
    return ti


def build_shadow_task_input(
    *,
    task_id: str,
    query: str,
    top_k: int = 3,
    thread_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Shared task_input for both pipelines (aligned with ``build_ask_task_input``)."""
    ti: dict[str, Any] = {
        "task_id": task_id,
        "goal": query,
        "query": query,
        "semantic_top_k": top_k,
        "top_k": top_k,
    }
    if thread_id:
        ti["thread_id"] = thread_id
    if session_id:
        ti["session_id"] = session_id
    return ti


def _derive_status(ok: Any, *, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    if ok is True:
        return "success"
    if ok is False:
        return "fail"
    return "unknown"


def summarize_ask_output(out: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize ask LangGraph payload for shadow diff."""
    answer_block = out.get("answer")
    answer_text = None
    if isinstance(answer_block, dict):
        answer_text = answer_block.get("answer") or answer_block.get("message")
    elif answer_block is not None:
        answer_text = answer_block

    errors = out.get("errors") or []
    error_type = None
    if errors:
        error_type = errors[0] if isinstance(errors[0], str) else str(errors[0])

    bridge = out.get("ibridge_record") if isinstance(out.get("ibridge_record"), dict) else {}
    retry_count = _safe_int(bridge.get("retry_count"))
    handoff_count = _safe_int(bridge.get("handoff_count"))

    selector = out.get("ask_selector") if isinstance(out.get("ask_selector"), dict) else {}
    ibridge = out.get("ibridge_v0") if isinstance(out.get("ibridge_v0"), dict) else {}
    selector_decision = (
        ibridge.get("selector_decision") if isinstance(ibridge.get("selector_decision"), dict) else {}
    )
    answer_block = out.get("answer") if isinstance(out.get("answer"), dict) else {}
    retrieve_fallback = bool(
        answer_block.get("retrieve_fallback") or selector_decision.get("retrieve_fallback")
    )
    entry_mode = None
    if isinstance(ibridge, dict) and ibridge:
        entry_mode = "ask_pipeline"
    elif isinstance(out.get("_context_entry_payload"), dict):
        meta = (out.get("_context_entry_payload") or {}).get("metadata") or {}
        if isinstance(meta, dict):
            entry_mode = meta.get("entry_mode")

    return {
        "pipeline": "ask",
        "ok": out.get("ok"),
        "status": _derive_status(out.get("ok")),
        "message_preview": _trunc(out.get("message")),
        "answer_preview": _trunc(answer_text),
        "retry_count": retry_count,
        "handoff_count": handoff_count,
        "error_type": error_type or (ibridge.get("error_type") if isinstance(ibridge, dict) else None),
        "context_entry_mode": entry_mode,
        "has_eval_metadata": False,
        "executed_node_count": len(out.get("executed_nodes") or []),
        "selector_use_rag": selector.get("use_rag"),
        "selector_rule_id": selector.get("selector_rule_id"),
        "retrieve_fallback": retrieve_fallback,
        "tags": _extract_ask_tags(out),
    }


def summarize_k2_output(out: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize K-2 ``run_k2_flow`` payload for shadow diff."""
    state = out.get("state") if isinstance(out.get("state"), dict) else {}
    record = out.get("record") if isinstance(out.get("record"), dict) else {}
    final = state.get("final_result") if isinstance(state.get("final_result"), dict) else {}
    ctx = state.get("context_payload") if isinstance(state.get("context_payload"), dict) else {}
    meta = ctx.get("metadata") if isinstance(ctx.get("metadata"), dict) else {}
    eval_meta = out.get("eval_metadata") if isinstance(out.get("eval_metadata"), dict) else {}

    result = final.get("result") if isinstance(final.get("result"), dict) else {}
    answer_preview = result.get("summary") or result.get("answer") or final.get("message")
    retrieve_skill = (
        (state.get("skill_results") or {}).get("retrieve")
        if isinstance(state.get("skill_results"), dict)
        else {}
    )
    if not isinstance(retrieve_skill, dict):
        retrieve_skill = {}
    eval_gate = eval_meta.get("eval_gate") if isinstance(eval_meta.get("eval_gate"), dict) else {}
    tags = _normalize_tags(eval_gate.get("tags"))
    if state.get("recovery_route") == "reviewer_fallback":
        tags = sorted(set(tags) | {"reviewer_fallback"})
    if retrieve_skill.get("retry_count", 0):
        tags = sorted(set(tags) | {"retrieve_retry"})

    return {
        "pipeline": "k2",
        "ok": out.get("ok"),
        "status": _derive_status(out.get("ok"), explicit=str(final.get("status") or "")),
        "message_preview": _trunc(out.get("message") or final.get("message")),
        "answer_preview": _trunc(answer_preview),
        "retry_count": _safe_int(record.get("retry_count")),
        "handoff_count": _safe_int(record.get("handoff_count")),
        "error_type": state.get("error_type") or final.get("error_type"),
        "context_entry_mode": meta.get("entry_mode"),
        "has_eval_metadata": bool(eval_meta),
        "executed_node_count": 0,
        "selector_use_rag": None,
        "selector_rule_id": "K2-N/A",
        "retrieve_fallback": bool(state.get("recovery_route") == "reviewer_fallback"),
        "tags": tags,
    }


def compare_shadow_summaries(
    ask_summary: Mapping[str, Any],
    k2_summary: Mapping[str, Any],
    *,
    fields: Sequence[str] = SHADOW_COMPARE_FIELDS,
) -> dict[str, Any]:
    """
    Compare normalized summaries field-wise.

    Returns ``{ok, matched_fields, mismatched, only_ask, only_k2}`` where ``ok`` means
    no mismatches on compared scalar fields (pipelines may still differ structurally).
    """
    mismatched: dict[str, dict[str, Any]] = {}
    matched: list[str] = []

    for field in fields:
        a_val = ask_summary.get(field)
        k_val = k2_summary.get(field)
        if a_val == k_val:
            matched.append(field)
        else:
            mismatched[field] = {"ask": a_val, "k2": k_val}

    return {
        "ok": len(mismatched) == 0,
        "matched_fields": matched,
        "mismatched": mismatched,
        "ask_summary": dict(ask_summary),
        "k2_summary": dict(k2_summary),
    }


def _layer_match(
    ask_summary: Mapping[str, Any],
    k2_summary: Mapping[str, Any],
    fields: Sequence[str],
) -> tuple[bool, dict[str, dict[str, Any]]]:
    mismatched: dict[str, dict[str, Any]] = {}
    for field in fields:
        a_val = ask_summary.get(field)
        k_val = k2_summary.get(field)
        if a_val != k_val:
            mismatched[field] = {"ask": a_val, "k2": k_val}
    return len(mismatched) == 0, mismatched


def _classify_mismatches(
    mismatched: Mapping[str, Mapping[str, Any]],
    *,
    ask_summary: Mapping[str, Any],
    k2_summary: Mapping[str, Any],
    answer_similarity: float,
) -> dict[str, list[str]]:
    expected: list[str] = []
    uncertain: list[str] = []
    unacceptable: list[str] = []

    for field in mismatched:
        if field in INVARIANT_DIFF_FIELDS:
            unacceptable.append(field)
        elif field in EXPECTED_DIFF_FIELDS:
            expected.append(field)
        elif field in UNCERTAIN_DIFF_FIELDS:
            uncertain.append(field)
        else:
            uncertain.append(field)

    if (
        "answer_preview" not in mismatched
        and answer_similarity < 0.25
        and ask_summary.get("ok") is k2_summary.get("ok") is True
    ):
        uncertain.append("answer_similarity_low")

    if ask_summary.get("ok") is True and k2_summary.get("ok") is False:
        unacceptable.append("functional_ok_regression")
    if ask_summary.get("ok") is False and k2_summary.get("ok") is True:
        uncertain.append("k2_recovered_where_ask_failed")

    return {
        "expected": sorted(set(expected)),
        "uncertain": sorted(set(uncertain)),
        "unacceptable": sorted(set(unacceptable)),
    }


def compare_shadow_profiles(
    ask_summary: Mapping[str, Any],
    k2_summary: Mapping[str, Any],
    *,
    case_name: str = "",
    answer_similarity_threshold: float = 0.25,
) -> dict[str, Any]:
    """
    Layered shadow diff for governance baseline.

    Returns structured profile with functional / orchestration / strategy /
    observability layer matches, answer similarity, and diff classification
    (expected / uncertain / unacceptable).
    """
    base = compare_shadow_summaries(ask_summary, k2_summary)
    answer_sim = _answer_similarity(
        str(ask_summary.get("answer_preview") or ""),
        str(k2_summary.get("answer_preview") or ""),
    )

    layers: dict[str, Any] = {}
    for layer_name, layer_fields in SHADOW_PROFILE_LAYERS.items():
        matched, layer_mismatched = _layer_match(ask_summary, k2_summary, layer_fields)
        layers[layer_name] = {
            "match": matched,
            "mismatched": layer_mismatched,
            "fields": list(layer_fields),
        }

    classification = _classify_mismatches(
        base.get("mismatched") or {},
        ask_summary=ask_summary,
        k2_summary=k2_summary,
        answer_similarity=answer_sim,
    )

    functional_ok = bool(layers.get("functional", {}).get("match"))
    if ask_summary.get("ok") is k2_summary.get("ok") is True:
        functional_ok = functional_ok or answer_sim >= answer_similarity_threshold

    merge_safe = (
        not classification.get("unacceptable")
        and ask_summary.get("ok") == k2_summary.get("ok")
    )

    return {
        "ok": base.get("ok"),
        "case_name": case_name,
        "answer_similarity": answer_sim,
        "functional_ok": functional_ok,
        "merge_safe": merge_safe,
        "layers": layers,
        "classification": classification,
        "matched_fields": base.get("matched_fields"),
        "mismatched": base.get("mismatched"),
        "ask_summary": dict(ask_summary),
        "k2_summary": dict(k2_summary),
    }


def format_shadow_report(case_name: str, comparison: Mapping[str, Any]) -> str:
    """Human-readable multi-line report for test logs."""
    lines = [
        f"=== shadow: {case_name} ===",
        f"match_ok={comparison.get('ok')}",
    ]
    if "answer_similarity" in comparison:
        lines.append(f"  answer_similarity={comparison.get('answer_similarity')}")
    if "merge_safe" in comparison:
        lines.append(f"  merge_safe={comparison.get('merge_safe')}")
    for field, delta in (comparison.get("mismatched") or {}).items():
        lines.append(f"  DIFF {field}: ask={delta.get('ask')!r} k2={delta.get('k2')!r}")
    if not comparison.get("mismatched"):
        lines.append("  (all compared fields equal)")
    classification = comparison.get("classification") or {}
    if classification:
        lines.append(f"  expected_diffs={classification.get('expected')}")
        lines.append(f"  uncertain_diffs={classification.get('uncertain')}")
        lines.append(f"  unacceptable_diffs={classification.get('unacceptable')}")
    ask_s = comparison.get("ask_summary") or {}
    k2_s = comparison.get("k2_summary") or {}
    lines.append(
        f"  ask: ok={ask_s.get('ok')} nodes={ask_s.get('executed_node_count')} "
        f"retry={ask_s.get('retry_count')} selector_rag={ask_s.get('selector_use_rag')} "
        f"fallback={ask_s.get('retrieve_fallback')}"
    )
    lines.append(
        f"  k2: ok={k2_s.get('ok')} entry_mode={k2_s.get('context_entry_mode')} "
        f"eval={k2_s.get('has_eval_metadata')} handoff={k2_s.get('handoff_count')} "
        f"retry={k2_s.get('retry_count')} tags={k2_s.get('tags')}"
    )
    return "\n".join(lines)


def run_shadow_pair(
    *,
    case_name: str,
    query: str,
    top_k: int = 3,
    task_id_prefix: str = "shadow",
    run_ask: Callable[..., dict[str, Any]],
    run_k2: Callable[..., dict[str, Any]],
    ask_kwargs: Mapping[str, Any] | None = None,
    k2_kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Execute ask mainline + K-2 on the same logical input; return comparison dict.

    ``run_ask`` / ``run_k2`` are injected so tests can apply mocks without touching API.

    Note: in tests that reload ``core`` between gov (ask) and repo (K-2), call ``run_ask``
    before importing K-2 modules, or invoke this helper without a prior ``_purge_core_modules``.
    """
    ask_kw = dict(ask_kwargs or {})
    k2_kw = dict(k2_kwargs or {})
    base_id = f"{task_id_prefix}-{case_name}"

    task_input = build_shadow_task_input(
        task_id=f"{base_id}-shared",
        query=query,
        top_k=top_k,
        thread_id=str(ask_kw.pop("thread_id", base_id)),
    )

    ask_out = run_ask(
        query,
        top_k=top_k,
        thread_id=task_input.get("thread_id"),
        session_id=task_input.get("session_id"),
        **ask_kw,
    )

    k2_ti = map_task_input_for_k2(task_input, default_goal=query)
    k2_out = run_k2(
        task_id=f"{base_id}-k2",
        goal=query,
        task_input=k2_ti,
        **k2_kw,
    )

    ask_summary = summarize_ask_output(ask_out)
    k2_summary = summarize_k2_output(k2_out)
    comparison = compare_shadow_profiles(
        ask_summary,
        k2_summary,
        case_name=case_name,
    )
    comparison["report"] = format_shadow_report(case_name, comparison)
    comparison["ask_raw_ok"] = ask_out.get("ok")
    comparison["k2_raw_ok"] = k2_out.get("ok")
    return comparison


# --- Merge hook draft (not wired to /api/ask) ---------------------------------


def k2_result_to_ask_response_envelope(
    k2_result: Mapping[str, Any],
    *,
    query: str,
    top_k: int = 3,
    include_eval: bool = True,
) -> dict[str, Any]:
    """
    Map K-2 ``run_k2_flow`` output to an ask-shaped response envelope.

    Draft for future merge hook; mirrors ``run_ask_flow`` top-level keys where possible.
    Does not invoke LangGraph ask nodes.
    """
    state = k2_result.get("state") if isinstance(k2_result.get("state"), dict) else {}
    record = k2_result.get("record") if isinstance(k2_result.get("record"), dict) else {}
    final = state.get("final_result") if isinstance(state.get("final_result"), dict) else {}
    result_body = final.get("result") if isinstance(final.get("result"), dict) else {}

    answer_payload: dict[str, Any] = {
        "ok": bool(k2_result.get("ok")),
        "message": final.get("message") or k2_result.get("message"),
        "query": query,
        "top_k": top_k,
        "answer": result_body.get("summary") or result_body.get("answer") or "",
        "source": "k2_merge_hook",
    }

    envelope: dict[str, Any] = {
        "mode": "ask",
        "query": query,
        "top_k": top_k,
        "ok": bool(k2_result.get("ok")),
        "message": str(k2_result.get("message") or final.get("message") or ""),
        "answer": answer_payload,
        "retrieve": (state.get("skill_results") or {}).get("retrieve"),
        "errors": [] if k2_result.get("ok") else [str(state.get("error_type") or "k2_fail")],
        "executed_nodes": ["k2_shadow_merge"],
    }

    if include_eval:
        eval_meta = k2_result.get("eval_metadata")
        if isinstance(eval_meta, dict) and eval_meta:
            envelope["k2_eval_metadata"] = eval_meta
        if record:
            envelope["k2_metrics_record"] = {
                "retry_count": record.get("retry_count"),
                "handoff_count": record.get("handoff_count"),
                "success": record.get("success"),
                "trace_completeness": record.get("trace_completeness"),
            }

    return envelope


def ask_response_envelope(
    ask_result: Mapping[str, Any],
    *,
    eval_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Stable ask API envelope wrapper (pass-through with optional eval overlay).

    Used by merge hook tests to document target shape when blending K-2 eval metadata
    into an existing ask payload without replacing node outputs.
    """
    out = dict(ask_result)
    if eval_metadata:
        out["k2_eval_metadata"] = dict(eval_metadata)
    return out
