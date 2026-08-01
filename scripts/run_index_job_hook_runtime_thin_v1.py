#!/usr/bin/env python3
"""Index job hook thin runtime v1 (FP-G2-T6) — dry-run + optional sandbox execute.

Builds on FP-G2-T1 skeleton. Consumes a local fixture directory / JSON plan,
returns a stable dict with planned_jobs and fixture_digest.

Default: dry-run only (no writes).
Bare ``--execute``: still blocked (≠ production ingest).
``--execute --sandbox``: writes ONLY under allowlisted local sandbox roots
(artifacts/p2_sandbox_index or fixture _sandbox_out). Never touches Qdrant,
production DB, 03_RAG_Database, or core ingest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.run_index_job_hook_v1 import (  # noqa: E402
    DOC_REL as T1_DOC_REL,
    run_index_job_hook,
)

SCHEMA_VERSION = "index_job_hook_runtime_thin_v1"
DOC_REL = "docs/phase2-index-job-hook-runtime-thin-v1.md"
DEFAULT_FIXTURE_REL = "tests/fixtures/index_job_hook_thin_v1"
DEFAULT_SANDBOX_OUT_REL = "artifacts/p2_sandbox_index"
# Writable roots for --execute --sandbox (repo-relative posix prefixes).
ALLOWED_SANDBOX_OUT_PREFIXES: Tuple[str, ...] = (
    "artifacts/p2_sandbox_index",
    "tests/fixtures/index_job_hook_thin_v1/_sandbox_out",
)


def _digest_path(path: Path) -> str:
    h = hashlib.sha256()
    if path.is_file():
        h.update(path.read_bytes())
    elif path.is_dir():
        for child in sorted(path.rglob("*")):
            if not child.is_file():
                continue
            # Skip prior sandbox out under fixture (if any)
            try:
                rel_parts = child.relative_to(path).parts
            except ValueError:
                continue
            if rel_parts and rel_parts[0] == "_sandbox_out":
                continue
            rel = child.relative_to(path).as_posix().encode("utf-8")
            h.update(rel)
            h.update(b"\0")
            h.update(child.read_bytes())
    else:
        h.update(b"missing")
    return h.hexdigest()[:16]


def _repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def _is_allowed_sandbox_out(out_root: Path) -> bool:
    rel = _repo_rel(out_root)
    return any(
        rel == prefix or rel.startswith(prefix + "/")
        for prefix in ALLOWED_SANDBOX_OUT_PREFIXES
    )


def _load_fixture_jobs(
    fixture_root: Path, *, sandbox: bool = False
) -> List[Dict[str, Any]]:
    plan_path = fixture_root / "plan.json"
    mode = "sandbox_local_write" if sandbox else "fixture_dry_run"
    writes = bool(sandbox)
    if plan_path.is_file():
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        jobs = data.get("planned_jobs") if isinstance(data, dict) else None
        if isinstance(jobs, list):
            out: List[Dict[str, Any]] = []
            for job in jobs:
                if not isinstance(job, dict):
                    continue
                entry = dict(job)
                entry["mode"] = mode
                entry["writes_index"] = writes
                if sandbox:
                    entry["notes"] = (
                        "sandbox execute · local artifact only · "
                        "≠ production Qdrant/PG/core ingest"
                    )
                out.append(entry)
            return out
    # Fallback: one job per *.txt / *.md under fixture (skip _sandbox_out)
    files = sorted(
        [
            p
            for p in fixture_root.rglob("*")
            if p.is_file()
            and p.suffix in {".txt", ".md", ".json"}
            and "_sandbox_out" not in p.relative_to(fixture_root).parts
        ]
    )
    return [
        {
            "job_id": f"fixture.{p.stem}",
            "pipeline": "document_chunks",
            "mode": mode,
            "writes_index": writes,
            "source_rel": p.relative_to(fixture_root).as_posix(),
            "notes": (
                "sandbox execute · local artifact only"
                if sandbox
                else "thin runtime · local fixture only · no ingest"
            ),
        }
        for p in files
        if p.name != "plan.json"
    ] or [
        {
            "job_id": "fixture.empty",
            "pipeline": "document_chunks",
            "mode": mode,
            "writes_index": writes,
            "notes": "empty fixture · plan-only",
        }
    ]


def _write_sandbox_artifacts(
    *,
    fixture: Path,
    out_root: Path,
    jobs: List[Dict[str, Any]],
    digest: str,
) -> Dict[str, Any]:
    """Write local sandbox index stub (JSON only). No vector DB / PG."""
    if not _is_allowed_sandbox_out(out_root):
        return {
            "ok": False,
            "message": (
                f"sandbox out rejected: {_repo_rel(out_root)} "
                f"not in allowlist {list(ALLOWED_SANDBOX_OUT_PREFIXES)}"
            ),
            "written_paths": [],
        }

    out_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    written: List[str] = []
    chunk_rows: List[Dict[str, Any]] = []
    for job in jobs:
        source_rel = job.get("source_rel")
        text = ""
        if isinstance(source_rel, str) and source_rel:
            src = fixture / source_rel
            if src.is_file():
                text = src.read_text(encoding="utf-8")
        chunk = {
            "job_id": job.get("job_id"),
            "pipeline": job.get("pipeline"),
            "source_rel": source_rel,
            "text_preview": (text[:200] if text else ""),
            "char_count": len(text),
            "sandbox": True,
            "writes_production_index": False,
        }
        chunk_rows.append(chunk)
        chunk_path = run_dir / f"{job.get('job_id', 'job')}.chunk.json"
        chunk_path.write_text(
            json.dumps(chunk, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(_repo_rel(chunk_path))

    manifest = {
        "schema": "p2_sandbox_index_manifest_v1",
        "run_id": run_id,
        "fixture": _repo_rel(fixture),
        "fixture_digest": digest,
        "sandbox": True,
        "writes_production_index": False,
        "collection": "sandbox_local_stub",
        "jobs": jobs,
        "chunks": chunk_rows,
        "cleanup": (
            f"Remove directory {_repo_rel(run_dir)} "
            f"(or entire {_repo_rel(out_root)})"
        ),
        "reversible": True,
    }
    manifest_path = run_dir / "sandbox_index_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    written.append(_repo_rel(manifest_path))
    latest = out_root / "latest.json"
    latest.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "manifest": _repo_rel(manifest_path),
                "run_dir": _repo_rel(run_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(_repo_rel(latest))

    return {
        "ok": True,
        "message": "sandbox local index stub written",
        "written_paths": written,
        "run_id": run_id,
        "run_dir": _repo_rel(run_dir),
        "manifest": _repo_rel(manifest_path),
        "collection": "sandbox_local_stub",
    }


def run_index_job_hook_runtime_thin(
    *,
    dry_run: bool = True,
    execute: bool = False,
    sandbox: bool = False,
    fixture_path: Path | None = None,
    sandbox_out: Path | None = None,
) -> Dict[str, Any]:
    """Thin runtime: dry-run by default; sandbox execute is opt-in + allowlisted."""
    # Bare execute (no sandbox) remains blocked by design (T6 / Wave B gate).
    if execute and not dry_run and not sandbox:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "skeleton": False,
            "thin_runtime": True,
            "mode": "execute_blocked",
            "dry_run": False,
            "sandbox": False,
            "message": (
                "execute blocked without --sandbox; "
                "use --execute --sandbox for allowlisted local writes only · "
                "≠ production ingest / Qdrant / PG"
            ),
            "planned_jobs": [],
            "writes_index": False,
            "fixture_digest": None,
            "doc": DOC_REL,
            "upstream_doc": T1_DOC_REL,
            "allowed_sandbox_out": list(ALLOWED_SANDBOX_OUT_PREFIXES),
        }

    fixture = fixture_path or (_REPO_ROOT / DEFAULT_FIXTURE_REL)
    if not fixture.exists():
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "thin_runtime": True,
            "mode": "error",
            "dry_run": True,
            "sandbox": False,
            "message": f"fixture missing: {fixture.as_posix()}",
            "planned_jobs": [],
            "writes_index": False,
            "fixture_digest": None,
            "doc": DOC_REL,
        }

    skeleton = run_index_job_hook(dry_run=True)
    digest = _digest_path(fixture)
    fixture_rel = _repo_rel(fixture)

    # Sandbox execute path
    if execute and not dry_run and sandbox:
        jobs = _load_fixture_jobs(fixture, sandbox=True)
        out_root = sandbox_out or (_REPO_ROOT / DEFAULT_SANDBOX_OUT_REL)
        if not out_root.is_absolute():
            out_root = _REPO_ROOT / out_root
        write_result = _write_sandbox_artifacts(
            fixture=fixture, out_root=out_root, jobs=jobs, digest=digest
        )
        if not write_result.get("ok"):
            return {
                "ok": False,
                "schema_version": SCHEMA_VERSION,
                "skeleton": False,
                "thin_runtime": True,
                "mode": "sandbox_rejected",
                "dry_run": False,
                "sandbox": True,
                "message": write_result.get("message"),
                "planned_jobs": jobs,
                "writes_index": False,
                "writes_production_index": False,
                "written_paths": [],
                "fixture": fixture_rel,
                "fixture_digest": digest,
                "doc": DOC_REL,
                "upstream_doc": T1_DOC_REL,
                "allowed_sandbox_out": list(ALLOWED_SANDBOX_OUT_PREFIXES),
            }

        return {
            "ok": True,
            "schema_version": SCHEMA_VERSION,
            "skeleton": False,
            "thin_runtime": True,
            "mode": "sandbox_execute",
            "dry_run": False,
            "sandbox": True,
            "message": (
                "sandbox execute ok · local stub index only · "
                "≠ production Qdrant/PG/core ingest · ≠ live corpus"
            ),
            "planned_jobs": jobs,
            "writes_index": True,
            "writes_production_index": False,
            "written_paths": write_result.get("written_paths") or [],
            "sandbox_run_id": write_result.get("run_id"),
            "sandbox_run_dir": write_result.get("run_dir"),
            "sandbox_manifest": write_result.get("manifest"),
            "sandbox_collection": write_result.get("collection"),
            "cleanup": (
                f"Delete {write_result.get('run_dir')} "
                f"or entire {DEFAULT_SANDBOX_OUT_REL}/"
            ),
            "reversible": True,
            "fixture": fixture_rel,
            "fixture_digest": digest,
            "upstream_skeleton_ok": bool(skeleton.get("ok")),
            "upstream_planned_job_count": len(skeleton.get("planned_jobs") or []),
            "doc": DOC_REL,
            "upstream_doc": T1_DOC_REL,
            "allowed_sandbox_out": list(ALLOWED_SANDBOX_OUT_PREFIXES),
            "risk": {
                "touches_live_qdrant": False,
                "touches_production_db": False,
                "touches_rag_database_tree": False,
                "touches_core_ingest": False,
                "notes": "JSON stub under allowlisted artifacts/ only",
            },
        }

    # Default dry-run
    jobs = _load_fixture_jobs(fixture, sandbox=False)
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "skeleton": False,
        "thin_runtime": True,
        "mode": "dry_run",
        "dry_run": True,
        "sandbox": False,
        "message": (
            "thin runtime dry-run · local fixture only · "
            "no production index write · no core ingest"
        ),
        "planned_jobs": jobs,
        "writes_index": False,
        "writes_production_index": False,
        "fixture": fixture_rel,
        "fixture_digest": digest,
        "upstream_skeleton_ok": bool(skeleton.get("ok")),
        "upstream_planned_job_count": len(skeleton.get("planned_jobs") or []),
        "doc": DOC_REL,
        "upstream_doc": T1_DOC_REL,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "FP-G2-T6 index job hook thin runtime "
            "(fixture dry-run; optional --execute --sandbox)"
        )
    )
    parser.add_argument("--dry-run", action="store_true", help="Default dry-run")
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Execute path (blocked unless combined with --sandbox)",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        default=False,
        help=(
            "With --execute: write local stub index under allowlisted "
            f"sandbox out (default {DEFAULT_SANDBOX_OUT_REL})"
        ),
    )
    parser.add_argument(
        "--sandbox-out",
        default=DEFAULT_SANDBOX_OUT_REL,
        help="Repo-relative sandbox output root (must be allowlisted)",
    )
    parser.add_argument(
        "--fixture",
        default=DEFAULT_FIXTURE_REL,
        help="Repo-relative local fixture dir or plan.json parent",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    fixture_path = Path(args.fixture)
    if not fixture_path.is_absolute():
        fixture_path = _REPO_ROOT / fixture_path

    sandbox_out = Path(args.sandbox_out)
    if not sandbox_out.is_absolute():
        sandbox_out = _REPO_ROOT / sandbox_out

    if args.execute and not args.dry_run:
        result = run_index_job_hook_runtime_thin(
            dry_run=False,
            execute=True,
            sandbox=bool(args.sandbox),
            fixture_path=fixture_path,
            sandbox_out=sandbox_out,
        )
    else:
        result = run_index_job_hook_runtime_thin(
            dry_run=True, fixture_path=fixture_path
        )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"ok={result.get('ok')} mode={result.get('mode')} "
            f"jobs={len(result.get('planned_jobs') or [])} "
            f"digest={result.get('fixture_digest')} "
            f"writes_index={result.get('writes_index')} "
            f"sandbox={result.get('sandbox')}"
        )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
