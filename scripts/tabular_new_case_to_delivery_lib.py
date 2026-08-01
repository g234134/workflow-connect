"""Intake → delivery one-command orchestration for Tabular cases."""



from __future__ import annotations



import json

from pathlib import Path

from typing import Any



from export_case_delivery_zip import export_case_delivery_zip

from new_cleaning_case import create_cleaning_case

from suggest_cleaning_profile import suggest_cleaning_profile

from tabular_automation_driver_lib import run_tabular_automation

from tabular_automation_state_lib import (

    PAUSE_REASON_CHECKPOINT_A,

    PAUSE_REASON_CHECKPOINT_B,

    load_state,

    start_automation,

    stop_automation,

)

from tabular_delivery_approval_lib import approve_tabular_delivery, load_approval

from tabular_hitl_resume_lib import apply_tabular_checkpoint_decision, resume_after_checkpoint

from tabular_warning_guard_lib import evaluate_case_guard_policy

from validate_intake import validate_intake



SCHEMA_VERSION = "tabular-new-case-to-delivery-v1"

DEFAULT_OPERATOR = "new_case_to_delivery"



_ANCHOR_CASES = frozenset(

    {

        "cases/demo_phase",

        "cases/sampleco/2026-0001",

        "cases/internal/generic-low-risk",

    }

)





def _repo_rel(path: Path, repo_root: Path) -> str:

    return path.resolve().relative_to(repo_root.resolve()).as_posix()





def _read_eligibility_result(case_dir: Path) -> dict[str, Any]:

    path = case_dir / "reports" / "eligibility_result.json"

    if not path.is_file():

        return {}

    try:

        data = json.loads(path.read_text(encoding="utf-8"))

    except (OSError, json.JSONDecodeError):

        return {}

    return data if isinstance(data, dict) else {}





def resolve_auto_resume_policy(case_dir: Path, *, repo_root: Path) -> dict[str, Any]:

    """Determine whether internal auto-resume is allowed (no silent full-auto for warning cases)."""

    profile = suggest_cleaning_profile(case_dir, repo_root=repo_root)

    guard = evaluate_case_guard_policy(case_dir)

    policy = guard.get("policy") or {}

    eligibility = profile.get("eligibility")

    suggested = profile.get("suggested_profile")

    elig_result = _read_eligibility_result(case_dir)

    gate_eligibility = str(elig_result.get("eligibility") or "")



    auto_resume_allowed = (

        suggested == "generic_low_risk_profile"

        and eligibility == "accepted"

        and gate_eligibility in {"", "accepted", "review_needed"}

        and bool(policy.get("cp_b_auto_skip_allowed", False) or suggested == "generic_low_risk_profile")

    )



    will_pause_at: str | None = None

    if gate_eligibility == "review_needed" and suggested != "generic_low_risk_profile":

        will_pause_at = "checkpoint_a"

    elif not policy.get("cp_b_auto_skip_allowed", True) and guard.get("profile") == "sampleco":

        will_pause_at = "checkpoint_b"

    elif eligibility == "needs_review":

        will_pause_at = "checkpoint_a"

    elif guard.get("guard_status") == "warning" and not policy.get("delivery_ready_allowed"):

        will_pause_at = "checkpoint_b"



    return {

        "auto_resume_allowed": auto_resume_allowed,

        "will_pause_at": will_pause_at,

        "suggested_profile": suggested,

        "eligibility": eligibility or gate_eligibility,

        "warning_guard_profile": guard.get("profile"),

        "output_guard_status": guard.get("guard_status"),

        "policy": policy,

    }





def plan_new_case_to_delivery_phases(

    *,

    start: bool,

    auto_resume: bool,

    export_zip: bool,

) -> list[str]:

    phases = ["validate_intake", "suggest_cleaning_profile", "resolve_auto_resume_policy"]

    if start:

        phases.extend(["start_automation", "run_tabular_automation"])

    if auto_resume:

        phases.append("auto_resume_hitl (internal allowlist only)")

    phases.extend(["approve_tabular_delivery"])

    if export_zip:

        phases.append("export_case_delivery_zip")

    return phases





