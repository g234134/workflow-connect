"""Unit tests for orchestrator notification events (WD-P7-T1).

Tests P75-G4 deferred items: intake.gate_decision and delivery.bundle_ready
events are emitted in --enable-notifications / env gate enabled scenario.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
_DEMO_PHASE = "cases/demo_phase"
_ADDITIONAL_DEMO = "cases/additional_demo"

_NOTIFICATION_ENV_KEYS = (
    "GOV_NOTIFICATION_GATEWAY_ENABLED",
    "GOV_NOTIFICATION_DISPATCH_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_ENABLED",
    "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST",
    "GOV_NOTIFICATION_WEBHOOK_URL",
)


def _snapshot_env(keys: tuple[str, ...]) -> dict[str, str | None]:
    return {key: os.environ.get(key) for key in keys}


def _restore_env(snapshot: dict[str, str | None]) -> None:
    for key, val in snapshot.items():
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val


def _clear_notification_env() -> dict[str, str | None]:
    snap = _snapshot_env(_NOTIFICATION_ENV_KEYS)
    for key in _NOTIFICATION_ENV_KEYS:
        os.environ.pop(key, None)
    return snap


def _load_cli_module():
    spec = importlib.util.spec_from_file_location(
        "run_agent_standard_case_experiment", _CLI_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_standard_case_experiment"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestOrchestratorNotifications(unittest.TestCase):
    """WD-P7-T1: orchestrator gate/bundle notification event tests."""

    @classmethod
    def setUpClass(cls) -> None:
        if not _CLI_PATH.is_file():
            raise unittest.SkipTest(f"missing CLI: {_CLI_PATH}")
        cls.cli = _load_cli_module()

    def _find_notification_events(self, outbox: Path, event_type: str) -> list[dict]:
        """Find all notification events of given type in outbox/notifications/."""
        events = []
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

    def _read_jsonl_events(self, outbox: Path) -> list[dict]:
        """Read all events from notification_events.jsonl."""
        jsonl_path = outbox / "notification_events.jsonl"
        events = []
        if not jsonl_path.exists():
            return events

        try:
            with jsonl_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            pass
        return events

    def test_enable_notifications_emits_intake_gate_decision(self) -> None:
        """AC-1: --enable-notifications emits intake.gate_decision event."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
                notifications_enabled=True,
            )

            # Verify orchestrator succeeded
            self.assertTrue(result.get("ok"))

            # Verify intake.gate_decision event was emitted
            events = self._find_notification_events(outbox, "intake.gate_decision")
            self.assertGreaterEqual(
                len(events),
                1,
                "Expected at least one intake.gate_decision event",
            )

            # Verify event structure
            event = events[0]
            self.assertIn("event_id", event)
            self.assertIn("emitted_at", event)
            self.assertIn("case_ref", event)
            self.assertEqual(event.get("case_ref"), "demo_phase")
            self.assertIn("artifacts", event)
            self.assertIn("decision", event["artifacts"])
            self.assertIn("risk_level", event["artifacts"])

            # Verify JSONL also contains the event
            jsonl_events = self._read_jsonl_events(outbox)
            intake_events = [e for e in jsonl_events if e.get("event_type") == "intake.gate_decision"]
            self.assertGreaterEqual(len(intake_events), 1)

    def test_enable_notifications_emits_delivery_bundle_ready_sandbox(self) -> None:
        """AC-1: --enable-notifications emits delivery.bundle_ready on sandbox success."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _ADDITIONAL_DEMO,
                mode="run",
                auto_approve_intake=True,
                sandbox_end_to_end=True,
                outbox_root_override=str(outbox),
                notifications_enabled=True,
            )

            # Verify orchestrator succeeded
            self.assertTrue(result.get("ok"))
            self.assertEqual(result.get("final_status"), "sandbox_e2e_complete")

            # Verify delivery.bundle_ready event was emitted
            events = self._find_notification_events(outbox, "delivery.bundle_ready")
            self.assertGreaterEqual(
                len(events),
                1,
                "Expected at least one delivery.bundle_ready event",
            )

            # Verify event structure
            event = events[0]
            self.assertIn("event_id", event)
            self.assertIn("emitted_at", event)
            self.assertEqual(event.get("case_ref"), "additional_demo")
            self.assertIn("artifacts", event)
            self.assertIn("manifest_path", event["artifacts"])
            self.assertIn("bundle_dir", event["artifacts"])

            # Verify JSONL also contains the event
            jsonl_events = self._read_jsonl_events(outbox)
            bundle_events = [e for e in jsonl_events if e.get("event_type") == "delivery.bundle_ready"]
            self.assertGreaterEqual(len(bundle_events), 1)

    def test_disable_notifications_no_events_emitted(self) -> None:
        """AC-2: notifications disabled → no intake.gate_decision or delivery.bundle_ready."""
        snap = _clear_notification_env()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                outbox = Path(tmp) / "outbox"
                result = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _ADDITIONAL_DEMO,
                    mode="run",
                    auto_approve_intake=True,
                    sandbox_end_to_end=True,
                    outbox_root_override=str(outbox),
                    notifications_enabled=False,  # Disabled
                )

                # Verify orchestrator still succeeded (fail-open)
                self.assertTrue(result.get("ok"))
                self.assertEqual(result.get("final_status"), "sandbox_e2e_complete")

                # Verify no notification events were written
                notifications_dir = outbox / "notifications"
                if notifications_dir.exists():
                    event_files = list(notifications_dir.rglob("*.json"))
                    self.assertEqual(
                        len(event_files),
                        0,
                        f"Expected no notification files when disabled, found: {event_files}",
                    )

                # Verify JSONL does not exist or is empty
                jsonl_path = outbox / "notification_events.jsonl"
                if jsonl_path.exists():
                    content = jsonl_path.read_text(encoding="utf-8").strip()
                    self.assertEqual(
                        content,
                        "",
                        "Expected empty JSONL when notifications disabled",
                    )

                # Specifically verify no intake.gate_decision or delivery.bundle_ready
                intake_events = self._find_notification_events(outbox, "intake.gate_decision")
                bundle_events = self._find_notification_events(outbox, "delivery.bundle_ready")
                self.assertEqual(len(intake_events), 0, "Expected no intake.gate_decision when disabled")
                self.assertEqual(len(bundle_events), 0, "Expected no delivery.bundle_ready when disabled")
        finally:
            _restore_env(snap)

    def test_notification_failure_does_not_block_orchestrator(self) -> None:
        """AC-3: notification errors fail-open → orchestrator ok stays true."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"

            # Use a read-only outbox path to force write failures (fail-open test)
            # Create a file at the expected directory path to block directory creation
            outbox.mkdir(parents=True, exist_ok=True)
            notifications_file = outbox / "notifications"
            notifications_file.write_text("not_a_directory", encoding="utf-8")

            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
                notifications_enabled=True,
            )

            # Verify orchestrator still succeeded despite notification write failure
            self.assertTrue(
                result.get("ok"),
                "Orchestrator should succeed even when notifications fail to write",
            )

            # Verify notifications list in result may show failure but doesn't block
            # The result should still have the basic structure
            self.assertIn("notifications", result)
            # Some notification attempts may have been recorded with ok=False
            # or the list may be empty if the failure happened before tracking

    def test_notification_events_tracked_in_result(self) -> None:
        """Verify notification events are tracked in result['notifications'] list."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self.cli.run_agent_standard_case_experiment(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                auto_approve_intake=True,
                outbox_root_override=str(outbox),
                notifications_enabled=True,
            )

            # Verify notifications list exists
            notifications = result.get("notifications")
            self.assertIsInstance(notifications, list)

            # Should have at least intake.gate_decision event tracked
            intake_tracked = [n for n in notifications if n.get("event_type") == "intake.gate_decision"]
            self.assertGreaterEqual(
                len(intake_tracked),
                1,
                "Expected intake.gate_decision tracked in result['notifications']",
            )

            # Verify tracked notification structure
            for tracked in intake_tracked:
                self.assertIn("event_id", tracked)
                self.assertIn("ok", tracked)


class TestOrchestratorNotificationEnvGate(unittest.TestCase):
    """WD-P7-T1: Environment variable gate tests."""

    @classmethod
    def setUpClass(cls) -> None:
        if not _CLI_PATH.is_file():
            raise unittest.SkipTest(f"missing CLI: {_CLI_PATH}")
        cls.cli = _load_cli_module()

    def _find_notification_events(self, outbox: Path, event_type: str) -> list[dict]:
        events = []
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

    def _read_jsonl_events(self, outbox: Path) -> list[dict]:
        jsonl_path = outbox / "notification_events.jsonl"
        events = []
        if not jsonl_path.exists():
            return events
        try:
            with jsonl_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            pass
        return events

    def test_env_gate_enables_notifications(self) -> None:
        """GOV_NOTIFICATION_GATEWAY_ENABLED=1 enables notifications without CLI flag."""
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"

            with mock.patch.dict(os.environ, {"GOV_NOTIFICATION_GATEWAY_ENABLED": "1"}):
                result = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _DEMO_PHASE,
                    mode="run",
                    auto_approve_intake=True,
                    outbox_root_override=str(outbox),
                    notifications_enabled=False,
                )

            self.assertTrue(result.get("ok"))

            events = self._find_notification_events(outbox, "intake.gate_decision")
            self.assertGreaterEqual(
                len(events),
                1,
                "env-only gate should emit intake.gate_decision to outbox",
            )
            jsonl_events = self._read_jsonl_events(outbox)
            intake_jsonl = [
                e for e in jsonl_events if e.get("event_type") == "intake.gate_decision"
            ]
            self.assertGreaterEqual(len(intake_jsonl), 1)

    def test_cli_flag_overrides_env_disable(self) -> None:
        """--enable-notifications flag works independently."""
        snap = _clear_notification_env()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                outbox = Path(tmp) / "outbox"

                # Env var not set, but CLI flag enabled
                result = self.cli.run_agent_standard_case_experiment(
                    "tabular.cleaning.mvp",
                    _DEMO_PHASE,
                    mode="run",
                    auto_approve_intake=True,
                    outbox_root_override=str(outbox),
                    notifications_enabled=True,  # CLI flag on
                )

                # Verify orchestrator succeeded
                self.assertTrue(result.get("ok"))

                # Verify notifications were emitted
                notifications_dir = outbox / "notifications"
                self.assertTrue(
                    notifications_dir.exists() or (outbox / "notification_events.jsonl").exists(),
                    "Expected notifications to be emitted when CLI flag enabled",
                )
        finally:
            _restore_env(snap)


if __name__ == "__main__":
    unittest.main()
