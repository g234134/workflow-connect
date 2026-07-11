"""HITL Checkpoints v1 — file-based state, events, and resume context (W5-T2B).

Writes checkpoint state under outbox/<case_ref>/ and append-only events at
outbox/checkpoint_events.jsonl. Tool-layer only; does not resume main chain.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.tabular_outbox_writer import DEFAULT_OUTBOX_DIRNAME, outbox_root

CHECKPOINT_SCHEMA_VERSION = "hitl_checkpoint_v1"
CHECKPOINT_EVENTS_FILENAME = "checkpoint_events.jsonl"

CHECKPOINT_A_ID = "A-intake-confirmation"
CHECKPOINT_B_ID = "B-delivery-confirmation"

CHECKPOINT_A_ACTIONS = frozenset({"approve", "reject", "revise_plan"})
CHECKPOINT_B_ACTIONS = frozenset({"approve_delivery", "request_changes", "hold"})

_REQUIRED_CHECKPOINT_KEYS = frozenset(
    {
        "schema_version",
        "checkpoint_id",
        "case_ref",
        "status",
        "created_at",
        "agent_output",
    }
)

_PENDING_STATUSES = frozenset({"awaiting_human"})

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return repo_root.resolve() if repo_root is not None else _REPO_ROOT


def _normalize_case_ref(case_ref: str) -> str:
    return case_ref.replace("\\", "/").strip("/")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compact_timestamp(iso_ts: str) -> str:
    try:
        parsed = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    except ValueError:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _resolve_outbox_root(
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    root = outbox_root(repo_root, outbox_root_override)
    if root.name != DEFAULT_OUTBOX_DIRNAME:
        raise ValueError(
            f"checkpoint writes must stay under {DEFAULT_OUTBOX_DIRNAME}/; got {root.name}"
        )
    return root


def _assert_under_outbox(target: Path, root: Path) -> None:
    """Reject writes outside the configured outbox root."""
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path must stay under outbox/: {target}") from exc


def _checkpoint_filename(checkpoint_id: str, created_at: str) -> str:
    safe_id = checkpoint_id.replace("/", "-")
    ts = _compact_timestamp(created_at)
    return f"checkpoint_{safe_id}_{ts}.json"


def build_checkpoint_rel_path(case_ref: str, checkpoint_id: str, created_at: str) -> str:
    safe_case = _normalize_case_ref(case_ref)
    return f"{DEFAULT_OUTBOX_DIRNAME}/{safe_case}/{_checkpoint_filename(checkpoint_id, created_at)}"


def validate_checkpoint(checkpoint: Dict[str, Any]) -> None:
    missing = _REQUIRED_CHECKPOINT_KEYS - set(checkpoint)
    if missing:
        raise ValueError(f"checkpoint missing required keys: {sorted(missing)}")
    if checkpoint.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {CHECKPOINT_SCHEMA_VERSION}")
    cid = str(checkpoint["checkpoint_id"])
    if cid not in (CHECKPOINT_A_ID, CHECKPOINT_B_ID):
        raise ValueError(f"unsupported checkpoint_id: {cid}")


def _iter_checkpoint_files(
    root: Path,
    *,
    case_ref: Optional[str] = None,
) -> List[Path]:
    if not root.is_dir():
        return []

    if case_ref is not None:
        case_dir = root / _normalize_case_ref(case_ref)
        if not case_dir.is_dir():
            return []
        return sorted(case_dir.glob("checkpoint_*.json"))

    paths: List[Path] = []
    for path in sorted(root.rglob("checkpoint_*.json")):
        if path.parent == root:
            continue
        paths.append(path)
    return paths


def _load_checkpoint_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _find_checkpoint_by_id(
    checkpoint_id: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    pending_only: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
    root = _resolve_outbox_root(repo_root, outbox_root_override)
    matches: List[Tuple[str, Dict[str, Any], Path]] = []

    for path in _iter_checkpoint_files(root):
        data = _load_checkpoint_file(path)
        if data is None:
            continue
        if data.get("checkpoint_id") != checkpoint_id:
            continue
        if pending_only and data.get("status") not in _PENDING_STATUSES:
            continue
        created = str(data.get("created_at", ""))
        matches.append((created, data, path))

    if not matches:
        return None, None

    matches.sort(key=lambda item: item[0])
    _, data, path = matches[-1]
    return data, path


def _status_for_action(checkpoint_id: str, action: str) -> str:
    if checkpoint_id == CHECKPOINT_A_ID:
        if action == "approve":
            return "approved"
        if action == "reject":
            return "rejected"
        if action == "revise_plan":
            return "revised"
    if checkpoint_id == CHECKPOINT_B_ID:
        if action == "approve_delivery":
            return "approved"
        if action == "request_changes":
            return "revised"
        if action == "hold":
            return "on_hold"
    raise ValueError(f"unsupported action {action!r} for {checkpoint_id}")


def _resume_from_for_action(checkpoint_id: str, action: str) -> Optional[str]:
    if checkpoint_id == CHECKPOINT_A_ID:
        if action == "approve":
            return "selector"
        if action == "reject":
            return None
        if action == "revise_plan":
            return "gate"
    if checkpoint_id == CHECKPOINT_B_ID:
        if action == "approve_delivery":
            return "delivery"
        if action == "request_changes":
            return "cleaning"
        if action == "hold":
            return None
    raise ValueError(f"unsupported action {action!r} for {checkpoint_id}")


def _original_decision_from_checkpoint(checkpoint: Dict[str, Any]) -> Dict[str, Any]:
    agent_output = checkpoint.get("agent_output") or {}
    if checkpoint.get("checkpoint_id") == CHECKPOINT_A_ID:
        intake = agent_output.get("intake_decision") or {}
        return {
            "decision": intake.get("decision"),
            "risk_level": intake.get("risk_level"),
        }
    if checkpoint.get("checkpoint_id") == CHECKPOINT_B_ID:
        guard = agent_output.get("output_guard") or {}
        return {
            "output_guard_status": guard.get("status"),
            "qa_status": (agent_output.get("cleaning_results") or {}).get("qa_status"),
        }
    return {}


def build_resume_context(
    checkpoint: Dict[str, Any],
    human_decision: Dict[str, Any],
) -> Dict[str, Any]:
    """Build resume_context dict per docs/hitl-checkpoints-v1.md §3.5 / §4.5."""
    checkpoint_id = str(checkpoint["checkpoint_id"])
    case_ref = str(checkpoint["case_ref"])
    action = str(human_decision.get("action", ""))
    resume_from = _resume_from_for_action(checkpoint_id, action)

    ctx: Dict[str, Any] = {
        "checkpoint_id": checkpoint_id,
        "case_ref": case_ref,
        "original_decision": _original_decision_from_checkpoint(checkpoint),
        "human_decision": human_decision,
        "resume_from": resume_from,
    }

    agent_output = checkpoint.get("agent_output") or {}
    if checkpoint_id == CHECKPOINT_A_ID and action == "approve":
        route = agent_output.get("intake_decision", {}).get("suggested_route") or {}
        if route.get("selector_task_type"):
            ctx["selector_task_type"] = route["selector_task_type"]
        planned = route.get("planned_tools")
        if planned:
            ctx["planned_tools"] = list(planned)

    if checkpoint_id == CHECKPOINT_B_ID and action in ("approve_delivery", "request_changes"):
        artifacts = agent_output.get("artifacts")
        if artifacts:
            ctx["artifacts"] = dict(artifacts)

    if action == "request_changes" and human_decision.get("change_request"):
        ctx["change_request"] = human_decision["change_request"]

    return ctx


def suggested_actions(checkpoint_id: str) -> List[str]:
    if checkpoint_id == CHECKPOINT_A_ID:
        return sorted(CHECKPOINT_A_ACTIONS)
    if checkpoint_id == CHECKPOINT_B_ID:
        return sorted(CHECKPOINT_B_ACTIONS)
    return []


def write_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    """Persist checkpoint state JSON under outbox/<case_ref>/."""
    validate_checkpoint(checkpoint)
    root = _resolve_outbox_root(repo_root, outbox_root_override)

    case_ref = _normalize_case_ref(str(checkpoint["case_ref"]))
    checkpoint_id = str(checkpoint["checkpoint_id"])
    created_at = str(checkpoint.get("created_at") or _utc_now_iso())

    payload = dict(checkpoint)
    payload.setdefault("schema_version", CHECKPOINT_SCHEMA_VERSION)
    payload.setdefault("created_at", created_at)
    payload.setdefault("status", "awaiting_human")
    payload.setdefault("human_decision", None)
    payload.setdefault("resume_context", None)

    dest_dir = root / case_ref
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / _checkpoint_filename(checkpoint_id, created_at)
    _assert_under_outbox(dest, root)

    rel_path = build_checkpoint_rel_path(case_ref, checkpoint_id, created_at)
    payload["checkpoint_path"] = rel_path

    with dest.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    append_checkpoint_event(
        {
            "event": "checkpoint_created",
            "checkpoint_id": checkpoint_id,
            "case_ref": case_ref,
            "status": payload["status"],
            "created_at": payload["created_at"],
            "checkpoint_path": rel_path,
        },
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    return dest


def append_checkpoint_event(
    event: Dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    root = _resolve_outbox_root(repo_root, outbox_root_override)
    root.mkdir(parents=True, exist_ok=True)
    events_path = root / CHECKPOINT_EVENTS_FILENAME
    _assert_under_outbox(events_path, root)
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return events_path


def list_pending_checkpoints(
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    case_ref: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return checkpoints with status awaiting_human."""
    root = _resolve_outbox_root(repo_root, outbox_root_override)
    pending: List[Dict[str, Any]] = []

    for path in _iter_checkpoint_files(root, case_ref=case_ref):
        data = _load_checkpoint_file(path)
        if data is None:
            continue
        if data.get("status") not in _PENDING_STATUSES:
            continue
        pending.append(
            {
                "checkpoint_id": data.get("checkpoint_id"),
                "case_ref": data.get("case_ref"),
                "type": data.get("checkpoint_id"),
                "created_at": data.get("created_at"),
                "expires_at": data.get("expires_at"),
                "checkpoint_path": data.get("checkpoint_path") or str(path.relative_to(_repo_root(repo_root))),
                "task_type": (data.get("agent_output") or {}).get("task_type")
                or data.get("task_type"),
            }
        )

    pending.sort(key=lambda item: str(item.get("created_at", "")))
    return pending


