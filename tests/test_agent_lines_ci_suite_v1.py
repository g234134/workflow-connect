"""Unit tests for Agent lines CI suite v1 (W10-T1)."""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI_SUITE_CLI = _REPO_ROOT / "scripts" / "run_agent_lines_ci_suite.py"
_MVP_REGRESSION_CLI = _REPO_ROOT / "scripts" / "run_mvp_mainline_regression.py"

_FORBIDDEN_IMPORT_PREFIXES = (
    "scripts.run_mvp_mainline_regression",
    "scripts.run_case_e2e_validation",
    "scripts.new_cleaning_case",
    "app.local_ui",
    "tools.tabular_tool_executor",
    "core.routing_policy_loader",
)

_REQUIRED_CI_SUMMARY_KEYS = (
    "schema_version",
    "suite_id",
    "timestamp",
    "scope",
    "scopes_run",
    "ok",
    "tabular",
    "non_tabular",
    "ci_summary_path",
    "message",
)


def _load_ci_suite_module():
    spec = importlib.util.spec_from_file_location("run_agent_lines_ci_suite", _CI_SUITE_CLI)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_lines_ci_suite"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestAgentLinesCiSuiteV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _CI_SUITE_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_CI_SUITE_CLI}")
        cls.suite = _load_ci_suite_module()

    def test_module_does_not_import_forbidden_modules(self) -> None:
        source = _CI_SUITE_CLI.read_text(encoding="utf-8")
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

    def test_does_not_modify_mainline_regression_script(self) -> None:
        self.assertTrue(_MVP_REGRESSION_CLI.is_file())
        mvp_source = _MVP_REGRESSION_CLI.read_text(encoding="utf-8")
        self.assertIn("test_mvp_mainline.py", mvp_source)
        self.assertNotIn("run_agent_lines_ci_suite", mvp_source)

    def test_scope_tabular_only(self) -> None:
        ts = "20260610T200000Z"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tabular_outbox = root / "tabular_outbox"
            ci_outbox = root / "agent_ci"
            result = self.suite.run_agent_lines_ci_suite(
                scope="tabular",
                tabular_outbox_root=str(tabular_outbox),
                ci_outbox_root=str(ci_outbox),
                write_non_tabular_outbox=False,
                timestamp=ts,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["scope"], "tabular")
            self.assertEqual(result["scopes_run"], ["tabular"])
            self.assertIsNotNone(result["tabular"])
            self.assertIsNone(result["non_tabular"])
            tabular = result["tabular"]
            self.assertEqual(tabular["run_mode"], "run-all-allowed")
            self.assertEqual(tabular["summary"]["total"], 2)
            for case in tabular["cases"]:
                self.assertIn("fixture_maturity", case)
                self.assertEqual(case["fixture_maturity"], "stable")
            by_maturity = tabular["summary"]["by_fixture_maturity"]
            self.assertEqual(by_maturity["stable"]["total"], 2)
            self.assertEqual(by_maturity["stable"]["passed"], 2)
            summary_file = ci_outbox / f"{ts}_ci_summary.json"
            self.assertTrue(summary_file.is_file())
            payload = json.loads(summary_file.read_text(encoding="utf-8"))
            for key in _REQUIRED_CI_SUMMARY_KEYS:
                self.assertIn(key, payload)
            self.assertEqual(payload["schema_version"], "agent_lines_ci_suite_v1")

    def test_scope_non_tabular_uses_real_fixtures_by_default(self) -> None:
        """Default non-tabular CI scope uses W9-T5/T6 real fixtures (NT-A/NT-B)."""
        ts = "20260610T200100Z"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nt_outbox = root / "nt_outbox"
            ci_outbox = root / "agent_ci"
            result = self.suite.run_agent_lines_ci_suite(
                scope="non_tabular",
                non_tabular_outbox_root=str(nt_outbox),
                ci_outbox_root=str(ci_outbox),
                timestamp=ts,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["scope"], "non_tabular")
            self.assertEqual(result["scopes_run"], ["non_tabular"])
            self.assertIsNone(result["tabular"])
            self.assertIsNotNone(result["non_tabular"])
            non_tabular = result["non_tabular"]
            # Verify real fixtures are used (W9-T5/T6)
            self.assertEqual(non_tabular.get("fixture_source"), "real")
            self.assertEqual(non_tabular["summary"]["total"], 2)
            fixture_ids = {item["fixture_id"] for item in non_tabular["fixtures"]}
            self.assertEqual(fixture_ids, {"NT-A", "NT-B"})
            # Verify real fixture paths (cases/docu-corp, cases/log-analytics-co)
            for item in non_tabular["fixtures"]:
                self.assertTrue(item["ok"])
                self.assertEqual(item["final_status"], "preview_ready")
                case_dir = item.get("case_dir", "")
                self.assertTrue(
                    "docu-corp/2026-0001" in case_dir or "log-analytics-co/2026-0001" in case_dir,
                    f"Expected real fixture path in {case_dir}"
                )
            summary_file = ci_outbox / f"{ts}_ci_summary.json"
            self.assertTrue(summary_file.is_file())
            self.assertTrue(str(result["ci_summary_path"]).endswith(f"{ts}_ci_summary.json"))

    def test_scope_non_tabular_stub_fallback_via_env(self) -> None:
        """AGENT_LINES_CI_USE_STUB_FIXTURES=1 uses stub fixtures."""
        import os
        ts = "20260610T200105Z"
        # Set env var to use stub
        os.environ["AGENT_LINES_CI_USE_STUB_FIXTURES"] = "1"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                nt_outbox = root / "nt_outbox"
                ci_outbox = root / "agent_ci"
                result = self.suite.run_agent_lines_ci_suite(
                    scope="non_tabular",
                    non_tabular_outbox_root=str(nt_outbox),
                    ci_outbox_root=str(ci_outbox),
                    timestamp=ts,
                )
                self.assertTrue(result["ok"])
                non_tabular = result["non_tabular"]
                # Verify stub fixtures are used
                self.assertEqual(non_tabular.get("fixture_source"), "stub")
                self.assertEqual(non_tabular["summary"]["total"], 2)
                fixture_ids = {item["fixture_id"] for item in non_tabular["fixtures"]}
                self.assertEqual(fixture_ids, {"NT-A-stub", "NT-B-stub"})
                # Verify stub paths
                for item in non_tabular["fixtures"]:
                    case_dir = item.get("case_dir", "")
                    self.assertTrue(
                        "_experiment_samples/nt_" in case_dir,
                        f"Expected stub path in {case_dir}"
                    )
        finally:
            # Cleanup env
            if "AGENT_LINES_CI_USE_STUB_FIXTURES" in os.environ:
                del os.environ["AGENT_LINES_CI_USE_STUB_FIXTURES"]
            # Reload to restore default behavior
            import importlib
            spec = importlib.util.spec_from_file_location("run_agent_lines_ci_suite", _CI_SUITE_CLI)
            assert spec and spec.loader
            self.suite = importlib.util.module_from_spec(spec)
            sys.modules["run_agent_lines_ci_suite"] = self.suite
            spec.loader.exec_module(self.suite)

    def test_scope_all_merged_summary(self) -> None:
        ts = "20260610T200200Z"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tabular_outbox = root / "tabular_outbox"
            nt_outbox = root / "nt_outbox"
            ci_outbox = root / "agent_ci"
            result = self.suite.run_agent_lines_ci_suite(
                scope="all",
                tabular_outbox_root=str(tabular_outbox),
                non_tabular_outbox_root=str(nt_outbox),
                ci_outbox_root=str(ci_outbox),
                timestamp=ts,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["scopes_run"], ["tabular", "non_tabular"])
            self.assertIsNotNone(result["tabular"])
            self.assertIsNotNone(result["non_tabular"])
            # Verify non-tabular uses real fixtures by default
            self.assertEqual(result["non_tabular"].get("fixture_source"), "real")
            summary_file = ci_outbox / f"{ts}_ci_summary.json"
            self.assertTrue(summary_file.is_file())
            payload = json.loads(summary_file.read_text(encoding="utf-8"))
            self.assertTrue(payload["tabular"]["ok"])
            self.assertTrue(payload["non_tabular"]["ok"])
            self.assertIn(f"{ts}_ci_summary.json", payload["ci_summary_path"])
            self.assertEqual(payload["schema_version"], "agent_lines_ci_suite_v1")

    def test_ci_summary_outbox_path_helper(self) -> None:
        outbox = Path("/tmp/agent_ci")
        path = self.suite.ci_summary_artifact_path(outbox_root=outbox, timestamp="20260610T120000Z")
        self.assertEqual(path.name, "20260610T120000Z_ci_summary.json")
        self.assertEqual(path.parent, outbox)

    def test_text_summary_includes_fixture_maturity(self) -> None:
        ts = "20260610T200300Z"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.suite.run_agent_lines_ci_suite(
                scope="tabular",
                tabular_outbox_root=str(root / "tabular"),
                ci_outbox_root=str(root / "ci"),
                write_ci_summary=False,
                timestamp=ts,
            )
            text = self.suite.format_ci_suite_summary_text(result)
            self.assertIn("[stable]", text)
            self.assertIn("by_fixture_maturity:", text)

    def test_resolve_fixture_maturity_fallback_for_legacy_case(self) -> None:
        legacy_case = {
            "case_ref": "additional_demo",
            "ok": True,
            "mode": "run",
        }
        maturity = self.suite.resolve_tabular_case_fixture_maturity(legacy_case)
        self.assertEqual(maturity, "controlled_experimental")

    def test_cli_scope_all_json_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cmd = [
                sys.executable,
                str(_CI_SUITE_CLI),
                "--scope",
                "all",
                "--format",
                "json",
                "--tabular-outbox-root",
                str(root / "tabular"),
                "--non-tabular-outbox-root",
                str(root / "nt"),
                "--ci-outbox-root",
                str(root / "ci"),
            ]
            proc = __import__("subprocess").run(
                cmd,
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["scope"], "all")
            self.assertIn("ci_summary_path", payload)


if __name__ == "__main__":
    unittest.main()
