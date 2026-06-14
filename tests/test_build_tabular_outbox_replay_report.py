"""Unit tests for tabular outbox replay report generator (W3-TL-T4 follow-up)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPORT_CLI = _REPO_ROOT / "scripts" / "build_tabular_outbox_replay_report.py"
_FIXTURE_OUTBOX = _REPO_ROOT / "tests" / "fixtures" / "outbox"


def _load_report_module():
    spec = importlib.util.spec_from_file_location(
        "build_tabular_outbox_replay_report", _REPORT_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_tabular_outbox_replay_report"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestBuildTabularOutboxReplayReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _REPORT_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_REPORT_CLI}")
        cls.report = _load_report_module()

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.outbox_root = Path(self._tmpdir.name) / "outbox"
        shutil.copytree(_FIXTURE_OUTBOX, self.outbox_root)
        self.output_dir = Path(self._tmpdir.name) / "reports"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_collect_replay_report_data_demo_phase(self) -> None:
        data = self.report.collect_replay_report_data(
            case_ref="demo_phase",
            outbox_root_override=str(self.outbox_root),
        )
        self.assertTrue(data["ok"])
        self.assertEqual(data["schema_version"], "tabular_outbox_replay_report_v1")
        self.assertEqual(data["case_count"], 1)
        self.assertGreaterEqual(data["run_count"], 2)
        case_view = data["cases"][0]
        self.assertTrue(case_view["ok"])
        self.assertIn("validate.eligibility", case_view["last_by_tool_id"])

    def test_collect_all_cases(self) -> None:
        data = self.report.collect_replay_report_data(
            outbox_root_override=str(self.outbox_root),
        )
        self.assertTrue(data["ok"])
        self.assertGreaterEqual(data["case_count"], 2)
        refs = {c["case_ref"] for c in data["cases"]}
        self.assertIn("demo_phase", refs)
        self.assertIn("sampleco/2026-0001", refs)

    def test_runs_include_artifacts(self) -> None:
        data = self.report.collect_replay_report_data(
            case_ref="demo_phase",
            outbox_root_override=str(self.outbox_root),
        )
        runs = data["cases"][0]["runs"]
        self.assertGreaterEqual(len(runs), 1)
        with_artifacts = [r for r in runs if r.get("artifacts")]
        self.assertGreaterEqual(len(with_artifacts), 1)

    def test_render_markdown_contains_timeline(self) -> None:
        data = self.report.collect_replay_report_data(
            case_ref="demo_phase",
            outbox_root_override=str(self.outbox_root),
        )
        md = self.report.render_replay_markdown(data)
        self.assertIn("# Tabular Outbox Replay Report", md)
        self.assertIn("Timeline (chronological)", md)
        self.assertIn("validate.eligibility", md)
        self.assertIn("Read-only replay", md)

    def test_render_html_is_self_contained(self) -> None:
        data = self.report.collect_replay_report_data(
            case_ref="demo_phase",
            outbox_root_override=str(self.outbox_root),
        )
        doc = self.report.render_replay_html(data)
        self.assertIn("<!DOCTYPE html>", doc)
        self.assertIn("Timeline", doc)
        self.assertNotIn('src="http', doc)

    def test_build_writes_md_and_html(self) -> None:
        result = self.report.build_tabular_outbox_replay_report(
            case_ref="demo_phase",
            outbox_root_override=str(self.outbox_root),
            output_dir=self.output_dir,
            fmt="both",
            write_outputs=True,
        )
        self.assertTrue(result["ok"])
        paths = result["report_paths"]
        self.assertIn("markdown", paths)
        self.assertIn("html", paths)
        md_path = self.output_dir / Path(paths["markdown"]).name
        html_path = self.output_dir / Path(paths["html"]).name
        self.assertTrue(md_path.is_file())
        self.assertTrue(html_path.is_file())
        self.assertGreater(md_path.stat().st_size, 100)
        self.assertGreater(html_path.stat().st_size, 100)

    def test_load_events_jsonl(self) -> None:
        events_path = self.outbox_root / "events.jsonl"
        events_path.write_text(
            json.dumps(
                {
                    "case_ref": "demo_phase",
                    "run_id": "2026-06-10T01-52-00Z_eligibility",
                    "tool_id": "validate.eligibility",
                    "ok": True,
                    "exit_code": 2,
                    "started_at": "2026-06-10T01:52:00Z",
                    "finished_at": "2026-06-10T01:52:01Z",
                    "dry_run": False,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        events = self.report.load_events_jsonl(self.outbox_root)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tool_id"], "validate.eligibility")

    def test_cli_json_stdout(self) -> None:
        import io
        from contextlib import redirect_stdout

        captured = io.StringIO()
        with redirect_stdout(captured):
            code = self.report.main(
                [
                    "--case-ref",
                    "demo_phase",
                    "--outbox-root",
                    str(self.outbox_root),
                    "--stdout",
                    "--json",
                    "--format",
                    "md",
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(captured.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["case_ref"], "demo_phase")
        self.assertGreaterEqual(payload["summary"]["run_count"], 2)


if __name__ == "__main__":
    unittest.main()
