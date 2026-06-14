"""Ticket eligibility v1 (WC-T1).

Pure eligibility helper for Multi-Chat ticket acceptance. Consumes parsed
ticket state (TicketRecord) and optional context; does not mutate state files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from dispatch_executor import (
    BLOCKED_STATUSES,
    DONE_STATUSES,
    TicketRecord,
    _is_infra_unblock,
    _is_waiting_reviewer,
    _normalize_done_set,
    _unresolved_dependencies,
    classify_ticket,
    parse_ticket_state_markdown,
    recommend_role,
    scan_ticket_files,
)

EligibilityStatus = Literal["eligible", "ineligible"]
VALID_REQUESTED_ROLES = frozenset({"implementer", "reviewer", "scribe", "orchestrator"})

_WAVE_PHASE_PATTERNS: tuple[tuple[re.Pattern[str], str, str | None], ...] = (
    (re.compile(r"^W-MVP-", re.I), "MVP", "MVP"),
    (re.compile(r"^WB-T", re.I), "B", "P8"),
    (re.compile(r"^WC-C1", re.I), "C", "C1"),
    (re.compile(r"^WC-PRE", re.I), "C", "PRE"),
    (re.compile(r"^WC-", re.I), "C", None),
    (re.compile(r"^WA-T6", re.I), "A", "P6"),
    (re.compile(r"^WA-T", re.I), "A", None),
    (re.compile(r"^W(\d+)-", re.I), "numeric", None),
    (re.compile(r"^B-F", re.I), "foundation", "B-F"),
    (re.compile(r"^C1-P", re.I), "collab", "C1"),
    (re.compile(r"^C2-", re.I), "collab", "C2"),
    (re.compile(r"^DEMO-", re.I), "demo", None),
)


@dataclass
class EligibilityContext:
    """Optional supplemental context for a single eligibility check."""

    requested_role: str | None = None
    wave: str | None = None
    phase: str | None = None
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> EligibilityContext:
        if not raw:
            return cls()
        role = raw.get("requested_role")
        if role is not None:
            role = str(role).strip().lower() or None
        wave = raw.get("wave")
        phase = raw.get("phase")
        notes_raw = raw.get("notes") or []
        notes = [str(n) for n in notes_raw] if isinstance(notes_raw, list) else []
        return cls(
            requested_role=role,
            wave=str(wave).strip() if wave else None,
            phase=str(phase).strip() if phase else None,
            notes=notes,
        )


def infer_wave_phase(ticket_id: str) -> tuple[str | None, str | None]:
    """Infer wave / phase labels from ticket id naming convention only."""
    tid = ticket_id.strip()
    for pattern, wave_label, phase_label in _WAVE_PHASE_PATTERNS:
        match = pattern.match(tid)
        if not match:
            continue
        if wave_label == "numeric" and match.lastindex:
            return f"Wave {match.group(1)}", phase_label
        return wave_label, phase_label
    return None, None


def evaluate_ticket_eligibility(
    ticket: TicketRecord,
    *,
    done_ids: set[str] | frozenset[str],
    context: EligibilityContext | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return structured eligible / ineligible decision with reason list."""
    ctx = context if isinstance(context, EligibilityContext) else EligibilityContext.from_dict(context)
    done_upper = {d.upper() for d in done_ids}

    reasons: list[str] = []
    warnings: list[str] = []

    if ctx.requested_role and ctx.requested_role not in VALID_REQUESTED_ROLES:
        warnings.append(f"unknown_requested_role:{ctx.requested_role}")

    wave, phase = ctx.wave, ctx.phase
    if not wave or not phase:
        inferred_wave, inferred_phase = infer_wave_phase(ticket.ticket_id)
        wave = wave or inferred_wave
        phase = phase or inferred_phase

    bucket = classify_ticket(ticket, done_ids=done_upper)
    role, role_reason = recommend_role(ticket, bucket)
    unresolved = _unresolved_dependencies(ticket, done_upper)

    if ticket.overall_status in DONE_STATUSES:
        if ctx.requested_role == "scribe" and (
            ticket.current_owner == "scribe"
            or "scribe" in (ticket.next_action or "").lower()
            or ticket.status_by_role.get("scribe") in {"pending", "in_progress"}
        ):
            reasons.append("done_ticket_pending_scribe")
            eligible: EligibilityStatus = "eligible"
        else:
            reasons.append("ticket_already_done")
            eligible = "ineligible"

    elif ticket.overall_status in BLOCKED_STATUSES and not _is_infra_unblock(ticket):
        reasons.append("overall_status_blocked")
        eligible = "ineligible"

    elif unresolved:
        for dep in unresolved:
            reasons.append(f"dependency_unresolved:{dep}")
        eligible = "ineligible"

    elif ticket.overall_status == "draft":
        na = (ticket.next_action or "").lower()
        if ctx.requested_role == "implementer":
            if "assign" in na or "implementer" in na or ticket.current_owner == "implementer":
                reasons.append("draft_assigned_to_implementer")
                eligible = "eligible"
            else:
                reasons.append("draft_not_assigned")
                eligible = "ineligible"
        elif ctx.requested_role == "orchestrator":
            reasons.append("draft_needs_orchestrator_framing")
            eligible = "eligible"
        else:
            reasons.append("draft_not_ready_for_role")
            eligible = "ineligible"

    elif ctx.requested_role == "implementer" and _is_waiting_reviewer(ticket):
        reasons.append("waiting_reviewer_gate")
        eligible = "ineligible"

    elif ctx.requested_role == "reviewer":
        if bucket == "in_review" or _is_waiting_reviewer(ticket):
            reasons.append("review_gate_active")
            eligible = "eligible"
        else:
            reasons.append("not_in_review")
            eligible = "ineligible"

    elif ctx.requested_role == "scribe":
        if ticket.overall_status in DONE_STATUSES or (
            ticket.current_owner == "scribe"
            or "scribe" in (ticket.next_action or "").lower()
        ):
            reasons.append("scribe_progress_append_ready")
            eligible = "eligible"
        else:
            reasons.append("scribe_not_ready")
            eligible = "ineligible"

    elif bucket == "blocked":
        if ticket.blockers:
            reasons.extend(ticket.blockers)
        else:
            reasons.append("classified_blocked")
        eligible = "ineligible"

    elif bucket in {"runnable_now", "in_review"}:
        reasons.append(f"bucket_{bucket}")
        if role:
            reasons.append(f"recommended_role:{role}")
        eligible = "eligible"

    elif bucket == "done":
        reasons.append("ticket_already_done")
        eligible = "ineligible"

    else:
        reasons.append(f"bucket_{bucket}")
        eligible = "eligible" if bucket == "draft" else "ineligible"

    if ctx.notes:
        reasons.extend(f"context_note:{n}" for n in ctx.notes)

    return {
        "ok": True,
        "ticket_id": ticket.ticket_id,
        "title": ticket.title,
        "eligible": eligible,
        "reasons": reasons,
        "bucket": bucket,
        "recommended_role": role,
        "recommended_role_reason": role_reason,
        "overall_status": ticket.overall_status,
        "current_owner": ticket.current_owner,
        "next_action": ticket.next_action,
        "dependencies": ticket.dependencies,
        "unresolved_dependencies": unresolved,
        "status_by_role": ticket.status_by_role,
        "wave": wave,
        "phase": phase,
        "requested_role": ctx.requested_role,
        "source_path": ticket.source_path,
        "warnings": warnings,
        "message": f"{eligible} · {len(reasons)} reason(s)",
    }


