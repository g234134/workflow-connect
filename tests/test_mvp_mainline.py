"""MVP mainline regression tests (Wave 1 · W1-T3).

Lightweight end-to-end checks for the cleaning main chain:
  gate → cleaning → bundle (via scripts/run_case_e2e_validation.py)

Standard fixtures: cases/demo_phase, cases/sampleco/2026-0001
(see docs/MVP_DEMO_WALKTHROUGH_v0.1.md · docs/MVP_CASE_E2E_DoD_v0.1.md)
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from run_case_e2e_validation import run_case_e2e_validation  # noqa: E402

_DEMO_PHASE = _REPO_ROOT / "cases" / "demo_phase"
_SAMPLECO = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"
_GENERIC_LOW_RISK = _REPO_ROOT / "cases" / "internal" / "generic-low-risk"
_E2E_CLI = _REPO_ROOT / "scripts" / "run_case_e2e_validation.py"

_REQUIRED_ARTIFACTS = (
    "cleaned",
    "reports/report.json",
    "reports/report.md",
    "reports/cleaning_stats.json",
    "delivery_signoff.md",
)


def _parse_cli_json(stdout: str) -> dict:
    """Extract root result dict from CLI stdout (human summary precedes JSON)."""
    start = stdout.rfind("\n{")
    if start < 0:
        start = stdout.find("{")
    if start < 0:
        return {}
    if stdout[start] == "\n":
        start += 1
    try:
        obj, _ = json.JSONDecoder().raw_decode(stdout[start:])
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    return {}


def _assert_artifacts(case_dir: Path) -> None:
    missing = [rel for rel in _REQUIRED_ARTIFACTS if not (case_dir / rel).exists()]
    if missing:
        raise AssertionError(f"missing artifacts under {case_dir}: {', '.join(missing)}")


class TestMvpMainlineDemoPhase(unittest.TestCase):
    """Regression: internal demo anchor (review_needed → forced clean → bundle)."""

    case_dir = _DEMO_PHASE

    @classmethod
    def setUpClass(cls) -> None:
        if not cls.case_dir.is_dir():
            raise unittest.SkipTest(f"fixture missing: {cls.case_dir}")

    def test_e2e_passes_with_force_review(self) -> None:
        result = run_case_e2e_validation(self.case_dir, force_review=True)
        self.assertTrue(result["ok"], result.get("message") or result.get("steps"))
        self.assertEqual(result["eligibility"], "review_needed")

        steps = result["steps"]
        self.assertTrue(steps["gate"]["ok"], steps["gate"])
        self.assertTrue(steps["cleaning"]["ok"], steps["cleaning"])
        self.assertTrue(steps["cleaning"].get("forced"), "demo_phase expects forced clean")
        self.assertTrue(steps["bundle"]["ok"], steps["bundle"])

        report = json.loads((self.case_dir / "reports" / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["total_rows"], 7)
        self.assertEqual(report["summary"]["accepted_rows"], 5)
        _assert_artifacts(self.case_dir)

    def test_cli_exit_zero_and_pass_banner(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_E2E_CLI),
                "--case-dir",
                str(self.case_dir),
                "--json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("overall_ok:   True", proc.stdout)
        data = _parse_cli_json(proc.stdout)
        self.assertTrue(data.get("ok"), data.get("message"))


class TestMvpMainlineSampleco(unittest.TestCase):
    """Regression: real-style sample (accepted gate · ratio guard warning)."""

    case_dir = _SAMPLECO

    @classmethod
    def setUpClass(cls) -> None:
        if not cls.case_dir.is_dir():
            raise unittest.SkipTest(f"fixture missing: {cls.case_dir}")

    def test_e2e_passes_accepted_gate(self) -> None:
        result = run_case_e2e_validation(self.case_dir, force_review=True)
        self.assertTrue(result["ok"], result.get("message") or result.get("steps"))
        self.assertEqual(result["eligibility"], "accepted")

        steps = result["steps"]
        self.assertTrue(steps["gate"]["ok"], steps["gate"])
        self.assertTrue(steps["cleaning"]["ok"], steps["cleaning"])
        self.assertFalse(steps["cleaning"].get("forced"), "sampleco should not need --force")
        self.assertTrue(steps["bundle"]["ok"], steps["bundle"])

        report = json.loads((self.case_dir / "reports" / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["total_rows"], 115)
        self.assertEqual(report["summary"]["accepted_rows"], 8)

        guard = result.get("output_guard") or report.get("output_guard")
        self.assertIsNotNone(guard, "expected output_guard on bundle/report")
        self.assertEqual(guard["status"], "warning")
        _assert_artifacts(self.case_dir)

    def test_cli_exit_zero(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_E2E_CLI),
                "--case-dir",
                str(self.case_dir),
                "--json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        data = _parse_cli_json(proc.stdout)
        self.assertTrue(data.get("ok"), data.get("message"))


class TestMvpMainlineFailureSignals(unittest.TestCase):
    """Ensure regressions surface non-zero exit and readable errors."""

    def test_missing_case_dir_fails(self) -> None:
        bogus = _REPO_ROOT / "cases" / "__mvp_regression_missing__"
        result = run_case_e2e_validation(bogus)
        self.assertFalse(result["ok"])
        self.assertIn("case structure incomplete", result.get("message", ""))

    def test_cli_missing_case_exit_nonzero(self) -> None:
        bogus = _REPO_ROOT / "cases" / "__mvp_regression_missing__"
        proc = subprocess.run(
            [
                sys.executable,
                str(_E2E_CLI),
                "--case-dir",
                str(bogus),
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertNotEqual(proc.returncode, 0, "expected failure exit code")
        self.assertIn("overall_ok:   False", proc.stdout)


class TestMvpMainlineGenericLowRisk(unittest.TestCase):
    """Regression: generic low-risk profile (primary key + numeric table)."""

    case_dir = _GENERIC_LOW_RISK

    @classmethod
    def setUpClass(cls) -> None:
        if not cls.case_dir.is_dir():
            raise unittest.SkipTest(f"fixture missing: {cls.case_dir}")

    def test_e2e_passes_with_force_review(self) -> None:
        result = run_case_e2e_validation(self.case_dir, force_review=True)
        self.assertTrue(result["ok"], result.get("message") or result.get("steps"))
        steps = result["steps"]
        self.assertTrue(steps["gate"]["ok"], steps["gate"])
        self.assertTrue(steps["cleaning"]["ok"], steps["cleaning"])
        self.assertTrue(steps["bundle"]["ok"], steps["bundle"])
        _assert_artifacts(self.case_dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)
