"""Thin tests for P3 Langfuse↔PG align FRAME v1 (doc/spec · no live PG)."""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC = _REPO_ROOT / "docs" / "p3-langfuse-pg-align-frame-v1.md"
_TICKET = (
    _REPO_ROOT
    / "04_Workflows"
    / "tickets"
    / "P3-LANGFUSE-PG-ALIGN-FRAME-v1_state.md"
)
_DEFERRED = _REPO_ROOT / "docs" / "langfuse-pg-alignment-deferred-index-v1.md"
_P1_STUB = (
    _REPO_ROOT
    / "04_Workflows"
    / "tickets"
    / "P1-OPS-CHECKLIST-CLOSURE-v1_state.md"
)

_REQUIRED_SNIPPETS = (
    "non_claims",
    "MVP",
    "stretch",
    "trace_id",
    "D-01",
    "D-04",
    "apply_phase_pct",
    "P3-LANGFUSE-PG-ALIGN-IMPL-v1",
    "P1-OPS-CHECKLIST-CLOSURE-v1",
    "P1-GOV-RESIDUAL-CHECKOFF-v1",
)


class TestP3LangfusePgAlignFrameV1(unittest.TestCase):
    def test_assets_exist(self) -> None:
        for path in (_DOC, _TICKET, _DEFERRED, _P1_STUB):
            self.assertTrue(path.is_file(), msg=f"missing {path}")

    def test_doc_required_sections(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        for snippet in _REQUIRED_SNIPPETS:
            self.assertIn(snippet, text, msg=f"missing snippet: {snippet}")

    def test_doc_forbids_live_pg(self) -> None:
        body = _DOC.read_text(encoding="utf-8")
        self.assertIn("planning", body.lower())
        self.assertTrue(
            ("無真 PG" in body) or ("不連真" in body) or ("真 PostgreSQL" in body),
            msg="FRAME must state no live PG",
        )
        self.assertIn("≠", body)

    def test_p1_stub_superseded(self) -> None:
        stub = _P1_STUB.read_text(encoding="utf-8")
        self.assertIn("superseded", stub)
        self.assertIn("P3-LANGFUSE-PG-ALIGN-FRAME-v1", stub)

    def test_ticket_frame_flags(self) -> None:
        ticket = _TICKET.read_text(encoding="utf-8")
        self.assertIn("apply_phase_pct: false", ticket)
        self.assertIn("doc/spec", ticket)
        self.assertIn("non_claims", ticket)
        self.assertIn("NonScope", ticket)
        self.assertIn("真 PG", ticket)


if __name__ == "__main__":
    unittest.main()
