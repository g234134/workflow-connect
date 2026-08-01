"""Unit tests for toolchain local gaps quickview v1 (WC-C1-01)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, Optional
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GAPS_CLI = _REPO_ROOT / "scripts" / "run_toolchain_local_gaps_quickview.py"


def _load_gaps_module():
    spec = importlib.util.spec_from_file_location(
        "run_toolchain_local_gaps_quickview", _GAPS_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_toolchain_local_gaps_quickview"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestToolchainLocalGapsQuickviewV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _GAPS_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_GAPS_CLI}")
        cls.gaps = _load_gaps_module()

    def _build(
        self,
        *,
        case_ref: Optional[str] = None,
        include_health: bool = False,
        tabular_probe=None,
        non_tabular_probe=None,
        executor_probe=None,
        audit_probe=None,
        smoke_probe=None,
        health_probe=None,
    ) -> Dict[str, Any]:
        return self.gaps.build_toolchain_local_gaps_report(
            case_ref=case_ref,
            dry_run=True,
            include_health_dashboard=include_health,
            repo_root=_REPO_ROOT,
            tabular_probe=tabular_probe,
            non_tabular_probe=non_tabular_probe,
            executor_probe=executor_probe,
            audit_probe=audit_probe,
            smoke_probe=smoke_probe,
            health_probe=health_probe,
        )

    def test_json_top_level_fields_and_gate_metadata(self) -> None:
        report = self._build()
        self.assertEqual(report["schema_version"], "toolchain_local_gaps_v1")
        self.assertEqual(report["gate_class"], "optional")
        self.assertFalse(report["blocks_mainline"])
        self.assertTrue(report["dry_run"])
        self.assertIn("sections", report)
        self.assertIn("generated_at", report)

    def test_required_section_names_and_shapes(self) -> None:
        report = self._build()
        required = (
            "selector_plan_only",
            "executor_timeout_contract",
            "audit_investigation",
            "smoke_matrix_dry_run",
        )
        for name in required:
            section = report["sections"][name]
            self.assertIn(section["status"], ("ok", "degraded", "missing", "skipped"))
            self.assertIn("ok", section)
            self.assertIn("message", section)

    def test_selector_plan_only_ok_when_both_plan_only_true(self) -> None:
        report = self._build(
            tabular_probe=lambda: {"ok": True, "plan_only": True, "selector_rule_id": "t"},
            non_tabular_probe=lambda: {"ok": True, "plan_only": True, "selector_rule_id": "n"},
        )
        section = report["sections"]["selector_plan_only"]
        self.assertEqual(section["status"], "ok")
        self.assertTrue(section["ok"])
        self.assertTrue(section["tabular"]["plan_only"])
        self.assertTrue(section["non_tabular"]["plan_only"])

    def test_selector_plan_only_degraded_when_plan_only_missing(self) -> None:
        report = self._build(
            tabular_probe=lambda: {"ok": False, "selector_rule_id": "t"},
            non_tabular_probe=lambda: {"ok": True, "plan_only": True, "selector_rule_id": "n"},
        )
        section = report["sections"]["selector_plan_only"]
        self.assertEqual(section["status"], "degraded")
        self.assertFalse(section["ok"])
        self.assertIn("tabular missing plan_only", section["message"])

    def test_selector_plan_only_degraded_when_plan_only_false(self) -> None:
        report = self._build(
            tabular_probe=lambda: {"ok": True, "plan_only": False, "selector_rule_id": "t"},
            non_tabular_probe=lambda: {"ok": True, "plan_only": True, "selector_rule_id": "n"},
        )
        section = report["sections"]["selector_plan_only"]
        self.assertEqual(section["status"], "degraded")
        self.assertFalse(section["ok"])

    def test_executor_timeout_contract_ok_via_mock_probe(self) -> None:
        report = self._build(
            executor_probe=lambda: {
                "status": "ok",
                "ok": True,
                "message": "mock ok",
                "timeout_seconds": 600,
                "subprocess_timeout_message_ok": True,
            }
        )
        section = report["sections"]["executor_timeout_contract"]
        self.assertTrue(section["ok"])
        self.assertEqual(section["timeout_seconds"], 600)

    def test_executor_timeout_contract_degraded_on_bad_contract(self) -> None:
        report = self._build(
            executor_probe=lambda: {
                "status": "degraded",
                "ok": False,
                "message": "timeout mismatch",
                "timeout_seconds": 300,
                "subprocess_timeout_message_ok": False,
            }
        )
        section = report["sections"]["executor_timeout_contract"]
        self.assertFalse(section["ok"])
        self.assertEqual(section["status"], "degraded")

    def test_executor_timeout_contract_live_mock_in_process(self) -> None:
        section = self.gaps.probe_executor_timeout_contract()
        self.assertEqual(section["timeout_seconds"], 600)
        self.assertTrue(section.get("mocked_probe"))
        self.assertTrue(section["ok"])

    def test_audit_investigation_skipped_without_case_ref(self) -> None:
        report = self._build(case_ref=None)
        section = report["sections"]["audit_investigation"]
        self.assertEqual(section["status"], "skipped")
        self.assertTrue(section["ok"])
        self.assertIn("no case-ref provided", section["message"])
        self.assertIsNone(section["gaps_count"])

    def test_audit_investigation_with_case_ref_via_mock(self) -> None:
        report = self._build(
            case_ref="demo_phase",
            audit_probe=lambda ref: {
                "status": "ok",
                "ok": True,
                "message": f"gaps for {ref}",
                "case_ref": ref,
                "gaps_count": 2,
                "top_gaps": [{"gap_id": "g1", "severity": "info", "reason": "test"}],
            },
        )
        section = report["sections"]["audit_investigation"]
        self.assertEqual(section["status"], "ok")
        self.assertEqual(section["gaps_count"], 2)
        self.assertEqual(len(section["top_gaps"]), 1)

    def test_smoke_matrix_dry_run_entries_and_tier_counts(self) -> None:
        report = self._build(
            smoke_probe=lambda: {
                "status": "ok",
                "ok": True,
                "message": "dry-run listed 4 entries",
                "dry_run": True,
                "entries_requested": 4,
                "tier_counts": {"local_recommended": 2, "optional_ci": 2},
            }
        )
        section = report["sections"]["smoke_matrix_dry_run"]
        self.assertTrue(section["dry_run"])
        self.assertEqual(section["entries_requested"], 4)
        self.assertEqual(section["tier_counts"]["local_recommended"], 2)

    def test_smoke_matrix_dry_run_live_against_repo_matrix(self) -> None:
        section = self.gaps.probe_smoke_matrix_dry_run(repo_root=_REPO_ROOT)
        self.assertTrue(section["dry_run"])
        self.assertGreater(section["entries_requested"], 0)
        self.assertTrue(section["tier_counts"])

    def test_include_health_dashboard_embed(self) -> None:
        report = self._build(
            include_health=True,
            health_probe=lambda: {
                "ok": True,
                "gate_class": "optional",
                "blocks_mainline": False,
                "dry_run": True,
                "schema_version": "toolchain_health_v1",
                "sections_populated": 5,
                "sections_ok": 3,
                "aggregated_health_score": 80,
                "message": "embedded",
            },
        )
        embed = report["toolchain_health_embed"]
        self.assertEqual(embed["gate_class"], "optional")
        self.assertFalse(embed["blocks_mainline"])
        self.assertEqual(embed["sections_populated"], 5)

    def test_overall_ok_false_when_any_section_not_ok(self) -> None:
        report = self._build(
            smoke_probe=lambda: {
                "status": "degraded",
                "ok": False,
                "message": "empty",
                "dry_run": True,
                "entries_requested": 0,
                "tier_counts": {},
            }
        )
        self.assertFalse(report["ok"])

    def test_format_text_includes_section_names_and_ok_summary(self) -> None:
        report = self._build(
            tabular_probe=lambda: {"ok": True, "plan_only": True},
            non_tabular_probe=lambda: {"ok": True, "plan_only": True},
            smoke_probe=lambda: {
                "status": "ok",
                "ok": True,
                "message": "listed",
                "dry_run": True,
                "entries_requested": 3,
                "tier_counts": {"local_recommended": 3},
            },
        )
        text = self.gaps.format_toolchain_local_gaps_text(report)
        for name in (
            "selector_plan_only",
            "executor_timeout_contract",
            "audit_investigation",
            "smoke_matrix_dry_run",
        ):
            self.assertIn(name, text)
        self.assertIn("[ok]", text)
        self.assertIn("gate_class: optional", text)

    def test_cli_json_exit_zero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_GAPS_CLI), "--format", "json"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema_version"], "toolchain_local_gaps_v1")
        self.assertTrue(payload["dry_run"])

    def test_cli_case_ref_json_exit_zero(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_GAPS_CLI),
                "--case-ref",
                "demo_phase",
                "--format",
                "json",
            ],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        audit = payload["sections"]["audit_investigation"]
        self.assertNotEqual(audit["status"], "skipped")
        self.assertIsNotNone(audit.get("gaps_count"))


if __name__ == "__main__":
    unittest.main()
