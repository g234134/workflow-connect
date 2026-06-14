"""Unit tests for 04_Workflows/ticket_eligibility.py (WC-T1)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from dispatch_executor import parse_ticket_state_markdown  # noqa: E402
from ticket_eligibility import (  # noqa: E402
    EligibilityContext,
    evaluate_ticket_eligibility,
    infer_wave_phase,
)

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "dispatch"


def _load_fixture(name: str):
    text = (_FIXTURES / name).read_text(encoding="utf-8")
    return parse_ticket_state_markdown(text, name)


class TestInferWavePhase(unittest.TestCase):
    def test_wave_b_ticket(self) -> None:
        wave, phase = infer_wave_phase("WB-T4-agent-lines")
        self.assertEqual(wave, "B")
        self.assertEqual(phase, "P8")

    def test_numeric_wave(self) -> None:
        wave, phase = infer_wave_phase("W7-T1-extend-fixtures")
        self.assertEqual(wave, "Wave 7")
        self.assertIsNone(phase)


class TestTicketEligibility(unittest.TestCase):
    def test_eligible_implementer_in_progress(self) -> None:
        rec = _load_fixture("in_review_ticket.md")
        rec.overall_status = "in_progress"
        rec.implementation_status = "pending"
        rec.current_owner = "implementer"
        rec.next_action = "Resume wiring tests"
        result = evaluate_ticket_eligibility(
            rec,
            done_ids=set(),
            context=EligibilityContext(requested_role="implementer"),
        )
        self.assertEqual(result["eligible"], "eligible")
        self.assertIn("bucket_runnable_now", result["reasons"])

    def test_ineligible_blocked_status(self) -> None:
        rec = _load_fixture("blocked_ticket.md")
        result = evaluate_ticket_eligibility(rec, done_ids=set())
        self.assertEqual(result["eligible"], "ineligible")
        self.assertIn("overall_status_blocked", result["reasons"])

    def test_ineligible_unresolved_dependency(self) -> None:
        rec = _load_fixture("blocked_ticket.md")
        rec.overall_status = "in_progress"
        result = evaluate_ticket_eligibility(rec, done_ids=set())
        self.assertEqual(result["eligible"], "ineligible")
        self.assertTrue(any(r.startswith("dependency_unresolved:") for r in result["reasons"]))

    def test_ineligible_done_ticket(self) -> None:
        rec = _load_fixture("scribe_done_ticket.md")
        result = evaluate_ticket_eligibility(
            rec,
            done_ids={"TEST-SCR"},
            context=EligibilityContext(requested_role="implementer"),
        )
        self.assertEqual(result["eligible"], "ineligible")
        self.assertIn("ticket_already_done", result["reasons"])

    def test_ineligible_implementer_during_review_gate(self) -> None:
        rec = _load_fixture("in_review_ticket.md")
        result = evaluate_ticket_eligibility(
            rec,
            done_ids=set(),
            context=EligibilityContext(requested_role="implementer"),
        )
        self.assertEqual(result["eligible"], "ineligible")
        self.assertIn("waiting_reviewer_gate", result["reasons"])

    def test_eligible_reviewer_in_review(self) -> None:
        rec = _load_fixture("in_review_ticket.md")
        result = evaluate_ticket_eligibility(
            rec,
            done_ids=set(),
            context=EligibilityContext(requested_role="reviewer"),
        )
        self.assertEqual(result["eligible"], "eligible")
        self.assertIn("review_gate_active", result["reasons"])

    def test_eligible_scribe_on_done_ticket(self) -> None:
        rec = _load_fixture("scribe_done_ticket.md")
        result = evaluate_ticket_eligibility(
            rec,
            done_ids={"TEST-SCR"},
            context=EligibilityContext(requested_role="scribe"),
        )
        self.assertEqual(result["eligible"], "eligible")
        self.assertIn("done_ticket_pending_scribe", result["reasons"])


class TestTicketEligibilityLiveLoad(unittest.TestCase):
    def test_check_demo_ticket(self) -> None:
        from ticket_eligibility import check_ticket_eligibility  # noqa: E402

        result = check_ticket_eligibility(
            "DEMO-1",
            _REPO_ROOT,
            context={"requested_role": "implementer"},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["eligible"], "ineligible")
        self.assertIn("ticket_already_done", result["reasons"])


if __name__ == "__main__":
    unittest.main()
