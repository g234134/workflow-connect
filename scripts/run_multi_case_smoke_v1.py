#!/usr/bin/env python3
"""Multi-case smoke runner v1 — orchestrates MP-SMOKE across representative cases.

Contract: docs/smoke-and-regression-contract-v1.md (MC-SMOKE · fleet release sanity).
Release pass path: --cases demo_phase,sampleco (excludes phi_demo deny probe).

Runs ``run_multi_phase_smoke_v1`` for each configured case/profile without
changing underlying smoke behavior. Aggregates per-case results into one
summary JSON or human-readable table.

Usage:
    python scripts/run_multi_case_smoke_v1.py --format json
    python scripts/run_multi_case_smoke_v1.py --cases demo_phase,sampleco --format text
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.list_operator_backlog_v1 import build_backlog_entry
from scripts.run_multi_phase_smoke_v1 import (
    DEFAULT_TASK_TYPE,
    run_multi_phase_smoke_v1,
)

SCHEMA_VERSION = "multi_case_smoke_v1"

# Representative cases for release sanity (internal SSOT for this runner).
DEFAULT_REPRESENTATIVE_CASES: List[Dict[str, Any]] = [
    {
        "case_ref": "demo_phase",
        "task_type": "tabular.cleaning.mvp",
        "label": "standard cleaning (primary run lab → bundle)",
    },
    {
        "case_ref": "sampleco/2026-0001",
        "task_type": "tabular.cleaning.mvp",
        "label": "controlled profile (stop at Checkpoint B)",
    },
    {
        "case_ref": "phi_demo",
        "task_type": "tabular.intake.new_case",
        "label": "policy deny path (PHI sensitivity → gate reject)",
        "synthetic_setup": "phi_deny",
    },
]

_CASE_REF_ALIASES: Dict[str, str] = {
    "sampleco": "sampleco/2026-0001",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_phi_demo_case(case_dir: Path) -> None:
    """Write synthetic PHI deny intake under an existing repo-relative case dir."""
    case_dir.mkdir(parents=True, exist_ok=True)
    intake = {
        "case_id": "phi_demo",
        "client_ref": "phi-override",
        "sensitivity": "phi",
        "provenance": {"source_type": "owned"},
        "structure": "text_only",
    }
    (case_dir / "intake.json").write_text(
        json.dumps(intake, ensure_ascii=False),
        encoding="utf-8",
    )


@contextmanager
def _ephemeral_repo_case(repo_root: Path, case_ref: str) -> Iterator[None]:
    """Create a short-lived ``cases/<case_ref>`` tree under repo_root for smoke."""
    case_dir = repo_root / "cases" / case_ref
    existed_before = case_dir.exists()
    backup: Optional[Path] = None
    if existed_before:
        backup = case_dir.with_name(f"{case_dir.name}.mc_smoke_bak")
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
        case_dir.rename(backup)

    try:
        _write_phi_demo_case(case_dir)
        yield
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)
        if backup is not None and backup.exists():
            backup.rename(case_dir)


def resolve_case_entries(
    case_refs: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Resolve CLI ``--cases`` slugs to configured case dicts."""
    if not case_refs:
        return [dict(entry) for entry in DEFAULT_REPRESENTATIVE_CASES]

    by_ref = {entry["case_ref"]: dict(entry) for entry in DEFAULT_REPRESENTATIVE_CASES}
    resolved: List[Dict[str, Any]] = []
    for raw in case_refs:
        slug = raw.strip()
        if not slug:
            continue
        key = _CASE_REF_ALIASES.get(slug, slug)
        if key in by_ref:
            resolved.append(dict(by_ref[key]))
        else:
            resolved.append(
                {
                    "case_ref": key,
                    "task_type": DEFAULT_TASK_TYPE,
                    "label": key,
                }
            )
    return resolved


def _failed_steps(smoke_result: Dict[str, Any]) -> List[str]:
    return [
        str(step.get("step_id"))
        for step in (smoke_result.get("steps") or [])
        if not step.get("ok")
    ]


def _gate_decision_from_smoke(smoke_result: Dict[str, Any]) -> Optional[str]:
    """Canonical gate outcome alias for MC-SMOKE (SSOT: gate_decision ≡ decision)."""
    for step in smoke_result.get("steps") or []:
        if step.get("step_id") != "gate_run_notify":
            continue
        detail = step.get("detail") or {}
        decision = detail.get("decision") or detail.get("gate_decision")
        if decision is not None:
            return str(decision)
    return None


