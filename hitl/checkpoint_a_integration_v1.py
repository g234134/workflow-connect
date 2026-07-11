"""Checkpoint A integration v1 (W6-T5).

Connects W5-T1 intake decision results with W5-T2B checkpoint state/resume.
Tool-layer only; does not resume main chain, UI, or durable workflow engine.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from hitl.checkpoints_v1 import (
    CHECKPOINT_A_ID,
    CHECKPOINT_SCHEMA_VERSION,
    build_resume_context,
    write_checkpoint,
)
from routing.intake_decision_rules_v1 import evaluate_intake_decision

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CHECKPOINT_A_EXPIRY_MINUTES = 5


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _expires_at_iso(minutes: int = _CHECKPOINT_A_EXPIRY_MINUTES) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return expires.strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_case_dir(case_dir: str) -> Path:
    path = Path(case_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path.resolve()


def case_ref_from_case_dir(case_dir: str) -> str:
    """Derive outbox case_ref from a repo-relative or absolute case directory."""
    rel = case_dir.replace("\\", "/").strip("/")
    if not Path(case_dir).is_absolute():
        try:
            rel = _normalize_case_dir(case_dir).relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            rel = case_dir.replace("\\", "/").strip("/")
    if rel.startswith("cases/"):
        rel = rel[len("cases/") :]
    return rel


def should_trigger_checkpoint_a(decision_result: Dict[str, Any]) -> bool:
    """Return True when Checkpoint A should be created per W6-T5 rules."""
    decision = str(decision_result.get("decision", ""))
    risk_level = str(decision_result.get("risk_level", ""))

    if decision == "reject":
        return False
    if decision == "needs_review":
        return True
    if risk_level in ("medium", "high"):
        return True
    return False


def _load_intake_summary(case_path: Path) -> Dict[str, Any]:
    intake_path = case_path / "intake.json"
    if not intake_path.is_file():
        return {}
    try:
        with intake_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    scale = data.get("scale") or {}
    return {
        "client_ref": data.get("client_ref"),
        "case_id": data.get("case_id") or case_path.name,
        "input_file": data.get("data_file"),
        "estimated_rows": scale.get("row_count"),
    }


def _load_gate_preview(case_path: Path, decision_result: Dict[str, Any]) -> Dict[str, Any]:
    report_path = case_path / "reports" / "eligibility_result.json"
    if report_path.is_file():
        try:
            with report_path.open(encoding="utf-8") as fh:
                report = json.load(fh)
        except (OSError, json.JSONDecodeError):
            report = {}
        if isinstance(report, dict):
            return {
                "eligibility": report.get("status"),
                "exit_code": 2 if report.get("status") == "review_needed" else 0,
                "reason_code": report.get("reason_code"),
            }

    glue = decision_result.get("glue_plan") or {}
    gate_notes = glue.get("inferred_gate_notes") or []
    eligibility = "review_needed" if gate_notes else "accepted"
    return {
        "eligibility": eligibility,
        "exit_code": 2 if eligibility == "review_needed" else 0,
        "reason_code": gate_notes[0] if gate_notes else None,
    }


def _intake_decision_block(decision_result: Dict[str, Any]) -> Dict[str, Any]:
    route = decision_result.get("suggested_route")
    block: Dict[str, Any] = {
        "decision": decision_result.get("decision"),
        "risk_level": decision_result.get("risk_level"),
        "rationale": list(decision_result.get("rationale") or []),
    }
    if isinstance(route, dict):
        block["suggested_route"] = dict(route)
    return block


def _intake_gate_block(decision_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    gate = decision_result.get("_intake_gate")
    if isinstance(gate, dict) and gate:
        return dict(gate)
    return None


def build_checkpoint_a_payload(
    task_type: str,
    case_dir: str,
    decision_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a Checkpoint A state dict ready for ``write_checkpoint``."""
    if not decision_result.get("ok"):
        raise ValueError("decision_result.ok must be True to build checkpoint payload")

    case_ref = case_ref_from_case_dir(case_dir)
    created_at = _utc_now_iso()
    case_path = _normalize_case_dir(case_dir)

    agent_output: Dict[str, Any] = {
        "task_type": task_type,
        "intake_decision": _intake_decision_block(decision_result),
        "case_summary": _load_intake_summary(case_path),
        "gate_preview": _load_gate_preview(case_path, decision_result),
    }
    intake_gate = _intake_gate_block(decision_result)
    if intake_gate:
        agent_output["intake_gate"] = intake_gate

    run_id = f"{created_at.replace(':', '-').replace('Z', 'Z')}_intake_confirm"

    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_A_ID,
        "case_ref": case_ref,
        "run_id": run_id,
        "status": "awaiting_human",
        "created_at": created_at,
        "expires_at": _expires_at_iso(),
        "task_type": task_type,
        "agent_output": agent_output,
        "human_decision": None,
        "resume_context": None,
    }