def _auto_resume_hitl_if_allowed(

    case_dir: Path,

    *,

    requested_by: str,

    phases: list[dict[str, Any]],

    policy: dict[str, Any],

) -> dict[str, Any]:

    if not policy.get("auto_resume_allowed"):

        return {

            "ok": True,

            "skipped": True,

            "message": "auto-resume not allowed by policy",

            "will_pause_at": policy.get("will_pause_at"),

        }



    for _ in range(6):

        state = load_state(case_dir)

        if state.get("automation_status") != "paused":

            break

        pause = state.get("pause_reason")

        if pause == PAUSE_REASON_CHECKPOINT_A:

            cmd = "approve-a"

        elif pause == PAUSE_REASON_CHECKPOINT_B:

            cmd = "approve-b"

        else:

            return {

                "ok": False,

                "message": f"unexpected pause_reason={pause!r}",

                "will_pause_at": policy.get("will_pause_at"),

            }

        decision = apply_tabular_checkpoint_decision(

            case_dir,

            command=cmd,

            operator_id=requested_by,

            notes="new_case_to_delivery internal auto-resume",

        )

        phases.append({"phase": cmd, "result": decision})

        if not decision.get("ok"):

            return decision

        resume = resume_after_checkpoint(case_dir, requested_by=requested_by)

        phases.append({"phase": f"resume-after-{cmd}", "result": resume})

        if not resume.get("ok"):

            return resume



        driver = run_tabular_automation(case_dir, start_from="intake", force=False)

        phases.append({"phase": "driver-after-resume", "result": driver})



    return {"ok": True, "message": "auto-resume complete"}





