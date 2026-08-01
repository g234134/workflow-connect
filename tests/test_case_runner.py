"""Unit tests for parameterized case-dir cleaning runner (Wave 2 P3)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"
_DEMO_CASE = _REPO_ROOT / "cases" / "demo_phase"
_RUNNER = _CSV_CLEANING / "clean_phase_demo.py"

if str(_CSV_CLEANING) not in sys.path:
    sys.path.insert(0, str(_CSV_CLEANING))

import clean_phase_demo  # noqa: E402
from case_intake_loader import load_case_runner_config  # noqa: E402


class TestCaseIntakeLoader(unittest.TestCase):
    def test_demo_phase_config_resolves_paths(self) -> None:
        config = load_case_runner_config(_DEMO_CASE)
        self.assertTrue(config["ok"])
        self.assertEqual(config["case_id"], "demo_phase")
        self.assertTrue(config["input_path"].name == "Phase.csv")
        self.assertEqual(config["output_path"].name, "Phase_cleaned.csv")
        self.assertEqual(config["report_json_path"].name, "report.json")

    def test_missing_intake_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir) / "empty_case"
            case_dir.mkdir()
            config = load_case_runner_config(case_dir)
            self.assertFalse(config["ok"])
            self.assertEqual(config["message"], "missing_intake_json")


class TestCaseRunnerCLI(unittest.TestCase):
    def _run(self, *extra: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(_RUNNER), *extra]
        return subprocess.run(cmd, cwd=_REPO_ROOT, capture_output=True, text=True, check=False)

    def test_demo_phase_skip_eligibility(self) -> None:
        proc = self._run("--case-dir", "cases/demo_phase", "--skip-eligibility")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["input_rows"], 7)
        self.assertEqual(payload["output_rows"], 5)
        self.assertTrue((_DEMO_CASE / "cleaned" / "Phase_cleaned.csv").is_file())
        self.assertTrue((_DEMO_CASE / "reports" / "report.json").is_file())
        self.assertTrue((_DEMO_CASE / "reports" / "cleaning_stats.json").is_file())
        self.assertTrue((_DEMO_CASE / "reports" / "report.md").is_file())

    def test_temp_case_copy_produces_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir) / "demo_copy"
            shutil.copytree(_DEMO_CASE, case_dir)
            for sub in ("cleaned", "reports"):
                target = case_dir / sub
                if target.is_dir():
                    shutil.rmtree(target)
                target.mkdir()

            proc = self._run("--case-dir", str(case_dir), "--skip-eligibility")
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            self.assertTrue((case_dir / "cleaned" / "Phase_cleaned.csv").is_file())
            self.assertTrue((case_dir / "reports" / "report.json").is_file())

    def test_missing_default_case_dir_errors(self) -> None:
        original = clean_phase_demo.DEFAULT_CASE_DIR
        try:
            clean_phase_demo.DEFAULT_CASE_DIR = Path("/nonexistent/demo_phase_anchor")
            case_dir, err = clean_phase_demo.resolve_case_dir(None)
            self.assertIsNone(case_dir)
            self.assertIsNotNone(err)
            self.assertIn("demo_phase", err)
        finally:
            clean_phase_demo.DEFAULT_CASE_DIR = original


if __name__ == "__main__":
    unittest.main()
