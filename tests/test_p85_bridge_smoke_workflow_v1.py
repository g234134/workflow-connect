"""Workflow config tests for P8.5 bridge-smoke.yml (Scenario 1 + Scenario 2)."""

from __future__ import annotations

import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - optional in minimal envs
    yaml = None  # type: ignore[assignment]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "bridge-smoke.yml"


def _workflow_on(workflow: dict) -> dict:
    # PyYAML 1.1 treats bare `on:` as boolean True in GitHub Actions YAML.
    block = workflow.get("on")
    if block is None and True in workflow:
        block = workflow[True]
    if not isinstance(block, dict):
        raise ValueError("workflow on/trigger block missing or invalid")
    return block


def _load_workflow() -> dict:
    if yaml is None:
        raise unittest.SkipTest("PyYAML not installed")
    if not _WORKFLOW.is_file():
        raise unittest.SkipTest(f"missing workflow: {_WORKFLOW}")
    with _WORKFLOW.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class TestP85BridgeSmokeWorkflowV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = _load_workflow()

    def test_workflow_dispatch_has_scenario_input(self) -> None:
        dispatch = _workflow_on(self.workflow)["workflow_dispatch"]
        scenario = dispatch["inputs"]["scenario"]
        self.assertEqual(scenario["default"], "default")
        self.assertIn("scenario2", scenario["options"])

    def test_scenario1_jobs_run_unless_scenario2_dispatch(self) -> None:
        for job_id in ("p85-bridge-smoke-a", "p85-bridge-smoke-b"):
            job_if = self.workflow["jobs"][job_id]["if"]
            self.assertIn("scenario2", job_if)
            self.assertTrue(self.workflow["jobs"][job_id]["continue-on-error"])

    def test_scenario2_jobs_only_on_dispatch_input(self) -> None:
        for job_id in ("p85-bridge-smoke-a-scenario2", "p85-bridge-smoke-b-scenario2"):
            job = self.workflow["jobs"][job_id]
            self.assertIn("workflow_dispatch", job["if"])
            self.assertIn("scenario2", job["if"])
            self.assertTrue(job["continue-on-error"])

    def test_scenario2_jobs_force_missing_dir_env(self) -> None:
        for job_id in ("p85-bridge-smoke-a-scenario2", "p85-bridge-smoke-b-scenario2"):
            env = self.workflow["jobs"][job_id]["env"]
            self.assertEqual(env["P85_BRIDGE_SMOKE_SCENARIO"], "2")
            self.assertEqual(env["P85_BRIDGE_SMOKE_FORCE_SKIP"], "missing_dir")

    def test_scenario2_smoke_scripts_emit_design_skip_notice(self) -> None:
        for job_id in ("p85-bridge-smoke-a-scenario2", "p85-bridge-smoke-b-scenario2"):
            steps = self.workflow["jobs"][job_id]["steps"]
            run_step = next(s for s in steps if s.get("run"))
            script = run_step["run"]
            self.assertIn("Scenario 2 skipped by design", script)
            self.assertIn("p85-scenario2-force-missing-gov-core", script)
            self.assertIn("exit 0", script)

    def test_scenario1_smoke_a_script_unchanged_happy_path(self) -> None:
        steps = self.workflow["jobs"]["p85-bridge-smoke-a"]["steps"]
        run_step = next(s for s in steps if s.get("id") == "smoke_a")
        script = run_step["run"]
        self.assertIn("01_Environments/python_venvs/gov_core_system", script)
        self.assertIn("test_minimal_orchestration_bridge", script)
        self.assertIn("Bridge Smoke A passed", script)
        self.assertNotIn("Scenario 2 skipped by design", script)


if __name__ == "__main__":
    unittest.main()
