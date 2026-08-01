"""Unit tests for Intake Gate notification wiring (P75-G4)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery import notification_gateway_v1 as gw
from delivery.notification_gateway_v1 import EVENT_TYPE_INTAKE_GATE_DECISION
from scripts.run_intake_gate_cli import _maybe_emit_gate_notification

_DEMO_PHASE = "cases/demo_phase"
_CLI = _REPO_ROOT / "scripts" / "run_intake_gate_cli.py"


def _sample_gate_result(*, outbox_record_path: str | None = "outbox/demo_phase/gate.json") -> dict:
    return {
        "ok": True,
        "schema_version": "intake_gate_result_v1",
        "intake_decision_id": "igd_2026-06-19T10-00-00Z_demo_phase_tabular.cleaning.mvp",
        "decision": "review_needed",
        "case_ref": "demo_phase",
        "case_dir": "cases/demo_phase",
        "reason_codes": ["manual_review_required", "allowlist_fixture"],
        "policy_version": "intake_gate_policy_v1",
        "outbox_record_path": outbox_record_path,
    }


class TestIntakeGateDecisionEvent(unittest.TestCase):
    def test_build_intake_gate_decision_event_payload_shape(self) -> None:
        gate = _sample_gate_result()
        event = gw.build_intake_gate_decision_event(gate)

        self.assertEqual(event["event_type"], EVENT_TYPE_INTAKE_GATE_DECISION)
        self.assertEqual(event["case_ref"], "demo_phase")
        self.assertEqual(event["checkpoint_id"], gate["intake_decision_id"])

        artifacts = event["artifacts"]
        self.assertEqual(artifacts["intake_decision_id"], gate["intake_decision_id"])
        self.assertEqual(artifacts["decision"], "review_needed")
        self.assertEqual(artifacts["reason_codes"], gate["reason_codes"])
        self.assertEqual(artifacts["policy_version"], "intake_gate_policy_v1")
        self.assertEqual(artifacts["outbox_record_path"], gate["outbox_record_path"])

        summary = event["status_summary"]
        self.assertEqual(summary["decision"], "review_needed")
        self.assertEqual(summary["reason_codes"], gate["reason_codes"])
        self.assertEqual(summary["policy_version"], "intake_gate_policy_v1")
        self.assertEqual(summary["intake_decision_id"], gate["intake_decision_id"])
        self.assertEqual(summary["outbox_record_path"], gate["outbox_record_path"])


class TestIntakeGateCliNotify(unittest.TestCase):
    def _run_cli(
        self,
        *,
        mode: str,
        extra_args: list[str] | None = None,
        outbox_root: Path,
    ) -> dict:
        cmd = [
            sys.executable,
            str(_CLI),
            "--task-type",
            "tabular.cleaning.mvp",
            "--case-dir",
            _DEMO_PHASE,
            "--mode",
            mode,
            "--format",
            "json",
            "--outbox-root",
            str(outbox_root),
        ]
        if extra_args:
            cmd.extend(extra_args)

        proc = subprocess.run(
            cmd,
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"CLI exit {proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
            )
        return json.loads(proc.stdout)

    def test_gate_run_mode_emits_intake_gate_decision_notification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self._run_cli(
                mode="run",
                extra_args=["--enable-notifications"],
                outbox_root=outbox,
            )

            self.assertTrue(result.get("ok"))
            self.assertIsNotNone(result.get("outbox_record_path"))
            notification = result.get("notification") or {}
            self.assertEqual(notification.get("event_type"), EVENT_TYPE_INTAKE_GATE_DECISION)
            self.assertTrue(notification.get("ok"))

            jsonl_path = outbox / "notification_events.jsonl"
            self.assertTrue(jsonl_path.is_file())
            lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
            self.assertGreaterEqual(len(lines), 1)
            last = json.loads(lines[-1])
            self.assertEqual(last["event_type"], EVENT_TYPE_INTAKE_GATE_DECISION)
            self.assertEqual(last["status_summary"]["decision"], result["decision"])

    def test_gate_preview_mode_does_not_emit_notification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self._run_cli(
                mode="preview",
                extra_args=["--enable-notifications"],
                outbox_root=outbox,
            )

            self.assertTrue(result.get("ok"))
            self.assertIsNone(result.get("outbox_record_path"))
            self.assertNotIn("notification", result)
            self.assertFalse((outbox / "notification_events.jsonl").exists())

    def test_gate_notifications_can_be_disabled_via_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = self._run_cli(mode="run", outbox_root=outbox)

            self.assertTrue(result.get("ok"))
            self.assertIsNotNone(result.get("outbox_record_path"))
            self.assertNotIn("notification", result)
            self.assertFalse((outbox / "notification_events.jsonl").exists())

    def test_notify_failure_does_not_break_gate_result(self) -> None:
        gate = _sample_gate_result()
        with mock.patch.object(
            gw,
            "send_notification",
            return_value={
                "ok": False,
                "message": "write failed",
                "event_id": "evt-fail",
                "sink_result": {"ok": False, "channel": "local_file", "message": "write failed"},
            },
        ):
            notification = _maybe_emit_gate_notification(
                gate,
                mode="run",
                notifications_enabled=True,
                outbox_root=None,
            )

        self.assertIsNotNone(notification)
        assert notification is not None
        self.assertFalse(notification["ok"])
        self.assertTrue(gate["ok"])


if __name__ == "__main__":
    unittest.main()
