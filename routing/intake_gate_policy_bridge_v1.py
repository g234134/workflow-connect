"""Bridge policy evaluator hits to gate_checks and reason_codes (P75-G3)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Mapping, Set

from routing.intake_gate_policy_evaluator_v1 import g1_reason_codes
from routing.intake_gate_policy_types_v1 import PolicyEvalResult, PolicyHit

BridgeResult = Dict[str, Any]

P75PolicyDecision = Literal["policy_deny", "policy_review", "policy_pass"]

P75_POLICY_DENY_REASON_CODES: frozenset[str] = frozenset(
    {
        "policy_deny_phi",
        "policy_deny_web_scraping",
        "policy_deny_audio_video",
        "policy_deny_scale_exceeds",
    }
)


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def policy_hit_to_gate_check(hit: PolicyHit) -> Dict[str, Any]:
    return {
        "rule_id": hit.rule_id,
        "passed": hit.passed,
        "detail": hit.detail,
    }


def bridge_policy_eval(
    eval_result: PolicyEvalResult,
    *,
    allowed_reason_codes: Set[str] | None = None,
) -> BridgeResult:
    """Convert evaluator hits into ``gate_checks`` and ``reason_codes`` arrays."""
    allowed = allowed_reason_codes or g1_reason_codes()
    gate_checks: List[Dict[str, Any]] = []
    reason_codes: List[str] = []

    for hit in eval_result.hits:
        gate_checks.append(policy_hit_to_gate_check(hit))
        if hit.reason_code and hit.reason_code in allowed:
            if not hit.passed or hit.reason_code in {
                "supported_task",
                "allowlist_fixture",
            }:
                reason_codes.append(hit.reason_code)

    return {
        "ok": True,
        "policy_version": eval_result.policy_version,
        "gate_checks": gate_checks,
        "reason_codes": _dedupe_preserve_order(reason_codes),
        "policy_hits": [hit.to_dict() for hit in eval_result.hits],
        "profile_id": eval_result.profile_id,
        "profile_tier": eval_result.profile_tier,
        "profile_maturity": eval_result.profile_maturity,
    }


def bridge_has_deny_failure(bridge: Mapping[str, Any]) -> bool:
    for check in bridge.get("gate_checks") or []:
        if not isinstance(check, dict):
            continue
        rule_id = str(check.get("rule_id") or "")
        if rule_id.startswith("POLICY-DENY-") and check.get("passed") is False:
            return True
    return False


def bridge_suggested_decision_override(bridge: Mapping[str, Any]) -> str | None:
    """Return canonical decision override implied by policy hits, if any."""
    reason_codes = set(bridge.get("reason_codes") or [])

    if bridge_has_deny_failure(bridge):
        return "reject"

    if "non_tabular_without_flag" in reason_codes:
        return "reject"

    if "unsupported_task_type" in reason_codes:
        return "reject"

    if "unknown_client_profile" in reason_codes:
        return "review_needed"

    if "experimental_fixture" in reason_codes:
        return "review_needed"

    return None


def _first_policy_deny_rule_detail(bridge: Mapping[str, Any]) -> str | None:
    for check in bridge.get("gate_checks") or []:
        if not isinstance(check, dict):
            continue
        rule_id = str(check.get("rule_id") or "")
        if rule_id.startswith("POLICY-DENY-") and check.get("passed") is False:
            detail = check.get("detail")
            return str(detail or rule_id)
    return None


def derive_p75_policy_trace(bridge: Mapping[str, Any]) -> Dict[str, Any]:
    """Observability fields for P7.5 policy deny MVP (W1-P75 · no external calls)."""
    reason_codes = list(bridge.get("reason_codes") or [])
    deny_codes = [code for code in reason_codes if code in P75_POLICY_DENY_REASON_CODES]
    override = bridge_suggested_decision_override(bridge)

    if deny_codes or override == "reject":
        p75_policy_decision: P75PolicyDecision = "policy_deny"
        deny_reason = deny_codes[0] if deny_codes else _first_policy_deny_rule_detail(bridge)
    elif override == "review_needed":
        p75_policy_decision = "policy_review"
        deny_reason = None
    else:
        p75_policy_decision = "policy_pass"
        deny_reason = None

    return {
        "p75_policy_decision": p75_policy_decision,
        "deny_reason": deny_reason,
    }
