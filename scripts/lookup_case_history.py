#!/usr/bin/env python3
"""Read-only historical case lookup against cases/index.json (Wave 4A MEMO).

Usage:
    python scripts/lookup_case_history.py --list-all
    python scripts/lookup_case_history.py --client-ref sampleco
    python scripts/lookup_case_history.py --product-sku CLEAN-BASIC
    python scripts/lookup_case_history.py --schema-headers Phase,名稱
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from cases_index_lib import (  # noqa: E402
    _extract_cleaning_rules,
    _load_report,
    _parse_header_list,
    _read_intake,
    lookup_cases,
    read_schema_headers,
    repo_root,
)

_RULES_SIDECAR_FILES = (
    "cleaning_goals.json",
    "schema_hints.json",
    "cleaning_rules.json",
)


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _case_rel_path(case_dir: Path, root: Path) -> str:
    try:
        return case_dir.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return case_dir.as_posix()


def _resolve_cleaning_goals(intake: dict[str, Any], sidecar: dict[str, Any] | None) -> str | None:
    if sidecar:
        goals = sidecar.get("goals")
        if isinstance(goals, str) and goals.strip():
            return goals.strip()
        text = sidecar.get("cleaning_goals")
        if isinstance(text, str) and text.strip():
            return text.strip()
    value = intake.get("cleaning_goals")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _resolve_cleaning_profile(intake: dict[str, Any], sidecar: dict[str, Any] | None) -> str | None:
    if sidecar:
        profile = sidecar.get("cleaning_profile")
        if isinstance(profile, str) and profile.strip():
            return profile.strip()
    value = intake.get("cleaning_profile")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _resolve_schema_hints(
    intake: dict[str, Any],
    sidecar: dict[str, Any] | None,
    *,
    schema_headers: list[str],
) -> dict[str, Any]:
    hints: dict[str, Any] = {}
    if sidecar:
        nested = sidecar.get("schema")
        if isinstance(nested, dict):
            hints.update(nested)
        for key, value in sidecar.items():
            if key in ("schema_version", "schema", "copied_from", "schema_headers"):
                continue
            hints.setdefault(key, value)
    intake_schema = intake.get("schema")
    if isinstance(intake_schema, dict):
        for key, value in intake_schema.items():
            hints.setdefault(key, value)
    if schema_headers:
        hints.setdefault("headers", schema_headers)
    return hints


def _resolve_cleaning_rules(
    rules_sidecar: dict[str, Any] | None,
    report: dict[str, Any] | None,
) -> list[Any]:
    if rules_sidecar:
        rules = rules_sidecar.get("cleaning_rules")
        if isinstance(rules, list) and rules:
            return list(rules)
        applied = rules_sidecar.get("cleaning_rules_applied")
        if isinstance(applied, list) and applied:
            return list(applied)
    extracted = _extract_cleaning_rules(report)
    if extracted:
        return [{"rule": rule_id, "description": rule_id} for rule_id in extracted]
    if report:
        applied = report.get("cleaning_rules_applied")
        if isinstance(applied, list):
            return list(applied)
    return []


def load_case_rules(case_dir: Path, repo_root_path: Path | None = None) -> dict[str, Any]:
    """Load rules / schema hints / goals summary for a case directory (read-only)."""
    root = repo_root_path or repo_root()
    case_dir = case_dir.resolve()
    if not case_dir.is_dir():
        return {
            "ok": False,
            "case_dir": _case_rel_path(case_dir, root),
            "message": "case_dir_missing",
        }

    intake = _read_intake(case_dir) or {}
    goals_sidecar = _read_json_file(case_dir / "cleaning_goals.json")
    schema_sidecar = _read_json_file(case_dir / "schema_hints.json")
    rules_sidecar = _read_json_file(case_dir / "cleaning_rules.json")
    report = _load_report(case_dir)
    schema_headers = read_schema_headers(case_dir, intake)

    case_id = intake.get("case_id")
    if not isinstance(case_id, str) or not case_id.strip():
        case_id = case_dir.name
    client_ref = intake.get("client_ref")
    if not isinstance(client_ref, str) or not client_ref.strip():
        client_ref = case_dir.parent.name

    cleaning_goals = _resolve_cleaning_goals(intake, goals_sidecar)
    cleaning_profile = _resolve_cleaning_profile(intake, goals_sidecar)
    if not cleaning_profile and report:
        profile_id = report.get("cleaning_profile_id")
        if isinstance(profile_id, str) and profile_id.strip():
            cleaning_profile = profile_id.strip()
        meta = report.get("meta") or {}
        meta_profile = meta.get("cleaning_profile_id")
        if isinstance(meta_profile, str) and meta_profile.strip():
            cleaning_profile = meta_profile.strip()

    schema_hints = _resolve_schema_hints(intake, schema_sidecar, schema_headers=schema_headers)
    cleaning_rules = _resolve_cleaning_rules(rules_sidecar, report)

    sources: dict[str, bool] = {
        "intake.json": (case_dir / "intake.json").is_file(),
        "cleaning_goals.json": goals_sidecar is not None,
        "schema_hints.json": schema_sidecar is not None,
        "cleaning_rules.json": rules_sidecar is not None,
        "reports/report.json": report is not None,
    }

    if not any([cleaning_goals, cleaning_profile, schema_hints, cleaning_rules]):
        return {
            "ok": False,
            "case_dir": _case_rel_path(case_dir, root),
            "case_id": case_id.strip(),
            "client_ref": client_ref.strip(),
            "sources": sources,
            "message": "no_rules_found",
        }

    return {
        "ok": True,
        "case_dir": _case_rel_path(case_dir, root),
        "case_id": case_id.strip(),
        "client_ref": client_ref.strip(),
        "cleaning_goals": cleaning_goals,
        "cleaning_profile": cleaning_profile,
        "schema_hints": schema_hints,
        "schema_headers": schema_headers,
        "cleaning_rules": cleaning_rules,
        "sources": sources,
        "message": "rules_loaded",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lookup registered cases from cases/index.json (structured filters only)."
    )
    parser.add_argument("--client-ref", help="Exact client_ref match (case-insensitive)")
    parser.add_argument("--product-sku", help="Exact product_sku match (case-insensitive)")
    parser.add_argument(
        "--schema-headers",
        help="Comma-separated header names; matches subset or exact set against indexed schema_headers",
    )
    parser.add_argument("--list-all", action="store_true", help="Return all indexed entries")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include schema_headers, cleaning_rules, delivery_template_ref, qa fields",
    )
    args = parser.parse_args(argv)

    if not args.list_all and not any([args.client_ref, args.product_sku, args.schema_headers]):
        parser.error("specify at least one filter or --list-all")

    result = lookup_cases(
        client_ref=args.client_ref,
        product_sku=args.product_sku,
        schema_headers=_parse_header_list(args.schema_headers),
        list_all=args.list_all,
        verbose=args.verbose,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
