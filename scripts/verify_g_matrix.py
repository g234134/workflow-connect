#!/usr/bin/env python3
"""Verify P7 resume-loop G-1–G-5 matrix schema (spec-only · W2-P7-matrix-G1-G5-resume-loop-v1).

Does NOT execute orchestrator resume paths or claim prod/staging closure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

try:
    import yaml
except ImportError:  # pragma: no cover - std fallback for minimal envs
    yaml = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX_PATH = (
    REPO_ROOT / "04_Workflows" / "testing" / "p7-resume-loop-g1-g5-matrix-v1.yaml"
)
REQUIRED_GAP_IDS = ("G-1", "G-2", "G-3", "G-4", "G-5")
REQUIRED_ENTRY_KEYS = (
    "gap_id",
    "matrix_row",
    "trigger",
    "expected_resume",
    "error_interrupt",
    "trace_fields",
    "verify_commands",
)
REQUIRED_EXPECTED_RESUME_KEYS = ("ok", "final_status", "orchestrator_enters_s7_s13")
BLOCKED_GAP_IDS = frozenset(REQUIRED_GAP_IDS)


def _load_matrix(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
    else:
        raise RuntimeError(
            "PyYAML not installed; install pyyaml or use Python with yaml available"
        )
    if not isinstance(data, dict):
        raise ValueError("matrix root must be a mapping")
    return data


def _collect_contradictions(entries: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    seen_rows: Dict[str, str] = {}
    seen_gap_ids: Set[str] = set()

    for key, entry in entries.items():
        if not isinstance(entry, dict):
            errors.append(f"entry {key!r} is not a mapping")
            continue

        gap_id = entry.get("gap_id")
        if gap_id != key:
            errors.append(f"entry key {key!r} mismatch gap_id {gap_id!r}")

        if gap_id in seen_gap_ids:
            errors.append(f"duplicate gap_id {gap_id!r}")
        seen_gap_ids.add(str(gap_id))

        for req in REQUIRED_ENTRY_KEYS:
            if req not in entry:
                errors.append(f"{gap_id}: missing required field {req!r}")

        expected = entry.get("expected_resume")
        if isinstance(expected, dict):
            for req in REQUIRED_EXPECTED_RESUME_KEYS:
                if req not in expected:
                    errors.append(f"{gap_id}: expected_resume missing {req!r}")
            if expected.get("ok") is not False:
                errors.append(
                    f"{gap_id}: all G-1–G-5 scenarios must expect ok=false in v1 spec"
                )
            if expected.get("orchestrator_enters_s7_s13") is not False:
                errors.append(
                    f"{gap_id}: orchestrator_enters_s7_s13 must be false for gap scenarios"
                )
            final_status = expected.get("final_status")
            if gap_id == "G-1" and final_status != "stale_checkpoint":
                errors.append(f"G-1: final_status must be stale_checkpoint")
            if gap_id in ("G-2", "G-3", "G-4", "G-5") and final_status != "blocked":
                errors.append(f"{gap_id}: final_status must be blocked")

        matrix_row = entry.get("matrix_row")
        if matrix_row:
            if matrix_row in seen_rows:
                errors.append(
                    f"duplicate matrix_row {matrix_row!r} "
                    f"({seen_rows[matrix_row]} vs {gap_id})"
                )
            seen_rows[str(matrix_row)] = str(gap_id)

        trace_fields = entry.get("trace_fields")
        if isinstance(trace_fields, dict):
            if gap_id == "G-1" and trace_fields.get("resume_eligibility") != "stale_checkpoint":
                errors.append("G-1: trace resume_eligibility must be stale_checkpoint")
            if gap_id == "G-2" and trace_fields.get("resume_blocked_reason") != "revise_needed":
                errors.append("G-2: resume_blocked_reason must be revise_needed")
            if gap_id == "G-3" and trace_fields.get("resume_blocked_reason") != "on_hold":
                errors.append("G-3: resume_blocked_reason must be on_hold")
            if gap_id == "G-4" and "checkpoint_load_error" not in trace_fields:
                errors.append("G-4: trace_fields must include checkpoint_load_error")
            if gap_id == "G-5" and trace_fields.get("case_allowlist_block") is not True:
                errors.append("G-5: case_allowlist_block must be true")

    missing = set(REQUIRED_GAP_IDS) - seen_gap_ids
    for gap_id in sorted(missing):
        errors.append(f"missing required gap entry {gap_id}")

    extra = seen_gap_ids - set(REQUIRED_GAP_IDS)
    for gap_id in sorted(extra):
        if gap_id.startswith("G-"):
            errors.append(f"unexpected G-* entry {gap_id} in G-1–G-5-only matrix")

    return errors


def verify_matrix(path: Path | None = None) -> Dict[str, Any]:
    matrix_path = path or DEFAULT_MATRIX_PATH
    if not matrix_path.is_file():
        return {
            "ok": False,
            "message": f"matrix file not found: {matrix_path}",
            "path": str(matrix_path),
        }

    try:
        data = _load_matrix(matrix_path)
    except Exception as exc:  # noqa: BLE001 - return structured dict
        return {"ok": False, "message": str(exc), "path": str(matrix_path)}

    required_gap_ids = data.get("required_gap_ids") or []
    if list(required_gap_ids) != list(REQUIRED_GAP_IDS):
        return {
            "ok": False,
            "message": "required_gap_ids must be G-1 through G-5 in order",
            "path": str(matrix_path),
        }

    entries = data.get("entries")
    if not isinstance(entries, dict):
        return {
            "ok": False,
            "message": "entries must be a mapping",
            "path": str(matrix_path),
        }

    errors = _collect_contradictions(entries)
    trace = data.get("trace_contract")
    if not isinstance(trace, dict):
        errors.append("trace_contract section missing or invalid")
    else:
        gate_status = trace.get("gate_trace_status")
        if gate_status not in ("active", "landed", "pending_w1_t5"):
            errors.append(
                "trace_contract.gate_trace_status must be active, landed, or pending_w1_t5"
            )
        mix = trace.get("gate_trace_fields_do_not_mix") or []
        if "intake.gate_decision" not in mix:
            errors.append("gate trace mix guard must list intake.gate_decision")

    non_claims = data.get("non_claims") or []
    if not any("prod gate" in str(item).lower() for item in non_claims):
        errors.append("non_claims must state spec is not runtime prod gate")

    if errors:
        return {
            "ok": False,
            "message": f"{len(errors)} matrix validation error(s)",
            "errors": errors,
            "path": str(matrix_path),
            "entries_checked": len(entries),
        }

    return {
        "ok": True,
        "message": "G-1–G-5 matrix schema complete; no contradictions detected",
        "path": str(matrix_path),
        "entries_checked": len(entries),
        "gap_ids": list(REQUIRED_GAP_IDS),
    }


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MATRIX_PATH
    result = verify_matrix(path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