def run_new_case_to_delivery(

    case_dir: Path,

    *,

    repo_root: Path,

    start: bool = False,

    requested_by: str = DEFAULT_OPERATOR,

    force_driver: bool = False,

    export_zip: bool = True,

    dry_run: bool = False,

) -> dict[str, Any]:

    case_dir = case_dir.resolve()

    rel = _repo_rel(case_dir, repo_root)

    phases: list[dict[str, Any]] = []



    policy = resolve_auto_resume_policy(case_dir, repo_root=repo_root)

    phases.append({"phase": "policy", "result": policy})



    planned = plan_new_case_to_delivery_phases(

        start=start,

        auto_resume=policy.get("auto_resume_allowed") is True and start,

        export_zip=export_zip,

    )



    if dry_run:

        return {

            "ok": True,

            "dry_run": True,

            "schema_version": SCHEMA_VERSION,

            "case_dir": rel,

            "phases": planned,

            "delivery_ready": None,

            "zip_path": None,

            "will_pause_at": policy.get("will_pause_at"),

            "auto_resume_allowed": policy.get("auto_resume_allowed"),

            "message": "dry-run plan only; no mutations",

        }



    intake = validate_intake(case_dir)

    phases.append({"phase": "validate-intake", "result": intake})

    if not intake.get("ok"):

        return {

            "ok": False,

            "schema_version": SCHEMA_VERSION,

            "case_dir": rel,

            "phases": phases,

            "delivery_ready": False,

            "zip_path": None,

            "will_pause_at": policy.get("will_pause_at"),

            "message": intake.get("message"),

        }



    profile = suggest_cleaning_profile(case_dir, repo_root=repo_root)

    phases.append({"phase": "suggest-profile", "result": profile})



    if start:

        state = load_state(case_dir)

        if state.get("automation_status") in {"running", "paused"}:

            stop = stop_automation(case_dir, requested_by=requested_by)

            phases.append({"phase": "stop-before-restart", "result": stop})

        ctl = start_automation(case_dir, requested_by=requested_by, restart=True)

        phases.append({"phase": "start", "result": ctl})

        if not ctl.get("ok"):

            return {

                "ok": False,

                "schema_version": SCHEMA_VERSION,

                "case_dir": rel,

                "phases": phases,

                "delivery_ready": False,

                "zip_path": None,

                "will_pause_at": policy.get("will_pause_at"),

                "message": ctl.get("message"),

            }



        driver = run_tabular_automation(case_dir, start_from="intake", force=force_driver)

        phases.append({"phase": "driver", "result": driver})



        if policy.get("auto_resume_allowed"):

            hitl = _auto_resume_hitl_if_allowed(

                case_dir,

                requested_by=requested_by,

                phases=phases,

                policy=policy,

            )

            phases.append({"phase": "auto-resume", "result": hitl})

            if not hitl.get("ok"):

                state = load_state(case_dir)

                return {

                    "ok": False,

                    "schema_version": SCHEMA_VERSION,

                    "case_dir": rel,

                    "phases": phases,

                    "delivery_ready": False,

                    "zip_path": None,

                    "will_pause_at": policy.get("will_pause_at") or state.get("current_step"),

                    "message": hitl.get("message"),

                }

        else:

            state = load_state(case_dir)

            if state.get("automation_status") == "paused":

                return {

                    "ok": True,

                    "schema_version": SCHEMA_VERSION,

                    "case_dir": rel,

                    "phases": phases,

                    "delivery_ready": False,

                    "zip_path": None,

                    "will_pause_at": policy.get("will_pause_at") or state.get("pause_reason"),

                    "message": "paused at HITL — auto-resume not allowed by policy",

                }



    approve = approve_tabular_delivery(

        case_dir,

        approved_by=requested_by,

        reason="new_case_to_delivery approve",

        repo_root=repo_root,

    )

    phases.append({"phase": "delivery-approve", "result": approve})



    zip_result: dict[str, Any] = {"ok": True, "skipped": True}

    zip_path: str | None = None

    if export_zip and approve.get("delivery_ready"):

        zip_result = export_case_delivery_zip(case_dir, repo_root=repo_root, refresh_bundle=False)

        phases.append({"phase": "export-zip", "result": zip_result})

        zip_path = zip_result.get("zip_path")



    delivery_ready = bool(approve.get("delivery_ready"))

    state = load_state(case_dir)

    will_pause = policy.get("will_pause_at")

    if state.get("automation_status") == "paused" and not delivery_ready:

        will_pause = will_pause or state.get("pause_reason") or state.get("current_step")



    chain_ok = True

    if start:

        chain_ok = any(

            (p.get("result") or {}).get("ok") is True

            for p in phases

            if p.get("phase") in {"driver", "driver-after-resume"}

        ) or state.get("automation_status") == "completed"



    ok = chain_ok and (delivery_ready or will_pause is not None or not start)

    return {

        "ok": ok,

        "schema_version": SCHEMA_VERSION,

        "case_dir": rel,

        "phases": phases,

        "delivery_ready": delivery_ready,

        "zip_path": zip_path,

        "will_pause_at": will_pause,

        "auto_resume_allowed": policy.get("auto_resume_allowed"),

        "message": "orchestration complete" if ok else "orchestration incomplete — see phases",

    }





def create_case_from_intake(

    *,

    client_ref: str,

    product_sku: str,

    source_file: Path,

    repo_root: Path,

) -> dict[str, Any]:

    return create_cleaning_case(

        client_ref=client_ref,

        product_sku=product_sku,

        source_file=source_file,

        repo_root=repo_root,

    )





def resolve_case_dir_from_args(

    *,

    case_dir: Path | None,

    client_ref: str | None,

    product_sku: str | None,

    source_file: Path | None,

    repo_root: Path,

) -> tuple[Path | None, dict[str, Any] | None]:

    if case_dir is not None:

        resolved = case_dir.resolve() if case_dir.is_absolute() else (repo_root / case_dir).resolve()

        if not resolved.is_dir():

            return None, {"ok": False, "message": f"case_dir not found: {case_dir}"}

        return resolved, None



    if client_ref and product_sku and source_file:

        created = create_case_from_intake(

            client_ref=client_ref,

            product_sku=product_sku,

            source_file=source_file if source_file.is_absolute() else repo_root / source_file,

            repo_root=repo_root,

        )

        if not created.get("ok"):

            return None, created

        return Path(created["case_dir"]).resolve(), created



    return None, {

        "ok": False,

        "message": "specify --case-dir or (--client-ref + --product-sku + --source-file)",

    }

