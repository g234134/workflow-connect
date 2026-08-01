"""Unit tests for W4-GUARD G2–G4 opt-in escalation (FP-G1-T3)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from w4_guard_escalation_v1 import (  # noqa: E402
    DEFAULT_RATIO_BLOCK,
    evaluate_guard_escalation,
)


def _sampleco_eligibility() -> dict:
    return {
        "eligibility": "accepted",
        "dimensions": {
            "schema": {
                "notes": ["phase_like", "multi_row_export", "schema_ambiguous"],
                "warnings": ["phase_like_headers_but_multi_row_or_sprint_pattern"],
            }
        },
    }


def _sampleco_guard(ratio: float = 8 / 115) -> dict:
    return {
        "status": "warning",
        "ratio": ratio,
        "input_rows": 115,
        "output_rows": 8,
        "threshold": 0.5,
        "schema_flags": ["multi_row_export", "schema_ambiguous"],
    }


class TestGuardEscalationDefaultSafe(unittest.TestCase):
    def test_default_observation_only_no_e2e_fail(self) -> None:
        esc = evaluate_guard_escalation(
            eligibility_raw=_sampleco_eligibility(),
            output_guard=_sampleco_guard(),
            qa_status="pass_with_warnings",
        )
        self.assertTrue(esc["ok"])
        self.assertTrue(esc["signals"]["g2_schema_ambiguous"])
        self.assertTrue(esc["signals"]["g3_ratio_warning"])
        self.assertTrue(esc["signals"]["g3_block_delivery"])
        self.assertTrue(esc["signals"]["g4_strict_candidate"])
        self.assertEqual(esc["applied"], {})
        self.assertFalse(esc["e2e_fail"])
        self.assertEqual(esc["message"], "observation_only_default_safe")
        self.assertFalse(esc["flags"]["strict_guards"])

    def test_demo_phase_no_g2(self) -> None:
        esc = evaluate_guard_escalation(
            eligibility_raw={
                "dimensions": {"schema": {"notes": ["phase_like", "phase_demo"]}}
            },
            output_guard={"status": "ok", "ratio": 0.71},
            qa_status="pass",
        )
        self.assertFalse(esc["signals"]["g2_schema_ambiguous"])
        self.assertFalse(esc["signals"]["g3_ratio_warning"])
        self.assertFalse(esc["e2e_fail"])


class TestGuardEscalationOptIn(unittest.TestCase):
    def test_enable_g2_applies_review_needed(self) -> None:
        esc = evaluate_guard_escalation(
            eligibility_raw=_sampleco_eligibility(),
            output_guard=_sampleco_guard(),
            qa_status="pass_with_warnings",
            enable_g2=True,
        )
        self.assertEqual(esc["applied"].get("gate_eligibility"), "review_needed")
        self.assertFalse(esc["e2e_fail"])

    def test_enable_g3_applies_block_delivery(self) -> None:
        esc = evaluate_guard_escalation(
            eligibility_raw=_sampleco_eligibility(),
            output_guard=_sampleco_guard(),
            qa_status="pass_with_warnings",
            enable_g3=True,
        )
        self.assertEqual(esc["applied"].get("delivery"), "block_delivery")
        self.assertLess(esc["ratio"], DEFAULT_RATIO_BLOCK)

    def test_strict_guards_fails_e2e_on_g4(self) -> None:
        esc = evaluate_guard_escalation(
            eligibility_raw=_sampleco_eligibility(),
            output_guard=_sampleco_guard(),
            qa_status="pass_with_warnings",
            strict_guards=True,
        )
        self.assertTrue(esc["e2e_fail"])
        self.assertEqual(esc["applied"].get("e2e"), "fail")
        self.assertTrue(esc["flags"]["strict_guards"])

    def test_strict_guards_without_g4_signal_does_not_fail(self) -> None:
        esc = evaluate_guard_escalation(
            eligibility_raw={"dimensions": {"schema": {"notes": ["phase_like"]}}},
            output_guard={"status": "ok", "ratio": 0.9},
            qa_status="pass",
            strict_guards=True,
        )
        self.assertFalse(esc["signals"]["g4_strict_candidate"])
        self.assertFalse(esc["e2e_fail"])


if __name__ == "__main__":
    unittest.main()
