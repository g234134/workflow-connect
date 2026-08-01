"""Unit tests for index job hook thin runtime (FP-G2-T6 + sandbox trial)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.run_index_job_hook_runtime_thin_v1 import (
    DOC_REL,
    SCHEMA_VERSION,
    main,
    run_index_job_hook_runtime_thin,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "index_job_hook_thin_v1"


class TestIndexJobHookRuntimeThinV1(unittest.TestCase):
    def test_dry_run_dict_shape(self) -> None:
        result = run_index_job_hook_runtime_thin(dry_run=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertTrue(result["thin_runtime"])
        self.assertFalse(result["skeleton"])
        self.assertEqual(result["mode"], "dry_run")
        self.assertFalse(result["writes_index"])
        self.assertIsInstance(result["planned_jobs"], list)
        self.assertGreaterEqual(len(result["planned_jobs"]), 1)
        self.assertTrue(result.get("fixture_digest"))
        self.assertEqual(result.get("doc"), DOC_REL)
        for job in result["planned_jobs"]:
            self.assertIs(job.get("writes_index"), False)

    def test_fixture_digest_stable(self) -> None:
        a = run_index_job_hook_runtime_thin(dry_run=True, fixture_path=_FIXTURE)
        b = run_index_job_hook_runtime_thin(dry_run=True, fixture_path=_FIXTURE)
        self.assertEqual(a["fixture_digest"], b["fixture_digest"])

    def test_no_production_write(self) -> None:
        seed = _REPO_ROOT / "03_RAG_Database"
        before = seed.stat().st_mtime if seed.exists() else None
        marker = _REPO_ROOT / "scripts" / ".index_job_hook_thin_write_probe"
        if marker.exists():
            marker.unlink()
        result = run_index_job_hook_runtime_thin(dry_run=True)
        self.assertTrue(result["ok"])
        self.assertFalse(marker.exists())
        if before is not None:
            self.assertEqual(seed.stat().st_mtime, before)

    def test_execute_blocked(self) -> None:
        result = run_index_job_hook_runtime_thin(dry_run=False, execute=True)
        self.assertFalse(result["ok"])
        self.assertEqual(result["mode"], "execute_blocked")
        self.assertFalse(result["writes_index"])

    def test_execute_sandbox_writes_allowlisted_only(self) -> None:
        out = (
            _REPO_ROOT
            / "tests"
            / "fixtures"
            / "index_job_hook_thin_v1"
            / "_sandbox_out"
            / "_ut_run"
        )
        if out.exists():
            shutil.rmtree(out)
        try:
            result = run_index_job_hook_runtime_thin(
                dry_run=False,
                execute=True,
                sandbox=True,
                fixture_path=_FIXTURE,
                sandbox_out=out,
            )
            self.assertTrue(result["ok"], msg=result.get("message"))
            self.assertEqual(result["mode"], "sandbox_execute")
            self.assertTrue(result["writes_index"])
            self.assertFalse(result["writes_production_index"])
            self.assertTrue(result.get("reversible"))
            paths = result.get("written_paths") or []
            self.assertGreaterEqual(len(paths), 1)
            for rel in paths:
                self.assertTrue(
                    rel.startswith(
                        "tests/fixtures/index_job_hook_thin_v1/_sandbox_out/"
                    ),
                    msg=rel,
                )
                self.assertTrue((_REPO_ROOT / rel).is_file(), msg=rel)
            risk = result.get("risk") or {}
            self.assertFalse(risk.get("touches_live_qdrant"))
            self.assertFalse(risk.get("touches_production_db"))
            self.assertFalse(risk.get("touches_rag_database_tree"))
        finally:
            parent = out.parent
            if parent.exists():
                shutil.rmtree(parent)

    def test_execute_sandbox_rejects_non_allowlisted_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "outside"
            result = run_index_job_hook_runtime_thin(
                dry_run=False,
                execute=True,
                sandbox=True,
                fixture_path=_FIXTURE,
                sandbox_out=bad,
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["mode"], "sandbox_rejected")
            self.assertFalse(result["writes_index"])

    def test_cli_json(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "run_index_job_hook_runtime_thin_v1.py"),
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
        self.assertIn("fixture_digest", payload)

    def test_main_text(self) -> None:
        self.assertEqual(main(["--dry-run", "--format", "text"]), 0)


if __name__ == "__main__":
    unittest.main()
