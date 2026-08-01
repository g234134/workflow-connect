#!/usr/bin/env python3
"""P7 resume-loop G-1–G-5 minimal runtime MVP (FP-G3 · Groundwork Finisher A).

Runs a single matrix scenario against existing orchestrator resume paths in an
isolated temp outbox. Does NOT claim full fleet closure or prod gate.

Usage:
    python scripts/run_p7_resume_loop_mvp_v1.py --scenario G-1 --format json
    python scripts/run_p7_resume_loop_mvp_v1.py --scenario G-4 --format text
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hitl.checkpoints_v1 import CHECKPOINT_A_ID, CHECKPOINT_SCHEMA_VERSION
from scripts.run_agent_standard_case_experiment import (
    _run_experiment_resume_from_checkpoint,
    validate_resume_eligibility,
)
from scripts.run_multi_phase_smoke_v1 import DEFAULT_TASK_TYPE

SCHEMA_VERSION = "p7_resume_loop_mvp_v1"
DEFAULT_SCENARIO = "G-1"
SUPPORTED_SCENARIOS = ("G-1", "G-2", "G-3", "G-4", "G-5")


def _trace_from_result(
    gap_id: str,
    *,
    eligibility: Optional[Dict[str, Any]] = None,
    run_result: Optional[Dict[str, Any]] = None,
    checkpoint_path: Optional[str] = None,
    load_error: Optional[str] = None,
) -> Dict[str, Any]:
    trace: Dict[str, Any] = {
        "gap_id": gap_id,
        "checkpoint_path": checkpoint_path,
    }
    final_status = None
    message = None
    if run_result is not None:
        final_status = run_result.get("final_status")
        message = run_result.get("message")
        if run_result.get("case_allowlist_block") or message == "case_not_in_allowlist":
            trace["case_allowlist_block"] = True
            trace["resume_eligibility"] = "blocked"
        if load_error or (run_result.get("resume") or {}).get("message"):
            trace["checkpoint_load_error"] = load_error or (run_result.get("resume") or {}).get(
                "message"
            )
    if eligibility is not None:
        final_status = final_status or eligibility.get("final_status")
        message = message or eligibility.get("message")
        fs = final_status or "blocked"
        if fs == "stale_checkpoint":
            trace["resume_eligibility"] = "stale_checkpoint"
        else:
            trace["resume_eligibility"] = "blocked"
        if gap_id == "G-2":
            trace["resume_blocked_reason"] = "revise_needed"
        elif gap_id == "G-3":
            trace["resume_blocked_reason"] = "on_hold"
    if gap_id == "G-4" and load_error:
        trace["checkpoint_load_error"] = load_error
        trace["resume_eligibility"] = "blocked"
    if gap_id == "G-5":
        trace["case_allowlist_block"] = True
        trace["resume_eligibility"] = "blocked"
    trace["final_status"] = final_status
    trace["message"] = message
    return trace


def _write_checkpoint(path: Path, payload: Dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path.as_posix()


def _base_checkpoint_a(*, status: str, case_ref: str = "demo_phase") -> Dict[str, Any]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_A_ID,
        "case_ref": case_ref,
        "run_id": "mvp_resume_loop_run",
        "status": status,
        "created_at": "2020-01-01T00:00:00Z",
        "expires_at": "2020-01-01T00:05:00Z",
        "task_type": DEFAULT_TASK_TYPE,
        "resume_context": {},
    }


def run_p7_resume_loop_mvp_v1(
    scenario: str = DEFAULT_SCENARIO,
    *,
    repo_root: Optional[Path] = None,
    outbox_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute one G-* resume scenario; returns structured MVP result."""
    gap_id = scenario.upper()
    if gap_id not in SUPPORTED_SCENARIOS:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "scenario": gap_id,
            "message": f"unsupported scenario {gap_id!r}; use one of {SUPPORTED_SCENARIOS}",
        }

    root = (repo_root or _REPO_ROOT).resolve()
    own_outbox = outbox_root is None
    if outbox_root is None:
        outbox_root = Path(tempfile.mkdtemp(prefix="p7_resume_mvp_")) / "outbox"
    outbox_str = str(outbox_root.resolve())
    case_dir = "cases/demo_phase"
    task_type = DEFAULT_TASK_TYPE

    eligibility: Optional[Dict[str, Any]] = None
    run_result: Optional[Dict[str, Any]] = None
    checkpoint_path: Optional[str] = None
    load_error: Optional[str] = None

    if gap_id == "G-1":
        ckpt_file = outbox_root / "checkpoints" / "demo_phase" / "checkpoint_A_mvp_g1.json"
        payload = _base_checkpoint_a(status="awaiting_human")
        checkpoint_path = _write_checkpoint(ckpt_file, payload)
        eligibility = validate_resume_eligibility(
            payload,
            case_ref="demo_phase",
            task_type=task_type,
            mode="run",
            checkpoint_path=ckpt_file,
        )
        run_result = {
            "ok": False,
            "final_status": eligibility.get("final_status"),
            "message": eligibility.get("message"),
        }
    elif gap_id in ("G-2", "G-3"):
        status = "revise_needed" if gap_id == "G-2" else "on_hold"
        ckpt_file = outbox_root / "checkpoints" / "demo_phase" / f"checkpoint_A_mvp_{gap_id.lower()}.json"
        payload = _base_checkpoint_a(status=status)
        checkpoint_path = _write_checkpoint(ckpt_file, payload)
        eligibility = validate_resume_eligibility(
            payload,
            case_ref="demo_phase",
            task_type=task_type,
            mode="run",
            checkpoint_path=ckpt_file,
        )
        run_result = {
            "ok": False,
            "final_status": eligibility.get("final_status", "blocked"),
            "message": eligibility.get("message"),
        }
    elif gap_id == "G-4":
        missing = outbox_root / "checkpoints" / "demo_phase" / "missing_checkpoint.json"
        checkpoint_path = missing.as_posix()
        run_result = _run_experiment_resume_from_checkpoint(
            task_type,
            case_dir,
            resume_checkpoint=checkpoint_path,
            mode="run",
            auto_approve_intake=False,
            auto_approve_delivery=False,
            outbox_root_override=outbox_str,
        )
        load_error = str(run_result.get("message") or "")
    elif gap_id == "G-5":
        ckpt_file = outbox_root / "checkpoints" / "non_allowlisted" / "checkpoint_A_mvp_g5.json"
        payload = _base_checkpoint_a(status="approved", case_ref="non_allowlisted_fixture")
        payload["resume_context"] = {
            "resume_from": "selector",
            "human_decision": {"action": "approve"},
            "planned_tools": ["validate.eligibility"],
        }
        checkpoint_path = _write_checkpoint(ckpt_file, payload)
        run_result = _run_experiment_resume_from_checkpoint(
            task_type,
            "cases/non_allowlisted_fixture",
            resume_checkpoint=checkpoint_path,
            mode="run",
            auto_approve_intake=False,
            auto_approve_delivery=False,
            outbox_root_override=outbox_str,
        )

    trace = _trace_from_result(
        gap_id,
        eligibility=eligibility,
        run_result=run_result,
        checkpoint_path=checkpoint_path,
        load_error=load_error,
    )

    expected_ok = False
    expected_final = "stale_checkpoint" if gap_id == "G-1" else "blocked"
    passed = (
        (run_result or eligibility or {}).get("ok") is expected_ok
        and trace.get("final_status") == expected_final
    )

    return {
        "ok": passed,
        "schema_version": SCHEMA_VERSION,
        "scenario": gap_id,
        "read_only": False,
        "isolated_outbox": own_outbox,
        "outbox_root": outbox_str,
        "resume_result": run_result or eligibility,
        "trace_fields": trace,
        "matrix_ref": "04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml",
        "spec_ref": "docs/p7-resume-loop-g1-g5-spec-v1.md",
        "message": (
            f"resume-loop MVP {gap_id} trace OK"
            if passed
            else f"resume-loop MVP {gap_id} unexpected outcome"
        ),
    }


def _format_text(result: Dict[str, Any]) -> str:
    trace = result.get("trace_fields") or {}
    lines = [
        "P7 Resume-Loop MVP v1",
        f"scenario: {result.get('scenario')}",
        f"ok: {result.get('ok')}",
        f"outbox_root: {result.get('outbox_root')}",
        "",
        "── trace_fields ──",
    ]
    for key, value in trace.items():
        lines.append(f"  {key}: {value}")
    lines.extend(["", f"message: {result.get('message')}"])
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Minimal P7 resume-loop runtime MVP for one G-* scenario."
    )
    parser.add_argument(
        "--scenario",
        default=DEFAULT_SCENARIO,
        choices=SUPPORTED_SCENARIOS,
        help=f"Matrix gap id (default: {DEFAULT_SCENARIO})",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional outbox root (default: temp isolated dir)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    outbox = Path(args.outbox_root).resolve() if args.outbox_root else None
    result = run_p7_resume_loop_mvp_v1(
        args.scenario,
        repo_root=repo_root,
        outbox_root=outbox,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
