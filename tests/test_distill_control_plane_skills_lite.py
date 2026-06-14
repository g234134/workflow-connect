"""Unit tests for WC-T6 skill distillation lite CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "scripts" / "distill_control_plane_skills_lite.py"
_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "skill_distillation"


class TestDistillControlPlaneSkillsLite(unittest.TestCase):
    def _run_cli(self, *extra: str) -> dict:
        cmd = [
            sys.executable,
            str(_SCRIPT),
            "--cards-dir",
            str(_FIXTURES / "cards"),
            "--comms-jsonl",
            str(_FIXTURES / "comms" / "one_comms.jsonl"),
            *extra,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=_REPO_ROOT)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        return json.loads(proc.stdout)

    def test_cli_ok_with_patterns_and_anti_patterns(self) -> None:
        result = self._run_cli("--pretty")
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(len(result["patterns"]), 1)
        self.assertGreaterEqual(len(result["anti_patterns"]), 1)
        self.assertIn("source_refs", result)

    def test_each_pattern_has_source_refs(self) -> None:
        result = self._run_cli()
        for item in result["patterns"] + result["anti_patterns"]:
            refs = item.get("source_refs") or []
            self.assertGreaterEqual(len(refs), 1, msg=item.get("id"))
            first = refs[0]
            self.assertTrue(
                first.get("path") or first.get("ticket_id"),
                msg=f"missing path/ticket_id in {item.get('id')}",
            )
            if first.get("path"):
                self.assertIn("skill_distillation", first["path"])

    def test_import_distill_skills(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from distill_control_plane_skills_lite import distill_skills  # noqa: WPS433

        result = distill_skills(
            cards_dir=_FIXTURES / "cards",
            comms_jsonl=_FIXTURES / "comms" / "one_comms.jsonl",
        )
        self.assertTrue(result["ok"])
        pattern_ids = {p["id"] for p in result["patterns"]}
        anti_ids = {a["id"] for a in result["anti_patterns"]}
        self.assertTrue(any("eligibility" in pid or "verification" in pid for pid in pattern_ids))
        self.assertIn("anti-skip-review-demo-bad", anti_ids)

    def test_canonical_path_id_maps_to_wc_m2(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from distill_control_plane_skills_lite import distill_skills  # noqa: WPS433

        result = distill_skills(
            cards_dir=_FIXTURES / "cards",
            comms_jsonl=_FIXTURES / "comms" / "one_comms.jsonl",
        )
        self.assertTrue(result["ok"])
        all_items = result["patterns"] + result["anti_patterns"]
        self.assertGreaterEqual(len(all_items), 2)

        wc_m2_canonical = [
            item for item in all_items if str(item.get("canonical_path_id", "")).startswith("wc.m2.")
        ]
        self.assertGreaterEqual(len(wc_m2_canonical), 1)

        for item in all_items:
            path_id = item.get("path_id")
            self.assertIsNotNone(path_id)
            self.assertTrue(
                str(path_id).startswith("cp."),
                msg=f"path_id should remain cp.* source: {path_id}",
            )
            self.assertIn("canonical_path_id", item)

        mapped = next(
            p for p in result["patterns"] if p["path_id"] == "cp.dispatch_cards.eligibility_gate"
        )
        self.assertEqual(mapped["canonical_path_id"], "wc.m2.dispatch.eligibility_gate_warn")

    def test_comms_handoff_pattern_references_ticket_id(self) -> None:
        result = self._run_cli()
        handoff = next(
            (p for p in result["patterns"] if p.get("path_id") == "cp.ticket_comms.state_transition"),
            None,
        )
        self.assertIsNotNone(handoff)
        refs = handoff["source_refs"]
        ticket_ids = {r.get("ticket_id") for r in refs}
        self.assertIn("DEMO-ELIG", ticket_ids)


if __name__ == "__main__":
    unittest.main()
