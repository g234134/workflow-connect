"""Unit tests for notification webhook dispatch v1 (WD-P7-T2).

AC-1: Default (env off) behavior matches prod — no HTTP calls
AC-2: Sandbox flag + allowlist case — mock server receives POST with matching payload
AC-3: Webhook failure — main dispatch flow / orchestrator "ok" unchanged (fail-open)
AC-4: Tests green + mock server usage documented
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery import notification_dispatch_v1 as dispatch
from delivery import notification_gateway_v1 as gw
from delivery import notification_webhook_adapter_v1 as webhook
from delivery import workflow_event_consumer_v1 as consumer


class MockWebhookRequestHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler that records POST requests for testing."""
    
    received_requests: List[Dict[str, Any]] = []
    
    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        MockWebhookRequestHandler.received_requests.append({
            "path": self.path,
            "headers": dict(self.headers),
            "body": body,
            "body_json": json.loads(body) if body else None,
        })
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    
    def log_message(self, format: str, *args: Any) -> None:
        # Suppress request logging during tests
        pass


class FailingMockHandler(BaseHTTPRequestHandler):
    """HTTP handler that returns 500 errors."""
    
    def do_POST(self) -> None:
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error":"server error"}')
    
    def log_message(self, format: str, *args: Any) -> None:
        pass


class Sequential503Then200Handler(BaseHTTPRequestHandler):
    """Returns 503 on first POST, 200 on subsequent requests."""

    call_count = 0
    received_requests: List[Dict[str, Any]] = []

    def do_POST(self) -> None:
        Sequential503Then200Handler.call_count += 1
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        Sequential503Then200Handler.received_requests.append({"body": body})
        if Sequential503Then200Handler.call_count == 1:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"unavailable"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format: str, *args: Any) -> None:
        pass


class BadRequest400Handler(BaseHTTPRequestHandler):
    """HTTP handler that returns 400 (non-retriable)."""

    received_requests: List[Dict[str, Any]] = []

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        BadRequest400Handler.received_requests.append({"body": body})
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error":"bad request"}')

    def log_message(self, format: str, *args: Any) -> None:
        pass


class MockWebhookServer:
    """Context manager for a mock HTTP server in tests."""
    
    def __init__(self, handler_class: type = MockWebhookRequestHandler, port: int = 0) -> None:
        self.handler_class = handler_class
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.url: str = ""
    
    def __enter__(self) -> "MockWebhookServer":
        if hasattr(self.handler_class, "received_requests"):
            self.handler_class.received_requests = []
        if hasattr(self.handler_class, "call_count"):
            self.handler_class.call_count = 0
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
        if hasattr(self.handler_class, "received_requests"):
            return self.handler_class.received_requests.copy()
        return MockWebhookRequestHandler.received_requests.copy()


class TestNotificationWebhookAdapter(unittest.TestCase):
    """Direct tests for webhook adapter module."""
    
    def test_is_webhook_enabled_returns_false_when_env_not_set(self) -> None:
        """AC-1: Default env off -> webhook disabled."""
        # Ensure env is not set
        old_val = os.environ.pop("GOV_NOTIFICATION_WEBHOOK_ENABLED", None)
        try:
            self.assertFalse(webhook.is_webhook_enabled_via_env())
        finally:
            if old_val is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = old_val
    
    def test_is_webhook_enabled_returns_true_when_env_set(self) -> None:
        """Webhook enabled when env=1."""
        old_val = os.environ.get("GOV_NOTIFICATION_WEBHOOK_ENABLED")
        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        try:
            self.assertTrue(webhook.is_webhook_enabled_via_env())
        finally:
            if old_val is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = old_val
            else:
                os.environ.pop("GOV_NOTIFICATION_WEBHOOK_ENABLED", None)
    
    def test_case_allowlist_empty_denies_all(self) -> None:
        """Empty allowlist means no cases allowed."""
        old_allowlist = os.environ.pop("GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST", None)
        try:
            patterns = webhook._get_allowlist_patterns()
            self.assertEqual(patterns, [])
            self.assertFalse(webhook._case_ref_matches_allowlist("demo_phase", patterns))
            self.assertFalse(webhook._case_ref_matches_allowlist("test_case", patterns))
        finally:
            if old_allowlist is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = old_allowlist
    
    def test_case_allowlist_glob_matching(self) -> None:
        """Allowlist glob patterns work correctly."""
        old_allowlist = os.environ.get("GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST")
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*,test_*"
        try:
            patterns = webhook._get_allowlist_patterns()
            self.assertEqual(patterns, ["demo_*", "test_*"])
            self.assertTrue(webhook._case_ref_matches_allowlist("demo_phase", patterns))
            self.assertTrue(webhook._case_ref_matches_allowlist("demo_case_1", patterns))
            self.assertTrue(webhook._case_ref_matches_allowlist("test_case", patterns))
            self.assertFalse(webhook._case_ref_matches_allowlist("prod_case", patterns))
            self.assertFalse(webhook._case_ref_matches_allowlist("other", patterns))
        finally:
            if old_allowlist is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = old_allowlist
            else:
                os.environ.pop("GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST", None)
    
    def test_sandbox_url_validation(self) -> None:
        """Only localhost and 127.0.0.1 allowed in sandbox."""
        self.assertTrue(webhook._is_safe_sandbox_url("http://localhost:8080/webhook"))
        self.assertTrue(webhook._is_safe_sandbox_url("https://localhost/webhook"))
        self.assertTrue(webhook._is_safe_sandbox_url("http://127.0.0.1:9999/path"))
        
        # These should be rejected in sandbox mode
        self.assertFalse(webhook._is_safe_sandbox_url("http://example.com/webhook"))
        self.assertFalse(webhook._is_safe_sandbox_url("https://api.example.com/v1/hook"))
        self.assertFalse(webhook._is_safe_sandbox_url("ftp://localhost/file"))
        self.assertFalse(webhook._is_safe_sandbox_url(""))
    
    def test_send_webhook_disabled_by_env(self) -> None:
        """AC-1: When env disabled, returns dry-run result with no HTTP."""
        old_enabled = os.environ.pop("GOV_NOTIFICATION_WEBHOOK_ENABLED", None)
        try:
            event = {"event_id": "evt-123", "event_type": "delivery.bundle_ready"}
            result = webhook.send_webhook_notification(event)
            
            self.assertTrue(result["ok"])  # Fail-open: still ok
            self.assertIn("disabled", result["message"].lower())
            
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertTrue(webhook_result["dry_run"])
            self.assertIsNone(webhook_result["endpoint_url"])
        finally:
            if old_enabled is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = old_enabled
    
    def test_send_webhook_allowlist_skip(self) -> None:
        """AC-1: When case not in allowlist, dry-run without HTTP."""
        old_enabled = os.environ.get("GOV_NOTIFICATION_WEBHOOK_ENABLED")
        old_allowlist = os.environ.get("GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST")
        
        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "allowed_*"
        
        try:
            # Case not matching allowlist
            event = {
                "event_id": "evt-456",
                "event_type": "run.completed",
                "case_ref": "blocked_case",
            }
            result = webhook.send_webhook_notification(event)
            
            self.assertTrue(result["ok"])
            self.assertIn("allowlist skip", result["message"].lower())
            
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertTrue(webhook_result["dry_run"])
            self.assertFalse(webhook_result["case_allowed"])
        finally:
            if old_enabled is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = old_enabled
            else:
                os.environ.pop("GOV_NOTIFICATION_WEBHOOK_ENABLED", None)
            if old_allowlist is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = old_allowlist
            else:
                os.environ.pop("GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST", None)
    
    def test_send_webhook_no_url_configured(self) -> None:
        """When enabled and allowed but no URL -> dry-run."""
        old_enabled = os.environ.get("GOV_NOTIFICATION_WEBHOOK_ENABLED")
        old_allowlist = os.environ.get("GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST")
        old_url = os.environ.pop("GOV_NOTIFICATION_WEBHOOK_URL", None)
        
        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
        
        try:
            event = {
                "event_id": "evt-789",
                "event_type": "checkpoint.approved",
                "case_ref": "demo_phase",
            }
            result = webhook.send_webhook_notification(event)
            
            self.assertTrue(result["ok"])
            self.assertIn("url not configured", result["message"].lower())
            
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertTrue(webhook_result["dry_run"])
            self.assertTrue(webhook_result["case_allowed"])
        finally:
            if old_enabled is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = old_enabled
            else:
                os.environ.pop("GOV_NOTIFICATION_WEBHOOK_ENABLED", None)
            if old_allowlist is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = old_allowlist
            else:
                os.environ.pop("GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST", None)
            if old_url is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = old_url


