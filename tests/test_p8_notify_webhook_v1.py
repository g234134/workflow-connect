"""Tests for P8 notify webhook v1 (real sandbox / staging / prod path)."""

from __future__ import annotations

import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

from delivery import notification_webhook_adapter_v1 as webhook
from delivery.p8_notify_webhook_v1 import (
    dispatch_bundle_ready,
    list_dlq,
    staging_prod_readiness_check,
)


_ENV_KEYS = (
    "GOV_NOTIFICATION_WEBHOOK_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_URL",
    "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
    "GOV_NOTIFICATION_WEBHOOK_TIER",
    "GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST",
    "GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET",
    "GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_DLQ_PATH",
    "GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS",
)


def _save_env(keys: tuple[str, ...]) -> Dict[str, Optional[str]]:
    return {k: os.environ.get(k) for k in keys}


def _restore_env(saved: Dict[str, Optional[str]]) -> None:
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


class _CaptureHandler(BaseHTTPRequestHandler):
    received: List[Dict[str, Any]] = []

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        _CaptureHandler.received.append({"body": body, "path": self.path})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


class _LocalServer:
    def __enter__(self) -> "_LocalServer":
        _CaptureHandler.received = []
        self.server = HTTPServer(("127.0.0.1", 0), _CaptureHandler)
        self.port = self.server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/webhook"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class TestP8NotifyWebhookV1(unittest.TestCase):
    def test_invalid_tier_fail_close(self) -> None:
        result = dispatch_bundle_ready(case_ref="demo_phase", tier="live")
        self.assertFalse(result["ok"])
        self.assertIn("fail-close", result["message"])

    def test_sandbox_real_http(self) -> None:
        saved = _save_env(_ENV_KEYS)
        try:
            with _LocalServer() as server:
                os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
                os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
                os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = server.url
                os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = "sandbox"
                result = dispatch_bundle_ready(
                    case_ref="demo_phase",
                    client_summary="bundle ready",
                    tier="sandbox",
                    endpoint_url=server.url,
                )
            self.assertTrue(result["ok"], msg=result.get("message"))
            self.assertTrue(result["external_http"])
            self.assertIsNotNone(result["delivered_at"])
            self.assertEqual(len(_CaptureHandler.received), 1)
            self.assertIn("delivery.bundle_ready", _CaptureHandler.received[0]["body"])
        finally:
            _restore_env(saved)

    def test_staging_path_with_mocked_http(self) -> None:
        saved = _save_env(_ENV_KEYS)
        target = "https://staging.internal.example.com/webhook"
        mock_http = {
            "http_status": 200,
            "response_body": '{"status":"ok"}',
            "error": None,
            "timeout": False,
        }
        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = target
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"] = (
            "staging.internal.example.com"
        )
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = "staging-test-secret"
        os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"] = "1"
        try:
            with patch.object(
                webhook,
                "_send_http_post_with_retry",
                return_value=(mock_http, 1, False),
            ) as mock_post:
                result = dispatch_bundle_ready(
                    case_ref="demo_phase",
                    tier="staging",
                    endpoint_url=target,
                )
            self.assertTrue(result["ok"])
            self.assertTrue(result["external_http"])
            self.assertEqual(result["tier"], "staging")
            mock_post.assert_called_once()
            self.assertEqual(mock_post.call_args[0][0], target)
        finally:
            _restore_env(saved)

    def test_prod_allowlist_miss_blocks(self) -> None:
        saved = _save_env(_ENV_KEYS)
        os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = "https://evil.example.com/hook"
        os.environ["GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"] = "hooks.prod.example.com"
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = "1"
        os.environ["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = "prod-test-secret"
        os.environ["GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"] = "1"
        try:
            with patch.object(webhook, "_send_http_post_with_retry") as mock_post:
                result = dispatch_bundle_ready(
                    case_ref="demo_phase",
                    tier="prod",
                    endpoint_url="https://evil.example.com/hook",
                )
            self.assertTrue(result["ok"])  # P7 fail-open at adapter layer
            self.assertFalse(result["external_http"])
            self.assertEqual(
                (result.get("webhook_result") or {}).get("blocked_reason"),
                "blocked_by_url_tier_policy",
            )
            mock_post.assert_not_called()
        finally:
            _restore_env(saved)

    def test_list_dlq_and_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dlq = Path(tmp) / "events.jsonl"
            listed = list_dlq(dlq_path_override=str(dlq))
            self.assertTrue(listed["ok"])
            self.assertEqual(listed["count"], 0)

        ready = staging_prod_readiness_check(tier="staging")
        self.assertTrue(ready["ok"])
        self.assertIn("gates_present", ready)
        self.assertNotIn("staging-test-secret", json_dumps_safe(ready))


def json_dumps_safe(obj: Any) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
