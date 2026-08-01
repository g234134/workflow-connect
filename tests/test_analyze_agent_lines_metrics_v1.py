"""Unit tests for offline agent-lines metrics extractor (W10-T2)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_METRICS_CLI = _REPO_ROOT / "scripts" / "analyze_agent_lines_metrics.py"


def _load_metrics_module():
    spec = importlib.util.spec_from_file_location(
        "analyze_agent_lines_metrics", _METRICS_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["analyze_agent_lines_metrics"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_regression_artifact(
    dest: Path,
    *,
    case_ref: str,
    ok: bool,
    cp_a: str,
    cp_b: str,
    cp_b_would_trigger: bool = False,
    timestamp: str = "20260610T120000Z",
    written_at: str = "2026-06-10T12:00:05Z",
    fixture_maturity: str | None = None,
) -> None:
    payload = {
        "schema_version": "agent_experiment_regression_v1",
        "written_at": written_at,
        "regression_meta": {
            "regression_id": "test-regression",
            "timestamp": timestamp,
            "run_mode": "preview",
        },
        "case_summary": {
            "case_ref": case_ref,
            "ok": ok,
            "final_status": "waiting_for_human" if ok else "blocked",
            "checkpoint_a_status": cp_a,
            "checkpoint_b_status": cp_b,
            "checkpoint_b_would_trigger": cp_b_would_trigger,
            **(
                {"fixture_maturity": fixture_maturity}
                if fixture_maturity is not None
                else {}
            ),
        },
        "experiment": {
            "ok": ok,
            "case_ref": case_ref,
            "checkpoint_a_status": {"would_trigger": cp_a == "would_pause"},
            "checkpoint_b_status": {"would_trigger": cp_b_would_trigger},
        },
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


class TestAnalyzeAgentLinesMetricsV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _METRICS_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_METRICS_CLI}")
        cls.metrics = _load_metrics_module()

    def test_checkpoint_helpers(self) -> None:
        cp_a_payload = {
            "case_summary": {"checkpoint_a_status": "would_pause"},
            "experiment": {"checkpoint_a_status": {"would_trigger": True}},
        }
        self.assertTrue(self.metrics.is_checkpoint_a_triggered(cp_a_payload))

        cp_b_payload = {
            "case_summary": {
                "checkpoint_b_status": "stopped_before_delivery",
                "checkpoint_b_would_trigger": False,
            }
        }
        self.assertTrue(self.metrics.is_checkpoint_b_triggered(cp_b_payload))

    def test_analyze_fake_outbox_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            regression_root = root / "outbox" / "agent_experiment_regression"
            _write_regression_artifact(
                regression_root / "20260610T120000Z_demo_phase.json",
                case_ref="demo_phase",
                ok=True,
                cp_a="would_pause",
                cp_b="planned",
            )
            _write_regression_artifact(
                regression_root / "20260610T120000Z_sampleco_2026-0001.json",
                case_ref="sampleco/2026-0001",
                ok=True,
                cp_a="auto_approved",
                cp_b="would_trigger",
                cp_b_would_trigger=True,
            )
            _write_regression_artifact(
                regression_root / "20260610T130000Z_sandbox_client.json",
                case_ref="sandbox_client",
                ok=False,
                cp_a="would_pause",
                cp_b="planned",
            )

            nt_root = root / "outbox" / "non_tabular_experiment"
            nt_root.mkdir(parents=True)
            with (nt_root / "20260610T140000Z_nt_docu_stub.json").open(
                "w", encoding="utf-8"
            ) as fh:
                json.dump(
                    {
                        "schema_version": "non_tabular_experiment_preview_v1",
                        "case_ref": "cases_experiment_samples_nt_docu_stub",
                        "final_status": "preview_ready",
                    },
                    fh,
                )
                fh.write("\n")

            summary = self.metrics.analyze_agent_lines_metrics(
                repo_root=root,
                scan_roots=[regression_root, root / "outbox" / "agent_ci", nt_root],
                write_outputs=True,
                output_dir=root / "outbox" / "agent_metrics",
            )

            agg = summary["aggregate"]
            self.assertEqual(agg["total_runs"], 4)
            self.assertEqual(agg["successful_runs"], 3)
            self.assertEqual(agg["failed_runs"], 1)
            self.assertAlmostEqual(agg["error_rate"], 0.25)
            self.assertEqual(agg["checkpoint_a_triggered"], 3)
            self.assertEqual(agg["checkpoint_b_triggered"], 1)

            demo = summary["by_case_ref"]["demo_phase"]
            self.assertEqual(demo["total_runs"], 1)
            self.assertEqual(demo["checkpoint_a_triggered"], 1)
            self.assertEqual(demo["checkpoint_b_triggered"], 0)

            sampleco = summary["by_case_ref"]["sampleco/2026-0001"]
            self.assertEqual(sampleco["checkpoint_a_triggered"], 1)
            self.assertEqual(sampleco["checkpoint_b_triggered"], 1)

            self.assertEqual(summary["by_source"]["agent_experiment_regression"]["total_runs"], 3)
            self.assertEqual(summary["by_source"]["non_tabular_experiment"]["total_runs"], 1)

            json_path = root / "outbox" / "agent_metrics" / "metrics_summary.json"
            csv_path = root / "outbox" / "agent_metrics" / "metrics_summary.csv"
            self.assertTrue(json_path.is_file())
            self.assertTrue(csv_path.is_file())

            with json_path.open("r", encoding="utf-8") as fh:
                written = json.load(fh)
            self.assertEqual(written["schema_version"], "agent_lines_metrics_v1")
            self.assertEqual(len(written["runs"]), 4)

            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertIn("section,source,case_ref", csv_text)
            self.assertIn("aggregate", csv_text)
            self.assertIn("demo_phase", csv_text)

    def test_fixture_maturity_grouping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            regression_root = root / "outbox" / "agent_experiment_regression"
            _write_regression_artifact(
                regression_root / "20260610T120000Z_demo_phase.json",
                case_ref="demo_phase",
                ok=True,
                cp_a="would_pause",
                cp_b="planned",
                fixture_maturity="stable",
            )
            _write_regression_artifact(
                regression_root / "20260610T120000Z_additional_demo.json",
                case_ref="additional_demo",
                ok=True,
                cp_a="auto_approved",
                cp_b="would_trigger",
                cp_b_would_trigger=True,
                fixture_maturity="controlled_experimental",
            )
            _write_regression_artifact(
                regression_root / "20260610T130000Z_legacy.json",
                case_ref="demo_phase",
                ok=True,
                cp_a="auto_approved",
                cp_b="planned",
            )

            summary = self.metrics.analyze_agent_lines_metrics(
                repo_root=root,
                scan_roots=[regression_root],
                write_outputs=False,
            )

            by_maturity = summary["by_fixture_maturity"]
            self.assertEqual(by_maturity["stable"]["total_runs"], 2)
            self.assertEqual(
                by_maturity["controlled_experimental"]["total_runs"], 1
            )
            self.assertEqual(
                by_maturity["controlled_experimental"]["checkpoint_b_triggered"], 1
            )

            maturity_by_case = {
                run["case_ref"]: run["fixture_maturity"] for run in summary["runs"]
            }
            self.assertEqual(maturity_by_case["demo_phase"], "stable")
            self.assertEqual(
                maturity_by_case["additional_demo"], "controlled_experimental"
            )

            text = self.metrics.format_metrics_summary_text(summary)
            self.assertIn("by_fixture_maturity (tabular tiers):", text)
            self.assertIn("stable:", text)
            self.assertIn("controlled_experimental:", text)

    def test_legacy_artifact_without_fixture_maturity_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            regression_root = root / "outbox" / "agent_experiment_regression"
            _write_regression_artifact(
                regression_root / "20260610T120000Z_demo_phase.json",
                case_ref="demo_phase",
                ok=True,
                cp_a="would_pause",
                cp_b="planned",
            )

            summary = self.metrics.analyze_agent_lines_metrics(
                repo_root=root,
                scan_roots=[regression_root],
                write_outputs=False,
            )

            self.assertEqual(summary["aggregate"]["total_runs"], 1)
            self.assertIn("by_fixture_maturity", summary)
            self.assertEqual(
                summary["by_fixture_maturity"]["stable"]["total_runs"], 1
            )
            self.assertEqual(summary["runs"][0]["fixture_maturity"], "stable")

    def test_non_tabular_runs_omit_fixture_maturity_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nt_root = root / "outbox" / "non_tabular_experiment"
            nt_root.mkdir(parents=True)
            with (nt_root / "20260610T140000Z_nt.json").open(
                "w", encoding="utf-8"
            ) as fh:
                json.dump(
                    {
                        "schema_version": "non_tabular_experiment_preview_v1",
                        "case_ref": "cases_experiment_samples_nt_docu_stub",
                        "final_status": "preview_ready",
                    },
                    fh,
                )
                fh.write("\n")

            summary = self.metrics.analyze_agent_lines_metrics(
                repo_root=root,
                scan_roots=[nt_root],
                write_outputs=False,
            )

            self.assertEqual(summary["aggregate"]["total_runs"], 1)
            self.assertEqual(summary["by_fixture_maturity"], {})
            self.assertIsNone(summary["runs"][0]["fixture_maturity"])

    def test_duration_inference(self) -> None:
        payload = {
            "written_at": "2026-06-10T12:00:10Z",
            "regression_meta": {"timestamp": "20260610T120000Z"},
        }
        seconds = self.metrics.infer_duration_seconds(
            payload, Path("20260610T120000Z_demo_phase.json")
        )
        self.assertEqual(seconds, 10.0)


if __name__ == "__main__":
    unittest.main()
