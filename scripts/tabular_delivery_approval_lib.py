"""Tabular delivery approval model and persistence (v1).

Structured delivery readiness / signoff / index updates after CP-B.
Separate from W8-T3 experiment-line ``delivery/delivery_approval_cli_v1.py``.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tabular_automation_state_lib import load_state  # noqa: E402
from tabular_internal_notify_lib import maybe_notify_completed_delivery_ready  # noqa: E402
from tabular_warning_guard_lib import (  # noqa: E402
    compute_delivery_ready_from_policy,
    evaluate_case_guard_policy,
    evaluate_guard_policy,
    load_output_guard_status,
    resolve_warning_guard_profile,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "tabular-delivery-approval-v1"
APPROVAL_FILENAME = "delivery_approval.json"
DEFAULT_BUNDLE_PATH = "reports/report.json"

VALID_APPROVAL_STATUSES = frozenset({"pending", "approved", "rejected"})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    return _REPO_ROOT


def approval_path(case_dir: Path) -> Path:
    return case_dir / APPROVAL_FILENAME


def default_approval(*, case_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "delivery_approval_status": "pending",
        "delivery_approved_by": None,
        "delivery_approved_at": None,
        "delivery_rejected_by": None,
        "delivery_rejected_at": None,
        "rejection_reason": None,
        "delivery_bundle_path": None,
        "delivery_ready": False,
        "signoff_recorded": False,
        "readiness_gaps": [],
        "last_updated_at": None,
        "last_updated_by": None,
    }


def load_approval(case_dir: Path) -> dict[str, Any]:
    path = approval_path(case_dir)
    if not path.is_file():
        case_id = _read_intake_case_id(case_dir) or case_dir.name
        return default_approval(case_id=case_id)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": f"failed to read delivery approval: {exc}",
            "path": str(path),
        }

    if not isinstance(data, dict):
        return {
            "ok": False,
            "message": "delivery_approval.json must be a JSON object",
            "path": str(path),
        }
    return data


def save_approval(case_dir: Path, approval: dict[str, Any]) -> Path:
    path = approval_path(case_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(approval, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _read_intake_case_id(case_dir: Path) -> str | None:
    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return None
    try:
        data = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    case_id = data.get("case_id")
    return str(case_id) if case_id else None


def _rel_case_path(case_dir: Path, repo_root: Path | None = None) -> str:
    root = repo_root or _REPO_ROOT
    try:
        return case_dir.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return case_dir.name


def _load_report(case_dir: Path) -> dict[str, Any] | None:
    report_path = case_dir / "reports" / "report.json"
    if not report_path.is_file():
        return None
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _load_automation_run_log(case_dir: Path) -> dict[str, Any] | None:
    log_path = case_dir / "reports" / "automation_run_log.json"
    if not log_path.is_file():
        return None
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _step_from_run_log(run_log: dict[str, Any] | None, step_name: str) -> dict[str, Any] | None:
    if not run_log:
        return None
    steps = run_log.get("steps")
    if not isinstance(steps, list):
        return None
    for step in reversed(steps):
        if isinstance(step, dict) and step.get("step_name") == step_name:
            return step
    return None


def _check_cp_b_approved(case_dir: Path) -> tuple[bool, str]:
    """Return (approved, evidence_source)."""
    state = load_state(case_dir)
    if state.get("ok") is not False and state.get("checkpoint_b_status") == "approved":
        return True, "automation_state.checkpoint_b_status.approved"

    step = _step_from_run_log(_load_automation_run_log(case_dir), "checkpoint_b")
    if step:
        status = str(step.get("step_status") or "")
        if status == "completed":
            return True, "automation_run_log.checkpoint_b.completed"
        if status == "awaiting_hitl":
            return False, "automation_run_log.checkpoint_b.awaiting_hitl"

    try:
        from hitl.checkpoints_v1 import get_checkpoint  # noqa: WPS433
        from hitl.checkpoint_b_integration_v1 import CHECKPOINT_B_ID  # noqa: WPS433

        checkpoint = get_checkpoint(CHECKPOINT_B_ID, pending_only=False, repo_root=_REPO_ROOT)
        if checkpoint:
            case_ref = _read_intake_case_id(case_dir) or case_dir.name
            cp_ref = str(checkpoint.get("case_ref") or "")
            if not cp_ref or cp_ref == case_ref or cp_ref in _rel_case_path(case_dir):
                hd = checkpoint.get("human_decision") or {}
                action = str(hd.get("action") or "")
                if action == "approve_delivery":
                    return True, "outbox.checkpoint_b.approve_delivery"
                if checkpoint.get("status") == "awaiting_human":
                    return False, "outbox.checkpoint_b.awaiting_human"
    except ImportError:
        pass

    approval = load_approval(case_dir)
    if isinstance(approval, dict) and approval.get("delivery_approval_status") == "approved":
        return True, "delivery_approval.json.approved"

    return False, "cp_b_not_approved"


def _check_e2e_pass(case_dir: Path) -> tuple[bool, str]:
    step = _step_from_run_log(_load_automation_run_log(case_dir), "e2e")
    if step:
        if step.get("step_status") == "completed":
            return True, "automation_run_log.e2e.completed"
        return False, f"automation_run_log.e2e.{step.get('step_status')}"

    report = _load_report(case_dir)
    signoff = case_dir / "delivery_signoff.md"
    cleaned = list((case_dir / "cleaned").glob("*_cleaned.csv")) if (case_dir / "cleaned").is_dir() else []
    if report and signoff.is_file() and cleaned:
        return True, "artifacts.implicit_e2e"
    return False, "e2e_not_pass"


def _check_output_guard_ok(case_dir: Path) -> tuple[bool, str]:
    status, guard = load_output_guard_status(case_dir)
    if guard is None:
        if status == "unknown":
            report = _load_report(case_dir)
            if not report:
                return False, "report.json.missing"
            return False, "output_guard.missing"
        return False, f"output_guard.{status}"
    profile = resolve_warning_guard_profile(case_dir)
    policy = evaluate_guard_policy(profile, status)
    if policy.get("delivery_ready_allowed") and status == "ok":
        return True, "output_guard.ok"
    return False, f"output_guard.{status}"


def resolve_bundle_path(case_dir: Path) -> str:
    report_path = case_dir / "reports" / "report.json"
    if report_path.is_file():
        return DEFAULT_BUNDLE_PATH
    return DEFAULT_BUNDLE_PATH


def evaluate_delivery_readiness(case_dir: Path) -> dict[str, Any]:
    """Evaluate CP-B / e2e / output_guard gates without mutating approval status."""
    cp_b_ok, cp_b_src = _check_cp_b_approved(case_dir)
    e2e_ok, e2e_src = _check_e2e_pass(case_dir)
    guard_ok, guard_src = _check_output_guard_ok(case_dir)

    guard_eval = evaluate_case_guard_policy(case_dir)
    policy = guard_eval.get("policy") or {}

    gaps: list[str] = []
    if not cp_b_ok:
        gaps.append(f"cp_b:{cp_b_src}")
    if not e2e_ok:
        gaps.append(f"e2e:{e2e_src}")
    if not guard_ok:
        gaps.append(f"output_guard:{guard_src}")
        if policy.get("partial_ready"):
            gaps.append("warning_guard:partial_ready_internal_only")

    delivery_ready = compute_delivery_ready_from_policy(
        cp_b_approved=cp_b_ok,
        e2e_pass=e2e_ok,
        policy=policy,
    )

    return {
        "ok": True,
        "case_dir": _rel_case_path(case_dir),
        "cp_b_approved": cp_b_ok,
        "cp_b_evidence": cp_b_src,
        "e2e_pass": e2e_ok,
        "e2e_evidence": e2e_src,
        "output_guard_ok": guard_ok,
        "output_guard_evidence": guard_src,
        "output_guard_status": guard_eval.get("guard_status"),
        "warning_guard_profile": guard_eval.get("profile"),
        "warning_guard_policy": policy,
        "internal_use_allowed": bool(policy.get("internal_use_allowed")),
        "partial_ready": bool(policy.get("partial_ready")),
        "delivery_ready": delivery_ready,
        "readiness_gaps": gaps,
        "delivery_bundle_path": resolve_bundle_path(case_dir),
    }


def _patch_markdown_table_field(content: str, field: str, value: str) -> str:
    pattern = rf"(^\|\s*{re.escape(field)}\s*\|\s*)([^|]*)(\|\s*$)"
    replacement = rf"\1{value} \3"
    updated, count = re.subn(pattern, replacement, content, count=1, flags=re.MULTILINE | re.IGNORECASE)
    if count:
        return updated

    signoff_anchor = "## Signoff"
    if signoff_anchor in content:
        insert = f"| {field} | {value} |\n"
        return content.replace(
            signoff_anchor + "\n",
            signoff_anchor + "\n\n| Field | Value |\n|-------|-------|\n" + insert,
            1,
        )
    return content + f"\n| {field} | {value} |\n"


def patch_delivery_signoff(case_dir: Path, approval: dict[str, Any]) -> dict[str, Any]:
    signoff_path = case_dir / "delivery_signoff.md"
    if not signoff_path.is_file():
        return {"ok": False, "message": "delivery_signoff.md missing", "path": str(signoff_path)}

    status = approval.get("delivery_approval_status")
    content = signoff_path.read_text(encoding="utf-8")

    if status == "approved":
        by = approval.get("delivery_approved_by") or "operator"
        at = approval.get("delivery_approved_at") or utc_now_iso()
        content = _patch_markdown_table_field(content, "lead_approval", f"`approved by {by}`")
        content = _patch_markdown_table_field(content, "delivered_at", f"`{at}`")
        content = _patch_markdown_table_field(content, "reviewer", f"`{by}`")
        content = _patch_markdown_table_field(content, "signer (Lead)", f"`{by}`")
        content = _patch_markdown_table_field(content, "signed_at", f"`{at}`")
        bundle_at = at
        content = _patch_markdown_table_field(content, "bundle_built_at", f"`{bundle_at}`")
    elif status == "rejected":
        by = approval.get("delivery_rejected_by") or "operator"
        reason = approval.get("rejection_reason") or "unspecified"
        content = _patch_markdown_table_field(content, "lead_approval", f"`rejected by {by}`")
        content = _patch_markdown_table_field(
            content,
            "delivered_at",
            f"`rejected — {reason[:80]}`",
        )

    signoff_path.write_text(content, encoding="utf-8")
    return {"ok": True, "path": _rel_case_path(signoff_path), "delivery_approval_status": status}


def patch_cases_index(
    case_dir: Path,
    approval: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    index_path = root / "cases" / "index.json"
    if not index_path.is_file():
        return {"ok": False, "message": "cases/index.json missing", "updated": False}

    try:
        index_data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": f"index unreadable: {exc}", "updated": False}

    case_key = _rel_case_path(case_dir, root)
    cases = index_data.get("cases")
    if not isinstance(cases, list):
        return {"ok": False, "message": "index missing cases array", "updated": False}

    patch_fields = {
        "delivery_approval_status": approval.get("delivery_approval_status"),
        "delivery_approved_by": approval.get("delivery_approved_by"),
        "delivery_approved_at": approval.get("delivery_approved_at"),
        "delivery_bundle_path": approval.get("delivery_bundle_path"),
        "delivery_ready": approval.get("delivery_ready"),
        "signoff_recorded": approval.get("signoff_recorded"),
    }
    if approval.get("delivery_approval_status") == "rejected":
        patch_fields["delivery_rejected_by"] = approval.get("delivery_rejected_by")
        patch_fields["delivery_rejected_at"] = approval.get("delivery_rejected_at")
        patch_fields["rejection_reason"] = approval.get("rejection_reason")

    updated = False
    for entry in cases:
        if not isinstance(entry, dict):
            continue
        entry_dir = str(entry.get("case_dir") or "").replace("\\", "/")
        if entry_dir == case_key:
            entry.update(patch_fields)
            updated = True
            break

    if updated:
        index_data["updated_at"] = utc_now_iso()
        index_path.write_text(json.dumps(index_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "updated": updated,
        "index_path": "cases/index.json",
        "case_dir": case_key,
    }


def sync_automation_state_delivery(case_dir: Path, approval: dict[str, Any]) -> dict[str, Any]:
    """Mirror delivery fields onto automation_state.json for driver visibility."""
    state_path = case_dir / "automation_state.json"
    if not state_path.is_file():
        return {"ok": True, "updated": False, "message": "no automation_state.json"}

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": f"automation state unreadable: {exc}"}

    if not isinstance(state, dict):
        return {"ok": False, "message": "automation_state.json invalid"}

    state["delivery"] = {
        "delivery_approval_status": approval.get("delivery_approval_status"),
        "delivery_approved_by": approval.get("delivery_approved_by"),
        "delivery_approved_at": approval.get("delivery_approved_at"),
        "delivery_bundle_path": approval.get("delivery_bundle_path"),
        "delivery_ready": approval.get("delivery_ready"),
        "signoff_recorded": approval.get("signoff_recorded"),
        "readiness_gaps": approval.get("readiness_gaps") or [],
    }
    if approval.get("current_step") == "delivery":
        state["current_step"] = "delivery"

    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "updated": True, "path": _rel_case_path(state_path)}


def maybe_update_delivery_readiness(
    case_dir: Path,
    *,
    updated_by: str = "tabular_automation_driver",
) -> dict[str, Any]:
    """Driver hook: set pending readiness gaps; never auto-flip rejected → approved."""
    approval = load_approval(case_dir)
    if approval.get("ok") is False:
        return approval

    previous_delivery_ready = bool(approval.get("delivery_ready"))

    if approval.get("delivery_approval_status") == "rejected":
        approval["delivery_ready"] = False
        approval["readiness_gaps"] = ["status:rejected_blocks_auto_ready"]
        approval["last_updated_at"] = utc_now_iso()
        approval["last_updated_by"] = updated_by
        save_approval(case_dir, approval)
        sync_automation_state_delivery(case_dir, approval)
        return {
            "ok": True,
            "message": "rejected status preserved; delivery_ready stays false",
            "delivery_approval_status": "rejected",
            "delivery_ready": False,
            "auto_updated": False,
        }

    readiness = evaluate_delivery_readiness(case_dir)
    approval["readiness_gaps"] = readiness.get("readiness_gaps") or []
    approval["delivery_bundle_path"] = readiness.get("delivery_bundle_path")
    approval["last_updated_at"] = utc_now_iso()
    approval["last_updated_by"] = updated_by

    if approval.get("delivery_approval_status") == "approved":
        approval["delivery_ready"] = bool(readiness.get("delivery_ready"))
    else:
        approval["delivery_approval_status"] = "pending"
        approval["delivery_ready"] = False

    save_approval(case_dir, approval)
    sync_automation_state_delivery(case_dir, approval)

    state = load_state(case_dir)
    if state.get("ok") is not False:
        maybe_notify_completed_delivery_ready(
            case_dir,
            previous_delivery_ready=previous_delivery_ready,
            delivery_ready=bool(approval.get("delivery_ready")),
            automation_status=str(state.get("automation_status", "")),
            case_id=str(approval.get("case_id") or ""),
            source="maybe_update_delivery_readiness",
        )

    return {
        "ok": True,
        "message": "delivery readiness evaluated",
        "delivery_approval_status": approval.get("delivery_approval_status"),
        "delivery_ready": approval.get("delivery_ready"),
        "readiness_gaps": approval.get("readiness_gaps"),
        "auto_updated": True,
    }


def approve_tabular_delivery(
    case_dir: Path,
    *,
    approved_by: str,
    reason: str = "",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Human approve: record audit fields and sync index/signoff when gates pass."""
    if not case_dir.is_dir():
        return {"ok": False, "message": f"case directory not found: {case_dir}"}

    case_id = _read_intake_case_id(case_dir) or case_dir.name
    approval = load_approval(case_dir)
    if approval.get("ok") is False:
        return approval

    previous_delivery_ready = bool(approval.get("delivery_ready"))

    readiness = evaluate_delivery_readiness(case_dir)
    at = utc_now_iso()

    approval.update(
        {
            "case_id": case_id,
            "delivery_approval_status": "approved",
            "delivery_approved_by": approved_by,
            "delivery_approved_at": at,
            "delivery_rejected_by": None,
            "delivery_rejected_at": None,
            "rejection_reason": None,
            "delivery_bundle_path": readiness.get("delivery_bundle_path"),
            "delivery_ready": bool(readiness.get("delivery_ready")),
            "signoff_recorded": bool(readiness.get("delivery_ready")),
            "readiness_gaps": readiness.get("readiness_gaps") or [],
            "approval_reason": reason or None,
            "last_updated_at": at,
            "last_updated_by": approved_by,
        }
    )

    if not approval["delivery_ready"]:
        approval["signoff_recorded"] = False

    path = save_approval(case_dir, approval)
    signoff_result = patch_delivery_signoff(case_dir, approval)
    index_result = patch_cases_index(case_dir, approval, repo_root=repo_root)
    state_result = sync_automation_state_delivery(case_dir, approval)

    cp_b_sync = None
    from tabular_checkpoint_sync_lib import sync_checkpoint_b_state_and_readiness  # noqa: WPS433

    cp_b_sync = sync_checkpoint_b_state_and_readiness(
        case_dir,
        checkpoint_b_status="approved",
        step_status="completed",
        current_step="delivery",
        updated_by=approved_by,
    )

    state = load_state(case_dir)
    if state.get("ok") is not False:
        maybe_notify_completed_delivery_ready(
            case_dir,
            previous_delivery_ready=previous_delivery_ready,
            delivery_ready=bool(approval.get("delivery_ready")),
            automation_status=str(state.get("automation_status", "")),
            case_id=case_id,
            source="approve_tabular_delivery",
            extra={"approved_by": approved_by},
        )

    ok = approval["delivery_ready"]
    message = (
        "delivery approved and ready"
        if ok
        else "delivery approved recorded; delivery_ready=false — gates not satisfied"
    )

    return {
        "ok": ok,
        "message": message,
        "case_id": case_id,
        "case_dir": _rel_case_path(case_dir),
        "delivery_approval_path": _rel_case_path(path),
        "delivery_approval_status": approval["delivery_approval_status"],
        "delivery_ready": approval["delivery_ready"],
        "signoff_recorded": approval["signoff_recorded"],
        "readiness": readiness,
        "readiness_gaps": approval["readiness_gaps"],
        "signoff": signoff_result,
        "index": index_result,
        "automation_state": state_result,
        "checkpoint_b_sync": cp_b_sync,
    }


