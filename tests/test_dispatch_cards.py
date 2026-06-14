"""Unit tests for 04_Workflows/_dispatch_cards (W-next DISPATCH-CARDS-MVP)."""



from __future__ import annotations



import json

import sys

import tempfile

import time

import unittest

from pathlib import Path



_REPO_ROOT = Path(__file__).resolve().parents[1]

_WORKFLOWS = _REPO_ROOT / "04_Workflows"

if str(_WORKFLOWS) not in sys.path:

    sys.path.insert(0, str(_WORKFLOWS))



from _dispatch_cards import (  # noqa: E402

    generate_cards,

    load_plan,

    parse_ticket_frame,

    render_card_markdown,

    select_tickets,

)



_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "dispatch"





class TestDispatchCardsSelection(unittest.TestCase):

    def test_select_runnable_and_draft(self) -> None:

        plan = load_plan(_FIXTURES / "sample_plan.json")

        entries, _ = select_tickets(plan, role="implementer", limit=5)

        ids = {e["ticket_id"] for e in entries}

        self.assertIn("CARD-GOOD", ids)

        self.assertIn("CARD-WARN", ids)



    def test_role_filter_excludes_scribe(self) -> None:

        plan = load_plan(_FIXTURES / "sample_plan.json")

        entries, _ = select_tickets(plan, role="scribe", limit=5)

        self.assertEqual(entries, [])





