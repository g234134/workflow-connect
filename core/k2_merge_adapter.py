"""
K-2 ↔ ask merge adapter (dev/test / shadow only).

Single switch point for future partial-traffic merge: callers run ask + K-2 in shadow,
then pass both payloads through ``merge_ask_and_k2`` without touching ``/api/ask``.

Strategy: ``docs/k2_merge_strategy.md``.
Envelope helpers: ``core.k2_ask_shadow`` (``ASK_MERGE_INTERFACE`` exit hooks).
"""

from __future__ import annotations

from typing import Any, Literal, Mapping

from core.k2_ask_shadow import ask_response_envelope, k2_result_to_ask_response_envelope

MergePrimarySource = Literal["ask", "k2"]
MergeGateResult = Literal["pass", "needs_review", "fail"]

STRATEGY_VERSION = "v0.1"

# Tags that fail the merged envelope even when ask succeeded (aligns with eval_ci_check).
SEVERE_EVAL_TAGS: frozenset[str] = frozenset({"infra_risk"})

# Tags that surface needs_review but do not force ok=False when ask succeeded.
REVIEW_EVAL_TAGS: frozenset[str] = frozenset(
    {
        "high_retry",
        "context_heavy",
        "many_handoffs",
        "observability_gap",
        "retrieve_retry",
    }
)


def _pipeline_ok(result: Mapping[str, Any]) -> bool:
    return result.get("ok") is True


def _extract_k2_eval_tags(k2_result: Mapping[str, Any]) -> list[str]:
    eval_meta = k2_result.get("eval_metadata")
    if not isinstance(eval_meta, dict):
        return []
    gate = eval_meta.get("eval_gate")
    if not isinstance(gate, dict):
        return []
    raw_tags = gate.get("tags")
    if not isinstance(raw_tags, list):
        return []
    return sorted({str(t) for t in raw_tags if t is not None})


def _extract_k2_error_type(k2_result: Mapping[str, Any]) -> str | None:
    state = k2_result.get("state") if isinstance(k2_result.get("state"), dict) else {}
    final = state.get("final_result") if isinstance(state.get("final_result"), dict) else {}
    raw = state.get("error_type") or final.get("error_type")
    return str(raw) if raw is not None else None


def _extract_ask_error_type(ask_result: Mapping[str, Any]) -> str | None:
    errors = ask_result.get("errors") or []
    if errors:
        first = errors[0]
        return first if isinstance(first, str) else str(first)
    answer = ask_result.get("answer") if isinstance(ask_result.get("answer"), dict) else {}
    raw = answer.get("retrieve_error_type")
    return str(raw) if raw is not None else None


def _classify_k2_eval(tags: list[str]) -> tuple[MergeGateResult, list[str], bool]:
    """
    Returns (gate_result, severe_tags, ci_fail).

    ``infra_risk`` forces fail + CI fail per merge strategy §2.2.
    """
    severe = [t for t in tags if t in SEVERE_EVAL_TAGS]
    if severe:
        return "fail", severe, True
    review = [t for t in tags if t in REVIEW_EVAL_TAGS]
    if review:
        return "needs_review", review, False
    return "pass", [], False


def _build_merge_meta(
    *,
    primary_source: MergePrimarySource,
    gate_result: MergeGateResult,
    decision: str,
    ci_fail: bool,
    ask_ok: bool,
    k2_ok: bool,
    k2_tags: list[str],
    severe_tags: list[str],
    ask_error_type: str | None,
    k2_error_type: str | None,
) -> dict[str, Any]:
    return {
        "strategy_version": STRATEGY_VERSION,
        "primary_source": primary_source,
        "gate_result": gate_result,
        "decision": decision,
        "ci_fail": ci_fail,
        "ask_ok": ask_ok,
        "k2_ok": k2_ok,
        "k2_eval_tags": k2_tags,
        "k2_severe_tags": severe_tags,
        "ask_error_type": ask_error_type,
        "k2_error_type": k2_error_type,
        "dev_only": True,
    }


