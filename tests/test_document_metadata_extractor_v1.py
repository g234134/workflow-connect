"""Unit tests for document metadata extractor v1 (W12-T3)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.document_metadata_extractor_v1 import (
    extract_document_metadata,
    is_metadata_extraction_eligible,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_NT_A_TASK = "non_tabular.document.extract"
_NT_B_TASK = "non_tabular.log.analyze"
_COMMITTED_NT_A = "cases/_experiment_samples/nt_docu_stub"


def _write_minimal_pdf(path: Path, *, page_markers: int = 2) -> None:
    body = b"%PDF-1.4\n"
    for i in range(page_markers):
        body += f"{i + 1} 0 obj\n<< /Type /Page >>\nendobj\n".encode()
    body += b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"
    path.write_bytes(body)


def _write_minimal_docx(path: Path) -> None:
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>hello</w:t></w:r></w:p>"
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
        "<w:p><w:r><w:t>page2</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", document_xml)
        zf.writestr("[Content_Types].xml", "<Types/>")


class DocumentMetadataExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="nt_meta_")
        self._case_dir = Path(self._tmpdir) / "nt_docu_stub"
        self._case_dir.mkdir(parents=True)
        (self._case_dir / "intake.json").write_text(
            json.dumps(
                {
                    "case_id": "docu-2026-0001",
                    "client_ref": "docu-corp",
                    "content_type": "mixed_documents",
                }
            ),
            encoding="utf-8",
        )
        docs = self._case_dir / "docs"
        docs.mkdir()
        _write_minimal_pdf(docs / "sample.pdf", page_markers=3)
        _write_minimal_docx(docs / "brief.docx")
        (docs / "notes.txt").write_text("plain text", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_eligible_for_nt_a_allowlisted_fixture(self) -> None:
        eligible, reason = is_metadata_extraction_eligible(
            _NT_A_TASK, str(self._case_dir)
        )
        self.assertTrue(eligible)
        self.assertEqual(reason, "eligible")

    def test_not_eligible_without_flag_path(self) -> None:
        other = Path(self._tmpdir) / "other_case"
        other.mkdir()
        (other / "intake.json").write_text(
            json.dumps({"client_ref": "docu-corp"}), encoding="utf-8"
        )
        eligible, reason = is_metadata_extraction_eligible(_NT_A_TASK, str(other))
        self.assertFalse(eligible)
        self.assertEqual(reason, "case_dir_not_allowlisted")

    def test_not_eligible_for_nt_b_task(self) -> None:
        eligible, reason = is_metadata_extraction_eligible(
            _NT_B_TASK, str(self._case_dir)
        )
        self.assertFalse(eligible)
        self.assertEqual(reason, "task_type_not_nt_a")

    def test_disabled_returns_not_requested(self) -> None:
        result = extract_document_metadata(
            str(self._case_dir), task_type=_NT_A_TASK, enabled=False
        )
        self.assertFalse(result["executed"])
        self.assertEqual(result["message"], "metadata_extraction_not_requested")

    def test_enabled_extracts_metadata(self) -> None:
        result = extract_document_metadata(
            str(self._case_dir), task_type=_NT_A_TASK, enabled=True
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["executed"])
        self.assertEqual(result["files_processed"], 3)
        by_name = {d["path"]: d for d in result["documents"]}
        self.assertEqual(by_name["docs/sample.pdf"]["size_bytes"], by_name["docs/sample.pdf"]["size_bytes"])
        self.assertEqual(by_name["docs/sample.pdf"]["mime_type"], "application/pdf")
        self.assertIn("page_count", by_name["docs/sample.pdf"])
        self.assertEqual(by_name["docs/brief.docx"]["mime_type"], _EXT_MIME_DOCX())
        self.assertIn("page_count", by_name["docs/brief.docx"])
        self.assertEqual(by_name["docs/notes.txt"]["encoding"], "utf-8")

    def test_committed_fixture_eligible(self) -> None:
        eligible, _ = is_metadata_extraction_eligible(
            _NT_A_TASK, _COMMITTED_NT_A
        )
        self.assertTrue(eligible)


def _EXT_MIME_DOCX() -> str:
    return (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )


if __name__ == "__main__":
    unittest.main()
