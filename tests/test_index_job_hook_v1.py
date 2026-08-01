"""Unit tests for index job hook skeleton v1 (FP-G2-T1 · dry-run only)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.run_index_job_hook_v1 import (
    DOC_REL,
    SCHEMA_VERSION,
    main,
    run_index_job_hook,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


class TestIndexJobHookV1(unittest.TestCase):
    def test_dry_run_returns_stable_dict_shape(self) -> None:
        result = run_index_job_hook(dry_run=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertTrue(result["skeleton"])
        self.assertEqual(result["mode"], "dry_run")
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["writes_index"])
        self.assertIn("message", result)
        self.assertIsInstance(result["planned_jobs"], list)
        self.assertGreaterEqual(len(result["planned_jobs"]), 1)
        for job in result["planned_jobs"]:
            self.assertIn("job_id", job)
            self.assertIn("pipeline", job)
            self.assertEqual(job.get("mode"), "plan_only")
            self.assertIs(job.get("writes_index"), False)
        self.assertEqual(result.get("doc"), DOC_REL)

    def test_dry_run_does_not_write_index_or_seed(self) -> None:
        """Skeleton must not create/mutate production index or seed corpus paths."""
        seed_marker = _REPO_ROOT / "03_RAG_Database"
        before = None
        if seed_marker.exists():
            before = seed_marker.stat().st_mtime

        result = run_index_job_hook(dry_run=True)
        self.assertTrue(result["ok"])
        self.assertFalse(result["writes_index"])
        self.assertTrue(all(not j.get("writes_index") for j in result["planned_jobs"]))

        # No side-effect files under scripts/ for this hook
        side_effect = _REPO_ROOT / "scripts" / ".index_job_hook_write_probe"
        self.assertFalse(side_effect.exists())

        if before is not None:
            self.assertEqual(seed_marker.stat().st_mtime, before)

    def test_execute_mode_blocked(self) -> None:
        result = run_index_job_hook(dry_run=False, execute=True)
        self.assertFalse(result["ok"])
        self.assertEqual(result["mode"], "execute_blocked")
        self.assertFalse(result["writes_index"])
        self.assertEqual(result["planned_jobs"], [])

    def test_cli_dry_run_json(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "run_index_job_hook_v1.py"),
                "--dry-run",
                "--format",
                "json",
            ],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertIn("planned_jobs", payload)
        self.assertFalse(payload["writes_index"])

    def test_main_json_exit_zero(self) -> None:
        # Capture via main() return code; stdout exercised in CLI test
        code = main(["--dry-run", "--format", "text"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
