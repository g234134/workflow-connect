"""Intake Gate durable outbox writer v1 (P75-G2).

Writes per-decision JSON under outbox/<case_ref>/ and appends intake_gate_events.jsonl.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from routing.intake_gate_mapping_v1 import compact_ts
from tools.tabular_outbox_writer import outbox_root

RECORD_TYPE = "intake_gate_decision"
EVENTS_FILENAME = "intake_gate_events.jsonl"


def intake_gate_record_filename(intake_decision_id: str, created_at: str) -> str:
    ts = compact_ts(created_at)
    short_id = intake_decision_id.rsplit("_", 1)[-1]
    return f"intake_gate_decision_{ts}_{short_id}.json"


def build_event_line(
    *,
    intake_decision_id: str,
    case_ref: str,
    decision: str,
    created_at: str,
    record_path: str,
) -> Dict[str, Any]:
    return {
        "intake_decision_id": intake_decision_id,
        "case_ref": case_ref,
        "decision": decision,
        "created_at": created_at,
        "record_path": record_path,
    }


def write_intake_gate_record(
    gate_result: Dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> str:
    """Persist full gate result; returns repo-relative record path."""
    root = outbox_root(repo_root, outbox_root_override)
    case_ref = str(gate_result["case_ref"])
    intake_decision_id = str(gate_result["intake_decision_id"])
    created_at = str(gate_result["created_at"])

    safe_case = case_ref.replace("\\", "/").strip("/")
    dest_dir = root / safe_case
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = intake_gate_record_filename(intake_decision_id, created_at)
    dest = dest_dir / filename

    payload = dict(gate_result)
    payload["record_type"] = RECORD_TYPE
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    try:
        repo = repo_root.resolve() if repo_root else Path(__file__).resolve().parents[1]
        rel = dest.relative_to(repo).as_posix()
    except ValueError:
        try:
            rel = dest.relative_to(root).as_posix()
            rel = f"outbox/{rel}"
        except ValueError:
            rel = str(dest)

    append_intake_gate_event(
        build_event_line(
            intake_decision_id=intake_decision_id,
            case_ref=case_ref,
            decision=str(gate_result.get("decision") or ""),
            created_at=created_at,
            record_path=rel,
        ),
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    return rel


def append_intake_gate_event(
    event: Dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    root = outbox_root(repo_root, outbox_root_override)
    root.mkdir(parents=True, exist_ok=True)
    events_path = root / EVENTS_FILENAME
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return events_path