def _auto_approve_resume_plan(
    task_type: str,
    case_dir: str,
    decision_result: Dict[str, Any],
) -> Dict[str, Any]:
    route = decision_result.get("suggested_route") or {}
    case_ref = case_ref_from_case_dir(case_dir)
    resume_context = {
        "checkpoint_id": CHECKPOINT_A_ID,
        "case_ref": case_ref,
        "original_decision": {
            "decision": decision_result.get("decision"),
            "risk_level": decision_result.get("risk_level"),
        },
        "human_decision": {
            "action": "approve",
            "operator_id": "auto_approve",
            "by": "auto_approve",
            "at": _utc_now_iso(),
            "comment": "auto_approve=True bypassed awaiting_human",
        },
        "resume_from": "selector",
    }
    if route.get("selector_task_type"):
        resume_context["selector_task_type"] = route["selector_task_type"]
    planned = route.get("planned_tools")
    if planned:
        resume_context["planned_tools"] = list(planned)

    plan = resume_plan_from_checkpoint_a(resume_context)
    plan["task_type"] = task_type
    plan["case_dir"] = decision_result.get("case_dir") or case_dir
    return plan


def maybe_create_checkpoint_a(
    task_type: str,
    case_dir: str,
    decision_result: Dict[str, Any],
    auto_approve: bool = False,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate intake decision and optionally persist Checkpoint A under outbox/."""
    if not decision_result.get("ok"):
        return {
            "ok": False,
            "status": "error",
            "message": decision_result.get("message", "decision evaluation failed"),
            "checkpoint_id": CHECKPOINT_A_ID,
        }

    case_ref = case_ref_from_case_dir(case_dir)
    decision = str(decision_result.get("decision", ""))
    risk_level = str(decision_result.get("risk_level", ""))

    if decision == "reject":
        return {
            "ok": True,
            "status": "rejected_intake",
            "checkpoint_id": CHECKPOINT_A_ID,
            "case_ref": case_ref,
            "decision": decision,
            "risk_level": risk_level,
            "message": "intake rejected; Checkpoint A not created",
        }

    if decision == "auto_accept" and auto_approve:
        resume_plan = _auto_approve_resume_plan(task_type, case_dir, decision_result)
        return {
            "ok": True,
            "status": "approved_auto",
            "checkpoint_id": CHECKPOINT_A_ID,
            "case_ref": case_ref,
            "decision": decision,
            "risk_level": risk_level,
            "resume_plan": resume_plan,
            "message": "auto_accept with auto_approve=True; Checkpoint A skipped",
        }

    if decision == "needs_review" and auto_approve:
        resume_plan = _auto_approve_resume_plan(task_type, case_dir, decision_result)
        return {
            "ok": True,
            "status": "auto_approved",
            "checkpoint_id": CHECKPOINT_A_ID,
            "case_ref": case_ref,
            "decision": decision,
            "risk_level": risk_level,
            "resume_plan": resume_plan,
            "reason": "auto_approve_skip",
            "message": "needs_review with auto_approve=True; Checkpoint A file write skipped, resume_plan generated",
        }

    if not should_trigger_checkpoint_a(decision_result):
        return {
            "ok": True,
            "status": "skipped",
            "checkpoint_id": CHECKPOINT_A_ID,
            "case_ref": case_ref,
            "decision": decision,
            "risk_level": risk_level,
            "message": "low-risk auto_accept; Checkpoint A not required",
        }

    payload = build_checkpoint_a_payload(task_type, case_dir, decision_result)
    write_kwargs: Dict[str, Any] = {}
    if repo_root is not None:
        write_kwargs["repo_root"] = repo_root
    if outbox_root_override is not None:
        write_kwargs["outbox_root_override"] = outbox_root_override

    dest = write_checkpoint(payload, **write_kwargs)
    # FIX (W6-T5/W6-T6-fix-outbox-root-override): Support custom outbox outside repo.
    # Try repo_root first (backward compat), then outbox_root, then absolute.
    _repo_root = repo_root or _REPO_ROOT
    try:
        checkpoint_path = str(dest.relative_to(_repo_root))
    except ValueError:
        # outbox is outside repo; compute relative to outbox_root instead
        from tools.tabular_outbox_writer import outbox_root as get_outbox_root
        outbox_base = Path(outbox_root_override) if outbox_root_override else get_outbox_root(_repo_root)
        try:
            checkpoint_path = str(dest.relative_to(outbox_base))
        except ValueError:
            # Final fallback: absolute path
            checkpoint_path = str(dest.resolve())

    return {
        "ok": True,
        "status": "awaiting_human",
        "checkpoint_id": CHECKPOINT_A_ID,
        "case_ref": case_ref,
        "decision": decision,
        "risk_level": risk_level,
        "checkpoint_path": checkpoint_path,
        "expires_at": payload.get("expires_at"),
        "message": "Checkpoint A created; awaiting human decision",
    }


def resume_plan_from_checkpoint_a(resume_context: Dict[str, Any]) -> Dict[str, Any]:
    """Translate Checkpoint A resume_context into an actionable resume plan dict."""
    if resume_context.get("checkpoint_id") != CHECKPOINT_A_ID:
        return {
            "ok": False,
            "message": f"expected checkpoint_id={CHECKPOINT_A_ID}",
        }

    action = str((resume_context.get("human_decision") or {}).get("action", ""))
    resume_from = resume_context.get("resume_from")

    if action == "approve":
        final_status = "approved"
    elif action == "revise_plan":
        final_status = "revise_needed"
    elif action == "reject":
        final_status = "rejected"
    else:
        return {
            "ok": False,
            "message": f"unsupported human action for Checkpoint A: {action!r}",
        }

    plan: Dict[str, Any] = {
        "ok": True,
        "checkpoint_id": CHECKPOINT_A_ID,
        "case_ref": resume_context.get("case_ref"),
        "human_action": action,
        "resume_from": resume_from,
        "final_status": final_status,
        "original_decision": dict(resume_context.get("original_decision") or {}),
    }

    if resume_from == "selector":
        if resume_context.get("selector_task_type"):
            plan["selector_task_type"] = resume_context["selector_task_type"]
        planned = resume_context.get("planned_tools")
        if planned:
            plan["planned_tools"] = list(planned)
        plan["message"] = "resume at selector with approved planned_tools"
    elif resume_from == "gate":
        plan["message"] = "resume at gate for plan revision"
    elif resume_from is None:
        plan["message"] = "flow terminated; no resume"
    else:
        plan["message"] = f"resume from {resume_from}"

    return plan


def evaluate_and_maybe_checkpoint_a(
    task_type: str,
    case_dir: str,
    auto_approve: bool = False,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience: run W5-T1 decision then apply Checkpoint A integration."""
    decision_result = evaluate_intake_decision(task_type, case_dir)
    result = maybe_create_checkpoint_a(
        task_type,
        case_dir,
        decision_result,
        auto_approve=auto_approve,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    result["decision_result"] = decision_result
    return result


def apply_human_decision_to_checkpoint_a(
    action: str,
    checkpoint: Dict[str, Any],
    *,
    operator_id: str = "operator_cli",
    notes: str = "",
) -> Dict[str, Any]:
    """Build resume_context + resume_plan from a checkpoint dict and human action."""
    resolved_at = _utc_now_iso()
    human_decision = {
        "action": action,
        "operator_id": operator_id,
        "comment": notes,
        "timestamp": resolved_at,
        "by": operator_id,
        "at": resolved_at,
    }
    resume_context = build_resume_context(checkpoint, human_decision)
    resume_plan = resume_plan_from_checkpoint_a(resume_context)
    return {
        "ok": True,
        "resume_context": resume_context,
        "resume_plan": resume_plan,
    }
