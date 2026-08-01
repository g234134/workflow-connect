#!/usr/bin/env python3
"""Checkpoint Admin CLI v1 (TAB-W4-H1).

List, expire, or requeue pending CP-A / CP-B checkpoints for operator triage.
Repo-local only; does not change driver decision logic or call external services.

Usage:
    python scripts/checkpoint_admin.py list --json
    python scripts/checkpoint_admin.py expire \\
        --checkpoint-id A-intake-confirmation --case-id demo_phase \\
        --reason "SLA exceeded" --json
    python scripts/checkpoint_admin.py requeue \\
        --checkpoint-id B-delivery-confirmation --case-id demo_phase --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hitl.checkpoints_v1 import (  # noqa: E402
    CHECKPOINT_A_ID,
    CHECKPOINT_B_ID,
    append_checkpoint_event,
)
from tabular_automation_state_lib import (  # noqa: E402
    PAUSE_REASON_CHECKPOINT_A,
    PAUSE_REASON_CHECKPOINT_B,
    save_state,
    utc_now_iso,
)
from tabular_checkpoint_sync_lib import (  # noqa: E402
    CHECKPOINT_ID_CP_A,
    CHECKPOINT_ID_CP_B,
    EXPIRED_CP_STATUS,
    cp_type_for_checkpoint_id,
    is_pending_checkpoint_status,
    list_pending_checkpoints_admin,
    normalize_cp_type,
    normalize_list_status,
    read_automation_checkpoint_status,
    resolve_case_dir_for_admin,
    status_field_for_cp_type,
)

_VALID_CHECKPOINT_IDS = frozenset({CHECKPOINT_ID_CP_A, CHECKPOINT_ID_CP_B, CHECKPOINT_A_ID, CHECKPOINT_B_ID})


def _error(action: str, *, error_code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "action": action,
        "error_code": error_code,
        "message": message,
    }


def _resolve_cp_type(
    *,
    checkpoint_id: str | None,
    cp_type: str | None,
) -> tuple[str | None, str | None]:
    if cp_type:
        normalized = normalize_cp_type(cp_type)
        if normalized:
            return normalized, None
        return None, f"unsupported cp_type: {cp_type!r}"

    if checkpoint_id:
        if checkpoint_id not in _VALID_CHECKPOINT_IDS:
            return None, f"unsupported checkpoint_id: {checkpoint_id!r}"
        mapped = cp_type_for_checkpoint_id(checkpoint_id)
        if mapped:
            return mapped, None
        return None, f"cannot map checkpoint_id: {checkpoint_id!r}"

    return None, "checkpoint_id or cp_type is required"


def _find_outbox_checkpoint_file(
    *,
    checkpoint_id: str,
    case_ref: str | None,
    repo_root: Path,
    pending_only: bool,
    allowed_statuses: frozenset[str] | None = None,
) -> tuple[dict[str, Any] | None, Path | None]:
    from hitl.checkpoints_v1 import _iter_checkpoint_files, _load_checkpoint_file, _resolve_outbox_root  # noqa: WPS433

    root = _resolve_outbox_root(repo_root, None)
    matches: list[tuple[str, dict[str, Any], Path]] = []

    for path in _iter_checkpoint_files(root, case_ref=case_ref):
        data = _load_checkpoint_file(path)
        if data is None:
            continue
        if data.get("checkpoint_id") != checkpoint_id:
            continue
        status = str(data.get("status") or "")
        if pending_only and not is_pending_checkpoint_status(status):
            continue
        if allowed_statuses is not None and status not in allowed_statuses:
            continue
        created = str(data.get("created_at", ""))
        matches.append((created, data, path))

    if not matches:
        return None, None

    matches.sort(key=lambda item: item[0])
    _, data, path = matches[-1]
    return data, path


def _write_outbox_checkpoint(path: Path, payload: dict[str, Any], repo_root: Path) -> None:
    from hitl.checkpoints_v1 import _assert_under_outbox, _resolve_outbox_root  # noqa: WPS433

    root = _resolve_outbox_root(repo_root, None)
    _assert_under_outbox(path, root)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_list(*, root: Path) -> dict[str, Any]:
    return list_pending_checkpoints_admin(root=root)


def cmd_expire(
    *,
    root: Path,
    checkpoint_id: str | None,
    cp_type: str | None,
    case_id: str | None,
    case_dir: Path | None,
    reason: str,
) -> dict[str, Any]:
    resolved_cp_type, err = _resolve_cp_type(checkpoint_id=checkpoint_id, cp_type=cp_type)
    if err:
        return _error("expire", error_code="invalid_target", message=err)

    assert resolved_cp_type is not None
    mapped_checkpoint_id = checkpoint_id or (
        CHECKPOINT_ID_CP_A if resolved_cp_type == "cp_a" else CHECKPOINT_ID_CP_B
    )

    resolved_case_dir = resolve_case_dir_for_admin(case_id=case_id, case_dir=case_dir, root=root)
    case_ref = case_id
    if resolved_case_dir is not None:
        row = read_automation_checkpoint_status(resolved_case_dir, resolved_cp_type)
        if row.get("ok"):
            case_ref = str(row.get("case_id") or case_id or "")

    expired_at = utc_now_iso()
    checkpoint_detail: dict[str, Any] = {
        "checkpoint_id": mapped_checkpoint_id,
        "cp_type": resolved_cp_type,
        "status": EXPIRED_CP_STATUS,
        "expire_reason": reason,
        "expired_at": expired_at,
    }

    outbox_data, outbox_path = _find_outbox_checkpoint_file(
        checkpoint_id=mapped_checkpoint_id,
        case_ref=case_ref,
        repo_root=root,
        pending_only=True,
    )
    if outbox_data is not None and outbox_path is not None:
        updated = dict(outbox_data)
        updated["status"] = EXPIRED_CP_STATUS
        updated["expired_at"] = expired_at
        updated["expire_reason"] = reason
        _write_outbox_checkpoint(outbox_path, updated, root)
        append_checkpoint_event(
            {
                "event": "checkpoint_expired",
                "checkpoint_id": mapped_checkpoint_id,
                "case_ref": updated.get("case_ref"),
                "status": EXPIRED_CP_STATUS,
                "expired_at": expired_at,
                "expire_reason": reason,
                "checkpoint_path": updated.get("checkpoint_path"),
            },
            repo_root=root,
        )
        checkpoint_detail.update(
            {
                "case_id": updated.get("case_ref"),
                "created_at": updated.get("created_at"),
                "updated_at": expired_at,
                "checkpoint_path": str(outbox_path.relative_to(root))
                if outbox_path.is_relative_to(root)
                else str(outbox_path),
                "source": "outbox",
            }
        )

    if resolved_case_dir is not None:
        row = read_automation_checkpoint_status(resolved_case_dir, resolved_cp_type)
        if row.get("ok"):
            status = str(row.get("status") or "")
            field = status_field_for_cp_type(resolved_cp_type)
            assert field is not None
            if is_pending_checkpoint_status(status):
                state = dict(row["state"])
                state[field] = EXPIRED_CP_STATUS
                state["last_transition_ts"] = expired_at
                state["pause_reason"] = reason or state.get("pause_reason")
                save_state(resolved_case_dir, state)
                checkpoint_detail.update(
                    {
                        "case_id": row.get("case_id"),
                        "created_at": row.get("updated_at"),
                        "updated_at": expired_at,
                        "pause_reason": state.get("pause_reason"),
                        "source": checkpoint_detail.get("source", "automation_state"),
                        "case_dir": str(resolved_case_dir),
                    }
                )
            elif checkpoint_detail.get("source") != "outbox":
                return _error(
                    "expire",
                    error_code="not_pending",
                    message=(
                        f"{field}={status!r} for case {row.get('case_id')!r}; "
                        "expected pending checkpoint"
                    ),
                )

    if checkpoint_detail.get("source") is None:
        return _error(
            "expire",
            error_code="not_found",
            message=(
                f"no pending checkpoint found for checkpoint_id={mapped_checkpoint_id!r} "
                f"case_id={case_id!r}"
            ),
        )

    return {
        "ok": True,
        "action": "expire",
        "checkpoint": checkpoint_detail,
    }


def cmd_requeue(
    *,
    root: Path,
    checkpoint_id: str | None,
    cp_type: str | None,
    case_id: str | None,
    case_dir: Path | None,
) -> dict[str, Any]:
    resolved_cp_type, err = _resolve_cp_type(checkpoint_id=checkpoint_id, cp_type=cp_type)
    if err:
        return _error("requeue", error_code="invalid_target", message=err)

    assert resolved_cp_type is not None
    mapped_checkpoint_id = checkpoint_id or (
        CHECKPOINT_ID_CP_A if resolved_cp_type == "cp_a" else CHECKPOINT_ID_CP_B
    )

    resolved_case_dir = resolve_case_dir_for_admin(case_id=case_id, case_dir=case_dir, root=root)
    case_ref = case_id
    if resolved_case_dir is not None:
        row = read_automation_checkpoint_status(resolved_case_dir, resolved_cp_type)
        if row.get("ok"):
            case_ref = str(row.get("case_id") or case_id or "")

    restored_at = utc_now_iso()
    pause_reason = (
        PAUSE_REASON_CHECKPOINT_A if resolved_cp_type == "cp_a" else PAUSE_REASON_CHECKPOINT_B
    )
    checkpoint_detail: dict[str, Any] = {
        "checkpoint_id": mapped_checkpoint_id,
        "cp_type": resolved_cp_type,
        "status": "awaiting_decision",
        "requeued_at": restored_at,
    }

    outbox_data, outbox_path = _find_outbox_checkpoint_file(
        checkpoint_id=mapped_checkpoint_id,
        case_ref=case_ref,
        repo_root=root,
        pending_only=False,
        allowed_statuses=frozenset({EXPIRED_CP_STATUS}),
    )
    if outbox_data is not None and outbox_path is not None:
        updated = dict(outbox_data)
        updated["status"] = "awaiting_human"
        updated.pop("expired_at", None)
        updated.pop("expire_reason", None)
        updated["requeued_at"] = restored_at
        _write_outbox_checkpoint(outbox_path, updated, root)
        append_checkpoint_event(
            {
                "event": "checkpoint_requeued",
                "checkpoint_id": mapped_checkpoint_id,
                "case_ref": updated.get("case_ref"),
                "status": "awaiting_human",
                "requeued_at": restored_at,
                "checkpoint_path": updated.get("checkpoint_path"),
            },
            repo_root=root,
        )
        checkpoint_detail.update(
            {
                "case_id": updated.get("case_ref"),
                "created_at": updated.get("created_at"),
                "updated_at": restored_at,
                "pause_reason": pause_reason,
                "checkpoint_path": updated.get("checkpoint_path"),
                "source": "outbox",
            }
        )

    if resolved_case_dir is not None:
        row = read_automation_checkpoint_status(resolved_case_dir, resolved_cp_type)
        if row.get("ok"):
            status = str(row.get("status") or "")
            field = status_field_for_cp_type(resolved_cp_type)
            assert field is not None
            if status == EXPIRED_CP_STATUS:
                state = dict(row["state"])
                state[field] = "pending"
                state["last_transition_ts"] = restored_at
                state["pause_reason"] = pause_reason
                state["requires_hitl_checkpoint"] = True
                state["automation_status"] = "paused"
                save_state(resolved_case_dir, state)
                checkpoint_detail.update(
                    {
                        "case_id": row.get("case_id"),
                        "created_at": row.get("updated_at"),
                        "updated_at": restored_at,
                        "pause_reason": pause_reason,
                        "source": checkpoint_detail.get("source", "automation_state"),
                        "case_dir": str(resolved_case_dir),
                    }
                )
            elif checkpoint_detail.get("source") != "outbox":
                return _error(
                    "requeue",
                    error_code="not_requeueable",
                    message=(
                        f"{field}={status!r} for case {row.get('case_id')!r}; "
                        f"expected {EXPIRED_CP_STATUS!r}"
                    ),
                )

    if checkpoint_detail.get("source") is None:
        return _error(
            "requeue",
            error_code="not_found",
            message=(
                f"no expired checkpoint found for checkpoint_id={mapped_checkpoint_id!r} "
                f"case_id={case_id!r}"
            ),
        )

    checkpoint_detail["status"] = normalize_list_status(
        "awaiting_human" if checkpoint_detail.get("source") == "outbox" else "pending"
    )
    return {
        "ok": True,
        "action": "requeue",
        "checkpoint": checkpoint_detail,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Checkpoint Admin CLI (TAB-W4-H1).")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repo root (default: parent of scripts/)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List pending CP-A/CP-B checkpoints")
    list_p.add_argument("--json", action="store_true", help="Emit structured JSON")

    expire_p = sub.add_parser("expire", help="Mark a pending checkpoint as expired")
    expire_p.add_argument("--json", action="store_true", help="Emit structured JSON")
    expire_p.add_argument("--checkpoint-id", help="Checkpoint id (A-intake-confirmation / B-delivery-confirmation)")
    expire_p.add_argument("--cp-type", choices=("cp_a", "cp_b"), help="Optional CP type helper")
    expire_p.add_argument("--case-id", help="Case id for disambiguation")
    expire_p.add_argument("--case-dir", type=Path, help="Explicit case directory")
    expire_p.add_argument("--reason", required=True, help="Human-readable expire reason")

    requeue_p = sub.add_parser("requeue", help="Restore an expired checkpoint to pending")
    requeue_p.add_argument("--json", action="store_true", help="Emit structured JSON")
    requeue_p.add_argument("--checkpoint-id", help="Checkpoint id")
    requeue_p.add_argument("--cp-type", choices=("cp_a", "cp_b"), help="Optional CP type helper")
    requeue_p.add_argument("--case-id", help="Case id for disambiguation")
    requeue_p.add_argument("--case-dir", type=Path, help="Explicit case directory")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = args.repo_root.resolve()

    if args.command == "list":
        result = cmd_list(root=root)
    elif args.command == "expire":
        if not args.checkpoint_id and not args.cp_type:
            result = _error(
                "expire",
                error_code="missing_target",
                message="expire requires --checkpoint-id and/or --cp-type",
            )
        else:
            result = cmd_expire(
                root=root,
                checkpoint_id=args.checkpoint_id,
                cp_type=args.cp_type,
                case_id=args.case_id,
                case_dir=args.case_dir,
                reason=args.reason,
            )
    elif args.command == "requeue":
        if not args.checkpoint_id and not args.cp_type:
            result = _error(
                "requeue",
                error_code="missing_target",
                message="requeue requires --checkpoint-id and/or --cp-type",
            )
        else:
            result = cmd_requeue(
                root=root,
                checkpoint_id=args.checkpoint_id,
                cp_type=args.cp_type,
                case_id=args.case_id,
                case_dir=args.case_dir,
            )
    else:
        result = _error("unknown", error_code="unknown_command", message=f"unknown command: {args.command}")

    if args.json or args.command != "list":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result.get("ok"):
        items = result.get("items") or []
        if not items:
            print("No pending checkpoints.")
        else:
            print(f"Pending checkpoints ({len(items)}):")
            for row in items:
                print(
                    "  - case_id={case_id} checkpoint_id={checkpoint_id} cp_type={cp_type} "
                    "status={status} pause_reason={pause_reason}".format(**row)
                )
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
