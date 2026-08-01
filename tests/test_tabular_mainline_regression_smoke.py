"""Unit tests for tri-case Tabular mainline regression smoke contract."""



from __future__ import annotations



import sys

import unittest

from pathlib import Path



_REPO_ROOT = Path(__file__).resolve().parents[1]

_SCRIPTS = _REPO_ROOT / "scripts"

if str(_SCRIPTS) not in sys.path:

    sys.path.insert(0, str(_SCRIPTS))



from run_tabular_mainline_regression_smoke import (  # noqa: E402

    SMOKE_CASES,

    run_tabular_mainline_regression_smoke,

)

from tabular_regression_smoke_lib import verify_case_regression  # noqa: E402





class TestSmokeCaseRegistry(unittest.TestCase):

    def test_smoke_registry_has_three_anchor_cases(self) -> None:

        self.assertEqual(len(SMOKE_CASES), 3)

        case_ids = {spec["case_id"] for spec in SMOKE_CASES}

        self.assertEqual(

            case_ids,

            {"demo_phase", "2026-0001", "generic-low-risk"},

        )



    def test_expected_delivery_ready_contract(self) -> None:

        by_id = {spec["case_id"]: spec for spec in SMOKE_CASES}

        self.assertTrue(by_id["demo_phase"]["expected_delivery_ready"])

        self.assertFalse(by_id["2026-0001"]["expected_delivery_ready"])

        self.assertTrue(by_id["generic-low-risk"]["expected_delivery_ready"])



    def test_smoke_case_dirs_exist(self) -> None:

        for spec in SMOKE_CASES:

            case_dir = _REPO_ROOT / spec["case_dir"]

            self.assertTrue(case_dir.is_dir(), spec["case_dir"])

            self.assertTrue((case_dir / "intake.json").is_file())





class TestVerifyCaseRegressionContract(unittest.TestCase):

    def test_sampleco_delivery_ready_false_is_allowed_when_expected(self) -> None:

        case_dir = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"

        if not (case_dir / "automation_state.json").is_file():

            self.skipTest("sampleco automation_state not present")

        result = verify_case_regression(

            case_dir,

            repo_root=_REPO_ROOT,

            case_id="2026-0001",

            expected_delivery_ready=False,

        )

        self.assertFalse(result.get("delivery_ready"))

        self.assertNotIn(

            "delivery_ready=false",

            " ".join(result.get("failures") or []),

        )



    def test_sampleco_would_fail_if_delivery_ready_expected_true(self) -> None:

        case_dir = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"

        if not (case_dir / "automation_state.json").is_file():

            self.skipTest("sampleco automation_state not present")

        result = verify_case_regression(

            case_dir,

            repo_root=_REPO_ROOT,

            case_id="2026-0001",

            expected_delivery_ready=True,

        )

        self.assertFalse(result.get("ok"))

        self.assertTrue(any("expected True" in f for f in result.get("failures") or []))





class TestSmokeDryRun(unittest.TestCase):

    def test_dry_run_returns_three_planned_cases(self) -> None:

        result = run_tabular_mainline_regression_smoke(dry_run=True)

        self.assertTrue(result.get("ok"))

        self.assertEqual(result.get("case_count"), 3)

        self.assertEqual(result.get("passed"), 3)

        for case in result.get("cases") or []:

            self.assertTrue(case.get("dry_run"))





if __name__ == "__main__":

    unittest.main()

