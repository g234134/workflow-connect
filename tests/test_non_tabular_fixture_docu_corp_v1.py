"""Unit tests for NT-A docu-corp fixture (W9-T5)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CASE_DIR = "cases/docu-corp/2026-0001"
_CASE_PATH = _REPO_ROOT / _CASE_DIR
_INTAKE_PATH = _CASE_PATH / "intake.json"
_RAW_DOCUMENTS = _CASE_PATH / "raw" / "documents"

_REQUIRED_INTAKE_KEYS = (
    "client_ref",
    "case_id",
    "content_type",
    "schema_hint",
    "sensitivity",
)

_NT_A_TASK_TYPES = (
    "non_tabular.document.extract",
    "non-tabular.document.clean_and_annotate",
)


def _load_intake() -> dict:
    return json.loads(_INTAKE_PATH.read_text(encoding="utf-8"))


class TestNonTabularFixtureDocuCorpV1(unittest.TestCase):
    def test_case_directory_structure(self) -> None:
        self.assertTrue(_CASE_PATH.is_dir(), f"missing case dir: {_CASE_DIR}")
        self.assertTrue(_INTAKE_PATH.is_file(), "intake.json must exist")
        self.assertTrue(_RAW_DOCUMENTS.is_dir(), "raw/documents/ must exist")

    def test_raw_documents_has_readable_sample(self) -> None:
        samples = [
            p
            for p in _RAW_DOCUMENTS.iterdir()
            if p.is_file() and p.suffix.lower() in {".txt", ".md", ".markdown"}
        ]
        self.assertGreaterEqual(len(samples), 1, "need >=1 text/markdown sample")
        content = samples[0].read_text(encoding="utf-8")
        self.assertGreater(len(content.strip()), 20)

    def test_intake_required_keys_and_values(self) -> None:
        intake = _load_intake()
        for key in _REQUIRED_INTAKE_KEYS:
            self.assertIn(key, intake, f"missing intake key: {key}")

        self.assertEqual(intake["client_ref"], "docu-corp")
        self.assertEqual(intake["case_id"], "docu-2026-0001")
        self.assertEqual(intake["content_type"], "mixed_documents")
        self.assertEqual(intake["schema_hint"], "schema-free")
        self.assertIn(intake["sensitivity"], {"public", "internal", "confidential"})

        data_source = intake.get("data_source", "")
        self.assertTrue(
            data_source.startswith("raw/documents/"),
            f"data_source should follow catalog convention, got {data_source!r}",
        )

    def test_v2_decision_nt_a_shadow_needs_review(self) -> None:
        for task_type in _NT_A_TASK_TYPES:
            with self.subTest(task_type=task_type):
                result = evaluate_intake_decision_v2(task_type, _CASE_DIR)
                self.assertTrue(result["ok"], result.get("message"))
                self.assertEqual(result["flow_family"], "non_tabular")
                self.assertEqual(result["fixture_profile_tier"], "NT-A")
                self.assertEqual(result["case_profile_tier"], "NT-A")
                self.assertEqual(result["decision"], "needs_review")
                self.assertEqual(result["risk_level"], "medium")
                self.assertIn(
                    "document_extraction_profile",
                    result["signals"]["medium"],
                )
                hook = result.get("shadow_flow_hook") or {}
                self.assertTrue(hook.get("eligible"))


if __name__ == "__main__":
    unittest.main()
