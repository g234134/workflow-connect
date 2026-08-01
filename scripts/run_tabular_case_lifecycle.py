#!/usr/bin/env python3
"""One-command Tabular case lifecycle (R1–R6): validate → start → driver → HITL → delivery.

Usage:
    python scripts/run_tabular_case_lifecycle.py --case-dir cases/demo_phase --start
    python scripts/run_tabular_case_lifecycle.py --case-dir cases/internal/generic-low-risk \\
        --start --auto-resume-internal --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
for path in (_SCRIPTS, _REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tabular_automation_driver_lib import run_tabular_automation  # noqa: E402
from tabular_automation_state_lib import (  # noqa: E402
    PAUSE_REASON_CHECKPOINT_A,
    PAUSE_REASON_CHECKPOINT_B,
    load_state,
    start_automation,
    stop_automation,
)
from tabular_delivery_approval_lib import approve_tabular_delivery  # noqa: E402
from tabular_hitl_resume_lib import (  # noqa: E402
    apply_tabular_checkpoint_decision,
    resume_after_checkpoint,
)
from validate_intake import validate_intake  # noqa: E402
from export_case_delivery_zip import export_case_delivery_zip  # noqa: E402


def _auto_resume_hitl(case_dir: Path, *, requested_by: str, phases: list[dict[str, Any]]) -> dict[str, Any]:
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
            return {"ok": False, "message": f"unexpected pause_reason={pause!r}"}
        decision = apply_tabular_checkpoint_decision(
            case_dir,
            command=cmd,
            operator_id=requested_by,
            notes="lifecycle auto-resume-internal",
        )
        phases.append({"phase": cmd, "result": decision})
        if not decision.get("ok"):
            return decision
        resume = resume_after_checkpoint(case_dir, requested_by=requested_by)
        phases.append({"phase": f"resume-after-{cmd}", "result": resume})
        if not resume.get("ok"):
            return resume
    return {"ok": True, "message": "hitl auto-resume complete"}


def run_tabular_case_lifecycle(
    case_dir: Path,
    *,
    start: bool = False,
    auto_resume_internal: bool = False,
    requested_by: str = "lifecycle_cli",
    force_driver: bool = False,
    export_zip: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    phases: list[dict[str, Any]] = []

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "case_dir": case_dir.relative_to(_REPO_ROOT).as_posix(),
            "planned": [
                "validate_intake",
                "start_automation (if --start)",
                "run_tabular_automation",
                "auto_resume_internal HITL",
                "approve_tabular_delivery",
                "export_case_delivery_zip",
            ],
        }

    intake = validate_intake(case_dir)
    phases.append({"phase": "validate-intake", "result": intake})
    if not intake.get("ok"):
        return {"ok": False, "phases": phases, "message": intake.get("message")}

    if start:
        state = load_state(case_dir)
        if state.get("automation_status") in {"running", "paused"}:
            stop = stop_automation(case_dir, requested_by=requested_by)
            phases.append({"phase": "stop-before-restart", "result": stop})
        ctl = start_automation(case_dir, requested_by=requested_by, restart=True)
        phases.append({"phase": "start", "result": ctl})
        if not ctl.get("ok"):
            return {"ok": False, "phases": phases, "message": ctl.get("message")}

    driver = run_tabular_automation(case_dir, start_from="intake", force=force_driver)
    phases.append({"phase": "driver", "result": driver})

    if auto_resume_internal:
        hitl = _auto_resume_hitl(case_dir, requested_by=requested_by, phases=phases)
        if not hitl.get("ok"):
            return {"ok": False, "phases": phases, "message": hitl.get("message")}

    approve = approve_tabular_delivery(
        case_dir,
        approved_by=requested_by,
        reason="lifecycle delivery approve",
        repo_root=_REPO_ROOT,
    )
    phases.append({"phase": "delivery-approve", "result": approve})

    zip_result: dict[str, Any] = {"ok": True, "skipped": True}
    if export_zip:
        zip_result = export_case_delivery_zip(case_dir, refresh_bundle=False)
        phases.append({"phase": "export-zip", "result": zip_result})

    ok = (
        driver.get("ok") is True
        and approve.get("delivery_ready") is True
        and zip_result.get("ok") is True
    )
    return {
        "ok": ok,
        "case_dir": case_dir.relative_to(_REPO_ROOT).as_posix(),
        "phases": phases,
        "delivery_ready": approve.get("delivery_ready"),
        "zip_path": zip_result.get("zip_path"),
        "message": "lifecycle completed" if ok else "lifecycle incomplete — see phases",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run full Tabular case lifecycle.")
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--start", action="store_true", help="Start automation before driver")
    parser.add_argument("--auto-resume-internal", action="store_true", help="Auto approve CP-A/B")
    parser.add_argument("--force", action="store_true", help="Pass --force to driver")
    parser.add_argument("--no-export-zip", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--requested-by", default="lifecycle_cli")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    case_dir = args.case_dir
    if not case_dir.is_absolute():
        case_dir = _REPO_ROOT / case_dir

    result = run_tabular_case_lifecycle(
        case_dir,
        start=args.start,
        auto_resume_internal=args.auto_resume_internal,
        requested_by=args.requested_by,
        force_driver=args.force,
        export_zip=not args.no_export_zip,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok={result.get('ok')} message={result.get('message')}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
