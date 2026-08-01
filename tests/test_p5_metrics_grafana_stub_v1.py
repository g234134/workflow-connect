"""Unit tests for P5 local Grafana/JSON对照 stub."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from observability.p5_metrics_grafana_stub_v1 import (
    DOC_REL,
    SCHEMA_VERSION,
    build_grafana_stub,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


class TestP5MetricsGrafanaStubV1(unittest.TestCase):
    def test_build_stub_shape(self) -> None:
        result = build_grafana_stub(case_ref="demo_phase", repo_root=_REPO_ROOT)
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertEqual(result["mode"], "local_stub")
        self.assertEqual(result["doc"], DOC_REL)
        self.assertIn("ok", result)
        self.assertIn("health", result)
        self.assertIn("ok", result["health"])
        self.assertEqual(result["health"]["source"], "toolchain_health_v1")
        self.assertIn("scrape_ok", result["metrics"])
        self.assertEqual(result["metrics"]["source"], "std_case_metrics_v1")
        budget = result["alert_budget_summary"]
        self.assertIn(budget["source"], ("narrative_stub", "p75_alert_sink_scan"))
        self.assertIsInstance(budget["warn_count"], int)
        self.assertIsInstance(budget["critical_count"], int)
        self.assertIsInstance(budget["total_events"], int)
        self.assertIn("≠ Grafana deployed", result["non_claims"])
        self.assertIsNone(result.get("artifact_path"))

    def test_alert_sink_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sink = Path(tmp) / "events.jsonl"
            rows = [
                {"severity": "warn", "code": "a"},
                {"severity": "critical", "code": "b"},
                {"severity": "warn", "code": "c"},
            ]
            sink.write_text(
                "\n".join(json.dumps(r) for r in rows) + "\n",
                encoding="utf-8",
            )
            result = build_grafana_stub(
                case_ref="demo_phase",
                repo_root=_REPO_ROOT,
                alert_sink_override=str(sink),
            )
            budget = result["alert_budget_summary"]
            self.assertEqual(budget["source"], "p75_alert_sink_scan")
            self.assertEqual(budget["warn_count"], 2)
            self.assertEqual(budget["critical_count"], 1)
            self.assertEqual(budget["total_events"], 3)

    def test_write_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stub.json"
            result = build_grafana_stub(
                case_ref="demo_phase",
                repo_root=_REPO_ROOT,
                write_artifact=True,
                artifact_path_override=str(out),
            )
            self.assertTrue(out.is_file())
            loaded = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema_version"], SCHEMA_VERSION)
            self.assertIsNotNone(result.get("artifact_path"))
            self.assertTrue(out.exists())

    def test_health_failure_failsoft(self) -> None:
        with mock.patch(
            "observability.p5_metrics_grafana_stub_v1._build_health_block",
            return_value={
                "ok": False,
                "source": "toolchain_health_v1",
                "sections_ok": None,
                "aggregated_health_score": None,
                "gate_class": None,
                "message": "forced fail",
            },
        ):
            result = build_grafana_stub(case_ref="demo_phase", repo_root=_REPO_ROOT)
        self.assertFalse(result["ok"])
        self.assertFalse(result["health"]["ok"])
        self.assertIn("message", result)

    def test_cli_json(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "run_p5_metrics_grafana_stub_v1.py"),
                "--format",
                "json",
                "--case-ref",
                "demo_phase",
            ],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn(proc.returncode, (0, 1), msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertIn("health", payload)
        self.assertIn("metrics", payload)


if __name__ == "__main__":
    unittest.main()
