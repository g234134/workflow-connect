"""_sync_progress_to_master.py — 從 Progress 解析 HQ 工單狀態並寫回 master_status.md"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from gov_paths import get_artifact_path  # type: ignore  # noqa: E402

_PROGRESS_KEY = "agent_work_progress"
_MASTER_KEY = "project_status_master"

_TICKET_HEADER = re.compile(
    r"^##\s+(?:HQ-)?(?P<id>HQ-[A-Z0-9-]+)|^##\s+Rules\s+面板抽測",
    re.MULTILINE,
)
_STATUS_LINE = re.compile(r"^\*\*狀態\*\*：\s*(.+)$", re.MULTILINE)
_TASK_ID_LINE = re.compile(r"^\*\*任務 ID\*\*：\s*`?(HQ-[A-Z0-9-]+)`?", re.MULTILINE)
_PANEL_TIME = re.compile(r"^\*\*抽測時間\*\*：\s*(.+)$", re.MULTILINE)

_DONE_MARKERS = ("done", "completed", "定稿", "pass", "核准")
_PANEL_TICKET = "HQ-P2-RULES-PANEL-VERIFICATION"


@dataclass
class TicketProgress:
    ticket_id: str
    status_raw: str
    completed_at: Optional[str] = None

    @property
    def is_done(self) -> bool:
        low = self.status_raw.lower()
        return any(m in low for m in _DONE_MARKERS) or "pass" in low

    @property
    def master_status(self) -> str:
        return "Completed" if self.is_done else "In Progress"


def _parse_progress_time(text: str) -> Optional[str]:
    """Normalize Progress timestamps to ISO-like local strings."""
    text = text.strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue
    return text


def parse_progress_tickets(progress_text: str) -> Dict[str, TicketProgress]:
    """Extract HQ ticket blocks from Progress markdown."""
    found: Dict[str, TicketProgress] = {}
    sections = re.split(r"(?=^## )", progress_text, flags=re.MULTILINE)

    for block in sections:
        if "Rules 面板抽測" in block:
            tid = _PANEL_TICKET
            status = "Done — PASS" if "✅ PASS" in block or "**總結**：✅ PASS" in block else "Unknown"
            time_m = _PANEL_TIME.search(block)
            completed = _parse_progress_time(time_m.group(1)) if time_m else None
            found[tid] = TicketProgress(tid, status, completed)
            continue

        id_m = _TASK_ID_LINE.search(block)
        if not id_m:
            hdr = re.match(r"^##\s+(HQ-[A-Z0-9-]+)", block)
            if not hdr:
                continue
            tid = hdr.group(1)
        else:
            tid = id_m.group(1)

        status_m = _STATUS_LINE.search(block)
        if not status_m:
            continue
        found[tid] = TicketProgress(tid, status_m.group(1).strip())
    return found


def _read_master_registry(master_text: str) -> Dict[str, Tuple[str, str]]:
    """Parse HQ 工單登錄 table rows: ticket -> (status, completed_at)."""
    registry: Dict[str, Tuple[str, str]] = {}
    in_table = False
    for line in master_text.splitlines():
        if line.startswith("## HQ 工單登錄"):
            in_table = True
            continue
        if in_table and line.startswith("## ") and "工單登錄" not in line:
            break
        if not in_table or not line.startswith("| `HQ-"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        ticket = parts[0].strip("`")
        registry[ticket] = (parts[1], parts[2].strip("`"))
    return registry


def _update_registry_row(
    master_text: str, ticket: str, status: str, completed_at: str, dry_run: bool
) -> str:
    pattern = re.compile(
        rf"(\|\s*`{re.escape(ticket)}`\s*\|\s*)([^|]+)(\|\s*)([^|]*)(\s*\|)",
        re.MULTILINE,
    )
    replacement = rf"\1{status}\3`{completed_at}`\5"
    new_text, n = pattern.subn(replacement, master_text, count=1)
    if n:
        return new_text

    marker = "## HQ 工單登錄"
    idx = master_text.find(marker)
    if idx < 0:
        return master_text
    insert_at = master_text.find("\n", idx)
    row = f"| `{ticket}` | {status} | `{completed_at}` |\n"
    if dry_run:
        return master_text
    return master_text[: insert_at + 1] + row + master_text[insert_at + 1 :]


def _update_ticket_section(
    master_text: str,
    ticket: TicketProgress,
    completed_at: str,
    dry_run: bool,
) -> Tuple[str, bool]:
    if ticket.master_status != "Completed":
        return master_text, False

    status_pat = re.compile(
        rf"(## [^\n]*{re.escape(ticket.ticket_id)}[^\n]*\n(?:.*?\n)*?- \*\*Status\*\*：\*\*)([^*]+)(\*\*)",
        re.DOTALL,
    )
    new_text, n1 = status_pat.subn(r"\1Completed\3", master_text, count=1)

    time_pat = re.compile(
        rf"(## [^\n]*{re.escape(ticket.ticket_id)}[^\n]*\n(?:.*?\n)*?- \*\*Completed at\*\*：)`[^`]*`",
        re.DOTALL,
    )
    new_text, n2 = time_pat.subn(rf"\1`{completed_at}`", new_text, count=1)

    if dry_run:
        return master_text, bool(n1 or n2)
    return new_text, bool(n1 or n2)


def sync_tickets(
    tickets: List[str],
    *,
    dry_run: bool = False,
    default_completed: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    progress_path = get_artifact_path(_PROGRESS_KEY)
    master_path = get_artifact_path(_MASTER_KEY)

    with open(progress_path, "r", encoding="utf-8") as f:
        progress_text = f.read()
    with open(master_path, "r", encoding="utf-8") as f:
        master_text = f.read()

    parsed = parse_progress_tickets(progress_text)
    registry_before = _read_master_registry(master_text)
    changes: List[Dict[str, str]] = []
    master_out = master_text

    defaults = default_completed or {}
    for tid in tickets:
        prog = parsed.get(tid)
        if not prog:
            changes.append({"ticket": tid, "action": "skip", "reason": "not in Progress"})
            continue
        completed_at = prog.completed_at or defaults.get(tid, "")
        before = registry_before.get(tid, ("—", "—"))
        after_status = prog.master_status

        master_out = _update_registry_row(
            master_out, tid, after_status, completed_at or before[1], dry_run
        )
        master_out, _ = _update_ticket_section(master_out, prog, completed_at or before[1], dry_run)

        changes.append(
            {
                "ticket": tid,
                "action": "update",
                "before_status": before[0],
                "after_status": after_status,
                "completed_at": completed_at or before[1],
                "progress_status": prog.status_raw,
            }
        )

    if not dry_run and master_out != master_text:
        with open(master_path, "w", encoding="utf-8") as f:
            f.write(master_out)

    return {
        "ok": True,
        "dry_run": dry_run,
        "progress_path": progress_path,
        "master_path": master_path,
        "changes": changes,
        "master_updated": (not dry_run) and master_out != master_text,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync HQ ticket status from Progress to master_status.md"
    )
    parser.add_argument(
        "--ticket",
        action="append",
        dest="tickets",
        help="Ticket ID (repeatable). Default: P3, P4, panel verification",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report only; do not write")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON result")
    args = parser.parse_args()

    tickets = args.tickets or [
        "HQ-P3-TASK-ROUTING",
        "HQ-P4-OPS-CYCLE",
        "HQ-P2-RULES-PANEL-VERIFICATION",
    ]
    result = sync_tickets(tickets, dry_run=args.dry_run)
    import json

    out = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
    print(out)
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
