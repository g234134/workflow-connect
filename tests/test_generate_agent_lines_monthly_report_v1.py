"""Unit tests for offline agent-lines monthly report generator (W11-T3)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPORT_CLI = _REPO_ROOT / "scripts" / "generate_agent_lines_monthly_report.py"


def _load_report_module():
    spec = importlib.util.spec_from_file_location(
        "generate_agent_lines_monthly_report", _REPORT_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["generate_agent_lines_monthly_report"] = mod
    spec.loader.exec_module(mod)
    return mod


def _fake_metrics_summary() -> dict:
    return {
        "ok": True,
        "schema_version": "agent_lines_metrics_v1",
        "generated_at": "2026-06-10T18:00:00Z",
        "runs": [
            {
                "source": "agent_experiment_regression",
                "path": "outbox/agent_experiment_regression/20260605T100000Z_demo.json",
                "case_ref": "demo_phase",
                "fixture_maturity": "stable",
                "ok": True,
                "checkpoint_a_triggered": True,
                "checkpoint_b_triggered": False,
                "written_at": "2026-06-05T10:00:05Z",
            },
            {
                "source": "agent_experiment_regression",
                "path": "outbox/agent_experiment_regression/20260605T110000Z_sampleco.json",
                "case_ref": "sampleco/2026-0001",
                "fixture_maturity": "stable",
                "ok": True,
                "checkpoint_a_triggered": True,
                "checkpoint_b_triggered": True,
                "written_at": "2026-06-05T11:00:05Z",
            },
            {
                "source": "agent_experiment_regression",
                "path": "outbox/agent_experiment_regression/20260615T120000Z_fail.json",
                "case_ref": "sandbox_client",
                "fixture_maturity": "controlled_experimental",
                "ok": False,
                "checkpoint_a_triggered": True,
                "checkpoint_b_triggered": False,
                "written_at": "2026-06-15T12:00:05Z",
            },
            {
                "source": "non_tabular_experiment",
                "path": "outbox/non_tabular_experiment/20260620T140000Z_nt.json",
                "case_ref": "cases_experiment_samples_nt_docu_stub",
                "ok": True,
                "checkpoint_a_triggered": None,
                "checkpoint_b_triggered": None,
                "written_at": "2026-06-20T14:00:05Z",
            },
            {
                "source": "agent_ci",
                "path": "outbox/agent_ci/20260701T090000Z_ci.json",
                "case_ref": "demo_phase",
                "fixture_maturity": "stable",
                "ok": True,
                "checkpoint_a_triggered": False,
                "checkpoint_b_triggered": False,
                "written_at": "2026-07-01T09:00:05Z",
            },
            {
                "source": "agent_experiment_regression",
                "path": "outbox/agent_experiment_regression/no_ts.json",
                "case_ref": "orphan",
                "ok": True,
                "checkpoint_a_triggered": False,
                "checkpoint_b_triggered": False,
                "written_at": None,
            },
        ],
    }


class TestGenerateAgentLinesMonthlyReportV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _REPORT_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_REPORT_CLI}")
        cls.report = _load_report_module()

    def test_parse_written_at_month(self) -> None:
        self.assertEqual(
            self.report._parse_written_at_month("2026-06-10T12:00:05Z"),
            "2026-06",
        )
        self.assertIsNone(self.report._parse_written_at_month(None))
        self.assertIsNone(self.report._parse_written_at_month(""))

    def test_classify_line_type(self) -> None:
        self.assertEqual(
            self.report.classify_line_type("agent_experiment_regression"), "tabular"
        )
        self.assertEqual(self.report.classify_line_type("agent_ci"), "tabular")
        self.assertEqual(
            self.report.classify_line_type("non_tabular_experiment"), "non_tabular"
        )

    def test_aggregate_runs_by_month(self) -> None:
        by_month = self.report.aggregate_runs_by_month(
            _fake_metrics_summary()["runs"]
        )
        self.assertIn("2026-06", by_month)
        self.assertIn("2026-07", by_month)
        self.assertNotIn("orphan", by_month)

        june = by_month["2026-06"]
        self.assertEqual(june["overall"]["total_runs"], 4)
        self.assertEqual(june["tabular"]["total_runs"], 3)
        self.assertEqual(june["non_tabular"]["total_runs"], 1)
        self.assertEqual(june["overall"]["failed_runs"], 1)
        self.assertAlmostEqual(june["overall"]["error_rate"], 0.25)
        self.assertEqual(june["overall"]["checkpoint_a_triggered"], 3)
        self.assertEqual(june["overall"]["checkpoint_b_triggered"], 1)
        self.assertEqual(june["tabular"]["checkpoint_a_trigger_rate"], 1.0)
        self.assertAlmostEqual(june["tabular"]["checkpoint_b_trigger_rate"], 0.3333, places=4)
        self.assertEqual(june["non_tabular"]["non_tabular_preview_count"], 1)

        july = by_month["2026-07"]
        self.assertEqual(july["overall"]["total_runs"], 1)
        self.assertEqual(july["tabular"]["total_runs"], 1)

    def test_generate_writes_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metrics_path = root / "outbox" / "agent_metrics" / "metrics_summary.json"
            metrics_path.parent.mkdir(parents=True)
            with metrics_path.open("w", encoding="utf-8") as fh:
                json.dump(_fake_metrics_summary(), fh, indent=2)
                fh.write("\n")

            result = self.report.generate_agent_lines_monthly_report(
                metrics_summary=_fake_metrics_summary(),
                repo_root=root,
                write_outputs=True,
                output_dir=root / "outbox" / "agent_metrics",
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["months"], ["2026-06", "2026-07"])
            self.assertEqual(result["skipped_runs_without_timestamp"], 1)

            june_path = root / "outbox" / "agent_metrics" / "monthly_report_2026-06.md"
            july_path = root / "outbox" / "agent_metrics" / "monthly_report_2026-07.md"
            self.assertTrue(june_path.is_file())
            self.assertTrue(july_path.is_file())

            june_text = june_path.read_text(encoding="utf-8")
            self.assertIn("# Agent Lines Monthly Report — 2026-06", june_text)
            self.assertIn("| Total runs | 4 | 3 | 1 |", june_text)
            self.assertIn("| Non-tabular previews | 1 | — | 1 |", june_text)
            self.assertIn("no external monitoring", june_text)

    def test_month_filter(self) -> None:
        result = self.report.generate_agent_lines_monthly_report(
            metrics_summary=_fake_metrics_summary(),
            write_outputs=False,
            months_filter=["2026-06"],
        )
        self.assertEqual(result["months"], ["2026-06"])
        self.assertNotIn("2026-07", result["by_month"])

    def test_aggregate_tabular_by_fixture_maturity(self) -> None:
        by_maturity = self.report.aggregate_tabular_runs_by_fixture_maturity(
            _fake_metrics_summary()["runs"],
            month="2026-06",
        )
        self.assertEqual(by_maturity["stable"]["total_runs"], 2)
        self.assertEqual(by_maturity["controlled_experimental"]["total_runs"], 1)
        self.assertEqual(by_maturity["controlled_experimental"]["failed_runs"], 1)
        self.assertAlmostEqual(by_maturity["stable"]["checkpoint_b_trigger_rate"], 0.5)

    def test_monthly_report_includes_fixture_maturity_table(self) -> None:
        by_month = self.report.aggregate_runs_by_month(_fake_metrics_summary()["runs"])
        by_maturity = self.report.aggregate_tabular_runs_by_fixture_maturity(
            _fake_metrics_summary()["runs"],
            month="2026-06",
        )
        md = self.report.render_monthly_markdown(
            "2026-06",
            by_month["2026-06"],
            source_summary=_fake_metrics_summary(),
            by_fixture_maturity=by_maturity,
        )
        self.assertIn("## Tabular fixture maturity (tier rollup)", md)
        self.assertIn("| `stable` | 2 |", md)
        self.assertIn("| `controlled_experimental` | 1 |", md)

    def test_legacy_runs_without_fixture_maturity_roll_to_unknown(self) -> None:
        runs = [
            {
                "source": "agent_experiment_regression",
                "case_ref": "demo_phase",
                "ok": True,
                "checkpoint_a_triggered": True,
                "checkpoint_b_triggered": False,
                "written_at": "2026-06-05T10:00:05Z",
            }
        ]
        by_maturity = self.report.aggregate_tabular_runs_by_fixture_maturity(
            runs,
            month="2026-06",
        )
        self.assertEqual(by_maturity["unknown"]["total_runs"], 1)

    def test_render_markdown_cp_rates(self) -> None:
        by_month = self.report.aggregate_runs_by_month(
            _fake_metrics_summary()["runs"]
        )
        md = self.report.render_monthly_markdown(
            "2026-06",
            by_month["2026-06"],
            source_summary=_fake_metrics_summary(),
        )
        self.assertIn("CP-A trigger rate", md)
        self.assertIn("75.0%", md)


if __name__ == "__main__":
    unittest.main()
