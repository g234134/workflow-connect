"""dispatch_cards — generate Cursor instruction cards from dispatch plan + ticket FRAME.



Read-only on ticket state files. When plan and ticket FRAME conflict, FRAME wins.

"""



from __future__ import annotations



import json

import re

import subprocess

import sys

from dataclasses import dataclass, field

from datetime import datetime, timezone

from pathlib import Path

from typing import Any



from dispatch_executor import (  # noqa: E402 — same 04_Workflows package

    _parse_verification_commands,

    _repo_relative_path,

    _section,

)

from ticket_eligibility import (  # noqa: E402 — same 04_Workflows package

    EligibilityContext,

    build_done_ids,

    check_ticket_eligibility,

)



VALID_ELIGIBILITY_GATES = frozenset({"off", "warn", "block"})





_FRAME_FIELD_START_RE = re.compile(
    r"^-\s+([A-Za-z][\w]*):\s*$",
    re.MULTILINE,
)



VALID_ROLES = frozenset({"implementer", "reviewer", "scribe", "orchestrator", "all"})





@dataclass

class DispatchCardInput:

    ticket_id: str

    role: str

    bucket: str

    reason: str

    title: str

    source_path: str

    plan_snapshot: str

    frame_allowed_paths: list[str] = field(default_factory=list)

    frame_blocked_paths: list[str] = field(default_factory=list)

    verification_commands: list[str] = field(default_factory=list)

    plan_commands: list[str] = field(default_factory=list)

    expected_output: str = ""

    parse_warnings: list[str] = field(default_factory=list)

    eligibility_warnings: list[str] = field(default_factory=list)

    eligibility_override: bool = False

    eligibility_warnings: list[str] = field(default_factory=list)

    eligibility_override: bool = False





@dataclass

class DispatchCardOutput:

    ticket_id: str

    role: str

    filepath: str

    markdown_text: str





def load_plan(path: Path) -> dict[str, Any]:

    """Load dispatch_plan JSON from disk."""

    text = path.read_text(encoding="utf-8")

    return json.loads(text)





def _frame_field_block(frame: str, field_name: str) -> str:
    """Return text under a top-level FRAME ``- Field:`` until the next top-level field."""
    start_match = re.search(
        rf"^-\s+{re.escape(field_name)}:\s*$",
        frame,
        re.MULTILINE | re.IGNORECASE,
    )
    if not start_match:
        return ""
    rest = frame[start_match.end() :]
    end_match = _FRAME_FIELD_START_RE.search(rest)
    return rest[: end_match.start()] if end_match else rest


def _parse_frame_list_field(frame: str, field_name: str) -> tuple[list[str], str | None]:
    """Parse bulleted FRAME list (AllowedPaths / BlockedPaths)."""
    block = _frame_field_block(frame, field_name)
    if not block.strip():
        return [], f"[parse_warning] 原始 state 格式無法解析 {field_name}"

    paths: list[str] = []
    for line in block.splitlines():
        m = re.match(r"\s+-\s+(.+)", line)
        if m:
            item = m.group(1).strip()
            if item.startswith("`") and item.endswith("`"):
                item = item[1:-1]
            if item:
                paths.append(item)
    if not paths:
        return [], f"[parse_warning] 原始 state 格式無法解析 {field_name}（區塊為空）"
    return paths, None





