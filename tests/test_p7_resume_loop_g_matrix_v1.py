"""Unit tests for P7 resume-loop G-1–G-5 matrix schema (spec-only)."""
from __future__ import annotations

import unittest
from pathlib import Path

from scripts.verify_g_matrix import DEFAULT_MATRIX_PATH, verify_matrix


class TestP7ResumeLoopGMatrixV1(unittest.TestCase):
    def test_matrix_file_exists(self) -> None:
        self.assertTrue(DEFAULT_MATRIX_PATH.is_file(), msg=str(DEFAULT_MATRIX_PATH))

    def test_verify_matrix_passes(self) -> None:
        result = verify_matrix(DEFAULT_MATRIX_PATH)
        self.assertTrue(result.get("ok"), msg=result)
        self.assertEqual(result.get("entries_checked"), 5)
        self.assertEqual(result.get("gap_ids"), ["G-1", "G-2", "G-3", "G-4", "G-5"])

    def test_all_g_entries_present(self) -> None:
        result = verify_matrix(DEFAULT_MATRIX_PATH)
        self.assertIn("G-1", result.get("gap_ids", []))
        self.assertIn("G-5", result.get("gap_ids", []))


if __name__ == "__main__":
    unittest.main()
