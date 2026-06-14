"""Unit tests for scripts/lookup_case_history.py (Wave 4A W-MVP-W4A-MEMO-LOOKUP)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOOKUP = _REPO_ROOT / "scripts" / "lookup_case_history.py"
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cases_index_lib import lookup_cases, schema_headers_match  # noqa: E402


def _run_lookup(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(_LOOKUP), *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"lookup failed rc={proc.returncode} stderr={proc.stderr}")
    return json.loads(proc.stdout)


class TestLookupCaseHistory(unittest.TestCase):
    def test_list_all_includes_demo_and_sampleco(self) -> None:
        result = _run_lookup("--list-all")
        self.assertTrue(result["ok"])
        dirs = {m["case_dir"] for m in result["matches"]}
        self.assertIn("cases/demo_phase", dirs)
        self.assertIn("cases/sampleco/2026-0001", dirs)
        self.assertGreaterEqual(len(result["matches"]), 2)

    def test_client_ref_sampleco_filters_single_case(self) -> None:
        result = _run_lookup("--client-ref", "SAMPLECO")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["matches"]), 1)
        match = result["matches"][0]
        self.assertEqual(match["case_dir"], "cases/sampleco/2026-0001")
        self.assertEqual(match["client_ref"], "sampleco")
        self.assertEqual(match.get("cleaning_profile"), "clean_basic_demo")
        self.assertIn("low_accepted_ratio", match.get("known_limits") or [])

    def test_verbose_includes_rules_and_template(self) -> None:
        result = _run_lookup("--client-ref", "sampleco", "--verbose")
        self.assertTrue(result["ok"])
        match = result["matches"][0]
        self.assertIn("cleaning_rules_applied", match)
        self.assertIn("delivery_template_ref", match)
        self.assertIn("dedup_by_phase", match["cleaning_rules_applied"])
        self.assertEqual(match.get("qa_status"), "pass_with_warnings")

    def test_schema_headers_subset_match(self) -> None:
        headers = "Phase,名稱"
        result = _run_lookup("--schema-headers", headers)
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(len(result["matches"]), 1)
        for match in result["matches"]:
            self.assertIn("gate_status", match)
            self.assertIsInstance(match["known_limits"], list)

    def test_schema_headers_match_helper_exact_and_subset(self) -> None:
        case = ["Phase", "名稱", "之前", "現在（建議）"]
        self.assertTrue(schema_headers_match(case, ["Phase", "名稱"]))
        self.assertTrue(schema_headers_match(case, case))
        self.assertFalse(schema_headers_match(case, ["Phase", "missing_col"]))

    def test_lookup_module_client_ref_case_insensitive(self) -> None:
        result = lookup_cases(client_ref="SAMPLECO")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["matches"]), 1)


if __name__ == "__main__":
    unittest.main()
