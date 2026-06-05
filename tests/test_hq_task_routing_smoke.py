"""Phase 6 smoke — HQ task routing (``02_Agents_Core/task_routing.py``)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AGENTS_CORE = _REPO_ROOT / "02_Agents_Core"
for p in (str(_AGENTS_CORE),):
    if p not in sys.path:
        sys.path.insert(0, p)

from task_routing import invalidate_routing_cache, load_routing_table, route_task  # noqa: E402


class TestHqTaskRoutingSmoke(unittest.TestCase):
    """Happy path + edge cases for HQ ``route_task`` (Phase 3 routing policy)."""

    @classmethod
    def setUpClass(cls) -> None:
        invalidate_routing_cache()

    def test_table_loads_with_routes(self) -> None:
        table = load_routing_table()
        self.assertEqual(table.get("routing_schema_version"), "v1")
        self.assertGreaterEqual(len(table.get("routes") or []), 10)

    def test_explicit_governance_assignable(self) -> None:
        out = route_task(task_type="hq.governance")
        self.assertTrue(out["ok"])
        self.assertEqual(out["worker"], "HQ-Governance-Worker")
        self.assertEqual(out["match_method"], "explicit")
        self.assertTrue(out["assignable"])

    def test_dark_infra_blocked_not_assignable(self) -> None:
        out = route_task(task_type="dark.infra")
        self.assertTrue(out["ok"])
        self.assertEqual(out["cabin"], "gov_core_system")
        self.assertFalse(out["assignable"])
        self.assertTrue(out["blocked"])

    def test_unknown_task_type_not_ok(self) -> None:
        out = route_task(task_type="not.a.real.type")
        self.assertFalse(out["ok"])
        self.assertTrue(out["blocked"])

    def test_keyword_scout_routes_agency_cabin(self) -> None:
        out = route_task(description="啟動 scout 偵察 playwright")
        self.assertEqual(out["task_type"], "chariot.scout")
        self.assertEqual(out["cabin"], "gov_agency")
        self.assertEqual(out["match_method"], "keyword")

    def test_default_coordination_when_no_keywords(self) -> None:
        out = route_task(description="xyz_no_keywords_12345")
        self.assertEqual(out["task_type"], "hq.coordination")
        self.assertEqual(out["match_method"], "default")


if __name__ == "__main__":
    unittest.main()
