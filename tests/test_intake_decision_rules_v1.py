"""Unit tests for intake decision rules v1 (W5-T1)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

from routing.intake_decision_rules_v1 import evaluate_intake_decision

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = _REPO_ROOT / "routing" / "intake_decision_rules_v1.py"
_DEMO_PHASE = "cases/demo_phase"
_SAMPLECO = "cases/sampleco/2026-0001"
_BAD_CASE_DIR = "cases/does_not_exist_zzzz"

_FORBIDDEN_IMPORT_PREFIXES = (
    "scripts.new_cleaning_case",
    "app.local_ui",
    "tools.tabular_tool_executor",
)


def _assert_decision_shape(result: dict) -> None:
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
    if result["decision"] != "reject":
        assert "suggested_route" in result
        route = result["suggested_route"]
        assert isinstance(route, dict)
        assert "selector_task_type" in route
        assert "planned_tools" in route
        assert isinstance(route["planned_tools"], list)


class TestIntakeDecisionRulesV1(unittest.TestCase):
    def test_module_does_not_import_forbidden_modules(self) -> None:
        source = _MODULE_PATH.read_text(encoding="utf-8")
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

    def test_demo_phase_cleaning_mvp_needs_review(self) -> None:
        result = evaluate_intake_decision("tabular.cleaning.mvp", _DEMO_PHASE)
        _assert_decision_shape(result)
        self.assertEqual(result["task_type"], "tabular.cleaning.mvp")
        self.assertEqual(result["case_dir"], _DEMO_PHASE)
        self.assertIn(result["decision"], ("auto_accept", "needs_review"))
        if result["decision"] == "needs_review":
            self.assertEqual(result["risk_level"], "medium")
            rationale_text = " ".join(result["rationale"])
            self.assertIn("manual_review_required", rationale_text)
        route = result["suggested_route"]
        self.assertEqual(route["selector_task_type"], "e2e")
        self.assertEqual(
            route["planned_tools"],
            [
                "validate.eligibility",
                "clean.phase_demo",
                "export.delivery_bundle",
            ],
        )

    def test_demo_phase_intake_new_case_auto_accept(self) -> None:
        result = evaluate_intake_decision("tabular.intake.new_case", _DEMO_PHASE)
        _assert_decision_shape(result)
        self.assertEqual(result["decision"], "auto_accept")
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["suggested_route"]["planned_tools"], ["intake.new_case"])

    def test_sampleco_needs_review(self) -> None:
        result = evaluate_intake_decision("tabular.cleaning.mvp", _SAMPLECO)
        _assert_decision_shape(result)
        self.assertEqual(result["decision"], "needs_review")
        self.assertEqual(result["risk_level"], "medium")
        rationale_text = " ".join(result["rationale"]).lower()
        self.assertTrue(
            "human_review_required" in rationale_text
            or "schema_ambiguous" in rationale_text,
            f"expected review signals in rationale: {result['rationale']}",
        )
        self.assertEqual(result["suggested_route"]["selector_task_type"], "e2e")

    def test_unsupported_family_reject(self) -> None:
        result = evaluate_intake_decision("gov.observability.eval", _DEMO_PHASE)
        _assert_decision_shape(result)
        self.assertEqual(result["decision"], "reject")
        self.assertEqual(result["risk_level"], "high")
        self.assertIsNone(result["suggested_route"])
        self.assertIn("non_tabular_family", result["message"])

    def test_bad_case_dir_reject(self) -> None:
        result = evaluate_intake_decision("tabular.cleaning.mvp", _BAD_CASE_DIR)
        _assert_decision_shape(result)
        self.assertEqual(result["decision"], "reject")
        self.assertEqual(result["risk_level"], "high")
        self.assertIsNone(result["suggested_route"])
        self.assertEqual(result["message"], "case_dir_not_found")

    def test_tabular_cleaning_regression_allowlist(self) -> None:
        result = evaluate_intake_decision("tabular.cleaning.regression", _DEMO_PHASE)
        _assert_decision_shape(result)
        self.assertIn(result["decision"], ("auto_accept", "needs_review"))
        self.assertEqual(
            result["suggested_route"]["planned_tools"],
            ["orchestrate.mainline_regression"],
        )

    def test_cli_json_demo_phase(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_MODULE_PATH),
                "--task-type",
                "tabular.cleaning.mvp",
                "--case-dir",
                _DEMO_PHASE,
                "--json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        _assert_decision_shape(payload)
        self.assertEqual(payload["case_dir"], _DEMO_PHASE)


if __name__ == "__main__":
    unittest.main()
