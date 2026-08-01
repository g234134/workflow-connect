"""Unit tests for 04_Workflows/_batch_orchestrator/loader (BATCH-MVP-01)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from _batch_orchestrator.loader import (  # noqa: E402
    load_batch_document,
    load_batch_manifest,
    load_subtask,
)


def _valid_subtask(**overrides):
    payload = {
        "parent_ticket_id": "BATCH-MVP-01",
        "subtask_id": "BATCH-MVP-01-S1",
        "subtask_type": "implementer",
        "target_paths": ["04_Workflows/_batch_orchestrator/loader.py"],
        "allowed_paths": ["04_Workflows/_batch_orchestrator/**"],
        "blocked_paths": ["04_Workflows/tickets/*_state.md"],
        "scope_summary": "Implement batch loader MVP",
        "acceptance_checks": ["pytest tests/test_batch_loader.py -q"],
        "priority": 1,
        "dependencies": [],
        "status": "pending",
        "preferred_model": "composer-2.5-fast",
    }
    payload.update(overrides)
    return payload


class TestBatchLoaderValid(unittest.TestCase):
    def test_load_valid_subtask(self) -> None:
        result = load_subtask(_valid_subtask())
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["data"]["kind"], "subtask")
        self.assertEqual(result["data"]["subtask"]["subtask_id"], "BATCH-MVP-01-S1")

    def test_load_valid_manifest(self) -> None:
        manifest = {
            "batch_id": "BATCH-MVP-01",
            "parent_ticket_id": "BATCH-MVP-01",
            "subtasks": [
                _valid_subtask(subtask_id="BATCH-MVP-01-S1", dependencies=[]),
                _valid_subtask(
                    subtask_id="BATCH-MVP-01-S2",
                    subtask_type="reviewer",
                    priority=2,
                    dependencies=["BATCH-MVP-01-S1"],
                    status="pending",
                ),
            ],
        }
        result = load_batch_manifest(manifest)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["kind"], "manifest")
        self.assertEqual(len(result["data"]["subtasks"]), 2)

    def test_load_batch_document_auto_detects_manifest(self) -> None:
        manifest = {
            "batch_id": "BATCH-MVP-01",
            "parent_ticket_id": "BATCH-MVP-01",
            "subtasks": [_valid_subtask()],
        }
        result = load_batch_document(manifest)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["kind"], "manifest")


class TestBatchLoaderMissingFields(unittest.TestCase):
    def test_missing_required_field(self) -> None:
        payload = _valid_subtask()
        del payload["scope_summary"]
        result = load_subtask(payload)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["data"])
        self.assertTrue(any("scope_summary" in err for err in result["errors"]))

    def test_missing_preferred_model(self) -> None:
        payload = _valid_subtask()
        del payload["preferred_model"]
        result = load_subtask(payload)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["data"])
        self.assertTrue(any("preferred_model" in err for err in result["errors"]))

    def test_invalid_json_string(self) -> None:
        result = load_subtask("{not-json")
        self.assertFalse(result["ok"])
        self.assertTrue(any("invalid JSON" in err for err in result["errors"]))


class TestBatchLoaderPreferredModel(unittest.TestCase):
    def test_preferred_model_null_accepted(self) -> None:
        result = load_subtask(_valid_subtask(preferred_model=None))
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertIsNone(result["data"]["subtask"]["preferred_model"])


class TestBatchLoaderEnumValidation(unittest.TestCase):
    def test_invalid_subtask_type(self) -> None:
        result = load_subtask(_valid_subtask(subtask_type="worker"))
        self.assertFalse(result["ok"])
        self.assertTrue(any("subtask_type" in err for err in result["errors"]))

    def test_invalid_status(self) -> None:
        result = load_subtask(_valid_subtask(status="finished"))
        self.assertFalse(result["ok"])
        self.assertTrue(any("status" in err for err in result["errors"]))


class TestBatchLoaderDependencies(unittest.TestCase):
    def test_self_dependency_rejected(self) -> None:
        result = load_subtask(
            _valid_subtask(
                subtask_id="BATCH-MVP-01-S1",
                dependencies=["BATCH-MVP-01-S1"],
            )
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any("must not reference itself" in err for err in result["errors"]))

    def test_unknown_dependency_in_manifest(self) -> None:
        manifest = {
            "batch_id": "BATCH-MVP-01",
            "parent_ticket_id": "BATCH-MVP-01",
            "subtasks": [
                _valid_subtask(
                    subtask_id="BATCH-MVP-01-S2",
                    dependencies=["BATCH-MVP-01-MISSING"],
                )
            ],
        }
        result = load_batch_manifest(manifest)
        self.assertFalse(result["ok"])
        self.assertTrue(
            any("not defined in batch manifest" in err for err in result["errors"])
        )

    def test_parent_ticket_mismatch_in_manifest(self) -> None:
        manifest = {
            "batch_id": "BATCH-MVP-01",
            "parent_ticket_id": "BATCH-MVP-01",
            "subtasks": [
                _valid_subtask(parent_ticket_id="OTHER-TICKET"),
            ],
        }
        result = load_batch_manifest(manifest)
        self.assertFalse(result["ok"])
        self.assertTrue(
            any("parent_ticket_id must match manifest parent_ticket_id" in err for err in result["errors"])
        )


if __name__ == "__main__":
    unittest.main()