def _operator_status_for_case(
    case_ref: str,
    *,
    repo_root: Path,
    outbox_root_override: Optional[str],
) -> str:
    entry = build_backlog_entry(
        case_ref,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    status = str(entry.get("status") or "inactive")
    if entry.get("skipped"):
        return "inactive"
    return status


def _summarize_case(
    case_entry: Dict[str, Any],
    smoke_result: Dict[str, Any],
    *,
    repo_root: Path,
    outbox_root_override: Optional[str],
) -> Dict[str, Any]:
    case_ref = str(case_entry["case_ref"])
    return {
        "case_ref": case_ref,
        "task_type": str(case_entry.get("task_type") or DEFAULT_TASK_TYPE),
        "label": str(case_entry.get("label") or case_ref),
        "ok": bool(smoke_result.get("ok")),
        "gate_decision": _gate_decision_from_smoke(smoke_result),
        "failed_steps": _failed_steps(smoke_result),
        "operator_status": _operator_status_for_case(
            case_ref,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
        ),
    }


def run_multi_case_smoke_v1(
    case_entries: Optional[List[Dict[str, Any]]] = None,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    enable_dispatch: bool = False,
    write_summary: bool = True,
) -> Dict[str, Any]:
    """Run multi-phase smoke for each case entry; return aggregated summary."""
    root = (repo_root or _REPO_ROOT).resolve()
    entries = case_entries if case_entries is not None else resolve_case_entries()
    case_summaries: List[Dict[str, Any]] = []
    failed_cases: List[str] = []

    for entry in entries:
        case_ref = str(entry["case_ref"])
        task_type = str(entry.get("task_type") or DEFAULT_TASK_TYPE)
        synthetic = entry.get("synthetic_setup")

        if synthetic == "phi_deny":
            with _ephemeral_repo_case(root, case_ref):
                smoke_result = run_multi_phase_smoke_v1(
                    case_ref,
                    task_type=task_type,
                    repo_root=root,
                    outbox_root_override=outbox_root_override,
                    enable_dispatch=enable_dispatch,
                    write_summary=False,
                )
        else:
            smoke_result = run_multi_phase_smoke_v1(
                case_ref,
                task_type=task_type,
                repo_root=root,
                outbox_root_override=outbox_root_override,
                enable_dispatch=enable_dispatch,
                write_summary=False,
            )

        summary = _summarize_case(
            entry,
            smoke_result,
            repo_root=root,
            outbox_root_override=outbox_root_override,
        )
        case_summaries.append(summary)
        if not summary["ok"]:
            failed_cases.append(case_ref)

    all_ok = not failed_cases
    artifact_paths: Dict[str, str] = {}
    summary_payload = {
        "schema_version": SCHEMA_VERSION,
        "ok": all_ok,
        "run_at": _utc_now_iso(),
        "cases_run": [e["case_ref"] for e in entries],
        "cases": case_summaries,
        "failed_cases": failed_cases,
        "enable_dispatch": enable_dispatch,
        "message": (
            "multi-case smoke v1 completed"
            if all_ok
            else f"multi-case smoke v1 completed with failures: {', '.join(failed_cases)}"
        ),
    }

    if write_summary:
        verification_dir = root / "outbox" / "verification"
        verification_dir.mkdir(parents=True, exist_ok=True)
        summary_path = verification_dir / "multi_case_smoke_run.json"
        summary_path.write_text(
            json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        artifact_paths["multi_case_smoke_run.json"] = summary_path.as_posix()

    summary_payload["artifact_paths"] = artifact_paths
    return summary_payload


def _format_text(result: Dict[str, Any]) -> str:
    lines = [
        "Multi-Case Smoke v1",
        f"ok: {result.get('ok')}",
        f"cases_run: {', '.join(result.get('cases_run') or [])}",
        f"enable_dispatch: {result.get('enable_dispatch')}",
        "",
        "── cases ──",
    ]
    for row in result.get("cases") or []:
        status = "OK" if row.get("ok") else "FAIL"
        lines.append(
            f"  [{status}] {row.get('case_ref')} ({row.get('task_type')})"
        )
        lines.append(f"      label: {row.get('label')}")
        lines.append(f"      operator_status: {row.get('operator_status')}")
        failed = row.get("failed_steps") or []
        if failed:
            lines.append(f"      failed_steps: {', '.join(failed)}")
    failed_cases = result.get("failed_cases") or []
    if failed_cases:
        lines.append("")
        lines.append(f"failed_cases: {', '.join(failed_cases)}")
    paths = result.get("artifact_paths") or {}
    if paths:
        lines.append("")
        lines.append("── summary artifacts ──")
        for key, path in paths.items():
            lines.append(f"  {key}: {path}")
    lines.append("")
    lines.append(f"message: {result.get('message')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run multi-case multi-phase smoke across representative standard pipelines."
    )
    parser.add_argument(
        "--cases",
        default=None,
        help="Comma-separated case_ref slugs (default: built-in representative list)",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional isolated outbox root (default: <repo>/outbox/)",
    )
    parser.add_argument(
        "--enable-dispatch",
        action="store_true",
        help="Enable post-emit notification dispatch during per-case smoke runs",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument(
        "--no-write-summary",
        action="store_true",
        help="Skip writing outbox/verification/multi_case_smoke_run.json",
    )
    args = parser.parse_args(argv)

    case_refs: Optional[List[str]] = None
    if args.cases:
        case_refs = [part.strip() for part in args.cases.split(",") if part.strip()]

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    result = run_multi_case_smoke_v1(
        resolve_case_entries(case_refs),
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
        enable_dispatch=args.enable_dispatch,
        write_summary=not args.no_write_summary,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
