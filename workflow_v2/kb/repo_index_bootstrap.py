"""
Wave B repo index bootstrap (HQ-side).

Scans governance-critical subtrees, writes manifest + index_status sidecar JSON.
Does not require PostgreSQL or Qdrant — dark-ops ``repo_index_v1`` can replace
this runner later while keeping the same status/manifest contract.

Usage (from repo root)::

    python workflow_v2/kb/repo_index_bootstrap.py run --case W2-1
    python workflow_v2/kb/repo_index_bootstrap.py run --case W2-1 --dry-run
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Iterator

STATUS_SCHEMA: Final[str] = "repo_index_status_v0.1"
MANIFEST_SCHEMA: Final[str] = "repo_index_manifest_v0.1"
SCOPE_SCHEMA: Final[str] = "repo_index_scope_v0.1"
JOB_TYPE: Final[str] = "repo_index_v1"
CHUNK_LINES: Final[int] = 40

DEFAULT_SCOPE_REL: Final[str] = "workflow_v2/kb/wave_b_gov_scope.json"
DEFAULT_STATUS_DIR: Final[str] = "workflow_v2/20_pilot/W3-B"


def find_repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for parent in here.parents:
        if (parent / "AGENTS.md").is_file() and (parent / "workflow_v2").is_dir():
            return parent
    return Path.cwd()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_scope_config(repo_root: Path, scope_rel: str) -> dict[str, Any]:
    path = repo_root / scope_rel
    if not path.is_file():
        return {"ok": False, "message": f"scope config not found: {scope_rel}"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "message": f"invalid scope JSON: {exc}"}
    if not isinstance(data, dict):
        return {"ok": False, "message": "scope config must be a JSON object"}
    return {"ok": True, "scope": data, "path": scope_rel}


def canonical_scope_digest(scope: dict[str, Any]) -> str:
    """Stable SHA-256 digest for scope fingerprint (W3-B §3.2)."""
    canonical = {
        "schema_version": scope.get("schema_version", SCOPE_SCHEMA),
        "kb_index_scope_kind": scope.get("kb_index_scope_kind"),
        "kb_index_repo_root_ref": scope.get("kb_index_repo_root_ref"),
        "kb_index_subtree": scope.get("kb_index_subtree"),
        "kb_index_subtrees": sorted(scope.get("kb_index_subtrees") or []),
        "kb_index_baseline_ref": scope.get("kb_index_baseline_ref"),
        "include_root_files": sorted(scope.get("include_root_files") or []),
        "include_globs": sorted(scope.get("include_globs") or []),
        "exclude_dir_names": sorted(scope.get("exclude_dir_names") or []),
        "exclude_globs": sorted(scope.get("exclude_globs") or []),
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _matches_any(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _should_skip_dir(name: str, exclude_names: set[str]) -> bool:
    return name in exclude_names


def iter_scope_files(
    repo_root: Path,
    scope: dict[str, Any],
) -> Iterator[Path]:
    subtrees: list[str] = list(scope.get("kb_index_subtrees") or [])
    if not subtrees and scope.get("kb_index_subtree"):
        subtrees = [str(scope["kb_index_subtree"])]

    include_globs: list[str] = list(scope.get("include_globs") or ["*.py", "*.md"])
    exclude_names: set[str] = set(scope.get("exclude_dir_names") or [])
    exclude_globs: list[str] = list(scope.get("exclude_globs") or [])

    seen: set[Path] = set()

    for rel_name in scope.get("include_root_files") or []:
        path = repo_root / str(rel_name)
        if path.is_file() and path not in seen:
            seen.add(path)
            yield path

    for subtree in subtrees:
        root = repo_root / subtree
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(_should_skip_dir(part, exclude_names) for part in path.parts):
                continue
            if not _matches_any(path.name, include_globs):
                continue
            if _matches_any(path.name, exclude_globs):
                continue
            rel = path.relative_to(repo_root).as_posix()
            if rel in seen:
                continue
            seen.add(path)
            yield path


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _chunk_file(rel_path: str, text: str, *, chunk_lines: int = CHUNK_LINES) -> list[dict[str, Any]]:
    lines = text.splitlines()
    chunks: list[dict[str, Any]] = []
    if not lines:
        return chunks
    idx = 0
    for start in range(0, len(lines), chunk_lines):
        end = min(start + chunk_lines, len(lines))
        block = "\n".join(lines[start:end])
        chunk_id = hashlib.sha256(f"{rel_path}:{start}:{end}".encode()).hexdigest()[:16]
        chunks.append(
            {
                "chunk_id": chunk_id,
                "path": rel_path,
                "start_line": start + 1,
                "end_line": end,
                "char_count": len(block),
                "text": block,
            }
        )
        idx += 1
    return chunks


def build_manifest(
    repo_root: Path,
    *,
    case_id: str,
    job_id: str,
    scope: dict[str, Any],
) -> dict[str, Any]:
    files_meta: list[dict[str, Any]] = []
    all_chunks: list[dict[str, Any]] = []

    for path in sorted(iter_scope_files(repo_root, scope), key=lambda p: p.as_posix()):
        rel = path.relative_to(repo_root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        file_chunks = _chunk_file(rel, text)
        files_meta.append(
            {
                "path": rel,
                "sha256": _file_sha256(path),
                "size_bytes": path.stat().st_size,
                "chunk_count": len(file_chunks),
            }
        )
        all_chunks.extend(file_chunks)

    return {
        "schema_version": MANIFEST_SCHEMA,
        "case_id": case_id,
        "job_id": job_id,
        "job_type": JOB_TYPE,
        "generated_at": _utc_now_iso(),
        "scope_digest": canonical_scope_digest(scope),
        "files": files_meta,
        "chunks": all_chunks,
        "summary": {
            "file_count": len(files_meta),
            "chunk_count": len(all_chunks),
        },
    }


def build_status(
    *,
    case_id: str,
    job_id: str,
    scope: dict[str, Any],
    manifest_rel: str,
    file_count: int,
    chunk_count: int,
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    scope_block = {
        "kb_index_scope_kind": scope.get("kb_index_scope_kind", "repo_subtree"),
        "kb_index_repo_root_ref": scope.get("kb_index_repo_root_ref", "repo_root"),
        "kb_index_subtree": scope.get("kb_index_subtree", "core"),
        "kb_index_baseline_ref": scope.get("kb_index_baseline_ref", "unpinned"),
    }
    subtrees = scope.get("kb_index_subtrees")
    if subtrees:
        scope_block["kb_index_subtrees"] = subtrees

    return {
        "schema_version": STATUS_SCHEMA,
        "case_id": case_id,
        "job_type": JOB_TYPE,
        "job_id": job_id,
        "status": "succeeded",
        "last_updated": finished_at,
        "started_at": started_at,
        "finished_at": finished_at,
        "scope": scope_block,
        "scope_digest": canonical_scope_digest(scope),
        "result_summary": {
            "file_count": file_count,
            "chunk_count": chunk_count,
            "manifest_ref": manifest_rel,
        },
    }


def fields_from_status(status: dict[str, Any], *, status_rel: str) -> dict[str, Any]:
    """Mirror wf_kb_index_sync.ps1 FieldsFromStatus for tests."""
    if status.get("schema_version") != STATUS_SCHEMA:
        return {
            "ok": False,
            "message": f"schema_version={status.get('schema_version')} (expected {STATUS_SCHEMA})",
        }

    scope = status.get("scope") or {}
    st = str(status.get("status", ""))
    fields: dict[str, Any] = {
        "kb_index_source": status.get("job_type") or JOB_TYPE,
        "kb_index_job_id": status.get("job_id"),
        "kb_index_scope_kind": scope.get("kb_index_scope_kind") or "repo_subtree",
        "kb_index_subtree": scope.get("kb_index_subtree"),
        "kb_index_baseline_ref": scope.get("kb_index_baseline_ref") or "unpinned",
        "kb_index_stale_ack": "false",
        "kb_index_stale_reason": "-",
        "kb_index_reindex_ticket": "W4-B-INDEX-INTEGRATION",
        "kb_index_evidence_refs": status_rel,
    }

    if st == "succeeded":
        finished = status.get("finished_at") or status.get("last_updated")
        fields["kb_index_status"] = "ready"
        fields["kb_index_last_updated"] = finished
        fields["kb_index_blocker"] = "-"
        return {"ok": True, "fields": fields}

    if st in ("failed", "canceled"):
        fields["kb_index_status"] = "missing"
        fields["kb_index_last_updated"] = "-"
        err_type = status.get("error_type")
        err_msg = status.get("error_message") or "-"
        if err_type == "infra_unavailable":
            fields["kb_index_blocker"] = f"infra_unavailable: {err_msg}"
        elif err_type:
            fields["kb_index_blocker"] = f"{err_type}: {err_msg}"
        else:
            fields["kb_index_blocker"] = err_msg
        return {"ok": True, "fields": fields}

    if st == "running":
        fields["kb_index_status"] = "missing"
        fields["kb_index_last_updated"] = "-"
        fields["kb_index_blocker"] = "index job running (not yet succeeded)"
        return {"ok": True, "fields": fields}

    return {"ok": False, "message": f"status={st} (expected running|succeeded|failed|canceled)"}


def run_bootstrap(
    repo_root: Path,
    *,
    case_id: str = "W2-1",
    scope_rel: str = DEFAULT_SCOPE_REL,
    status_dir_rel: str = DEFAULT_STATUS_DIR,
    dry_run: bool = False,
) -> dict[str, Any]:
    loaded = load_scope_config(repo_root, scope_rel)
    if not loaded.get("ok"):
        return {"ok": False, "message": loaded.get("message", "scope load failed")}

    scope: dict[str, Any] = loaded["scope"]
    if scope.get("case_id") and scope["case_id"] != case_id:
        return {
            "ok": False,
            "message": f"scope case_id={scope['case_id']} != requested {case_id}",
        }

    job_id = f"repo_index_v1_job__{case_id}__wave_b_gov_scope"
    started_at = _utc_now_iso()

    manifest_rel = f"{status_dir_rel}/index_manifest_{case_id}.json"
    status_rel = f"{status_dir_rel}/index_status_{case_id}.json"

    manifest = build_manifest(repo_root, case_id=case_id, job_id=job_id, scope=scope)
    file_count = int(manifest["summary"]["file_count"])
    chunk_count = int(manifest["summary"]["chunk_count"])

    if file_count <= 0:
        return {
            "ok": False,
            "message": "no files indexed — check subtrees exist under repo root",
            "file_count": file_count,
            "chunk_count": chunk_count,
        }

    finished_at = _utc_now_iso()
    status = build_status(
        case_id=case_id,
        job_id=job_id,
        scope=scope,
        manifest_rel=manifest_rel,
        file_count=file_count,
        chunk_count=chunk_count,
        started_at=started_at,
        finished_at=finished_at,
    )

    if dry_run:
        return {
            "ok": True,
            "message": "dry-run: would write manifest and status",
            "job_id": job_id,
            "file_count": file_count,
            "chunk_count": chunk_count,
            "manifest_rel": manifest_rel,
            "status_rel": status_rel,
            "scope_digest": status["scope_digest"],
        }

    manifest_path = repo_root / Path(manifest_rel)
    status_path = repo_root / Path(status_rel)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "message": "index bootstrap completed",
        "job_id": job_id,
        "file_count": file_count,
        "chunk_count": chunk_count,
        "manifest_rel": manifest_rel,
        "status_rel": status_rel,
        "scope_digest": status["scope_digest"],
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wave B repo index bootstrap (HQ-side)")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Scan subtrees and write manifest + index_status")
    run_p.add_argument("--case", default="W2-1", help="Pilot case id (default: W2-1)")
    run_p.add_argument("--scope", default=DEFAULT_SCOPE_REL, help="Scope config JSON (repo-relative)")
    run_p.add_argument("--status-dir", default=DEFAULT_STATUS_DIR, help="Output dir for status/manifest")
    run_p.add_argument("--repo-root", default="", help="Repo root (auto-detected if omitted)")
    run_p.add_argument("--dry-run", action="store_true", help="Compute counts without writing files")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root()

    if args.command == "run":
        result = run_bootstrap(
            repo_root,
            case_id=args.case,
            scope_rel=args.scope,
            status_dir_rel=args.status_dir,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
