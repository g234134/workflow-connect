"""Tests for tabular cleaning profile registry (v1)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"
if str(_CSV_CLEANING) not in sys.path:
    sys.path.insert(0, str(_CSV_CLEANING))

from cleaning_profiles_v1 import (  # noqa: E402
    build_runtime_profile,
    get_profile,
    list_profile_ids,
    resolve_cleaning_profile,
    resolve_runtime_profile,
    validate_profile_schema,
)


class TestCleaningProfilesV1(unittest.TestCase):
    def test_registry_lists_all_profiles(self) -> None:
        ids = list_profile_ids()
        self.assertIn("phase_demo_v1", ids)
        self.assertIn("sampleco_order_profile", ids)
        self.assertIn("generic_low_risk_profile", ids)
        self.assertEqual(len(ids), 3)

    def test_resolve_demo_phase_from_intake(self) -> None:
        case_dir = _REPO_ROOT / "cases" / "demo_phase"
        intake = {"cleaning_profile": "phase_demo_v1"}
        profile, err = resolve_cleaning_profile(case_dir, intake, repo_root=_REPO_ROOT)
        self.assertIsNone(err)
        assert profile is not None
        self.assertEqual(profile["profile_id"], "phase_demo_v1")
        self.assertEqual(profile["risk_level"], "low")
        self.assertEqual(profile["runner"], "clean.phase_demo")

    def test_resolve_sampleco_from_case_dir_fallback(self) -> None:
        case_dir = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"
        profile, err = resolve_cleaning_profile(case_dir, {}, repo_root=_REPO_ROOT)
        self.assertIsNone(err)
        assert profile is not None
        self.assertEqual(profile["profile_id"], "sampleco_order_profile")

    def test_resolve_generic_from_case_dir_fallback(self) -> None:
        case_dir = _REPO_ROOT / "cases" / "internal" / "generic-low-risk"
        profile, err = resolve_cleaning_profile(case_dir, {}, repo_root=_REPO_ROOT)
        self.assertIsNone(err)
        assert profile is not None
        self.assertEqual(profile["profile_id"], "generic_low_risk_profile")
        self.assertEqual(profile["runner"], "clean.generic")

    def test_unknown_profile_errors(self) -> None:
        case_dir = _REPO_ROOT / "cases" / "demo_phase"
        profile, err = resolve_cleaning_profile(
            case_dir, {"cleaning_profile": "nonexistent_profile"}, repo_root=_REPO_ROOT
        )
        self.assertIsNone(profile)
        self.assertIn("unknown_cleaning_profile", err or "")

    def test_sampleco_profile_has_field_roles(self) -> None:
        profile = get_profile("sampleco_order_profile")
        assert profile is not None
        roles = profile["field_roles"]
        self.assertEqual(roles["Phase"], "milestone_phase")
        self.assertIn("missing", profile["rules"])
        self.assertIn("duplicate", profile["rules"])
        self.assertIn("hitl", profile)

    def test_generic_runtime_profile_merges_intake_schema(self) -> None:
        case_dir = _REPO_ROOT / "cases" / "internal" / "generic-low-risk"
        intake_path = case_dir / "intake.json"
        import json

        intake = json.loads(intake_path.read_text(encoding="utf-8"))
        headers = ["order_id", "product", "amount", "notes"]
        runtime, err = resolve_runtime_profile(
            case_dir, intake, repo_root=_REPO_ROOT, csv_headers=headers
        )
        self.assertIsNone(err)
        assert runtime is not None
        self.assertEqual(runtime["profile_id"], "generic_low_risk_profile")
        self.assertEqual(runtime["primary_key"], "order_id")
        self.assertEqual(runtime["field_roles"]["amount"], "numeric")
        self.assertEqual(runtime["dedup_keys"], ["order_id"])

    def test_generic_schema_validation_rejects_missing_pk(self) -> None:
        profile = get_profile("generic_low_risk_profile")
        assert profile is not None
        ok, err = validate_profile_schema(profile, {"schema": {"column_roles": {"x": "text"}}}, ["x"])
        self.assertFalse(ok)
        self.assertIn("primary_key", err or "")


class TestCleanGeneric(unittest.TestCase):
    def test_generic_clean_fixture_produces_five_rows(self) -> None:
        import json

        import clean_generic  # noqa: E402
        from cleaning_profiles_v1 import resolve_runtime_profile  # noqa: E402

        case_dir = _REPO_ROOT / "cases" / "internal" / "generic-low-risk"
        intake = json.loads((case_dir / "intake.json").read_text(encoding="utf-8"))
        csv_path = case_dir / "raw" / "simple_orders.csv"
        rows = clean_generic.read_rows(csv_path)
        headers = list(rows[0].keys())
        runtime, err = resolve_runtime_profile(
            case_dir, intake, repo_root=_REPO_ROOT, csv_headers=headers
        )
        self.assertIsNone(err)
        assert runtime is not None
        cleaned, meta = clean_generic.clean(rows, profile_cfg=runtime)
        self.assertEqual(len(cleaned), 5)
        self.assertEqual(len(meta["dropped_rows"]), 1)
        self.assertEqual(len(meta["deduped_rows"]), 1)


if __name__ == "__main__":
    unittest.main()
