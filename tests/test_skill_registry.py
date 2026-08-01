"""Tests for Wave 8 approved skill registry (promote-from-queue / list-approved)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "04_Workflows" / "_wave8_skill_card_review_queue.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("wave8_review_queue", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _draft_with_scenarios(*, skill_id: str = "draft-clean-basic-job-001") -> dict:
    return {
        "schema_version": "skill_card_v0.1",
        "card_meta": {
            "skill_id": skill_id,
            "title": "Draft skill for CLEAN-BASIC",
            "confidence_level": "low",
            "review_status": "draft",
            "version": "1.0.0",
        },
        "applicable_scenarios": ["tabular-clean-basic"],
        "scope": {"product_sku_scope": "CLEAN-BASIC"},
    }


class TestSkillRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.skills_root = Path(self.tmp.name) / "skills"
        (self.skills_root / "drafts").mkdir(parents=True)
        (self.skills_root / "cards").mkdir(parents=True)
        (self.skills_root / "rejected").mkdir(parents=True)
        registry = {
            "schema_version": "approved_skill_registry_v1",
            "registry_revision": "1.0.0",
            "approved": [],
        }
        (self.skills_root / "approved_registry.json").write_text(
            json.dumps(registry, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_draft(self, name: str, payload: dict) -> Path:
        path = self.skills_root / "drafts" / name
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def test_promote_approved_draft(self) -> None:
        draft_path = self._write_draft("promote-me.json", _draft_with_scenarios())
        self.mod.approve_draft(draft_path, skills_root=self.skills_root)
        card_path = self.skills_root / "cards" / "promote-me.json"

        result = self.mod.promote_from_queue(card_path, skills_root=self.skills_root)
        self.assertTrue(result["ok"])
        self.assertFalse(result.get("skipped"))
        self.assertEqual(result["skill_id"], "draft-clean-basic-job-001")
        self.assertIn("approved_at", result)

        listed = self.mod.list_approved(skills_root=self.skills_root)
        self.assertTrue(listed["ok"])
        self.assertEqual(listed["count"], 1)
        entry = listed["approved"][0]
        self.assertEqual(entry["skill_id"], "draft-clean-basic-job-001")
        self.assertEqual(entry["version"], "1.0.0")
        self.assertIn("source_card_path", entry)

    def test_reject_does_not_enter_registry(self) -> None:
        draft_path = self._write_draft("drop-me.json", _draft_with_scenarios())
        self.mod.reject_draft(draft_path, skills_root=self.skills_root)
        rejected_path = self.skills_root / "rejected" / "drop-me.json"

        result = self.mod.promote_from_queue(rejected_path, skills_root=self.skills_root)
        self.assertFalse(result["ok"])

        listed = self.mod.list_approved(skills_root=self.skills_root)
        self.assertEqual(listed["count"], 0)

    def test_duplicate_promote_is_idempotent(self) -> None:
        draft_path = self._write_draft("dup.json", _draft_with_scenarios(skill_id="dup-skill"))
        self.mod.approve_draft(draft_path, skills_root=self.skills_root)
        card_path = self.skills_root / "cards" / "dup.json"

        first = self.mod.promote_from_queue(card_path, skills_root=self.skills_root)
        second = self.mod.promote_from_queue(card_path, skills_root=self.skills_root)
        self.assertTrue(first["ok"])
        self.assertFalse(first.get("skipped"))
        self.assertTrue(second["ok"])
        self.assertTrue(second.get("skipped"))

        listed = self.mod.list_approved(skills_root=self.skills_root)
        self.assertEqual(listed["count"], 1)

    def test_unapproved_draft_promote_fails(self) -> None:
        draft_path = self._write_draft("still-draft.json", _draft_with_scenarios())
        result = self.mod.promote_from_queue(draft_path, skills_root=self.skills_root)
        self.assertFalse(result["ok"])
        self.assertIn("approved", result["message"])

        listed = self.mod.list_approved(skills_root=self.skills_root)
        self.assertEqual(listed["count"], 0)

    def test_incomplete_card_missing_scenarios_fails(self) -> None:
        payload = _draft_with_scenarios(skill_id="no-scenarios")
        del payload["applicable_scenarios"]
        draft_path = self._write_draft("incomplete.json", payload)
        self.mod.approve_draft(draft_path, skills_root=self.skills_root)
        card_path = self.skills_root / "cards" / "incomplete.json"

        result = self.mod.promote_from_queue(card_path, skills_root=self.skills_root)
        self.assertFalse(result["ok"])
        self.assertIn("applicable_scenarios", result["message"])

    def test_cli_list_approved_exit_zero(self) -> None:
        draft_path = self._write_draft("cli.json", _draft_with_scenarios())
        self.mod.approve_draft(draft_path, skills_root=self.skills_root)
        card_path = self.skills_root / "cards" / "cli.json"
        self.mod.promote_from_queue(card_path, skills_root=self.skills_root)

        proc = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT),
                "list-approved",
                "--skills-root",
                str(self.skills_root),
                "--pretty",
            ],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["count"], 1)


if __name__ == "__main__":
    unittest.main()
