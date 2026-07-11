"""dispatch_executor — read-only control-plane dispatch suggestion (W-next MVP).

Scans Multi-Chat ticket state markdown, optional run queue / latest status,
and emits structured JSON + Markdown dispatch plans. Does not call external
models, open chats, or mutate runtime state.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TICKET_ID_RE = re.compile(r"^# TICKET STATE · ([^·]+) ·", re.MULTILINE)
STATE_FIELD_RE = re.compile(r"^-\s+([\w_]+):\s*(.+?)\s*$", re.MULTILINE)
ROLE_STATUS_RE = re.compile(r"^\s+-\s+(\w+):\s*(.+?)\s*$", re.MULTILINE)
VERIFICATION_CMD_RE = re.compile(
    r"^\s*-\s*`([^`]+)`",
    re.MULTILINE,
)

IMPLEMENTER_KEYWORDS = (
    "implement",
    "resume",
    "wire",
    "test",
    "施工",
    "接線",
    "開工",
    "soak",
    "preflight",
    "infra_unblock",
)
REVIEWER_WAIT_KEYWORDS = (
    "等待 reviewer",
    "wait for reviewer",
    "reviewer acceptance",
    "reviewer 驗收",
    "reviewer 第二輪",
    "reviewer 讀",
)
DONE_STATUSES = frozenset({"done", "accepted", "accepted_with_gaps"})
BLOCKED_STATUSES = frozenset({"blocked"})


@dataclass
class TicketRecord:
    ticket_id: str
    title: str
    overall_status: str
    implementation_status: str | None = None
    current_owner: str | None = None
    next_action: str | None = None
    blockers: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status_by_role: dict[str, str] = field(default_factory=dict)
    source_path: str = ""
    confidence: dict[str, str] = field(default_factory=dict)
    verification_commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"\n##\s+", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def _extract_title(text: str, ticket_id: str) -> tuple[str, str]:
    header = TICKET_ID_RE.search(text)
    if header:
        return header.group(1).strip(), "high"
    return ticket_id, "low"


def _parse_frame_dependencies(frame: str) -> tuple[list[str], str]:
    deps: list[str] = []
    confidence = "medium"
    dep_block = re.search(
        r"-\s+Dependencies:\s*\n((?:\s+-\s+.+\n?)*)",
        frame,
        re.IGNORECASE,
    )
    if not dep_block:
        single = re.search(r"-\s+Dependencies:\s*(.+)$", frame, re.MULTILINE | re.IGNORECASE)
        if single:
            raw = single.group(1).strip()
            if raw.lower() not in {"无", "無", "none", "-", "n/a"}:
                deps = _tokenize_dependencies(raw)
        return deps, "low" if deps else "medium"

    for line in dep_block.group(1).splitlines():
        m = re.match(r"\s+-\s+(.+)", line)
        if m:
            deps.extend(_tokenize_dependencies(m.group(1)))
    return deps, "high" if deps else "medium"


def _tokenize_dependencies(raw: str) -> list[str]:
    tokens: list[str] = []
    for part in re.split(r"[,;、]", raw):
        part = part.strip()
        if not part or part.lower() in {"无", "無", "none", "n/a"}:
            continue
        for ticket in re.findall(r"[A-Z]\d?-[A-Z]\d+|[A-Z]+-[A-Z]\d+|[A-Z]+\d?-T\d+", part):
            if ticket not in tokens:
                tokens.append(ticket)
    return tokens


def _parse_verification_commands(frame: str) -> list[str]:
    block = re.search(
        r"-\s+VerificationCommands:\s*\n((?:\s+-\s+`[^`]+`.*\n?)*)",
        frame,
        re.IGNORECASE,
    )
    if not block:
        return []
    return [m.group(1).strip() for m in VERIFICATION_CMD_RE.finditer(block.group(1))]


def _repo_relative_path(path: Path | str, repo_root: Path | None = None) -> str:
    """Return repo-relative posix path; avoid absolute disk paths in artifacts."""
    p = Path(path)
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    try:
        return p.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        raw = str(path).replace("\\", "/")
        marker = "04_Workflows/"
        if marker in raw:
            return raw[raw.index(marker) :]
        return raw.lstrip("/")


def parse_ticket_state_markdown(
    text: str,
    source_path: str | Path = "",
    *,
    repo_root: Path | None = None,
) -> TicketRecord:
    """Parse a ticket state markdown file into a TicketRecord."""
    source = _repo_relative_path(source_path, repo_root) if source_path else ""
    ticket_id, id_conf = _extract_title(text, Path(source).stem.replace("_state", ""))

    title_match = re.search(r"-\s+Title:\s*(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ticket_id
    title_conf = "high" if title_match else "low"

    frame = _section(text, "FRAME")
    state = _section(text, "STATE")

    fields: dict[str, str] = {}
    for m in STATE_FIELD_RE.finditer(state):
        key, val = m.group(1), m.group(2).strip()
        if key not in fields:
            fields[key] = val

    status_by_role: dict[str, str] = {}
    role_block = re.search(
        r"-\s+status_by_role:\s*\n((?:\s+-\s+\w+:.+\n?)*)",
        state,
        re.IGNORECASE,
    )
    if role_block:
        for m in ROLE_STATUS_RE.finditer(role_block.group(1)):
            status_by_role[m.group(1).strip()] = m.group(2).strip()

    deps, dep_conf = _parse_frame_dependencies(frame)
    verification_commands = _parse_verification_commands(frame)

    overall = (fields.get("overall_status") or "unknown").lower().strip()
    impl = fields.get("implementation_status", "").lower().strip() or None
    owner = fields.get("current_owner", "").lower().strip() or None
    next_action = fields.get("next_action") or None

    confidence: dict[str, str] = {
        "ticket_id": id_conf,
        "title": title_conf,
        "overall_status": "high" if "overall_status" in fields else "low",
        "dependencies": dep_conf,
    }
    if impl:
        confidence["implementation_status"] = "high"
    if owner:
        confidence["current_owner"] = "high"
    if next_action:
        confidence["next_action"] = "high"

    return TicketRecord(
        ticket_id=ticket_id,
        title=title,
        overall_status=overall,
        implementation_status=impl,
        current_owner=owner,
        next_action=next_action,
        dependencies=deps,
        status_by_role=status_by_role,
        source_path=source,
        confidence=confidence,
        verification_commands=verification_commands,
    )


def scan_ticket_files(
    tickets_dir: Path,
    *,
    ticket_filter: str | None = None,
) -> tuple[list[TicketRecord], list[str]]:
    """Scan ``*_state.md`` files; return records and warnings."""
    warnings: list[str] = []
    records: list[TicketRecord] = []

    if not tickets_dir.is_dir():
        warnings.append(f"tickets_dir_missing:{tickets_dir.as_posix()}")
        return records, warnings

    paths = sorted(tickets_dir.glob("*_state.md"))
    if ticket_filter:
        needle = ticket_filter.upper()
        paths = [p for p in paths if needle in p.stem.upper()]

    if not paths:
        warnings.append("no_ticket_state_files_matched")
        return records, warnings

    for path in paths:
        if path.name.startswith("_") or "/_templates/" in path.as_posix():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.append(f"read_failed:{path.name}:{exc}")
            continue
        repo_root = tickets_dir.parent.parent
        records.append(parse_ticket_state_markdown(text, path, repo_root=repo_root))

    return records, warnings


def _normalize_done_set(tickets: list[TicketRecord]) -> set[str]:
    done: set[str] = set()
    for t in tickets:
        if t.overall_status in DONE_STATUSES:
            done.add(t.ticket_id.upper())
    return done


def _unresolved_dependencies(ticket: TicketRecord, done_ids: set[str]) -> list[str]:
    unresolved: list[str] = []
    for dep in ticket.dependencies:
        if dep.upper() not in done_ids:
            unresolved.append(dep)
    return unresolved


def _next_action_lower(ticket: TicketRecord) -> str:
    return (ticket.next_action or "").lower()


def _is_waiting_reviewer(ticket: TicketRecord) -> bool:
    na = _next_action_lower(ticket)
    if any(k in na for k in REVIEWER_WAIT_KEYWORDS):
        return True
    if ticket.current_owner == "reviewer":
        return True
    if ticket.implementation_status == "in_review":
        return True
    if ticket.overall_status == "review":
        return True
    return False


def _is_infra_unblock(ticket: TicketRecord) -> bool:
    return "infra_unblock" in _next_action_lower(ticket)


def classify_ticket(
    ticket: TicketRecord,
    *,
    done_ids: set[str],
) -> str:
    """Return bucket: done | blocked | in_review | runnable_now | draft."""
    if ticket.overall_status in DONE_STATUSES:
        if ticket.current_owner == "scribe" and "scribe" in (ticket.next_action or "").lower():
            return "done"
        if ticket.status_by_role.get("scribe") == "pending" and ticket.current_owner == "scribe":
            return "done"
        return "done"

    unresolved = _unresolved_dependencies(ticket, done_ids)
    if unresolved:
        ticket.blockers = list(dict.fromkeys(ticket.blockers + [f"dependency:{d}" for d in unresolved]))

    if ticket.overall_status in BLOCKED_STATUSES and not _is_infra_unblock(ticket):
        ticket.blockers.append("overall_status:blocked")
        return "blocked"

    if unresolved:
        return "blocked"

    if _is_waiting_reviewer(ticket):
        return "in_review"

    if ticket.overall_status == "draft":
        return "draft"

    if ticket.overall_status == "in_progress":
        if _is_waiting_reviewer(ticket):
            return "in_review"
        return "runnable_now"

    if ticket.overall_status in {"scribe", "review"}:
        return "in_review" if ticket.overall_status == "review" else "runnable_now"

    return "runnable_now"


def recommend_role(ticket: TicketRecord, bucket: str) -> tuple[str | None, str]:
    """Return (recommended_role, reason)."""
    na = _next_action_lower(ticket)

    if bucket == "blocked":
        if _is_infra_unblock(ticket):
            return "implementer", "next_action requests infra_unblock despite blocked overall_status"
        return None, "ticket is blocked"

    if bucket == "done":
        if ticket.current_owner == "scribe" or "scribe" in na or "progress" in na:
            return "scribe", "done ticket pending scribe progress append"
        return "orchestrator", "ticket done; orchestrator may close or archive"

    if bucket == "in_review" or _is_waiting_reviewer(ticket):
        return "reviewer", "implementation or acceptance awaiting reviewer"

    if any(k in na for k in ("等待 reviewer", "reviewer acceptance", "wait for reviewer")):
        return "reviewer", "next_action indicates reviewer gate"

    if bucket == "draft":
        if "assign" in na or "implementer" in na:
            return "implementer", "draft ticket assigned to implementer"
        return "orchestrator", "draft ticket needs orchestrator framing or assign"

    if ticket.overall_status == "in_progress":
        if any(k in na for k in IMPLEMENTER_KEYWORDS):
            return "implementer", "in_progress with implement/resume/wire/test next_action"
        if ticket.current_owner == "implementer":
            return "implementer", "current_owner is implementer"

    if ticket.status_by_role.get("implementer") in {"pending", "in_progress"}:
        if ticket.status_by_role.get("orchestrator") == "done":
            return "implementer", "implementer pending after orchestrator done"

    if ticket.current_owner:
        return ticket.current_owner, f"current_owner is {ticket.current_owner}"

    return "orchestrator", "fallback to orchestrator triage"


def _role_commands(ticket: TicketRecord, role: str | None) -> list[str]:
    cmds: list[str] = []
    state_path = ticket.source_path or f"04_Workflows/tickets/{ticket.ticket_id}_state.md"
    if role == "implementer":
        cmds.append(f"Open Implementer chat; read {state_path}; execute next_action")
    elif role == "reviewer":
        cmds.append(f"Open Reviewer chat; read {state_path}; write C_REPORT")
    elif role == "scribe":
        cmds.append(
            "python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT"
        )
        cmds.append(f"Open Scribe chat; read {state_path}; write D_REPORT + Progress append")
    elif role == "orchestrator":
        cmds.append(f"Open Orchestrator chat; read {state_path}; update STATE")
    if ticket.verification_commands:
        cmds.extend(ticket.verification_commands[:3])
    return cmds


def _expected_output(role: str | None, ticket: TicketRecord) -> str:
    if role == "implementer":
        return "B_REPORT updated; STATE overall_status in_progress"
    if role == "reviewer":
        return "C_REPORT with conclusion accepted|needs_changes|rejected"
    if role == "scribe":
        return "D_REPORT + suggested Progress entry"
    if role == "orchestrator":
        return "FRAME/STATE updated; ticket routed to next role"
    return "manual triage"


def build_parallel_groups(
    suggestions: list[dict[str, Any]],
) -> list[list[str]]:
    """Group runnable suggestions that can run in parallel."""
    parallel_candidates = [
        s for s in suggestions
        if s.get("can_parallelize") and s.get("recommended_role") in {"implementer", "reviewer", "scribe"}
    ]
    if len(parallel_candidates) < 2:
        return []

    by_role: dict[str, list[str]] = {}
    for s in parallel_candidates:
        role = s["recommended_role"]
        by_role.setdefault(role, []).append(s["ticket_id"])

    groups: list[list[str]] = []
    group_id = 1
    for role, ids in by_role.items():
        if len(ids) >= 2:
            for s in parallel_candidates:
                if s["ticket_id"] in ids:
                    s["parallel_group"] = f"pg-{group_id}-{role}"
            groups.append(ids)
            group_id += 1

    cross_role: list[str] = []
    owners = {s["ticket_id"]: s["recommended_role"] for s in parallel_candidates}
    ids = list(owners.keys())
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            if owners[a] != owners[b]:
                sa = next(x for x in parallel_candidates if x["ticket_id"] == a)
                sb = next(x for x in parallel_candidates if x["ticket_id"] == b)
                if not sa.get("blocked_by") and not sb.get("blocked_by"):
                    if a not in cross_role:
                        cross_role.append(a)
                    if b not in cross_role:
                        cross_role.append(b)
    if len(cross_role) >= 2:
        gid = f"pg-{group_id}-mixed"
        for s in parallel_candidates:
            if s["ticket_id"] in cross_role and not s.get("parallel_group"):
                s["parallel_group"] = gid
        groups.append(cross_role)

    return groups


def load_context_snippets(
    repo_root: Path,
) -> tuple[dict[str, Any], list[str]]:
    """Load optional run queue / latest status snippets."""
    warnings: list[str] = []
    context: dict[str, Any] = {
        "run_queue_paths": [],
        "latest_status_paths": [],
        "run_queue_todo_ids": [],
        "latest_status_wave": None,
    }

    candidates = [
        repo_root / "workflow_v2" / "90_run_queue.md",
        repo_root / "workflow_upgrade" / "90_run_queue.md",
        repo_root / "04_Workflows" / "90_run_queue.md",
    ]
    for path in candidates:
        if path.is_file():
            context["run_queue_paths"].append(_repo_relative_path(path, repo_root))
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                if "|" in line and re.search(r"\|\s*TODO\s*\|", line, re.IGNORECASE):
                    cols = [c.strip() for c in line.split("|")]
                    if cols and cols[0]:
                        context["run_queue_todo_ids"].append(cols[0])
            break
    else:
        warnings.append("run_queue_not_found")

    status_candidates = [
        repo_root / "workflow_v2" / "99_latest_status.md",
        repo_root / "04_Workflows" / "99_latest_status.md",
    ]
    for path in status_candidates:
        if path.is_file():
            context["latest_status_paths"].append(_repo_relative_path(path, repo_root))
            text = path.read_text(encoding="utf-8")
            wave = re.search(r"##\s*1\.\s*当前 Wave|##\s*1\.\s*當前 Wave", text)
            if wave:
                snippet = text[wave.start() : wave.start() + 400]
                context["latest_status_wave"] = snippet.split("---")[0].strip()[:300]
            break
    else:
        warnings.append("latest_status_not_found")

    return context, warnings


def build_dispatch_plan(
    repo_root: Path,
    *,
    ticket_filter: str | None = None,
) -> dict[str, Any]:
    """Build full dispatch plan dict."""
    tickets_dir = repo_root / "04_Workflows" / "tickets"
    tickets, scan_warnings = scan_ticket_files(tickets_dir, ticket_filter=ticket_filter)
    context, ctx_warnings = load_context_snippets(repo_root)
    warnings = scan_warnings + ctx_warnings

    done_ids = _normalize_done_set(tickets)

    buckets: dict[str, list[dict[str, Any]]] = {
        "runnable_now": [],
        "blocked": [],
        "in_review": [],
        "done": [],
        "draft": [],
    }

    suggested_next: list[dict[str, Any]] = []

    for ticket in tickets:
        bucket = classify_ticket(ticket, done_ids=done_ids)
        entry = {
            "ticket_id": ticket.ticket_id,
            "title": ticket.title,
            "overall_status": ticket.overall_status,
            "implementation_status": ticket.implementation_status,
            "current_owner": ticket.current_owner,
            "next_action": ticket.next_action,
            "blockers": ticket.blockers,
            "dependencies": ticket.dependencies,
            "confidence": ticket.confidence,
            "source_path": ticket.source_path,
        }
        buckets.setdefault(bucket, []).append(entry)

        role, reason = recommend_role(ticket, bucket)
        if role is None and bucket == "blocked":
            continue
        if bucket == "done" and role == "orchestrator" and ticket.current_owner != "scribe":
            continue
        if bucket == "draft" and role == "orchestrator" and "assign" not in _next_action_lower(ticket):
            continue

        blocked_by = list(ticket.blockers)
        if bucket == "blocked":
            blocked_by = ticket.blockers or ["classified blocked"]

        can_parallelize = bucket in {"runnable_now", "in_review", "done"} and not blocked_by
        if _is_waiting_reviewer(ticket) and role == "implementer":
            can_parallelize = False

        suggestion = {
            "ticket_id": ticket.ticket_id,
            "recommended_role": role,
            "reason": reason,
            "commands": _role_commands(ticket, role),
            "can_parallelize": can_parallelize,
            "parallel_group": None,
            "blocked_by": blocked_by,
            "expected_output": _expected_output(role, ticket),
            "bucket": bucket,
        }
        suggested_next.append(suggestion)

    parallel_groups = build_parallel_groups(suggested_next)

    coordination_notes: list[str] = []
    if context.get("run_queue_todo_ids"):
        coordination_notes.append(
            f"workflow_v2 run_queue has {len(context['run_queue_todo_ids'])} TODO rows (heuristic parse)"
        )
    if len(buckets["runnable_now"]) >= 2:
        coordination_notes.append(
            f"{len(buckets['runnable_now'])} tickets runnable_now; check parallel_groups before opening chats"
        )
    if buckets["in_review"]:
        coordination_notes.append(
            f"{len(buckets['in_review'])} tickets in_review — prioritize Reviewer chats"
        )
    scribe_pending = [s for s in suggested_next if s["recommended_role"] == "scribe"]
    if scribe_pending:
        coordination_notes.append(
            f"{len(scribe_pending)} done tickets suggest Scribe progress append"
        )

    recommended_chat_count = len({s["recommended_role"] for s in suggested_next if s["recommended_role"]})

    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tickets_scanned": len(tickets),
        "runnable_now": buckets.get("runnable_now", []),
        "blocked": buckets.get("blocked", []),
        "in_review": buckets.get("in_review", []),
        "done": buckets.get("done", []),
        "draft": buckets.get("draft", []),
        "suggested_next": suggested_next,
        "parallel_groups": parallel_groups,
        "coordination_notes": coordination_notes,
        "recommended_chat_count": recommended_chat_count,
        "context_sources": context,
        "warnings": warnings,
    }


def render_dispatch_markdown(plan: dict[str, Any]) -> str:
    """Render human-readable Markdown summary."""
    lines = [
        "# Dispatch Plan (control plane · read-only)",
        "",
        f"- **Generated at**: {plan.get('generated_at', 'unknown')}",
        f"- **Tickets scanned**: {plan.get('tickets_scanned', 0)}",
        f"- **Recommended chats**: {plan.get('recommended_chat_count', 0)}",
        "",
    ]

    if plan.get("warnings"):
        lines.extend(["## Warnings", ""])
        for w in plan["warnings"]:
            lines.append(f"- {w}")
        lines.append("")

    lines.extend(["## Summary", ""])
    for key in ("runnable_now", "in_review", "blocked", "done", "draft"):
        items = plan.get(key, [])
        lines.append(f"- **{key}**: {len(items)}")
    lines.append("")

    if plan.get("parallel_groups"):
        lines.extend(["## Parallel groups", ""])
        for i, group in enumerate(plan["parallel_groups"], 1):
            lines.append(f"{i}. {', '.join(group)}")
        lines.append("")

    lines.extend(["## Suggested next", ""])
    for s in plan.get("suggested_next", []):
        lines.append(f"### {s['ticket_id']} → {s['recommended_role']}")
        lines.append(f"- **Reason**: {s['reason']}")
        lines.append(f"- **Bucket**: {s.get('bucket', '?')}")
        if s.get("blocked_by"):
            lines.append(f"- **Blocked by**: {', '.join(s['blocked_by'])}")
        lines.append(f"- **Parallel**: {s.get('can_parallelize', False)}"
                     + (f" (group {s['parallel_group']})" if s.get("parallel_group") else ""))
        lines.append(f"- **Expected**: {s.get('expected_output', '')}")
        if s.get("commands"):
            lines.append("- **Commands**:")
            for cmd in s["commands"]:
                lines.append(f"  - `{cmd}`")
        lines.append("")

    if plan.get("coordination_notes"):
        lines.extend(["## Coordination notes", ""])
        for note in plan["coordination_notes"]:
            lines.append(f"- {note}")
        lines.append("")

    lines.extend([
        "---",
        "*Heuristic markdown parser · suggestion only · no auto-dispatch*",
    ])
    return "\n".join(lines)


def write_dispatch_artifacts(
    plan: dict[str, Any],
    *,
    json_out: Path | None = None,
    md_out: Path | None = None,
) -> dict[str, str]:
    """Write JSON and/or Markdown artifacts; return paths written."""
    written: dict[str, str] = {}
    if json_out:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written["json"] = json_out.as_posix()
    if md_out:
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(render_dispatch_markdown(plan), encoding="utf-8")
        written["md"] = md_out.as_posix()
    return written
