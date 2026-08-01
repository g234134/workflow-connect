#!/usr/bin/env python3
"""P2 GraphRAG jobs thin runner v1 — local fixture state-machine simulation.

Ticket: P2-GRAPHRAG-THIN-RUNNER-v1
Design: docs/phase2-graphrag-thin-runner-v1.md
Upstream state machine: docs/phase2-graphrag-jobs-state-machine-v1.md (FP-G2-T4)

Simulates MVP transitions queued → running → succeeded|failed against a
local fixture. Does **not** touch PG, core/graphrag_backend, ask selector,
or production index.

Usage:
    python scripts/run_p2_graphrag_thin_runner_v1.py --format text
    python scripts/run_p2_graphrag_thin_runner_v1.py --pretty
    python scripts/run_p2_graphrag_thin_runner_v1.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SCHEMA_VERSION = "p2_graphrag_thin_runner_v1"
DOC_REL = "docs/phase2-graphrag-thin-runner-v1.md"
DEFAULT_FIXTURE_REL = "tests/fixtures/graphrag_jobs_thin_v1/plan.json"
DEFAULT_ARTIFACT_REL = "artifacts/p2_graphrag_thin"
MVP_STATUSES = ("queued", "running", "succeeded", "failed")
_NON_CLAIMS = (
    "≠ GraphRAG primary retrieval / ask selector consumption",
    "≠ production graphrag_jobs DB migration / cron / live batch",
    "≠ P2 sandbox Wave B formal GO / RAG E2E MVP",
    "≠ mandatory CI / Dashboard Phase% apply",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def _load_fixture(fixture_path: Path) -> Dict[str, Any]:
    if not fixture_path.is_file():
        raise FileNotFoundError(f"fixture not found: {_repo_rel(fixture_path)}")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("fixture root must be a JSON object")
    jobs = data.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("fixture.jobs must be a non-empty list")
    return data


def _transition_job(job: Dict[str, Any], *, now: str) -> Dict[str, Any]:
    """Apply MVP path: queued → running → succeeded|failed (in-process)."""
    out = dict(job)
    start_status = str(out.get("status") or "queued")
    if start_status not in MVP_STATUSES:
        out["status"] = "failed"
        out["error_code"] = out.get("error_code") or "INVALID_STATUS"
        out["message"] = f"unknown start status: {start_status}"
        out["finished_at"] = now
        out["transitions"] = [start_status, "failed"]
        return out

    if start_status in ("succeeded", "failed"):
        out["transitions"] = [start_status]
        out["message"] = out.get("message") or "already terminal"
        return out

    transitions: List[str] = [start_status]
    if start_status == "queued":
        out["status"] = "running"
        out["started_at"] = now
        transitions.append("running")

    # From running → terminal
    simulate = str(out.get("simulate") or "").lower()
    force_fail = simulate in {"fail", "failed", "error"}
    if force_fail:
        out["status"] = "failed"
        out["error_code"] = out.get("error_code") or "FIXTURE_SIMULATED_FAIL"
        out["message"] = out.get("message") or "fixture simulated failure"
        out["finished_at"] = now
        transitions.append("failed")
    else:
        out["status"] = "succeeded"
        out["message"] = out.get("message") or "fixture simulated success"
        out["finished_at"] = now
        out.pop("error_code", None)
        transitions.append("succeeded")

    out["transitions"] = transitions
    out["skeleton"] = True if out.get("skeleton") is None else bool(out.get("skeleton"))
    out["job_type"] = out.get("job_type") or "graphrag"
    return out


def run_p2_graphrag_thin_runner(
    *,
    fixture: Optional[Path] = None,
    write: bool = False,
    artifact_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run local GraphRAG job state-machine simulation. Returns stable dict."""
    fixture_path = fixture or (_REPO_ROOT / DEFAULT_FIXTURE_REL)
    now = _utc_now()
    try:
        raw = _load_fixture(fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "message": str(exc),
            "doc": DOC_REL,
            "fixture": _repo_rel(fixture_path),
            "primary_retrieval": False,
            "writes_production_db": False,
            "apply_phase_pct": False,
            "jobs": [],
            "summary": {},
            "non_claims": list(_NON_CLAIMS),
        }

    jobs_out: List[Dict[str, Any]] = []
    for item in raw["jobs"]:
        if not isinstance(item, dict):
            jobs_out.append(
                {
                    "job_id": None,
                    "status": "failed",
                    "error_code": "INVALID_JOB",
                    "message": "job entry must be object",
                    "transitions": [],
                    "skeleton": True,
                }
            )
            continue
        jobs_out.append(_transition_job(item, now=now))

    succeeded = sum(1 for j in jobs_out if j.get("status") == "succeeded")
    failed = sum(1 for j in jobs_out if j.get("status") == "failed")
    # Runner itself is ok when simulation completed with structured results.
    # Presence of fixture-failed jobs is expected (AC-4) and does not fail ok.
    invalid = sum(1 for j in jobs_out if j.get("error_code") == "INVALID_JOB")
    ok = invalid == 0 and len(jobs_out) > 0

    result: Dict[str, Any] = {
        "ok": ok,
        "schema_version": SCHEMA_VERSION,
        "message": (
            "graphrag thin runner simulated MVP transitions"
            if ok
            else "fixture or job shape invalid"
        ),
        "doc": DOC_REL,
        "fixture": _repo_rel(fixture_path),
        "primary_retrieval": False,
        "writes_production_db": False,
        "apply_phase_pct": False,
        "mvp_statuses": list(MVP_STATUSES),
        "jobs": jobs_out,
        "summary": {
            "total": len(jobs_out),
            "succeeded": succeeded,
            "failed": failed,
            "invalid": invalid,
        },
        "non_claims": list(_NON_CLAIMS),
    }

    if write and ok:
        out_root = artifact_dir or (_REPO_ROOT / DEFAULT_ARTIFACT_REL)
        out_root.mkdir(parents=True, exist_ok=True)
        stamp = now.replace(":", "").replace("-", "")
        out_path = out_root / f"run_{stamp}.json"
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result["artifact"] = _repo_rel(out_path)

    return result


def _format_text(result: Dict[str, Any]) -> str:
    lines = [
        f"ok: {result.get('ok')}",
        f"schema_version={result.get('schema_version')}",
        f"primary_retrieval={result.get('primary_retrieval')}",
        f"apply_phase_pct={result.get('apply_phase_pct')}",
        f"fixture={result.get('fixture')}",
        f"summary={result.get('summary')}",
    ]
    for job in result.get("jobs") or []:
        jid = job.get("job_id")
        st = job.get("status")
        tr = "→".join(job.get("transitions") or [])
        lines.append(f"  job {jid}: {st} ({tr})")
    lines.append("non_claims:")
    for c in result.get("non_claims") or []:
        lines.append(f"  - {c}")
    if result.get("message"):
        lines.append(f"message: {result['message']}")
    if result.get("artifact"):
        lines.append(f"artifact: {result['artifact']}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="P2 GraphRAG jobs thin runner (local fixture only)"
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help=f"fixture plan.json (default: {DEFAULT_FIXTURE_REL})",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=f"write summary under {DEFAULT_ARTIFACT_REL}/",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="pretty-print JSON (implies --format json)",
    )
    args = parser.parse_args(argv)

    result = run_p2_graphrag_thin_runner(fixture=args.fixture, write=args.write)
    as_json = args.format == "json" or args.pretty
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    else:
        print(_format_text(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
