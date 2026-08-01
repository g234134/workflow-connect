"""Unit tests for Tabular fleet ops summary (read-only)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_ops_summary_lib import (  # noqa: E402
    FLEET_SCHEMA_VERSION,
    SCHEMA_VERSION,
    build_fleet_ops_rollup,
    build_ops_summary,
    compute_fleet_summary,
    summarize_case,
)

_ANCHOR_CASE_IDS = frozenset({"demo_phase", "2026-0001", "generic-low-risk"})


class TestFleetOpsSummary(unittest.TestCase):
    def test_build_ops_summary_all_includes_fleet_rollup(self) -> None:
        result = build_ops_summary(list_all=True, root=_REPO_ROOT)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("schema_version"), SCHEMA_VERSION)
        self.assertGreaterEqual(result.get("case_count", 0), 3)
        summary = result.get("summary") or {}
        self.assertIn("delivery_ready_count", summary)
        self.assertIn("stuck_at_hitl_count", summary)
        self.assertIn("dlq_queued_total", summary)
        self.assertIn("stuck_cases", summary)
        self.assertIsInstance(summary.get("stuck_cases"), list)

    def test_three_anchor_cases_present_in_fleet(self) -> None:
        result = build_ops_summary(list_all=True, root=_REPO_ROOT)
        case_ids = {row.get("case_id") for row in result.get("cases") or []}
        self.assertIn("demo_phase", case_ids)
        self.assertIn("2026-0001", case_ids)
        self.assertIn("generic-low-risk", case_ids)

    def test_sampleco_delivery_ready_false_in_fleet(self) -> None:
        result = build_ops_summary(list_all=True, root=_REPO_ROOT)
        sampleco = next(
            (row for row in result.get("cases") or [] if row.get("case_id") == "2026-0001"),
            None,
        )
        self.assertIsNotNone(sampleco)
        assert sampleco is not None
        self.assertFalse(sampleco.get("delivery_ready"))

    def test_summarize_case_is_read_only_shape(self) -> None:
        case_dir = _REPO_ROOT / "cases" / "demo_phase"
        row = summarize_case(case_dir, root=_REPO_ROOT)
        self.assertTrue(row.get("ok"))
        for key in (
            "case_id",
            "automation_status",
            "delivery_ready",
            "checkpoint_a_status",
            "checkpoint_b_status",
            "dlq",
        ):
            self.assertIn(key, row)

    def test_compute_fleet_summary_counts(self) -> None:
        cases = [
            {"ok": True, "delivery_ready": True, "dlq": {"queued_count": 0}},
            {"ok": True, "delivery_ready": False, "dlq": {"queued_count": 2}},
            {
                "ok": True,
                "delivery_ready": False,
                "automation_status": "paused",
                "pause_reason": "checkpoint_b",
                "dlq": {"queued_count": 1},
            },
        ]
        summary = compute_fleet_summary(cases)
        self.assertEqual(summary["delivery_ready_count"], 1)
        self.assertEqual(summary["stuck_at_hitl_count"], 1)
        self.assertEqual(summary["dlq_queued_total"], 3)
        self.assertEqual(len(summary["stuck_cases"]), 1)

    def test_fleet_ops_rollup_includes_three_anchor_cases(self) -> None:
        result = build_ops_summary(list_all=True, fleet=True, root=_REPO_ROOT)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("schema_version"), FLEET_SCHEMA_VERSION)
        case_ids = {row.get("case_id") for row in result.get("cases") or []}
        self.assertTrue(_ANCHOR_CASE_IDS.issubset(case_ids))
        summary = result.get("summary") or {}
        for key in (
            "pending_cp_a_count",
            "pending_cp_b_count",
            "pending_checkpoints",
            "dlq_queued_total",
            "dlq_cases",
            "not_delivery_ready_count",
            "not_delivery_ready_cases",
            "stuck_at_hitl_count",
        ):
            self.assertIn(key, summary)

    def test_sampleco_not_delivery_ready_appears_in_not_delivery_ready_list(self) -> None:
        result = build_ops_summary(list_all=True, fleet=True, root=_REPO_ROOT)
        summary = result.get("summary") or {}
        not_ready_ids = {
            row.get("case_id") for row in summary.get("not_delivery_ready_cases") or []
        }
        self.assertIn("2026-0001", not_ready_ids)
        sampleco_entry = next(
            row
            for row in summary.get("not_delivery_ready_cases") or []
            if row.get("case_id") == "2026-0001"
        )
        self.assertFalse(sampleco_entry.get("delivery_ready"))
        self.assertIn("delivery_approval_status", sampleco_entry)
        self.assertIn("output_guard_status", sampleco_entry)

    def test_dlq_queued_total_non_negative(self) -> None:
        result = build_ops_summary(list_all=True, fleet=True, root=_REPO_ROOT)
        summary = result.get("summary") or {}
        dlq_total = summary.get("dlq_queued_total")
        self.assertIsInstance(dlq_total, int)
        self.assertGreaterEqual(dlq_total, 0)
        rollup = build_fleet_ops_rollup(result.get("cases") or [])
        self.assertGreaterEqual(rollup.get("dlq_queued_total", -1), 0)


if __name__ == "__main__":
    unittest.main()
