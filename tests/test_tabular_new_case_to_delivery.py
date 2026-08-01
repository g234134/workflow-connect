"""Unit tests for Tabular intake → delivery orchestration."""



from __future__ import annotations



import sys

import unittest

from pathlib import Path



_REPO_ROOT = Path(__file__).resolve().parents[1]

_SCRIPTS = _REPO_ROOT / "scripts"

if str(_SCRIPTS) not in sys.path:

    sys.path.insert(0, str(_SCRIPTS))



from tabular_new_case_to_delivery_lib import (  # noqa: E402

    resolve_auto_resume_policy,

    run_new_case_to_delivery,

)





class TestAutoResumePolicy(unittest.TestCase):

    def test_generic_low_risk_allows_auto_resume(self) -> None:

        case_dir = _REPO_ROOT / "cases" / "internal" / "generic-low-risk"

        policy = resolve_auto_resume_policy(case_dir, repo_root=_REPO_ROOT)

        self.assertTrue(policy.get("auto_resume_allowed"))

        self.assertIsNone(policy.get("will_pause_at"))



    def test_sampleco_blocks_silent_full_auto(self) -> None:

        case_dir = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"

        policy = resolve_auto_resume_policy(case_dir, repo_root=_REPO_ROOT)

        self.assertFalse(policy.get("auto_resume_allowed"))

        self.assertEqual(policy.get("will_pause_at"), "checkpoint_b")





class TestNewCaseToDeliveryDryRun(unittest.TestCase):

    def test_generic_low_risk_dry_run_phases(self) -> None:

        case_dir = _REPO_ROOT / "cases" / "internal" / "generic-low-risk"

        result = run_new_case_to_delivery(

            case_dir,

            repo_root=_REPO_ROOT,

            start=True,

            dry_run=True,

        )

        self.assertTrue(result.get("ok"))

        self.assertTrue(result.get("dry_run"))

        self.assertTrue(result.get("auto_resume_allowed"))

        self.assertIsNone(result.get("will_pause_at"))

        phases = result.get("phases") or []

        self.assertIn("run_tabular_automation", phases)

        self.assertIn("auto_resume_hitl (internal allowlist only)", phases)



    def test_sampleco_dry_run_will_pause_at_checkpoint_b(self) -> None:

        case_dir = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"

        result = run_new_case_to_delivery(

            case_dir,

            repo_root=_REPO_ROOT,

            start=True,

            dry_run=True,

        )

        self.assertTrue(result.get("ok"))

        self.assertFalse(result.get("auto_resume_allowed"))

        self.assertEqual(result.get("will_pause_at"), "checkpoint_b")

        phases = result.get("phases") or []

        self.assertNotIn("auto_resume_hitl (internal allowlist only)", phases)



    def test_dry_run_output_shape(self) -> None:

        case_dir = _REPO_ROOT / "cases" / "demo_phase"

        result = run_new_case_to_delivery(

            case_dir,

            repo_root=_REPO_ROOT,

            dry_run=True,

        )

        for key in ("ok", "phases", "delivery_ready", "zip_path", "will_pause_at"):

            self.assertIn(key, result)





if __name__ == "__main__":

    unittest.main()