def merge_ask_and_k2(
    ask_result: Mapping[str, Any],
    k2_result: Mapping[str, Any],
    *,
    query: str,
    top_k: int,
    include_eval_in_envelope: bool = True,
) -> dict[str, Any]:
    """
    Merge ask mainline and K-2 shadow outputs into a single ask-shaped envelope.

    Production owner remains **ask** until governance enables K-2 partial traffic.
    K-2 eval metadata is attached for shadow observability; severe ``infra_risk``
    can force ``ok=False`` even when ask succeeded.

    Returns an ask-compatible dict plus ``k2_merge`` governance block (dev/test).
    """
    ask_ok = _pipeline_ok(ask_result)
    k2_ok = _pipeline_ok(k2_result)
    k2_tags = _extract_k2_eval_tags(k2_result)
    eval_gate_result, severe_tags, ci_fail = _classify_k2_eval(k2_tags)
    ask_error_type = _extract_ask_error_type(ask_result)
    k2_error_type = _extract_k2_error_type(k2_result)

    k2_envelope = k2_result_to_ask_response_envelope(
        k2_result,
        query=query,
        top_k=top_k,
        include_eval=include_eval_in_envelope,
    )
    eval_meta = k2_envelope.get("k2_eval_metadata") if include_eval_in_envelope else None

    # --- Both pipelines succeeded ------------------------------------------------
    if ask_ok and k2_ok:
        if eval_gate_result == "fail":
            merged = ask_response_envelope(ask_result, eval_metadata=eval_meta)
            merged["ok"] = False
            merged["errors"] = list(merged.get("errors") or [])
            merged["errors"].append(f"k2_merge:severe_eval:{','.join(severe_tags)}")
            merge_meta = _build_merge_meta(
                primary_source="ask",
                gate_result="fail",
                decision="both_ok_k2_severe_eval_fallback_ask_content",
                ci_fail=True,
                ask_ok=True,
                k2_ok=True,
                k2_tags=k2_tags,
                severe_tags=severe_tags,
                ask_error_type=ask_error_type,
                k2_error_type=k2_error_type,
            )
        else:
            merged = ask_response_envelope(ask_result, eval_metadata=eval_meta)
            decision = "both_ok_ask_primary"
            gate: MergeGateResult = eval_gate_result
            if gate == "pass" and k2_tags:
                gate = "needs_review"
            merge_meta = _build_merge_meta(
                primary_source="ask",
                gate_result=gate,
                decision=decision,
                ci_fail=ci_fail,
                ask_ok=True,
                k2_ok=True,
                k2_tags=k2_tags,
                severe_tags=severe_tags,
                ask_error_type=ask_error_type,
                k2_error_type=k2_error_type,
            )
            if k2_envelope.get("answer"):
                merge_meta["k2_answer_preview"] = (
                    (k2_envelope.get("answer") or {}).get("answer")
                )

    # --- Ask ok, K-2 failed ------------------------------------------------------
    elif ask_ok and not k2_ok:
        merged = ask_response_envelope(ask_result, eval_metadata=None)
        merge_meta = _build_merge_meta(
            primary_source="ask",
            gate_result="needs_review",
            decision="ask_ok_k2_fail_use_ask",
            ci_fail=False,
            ask_ok=True,
            k2_ok=False,
            k2_tags=k2_tags,
            severe_tags=severe_tags,
            ask_error_type=ask_error_type,
            k2_error_type=k2_error_type,
        )
        if include_eval_in_envelope and eval_meta:
            merged["k2_eval_metadata"] = eval_meta

    # --- Ask failed, K-2 ok (conservative: keep ask failure) ---------------------
    elif not ask_ok and k2_ok:
        merged = ask_response_envelope(ask_result, eval_metadata=eval_meta)
        merge_meta = _build_merge_meta(
            primary_source="ask",
            gate_result="needs_review",
            decision="ask_fail_k2_ok_keep_ask_failure",
            ci_fail=False,
            ask_ok=False,
            k2_ok=True,
            k2_tags=k2_tags,
            severe_tags=severe_tags,
            ask_error_type=ask_error_type,
            k2_error_type=k2_error_type,
        )
        merge_meta["k2_recovered"] = True
        if k2_envelope.get("answer"):
            merge_meta["k2_answer_preview"] = (
                (k2_envelope.get("answer") or {}).get("answer")
            )

    # --- Both failed -------------------------------------------------------------
    else:
        merged = ask_response_envelope(ask_result, eval_metadata=eval_meta)
        errors = list(merged.get("errors") or [])
        if k2_error_type and k2_error_type not in errors:
            errors.append(f"k2:{k2_error_type}")
        merged["errors"] = errors
        merge_meta = _build_merge_meta(
            primary_source="ask",
            gate_result="fail",
            decision="both_fail_ask_envelope",
            ci_fail=True,
            ask_ok=False,
            k2_ok=False,
            k2_tags=k2_tags,
            severe_tags=severe_tags,
            ask_error_type=ask_error_type,
            k2_error_type=k2_error_type,
        )

    if k2_envelope.get("k2_metrics_record"):
        merged["k2_metrics_record"] = k2_envelope["k2_metrics_record"]

    merged["k2_merge"] = merge_meta
    return merged
