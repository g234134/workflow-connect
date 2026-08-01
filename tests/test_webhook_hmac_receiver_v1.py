"""Contract tests for Gov webhook HMAC receiver reference (§4.6.5.2)."""

from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.webhook_hmac_receiver_v1 import (
    ReplayCache,
    sign_gov_webhook_headers,
    verify_gov_webhook,
)

FIXTURE_DIR = _REPO_ROOT / "tests" / "fixtures" / "webhook_hmac"
FIXTURE_SECRET = "p7-staging-fixture-hmac-secret-v1"


def _load_fixture(name: str) -> tuple[bytes, dict[str, str]]:
    body_path = FIXTURE_DIR / f"{name}.json"
    headers_path = FIXTURE_DIR / f"{name}.headers.json"
    body_bytes = body_path.read_bytes()
    headers = json.loads(headers_path.read_text(encoding="utf-8"))
    return body_bytes, headers


class TestWebhookHmacReceiverContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (FIXTURE_DIR / "signed_delivery_bundle_ready.json").is_file():
            from tools.generate_webhook_hmac_fixtures_v1 import main as generate

            generate()

    def test_signed_fixture_accepts(self) -> None:
        body_bytes, headers = _load_fixture("signed_delivery_bundle_ready")
        result = verify_gov_webhook(
            body_bytes=body_bytes,
            headers=headers,
            shared_secret=FIXTURE_SECRET,
            now_ts=1750000000,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.reason, "accepted")
        self.assertEqual(result.event_id, "evt-fixture-signed-001")

    def test_invalid_signature_rejects(self) -> None:
        body_bytes, headers = _load_fixture("invalid_signature")
        result = verify_gov_webhook(
            body_bytes=body_bytes,
            headers=headers,
            shared_secret=FIXTURE_SECRET,
            now_ts=1750000000,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.reason, "invalid_signature")

    def test_expired_timestamp_rejects(self) -> None:
        body_bytes, headers = _load_fixture("expired_timestamp")
        result = verify_gov_webhook(
            body_bytes=body_bytes,
            headers=headers,
            shared_secret=FIXTURE_SECRET,
            now_ts=int(time.time()),
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.reason, "timestamp_out_of_window")

    def test_event_id_mismatch_rejects(self) -> None:
        body_bytes, headers = _load_fixture("event_id_mismatch")
        result = verify_gov_webhook(
            body_bytes=body_bytes,
            headers=headers,
            shared_secret=FIXTURE_SECRET,
            now_ts=int(time.time()),
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.reason, "event_id_mismatch")

    def test_replay_returns_idempotent_accept(self) -> None:
        body_bytes, headers = _load_fixture("replay_same_event_id")
        cache = ReplayCache(max_seen_window_sec=86400)
        now = int(time.time())
        first = verify_gov_webhook(
            body_bytes=body_bytes,
            headers=headers,
            shared_secret=FIXTURE_SECRET,
            replay_cache=cache,
            now_ts=now,
        )
        second = verify_gov_webhook(
            body_bytes=body_bytes,
            headers=headers,
            shared_secret=FIXTURE_SECRET,
            replay_cache=cache,
            now_ts=now + 1,
        )
        self.assertTrue(first.ok)
        self.assertFalse(first.idempotent)
        self.assertTrue(second.ok)
        self.assertTrue(second.idempotent)
        self.assertEqual(second.reason, "replay_idempotent_accept")

    def test_missing_headers_rejects(self) -> None:
        body = {
            "event_id": "evt-missing-headers-001",
            "event_type": "run.completed",
        }
        body_bytes = json.dumps(body).encode("utf-8")
        result = verify_gov_webhook(
            body_bytes=body_bytes,
            headers={},
            shared_secret=FIXTURE_SECRET,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "missing_signature_headers")

    def test_sender_adapter_roundtrip(self) -> None:
        body = {
            "schema_version": "notification_event_v1",
            "event_id": "evt-roundtrip-001",
            "event_type": "run.completed",
            "case_ref": "demo_phase",
        }
        body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = sign_gov_webhook_headers(
            body_bytes,
            shared_secret=FIXTURE_SECRET,
            event_id=body["event_id"],
        )
        result = verify_gov_webhook(
            body_bytes=body_bytes,
            headers=headers,
            shared_secret=FIXTURE_SECRET,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.event_id, "evt-roundtrip-001")


if __name__ == "__main__":
    unittest.main()
