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
