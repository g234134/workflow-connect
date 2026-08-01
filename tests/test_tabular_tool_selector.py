"""Unit tests for Tabular Tool Selector v1 (W3-TL-T2)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.tabular_tool_selector import select_tabular_tools

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEMO_PHASE_DIR = _REPO_ROOT / "cases" / "demo_phase"
_SAMPLECO_DIR = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"

_REQUIRED_TOP_KEYS = frozenset(
    {"ok", "message", "selector_rule_id", "plan_only", "candidate_tools"}
)
_REQUIRED_CANDIDATE_KEYS = frozenset(
    {"tool_id", "reason", "requires_force", "human_review_required"}
)


def _load_intake(case_dir: Path) -> dict:
    with (case_dir / "intake.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def _assert_result_shape(result: dict) -> None:
    missing = _REQUIRED_TOP_KEYS - set(result)
    assert not missing, f"missing top-level keys: {sorted(missing)}"
    assert isinstance(result["ok"], bool)
    assert isinstance(result["message"], str)
    assert isinstance(result["selector_rule_id"], str)
    assert result["plan_only"] is True
    assert isinstance(result["candidate_tools"], list)
    for item in result["candidate_tools"]:
        missing_c = _REQUIRED_CANDIDATE_KEYS - set(item)
        assert not missing_c, f"missing candidate keys: {sorted(missing_c)}"


class TestTabularToolSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.demo_intake = _load_intake(_DEMO_PHASE_DIR)
        cls.sampleco_intake = _load_intake(_SAMPLECO_DIR)

    def test_result_dict_has_required_keys(self) -> None:
        result = select_tabular_tools(
            str(_DEMO_PHASE_DIR),
            "clean",
            intake=self.demo_intake,
            gate_notes=["phase_like", "phase_demo"],
        )
        _assert_result_shape(result)

    def test_ac2_demo_phase_clean_requires_force(self) -> None:
        result = select_tabular_tools(
            str(_DEMO_PHASE_DIR),
            "clean",
            intake=self.demo_intake,
            gate_notes=["phase_like", "phase_demo"],
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["selector_rule_id"], "phase_demo.clean.force")
        self.assertEqual(len(result["candidate_tools"]), 1)
        tool = result["candidate_tools"][0]
        self.assertEqual(tool["tool_id"], "clean.phase_demo")
        self.assertTrue(tool["requires_force"])
        self.assertFalse(tool["human_review_required"])

    def test_ac3_sampleco_clean_human_review_required(self) -> None:
        result = select_tabular_tools(
            str(_SAMPLECO_DIR),
            "clean",
            intake=self.sampleco_intake,
            gate_notes=["phase_like", "multi_row_export", "schema_ambiguous"],
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["selector_rule_id"], "sampleco.clean.review")
        self.assertEqual(len(result["candidate_tools"]), 1)
        tool = result["candidate_tools"][0]
        self.assertEqual(tool["tool_id"], "clean.phase_demo")
        self.assertFalse(tool["requires_force"])
        self.assertTrue(tool["human_review_required"])

    def test_ac4_gate_only_eligibility_only(self) -> None:
        result = select_tabular_tools(
            str(_DEMO_PHASE_DIR),
            "gate_only",
            intake=self.demo_intake,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["selector_rule_id"], "gate_only.eligibility")
        tool_ids = [t["tool_id"] for t in result["candidate_tools"]]
        self.assertEqual(tool_ids, ["validate.eligibility"])
        self.assertNotIn("clean.phase_demo", tool_ids)
        self.assertNotIn("export.delivery_bundle", tool_ids)

    def test_ac5_missing_intake_ok_false_empty_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp)
            (case_dir / "raw").mkdir()
            (case_dir / "raw" / "data.csv").write_text("a\n1\n", encoding="utf-8")
            result = select_tabular_tools(
                str(case_dir),
                "clean",
                intake=None,
                gate_notes=["phase_like"],
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.missing_intake")
        self.assertEqual(result["candidate_tools"], [])

    def test_missing_gate_notes_ok_false(self) -> None:
        result = select_tabular_tools(
            str(_DEMO_PHASE_DIR),
            "clean",
            intake=self.demo_intake,
            gate_notes=[],
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.missing_gate_notes")
        self.assertEqual(result["candidate_tools"], [])

    def test_e2e_same_clean_recommendation_demo_phase(self) -> None:
        result = select_tabular_tools(
            str(_DEMO_PHASE_DIR),
            "e2e",
            intake=self.demo_intake,
            gate_notes=["phase_like", "phase_demo"],
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate_tools"][0]["tool_id"], "clean.phase_demo")
        self.assertTrue(result["candidate_tools"][0]["requires_force"])

    def test_bundle_recommends_delivery_when_cleaned_exists(self) -> None:
        result = select_tabular_tools(
            str(_DEMO_PHASE_DIR),
            "bundle",
            intake=self.demo_intake,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["selector_rule_id"], "bundle.delivery")
        self.assertEqual(
            result["candidate_tools"][0]["tool_id"],
            "export.delivery_bundle",
        )

    def test_inferred_gate_notes_demo_phase_without_explicit_notes(self) -> None:
        result = select_tabular_tools(
            str(_DEMO_PHASE_DIR),
            "clean",
            intake=self.demo_intake,
            gate_notes=None,
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["candidate_tools"][0]["requires_force"])


if __name__ == "__main__":
    unittest.main()
