"""Unit tests for output row-ratio guard (Wave 4B · W-MVP-W4B-GUARD-RATIO)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"
if str(_CSV_CLEANING) not in sys.path:
    sys.path.insert(0, str(_CSV_CLEANING))

from case_delivery_bundle import build_case_delivery_bundle  # noqa: E402
from output_guard import (  # noqa: E402
    DEFAULT_RATIO_THRESHOLD,
    apply_output_guard_to_report,
    compute_output_guard,
)

_DEMO = _REPO_ROOT / "cases" / "demo_phase"
_SAMPLECO = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"
_E2E_SCRIPT = _REPO_ROOT / "scripts" / "run_case_e2e_validation.py"
_BUNDLE_SCRIPT = _REPO_ROOT / "scripts" / "build_case_delivery_bundle.py"


def _load_report(case_dir: Path) -> dict:
    return json.loads((case_dir / "reports" / "report.json").read_text(encoding="utf-8"))


def _parse_cli_json(stdout: str) -> dict:
    """Extract root result dict from CLI stdout (human summary precedes JSON)."""
    for marker in ('\n{\n  "ok"', '\n{\n  "case_dir"'):
        idx = stdout.rfind(marker)
        if idx < 0:
            continue
        start = idx + 1
        try:
            obj, _ = json.JSONDecoder().raw_decode(stdout[start:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return {}


class TestOutputGuardCompute(unittest.TestCase):
    def test_demo_phase_ratio_ok(self) -> None:
        report = _load_report(_DEMO)
        guard = compute_output_guard(report)
        self.assertEqual(guard["status"], "ok")
        self.assertGreaterEqual(guard["ratio"], DEFAULT_RATIO_THRESHOLD)
        self.assertEqual(guard["input_rows"], 7)
        self.assertEqual(guard["output_rows"], 5)

    def test_sampleco_ratio_warning(self) -> None:
        report = _load_report(_SAMPLECO)
        guard = compute_output_guard(report)
        self.assertEqual(guard["status"], "warning")
        self.assertLess(guard["ratio"], DEFAULT_RATIO_THRESHOLD)
        self.assertAlmostEqual(guard["ratio"], 8 / 115, places=3)
        self.assertEqual(guard["input_rows"], 115)
        self.assertEqual(guard["output_rows"], 8)


class TestOutputGuardIntegration(unittest.TestCase):
    def test_bundle_attaches_output_guard_demo_phase(self) -> None:
        result = build_case_delivery_bundle(_DEMO, refresh_eligibility=False)
        self.assertTrue(result["ok"], result.get("message"))
        guard = result.get("output_guard")
        self.assertIsNotNone(guard)
        self.assertEqual(guard["status"], "ok")

        report = _load_report(_DEMO)
        self.assertIn("output_guard", report)
        self.assertEqual(report["output_guard"]["status"], "ok")

    def test_bundle_attaches_output_guard_sampleco(self) -> None:
        result = build_case_delivery_bundle(_SAMPLECO, refresh_eligibility=False)
        self.assertTrue(result["ok"], result.get("message"))
        guard = result.get("output_guard")
        self.assertIsNotNone(guard)
        self.assertEqual(guard["status"], "warning")
        self.assertIn("schema_flags", guard)
        self.assertIn("multi_row_export", guard["schema_flags"])
        self.assertIn("schema_ambiguous", guard["schema_flags"])

    def test_apply_output_guard_schema_flags(self) -> None:
        report = _load_report(_SAMPLECO)
        eligibility_raw = {
            "dimensions": {
                "schema": {
                    "notes": ["phase_like", "multi_row_export", "schema_ambiguous"],
                    "warnings": ["phase_like_headers_but_multi_row_or_sprint_pattern"],
                }
            }
        }
        guard = compute_output_guard(report, eligibility_raw=eligibility_raw)
        self.assertEqual(guard["status"], "warning")
        self.assertEqual(
            guard["schema_flags"],
            ["multi_row_export", "schema_ambiguous"],
        )


class TestOutputGuardCli(unittest.TestCase):
    def test_bundle_cli_json_includes_output_guard(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_BUNDLE_SCRIPT),
                "--case-dir",
                str(_SAMPLECO),
                "--json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        data = _parse_cli_json(proc.stdout)
        guard = data.get("output_guard")
        self.assertIsNotNone(guard)
        self.assertEqual(guard["status"], "warning")

    def test_e2e_cli_json_includes_output_guard(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_E2E_SCRIPT),
                "--case-dir",
                str(_SAMPLECO),
                "--json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        data = _parse_cli_json(proc.stdout)
        self.assertTrue(data.get("ok"))
        guard = data.get("output_guard")
        self.assertIsNotNone(guard)
        self.assertEqual(guard["status"], "warning")
        self.assertAlmostEqual(guard["ratio"], 8 / 115, places=3)


if __name__ == "__main__":
    unittest.main()
