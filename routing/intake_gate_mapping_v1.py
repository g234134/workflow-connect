"""Intake Gate canonical mapping v1 (P75-G2).

Maps v1/v2 internal decisions to canonical accept / review_needed / reject,
builds gate_checks and reason_codes, and adapts gate results for Checkpoint A.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

CanonicalDecision = Literal["accept", "review_needed", "reject"]
InternalDecision = Literal["auto_accept", "needs_review", "reject", "accept", "defer"]
RiskLevel = Literal["low", "medium", "high"]

SCHEMA_VERSION = "intake_gate_result_v1"
DECIDER = "intake_gate_layer_v1"
DEFAULT_POLICY_VERSION = "intake_gate_policy_v1"

_INTERNAL_TO_CANONICAL: Dict[str, CanonicalDecision] = {
    "auto_accept": "accept",
    "needs_review": "review_needed",
    "reject": "reject",
    "accept": "accept",
    "defer": "review_needed",
}

_CANONICAL_TO_INTERNAL: Dict[str, InternalDecision] = {
    "accept": "auto_accept",
    "review_needed": "needs_review",
    "reject": "reject",
}

_MESSAGE_TO_REASON: Dict[str, str] = {
    "unsupported_task_type": "unsupported_task_type",
    "non_tabular_family": "non_tabular_without_flag",
    "case_dir_not_found": "case_dir_not_found",
    "glue_plan_failed": "glue_plan_failed",
    "intake_unparseable": "glue_plan_failed",
    "content_corrupt_or_unreadable": "glue_plan_failed",
}

_PM_DECISIONS_APPLIED: Dict[str, str] = {
    "PM-D1": "defer_merged_into_review_needed",
    "PM-D2": "unsupported_task_type_reject",
    "PM-D6": "unknown_client_review_needed",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compact_ts(iso_ts: Optional[str] = None) -> str:
    ts = iso_ts or utc_now_iso()
    return ts.replace(":", "-").replace("Z", "Z")


def task_type_slug(task_type: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", task_type).strip("_") or "unknown"


def map_internal_to_canonical(decision_internal: str) -> CanonicalDecision:
    mapped = _INTERNAL_TO_CANONICAL.get(decision_internal)
    if mapped is None:
        return "review_needed"
    return mapped


def map_canonical_to_internal(decision: str) -> InternalDecision:
    mapped = _CANONICAL_TO_INTERNAL.get(decision)
    if mapped is None:
        return "needs_review"
    return mapped


def derive_case_ref(case_dir: str) -> str:
    rel = case_dir.replace("\\", "/").strip("/")
    if rel.startswith("cases/"):
        rel = rel[len("cases/") :]
    return rel or "unknown"


def build_intake_decision_id(
    *,
    case_ref: str,
    task_type: str,
    created_at: Optional[str] = None,
    include_uuid: bool = True,
) -> str:
    ts = compact_ts(created_at)
    slug = task_type_slug(task_type)
    suffix = f"{case_ref}_{slug}"
    if include_uuid:
        suffix = f"{suffix}_{uuid.uuid4().hex[:8]}"
    return f"igd_{ts}_{suffix}"


def extract_reason_codes(rules_result: Dict[str, Any]) -> List[str]:
    codes: List[str] = []
    message = str(rules_result.get("message") or "")
    if message in _MESSAGE_TO_REASON:
        codes.append(_MESSAGE_TO_REASON[message])

    signals = rules_result.get("signals") or {}
    medium = set(signals.get("medium") or [])
    if "manual_review_required" in medium or "human_review_required" in medium:
        codes.append("manual_review_required")
    if "experimental_fixture_profile" in medium:
        codes.append("experimental_fixture")
    if "unknown_fixture_profile" in medium:
        codes.append("unknown_client_profile")

    rationale_text = " ".join(str(x) for x in (rules_result.get("rationale") or []))
    if "decision_allowlist_fixture" in rationale_text:
        codes.append("allowlist_fixture")
    if rules_result.get("decision") == "auto_accept" and "unsupported_task_type" not in codes:
        if "allowlist_fixture" in codes or rules_result.get("profile_maturity") == "stable":
            if "manual_review_required" not in codes:
                codes.append("supported_task")

    decision_internal = str(rules_result.get("decision") or "")
    if decision_internal == "auto_accept" and "supported_task" not in codes and not codes:
        codes.append("supported_task")

    if not codes and decision_internal == "needs_review":
        codes.append("manual_review_required")

    # Stable order, dedupe
    seen: set[str] = set()
    ordered: List[str] = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return ordered


def build_gate_checks(rules_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    task_type = str(rules_result.get("task_type") or "")
    decision_internal = str(rules_result.get("decision") or "")
    message = str(rules_result.get("message") or "")

    supported = decision_internal != "reject" or message not in (
        "unsupported_task_type",
        "non_tabular_family",
    )
    checks.append(
        {
            "rule_id": "G-TASK-01",
            "passed": supported and message != "unsupported_task_type",
            "detail": f"{task_type} evaluated by rules engine",
        }
    )

    risk_level = str(rules_result.get("risk_level") or "medium")
    medium_signals = (rules_result.get("signals") or {}).get("medium") or []
    risk_passed = risk_level == "low" and decision_internal == "auto_accept"
    checks.append(
        {
            "rule_id": "G-RISK-02",
            "passed": risk_passed,
            "detail": (
                f"risk_level={risk_level}"
                + (f"; medium signals={medium_signals}" if medium_signals else "")
            ),
        }
    )

    if message in _MESSAGE_TO_REASON:
        checks.append(
            {
                "rule_id": "G-DENY-01",
                "passed": False,
                "detail": message,
            }
        )

    return checks


def extract_risk_flags(rules_result: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    signals = rules_result.get("signals") or {}
    for tier in ("low", "medium", "high"):
        for sig in signals.get(tier) or []:
            flags.append(str(sig))
    if rules_result.get("profile_maturity") == "experimental":
        flags.append("experimental_fixture_profile")
    seen: set[str] = set()
    ordered: List[str] = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            ordered.append(flag)
    return ordered


def compute_checkpoint_a_preview(
    *,
    decision: CanonicalDecision,
    risk_level: str,
) -> Dict[str, Any]:
    if decision == "reject":
        return {"would_trigger": False, "trigger_reason": "decision_reject"}
    if decision == "review_needed":
        return {"would_trigger": True, "trigger_reason": "decision_review_needed"}
    if risk_level in ("medium", "high"):
        return {"would_trigger": True, "trigger_reason": "risk_level_override"}
    return {"would_trigger": False, "trigger_reason": "low_risk_accept"}


def rules_engine_metadata(rules_result: Dict[str, Any]) -> Tuple[str, str]:
    version = str(rules_result.get("rules_version") or "v2")
    if version == "v1_fallback":
        return "intake_decision_rules_v1", "v1_fallback"
    if version == "v1":
        return "intake_decision_rules_v1", "v1"
    return "intake_decision_rules_v2", version


def glue_plan_summary(rules_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    glue = rules_result.get("glue_plan")
    if not isinstance(glue, dict):
        return None
    planned_tools = glue.get("planned_tools")
    if planned_tools is None and rules_result.get("suggested_route"):
        planned_tools = (rules_result.get("suggested_route") or {}).get("planned_tools")
    return {
        "ok": True,
        "planned_tool_count": len(list(planned_tools or [])),
        "case_profile": glue.get("case_profile"),
    }


def decision_result_from_gate(gate_result: Dict[str, Any]) -> Dict[str, Any]:
    """Adapt intake_gate_result_v1 for Checkpoint A integration (internal decision values)."""
    internal = gate_result.get("decision_internal") or map_canonical_to_internal(
        str(gate_result.get("decision") or "")
    )
    rationale: List[str] = []
    for check in gate_result.get("gate_checks") or []:
        if isinstance(check, dict) and check.get("detail"):
            rationale.append(f"{check.get('rule_id')}: {check['detail']}")
    for code in gate_result.get("reason_codes") or []:
        rationale.append(f"reason_code={code}")

    adapted: Dict[str, Any] = {
        "ok": gate_result.get("ok", True),
        "decision": internal,
        "risk_level": gate_result.get("risk_level"),
        "rationale": rationale or [gate_result.get("message") or ""],
        "suggested_route": gate_result.get("suggested_route"),
        "message": gate_result.get("message"),
        "glue_plan": gate_result.get("glue_plan"),
        "case_dir": gate_result.get("case_dir"),
    }
    intake_gate_block: Dict[str, Any] = {
        "intake_decision_id": gate_result.get("intake_decision_id"),
        "decision": gate_result.get("decision"),
        "decision_internal": internal,
        "risk_level": gate_result.get("risk_level"),
        "reason_codes": list(gate_result.get("reason_codes") or []),
        "gate_checks": list(gate_result.get("gate_checks") or []),
        "outbox_record_path": gate_result.get("outbox_record_path"),
    }
    adapted["_intake_gate"] = intake_gate_block
    return adapted