class TestNotificationWebhookDispatchIntegration(unittest.TestCase):
    """Integration tests with mock HTTP server."""
    
    def test_webhook_post_to_mock_server_success(self) -> None:
        """AC-2: Enabled + allowlist match -> POST to mock server, payload matches."""
        # Save and set env
        old_env = {}
        env_keys = [
            "GOV_NOTIFICATION_WEBHOOK_ENABLED",
            "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
            "GOV_NOTIFICATION_WEBHOOK_URL",
        ]
        for key in env_keys:
            old_env[key] = os.environ.pop(key, None)
        
        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            
            try:
                event = gw.build_notification_event(
                    "delivery.bundle_ready",
                    case_ref="demo_phase",
                    case_dir="cases/demo_phase",
                    artifacts={"bundle_path": "/path/to/bundle.zip"},
                )
                
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")
                
                # Assert success
                self.assertTrue(result["ok"])
                self.assertIn("succeeded", result["message"].lower())
                
                webhook_result = result["webhook_result"]
                self.assertTrue(webhook_result["dispatched"])
                self.assertFalse(webhook_result["dry_run"])
                self.assertEqual(webhook_result["http_status"], 200)
                self.assertTrue(webhook_result["case_allowed"])
                
                # Assert mock server received the POST
                requests = mock_server.get_requests()
                self.assertEqual(len(requests), 1)
                
                req = requests[0]
                self.assertEqual(req["path"], "/webhook")
                self.assertEqual(req["headers"]["Content-Type"], "application/json")
                
                # Verify payload matches
                body_json = req["body_json"]
                self.assertEqual(body_json["event_id"], event["event_id"])
                self.assertEqual(body_json["event_type"], "delivery.bundle_ready")
                self.assertEqual(body_json["case_ref"], "demo_phase")
                self.assertEqual(body_json["artifacts"]["bundle_path"], "/path/to/bundle.zip")
                
            finally:
                for key, val in old_env.items():
                    if val is not None:
                        os.environ[key] = val
                    else:
                        os.environ.pop(key, None)
    
    def test_webhook_failure_is_fail_open(self) -> None:
        """AC-3: Webhook failure -> main flow ok=True (fail-open)."""
        old_env = {}
        env_keys = [
            "GOV_NOTIFICATION_WEBHOOK_ENABLED",
            "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
            "GOV_NOTIFICATION_WEBHOOK_URL",
        ]
        for key in env_keys:
            old_env[key] = os.environ.pop(key, None)
        
        # Use failing mock server (returns 500)
        class FailingServer:
            def __enter__(self) -> "FailingServer":
                self.server = HTTPServer(("127.0.0.1", 0), FailingMockHandler)
                self.port = self.server.server_address[1]
                self.url = f"http://127.0.0.1:{self.port}/webhook"
                self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.thread.start()
                return self
            
            def __exit__(self, *args: Any) -> None:
                self.server.shutdown()
                self.server.server_close()
                self.thread.join(timeout=2)
        
        with FailingServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            
            try:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")
                
                # CRITICAL: AC-3 requires ok=True even on webhook failure
                self.assertTrue(result["ok"], "Webhook failure should be fail-open (ok=True)")
                self.assertIn("fail-open", result["message"].lower())
                
                webhook_result = result["webhook_result"]
                self.assertFalse(webhook_result["dispatched"])
                self.assertEqual(webhook_result["http_status"], 500)
                self.assertIsNotNone(webhook_result["error"])
                
            finally:
                for key, val in old_env.items():
                    if val is not None:
                        os.environ[key] = val
                    else:
                        os.environ.pop(key, None)


