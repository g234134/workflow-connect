"""Shared Tabular main-chain regression smoke helpers (multi-case)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tabular_automation_driver_lib import run_log_path, run_tabular_automation  # noqa: E402
from tabular_automation_state_lib import (  # noqa: E402
    PAUSE_REASON_CHECKPOINT_A,
    PAUSE_REASON_CHECKPOINT_B,
    load_state,
    start_automation,
    stop_automation,
)
from tabular_delivery_approval_lib import (  # noqa: E402
    approve_tabular_delivery,
    evaluate_delivery_readiness,
    load_approval,
)
from tabular_hitl_resume_lib import (  # noqa: E402
    apply_tabular_checkpoint_decision,
    resume_after_checkpoint,
)

DEFAULT_OPERATOR = "regression_smoke"


def _repo_rel(case_dir: Path, repo_root: Path) -> str:
    return case_dir.resolve().relative_to(repo_root.resolve()).as_posix()


def _load_run_log(case_dir: Path) -> dict[str, Any]:
    path = run_log_path(case_dir)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _step_from_run_log(run_log: dict[str, Any], step_name: str) -> dict[str, Any] | None:
    steps = run_log.get("steps")
    if not isinstance(steps, list):
        return None
    for step in reversed(steps):
        if isinstance(step, dict) and step.get("step_name") == step_name:
            return step
    return None


def _artifact_paths(case_dir: Path) -> dict[str, Any]:
    cleaned = (
        sorted((case_dir / "cleaned").glob("*_cleaned.csv"))
        if (case_dir / "cleaned").is_dir()
        else []
    )
    return {
        "automation_state": str(case_dir / "automation_state.json"),
        "automation_run_log": str(run_log_path(case_dir)),
        "delivery_approval": str(case_dir / "delivery_approval.json"),
        "eligibility_result": str(case_dir / "reports" / "eligibility_result.json"),
        "report_json": str(case_dir / "reports" / "report.json"),
        "report_md": str(case_dir / "reports" / "report.md"),
        "cleaning_stats": str(case_dir / "reports" / "cleaning_stats.json"),
        "delivery_signoff": str(case_dir / "delivery_signoff.md"),
        "cleaned_csv_count": len(cleaned),
        "cleaned_csv": [str(p) for p in cleaned[:3]],
    }


def verify_case_regression(
    case_dir: Path,
    *,
    repo_root: Path,
    case_id: str | None = None,
    expected_delivery_ready: bool | None = None,
) -> dict[str, Any]:
    state = load_state(case_dir)
    approval = load_approval(case_dir)
    run_log = _load_run_log(case_dir)
    readiness = evaluate_delivery_readiness(case_dir)

    failures: list[str] = []
    automation_status = state.get("automation_status")
    current_step = state.get("current_step")
    delivery_ready = bool(approval.get("delivery_ready"))

    if automation_status != "completed":
        failures.append(f"automation_status={automation_status!r}; expected 'completed'")

    e2e_step = _step_from_run_log(run_log, "e2e")
    e2e_ok = e2e_step is not None and e2e_step.get("step_status") == "completed"
    if not e2e_ok:
        failures.append("overall_ok=false: automation_run_log e2e step missing or not completed")

    cp_a = state.get("checkpoint_a_status")
    cp_b = state.get("checkpoint_b_status")
    cp_b_step = _step_from_run_log(run_log, "checkpoint_b")
    cp_b_step_ok = cp_b_step is not None and cp_b_step.get("step_status") == "completed"

    if cp_a not in ("approved", "not_required"):
        failures.append(f"checkpoint_a_status={cp_a!r}; expected 'approved' or 'not_required'")
    if cp_b not in ("approved", "not_required"):
        failures.append(f"checkpoint_b_status={cp_b!r}; expected 'approved' or 'not_required'")
    elif cp_b == "not_required" and not cp_b_step_ok:
        failures.append("checkpoint_b_status='not_required' but run log checkpoint_b not completed")

    acceptable_steps = {"checkpoint_b", "delivery", "approved_for_delivery"}
    if current_step not in acceptable_steps:
        failures.append(
            f"current_step={current_step!r}; expected one of {sorted(acceptable_steps)}"
        )

    if expected_delivery_ready is not None:
        if delivery_ready != expected_delivery_ready:
            gaps = approval.get("readiness_gaps") or readiness.get("readiness_gaps") or []
            failures.append(
                f"delivery_ready={delivery_ready}; expected {expected_delivery_ready}; gaps={gaps}"
            )
    elif not delivery_ready and approval.get("delivery_approval_status") != "approved":
        gaps = approval.get("readiness_gaps") or readiness.get("readiness_gaps") or []
        failures.append(f"delivery_ready=false; gaps={gaps}")

    artifacts = _artifact_paths(case_dir)
    for key in ("report_json", "delivery_signoff"):
        if not Path(artifacts[key]).is_file():
            failures.append(f"missing artifact: {key}")
    if artifacts["cleaned_csv_count"] < 1:
        failures.append("missing cleaned/*_cleaned.csv")

    overall_ok = not failures and e2e_ok
    resolved_case_id = case_id or state.get("case_id") or case_dir.name

    return {
        "ok": overall_ok,
        "case_id": resolved_case_id,
        "case_dir": _repo_rel(case_dir, repo_root),
        "automation_status": automation_status,
        "current_step": current_step,
        "overall_ok": overall_ok,
        "delivery_ready": delivery_ready,
        "delivery_approval_status": approval.get("delivery_approval_status"),
        "checkpoint_a_status": cp_a,
        "checkpoint_b_status": cp_b,
        "e2e_step_status": (e2e_step or {}).get("step_status"),
        "run_log_ok": run_log.get("ok"),
        "readiness": readiness,
        "artifacts": artifacts,
        "failures": failures,
        "expected_delivery_ready": expected_delivery_ready,
    }


def _prepare_fresh_start(case_dir: Path, *, requested_by: str) -> dict[str, Any]:
    state = load_state(case_dir)
    status = state.get("automation_status", "idle")
    if status in {"running", "paused"}:
        stop_result = stop_automation(case_dir, requested_by=requested_by)
        if not stop_result.get("ok"):
            return stop_result
    return start_automation(case_dir, requested_by=requested_by, restart=True)


def _handle_hitl_pause(
    case_dir: Path,
    *,
    requested_by: str,
    phases: list[dict[str, Any]],
) -> dict[str, Any]:
    state = load_state(case_dir)
    pause_reason = state.get("pause_reason")
    if state.get("automation_status") != "paused":
        return {"ok": True, "action": "none", "pause_reason": pause_reason, "state": state}

    if pause_reason == PAUSE_REASON_CHECKPOINT_A:
        approve = apply_tabular_checkpoint_decision(
            case_dir,
            command="approve-a",
            operator_id=requested_by,
            notes="regression smoke auto-approve CP-A",
        )
        phases.append({"phase": "approve-a", "result": approve})
        if not approve.get("ok"):
            return approve
        resume = resume_after_checkpoint(case_dir, requested_by=requested_by)
        phases.append({"phase": "resume-after-cp-a", "result": resume})
        return resume

    if pause_reason == PAUSE_REASON_CHECKPOINT_B:
        approve = apply_tabular_checkpoint_decision(
            case_dir,
            command="approve-b",
            operator_id=requested_by,
            notes="regression smoke auto-approve CP-B",
        )
        phases.append({"phase": "approve-b", "result": approve})
        if not approve.get("ok"):
            return approve
        resume = resume_after_checkpoint(case_dir, requested_by=requested_by)
        phases.append({"phase": "resume-after-cp-b", "result": resume})
        return resume

    return {
        "ok": False,
        "message": f"unexpected pause_reason={pause_reason!r}",
        "state": state,
    }


def run_case_regression_smoke(
    case_dir: Path,
    *,
    repo_root: Path,
    case_id: str | None = None,
    requested_by: str = DEFAULT_OPERATOR,
    dry_run: bool = False,
    force_driver: bool = False,
    expected_delivery_ready: bool | None = None,
) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    resolved_id = case_id or case_dir.name
    phases: list[dict[str, Any]] = []

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "case_id": resolved_id,
            "case_dir": _repo_rel(case_dir, repo_root),
            "planned_phases": [
                "prepare_fresh_start",
                "run_tabular_automation",
                "approve-a/b + resume-after-checkpoint (if paused)",
                "approve_tabular_delivery",
                "verify_regression",
            ],
            "message": "dry-run plan only; no mutations",
        }

    start = _prepare_fresh_start(case_dir, requested_by=requested_by)
    phases.append({"phase": "start", "result": start})
    if not start.get("ok"):
        return {
            "ok": False,
            "case_id": resolved_id,
            "phases": phases,
            "message": start.get("message", "start failed"),
            "verification": verify_case_regression(
                case_dir,
                repo_root=repo_root,
                case_id=resolved_id,
                expected_delivery_ready=expected_delivery_ready,
            ),
        }

    driver = run_tabular_automation(
        case_dir,
        start_from="intake",
        force=force_driver,
    )
    phases.append({"phase": "driver-initial", "result": driver})

    for _ in range(6):
        state = load_state(case_dir)
        if state.get("automation_status") == "paused":
            hitl = _handle_hitl_pause(case_dir, requested_by=requested_by, phases=phases)
            if hitl.get("action") == "none":
                break
            if not hitl.get("ok"):
                state = load_state(case_dir)
                if state.get("automation_status") != "paused":
                    return {
                        "ok": False,
                        "case_id": resolved_id,
                        "phases": phases,
                        "message": hitl.get("message", "HITL resume failed"),
                        "verification": verify_case_regression(
                            case_dir,
                            repo_root=repo_root,
                            case_id=resolved_id,
                            expected_delivery_ready=expected_delivery_ready,
                        ),
                    }
            continue

        if state.get("automation_status") == "running" and state.get("checkpoint_resume_step"):
            resume = resume_after_checkpoint(case_dir, requested_by=requested_by)
            phases.append({"phase": "resume-after-checkpoint", "result": resume})
            if not resume.get("ok"):
                state = load_state(case_dir)
                if state.get("automation_status") == "paused":
                    continue
            continue

        if state.get("automation_status") in {"completed", "failed", "stopped"}:
            break

        driver_follow = run_tabular_automation(case_dir, start_from="intake", force=force_driver)
        phases.append({"phase": "driver-followup", "result": driver_follow})
        if driver_follow.get("ok"):
            break
        state = load_state(case_dir)
        if state.get("automation_status") != "paused":
            break

    approve = approve_tabular_delivery(
        case_dir,
        approved_by=requested_by,
        reason=f"{resolved_id} regression smoke",
        repo_root=repo_root,
    )
    phases.append({"phase": "delivery-approve", "result": approve})

    verification = verify_case_regression(
        case_dir,
        repo_root=repo_root,
        case_id=resolved_id,
        expected_delivery_ready=expected_delivery_ready,
    )
    overall_ok = verification.get("overall_ok") is True
    verification["ok"] = overall_ok

    return {
        "ok": overall_ok,
        "case_id": resolved_id,
        "phases": phases,
        "delivery_approve": {
            "ok": approve.get("ok"),
            "delivery_ready": approve.get("delivery_ready"),
            "message": approve.get("message"),
        },
        "verification": verification,
        "message": (
            f"{resolved_id} main-chain regression passed"
            if overall_ok
            else f"{resolved_id} main-chain regression failed — see verification.failures"
        ),
    }