def reject_tabular_delivery(
    case_dir: Path,
    *,
    rejected_by: str,
    reason: str = "",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Human reject: fail-closed; never sets delivery_ready."""
    if not case_dir.is_dir():
        return {"ok": False, "message": f"case directory not found: {case_dir}"}

    case_id = _read_intake_case_id(case_dir) or case_dir.name
    approval = load_approval(case_dir)
    if approval.get("ok") is False:
        return approval

    at = utc_now_iso()
    approval.update(
        {
            "case_id": case_id,
            "delivery_approval_status": "rejected",
            "delivery_approved_by": None,
            "delivery_approved_at": None,
            "delivery_rejected_by": rejected_by,
            "delivery_rejected_at": at,
            "rejection_reason": reason or "unspecified",
            "delivery_ready": False,
            "signoff_recorded": False,
            "readiness_gaps": ["status:rejected"],
            "last_updated_at": at,
            "last_updated_by": rejected_by,
        }
    )

    path = save_approval(case_dir, approval)
    signoff_result = patch_delivery_signoff(case_dir, approval)
    index_result = patch_cases_index(case_dir, approval, repo_root=repo_root)
    state_result = sync_automation_state_delivery(case_dir, approval)

    return {
        "ok": True,
        "message": "delivery rejected; delivery_ready=false",
        "case_id": case_id,
        "case_dir": _rel_case_path(case_dir),
        "delivery_approval_path": _rel_case_path(path),
        "delivery_approval_status": "rejected",
        "delivery_ready": False,
        "signoff_recorded": False,
        "rejection_reason": approval["rejection_reason"],
        "signoff": signoff_result,
        "index": index_result,
        "automation_state": state_result,
    }
