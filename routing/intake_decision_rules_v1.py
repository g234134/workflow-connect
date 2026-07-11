"""Intake decision rules v1 (W5-T1).

Pure decision helper for Tabular MVP intake cases. Consumes W4-T1 glue plans
and emits structured accept / review / reject decisions without changing
main-chain routing or intake CLIs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from routing.intake_to_tabular_glue import plan_tabular_route

Decision = Literal["auto_accept", "needs_review", "reject"]
RiskLevel = Literal["low", "medium", "high"]

_SUPPORTED_TASK_TYPES = frozenset(
    {
        "tabular.cleaning.mvp",
        "tabular.cleaning.regression",
        "tabular.intake.new_case",
    }
)

_ALLOWLIST_PROFILES = frozenset({"demo_phase", "sampleco"})

_MEDIUM_RISK_SIGNALS = frozenset(
    {
        "schema_ambiguous",
        "human_review_required",
        "manual_review_required",
        "review_needed",
    }
)

_TASK_TYPES_REQUIRING_CASE_DIR = frozenset(
    {
        "tabular.cleaning.mvp",
        "tabular.cleaning.regression",
    }
)


def _normalize_case_dir(case_dir: str) -> Path:
    path = Path(case_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path.resolve()


def _is_tabular_family(task_type: str) -> bool:
    return task_type.startswith("tabular.")


def _collect_risk_signals(glue_plan: Dict[str, Any]) -> Set[str]:
    signals: Set[str] = set()
    for note in glue_plan.get("notes") or []:
        note_lower = str(note).lower()
        for signal in _MEDIUM_RISK_SIGNALS:
            if signal in note_lower:
                signals.add(signal)
    for gate_note in glue_plan.get("inferred_gate_notes") or []:
        gate_str = str(gate_note).lower()
        if gate_str in _MEDIUM_RISK_SIGNALS:
            signals.add(gate_str)
        if gate_str == "schema_ambiguous":
            signals.add("schema_ambiguous")
        if gate_str == "multi_row_export":
            signals.add("multi_row_export")
    if glue_plan.get("case_profile") not in _ALLOWLIST_PROFILES:
        profile = str(glue_plan.get("case_profile") or "")
        if profile and profile not in _ALLOWLIST_PROFILES:
            signals.add("unknown_fixture_profile")
    return signals


def _risk_level_for(
    decision: Decision,
    signals: Set[str],
    *,
    allowlist: bool,
) -> RiskLevel:
    if decision == "reject":
        return "high"
    if decision == "needs_review" or signals:
        return "medium"
    if allowlist:
        return "low"
    return "medium"


def _decision_from_signals(
    task_type: str,
    glue_plan: Dict[str, Any],
    signals: Set[str],
) -> Decision:
    profile = str(glue_plan.get("case_profile") or "")
    allowlist = profile in _ALLOWLIST_PROFILES

    if task_type == "tabular.intake.new_case" and glue_plan.get("ok"):
        return "auto_accept"

    if signals:
        return "needs_review"

    if allowlist:
        return "auto_accept"

    return "needs_review"


def _build_rationale(
    decision: Decision,
    risk_level: RiskLevel,
    *,
    task_type: str,
    glue_plan: Dict[str, Any],
    signals: Set[str],
    extra: Optional[List[str]] = None,
) -> List[str]:
    rationale: List[str] = [
        f"task_type={task_type}",
        f"decision={decision}",
        f"risk_level={risk_level}",
    ]
    profile = glue_plan.get("case_profile")
    if profile:
        rationale.append(f"case_profile={profile}")
    if profile in _ALLOWLIST_PROFILES:
        rationale.append("allowlist_fixture")
    elif profile:
        rationale.append("non_allowlist_fixture")
    if signals:
        rationale.append(f"risk_signals={sorted(signals)}")
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
) -> Dict[str, Any]:
    rationale = [f"task_type={task_type}", f"decision=reject", "risk_level=high", message]
    rationale.extend(rationale_extra)
    return {
        "ok": True,
        "task_type": task_type,
        "case_dir": case_dir,
        "decision": "reject",
        "risk_level": "high",
        "rationale": rationale,
        "suggested_route": None,
        "message": message,
    }


def evaluate_intake_decision(task_type: str, case_dir: str) -> Dict[str, Any]:
    """Evaluate intake accept/review/reject for a Tabular MVP task_type + case_dir.

    Returns a stable dict with ``ok``, ``decision``, ``risk_level``, ``rationale``,
    and ``suggested_route`` (when planning succeeded). This helper does not mutate
    intake state or invoke main-chain CLIs.
    """
    rel_case_dir = case_dir.replace("\\", "/")
    if not Path(case_dir).is_absolute():
        try:
            rel_case_dir = _normalize_case_dir(case_dir).relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            rel_case_dir = case_dir.replace("\\", "/")

    if not _is_tabular_family(task_type):
        return _reject_result(
            task_type,
            rel_case_dir,
            message="non_tabular_family",
            rationale_extra=[f"supported_family=tabular.* only"],
        )

    if task_type not in _SUPPORTED_TASK_TYPES:
        return _reject_result(
            task_type,
            rel_case_dir,
            message="unsupported_task_type",
            rationale_extra=[f"supported={sorted(_SUPPORTED_TASK_TYPES)}"],
        )

    if task_type in _TASK_TYPES_REQUIRING_CASE_DIR:
        normalized = _normalize_case_dir(case_dir)
        if not normalized.is_dir():
            return _reject_result(
                task_type,
                rel_case_dir,
                message="case_dir_not_found",
                rationale_extra=[f"expected_directory={rel_case_dir}"],
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
        )

    signals = _collect_risk_signals(glue_plan)
    if task_type == "tabular.intake.new_case":
        signals = set()
    decision = _decision_from_signals(task_type, glue_plan, signals)
    profile = str(glue_plan.get("case_profile") or "")
    allowlist = profile in _ALLOWLIST_PROFILES
    risk_level = _risk_level_for(decision, signals, allowlist=allowlist)

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
        signals=signals,
    )

    return {
        "ok": True,
        "task_type": task_type,
        "case_dir": rel_case_dir,
        "decision": decision,
        "risk_level": risk_level,
        "rationale": rationale,
        "suggested_route": suggested_route,
        "message": f"decision={decision} risk={risk_level}",
        "glue_plan": {
            "case_profile": glue_plan.get("case_profile"),
            "inferred_gate_notes": glue_plan.get("inferred_gate_notes"),
            "notes": glue_plan.get("notes"),
        },
    }


def _cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate intake decision rules v1 (Tabular MVP, plan-only)."
    )
    parser.add_argument("--task-type", required=True, help="W2 routing catalog task_type")
    parser.add_argument("--case-dir", required=True, help="Repo-relative or absolute case path")
    parser.add_argument("--json", action="store_true", help="Emit full result as JSON")
    args = parser.parse_args(argv)

    result = evaluate_intake_decision(args.task_type, args.case_dir)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"decision: {result['decision']}")
        print(f"risk_level: {result['risk_level']}")
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
