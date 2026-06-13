"""Unit tests for WC-T7 M2 E2E walkthrough runner (dry-run guards)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _REPO_ROOT / "scripts" / "run_wc_m2_e2e_walkthrough.py"


class TestRunWcM2E2eWalkthrough(unittest.TestCase):
    def _run_cli(self, *extra: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(_RUNNER), *extra]
        return subprocess.run(
            cmd,
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_reject_non_demo_ticket(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-NOT-ALLOWED",
            "--dry-run",
            "--json",
        )
        self.assertNotEqual(proc.returncode, 0)
        err_payload = json.loads(proc.stderr.strip())
        self.assertFalse(err_payload["ok"])
        self.assertIn("WC-DEMO-", err_payload["message"])

    def test_dry_run_with_demo_ticket(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-DEMO-1",
            "--artifacts-root",
            "artifacts/e2e",
            "--dry-run",
            "--json",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout.strip())
        self.assertTrue(payload["ok"])
        self.assertIn(
            "docs/wave_c/WC_T7_e2e_walkthrough_runbook.md",
            payload["runbook"],
        )
        self.assertGreaterEqual(len(payload["steps"]), 3)
        step_ids = [step["step_id"] for step in payload["steps"]]
        self.assertIn("2", step_ids)
        self.assertIn("5", step_ids)

    def test_reject_non_e2e_artifacts_root(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-DEMO-1",
            "--artifacts-root",
            "artifacts/not_e2e",
            "--dry-run",
            "--json",
        )
        self.assertNotEqual(proc.returncode, 0)
        err_payload = json.loads(proc.stderr.strip())
        self.assertFalse(err_payload["ok"])
        self.assertIn("artifacts/e2e", err_payload["message"])


if __name__ == "__main__":
    unittest.main()
