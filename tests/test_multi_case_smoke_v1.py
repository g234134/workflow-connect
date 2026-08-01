"""Unit tests for multi-case smoke runner v1 (MC-SMOKE)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.run_multi_case_smoke_v1 import (
    DEFAULT_REPRESENTATIVE_CASES,
    resolve_case_entries,
    run_multi_case_smoke_v1,
)

_GOOD_SMOKE = {
    "ok": True,
    "steps": [
        {"step_id": "gate_preview", "ok": True},
        {"step_id": "gate_run_notify", "ok": True},
        {"step_id": "std_case_experiment", "ok": True},
        {"step_id": "workflow_events_inspect", "ok": True},
        {"step_id": "feedback_ingest_dry_run", "ok": True},
        {"step_id": "p89_verification_bundle", "ok": True},
        {"step_id": "operator_backlog", "ok": True},
    ],
}

_FAIL_SMOKE = {
    "ok": False,
    "steps": [
        {"step_id": "gate_preview", "ok": True},
        {"step_id": "gate_run_notify", "ok": False},
        {"step_id": "std_case_experiment", "ok": False},
    ],
}


class TestMultiCaseSmokeV1(unittest.TestCase):
    def test_multi_case_smoke_summary_contains_all_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            outbox_root = tmp_path / "outbox"
            with patch(
                "scripts.run_multi_case_smoke_v1.run_multi_phase_smoke_v1",
                return_value=_GOOD_SMOKE,
            ):
                result = run_multi_case_smoke_v1(
                    resolve_case_entries(),
                    repo_root=tmp_path,
                    outbox_root_override=str(outbox_root),
                    write_summary=False,
                )

            self.assertEqual(result.get("schema_version"), "multi_case_smoke_v1")
            self.assertTrue(result.get("ok"))
            self.assertEqual(result.get("failed_cases"), [])

            cases = result.get("cases") or []
            self.assertEqual(len(cases), len(DEFAULT_REPRESENTATIVE_CASES))

            expected_refs = {entry["case_ref"] for entry in DEFAULT_REPRESENTATIVE_CASES}
            actual_refs = {row["case_ref"] for row in cases}
            self.assertEqual(actual_refs, expected_refs)

            for row in cases:
                self.assertIn("task_type", row)
                self.assertIn("label", row)
                self.assertIn("ok", row)
                self.assertIn("failed_steps", row)
                self.assertIn("operator_status", row)
                self.assertTrue(row["ok"])
                self.assertEqual(row["failed_steps"], [])

    def test_multi_case_smoke_summary_top_level_ok_false_when_any_case_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            outbox_root = tmp_path / "outbox"

            def _side_effect(case_ref, **kwargs):
                if case_ref == "phi_demo":
                    return _FAIL_SMOKE
                return _GOOD_SMOKE

            with patch(
                "scripts.run_multi_case_smoke_v1.run_multi_phase_smoke_v1",
                side_effect=_side_effect,
            ):
                result = run_multi_case_smoke_v1(
                    resolve_case_entries(["demo_phase", "phi_demo"]),
                    repo_root=tmp_path,
                    outbox_root_override=str(outbox_root),
                    write_summary=False,
                )

            self.assertFalse(result.get("ok"))
            self.assertEqual(result.get("failed_cases"), ["phi_demo"])

            by_ref = {row["case_ref"]: row for row in result.get("cases") or []}
            self.assertTrue(by_ref["demo_phase"]["ok"])
            self.assertFalse(by_ref["phi_demo"]["ok"])
            self.assertEqual(
                by_ref["phi_demo"]["failed_steps"],
                ["gate_run_notify", "std_case_experiment"],
            )


if __name__ == "__main__":
    unittest.main()