def resolve_ticket_state_path(ticket_id: str, repo_root: Path) -> Path | None:
    """Resolve ``<ticket_id>_state.md`` under tickets dir (exact id match)."""
    tickets_dir = repo_root / "04_Workflows" / "tickets"
    needle = ticket_id.strip()
    if not needle:
        return None

    exact = tickets_dir / f"{needle}_state.md"
    if exact.is_file():
        return exact

    upper = needle.upper()
    for path in sorted(tickets_dir.glob("*_state.md")):
        stem = path.stem.replace("_state", "")
        if stem.upper() == upper:
            return path
    return None


def load_ticket_record(
    ticket_id: str,
    repo_root: Path,
) -> tuple[TicketRecord | None, list[str]]:
    """Load a single ticket state file; return record and warnings."""
    warnings: list[str] = []
    path = resolve_ticket_state_path(ticket_id, repo_root)
    if path is None:
        return None, [f"ticket_not_found:{ticket_id}"]

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"read_failed:{path.name}:{exc}"]

    record = parse_ticket_state_markdown(text, path, repo_root=repo_root)
    if record.ticket_id.upper() != ticket_id.strip().upper() and record.confidence.get("ticket_id") == "low":
        warnings.append(f"ticket_id_header_mismatch:expected={ticket_id}:parsed={record.ticket_id}")
    return record, warnings


def build_done_ids(repo_root: Path) -> set[str]:
    """Scan all ticket state files and collect ids in done-like statuses."""
    tickets_dir = repo_root / "04_Workflows" / "tickets"
    records, _ = scan_ticket_files(tickets_dir)
    return _normalize_done_set(records)


def check_ticket_eligibility(
    ticket_id: str,
    repo_root: Path,
    *,
    context: EligibilityContext | dict[str, Any] | None = None,
    done_ids: set[str] | None = None,
) -> dict[str, Any]:
    """End-to-end: load ticket, evaluate eligibility, return structured dict."""
    record, load_warnings = load_ticket_record(ticket_id, repo_root)
    if record is None:
        return {
            "ok": False,
            "ticket_id": ticket_id,
            "eligible": "ineligible",
            "reasons": load_warnings,
            "message": load_warnings[0] if load_warnings else "ticket_not_found",
            "warnings": [],
        }

    done = done_ids if done_ids is not None else build_done_ids(repo_root)
    result = evaluate_ticket_eligibility(record, done_ids=done, context=context)
    if load_warnings:
        result["warnings"] = list(result.get("warnings") or []) + load_warnings
    return result
