"""test_task_routing.py — HQ-P3 任務路由單元測試"""
from __future__ import annotations

import os
import sys
import unittest

from _tang_paths import bootstrap_sys_path

bootstrap_sys_path(os.path.dirname(os.path.abspath(__file__)))

from task_routing import (  # noqa: E402
    invalidate_routing_cache,
    load_routing_table,
    route_task,
)


class TaskRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        invalidate_routing_cache()

    def test_table_loads(self) -> None:
        table = load_routing_table()
        self.assertEqual(table.get("routing_schema_version"), "v1")
        self.assertGreaterEqual(len(table.get("routes") or []), 10)

    def test_explicit_governance(self) -> None:
        r = route_task(task_type="hq.governance")
        self.assertTrue(r["ok"])
        self.assertEqual(r["worker"], "HQ-Governance-Worker")
        self.assertEqual(r["match_method"], "explicit")
        self.assertTrue(r["assignable"])

    def test_explicit_dark_blocked(self) -> None:
        r = route_task(task_type="dark.infra")
        self.assertTrue(r["ok"])
        self.assertEqual(r["worker"], "DarkOps-Worker")
        self.assertEqual(r["cabin"], "gov_core_system")
        self.assertEqual(r["dark_agent"], "Infra")
        self.assertFalse(r["assignable"])
        self.assertTrue(r["blocked"])

    def test_keyword_scout(self) -> None:
        r = route_task(description="啟動 scout 偵察 playwright")
        self.assertEqual(r["task_type"], "chariot.scout")
        self.assertEqual(r["cabin"], "gov_agency")
        self.assertEqual(r["match_method"], "keyword")

    def test_unknown_type(self) -> None:
        r = route_task(task_type="not.a.real.type")
        self.assertFalse(r["ok"])
        self.assertTrue(r["blocked"])

    def test_default_coordination(self) -> None:
        r = route_task(description="xyz_no_keywords_12345")
        self.assertEqual(r["task_type"], "hq.coordination")
        self.assertEqual(r["match_method"], "default")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
