"""Thin structure checks for phase2-index-obs-footnote-v1 (P2-INDEX-OBS-FOOTNOTE-v1).

Doc/footnote only: no live PG/Qdrant; no agent_runs wiring.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FOOTNOTE = _REPO_ROOT / "docs" / "phase2-index-obs-footnote-v1.md"
_GAP_AUDIT = _REPO_ROOT / "docs" / "phase2-index-contract-gap-audit-v1.md"
_CONTRACT = _REPO_ROOT / "docs" / "phase2-knowledge-indexing-contract-v1.md"
_OBS = _REPO_ROOT / "docs" / "observability.md"
_HOOK = _REPO_ROOT / "docs" / "phase2-index-job-hook-v1.md"
_TICKET_STATE = (
    _REPO_ROOT / "04_Workflows" / "tickets" / "P2-INDEX-OBS-FOOTNOTE-v1_state.md"
)
_WORKFLOW_INDEX = _REPO_ROOT / "04_Workflows" / "WORKFLOW_INDEX.md"

_REQUIRED_MARKERS = (
    "GAP-OBS-INDEX",
    "run_id",
    "agent_runs",
    "index_cases",
    "non_claims",
    "phase2-index-obs-footnote-v1",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing required file: {path.relative_to(_REPO_ROOT)}")
    return path.read_text(encoding="utf-8")


class TestPhase2IndexObsFootnoteV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.footnote = _read(_FOOTNOTE)
        cls.gap_audit = _read(_GAP_AUDIT)
        cls.contract = _read(_CONTRACT)
        cls.observability = _read(_OBS)
        cls.hook = _read(_HOOK)

    def test_footnote_file_exists(self) -> None:
        self.assertTrue(_FOOTNOTE.is_file())

    def test_footnote_required_markers(self) -> None:
        missing = [m for m in _REQUIRED_MARKERS if m not in self.footnote]
        self.assertEqual(missing, [], f"footnote missing markers: {missing}")

    def test_non_claims_reject_wiring_and_phase_pct(self) -> None:
        self.assertIn("≠", self.footnote)
        self.assertIn("apply_phase_pct", self.footnote)
        self.assertIn("false", self.footnote)
        self.assertIn("WORKFLOW_INDEX", self.footnote)

    def test_cross_refs_point_to_footnote(self) -> None:
        needle = "phase2-index-obs-footnote-v1"
        for name, text in (
            ("gap_audit", self.gap_audit),
            ("contract", self.contract),
            ("observability", self.observability),
            ("hook", self.hook),
        ):
            with self.subTest(doc=name):
                self.assertIn(needle, text)

    def test_gap_audit_gap_obs_index_row_updated(self) -> None:
        self.assertIn("GAP-OBS-INDEX", self.gap_audit)
        self.assertIn("P2-INDEX-OBS-FOOTNOTE-v1", self.gap_audit)

    def test_ticket_state_exists(self) -> None:
        self.assertTrue(_TICKET_STATE.is_file())

    def test_no_windows_drive_absolute_paths_in_footnote(self) -> None:
        # Forbid machine-local absolute paths (drive letter); allow repo-relative only.
        self.assertNotRegex(self.footnote, r"[A-Za-z]:\\")

    def test_workflow_index_not_required_to_mention_this_ticket(self) -> None:
        """R4 defer: this ticket must not rewrite INDEX; presence is optional."""
        self.assertTrue(_WORKFLOW_INDEX.is_file())


if __name__ == "__main__":
    unittest.main()
