"""Unit tests for Tabular tri-case HITL matrix contract (spec-only · TAB-S5-WS-A-T3)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from run_tabular_mainline_regression_smoke import SMOKE_CASES  # noqa: E402
from verify_tabular_tri_case_hitl_matrix import (  # noqa: E402
    DEFAULT_MATRIX_PATH,
    REQUIRED_CASE_IDS,
    verify_matrix,
)


class TestTabularTriCaseHitlMatrixV1(unittest.TestCase):
    def test_matrix_file_exists(self) -> None:
        self.assertTrue(DEFAULT_MATRIX_PATH.is_file(), msg=str(DEFAULT_MATRIX_PATH))

    def test_verify_matrix_passes(self) -> None:
        result = verify_matrix(DEFAULT_MATRIX_PATH)
        self.assertTrue(result.get("ok"), msg=result)
        self.assertEqual(result.get("entries_checked"), 3)
        self.assertEqual(result.get("case_ids"), list(REQUIRED_CASE_IDS))

    def test_all_tri_case_entries_present(self) -> None:
        result = verify_matrix(DEFAULT_MATRIX_PATH)
        for case_id in REQUIRED_CASE_IDS:
            self.assertIn(case_id, result.get("case_ids", []))

    def test_smoke_registry_has_three_cases_aligned_with_matrix(self) -> None:
        self.assertEqual(len(SMOKE_CASES), 3)
        smoke_ids = {spec["case_id"] for spec in SMOKE_CASES}
        self.assertEqual(smoke_ids, set(REQUIRED_CASE_IDS))

        by_id = {spec["case_id"]: spec for spec in SMOKE_CASES}
        expected_delivery = {
            "demo_phase": True,
            "2026-0001": False,
            "generic-low-risk": True,
        }
        for case_id, expected in expected_delivery.items():
            self.assertEqual(by_id[case_id]["expected_delivery_ready"], expected)


if __name__ == "__main__":
    unittest.main()
