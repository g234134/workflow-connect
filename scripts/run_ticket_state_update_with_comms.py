#!/usr/bin/env python3
"""Apply a ticket STATE change and emit comms JSONL (WC-T2 first integration path).

Reads two ticket state markdown snapshots (before / after), parses them with
``dispatch_executor``, and calls ``emit_ticket_comms_on_change`` to append a
``ticket_comms_v0.1`` record under the outbox directory.

Usage:
    python scripts/run_ticket_state_update_with_comms.py \\
        --before tests/fixtures/ticket_comms/wc_t2_before_state.md \\
        --after tests/fixtures/ticket_comms/wc_t2_after_state.md

    python scripts/run_ticket_state_update_with_comms.py \\
        --before path/to/old.md --after path/to/new.md --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from dispatch_executor import parse_ticket_state_markdown  # noqa: E402
from ticket_comms import emit_ticket_comms_on_change, snapshot_from_ticket_record  # noqa: E402


def run_ticket_state_update_with_comms(
    before_path: Path,
    after_path: Path,
    *,
    repo_root: Path | None = None,
    outbox_dir: str | Path = "artifacts/ticket_comms",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Parse before/after STATE markdown and emit comms on detected changes."""
    root = repo_root or _REPO_ROOT
    before_text = before_path.read_text(encoding="utf-8")
    after_text = after_path.read_text(encoding="utf-8")

    state_ref = after_path
    try:
        state_ref = after_path.resolve().relative_to(root.resolve())
    except ValueError:
        pass

    before_rec = parse_ticket_state_markdown(
        before_text,
        state_ref,
        repo_root=root,
    )
    after_rec = parse_ticket_state_markdown(
        after_text,
        state_ref,
        repo_root=root,
    )

    return emit_ticket_comms_on_change(
        snapshot_from_ticket_record(before_rec),
        snapshot_from_ticket_record(after_rec),
        dry_run=dry_run,
        outbox_dir=str(outbox_dir),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Emit ticket comms JSONL for a ticket STATE transition (WC-T2). "
            "Does not write *_state.md — supply before/after snapshots."
        ),
    )
    parser.add_argument(
        "--before",
        required=True,
        type=Path,
        help="Path to ticket state markdown before the change",
    )
    parser.add_argument(
        "--after",
        required=True,
        type=Path,
        help="Path to ticket state markdown after the change",
    )
    parser.add_argument(
        "--outbox-dir",
        default="artifacts/ticket_comms",
        help="Directory for ticket_comms.jsonl (default: artifacts/ticket_comms)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build payload without writing JSONL",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Stdout format (default: json)",
    )
    args = parser.parse_args()

    for label, path in (("before", args.before), ("after", args.after)):
        if not path.is_file():
            err = {"ok": False, "message": f"{label}_file_not_found", "path": str(path)}
            print(json.dumps(err, ensure_ascii=False, indent=2))
            return 2

    result = run_ticket_state_update_with_comms(
        args.before,
        args.after,
        repo_root=_REPO_ROOT,
        outbox_dir=args.outbox_dir,
        dry_run=args.dry_run,
    )

    if args.format == "text":
        lines = [
            "Ticket State Update + Comms (WC-T2)",
            f"ticket_id: {result.get('ticket_id')}",
            f"ok: {result.get('ok')}",
            f"message: {result.get('message')}",
            f"sent: {result.get('sent')}",
        ]
        send_result = result.get("send_result") or {}
        if send_result.get("artifact_path"):
            lines.append(f"artifact_path: {send_result['artifact_path']}")
        print("\n".join(lines))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
