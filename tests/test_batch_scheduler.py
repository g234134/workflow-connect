"""Tests for batch orchestrator scheduler (BATCH-MVP-02)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from _batch_orchestrator.scheduler import plan_from_loader_data, plan_from_subtasks  # noqa: E402


def _st(
    sid: str,
    *,
    priority: int = 10,
    deps: list[str] | None = None,
    parent: str = "BATCH-MVP-02",
) -> dict:
    return {
        "parent_ticket_id": parent,
        "subtask_id": sid,
        "subtask_type": "implementer",
        "target_paths": ["docs/x.md"],
        "allowed_paths": ["docs/x.md"],
        "blocked_paths": ["core/**"],
        "scope_summary": f"scope {sid}",
        "acceptance_checks": ["unittest"],
        "priority": priority,
        "dependencies": deps or [],
        "status": "pending",
        "preferred_model": None,
    }


class TestBatchScheduler(unittest.TestCase):
    def test_no_deps_single_wave(self) -> None:
        # AC-4a: no deps → all in wave1; priority order
        subs = [
            _st("C", priority=30),
            _st("A", priority=10),
            _st("B", priority=20),
        ]
        result = plan_from_subtasks(subs)
        self.assertTrue(result["ok"])
        self.assertEqual(result["waves"], [["A", "B", "C"]])
        self.assertEqual(result["order"], ["A", "B", "C"])
        self.assertIn("A", result["eligibility"]["parallel_ok"])

    def test_linear_chain(self) -> None:
        # AC-4b: A→B→C
        subs = [
            _st("A", priority=1, deps=[]),
            _st("B", priority=1, deps=["A"]),
            _st("C", priority=1, deps=["B"]),
        ]
        result = plan_from_subtasks(subs)
        self.assertTrue(result["ok"])
        self.assertEqual(result["waves"], [["A"], ["B"], ["C"]])
        self.assertEqual(result["order"], ["A", "B", "C"])
        # B depends on A → not same wave
        for wave in result["waves"]:
            if "A" in wave:
                self.assertNotIn("B", wave)
            if "B" in wave:
                self.assertNotIn("C", wave)

    def test_partial_parallel(self) -> None:
        # AC-4c: A→C, B free → wave1=[A,B] (priority), wave2=[C]
        subs = [
            _st("A", priority=10, deps=[]),
            _st("B", priority=20, deps=[]),
            _st("C", priority=10, deps=["A"]),
        ]
        result = plan_from_subtasks(subs)
        self.assertTrue(result["ok"])
        self.assertEqual(result["waves"][0], ["A", "B"])
        self.assertEqual(result["waves"][1], ["C"])
        self.assertEqual(result["order"], ["A", "B", "C"])

    def test_priority_within_wave(self) -> None:
        # AC-3: lower priority number first in order within wave
        subs = [
            _st("X", priority=5, deps=[]),
            _st("Y", priority=1, deps=[]),
            _st("Z", priority=3, deps=[]),
        ]
        result = plan_from_subtasks(subs)
        self.assertTrue(result["ok"])
        self.assertEqual(result["order"], ["Y", "Z", "X"])

    def test_cycle_detection(self) -> None:
        # AC-2: cycle → ok false + eligibility.errors
        subs = [
            _st("A", deps=["B"]),
            _st("B", deps=["A"]),
        ]
        result = plan_from_subtasks(subs)
        self.assertFalse(result["ok"])
        self.assertEqual(result["waves"], [])
        self.assertTrue(result["eligibility"]["errors"])
        self.assertIn("cycle", result["eligibility"]["errors"][0].lower())

    def test_from_loader_data(self) -> None:
        data = {"kind": "manifest", "subtasks": [_st("S1"), _st("S2", deps=["S1"])]}
        result = plan_from_loader_data(data)
        self.assertTrue(result["ok"])
        self.assertEqual(result["waves"], [["S1"], ["S2"]])


if __name__ == "__main__":
    unittest.main()
