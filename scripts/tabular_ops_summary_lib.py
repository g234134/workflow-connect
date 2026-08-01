"""Tabular ops summary aggregation (read-only).

Collects automation state, HITL checkpoints, delivery approval, and DLQ
signals into a single operator-facing summary per case.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tabular_automation_driver_lib import STEP_ORDER, resolve_case_dir
from tabular_automation_retry_dlq_lib import dlq_index_path
from tabular_automation_state_lib import load_state, read_intake_case_id
from tabular_delivery_approval_lib import load_approval
from tabular_warning_guard_lib import evaluate_case_guard_policy

SCHEMA_VERSION = "tabular-ops-summary-v1"
FLEET_SCHEMA_VERSION = "tabular-fleet-ops-v1"
RUN_LOG_FILENAME = "automation_run_log.json"

_SKIP_CASE_PREFIXES = ("_",)
_PENDING_CP_STATUSES = frozenset({"pending", "awaiting_human"})


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _rel_path(path: Path, root: Path | None = None) -> str:
    base = root or repo_root()
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _read_intake(case_dir: Path) -> dict[str, Any]:
    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return {}
    try:
        data = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _load_run_log(case_dir: Path) -> dict[str, Any] | None:
    path = case_dir / "reports" / RUN_LOG_FILENAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _completed_steps_from_run_log(run_log: dict[str, Any] | None) -> int | None:
    if not run_log:
        return None
    steps = run_log.get("steps")
    if not isinstance(steps, list) or not steps:
        return None

    def _step_done(step: dict[str, Any]) -> bool:
        if step.get("ok") is True:
            return True
        return str(step.get("step_status") or "").strip().lower() == "completed"

    return sum(1 for step in steps if isinstance(step, dict) and _step_done(step))


def _completed_steps_from_current(current_step: str | None, *, total_steps: int) -> int:
    if not current_step:
        return 0
    if current_step in STEP_ORDER:
        return STEP_ORDER.index(current_step)
    if current_step in {"delivery", "approved_for_delivery"}:
        return total_steps
    return 0


def _delivery_fields(case_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    approval = load_approval(case_dir)
    if approval.get("ok") is False:
        return {
            "delivery_approval_status": "unknown",
            "delivery_ready": False,
            "source": "error",
            "message": approval.get("message"),
        }

    mirrored = state.get("delivery")
    if isinstance(mirrored, dict) and mirrored.get("delivery_approval_status"):
        return {
            "delivery_approval_status": mirrored.get("delivery_approval_status"),
            "delivery_ready": bool(mirrored.get("delivery_ready")),
            "source": "automation_state.delivery",
        }

    return {
        "delivery_approval_status": approval.get("delivery_approval_status", "pending"),
        "delivery_ready": bool(approval.get("delivery_ready")),
        "source": "delivery_approval.json",
    }


def _dlq_summary(case_dir: Path) -> dict[str, Any]:
    index_path = dlq_index_path(case_dir)
    if not index_path.is_file():
        return {
            "has_records": False,
            "total_count": 0,
            "queued_count": 0,
            "handled_count": 0,
            "index_path": None,
        }

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "has_records": False,
            "total_count": 0,
            "queued_count": 0,
            "handled_count": 0,
            "index_path": _rel_path(index_path),
            "message": "dlq index unreadable",
        }

    entries = data.get("entries") if isinstance(data, dict) else []
    if not isinstance(entries, list):
        entries = []

    queued = sum(1 for row in entries if isinstance(row, dict) and row.get("status") == "queued")
    handled = sum(1 for row in entries if isinstance(row, dict) and row.get("status") == "handled")
    total = len(entries)

    return {
        "has_records": total > 0,
        "total_count": total,
        "queued_count": queued,
        "handled_count": handled,
        "index_path": _rel_path(index_path),
    }


def summarize_case(case_dir: Path, *, root: Path | None = None) -> dict[str, Any]:
    """Build one case ops summary dict."""
    base = root or repo_root()
    case_dir = case_dir.resolve()
    intake = _read_intake(case_dir)
    case_id = read_intake_case_id(case_dir) or intake.get("case_id") or case_dir.name
    client_ref = intake.get("client_ref")

    state = load_state(case_dir)
    if state.get("ok") is False:
        return {
            "ok": False,
            "case_id": str(case_id),
            "client_ref": client_ref,
            "case_dir": _rel_path(case_dir, base),
            "message": state.get("message", "failed to load automation state"),
        }

    run_log = _load_run_log(case_dir)
    total_steps = len(STEP_ORDER)
    completed_from_log = _completed_steps_from_run_log(run_log)
    current_step = state.get("current_step")
    completed_steps = (
        completed_from_log
        if completed_from_log is not None
        else _completed_steps_from_current(current_step, total_steps=total_steps)
    )

    delivery = _delivery_fields(case_dir, state)
    dlq = _dlq_summary(case_dir)
    guard_eval = evaluate_case_guard_policy(case_dir)
    policy = guard_eval.get("policy") or {}

    return {
        "ok": True,
        "case_id": str(case_id),
        "client_ref": client_ref,
        "case_dir": _rel_path(case_dir, base),
        "automation_status": state.get("automation_status"),
        "current_step": current_step,
        "steps_completed": completed_steps,
        "steps_total": total_steps,
        "pause_reason": state.get("pause_reason"),
        "checkpoint_a_status": state.get("checkpoint_a_status", "not_required"),
        "checkpoint_b_status": state.get("checkpoint_b_status", "not_required"),
        "delivery_approval_status": delivery.get("delivery_approval_status"),
        "delivery_ready": delivery.get("delivery_ready"),
        "output_guard_status": guard_eval.get("guard_status"),
        "warning_guard_profile": guard_eval.get("profile"),
        "internal_use_allowed": bool(policy.get("internal_use_allowed")),
        "partial_ready": bool(policy.get("partial_ready")),
        "dlq_status": state.get("dlq_status", "none"),
        "dlq": dlq,
        "last_transition_ts": state.get("last_transition_ts"),
        "last_error": state.get("last_error"),
    }


def _should_skip_case_dir(case_dir: Path, cases_root: Path) -> bool:
    try:
        rel = case_dir.relative_to(cases_root)
    except ValueError:
        return True
    if not rel.parts:
        return True
    return rel.parts[0].startswith(_SKIP_CASE_PREFIXES)


def discover_case_dirs(
    *,
    case_id: str | None = None,
    client_ref: str | None = None,
    list_all: bool = False,
    root: Path | None = None,
) -> tuple[list[Path], str | None]:
    """Resolve case directories for summary query modes."""
    base = root or repo_root()
    cases_root = base / "cases"

    if case_id:
        resolved = resolve_case_dir(case_id=case_id)
        if resolved is None:
            return [], f"case not found for case_id={case_id!r}"
        return [resolved], None

    if not list_all and not client_ref:
        return [], "specify --case-id, --client-ref, or --all"

    matches: list[Path] = []
    client_token = client_ref.strip().lower() if client_ref else None

    for intake_path in sorted(cases_root.rglob("intake.json")):
        parent = intake_path.parent
        if _should_skip_case_dir(parent, cases_root):
            continue
        if list_all:
            matches.append(parent.resolve())
            continue
        intake = _read_intake(parent)
        ref = str(intake.get("client_ref", "")).strip().lower()
        if ref and ref == client_token:
            matches.append(parent.resolve())

    if client_ref and not matches:
        return [], f"no cases found for client_ref={client_ref!r}"

    return matches, None


def _is_stuck_at_hitl(row: dict[str, Any]) -> bool:
    if row.get("ok") is False:
        return False
    if row.get("automation_status") == "paused":
        return True
    pause = str(row.get("pause_reason") or "")
    if "checkpoint" in pause.lower():
        return True
    for key in ("checkpoint_a_status", "checkpoint_b_status"):
        status = str(row.get(key) or "")
        if status in {"pending", "awaiting_human"}:
            return True
    return False


def _stuck_case_entry(row: dict[str, Any]) -> dict[str, Any]:
    reason = "paused"
    if row.get("pause_reason"):
        reason = str(row["pause_reason"])
    elif row.get("checkpoint_b_status") in {"pending", "awaiting_human"}:
        reason = "checkpoint_b_pending"
    elif row.get("checkpoint_a_status") in {"pending", "awaiting_human"}:
        reason = "checkpoint_a_pending"
    elif row.get("automation_status") == "failed":
        reason = "automation_failed"
    return {
        "case_id": row.get("case_id"),
        "client_ref": row.get("client_ref"),
        "case_dir": row.get("case_dir"),
        "automation_status": row.get("automation_status"),
        "current_step": row.get("current_step"),
        "pause_reason": row.get("pause_reason"),
        "checkpoint_a_status": row.get("checkpoint_a_status"),
        "checkpoint_b_status": row.get("checkpoint_b_status"),
        "delivery_ready": row.get("delivery_ready"),
        "stuck_reason": reason,
    }


def _is_pending_checkpoint_status(status: str | None) -> bool:
    return str(status or "").strip().lower() in _PENDING_CP_STATUSES


def _pending_checkpoint_entries(row: dict[str, Any]) -> list[dict[str, Any]]:
    if row.get("ok") is False:
        return []
    entries: list[dict[str, Any]] = []
    for cp_type, key in (
        ("checkpoint_a", "checkpoint_a_status"),
        ("checkpoint_b", "checkpoint_b_status"),
    ):
        status = str(row.get(key) or "")
        if _is_pending_checkpoint_status(status):
            entries.append(
                {
                    "case_id": row.get("case_id"),
                    "cp_type": cp_type,
                    "status": status,
                    "pause_reason": row.get("pause_reason"),
                }
            )
    return entries


def _not_delivery_ready_entry(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("ok") is False or row.get("delivery_ready"):
        return None
    return {
        "case_id": row.get("case_id"),
        "delivery_ready": row.get("delivery_ready"),
        "delivery_approval_status": row.get("delivery_approval_status"),
        "output_guard_status": row.get("output_guard_status"),
    }


def _dlq_case_entry(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("ok") is False:
        return None
    dlq = row.get("dlq") or {}
    queued = int(dlq.get("queued_count") or 0)
    total = int(dlq.get("total_count") or 0)
    if queued <= 0 and total <= 0:
        return None
    return {
        "case_id": row.get("case_id"),
        "dlq_entry_count": total,
        "dlq_queued_count": queued,
    }


def build_fleet_ops_rollup(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Roll up fleet-level blockers for one-screen operator observability."""
    ok_cases = [row for row in cases if row.get("ok") is not False]
    delivery_ready_count = sum(1 for row in ok_cases if row.get("delivery_ready"))
    stuck_at_hitl = [row for row in ok_cases if _is_stuck_at_hitl(row)]
    dlq_queued_total = sum(
        int((row.get("dlq") or {}).get("queued_count") or 0) for row in ok_cases
    )
    stuck_cases: list[dict[str, Any]] = []
    for row in ok_cases:
        if _is_stuck_at_hitl(row):
            stuck_cases.append(_stuck_case_entry(row))
            continue
        if row.get("automation_status") in {"failed", "stopped"}:
            stuck_cases.append(_stuck_case_entry(row))

    pending_checkpoints: list[dict[str, Any]] = []
    pending_cp_a_count = 0
    pending_cp_b_count = 0
    for row in ok_cases:
        for entry in _pending_checkpoint_entries(row):
            pending_checkpoints.append(entry)
            if entry["cp_type"] == "checkpoint_a":
                pending_cp_a_count += 1
            else:
                pending_cp_b_count += 1

    not_delivery_ready_cases = [
        entry
        for row in ok_cases
        if (entry := _not_delivery_ready_entry(row)) is not None
    ]
    dlq_cases = [
        entry for row in ok_cases if (entry := _dlq_case_entry(row)) is not None
    ]

    return {
        "delivery_ready_count": delivery_ready_count,
        "stuck_at_hitl_count": len(stuck_at_hitl),
        "dlq_queued_total": dlq_queued_total,
        "stuck_cases": stuck_cases,
        "pending_cp_a_count": pending_cp_a_count,
        "pending_cp_b_count": pending_cp_b_count,
        "pending_checkpoints": pending_checkpoints,
        "not_delivery_ready_count": len(not_delivery_ready_cases),
        "not_delivery_ready_cases": not_delivery_ready_cases,
        "dlq_cases": dlq_cases,
    }


