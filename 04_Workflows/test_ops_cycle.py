"""test_ops_cycle.py — HQ-P4 營運週期單元測試"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

from _tang_paths import bootstrap_sys_path

bootstrap_sys_path(os.path.dirname(os.path.abspath(__file__)))

from ops_cycle import (  # noqa: E402
    append_battle_report,
    get_archive_checklist,
    invalidate_ops_cycle_cache,
    load_ops_cycle_schema,
    render_battle_report_markdown,
    validate_archive,
    validate_battle_report,
    write_review_template,
)


def _sample_report() -> dict:
    return {
        "ticket_id": "HQ-P4-TEST",
        "role": "大唐副官",
        "status": "done",
        "executed": ["python .\\04_Workflows\\test_ops_cycle.py"],
        "results": "6/6 OK",
        "blockers": "無",
        "next_steps": "交付 HQ-P4-OPS-CYCLE",
        "forbidden_zone_note": "未接觸 DarkOps runtime",
    }


class OpsCycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        invalidate_ops_cycle_cache()

    def test_schema_loads(self) -> None:
        schema = load_ops_cycle_schema()
        self.assertEqual(schema.get("ops_cycle_schema_version"), "v1")
        self.assertIn("battle_report", schema)

    def test_validate_ok(self) -> None:
        r = validate_battle_report(_sample_report())
        self.assertTrue(r["ok"])
        self.assertEqual(r["missing_fields"], [])

    def test_validate_missing(self) -> None:
        bad = {"ticket_id": "X"}
        r = validate_battle_report(bad)
        self.assertFalse(r["ok"])
        self.assertIn("role", r["missing_fields"])

    def test_render_markdown(self) -> None:
        md = render_battle_report_markdown(_sample_report())
        self.assertIn("HQ-P4-TEST", md)
        self.assertIn("Work Report", md)

    def test_archive_checklist_full(self) -> None:
        r = get_archive_checklist("full")
        self.assertIn("steps", r)
        self.assertGreaterEqual(len(r["steps"]), 5)

    def test_validate_archive_minimal(self) -> None:
        r = validate_archive("minimal")
        self.assertIn("ready_for_archive", r)

    def test_append_dry_run(self) -> None:
        r = append_battle_report(_sample_report(), dry_run=True)
        self.assertTrue(r["ok"])
        self.assertTrue(r["dry_run"])

    def test_new_review_dry_run(self) -> None:
        r = write_review_template("sprint", "HQ-P4-TEST", ticket="HQ-P4-OPS-CYCLE", dry_run=True)
        self.assertTrue(r["ok"])
        self.assertTrue(r["dry_run"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
