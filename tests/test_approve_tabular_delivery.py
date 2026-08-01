"""Unit tests for tabular delivery approval CLI and library."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_delivery_approval_lib import (  # noqa: E402
    approve_tabular_delivery,
    evaluate_delivery_readiness,
    load_approval,
    maybe_update_delivery_readiness,
    reject_tabular_delivery,
)


def _seed_case(root: Path, *, output_guard_status: str = "ok") -> Path:
    case_dir = root / "cases" / "demo_phase"
    case_dir.mkdir(parents=True)
    (case_dir / "intake.json").write_text(
        json.dumps({"case_id": "demo_phase", "client_ref": "internal-demo"}),
        encoding="utf-8",
    )
    (case_dir / "raw").mkdir()
    (case_dir / "cleaned").mkdir()
    (case_dir / "cleaned" / "Phase_cleaned.csv").write_text("Phase\n1\n", encoding="utf-8")
    reports = case_dir / "reports"
    reports.mkdir()
    (reports / "report.json").write_text(
        json.dumps(
            {
                "summary": {"qa_status": "pass"},
                "output_guard": {"status": output_guard_status, "input_rows": 7, "output_rows": 5},
            }
        ),
        encoding="utf-8",
    )
    (case_dir / "delivery_signoff.md").write_text(
        "| Field | Value |\n|-------|-------|\n"
        "| case_id | `demo_phase` |\n"
        "| lead_approval | _pending_ |\n"
        "| delivered_at | _pending_ |\n\n"
        "## Signoff\n\n| Field | Value |\n|-------|-------|\n"
        "| reviewer | _pending_ |\n"
        "| signer (Lead) | _pending_ |\n"
        "| signed_at | _pending_ |\n",
        encoding="utf-8",
    )
    (reports / "automation_run_log.json").write_text(
        json.dumps(
            {
                "steps": [
                    {"step_name": "e2e", "step_status": "completed"},
                    {"step_name": "checkpoint_b", "step_status": "completed"},
                ]
            }
        ),
        encoding="utf-8",
    )
    index_path = root / "cases" / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "schema_version": "gov-cases-index-v0.1",
                "cases": [{"case_dir": "cases/demo_phase", "case_id": "demo_phase"}],
            }
        ),
        encoding="utf-8",
    )
    return case_dir


class TestTabularDeliveryApproval(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.case_dir = _seed_case(self.root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_evaluate_readiness_all_gates_pass(self) -> None:
        result = evaluate_delivery_readiness(self.case_dir)
        self.assertTrue(result["delivery_ready"])
        self.assertTrue(result["cp_b_approved"])
        self.assertTrue(result["e2e_pass"])
        self.assertTrue(result["output_guard_ok"])
        self.assertEqual(result["readiness_gaps"], [])

    def test_evaluate_readiness_guard_blocks(self) -> None:
        report_path = self.case_dir / "reports" / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["output_guard"]["status"] = "warning"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        result = evaluate_delivery_readiness(self.case_dir)
        self.assertFalse(result["delivery_ready"])
        self.assertTrue(any("output_guard" in gap for gap in result["readiness_gaps"]))

    def test_approve_sets_ready_and_signoff(self) -> None:
        result = approve_tabular_delivery(self.case_dir, approved_by="lead_test", reason="LGTM", repo_root=self.root)
        self.assertTrue(result["ok"])
        self.assertTrue(result["delivery_ready"])
        self.assertTrue(result["signoff_recorded"])

        approval = load_approval(self.case_dir)
        self.assertEqual(approval["delivery_approval_status"], "approved")
        self.assertEqual(approval["delivery_approved_by"], "lead_test")

        signoff = (self.case_dir / "delivery_signoff.md").read_text(encoding="utf-8")
        self.assertIn("approved by lead_test", signoff)

        index = json.loads((self.root / "cases" / "index.json").read_text(encoding="utf-8"))
        entry = index["cases"][0]
        self.assertEqual(entry["delivery_approval_status"], "approved")
        self.assertTrue(entry["delivery_ready"])

    def test_reject_blocks_auto_ready(self) -> None:
        reject_tabular_delivery(self.case_dir, rejected_by="lead", reason="needs rework")
        readiness = maybe_update_delivery_readiness(self.case_dir)
        self.assertFalse(readiness["delivery_ready"])
        self.assertEqual(readiness["delivery_approval_status"], "rejected")

        approval = load_approval(self.case_dir)
        self.assertEqual(approval["delivery_approval_status"], "rejected")
        self.assertFalse(approval["delivery_ready"])

    def test_rejected_can_be_human_reapproved(self) -> None:
        reject_tabular_delivery(self.case_dir, rejected_by="lead", reason="first pass no")
        result = approve_tabular_delivery(self.case_dir, approved_by="lead", reason="fixed")
        self.assertEqual(result["delivery_approval_status"], "approved")
        self.assertTrue(result["delivery_ready"])

    def test_approve_with_guard_gap_ok_false(self) -> None:
        report_path = self.case_dir / "reports" / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["output_guard"]["status"] = "warning"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        result = approve_tabular_delivery(
            self.case_dir, approved_by="lead", reason="override attempt", repo_root=self.root
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["delivery_ready"])
        self.assertFalse(result["signoff_recorded"])
        self.assertEqual(result["delivery_approval_status"], "approved")


if __name__ == "__main__":
    unittest.main()
