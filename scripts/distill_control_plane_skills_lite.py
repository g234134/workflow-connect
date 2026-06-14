#!/usr/bin/env python3
"""Skill distillation lite CLI (WC-T6).

Scans dispatch cards, ticket comms JSONL, and optional handoff reports locally.
v0.1: heuristic pattern extraction only — no network, no LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]

# T6 source path_id (cp.*) → WC-T5 canonical path_id (wc.m2.*).
# See docs/wave_c/WC_T6_skill_distillation_lite.md § Path id mapping to WC-T5.
PATH_ID_MAPPING: dict[str, str] = {
    "cp.dispatch_cards.eligibility_gate": "wc.m2.dispatch.eligibility_gate_warn",
    "cp.dispatch_cards.generate": "wc.m2.dispatch.cards_generate",
    "cp.ticket_comms.state_transition": "wc.m2.comms.state_transition",
    "cp.ticket_comms.emit": "wc.m2.comms.state_transition",
}

_SOURCE_TYPE_CARD = "card"
_SOURCE_TYPE_COMMS = "comms"
_SOURCE_TYPE_REPORT = "report"

_TICKET_ID_RE = re.compile(r"# Cursor Instruction Card · ([^·]+) ·")
_VERIFICATION_RE = re.compile(r"VerificationCommands|python -m unittest|python scripts/")
_ELIGIBILITY_RE = re.compile(r"eligibility_gate|eligibility_warning|eligibility_override", re.I)


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _ref(*, ticket_id: str | None = None, path: str | None = None) -> dict[str, str]:
    out: dict[str, str] = {}
    if ticket_id:
        out["ticket_id"] = ticket_id
    if path:
        out["path"] = path
    return out


def _canonical_path_id(path_id: str) -> str:
    return PATH_ID_MAPPING.get(path_id, path_id)


def _with_canonical_path_id(item: dict[str, Any]) -> dict[str, Any]:
    path_id = str(item.get("path_id") or "")
    item["canonical_path_id"] = _canonical_path_id(path_id)
    return item


def _scan_cards(cards_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    patterns: list[dict[str, Any]] = []
    anti_patterns: list[dict[str, Any]] = []
    source_refs: list[dict[str, str]] = []

    if not cards_dir.is_dir():
        return patterns, anti_patterns, source_refs

    for card_path in sorted(cards_dir.glob("*.cursor.md")):
        text = card_path.read_text(encoding="utf-8")
        rel = _repo_relative(card_path)
        match = _TICKET_ID_RE.search(text)
        ticket_id = match.group(1).strip() if match else card_path.stem.split("__")[0]
        ref = _ref(ticket_id=ticket_id, path=rel)
        source_refs.append(ref)

        has_verification = bool(_VERIFICATION_RE.search(text))
        has_eligibility = bool(_ELIGIBILITY_RE.search(text))

        if has_verification and has_eligibility:
            patterns.append(
                {
                    "id": f"pat-eligibility-verification-{ticket_id.lower()}",
                    "title": "Dispatch card with eligibility gate and verification",
                    "description": (
                        f"Card for {ticket_id} documents eligibility discipline and "
                        "repeatable VerificationCommands for handoff."
                    ),
                    "source_type": _SOURCE_TYPE_CARD,
                    "path_id": "cp.dispatch_cards.eligibility_gate",
                    "recommendation": (
                        "Keep --eligibility-gate block on Multi-Chat open; mirror "
                        "VerificationCommands from FRAME in the generated card."
                    ),
                    "source_refs": [ref],
                }
            )
        elif has_verification:
            patterns.append(
                {
                    "id": f"pat-verification-{ticket_id.lower()}",
                    "title": "Dispatch card includes verification commands",
                    "description": (
                        f"Card for {ticket_id} lists unittest or script commands "
                        "implementer can re-run before handoff."
                    ),
                    "source_type": _SOURCE_TYPE_CARD,
                    "path_id": "cp.dispatch_cards.generate",
                    "recommendation": (
                        "Always embed VerificationCommands in FRAME so cards "
                        "inherit a concrete acceptance command."
                    ),
                    "source_refs": [ref],
                }
            )
        else:
            anti_patterns.append(
                {
                    "id": f"anti-no-verification-{ticket_id.lower()}",
                    "title": "Dispatch card missing verification commands",
                    "description": (
                        f"Card for {ticket_id} has no VerificationCommands or "
                        "unittest/script references — risky for blind handoff."
                    ),
                    "source_type": _SOURCE_TYPE_CARD,
                    "path_id": "cp.dispatch_cards.generate",
                    "recommendation": (
                        "Add VerificationCommands to ticket FRAME before generating cards; "
                        "reject cards without a runnable check."
                    ),
                    "source_refs": [ref],
                }
            )

    return patterns, anti_patterns, source_refs


def _scan_comms(comms_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    patterns: list[dict[str, Any]] = []
    anti_patterns: list[dict[str, Any]] = []
    source_refs: list[dict[str, str]] = []

    if not comms_path.is_file():
        return patterns, anti_patterns, source_refs

    rel = _repo_relative(comms_path)
    for line_no, line in enumerate(comms_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        ticket_id = str(record.get("ticket_id") or "UNKNOWN")
        ref = _ref(ticket_id=ticket_id, path=f"{rel}:{line_no}")
        source_refs.append(ref)

        diff = record.get("state_diff") or {}
        changed = diff.get("changed_fields") or []
        before = diff.get("before") or {}
        after = diff.get("after") or {}

        if "overall_status" in changed and "current_owner" in changed:
            patterns.append(
                {
                    "id": f"pat-comms-handoff-{ticket_id.lower()}",
                    "title": "Comms records owner and status transition",
                    "description": (
                        f"Comms line for {ticket_id} captures overall_status and "
                        "current_owner change — suitable for Multi-Chat handoff audit."
                    ),
                    "source_type": _SOURCE_TYPE_COMMS,
                    "path_id": "cp.ticket_comms.state_transition",
                    "recommendation": (
                        "Emit comms on every owner/status change; keep JSONL append-only "
                        "under artifacts/e2e/<ticket_id>/comms/."
                    ),
                    "source_refs": [ref],
                }
            )

        prev_status = str(before.get("overall_status") or "")
        next_status = str(after.get("overall_status") or "")
        if prev_status == "in_progress" and next_status == "done":
            anti_patterns.append(
                {
                    "id": f"anti-skip-review-{ticket_id.lower()}",
                    "title": "Skipped review gate in STATE transition",
                    "description": (
                        f"Comms for {ticket_id} shows in_progress → done without "
                        "an intermediate review state."
                    ),
                    "source_type": _SOURCE_TYPE_COMMS,
                    "path_id": "cp.ticket_comms.state_transition",
                    "recommendation": (
                        "Route through review (overall_status=review, current_owner=reviewer) "
                        "before done or ready_for_order."
                    ),
                    "source_refs": [ref],
                }
            )
        elif record.get("schema_version") == "ticket_comms_v0.1" and not changed:
            anti_patterns.append(
                {
                    "id": f"anti-empty-diff-{ticket_id.lower()}",
                    "title": "Comms payload with empty state diff",
                    "description": (
                        f"Comms record for {ticket_id} has no changed_fields — "
                        "likely duplicate emit or snapshot mismatch."
                    ),
                    "source_type": _SOURCE_TYPE_COMMS,
                    "path_id": "cp.ticket_comms.emit",
                    "recommendation": (
                        "Compare distinct before/after snapshots; skip emit when diff is empty."
                    ),
                    "source_refs": [ref],
                }
            )

    return patterns, anti_patterns, source_refs


def _scan_reports(reports_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    patterns: list[dict[str, Any]] = []
    anti_patterns: list[dict[str, Any]] = []
    source_refs: list[dict[str, str]] = []

    if not reports_dir.is_dir():
        return patterns, anti_patterns, source_refs

    for report_path in sorted(reports_dir.glob("*.md")):
        text = report_path.read_text(encoding="utf-8")
        rel = _repo_relative(report_path)
        ticket_match = re.search(r"# TICKET STATE · ([^·]+) ·", text)
        ticket_id = ticket_match.group(1).strip() if ticket_match else report_path.stem
        ref = _ref(ticket_id=ticket_id, path=rel)
        source_refs.append(ref)

        b_report = re.search(r"## B_REPORT\s+(.*?)(?=\n## |\Z)", text, re.DOTALL)
        if not b_report:
            continue
        body = b_report.group(1)
        has_verification = "verification:" in body.lower()
        has_changed = "changed_files:" in body.lower()

        if has_verification and has_changed:
            patterns.append(
                {
                    "id": f"pat-b-report-{ticket_id.lower()}",
                    "title": "B_REPORT documents changes and verification",
                    "description": (
                        f"B_REPORT for {ticket_id} lists changed_files and verification "
                        "evidence — good Scribe / Reviewer input."
                    ),
                    "source_type": _SOURCE_TYPE_REPORT,
                    "path_id": "cp.ticket_state.b_report",
                    "recommendation": (
                        "Fill B_REPORT verification with exact commands and ok/fail semantics "
                        "before moving STATE to review."
                    ),
                    "source_refs": [ref],
                }
            )
        elif not has_verification:
            anti_patterns.append(
                {
                    "id": f"anti-b-report-no-verify-{ticket_id.lower()}",
                    "title": "B_REPORT missing verification block",
                    "description": (
                        f"B_REPORT for {ticket_id} lacks verification commands — "
                        "Reviewer cannot confirm acceptance."
                    ),
                    "source_type": _SOURCE_TYPE_REPORT,
                    "path_id": "cp.ticket_state.b_report",
                    "recommendation": (
                        "Add verification bullet with command and key result before handoff."
                    ),
                    "source_refs": [ref],
                }
            )

    return patterns, anti_patterns, source_refs


def distill_skills(
    *,
    cards_dir: Path | None = None,
    comms_jsonl: Path | None = None,
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    anti_patterns: list[dict[str, Any]] = []
    source_refs: list[dict[str, str]] = []

    if cards_dir:
        p, a, r = _scan_cards(cards_dir)
        patterns.extend(p)
        anti_patterns.extend(a)
        source_refs.extend(r)

    if comms_jsonl:
        p, a, r = _scan_comms(comms_jsonl)
        patterns.extend(p)
        anti_patterns.extend(a)
        source_refs.extend(r)

    if reports_dir:
        p, a, r = _scan_reports(reports_dir)
        patterns.extend(p)
        anti_patterns.extend(a)
        source_refs.extend(r)

    patterns = [_with_canonical_path_id(p) for p in patterns]
    anti_patterns = [_with_canonical_path_id(a) for a in anti_patterns]

    ok = bool(patterns) and bool(anti_patterns)
    message = "distillation_complete" if ok else "insufficient_signals"
    return {
        "ok": ok,
        "message": message,
        "patterns": patterns,
        "anti_patterns": anti_patterns,
        "source_refs": source_refs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Distill Control Plane skill patterns from cards/comms/reports (WC-T6 v0.1).",
    )
    parser.add_argument(
        "--cards-dir",
        type=Path,
        help="Directory of *.cursor.md dispatch instruction cards",
    )
    parser.add_argument(
        "--comms-jsonl",
        type=Path,
        help="Path to ticket_comms.jsonl (one JSON object per line)",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        help="Directory of *_state.md or handoff markdown with B_REPORT sections",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional output file (default: stdout only)",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    if not any([args.cards_dir, args.comms_jsonl, args.reports_dir]):
        parser.error("At least one of --cards-dir, --comms-jsonl, --reports-dir is required")

    result = distill_skills(
        cards_dir=args.cards_dir,
        comms_jsonl=args.comms_jsonl,
        reports_dir=args.reports_dir,
    )

    indent = 2 if args.pretty else None
    payload = json.dumps(result, ensure_ascii=False, indent=indent) + "\n"

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")

    sys.stdout.write(payload)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
