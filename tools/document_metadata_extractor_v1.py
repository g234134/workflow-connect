"""Document metadata extractor v1 (W12-T3) — sandbox-only, experimental.

Extracts allowed metadata fields (size, mime type, page count where applicable,
text encoding) from document files under an NT-A fixture case directory.

Does NOT perform OCR, full-text parsing, or write to production outbox.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Explicit repo-relative case_dir allowlist (NT-A docu-corp fixtures only).
_CASE_DIR_ALLOWLIST: frozenset[str] = frozenset(
    {
        "cases/_experiment_samples/nt_docu_stub",
    }
)

# Path segment that must appear for allowlist match (fixture folder name).
_CASE_DIR_PATH_HINT = "nt_docu_stub"

_NT_A_TASK_TYPES: frozenset[str] = frozenset({"non_tabular.document.extract"})

_DOC_EXTENSIONS: frozenset[str] = frozenset(
    {"pdf", "docx", "doc", "txt", "md", "rtf"}
)

_EXT_MIME: Dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "txt": "text/plain",
    "md": "text/markdown",
    "rtf": "application/rtf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}

_MAGIC_MIME: Tuple[Tuple[bytes, str], ...] = (
    (b"%PDF", "application/pdf"),
    (b"PK\x03\x04", "application/zip"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)

_DOCX_PAGE_BREAK = re.compile(
    rb"(?:<w:br[^>]*w:type=\"page\"|<w:lastRenderedPageBreak\b)",
    re.IGNORECASE,
)


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


def _read_intake_client_ref(case_path: Path) -> Optional[str]:
    intake_path = case_path / "intake.json"
    if not intake_path.is_file():
        return None
    try:
        payload = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    client_ref = payload.get("client_ref")
    return str(client_ref) if client_ref else None


def is_metadata_extraction_eligible(
    task_type: str,
    case_dir: str,
) -> Tuple[bool, str]:
    """Return (eligible, reason) for metadata extraction gate."""
    if task_type not in _NT_A_TASK_TYPES:
        return False, "task_type_not_nt_a"

    _, rel_case_dir = _normalize_case_dir(case_dir)
    norm = rel_case_dir.replace("\\", "/").rstrip("/")

    path_ok = norm in _CASE_DIR_ALLOWLIST or _CASE_DIR_PATH_HINT in norm
    if not path_ok:
        return False, "case_dir_not_allowlisted"

    case_path, _ = _normalize_case_dir(case_dir)
    client_ref = _read_intake_client_ref(case_path)
    if client_ref not in {"docu-corp", "docu_corp"}:
        return False, "intake_client_ref_not_docu_corp"

    return True, "eligible"


def _detect_mime(path: Path, ext: str) -> str:
    mime = _EXT_MIME.get(ext, "application/octet-stream")
    try:
        with path.open("rb") as fh:
            head = fh.read(16)
    except OSError:
        return mime
    for magic, magic_mime in _MAGIC_MIME:
        if head.startswith(magic):
            if ext == "docx" and magic_mime == "application/zip":
                return _EXT_MIME["docx"]
            return magic_mime
    return mime


def _pdf_page_count(path: Path) -> Optional[int]:
    try:
        import pypdfium2 as pdfium  # type: ignore[import-untyped]

        doc = pdfium.PdfDocument(str(path))
        try:
            return len(doc)
        finally:
            doc.close()
    except Exception:
        pass

    try:
        data = path.read_bytes()
    except OSError:
        return None

    count = data.count(b"/Type/Page") + data.count(b"/Type /Page")
    return count if count > 0 else None


def _docx_page_count(path: Path) -> Optional[int]:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            if "word/document.xml" not in zf.namelist():
                return None
            xml_bytes = zf.read("word/document.xml")
    except (OSError, zipfile.BadZipFile, KeyError):
        return None

    breaks = len(_DOCX_PAGE_BREAK.findall(xml_bytes))
    return max(breaks + 1, 1) if breaks >= 0 else None


def _text_encoding(path: Path) -> Optional[str]:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if not raw:
        return "utf-8"
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        raw.decode("latin-1")
        return "latin-1"
    except UnicodeDecodeError:
        return "binary"


def _extract_file_metadata(path: Path, rel_path: str) -> Dict[str, Any]:
    ext = path.suffix.lower().lstrip(".")
    stat = path.stat()
    entry: Dict[str, Any] = {
        "path": rel_path,
        "size_bytes": int(stat.st_size),
        "extension": ext or "(no_ext)",
        "mime_type": _detect_mime(path, ext),
    }

    if ext == "pdf":
        pages = _pdf_page_count(path)
        if pages is not None:
            entry["page_count"] = pages
    elif ext == "docx":
        pages = _docx_page_count(path)
        if pages is not None:
            entry["page_count"] = pages
    elif ext in {"txt", "md"}:
        encoding = _text_encoding(path)
        if encoding:
            entry["encoding"] = encoding

    return entry


def extract_document_metadata(
    case_dir: str,
    *,
    task_type: str,
    enabled: bool = False,
    max_files: int = 20,
    include_extensions: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Extract sandbox metadata for allowlisted NT-A fixtures when explicitly enabled."""
    base: Dict[str, Any] = {
        "ok": False,
        "tool_id": "document_metadata_extractor_v1",
        "sandbox_only": True,
        "experimental": True,
        "extraction_method": "metadata_only",
        "enabled": enabled,
        "executed": False,
        "files_processed": 0,
        "documents": [],
        "notes": [
            "W12-T3 sandbox metadata extraction; no OCR or full-text parse",
            "writes only via orchestrator preview sandbox outbox",
        ],
    }

    if not enabled:
        base["message"] = "metadata_extraction_not_requested"
        base["notes"].append("pass with_metadata_extraction=True to enable")
        return base

    eligible, reason = is_metadata_extraction_eligible(task_type, case_dir)
    base["eligibility"] = {"eligible": eligible, "reason": reason}
    if not eligible:
        base["message"] = f"metadata_extraction_skipped:{reason}"
        return base

    case_path, rel_case_dir = _normalize_case_dir(case_dir)
    base["case_dir"] = rel_case_dir

    if not case_path.is_dir():
        base["message"] = "case_dir_not_found"
        return base

    allowed_ext = include_extensions or _DOC_EXTENSIONS
    documents: List[Dict[str, Any]] = []

    for entry in sorted(case_path.rglob("*")):
        if not entry.is_file():
            continue
        ext = entry.suffix.lower().lstrip(".")
        if ext not in allowed_ext:
            continue
        try:
            rel_file = entry.relative_to(case_path).as_posix()
        except ValueError:
            rel_file = entry.name
        documents.append(_extract_file_metadata(entry, rel_file))
        if len(documents) >= max_files:
            base["notes"].append(f"truncated at max_files={max_files}")
            break

    base["ok"] = True
    base["executed"] = True
    base["message"] = f"extracted metadata for {len(documents)} document(s)"
    base["files_processed"] = len(documents)
    base["documents"] = documents
    return base
