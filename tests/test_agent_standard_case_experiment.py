"""Unit tests for Agent-run standard case experiment orchestrator (W6-T4)."""

from __future__ import annotations

import ast
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
_DEMO_PHASE = "cases/demo_phase"
_SAMPLECO = "cases/sampleco/2026-0001"
_ADDITIONAL_DEMO = "cases/additional_demo"
_SANDBOX_CLIENT = "cases/sandbox_client"

_FORBIDDEN_IMPORT_PREFIXES = (
    "scripts.new_cleaning_case",
    "app.local_ui",
    "scripts.run_mvp_mainline_regression",
    "tools.tabular_tool_executor",
    "tools.tabular_tool_selector",
    "core.routing_policy_loader",
    "scripts.run_routing_eval",
)

_REQUIRED_TOP_KEYS = (
    "ok",
    "experiment_id",
    "case_ref",
    "task_type",
    "intake_gate",
    "decision",
    "checkpoint_a_status",
    "planned_route",
    "tool_path_preview",
    "checkpoint_b_status",
    "final_status",
)


def _load_cli_module():
    spec = importlib.util.spec_from_file_location(
        "run_agent_standard_case_experiment", _CLI_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_standard_case_experiment"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_cli_json(
    task_type: str,
    case_dir: str,
    *,
    mode: str = "preview",
    extra_args: list[str] | None = None,
) -> dict:
    cmd = [
        sys.executable,
        str(_CLI_PATH),
        "--task-type",
        task_type,
        "--case-dir",
        case_dir,
        "--mode",
        mode,
        "--format",
        "json",
    ]
    if extra_args:
        cmd.extend(extra_args)
    proc = subprocess.run(
        cmd,
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"CLI exit {proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return json.loads(proc.stdout)


def _assert_experiment_shape(result: dict) -> None:
    for key in _REQUIRED_TOP_KEYS:
        assert key in result, f"missing key: {key}"
    assert isinstance(result["experiment_id"], str) and result["experiment_id"]
    decision = result["decision"]
    assert decision["decision"] in ("auto_accept", "needs_review", "reject")
    assert decision["risk_level"] in ("low", "medium", "high")
    cp_a = result["checkpoint_a_status"]
    assert "status" in cp_a
    assert "would_trigger" in cp_a
    cp_b = result["checkpoint_b_status"]
    assert "status" in cp_b
    assert result["final_status"] in (
        "preview_ready",
        "waiting_for_human",
        "blocked",
        "blocked_at_selector_registry",
        "resume_plan_ready",
        "run_complete",
        "stopped_at_checkpoint_b",
        "stopped_at_cleaning_preview",
        "sandbox_e2e_complete",
        "sandbox_e2e_blocked_at_checkpoint_b",
    )


class TestAgentStandardCaseExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _CLI_PATH.is_file():
            raise unittest.SkipTest(f"missing CLI: {_CLI_PATH}")
        cls.cli = _load_cli_module()

    def test_module_does_not_import_forbidden_modules(self) -> None:
        source = _CLI_PATH.read_text(encoding="utf-8")
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

    def test_demo_phase_preview_produces_decision_route_checkpoint_a(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        _assert_experiment_shape(result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["case_ref"], "demo_phase")
        gate = result["intake_gate"]
        self.assertEqual(gate["schema_version"], "intake_gate_result_v1")
        self.assertEqual(gate["decision"], "review_needed")
        self.assertEqual(gate["decider"], "intake_gate_layer_v1")
        self.assertEqual(result["decision"]["decision"], "needs_review")
        self.assertEqual(result["decision"]["risk_level"], "medium")
        self.assertEqual(result["checkpoint_a_status"]["status"], "would_pause")
        self.assertTrue(result["checkpoint_a_status"]["would_trigger"])
        route = result["planned_route"]
        self.assertTrue(route["ok"])
        self.assertEqual(
            route["planned_tools"],
            [
                "validate.eligibility",
                "clean.phase_demo",
                "export.delivery_bundle",
            ],
        )
        preview = result["tool_path_preview"]
        self.assertTrue(preview["ok"])
        self.assertEqual(result["final_status"], "waiting_for_human")

    def test_sampleco_preview_checkpoint_a_needs_human_review(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _SAMPLECO,
            mode="preview",
        )
        _assert_experiment_shape(result)
        self.assertEqual(result["case_ref"], "sampleco/2026-0001")
        self.assertEqual(result["decision"]["decision"], "needs_review")
        cp_a = result["checkpoint_a_status"]
        self.assertTrue(cp_a["would_trigger"])
        self.assertEqual(cp_a["status"], "would_pause")
        self.assertIn(
            cp_a["status"],
            ("would_pause", "written"),
            "sampleco should indicate human review at Checkpoint A",
        )
        self.assertEqual(result["final_status"], "waiting_for_human")
        self.assertTrue(result["checkpoint_b_status"]["would_trigger"])

    def test_non_tabular_blocked(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "gov.observability.eval",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertEqual(result["intake_gate"]["decision"], "reject")
        self.assertEqual(result["decision"]["decision"], "reject")
        self.assertEqual(result["final_status"], "blocked")
        self.assertIsNone(result.get("planned_route"))
        cp_a = result["checkpoint_a_status"]
        self.assertFalse(cp_a["would_trigger"])
        self.assertEqual(cp_a["status"], "not_applicable")

    def test_json_structure_complete_via_cli(self) -> None:
        payload = _run_cli_json("tabular.cleaning.mvp", _DEMO_PHASE)
        _assert_experiment_shape(payload)
        self.assertIn("output_guard", payload)
        self.assertIn("mock", payload["output_guard"].get("note", "").lower())

    def test_run_mode_auto_approve_intake_resume_plan_via_integration_layer(self) -> None:
        """Run mode auto-approve delegates skip/resume to W6-T5 integration layer (SSOT)."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result["ok"])
        cp_a = result.get("checkpoint_a_status") or {}
        self.assertEqual(cp_a.get("status"), "auto_approved")
        self.assertEqual(cp_a.get("integration_layer"), "hitl.checkpoint_a_integration_v1")
        integration = cp_a.get("integration") or {}
        self.assertEqual(integration.get("status"), "auto_approved")
        self.assertNotIn("bypass_reason", cp_a)
        self.assertNotIn("checkpoint_path", cp_a)
        checkpoints = list(outbox.rglob("checkpoint_*.json"))
        self.assertEqual(checkpoints, [])
        resume = result.get("resume_plan") or {}
        self.assertEqual(resume.get("resume_from"), "selector")
        self.assertTrue(resume.get("planned_tools"))

    def test_run_mode_auto_approve_intake_resume_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["checkpoint_a_status"]["status"], "auto_approved")
        self.assertEqual(result["path_kind"], "run")
        self.assertIn("run_execution", result)
        self.assertIn(
            result["final_status"],
            ("waiting_for_human", "run_complete", "resume_plan_ready"),
        )
        resume = result.get("resume_plan") or {}
        self.assertEqual(resume.get("resume_from"), "selector")
        self.assertTrue(resume.get("planned_tools"))

    def test_demo_phase_run_mode_executes_to_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result["ok"])
        profile = result.get("run_path_profile") or {}
        self.assertEqual(profile.get("stop_at"), "bundle")
        run_exec = result.get("run_execution") or {}
        self.assertTrue(run_exec.get("ok"))
        self.assertIn("export.delivery_bundle", run_exec.get("tools_executed") or [])
        self.assertTrue(run_exec.get("outbox_entries"))
        self.assertEqual(result["output_guard"].get("source"), "live_cleaning_stats")

    def test_sampleco_run_mode_stops_at_checkpoint_b(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _SAMPLECO,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result["ok"])
        profile = result.get("run_path_profile") or {}
        self.assertEqual(profile.get("stop_at"), "checkpoint_b")
        self.assertTrue(profile.get("stop_before_delivery"))
        run_exec = result.get("run_execution") or {}
        self.assertTrue(run_exec.get("ok"))
        executed = run_exec.get("tools_executed") or []
        self.assertIn("clean.phase_demo", executed)
        self.assertNotIn("export.delivery_bundle", executed)
        self.assertEqual(result["final_status"], "stopped_at_checkpoint_b")
        cp_b = result.get("checkpoint_b_status") or {}
        self.assertIn(
            cp_b.get("status"),
            ("written", "stopped_before_delivery"),
        )

    def test_preview_does_not_write_checkpoint_state_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="preview",
                outbox_root_override=str(outbox),
            )
        self.assertEqual(result["checkpoint_a_status"]["status"], "would_pause")
        self.assertNotIn("checkpoint_path", result["checkpoint_a_status"])
        checkpoints = list(outbox.rglob("checkpoint_*.json"))
        self.assertEqual(checkpoints, [])

    def test_checkpoint_a_uses_w6_t5_integration_layer(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        cp_a = result["checkpoint_a_status"]
        self.assertEqual(cp_a.get("integration_layer"), "hitl.checkpoint_a_integration_v1")
        self.assertTrue(cp_a["would_trigger"])

    def test_checkpoint_b_preview_has_integration_layer_field(self) -> None:
        """W6-T10 C_REPORT gap fix: preview checkpoint_b_status includes integration_layer."""
        # Use sampleco case (warning status triggers checkpoint B would_trigger=True)
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _SAMPLECO,
            mode="preview",
        )
        cp_b = result["checkpoint_b_status"]
        self.assertEqual(cp_b.get("integration_layer"), "hitl.checkpoint_b_integration_v1")
        self.assertEqual(cp_b.get("status"), "planned")
        self.assertTrue(cp_b["would_trigger"])

    def test_sampleco_run_writes_checkpoint_b_via_w6_t6_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _SAMPLECO,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        cp_b = result.get("checkpoint_b_status") or {}
        self.assertEqual(cp_b.get("integration_layer"), "hitl.checkpoint_b_integration_v1")
        self.assertIn(cp_b.get("status"), ("written", "stopped_before_delivery"))
        b_files = list(outbox.rglob("checkpoint_B*.json"))
        if cp_b.get("status") == "written":
            self.assertGreaterEqual(len(b_files), 1)

    def test_run_mode_writes_checkpoint_a_when_needed(self) -> None:
        """Verify checkpoint A is written when needs_review (not auto-approved).

        Uses external outbox path - integration layer handles via three-layer fallback.
        """
        with tempfile.TemporaryDirectory() as tmp:
            external_outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=False,
                outbox_root_override=str(external_outbox),
            )
            self.assertEqual(result["checkpoint_a_status"]["status"], "written")
            self.assertIn("checkpoint_path", result["checkpoint_a_status"])
            checkpoints = list(external_outbox.rglob("checkpoint_*.json"))
            self.assertGreaterEqual(len(checkpoints), 1)
            gate = result.get("intake_gate") or {}
            self.assertEqual(gate.get("decision"), "review_needed")
            if gate.get("intake_decision_id"):
                ckpt_data = json.loads(checkpoints[0].read_text(encoding="utf-8"))
                agent_output = ckpt_data.get("agent_output") or {}
                intake_gate = agent_output.get("intake_gate") or {}
                self.assertEqual(
                    intake_gate.get("intake_decision_id"),
                    gate.get("intake_decision_id"),
                )

    def test_additional_demo_preview_experiment_line(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _ADDITIONAL_DEMO,
            mode="preview",
        )
        _assert_experiment_shape(result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["case_ref"], "additional_demo")
        self.assertEqual(result["decision"]["decision"], "needs_review")
        self.assertEqual(result["checkpoint_a_status"]["status"], "would_pause")
        self.assertTrue(result["planned_route"]["ok"])
        self.assertEqual(result["final_status"], "waiting_for_human")

    def test_sandbox_client_preview_experiment_line(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _SANDBOX_CLIENT,
            mode="preview",
        )
        _assert_experiment_shape(result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["case_ref"], "sandbox_client")
        self.assertEqual(result["decision"]["decision"], "needs_review")
        self.assertEqual(result["output_guard"]["source"], "mock_profile_sandbox_client")
        self.assertEqual(result["final_status"], "waiting_for_human")

    def test_additional_demo_run_mode_stops_at_checkpoint_b(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _ADDITIONAL_DEMO,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result["ok"])
        profile = result.get("run_path_profile") or {}
        self.assertEqual(profile.get("stop_at"), "checkpoint_b")
        self.assertEqual(profile.get("maturity"), "controlled_experimental")
        self.assertEqual(result.get("fixture_maturity"), "controlled_experimental")
        self.assertTrue(profile.get("experimental"))
        self.assertTrue(profile.get("force_cleaning"))
        self.assertTrue(profile.get("stop_before_delivery"))
        run_exec = result.get("run_execution") or {}
        self.assertTrue(run_exec.get("ok"))
        executed = run_exec.get("tools_executed") or []
        self.assertIn("clean.phase_demo", executed)
        self.assertNotIn("export.delivery_bundle", executed)
        self.assertFalse(run_exec.get("regression_bundle_probe"))
        self.assertTrue(run_exec.get("outbox_entries"))
        self.assertEqual(result["final_status"], "stopped_at_checkpoint_b")
        cp_b = result.get("checkpoint_b_status") or {}
        self.assertIn(
            cp_b.get("status"),
            ("written", "stopped_before_delivery"),
        )

    def test_additional_demo_regression_bundle_probe_attempts_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _ADDITIONAL_DEMO,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
                regression_bundle_probe=True,
            )
        self.assertTrue(result["ok"])
        run_exec = result.get("run_execution") or {}
        self.assertTrue(run_exec.get("regression_bundle_probe"))
        executed = run_exec.get("tools_executed") or []
        self.assertIn("export.delivery_bundle", executed)
        notes = " ".join(result.get("notes") or [])
        self.assertIn("regression_bundle_probe", notes)

    def test_sandbox_client_run_mode_stops_at_cleaning_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _SANDBOX_CLIENT,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result["ok"])
        profile = result.get("run_path_profile") or {}
        self.assertEqual(profile.get("stop_at"), "cleaning_preview")
        self.assertEqual(profile.get("maturity"), "controlled_experimental")
        self.assertEqual(result.get("fixture_maturity"), "controlled_experimental")
        self.assertTrue(profile.get("experimental"))
        run_exec = result.get("run_execution") or {}
        self.assertTrue(run_exec.get("ok"))
        executed = run_exec.get("tools_executed") or []
        self.assertIn("validate.eligibility", executed)
        self.assertIn("clean.phase_demo", executed)
        self.assertNotIn("export.delivery_bundle", executed)
        self.assertEqual(result["final_status"], "stopped_at_cleaning_preview")
        cp_b = result.get("checkpoint_b_status") or {}
        self.assertEqual(cp_b.get("status"), "stopped_at_cleaning_preview")
        self.assertFalse(cp_b.get("would_trigger"))
        guard = result.get("output_guard") or {}
        self.assertIn(
            guard.get("source"),
            ("live_cleaning_stats", "mock_profile_sandbox_client"),
        )
        self.assertIn("cleaning", guard.get("note", "").lower())
        if guard.get("source") == "live_cleaning_stats":
            self.assertEqual(guard.get("evaluation_mode"), "cleaning_preview_stop")
            self.assertEqual(guard.get("checks", {}).get("schema_check"), "review")

    def test_demo_phase_fixture_maturity_stable_unchanged(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertEqual(result.get("fixture_maturity"), "stable")
        profile = result.get("run_path_profile") or {}
        self.assertEqual(profile.get("stop_at"), "bundle")
        self.assertFalse(profile.get("experimental"))

    def test_sandbox_end_to_end_blocked_for_demo_phase(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="run",
            auto_approve_intake=True,
            sandbox_end_to_end=True,
        )
        self.assertEqual(result["final_status"], "blocked")
        self.assertEqual(result["message"], "sandbox_end_to_end_not_allowed")
        self.assertTrue(result.get("sandbox_end_to_end"))

    def test_sandbox_end_to_end_blocked_for_sandbox_client(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _SANDBOX_CLIENT,
            mode="run",
            auto_approve_intake=True,
            sandbox_end_to_end=True,
        )
        self.assertEqual(result["final_status"], "blocked")
        self.assertEqual(result["message"], "sandbox_end_to_end_not_allowed")

    def test_additional_demo_sandbox_end_to_end_produces_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _ADDITIONAL_DEMO,
                mode="run",
                auto_approve_intake=True,
                sandbox_end_to_end=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result.get("sandbox_end_to_end"))
        profile = result.get("run_path_profile") or {}
        self.assertEqual(profile.get("stop_at"), "sandbox_bundle")
        self.assertTrue(profile.get("sandbox_end_to_end"))
        run_exec = result.get("run_execution") or {}
        self.assertTrue(run_exec.get("ok"))
        self.assertIn("export.delivery_bundle", run_exec.get("tools_executed") or [])
        sandbox_delivery = result.get("sandbox_delivery") or {}
        self.assertTrue(sandbox_delivery.get("ok"))
        self.assertTrue(sandbox_delivery.get("sandbox"))
        self.assertFalse(sandbox_delivery.get("notify_triggered"))
        self.assertEqual(result["final_status"], "sandbox_e2e_complete")
        guard = result.get("output_guard") or {}
        self.assertEqual(guard.get("source"), "live_cleaning_stats")
        cp_b = result.get("checkpoint_b_status") or {}
        self.assertEqual(cp_b.get("integration_layer"), "hitl.checkpoint_b_integration_v1")
        self.assertEqual(cp_b.get("status"), "skipped")
        self.assertIn("S12_checkpoint_b_run", result.get("steps_run") or [])

    def test_sandbox_end_to_end_cli_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            payload = _run_cli_json(
                "tabular.cleaning.mvp",
                _ADDITIONAL_DEMO,
                mode="run",
                extra_args=[
                    "--auto-approve-intake",
                    "--sandbox-end-to-end",
                    "--outbox-root",
                    str(outbox),
                ],
            )
        self.assertTrue(payload.get("sandbox_end_to_end"))
        self.assertEqual(payload["final_status"], "sandbox_e2e_complete")
        self.assertIn("sandbox_delivery", payload)

    # W6-T10 integration layer wiring tests (orchestrator pass-through to W6-T5/W6-T6)

    def test_auto_approve_intake_does_not_write_checkpoint_a_file(self) -> None:
        """
        Auto-approve intake skips checkpoint A file creation.

        When --auto-approve-intake is set and intake decision is needs_review,
        the orchestrator bypasses checkpoint creation and returns status=auto_approved
        with bypass_reason. No checkpoint file is written to outbox.
        """
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result["ok"])
        cp_a = result.get("checkpoint_a_status") or {}
        self.assertEqual(cp_a.get("status"), "auto_approved")
        integration = cp_a.get("integration") or {}
        self.assertEqual(integration.get("status"), "auto_approved")
        self.assertNotIn("bypass_reason", cp_a)
        self.assertNotIn("checkpoint_path", cp_a)
        # Key assertion: NO checkpoint files written to outbox
        checkpoints = list(outbox.rglob("checkpoint_*.json"))
        self.assertEqual(
            len(checkpoints),
            0,
            f"Expected NO checkpoint files with auto_approve_intake=True, found: {checkpoints}",
        )

    def test_custom_outbox_root_outside_repo_writes_checkpoint_via_orchestrator(self) -> None:
        """
        External outbox paths are handled by integration layer three-tier fallback.

        Context: W6-T5/T6 integration layer supports external outbox paths outside
        repo_root via three-tier checkpoint_path fallback (repo-relative ->
        outbox-relative -> absolute). The orchestrator passes outbox_root_override
        directly to the integration layer (pass-through), which handles path
        resolution internally.

        This test verifies:
        1. Checkpoint file is written to the caller-specified external outbox
        2. Integration layer fallback handles external paths without error
        3. File is valid JSON with correct checkpoint_id
        4. checkpoint_path in result reflects actual file location
        """
        with tempfile.TemporaryDirectory() as tmp:
            # Temp dir is outside repo_root - integration layer three-tier fallback handles this
            external_outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=False,  # Allow checkpoint to be written
                outbox_root_override=str(external_outbox),
            )

            # Verify orchestrator result
            self.assertTrue(result["ok"])
            cp_a = result.get("checkpoint_a_status") or {}
            self.assertEqual(cp_a.get("status"), "written")

            # Checkpoint is written to the external outbox (no redirect)
            checkpoints = list(external_outbox.rglob("checkpoint_*.json"))
            self.assertGreaterEqual(
                len(checkpoints),
                1,
                f"Expected checkpoint file in external outbox {external_outbox}",
            )

            # Verify we can read the checkpoint content
            for ckpt_file in checkpoints:
                try:
                    data = json.loads(ckpt_file.read_text(encoding="utf-8"))
                    self.assertIn("checkpoint_id", data)
                    self.assertEqual(data.get("checkpoint_id"), "A-intake-confirmation")
                except (json.JSONDecodeError, OSError) as e:
                    self.fail(f"Checkpoint file {ckpt_file} is not valid JSON: {e}")

            # Verify checkpoint_path returned in result reflects actual location
            ckpt_path = cp_a.get("checkpoint_path")
            self.assertIsNotNone(ckpt_path)
            self.assertIsInstance(ckpt_path, str)
            # checkpoint_path should NOT contain .temp_test_outbox_area (no redirect)
            self.assertNotIn(".temp_test_outbox_area", ckpt_path)

            # Verify status details
            self.assertEqual(cp_a.get("checkpoint_id"), "A-intake-confirmation")
            self.assertIn("message", cp_a)

            print(f"\n[External outbox via orchestrator verified]")
            print(f"  External outbox: {external_outbox}")
            print(f"  Checkpoints found: {len(checkpoints)}")
            print(f"  Result checkpoint_path: {ckpt_path}")

    # W12-T2-P2: Sandbox E2E Checkpoint B test matrix

    def test_sandbox_e2e_checkpoint_b_skipped_ok_path_completes_bundle(self) -> None:
        """Sandbox E2E ok path: checkpoint B skipped, bundle produced.

        Uses additional_demo (controlled experimental) in sandbox_end_to_end mode.
        Output guard passes (ok_no_human_gate), so checkpoint B does not trigger.

        Expected behavior:
        - checkpoint_b_status["status"] = "skipped"
        - checkpoint_b_status["would_trigger"] = False
        - No checkpoint B file written
        - final_status = "sandbox_e2e_complete"
        - Sandbox bundle is produced
        """
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _ADDITIONAL_DEMO,
                mode="run",
                auto_approve_intake=True,
                sandbox_end_to_end=True,
                outbox_root_override=str(outbox),
            )
        # Verify sandbox e2e completes
        self.assertTrue(result.get("ok"))
        self.assertEqual(result["final_status"], "sandbox_e2e_complete")

        # Verify checkpoint B status shows skipped (ok path)
        cp_b = result.get("checkpoint_b_status") or {}
        self.assertEqual(cp_b.get("integration_layer"), "hitl.checkpoint_b_integration_v1")
        self.assertEqual(cp_b.get("status"), "skipped")
        self.assertFalse(cp_b.get("would_trigger"))
        self.assertEqual(cp_b.get("integration", {}).get("skipped"), True)
        self.assertEqual(cp_b.get("integration", {}).get("skip_reason"), "ok_no_human_gate")

        # Verify NO checkpoint B file is written (ok path)
        b_files = list(outbox.rglob("checkpoint_B*.json"))
        self.assertEqual(len(b_files), 0, "Expected NO checkpoint B file for ok path")

        # Verify sandbox bundle is produced
        sandbox_delivery = result.get("sandbox_delivery") or {}
        self.assertTrue(sandbox_delivery.get("ok"))
        self.assertTrue(sandbox_delivery.get("sandbox"))
        self.assertFalse(sandbox_delivery.get("notify_triggered"))

        # Verify bundle tools executed
        run_exec = result.get("run_execution") or {}
        self.assertIn("export.delivery_bundle", run_exec.get("tools_executed") or [])

    def test_run_mode_checkpoint_b_stops_without_auto_approve_delivery(self) -> None:
        """Run mode (non-sandbox): experimental fixture stops at checkpoint B.

        Uses additional_demo in standard run mode (not sandbox_end_to_end).
        Controlled experimental fixture triggers checkpoint B via run_path_profile.

        Expected behavior:
        - final_status = "stopped_at_checkpoint_b"
        - checkpoint_b_status["status"] = "stopped_before_delivery"
        - export.delivery_bundle NOT executed
        - No checkpoint B file written (no integration layer file creation in this path)
        """
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _ADDITIONAL_DEMO,
                mode="run",
                auto_approve_intake=True,
                # No sandbox_end_to_end, no auto_approve_delivery
                outbox_root_override=str(outbox),
            )
        # Verify stopped at checkpoint B
        self.assertTrue(result.get("ok"))
        self.assertEqual(result["final_status"], "stopped_at_checkpoint_b")

        # Verify checkpoint B status
        cp_b = result.get("checkpoint_b_status") or {}
        self.assertEqual(cp_b.get("integration_layer"), "hitl.checkpoint_b_integration_v1")
        self.assertEqual(cp_b.get("status"), "stopped_before_delivery")

        # Verify delivery bundle NOT executed (stopped before delivery)
        run_exec = result.get("run_execution") or {}
        self.assertIn("validate.eligibility", run_exec.get("tools_executed") or [])
        self.assertIn("clean.phase_demo", run_exec.get("tools_executed") or [])
        self.assertNotIn("export.delivery_bundle", run_exec.get("tools_executed") or [])

        # Verify NO sandbox delivery
        sandbox_delivery = result.get("sandbox_delivery")
        if sandbox_delivery is not None:
            self.assertFalse(sandbox_delivery.get("ok", True))

    def test_sandbox_e2e_checkpoint_b_status_integration_layer_structure(self) -> None:
        """Verify checkpoint_b_status integration layer structure in sandbox E2E.

        Validates W6-T6 integration layer wiring:
        - integration_layer field present and correct
        - integration sub-dict with expected keys
        - delivery_plan_action and sandbox_bundle_gate fields

        This test ensures the checkpoint B status contract is maintained
        regardless of whether checkpoint B is triggered or skipped.
        """
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _ADDITIONAL_DEMO,
                mode="run",
                auto_approve_intake=True,
                sandbox_end_to_end=True,
                outbox_root_override=str(outbox),
            )
        # Verify result structure
        self.assertTrue(result.get("ok"))
        self.assertEqual(result["final_status"], "sandbox_e2e_complete")

        # Verify checkpoint B status structure
        cp_b = result.get("checkpoint_b_status") or {}

        # Required fields per W6-T6 integration layer contract
        self.assertEqual(cp_b.get("checkpoint_id"), "B-delivery-confirmation")
        self.assertEqual(cp_b.get("integration_layer"), "hitl.checkpoint_b_integration_v1")
        self.assertIn("status", cp_b)
        self.assertIn("would_trigger", cp_b)
        self.assertIn("integration", cp_b)
        self.assertIn("message", cp_b)

        # Integration sub-dict structure
        integration = cp_b.get("integration") or {}
        self.assertIn("checkpoint_created", integration)
        self.assertIn("skipped", integration)

        # Additional fields for sandbox e2e path
        self.assertIn("delivery_plan_action", cp_b)
        self.assertIn("sandbox_bundle_gate", cp_b)

        # Verify S12_checkpoint_b_run is in steps_run
        steps = result.get("steps_run") or []
        self.assertIn("S12_checkpoint_b_run", steps)

    def test_sandbox_e2e_warning_writes_checkpoint_b_and_blocks_bundle(self) -> None:
        """Sandbox E2E warning path: CP-B written, bundle blocked, final_status correct.

        W12-T2 Risk-2: When output_guard.status=warning, the integration layer
        creates checkpoint B file and sandbox bundle should NOT proceed.

        Uses additional_demo (allowlisted for sandbox) with mocked output_guard
        to deterministic trigger warning path without modifying fixture data.

        Expected behavior:
        - final_status = "sandbox_e2e_blocked_at_checkpoint_b"
        - checkpoint_b_status["status"] = "written" (CP-B file created)
        - checkpoint_B_*.json file exists in outbox/{case_ref}/
        - No sandbox_delivery manifest created (bundle blocked)
        - checkpoint_b_status["integration_layer"] matches normal run path
        """
        warning_guard = {
            "status": "warning",
            "checks": {"ratio_check": "warning", "schema_check": "ok"},
            "removal_ratio": 0.75,
            "forced_cleaning": False,
            "input_rows": 12,
            "output_rows": 3,
            "note": "S11 mocked for warning path test (W12-T2-sandbox-e2e-warning)",
            "source": "mock_warning_for_test",
        }

        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"

            # Patch at the module level where the function is defined
            with patch.object(
                self.cli,
                "_read_live_output_guard",
                return_value=warning_guard,
            ):
                result = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _ADDITIONAL_DEMO,
                    mode="run",
                    auto_approve_intake=True,
                    sandbox_end_to_end=True,
                    outbox_root_override=str(outbox),
                )

            # NOTE: All assertions must be inside the tempfile.TemporaryDirectory
            # context manager to ensure the outbox directory still exists.

            # Verify result structure
            self.assertTrue(result.get("ok"))
            self.assertEqual(result["final_status"], "sandbox_e2e_blocked_at_checkpoint_b")

            # Verify sandbox_end_to_end flag set
            self.assertTrue(result.get("sandbox_end_to_end"))
            run_exec = result.get("run_execution") or {}
            self.assertTrue(run_exec.get("sandbox_bundle_blocked"))

            # Verify checkpoint B status
            cp_b = result.get("checkpoint_b_status") or {}
            self.assertEqual(cp_b.get("integration_layer"), "hitl.checkpoint_b_integration_v1")
            self.assertEqual(cp_b.get("status"), "written")
            self.assertTrue(cp_b.get("would_trigger"))
            self.assertEqual(cp_b.get("delivery_plan_action"), "await_human")
            self.assertEqual(cp_b.get("sandbox_bundle_gate"), "checkpoint_b_written")

            # Verify integration sub-dict structure (consistent with normal run path)
            integration = cp_b.get("integration") or {}
            self.assertTrue(integration.get("checkpoint_created"))
            # checkpoint_id is at top level of cp_b, not in integration sub-dict
            self.assertEqual(cp_b.get("checkpoint_id"), "B-delivery-confirmation")

            # Verify CP-B file was written to outbox
            b_files = list(outbox.rglob("checkpoint_B*.json"))
            self.assertGreaterEqual(
                len(b_files),
                1,
                f"Expected checkpoint B file in outbox, found: {b_files}",
            )

            # Verify checkpoint_B file contains valid JSON with expected structure
            for b_file in b_files:
                try:
                    data = json.loads(b_file.read_text(encoding="utf-8"))
                    self.assertEqual(data.get("checkpoint_id"), "B-delivery-confirmation")
                    self.assertEqual(data.get("case_ref"), "additional_demo")
                    # Verify output_guard in checkpoint file (nested in agent_output)
                    agent_output = data.get("agent_output") or {}
                    file_guard = agent_output.get("output_guard") or {}
                    self.assertEqual(file_guard.get("status"), "warning")
                except (json.JSONDecodeError, OSError) as e:
                    self.fail(f"Checkpoint B file {b_file} is not valid JSON: {e}")

            # Verify NO sandbox delivery bundle created (bundle blocked)
            sandbox_delivery = result.get("sandbox_delivery")
            self.assertFalse(
                sandbox_delivery is not None and sandbox_delivery.get("ok"),
                "sandbox_delivery should NOT be created when CP-B blocks bundle",
            )

            # Verify export.delivery_bundle NOT executed (bundle blocked)
            self.assertNotIn(
                "export.delivery_bundle",
                run_exec.get("tools_executed") or [],
                "delivery_bundle should NOT be executed when CP-B blocks",
            )

            # Verify pre-bundle tools were executed (cleaning completed)
            self.assertIn("validate.eligibility", run_exec.get("tools_executed") or [])
            self.assertIn("clean.phase_demo", run_exec.get("tools_executed") or [])

            # Verify steps_run includes S12_checkpoint_b_run
            steps = result.get("steps_run") or []
            self.assertIn("S12_checkpoint_b_run", steps)

    # W10-T3: orchestrator registry fail-closed wiring

    def _mock_tool_path_registry_fail_closed(
        self,
        *,
        rule_id: str = "error.registry_fail_closed",
    ) -> dict:
        return {
            "ok": True,
            "mode": "dry_run_preview",
            "glue_plan": {},
            "selector_view": {
                "ok": False,
                "selector_rule_id": rule_id,
                "selector_task_type": "e2e",
                "candidates": [],
                "per_step": [],
                "notes": [f"overall selector failed: {rule_id}"],
            },
            "executor_plan": [],
            "notes": ["path preview only"],
            "message": "dry-run preview for tabular.cleaning.mvp",
        }

    def test_registry_fail_closed_blocks_run_path_no_checkpoints(self) -> None:
        """W10-T3: registry fail-closed blocks run path; no CP-A/B; no tool execution."""
        mock_path = self._mock_tool_path_registry_fail_closed()
        with mock.patch.object(
            self.cli,
            "run_tabular_intake_tool_path",
            return_value=mock_path,
        ):
            with tempfile.TemporaryDirectory() as tmp:
                outbox = Path(tmp) / "outbox"
                result = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _DEMO_PHASE,
                    mode="run",
                    auto_approve_intake=True,
                    outbox_root_override=str(outbox),
                )
        self.assertFalse(result["ok"])
        self.assertEqual(result["final_status"], "blocked_at_selector_registry")
        self.assertNotIn("run_execution", result)
        steps = result.get("steps_run") or []
        self.assertIn("S6_selector_registry_blocked", steps)
        self.assertNotIn("S7_S10_run_path_execution", steps)
        self.assertNotIn("S4_checkpoint_a", steps)
        cp_a = result["checkpoint_a_status"]
        self.assertEqual(cp_a["status"], "not_applicable")
        cp_b = result["checkpoint_b_status"]
        self.assertEqual(cp_b["status"], "not_applicable")
        checkpoints = list(outbox.rglob("checkpoint_*.json"))
        self.assertEqual(checkpoints, [])
        selector = (result.get("tool_path_preview") or {}).get("selector_view") or {}
        self.assertEqual(selector.get("error_rule_id"), "error.registry_fail_closed")

    def test_registry_not_approved_blocks_preview_mode(self) -> None:
        """W10-T3: registry_not_approved fail-closes in preview mode too."""
        mock_path = self._mock_tool_path_registry_fail_closed(
            rule_id="error.registry_not_approved",
        )
        with mock.patch.object(
            self.cli,
            "run_tabular_intake_tool_path",
            return_value=mock_path,
        ):
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="preview",
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["final_status"], "blocked_at_selector_registry")
        self.assertNotIn("run_execution", result)
        selector = (result.get("tool_path_preview") or {}).get("selector_view") or {}
        self.assertEqual(selector.get("error_rule_id"), "error.registry_not_approved")

    def test_ok_path_regression_after_registry_wiring(self) -> None:
        """W10-T3: ok selector path unchanged — run mode still executes tools."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
            )
        self.assertTrue(result["ok"])
        self.assertIn("run_execution", result)
        self.assertIn("S7_S10_run_path_execution", result.get("steps_run") or [])
        self.assertNotEqual(result["final_status"], "blocked_at_selector_registry")
        preview = result.get("tool_path_preview") or {}
        self.assertTrue((preview.get("selector_view") or {}).get("ok"))

    # W6-T11-P2/P3: checkpoint resume loop (happy path + fail-close matrix)

    def test_approved_checkpoint_a_resume_runs_s7_path(self) -> None:
        """P2 happy path: approved Checkpoint A resume skips S3–S6 and continues at S7."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            initial = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=False,
                outbox_root_override=str(outbox),
            )
            self.assertEqual(initial["final_status"], "waiting_for_human")
            ckpt_files = list(outbox.rglob("checkpoint_A*.json"))
            self.assertEqual(len(ckpt_files), 1)
            _apply_human_decision_to_checkpoint_file(ckpt_files[0], "approve")
            resumed = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                resume_checkpoint=str(ckpt_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertTrue(resumed.get("ok"))
        resume = resumed.get("resume") or {}
        self.assertTrue(resume.get("ok"))
        self.assertEqual(resume.get("resume_from_step"), "S7")
        steps = resumed.get("steps_run") or []
        self.assertIn("S7_S10_run_path_execution", steps)
        self.assertNotIn("S3_decision_evaluate", steps)
        for skipped in (
            "S3_decision_evaluate",
            "S4_checkpoint_a",
            "S5_route_planning",
            "S6_tool_path_preview",
        ):
            self.assertIn(skipped, resume.get("skipped_steps") or [])

    def test_approved_checkpoint_b_resume_runs_s13_delivery(self) -> None:
        """P2 happy path: approved Checkpoint B resume skips S3–S12 and runs S13 delivery."""
        warning_guard = {
            "status": "warning",
            "checks": {"ratio_check": "warning", "schema_check": "ok"},
            "removal_ratio": 0.93,
            "forced_cleaning": False,
            "source": "mock_warning_for_cp_b_resume_test",
        }
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            with patch.object(
                self.cli,
                "_read_live_output_guard",
                return_value=warning_guard,
            ):
                initial = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _SAMPLECO,
                    mode="run",
                    auto_approve_intake=True,
                    outbox_root_override=str(outbox),
                )
            self.assertEqual(initial["final_status"], "stopped_at_checkpoint_b")
            b_files = list(outbox.rglob("checkpoint_B*.json"))
            self.assertGreaterEqual(len(b_files), 1)
            _apply_human_decision_to_checkpoint_file(b_files[0], "approve_delivery")
            resumed = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _SAMPLECO,
                mode="run",
                resume_checkpoint=str(b_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertTrue(resumed.get("ok"))
        resume = resumed.get("resume") or {}
        self.assertTrue(resume.get("ok"))
        self.assertEqual(resume.get("resume_from_step"), "S13")
        self.assertIn("S13_delivery_export", resumed.get("steps_run") or [])
        run_exec = resumed.get("run_execution") or {}
        self.assertIn("export.delivery_bundle", run_exec.get("tools_executed") or [])
        self.assertEqual(resumed.get("final_status"), "run_complete")

    def test_resume_checkpoint_case_ref_mismatch_blocked(self) -> None:
        """P2 fail-close: checkpoint case_ref ≠ CLI --case-dir → checkpoint_mismatch."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            initial = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=False,
                outbox_root_override=str(outbox),
            )
            self.assertEqual(initial["final_status"], "waiting_for_human")
            ckpt_files = list(outbox.rglob("checkpoint_A*.json"))
            _apply_human_decision_to_checkpoint_file(ckpt_files[0], "approve")
            resumed = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _SAMPLECO,
                mode="run",
                resume_checkpoint=str(ckpt_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertFalse(resumed.get("ok"))
        self.assertEqual(resumed.get("final_status"), "checkpoint_mismatch")
        self.assertFalse((resumed.get("resume") or {}).get("ok", True))

    def test_resume_checkpoint_awaiting_human_blocked(self) -> None:
        """P3 reviewer #1: resume before --apply-decision → blocked (awaiting_human)."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            initial = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=False,
                outbox_root_override=str(outbox),
            )
            self.assertEqual(initial["final_status"], "waiting_for_human")
            ckpt_files = list(outbox.rglob("checkpoint_A*.json"))
            self.assertEqual(len(ckpt_files), 1)
            resumed = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                resume_checkpoint=str(ckpt_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertFalse(resumed.get("ok"))
        self.assertEqual(resumed.get("final_status"), "blocked")
        self.assertIn(
            "awaiting human decision",
            (resumed.get("message") or "").lower(),
        )
        self.assertFalse((resumed.get("resume") or {}).get("ok", True))

    def test_resume_checkpoint_preview_mode_blocked(self) -> None:
        """P3 reviewer #2: --mode preview + --resume-checkpoint → blocked."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            initial = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=False,
                outbox_root_override=str(outbox),
            )
            ckpt_files = list(outbox.rglob("checkpoint_A*.json"))
            _apply_human_decision_to_checkpoint_file(ckpt_files[0], "approve")
            resumed = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="preview",
                resume_checkpoint=str(ckpt_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertFalse(resumed.get("ok"))
        self.assertEqual(resumed.get("final_status"), "blocked")
        self.assertIn("resume requires --mode run", resumed.get("message") or "")
        self.assertFalse((resumed.get("resume") or {}).get("ok", True))

    def test_resume_checkpoint_duplicate_delivery_blocked(self) -> None:
        """P3 reviewer #3: second B resume for same checkpoint → duplicate_delivery."""
        warning_guard = {
            "status": "warning",
            "checks": {"ratio_check": "warning", "schema_check": "ok"},
            "removal_ratio": 0.93,
            "forced_cleaning": False,
            "source": "mock_warning_for_cp_b_duplicate_resume_test",
        }
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            with patch.object(
                self.cli,
                "_read_live_output_guard",
                return_value=warning_guard,
            ):
                initial = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _SAMPLECO,
                    mode="run",
                    auto_approve_intake=True,
                    outbox_root_override=str(outbox),
                )
            b_files = list(outbox.rglob("checkpoint_B*.json"))
            _apply_human_decision_to_checkpoint_file(b_files[0], "approve_delivery")
            first = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _SAMPLECO,
                mode="run",
                resume_checkpoint=str(b_files[0]),
                outbox_root_override=str(outbox),
            )
            self.assertTrue(first.get("ok"))
            second = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _SAMPLECO,
                mode="run",
                resume_checkpoint=str(b_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertFalse(second.get("ok"))
        self.assertEqual(second.get("final_status"), "duplicate_delivery")
        self.assertIn("delivery already resumed", second.get("message") or "")
        self.assertFalse((second.get("resume") or {}).get("ok", True))

    def test_resume_checkpoint_b_stale_artifacts_blocked(self) -> None:
        """P3 reviewer #4: missing B resume artifacts → fail-close (stale)."""
        warning_guard = {
            "status": "warning",
            "checks": {"ratio_check": "warning", "schema_check": "ok"},
            "removal_ratio": 0.93,
            "forced_cleaning": False,
            "source": "mock_warning_for_cp_b_stale_artifacts_test",
        }
        cleaned_dir = _REPO_ROOT / _SAMPLECO / "cleaned"
        cleaned_backup = cleaned_dir.with_name("cleaned.w6t11_stale_bak")
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            with patch.object(
                self.cli,
                "_read_live_output_guard",
                return_value=warning_guard,
            ):
                initial = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _SAMPLECO,
                    mode="run",
                    auto_approve_intake=True,
                    outbox_root_override=str(outbox),
                )
            self.assertEqual(initial["final_status"], "stopped_at_checkpoint_b")
            b_files = list(outbox.rglob("checkpoint_B*.json"))
            _apply_human_decision_to_checkpoint_file(b_files[0], "approve_delivery")
            data = json.loads(b_files[0].read_text(encoding="utf-8"))
            artifacts = (data.get("resume_context") or {}).setdefault("artifacts", {})
            artifacts["eligibility_report"] = "outbox/_w6t11_stale_missing/eligibility.json"
            artifacts["cleaned_csv"] = "outbox/_w6t11_stale_missing/cleaned.csv"
            b_files[0].write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            moved_cleaned = False
            if cleaned_dir.is_dir():
                if cleaned_backup.is_dir():
                    shutil.rmtree(cleaned_backup)
                shutil.move(str(cleaned_dir), str(cleaned_backup))
                moved_cleaned = True
            try:
                resumed = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _SAMPLECO,
                    mode="run",
                    resume_checkpoint=str(b_files[0]),
                    outbox_root_override=str(outbox),
                )
            finally:
                if moved_cleaned and cleaned_backup.is_dir():
                    if cleaned_dir.is_dir():
                        shutil.rmtree(cleaned_dir)
                    shutil.move(str(cleaned_backup), str(cleaned_dir))
        self.assertFalse(resumed.get("ok"))
        self.assertEqual(resumed.get("final_status"), "blocked")
        self.assertIn("stale checkpoint artifacts", resumed.get("message") or "")
        self.assertFalse((resumed.get("resume") or {}).get("ok", True))

    def test_resume_checkpoint_task_type_mismatch_blocked(self) -> None:
        """P3 reviewer secondary: checkpoint task_type ≠ CLI --task-type → mismatch."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            initial = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=False,
                outbox_root_override=str(outbox),
            )
            ckpt_files = list(outbox.rglob("checkpoint_A*.json"))
            _apply_human_decision_to_checkpoint_file(ckpt_files[0], "approve")
            resumed = self.cli.run_agent_standard_case_experiment(
                "gov.observability.eval",
                _DEMO_PHASE,
                mode="run",
                resume_checkpoint=str(ckpt_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertFalse(resumed.get("ok"))
        self.assertEqual(resumed.get("final_status"), "checkpoint_mismatch")
        self.assertIn("task_type mismatch", resumed.get("message") or "")
        self.assertFalse((resumed.get("resume") or {}).get("ok", True))

    def test_resume_checkpoint_rejected_status_blocked(self) -> None:
        """P3 reviewer secondary: status=rejected checkpoint → blocked."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            initial = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=False,
                outbox_root_override=str(outbox),
            )
            ckpt_files = list(outbox.rglob("checkpoint_A*.json"))
            data = json.loads(ckpt_files[0].read_text(encoding="utf-8"))
            data["status"] = "rejected"
            data["human_decision"] = {
                "action": "reject",
                "operator_id": "unit_test",
                "comment": "rejected in unit test",
            }
            ckpt_files[0].write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            resumed = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                resume_checkpoint=str(ckpt_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertFalse(resumed.get("ok"))
        self.assertEqual(resumed.get("final_status"), "blocked")
        self.assertIn("status='rejected'", resumed.get("message") or "")
        self.assertFalse((resumed.get("resume") or {}).get("ok", True))

    def test_resume_checkpoint_wrong_human_action_blocked(self) -> None:
        """P3 reviewer secondary: approved CP-B with wrong human action → blocked."""
        warning_guard = {
            "status": "warning",
            "checks": {"ratio_check": "warning", "schema_check": "ok"},
            "removal_ratio": 0.93,
            "forced_cleaning": False,
            "source": "mock_warning_for_cp_b_wrong_action_test",
        }
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            with patch.object(
                self.cli,
                "_read_live_output_guard",
                return_value=warning_guard,
            ):
                initial = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _SAMPLECO,
                    mode="run",
                    auto_approve_intake=True,
                    outbox_root_override=str(outbox),
                )
            b_files = list(outbox.rglob("checkpoint_B*.json"))
            data = json.loads(b_files[0].read_text(encoding="utf-8"))
            _apply_human_decision_to_checkpoint_file(b_files[0], "approve_delivery")
            data = json.loads(b_files[0].read_text(encoding="utf-8"))
            data["resume_context"]["human_decision"]["action"] = "request_changes"
            data["human_decision"]["action"] = "request_changes"
            b_files[0].write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            resumed = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _SAMPLECO,
                mode="run",
                resume_checkpoint=str(b_files[0]),
                outbox_root_override=str(outbox),
            )
        self.assertFalse(resumed.get("ok"))
        self.assertEqual(resumed.get("final_status"), "blocked")
        self.assertIn("approve_delivery", resumed.get("message") or "")
        self.assertFalse((resumed.get("resume") or {}).get("ok", True))


def _apply_human_decision_to_checkpoint_file(path: Path, action: str) -> None:
    from datetime import datetime, timezone

    from hitl.checkpoints_v1 import (
        CHECKPOINT_A_ID,
        CHECKPOINT_B_ID,
        build_resume_context,
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    resolved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    human_decision = {
        "action": action,
        "operator_id": "unit_test",
        "comment": "unit test decision",
        "timestamp": resolved_at,
        "by": "unit_test",
        "at": resolved_at,
    }
    resume_context = build_resume_context(data, human_decision)
    checkpoint_id = str(data.get("checkpoint_id") or "")
    if checkpoint_id == CHECKPOINT_A_ID:
        status = "approved" if action == "approve" else str(data.get("status") or "blocked")
    elif checkpoint_id == CHECKPOINT_B_ID:
        status = "approved" if action == "approve_delivery" else str(data.get("status") or "blocked")
    else:
        status = "approved"
    data["human_decision"] = human_decision
    data["resume_context"] = resume_context
    data["status"] = status
    data["resolved_at"] = resolved_at
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
