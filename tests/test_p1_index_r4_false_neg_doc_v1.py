"""Thin structure checks for P1-INDEX-R4-FALSE-NEG-DOC-v1 (INDEX false-negative light fix).

Doc-only: no DarkOps unlock; no Phase% apply; no formal GraphRAG smoke runbook claim.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC = _REPO_ROOT / "docs" / "p1-index-r4-false-neg-doc-v1.md"
_CHECKOFF = _REPO_ROOT / "docs" / "p1-gov-residual-checkoff-v1.md"
_INDEX = _REPO_ROOT / "04_Workflows" / "WORKFLOW_INDEX.md"
_TICKET = (
    _REPO_ROOT / "04_Workflows" / "tickets" / "P1-INDEX-R4-FALSE-NEG-DOC-v1_state.md"
)
_RAG_RUNBOOK = (
    _REPO_ROOT / "04_Workflows" / "runbooks" / "RAG_SMOKE_TEST_RUNBOOK_v0.1.md"
)
_GRAPH_THIN = _REPO_ROOT / "docs" / "phase2-graphrag-thin-runner-v1.md"

_DOC_MARKERS = (
    "FN-1",
    "FN-2",
    "FN-3",
    "non_claims",
    "apply_phase_pct",
    "RAG_SMOKE_TEST_RUNBOOK",
    "phase2-graphrag-thin-runner-v1",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing required file: {path.relative_to(_REPO_ROOT)}")
    return path.read_text(encoding="utf-8")


def _section_2_1(index_text: str) -> str:
    m = re.search(
        r"### 2\.1 GraphRAG Job Smoke Test.*?(?=\n### 2\.2 |\n## 3\. |\Z)",
        index_text,
        flags=re.DOTALL,
    )
    if not m:
        raise AssertionError("WORKFLOW_INDEX.md missing §2.1 GraphRAG section")
    return m.group(0)


class TestP1IndexR4FalseNegDocV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = _read(_DOC)
        cls.checkoff = _read(_CHECKOFF)
        cls.index = _read(_INDEX)
        cls.section_2_1 = _section_2_1(cls.index)

    def test_doc_and_deps_exist(self) -> None:
        self.assertTrue(_DOC.is_file())
        self.assertTrue(_TICKET.is_file())
        self.assertTrue(_RAG_RUNBOOK.is_file())
        self.assertTrue(_GRAPH_THIN.is_file())

    def test_doc_required_markers(self) -> None:
        missing = [m for m in _DOC_MARKERS if m not in self.doc]
        self.assertEqual(missing, [], f"doc missing markers: {missing}")

    def test_section_2_1_no_stale_rag_todo(self) -> None:
        stale = "待完成 RAG_Smoke_Test v0.1"
        self.assertNotIn(stale, self.section_2_1)
        self.assertNotIn("待完成 RAG_Smoke_Test", self.section_2_1)

    def test_section_2_1_points_to_rag_and_thin(self) -> None:
        self.assertIn("RAG_SMOKE_TEST_RUNBOOK_v0.1.md", self.section_2_1)
        self.assertIn("phase2-graphrag-thin-runner-v1.md", self.section_2_1)
        self.assertIn("P1-INDEX-R4-FALSE-NEG-DOC-v1", self.section_2_1)

    def test_checkoff_r4_done(self) -> None:
        # Row R4 must be done and cite this ticket (not explicit defer).
        self.assertRegex(
            self.checkoff,
            r"\|\s*R4\s*\|[^|]*\|\s*\*\*done\*\*\s*\|",
        )
        self.assertIn("P1-INDEX-R4-FALSE-NEG-DOC-v1", self.checkoff)
        # Guard: R4 note must not still say explicit defer as Verdict.
        r4_line = next(
            (ln for ln in self.checkoff.splitlines() if ln.strip().startswith("| R4 ")),
            "",
        )
        self.assertIn("**done**", r4_line)
        self.assertNotIn("explicit defer", r4_line)

    def test_apply_phase_pct_false_in_doc(self) -> None:
        self.assertIn("apply_phase_pct", self.doc)
        self.assertIn("false", self.doc.lower())

    def test_no_windows_drive_absolute_paths_in_doc(self) -> None:
        self.assertNotRegex(self.doc, r"[A-Za-z]:\\")


if __name__ == "__main__":
    unittest.main()
