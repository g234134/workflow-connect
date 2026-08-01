#!/usr/bin/env python3
"""Operator backlog CLI v1 + T2b batch-approve / resume-latest (P8-T2 / P8-T2b).

v1: read-only aggregation over outbox workflow events, checkpoint state, and intake
gate records.

T2b additions (mutations limited to checkpoint approve + resume path resolution):
    --batch-approve --task-type <type>   # same task_type only
    --resume-latest-approved             # fail-close when multiple approved

Usage:
    python scripts/list_operator_backlog_v1.py --status pending --format json
    python scripts/list_operator_backlog_v1.py --status blocked --format table
    python scripts/list_operator_backlog_v1.py --case-ref demo_phase --format json
    python scripts/list_operator_backlog_v1.py --batch-approve --task-type tabular.cleaning.mvp --format json
    python scripts/list_operator_backlog_v1.py --resume-latest-approved --task-type tabular.cleaning.mvp --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.workflow_event_consumer_v1 import load_workflow_events
from hitl.checkpoints_v1 import (
    CHECKPOINT_A_ID,
    append_checkpoint_event,
    build_resume_context,
    list_pending_checkpoints,
)

SCHEMA_VERSION = "operator_backlog_v1"
SCHEMA_VERSION_T2B = "operator_backlog_t2b_v1"

_TERMINAL_RUN_EVENTS = frozenset({"run.completed", "run.blocked", "run.failed"})
_RESOLVED_CP_A_STATUSES = frozenset(
    {"approved", "rejected", "revised", "auto_approved", "on_hold"}
)
_OUTBOX_SKIP_DIRS = frozenset(
    {
        "feedback",
        "notifications",
        "reports",
        "agent_ci",
        "agent_lines",
        "tabular",
    }
)
_OUTBOX_SKIP_FILES = frozenset(
    {
        "notification_events.jsonl",
        "checkpoint_events.jsonl",
        "intake_gate_events.jsonl",
    }
)


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def _outbox_root(
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    if outbox_root_override:
        return Path(outbox_root_override).resolve()
    return _repo_root(repo_root) / "outbox"


def _normalize_case_ref(case_ref: str) -> str:
    return case_ref.replace("\\", "/").strip("/")


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _read_jsonl_case_refs(path: Path) -> Set[str]:
    refs: Set[str] = set()
    if not path.is_file():
        return refs
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("case_ref"):
                refs.add(_normalize_case_ref(str(obj["case_ref"])))
    except OSError:
        return refs
    return refs


def discover_case_refs(
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> List[str]:
    """Discover case_ref slugs from outbox layout and append-only event logs."""
    outbox = _outbox_root(repo_root, outbox_root_override)
    refs: Set[str] = set()

    if outbox.is_dir():
        for child in sorted(outbox.iterdir()):
            if child.is_file() and child.name in _OUTBOX_SKIP_FILES:
                refs.update(_read_jsonl_case_refs(child))
            elif child.is_dir() and child.name not in _OUTBOX_SKIP_DIRS:
                refs.add(_normalize_case_ref(child.name))

        for path in outbox.rglob("intake_gate_decision_*.json"):
            if path.parent == outbox:
                continue
            try:
                rel = path.parent.relative_to(outbox).as_posix()
            except ValueError:
                continue
            if rel and "/" not in rel:
                refs.add(rel)

    return sorted(refs)


def _latest_checkpoint_a(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    outbox = _outbox_root(repo_root, outbox_root_override)
    safe_case = _normalize_case_ref(case_ref)
    case_dir = outbox / safe_case
    if not case_dir.is_dir():
        return None

    matches: List[tuple[str, Dict[str, Any]]] = []
    for path in sorted(case_dir.glob("checkpoint_*.json")):
        data = _load_json_file(path)
        if not data or data.get("checkpoint_id") != CHECKPOINT_A_ID:
            continue
        created = str(data.get("created_at", ""))
        matches.append((created, data))

    if not matches:
        return None
    matches.sort(key=lambda item: item[0])
    return matches[-1][1]


def _latest_intake_gate_record(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    outbox = _outbox_root(repo_root, outbox_root_override)
    safe_case = _normalize_case_ref(case_ref)
    case_dir = outbox / safe_case
    if not case_dir.is_dir():
        return None

    matches: List[tuple[str, Dict[str, Any]]] = []
    for path in sorted(case_dir.glob("intake_gate_decision_*.json")):
        data = _load_json_file(path)
        if not data:
            continue
        created = str(data.get("created_at", ""))
        matches.append((created, data))

    if not matches:
        return None
    matches.sort(key=lambda item: item[0])
    return matches[-1][1]


def _latest_terminal_run_event(
    timeline: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    terminal: List[tuple[str, Dict[str, Any]]] = []
    for row in timeline:
        event_type = str(row.get("event_type", ""))
        if event_type in _TERMINAL_RUN_EVENTS:
            terminal.append((str(row.get("emitted_at", "")), row))
    if not terminal:
        return None
    terminal.sort(key=lambda item: item[0])
    return terminal[-1][1]


def _checkpoint_a_status_label(checkpoint: Optional[Dict[str, Any]]) -> str:
    if not checkpoint:
        return "none"
    return str(checkpoint.get("status") or "none")


def _case_has_signals(
    *,
    checkpoint_a_status: str,
    intake_decision: Optional[str],
    timeline: List[Dict[str, Any]],
    gate_record: Optional[Dict[str, Any]],
) -> bool:
    if checkpoint_a_status != "none":
        return True
    if intake_decision:
        return True
    if gate_record:
        return True
    return bool(timeline)


def classify_operator_status(
    *,
    checkpoint_a_status: str,
    intake_decision: Optional[str],
    last_terminal_event_type: Optional[str],
    has_timeline: bool = False,
) -> str:
    """Map case signals to operator backlog status (pending / blocked / completed)."""
    cp_status = checkpoint_a_status or "none"
    decision = (intake_decision or "").lower()

    if cp_status == "awaiting_human":
        return "pending"

    if decision == "review_needed" and cp_status not in _RESOLVED_CP_A_STATUSES:
        return "pending"

    if last_terminal_event_type in ("run.blocked", "run.failed"):
        return "blocked"

    if cp_status == "rejected":
        return "blocked"

    if last_terminal_event_type == "run.completed" and cp_status != "awaiting_human":
        return "completed"

    if cp_status in _RESOLVED_CP_A_STATUSES and last_terminal_event_type != "run.completed":
        return "pending"

    if decision == "reject":
        return "blocked"

    if has_timeline and last_terminal_event_type is None:
        return "pending"

    return "inactive"


def build_backlog_entry(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Build one operator backlog row for a case."""
    safe_case = _normalize_case_ref(case_ref)
    checkpoint = _latest_checkpoint_a(
        safe_case,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    gate_record = _latest_intake_gate_record(
        safe_case,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )

    events_result = load_workflow_events(
        safe_case,
        repo_root=_repo_root(repo_root),
        outbox_root_override=outbox_root_override,
    )
    timeline = events_result.get("timeline") or []
    last_row = timeline[-1] if timeline else None
    last_terminal = _latest_terminal_run_event(timeline)

    checkpoint_a_status = _checkpoint_a_status_label(checkpoint)
    intake_decision = None
    task_type = None

    if gate_record:
        intake_decision = str(gate_record.get("decision") or "")
        task_type = gate_record.get("task_type")

    if checkpoint:
        task_type = task_type or checkpoint.get("task_type")
        agent_output = checkpoint.get("agent_output") or {}
        if not intake_decision:
            intake_block = agent_output.get("intake_decision") or {}
            intake_decision = intake_block.get("decision")
            gate_embed = agent_output.get("intake_gate") or {}
            if gate_embed.get("decision"):
                intake_decision = gate_embed.get("decision")
        task_type = task_type or agent_output.get("task_type")

    last_terminal_type = (
        str(last_terminal.get("event_type")) if last_terminal else None
    )
    has_timeline = bool(timeline)
    if not _case_has_signals(
        checkpoint_a_status=checkpoint_a_status,
        intake_decision=str(intake_decision) if intake_decision else None,
        timeline=timeline,
        gate_record=gate_record,
    ):
        return {
            "case_ref": safe_case,
            "task_type": task_type,
            "status": "inactive",
            "last_event_type": None,
            "last_updated_at": None,
            "intake_decision": intake_decision,
            "checkpoint_a_status": checkpoint_a_status,
            "skipped": True,
        }

    status = classify_operator_status(
        checkpoint_a_status=checkpoint_a_status,
        intake_decision=str(intake_decision) if intake_decision else None,
        last_terminal_event_type=last_terminal_type,
        has_timeline=has_timeline,
    )

    return {
        "case_ref": safe_case,
        "task_type": task_type,
        "status": status,
        "last_event_type": last_row.get("event_type") if last_row else None,
        "last_updated_at": last_row.get("emitted_at") if last_row else None,
        "intake_decision": intake_decision,
        "checkpoint_a_status": checkpoint_a_status,
    }


def list_operator_backlog(
    *,
    case_ref: Optional[str] = None,
    status: Optional[str] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """List operator backlog rows with optional case_ref and status filters."""
    root = _repo_root(repo_root)
    if case_ref:
        case_refs = [_normalize_case_ref(case_ref)]
    else:
        case_refs = discover_case_refs(
            repo_root=root,
            outbox_root_override=outbox_root_override,
        )

    rows: List[Dict[str, Any]] = []
    for ref in case_refs:
        entry = build_backlog_entry(
            ref,
            repo_root=root,
            outbox_root_override=outbox_root_override,
        )
        if entry.get("skipped"):
            continue
        if status and entry.get("status") != status:
            continue
        entry.pop("skipped", None)
        rows.append(entry)

    rows.sort(key=lambda row: (str(row.get("last_updated_at") or ""), row.get("case_ref", "")))

    status_filter = status or "all"
    return {
        "ok": True,
        "read_only": True,
        "schema_version": SCHEMA_VERSION,
        "status_filter": status_filter,
        "count": len(rows),
        "items": rows,
        "message": f"found {len(rows)} backlog row(s) for filter={status_filter}",
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _checkpoint_task_type(checkpoint: Dict[str, Any]) -> Optional[str]:
    task_type = checkpoint.get("task_type")
    if task_type:
        return str(task_type)
    agent_output = checkpoint.get("agent_output") or {}
    if agent_output.get("task_type"):
        return str(agent_output["task_type"])
    return None


def _iter_case_checkpoint_a_files(
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    case_ref: Optional[str] = None,
) -> List[tuple[Path, Dict[str, Any]]]:
    outbox = _outbox_root(repo_root, outbox_root_override)
    if not outbox.is_dir():
        return []

    paths: List[Path] = []
    if case_ref:
        case_dir = outbox / _normalize_case_ref(case_ref)
        if case_dir.is_dir():
            paths.extend(sorted(case_dir.glob("checkpoint_*.json")))
    else:
        for path in sorted(outbox.rglob("checkpoint_*.json")):
            if path.parent == outbox:
                continue
            paths.append(path)

    rows: List[tuple[Path, Dict[str, Any]]] = []
    for path in paths:
        data = _load_json_file(path)
        if not data or data.get("checkpoint_id") != CHECKPOINT_A_ID:
            continue
        rows.append((path, data))
    return rows


def _apply_approve_to_checkpoint_file(
    path: Path,
    checkpoint: Dict[str, Any],
    *,
    operator_id: str,
    notes: str,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Case-scoped approve (avoids global checkpoint_id ambiguity)."""
    if checkpoint.get("status") != "awaiting_human":
        return {
            "ok": False,
            "case_ref": checkpoint.get("case_ref"),
            "message": f"checkpoint not awaiting_human (status={checkpoint.get('status')})",
        }

    resolved_at = _utc_now_iso()
    human_decision = {
        "action": "approve",
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
    updated["status"] = "approved"
    updated["resolved_at"] = resolved_at

    path.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_checkpoint_event(
        {
            "event": "human_decision_recorded",
            "checkpoint_id": CHECKPOINT_A_ID,
            "case_ref": updated.get("case_ref"),
            "action": "approve",
            "operator_id": operator_id,
            "resolved_at": resolved_at,
            "resume_from": resume_context.get("resume_from"),
            "checkpoint_path": updated.get("checkpoint_path"),
            "source": "operator_backlog_t2b_batch_approve",
        },
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    return {
        "ok": True,
        "case_ref": updated.get("case_ref"),
        "task_type": _checkpoint_task_type(updated),
        "status": "approved",
        "checkpoint_path": updated.get("checkpoint_path") or str(path.as_posix()),
        "resume_context": resume_context,
        "message": "approved",
    }


def batch_approve_pending(
    *,
    task_type: str,
    dry_run: bool = False,
    operator_id: str = "operator_cli",
    notes: str = "batch-approve",
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Approve all awaiting_human CP-A rows that match ``task_type`` (same-type only)."""
    required_type = (task_type or "").strip()
    if not required_type:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION_T2B,
            "action": "batch_approve",
            "message": "task_type is required for --batch-approve",
            "approved": [],
            "skipped": [],
            "count_approved": 0,
        }

    pending = list_pending_checkpoints(
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    matched: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for row in pending:
        if row.get("checkpoint_id") != CHECKPOINT_A_ID:
            skipped.append(
                {
                    "case_ref": row.get("case_ref"),
                    "reason": "not_checkpoint_a",
                    "checkpoint_id": row.get("checkpoint_id"),
                }
            )
            continue
        row_type = str(row.get("task_type") or "").strip()
        if row_type != required_type:
            skipped.append(
                {
                    "case_ref": row.get("case_ref"),
                    "reason": "task_type_mismatch",
                    "task_type": row_type or None,
                }
            )
            continue
        matched.append(row)

    if dry_run:
        return {
            "ok": True,
            "schema_version": SCHEMA_VERSION_T2B,
            "action": "batch_approve",
            "dry_run": True,
            "task_type": required_type,
            "would_approve": [
                {
                    "case_ref": row.get("case_ref"),
                    "checkpoint_path": row.get("checkpoint_path"),
                    "task_type": row.get("task_type"),
                }
                for row in matched
            ],
            "skipped": skipped,
            "count_approved": 0,
            "count_would_approve": len(matched),
            "message": f"dry-run: would approve {len(matched)} checkpoint(s) for task_type={required_type}",
        }

    approved: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for row in matched:
        case_ref = str(row.get("case_ref") or "")
        files = _iter_case_checkpoint_a_files(
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
            case_ref=case_ref,
        )
        target: Optional[tuple[Path, Dict[str, Any]]] = None
        for path, data in files:
            if data.get("status") == "awaiting_human":
                target = (path, data)
        if target is None:
            errors.append({"case_ref": case_ref, "message": "pending file not found"})
            continue
        path, data = target
        result = _apply_approve_to_checkpoint_file(
            path,
            data,
            operator_id=operator_id,
            notes=notes,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
        )
        if result.get("ok"):
            approved.append(result)
        else:
            errors.append(result)

    ok = len(errors) == 0
    return {
        "ok": ok,
        "schema_version": SCHEMA_VERSION_T2B,
        "action": "batch_approve",
        "dry_run": False,
        "task_type": required_type,
        "approved": approved,
        "skipped": skipped,
        "errors": errors,
        "count_approved": len(approved),
        "message": (
            f"approved {len(approved)} checkpoint(s) for task_type={required_type}"
            if ok
            else f"batch-approve completed with {len(errors)} error(s)"
        ),
    }


def list_approved_checkpoint_a(
    *,
    task_type: Optional[str] = None,
    case_ref: Optional[str] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return approved Checkpoint-A rows (latest per case), optional filters."""
    files = _iter_case_checkpoint_a_files(
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
        case_ref=case_ref,
    )
    # Keep latest approved per case_ref
    latest: Dict[str, Dict[str, Any]] = {}
    for path, data in files:
        if data.get("status") != "approved":
            continue
        row_type = _checkpoint_task_type(data)
        if task_type and str(row_type or "") != task_type:
            continue
        ref = _normalize_case_ref(str(data.get("case_ref") or path.parent.name))
        created = str(data.get("created_at") or data.get("resolved_at") or "")
        candidate = {
            "case_ref": ref,
            "task_type": row_type,
            "status": "approved",
            "created_at": data.get("created_at"),
            "resolved_at": data.get("resolved_at"),
            "checkpoint_path": data.get("checkpoint_path") or path.as_posix(),
            "resume_context": data.get("resume_context"),
            "filesystem_path": path.as_posix(),
            "_sort": created,
        }
        prev = latest.get(ref)
        if prev is None or str(candidate["_sort"]) >= str(prev.get("_sort") or ""):
            latest[ref] = candidate

    rows = list(latest.values())
    for row in rows:
        row.pop("_sort", None)
    rows.sort(key=lambda item: (str(item.get("resolved_at") or item.get("created_at") or ""), item["case_ref"]))
    return rows


def resume_latest_approved(
    *,
    task_type: Optional[str] = None,
    case_ref: Optional[str] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve the latest approved CP-A path; fail-close when multiple without case_ref."""
    rows = list_approved_checkpoint_a(
        task_type=task_type,
        case_ref=case_ref,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    if not rows:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION_T2B,
            "action": "resume_latest_approved",
            "message": "no approved checkpoint-A found for filters",
            "options": [],
            "selected": None,
        }

    if len(rows) > 1 and not case_ref:
        options = [
            {
                "case_ref": row["case_ref"],
                "task_type": row.get("task_type"),
                "checkpoint_path": row.get("checkpoint_path"),
                "resolved_at": row.get("resolved_at"),
            }
            for row in rows
        ]
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION_T2B,
            "action": "resume_latest_approved",
            "fail_close": True,
            "message": (
                "multiple approved checkpoints found; "
                "re-run with --case-ref <slug> to disambiguate"
            ),
            "options": options,
            "selected": None,
            "count_options": len(options),
        }

    selected = rows[-1]
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION_T2B,
        "action": "resume_latest_approved",
        "message": f"selected approved checkpoint for case_ref={selected['case_ref']}",
        "selected": {
            "case_ref": selected["case_ref"],
            "task_type": selected.get("task_type"),
            "checkpoint_path": selected.get("checkpoint_path"),
            "filesystem_path": selected.get("filesystem_path"),
            "resume_context": selected.get("resume_context"),
            "resolved_at": selected.get("resolved_at"),
        },
        "options": [],
        "resume_hint": (
            "python scripts/run_agent_standard_case_experiment.py "
            f"--resume-checkpoint {selected.get('checkpoint_path')}"
        ),
        # T2b resolves path only; does not auto-run the full experiment orchestrator.
        "executed_resume": False,
    }


def _format_table(result: dict) -> str:
    action = result.get("action")
    if action == "batch_approve":
        lines = [
            "Operator Backlog T2b · batch-approve",
            f"task_type: {result.get('task_type')}",
            f"dry_run: {result.get('dry_run')}",
            f"count_approved: {result.get('count_approved', result.get('count_would_approve', 0))}",
            f"message: {result.get('message')}",
        ]
        return "\n".join(lines)
    if action == "resume_latest_approved":
        lines = [
            "Operator Backlog T2b · resume-latest-approved",
            f"ok: {result.get('ok')}",
            f"message: {result.get('message')}",
        ]
        selected = result.get("selected") or {}
        if selected:
            lines.append(f"case_ref: {selected.get('case_ref')}")
            lines.append(f"checkpoint_path: {selected.get('checkpoint_path')}")
        options = result.get("options") or []
        if options:
            lines.append("options:")
            for opt in options:
                lines.append(
                    f"  - case_ref={opt.get('case_ref')} path={opt.get('checkpoint_path')}"
                )
        return "\n".join(lines)

    lines = [
        "Operator Backlog v1 (P8-T2 · read-only)",
        f"status_filter: {result.get('status_filter')}",
        f"count: {result.get('count', 0)}",
        "",
    ]
    items = result.get("items") or []
    if not items:
        lines.append("(no cases match filter)")
        return "\n".join(lines)

    header = (
        f"{'case_ref':<24} {'status':<10} {'task_type':<28} "
        f"{'cp_a':<16} {'intake':<14} {'last_event':<28} {'updated_at'}"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for row in items:
        lines.append(
            f"{str(row.get('case_ref') or ''):<24} "
            f"{str(row.get('status') or ''):<10} "
            f"{str(row.get('task_type') or ''):<28} "
            f"{str(row.get('checkpoint_a_status') or ''):<16} "
            f"{str(row.get('intake_decision') or ''):<14} "
            f"{str(row.get('last_event_type') or ''):<28} "
            f"{str(row.get('last_updated_at') or '')}"
        )
    lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Operator backlog CLI (P8-T2 read-only + P8-T2b batch-approve / resume-latest)."
        )
    )
    parser.add_argument(
        "--case-ref",
        default=None,
        help="Optional single case slug (e.g. demo_phase)",
    )
    parser.add_argument(
        "--status",
        choices=("pending", "blocked", "completed"),
        default=None,
        help="Filter by operator backlog status",
    )
    parser.add_argument(
        "--format",
        choices=("json", "table"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument("--outbox-root", default=None, help="Optional outbox root override")
    parser.add_argument(
        "--batch-approve",
        action="store_true",
        help="P8-T2b: approve all awaiting_human CP-A rows for --task-type",
    )
    parser.add_argument(
        "--resume-latest-approved",
        action="store_true",
        help="P8-T2b: resolve latest approved CP-A path (fail-close if multiple)",
    )
    parser.add_argument(
        "--task-type",
        default=None,
        help="Required for --batch-approve; optional filter for --resume-latest-approved",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --batch-approve: preview only, no writes",
    )
    parser.add_argument(
        "--operator-id",
        default="operator_cli",
        help="Operator id recorded on batch-approve decisions",
    )
    parser.add_argument(
        "--notes",
        default="batch-approve",
        help="Notes recorded on batch-approve decisions",
    )
    args = parser.parse_args(argv)

    if args.batch_approve and args.resume_latest_approved:
        err = {
            "ok": False,
            "message": "use only one of --batch-approve or --resume-latest-approved",
        }
        print(json.dumps(err, indent=2, ensure_ascii=False))
        return 1

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT

    if args.batch_approve:
        result = batch_approve_pending(
            task_type=str(args.task_type or ""),
            dry_run=bool(args.dry_run),
            operator_id=args.operator_id,
            notes=args.notes,
            repo_root=repo_root,
            outbox_root_override=args.outbox_root,
        )
    elif args.resume_latest_approved:
        result = resume_latest_approved(
            task_type=args.task_type,
            case_ref=args.case_ref,
            repo_root=repo_root,
            outbox_root_override=args.outbox_root,
        )
    else:
        result = list_operator_backlog(
            case_ref=args.case_ref,
            status=args.status,
            repo_root=repo_root,
            outbox_root_override=args.outbox_root,
        )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_table(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
