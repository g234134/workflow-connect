#!/usr/bin/env python3
"""Verify Tabular tri-case HITL matrix schema and SMOKE_CASES drift (spec-only · TAB-S5-WS-A-T3).

Does NOT execute orchestrator resume paths, driver smoke, or claim prod/staging closure.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX_PATH = REPO_ROOT / "docs" / "tabular-tri-case-hitl-matrix-v1.yaml"

REQUIRED_CASE_IDS = ("demo_phase", "2026-0001", "generic-low-risk")
SMOKE_DRIFT_KEYS = ("case_id", "case_dir", "force_driver", "expected_delivery_ready")
REQUIRED_ENTRY_KEYS = (
    "case_id",
    "case_dir",
    "force_driver",
    "expected_delivery_ready",
    "cleaning_profile_id",
    "gate_status",
    "output_guard",
    "checkpoint_a_status",
    "checkpoint_b_status",
    "current_step",
    "automation_status",
    "verify_assertions",
)


def _load_matrix(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML not installed")
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("matrix root must be a mapping")
    return data


def _load_smoke_cases() -> list[dict[str, Any]]:
    scripts = str(REPO_ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    mod = importlib.import_module("run_tabular_mainline_regression_smoke")
    cases = getattr(mod, "SMOKE_CASES", None)
    if not isinstance(cases, list):
        raise ValueError("SMOKE_CASES must be a list")
    return cases


def _smoke_by_case_id(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for spec in cases:
        if not isinstance(spec, dict):
            continue
        cid = str(spec.get("case_id", ""))
        if cid in out:
            raise ValueError(f"duplicate SMOKE_CASES case_id {cid!r}")
        out[cid] = spec
    return out


def _collect_schema_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if data.get("schema_version") != "tabular_tri_case_hitl_matrix_v1":
        errors.append("schema_version must be tabular_tri_case_hitl_matrix_v1")
    if data.get("ticket_id") != "TAB-S5-WS-A-T3":
        errors.append("ticket_id must be TAB-S5-WS-A-T3")

    required_ids = data.get("required_case_ids") or []
    if list(required_ids) != list(REQUIRED_CASE_IDS):
        errors.append(f"required_case_ids must be {list(REQUIRED_CASE_IDS)}")

    entries = data.get("entries")
    if not isinstance(entries, dict):
        errors.append("entries must be a mapping")
        return errors

    if set(entries.keys()) != set(REQUIRED_CASE_IDS):
        errors.append(
            f"entries keys must match required_case_ids; got {sorted(entries.keys())}"
        )

    domain = data.get("verify_domain")
    if not isinstance(domain, dict):
        errors.append("verify_domain section missing or invalid")

    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        errors.append("extensions section missing or invalid")
    else:
        ws_b = extensions.get("ws_b_boundary")
        if not isinstance(ws_b, dict):
            errors.append("extensions.ws_b_boundary missing or invalid")
        elif not ws_b.get("readonly_fields"):
            errors.append("extensions.ws_b_boundary.readonly_fields must be non-empty")

    non_claims = data.get("non_claims") or []
    if not any("prod gate" in str(item).lower() for item in non_claims):
        errors.append("non_claims must state spec is not runtime prod gate")

    cp_a_allowed: set[str] = set()
    cp_b_allowed: set[str] = set()
    step_allowed: set[str] = set()
    if isinstance(domain, dict):
        cp_a_allowed = set(domain.get("checkpoint_a_status_allowed") or [])
        cp_b_allowed = set(domain.get("checkpoint_b_status_allowed") or [])
        step_allowed = set(domain.get("current_step_allowed") or [])

    for case_id, entry in entries.items():
        if not isinstance(entry, dict):
            errors.append(f"entry {case_id!r} is not a mapping")
            continue
        if entry.get("case_id") != case_id:
            errors.append(f"entry key {case_id!r} mismatch case_id {entry.get('case_id')!r}")

        for req in REQUIRED_ENTRY_KEYS:
            if req not in entry:
                errors.append(f"{case_id}: missing required field {req!r}")

        og = entry.get("output_guard")
        if not isinstance(og, dict) or "status" not in og:
            errors.append(f"{case_id}: output_guard.status required")

        assertions = entry.get("verify_assertions")
        if not isinstance(assertions, list) or len(assertions) < 3:
            errors.append(f"{case_id}: verify_assertions must be a non-empty list")

        if domain and entry.get("automation_status") != domain.get("automation_status"):
            errors.append(
                f"{case_id}: automation_status must match verify_domain "
                f"({domain.get('automation_status')!r})"
            )

        cp_a = entry.get("checkpoint_a_status")
        if cp_a_allowed and cp_a not in cp_a_allowed:
            errors.append(f"{case_id}: checkpoint_a_status {cp_a!r} not in allowed set")

        cp_b = entry.get("checkpoint_b_status")
        also_valid = entry.get("checkpoint_b_status_also_valid") or []
        cp_b_valid = {cp_b} | {x for x in also_valid if x}
        if cp_b_allowed and not cp_b_valid.issubset(cp_b_allowed):
            errors.append(f"{case_id}: checkpoint_b terminal values not in allowed set")

        step = entry.get("current_step")
        if step_allowed and step not in step_allowed:
            errors.append(f"{case_id}: current_step {step!r} not in allowed set")

        if entry.get("dlq_status") != "none":
            errors.append(f"{case_id}: tri-case smoke happy path expects dlq_status=none")

    return errors


def _collect_smoke_drift(
    entries: dict[str, Any],
    smoke_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []

    if set(smoke_by_id.keys()) != set(REQUIRED_CASE_IDS):
        errors.append(
            f"SMOKE_CASES case_ids {sorted(smoke_by_id.keys())} "
            f"must match matrix {list(REQUIRED_CASE_IDS)}"
        )

    for case_id in REQUIRED_CASE_IDS:
        entry = entries.get(case_id)
        smoke = smoke_by_id.get(case_id)
        if not isinstance(entry, dict) or not isinstance(smoke, dict):
            continue
        for key in SMOKE_DRIFT_KEYS:
            matrix_val = entry.get(key)
            smoke_val = smoke.get(key)
            if matrix_val != smoke_val:
                errors.append(
                    f"{case_id}: drift on {key}: matrix={matrix_val!r} smoke={smoke_val!r}"
                )

    return errors


def verify_matrix(path: Path | None = None) -> dict[str, Any]:
    matrix_path = path or DEFAULT_MATRIX_PATH
    if not matrix_path.is_file():
        return {
            "ok": False,
            "message": f"matrix file not found: {matrix_path}",
            "path": str(matrix_path.relative_to(REPO_ROOT).as_posix()),
        }

    try:
        data = _load_matrix(matrix_path)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "message": str(exc),
            "path": str(matrix_path.relative_to(REPO_ROOT).as_posix()),
        }

    errors = _collect_schema_errors(data)

    entries = data.get("entries")
    if isinstance(entries, dict):
        try:
            smoke_cases = _load_smoke_cases()
            smoke_by_id = _smoke_by_case_id(smoke_cases)
            errors.extend(_collect_smoke_drift(entries, smoke_by_id))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"SMOKE_CASES load failed: {exc}")

    if errors:
        return {
            "ok": False,
            "message": f"{len(errors)} matrix validation error(s)",
            "errors": errors,
            "path": str(matrix_path.relative_to(REPO_ROOT).as_posix()),
            "entries_checked": len(entries) if isinstance(entries, dict) else 0,
            "case_ids": list(REQUIRED_CASE_IDS),
        }

    return {
        "ok": True,
        "message": "tri-case HITL matrix schema complete; SMOKE_CASES aligned",
        "path": str(matrix_path.relative_to(REPO_ROOT).as_posix()),
        "entries_checked": len(entries),
        "case_ids": list(REQUIRED_CASE_IDS),
        "ticket_id": "TAB-S5-WS-A-T3",
    }


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MATRIX_PATH
    result = verify_matrix(path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