_RETRY_ENV_KEYS = [
    "GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS",
    "GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS",
    "GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS",
]


def _save_env(keys: List[str]) -> Dict[str, Optional[str]]:
    saved: Dict[str, Optional[str]] = {}
    for key in keys:
        saved[key] = os.environ.pop(key, None)
    return saved


def _restore_env(saved: Dict[str, Optional[str]]) -> None:
    for key, val in saved.items():
        if val is not None:
            os.environ[key] = val
        else:
            os.environ.pop(key, None)


_TIER_ENV_KEYS = [
    "GOV_NOTIFICATION_WEBHOOK_TIER",
    "GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST",
]

_HMAC_ENV_KEYS = [
    "GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET",
    "GOV_NOTIFICATION_WEBHOOK_HMAC_HEADER",
    "GOV_NOTIFICATION_WEBHOOK_TIMESTAMP_HEADER",
    "GOV_NOTIFICATION_WEBHOOK_EVENT_ID_HEADER",
]

_DLQ_ENV_KEYS = [
    "GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_DLQ_PATH",
    "GOV_NOTIFICATION_WEBHOOK_DLQ_TIER",
]


class TestNotificationWebhookTierUrlPolicy(unittest.TestCase):
    """Tier / URL allowlist gate tests (WH-P7-NOTIF-PROD-URL-impl-v1)."""

    _WEBHOOK_ENV_KEYS = [
        "GOV_NOTIFICATION_WEBHOOK_ENABLED",
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
        "GOV_NOTIFICATION_WEBHOOK_URL",
        *_TIER_ENV_KEYS,
        *_DLQ_ENV_KEYS,
        *_HMAC_ENV_KEYS,
    ]

    def test_sandbox_tier_ignores_url_allowlist_regression(self) -> None:
        """TIER unset/sandbox + localhost URL: allowlist must not block POST."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"] = (
                "staging.internal.example.com"
            )

            try:
                event = gw.build_notification_event(
                    "delivery.bundle_ready",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

                self.assertTrue(result["ok"])
                self.assertTrue(result["webhook_result"]["dispatched"])
                self.assertEqual(len(mock_server.get_requests()), 1)
            finally:
                _restore_env(old_env)

    def test_staging_tier_allowlist_match_allows_post(self) -> None:
        """TIER=staging + matching allowlist -> POST allowed (mocked HTTP)."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)
        target_url = "https://staging.internal.example.com/webhook"
        mock_http_result = {
            "http_status": 200,
            "response_body": '{"status":"ok"}',
            "error": None,
            "timeout": False,
        }

        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = target_url
        os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = "staging"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"] = (
            "staging.internal.example.com"
        )
        os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = "staging-test-secret"

        try:
            with patch.object(
                webhook,
                "_send_http_post_with_retry",
                return_value=(mock_http_result, 1, False),
            ) as mock_post:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

            self.assertTrue(result["ok"])
            self.assertTrue(result["webhook_result"]["dispatched"])
            self.assertEqual(result["webhook_result"]["http_status"], 200)
            mock_post.assert_called_once()
            self.assertEqual(mock_post.call_args[0][0], target_url)
        finally:
            _restore_env(old_env)

    def test_staging_tier_allowlist_miss_blocks_post(self) -> None:
        """TIER=staging + allowlist miss -> blocked, no POST, fail-open ok."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = (
            "https://evil.example.com/webhook"
        )
        os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = "staging"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"] = (
            "staging.internal.example.com"
        )

        try:
            with patch.object(webhook, "_send_http_post_with_retry") as mock_post:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertTrue(webhook_result["dry_run"])
            self.assertEqual(
                webhook_result["blocked_reason"],
                "blocked_by_url_tier_policy",
            )
            self.assertEqual(webhook_result["blocked_rule"], "url_allowlist_mismatch")
            self.assertIn("blocked_by_url_tier_policy", webhook_result["error"])
            mock_post.assert_not_called()
        finally:
            _restore_env(old_env)

    def test_prod_tier_missing_allowlist_blocks_post(self) -> None:
        """TIER=prod + unset allowlist -> blocked with url_allowlist_missing."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = (
            "https://api.customer.example.com/webhook"
        )
        os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = "prod"

        try:
            with patch.object(webhook, "_send_http_post_with_retry") as mock_post:
                with self.assertLogs(
                    "delivery.notification_webhook_adapter_v1",
                    level="WARNING",
                ) as log_ctx:
                    event = gw.build_notification_event(
                        "delivery.bundle_ready",
                        case_ref="demo_phase",
                    )
                    result = webhook.send_webhook_notification(
                        event,
                        case_ref="demo_phase",
                    )

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertEqual(
                webhook_result["blocked_reason"],
                "blocked_by_url_tier_policy",
            )
            self.assertEqual(webhook_result["blocked_rule"], "url_allowlist_missing")
            self.assertTrue(
                any(
                    "allowlist" in msg.lower()
                    for msg in log_ctx.output
                ),
                log_ctx.output,
            )
            mock_post.assert_not_called()
        finally:
            _restore_env(old_env)


