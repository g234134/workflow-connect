"""Unit tests for Non-Tabular lightweight inspector v1 (W11-T2)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.non_tabular_lightweight_inspector_v1 import inspect_non_tabular_case_dir

_REPO_ROOT = Path(__file__).resolve().parents[1]


class NonTabularLightweightInspectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="nt_inspector_")
        self._case_dir = Path(self._tmpdir) / "fake_case"
        self._case_dir.mkdir(parents=True)
        (self._case_dir / "intake.json").write_text("{}", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _touch(self, rel_path: str, size: int = 0) -> Path:
        path = self._case_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if size > 0:
            path.write_bytes(b"x" * size)
        else:
            path.write_bytes(b"")
        return path

    def test_extension_and_size_stats(self) -> None:
        self._touch("docs/report.pdf", size=100)
        self._touch("docs/notes.docx", size=200)
        self._touch("images/scan.png", size=50)
        self._touch("images/photo.jpg", size=75)
        self._touch("README", size=10)

        result = inspect_non_tabular_case_dir(str(self._case_dir))

        self.assertTrue(result["ok"])
        self.assertTrue(result["metadata_only"])
        self.assertEqual(result["inspection_method"], "stat_only")
        self.assertEqual(result["file_count"], 6)  # 5 + intake.json
        self.assertEqual(result["total_size_bytes"], 100 + 200 + 50 + 75 + 10 + 2)
        self.assertEqual(result["extension_distribution"]["pdf"], 1)
        self.assertEqual(result["extension_distribution"]["docx"], 1)
        self.assertEqual(result["extension_distribution"]["png"], 1)
        self.assertEqual(result["extension_distribution"]["jpg"], 1)
        self.assertEqual(result["extension_distribution"]["json"], 1)
        self.assertEqual(result["extension_distribution"]["(no_ext)"], 1)
        self.assertEqual(result["type_tag_distribution"]["document"], 2)
        self.assertEqual(result["type_tag_distribution"]["image"], 2)
        self.assertEqual(result["type_tag_distribution"]["structured"], 1)
        self.assertEqual(result["type_tag_distribution"]["other"], 1)

    def test_log_stub_pattern_hints(self) -> None:
        self._touch("raw/server_logs/access-2026-05-01.log", size=512)
        self._touch("raw/server_logs/error-2026-05-02.log", size=256)

        result = inspect_non_tabular_case_dir(str(self._case_dir))

        self.assertTrue(result["ok"])
        self.assertEqual(result["extension_distribution"]["log"], 2)
        self.assertEqual(result["type_tag_distribution"]["log"], 2)
        self.assertIn("date_in_filename", result["filename_pattern_hints"])
        self.assertIn("log_like_name", result["filename_pattern_hints"])

    def test_missing_case_dir(self) -> None:
        missing = Path(self._tmpdir) / "does_not_exist"
        result = inspect_non_tabular_case_dir(str(missing))
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "case_dir_not_found")

    def test_does_not_read_file_contents(self) -> None:
        doc = self._case_dir / "secret.pdf"
        doc.write_bytes(b"%PDF-secret-content-should-not-be-read")

        with mock.patch("builtins.open", side_effect=AssertionError("open() must not be called")):
            result = inspect_non_tabular_case_dir(str(self._case_dir))

        self.assertTrue(result["ok"])
        self.assertEqual(result["file_count"], 2)  # secret.pdf + intake.json


if __name__ == "__main__":
    unittest.main()
