"""Implementer prompt builder for batch orchestrator (BATCH-MVP-03).

Consumes loader/scheduler subtask dicts + parent FRAME. Does not call workers
or write ticket state / Progress.
"""

from __future__ import annotations

from typing import Any, Mapping


_ROLE_RULES_REF = ".cursor/rules/multi_chat_roles.mdc"
_AGENTS_REF = "AGENTS.md"
_DEFAULT_PARENT_STATE_TMPL = "04_Workflows/tickets/{parent_ticket_id}_state.md"


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    text = str(value).strip()
    return [text] if text else []


def _parent_state_path(subtask: Mapping[str, Any], parent_frame: Mapping[str, Any]) -> str:
    explicit = parent_frame.get("parent_state_path") or parent_frame.get("state_path")
    if explicit:
        return str(explicit).replace("\\", "/")
    parent_id = (
        str(parent_frame.get("parent_ticket_id") or "").strip()
        or str(subtask.get("parent_ticket_id") or "").strip()
        or "UNKNOWN"
    )
    return _DEFAULT_PARENT_STATE_TMPL.format(parent_ticket_id=parent_id)


def _goal_statement(subtask: Mapping[str, Any], parent_frame: Mapping[str, Any]) -> str:
    goal = parent_frame.get("goal") or parent_frame.get("Goal")
    if goal:
        return str(goal).strip()
    scope = str(subtask.get("scope_summary") or "").strip()
    sid = str(subtask.get("subtask_id") or "").strip() or "subtask"
    if scope:
        return f"Implement {sid}: {scope}"
    return f"Implement subtask {sid}"


def _acceptance_checks_summary(subtask: Mapping[str, Any]) -> str:
    checks = _as_str_list(subtask.get("acceptance_checks"))
    if not checks:
        return "(no acceptance_checks provided)"
    if len(checks) == 1:
        return checks[0]
    return "; ".join(f"{i}. {c}" for i, c in enumerate(checks, start=1))


def build_implementer_prompt(
    subtask: dict,
    parent_frame: dict,
) -> dict:
    """Build an Implementer-facing prompt structure from a subtask + parent FRAME.

    Returns a dict with at least:
      role, goal_statement, must_read, allowed_paths, blocked_paths,
      acceptance_checks_summary
    """
    if not isinstance(subtask, Mapping):
        return {
            "ok": False,
            "role": "implementer",
            "goal_statement": "",
            "must_read": [],
            "allowed_paths": [],
            "blocked_paths": [],
            "acceptance_checks_summary": "",
            "message": "subtask must be a mapping",
        }
    frame = parent_frame if isinstance(parent_frame, Mapping) else {}

    parent_state = _parent_state_path(subtask, frame)
    must_read = [
        parent_state,
        _ROLE_RULES_REF,
        _AGENTS_REF,
    ]
    # Prefer explicit must_read from FRAME, then append defaults (dedupe).
    frame_must = _as_str_list(frame.get("must_read"))
    for path in frame_must:
        if path not in must_read:
            must_read.append(path)

    allowed = _as_str_list(subtask.get("allowed_paths"))
    blocked = _as_str_list(subtask.get("blocked_paths"))
    # FRAME may tighten / extend path lists without mutating subtask contract.
    for path in _as_str_list(frame.get("allowed_paths")):
        if path not in allowed:
            allowed.append(path)
    for path in _as_str_list(frame.get("blocked_paths")):
        if path not in blocked:
            blocked.append(path)

    return {
        "ok": True,
        "role": "implementer",
        "subtask_id": str(subtask.get("subtask_id") or "").strip() or None,
        "parent_ticket_id": str(subtask.get("parent_ticket_id") or "").strip() or None,
        "goal_statement": _goal_statement(subtask, frame),
        "must_read": must_read,
        "allowed_paths": allowed,
        "blocked_paths": blocked,
        "acceptance_checks_summary": _acceptance_checks_summary(subtask),
        "scope_summary": str(subtask.get("scope_summary") or "").strip(),
        "target_paths": _as_str_list(subtask.get("target_paths")),
        "role_rules_ref": _ROLE_RULES_REF,
        "agents_ref": _AGENTS_REF,
        "message": "implementer prompt built",
    }