class TestDispatchCardsGeneration(unittest.TestCase):

    def setUp(self) -> None:

        self._tmp = tempfile.TemporaryDirectory()

        self.out_dir = Path(self._tmp.name) / "cards"



    def tearDown(self) -> None:

        self._tmp.cleanup()



    def _write_fixture_states(self, tmp_repo: Path) -> None:

        tickets_dir = tmp_repo / "04_Workflows" / "tickets"

        tickets_dir.mkdir(parents=True)

        for name in ("card_ticket_good.md", "card_ticket_no_paths.md"):

            src = _FIXTURES / name

            tid = name.replace("card_ticket_", "").replace(".md", "")

            ticket_name = "CARD-GOOD" if "good" in name else "CARD-WARN"

            (tickets_dir / f"{ticket_name}_state.md").write_text(

                src.read_text(encoding="utf-8"),

                encoding="utf-8",

            )



    def test_happy_path_writes_card_with_provenance(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            tmp_repo = Path(tmp)

            self._write_fixture_states(tmp_repo)

            plan_path = _FIXTURES / "sample_plan.json"

            out_dir = tmp_repo / "artifacts" / "control_plane" / "cards"



            summary = generate_cards(

                tmp_repo,

                plan_path=plan_path,

                out_dir=out_dir,

                role="implementer",

                limit=5,

                dry_run=False,

            )

            self.assertGreaterEqual(summary["cards_generated"], 1)



            card_path = out_dir / "CARD-GOOD__implementer.cursor.md"

            self.assertTrue(card_path.is_file())

            text = card_path.read_text(encoding="utf-8")

            self.assertIn("source_path", text)

            self.assertIn("generated_at", text)

            self.assertIn("`tests/fixtures/dispatch/**`", text)

            self.assertIn("`core/**`", text)

            self.assertIn("python -m unittest tests.test_dispatch_cards -v", text)



    def test_parse_warning_in_card(self) -> None:

        frame = parse_ticket_frame(

            _FIXTURES / "card_ticket_no_paths.md",

            repo_root=_REPO_ROOT,

        )

        self.assertTrue(any("AllowedPaths" in w for w in frame["parse_warnings"]))



        from _dispatch_cards import DispatchCardInput, build_card_input



        entry = {

            "ticket_id": "CARD-WARN",

            "bucket": "draft",

            "reason": "test",

            "recommended_role": "implementer",

            "commands": [],

            "expected_output": "",

            "source_path": "tests/fixtures/dispatch/card_ticket_no_paths.md",

            "title": "CARD-WARN",

        }

        card_in = build_card_input(

            entry,

            frame,

            plan_snapshot="tests/fixtures/dispatch/sample_plan.json",

            generated_at="2026-06-07T12:00:00+00:00",

        )

        md = render_card_markdown(card_in, generated_at="2026-06-07T12:00:00+00:00")

        self.assertIn("[parse_warning]", md)



    def test_dry_run_writes_no_files(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            tmp_repo = Path(tmp)

            self._write_fixture_states(tmp_repo)

            out_dir = tmp_repo / "artifacts" / "control_plane" / "cards"



            summary = generate_cards(

                tmp_repo,

                plan_path=_FIXTURES / "sample_plan.json",

                out_dir=out_dir,

                role="implementer",

                limit=5,

                dry_run=True,

            )

            self.assertTrue(summary["dry_run"])

            self.assertGreaterEqual(summary["cards_generated"], 1)

            self.assertFalse(any(out_dir.glob("*.cursor.md")))



    def test_ticket_state_mtime_unchanged(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            tmp_repo = Path(tmp)

            self._write_fixture_states(tmp_repo)

            state_path = tmp_repo / "04_Workflows" / "tickets" / "CARD-GOOD_state.md"

            mtime_before = state_path.stat().st_mtime

            time.sleep(0.05)



            generate_cards(

                tmp_repo,

                plan_path=_FIXTURES / "sample_plan.json",

                out_dir=tmp_repo / "cards",

                role="implementer",

                limit=1,

                dry_run=False,

            )

            mtime_after = state_path.stat().st_mtime

            self.assertEqual(mtime_before, mtime_after)





class TestDispatchCardsEligibilityGate(unittest.TestCase):

    """WC-T1-INTEGRATION: eligibility gate on generate_cards (entry A)."""

    def setUp(self) -> None:

        self._tmp = tempfile.TemporaryDirectory()

        self.tmp_repo = Path(self._tmp.name)

        tickets_dir = self.tmp_repo / "04_Workflows" / "tickets"

        tickets_dir.mkdir(parents=True)

        blocked_src = _FIXTURES / "blocked_ticket.md"

        (tickets_dir / "TEST-BLK_state.md").write_text(

            blocked_src.read_text(encoding="utf-8"),

            encoding="utf-8",

        )

        self.plan_path = _FIXTURES / "blocked_plan.json"

        self.out_dir = self.tmp_repo / "artifacts" / "control_plane" / "cards"



    def tearDown(self) -> None:

        self._tmp.cleanup()



    def _run(self, *, gate: str, force: bool = False, dry_run: bool = True) -> dict:

        return generate_cards(

            self.tmp_repo,

            plan_path=self.plan_path,

            out_dir=self.out_dir,

            role="implementer",

            limit=5,

            ticket_id="TEST-BLK",

            dry_run=dry_run,

            eligibility_gate=gate,

            force_eligibility=force,

        )



    def test_gate_block_skips_ineligible_ticket(self) -> None:

        summary = self._run(gate="block")

        self.assertEqual(summary["cards_generated"], 0)

        self.assertEqual(summary["cards_skipped"], 1)

        self.assertEqual(summary["eligibility_gate"], "block")

        blocked = summary["eligibility_blocked"]

        self.assertEqual(len(blocked), 1)

        self.assertEqual(blocked[0]["ticket_id"], "TEST-BLK")

        self.assertIn("overall_status_blocked", blocked[0]["reasons"])

        self.assertTrue(any("eligibility_blocked:TEST-BLK" in w for w in summary["warnings"]))



    def test_gate_off_generates_despite_ineligible(self) -> None:

        summary = self._run(gate="off", dry_run=False)

        self.assertEqual(summary["cards_generated"], 1)

        self.assertEqual(summary["eligibility_gate"], "off")

        self.assertEqual(summary.get("eligibility_blocked", []), [])

        card_path = self.out_dir / "TEST-BLK__implementer.cursor.md"

        self.assertTrue(card_path.is_file())

        self.assertNotIn("eligibility_warning", card_path.read_text(encoding="utf-8"))



    def test_gate_warn_generates_with_warning(self) -> None:

        summary = self._run(gate="warn", dry_run=False)

        self.assertEqual(summary["cards_generated"], 1)

        self.assertEqual(summary["eligibility_gate"], "warn")

        self.assertEqual(summary.get("eligibility_blocked", []), [])

        self.assertTrue(any("eligibility_warn:TEST-BLK" in w for w in summary["warnings"]))

        card_record = summary["cards"][0]

        self.assertIn("eligibility_warnings", card_record)

        self.assertIn("overall_status_blocked", card_record["eligibility_warnings"])

        card_path = self.out_dir / "TEST-BLK__implementer.cursor.md"

        text = card_path.read_text(encoding="utf-8")

        self.assertIn("eligibility_warning", text)

        self.assertIn("overall_status_blocked", text)



    def test_force_eligibility_override_in_block_mode(self) -> None:

        summary = self._run(gate="block", force=True, dry_run=False)

        self.assertEqual(summary["cards_generated"], 1)

        self.assertEqual(summary["cards_skipped"], 0)

        self.assertTrue(summary.get("eligibility_override"))

        self.assertIn("TEST-BLK", summary.get("eligibility_overridden_tickets", []))

        self.assertEqual(summary.get("eligibility_blocked", []), [])

        self.assertTrue(any("eligibility_override:TEST-BLK" in w for w in summary["warnings"]))

        card_path = self.out_dir / "TEST-BLK__implementer.cursor.md"

        text = card_path.read_text(encoding="utf-8")

        self.assertIn("eligibility_override", text)

        card_record = summary["cards"][0]

        self.assertTrue(card_record.get("eligibility_override"))





class TestDispatchCardsLive(unittest.TestCase):

    def test_live_plan_implementer_cards(self) -> None:

        plan_path = _REPO_ROOT / "artifacts" / "control_plane" / "dispatch_plan.latest.json"

        if not plan_path.is_file():

            self.skipTest("dispatch_plan.latest.json missing")

        plan = load_plan(plan_path)

        entries, _ = select_tickets(plan, role="implementer", limit=5)

        self.assertGreaterEqual(len(entries), 1)





if __name__ == "__main__":

    unittest.main()


