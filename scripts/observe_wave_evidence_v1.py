#!/usr/bin/env python3
"""Wave evidence ingestion observer v1 (W5-T3 · read-only skeleton).

Scans ticket STATE B_REPORT.verification and known smoke artifact logical
paths. Does NOT write DB, mutate smoke runners, or mark human-only run URLs
as verified.

Usage:
    python scripts/observe_wave_evidence_v1.py --wave W5 --format json
    python scripts/observe_wave_evidence_v1.py --ticket-id W5-T5-cross-wave-playbook-index-v1 --format text
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SCHEMA_VERSION = "wave_evidence_observer_v1"
TICKETS_DIR_REL = "04_Workflows/tickets"
OUTBOX_VERIFICATION_REL = "outbox/verification"
PROGRESS_REL = "04_Workflows/00_Agent_Work_Progress.md"

# Wave → ticket filename prefix filter (planning-stage gaps expected).
_WAVE_PREFIX: Dict[str, tuple[str, ...]] = {
    "W1": ("W1-", "W1_"),
    "W2": ("W2-", "W2_"),
    "W3": ("W3-", "W3_"),
    "W4": ("W4-", "W4_"),
    "W5": ("W5-", "W5_"),
}

_PLACEHOLDER_URL_RE = re.compile(
    r"(?i)(placeholder|TODO|TBD|pending|<\s*run[_ ]?url\s*>|example\.com)"
)
_HTTP_URL_RE = re.compile(r"https?://[^\s\)\]\"']+")


def _repo_root(override: Optional[Path] = None) -> Path:
    return (override or _REPO_ROOT).resolve()


def _ticket_id_from_path(path: Path) -> str:
    name = path.name
    if name.endswith("_state.md"):
        return name[: -len("_state.md")]
    return path.stem


def _extract_b_report_verification(text: str) -> Optional[str]:
    """Return B_REPORT verification body text, or None if section missing/empty."""
    m = re.search(
        r"^##\s+B_REPORT\s*$([\s\S]*?)(?=^##\s+|\Z)",
        text,
        flags=re.MULTILINE,
    )
    if not m:
        return None
    body = m.group(1)
    vm = re.search(
        r"(?im)^(?:-\s*)?\*?\*?verification\*?\*?\s*:\s*(.*)$",
        body,
    )
    if not vm:
        # Also accept a ### Verification subsection
        sub = re.search(
            r"(?im)^###\s+verification\s*$([\s\S]*?)(?=^###\s+|^##\s+|\Z)",
            body,
        )
        if not sub:
            return None
        content = sub.group(1).strip()
        return content or None
    # Collect verification bullet and following indented / list lines until next top-level key
    lines = body[vm.start() :].splitlines()
    collected: List[str] = []
    for i, line in enumerate(lines):
        if i == 0:
            collected.append(line)
            continue
        if re.match(r"(?im)^(?:-\s*)?\*?\*?(changed_files|artifacts|behavior_notes|deferred_items)\*?\*?\s*:", line):
            break
        if re.match(r"^##\s+", line):
            break
        collected.append(line)
    content = "\n".join(collected).strip()
    # Strip the leading "verification:" label for emptiness check
    stripped = re.sub(
        r"(?im)^(?:-\s*)?\*?\*?verification\*?\*?\s*:\s*",
        "",
        content,
        count=1,
    ).strip()
    _empty_markers = (
        "<!-- Implementer 填：執行 VerificationCommands 結果 -->",
        "<!-- pending -->",
        "（待填）",
        "TBD",
        "pending",
    )
    if not stripped or stripped in _empty_markers:
        return None
    return stripped


def _scan_ga_run_urls(text: str) -> Dict[str, Any]:
    urls = _HTTP_URL_RE.findall(text)
    if not urls:
        return {
            "present": False,
            "human_only": True,
            "verified": False,
            "urls": [],
            "note": "no_http_url",
        }
    placeholders = [u for u in urls if _PLACEHOLDER_URL_RE.search(u)]
    realish = [u for u in urls if u not in placeholders]
    # Never mark as verified — human-only evidence boundary (AC-4)
    return {
        "present": True,
        "human_only": True,
        "verified": False,
        "urls": urls[:5],
        "placeholder_count": len(placeholders),
        "candidate_count": len(realish),
        "note": "human_only_not_auto_verified",
    }


def _list_ticket_paths(
    root: Path,
    *,
    wave: Optional[str] = None,
    ticket_id: Optional[str] = None,
) -> List[Path]:
    tickets_dir = root / TICKETS_DIR_REL
    if not tickets_dir.is_dir():
        return []
    if ticket_id:
        candidate = tickets_dir / f"{ticket_id}_state.md"
        return [candidate] if candidate.is_file() else []
    prefixes = _WAVE_PREFIX.get(wave or "", ())
    out: List[Path] = []
    for path in sorted(tickets_dir.glob("*_state.md")):
        tid = _ticket_id_from_path(path)
        if prefixes and not tid.startswith(prefixes):
            continue
        out.append(path)
    return out


def _smoke_artifact_status(root: Path) -> List[Dict[str, Any]]:
    """Probe known demo smoke logical paths (honest gaps if missing)."""
    results: List[Dict[str, Any]] = []
    probes = [
        (
            "multi_phase_smoke_run",
            OUTBOX_VERIFICATION_REL + "/demo_phase/multi_phase_smoke_run.json",
        ),
        (
            "multi_case_smoke_run",
            OUTBOX_VERIFICATION_REL + "/multi_case_smoke_run.json",
        ),
    ]
    for evidence_type, rel in probes:
        path = root / rel
        entry: Dict[str, Any] = {
            "evidence_type": evidence_type,
            "path": rel.replace("\\", "/"),
            "exists": path.is_file(),
        }
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                entry["ok"] = bool(data.get("ok")) if isinstance(data, dict) else None
                if isinstance(data, dict) and data.get("run_id") is not None:
                    entry["run_id"] = data.get("run_id")
            except (OSError, json.JSONDecodeError) as exc:
                entry["ok"] = None
                entry["parse_error"] = type(exc).__name__
        results.append(entry)
    return results


def _progress_mentions(root: Path, ticket_ids: Sequence[str]) -> Dict[str, bool]:
    progress = root / PROGRESS_REL
    if not progress.is_file():
        return {tid: False for tid in ticket_ids}
    # Tail-only scan (last ~80KB) to avoid loading huge Progress
    try:
        raw = progress.read_bytes()
        text = raw[-80_000:].decode("utf-8", errors="replace")
    except OSError:
        return {tid: False for tid in ticket_ids}
    return {tid: (tid in text) for tid in ticket_ids}


def observe_wave_evidence(
    *,
    wave: Optional[str] = None,
    ticket_id: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Read-only evidence summary. Missing artifacts → gaps, not crash."""
    root = _repo_root(repo_root)
    if not wave and not ticket_id:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "wave": None,
            "tickets": [],
            "evidence_summary": [],
            "gaps": [{"gap_reason": "missing_wave_or_ticket_id"}],
            "message": "Provide --wave or --ticket-id",
        }

    paths = _list_ticket_paths(root, wave=wave, ticket_id=ticket_id)
    tickets: List[Dict[str, Any]] = []
    evidence_summary: List[Dict[str, Any]] = []
    gaps: List[Dict[str, Any]] = []

    if ticket_id and not paths:
        gaps.append(
            {
                "ticket_id": ticket_id,
                "evidence_type": "b_report_verification",
                "gap_reason": "ticket_state_missing",
            }
        )

    if wave and not paths and not ticket_id:
        gaps.append(
            {
                "wave": wave,
                "evidence_type": "b_report_verification",
                "gap_reason": "no_ticket_states_for_wave",
            }
        )

    ticket_ids: List[str] = []
    for path in paths:
        tid = _ticket_id_from_path(path)
        ticket_ids.append(tid)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            gaps.append(
                {
                    "ticket_id": tid,
                    "evidence_type": "b_report_verification",
                    "gap_reason": f"read_error:{type(exc).__name__}",
                }
            )
            tickets.append({"ticket_id": tid, "state_path": path.as_posix(), "readable": False})
            continue

        verification = _extract_b_report_verification(text)
        ga = _scan_ga_run_urls(text)
        tickets.append(
            {
                "ticket_id": tid,
                "state_path": f"{TICKETS_DIR_REL}/{path.name}",
                "readable": True,
                "has_b_report_verification": verification is not None,
            }
        )
        if verification is not None:
            evidence_summary.append(
                {
                    "ticket_id": tid,
                    "evidence_type": "b_report_verification",
                    "present": True,
                    "human_only": False,
                    "preview": verification[:200],
                }
            )
        else:
            gaps.append(
                {
                    "ticket_id": tid,
                    "evidence_type": "b_report_verification",
                    "gap_reason": "empty_or_missing_verification",
                }
            )

        evidence_summary.append(
            {
                "ticket_id": tid,
                "evidence_type": "ga_run_url_placeholder",
                "present": ga["present"],
                "human_only": True,
                "verified": False,
                "detail": ga,
            }
        )
        if not ga["present"]:
            gaps.append(
                {
                    "ticket_id": tid,
                    "evidence_type": "ga_run_url_placeholder",
                    "gap_reason": "no_run_url",
                    "human_only": True,
                }
            )

    smoke = _smoke_artifact_status(root)
    for item in smoke:
        evidence_summary.append(
            {
                "ticket_id": None,
                "evidence_type": item["evidence_type"],
                "present": item["exists"],
                "human_only": False,
                "path": item["path"],
                "ok": item.get("ok"),
                "run_id": item.get("run_id"),
            }
        )
        if not item["exists"]:
            gaps.append(
                {
                    "evidence_type": item["evidence_type"],
                    "path": item["path"],
                    "gap_reason": "artifact_missing",
                }
            )

    mentions = _progress_mentions(root, ticket_ids)
    for tid, found in mentions.items():
        evidence_summary.append(
            {
                "ticket_id": tid,
                "evidence_type": "progress_append",
                "present": found,
                "human_only": False,
                "path": PROGRESS_REL,
            }
        )
        if not found:
            gaps.append(
                {
                    "ticket_id": tid,
                    "evidence_type": "progress_append",
                    "gap_reason": "not_found_in_progress_tail",
                }
            )

    wave_label = wave or (ticket_id.split("-")[0] if ticket_id else None)
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "skeleton": True,
        "wave": wave_label,
        "tickets": tickets,
        "evidence_summary": evidence_summary,
        "gaps": gaps,
        "message": (
            f"observed {len(tickets)} ticket(s); "
            f"{len(evidence_summary)} evidence row(s); "
            f"{len(gaps)} gap(s) (honest · planning gaps expected)"
        ),
    }


def _format_text(result: Dict[str, Any]) -> str:
    lines = [
        f"ok={result.get('ok')} schema={result.get('schema_version')} wave={result.get('wave')}",
        f"tickets={len(result.get('tickets') or [])} "
        f"evidence={len(result.get('evidence_summary') or [])} "
        f"gaps={len(result.get('gaps') or [])}",
        f"message={result.get('message')}",
    ]
    for gap in (result.get("gaps") or [])[:20]:
        lines.append(f"  gap: {gap}")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="W5-T3 read-only wave evidence observer (skeleton)"
    )
    parser.add_argument("--wave", choices=sorted(_WAVE_PREFIX.keys()), default=None)
    parser.add_argument("--ticket-id", default=None)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Override repo root (tests / ephemeral fixtures)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.repo_root).resolve() if args.repo_root else None
    result = observe_wave_evidence(
        wave=args.wave,
        ticket_id=args.ticket_id,
        repo_root=root,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_text(result), end="")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
