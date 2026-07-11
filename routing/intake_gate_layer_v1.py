"""Intake Gate integration layer v1 (P75-G2 + P75-G3 policy merge).

Single canonical producer for intake gate decisions: wraps v2 rules (v1 fallback),
maps to accept / review_needed / reject, merges policy SSOT hits, and optionally
writes durable outbox records.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal, Mapping, Optional

from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2
from routing.intake_gate_mapping_v1 import (
    DECIDER,
    SCHEMA_VERSION,
    _PM_DECISIONS_APPLIED,
    build_gate_checks,
    build_intake_decision_id,
    compute_checkpoint_a_preview,
    derive_case_ref,
    extract_reason_codes,
    extract_risk_flags,
    glue_plan_summary,
    map_internal_to_canonical,
    rules_engine_metadata,
    utc_now_iso,
)
from routing.intake_gate_outbox_v1 import write_intake_gate_record
from routing.intake_gate_policy_bridge_v1 import (
    bridge_policy_eval,
    derive_p75_policy_trace,
    bridge_suggested_decision_override,
)
from routing.intake_gate_policy_evaluator_v1 import evaluate_policy
from routing.intake_gate_policy_loader_v1 import load_intake_gate_policy

Mode = Literal["preview", "run"]
_REPO_ROOT = Path(__file__).resolve().parents[1]


def _dedupe_reason_codes(*groups: Optional[list[str]]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for code in group or []:
            if code in seen:
                continue
            seen.add(code)
            merged.append(code)
    return merged


def merge_policy_with_v2(
    rules_result: Mapping[str, Any],
    bridge: Mapping[str, Any],
) -> str:
    """Apply policy override on canonical decision derived from rules engine."""
    base = map_internal_to_canonical(str(rules_result.get("decision") or ""))
    override = bridge_suggested_decision_override(bridge)
    if override == "reject":
        return "reject"
    if override == "review_needed" and base == "accept":
        return "review_needed"
    return base


def _merge_gate_checks(
    rules_checks: list[dict[str, Any]],
    policy_checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [*rules_checks, *policy_checks]


def evaluate_intake_gate(
    task_type: str,
    case_dir: str,
    *,
    mode: Mode = "preview",
    policy_path: Optional[str] = None,
    use_v1_fallback: bool = True,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    flags: Optional[Mapping[str, Any]] = None,
    **_: Any,
) -> Dict[str, Any]:
    """Evaluate intake gate and return ``intake_gate_result_v1`` shaped dict.

    Preview mode never writes outbox; run mode writes durable record + jsonl event.
    """
    created_at = utc_now_iso()
    case_ref = derive_case_ref(case_dir)
    rel_case_dir = case_dir.replace("\\", "/")

    policy_load = load_intake_gate_policy(policy_path)
    if not policy_load.get("ok"):
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "task_type": task_type,
            "case_dir": rel_case_dir,
            "case_ref": case_ref,
            "mode": mode,
            "created_at": created_at,
            "decider": DECIDER,
            "message": str(policy_load.get("error") or "policy load failed"),
            "outbox_record_path": None,
        }

    policy = policy_load["policy"]
    assert policy is not None

    try:
        rules_result = evaluate_intake_decision_v2(
            task_type,
            case_dir,
            use_v1_fallback=use_v1_fallback,
        )
    except Exception as exc:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "task_type": task_type,
            "case_dir": rel_case_dir,
            "case_ref": case_ref,
            "mode": mode,
            "created_at": created_at,
            "decider": DECIDER,
            "message": f"rules engine error: {exc}",
            "outbox_record_path": None,
        }

    if not rules_result.get("ok"):
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "task_type": task_type,
            "case_dir": rel_case_dir,
            "case_ref": case_ref,
            "mode": mode,
            "created_at": created_at,
            "decider": DECIDER,
            "message": str(rules_result.get("message") or "rules evaluation failed"),
            "outbox_record_path": None,
        }

    policy_eval = evaluate_policy(
        policy,
        task_type=task_type,
        case_dir=case_dir,
        flags=flags,
    )
    policy_bridge = bridge_policy_eval(policy_eval)

    decision_internal = str(rules_result.get("decision") or "")
    decision = merge_policy_with_v2(rules_result, policy_bridge)
    risk_level = str(rules_result.get("risk_level") or "medium")
    reason_codes = _dedupe_reason_codes(
        extract_reason_codes(rules_result),
        list(policy_bridge.get("reason_codes") or []),
    )
    gate_checks = _merge_gate_checks(
        build_gate_checks(rules_result),
        list(policy_bridge.get("gate_checks") or []),
    )
    rules_engine, rules_engine_version = rules_engine_metadata(rules_result)

    intake_decision_id = build_intake_decision_id(
        case_ref=case_ref,
        task_type=task_type,
        created_at=created_at,
    )

    result: Dict[str, Any] = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "intake_decision_id": intake_decision_id,
        "decision": decision,
        "decision_normalized": decision,
        "decision_internal": decision_internal,
        "task_type": task_type,
        "case_ref": case_ref,
        "case_dir": rules_result.get("case_dir") or rel_case_dir,
        "risk_level": risk_level,
        "risk_flags": extract_risk_flags(rules_result),
        "reason_codes": reason_codes,
        "message": rules_result.get("message")
        or f"decision={decision} risk={risk_level}",
        "gate_checks": gate_checks,
        "suggested_route": rules_result.get("suggested_route"),
        "policy_version": policy_bridge.get("policy_version"),
        "rules_engine": rules_engine,
        "rules_engine_version": rules_engine_version,
        "decider": DECIDER,
        "mode": mode,
        "created_at": created_at,
        "pm_decisions_applied": dict(_PM_DECISIONS_APPLIED),
        "outbox_record_path": None,
        "checkpoint_a": compute_checkpoint_a_preview(
            decision=decision,  # type: ignore[arg-type]
            risk_level=risk_level,
        ),
        "policy_profile_id": policy_bridge.get("profile_id"),
        "policy_profile_tier": policy_bridge.get("profile_tier"),
        "policy_profile_maturity": policy_bridge.get("profile_maturity"),
        **derive_p75_policy_trace(policy_bridge),
    }
    if rules_result.get("glue_plan"):
        result["glue_plan"] = rules_result.get("glue_plan")
    else:
        summary = glue_plan_summary(rules_result)
        if summary:
            result["glue_plan"] = summary

    if decision == "reject":
        result["suggested_route"] = None

    if mode == "run":
        root = repo_root or _REPO_ROOT
        record_path = write_intake_gate_record(
            result,
            repo_root=root,
            outbox_root_override=outbox_root_override,
        )
        result["outbox_record_path"] = record_path

    return result
