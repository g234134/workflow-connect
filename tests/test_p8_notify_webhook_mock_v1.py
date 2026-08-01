"""Tests for P8-T3 notify webhook mock / DLQ replay MVP."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from delivery.p8_notify_webhook_mock_v1 import (
    list_dlq,
    mock_dispatch_bundle_ready,
    replay_dlq_event,
)


class TestP8NotifyWebhookMockV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.dlq = self.repo_root / "outbox" / "p8_notify_dlq_mock" / "events.jsonl"
        self.extra = {
            "repo_root": self.repo_root,
            "dlq_path_override": str(self.dlq),
        }

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_mock_dispatch_success(self) -> None:
        result = mock_dispatch_bundle_ready(
            case_ref="demo_phase",
            client_summary="bundle ready for client",
            **self.extra,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "mock")
        self.assertFalse(result["external_http"])
        self.assertIsNotNone(result["delivered_at"])
        self.assertFalse(result["retry_exhausted"])

    def test_force_fail_writes_dlq(self) -> None:
        result = mock_dispatch_bundle_ready(
            case_ref="demo_phase",
            force_fail=True,
            max_attempts=3,
            **self.extra,
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["retry_exhausted"])
        self.assertEqual(result["attempt_count"], 3)
        self.assertFalse(result["external_http"])
        self.assertTrue(self.dlq.is_file())

        listed = list_dlq(**self.extra)
        self.assertEqual(listed["count"], 1)
        self.assertEqual(listed["items"][0]["case_ref"], "demo_phase")
        event_id = listed["items"][0]["event_id"]

        dry = replay_dlq_event(event_id=event_id, dry_run=True, **self.extra)
        self.assertTrue(dry["ok"])
        self.assertTrue(dry["would_replay"])

        replayed = replay_dlq_event(event_id=event_id, dry_run=False, **self.extra)
        self.assertTrue(replayed["ok"])
        self.assertTrue(replayed["replayed"])
        self.assertFalse(replayed["external_http"])

        listed2 = list_dlq(**self.extra)
        self.assertIsNotNone(listed2["items"][0].get("replayed_at"))

    def test_live_mode_fail_close(self) -> None:
        result = mock_dispatch_bundle_ready(
            case_ref="demo_phase",
            mode="live",
            **self.extra,
        )
        self.assertFalse(result["ok"])
        self.assertIn("fail-close", result["message"])

    def test_replay_live_fail_close(self) -> None:
        mock_dispatch_bundle_ready(case_ref="x", force_fail=True, **self.extra)
        event_id = list_dlq(**self.extra)["items"][0]["event_id"]
        result = replay_dlq_event(
            event_id=event_id,
            dry_run=False,
            mode="live",
            **self.extra,
        )
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
