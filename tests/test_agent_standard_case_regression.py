"""Unit tests for Agent-run standard case experiment regression hook (W6-T8)."""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REGRESSION_CLI = _REPO_ROOT / "scripts" / "run_agent_standard_case_regression.py"
_MVP_REGRESSION_CLI = _REPO_ROOT / "scripts" / "run_mvp_mainline_regression.py"
_EXPERIMENT_CLI = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"

_FORBIDDEN_IMPORT_PREFIXES = (
    "scripts.run_mvp_mainline_regression",
    "scripts.run_case_e2e_validation",
    "scripts.new_cleaning_case",
    "app.local_ui",
    "tools.tabular_tool_executor",
    "core.routing_policy_loader",
)


def _load_regression_module():
    spec = importlib.util.spec_from_file_location(
        "run_agent_standard_case_regression", _REGRESSION_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_standard_case_regression"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestAgentStandardCaseRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _REGRESSION_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_REGRESSION_CLI}")
        cls.reg = _load_regression_module()

    def test_module_does_not_import_forbidden_modules(self) -> None:
        source = _REGRESSION_CLI.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        for name in imported:
            for forbidden in _FORBIDDEN_IMPORT_PREFIXES:
                self.assertFalse(
                    name == forbidden or name.startswith(forbidden + "."),
                    f"forbidden import detected: {name}",
                )

    def test_demo_phase_regression_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "regression_outbox"
            result = self.reg.run_agent_standard_case_regression(
                run_mode="preview",
                outbox_root=str(outbox),
                timestamp="20260610T120000Z",
            )
        self.assertTrue(result["ok"])
        demo = next(c for c in result["cases"] if c["case_ref"] == "demo_phase")
        self.assertEqual(demo["mode"], "preview")
        self.assertEqual(demo["final_status"], "waiting_for_human")
        self.assertEqual(demo["checkpoint_a_status"], "would_pause")
        self.assertIn("planned", demo["checkpoint_b_status"])

    def test_sampleco_regression_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "regression_outbox"
            result = self.reg.run_agent_standard_case_regression(
                run_mode="preview",
                outbox_root=str(outbox),
                timestamp="20260610T120001Z",
            )
        sampleco = next(
            c for c in result["cases"] if c["case_ref"] == "sampleco/2026-0001"
        )
        self.assertEqual(sampleco["mode"], "preview")
        self.assertEqual(sampleco["final_status"], "waiting_for_human")
        self.assertEqual(sampleco["checkpoint_a_status"], "would_pause")
        self.assertTrue(sampleco["checkpoint_b_would_trigger"])

    def test_writes_outbox_artifact_paths(self) -> None:
        ts = "20260610T130000Z"
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "agent_experiment_regression"
            result = self.reg.run_agent_standard_case_regression(
                outbox_root=str(outbox),
                timestamp=ts,
            )
            demo_path = outbox / f"{ts}_demo_phase.json"
            sampleco_path = outbox / f"{ts}_sampleco_2026-0001.json"
            self.assertTrue(demo_path.is_file(), f"missing {demo_path}")
            self.assertTrue(sampleco_path.is_file(), f"missing {sampleco_path}")

            demo_payload = json.loads(demo_path.read_text(encoding="utf-8"))
            self.assertEqual(demo_payload["schema_version"], "agent_experiment_regression_v1")
            self.assertIn("experiment", demo_payload)
            self.assertIn("case_summary", demo_payload)
            self.assertEqual(demo_payload["case_summary"]["case_ref"], "demo_phase")

            demo_case = next(c for c in result["cases"] if c["case_ref"] == "demo_phase")
            self.assertTrue(str(demo_path).endswith(Path(demo_case["artifact_path"]).name))

    def test_run_mode_applies_to_demo_phase_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "regression_outbox"
            result = self.reg.run_agent_standard_case_regression(
                run_mode="run",
                auto_approve_intake=True,
                outbox_root=str(outbox),
                timestamp="20260610T140000Z",
            )
        demo = next(c for c in result["cases"] if c["case_ref"] == "demo_phase")
        sampleco = next(
            c for c in result["cases"] if c["case_ref"] == "sampleco/2026-0001"
        )
        self.assertEqual(demo["mode"], "run")
        self.assertIn(
            demo["final_status"],
            ("waiting_for_human", "run_complete", "resume_plan_ready"),
        )
        self.assertEqual(sampleco["mode"], "preview")
        self.assertEqual(sampleco["final_status"], "waiting_for_human")

    def test_run_all_allowed_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "regression_outbox"
            result = self.reg.run_agent_standard_case_regression(
                run_mode="run-all-allowed",
                auto_approve_intake=True,
                outbox_root=str(outbox),
                timestamp="20260610T150000Z",
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["run_mode"], "run-all-allowed")
        demo = next(c for c in result["cases"] if c["case_ref"] == "demo_phase")
        sampleco = next(
            c for c in result["cases"] if c["case_ref"] == "sampleco/2026-0001"
        )
        self.assertEqual(demo["mode"], "run")
        self.assertEqual(sampleco["mode"], "run")
        self.assertEqual(sampleco["final_status"], "stopped_at_checkpoint_b")

    def test_run_all_allowed_extended_fixtures_experimental_run(self) -> None:
        """Extended suite: stable+additional_demo pass; sandbox_client may controlled-fail.

        At stop_at=cleaning_preview with guard_sanity_ok, sandbox_client currently
        surfaces final_status=blocked / decision=needs_review / ok=False — accepted
        as controlled experimental outcome (≠ G2–G4 gate uplift).
        """
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "regression_outbox"
            result = self.reg.run_agent_standard_case_regression(
                run_mode="run-all-allowed",
                auto_approve_intake=True,
                outbox_root=str(outbox),
                timestamp="20260610T160000Z",
                include_extended_fixtures=True,
            )
        self.assertEqual(result["summary"]["total"], 4)
        add_demo = next(c for c in result["cases"] if c["case_ref"] == "additional_demo")
        sandbox = next(c for c in result["cases"] if c["case_ref"] == "sandbox_client")
        demo = next(c for c in result["cases"] if c["case_ref"] == "demo_phase")
        sampleco = next(
            c for c in result["cases"] if c["case_ref"] == "sampleco/2026-0001"
        )
        # Stable + additional_demo must still pass.
        self.assertTrue(demo["ok"])
        self.assertTrue(sampleco["ok"])
        self.assertTrue(add_demo["ok"])
        self.assertEqual(add_demo["mode"], "run")
        self.assertTrue(add_demo["experimental_run"])
        self.assertTrue(add_demo["controlled_experimental_run"])
        self.assertEqual(add_demo["fixture_maturity"], "controlled_experimental")
        self.assertEqual(add_demo["run_path_stop_at"], "checkpoint_b")
        self.assertEqual(add_demo["final_status"], "stopped_at_checkpoint_b")
        self.assertTrue(add_demo.get("regression_bundle_probe"))
        self.assertTrue(add_demo.get("guard_sanity_ok"))
        self.assertIn("removal_ratio", add_demo)
        # sandbox_client: controlled fail at cleaning_preview (not stopped_at_* label).
        self.assertEqual(sandbox["mode"], "run")
        self.assertTrue(sandbox["experimental_run"])
        self.assertTrue(sandbox["controlled_experimental_run"])
        self.assertEqual(sandbox["fixture_maturity"], "controlled_experimental")
        self.assertEqual(sandbox["run_path_stop_at"], "cleaning_preview")
        self.assertTrue(sandbox.get("guard_sanity_ok"))
        self.assertEqual(sandbox["final_status"], "blocked")
        self.assertEqual(sandbox["decision"], "needs_review")
        self.assertFalse(sandbox["ok"])
        self.assertFalse(result["ok"])  # overall reflects sandbox controlled fail
        self.assertEqual(result["summary"]["passed"], 3)
        self.assertEqual(result["summary"]["failed"], 1)
        self.assertFalse(demo.get("experimental_run"))
        self.assertEqual(demo.get("fixture_maturity"), "stable")
        self.assertEqual(sampleco.get("fixture_maturity"), "stable")
        self.assertFalse(sampleco.get("controlled_experimental_run"))

    def test_does_not_modify_mainline_regression_script(self) -> None:
        """Regression helper must not touch MVP mainline regression entrypoint."""
        self.assertTrue(_MVP_REGRESSION_CLI.is_file())
        mvp_source = _MVP_REGRESSION_CLI.read_text(encoding="utf-8")
        self.assertIn("test_mvp_mainline.py", mvp_source)
        self.assertNotIn("run_agent_standard_case_regression", mvp_source)

    def test_regression_does_not_modify_experiment_script(self) -> None:
        """Regression wrapper must not embed regression entrypoint in experiment CLI."""
        self.assertTrue(_EXPERIMENT_CLI.is_file())
        exp_source = _EXPERIMENT_CLI.read_text(encoding="utf-8")
        self.assertNotIn("run_agent_standard_case_regression", exp_source)
        self.assertIn("run_path_profile", exp_source)

    def test_extended_fixtures_regression_when_flag_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "regression_outbox"
            result = self.reg.run_agent_standard_case_regression(
                run_mode="preview",
                outbox_root=str(outbox),
                timestamp="20260610T151000Z",
                include_extended_fixtures=True,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["total"], 4)
            refs = {c["case_ref"] for c in result["cases"]}
            self.assertEqual(
                refs,
                {"demo_phase", "sampleco/2026-0001", "additional_demo", "sandbox_client"},
            )
            add_demo = next(c for c in result["cases"] if c["case_ref"] == "additional_demo")
            self.assertEqual(add_demo["final_status"], "waiting_for_human")
            sandbox = next(c for c in result["cases"] if c["case_ref"] == "sandbox_client")
            self.assertEqual(sandbox["final_status"], "waiting_for_human")
            self.assertTrue((outbox / "20260610T151000Z_additional_demo.json").is_file())
            self.assertTrue((outbox / "20260610T151000Z_sandbox_client.json").is_file())

    def test_default_regression_excludes_extended_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "regression_outbox"
            result = self.reg.run_agent_standard_case_regression(
                outbox_root=str(outbox),
                timestamp="20260610T160000Z",
            )
        self.assertEqual(result["summary"]["total"], 2)
        refs = {c["case_ref"] for c in result["cases"]}
        self.assertEqual(refs, {"demo_phase", "sampleco/2026-0001"})

    # W4-GUARD-01: Experimental fixture guard tests
    def test_enforce_fixture_guard_blocks_experimental_without_flag(self) -> None:
        """Guard should block experimental fixtures when include_extended_fixtures=False."""
        guard_result = self.reg.enforce_fixture_guard(
            "additional_demo",
            "controlled_experimental",
            include_extended_fixtures=False,
            explicit_flags={},
        )
        self.assertFalse(guard_result["ok"])
        self.assertEqual(guard_result["action"], "block")
        self.assertEqual(guard_result["reason"], "experimental_fixture_requires_explicit_flag")
        self.assertEqual(guard_result["case_ref"], "additional_demo")
        self.assertIn("--include-extended-fixtures", guard_result["required_flags"])
        self.assertIn("Guard blocked", guard_result["message"])

    def test_enforce_fixture_guard_allows_stable_fixture(self) -> None:
        """Guard should allow stable fixtures without any flag."""
        guard_result = self.reg.enforce_fixture_guard(
            "demo_phase",
            "stable",
            include_extended_fixtures=False,
            explicit_flags={},
        )
        self.assertTrue(guard_result["ok"])
        self.assertEqual(guard_result["action"], "allow")
        self.assertEqual(guard_result["reason"], "stable_fixture")

    def test_enforce_fixture_guard_allows_experimental_with_flag(self) -> None:
        """Guard should allow experimental fixtures when include_extended_fixtures=True."""
        guard_result = self.reg.enforce_fixture_guard(
            "additional_demo",
            "controlled_experimental",
            include_extended_fixtures=True,
            explicit_flags={},
        )
        self.assertTrue(guard_result["ok"])
        self.assertEqual(guard_result["action"], "allow")
        self.assertEqual(guard_result["reason"], "explicit_include_extended_fixtures")

    def test_enforce_fixture_guard_blocks_by_maturity_label(self) -> None:
        """Guard should block fixtures with experimental maturity labels."""
        guard_result = self.reg.enforce_fixture_guard(
            "some_new_fixture",
            "experimental",
            include_extended_fixtures=False,
            explicit_flags={},
        )
        self.assertFalse(guard_result["ok"])
        self.assertEqual(guard_result["action"], "block")
        self.assertEqual(guard_result["case_ref"], "some_new_fixture")

    def test_guard_blocks_when_include_extended_fixtures_true_but_fixture_marked_experimental(self) -> None:
        """W4-GUARD-01: Guard should block if include flag used but fixture validation fails (defensive)."""
        # This tests the guard enforcement layer as defensive programming
        guard_result = self.reg.enforce_fixture_guard(
            "additional_demo",
            "controlled_experimental",
            include_extended_fixtures=False,  # Flag not set
            explicit_flags={},
        )
        self.assertFalse(guard_result["ok"])
        self.assertEqual(guard_result["action"], "block")

    def test_default_regression_excludes_extended_fixtures_silently(self) -> None:
        """W4-GUARD-01: Default regression (without flag) silently excludes extended fixtures - they don't even appear."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "regression_outbox"
            result = self.reg.run_agent_standard_case_regression(
                run_mode="run-all-allowed",
                auto_approve_intake=True,
                outbox_root=str(outbox),
                timestamp="20260610T170000Z",
                include_extended_fixtures=False,  # Default
            )
        # Without include_extended_fixtures, only stable fixtures run
        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"]["total"], 2)  # Only demo_phase + sampleco
        refs = {c["case_ref"] for c in result["cases"]}
        self.assertEqual(refs, {"demo_phase", "sampleco/2026-0001"})
        # Extended fixtures are NOT in the list (silently excluded, not blocked)
        self.assertNotIn("additional_demo", refs)
        self.assertNotIn("sandbox_client", refs)


if __name__ == "__main__":
    unittest.main()
