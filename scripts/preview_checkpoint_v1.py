#!/usr/bin/env python3
"""Checkpoint preview CLI v1 (P8-T2c) — read-only operator preview before decide.

Usage:
    python scripts/preview_checkpoint_v1.py --checkpoint-path outbox/demo_phase/A-....json
    python scripts/preview_checkpoint_v1.py --checkpoint-id A-intake-confirmation --case-ref demo_phase
    python scripts/preview_checkpoint_v1.py --checkpoint-id A-intake-confirmation --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hitl.checkpoints_v1 import (  # noqa: E402
    get_checkpoint,
    review_summary,
)
from tools.tabular_outbox_writer import outbox_root  # noqa: E402

SCHEMA_VERSION = "checkpoint_preview_v1"


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def _resolve_outbox(
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    return outbox_root(repo_root or _REPO_ROOT, outbox_root_override).resolve()


def _assert_under_outbox(target: Path, root: Path) -> None:
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path must stay under outbox/: {target}") from exc


def _load_checkpoint_from_path(
    checkpoint_path: str | Path,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Load checkpoint JSON; fail-close if outside outbox or invalid JSON."""
    path = Path(checkpoint_path)
    if not path.is_absolute():
        path = _repo_root(repo_root) / path
    path = path.resolve()
    root = _resolve_outbox(repo_root, outbox_root_override)
    _assert_under_outbox(path, root)
    if not path.is_file():
        raise FileNotFoundError(f"checkpoint file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("checkpoint JSON must be an object")
    return data


def preview_checkpoint(
    *,
    checkpoint_path: Optional[str] = None,
    checkpoint_id: Optional[str] = None,
    case_ref: Optional[str] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a read-only preview dict for operator decision support."""
    base: Dict[str, Any] = {
        "ok": False,
        "read_only": True,
        "schema_version": SCHEMA_VERSION,
        "mutated": False,
        "checkpoint_path": None,
        "preview": None,
        "message": "",
    }

    if bool(checkpoint_path) == bool(checkpoint_id):
        base["message"] = "exactly one of --checkpoint-path or --checkpoint-id is required"
        return base

    try:
        if checkpoint_path:
            data = _load_checkpoint_from_path(
                checkpoint_path,
                repo_root=repo_root,
                outbox_root_override=outbox_root_override,
            )
            resolved_path = str(
                (Path(checkpoint_path) if Path(checkpoint_path).is_absolute() else _repo_root(repo_root) / checkpoint_path).resolve()
            )
        else:
            assert checkpoint_id is not None
            data = get_checkpoint(
                checkpoint_id,
                repo_root=repo_root,
                outbox_root_override=outbox_root_override,
                pending_only=False,
            )
            if data is None:
                base["message"] = f"checkpoint not found for id={checkpoint_id!r}"
                return base
            if case_ref and str(data.get("case_ref") or "") != case_ref:
                # get_checkpoint returns first match; enforce case_ref when provided
                root = _resolve_outbox(repo_root, outbox_root_override)
                matched = None
                for path in root.rglob("*.json"):
                    try:
                        with path.open("r", encoding="utf-8") as fh:
                            cand = json.load(fh)
                    except (OSError, json.JSONDecodeError):
                        continue
                    if not isinstance(cand, dict):
                        continue
                    if cand.get("checkpoint_id") != checkpoint_id:
                        continue
                    if str(cand.get("case_ref") or "") != case_ref:
                        continue
                    matched = (cand, path)
                    break
                if matched is None:
                    base["message"] = (
                        f"checkpoint not found for id={checkpoint_id!r} case_ref={case_ref!r}"
                    )
                    return base
                data, path_obj = matched
                resolved_path = str(path_obj.resolve())
            else:
                resolved_path = data.get("checkpoint_path")

        preview = review_summary(data)
        preview["human_decision"] = data.get("human_decision")
        preview["resume_from"] = (data.get("resume_context") or {}).get("resume_from")
        base.update(
            {
                "ok": True,
                "checkpoint_path": resolved_path,
                "preview": preview,
                "message": (
                    f"preview ready for {preview.get('checkpoint_id')} "
                    f"case_ref={preview.get('case_ref')} status={preview.get('status')}"
                ),
            }
        )
        return base
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        base["message"] = str(exc)
        return base


def _format_text(result: Dict[str, Any]) -> str:
    lines = [
        f"ok: {result.get('ok')}",
        f"read_only: {result.get('read_only')}",
        f"message: {result.get('message')}",
    ]
    preview = result.get("preview") or {}
    if preview:
        lines.extend(
            [
                f"checkpoint_id: {preview.get('checkpoint_id')}",
                f"case_ref: {preview.get('case_ref')}",
                f"status: {preview.get('status')}",
                f"task_type: {preview.get('task_type')}",
            ]
        )
        actions = preview.get("suggested_actions") or []
        if actions:
            lines.append("suggested_actions:")
            for action in actions:
                lines.append(f"  - {action}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only checkpoint preview for operator decisions (P8-T2c).",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--checkpoint-path",
        help="Path to checkpoint JSON under outbox/ (repo-relative or absolute)",
    )
    target.add_argument(
        "--checkpoint-id",
        help="Checkpoint id (e.g. A-intake-confirmation)",
    )
    parser.add_argument(
        "--case-ref",
        default=None,
        help="Optional case_ref filter when using --checkpoint-id",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional outbox root override",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = preview_checkpoint(
        checkpoint_path=args.checkpoint_path,
        checkpoint_id=args.checkpoint_id,
        case_ref=args.case_ref,
        repo_root=Path(args.repo_root) if args.repo_root else None,
        outbox_root_override=args.outbox_root,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_text(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
