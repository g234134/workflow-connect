"""Non-Tabular lightweight content inspector v1 (W11-T2).

Metadata-only case directory scan: file enumeration, size/count stats,
extension distribution, and filename pattern hints. Does not read file
contents or invoke OCR / log parsers.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Extension → coarse content-type tag (metadata heuristic only).
_EXT_TYPE_TAGS: Dict[str, str] = {
    "pdf": "document",
    "docx": "document",
    "doc": "document",
    "txt": "document",
    "md": "document",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "gif": "image",
    "webp": "image",
    "log": "log",
    "json": "structured",
    "jsonl": "structured",
    "csv": "tabular",
}

_DATE_PATTERN = re.compile(r"\d{4}[-_]\d{2}[-_]\d{2}")
_NUMERIC_SUFFIX = re.compile(r"[-_]\d{3,}$")
_LOG_LIKE_NAME = re.compile(r"(?i)(access|error|app|server|audit).*\.log$")


def _normalize_case_dir(case_dir: str) -> Tuple[Path, str]:
    path = Path(case_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        rel = resolved.as_posix()
    return resolved, rel


def _extension_key(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix if suffix else "(no_ext)"


def _filename_pattern_hints(name: str) -> Set[str]:
    hints: Set[str] = set()
    if _DATE_PATTERN.search(name):
        hints.add("date_in_filename")
    if _NUMERIC_SUFFIX.search(path_stem := Path(name).stem):
        hints.add("numeric_suffix")
    if _LOG_LIKE_NAME.search(name):
        hints.add("log_like_name")
    if name.startswith("."):
        hints.add("hidden_file")
    return hints


def inspect_non_tabular_case_dir(case_dir: str) -> Dict[str, Any]:
    """Inspect a case directory using path/stat metadata only (no content reads).

    Returns file counts, total size, extension distribution, coarse type tags,
    and filename pattern hints suitable for non-tabular preview ``content_summary``.
    """
    case_path, rel_case_dir = _normalize_case_dir(case_dir)

    base: Dict[str, Any] = {
        "ok": False,
        "case_dir": rel_case_dir,
        "metadata_only": True,
        "inspection_method": "stat_only",
        "file_count": 0,
        "total_size_bytes": 0,
        "extension_distribution": {},
        "type_tag_distribution": {},
        "filename_pattern_hints": [],
        "largest_file_bytes": 0,
        "notes": [],
    }

    if not case_path.exists():
        base["message"] = "case_dir_not_found"
        base["notes"].append(f"path does not exist: {rel_case_dir}")
        return base

    if not case_path.is_dir():
        base["message"] = "case_dir_not_a_directory"
        return base

    ext_counter: Counter[str] = Counter()
    type_tag_counter: Counter[str] = Counter()
    pattern_hints: Set[str] = set()
    total_size = 0
    file_count = 0
    largest = 0
    skipped_non_file = 0

    for entry in case_path.rglob("*"):
        if not entry.is_file():
            continue
        try:
            stat = entry.stat()
        except OSError:
            skipped_non_file += 1
            continue

        size = int(stat.st_size)
        file_count += 1
        total_size += size
        largest = max(largest, size)

        ext_key = _extension_key(entry)
        ext_counter[ext_key] += 1

        type_tag = _EXT_TYPE_TAGS.get(ext_key, "other")
        type_tag_counter[type_tag] += 1

        pattern_hints.update(_filename_pattern_hints(entry.name))

    if skipped_non_file:
        base["notes"].append(f"skipped {skipped_non_file} path(s) due to stat errors")

    base["ok"] = True
    base["message"] = f"inspected {file_count} file(s); metadata only (stat/path)"
    base["file_count"] = file_count
    base["total_size_bytes"] = total_size
    base["largest_file_bytes"] = largest
    base["extension_distribution"] = dict(sorted(ext_counter.items()))
    base["type_tag_distribution"] = dict(sorted(type_tag_counter.items()))
    base["filename_pattern_hints"] = sorted(pattern_hints)

    if file_count == 0:
        base["notes"].append("no files found under case_dir (intake.json-only stub?)")

    return base