class TestNotificationWebhookRetry(unittest.TestCase):
    """Retry loop tests (WH-P7-NOTIF-RETRY-SANDBOX-v1)."""

    _WEBHOOK_ENV_KEYS = [
        "GOV_NOTIFICATION_WEBHOOK_ENABLED",
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
        "GOV_NOTIFICATION_WEBHOOK_URL",
        *_RETRY_ENV_KEYS,
    ]

    def test_default_no_retry_env_single_post_only(self) -> None:
        """AC-1: Without RETRY env -> single POST (regression guard)."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url

            try:
                event = gw.build_notification_event(
                    "delivery.bundle_ready",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

                self.assertTrue(result["ok"])
                webhook_result = result["webhook_result"]
                self.assertTrue(webhook_result["dispatched"])
                self.assertEqual(webhook_result.get("attempt_count"), 1)
                self.assertFalse(webhook_result.get("retry_exhausted"))
                self.assertEqual(len(mock_server.get_requests()), 1)
            finally:
                _restore_env(old_env)

    def test_retry_503_then_200_succeeds(self) -> None:
        """AC-2: 503 then 200 with max_attempts=2 -> dispatched, fail-open ok."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        Sequential503Then200Handler.call_count = 0
        with MockWebhookServer(handler_class=Sequential503Then200Handler) as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"] = "2"
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS"] = "10"

            try:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

                self.assertTrue(result["ok"])
                webhook_result = result["webhook_result"]
                self.assertTrue(webhook_result["dispatched"])
                self.assertGreaterEqual(webhook_result["attempt_count"], 2)
                self.assertFalse(webhook_result["retry_exhausted"])
                self.assertEqual(len(mock_server.get_requests()), 2)
            finally:
                _restore_env(old_env)

    def test_retry_exhausted_on_persistent_500(self) -> None:
        """AC-3: Persistent 500 with max_attempts=2 -> retry_exhausted, fail-open ok."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        class FailingServer:
            def __enter__(self) -> "FailingServer":
                self.server = HTTPServer(("127.0.0.1", 0), FailingMockHandler)
                self.port = self.server.server_address[1]
                self.url = f"http://127.0.0.1:{self.port}/webhook"
                self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.thread.start()
                return self

            def __exit__(self, *args: Any) -> None:
                self.server.shutdown()
                self.server.server_close()
                self.thread.join(timeout=2)

        with FailingServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"] = "2"
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS"] = "10"

            try:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

                self.assertTrue(result["ok"], "Fail-open: ok=True even when retries exhausted")
                webhook_result = result["webhook_result"]
                self.assertFalse(webhook_result["dispatched"])
                self.assertTrue(webhook_result["retry_exhausted"])
                self.assertEqual(webhook_result["attempt_count"], 2)
                self.assertEqual(webhook_result["http_status"], 500)
            finally:
                _restore_env(old_env)

    def test_non_retriable_400_no_retry(self) -> None:
        """400 is non-retriable: single attempt even when max_attempts>0."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with MockWebhookServer(handler_class=BadRequest400Handler) as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"] = "3"
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"] = "1"

            try:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

                self.assertTrue(result["ok"])
                webhook_result = result["webhook_result"]
                self.assertFalse(webhook_result["dispatched"])
                self.assertEqual(webhook_result["attempt_count"], 1)
                self.assertFalse(webhook_result["retry_exhausted"])
                self.assertEqual(webhook_result["http_status"], 400)
                self.assertEqual(len(mock_server.get_requests()), 1)
            finally:
                _restore_env(old_env)


_STAGING_RETRY_READY_ENV = {
    "GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED": "1",
    "GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED": "1",
    "GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET": "staging-retry-test-secret",
    "GOV_NOTIFICATION_WEBHOOK_DLQ_TIER": "staging",
}


