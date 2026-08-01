"""Unit tests for P75-G7 Intake Gate HTTP stub."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from routing.intake_gate_http_stub_v1 import (
    GATE_PATH,
    SCHEMA_VERSION,
    create_server,
    handle_gate_request,
)


class TestIntakeGateHttpStubHandle(unittest.TestCase):
    def test_preview_once_ok(self) -> None:
        status, payload = handle_gate_request(
            {
                "task_type": "tabular.cleaning.mvp",
                "case_dir": "cases/demo_phase",
                "mode": "preview",
            }
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertTrue(payload["http"]["stub"])
        self.assertEqual(payload["http"]["path"], GATE_PATH)
        gate = payload["gate"]
        self.assertIsInstance(gate, dict)
        self.assertTrue(gate.get("ok"))
        self.assertIn(gate.get("decision"), ("accept", "review_needed", "reject"))
        self.assertIsNone(gate.get("outbox_record_path"))
        self.assertIsNone(payload.get("notification"))

    def test_missing_task_type_400(self) -> None:
        status, payload = handle_gate_request({"case_dir": "cases/demo_phase"})
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error_code"], "missing_task_type")

    def test_invalid_mode_400(self) -> None:
        status, payload = handle_gate_request(
            {
                "task_type": "tabular.cleaning.mvp",
                "case_dir": "cases/demo_phase",
                "mode": "shadow",
            }
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error_code"], "invalid_mode")

    def test_run_writes_outbox_under_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            status, payload = handle_gate_request(
                {
                    "task_type": "tabular.cleaning.mvp",
                    "case_dir": "cases/demo_phase",
                    "mode": "run",
                    "outbox_root": str(outbox),
                }
            )
            self.assertEqual(status, 200)
            self.assertTrue(payload["ok"])
            gate = payload["gate"]
            rel = gate.get("outbox_record_path")
            self.assertIsNotNone(rel)
            # Writer returns repo-style relative path; bytes land under override root.
            written = list(outbox.glob("**/intake_gate_decision_*.json"))
            self.assertEqual(len(written), 1)
            self.assertTrue(written[0].is_file())
            self.assertIn("demo_phase", str(rel).replace("\\", "/"))


class TestIntakeGateHttpStubServer(unittest.TestCase):
    def setUp(self) -> None:
        self.server = create_server("127.0.0.1", 0)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_health(self) -> None:
        with urlopen(f"http://127.0.0.1:{self.port}/health", timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(body["ok"])
        self.assertTrue(body["stub"])

    def test_post_gate_preview(self) -> None:
        req = Request(
            f"http://127.0.0.1:{self.port}{GATE_PATH}",
            data=json.dumps(
                {
                    "task_type": "tabular.cleaning.mvp",
                    "case_dir": "cases/demo_phase",
                    "mode": "preview",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["gate"]["schema_version"], "intake_gate_result_v1")

    def test_post_missing_fields_400(self) -> None:
        req = Request(
            f"http://127.0.0.1:{self.port}{GATE_PATH}",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)

    def test_non_loopback_host_rejected(self) -> None:
        with self.assertRaises(ValueError):
            create_server("0.0.0.0", 0)


if __name__ == "__main__":
    unittest.main()
