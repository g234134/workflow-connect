"""Unit tests for notebooks/csv_cleaning/case_eligibility.py (Wave 2 P2)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"
if str(_CSV_CLEANING) not in sys.path:
    sys.path.insert(0, str(_CSV_CLEANING))

from case_eligibility import check_case_eligibility  # noqa: E402

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "eligibility"


def _write_case(tmp: Path, intake: dict, csv_lines: list[str] | None = None) -> Path:
    case_dir = tmp / "case"
    case_dir.mkdir(parents=True)
    (case_dir / "intake.json").write_text(json.dumps(intake, ensure_ascii=False, indent=2), encoding="utf-8")
    if csv_lines is not None:
        (case_dir / "data.csv").write_text("\n".join(csv_lines) + "\n", encoding="utf-8")
    return case_dir


class TestCaseEligibility(unittest.TestCase):
    def test_demo_phase_review_small_row_count(self) -> None:
        result = check_case_eligibility(_REPO_ROOT / "cases" / "demo_phase")
        self.assertTrue(result["ok"])
        self.assertEqual(result["eligibility"], "review_needed")
        self.assertIn("rows<100", result["notes"])
        schema = result["dimensions"]["schema"]
        self.assertEqual(schema["status"], "accepted")
        self.assertIn("phase_demo", schema["notes"])
        self.assertIn("phase_like", schema["notes"])
        self.assertNotIn("multi_row_export", schema["notes"])
        self.assertNotIn("schema_ambiguous", schema["notes"])

    def test_sampleco_schema_multi_row_export_warning(self) -> None:
        result = check_case_eligibility(_REPO_ROOT / "cases" / "sampleco" / "2026-0001")
        self.assertTrue(result["ok"])
        self.assertEqual(result["eligibility"], "accepted")
        schema = result["dimensions"]["schema"]
        self.assertEqual(schema["status"], "accepted")
        self.assertIn("phase_like", schema["notes"])
        self.assertIn("multi_row_export", schema["notes"])
        self.assertIn("schema_ambiguous", schema["notes"])
        self.assertTrue(schema.get("warnings"))

    def test_accepted_low_risk_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            intake = {
                "case_id": "ok-case",
                "data_file": "data.csv",
                "file_format": "csv",
                "encoding": "utf-8",
                "scale": {"row_count": 5000, "file_size_bytes": 500_000},
                "schema": {"field_count": 12},
                "provenance": {"source_type": "owned"},
                "sensitivity": "internal",
                "structure": "text_only",
            }
            case_dir = _write_case(
                Path(tmpdir),
                intake,
                ["id,category,value", "1,a,10", "2,b,20"],
            )
            result = check_case_eligibility(case_dir)
            self.assertEqual(result["eligibility"], "accepted")
            self.assertEqual(result["exit_code"], 0)

    def test_rejected_web_scraping(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            intake = {
                "case_id": "bad-src",
                "data_file": "data.csv",
                "file_format": "csv",
                "encoding": "utf-8",
                "scale": {"row_count": 5000, "file_size_bytes": 500_000},
                "schema": {"field_count": 5},
                "provenance": {"source_type": "web_scraping"},
                "sensitivity": "internal",
                "structure": "text_only",
            }
            case_dir = _write_case(Path(tmpdir), intake, ["id,x", "1,y"])
            result = check_case_eligibility(case_dir)
            self.assertEqual(result["eligibility"], "rejected")
            self.assertEqual(result["reason_code"], "provenance_web_scrape")
            self.assertEqual(result["exit_code"], 1)

    def test_rejected_phi(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            intake = {
                "case_id": "phi-case",
                "data_file": "data.csv",
                "file_format": "csv",
                "encoding": "utf-8",
                "scale": {"row_count": 5000, "file_size_bytes": 500_000},
                "schema": {"field_count": 5},
                "provenance": {"source_type": "owned"},
                "sensitivity": ["phi"],
                "structure": "text_only",
            }
            case_dir = _write_case(Path(tmpdir), intake, ["id,x", "1,y"])
            result = check_case_eligibility(case_dir)
            self.assertEqual(result["eligibility"], "rejected")
            self.assertEqual(result["reason_code"], "phi_not_supported")

    def test_review_pii_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            intake = {
                "case_id": "pii-case",
                "data_file": "data.csv",
                "file_format": "csv",
                "encoding": "utf-8",
                "scale": {"row_count": 5000, "file_size_bytes": 500_000},
                "schema": {"field_count": 5},
                "provenance": {"source_type": "owned"},
                "sensitivity": ["pii"],
                "structure": "text_only",
            }
            case_dir = _write_case(Path(tmpdir), intake, ["id,x", "1,y"])
            result = check_case_eligibility(case_dir)
            self.assertEqual(result["eligibility"], "review_needed")
            self.assertEqual(result["exit_code"], 2)

    def test_rejected_scale_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            intake = {
                "case_id": "huge",
                "data_file": "data.csv",
                "file_format": "csv",
                "encoding": "utf-8",
                "scale": {"row_count": 20_000_000, "file_size_bytes": 500_000},
                "schema": {"field_count": 5},
                "provenance": {"source_type": "owned"},
                "sensitivity": "internal",
                "structure": "text_only",
            }
            case_dir = _write_case(Path(tmpdir), intake, ["id,x", "1,y"])
            result = check_case_eligibility(case_dir)
            self.assertEqual(result["eligibility"], "rejected")
            self.assertEqual(result["reason_code"], "scale_exceeds_capacity")

    def test_missing_intake_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir) / "empty"
            case_dir.mkdir()
            result = check_case_eligibility(case_dir)
            self.assertEqual(result["eligibility"], "review_needed")
            self.assertEqual(result["reason_code"], "missing_intake_json")

    def test_pii_column_heuristic_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            intake = {
                "case_id": "heuristic",
                "data_file": "data.csv",
                "file_format": "csv",
                "encoding": "utf-8",
                "scale": {"row_count": 5000, "file_size_bytes": 500_000},
                "schema": {"field_count": 3},
                "provenance": {"source_type": "owned"},
                "sensitivity": "internal",
                "structure": "text_only",
            }
            case_dir = _write_case(
                Path(tmpdir),
                intake,
                ["id,email,score", "1,a@x.com,1"],
            )
            result = check_case_eligibility(case_dir)
            self.assertEqual(result["eligibility"], "review_needed")
            self.assertIn("possible_pii_columns", result["review_reasons"])


class TestCaseEligibilityCLI(unittest.TestCase):
    def test_cli_demo_phase_exit_code(self) -> None:
        import subprocess

        proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "check_case_eligibility.py"),
                "--case-dir",
                str(_REPO_ROOT / "cases" / "demo_phase"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("eligibility=review_needed", proc.stdout)


if __name__ == "__main__":
    unittest.main()