class TestNotificationWebhookStagingProdRetry(unittest.TestCase):
    """Staging/prod tier retry readiness + retry loop (WH-P7-NOTIF-RETRY-prod-impl-v1)."""

    _WEBHOOK_ENV_KEYS = [
        "GOV_NOTIFICATION_WEBHOOK_ENABLED",
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
        "GOV_NOTIFICATION_WEBHOOK_URL",
        *_RETRY_ENV_KEYS,
        *_TIER_ENV_KEYS,
        *_DLQ_ENV_KEYS,
        *_HMAC_ENV_KEYS,
    ]

    def _apply_staging_retry_ready_env(
        self,
        *,
        dlq_enabled: str = "1",
        hmac_enabled: str = "1",
        hmac_secret: Optional[str] = "staging-retry-test-secret",
        retry_max_attempts: Optional[str] = None,
    ) -> None:
        os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = "staging"
        os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"] = dlq_enabled
        os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_TIER"] = "staging"
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = hmac_enabled
        if hmac_secret is not None:
            os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = hmac_secret
        else:
            os.environ.pop("GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET", None)
        if retry_max_attempts is not None:
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"] = retry_max_attempts
        else:
            os.environ.pop("GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS", None)

    def test_staging_retry_503_then_200_succeeds_no_dlq(self) -> None:
        """Staging tier + readiness gate pass -> 503 then 200, no DLQ."""
        import tempfile

        old_env = _save_env(self._WEBHOOK_ENV_KEYS)
        Sequential503Then200Handler.call_count = 0

        with tempfile.TemporaryDirectory() as tmp:
            dlq_path = Path(tmp) / "events.jsonl"
            with MockWebhookServer(handler_class=Sequential503Then200Handler) as mock_server:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
                os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
                os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
                os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"] = "1"
                os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS"] = "10"
                os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_PATH"] = str(dlq_path)
                self._apply_staging_retry_ready_env(retry_max_attempts="3")

                try:
                    with patch.object(
                        webhook,
                        "_check_url_tier_policy",
                        return_value=(True, None, None),
                    ):
                        event = gw.build_notification_event(
                            "run.completed",
                            case_ref="demo_phase",
                        )
                        result = webhook.send_webhook_notification(
                            event,
                            case_ref="demo_phase",
                        )

                    self.assertTrue(result["ok"])
                    webhook_result = result["webhook_result"]
                    self.assertTrue(webhook_result["dispatched"])
                    self.assertGreaterEqual(webhook_result["attempt_count"], 2)
                    self.assertFalse(webhook_result["retry_exhausted"])
                    self.assertEqual(len(mock_server.get_requests()), 2)
                    self.assertFalse(dlq_path.exists())
                finally:
                    _restore_env(old_env)

    def test_staging_retry_exhausted_writes_one_dlq_record(self) -> None:
        """Staging tier + persistent 500 -> retry exhausted, exactly one DLQ line."""
        import tempfile

        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        class FailingServer:
            def __enter__(self) -> "FailingServer":
                self.server = HTTPServer(("127.0.0.1", 0), FailingMockHandler)
                self.port = self.server.server_address[1]
                self.url = f"http://127.0.0.1:{self.port}/webhook"
                self.thread = threading.Thread(
                    target=self.server.serve_forever,
                    daemon=True,
                )
                self.thread.start()
                return self

            def __exit__(self, *args: Any) -> None:
                self.server.shutdown()
                self.server.server_close()
                self.thread.join(timeout=2)

        with tempfile.TemporaryDirectory() as tmp:
            dlq_path = Path(tmp) / "events.jsonl"
            with FailingServer() as mock_server:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
                os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
                os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
                os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"] = "1"
                os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS"] = "10"
                os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_PATH"] = str(dlq_path)
                self._apply_staging_retry_ready_env(retry_max_attempts="3")

                try:
                    with patch.object(
                        webhook,
                        "_check_url_tier_policy",
                        return_value=(True, None, None),
                    ):
                        event = gw.build_notification_event(
                            "run.completed",
                            case_ref="demo_phase",
                        )
                        result = webhook.send_webhook_notification(
                            event,
                            case_ref="demo_phase",
                        )

                    self.assertTrue(result["ok"])
                    webhook_result = result["webhook_result"]
                    self.assertFalse(webhook_result["dispatched"])
                    self.assertTrue(webhook_result["retry_exhausted"])
                    self.assertEqual(webhook_result["attempt_count"], 3)
                    self.assertEqual(webhook_result["http_status"], 500)

                    self.assertTrue(dlq_path.exists())
                    lines = dlq_path.read_text(encoding="utf-8").strip().splitlines()
                    self.assertEqual(len(lines), 1)
                    record = json.loads(lines[0])
                    self.assertEqual(record["tier"], "staging")
                    self.assertTrue(record["retry_exhausted"])
                finally:
                    _restore_env(old_env)

    def test_staging_precondition_dlq_disabled_blocks_retry(self) -> None:
        """Staging tier + DLQ off -> no retry loop, dlq_policy_violation."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            self._apply_staging_retry_ready_env(dlq_enabled="0")

            try:
                with patch.object(
                    webhook,
                    "_check_url_tier_policy",
                    return_value=(True, None, None),
                ):
                    event = gw.build_notification_event(
                        "run.completed",
                        case_ref="demo_phase",
                    )
                    result = webhook.send_webhook_notification(
                        event,
                        case_ref="demo_phase",
                    )

                self.assertTrue(result["ok"])
                webhook_result = result["webhook_result"]
                self.assertFalse(webhook_result["dispatched"])
                self.assertTrue(webhook_result["dry_run"])
                self.assertEqual(
                    webhook_result["blocked_rule"],
                    "dlq_policy_violation",
                )
                self.assertEqual(len(mock_server.get_requests()), 0)
            finally:
                _restore_env(old_env)

    def test_staging_precondition_hmac_disabled_blocks_retry(self) -> None:
        """Staging tier + HMAC off -> HMAC tier gate blocks before retry (hmac_disabled)."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            self._apply_staging_retry_ready_env(hmac_enabled="0", hmac_secret=None)

            try:
                with patch.object(
                    webhook,
                    "_check_url_tier_policy",
                    return_value=(True, None, None),
                ):
                    event = gw.build_notification_event(
                        "run.completed",
                        case_ref="demo_phase",
                    )
                    result = webhook.send_webhook_notification(
                        event,
                        case_ref="demo_phase",
                    )

                self.assertTrue(result["ok"])
                webhook_result = result["webhook_result"]
                self.assertFalse(webhook_result["dispatched"])
                self.assertEqual(
                    webhook_result["blocked_rule"],
                    "hmac_disabled",
                )
                self.assertEqual(len(mock_server.get_requests()), 0)
            finally:
                _restore_env(old_env)

    def test_sandbox_tier_single_post_regression(self) -> None:
        """Sandbox tier explicitly set -> still single POST without DLQ/HMAC mandatory."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = "sandbox"

            try:
                event = gw.build_notification_event(
                    "delivery.bundle_ready",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(
                    event,
                    case_ref="demo_phase",
                )

                self.assertTrue(result["ok"])
                webhook_result = result["webhook_result"]
                self.assertTrue(webhook_result["dispatched"])
                self.assertEqual(webhook_result.get("attempt_count"), 1)
                self.assertFalse(webhook_result.get("retry_exhausted"))
                self.assertEqual(len(mock_server.get_requests()), 1)
            finally:
                _restore_env(old_env)


class TestNotificationWebhookDlq(unittest.TestCase):
    """DLQ audit log tests (WH-P7-NOTIF-DLQ-impl-v1)."""

    _WEBHOOK_ENV_KEYS = [
        "GOV_NOTIFICATION_WEBHOOK_ENABLED",
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
        "GOV_NOTIFICATION_WEBHOOK_URL",
        *_RETRY_ENV_KEYS,
        *_DLQ_ENV_KEYS,
    ]

    def _run_persistent_500(
        self,
        tmp_path: Path,
        *,
        dlq_enabled: Optional[str] = None,
    ) -> tuple[Dict[str, Any], Path]:
        dlq_path = tmp_path / "events.jsonl"
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        class FailingServer:
            def __enter__(self) -> "FailingServer":
                self.server = HTTPServer(("127.0.0.1", 0), FailingMockHandler)
                self.port = self.server.server_address[1]
                self.url = f"http://127.0.0.1:{self.port}/webhook"
                self.thread = threading.Thread(
                    target=self.server.serve_forever,
                    daemon=True,
                )
                self.thread.start()
                return self

            def __exit__(self, *args: Any) -> None:
                self.server.shutdown()
                self.server.server_close()
                self.thread.join(timeout=2)

        with FailingServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"] = "2"
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS"] = "10"
            os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_PATH"] = str(dlq_path)
            if dlq_enabled is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"] = dlq_enabled

            try:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(
                    event,
                    case_ref="demo_phase",
                )
                return result, dlq_path
            finally:
                _restore_env(old_env)

    def test_dlq_disabled_no_jsonl_on_retry_exhausted(self) -> None:
        """DLQ off (default) -> retry exhausted but no events.jsonl write."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result, dlq_path = self._run_persistent_500(Path(tmp), dlq_enabled=None)

            self.assertTrue(result["ok"])
            self.assertTrue(result["webhook_result"]["retry_exhausted"])
            self.assertFalse(dlq_path.exists())

    def test_dlq_disabled_explicit_zero_no_jsonl(self) -> None:
        """DLQ_ENABLED=0 -> no jsonl write on final failure."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result, dlq_path = self._run_persistent_500(Path(tmp), dlq_enabled="0")

            self.assertTrue(result["ok"])
            self.assertFalse(result["webhook_result"]["dispatched"])
            self.assertFalse(dlq_path.exists())

    def test_dlq_enabled_writes_record_on_retry_exhausted(self) -> None:
        """DLQ enabled + persistent 500 -> one jsonl record with required fields."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result, dlq_path = self._run_persistent_500(Path(tmp), dlq_enabled="1")

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertTrue(webhook_result["retry_exhausted"])
            self.assertEqual(webhook_result["http_status"], 500)
            self.assertEqual(webhook_result["attempt_count"], 2)

            self.assertTrue(dlq_path.exists())
            lines = dlq_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)

            record = json.loads(lines[0])
            self.assertEqual(record["schema_id"], "notification_webhook_dlq_v1")
            self.assertEqual(record["http_status"], 500)
            self.assertEqual(record["attempt_count"], 2)
            self.assertTrue(record["retry_exhausted"])
            self.assertIn("endpoint", record)
            self.assertIn("127.0.0.1", record["endpoint"])
            self.assertIsNotNone(record["last_error"])
            self.assertEqual(record["event_type"], "run.completed")
            self.assertEqual(record["tier"], "sandbox")
            self.assertIn("webhook_result", record)
            self.assertEqual(
                record["webhook_result"]["http_status"],
                webhook_result["http_status"],
            )

    def test_dlq_enabled_no_write_on_eventual_success(self) -> None:
        """DLQ enabled + 503 then 200 -> no DLQ lines."""
        import tempfile

        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with tempfile.TemporaryDirectory() as tmp:
            dlq_path = Path(tmp) / "events.jsonl"
            Sequential503Then200Handler.call_count = 0

            with MockWebhookServer(handler_class=Sequential503Then200Handler) as mock_server:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
                os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
                os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
                os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"] = "2"
                os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"] = "1"
                os.environ["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS"] = "10"
                os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"] = "1"
                os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_PATH"] = str(dlq_path)

                try:
                    event = gw.build_notification_event(
                        "run.completed",
                        case_ref="demo_phase",
                    )
                    result = webhook.send_webhook_notification(
                        event,
                        case_ref="demo_phase",
                    )

                    self.assertTrue(result["ok"])
                    self.assertTrue(result["webhook_result"]["dispatched"])
                    self.assertFalse(result["webhook_result"]["retry_exhausted"])
                    if dlq_path.exists():
                        self.assertEqual(
                            len(dlq_path.read_text(encoding="utf-8").strip()),
                            0,
                        )
                    else:
                        self.assertFalse(dlq_path.exists())
                finally:
                    _restore_env(old_env)