def get_checkpoint(
    checkpoint_id: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    pending_only: bool = False,
) -> Optional[Dict[str, Any]]:
    data, _ = _find_checkpoint_by_id(
        checkpoint_id,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
        pending_only=pending_only,
    )
    return data


def record_human_decision(
    checkpoint_id: str,
    decision: str,
    notes: str = "",
    *,
    operator_id: str = "operator_cli",
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply human decision, update checkpoint file, append event, return resume_context."""
    checkpoint, path = _find_checkpoint_by_id(
        checkpoint_id,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
        pending_only=True,
    )
    if checkpoint is None or path is None:
        raise ValueError(f"no pending checkpoint found for id: {checkpoint_id}")

    cid = str(checkpoint["checkpoint_id"])
    allowed = (
        CHECKPOINT_A_ACTIONS if cid == CHECKPOINT_A_ID else CHECKPOINT_B_ACTIONS
    )
    if decision not in allowed:
        raise ValueError(
            f"invalid decision {decision!r} for {cid}; allowed: {sorted(allowed)}"
        )

    resolved_at = _utc_now_iso()
    human_decision = {
        "action": decision,
        "operator_id": operator_id,
        "comment": notes,
        "timestamp": resolved_at,
        "by": operator_id,
        "at": resolved_at,
    }
    resume_context = build_resume_context(checkpoint, human_decision)

    updated = dict(checkpoint)
    updated["human_decision"] = human_decision
    updated["resume_context"] = resume_context
    updated["status"] = _status_for_action(cid, decision)
    updated["resolved_at"] = resolved_at

    root = _resolve_outbox_root(repo_root, outbox_root_override)
    _assert_under_outbox(path, root)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(updated, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    append_checkpoint_event(
        {
            "event": "human_decision_recorded",
            "checkpoint_id": cid,
            "case_ref": updated.get("case_ref"),
            "action": decision,
            "operator_id": operator_id,
            "resolved_at": resolved_at,
            "resume_from": resume_context.get("resume_from"),
            "checkpoint_path": updated.get("checkpoint_path"),
        },
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    return resume_context


def review_summary(checkpoint: Dict[str, Any]) -> Dict[str, Any]:
    """Compact summary for CLI --review."""
    agent_output = checkpoint.get("agent_output") or {}
    summary: Dict[str, Any] = {
        "checkpoint_id": checkpoint.get("checkpoint_id"),
        "case_ref": checkpoint.get("case_ref"),
        "status": checkpoint.get("status"),
        "created_at": checkpoint.get("created_at"),
        "expires_at": checkpoint.get("expires_at"),
        "suggested_actions": suggested_actions(str(checkpoint.get("checkpoint_id", ""))),
    }

    if checkpoint.get("checkpoint_id") == CHECKPOINT_A_ID:
        intake = agent_output.get("intake_decision") or {}
        summary["task_type"] = agent_output.get("task_type") or checkpoint.get("task_type")
        summary["decision"] = intake.get("decision")
        summary["risk_level"] = intake.get("risk_level")
        summary["risk_signals"] = intake.get("rationale") or []
        route = intake.get("suggested_route") or {}
        summary["planned_tools"] = route.get("planned_tools") or []
        gate = agent_output.get("gate_preview") or {}
        summary["output_guard"] = {
            "eligibility": gate.get("eligibility"),
            "exit_code": gate.get("exit_code"),
            "reason_code": gate.get("reason_code"),
        }
    elif checkpoint.get("checkpoint_id") == CHECKPOINT_B_ID:
        summary["task_type"] = agent_output.get("task_type") or checkpoint.get("task_type")
        guard = agent_output.get("output_guard") or {}
        summary["output_guard"] = {
            "status": guard.get("status"),
            "checks": guard.get("checks"),
        }
        summary["cleaning_results"] = agent_output.get("cleaning_results") or {}
        summary["delivery_draft"] = agent_output.get("delivery_draft") or {}

    return summary
