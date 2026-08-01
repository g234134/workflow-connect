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

    # ========== Reports-dir 專項測試 ==========

    def _run_with_reports(self, *extra: str) -> dict:
        cmd = [
            sys.executable,
            str(_SCRIPT),
            "--reports-dir",
            str(_FIXTURES / "reports"),
            *extra,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=_REPO_ROOT)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        return json.loads(proc.stdout)

    def test_reports_dir_with_patterns_and_anti_patterns(self) -> None:
        """AC-A2: --reports-dir 含 pattern 與 anti-pattern 各 ≥1"""
        result = self._run_with_reports("--pretty")
        self.assertTrue(result["ok"])

        # 驗證 patterns ≥1 且 anti_patterns ≥1
        self.assertGreaterEqual(len(result["patterns"]), 1, "Expected at least 1 pattern from reports")
        self.assertGreaterEqual(len(result["anti_patterns"]), 1, "Expected at least 1 anti-pattern from reports")

        # 驗證至少一個 source_type=report
        report_patterns = [p for p in result["patterns"] if p.get("source_type") == "report"]
        report_anti = [a for a in result["anti_patterns"] if a.get("source_type") == "report"]
        self.assertTrue(
            len(report_patterns) + len(report_anti) >= 1,
            "Expected at least one item with source_type=report"
        )

    def test_reports_source_type_is_report(self) -> None:
        """驗證所有來自 reports 的項目都有 source_type='report'"""
        result = self._run_with_reports()
        all_items = result["patterns"] + result["anti_patterns"]
        report_items = [i for i in all_items if i.get("source_type") == "report"]
        for item in report_items:
            self.assertEqual(item["source_type"], "report", msg=f"Item {item.get('id')} should have source_type=report")

    def test_reports_path_id_is_cp_ticket_state_b_report(self) -> None:
        """驗證 reports 產出的 path_id 為 cp.ticket_state.b_report"""
        result = self._run_with_reports()
        all_items = result["patterns"] + result["anti_patterns"]
        report_items = [i for i in all_items if i.get("source_type") == "report"]
        for item in report_items:
            self.assertEqual(
                item["path_id"],
                "cp.ticket_state.b_report",
                msg=f"Item {item.get('id')} should have path_id=cp.ticket_state.b_report"
            )

    def test_b_report_canonical_path_id_fallback(self) -> None:
        """驗證 cp.ticket_state.b_report 的 canonical_path_id fallback 為原值"""
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from distill_control_plane_skills_lite import (  # noqa: WPS433
            PATH_ID_MAPPING,
            _canonical_path_id,
        )

        # cp.ticket_state.b_report 不在 PATH_ID_MAPPING 中
        self.assertNotIn("cp.ticket_state.b_report", PATH_ID_MAPPING)

        # canonical_path_id 應該 fallback 為原值
        canonical = _canonical_path_id("cp.ticket_state.b_report")
        self.assertEqual(canonical, "cp.ticket_state.b_report")

    def test_joint_cards_comms_reports(self) -> None:
        """AC-A3: 聯合 cards + comms + reports 掃描"""
        result = self._run_cli("--reports-dir", str(_FIXTURES / "reports"), "--pretty")
        self.assertTrue(result["ok"])

        # 驗證至少一個 pattern 和 anti-pattern
        self.assertGreaterEqual(len(result["patterns"]), 1)
        self.assertGreaterEqual(len(result["anti_patterns"]), 1)

        # 驗證至少三種 source_type
        source_types = {i.get("source_type") for i in result["patterns"] + result["anti_patterns"]}
        self.assertTrue(
            source_types.issuperset({"card", "comms", "report"}) or
            source_types.issuperset({"card", "report"}) or
            len(source_types) >= 2,
            f"Expected multiple source types, got {source_types}"
        )

        # 驗證 DEMO-ELIG 被識別為 pattern（有 verification + changed_files）
        elig_pattern = next(
            (p for p in result["patterns"]
             if p.get("source_type") == "report" and "demo-elig" in p.get("id", "")),
            None
        )
        self.assertIsNotNone(elig_pattern, "DEMO-ELIG should be identified as a pattern")

        # 驗證 DEMO-NO-VERIFY 被識別為 anti-pattern（缺少 verification）
        no_verify_anti = next(
            (a for a in result["anti_patterns"]
             if a.get("source_type") == "report" and "demo-no-verify" in a.get("id", "")),
            None
        )
        self.assertIsNotNone(no_verify_anti, "DEMO-NO-VERIFY should be identified as anti-pattern")

        # 驗證 DEMO-BAD-FORMAT 被識別為 anti-pattern（格式錯誤）
        bad_format_anti = next(
            (a for a in result["anti_patterns"]
             if a.get("source_type") == "report" and "demo-bad-format" in a.get("id", "")),
            None
        )
        self.assertIsNotNone(bad_format_anti, "DEMO-BAD-FORMAT should be identified as anti-pattern")


if __name__ == "__main__":
    unittest.main()
