"""Tests for Wave 8 Skill Card review queue (04_Workflows)."""

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


def _minimal_draft(*, skill_id: str = "draft-clean-basic-job-001") -> dict:
    return {
        "schema_version": "skill_card_v0.1",
        "card_meta": {
            "skill_id": skill_id,
            "title": "Draft skill for CLEAN-BASIC",
            "confidence_level": "low",
            "review_status": "draft",
        },
        "scope": {"product_sku_scope": "CLEAN-BASIC"},
    }


class TestSkillCardReviewQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.skills_root = Path(self.tmp.name) / "skills"
        (self.skills_root / "drafts").mkdir(parents=True)
        (self.skills_root / "cards").mkdir(parents=True)
        (self.skills_root / "rejected").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_draft(self, name: str, payload: dict | str) -> Path:
        path = self.skills_root / "drafts" / name
        if isinstance(payload, dict):
            path.write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            path.write_text(payload, encoding="utf-8")
        return path

    def test_list_lists_drafts(self) -> None:
        self._write_draft("a.json", _minimal_draft(skill_id="draft-a"))
        self._write_draft("b.json", _minimal_draft(skill_id="draft-b"))
        (self.skills_root / "drafts" / "note.txt").write_text("skip", encoding="utf-8")

        result = self.mod.list_drafts(skills_root=self.skills_root)
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 2)
        filenames = {d["filename"] for d in result["drafts"]}
        self.assertEqual(filenames, {"a.json", "b.json"})
        ids = {d["skill_id"] for d in result["drafts"]}
        self.assertEqual(ids, {"draft-a", "draft-b"})

    def test_approve_moves_to_cards(self) -> None:
        draft_path = self._write_draft("promote-me.json", _minimal_draft())
        result = self.mod.approve_draft(
            draft_path,
            skills_root=self.skills_root,
            review_notes="ok for pilot",
        )
        self.assertTrue(result["ok"])
        self.assertFalse(draft_path.exists())
        card_path = self.skills_root / "cards" / "promote-me.json"
        self.assertTrue(card_path.is_file())
        data = json.loads(card_path.read_text(encoding="utf-8"))
        self.assertEqual(data["card_meta"]["review_status"], "approved")
        self.assertEqual(data["review_notes"], "ok for pilot")
        self.assertIn("reviewed_at", data)

    def test_reject_moves_to_rejected(self) -> None:
        draft_path = self._write_draft("drop-me.json", _minimal_draft())
        result = self.mod.reject_draft(
            draft_path,
            skills_root=self.skills_root,
            review_notes="scope mismatch",
        )
        self.assertTrue(result["ok"])
        self.assertFalse(draft_path.exists())
        rejected_path = self.skills_root / "rejected" / "drop-me.json"
        self.assertTrue(rejected_path.is_file())
        data = json.loads(rejected_path.read_text(encoding="utf-8"))
        self.assertEqual(data["card_meta"]["review_status"], "rejected")
        self.assertEqual(data["review_notes"], "scope mismatch")

    def test_invalid_json_cannot_approve(self) -> None:
        draft_path = self._write_draft("broken.json", "{ not json")
        with self.assertRaises(ValueError):
            self.mod.approve_draft(draft_path, skills_root=self.skills_root)
        self.assertTrue(draft_path.is_file())
        self.assertFalse((self.skills_root / "cards" / "broken.json").exists())

    def test_invalid_json_cannot_reject(self) -> None:
        draft_path = self._write_draft("broken2.json", "{ not json")
        with self.assertRaises(ValueError):
            self.mod.reject_draft(draft_path, skills_root=self.skills_root)
        self.assertTrue(draft_path.is_file())
        self.assertFalse((self.skills_root / "rejected" / "broken2.json").exists())

    def test_cli_list_exit_zero(self) -> None:
        self._write_draft("cli.json", _minimal_draft())
        proc = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT),
                "list",
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
