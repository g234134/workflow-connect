"""Unit tests for WC-T2 ticket comms (message generator + sender + transition hook)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from dispatch_executor import parse_ticket_state_markdown  # noqa: E402
from ticket_comms.message_generator import (  # noqa: E402
    SCHEMA_VERSION,
    TicketStateSnapshot,
    build_comms_payload,
    compute_state_diff,
    snapshot_from_ticket_record,
)
from ticket_comms.sender import FileLogSender, NullSender  # noqa: E402
from ticket_comms.transition import emit_ticket_comms_on_change  # noqa: E402

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "dispatch"


def _snap(
    ticket_id: str = "TEST-1",
    overall_status: str = "in_progress",
    current_owner: str | None = "implementer",
    **kwargs: object,
) -> TicketStateSnapshot:
    return TicketStateSnapshot(
        ticket_id=ticket_id,
        title=str(kwargs.get("title", "Sample ticket")),
        overall_status=overall_status,
        current_owner=current_owner,
        implementation_status=kwargs.get("implementation_status"),  # type: ignore[arg-type]
        next_action=kwargs.get("next_action"),  # type: ignore[arg-type]
        status_by_role=dict(kwargs.get("status_by_role") or {}),  # type: ignore[arg-type]
        source_path=str(kwargs.get("source_path", f"04_Workflows/tickets/{ticket_id}_state.md")),
    )


class TestStateDiff(unittest.TestCase):
    def test_no_change_returns_empty_diff(self) -> None:
        snap = _snap()
        diff = compute_state_diff(snap, snap)
        self.assertFalse(diff.has_changes())
        self.assertEqual(diff.changed_fields, [])

    def test_detects_overall_status_and_owner(self) -> None:
        before = _snap(overall_status="in_progress", current_owner="implementer")
        after = _snap(overall_status="review", current_owner="reviewer")
        diff = compute_state_diff(before, after)
        self.assertEqual(diff.changed_fields, ["overall_status", "current_owner"])
        self.assertEqual(diff.before["overall_status"], "in_progress")
        self.assertEqual(diff.after["overall_status"], "review")

    def test_detects_status_by_role_change(self) -> None:
        before = _snap(status_by_role={"implementer": "in_progress"})
        after = _snap(status_by_role={"implementer": "done"})
        diff = compute_state_diff(before, after)
        self.assertIn("status_by_role", diff.changed_fields)


class TestMessageGenerator(unittest.TestCase):
    def test_build_payload_shape(self) -> None:
        before = _snap(overall_status="in_progress", current_owner="implementer")
        after = _snap(overall_status="review", current_owner="reviewer")
        diff = compute_state_diff(before, after)
        payload = build_comms_payload(after, diff, generated_at="2026-06-13T00:00:00Z")

        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertEqual(payload["ticket_id"], "TEST-1")
        self.assertIn("title", payload)
        self.assertIn("summary", payload)
        self.assertIn("ticket_ref", payload)
        self.assertEqual(payload["status"]["before"]["overall_status"], "in_progress")
        self.assertEqual(payload["status"]["after"]["overall_status"], "review")
        self.assertEqual(payload["changed_fields"], ["overall_status", "current_owner"])
        self.assertEqual(payload["generated_at"], "2026-06-13T00:00:00Z")

    def test_summary_mentions_status_transition(self) -> None:
        before = _snap(overall_status="draft")
        after = _snap(overall_status="in_progress")
        diff = compute_state_diff(before, after)
        payload = build_comms_payload(after, diff)
        self.assertIn("in progress", payload["summary"].lower())
        self.assertIn("TEST-1", payload["summary"])

    def test_snapshot_from_ticket_record_fixture(self) -> None:
        text = (_FIXTURES / "in_review_ticket.md").read_text(encoding="utf-8")
        rec = parse_ticket_state_markdown(text, "in_review_ticket.md")
        snap = snapshot_from_ticket_record(rec)
        self.assertEqual(snap.ticket_id, "TEST-REV")
        self.assertEqual(snap.overall_status, "in_progress")
        self.assertEqual(snap.current_owner, "reviewer")


class TestSender(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.outbox = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_null_sender_dry_run(self) -> None:
        result = NullSender().send({"ticket_id": "T-1", "summary": "x"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "null")

    def test_file_log_sender_appends_jsonl(self) -> None:
        sender = FileLogSender(self.outbox)
        payload = {"ticket_id": "T-2", "summary": "blocked"}
        result = sender.send(payload)
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "file_log")

        log_path = self.outbox / "ticket_comms.jsonl"
        self.assertTrue(log_path.is_file())
        line = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertTrue(line["simulated"])
        self.assertFalse(line["external_dispatch"])
        self.assertEqual(line["payload"]["ticket_id"], "T-2")


class TestTransitionHook(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.outbox = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_no_change_skips_send(self) -> None:
        snap = _snap()
        result = emit_ticket_comms_on_change(snap, snap, dry_run=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["message"], "no_state_change")
        self.assertFalse(result["sent"])
        self.assertIsNone(result["payload"])

    def test_mismatch_ticket_id_fails(self) -> None:
        result = emit_ticket_comms_on_change(
            _snap(ticket_id="A"),
            _snap(ticket_id="B"),
            dry_run=True,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "ticket_id_mismatch")

    def test_emit_writes_on_status_change(self) -> None:
        before = _snap(overall_status="in_progress")
        after = _snap(overall_status="done", current_owner="scribe")
        result = emit_ticket_comms_on_change(
            before,
            after,
            outbox_dir=str(self.outbox),
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["sent"])
        self.assertIsNotNone(result["payload"])
        self.assertEqual(result["payload"]["status"]["after"]["overall_status"], "done")
        self.assertTrue((self.outbox / "ticket_comms.jsonl").is_file())

    def test_blocked_transition_from_fixture(self) -> None:
        text = (_FIXTURES / "blocked_ticket.md").read_text(encoding="utf-8")
        rec = parse_ticket_state_markdown(text, "blocked_ticket.md")
        before_snap = snapshot_from_ticket_record(rec)
        after_snap = snapshot_from_ticket_record(rec)
        after_snap = TicketStateSnapshot(
            ticket_id=after_snap.ticket_id,
            title=after_snap.title,
            overall_status="in_progress",
            current_owner="implementer",
            source_path=after_snap.source_path,
            status_by_role=dict(after_snap.status_by_role),
        )
        result = emit_ticket_comms_on_change(before_snap, after_snap, dry_run=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["sent"])
        self.assertIn("blocked", result["payload"]["summary"].lower())


if __name__ == "__main__":
    unittest.main()
