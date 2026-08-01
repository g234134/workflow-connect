"""Unit tests for tabular automation unified driver (v1)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_automation_driver_lib import (  # noqa: E402
    STEP_ORDER,
    normalize_step_name,
    resolve_case_dir,
    run_tabular_automation,
    run_log_path,
)
from tabular_automation_state_lib import start_automation  # noqa: E402


class TestTabularAutomationDriver(unittest.TestCase):
    def test_normalize_step_aliases(self) -> None:
        self.assertEqual(normalize_step_name("gate"), "eligibility")
        self.assertEqual(normalize_step_name("clean"), "cleaning")
        self.assertEqual(normalize_step_name("stats"), "report")
        self.assertIsNone(normalize_step_name("unknown_step"))

    def test_resolve_demo_phase(self) -> None:
        case_dir = resolve_case_dir(case_id="demo_phase")
        self.assertIsNotNone(case_dir)
        assert case_dir is not None
        self.assertTrue((case_dir / "intake.json").is_file())

    def test_dry_run_plans_all_steps(self) -> None:
        case_dir = _REPO_ROOT / "cases" / "demo_phase"
        result = run_tabular_automation(case_dir, dry_run=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["planned_steps"], STEP_ORDER)
        log_path = run_log_path(case_dir)
        self.assertTrue(log_path.is_file())
        log = json.loads(log_path.read_text(encoding="utf-8"))
        self.assertEqual(log["schema_version"], "tabular-automation-run-log-v1")
        self.assertTrue(log["dry_run"])
        self.assertEqual(log.get("cleaning_profile_id"), "phase_demo_v1")

    def test_requires_running_without_dry_run(self) -> None:
        case_dir = _REPO_ROOT / "cases" / "demo_phase"
        result = run_tabular_automation(case_dir, dry_run=False)
        if result.get("automation_status") == "completed":
            self.skipTest("prior completed run; reset state to test guard")
        self.assertFalse(result["ok"])
        self.assertIn("running", result.get("message", ""))


if __name__ == "__main__":
    unittest.main()
