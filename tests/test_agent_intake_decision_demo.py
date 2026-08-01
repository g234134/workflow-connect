"""Unit tests for Agent/Orchestrator intake decision demo CLI (W5-T1B)."""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "run_agent_intake_decision_demo.py"
_DEMO_PHASE = "cases/demo_phase"
_SAMPLECO = "cases/sampleco/2026-0001"

_FORBIDDEN_IMPORT_PREFIXES = (
    "scripts.new_cleaning_case",
    "app.local_ui",
    "scripts.run_mvp_mainline_regression",
    "tools.tabular_tool_executor",
)


def _load_cli_module():
    spec = importlib.util.spec_from_file_location(
        "run_agent_intake_decision_demo", _CLI_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_intake_decision_demo"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_cli_json(task_type: str, case_dir: str) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(_CLI_PATH),
            "--task-type",
            task_type,
            "--case-dir",
            case_dir,
            "--format",
            "json",
        ],
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


def _assert_w5_t1_shape(result: dict) -> None:
    for key in (
        "ok",
        "task_type",
        "case_dir",
        "decision",
        "risk_level",
        "rationale",
    ):
        assert key in result, f"missing key: {key}"
    assert result["ok"] is True
    assert result["decision"] in ("auto_accept", "needs_review", "reject")
    assert result["risk_level"] in ("low", "medium", "high")
    assert isinstance(result["rationale"], list)


class TestAgentIntakeDecisionDemo(unittest.TestCase):
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

    def test_demo_phase_cleaning_needs_review_medium(self) -> None:
        result = self.cli.run_agent_intake_decision(
            "tabular.cleaning.mvp", _DEMO_PHASE
        )
        _assert_w5_t1_shape(result)
        self.assertEqual(result["decision"], "needs_review")
        self.assertEqual(result["risk_level"], "medium")
        route = result["suggested_route"]
        self.assertIsInstance(route, dict)
        self.assertEqual(
            route["planned_tools"],
            [
                "validate.eligibility",
                "clean.phase_demo",
                "export.delivery_bundle",
            ],
        )

        payload = _run_cli_json("tabular.cleaning.mvp", _DEMO_PHASE)
        _assert_w5_t1_shape(payload)
        self.assertEqual(payload["decision"], "needs_review")
        self.assertEqual(payload["risk_level"], "medium")

    def test_demo_phase_intake_new_case_auto_accept_low(self) -> None:
        result = self.cli.run_agent_intake_decision(
            "tabular.intake.new_case", _DEMO_PHASE
        )
        _assert_w5_t1_shape(result)
        self.assertEqual(result["decision"], "auto_accept")
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(
            result["suggested_route"]["planned_tools"], ["intake.new_case"]
        )

    def test_sampleco_cleaning_needs_review_medium(self) -> None:
        result = self.cli.run_agent_intake_decision(
            "tabular.cleaning.mvp", _SAMPLECO
        )
        _assert_w5_t1_shape(result)
        self.assertEqual(result["decision"], "needs_review")
        self.assertEqual(result["risk_level"], "medium")
        rationale_text = " ".join(result["rationale"]).lower()
        self.assertTrue(
            "human_review_required" in rationale_text
            or "schema_ambiguous" in rationale_text,
            f"expected review signals in rationale: {result['rationale']}",
        )

    def test_non_tabular_reject_high(self) -> None:
        result = self.cli.run_agent_intake_decision(
            "gov.observability.eval", _DEMO_PHASE
        )
        _assert_w5_t1_shape(result)
        self.assertEqual(result["decision"], "reject")
        self.assertEqual(result["risk_level"], "high")
        self.assertIsNone(result["suggested_route"])
        self.assertIn("non_tabular_family", result["message"])

    def test_text_format_includes_summary_fields(self) -> None:
        result = self.cli.run_agent_intake_decision(
            "tabular.cleaning.mvp", _DEMO_PHASE
        )
        text = self.cli.format_decision_summary_text(result)
        self.assertIn("task_type:", text)
        self.assertIn("case_dir:", text)
        self.assertIn("decision:", text)
        self.assertIn("risk_level:", text)
        self.assertIn("rationale:", text)
        self.assertIn("suggested_route.planned_tools:", text)
        self.assertIn("validate.eligibility", text)


if __name__ == "__main__":
    unittest.main()
