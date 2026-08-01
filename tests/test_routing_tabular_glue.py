"""Unit tests for Routing → Tabular Tool Layer glue v1 (W4-T1)."""

from __future__ import annotations

import ast
import inspect
import unittest
from pathlib import Path

from routing.intake_to_tabular_glue import (
    TABULAR_ROUTING_GLUE_ENABLED,
    plan_tabular_route,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GLUE_MODULE_PATH = _REPO_ROOT / "routing" / "intake_to_tabular_glue.py"
_DEMO_PHASE = "cases/demo_phase"
_SAMPLECO = "cases/sampleco/2026-0001"

_MVP_PLANNED_TOOLS = [
    "validate.eligibility",
    "clean.phase_demo",
    "export.delivery_bundle",
]

_FORBIDDEN_IMPORT_PREFIXES = (
    "scripts.run_case_e2e_validation",
    "scripts.run_mvp_mainline_regression",
    "tools.tabular_tool_executor",
)


def _assert_plan_shape(result: dict, *, expect_ok: bool) -> None:
    for key in ("ok", "task_type", "case_dir", "glue_enabled"):
        assert key in result, f"missing key: {key}"
    assert result["ok"] is expect_ok
    if expect_ok:
        for key in ("selector_task_type", "planned_tools", "notes", "message"):
            assert key in result, f"missing success key: {key}"
        assert isinstance(result["planned_tools"], list)
        assert isinstance(result["notes"], list)


class TestRoutingTabularGlue(unittest.TestCase):
    def test_glue_feature_flag_defaults_off(self) -> None:
        self.assertFalse(TABULAR_ROUTING_GLUE_ENABLED)

    def test_glue_module_does_not_import_forbidden_modules(self) -> None:
        source = _GLUE_MODULE_PATH.read_text(encoding="utf-8")
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

    def test_plan_tabular_route_signature(self) -> None:
        sig = inspect.signature(plan_tabular_route)
        params = list(sig.parameters)
        self.assertEqual(params, ["task_type", "case_dir"])

    def test_demo_phase_tabular_cleaning_mvp(self) -> None:
        result = plan_tabular_route("tabular.cleaning.mvp", _DEMO_PHASE)
        _assert_plan_shape(result, expect_ok=True)
        self.assertEqual(result["task_type"], "tabular.cleaning.mvp")
        self.assertEqual(result["case_dir"], _DEMO_PHASE)
        self.assertEqual(result["case_profile"], "demo_phase")
        self.assertEqual(result["selector_task_type"], "e2e")
        self.assertEqual(result["planned_tools"], _MVP_PLANNED_TOOLS)
        self.assertEqual(result["routing_catalog_tool_ids"], _MVP_PLANNED_TOOLS)
        self.assertEqual(result["orchestration_tool_id"], "orchestrate.e2e")
        notes_text = " ".join(result["notes"])
        self.assertIn("manual_review_required", notes_text)
        self.assertIn("requires --force", notes_text)

    def test_sampleco_tabular_cleaning_mvp(self) -> None:
        result = plan_tabular_route("tabular.cleaning.mvp", _SAMPLECO)
        _assert_plan_shape(result, expect_ok=True)
        self.assertEqual(result["case_profile"], "sampleco")
        self.assertEqual(result["planned_tools"], _MVP_PLANNED_TOOLS)
        notes_text = " ".join(result["notes"])
        self.assertIn("human_review_required", notes_text)
        self.assertIn("multi_row_export", notes_text)
        self.assertIn("schema_ambiguous", notes_text)
        gate_notes = result.get("inferred_gate_notes") or []
        self.assertIn("multi_row_export", gate_notes)
        self.assertIn("schema_ambiguous", gate_notes)

    def test_tabular_cleaning_regression(self) -> None:
        result = plan_tabular_route("tabular.cleaning.regression", _DEMO_PHASE)
        _assert_plan_shape(result, expect_ok=True)
        self.assertEqual(result["selector_task_type"], "e2e")
        self.assertEqual(result["planned_tools"], ["orchestrate.mainline_regression"])

    def test_unsupported_task_type(self) -> None:
        result = plan_tabular_route("gov.observability.eval", _DEMO_PHASE)
        _assert_plan_shape(result, expect_ok=False)
        self.assertEqual(result["message"], "unsupported_task_type")

    def test_planned_tools_subset_of_routing_catalog(self) -> None:
        for case_dir in (_DEMO_PHASE, _SAMPLECO):
            result = plan_tabular_route("tabular.cleaning.mvp", case_dir)
            self.assertTrue(result["ok"])
            routing_ids = set(result["routing_catalog_tool_ids"])
            for tool_id in result["planned_tools"]:
                self.assertIn(tool_id, routing_ids)

    def test_selector_task_type_alignment_documented_steps(self) -> None:
        """Static alignment: e2e plan steps map to selector intents (no Selector import)."""
        result = plan_tabular_route("tabular.cleaning.mvp", _DEMO_PHASE)
        self.assertEqual(result["selector_task_type"], "e2e")
        step_to_selector = {
            "validate.eligibility": "gate_only",
            "clean.phase_demo": "clean",
            "export.delivery_bundle": "bundle",
        }
        for tool_id in result["planned_tools"]:
            self.assertIn(tool_id, step_to_selector)


if __name__ == "__main__":
    unittest.main()
