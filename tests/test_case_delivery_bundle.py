"""Unit tests for case delivery bundle builder (Wave 2 P4)."""

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
if str(_CSV_CLEANING) not in sys.path:
    sys.path.insert(0, str(_CSV_CLEANING))

from case_delivery_bundle import build_case_delivery_bundle  # noqa: E402

_DEMO = _REPO_ROOT / "cases" / "demo_phase"
_BUNDLE_SCRIPT = _REPO_ROOT / "scripts" / "build_case_delivery_bundle.py"


class TestCaseDeliveryBundle(unittest.TestCase):
    def test_demo_phase_bundle_ok(self) -> None:
        result = build_case_delivery_bundle(_DEMO, refresh_eligibility=True)
        self.assertTrue(result["ok"], result.get("message"))
        self.assertEqual(result["case_id"], "demo_phase")
        self.assertIn(result["eligibility_status"], ("accepted", "rejected", "review_needed"))

        eligibility_path = _DEMO / "reports" / "eligibility_result.json"
        self.assertTrue(eligibility_path.is_file())
        eligibility = json.loads(eligibility_path.read_text(encoding="utf-8"))
        self.assertIn(eligibility["status"], ("accepted", "rejected", "review_needed"))
        self.assertIn("checked_at", eligibility)
        self.assertIn("dimensions_summary", eligibility)

        signoff = _DEMO / "delivery_signoff.md"
        self.assertTrue(signoff.is_file())
        text = signoff.read_text(encoding="utf-8")
        self.assertIn("demo_phase", text)

        report = json.loads((_DEMO / "reports" / "report.json").read_text(encoding="utf-8"))
        for key in ("case_id", "client_ref", "product_sku", "cleaning_stats", "issues_summary", "generated_at"):
            self.assertIn(key, report, msg=f"missing report v1 key: {key}")

    def test_temp_case_bundle_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir) / "bundle_case"
            shutil.copytree(_DEMO, case_dir)
            intake_path = case_dir / "intake.json"
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
            intake["case_id"] = "bundle_case"
            intake_path.write_text(json.dumps(intake, ensure_ascii=False, indent=2), encoding="utf-8")
            signoff = case_dir / "delivery_signoff.md"
            if signoff.is_file():
                signoff.unlink()
            elig = case_dir / "reports" / "eligibility_result.json"
            if elig.is_file():
                elig.unlink()

            proc = subprocess.run(
                [sys.executable, str(_BUNDLE_SCRIPT), "--case-dir", str(case_dir)],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

            required = [
                case_dir / "cleaned" / "Phase_cleaned.csv",
                case_dir / "reports" / "report.json",
                case_dir / "reports" / "report.md",
                case_dir / "reports" / "eligibility_result.json",
                case_dir / "delivery_signoff.md",
            ]
            for path in required:
                self.assertTrue(path.is_file(), f"missing {path.name}")

            signoff_text = (case_dir / "delivery_signoff.md").read_text(encoding="utf-8")
            self.assertIn("bundle_case", signoff_text)
            self.assertIn("Eligibility summary", signoff_text)

    def test_missing_cleaned_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir) / "empty_case"
            case_dir.mkdir()
            (case_dir / "reports").mkdir()
            (case_dir / "reports" / "report.json").write_text("{}", encoding="utf-8")
            (case_dir / "intake.json").write_text(
                json.dumps({"case_id": "empty_case", "client_ref": "test"}),
                encoding="utf-8",
            )
            result = build_case_delivery_bundle(case_dir)
            self.assertFalse(result["ok"])
            self.assertIn("cleaned/*.csv", result.get("missing", []))


if __name__ == "__main__":
    unittest.main()
