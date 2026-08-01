"""Tests for tabular warning guard policy (v1)."""

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

from tabular_delivery_approval_lib import evaluate_delivery_readiness  # noqa: E402
from tabular_warning_guard_lib import (  # noqa: E402
    compute_delivery_ready_from_policy,
    evaluate_guard_policy,
    resolve_warning_guard_profile,
    should_auto_skip_checkpoint_b,
)


class TestTabularWarningGuardPolicy(unittest.TestCase):
    def test_demo_phase_ok_allows_delivery_ready(self) -> None:
        policy = evaluate_guard_policy("demo_phase", "ok")
        self.assertTrue(policy["delivery_ready_allowed"])
        self.assertTrue(
            compute_delivery_ready_from_policy(
                cp_b_approved=True, e2e_pass=True, policy=policy
            )
        )

    def test_sampleco_warning_fail_closed(self) -> None:
        policy = evaluate_guard_policy("sampleco", "warning")
        self.assertFalse(policy["delivery_ready_allowed"])
        self.assertTrue(policy["partial_ready"])
        self.assertTrue(policy["internal_use_allowed"])
        self.assertFalse(
            compute_delivery_ready_from_policy(
                cp_b_approved=True, e2e_pass=True, policy=policy
            )
        )
        self.assertFalse(
            should_auto_skip_checkpoint_b(
                policy=policy, qa_status="pass", removal_ratio=0.07
            )
        )

    def test_generic_low_risk_warning_partial_only(self) -> None:
        policy = evaluate_guard_policy("generic_low_risk_case", "warning")
        self.assertFalse(policy["delivery_ready_allowed"])
        self.assertTrue(policy["partial_ready"])

    def test_unknown_profile_fail_closed(self) -> None:
        policy = evaluate_guard_policy("unknown", "ok")
        self.assertFalse(policy["delivery_ready_allowed"])
        self.assertFalse(policy["internal_use_allowed"])

    def test_resolve_sampleco_nested_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "cases" / "sampleco" / "2026-0001"
            case_dir.mkdir(parents=True)
            (case_dir / "intake.json").write_text(
                json.dumps({"case_id": "2026-0001", "client_ref": "sampleco"}),
                encoding="utf-8",
            )
            self.assertEqual(resolve_warning_guard_profile(case_dir), "sampleco")

    def test_evaluate_readiness_includes_policy_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = root / "cases" / "sampleco" / "2026-0001"
            reports = case_dir / "reports"
            reports.mkdir(parents=True)
            (case_dir / "intake.json").write_text(
                json.dumps({"case_id": "2026-0001", "client_ref": "sampleco"}),
                encoding="utf-8",
            )
            (reports / "report.json").write_text(
                json.dumps({"output_guard": {"status": "warning"}}),
                encoding="utf-8",
            )
            (reports / "automation_run_log.json").write_text(
                json.dumps(
                    {
                        "steps": [
                            {"step_name": "e2e", "step_status": "completed"},
                            {"step_name": "checkpoint_b", "step_status": "completed"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = evaluate_delivery_readiness(case_dir)
            self.assertEqual(result["warning_guard_profile"], "sampleco")
            self.assertEqual(result["output_guard_status"], "warning")
            self.assertFalse(result["delivery_ready"])
            self.assertTrue(result["partial_ready"])
            self.assertTrue(
                any("partial_ready_internal_only" in gap for gap in result["readiness_gaps"])
            )


if __name__ == "__main__":
    unittest.main()
