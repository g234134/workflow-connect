"""Unit tests for Intake Gate SLO / alert probe (P75-G5)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.run_intake_slo_alert_probe_v1 import (
    DOC_REL,
    SCHEMA_VERSION,
    evaluate_slo_probe,
    main,
    run_intake_slo_alert_probe,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


class TestIntakeSloAlertProbeV1(unittest.TestCase):
    def test_default_fixture_healthy(self) -> None:
        result = run_intake_slo_alert_probe(dry_run=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertEqual(result["probe_mode"], "dry_run")
        self.assertEqual(result.get("doc"), DOC_REL)
        self.assertIn("slo", result)
        self.assertGreaterEqual(result["slo"]["sample_count"], 1)
        self.assertEqual(result["alerts"], [])
        self.assertFalse(result["would_emit"])

    def test_latency_warn_alert(self) -> None:
        fixture = {
            "samples": [
                {"latency_ms": 2500, "ok": True},
                {"latency_ms": 2600, "ok": True},
            ]
        }
        result = evaluate_slo_probe(fixture, dry_run=True)
        self.assertTrue(result["ok"])  # warn only
        codes = [a["code"] for a in result["alerts"]]
        self.assertIn("latency_p95_warn", codes)

    def test_error_rate_critical(self) -> None:
        fixture = {
            "samples": [
                {"latency_ms": 10, "ok": False},
                {"latency_ms": 10, "ok": False},
                {"latency_ms": 10, "ok": True},
            ]
        }
        result = evaluate_slo_probe(fixture, dry_run=True, emit_alert=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any(a["level"] == "critical" for a in result["alerts"]))
        self.assertTrue(result["would_emit"])

    def test_emit_does_not_write_external_sink(self) -> None:
        probe_marker = _REPO_ROOT / "scripts" / ".slo_alert_probe_emit_marker"
        if probe_marker.exists():
            probe_marker.unlink()
        result = run_intake_slo_alert_probe(dry_run=True, emit_alert=True)
        self.assertTrue(result["ok"])
        self.assertFalse(probe_marker.exists())

    def test_cli_json(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "run_intake_slo_alert_probe_v1.py"),
                "--format",
                "json",
            ],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertIn("slo", payload)

    def test_main_text_exit(self) -> None:
        code = main(["--format", "text"])
        self.assertEqual(code, 0)

    def test_missing_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            result = run_intake_slo_alert_probe(fixture_path=missing)
            self.assertFalse(result["ok"])
            self.assertEqual(result["probe_mode"], "error")


if __name__ == "__main__":
    unittest.main()
