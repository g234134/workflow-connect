"""Intake decision rules v2 (W8-T2 + W9-T2).

Extends v1 with A/B/C/D fixture profile tiers, tiered risk signals, and
reduced false-positive rejects for experimental Tabular fixtures. Adds a
conservative ``non_tabular.*`` decision helper (NT-A / NT-B profiles) per
W9-T2; Tabular behavior unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from routing.intake_decision_rules_v1 import evaluate_intake_decision
from routing.intake_to_tabular_glue import plan_tabular_route

Decision = Literal["auto_accept", "needs_review", "reject"]
RiskLevel = Literal["low", "medium", "high"]
ProfileTier = Literal["A", "B", "C", "D", "NT-A", "NT-B", "unknown"]
NonTabularProfileTier = Literal["NT-A", "NT-B", "unknown"]
ProfileMaturity = Literal["stable", "experimental", "shadow", "unknown"]
FlowFamily = Literal["tabular", "non_tabular"]

_RULES_VERSION = "v2"

_SUPPORTED_TASK_TYPES = frozenset(
    {
        "tabular.cleaning.mvp",
        "tabular.cleaning.regression",
        "tabular.intake.new_case",
    }
)

_DECISION_ALLOWLIST_PROFILES = frozenset({"demo_phase", "sampleco"})

_EXPERIMENTAL_PROFILES = frozenset({"additional_demo", "sandbox_client"})

_PROFILE_TIER_MAP: Dict[str, ProfileTier] = {
    "demo_phase": "A",
    "sampleco": "B",
    "generic-low-risk": "B",
    "additional_demo": "C",
    "sandbox_client": "D",
}

_LOW_RISK_SIGNALS = frozenset(
    {
        "phase_like",
        "phase_demo",
        "review_needed",
        "multi_row_export",
    }
)

_MEDIUM_RISK_SIGNALS = frozenset(
    {
        "schema_ambiguous",
        "human_review_required",
        "manual_review_required",
        "experimental_fixture_profile",
        "unknown_fixture_profile",
    }
)

_HARD_REJECT_MESSAGES = frozenset(
    {
        "non_tabular_family",
        "unsupported_task_type",
        "case_dir_not_found",
        "glue_plan_failed",
    }
)

_TASK_TYPES_REQUIRING_CASE_DIR = frozenset(
    {
        "tabular.cleaning.mvp",
        "tabular.cleaning.regression",
    }
)

_NON_TABULAR_SUPPORTED_TASK_TYPES = frozenset(
    {
        "non_tabular.document.extract",
        "non_tabular.log.analyze",
        "non_tabular.generic.transform",
    }
)

_NT_A_TASK_TYPES = frozenset({"non_tabular.document.extract"})
_NT_B_TASK_TYPES = frozenset({"non_tabular.log.analyze"})

_NT_A_PATH_HINTS = frozenset({"docu-corp", "docu_corp"})
_NT_B_PATH_HINTS = frozenset({"log-analytics-co", "log_analytics_co"})


def _normalize_case_dir(case_dir: str) -> Path:
    path = Path(case_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path.resolve()


def _rel_case_dir(case_dir: str) -> str:
    if Path(case_dir).is_absolute():
        try:
            return _normalize_case_dir(case_dir).relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            return case_dir.replace("\\", "/")
    return case_dir.replace("\\", "/")


def _is_tabular_family(task_type: str) -> bool:
    return task_type.startswith("tabular.")


def _is_non_tabular_family(task_type: str) -> bool:
    return task_type.startswith("non_tabular.") or task_type.startswith("non-tabular.")


def _normalize_non_tabular_task_type(task_type: str) -> str:
    if task_type.startswith("non-tabular."):
        return "non_tabular." + task_type[len("non-tabular.") :]
    return task_type


def _read_intake_json(case_dir: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return None, None
    try:
        text = intake_path.read_text(encoding="utf-8")
        if not text.strip():
            return None, "intake_empty"
        payload = json.loads(text)
        if not isinstance(payload, dict):
            return None, "intake_json_not_object"
        return payload, None
    except json.JSONDecodeError as exc:
        return None, f"intake_json_invalid: {exc.msg}"
    except OSError as exc:
        return None, f"intake_read_failed: {exc}"


def _non_tabular_content_corrupt(intake: Optional[Dict[str, Any]]) -> bool:
    if not intake:
        return False
    if intake.get("_corrupt") is True:
        return True
    if intake.get("format_status") == "corrupt":
        return True
    if intake.get("content_accessible") is False:
        return True
    return False


def _resolve_non_tabular_profile(
    task_type: str,
    case_dir_path: Path,
    intake: Optional[Dict[str, Any]],
) -> Tuple[NonTabularProfileTier, str, ProfileMaturity]:
    normalized_tt = _normalize_non_tabular_task_type(task_type)
    rel_lower = case_dir_path.as_posix().lower()

    profile_id = ""
    if intake:
        profile_id = str(intake.get("client_ref") or intake.get("case_id") or "")

    content_type = str((intake or {}).get("content_type") or "").lower()
    schema_hint = str((intake or {}).get("schema_hint") or "").lower()

    if (
        normalized_tt in _NT_A_TASK_TYPES
        or any(hint in rel_lower for hint in _NT_A_PATH_HINTS)
        or content_type in {"document", "mixed_documents", "documents"}
    ):
        return "NT-A", profile_id or "docu-corp", "shadow"

    if (
        normalized_tt in _NT_B_TASK_TYPES
        or any(hint in rel_lower for hint in _NT_B_PATH_HINTS)
        or content_type in {"log", "logs", "server_logs"}
        or schema_hint == "semi-structured"
    ):
        return "NT-B", profile_id or "log-analytics-co", "shadow"

    if normalized_tt == "non_tabular.generic.transform":
        return "unknown", profile_id or "generic", "unknown"

    return "unknown", profile_id, "unknown"


def _build_non_tabular_rationale(
    decision: Decision,
    risk_level: RiskLevel,
    *,
    task_type: str,
    profile_id: str,
    profile_tier: NonTabularProfileTier,
    profile_maturity: ProfileMaturity,
    signals: Dict[str, List[str]],
    extra: Optional[List[str]] = None,
) -> List[str]:
    rationale: List[str] = [
        f"rules_version={_RULES_VERSION}",
        f"task_type={task_type}",
        f"decision={decision}",
        f"risk_level={risk_level}",
        f"flow_family=non_tabular",
        f"fixture_profile_tier={profile_tier}",
        f"case_profile_tier={profile_tier}",
    ]
    if profile_id:
        rationale.append(f"case_profile={profile_id}")
        rationale.append(f"profile_maturity={profile_maturity}")
    if profile_tier == "NT-A":
        rationale.append("non_tabular_profile=NT-A_document_extraction")
    elif profile_tier == "NT-B":
        rationale.append("non_tabular_profile=NT-B_log_analysis")
    for tier_name in ("low", "medium", "high"):
        tier_signals = signals.get(tier_name) or []
        if tier_signals:
            rationale.append(f"{tier_name}_risk_signals={tier_signals}")
    rationale.append("non_tabular_v1_conservative=needs_review_default")
    if extra:
        rationale.extend(extra)
    return rationale


def _evaluate_non_tabular_decision_v2(task_type: str, case_dir: str) -> Dict[str, Any]:
    rel_case_dir = _rel_case_dir(case_dir)
    normalized_tt = _normalize_non_tabular_task_type(task_type)
    normalized_path = _normalize_case_dir(case_dir)

    if not normalized_path.is_dir():
        return _reject_result(
            task_type,
            rel_case_dir,
            message="case_dir_not_found",
            rationale_extra=[f"expected_directory={rel_case_dir}"],
            flow_family="non_tabular",
        )

    intake, parse_error = _read_intake_json(normalized_path)
    if parse_error:
        return _reject_result(
            task_type,
            rel_case_dir,
            message="intake_unparseable",
            rationale_extra=[parse_error, "risk=R-NT1"],
            flow_family="non_tabular",
        )

    if _non_tabular_content_corrupt(intake):
        return _reject_result(
            task_type,
            rel_case_dir,
            message="content_corrupt_or_unreadable",
            rationale_extra=["risk=R-NT1", "format_unparseable_or_corrupt"],
            flow_family="non_tabular",
        )

    profile_tier, profile_id, profile_maturity = _resolve_non_tabular_profile(
        normalized_tt,
        normalized_path,
        intake,
    )

    decision: Decision = "needs_review"
    risk_level: RiskLevel = "medium"
    medium_signals: List[str] = ["non_tabular_shadow_v1", "conservative_review"]
    if profile_tier == "NT-A":
        medium_signals.append("document_extraction_profile")
    elif profile_tier == "NT-B":
        medium_signals.append("log_analysis_profile")
    if normalized_tt not in _NON_TABULAR_SUPPORTED_TASK_TYPES:
        medium_signals.append("unsupported_non_tabular_task_type")

    signals = {"low": [], "medium": sorted(set(medium_signals)), "high": []}

    suggested_route = {
        "selector_task_type": normalized_tt,
        "planned_tools": [],
        "shadow_only": True,
    }

    rationale = _build_non_tabular_rationale(
        decision,
        risk_level,
        task_type=task_type,
        profile_id=profile_id,
        profile_tier=profile_tier,
        profile_maturity=profile_maturity,
        signals=signals,
    )

    return {
        "ok": True,
        "rules_version": _RULES_VERSION,
        "task_type": task_type,
        "case_dir": rel_case_dir,
        "flow_family": "non_tabular",
        "fixture_profile": profile_id,
        "fixture_profile_tier": profile_tier,
        "case_profile_tier": profile_tier,
        "profile_maturity": profile_maturity,
        "decision": decision,
        "risk_level": risk_level,
        "signals": signals,
        "rationale": rationale,
        "suggested_route": suggested_route,
        "message": f"decision={decision} risk={risk_level}",
        "shadow_flow_hook": {
            "eligible": True,
            "implemented_by": "W9-T2-non-tabular-decision-rules-v1",
            "glue_planner": "W9-T4-non-tabular-glue-layer-v1",
        },
    }


def _classify_profile(profile_id: str) -> Tuple[ProfileTier, ProfileMaturity]:
    tier = _PROFILE_TIER_MAP.get(profile_id, "unknown")
    if profile_id in _DECISION_ALLOWLIST_PROFILES:
        return tier, "stable"
    if profile_id in _EXPERIMENTAL_PROFILES:
        return tier, "experimental"
    if profile_id:
        return tier, "unknown"
    return "unknown", "unknown"


def _tiered_signals(
    glue_plan: Dict[str, Any],
    *,
    profile_id: str,
    profile_maturity: ProfileMaturity,
) -> Dict[str, List[str]]:
    low: Set[str] = set()
    medium: Set[str] = set()
    high: Set[str] = set()

    for note in glue_plan.get("notes") or []:
        note_lower = str(note).lower()
        for signal in _LOW_RISK_SIGNALS:
            if signal in note_lower:
                low.add(signal)
        for signal in _MEDIUM_RISK_SIGNALS:
            if signal in note_lower:
                medium.add(signal)

    for gate_note in glue_plan.get("inferred_gate_notes") or []:
        gate_str = str(gate_note).lower()
        if gate_str in _LOW_RISK_SIGNALS:
            low.add(gate_str)
        elif gate_str in _MEDIUM_RISK_SIGNALS:
            medium.add(gate_str)
        else:
            for signal in _MEDIUM_RISK_SIGNALS:
                if signal in gate_str:
                    medium.add(signal)

    if profile_maturity == "experimental":
        medium.add("experimental_fixture_profile")
    elif profile_id and profile_id not in _DECISION_ALLOWLIST_PROFILES:
        medium.add("unknown_fixture_profile")

    return {
        "low": sorted(low),
        "medium": sorted(medium),
        "high": sorted(high),
    }


def _decision_from_profile_and_signals(
    task_type: str,
    *,
    profile_id: str,
    profile_maturity: ProfileMaturity,
    signals: Dict[str, List[str]],
    intake: Optional[Dict[str, Any]] = None,
) -> Decision:
    medium = set(signals.get("medium") or [])
    high = set(signals.get("high") or [])

    if high:
        return "reject"

    if task_type == "tabular.intake.new_case":
        return "auto_accept"

    provenance = (intake or {}).get("provenance") or {}
    source_type = str(provenance.get("source_type") or "")
    cleaning_profile = str((intake or {}).get("cleaning_profile") or "")
    if (
        (profile_id == "generic-low-risk" or cleaning_profile == "generic_low_risk_profile")
        and source_type == "owned"
    ):
        return "needs_review"

    if profile_maturity == "experimental":
        return "needs_review"

    if medium:
        return "needs_review"

    if profile_id in _DECISION_ALLOWLIST_PROFILES:
        return "auto_accept"

    return "needs_review"


def _risk_level_for(
    decision: Decision,
    signals: Dict[str, List[str]],
    *,
    profile_maturity: ProfileMaturity,
    task_type: str = "",
) -> RiskLevel:
    if decision == "reject":
        return "high"
    if task_type == "tabular.intake.new_case" and decision == "auto_accept":
        return "low"
    if decision == "needs_review" or signals.get("medium") or signals.get("high"):
        return "medium"
    if profile_maturity == "stable" and decision == "auto_accept":
        return "low"
    return "medium"


def _build_rationale(
    decision: Decision,
    risk_level: RiskLevel,
    *,
    task_type: str,
    glue_plan: Dict[str, Any],
    profile_id: str,
    profile_tier: ProfileTier,
    profile_maturity: ProfileMaturity,
    signals: Dict[str, List[str]],
    extra: Optional[List[str]] = None,
) -> List[str]:
    rationale: List[str] = [
        f"rules_version={_RULES_VERSION}",
        f"task_type={task_type}",
        f"decision={decision}",
        f"risk_level={risk_level}",
        f"fixture_profile_tier={profile_tier}",
    ]
    if profile_id:
        rationale.append(f"case_profile={profile_id}")
        rationale.append(f"profile_maturity={profile_maturity}")
    if profile_id in _DECISION_ALLOWLIST_PROFILES:
        rationale.append("decision_allowlist_fixture")
    elif profile_maturity == "experimental":
        rationale.append("experimental_fixture")
    elif profile_id:
        rationale.append("non_allowlist_fixture")
    for tier_name in ("low", "medium", "high"):
        tier_signals = signals.get(tier_name) or []
        if tier_signals:
            rationale.append(f"{tier_name}_risk_signals={tier_signals}")
    if glue_plan.get("ok"):
        rationale.append(f"glue_plan_ok: {glue_plan.get('message', 'planned')}")
    if extra:
        rationale.extend(extra)
    return rationale


def _reject_result(
    task_type: str,
    case_dir: str,
    *,
    message: str,
    rationale_extra: List[str],
    flow_family: FlowFamily = "non_tabular",
) -> Dict[str, Any]:
    rationale = [
        f"rules_version={_RULES_VERSION}",
        f"task_type={task_type}",
        f"decision=reject",
        "risk_level=high",
        f"flow_family={flow_family}",
        message,
    ]
    rationale.extend(rationale_extra)
    payload: Dict[str, Any] = {
        "ok": True,
        "rules_version": _RULES_VERSION,
        "task_type": task_type,
        "case_dir": case_dir,
        "flow_family": flow_family,
        "fixture_profile_tier": "unknown",
        "profile_maturity": "unknown",
        "decision": "reject",
        "risk_level": "high",
        "rationale": rationale,
        "suggested_route": None,
        "message": message,
        "signals": {"low": [], "medium": [], "high": ["hard_reject"]},
    }
    if flow_family == "non_tabular":
        payload["shadow_flow_hook"] = {
            "eligible": False,
            "future_ticket": "W8-T5-non-tabular-intake-shadow",
        }
    return payload


def _enrich_success_result(
    base: Dict[str, Any],
    *,
    glue_plan: Dict[str, Any],
    profile_id: str,
    profile_tier: ProfileTier,
    profile_maturity: ProfileMaturity,
    signals: Dict[str, List[str]],
) -> Dict[str, Any]:
    base["rules_version"] = _RULES_VERSION
    base["flow_family"] = "tabular"
    base["fixture_profile"] = profile_id
    base["fixture_profile_tier"] = profile_tier
    base["profile_maturity"] = profile_maturity
    base["signals"] = signals
    base["glue_plan"] = {
        "case_profile": glue_plan.get("case_profile"),
        "inferred_gate_notes": glue_plan.get("inferred_gate_notes"),
        "notes": glue_plan.get("notes"),
    }
    return base


def evaluate_intake_decision_v2(
    task_type: str,
    case_dir: str,
    *,
    use_v1_fallback: bool = True,
) -> Dict[str, Any]:
    """Evaluate intake accept/review/reject using v2 profile tiers and signal classes.

    When ``use_v1_fallback`` is True, any internal evaluation error falls back to
    v1 ``evaluate_intake_decision`` with ``rules_version=v1_fallback`` annotation.
    """
    try:
        return _evaluate_intake_decision_v2_core(task_type, case_dir)
    except Exception as exc:
        if not use_v1_fallback:
            raise
        v1_result = evaluate_intake_decision(task_type, case_dir)
        v1_result["rules_version"] = "v1_fallback"
        v1_result["v2_fallback_reason"] = str(exc)
        return v1_result


def _evaluate_intake_decision_v2_core(task_type: str, case_dir: str) -> Dict[str, Any]:
    rel_case_dir = _rel_case_dir(case_dir)

    if _is_non_tabular_family(task_type):
        return _evaluate_non_tabular_decision_v2(task_type, case_dir)

    if not _is_tabular_family(task_type):
        return _reject_result(
            task_type,
            rel_case_dir,
            message="non_tabular_family",
            rationale_extra=[
                "supported_family=tabular.* or non_tabular.* (v2); "
                "other families remain reject",
            ],
            flow_family="non_tabular",
        )

    if task_type not in _SUPPORTED_TASK_TYPES:
        return _reject_result(
            task_type,
            rel_case_dir,
            message="unsupported_task_type",
            rationale_extra=[f"supported={sorted(_SUPPORTED_TASK_TYPES)}"],
            flow_family="tabular",
        )

    if task_type in _TASK_TYPES_REQUIRING_CASE_DIR:
        normalized = _normalize_case_dir(case_dir)
        if not normalized.is_dir():
            return _reject_result(
                task_type,
                rel_case_dir,
                message="case_dir_not_found",
                rationale_extra=[f"expected_directory={rel_case_dir}"],
                flow_family="tabular",
            )

    glue_plan = plan_tabular_route(task_type, case_dir)
    if not glue_plan.get("ok"):
        return _reject_result(
            task_type,
            rel_case_dir,
            message="glue_plan_failed",
            rationale_extra=[
                f"glue_message={glue_plan.get('message', 'unknown')}",
                *(glue_plan.get("notes") or []),
            ],
            flow_family="tabular",
        )

    profile_id = str(glue_plan.get("case_profile") or "")
    profile_tier, profile_maturity = _classify_profile(profile_id)
    signals = _tiered_signals(
        glue_plan,
        profile_id=profile_id,
        profile_maturity=profile_maturity,
    )

    if task_type == "tabular.intake.new_case":
        signals = {"low": [], "medium": [], "high": []}

    decision = _decision_from_profile_and_signals(
        task_type,
        profile_id=profile_id,
        profile_maturity=profile_maturity,
        signals=signals,
        intake=intake,
    )
    risk_level = _risk_level_for(
        decision,
        signals,
        profile_maturity=profile_maturity,
        task_type=task_type,
    )

    suggested_route = {
        "selector_task_type": glue_plan.get("selector_task_type"),
        "planned_tools": list(glue_plan.get("planned_tools") or []),
    }
    if glue_plan.get("orchestration_tool_id"):
        suggested_route["orchestration_tool_id"] = glue_plan["orchestration_tool_id"]

    rationale = _build_rationale(
        decision,
        risk_level,
        task_type=task_type,
        glue_plan=glue_plan,
        profile_id=profile_id,
        profile_tier=profile_tier,
        profile_maturity=profile_maturity,
        signals=signals,
    )

    result: Dict[str, Any] = {
        "ok": True,
        "task_type": task_type,
        "case_dir": rel_case_dir,
        "decision": decision,
        "risk_level": risk_level,
        "rationale": rationale,
        "suggested_route": suggested_route if decision != "reject" else None,
        "message": f"decision={decision} risk={risk_level}",
    }
    return _enrich_success_result(
        result,
        glue_plan=glue_plan,
        profile_id=profile_id,
        profile_tier=profile_tier,
        profile_maturity=profile_maturity,
        signals=signals,
    )


def _cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate intake decision rules v2 (Tabular + non_tabular.*, plan-only)."
    )
    parser.add_argument("--task-type", required=True, help="W2 routing catalog task_type")
    parser.add_argument("--case-dir", required=True, help="Repo-relative or absolute case path")
    parser.add_argument(
        "--no-v1-fallback",
        action="store_true",
        help="Disable v1 fallback on internal errors",
    )
    parser.add_argument("--json", action="store_true", help="Emit full result as JSON")
    args = parser.parse_args(argv)

    result = evaluate_intake_decision_v2(
        args.task_type,
        args.case_dir,
        use_v1_fallback=not args.no_v1_fallback,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"rules_version: {result.get('rules_version', _RULES_VERSION)}")
        print(f"decision: {result['decision']}")
        print(f"risk_level: {result['risk_level']}")
        print(f"fixture_profile_tier: {result.get('fixture_profile_tier', 'unknown')}")
        print(f"message: {result.get('message', '')}")
        route = result.get("suggested_route") or {}
        if route:
            print(f"selector_task_type: {route.get('selector_task_type')}")
            print(f"planned_tools: {', '.join(route.get('planned_tools') or [])}")
        for line in result.get("rationale") or []:
            print(f"  - {line}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
