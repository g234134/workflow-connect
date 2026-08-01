"""Unit tests for P2 GraphRAG thin runner v1."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "scripts" / "run_p2_graphrag_thin_runner_v1.py"
_DOC = _REPO_ROOT / "docs" / "phase2-graphrag-thin-runner-v1.md"
_TICKET = (
    _REPO_ROOT
    / "04_Workflows"
    / "tickets"
    / "P2-GRAPHRAG-THIN-RUNNER-v1_state.md"
)
_FIXTURE = (
    _REPO_ROOT / "tests" / "fixtures" / "graphrag_jobs_thin_v1" / "plan.json"
)


class TestP2GraphragThinRunnerV1(unittest.TestCase):
    def test_assets_exist(self) -> None:
        for path in (_SCRIPT, _DOC, _TICKET, _FIXTURE):
            self.assertTrue(path.is_file(), msg=f"missing {path}")

    def test_doc_has_non_claims_and_commands(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        self.assertIn("non_claims", text.lower())
        self.assertIn("run_p2_graphrag_thin_runner_v1.py", text)
        self.assertIn("primary retrieval", text.lower())
        self.assertIn("apply_phase_pct", text)

    def test_default_fixture_ok_with_fail_path(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from run_p2_graphrag_thin_runner_v1 import (  # noqa: WPS433
            run_p2_graphrag_thin_runner,
        )

        result = run_p2_graphrag_thin_runner()
        self.assertTrue(result.get("ok"), msg=result)
        self.assertEqual(result.get("schema_version"), "p2_graphrag_thin_runner_v1")
        self.assertFalse(result.get("primary_retrieval"))
        self.assertFalse(result.get("writes_production_db"))
        self.assertFalse(result.get("apply_phase_pct"))
        summary = result.get("summary") or {}
        self.assertGreaterEqual(summary.get("succeeded", 0), 1)
        self.assertGreaterEqual(summary.get("failed", 0), 1)
        jobs = {j["job_id"]: j for j in (result.get("jobs") or [])}
        self.assertEqual(jobs["grag-fixture-ok-001"]["status"], "succeeded")
        self.assertEqual(
            jobs["grag-fixture-ok-001"]["transitions"],
            ["queued", "running", "succeeded"],
        )
        fail = jobs["grag-fixture-fail-001"]
        self.assertEqual(fail["status"], "failed")
        self.assertEqual(fail.get("error_code"), "FIXTURE_SIMULATED_FAIL")
        self.assertEqual(fail["transitions"], ["queued", "running", "failed"])
        claims = result.get("non_claims") or []
        self.assertTrue(any("primary retrieval" in c for c in claims))
        self.assertTrue(any("Phase%" in c for c in claims))

    def test_missing_fixture_ok_false(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from run_p2_graphrag_thin_runner_v1 import (  # noqa: WPS433
            run_p2_graphrag_thin_runner,
        )

        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            result = run_p2_graphrag_thin_runner(fixture=missing)
            self.assertFalse(result.get("ok"))
            self.assertIn("not found", (result.get("message") or "").lower())

    def test_cli_text_ok(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPT), "--format", "text"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("ok: True", proc.stdout)
        self.assertIn("schema_version=p2_graphrag_thin_runner_v1", proc.stdout)
        self.assertIn("primary_retrieval=False", proc.stdout)

    def test_cli_json_ok(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPT), "--pretty"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("schema_version"), "p2_graphrag_thin_runner_v1")


if __name__ == "__main__":
    unittest.main()
