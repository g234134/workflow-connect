#!/usr/bin/env python3
"""Suggest cleaning profile from intake.json and raw CSV headers.

Usage:
    python scripts/suggest_cleaning_profile.py --case-dir cases/demo_phase
    python scripts/suggest_cleaning_profile.py --case-dir cases/internal/generic-low-risk --json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"
_SCRIPTS = _REPO_ROOT / "scripts"
for path in (_REPO_ROOT, _CSV_CLEANING, _SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from cleaning_profiles_v1 import (  # noqa: E402
    get_profile,
    list_profile_ids,
    resolve_cleaning_profile,
    validate_profile_schema,
)


def _read_intake(case_dir: Path) -> dict[str, Any]:
    path = case_dir / "intake.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _read_csv_headers(case_dir: Path, intake: dict[str, Any]) -> tuple[list[str] | None, str | None]:
    data_file = intake.get("data_file")
    if not isinstance(data_file, str) or not data_file.strip():
        return None, "missing_data_file"
    raw_path = case_dir / data_file
    if not raw_path.is_file():
        return None, f"raw_missing:{data_file}"

    encoding = str(intake.get("encoding") or "utf-8-sig")
    delimiter = str(intake.get("delimiter") or ",")
    for enc in (encoding, "utf-8-sig", "utf-8", "gbk"):
        try:
            with raw_path.open(encoding=enc, newline="") as fh:
                reader = csv.reader(fh, delimiter=delimiter[:1] or ",")
                row = next(reader, None)
                if row is None:
                    return [], None
                return [str(c).strip() for c in row], None
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    return None, "header_read_failed"


def _score_profile(profile_id: str, headers: list[str] | None, intake: dict[str, Any]) -> dict[str, Any]:
    profile = get_profile(profile_id)
    if profile is None:
        return {"profile_id": profile_id, "match": False, "reason": "unknown_profile"}

    if profile.get("schema_from_intake"):
        ok, err = validate_profile_schema(profile, intake, headers)
        return {
            "profile_id": profile_id,
            "match": ok,
            "reason": err or "schema_ok",
            "risk_level": profile.get("risk_level"),
        }

    expected = profile.get("columns") or []
    if not headers:
        return {"profile_id": profile_id, "match": False, "reason": "no_headers"}
    header_set = frozenset(headers)
    missing = [c for c in expected if c not in header_set]
    if missing:
        return {
            "profile_id": profile_id,
            "match": False,
            "reason": f"header_mismatch:{','.join(missing)}",
            "risk_level": profile.get("risk_level"),
        }
    return {
        "profile_id": profile_id,
        "match": True,
        "reason": "columns_match",
        "risk_level": profile.get("risk_level"),
    }


def suggest_cleaning_profile(case_dir: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    case_dir = case_dir.resolve()
    intake = _read_intake(case_dir)
    headers, header_err = _read_csv_headers(case_dir, intake)

    configured, cfg_err = resolve_cleaning_profile(case_dir, intake, repo_root=root)
    configured_id = str(configured.get("profile_id") or "") if configured else None

    scores = [_score_profile(pid, headers, intake) for pid in list_profile_ids()]
    matches = [s for s in scores if s.get("match")]

    if configured_id and any(s["profile_id"] == configured_id and s.get("match") for s in scores):
        suggested = configured_id
        eligibility = "accepted"
    elif matches:
        suggested = matches[0]["profile_id"]
        eligibility = "accepted" if suggested == "generic_low_risk_profile" else "needs_review"
    elif header_err or headers is None:
        suggested = configured_id or "generic_low_risk_profile"
        eligibility = "needs_review"
    else:
        unknown = [h for h in headers if h]
        suggested = configured_id or "generic_low_risk_profile"
        eligibility = "needs_review"
        if unknown and not configured_id:
            eligibility = "needs_review"

    risk = "low"
    if eligibility == "needs_review":
        risk = "medium"
    if header_err == "header_read_failed":
        risk = "high"
        eligibility = "needs_review"

    return {
        "ok": True,
        "case_dir": case_dir.relative_to(root).as_posix(),
        "case_id": intake.get("case_id") or case_dir.name,
        "suggested_profile": suggested,
        "configured_profile": configured_id,
        "profile_resolution_error": cfg_err,
        "eligibility": eligibility,
        "risk_level": risk,
        "headers": headers,
        "header_error": header_err,
        "profile_scores": scores,
        "message": f"suggested={suggested} eligibility={eligibility}",
    }


def apply_suggested_profile(case_dir: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Persist a successful suggestion as the case's explicit runner profile."""
    if not result.get("ok"):
        return {"ok": False, "message": "cannot_apply_failed_suggestion"}

    suggested = result.get("suggested_profile")
    if not isinstance(suggested, str) or not get_profile(suggested):
        return {"ok": False, "message": "cannot_apply_unknown_profile"}

    intake_path = case_dir / "intake.json"
    intake = _read_intake(case_dir)
    if not intake:
        return {"ok": False, "message": "cannot_apply_missing_or_invalid_intake"}

    intake["cleaning_profile"] = suggested
    intake_path.write_text(json.dumps(intake, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "case_dir": result.get("case_dir"),
        "applied_profile": suggested,
        "intake_path": str(intake_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Suggest tabular cleaning profile from intake + CSV.")
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the suggested profile to intake.json after an explicit operator review.",
    )
    args = parser.parse_args(argv)

    case_dir = args.case_dir
    if not case_dir.is_absolute():
        case_dir = _REPO_ROOT / case_dir

    result = suggest_cleaning_profile(case_dir)
    if args.apply:
        result["apply_result"] = apply_suggested_profile(case_dir, result)
        if not result["apply_result"].get("ok"):
            result["ok"] = False
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result.get("message", ""))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
