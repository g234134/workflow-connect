#!/usr/bin/env python3
"""
web_cleaner.py — Stage 2: 網路數據清洗 + 去重 + 進池

讀取 web_staging/ 暫存目錄中的已下載檔案，
轉換為 cleaned_full JSON schema v2.0 格式，
去重（content_sha256 比對已有池），新增有效件到 cleaned_full。

用法:
    python core/web_cleaner.py [--config core/web_pipeline_config.yaml]
                               [--staging-dir 05_Temp_Cache/web_staging]
                               [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ── Paths ───────────────────────────────────────
_REPO = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG = _REPO / "core" / "web_pipeline_config.yaml"
_CLEANED_FULL = _REPO / "05_Temp_Cache" / "cleaned_full"
_STAGING_DEFAULT = _REPO / "05_Temp_Cache" / "web_staging"


# ── YAML Loader ─────────────────────────────────
def _load_yaml(path: Path) -> Dict[str, Any]:
    import yaml  # type: ignore
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Content Analysis ────────────────────────────
_TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".html", ".htm", ".css", ".scss", ".less",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".csv", ".tsv",
    ".md", ".rst", ".txt", ".log", ".ini", ".cfg", ".conf",
    ".sql", ".sh", ".bash", ".ps1", ".bat", ".cmd",
    ".r", ".R", ".m", ".mm", ".dart", ".lua", ".perl", ".pl",
}

_DATA_EXTENSIONS = {
    ".csv", ".tsv", ".json", ".jsonl", ".xml", ".yaml", ".yml",
    ".xlsx", ".xls", ".parquet", ".feather",
}

_ARCHIVE_EXTENSIONS = {
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
}

_CODE_CONTENT_PATTERNS = [
    re.compile(r"^\s*(def |class |function |import |from |const |let |var )", re.MULTILINE),
    re.compile(r"^\s*(#include|#define|#pragma|#ifdef)", re.MULTILINE),
    re.compile(r"<(html|head|body|div|span|script)\b", re.IGNORECASE),
]


def _detect_content_type(ext: str, content: bytes) -> str:
    """Detect original_type from extension + content analysis."""
    ext_lower = ext.lower()

    if ext_lower in _CODE_EXTENSIONS:
        return "code"
    if ext_lower in _DATA_EXTENSIONS:
        return "data"
    if ext_lower in _ARCHIVE_EXTENSIONS:
        return "archive"
    if ext_lower in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp"}:
        return "image"
    if ext_lower in {".pdf", ".doc", ".docx", ".xls", ".ppt"}:
        return "document"

    # Content-based detection for unknown extensions
    try:
        text_sample = content[:4096].decode("utf-8", errors="ignore")
    except Exception:
        return "unknown"

    for pattern in _CODE_CONTENT_PATTERNS:
        if pattern.search(text_sample):
            return "code"

    if "<html" in text_sample.lower():
        return "html"

    return "text"


_CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".r", ".R", ".m", ".mm", ".dart", ".lua", ".perl", ".pl",
}


def _detect_encoding(content: bytes) -> str:
    """Detect text encoding."""
    # Try UTF-8 first
    try:
        content.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass

    # Try UTF-8-SIG (with BOM)
    if content[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"

    # Try latin-1 (always succeeds)
    try:
        content.decode("latin-1")
        return "latin-1"
    except Exception:
        pass

    return "binary"


def _extract_content_summary(content: bytes, encoding: str, content_type: str) -> Dict[str, Any]:
    """Extract summary from text content."""
    summary: Dict[str, Any] = {}

    if content_type in ("image", "archive", "binary"):
        summary["size_bytes"] = len(content)
        return summary

    try:
        text = content.decode(encoding, errors="replace")
        lines = text.split("\n")
        non_empty = [l for l in lines if l.strip()]
        summary["line_count"] = len(lines)
        summary["non_empty_lines"] = len(non_empty)
        summary["char_count"] = len(text)
        summary["preview_lines"] = non_empty[:5]
    except Exception:
        summary["size_bytes"] = len(content)

    return summary


# ── Dedup ───────────────────────────────────────
def _load_existing_hashes(cleaned_full: Path) -> Set[str]:
    """Load all content_sha256 from existing cleaned_full JSONs, with cache."""
    cache_path = cleaned_full.parent / "_hash_cache.json"

    # Check if cache is newer than last pool modification
    if cache_path.exists():
        cache_mtime = cache_path.stat().st_mtime
        # Find newest JSON in pool
        newest = max(
            (fp.stat().st_mtime for fp in cleaned_full.glob("*.json")),
            default=0
        )
        if cache_mtime >= newest:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            hashes = set(cached.get("hashes", []))
            print(f"  📦 Hash cache hit: {len(hashes)} hashes (from cache)")
            return hashes

    # Build cache from scratch
    print(f"  📂 Building hash cache (first run, slow)...")
    hashes: Set[str] = set()
    count = 0
    for fp in cleaned_full.glob("*.json"):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                rec = json.load(f)
            h = str(rec.get("content_sha256", "")).strip().lower()
            if h and len(h) == 64:
                hashes.add(h)
            count += 1
            if count % 5000 == 0:
                print(f"    ... {count} records")
        except Exception:
            continue

    # Save cache
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"hashes": list(hashes), "count": count}, f)
    except Exception:
        pass

    print(f"  📊 Pool: {count} records, {len(hashes)} hashes (cache saved)")
    return hashes


# ── Stage Number Generator ──────────────────────
def _next_wave_number(cleaned_full: Path) -> int:
    """Find the next wave number for web-sourced data."""
    max_wave = 0
    for fp in cleaned_full.glob("*.json"):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                rec = json.load(f)
            w = int(rec.get("wave", 0))
            if w > max_wave:
                max_wave = w
        except Exception:
            continue
    return max_wave + 1


# ── Main Cleaning Logic ────────────────────────
def clean_staging(
    staging_dir: Path,
    cleaned_full: Path,
    cleaning_config: Dict[str, Any],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Clean all staged files, dedup, and add to cleaned_full pool.

    Returns summary dict.
    """
    dedup = cleaning_config.get("dedup", True)
    max_size = cleaning_config.get("max_file_size", 10_485_760)
    min_size = cleaning_config.get("min_file_size", 10)
    fallback_enc = cleaning_config.get("fallback_encoding", "utf-8")

    # Load existing hashes for dedup
    existing_hashes: Set[str] = set()
    if dedup:
        existing_hashes = _load_existing_hashes(cleaned_full)

    # Find next wave number
    wave = _next_wave_number(cleaned_full)
    run_id = hashlib.md5(datetime.now(timezone.utc).isoformat().encode()).hexdigest()

    # Collect all staged files
    staged_files = []
    for target_dir in staging_dir.iterdir():
        if target_dir.is_dir() and not target_dir.name.startswith("_"):
            for fp in target_dir.iterdir():
                if fp.is_file() and fp.suffix != ".json" and not fp.name.startswith("_"):
                    staged_files.append(fp)

    print(f"\n═══ Stage 2: Web Data Cleaner ═══")
    print(f"  Staged files: {len(staged_files)}")
    print(f"  Target pool: {cleaned_full}")
    print(f"  Dedup: {'ON' if dedup else 'OFF'}")
    print(f"  Wave: {wave}")
    print(f"  Dry run: {dry_run}")

    stats = {
        "total_staged": len(staged_files),
        "added": 0,
        "skipped_size": 0,
        "skipped_dedup": 0,
        "skipped_binary": 0,
        "errors": 0,
    }

    for i, fp in enumerate(staged_files):
        try:
            content = fp.read_bytes()
            size = len(content)

            # Size filters
            if size > max_size:
                stats["skipped_size"] += 1
                continue
            if size < min_size:
                stats["skipped_size"] += 1
                continue

            # Content hash
            content_sha = hashlib.sha256(content).hexdigest()

            # Dedup check
            if dedup and content_sha in existing_hashes:
                stats["skipped_dedup"] += 1
                continue

            # Detect encoding and content type
            ext = fp.suffix
            encoding = _detect_encoding(content)
            content_type = _detect_content_type(ext, content)

            if content_type in ("image", "archive") and encoding == "binary":
                stats["skipped_binary"] += 1
                continue

            # Build cleaned_full record (schema v2.0)
            idx = stats["added"] + 1
            record = {
                "schema_version": "2.0",
                "run_id": run_id,
                "wave": wave,
                "idx_in_wave": idx,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_path": f"web://{fp.parent.name}/{fp.name}",
                "name": fp.name,
                "extension": ext,
                "original_type": content_type,
                "size_bytes": size,
                "content_sha256": content_sha,
                "encoding": encoding,
                "parse_strategy": None,
                "groq_used": False,
                "groq_reason": None,
                "clean_status": "ok",
                "warnings": [],
                "content_summary": _extract_content_summary(content, encoding, content_type),
                "web_source": {
                    "target_id": fp.parent.name,
                    "original_filename": fp.name,
                },
            }

            # Output filename
            safe_name = re.sub(r'[^\w\-]', '_', fp.stem)[:80]
            out_name = f"web_w{wave:04d}_{idx:03d}_{content_sha[:16]}_{safe_name}{ext}.json"
            out_path = cleaned_full / out_name

            if not dry_run:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(record, f, indent=2, ensure_ascii=False)
                existing_hashes.add(content_sha)

            stats["added"] += 1

            if stats["added"] % 10 == 0 or stats["added"] <= 3:
                print(f"  ✅ [{idx}] {fp.name} ({size:,} bytes, {content_type})")

        except Exception as e:
            stats["errors"] += 1
            if stats["errors"] <= 5:
                print(f"  ❌ Error processing {fp.name}: {e}")

    print(f"\n═══ Stage 2 Complete ═══")
    print(f"  Added: {stats['added']}")
    print(f"  Skipped (size): {stats['skipped_size']}")
    print(f"  Skipped (dedup): {stats['skipped_dedup']}")
    print(f"  Skipped (binary): {stats['skipped_binary']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Pool size now: {sum(1 for _ in cleaned_full.glob('*.json'))}")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 2: 網路數據清洗 + 去重")
    parser.add_argument("--config", default=str(_DEFAULT_CONFIG), help="Config YAML path")
    parser.add_argument("--staging-dir", default=str(_STAGING_DEFAULT), help="Staging directory")
    parser.add_argument("--cleaned-full", default=str(_CLEANED_FULL), help="Cleaned full pool dir")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files")
    args = parser.parse_args()

    config = _load_yaml(Path(args.config))
    cleaning = config.get("cleaning", {})

    stats = clean_staging(
        staging_dir=Path(args.staging_dir),
        cleaned_full=Path(args.cleaned_full),
        cleaning_config=cleaning,
        dry_run=args.dry_run,
    )

    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