def parse_ticket_frame(

    state_path: Path,

    *,

    repo_root: Path,

) -> dict[str, Any]:

    """Read ticket state markdown; extract FRAME paths and verification commands."""

    warnings: list[str] = []

    rel_source = _repo_relative_path(state_path, repo_root)



    try:

        text = state_path.read_text(encoding="utf-8")

    except OSError as exc:

        return {

            "source_path": rel_source,

            "allowed_paths": [],

            "blocked_paths": [],

            "verification_commands": [],

            "title": state_path.stem.replace("_state", ""),

            "parse_warnings": [f"[parse_warning] read_failed:{exc}"],

        }



    frame = _section(text, "FRAME")

    if not frame.strip():

        warnings.append("[parse_warning] 原始 state 格式無法解析 FRAME 區塊")



    allowed, w_allowed = _parse_frame_list_field(frame, "AllowedPaths")

    if w_allowed:

        warnings.append(w_allowed)



    blocked, w_blocked = _parse_frame_list_field(frame, "BlockedPaths")

    if w_blocked:

        warnings.append(w_blocked)



    verification_commands = _parse_verification_commands(frame)



    title_match = re.search(r"-\s+Title:\s*(.+)$", text, re.MULTILINE)

    title = title_match.group(1).strip() if title_match else state_path.stem.replace("_state", "")



    return {

        "source_path": rel_source,

        "allowed_paths": allowed,

        "blocked_paths": blocked,

        "verification_commands": verification_commands,

        "title": title,

        "parse_warnings": warnings,

    }





def _dedupe_commands(commands: list[str]) -> list[str]:

    seen: set[str] = set()

    out: list[str] = []

    for cmd in commands:

        key = cmd.strip()

        if not key or key in seen:

            continue

        seen.add(key)

        out.append(key)

    return out





