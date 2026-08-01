"""Unit tests for 04_Workflows/dispatch_executor (W-next control plane MVP)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from dispatch_executor import (  # noqa: E402
    build_dispatch_plan,
    classify_ticket,
    parse_ticket_state_markdown,
    recommend_role,
    scan_ticket_files,
)

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "dispatch"


class TestDispatchParsing(unittest.TestCase):
    def test_parse_blocked_fixture(self) -> None:
        text = (_FIXTURES / "blocked_ticket.md").read_text(encoding="utf-8")
        rec = parse_ticket_state_markdown(text, "blocked_ticket.md")
        self.assertEqual(rec.ticket_id, "TEST-BLK")
        self.assertEqual(rec.overall_status, "blocked")
        self.assertEqual(rec.current_owner, "implementer")
        self.assertIn("W9-T9", rec.dependencies)
        self.assertEqual(rec.confidence["overall_status"], "high")

    def test_parse_in_review_fixture(self) -> None:
        text = (_FIXTURES / "in_review_ticket.md").read_text(encoding="utf-8")
        rec = parse_ticket_state_markdown(text, "in_review_ticket.md")
        self.assertEqual(rec.implementation_status, "in_review")
        self.assertEqual(rec.current_owner, "reviewer")
        self.assertTrue(rec.verification_commands)

    def test_blocked_not_runnable(self) -> None:
        text = (_FIXTURES / "blocked_ticket.md").read_text(encoding="utf-8")
        rec = parse_ticket_state_markdown(text, "blocked_ticket.md")
        bucket = classify_ticket(rec, done_ids=set())
        self.assertEqual(bucket, "blocked")
        role, _ = recommend_role(rec, bucket)
        self.assertIsNone(role)

    def test_in_review_routes_reviewer(self) -> None:
        text = (_FIXTURES / "in_review_ticket.md").read_text(encoding="utf-8")
        rec = parse_ticket_state_markdown(text, "in_review_ticket.md")
        bucket = classify_ticket(rec, done_ids=set())
        self.assertEqual(bucket, "in_review")
        role, reason = recommend_role(rec, bucket)
        self.assertEqual(role, "reviewer")
        self.assertIn("reviewer", reason.lower())

    def test_done_scribe_suggestion(self) -> None:
        text = (_FIXTURES / "scribe_done_ticket.md").read_text(encoding="utf-8")
        rec = parse_ticket_state_markdown(text, "scribe_done_ticket.md")
        bucket = classify_ticket(rec, done_ids={"TEST-SCR"})
        self.assertEqual(bucket, "done")
        role, reason = recommend_role(rec, bucket)
        self.assertEqual(role, "scribe")
        self.assertIn("scribe", reason.lower())


class TestDispatchLiveScan(unittest.TestCase):
    def test_scan_repo_tickets(self) -> None:
        tickets_dir = _REPO_ROOT / "04_Workflows" / "tickets"
        records, warnings = scan_ticket_files(tickets_dir)
        self.assertGreater(len(records), 5)
        ids = {r.ticket_id for r in records}
        self.assertIn("W1-T1", ids)
        self.assertIn("W1-T2", ids)
        self.assertNotIn("_templates", warnings)

    def test_build_plan_classifies_w1_tickets(self) -> None:
        plan = build_dispatch_plan(_REPO_ROOT, ticket_filter="W1-T")
        self.assertTrue(plan["ok"])
        done_ids = {t["ticket_id"] for t in plan["done"]}
        in_review_ids = {t["ticket_id"] for t in plan["in_review"]}
        self.assertIn("W1-T2", done_ids)
        self.assertIn("W1-T1", in_review_ids)
        w1t2_runnable = [t for t in plan["runnable_now"] if t["ticket_id"] == "W1-T2"]
        self.assertEqual(w1t2_runnable, [])
        suggestions = {s["ticket_id"]: s for s in plan["suggested_next"]}
        self.assertEqual(suggestions["W1-T1"]["recommended_role"], "reviewer")
        self.assertEqual(suggestions["W1-T2"]["recommended_role"], "scribe")


if __name__ == "__main__":
    unittest.main()
