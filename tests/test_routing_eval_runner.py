"""Unit tests for routing eval runner v1 (W4-T2)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RUNNER_PATH = _REPO_ROOT / "scripts" / "run_routing_eval.py"
_CASES_PATH = _REPO_ROOT / "routing" / "routing_eval_cases_v1.yaml"
_CATALOG_PATH = _REPO_ROOT / "routing" / "intake_routing_catalog_v1.yaml"

_KNOWN_CASE_IDS = frozenset(
    {
        "tabular_demo_phase_clean",
        "tabular_sampleco_e2e",
        "gov_obs_eval_gate",
        "tabular_mainline_regression",
    }
)


def _load_runner_module():
    spec = importlib.util.spec_from_file_location("run_routing_eval", _RUNNER_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_routing_eval"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestRoutingEvalRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _RUNNER_PATH.is_file():
            raise unittest.SkipTest(f"missing runner: {_RUNNER_PATH}")
        if not _CASES_PATH.is_file():
            raise unittest.SkipTest(f"missing cases: {_CASES_PATH}")
        cls.runner = _load_runner_module()

    def test_dry_run_all_known_cases_ok(self) -> None:
        report = self.runner.run_eval(dry_run=True)
        self.assertTrue(report.get("ok"), msg=report.get("message"))
        self.assertEqual(report.get("cases_run"), 4)
        self.assertEqual(report.get("cases_ok"), 4)
        result_ids = {r["id"] for r in report.get("results") or []}
        self.assertEqual(result_ids, _KNOWN_CASE_IDS)

    def test_each_case_has_task_type_in_catalog(self) -> None:
        catalog = self.runner.load_routing_catalog()
        routes = self.runner._routes_by_task_type(catalog)
        report = self.runner.run_eval(dry_run=True)
        for item in report["results"]:
            with self.subTest(case_id=item["id"]):
                self.assertIn(item["task_type"], routes)

    def test_tabular_cases_planned_tools_cover_expected(self) -> None:
        report = self.runner.run_eval(dry_run=True)
        tabular_ids = {
            "tabular_demo_phase_clean",
            "tabular_sampleco_e2e",
            "tabular_mainline_regression",
        }
        for item in report["results"]:
            if item["id"] not in tabular_ids:
                continue
            with self.subTest(case_id=item["id"]):
                self.assertTrue(item["ok"], msg=item.get("message"))
                planned = set(item.get("planned_tools") or [])
                for tid in item.get("expected_tool_ids") or []:
                    self.assertIn(tid, planned)

    def test_gov_case_policy_alignment(self) -> None:
        report = self.runner.run_eval(dry_run=True)
        gov = next(r for r in report["results"] if r["id"] == "gov_obs_eval_gate")
        self.assertTrue(gov["ok"], msg=gov.get("message"))
        self.assertEqual(gov["family"], "gov_registry")
        self.assertEqual(gov.get("policy_route_id"), "wave_b.eval_report")
        planned = set(gov.get("planned_tools") or [])
        for tid in gov.get("expected_tool_ids") or []:
            self.assertIn(tid, planned)

    def test_demo_phase_case_details(self) -> None:
        report = self.runner.run_eval(case_id="tabular_demo_phase_clean", dry_run=True)
        self.assertEqual(report["cases_run"], 1)
        item = report["results"][0]
        self.assertTrue(item["ok"])
        self.assertEqual(item["case_dir"], "cases/demo_phase")
        self.assertEqual(
            item["planned_tools"],
            ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"],
        )
        self.assertEqual(item["mismatched_tools"], [])

    def test_unknown_case_id_returns_not_found(self) -> None:
        report = self.runner.run_eval(case_id="no_such_case_xyz", dry_run=True)
        self.assertFalse(report["ok"])
        self.assertEqual(report["cases_run"], 0)
        self.assertIn("not found", report.get("message", ""))

    def test_missing_route_case_fails(self) -> None:
        cases_doc = self.runner.load_eval_cases()
        catalog = self.runner.load_routing_catalog()
        bad_case = {
            "id": "synthetic_missing_route",
            "task_type": "nonexistent.task.type.xyz",
            "input_summary": "synthetic",
            "expected_families": ["tabular_mvp"],
            "expected_tool_ids": ["validate.eligibility"],
        }
        result = self.runner.evaluate_case(bad_case, catalog=catalog, dry_run=True)
        self.assertFalse(result["ok"])
        self.assertIn("not found", result.get("message", ""))

    def test_tabular_case_without_case_dir_fails(self) -> None:
        catalog = self.runner.load_routing_catalog()
        bad_case = {
            "id": "synthetic_no_case_dir",
            "task_type": "tabular.cleaning.mvp",
            "input_summary": "synthetic",
            "expected_families": ["tabular_mvp"],
            "expected_tool_ids": ["validate.eligibility"],
            "input_context": {},
        }
        result = self.runner.evaluate_case(bad_case, catalog=catalog, dry_run=True)
        self.assertFalse(result["ok"])
        self.assertIn("case_dir", result.get("message", ""))

    def test_execute_path_uses_subprocess_mock(self) -> None:
        smoke = {"ok": True, "exit_code": 0, "command": "mock"}
        with mock.patch.object(self.runner, "_run_mainline_regression_subprocess", return_value=smoke):
            report = self.runner.run_eval(
                case_id="tabular_mainline_regression",
                dry_run=False,
                execute=True,
            )
        item = report["results"][0]
        self.assertIn("execute", item)
        self.assertTrue(item["execute"]["ok"])
        self.assertTrue(item["ok"])

    def test_format_table_non_empty(self) -> None:
        report = self.runner.run_eval(dry_run=True)
        table = self.runner._format_table(report)
        self.assertIn("tabular_demo_phase_clean", table)
        self.assertIn("gov_obs_eval_gate", table)

    def test_main_json_serializable(self) -> None:
        report = self.runner.run_eval(dry_run=True)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertIn("routing_eval_cases_v1", serialized)


class TestRoutingEvalRunnerWithTempCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _RUNNER_PATH.is_file():
            raise unittest.SkipTest(f"missing runner: {_RUNNER_PATH}")
        cls.runner = _load_runner_module()

    def test_custom_cases_file_via_temp_yaml(self) -> None:
        try:
            import yaml  # type: ignore
        except ImportError:
            raise unittest.SkipTest("pyyaml not installed")

        payload = {
            "schema_version": "routing_eval_cases_v1",
            "catalog_ref": "routing/intake_routing_catalog_v1.yaml",
            "cases": [
                {
                    "id": "temp_gov_only",
                    "task_type": "gov.observability.eval",
                    "input_summary": "temp",
                    "expected_families": ["gov_registry"],
                    "expected_tool_ids": ["obs.eval.export"],
                    "input_context": {"policy_route_id": "wave_b.eval_report"},
                }
            ],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as fh:
            yaml.safe_dump(payload, fh, allow_unicode=True)
            temp_path = Path(fh.name)

        try:
            report = self.runner.run_eval(
                case_id="temp_gov_only",
                dry_run=True,
                cases_path=temp_path,
                catalog_path=_CATALOG_PATH,
            )
            self.assertTrue(report["ok"])
            self.assertEqual(report["cases_run"], 1)
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