def compute_fleet_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Roll up fleet-level counters from per-case summaries (read-only)."""
    rollup = build_fleet_ops_rollup(cases)
    return {
        "delivery_ready_count": rollup["delivery_ready_count"],
        "stuck_at_hitl_count": rollup["stuck_at_hitl_count"],
        "dlq_queued_total": rollup["dlq_queued_total"],
        "stuck_cases": rollup["stuck_cases"],
    }


def build_ops_summary(
    *,
    case_id: str | None = None,
    client_ref: str | None = None,
    list_all: bool = False,
    fleet: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    """Aggregate ops summaries for selected cases."""
    base = root or repo_root()
    schema_version = FLEET_SCHEMA_VERSION if fleet else SCHEMA_VERSION
    case_dirs, err = discover_case_dirs(
        case_id=case_id,
        client_ref=client_ref,
        list_all=list_all,
        root=base,
    )
    if err:
        return {
            "ok": False,
            "schema_version": schema_version,
            "query": {
                "case_id": case_id,
                "client_ref": client_ref,
                "all": list_all,
                "fleet": fleet,
            },
            "count": 0,
            "cases": [],
            "message": err,
        }

    summaries = [summarize_case(case_dir, root=base) for case_dir in case_dirs]
    ok = all(item.get("ok") is not False for item in summaries)
    fleet_summary = (
        build_fleet_ops_rollup(summaries) if fleet else compute_fleet_summary(summaries)
    )

    return {
        "ok": ok,
        "schema_version": schema_version,
        "query": {
            "case_id": case_id,
            "client_ref": client_ref,
            "all": list_all,
            "fleet": fleet,
        },
        "count": len(summaries),
        "case_count": len(summaries),
        "cases": summaries,
        "summary": fleet_summary,
        "message": f"summarized {len(summaries)} case(s)",
    }


def format_ops_table(result: dict[str, Any]) -> str:
    """Human-readable table for operator review."""
    lines = [
        "Tabular Ops Summary (read-only)",
        f"query: {result.get('query')}",
        f"count: {result.get('count', 0)}",
        "",
    ]

    if not result.get("ok"):
        lines.append(f"error: {result.get('message')}")
        return "\n".join(lines)

    cases = result.get("cases") or []
    if not cases:
        lines.append("(no cases matched)")
        lines.append("")
        lines.append(f"message: {result.get('message')}")
        return "\n".join(lines)

    header = (
        f"{'case_id':<16} {'client_ref':<16} {'auto':<10} {'step':<14} "
        f"{'done':<5} {'cp_a':<12} {'cp_b':<12} {'guard':<8} "
        f"{'deliv':<10} {'ready':<5} {'dlq':<4}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for row in cases:
        if row.get("ok") is False:
            lines.append(
                f"{str(row.get('case_id') or ''):<16} "
                f"{'—':<16} {'ERROR':<10} {'—':<14} {'—':<5} {'—':<12} {'—':<12} "
                f"{'—':<8} {'—':<10} {'—':<5} {'—':<4}"
            )
            lines.append(f"  ↳ {row.get('message')}")
            continue

        dlq = row.get("dlq") or {}
        dlq_flag = "yes" if dlq.get("has_records") else "no"
        done = f"{row.get('steps_completed', 0)}/{row.get('steps_total', 0)}"
        ready = "yes" if row.get("delivery_ready") else "no"
        guard = str(row.get("output_guard_status") or "—")

        lines.append(
            f"{str(row.get('case_id') or ''):<16} "
            f"{str(row.get('client_ref') or '—'):<16} "
            f"{str(row.get('automation_status') or '—'):<10} "
            f"{str(row.get('current_step') or '—'):<14} "
            f"{done:<5} "
            f"{str(row.get('checkpoint_a_status') or '—'):<12} "
            f"{str(row.get('checkpoint_b_status') or '—'):<12} "
            f"{guard:<8} "
            f"{str(row.get('delivery_approval_status') or '—'):<10} "
            f"{ready:<5} "
            f"{dlq_flag:<4}"
        )

        if row.get("warning_guard_profile"):
            lines.append(
                f"  ↳ profile={row.get('warning_guard_profile')} "
                f"internal_use={'yes' if row.get('internal_use_allowed') else 'no'} "
                f"partial_ready={'yes' if row.get('partial_ready') else 'no'}"
            )

        if dlq.get("queued_count"):
            lines.append(
                f"  ↳ dlq queued={dlq.get('queued_count')} total={dlq.get('total_count')}"
            )
        if row.get("pause_reason"):
            lines.append(f"  ↳ pause: {row.get('pause_reason')}")
        if row.get("last_error"):
            lines.append(f"  ↳ last_error: {row.get('last_error')}")

    lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def format_fleet_blockers(result: dict[str, Any]) -> str:
    """One-screen fleet blocker summary for operator review."""
    summary = result.get("summary") or {}
    lines = [
        "Tabular Fleet Ops Blockers (read-only)",
        f"schema: {result.get('schema_version')}",
        f"case_count: {result.get('case_count', 0)}",
        "",
        "Summary counters:",
        f"  pending_cp_a_count: {summary.get('pending_cp_a_count', 0)}",
        f"  pending_cp_b_count: {summary.get('pending_cp_b_count', 0)}",
        f"  dlq_queued_total: {summary.get('dlq_queued_total', 0)}",
        f"  not_delivery_ready_count: {summary.get('not_delivery_ready_count', 0)}",
        f"  stuck_at_hitl_count: {summary.get('stuck_at_hitl_count', 0)}",
        f"  delivery_ready_count: {summary.get('delivery_ready_count', 0)}",
        "",
    ]

    pending = summary.get("pending_checkpoints") or []
    lines.append(f"Pending checkpoints ({len(pending)}):")
    if pending:
        for row in pending:
            lines.append(
                f"  - {row.get('case_id')} {row.get('cp_type')} "
                f"status={row.get('status')} pause={row.get('pause_reason') or '—'}"
            )
    else:
        lines.append("  (none)")

    dlq_cases = summary.get("dlq_cases") or []
    lines.append("")
    lines.append(f"DLQ cases ({len(dlq_cases)}):")
    if dlq_cases:
        for row in dlq_cases:
            lines.append(
                f"  - {row.get('case_id')} entries={row.get('dlq_entry_count')} "
                f"queued={row.get('dlq_queued_count')}"
            )
    else:
        lines.append("  (none)")

    not_ready = summary.get("not_delivery_ready_cases") or []
    lines.append("")
    lines.append(f"Not delivery_ready ({len(not_ready)}):")
    if not_ready:
        for row in not_ready:
            lines.append(
                f"  - {row.get('case_id')} approval={row.get('delivery_approval_status')} "
                f"guard={row.get('output_guard_status')}"
            )
    else:
        lines.append("  (none)")

    stuck = summary.get("stuck_cases") or []
    lines.append("")
    lines.append(f"Stuck cases ({len(stuck)}):")
    if stuck:
        for row in stuck:
            lines.append(
                f"  - {row.get('case_id')} reason={row.get('stuck_reason')} "
                f"status={row.get('automation_status')}"
            )
    else:
        lines.append("  (none)")

    return "\n".join(lines)
