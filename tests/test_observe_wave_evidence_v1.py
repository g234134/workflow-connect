"""Unit tests for wave evidence observer v1 (W5-T3 · read-only skeleton)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.observe_wave_evidence_v1 import (
    observe_wave_evidence,
    main,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


_STATE_WITH_VERIFICATION = """# TICKET STATE · W5-DEMO-ticket-v1

## FRAME
- Goal: demo

## STATE
- overall_status: done

## B_REPORT
- changed_files:
  - docs/demo.md
- artifacts: none
- verification:
  - `python scripts/demo.py` → ok=true
- behavior_notes: n/a
- deferred_items: 無

## C_REPORT
- conclusion: accepted
"""

_STATE_EMPTY_VERIFICATION = """# TICKET STATE · W5-EMPTY-ticket-v1

## B_REPORT
- verification: <!-- Implementer 填：執行 VerificationCommands 結果 -->
- deferred_items: 無

## C_REPORT
- conclusion: pending
"""


class TestObserveWaveEvidenceV1(unittest.TestCase):
    def test_missing_args_returns_ok_false(self) -> None:
        result = observe_wave_evidence()
        self.assertFalse(result["ok"])
        self.assertTrue(any(g.get("gap_reason") == "missing_wave_or_ticket_id" for g in result["gaps"]))

    def test_lists_verification_and_honest_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / "04_Workflows" / "tickets" / "W5-DEMO-ticket-v1_state.md",
                _STATE_WITH_VERIFICATION,
            )
            _write(
                root / "04_Workflows" / "tickets" / "W5-EMPTY-ticket-v1_state.md",
                _STATE_EMPTY_VERIFICATION,
            )
            _write(
                root / "04_Workflows" / "00_Agent_Work_Progress.md",
                "## 2026-07-09 · W5-DEMO-ticket-v1 done\n",
            )
            smoke_dir = root / "outbox" / "verification" / "demo_phase"
            smoke_dir.mkdir(parents=True)
            (smoke_dir / "multi_phase_smoke_run.json").write_text(
                json.dumps({"ok": True, "run_id": "demo-run-1"}),
                encoding="utf-8",
            )

            result = observe_wave_evidence(wave="W5", repo_root=root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["wave"], "W5")
            self.assertEqual(len(result["tickets"]), 2)

            types = {e["evidence_type"] for e in result["evidence_summary"]}
            self.assertIn("b_report_verification", types)
            self.assertIn("multi_phase_smoke_run", types)
            self.assertIn("ga_run_url_placeholder", types)

            # Empty verification → gap, not crash
            self.assertTrue(
                any(
                    g.get("ticket_id") == "W5-EMPTY-ticket-v1"
                    and g.get("gap_reason") == "empty_or_missing_verification"
                    for g in result["gaps"]
                )
            )
            # multi_case missing → honest gap
            self.assertTrue(
                any(
                    g.get("evidence_type") == "multi_case_smoke_run"
                    and g.get("gap_reason") == "artifact_missing"
                    for g in result["gaps"]
                )
            )
            # smoke present
            mp = next(
                e
                for e in result["evidence_summary"]
                if e.get("evidence_type") == "multi_phase_smoke_run"
            )
            self.assertTrue(mp["present"])
            self.assertTrue(mp.get("ok"))

            # human-only URLs never verified
            ga_rows = [
                e
                for e in result["evidence_summary"]
                if e.get("evidence_type") == "ga_run_url_placeholder"
            ]
            self.assertTrue(ga_rows)
            self.assertTrue(all(e.get("verified") is False for e in ga_rows))
            self.assertTrue(all(e.get("human_only") is True for e in ga_rows))

    def test_ticket_id_missing_state_honest_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "04_Workflows" / "tickets").mkdir(parents=True)
            result = observe_wave_evidence(
                ticket_id="W5-DOES-NOT-EXIST",
                repo_root=root,
            )
            self.assertTrue(result["ok"])
            self.assertTrue(
                any(g.get("gap_reason") == "ticket_state_missing" for g in result["gaps"])
            )

    def test_main_json_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "04_Workflows" / "tickets").mkdir(parents=True)
            code = main(["--wave", "W1", "--format", "json", "--repo-root", str(root)])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
