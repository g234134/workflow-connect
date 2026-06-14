"""Structured comms payload generation for ticket STATE transitions (WC-T2)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "ticket_comms_v0.1"

TRACKED_FIELDS = (
    "overall_status",
    "implementation_status",
    "current_owner",
    "next_action",
    "status_by_role",
)


@dataclass
class TicketStateSnapshot:
    ticket_id: str
    title: str
    overall_status: str
    implementation_status: str | None = None
    current_owner: str | None = None
    next_action: str | None = None
    status_by_role: dict[str, str] = field(default_factory=dict)
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StateDiff:
    changed_fields: list[str] = field(default_factory=list)
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return bool(self.changed_fields)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _field_value(snapshot: TicketStateSnapshot, field_name: str) -> Any:
    if field_name == "status_by_role":
        return dict(snapshot.status_by_role)
    return getattr(snapshot, field_name)


def compute_state_diff(
    before: TicketStateSnapshot,
    after: TicketStateSnapshot,
) -> StateDiff:
    """Compare tracked STATE fields between two snapshots."""
    changed: list[str] = []
    before_vals: dict[str, Any] = {}
    after_vals: dict[str, Any] = {}

    for name in TRACKED_FIELDS:
        old = _field_value(before, name)
        new = _field_value(after, name)
        if old != new:
            changed.append(name)
            before_vals[name] = old
            after_vals[name] = new

    return StateDiff(changed_fields=changed, before=before_vals, after=after_vals)


def _status_phrase(status: str) -> str:
    phrases = {
        "draft": "drafted",
        "in_progress": "in progress",
        "review": "under review",
        "scribe": "awaiting documentation",
        "done": "completed",
        "blocked": "blocked",
    }
    return phrases.get(status, status.replace("_", " "))


def _build_summary(snapshot: TicketStateSnapshot, diff: StateDiff) -> str:
    parts: list[str] = []

    if "overall_status" in diff.changed_fields:
        old = diff.before.get("overall_status", snapshot.overall_status)
        new = diff.after.get("overall_status", snapshot.overall_status)
        parts.append(
            f"status {_status_phrase(str(old))} → {_status_phrase(str(new))}"
        )

    if "current_owner" in diff.changed_fields:
        new_owner = diff.after.get("current_owner")
        if new_owner:
            parts.append(f"owner now {new_owner}")

    if "implementation_status" in diff.changed_fields:
        new_impl = diff.after.get("implementation_status")
        if new_impl:
            parts.append(f"implementation {new_impl}")

    if "next_action" in diff.changed_fields:
        new_action = diff.after.get("next_action")
        if new_action:
            snippet = str(new_action)
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            parts.append(f"next: {snippet}")

    if not parts:
        parts.append("state updated")

    return f"Ticket {snapshot.ticket_id}: " + "; ".join(parts) + "."


def _build_title(snapshot: TicketStateSnapshot, diff: StateDiff) -> str:
    if "overall_status" in diff.changed_fields:
        new_status = str(diff.after.get("overall_status", snapshot.overall_status))
        return f"[{snapshot.ticket_id}] {_status_phrase(new_status).title()}"
    if snapshot.title and snapshot.title != snapshot.ticket_id:
        return f"[{snapshot.ticket_id}] {snapshot.title}"
    return f"[{snapshot.ticket_id}] Update"


def build_comms_payload(
    snapshot: TicketStateSnapshot,
    diff: StateDiff,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build structured JSON payload for a ticket STATE change."""
    ticket_ref = snapshot.source_path or f"04_Workflows/tickets/{snapshot.ticket_id}_state.md"

    return {
        "schema_version": SCHEMA_VERSION,
        "ticket_id": snapshot.ticket_id,
        "title": _build_title(snapshot, diff),
        "summary": _build_summary(snapshot, diff),
        "ticket_ref": ticket_ref,
        "status": {
            "before": {
                "overall_status": diff.before.get(
                    "overall_status", snapshot.overall_status
                ),
                "current_owner": diff.before.get(
                    "current_owner", snapshot.current_owner
                ),
            },
            "after": {
                "overall_status": diff.after.get(
                    "overall_status", snapshot.overall_status
                ),
                "current_owner": diff.after.get(
                    "current_owner", snapshot.current_owner
                ),
            },
        },
        "changed_fields": list(diff.changed_fields),
        "diff": diff.to_dict(),
        "generated_at": generated_at or _utc_now_iso(),
    }


def snapshot_from_ticket_record(record: Any) -> TicketStateSnapshot:
    """Convert dispatch_executor.TicketRecord to TicketStateSnapshot."""
    return TicketStateSnapshot(
        ticket_id=str(getattr(record, "ticket_id", "") or ""),
        title=str(getattr(record, "title", "") or ""),
        overall_status=str(getattr(record, "overall_status", "unknown") or "unknown"),
        implementation_status=getattr(record, "implementation_status", None),
        current_owner=getattr(record, "current_owner", None),
        next_action=getattr(record, "next_action", None),
        status_by_role=dict(getattr(record, "status_by_role", {}) or {}),
        source_path=str(getattr(record, "source_path", "") or ""),
    )
