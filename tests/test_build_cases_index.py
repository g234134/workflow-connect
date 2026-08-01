"""Unit tests for scripts/build_cases_index.py and cases_index_lib refresh (W4-MEM-01/02)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cases_index_lib import (  # noqa: E402
    REGISTERED_CASE_DIRS,
    build_case_entry,
    discover_case_dirs,
    refresh_cases_index,
    schema_fingerprint,
)


class TestBuildCasesIndex(unittest.TestCase):
    def test_registered_dirs_include_anchors(self) -> None:
        self.assertIn("cases/demo_phase", REGISTERED_CASE_DIRS)
        self.assertIn("cases/sampleco/2026-0001", REGISTERED_CASE_DIRS)

    def test_discover_includes_anchors_and_client_id(self) -> None:
        discovered = discover_case_dirs(_REPO_ROOT)
        self.assertIn("cases/demo_phase", discovered)
        self.assertIn("cases/sampleco/2026-0001", discovered)
        self.assertIn("cases/acme/2026-0001", discovered)
        self.assertNotIn("cases/_TEMPLATE_case", discovered)
        self.assertFalse(any("/_experiment_samples/" in p or p.endswith("/_TEMPLATE_case") for p in discovered))

    def test_schema_fingerprint_sorted_stable(self) -> None:
        a = schema_fingerprint(["b", "a"])
        b = schema_fingerprint(["a", "b"])
        self.assertEqual(a, b)
        self.assertIsNotNone(a)
        assert a is not None
        self.assertEqual(len(a), 16)
        self.assertIsNone(schema_fingerprint([]))
        self.assertIsNone(schema_fingerprint(None))

    def test_demo_phase_entry_has_cleaning_profile(self) -> None:
        entry = build_case_entry("cases/demo_phase", _REPO_ROOT)
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry["cleaning_profile"], "phase_demo_v1")
        self.assertIn("delivery_template_ref", entry)
        self.assertIsInstance(entry.get("cleaning_rules_applied"), list)
        self.assertIsNotNone(entry.get("schema_fingerprint"))
        self.assertEqual(
            entry["schema_fingerprint"],
            schema_fingerprint(entry["schema_headers"]),
        )

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
        self.assertEqual(entry.get("cleaning_profile"), "sampleco_order_profile")
        ratio = entry.get("accepted_ratio")
        self.assertIsInstance(ratio, float)
        assert isinstance(ratio, float)
        self.assertLess(ratio, 0.1)

    def test_refresh_writes_valid_index(self) -> None:
        result = refresh_cases_index(repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["cases_written"], len(REGISTERED_CASE_DIRS))
        index_path = _REPO_ROOT / "cases" / "index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "gov-cases-index-v0.1")
        case_dirs = {c["case_dir"] for c in data["cases"]}
        self.assertIn("cases/demo_phase", case_dirs)
        self.assertIn("cases/sampleco/2026-0001", case_dirs)
        for case in data["cases"]:
            if case.get("schema_headers"):
                self.assertEqual(
                    case.get("schema_fingerprint"),
                    schema_fingerprint(case["schema_headers"]),
                )

    def test_temp_dir_index_refresh_discovers_new_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_rel = "cases/acme/2026-0002"
            case_dir = root / case_rel
            raw_dir = case_dir / "raw"
            raw_dir.mkdir(parents=True)
            (case_dir / "intake.json").write_text(
                json.dumps(
                    {
                        "client_ref": "acme",
                        "case_id": "2026-0002",
                        "product_sku": "CLEAN-BASIC",
                        "data_file": "raw/orders.csv",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (raw_dir / "orders.csv").write_text("id,name\n1,alpha\n", encoding="utf-8")

            index_path = root / "cases" / "index.json"
            result = refresh_cases_index(index_path=index_path, repo_root=root)
            self.assertTrue(result["ok"])
            self.assertGreaterEqual(result["cases_written"], 1)
            data = json.loads(index_path.read_text(encoding="utf-8"))
            by_dir = {c["case_dir"]: c for c in data["cases"]}
            self.assertIn(case_rel, by_dir)
            entry = by_dir[case_rel]
            self.assertEqual(entry["client_ref"], "acme")
            self.assertIsNotNone(entry.get("schema_fingerprint"))
            self.assertEqual(
                entry["schema_fingerprint"],
                schema_fingerprint(["id", "name"]),
            )
            # Missing anchors under temp root are skipped — not silently invented.
            self.assertNotIn("cases/demo_phase", by_dir)


if __name__ == "__main__":
    unittest.main()
