"""Render batch JSON + state_patch_suggestion only (BATCH-MVP-04).

Hard constraint: never writes other ``*_state.md`` files. Callers may persist
suggestion JSON under tests/ or output/ only.
"""

from __future__ import annotations

from typing import Any, Mapping

from .collector import BatchResult


def _as_batch_dict(batch_result: BatchResult | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(batch_result, BatchResult):
        return batch_result.to_dict()
    if isinstance(batch_result, Mapping):
        return dict(batch_result)
    raise TypeError("batch_result must be BatchResult or mapping")


def render_batch_result_json(batch_result: BatchResult | Mapping[str, Any]) -> dict:
    """Return a JSON-serializable batch_result document for tool consumption."""
    payload = _as_batch_dict(batch_result)
    return {
        "schema_version": "batch_result_v1",
        "batch_id": payload.get("batch_id"),
        "ok": bool(payload.get("ok")),
        "message": payload.get("message") or "",
        "summary": dict(payload.get("summary") or {}),
        "subtask_results": list(payload.get("subtask_results") or []),
    }


def render_state_patch_suggestion(
    batch_result: BatchResult | Mapping[str, Any],
    *,
    parent_ticket_id: str | None = None,
) -> dict:
    """Suggest parent-ticket STATE updates without writing any ``*_state.md``.

    Returns a suggestion dict only. Callers must not auto-apply to live tickets.
    """
    payload = _as_batch_dict(batch_result)
    summary = dict(payload.get("summary") or {})
    ok = bool(payload.get("ok"))
    parent = (parent_ticket_id or "").strip() or None
    return {
        "schema_version": "batch_state_patch_suggestion_v1",
        "suggestion_only": True,
        "writes_ticket_state": False,
        "parent_ticket_id": parent,
        "batch_id": payload.get("batch_id"),
        "proposed_overall_status": "accepted" if ok else "needs_changes",
        "proposed_ac_note": (
            "mock batch pipeline completed successfully"
            if ok
            else "mock batch pipeline reported failures; review subtask_results"
        ),
        "summary": summary,
        "subtask_ids": [
            str(row.get("subtask_id") or "")
            for row in (payload.get("subtask_results") or [])
            if isinstance(row, Mapping)
        ],
        "message": (
            "state_patch_suggestion only — do not auto-write *_state.md; "
            "operator/Orchestrator applies manually if desired"
        ),
    }
