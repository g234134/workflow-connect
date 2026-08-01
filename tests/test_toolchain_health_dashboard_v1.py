"""Unit tests for toolchain health dashboard v1 (WB-T4)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DASHBOARD_CLI = _REPO_ROOT / "scripts" / "run_toolchain_health_dashboard.py"


def _load_dashboard_module():
    spec = importlib.util.spec_from_file_location(
        "run_toolchain_health_dashboard", _DASHBOARD_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_toolchain_health_dashboard"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_ci_summary(dest: Path, *, ok: bool = True) -> None:
    payload = {
        "schema_version": "agent_lines_ci_suite_v1",
        "written_at": "2026-06-10T12:00:00Z",
        "suite_id": "test-suite",
        "scope": "all",
        "scopes_run": ["tabular", "non_tabular"],
        "ok": ok,
        "tabular": {
            "ok": ok,
            "summary": {
                "passed": 2,
                "total": 2,
                "by_fixture_maturity": {
                    "stable": {"total": 2, "passed": 2, "failed": 0},
                },
            },
        },
        "non_tabular": {"ok": ok, "summary": {"passed": 2, "total": 2}},
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_metrics_summary(dest: Path, *, runs: int = 3) -> None:
    runs_list = []
    for idx in range(runs):
        runs_list.append(
            {
                "ok": True,
                "source": "agent_experiment_regression",
                "case_ref": "demo_phase",
                "fixture_maturity": "stable",
                "written_at": f"2026-06-0{idx + 1}T12:00:00Z",
            }
        )
    payload = {
        "ok": True,
        "schema_version": "agent_lines_metrics_v1",
        "generated_at": "2026-06-10T12:00:00Z",
        "aggregate": {
            "total_runs": runs,
            "successful_runs": runs,
            "failed_runs": 0,
            "error_rate": 0.0,
            "checkpoint_a_trigger_rate": 0.1,
            "checkpoint_b_trigger_rate": 0.0,
        },
        "by_fixture_maturity": {
            "stable": {
                "total_runs": runs,
                "error_rate": 0.0,
            }
        },
        "runs": runs_list,
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class TestToolchainHealthDashboardV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _DASHBOARD_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_DASHBOARD_CLI}")
        cls.dash = _load_dashboard_module()

    def test_schema_version_constant(self) -> None:
        self.assertEqual(self.dash._SCHEMA_VERSION, "toolchain_health_v1")

    def test_empty_outbox_degrades_not_false_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            for name in ("tabular_tool_catalog_v1.json", "non_tabular_tool_catalog_v1.json"):
                src = _REPO_ROOT / "tools" / name
                if src.is_file():
                    (root / "tools" / name).write_text(
                        src.read_text(encoding="utf-8"), encoding="utf-8"
                    )
            payload = self.dash.build_toolchain_health(repo_root=root, dry_run=True)
            self.assertEqual(payload["schema_version"], "toolchain_health_v1")
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["sections"]["agent_ci"]["status"], "degraded")
            self.assertEqual(payload["sections"]["metrics_summary"]["status"], "degraded")

    def test_populated_sections_minimum_example(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tabular_tool_catalog_v1.json", "non_tabular_tool_catalog_v1.json"):
                src = _REPO_ROOT / "tools" / name
                (root / "tools").mkdir(parents=True, exist_ok=True)
                (root / "tools" / name).write_text(
                    src.read_text(encoding="utf-8"), encoding="utf-8"
                )
            _write_ci_summary(root / "outbox" / "agent_ci" / "20260610T120000Z_ci_summary.json")
            _write_metrics_summary(root / "outbox" / "agent_metrics" / "metrics_summary.json")
            payload = self.dash.build_toolchain_health(repo_root=root, dry_run=True)
            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(payload["sections_populated"], 3)
            self.assertIn("agent_ci", payload["sections"])
            self.assertIn("catalog_health", payload["sections"])
            self.assertEqual(payload["gate_class"], "optional")
            self.assertFalse(payload["blocks_mainline"])

    def test_catalog_health_tool_counts(self) -> None:
        payload = self.dash.load_catalog_health_section(_REPO_ROOT)
        self.assertGreater(payload["tabular_tool_count"], 0)
        self.assertGreater(payload["non_tabular_tool_count"], 0)
        self.assertEqual(
            payload["total_tool_count"],
            payload["tabular_tool_count"] + payload["non_tabular_tool_count"],
        )
        self.assertIn("stale_revision", payload)

    def test_fixture_maturity_merge(self) -> None:
        metrics = {
            "by_fixture_maturity": {
                "stable": {"total_runs": 5, "error_rate": 0.1},
            }
        }
        agent_ci = {
            "by_fixture_maturity": {
                "stable": {"passed": 2, "total": 2},
                "experimental": {"passed": 0, "total": 1},
            },
        }
        merged = self.dash.merge_fixture_maturity_tiers(
            metrics_section=metrics,
            agent_ci_section=agent_ci,
        )
        self.assertTrue(merged["ok"])
        tiers = {row["tier"] for row in merged["tiers"]}
        self.assertIn("stable", tiers)
        self.assertIn("experimental", tiers)

    def test_wf_status_missing_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            section = self.dash.load_wf_status_summary_section(
                root,
                wf_status_path=root / "artifacts" / "wf" / "wf_status_summary.latest.json",
                include_wf_status=True,
            )
            self.assertFalse(section["ok"])
            self.assertEqual(section["status"], "degraded")

    def test_wf_status_skipped_when_not_requested(self) -> None:
        section = self.dash.load_wf_status_summary_section(
            _REPO_ROOT,
            wf_status_path=_REPO_ROOT / "artifacts" / "wf" / "missing.json",
            include_wf_status=False,
        )
        self.assertEqual(section["status"], "missing")

    def test_dry_run_does_not_invoke_ci_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tabular_tool_catalog_v1.json", "non_tabular_tool_catalog_v1.json"):
                src = _REPO_ROOT / "tools" / name
                (root / "tools").mkdir(parents=True, exist_ok=True)
                (root / "tools" / name).write_text(
                    src.read_text(encoding="utf-8"), encoding="utf-8"
                )
            with mock.patch.object(self.dash, "maybe_run_agent_ci_suite") as mocked:
                self.dash.main(
                    [
                        "--repo-root",
                        str(root),
                        "--dry-run",
                        "--format",
                        "json",
                        "--no-write",
                    ]
                )
                mocked.assert_not_called()

    def test_write_artifacts_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tabular_tool_catalog_v1.json", "non_tabular_tool_catalog_v1.json"):
                src = _REPO_ROOT / "tools" / name
                (root / "tools").mkdir(parents=True, exist_ok=True)
                (root / "tools" / name).write_text(
                    src.read_text(encoding="utf-8"), encoding="utf-8"
                )
            _write_ci_summary(root / "outbox" / "agent_ci" / "20260610T120000Z_ci_summary.json")
            _write_metrics_summary(root / "outbox" / "agent_metrics" / "metrics_summary.json")
            payload = self.dash.build_toolchain_health(repo_root=root, dry_run=True)
            out_dir = root / "artifacts" / "toolchain"
            paths = self.dash.write_toolchain_health_artifacts(
                payload, repo_root=root, output_dir=out_dir
            )
            self.assertTrue((root / paths["json"]).is_file())
            self.assertTrue((root / paths["markdown"]).is_file())
            md_text = (root / paths["markdown"]).read_text(encoding="utf-8")
            self.assertIn("Toolchain Health Dashboard", md_text)

    def test_cli_json_stdout_schema(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_DASHBOARD_CLI),
                "--format",
                "json",
                "--no-write",
                "--dry-run",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema_version"], "toolchain_health_v1")
        self.assertIn("sections", payload)
        self.assertIn("aggregated_health_score", payload)


class TestToolchainHealthDashboardTolerantParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _DASHBOARD_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_DASHBOARD_CLI}")
        cls.dash = _load_dashboard_module()

    def test_metrics_summary_tolerant_extra_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metrics_path = root / "outbox" / "agent_metrics" / "metrics_summary.json"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                json.dumps(
                    {
                        "schema_version": "agent_lines_metrics_v1",
                        "future_field": {"nested": True},
                        "aggregate": {"total_runs": 1, "successful_runs": 1, "failed_runs": 0},
                        "runs": [{"ok": True, "written_at": "2026-06-10T12:00:00Z"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            section = self.dash.load_metrics_summary_section(root, metrics_path=metrics_path)
            self.assertEqual(section["status"], "ok")
            self.assertEqual(section["runs_parsed"], 1)


if __name__ == "__main__":
    unittest.main()