def _suggestion_index(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:

    return {s["ticket_id"]: s for s in plan.get("suggested_next", [])}





def _runnable_index(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:

    return {t["ticket_id"]: t for t in plan.get("runnable_now", [])}





def select_tickets(

    plan: dict[str, Any],

    *,

    role: str = "all",

    limit: int = 5,

    ticket_id: str | None = None,

) -> tuple[list[dict[str, Any]], list[str]]:

    """Select ticket entries to generate cards for.



    runnable_now is included in full (role-filtered). suggested_next supplements

    with bucket runnable_now/draft and empty blocked_by up to ``limit``.

    """

    warnings: list[str] = []

    suggestions = _suggestion_index(plan)

    runnable = _runnable_index(plan)



    selected_ids: list[str] = []

    selected: list[dict[str, Any]] = []



    def _role_matches(rec_role: str | None) -> bool:

        if role == "all":

            return True

        return rec_role == role



    def _add_entry(tid: str, bucket: str, *, from_runnable: bool) -> None:

        if tid in selected_ids:

            return

        if ticket_id and tid.upper() != ticket_id.upper():

            return



        sug = suggestions.get(tid)

        rec_role = (sug or {}).get("recommended_role") or "orchestrator"

        if not _role_matches(rec_role):

            return



        entry = {

            "ticket_id": tid,

            "bucket": bucket,

            "reason": (sug or {}).get("reason", "runnable_now bucket"),

            "recommended_role": rec_role,

            "commands": (sug or {}).get("commands", []),

            "expected_output": (sug or {}).get("expected_output", ""),

            "source_path": (runnable.get(tid) or sug or {}).get("source_path")

            or f"04_Workflows/tickets/{tid}_state.md",

            "title": (runnable.get(tid) or sug or {}).get("title", tid),

            "from_runnable": from_runnable,

        }

        selected_ids.append(tid)

        selected.append(entry)



    for tid in runnable:

        _add_entry(tid, "runnable_now", from_runnable=True)



    supplement_count = 0

    for sug in plan.get("suggested_next", []):

        if supplement_count >= limit:

            break

        bucket = sug.get("bucket", "")

        if bucket not in {"runnable_now", "draft"}:

            continue

        if sug.get("blocked_by"):

            continue

        tid = sug["ticket_id"]

        if tid in selected_ids:

            continue

        if ticket_id and tid.upper() != ticket_id.upper():

            continue

        rec_role = sug.get("recommended_role") or "orchestrator"

        if not _role_matches(rec_role):

            continue

        selected_ids.append(tid)

        selected.append(

            {

                "ticket_id": tid,

                "bucket": bucket,

                "reason": sug.get("reason", ""),

                "recommended_role": rec_role,

                "commands": sug.get("commands", []),

                "expected_output": sug.get("expected_output", ""),

                "source_path": sug.get("source_path")

                or f"04_Workflows/tickets/{tid}_state.md",

                "title": sug.get("title", tid),

                "from_runnable": False,

            }

        )

        supplement_count += 1



    if ticket_id and not selected:

        warnings.append(f"ticket_not_found_or_role_filtered:{ticket_id}")



    return selected, warnings





def _role_section_title(role: str) -> str:

    mapping = {

        "implementer": "Implementer",

        "reviewer": "Reviewer",

        "scribe": "Scribe",

        "orchestrator": "Orchestrator",

    }

    return mapping.get(role, role.title())





def _expected_output_block(role: str) -> str:

    if role == "implementer":

        return "\n".join(

            [

                "<!-- Implementer: update B_REPORT only -->",

                "- changed_files:",

                "- artifacts:",

                "- verification:",

                "- behavior_notes:",

                "- deferred_items:",

            ]

        )

    if role == "reviewer":

        return "\n".join(

            [

                "<!-- Reviewer: update C_REPORT only -->",

                "- conclusion:",

                "- blocking_issues:",

                "- checks_summary:",

                "- risk_level:",

                "- suggestions:",

            ]

        )

    if role == "scribe":

        return "\n".join(

            [

                "<!-- Scribe: update D_REPORT only -->",

                "- docs_updates:",

                "- progress_entry:",

                "- followup_suggestions:",

            ]

        )

    return "<!-- Orchestrator: update STATE / routing only; do not edit FRAME -->"





def build_card_input(

    entry: dict[str, Any],

    frame_data: dict[str, Any],

    *,

    plan_snapshot: str,

    generated_at: str,

    eligibility_warnings: list[str] | None = None,

    eligibility_override: bool = False,

) -> DispatchCardInput:

    """Combine plan entry with parsed FRAME data."""

    commands = _dedupe_commands(

        list(entry.get("commands", [])) + list(frame_data.get("verification_commands", []))

    )

    return DispatchCardInput(

        ticket_id=entry["ticket_id"],

        role=entry["recommended_role"],

        bucket=entry.get("bucket", "unknown"),

        reason=entry.get("reason", ""),

        title=frame_data.get("title") or entry.get("title", entry["ticket_id"]),

        source_path=frame_data.get("source_path") or entry.get("source_path", ""),

        plan_snapshot=plan_snapshot,

        frame_allowed_paths=list(frame_data.get("allowed_paths", [])),

        frame_blocked_paths=list(frame_data.get("blocked_paths", [])),

        verification_commands=list(frame_data.get("verification_commands", [])),

        plan_commands=commands,

        expected_output=entry.get("expected_output", ""),

        parse_warnings=list(frame_data.get("parse_warnings", [])),

        eligibility_warnings=list(eligibility_warnings or []),

        eligibility_override=eligibility_override,

    )





def render_card_markdown(card: DispatchCardInput, *, generated_at: str) -> str:

    """Render a single *.cursor.md instruction card."""

    role_title = _role_section_title(card.role)

    lines = [

        f"# Cursor Instruction Card · {card.ticket_id} · {card.role}",

        "",

        "## Provenance",

        f"- **source_path**: {card.source_path}",

        f"- **generated_at**: {generated_at}",

        f"- **plan_snapshot**: {card.plan_snapshot}",

    ]

    if card.eligibility_warnings:

        lines.append(f"- **eligibility_warning**: {', '.join(card.eligibility_warnings)}")

    if card.eligibility_override:

        lines.append("- **eligibility_override**: true (Orchestrator force)")

    lines.extend(
        [
            "",
            "## Role",
            "",
            card.role,
            "",
            "## Ticket",
            f"- **ID**: {card.ticket_id}",
            f"- **Title**: {card.title}",
            f"- **State file**: `{card.source_path}`",
            f"- **Bucket**: {card.bucket}",
            f"- **Reason**: {card.reason}",
            "",
            "## Must Read (before any edit)",
            f"1. `{card.source_path}`（FRAME + STATE + 允許區 REPORT）",
            f"2. `.cursor/rules/multi_chat_roles.mdc` §{_role_section_title(card.role)}",
            "3. `AGENTS.md` §初始化校準（接戰時）",
            "",
            "## AllowedPaths",
        ]
    )



    if card.parse_warnings:

        for w in card.parse_warnings:

            if "AllowedPaths" in w or "FRAME" in w:

                lines.append(f"- {w}")

    if card.frame_allowed_paths:

        for p in card.frame_allowed_paths:

            lines.append(f"- `{p}`")

    elif not any("AllowedPaths" in w for w in card.parse_warnings):

        lines.append("- [parse_warning] 原始 state 格式無法解析 AllowedPaths")



    lines.extend(["", "## BlockedPaths"])

    if card.frame_blocked_paths:

        for p in card.frame_blocked_paths:

            lines.append(f"- `{p}`")

    else:

        for w in card.parse_warnings:

            if "BlockedPaths" in w:

                lines.append(f"- {w}")

        if not card.parse_warnings:

            lines.append("- _(none parsed)_")



    lines.extend(["", "## Suggested Commands"])

    if card.plan_commands:

        for cmd in card.plan_commands:

            lines.append(f"- `{cmd}`")

    else:

        lines.append("- _(no commands)_")



    lines.extend(

        [

            "",

            f"## Expected Output ({card.role})",

            _expected_output_block(card.role),

            "",

            "## Handoff",

            "- 完成後更新 ticket STATE 的指定區塊；**勿改 FRAME**",

            "- 若 plan 與 ticket FRAME 衝突，**以 ticket state FRAME 為權威**（AllowedPaths／BlockedPaths）",

            "- plan 僅負責排序與建議，不得覆寫 FRAME 邊界",

        ]

    )

    if card.expected_output:

        lines.append(f"- Plan expected_output hint: {card.expected_output}")



    return "\n".join(lines) + "\n"





def _card_filename(ticket_id: str, role: str) -> str:

    safe_id = ticket_id.replace("/", "_")

    return f"{safe_id}__{role}.cursor.md"





def generate_cards(

    repo_root: Path,

    *,

    plan_path: Path,

    out_dir: Path,

    role: str = "all",

    limit: int = 5,

    ticket_id: str | None = None,

    dry_run: bool = False,

    eligibility_gate: str = "block",

    force_eligibility: bool = False,

) -> dict[str, Any]:

    """Generate instruction cards; return JSON summary."""

    gate = eligibility_gate if eligibility_gate in VALID_ELIGIBILITY_GATES else "block"

    plan = load_plan(plan_path)

    plan_snapshot = _repo_relative_path(plan_path, repo_root)

    generated_at = datetime.now(timezone.utc).isoformat()



    entries, select_warnings = select_tickets(

        plan, role=role, limit=limit, ticket_id=ticket_id

    )



    tickets_dir = repo_root / "04_Workflows" / "tickets"

    cards_generated = 0

    cards_skipped = 0

    all_warnings = list(select_warnings)

    card_records: list[dict[str, Any]] = []

    outputs: list[DispatchCardOutput] = []

    eligibility_blocked: list[dict[str, Any]] = []

    eligibility_overrides: list[str] = []

    done_ids = build_done_ids(repo_root) if gate != "off" else set()



    for entry in entries:

        tid = entry["ticket_id"]

        rec_role = entry.get("recommended_role") or "implementer"

        state_path = tickets_dir / f"{tid}_state.md"

        if not state_path.is_file():

            alt = repo_root / entry.get("source_path", "")

            if alt.is_file():

                state_path = alt

            else:

                cards_skipped += 1

                all_warnings.append(f"state_missing:{tid}")

                card_records.append({"ticket_id": tid, "role": rec_role, "skipped": True})

                continue



        elig_result: dict[str, Any] | None = None

        elig_warnings: list[str] = []

        elig_override = False

        if gate != "off":

            elig_result = check_ticket_eligibility(

                tid,

                repo_root,

                context=EligibilityContext(requested_role=rec_role),

                done_ids=done_ids,

            )

            if elig_result.get("eligible") == "ineligible":

                reasons = elig_result.get("reasons") or []

                reason_text = ",".join(reasons)

                if force_eligibility:

                    elig_override = True

                    eligibility_overrides.append(tid)

                    all_warnings.append(f"eligibility_override:{tid}:{reason_text}")

                elif gate == "block":

                    cards_skipped += 1

                    all_warnings.append(f"eligibility_blocked:{tid}:{reason_text}")

                    eligibility_blocked.append(

                        {

                            "ticket_id": tid,

                            "role": rec_role,

                            "reasons": reasons,

                            "bucket": elig_result.get("bucket"),

                        }

                    )

                    card_records.append(

                        {

                            "ticket_id": tid,

                            "role": rec_role,

                            "skipped": True,

                            "eligibility": elig_result,

                        }

                    )

                    continue

                elif gate == "warn":

                    elig_warnings = list(reasons)

                    warn_tag = f"eligibility_warn:{tid}:{reason_text}"

                    all_warnings.append(warn_tag)



        frame_data = parse_ticket_frame(state_path, repo_root=repo_root)

        all_warnings.extend(frame_data.get("parse_warnings", []))



        card_in = build_card_input(

            entry,

            frame_data,

            plan_snapshot=plan_snapshot,

            generated_at=generated_at,

            eligibility_warnings=elig_warnings,

            eligibility_override=elig_override,

        )

        md = render_card_markdown(card_in, generated_at=generated_at)

        rel_out = _repo_relative_path(out_dir / _card_filename(tid, card_in.role), repo_root)



        outputs.append(

            DispatchCardOutput(

                ticket_id=tid,

                role=card_in.role,

                filepath=rel_out,

                markdown_text=md,

            )

        )

        cards_generated += 1

        record: dict[str, Any] = {

            "ticket_id": tid,

            "role": card_in.role,

            "filepath": rel_out,

            "skipped": False,

            "parse_warnings": card_in.parse_warnings,

        }

        if elig_warnings:

            record["eligibility_warnings"] = elig_warnings

        if elig_override:

            record["eligibility_override"] = True

            if elig_result is not None:

                record["eligibility"] = elig_result

        elif gate == "warn" and elig_result is not None and elig_warnings:

            record["eligibility"] = elig_result

        card_records.append(record)



    if not dry_run and outputs:

        out_dir.mkdir(parents=True, exist_ok=True)

        for out in outputs:

            path = repo_root / out.filepath

            path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(out.markdown_text, encoding="utf-8")



    summary: dict[str, Any] = {

        "ok": True,

        "generated_at": generated_at,

        "plan_snapshot": plan_snapshot,

        "cards_generated": cards_generated,

        "cards_skipped": cards_skipped,

        "warnings": all_warnings,

        "cards": card_records,

        "dry_run": dry_run,

        "role_filter": role,

        "limit": limit,

        "eligibility_gate": gate,

        "eligibility_blocked": eligibility_blocked,

    }

    if eligibility_overrides:

        summary["eligibility_override"] = True

        summary["eligibility_overridden_tickets"] = eligibility_overrides

    return summary





def refresh_dispatch_plan(repo_root: Path) -> dict[str, Any]:

    """Run dispatch_executor to refresh plan artifacts."""

    script = repo_root / "Scripts" / "run_dispatch_executor.py"

    cmd = [

        sys.executable,

        str(script),

        "--json-out",

        "artifacts/control_plane/dispatch_plan.latest.json",

        "--md-out",

        "artifacts/control_plane/dispatch_plan.latest.md",

    ]

    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)

    return {

        "ok": proc.returncode == 0,

        "returncode": proc.returncode,

        "stdout": proc.stdout[-500:] if proc.stdout else "",

        "stderr": proc.stderr[-500:] if proc.stderr else "",

    }





def write_run_summary(summary: dict[str, Any], path: Path) -> None:

    """Optional JSON summary artifact for this card generation run."""

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


