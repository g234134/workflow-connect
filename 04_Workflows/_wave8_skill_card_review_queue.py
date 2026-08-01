#!/usr/bin/env python3
"""
Wave 8 — Skill Card review queue (v0.1).

Minimal list / approve / reject workflow for JSON drafts under skills/drafts/.
Does not modify Skill Registry loader or Submit CLI.

Usage:
    python 04_Workflows/_wave8_skill_card_review_queue.py list

    python 04_Workflows/_wave8_skill_card_review_queue.py approve \\
        --draft skills/drafts/draft-clean-basic-job.json \\
        --review-notes "verified run_summary"

    python 04_Workflows/_wave8_skill_card_review_queue.py reject \\
        --draft skills/drafts/bad-draft.json \\
        --review-notes "scope too broad"

    python 04_Workflows/_wave8_skill_card_review_queue.py list-approved --pretty

    python 04_Workflows/_wave8_skill_card_review_queue.py promote-from-queue \\
        --draft skills/cards/promote-me.json --pretty

Exit codes:
    0 — success
    1 — validation, I/O, or JSON parse error
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_JSON_SUFFIX = ".json"


def _resolve_repo_root() -> Path:
    """Repo root (parent of 04_Workflows)."""
    return Path(__file__).parent.resolve().parent


def resolve_skills_root(skills_root: str | Path | None = None) -> Path:
    """Root of skills tree (contains drafts/, cards/, rejected/)."""
    if skills_root is not None:
        return Path(skills_root).resolve()
    return _resolve_repo_root() / "skills"


def drafts_dir(skills_root: Path) -> Path:
    return skills_root / "drafts"


def cards_dir(skills_root: Path) -> Path:
    return skills_root / "cards"


def rejected_dir(skills_root: Path) -> Path:
    return skills_root / "rejected"


def approved_registry_path(skills_root: Path) -> Path:
    return skills_root / "approved_registry.json"


_DEFAULT_REGISTRY_SCHEMA = "approved_skill_registry_v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_draft_json(path: Path) -> dict[str, Any]:
    """Load draft JSON; raise ValueError on parse or non-object root."""
    if path.suffix.lower() != _JSON_SUFFIX:
        raise ValueError(f"draft must be a {_JSON_SUFFIX} file: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"draft not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in draft: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("draft root must be a JSON object")
    return data


def _review_status(doc: dict[str, Any]) -> str | None:
    meta = doc.get("card_meta")
    if isinstance(meta, dict) and meta.get("review_status") is not None:
        return str(meta["review_status"])
    status = doc.get("review_status")
    return str(status) if status is not None else None


def _skill_id(doc: dict[str, Any]) -> str | None:
    meta = doc.get("card_meta")
    if isinstance(meta, dict) and meta.get("skill_id"):
        return str(meta["skill_id"])
    skill_id = doc.get("skill_id")
    return str(skill_id) if skill_id else None


def _skill_version(doc: dict[str, Any]) -> str:
    meta = doc.get("card_meta")
    if isinstance(meta, dict) and meta.get("version"):
        return str(meta["version"])
    return str(doc.get("version") or "0.1.0")


def _has_applicable_scenarios(doc: dict[str, Any]) -> bool:
    scenarios = doc.get("applicable_scenarios")
    return isinstance(scenarios, list) and len(scenarios) > 0


def _load_registry(skills_root: Path) -> dict[str, Any]:
    path = approved_registry_path(skills_root)
    if not path.is_file():
        return {
            "schema_version": _DEFAULT_REGISTRY_SCHEMA,
            "registry_revision": "1.0.0",
            "approved": [],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("approved_registry.json root must be a JSON object")
    approved = data.get("approved")
    if not isinstance(approved, list):
        raise ValueError("approved_registry.json approved must be an array")
    return data


def _save_registry(skills_root: Path, doc: dict[str, Any]) -> None:
    path = approved_registry_path(skills_root)
    _write_json(path, doc)


def list_approved(*, skills_root: Path) -> dict[str, Any]:
    """Return approved skill registry entries (index/metadata SSOT)."""
    registry = _load_registry(skills_root)
    approved = registry.get("approved", [])
    return {
        "ok": True,
        "registry_path": str(approved_registry_path(skills_root)),
        "schema_version": registry.get("schema_version"),
        "registry_revision": registry.get("registry_revision"),
        "count": len(approved),
        "approved": approved,
    }


def promote_from_queue(
    card_path: str | Path,
    *,
    skills_root: Path,
) -> dict[str, Any]:
    """
    Promote an approved skill card into approved_registry.json.

    Card must have review_status=approved and non-empty applicable_scenarios.
    Does not move files; use approve/reject for draft queue moves.
    """
    src = Path(card_path).resolve()
    doc = load_draft_json(src)
    review_status = _review_status(doc)
    if review_status != "approved":
        return {
            "ok": False,
            "message": f"card review_status must be approved, got {review_status!r}",
            "skill_id": _skill_id(doc),
        }

    skill_id = _skill_id(doc)
    if not skill_id:
        return {"ok": False, "message": "card missing skill_id"}

    if not _has_applicable_scenarios(doc):
        return {
            "ok": False,
            "message": "card incomplete: applicable_scenarios required for registry",
            "skill_id": skill_id,
            "selector_eligible": False,
        }

    version = _skill_version(doc)
    reviewed_at = doc.get("reviewed_at") or _utc_now_iso()
    registry = _load_registry(skills_root)
    approved_list: list[dict[str, Any]] = list(registry.get("approved", []))

    for entry in approved_list:
        if isinstance(entry, dict) and entry.get("skill_id") == skill_id:
            return {
                "ok": True,
                "skipped": True,
                "message": f"skill_id already in registry: {skill_id}",
                "skill_id": skill_id,
                "version": entry.get("version", version),
            }

    entry = {
        "skill_id": skill_id,
        "version": version,
        "approved_at": reviewed_at,
        "source_card_path": str(src),
        "selector_eligible": True,
    }
    approved_list.append(entry)
    registry["approved"] = approved_list
    _save_registry(skills_root, registry)

    return {
        "ok": True,
        "skipped": False,
        "skill_id": skill_id,
        "version": version,
        "approved_at": reviewed_at,
        "registry_path": str(approved_registry_path(skills_root)),
    }


def _draft_summary(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    meta = data.get("card_meta")
    skill_id = None
    review_status = data.get("review_status")
    if isinstance(meta, dict):
        skill_id = meta.get("skill_id")
        if review_status is None:
            review_status = meta.get("review_status")
    if skill_id is None:
        skill_id = data.get("skill_id")
    return {
        "path": str(path),
        "filename": path.name,
        "skill_id": skill_id,
        "review_status": review_status,
    }


def list_drafts(*, skills_root: Path) -> dict[str, Any]:
    """List all .json files directly under skills/drafts/."""
    root = drafts_dir(skills_root)
    root.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    for path in sorted(root.glob(f"*{_JSON_SUFFIX}")):
        if not path.is_file():
            continue
        try:
            data = load_draft_json(path)
        except (FileNotFoundError, ValueError):
            entries.append(
                {
                    "path": str(path),
                    "filename": path.name,
                    "skill_id": None,
                    "review_status": None,
                    "parse_ok": False,
                }
            )
            continue
        row = _draft_summary(path, data)
        row["parse_ok"] = True
        entries.append(row)

    return {
        "ok": True,
        "drafts_dir": str(root),
        "count": len(entries),
        "drafts": entries,
    }


def _apply_review_fields(
    doc: dict[str, Any],
    *,
    review_status: str,
    reviewed_at: str,
    review_notes: str | None,
) -> None:
    """Minimal in-place updates; preserve all other fields."""
    meta = doc.get("card_meta")
    if isinstance(meta, dict):
        meta["review_status"] = review_status
    else:
        doc["review_status"] = review_status
    doc["reviewed_at"] = reviewed_at
    if review_notes:
        doc["review_notes"] = review_notes


def _write_json(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def _move_promoted(
    draft_path: Path,
    dest_path: Path,
    doc: dict[str, Any],
) -> dict[str, Any]:
    if dest_path.exists():
        raise FileExistsError(f"destination already exists: {dest_path}")
    _write_json(dest_path, doc)
    draft_path.unlink()
    return {
        "ok": True,
        "action": "moved",
        "from": str(draft_path),
        "to": str(dest_path),
    }


def approve_draft(
    draft_path: str | Path,
    *,
    skills_root: Path,
    review_notes: str | None = None,
) -> dict[str, Any]:
    """Validate JSON, set review fields, move draft to skills/cards/."""
    src = Path(draft_path).resolve()
    doc = load_draft_json(src)
    reviewed_at = _utc_now_iso()
    _apply_review_fields(
        doc,
        review_status="approved",
        reviewed_at=reviewed_at,
        review_notes=review_notes,
    )
    dest = cards_dir(skills_root) / src.name
    result = _move_promoted(src, dest, doc)
    result["review_status"] = "approved"
    result["reviewed_at"] = reviewed_at
    return result


def reject_draft(
    draft_path: str | Path,
    *,
    skills_root: Path,
    review_notes: str | None = None,
) -> dict[str, Any]:
    """Validate JSON, set review fields, move draft to skills/rejected/."""
    src = Path(draft_path).resolve()
    doc = load_draft_json(src)
    reviewed_at = _utc_now_iso()
    _apply_review_fields(
        doc,
        review_status="rejected",
        reviewed_at=reviewed_at,
        review_notes=review_notes,
    )
    dest = rejected_dir(skills_root) / src.name
    result = _move_promoted(src, dest, doc)
    result["review_status"] = "rejected"
    result["reviewed_at"] = reviewed_at
    return result


def _emit_result(payload: dict[str, Any], *, pretty: bool) -> None:
    indent = 2 if pretty else None
    print(json.dumps(payload, indent=indent, ensure_ascii=False))


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--skills-root",
        default=None,
        help="Override skills/ tree root (default: <repo>/skills)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON stdout",
    )


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    _add_common_args(common)

    parser = argparse.ArgumentParser(
        description="Wave 8 Skill Card review queue: list, approve, or reject JSON drafts",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "list",
        help="List JSON drafts under skills/drafts/",
        parents=[common],
    )

    approve_p = sub.add_parser(
        "approve",
        help="Promote draft to skills/cards/",
        parents=[common],
    )
    approve_p.add_argument("--draft", required=True, help="Path to draft .json file")
    approve_p.add_argument(
        "--review-notes",
        default=None,
        help="Optional reviewer notes stored on the card",
    )

    reject_p = sub.add_parser(
        "reject",
        help="Archive draft to skills/rejected/",
        parents=[common],
    )
    reject_p.add_argument("--draft", required=True, help="Path to draft .json file")
    reject_p.add_argument(
        "--review-notes",
        default=None,
        help="Optional reviewer notes stored on the card",
    )

    sub.add_parser(
        "list-approved",
        help="List entries in skills/approved_registry.json",
        parents=[common],
    )

    promote_p = sub.add_parser(
        "promote-from-queue",
        help="Promote approved card into approved_registry.json",
        parents=[common],
    )
    promote_p.add_argument(
        "--draft",
        required=True,
        help="Path to approved card JSON (typically under skills/cards/)",
    )

    args = parser.parse_args(argv)
    skills_root = resolve_skills_root(args.skills_root)

    try:
        if args.command == "list":
            payload = list_drafts(skills_root=skills_root)
            _emit_result(payload, pretty=args.pretty)
            return 0
        if args.command == "approve":
            payload = approve_draft(
                args.draft,
                skills_root=skills_root,
                review_notes=args.review_notes,
            )
            _emit_result(payload, pretty=args.pretty)
            return 0
        if args.command == "reject":
            payload = reject_draft(
                args.draft,
                skills_root=skills_root,
                review_notes=args.review_notes,
            )
            _emit_result(payload, pretty=args.pretty)
            return 0
        if args.command == "list-approved":
            payload = list_approved(skills_root=skills_root)
            _emit_result(payload, pretty=args.pretty)
            return 0
        if args.command == "promote-from-queue":
            payload = promote_from_queue(
                args.draft,
                skills_root=skills_root,
            )
            _emit_result(payload, pretty=args.pretty)
            return 0 if payload.get("ok") else 1
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except (ValueError, FileExistsError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print("[ERROR] unknown command", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
