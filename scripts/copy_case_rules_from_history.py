#!/usr/bin/env python3
"""Copy cleaning rules / schema hints / goals from a historical case to a new case.

Usage:
    python scripts/copy_case_rules_from_history.py \\
        --from-case-dir cases/sampleco/2026-0001 \\
        --to-case-dir cases/internal/new-demo-case \\
        --json

    python scripts/copy_case_rules_from_history.py \\
        --from-case-dir cases/sampleco/2026-0001 \\
        --to-case-dir cases/internal/new-demo-case \\
        --dry-run --json
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lookup_case_history import load_case_rules  # noqa: E402

_INTAKE_IDENTITY_KEYS = frozenset(
    {
        "case_id",
        "client_ref",
        "product_sku",
        "data_file",
        "file_format",
        "encoding",
        "delimiter",
        "scale",
        "provenance",
        "sensitivity",
        "structure",
        "security_compliance",
    }
)

_COPY_TARGETS = (
    "cleaning_goals.json",
    "schema_hints.json",
    "cleaning_rules.json",
    "intake.json",
)


def _resolve_case_dir(case_dir: Path, repo_root: Path) -> Path:
    if case_dir.is_absolute():
        return case_dir.resolve()
    return (repo_root / case_dir).resolve()


def _build_cleaning_goals_payload(source: dict[str, Any], from_rel: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "gov-cleaning-goals-v0.1",
        "copied_from": from_rel,
    }
    goals = source.get("cleaning_goals")
    if isinstance(goals, str) and goals.strip():
        payload["goals"] = goals.strip()
    profile = source.get("cleaning_profile")
    if isinstance(profile, str) and profile.strip():
        payload["cleaning_profile"] = profile.strip()
    return payload


def _build_schema_hints_payload(source: dict[str, Any], from_rel: str) -> dict[str, Any]:
    hints = source.get("schema_hints")
    schema = deepcopy(hints) if isinstance(hints, dict) else {}
    headers = source.get("schema_headers")
    if isinstance(headers, list) and headers:
        schema.setdefault("headers", headers)
    return {
        "schema_version": "gov-schema-hints-v0.1",
        "copied_from": from_rel,
        "schema": schema,
    }


def _build_cleaning_rules_payload(source: dict[str, Any], from_rel: str) -> dict[str, Any]:
    rules = source.get("cleaning_rules")
    return {
        "schema_version": "gov-cleaning-rules-v0.1",
        "copied_from": from_rel,
        "cleaning_rules": list(rules) if isinstance(rules, list) else [],
    }


def _patch_intake_rules(
    target_intake: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    patched = deepcopy(target_intake)
    goals = source.get("cleaning_goals")
    if isinstance(goals, str) and goals.strip():
        patched["cleaning_goals"] = goals.strip()
    profile = source.get("cleaning_profile")
    if isinstance(profile, str) and profile.strip():
        patched["cleaning_profile"] = profile.strip()
    hints = source.get("schema_hints")
    if isinstance(hints, dict) and hints:
        patched["schema"] = deepcopy(hints)
    return patched


def _read_target_intake(to_case_dir: Path) -> tuple[dict[str, Any], bool]:
    intake_path = to_case_dir / "intake.json"
    if not intake_path.is_file():
        return {}, False
    try:
        data = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, True
    return (data if isinstance(data, dict) else {}), True


def copy_case_rules_from_history(
    *,
    from_case_dir: Path,
    to_case_dir: Path,
    dry_run: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    from_dir = _resolve_case_dir(from_case_dir, root)
    to_dir = _resolve_case_dir(to_case_dir, root)

    source = load_case_rules(from_dir, root)
    if not source.get("ok"):
        return {
            "ok": False,
            "from_case_id": None,
            "to_case_id": None,
            "copied_files": [],
            "dry_run": dry_run,
            "message": f"source_load_failed:{source.get('message', 'unknown')}",
        }

    if not to_dir.is_dir():
        return {
            "ok": False,
            "from_case_id": source.get("case_id"),
            "to_case_id": None,
            "copied_files": [],
            "dry_run": dry_run,
            "message": "target_case_dir_missing",
        }

    from_rel = str(source.get("case_dir") or _resolve_case_dir(from_case_dir, root))
    target_intake, had_intake = _read_target_intake(to_dir)
    to_case_id = target_intake.get("case_id") if isinstance(target_intake.get("case_id"), str) else to_dir.name

    planned_writes: list[dict[str, Any]] = [
        {
            "path": "cleaning_goals.json",
            "action": "overwrite" if (to_dir / "cleaning_goals.json").is_file() else "create",
            "payload": _build_cleaning_goals_payload(source, from_rel),
        },
        {
            "path": "schema_hints.json",
            "action": "overwrite" if (to_dir / "schema_hints.json").is_file() else "create",
            "payload": _build_schema_hints_payload(source, from_rel),
        },
        {
            "path": "cleaning_rules.json",
            "action": "overwrite" if (to_dir / "cleaning_rules.json").is_file() else "create",
            "payload": _build_cleaning_rules_payload(source, from_rel),
        },
    ]

    intake_action = "overwrite" if had_intake else "create"
    intake_payload = _patch_intake_rules(target_intake, source) if had_intake else _patch_intake_rules({}, source)
    planned_writes.append(
        {
            "path": "intake.json",
            "action": intake_action,
            "payload": intake_payload,
            "preserve_identity_keys": sorted(_INTAKE_IDENTITY_KEYS),
        }
    )

    copied_files: list[str] = []
    if dry_run:
        copied_files = [item["path"] for item in planned_writes]
        return {
            "ok": True,
            "from_case_id": source.get("case_id"),
            "to_case_id": to_case_id,
            "copied_files": copied_files,
            "dry_run": True,
            "planned_writes": [
                {
                    "path": item["path"],
                    "action": item["action"],
                }
                for item in planned_writes
            ],
            "message": "dry_run: would overwrite sidecar files and patch intake rules fields",
        }

    to_dir.mkdir(parents=True, exist_ok=True)
    for item in planned_writes:
        rel_path = item["path"]
        target_path = to_dir / rel_path
        existed = target_path.is_file()
        target_path.write_text(
            json.dumps(item["payload"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        action = "overwrote" if existed else "created"
        copied_files.append(f"{rel_path} ({action})")

    return {
        "ok": True,
        "from_case_id": source.get("case_id"),
        "to_case_id": to_case_id,
        "copied_files": copied_files,
        "dry_run": False,
        "message": "copied rules via overwrite (sidecar files + intake rules fields; intake identity preserved)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy cleaning rules / schema hints / goals from a historical case."
    )
    parser.add_argument("--from-case-dir", required=True, type=Path, help="Source historical case directory")
    parser.add_argument("--to-case-dir", required=True, type=Path, help="Target new case directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview copy actions without writing files")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON result")
    args = parser.parse_args(argv)

    result = copy_case_rules_from_history(
        from_case_dir=args.from_case_dir,
        to_case_dir=args.to_case_dir,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "DRY RUN" if result.get("dry_run") else "COPY"
        print(f"[{status}] ok={result.get('ok')} message={result.get('message')}")
        for path in result.get("copied_files") or []:
            print(f"  - {path}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
