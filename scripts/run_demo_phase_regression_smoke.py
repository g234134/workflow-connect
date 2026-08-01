#!/usr/bin/env python3
"""Tabular demo_phase main-chain regression smoke (control plane + driver + HITL + approve).

Runs the full demo_phase anchor flow and verifies pass criteria documented in
``docs/tabular-demo_phase-regression-v1.md``.

Usage:
    python scripts/run_demo_phase_regression_smoke.py
    python scripts/run_demo_phase_regression_smoke.py --json
    python scripts/run_demo_phase_regression_smoke.py --dry-run --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_automation_driver_lib import (  # noqa: E402
    run_log_path,
    run_tabular_automation,
)
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

CASE_ID = "demo_phase"
CASE_DIR = _REPO_ROOT / "cases" / "demo_phase"
DEFAULT_OPERATOR = "regression_smoke"


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
    cleaned = sorted((case_dir / "cleaned").glob("*_cleaned.csv")) if (case_dir / "cleaned").is_dir() else []
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


def verify_regression(case_dir: Path) -> dict[str, Any]:
    """Evaluate post-run pass criteria (see docs/tabular-demo_phase-regression-v1.md §4)."""
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
        failures.append(
            "overall_ok=false: automation_run_log e2e step missing or not completed"
        )

    cp_a = state.get("checkpoint_a_status")
    cp_b = state.get("checkpoint_b_status")
    cp_b_step = _step_from_run_log(run_log, "checkpoint_b")
    cp_b_step_ok = cp_b_step is not None and cp_b_step.get("step_status") == "completed"

    if cp_a != "approved":
        failures.append(f"checkpoint_a_status={cp_a!r}; expected 'approved'")
    if cp_b not in ("approved", "not_required"):
        failures.append(f"checkpoint_b_status={cp_b!r}; expected 'approved' or 'not_required'")
    elif cp_b == "not_required" and not cp_b_step_ok:
        failures.append("checkpoint_b_status='not_required' but run log checkpoint_b not completed")

    acceptable_steps = {"checkpoint_b", "delivery", "approved_for_delivery"}
    if current_step not in acceptable_steps:
        failures.append(
            f"current_step={current_step!r}; expected one of {sorted(acceptable_steps)}"
        )

    if not delivery_ready:
        gaps = approval.get("readiness_gaps") or readiness.get("readiness_gaps") or []
        failures.append(f"delivery_ready=false; gaps={gaps}")

    artifacts = _artifact_paths(case_dir)
    for key in ("report_json", "delivery_signoff"):
        if not Path(artifacts[key]).is_file():
            failures.append(f"missing artifact: {key}")
    if artifacts["cleaned_csv_count"] < 1:
        failures.append("missing cleaned/*_cleaned.csv")

    overall_ok = not failures and e2e_ok

    return {
        "ok": overall_ok,
        "case_id": CASE_ID,
        "case_dir": str(case_dir.relative_to(_REPO_ROOT)).replace("\\", "/"),
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


def run_demo_phase_regression_smoke(
    *,
    requested_by: str = DEFAULT_OPERATOR,
    dry_run: bool = False,
) -> dict[str, Any]:
    case_dir = CASE_DIR.resolve()
    phases: list[dict[str, Any]] = []

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "case_id": CASE_ID,
            "case_dir": str(case_dir.relative_to(_REPO_ROOT)).replace("\\", "/"),
            "planned_phases": [
                "prepare_fresh_start",
                "run_tabular_automation (no --force)",
                "approve-a + resume-after-checkpoint",
                "approve-b + resume-after-checkpoint (if paused)",
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
            "case_id": CASE_ID,
            "phases": phases,
            "message": start.get("message", "start failed"),
            "verification": verify_regression(case_dir),
        }

    driver = run_tabular_automation(case_dir, start_from="intake", force=False)
    phases.append({"phase": "driver-initial", "result": driver})

    hitl_a = _handle_hitl_pause(case_dir, requested_by=requested_by, phases=phases)
    if not hitl_a.get("ok"):
        verification = verify_regression(case_dir)
        return {
            "ok": False,
            "case_id": CASE_ID,
            "phases": phases,
            "message": hitl_a.get("message", "CP-A resume failed"),
            "verification": verification,
        }

    hitl_b = _handle_hitl_pause(case_dir, requested_by=requested_by, phases=phases)
    if not hitl_b.get("ok"):
        verification = verify_regression(case_dir)
        return {
            "ok": False,
            "case_id": CASE_ID,
            "phases": phases,
            "message": hitl_b.get("message", "CP-B resume failed"),
            "verification": verification,
        }

    approve = approve_tabular_delivery(
        case_dir,
        approved_by=requested_by,
        reason="demo_phase regression smoke",
    )
    phases.append({"phase": "delivery-approve", "result": approve})

    verification = verify_regression(case_dir)
    overall_ok = verification.get("overall_ok") is True and approve.get("delivery_ready") is True
    verification["ok"] = overall_ok

    return {
        "ok": overall_ok,
        "case_id": CASE_ID,
        "phases": phases,
        "delivery_approve": {
            "ok": approve.get("ok"),
            "delivery_ready": approve.get("delivery_ready"),
            "message": approve.get("message"),
        },
        "verification": verification,
        "summary": {
            "automation_status": verification.get("automation_status"),
            "overall_ok": verification.get("overall_ok"),
            "delivery_ready": verification.get("delivery_ready"),
            "e2e_step_status": verification.get("e2e_step_status"),
            "failures": verification.get("failures"),
        },
        "message": (
            "demo_phase main-chain regression passed"
            if overall_ok
            else "demo_phase main-chain regression failed — see verification.failures"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run Tabular demo_phase main-chain regression "
            "(control plane + driver + HITL + delivery approve)."
        )
    )
    parser.add_argument(
        "--operator",
        default=DEFAULT_OPERATOR,
        help=f"Operator id for HITL/approve audit (default: {DEFAULT_OPERATOR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned phases only; do not mutate case artifacts",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON result")
    args = parser.parse_args(argv)

    result = run_demo_phase_regression_smoke(
        requested_by=args.operator,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result.get("summary") or result
        print(
            f"ok={result.get('ok')} case={result.get('case_id')} "
            f"message={result.get('message', '')}"
        )
        if isinstance(summary, dict) and summary is not result:
            print(
                "  automation_status={automation_status} overall_ok={overall_ok} "
                "delivery_ready={delivery_ready}".format(**summary)
            )
            failures = summary.get("failures") or []
            if failures:
                print("  failures:")
                for item in failures:
                    print(f"    - {item}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
