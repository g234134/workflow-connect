"""Unit tests for scripts/new_cleaning_case.py (Wave 3 W-MVP-W3-INTAKE-CLI)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "scripts" / "new_cleaning_case.py"
_DEMO_CSV = _REPO_ROOT / "cases" / "demo_phase" / "raw" / "Phase.csv"

_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from new_cleaning_case import create_cleaning_case  # noqa: E402


class TestNewCleaningCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.cases_root = self.tmp / "cases"
        self.cases_root.mkdir()
        template = _REPO_ROOT / "cases" / "_TEMPLATE_case"
        shutil.copytree(template, self.cases_root / "_TEMPLATE_case")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_create_case_dir_and_intake(self) -> None:
        source = self.tmp / "input.csv"
        shutil.copy2(_DEMO_CSV, source)

        result = create_cleaning_case(
            client_ref="ACME",
            product_sku="CLEAN-BASIC",
            source_file=source,
            encoding="utf-8",
            delimiter=",",
            repo_root=self.tmp,
        )
        self.assertTrue(result["ok"], result.get("message"))
        case_dir = Path(result["case_dir"])
        self.assertTrue(case_dir.is_dir())
        self.assertTrue((case_dir / "intake.json").is_file())
        self.assertTrue((case_dir / "raw" / "input.csv").is_file())
        self.assertTrue((case_dir / "cleaned").is_dir())
        self.assertTrue((case_dir / "reports").is_dir())
        self.assertTrue((case_dir / "delivery_signoff.md").is_file())

        intake = json.loads((case_dir / "intake.json").read_text(encoding="utf-8"))
        self.assertEqual(intake["client_ref"], "acme")
        self.assertEqual(intake["product_sku"], "CLEAN-BASIC")
        self.assertEqual(intake["data_file"], "raw/input.csv")
        self.assertEqual(intake["file_format"], "csv")
        self.assertEqual(intake["encoding"], "utf-8")
        self.assertIn("row_count", intake["scale"])
        self.assertIn("file_size_bytes", intake["scale"])

    def test_cli_with_run_gate(self) -> None:
        if not _DEMO_CSV.is_file():
            self.skipTest("demo Phase.csv missing")

        client_slug = "w3-intake-cli-test"
        client_dir = _REPO_ROOT / "cases" / client_slug
        try:
            cmd = [
                sys.executable,
                str(_SCRIPT),
                "--client-ref",
                client_slug,
                "--product-sku",
                "CLEAN-BASIC",
                "--source-file",
                str(_DEMO_CSV),
                "--encoding",
                "utf-8-sig",
                "--run-gate",
            ]
            proc = subprocess.run(
                cmd,
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
            self.assertIn("gate_status:", proc.stdout)
            self.assertIn("eligibility=", proc.stdout)
            self.assertIn("review_needed", proc.stdout)
        finally:
            if client_dir.is_dir():
                shutil.rmtree(client_dir)


    def test_cli_with_run_p75_gate(self) -> None:
        if not _DEMO_CSV.is_file():
            self.skipTest("demo Phase.csv missing")

        client_slug = "w1-p75-intake-cli-test"
        client_dir = _REPO_ROOT / "cases" / client_slug
        try:
            cmd = [
                sys.executable,
                str(_SCRIPT),
                "--client-ref",
                client_slug,
                "--product-sku",
                "CLEAN-BASIC",
                "--source-file",
                str(_DEMO_CSV),
                "--encoding",
                "utf-8-sig",
                "--run-p75-gate",
            ]
            proc = subprocess.run(
                cmd,
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
            self.assertIn("gate_status:", proc.stdout)
            self.assertIn("decision=", proc.stdout)
            self.assertIn("reason_codes:", proc.stdout)
        finally:
            if client_dir.is_dir():
                shutil.rmtree(client_dir)


if __name__ == "__main__":
    unittest.main()
