"""Full-chain smoke: orchestrator → gateway emit → dispatch → webhook sandbox (WD-P7-T3).

Validates env-only gate (no --enable-notifications), outbox/jsonl writes,
dispatch registry webhook handler, and fail-open on webhook errors.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
_DEMO_PHASE = "cases/demo_phase"
_ADDITIONAL_DEMO = "cases/additional_demo"

_FULL_CHAIN_ENV_KEYS = (
    "GOV_NOTIFICATION_GATEWAY_ENABLED",
    "GOV_NOTIFICATION_DISPATCH_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
    "GOV_NOTIFICATION_WEBHOOK_URL",
)


def _load_cli_module():
    spec = importlib.util.spec_from_file_location(
        "run_agent_standard_case_experiment", _CLI_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_standard_case_experiment"] = mod
    spec.loader.exec_module(mod)
    return mod


def _snapshot_env(keys: tuple[str, ...]) -> Dict[str, Optional[str]]:
    return {key: os.environ.get(key) for key in keys}


def _restore_env(snapshot: Dict[str, Optional[str]]) -> None:
    for key, val in snapshot.items():
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val


def _find_notification_events(outbox: Path, event_type: str) -> list[dict]:
    events: list[dict] = []
    notifications_dir = outbox / "notifications"
    if not notifications_dir.exists():
        return events
    for event_file in notifications_dir.rglob("*.json"):
        try:
            data = json.loads(event_file.read_text(encoding="utf-8"))
            if data.get("event_type") == event_type:
                events.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return events


def _read_jsonl_events(outbox: Path) -> list[dict]:
    jsonl_path = outbox / "notification_events.jsonl"
    events: list[dict] = []
    if not jsonl_path.exists():
        return events
    try:
        with jsonl_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    except (json.JSONDecodeError, OSError):
        pass
    return events


class MockWebhookRequestHandler(BaseHTTPRequestHandler):
    """Records POST bodies for full-chain smoke assertions."""

    received_requests: List[Dict[str, Any]] = []

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        MockWebhookRequestHandler.received_requests.append(
            {
                "path": self.path,
                "headers": dict(self.headers),
                "body": body,
                "body_json": json.loads(body) if body else None,
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format: str, *args: Any) -> None:
        pass


class FailingMockWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error":"server error"}')

    def log_message(self, format: str, *args: Any) -> None:
        pass


class MockWebhookServer:
    def __init__(
        self,
        handler_class: type = MockWebhookRequestHandler,
        port: int = 0,
    ) -> None:
        self.handler_class = handler_class
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.url: str = ""

    def __enter__(self) -> "MockWebhookServer":
        MockWebhookRequestHandler.received_requests = []
        self.server = HTTPServer(("127.0.0.1", self.port), self.handler_class)
        self.port = self.server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/webhook"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=2)

    def get_requests(self) -> List[Dict[str, Any]]:
        return MockWebhookRequestHandler.received_requests.copy()


def _full_chain_env(webhook_url: str) -> Dict[str, str]:
    return {
        "GOV_NOTIFICATION_GATEWAY_ENABLED": "1",
        "GOV_NOTIFICATION_DISPATCH_ENABLED": "1",
        "GOV_NOTIFICATION_WEBHOOK_ENABLED": "1",
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST": "demo_*,additional_*",
        "GOV_NOTIFICATION_WEBHOOK_URL": webhook_url,
    }


class TestOrchestratorDispatchFullSmoke(unittest.TestCase):
    """WD-P7-T3: orchestrator → emit → dispatch → webhook sandbox."""

    @classmethod
    def setUpClass(cls) -> None:
        if not _CLI_PATH.is_file():
            raise unittest.SkipTest(f"missing CLI: {_CLI_PATH}")
        cls.cli = _load_cli_module()

    def test_env_only_gate_emits_intake_gate_decision_python_api(self) -> None:
        """AC-2: env gate on, no CLI flag — intake.gate_decision in outbox/jsonl."""
        snap = _snapshot_env(_FULL_CHAIN_ENV_KEYS)
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            env = {
                "GOV_NOTIFICATION_GATEWAY_ENABLED": "1",
                "GOV_NOTIFICATION_DISPATCH_ENABLED": "1",
            }
            try:
                with mock.patch.dict(os.environ, env, clear=False):
                    result = self.cli.run_agent_standard_case_experiment(
                        "tabular.cleaning.mvp",
                        _DEMO_PHASE,
                        mode="run",
                        auto_approve_intake=True,
                        outbox_root_override=str(outbox),
                        notifications_enabled=False,
                    )
            finally:
                _restore_env(snap)

            self.assertTrue(result.get("ok"))
            intake_files = _find_notification_events(outbox, "intake.gate_decision")
            self.assertGreaterEqual(len(intake_files), 1)
            self.assertEqual(intake_files[0].get("case_ref"), "demo_phase")

            jsonl_intake = [
                e for e in _read_jsonl_events(outbox)
                if e.get("event_type") == "intake.gate_decision"
            ]
            self.assertGreaterEqual(len(jsonl_intake), 1)

            tracked = [
                n for n in (result.get("notifications") or [])
                if n.get("event_type") == "intake.gate_decision"
            ]
            self.assertGreaterEqual(len(tracked), 1)

    def test_env_only_subprocess_cli_emits_intake_gate_decision(self) -> None:
        """AC-2: subprocess CLI without --enable-notifications, env gate only."""
        snap = _snapshot_env(_FULL_CHAIN_ENV_KEYS)
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            env = os.environ.copy()
            env.update(
                {
                    "GOV_NOTIFICATION_GATEWAY_ENABLED": "1",
                    "GOV_NOTIFICATION_DISPATCH_ENABLED": "0",
                }
            )
            cmd = [
                sys.executable,
                str(_CLI_PATH),
                "--task-type",
                "tabular.cleaning.mvp",
                "--case-dir",
                _DEMO_PHASE,
                "--mode",
                "run",
                "--auto-approve-intake",
                "--format",
                "json",
                "--outbox-root",
                str(outbox),
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(_REPO_ROOT),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            finally:
                _restore_env(snap)

            self.assertEqual(
                proc.returncode,
                0,
                msg=f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result.get("ok"))

            intake_files = _find_notification_events(outbox, "intake.gate_decision")
            self.assertGreaterEqual(len(intake_files), 1)

    def test_full_chain_webhook_receives_delivery_bundle_ready(self) -> None:
        """AC-3: dispatch registry → webhook sandbox POST with event_type / case_ref."""
        snap = _snapshot_env(_FULL_CHAIN_ENV_KEYS)
        with MockWebhookServer() as mock_server:
            with tempfile.TemporaryDirectory() as tmp:
                outbox = Path(tmp) / "outbox"
                env = _full_chain_env(mock_server.url)
                try:
                    with mock.patch.dict(os.environ, env, clear=False):
                        result = self.cli.run_agent_standard_case_experiment(
                            "tabular.cleaning.mvp",
                            _ADDITIONAL_DEMO,
                            mode="run",
                            auto_approve_intake=True,
                            sandbox_end_to_end=True,
                            outbox_root_override=str(outbox),
                            notifications_enabled=False,
                        )
                finally:
                    _restore_env(snap)

                self.assertTrue(result.get("ok"))
                self.assertEqual(result.get("final_status"), "sandbox_e2e_complete")

                bundle_files = _find_notification_events(outbox, "delivery.bundle_ready")
                self.assertGreaterEqual(len(bundle_files), 1)
                self.assertEqual(bundle_files[0].get("case_ref"), "additional_demo")

                requests = mock_server.get_requests()
                self.assertGreaterEqual(
                    len(requests),
                    1,
                    "Expected webhook POST from dispatch registry",
                )
                webhook_posts = [
                    r
                    for r in requests
                    if (r.get("body_json") or {}).get("event_type")
                    == "delivery.bundle_ready"
                ]
                self.assertGreaterEqual(len(webhook_posts), 1)
                payload = webhook_posts[0]["body_json"]
                self.assertEqual(payload.get("case_ref"), "additional_demo")
                self.assertIn("event_id", payload)

    def test_webhook_failure_fail_open_orchestrator_still_ok(self) -> None:
        """AC-4: webhook 500 — orchestrator main path ok remains true."""
        snap = _snapshot_env(_FULL_CHAIN_ENV_KEYS)

        class FailingServer:
            def __enter__(self) -> "FailingServer":
                self.server = HTTPServer(("127.0.0.1", 0), FailingMockWebhookHandler)
                self.port = self.server.server_address[1]
                self.url = f"http://127.0.0.1:{self.port}/webhook"
                self.thread = threading.Thread(
                    target=self.server.serve_forever, daemon=True
                )
                self.thread.start()
                return self

            def __exit__(self, *args: Any) -> None:
                self.server.shutdown()
                self.server.server_close()
                self.thread.join(timeout=2)

        with FailingServer() as mock_server:
            with tempfile.TemporaryDirectory() as tmp:
                outbox = Path(tmp) / "outbox"
                env = _full_chain_env(mock_server.url)
                try:
                    with mock.patch.dict(os.environ, env, clear=False):
                        result = self.cli.run_agent_standard_case_experiment(
                            "tabular.cleaning.mvp",
                            _ADDITIONAL_DEMO,
                            mode="run",
                            auto_approve_intake=True,
                            sandbox_end_to_end=True,
                            outbox_root_override=str(outbox),
                            notifications_enabled=False,
                        )
                finally:
                    _restore_env(snap)

                self.assertTrue(
                    result.get("ok"),
                    "Orchestrator must stay ok when webhook returns 500 (fail-open)",
                )
                self.assertEqual(result.get("final_status"), "sandbox_e2e_complete")

                bundle_files = _find_notification_events(outbox, "delivery.bundle_ready")
                self.assertGreaterEqual(len(bundle_files), 1)

    def test_all_gates_off_baseline_no_notifications(self) -> None:
        """AC-5: all env/flags off — no notification files, orchestrator unchanged."""
        snap = _snapshot_env(_FULL_CHAIN_ENV_KEYS)
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            cleared = {key: None for key in _FULL_CHAIN_ENV_KEYS}
            try:
                _restore_env(cleared)  # type: ignore[arg-type]
                result = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _DEMO_PHASE,
                    mode="run",
                    auto_approve_intake=True,
                    outbox_root_override=str(outbox),
                    notifications_enabled=False,
                )
            finally:
                _restore_env(snap)

            self.assertTrue(result.get("ok"))
            notifications_dir = outbox / "notifications"
            if notifications_dir.exists():
                self.assertEqual(list(notifications_dir.rglob("*.json")), [])
            jsonl = outbox / "notification_events.jsonl"
            if jsonl.exists():
                self.assertEqual(jsonl.read_text(encoding="utf-8").strip(), "")
            self.assertEqual(result.get("notifications") or [], [])


if __name__ == "__main__":
    unittest.main()