class TestNotificationWebhookHmac(unittest.TestCase):
    """HMAC sender tests (WH-P7-NOTIF-HMAC-impl-v1)."""

    _WEBHOOK_ENV_KEYS = [
        "GOV_NOTIFICATION_WEBHOOK_ENABLED",
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
        "GOV_NOTIFICATION_WEBHOOK_URL",
        *_HMAC_ENV_KEYS,
    ]

    def test_hmac_disabled_by_default_no_signature_headers(self) -> None:
        """Default (no HMAC env) -> no Gov HMAC/Timestamp/Event-Id headers."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url

            try:
                event = gw.build_notification_event(
                    "delivery.bundle_ready",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

                self.assertTrue(result["ok"])
                self.assertTrue(result["webhook_result"]["dispatched"])

                req = mock_server.get_requests()[0]
                headers = req["headers"]
                self.assertNotIn("X-Gov-Signature-256", headers)
                self.assertNotIn("X-Gov-Timestamp", headers)
                self.assertNotIn("X-Gov-Event-Id", headers)
            finally:
                _restore_env(old_env)

    def test_hmac_enabled_with_valid_secret_adds_headers_and_digest(self) -> None:
        """HMAC_ENABLED=1 + secret -> signature headers with verifiable digest."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)
        secret = "unit-test-hmac-secret"

        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = secret

            try:
                event = gw.build_notification_event(
                    "delivery.bundle_ready",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

                self.assertTrue(result["ok"])
                self.assertTrue(result["webhook_result"]["dispatched"])

                req = mock_server.get_requests()[0]
                headers = req["headers"]
                body = req["body"]
                event_id = req["body_json"]["event_id"]

                self.assertIn("X-Gov-Signature-256", headers)
                self.assertIn("X-Gov-Timestamp", headers)
                self.assertIn("X-Gov-Event-Id", headers)
                self.assertEqual(headers["X-Gov-Event-Id"], event_id)
                self.assertTrue(headers["X-Gov-Signature-256"].startswith("sha256="))

                timestamp = headers["X-Gov-Timestamp"]
                message = f"{timestamp}.{event_id}.{body}".encode("utf-8")
                expected_hex = hmac.new(
                    secret.encode("utf-8"),
                    message,
                    hashlib.sha256,
                ).hexdigest()
                self.assertEqual(
                    headers["X-Gov-Signature-256"],
                    f"sha256={expected_hex}",
                )
            finally:
                _restore_env(old_env)

    def test_hmac_enabled_missing_secret_fail_open_unsigned(self) -> None:
        """HMAC_ENABLED=1 but empty secret -> unsigned POST, fail-open ok, warning log."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        with MockWebhookServer() as mock_server:
            os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
            os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
            os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
            os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = "1"
            os.environ.pop("GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET", None)

            try:
                with self.assertLogs(
                    "delivery.notification_webhook_adapter_v1",
                    level="WARNING",
                ) as log_ctx:
                    event = gw.build_notification_event(
                        "run.completed",
                        case_ref="demo_phase",
                    )
                    result = webhook.send_webhook_notification(
                        event,
                        case_ref="demo_phase",
                    )

                self.assertTrue(result["ok"])
                self.assertTrue(result["webhook_result"]["dispatched"])
                self.assertEqual(result["webhook_result"]["http_status"], 200)
                self.assertTrue(
                    any("HMAC signing disabled" in msg for msg in log_ctx.output),
                    log_ctx.output,
                )

                req = mock_server.get_requests()[0]
                headers = req["headers"]
                self.assertNotIn("X-Gov-Signature-256", headers)
                self.assertNotIn("X-Gov-Timestamp", headers)
            finally:
                _restore_env(old_env)


class TestNotificationWebhookHmacTierPolicy(unittest.TestCase):
    """Tier HMAC mandatory gate tests (WH-P7-NOTIF-HMAC-prod-impl-v1)."""

    _WEBHOOK_ENV_KEYS = [
        "GOV_NOTIFICATION_WEBHOOK_ENABLED",
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
        "GOV_NOTIFICATION_WEBHOOK_URL",
        *_TIER_ENV_KEYS,
        *_HMAC_ENV_KEYS,
        *_DLQ_ENV_KEYS,
    ]

    _STAGING_URL = "https://staging.internal.example.com/webhook"
    _STAGING_ALLOWLIST = "staging.internal.example.com"

    def _staging_env(
        self,
        *,
        hmac_enabled: Optional[str] = None,
        hmac_secret: Optional[str] = None,
        tier: str = "staging",
    ) -> None:
        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = self._STAGING_URL
        os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = tier
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"] = self._STAGING_ALLOWLIST
        os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"] = "1"
        if hmac_enabled is not None:
            os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = hmac_enabled
        else:
            os.environ.pop("GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED", None)
        if hmac_secret is not None:
            os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = hmac_secret
        else:
            os.environ.pop("GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET", None)

    def test_sandbox_tier_hmac_gate_regression_allows_post(self) -> None:
        """Sandbox tier: HMAC on/off both POST; no blocked_reason."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        try:
            with MockWebhookServer() as mock_server:
                for hmac_enabled, hmac_secret in (
                    (None, None),
                    ("1", "unit-test-hmac-secret"),
                ):
                    with self.subTest(hmac_enabled=hmac_enabled, hmac_secret=hmac_secret):
                        MockWebhookRequestHandler.received_requests = []
                        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
                        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
                        os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock_server.url
                        os.environ.pop("GOV_NOTIFICATION_WEBHOOK_TIER", None)
                        os.environ.pop("GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED", None)
                        os.environ.pop("GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET", None)
                        if hmac_enabled is not None:
                            os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = hmac_enabled
                        if hmac_secret is not None:
                            os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = hmac_secret

                        event = gw.build_notification_event(
                            "delivery.bundle_ready",
                            case_ref="demo_phase",
                        )
                        result = webhook.send_webhook_notification(
                            event,
                            case_ref="demo_phase",
                        )

                        self.assertTrue(result["ok"])
                        self.assertTrue(result["webhook_result"]["dispatched"])
                        self.assertNotIn("blocked_reason", result["webhook_result"])
                        self.assertEqual(len(mock_server.get_requests()), 1)
        finally:
            _restore_env(old_env)

    def test_staging_tier_hmac_ready_allows_signed_post(self) -> None:
        """Staging + HMAC ready + allowlist OK -> signed POST."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)
        secret = "unit-test-hmac-secret"
        self._staging_env(hmac_enabled="1", hmac_secret=secret)

        try:
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_resp = mock_urlopen.return_value.__enter__.return_value
                mock_resp.getcode.return_value = 200
                mock_resp.read.return_value = b'{"status":"ok"}'

                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertTrue(webhook_result["dispatched"])
            self.assertNotIn("blocked_reason", webhook_result)
            self.assertNotIn("blocked_rule", webhook_result)
            mock_urlopen.assert_called_once()

            req = mock_urlopen.call_args[0][0]
            headers = {k.lower(): v for k, v in req.header_items()}
            body = req.data.decode("utf-8")
            event_id = json.loads(body)["event_id"]
            self.assertIn("x-gov-signature-256", headers)
            self.assertIn("x-gov-timestamp", headers)
            self.assertIn("x-gov-event-id", headers)
            self.assertEqual(headers["x-gov-event-id"], event_id)
            message = f"{headers['x-gov-timestamp']}.{event_id}.{body}".encode("utf-8")
            expected_hex = hmac.new(
                secret.encode("utf-8"),
                message,
                hashlib.sha256,
            ).hexdigest()
            self.assertEqual(
                headers["x-gov-signature-256"],
                f"sha256={expected_hex}",
            )
        finally:
            _restore_env(old_env)

    def test_staging_tier_hmac_disabled_blocks_post(self) -> None:
        """Staging + HMAC off -> no POST, blocked_rule=hmac_disabled."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)
        self._staging_env(hmac_enabled="0")

        try:
            with patch.object(webhook, "_send_http_post_with_retry") as mock_post:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertTrue(webhook_result["dry_run"])
            self.assertEqual(
                webhook_result["blocked_reason"],
                "blocked_by_hmac_tier_policy",
            )
            self.assertEqual(webhook_result["blocked_rule"], "hmac_disabled")
            mock_post.assert_not_called()
        finally:
            _restore_env(old_env)

    def test_staging_tier_hmac_secret_missing_blocks_post(self) -> None:
        """Staging + HMAC on + empty secret -> no POST, hmac_secret_missing."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)
        self._staging_env(hmac_enabled="1", hmac_secret="")

        try:
            with patch.object(webhook, "_send_http_post_with_retry") as mock_post:
                event = gw.build_notification_event(
                    "run.completed",
                    case_ref="demo_phase",
                )
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertEqual(
                webhook_result["blocked_reason"],
                "blocked_by_hmac_tier_policy",
            )
            self.assertEqual(webhook_result["blocked_rule"], "hmac_secret_missing")
            mock_post.assert_not_called()
        finally:
            _restore_env(old_env)

    def test_staging_tier_hmac_signing_failed_blocks_post(self) -> None:
        """Staging + signing error -> no POST, blocked_rule=hmac_signing_failed."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)
        self._staging_env(hmac_enabled="1", hmac_secret="unit-test-hmac-secret")

        try:
            with patch.object(
                webhook,
                "_compute_hmac_sha256_hex",
                side_effect=RuntimeError("simulated signing failure"),
            ):
                with patch.object(webhook, "_send_http_post_with_retry") as mock_post:
                    event = gw.build_notification_event(
                        "run.completed",
                        case_ref="demo_phase",
                    )
                    result = webhook.send_webhook_notification(
                        event,
                        case_ref="demo_phase",
                    )

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertEqual(
                webhook_result["blocked_reason"],
                "blocked_by_hmac_tier_policy",
            )
            self.assertEqual(webhook_result["blocked_rule"], "hmac_signing_failed")
            mock_post.assert_not_called()
        finally:
            _restore_env(old_env)

    def test_staging_tier_missing_event_id_blocks_post(self) -> None:
        """Staging + payload without event_id -> hmac_event_id_missing."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)
        self._staging_env(hmac_enabled="1", hmac_secret="unit-test-hmac-secret")

        try:
            with patch.object(webhook, "_send_http_post_with_retry") as mock_post:
                event = {
                    "event_type": "run.completed",
                    "case_ref": "demo_phase",
                }
                result = webhook.send_webhook_notification(event, case_ref="demo_phase")

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertFalse(webhook_result["dispatched"])
            self.assertEqual(
                webhook_result["blocked_rule"],
                "hmac_event_id_missing",
            )
            mock_post.assert_not_called()
        finally:
            _restore_env(old_env)

    def test_prod_tier_url_gate_blocks_before_hmac_gate(self) -> None:
        """Prod + missing allowlist -> URL gate blocks; HMAC gate not reached."""
        old_env = _save_env(self._WEBHOOK_ENV_KEYS)

        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = (
            "https://api.customer.example.com/webhook"
        )
        os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = "prod"
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = "unit-test-hmac-secret"

        try:
            with patch.object(webhook, "_check_hmac_tier_policy") as mock_hmac_gate:
                with patch.object(webhook, "_send_http_post_with_retry") as mock_post:
                    event = gw.build_notification_event(
                        "delivery.bundle_ready",
                        case_ref="demo_phase",
                    )
                    result = webhook.send_webhook_notification(
                        event,
                        case_ref="demo_phase",
                    )

            self.assertTrue(result["ok"])
            webhook_result = result["webhook_result"]
            self.assertEqual(
                webhook_result["blocked_reason"],
                "blocked_by_url_tier_policy",
            )
            self.assertEqual(webhook_result["blocked_rule"], "url_allowlist_missing")
            mock_hmac_gate.assert_not_called()
            mock_post.assert_not_called()
        finally:
            _restore_env(old_env)


class TestWebhookDispatchHandler(unittest.TestCase):
    """Tests for dispatch handler integration."""
    
    def test_dispatch_handler_registry_integration(self) -> None:
        """Handler is registered and callable via dispatch registry."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            
            # Save env
            old_enabled = os.environ.pop("GOV_NOTIFICATION_WEBHOOK_ENABLED", None)
            
            try:
                # When env disabled, handler should return ok=True but not dispatch
                event = gw.build_notification_event(
                    "delivery.bundle_ready",
                    case_ref="demo_phase",
                    case_dir="cases/demo_phase",
                )
                
                # Emit the notification first
                gw.send_notification(
                    event,
                    enabled=True,
                    repo_root=Path(tmp),
                    outbox_root_override=str(outbox),
                )
                
                # Create registry with webhook handler
                registry = dispatch.HandlerRegistry()
                registry.register_handler(
                    "webhook_dispatch_v1",
                    ["delivery.bundle_ready"],
                    dispatch.handle_webhook_dispatch,
                )
                
                # Dispatch
                result = dispatch.dispatch_event(
                    event,
                    handler_registry=registry,
                    repo_root=Path(tmp),
                    outbox_root_override=str(outbox),
                )
                
                # Should succeed (fail-open)
                self.assertTrue(result["ok"])
                self.assertIn("webhook_dispatch_v1", result["handlers_invoked"])
                
                # Find webhook handler result
                webhook_result = None
                for hr in result["handler_results"]:
                    if hr["handler_id"] == "webhook_dispatch_v1":
                        webhook_result = hr
                        break
                
                self.assertIsNotNone(webhook_result)
                self.assertTrue(webhook_result["ok"])  # Fail-open
                
            finally:
                if old_enabled is not None:
                    os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = old_enabled
    
    def test_yaml_registry_loads_webhook_handler(self) -> None:
        """YAML config loads webhook handler with enabled_when gate."""
        registry = dispatch.load_default_handler_registry(repo_root=_REPO_ROOT)
        handlers = registry.list_handlers()
        
        # Find webhook handler
        webhook_handler = None
        for h in handlers:
            if h["handler_id"] == "webhook_dispatch_v1":
                webhook_handler = h
                break
        
        self.assertIsNotNone(webhook_handler, "webhook_dispatch_v1 should be in YAML")
        self.assertEqual(webhook_handler["enabled_when"], "webhook_dispatch")
        self.assertIn("delivery.bundle_ready", webhook_handler["event_types"])
        
        # When env is off, handler should be disabled
        old_enabled = os.environ.pop("GOV_NOTIFICATION_WEBHOOK_ENABLED", None)
        try:
            # Re-load registry (enabled status is checked at find_handlers time)
            registry2 = dispatch.load_default_handler_registry(repo_root=_REPO_ROOT)
            handlers2 = registry2.list_handlers()
            webhook_handler2 = None
            for h in handlers2:
                if h["handler_id"] == "webhook_dispatch_v1":
                    webhook_handler2 = h
                    break
            
            self.assertIsNotNone(webhook_handler2)
            self.assertFalse(webhook_handler2["enabled"])
        finally:
            if old_enabled is not None:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = old_enabled


if __name__ == "__main__":
    unittest.main()
