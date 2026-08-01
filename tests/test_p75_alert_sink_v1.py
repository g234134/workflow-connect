"""Unit tests for P7.5 local alert sink (P75-G6)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from delivery.p75_alert_sink_v1 import (
    DOC_REL,
    SCHEMA_VERSION,
    alerts_from_probe_result,
    clear_stub_inbox,
    emit_alerts,
    stub_inbox_snapshot,
)
from scripts.run_intake_slo_alert_probe_v1 import evaluate_slo_probe

_REPO_ROOT = Path(__file__).resolve().parents[1]


class _StubHandler(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        try:
            _StubHandler.received.append(json.loads(body.decode("utf-8")))
        except json.JSONDecodeError:
            _StubHandler.received.append({"raw": body.decode("utf-8", errors="replace")})
        self.send_response(202)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class TestP75AlertSinkV1(unittest.TestCase):
    def test_file_sink_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sink = Path(tmp) / "events.jsonl"
            result = emit_alerts(
                [{"level": "warn", "code": "latency_p95_warn", "detail": "p95=2500"}],
                mode="file",
                sink_path_override=str(sink),
                repo_root=_REPO_ROOT,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["schema_version"], SCHEMA_VERSION)
            self.assertEqual(result["emitted"], 1)
            self.assertEqual(result.get("doc"), DOC_REL)
            self.assertTrue(sink.is_file())
            row = json.loads(sink.read_text(encoding="utf-8").strip().splitlines()[-1])
            self.assertEqual(row["schema_version"], SCHEMA_VERSION)
            self.assertEqual(row["severity"], "warn")
            self.assertEqual(row["code"], "latency_p95_warn")
            self.assertTrue(row["sink"]["delivered"])
            self.assertEqual(row["sink"]["mode"], "file")

    def test_stub_http_inprocess(self) -> None:
        clear_stub_inbox()
        result = emit_alerts(
            [{"level": "critical", "code": "error_rate_critical", "detail": "0.9"}],
            mode="stub_http",
            repo_root=_REPO_ROOT,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["sink_mode"], "stub_http")
        inbox = stub_inbox_snapshot()
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0]["severity"], "critical")
        self.assertEqual(inbox[0]["sink"]["http_status"], 202)

    def test_stub_http_force_fail(self) -> None:
        result = emit_alerts(
            [{"level": "warn", "code": "x", "detail": "y"}],
            mode="stub_http",
            force_fail=True,
            repo_root=_REPO_ROOT,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["emitted"], 1)
        self.assertFalse(result["events"][0]["sink"]["delivered"])

    def test_stub_http_loopback(self) -> None:
        _StubHandler.received = []
        server = HTTPServer(("127.0.0.1", 0), _StubHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{port}/alerts"
            result = emit_alerts(
                [{"level": "warn", "code": "loopback", "detail": "ok"}],
                mode="stub_http",
                stub_url=url,
                repo_root=_REPO_ROOT,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(len(_StubHandler.received), 1)
            self.assertEqual(_StubHandler.received[0]["code"], "loopback")
        finally:
            server.shutdown()
            server.server_close()

    def test_alerts_from_probe_and_emit(self) -> None:
        fixture = {
            "samples": [
                {"latency_ms": 6000, "ok": True},
                {"latency_ms": 6100, "ok": True},
            ]
        }
        probe = evaluate_slo_probe(fixture, dry_run=True, emit_alert=True)
        self.assertFalse(probe["ok"])
        alerts = alerts_from_probe_result(probe)
        self.assertGreaterEqual(len(alerts), 1)
        with tempfile.TemporaryDirectory() as tmp:
            sink = Path(tmp) / "from_probe.jsonl"
            result = emit_alerts(
                alerts,
                mode="file",
                probe_snapshot=probe.get("slo"),
                sink_path_override=str(sink),
                repo_root=_REPO_ROOT,
            )
            self.assertTrue(result["ok"])
            self.assertGreaterEqual(result["emitted"], 1)
            row = json.loads(sink.read_text(encoding="utf-8").strip().splitlines()[0])
            self.assertIn("probe_snapshot", row)

    def test_empty_alerts_ok(self) -> None:
        result = emit_alerts([], mode="file", repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"])
        self.assertEqual(result["emitted"], 0)

    def test_cli_from_probe_json(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "run_p75_alert_sink_v1.py"),
                "--from-probe",
                "--mode",
                "file",
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
        self.assertIn("emitted", payload)
        # default fixture is healthy → no alerts
        self.assertEqual(payload["emitted"], 0)

    def test_cli_alert_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sink = Path(tmp) / "cli.jsonl"
            alert_json = json.dumps(
                [{"level": "warn", "code": "cli_demo", "detail": "from-cli"}]
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_REPO_ROOT / "scripts" / "run_p75_alert_sink_v1.py"),
                    "--alert-json",
                    alert_json,
                    "--mode",
                    "file",
                    "--sink-path",
                    str(sink),
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
            self.assertEqual(payload["emitted"], 1)
            self.assertTrue(sink.is_file())


if __name__ == "__main__":
    unittest.main()
