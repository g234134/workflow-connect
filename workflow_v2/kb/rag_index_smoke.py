"""
Manifest-based RAG smoke for Wave B index bootstrap.

Reads ``index_manifest_<CASE>.json`` produced by ``repo_index_bootstrap`` and
returns keyword hits without PostgreSQL / Qdrant.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

def _import_bootstrap():
    try:
        from workflow_v2.kb.repo_index_bootstrap import DEFAULT_STATUS_DIR, find_repo_root

        return DEFAULT_STATUS_DIR, find_repo_root
    except ModuleNotFoundError:
        from repo_index_bootstrap import DEFAULT_STATUS_DIR, find_repo_root  # type: ignore

        return DEFAULT_STATUS_DIR, find_repo_root


DEFAULT_STATUS_DIR, find_repo_root = _import_bootstrap()


def _tokenize(query: str) -> list[str]:
    return [t for t in re.split(r"\W+", query.lower()) if len(t) >= 2]


def search_manifest(manifest: dict[str, Any], query: str, *, top_k: int = 5) -> dict[str, Any]:
    tokens = _tokenize(query)
    if not tokens:
        return {"ok": False, "message": "query too short", "query": query, "hits": []}

    chunks: list[dict[str, Any]] = list(manifest.get("chunks") or [])
    scored: list[tuple[float, dict[str, Any]]] = []

    for chunk in chunks:
        text = str(chunk.get("text", "")).lower()
        path = str(chunk.get("path", ""))
        score = 0.0
        for tok in tokens:
            if tok in text:
                score += 2.0
            if tok in path.lower():
                score += 1.0
        if score > 0:
            scored.append(
                (
                    score,
                    {
                        "score": round(score, 2),
                        "path": path,
                        "chunk_id": chunk.get("chunk_id"),
                        "start_line": chunk.get("start_line"),
                        "end_line": chunk.get("end_line"),
                        "preview": text[:200],
                    },
                )
            )

    scored.sort(key=lambda x: (-x[0], x[1]["path"]))
    hits = [item for _, item in scored[:top_k]]

    return {
        "ok": True,
        "message": "manifest search complete",
        "collection": "repo_index_manifest",
        "query": query,
        "top_k": top_k,
        "hits": hits,
        "hit_count": len(hits),
    }


def run_smoke(
    repo_root: Path,
    query: str,
    *,
    case_id: str = "W2-1",
    status_dir_rel: str = DEFAULT_STATUS_DIR,
    top_k: int = 5,
) -> dict[str, Any]:
    manifest_rel = f"{status_dir_rel}/index_manifest_{case_id}.json"
    manifest_path = repo_root / Path(manifest_rel)
    if not manifest_path.is_file():
        return {
            "ok": False,
            "message": f"manifest not found: {manifest_rel}",
            "query": query,
            "hits": [],
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = search_manifest(manifest, query, top_k=top_k)
    result["manifest_ref"] = manifest_rel
    return result


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wave B manifest RAG smoke")
    parser.add_argument("query", help="Search query (e.g. AGENTS.md)")
    parser.add_argument("--case", default="W2-1")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--status-dir", default=DEFAULT_STATUS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root()
    result = run_smoke(
        repo_root,
        args.query,
        case_id=args.case,
        status_dir_rel=args.status_dir,
        top_k=args.top_k,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") and result.get("hit_count", 0) >= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
