"""Unit tests for P8.9 verification bundle v1 (REGRESSION)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_BUNDLE_CLI = _REPO_ROOT / "scripts" / "run_p8_9_verification_bundle_v1.py"

_BUNDLE_FILENAMES = (
    "p8.9_verification_run.json",
    "events.json",
    "audit_quickview.json",
    "acks.json",
)

_EXPECTED_EVENT_TYPES_WITH_NOTIFICATIONS = frozenset(
    {
        "checkpoint.approved",
        "run.completed",
    }
)

_VALID_ACK_STATUSES = frozenset({"received", "failed"})
_VALID_TRACKING_STATUSES = frozenset({"pending_ack", "acked", "failed", "recorded"})


def _load_bundle_module():
    spec = importlib.util.spec_from_file_location(
        "run_p8_9_verification_bundle_v1", _BUNDLE_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_p8_9_verification_bundle_v1"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestP89VerificationBundleV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _BUNDLE_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_BUNDLE_CLI}")
        cls.bundle = _load_bundle_module()

    def test_verification_bundle_script_produces_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "verification" / "demo_phase"
            outbox_root = output_dir / "outbox"
            result = self.bundle.run_p8_9_verification_bundle(
                "demo_phase",
                repo_root=_REPO_ROOT,
                output_dir=output_dir,
                outbox_root_override=str(outbox_root),
                enable_notifications=True,
                enable_dispatch=True,
            )
            self.assertTrue(result.get("ok"), msg=result.get("message"))
            for filename in _BUNDLE_FILENAMES:
                path = output_dir / filename
                self.assertTrue(path.is_file(), f"missing artifact: {filename}")
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)

            summary = json.loads((output_dir / "p8.9_verification_run.json").read_text(encoding="utf-8"))
            self.assertEqual(summary.get("schema_version"), "p8_9_verification_run_v1")
            self.assertEqual(summary.get("case_ref"), "demo_phase")
            self.assertIn("events_summary", summary)
            self.assertIn("artifact_paths", summary)

    def test_verification_bundle_contains_expected_event_types_and_ack_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "verification" / "demo_phase"
            outbox_root = output_dir / "outbox"
            result = self.bundle.run_p8_9_verification_bundle(
                "demo_phase",
                repo_root=_REPO_ROOT,
                output_dir=output_dir,
                outbox_root_override=str(outbox_root),
                enable_notifications=True,
                enable_dispatch=True,
            )
            self.assertTrue(result.get("ok"))

            events = json.loads((output_dir / "events.json").read_text(encoding="utf-8"))
            self.assertTrue(events.get("ok"))
            notification_rows = [
                r for r in events.get("events") or [] if r.get("source_stream") == "notification"
            ]
            self.assertGreater(len(notification_rows), 0, "expected notification rows after enabled run")

            event_types = {str(r.get("event_type")) for r in notification_rows}
            self.assertTrue(
                event_types & _EXPECTED_EVENT_TYPES_WITH_NOTIFICATIONS,
                f"expected at least one of {_EXPECTED_EVENT_TYPES_WITH_NOTIFICATIONS}, got {event_types}",
            )
            for row in notification_rows:
                tracking = str(row.get("tracking_status", ""))
                self.assertIn(
                    tracking,
                    _VALID_TRACKING_STATUSES,
                    f"unexpected tracking_status: {tracking}",
                )

            acks = json.loads((output_dir / "acks.json").read_text(encoding="utf-8"))
            self.assertEqual(acks.get("schema_version"), "p8_9_verification_acks_v1")
            self.assertTrue(acks.get("ok"))
            self.assertIn("ingest", acks)
            ack_records = acks.get("ack_records") or []
            if ack_records:
                for record in ack_records:
                    self.assertIn(record.get("status"), _VALID_ACK_STATUSES)

            # run.completed should be acked when dispatch enabled
            run_completed_rows = [r for r in notification_rows if r.get("event_type") == "run.completed"]
            if run_completed_rows:
                self.assertEqual(run_completed_rows[0].get("tracking_status"), "acked")
                self.assertGreaterEqual(acks.get("ack_count", 0), 1)

            audit = json.loads((output_dir / "audit_quickview.json").read_text(encoding="utf-8"))
            wf = audit.get("workflow_notifications") or {}
            self.assertTrue(wf.get("found"))
            self.assertGreater(wf.get("count", 0), 0)


if __name__ == "__main__":
    unittest.main()
