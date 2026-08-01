"""Tests for P8.6–8.8 runtime inspect (Wave 2 thin wiring)."""

from __future__ import annotations

import unittest
from pathlib import Path

from delivery.p868_runtime_inspect_v1 import (
    NON_CLAIMS,
    SCHEMA_VERSION,
    inspect_p868_runtime,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestP868RuntimeInspect(unittest.TestCase):
    def test_empty_case_ref_fails_closed(self) -> None:
        result = inspect_p868_runtime("", repo_root=REPO_ROOT)
        self.assertFalse(result["ok"])
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertTrue(result["read_only"])
        self.assertEqual(result["non_claims"], list(NON_CLAIMS))

    def test_demo_phase_gate_only_chain(self) -> None:
        result = inspect_p868_runtime(
            "demo_phase",
            task_type="gate_only",
            repo_root=REPO_ROOT,
        )
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["catalog"]["ok"])
        self.assertEqual(result["catalog"]["collision_tool_ids"], [])
        self.assertGreater(result["catalog"]["tabular_count"], 0)
        self.assertGreater(result["catalog"]["non_tabular_count"], 0)

        self.assertTrue(result["selector"]["ok"])
        self.assertTrue(result["selector"]["plan_only"])
        self.assertGreaterEqual(result["selector"]["candidate_count"], 1)
        self.assertEqual(
            result["selector"]["candidate_tools"][0]["tool_id"],
            "validate.eligibility",
        )

        self.assertTrue(result["executor"]["ok"])
        self.assertEqual(result["executor"]["execution_mode"], "dry_run")
        self.assertTrue(result["executor"]["dry_run"])
        self.assertEqual(result["executor"]["tool_id"], "validate.eligibility")

        self.assertTrue(result["allowlist"]["allowlisted"])
        self.assertTrue(result["allowlist"]["modes"]["dry_run"])
        self.assertFalse(result["allowlist"]["modes"]["sandbox_end_to_end"])

        self.assertIsNotNone(result["nt_selector"])
        self.assertTrue(result["nt_selector"]["ok"])
        self.assertTrue(result["nt_selector"]["plan_only"])

    def test_unknown_case_allowlist_flag(self) -> None:
        result = inspect_p868_runtime(
            "not_a_real_case_xyz",
            task_type="gate_only",
            repo_root=REPO_ROOT,
            include_nt_selector=False,
        )
        # Selector will fail (no intake); allowlist should flag unknown.
        self.assertFalse(result["allowlist"]["allowlisted"])
        self.assertFalse(result["ok"])
        self.assertIsNone(result["nt_selector"])


if __name__ == "__main__":
    unittest.main()
