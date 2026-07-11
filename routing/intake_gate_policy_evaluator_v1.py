"""Evaluate Intake Gate policy hits (P75-G3).

Outputs policy hits only; canonical gate ``decision`` is resolved by the layer
after merging with ``intake_decision_rules_v2``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

from routing.intake_gate_policy_types_v1 import PolicyEvalResult, PolicyHit

_REPO_ROOT = Path(__file__).resolve().parents[1]

_G1_REASON_CODES: Set[str] = {
    "supported_task",
    "allowlist_fixture",
    "manual_review_required",
    "experimental_fixture",
    "unknown_client_profile",
    "unsupported_task_type",
    "non_tabular_without_flag",
    "case_dir_not_found",
    "glue_plan_failed",
    "policy_deny_phi",
    "policy_deny_web_scraping",
    "policy_deny_audio_video",
    "policy_deny_scale_exceeds",
}


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


def _read_intake(case_dir: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    normalized = _normalize_case_dir(case_dir)
    intake_path = normalized / "intake.json"
    if not intake_path.is_file():
        return None, None
    try:
        payload = json.loads(intake_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"intake_json_invalid: {exc.msg}"
    except OSError as exc:
        return None, f"intake_read_failed: {exc}"
    if not isinstance(payload, dict):
        return None, "intake_json_not_object"
    return payload, None


def _coerce_flags(flags: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not flags:
        return {}
    return dict(flags)


def _supported_task_types(policy: Mapping[str, Any]) -> Tuple[Set[str], Set[str]]:
    supported = policy.get("supported_task_types") or {}
    tabular = {str(item) for item in supported.get("tabular") or []}
    non_tabular = {str(item) for item in supported.get("non_tabular") or []}
    return tabular, non_tabular


def _resolve_profile_from_policy(
    policy: Mapping[str, Any],
    *,
    case_dir: str,
    intake: Optional[Mapping[str, Any]],
) -> Tuple[str, str, str, Optional[Mapping[str, Any]]]:
    normalized = _normalize_case_dir(case_dir)
    case_id = str((intake or {}).get("case_id") or normalized.name)
    client_ref = str((intake or {}).get("client_ref") or "")

    for tier_entry in policy.get("allowlist_tiers") or []:
        if not isinstance(tier_entry, dict):
            continue
        match = tier_entry.get("match") or {}
        case_ids = {str(item) for item in match.get("case_ids") or []}
        client_refs = {str(item) for item in match.get("client_refs") or []}
        profile_id = str(tier_entry.get("profile_id") or "")
        if case_id in case_ids or client_ref in client_refs:
            return (
                profile_id,
                str(tier_entry.get("tier") or "unknown"),
                str(tier_entry.get("maturity") or "unknown"),
                tier_entry,
            )
        if profile_id and (case_id == profile_id or normalized.name == profile_id):
            return (
                profile_id,
                str(tier_entry.get("tier") or "unknown"),
                str(tier_entry.get("maturity") or "unknown"),
                tier_entry,
            )

    profile_id = case_id or normalized.name
    return profile_id, "unknown", "unknown", None


def _intake_flag_true(intake: Optional[Mapping[str, Any]], flag_name: str) -> bool:
    if not intake:
        return False
    if intake.get(flag_name) is True:
        return True
    security = intake.get("security_compliance")
    if isinstance(security, dict) and security.get(flag_name) is True:
        return True
    return False


def _matches_deny_rule(
    rule: Mapping[str, Any],
    *,
    intake: Optional[Mapping[str, Any]],
) -> Tuple[bool, str]:
    match = rule.get("match") or {}
    if not isinstance(match, dict):
        return False, "invalid deny match block"

    sensitivity_values = {str(v).lower() for v in match.get("sensitivity_values") or []}
    if sensitivity_values and intake:
        sensitivity = str(intake.get("sensitivity") or "").lower()
        if sensitivity in sensitivity_values:
            return True, f"sensitivity={sensitivity}"

    for flag_name in match.get("intake_flags") or []:
        if _intake_flag_true(intake, str(flag_name)):
            return True, f"intake_flag={flag_name}"

    provenance_types = {str(v).lower() for v in match.get("provenance_source_types") or []}
    if provenance_types and intake:
        provenance = intake.get("provenance")
        if isinstance(provenance, dict):
            source_type = str(provenance.get("source_type") or "").lower()
            if source_type in provenance_types:
                return True, f"provenance.source_type={source_type}"

    structure_values = {str(v).lower() for v in match.get("structure_values") or []}
    if structure_values and intake:
        structure = str(intake.get("structure") or "").lower()
        if structure in structure_values:
            return True, f"structure={structure}"

    scale_limits = match.get("scale_limits")
    if isinstance(scale_limits, dict) and intake:
        scale = intake.get("scale")
        if isinstance(scale, dict):
            row_count = scale.get("row_count")
            file_size = scale.get("file_size_bytes")
            batch_files = scale.get("batch_files")
            max_rows = scale_limits.get("max_row_count")
            max_size = scale_limits.get("max_file_size_bytes")
            max_batch = scale_limits.get("max_batch_files")
            if isinstance(max_rows, int) and isinstance(row_count, int) and row_count > max_rows:
                return True, f"scale.row_count={row_count}>{max_rows}"
            if isinstance(max_size, int) and isinstance(file_size, int) and file_size > max_size:
                return True, f"scale.file_size_bytes={file_size}>{max_size}"
            if isinstance(max_batch, int) and isinstance(batch_files, int) and batch_files > max_batch:
                return True, f"scale.batch_files={batch_files}>{max_batch}"

    return False, "no deny match"


def _evaluate_deny_rules(
    policy: Mapping[str, Any],
    *,
    intake: Optional[Mapping[str, Any]],
) -> List[PolicyHit]:
    hits: List[PolicyHit] = []
    for rule in policy.get("deny_rules") or []:
        if not isinstance(rule, dict):
            continue
        matched, detail = _matches_deny_rule(rule, intake=intake)
        rule_id = str(rule.get("rule_id") or "POLICY-DENY-UNKNOWN")
        reason_code = str(rule.get("reason_code") or "")
        hits.append(
            PolicyHit(
                rule_id=rule_id,
                passed=not matched,
                detail=detail if matched else "deny rule not matched",
                reason_code=reason_code if matched else None,
                suggested_action="reject" if matched else "none",
                hit_kind="deny",
            )
        )
    return hits


def evaluate_policy(
    policy: Mapping[str, Any],
    *,
    task_type: str,
    case_dir: str,
    intake: Optional[Mapping[str, Any]] = None,
    flags: Optional[Mapping[str, Any]] = None,
) -> PolicyEvalResult:
    """Evaluate policy and return structured hits (not canonical gate decision)."""
    policy_version = str(policy.get("policy_version") or "intake_gate_policy_v1")
    flag_map = _coerce_flags(flags)
    include_extended = bool(flag_map.get("include_extended_fixtures"))

    if intake is None:
        intake, _ = _read_intake(case_dir)

    profile_id, profile_tier, profile_maturity, tier_entry = _resolve_profile_from_policy(
        policy,
        case_dir=case_dir,
        intake=intake,
    )

    hits: List[PolicyHit] = []
    defaults = policy.get("defaults") or {}
    tabular_supported, non_tabular_supported = _supported_task_types(policy)
    normalized_tt = _normalize_non_tabular_task_type(task_type)

    hits.extend(_evaluate_deny_rules(policy, intake=intake))

    if _is_tabular_family(task_type):
        task_supported = task_type in tabular_supported
        family = "tabular"
    elif _is_non_tabular_family(task_type):
        task_supported = normalized_tt in non_tabular_supported
        family = "non_tabular"
    else:
        task_supported = False
        family = "other"

    hits.append(
        PolicyHit(
            rule_id="POLICY-TASK-01",
            passed=task_supported,
            detail=(
                f"task_type={task_type} supported in {family} set"
                if task_supported
                else f"task_type={task_type} not in policy supported_task_types"
            ),
            reason_code="supported_task" if task_supported else "unsupported_task_type",
            suggested_action="none" if task_supported else str(defaults.get("unsupported_task_type") or "reject"),
            hit_kind="task_type",
        )
    )

    if family == "non_tabular" and not include_extended:
        non_tabular_action = str(defaults.get("non_tabular_without_extended_flag") or "reject")
        hits.append(
            PolicyHit(
                rule_id="POLICY-NT-01",
                passed=False,
                detail="non_tabular task without include_extended_fixtures flag",
                reason_code="non_tabular_without_flag",
                suggested_action=non_tabular_action,  # type: ignore[arg-type]
                hit_kind="non_tabular_flag",
            )
        )
    elif family == "non_tabular":
        hits.append(
            PolicyHit(
                rule_id="POLICY-NT-01",
                passed=True,
                detail="include_extended_fixtures flag set for non_tabular",
                hit_kind="non_tabular_flag",
            )
        )

    if tier_entry is not None:
        hits.append(
            PolicyHit(
                rule_id="POLICY-ALLOW-01",
                passed=True,
                detail=f"allowlist profile={profile_id} tier={profile_tier} maturity={profile_maturity}",
                reason_code="allowlist_fixture",
                hit_kind="allowlist",
            )
        )
        requires_extended = bool(tier_entry.get("requires_extended_fixture_flag"))
        if requires_extended and not include_extended:
            hits.append(
                PolicyHit(
                    rule_id="POLICY-TIER-EXT-01",
                    passed=False,
                    detail=f"tier {profile_tier} requires include_extended_fixtures",
                    reason_code="experimental_fixture",
                    suggested_action="review_needed",
                    hit_kind="allowlist",
                )
            )
        elif requires_extended:
            hits.append(
                PolicyHit(
                    rule_id="POLICY-TIER-EXT-01",
                    passed=True,
                    detail=f"tier {profile_tier} extended flag satisfied",
                    hit_kind="allowlist",
                )
            )
    else:
        unknown_action = str(defaults.get("unknown_client") or "review_needed")
        hits.append(
            PolicyHit(
                rule_id="POLICY-UNKNOWN-01",
                passed=False,
                detail=f"profile={profile_id} not in allowlist tiers",
                reason_code="unknown_client_profile",
                suggested_action=unknown_action,  # type: ignore[arg-type]
                hit_kind="allowlist",
            )
        )

    return PolicyEvalResult(
        ok=True,
        policy_version=policy_version,
        profile_id=profile_id,
        profile_tier=profile_tier,
        profile_maturity=profile_maturity,
        hits=hits,
        message=f"policy evaluated for task_type={task_type} case_dir={_rel_case_dir(case_dir)}",
    )


def g1_reason_codes() -> Set[str]:
    """Return the G1 reason_code enum subset referenced by policy bridge."""
    return set(_G1_REASON_CODES)
