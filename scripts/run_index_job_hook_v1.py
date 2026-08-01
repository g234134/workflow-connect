#!/usr/bin/env python3
"""Index job scheduler hook v1 — dry-run / plan-only skeleton (FP-G2-T1).

Design SSOT: docs/phase2-index-job-hook-v1.md

Default mode is dry-run: returns a stable dict with planned_jobs and does
NOT write production index, mutate seed corpus, or call core ingest.

Usage:
    python scripts/run_index_job_hook_v1.py --dry-run --format json
    python scripts/run_index_job_hook_v1.py --format text
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SCHEMA_VERSION = "index_job_hook_v1"
DOC_REL = "docs/phase2-index-job-hook-v1.md"


def _planned_jobs_skeleton() -> List[Dict[str, Any]]:
    """Logical plan preview only — never marks writes_index true in this ticket."""
    return [
        {
            "job_id": "document_chunks.plan",
            "pipeline": "document_chunks",
            "mode": "plan_only",
            "writes_index": False,
            "notes": "skeleton · no ingest · see WA-T1 document pipeline",
        },
        {
            "job_id": "repo_chunks.plan",
            "pipeline": "repo_chunks",
            "mode": "plan_only",
            "writes_index": False,
            "notes": "skeleton · no repo_index write · W3-B remains experimental",
        },
    ]


def run_index_job_hook(
    *,
    dry_run: bool = True,
    execute: bool = False,
) -> Dict[str, Any]:
    """Return structured hook result. Execute path is intentionally blocked."""
    if execute and not dry_run:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "skeleton": True,
            "mode": "execute_blocked",
            "dry_run": False,
            "message": (
                "execute mode not implemented in FP-G2-T1 skeleton; "
                "requires infra/PM unblock + separate core wiring ticket"
            ),
            "planned_jobs": [],
            "writes_index": False,
            "doc": DOC_REL,
        }

    # Default and explicit dry-run: plan-only preview
    jobs = _planned_jobs_skeleton()
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "skeleton": True,
        "mode": "dry_run",
        "dry_run": True,
        "message": (
            "dry-run plan-only · no production index write · "
            "skeleton ≠ scheduled cron"
        ),
        "planned_jobs": jobs,
        "writes_index": False,
        "doc": DOC_REL,
    }


def _format_text(result: Dict[str, Any]) -> str:
    lines = [
        f"ok={result.get('ok')} mode={result.get('mode')} "
        f"schema={result.get('schema_version')}",
        f"message={result.get('message')}",
        f"writes_index={result.get('writes_index')} "
        f"planned_jobs={len(result.get('planned_jobs') or [])}",
    ]
    for job in result.get("planned_jobs") or []:
        lines.append(
            f"  - {job.get('job_id')}: pipeline={job.get('pipeline')} "
            f"mode={job.get('mode')} writes_index={job.get('writes_index')}"
        )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "FP-G2-T1 index job hook skeleton (default dry-run / plan-only)"
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan-only preview (default when --execute omitted)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Attempt execute (blocked in this skeleton; returns ok=false)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Default = dry-run. --execute alone → blocked ok=false.
    # If both flags set, prefer dry-run safety.
    if args.execute and not args.dry_run:
        result = run_index_job_hook(dry_run=False, execute=True)
    else:
        result = run_index_job_hook(dry_run=True)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_text(result), end="")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
