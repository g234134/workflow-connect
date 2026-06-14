"""Unit tests for scripts/build_cases_index.py and cases_index_lib refresh (W4-MEM-01)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cases_index_lib import (  # noqa: E402
    REGISTERED_CASE_DIRS,
    build_case_entry,
    refresh_cases_index,
)


class TestBuildCasesIndex(unittest.TestCase):
    def test_registered_dirs_include_anchors(self) -> None:
        self.assertIn("cases/demo_phase", REGISTERED_CASE_DIRS)
        self.assertIn("cases/sampleco/2026-0001", REGISTERED_CASE_DIRS)

    def test_demo_phase_entry_has_cleaning_profile(self) -> None:
        entry = build_case_entry("cases/demo_phase", _REPO_ROOT)
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry["cleaning_profile"], "phase_demo_v1")
        self.assertIn("delivery_template_ref", entry)
        self.assertIsInstance(entry.get("cleaning_rules_applied"), list)

    def test_sampleco_entry_enriched_limits(self) -> None:
        entry = build_case_entry("cases/sampleco/2026-0001", _REPO_ROOT)
        self.assertIsNotNone(entry)
        assert entry is not None
        limits = entry.get("known_limits") or []
        self.assertIn("low_accepted_ratio", limits)
        self.assertTrue(
            "multi_row_export" in limits or "multi_row_milestone_export" in limits,
            msg=f"expected multi_row tag in {limits}",
        )
        self.assertEqual(entry.get("cleaning_profile"), "clean_basic_demo")
        ratio = entry.get("accepted_ratio")
        self.assertIsInstance(ratio, float)
        assert isinstance(ratio, float)
        self.assertLess(ratio, 0.1)

    def test_refresh_writes_valid_index(self) -> None:
        result = refresh_cases_index(repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"])
        self.assertEqual(result["cases_written"], len(REGISTERED_CASE_DIRS))
        index_path = _REPO_ROOT / "cases" / "index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "gov-cases-index-v0.1")
        case_dirs = {c["case_dir"] for c in data["cases"]}
        self.assertIn("cases/sampleco/2026-0001", case_dirs)


if __name__ == "__main__":
    unittest.main()
