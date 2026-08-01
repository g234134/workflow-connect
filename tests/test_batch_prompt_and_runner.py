"""Tests for batch prompt builder + mock runner (BATCH-MVP-03)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from _batch_orchestrator.prompt_builder import build_implementer_prompt  # noqa: E402
from _batch_orchestrator.runner_mock import (  # noqa: E402
    ExecutionResult,
    run_subtasks_mock,
)


def _st(
    sid: str,
    *,
    priority: int = 10,
    deps: list[str] | None = None,
    parent: str = "BATCH-MVP-03",
) -> dict:
    return {
        "parent_ticket_id": parent,
        "subtask_id": sid,
        "subtask_type": "implementer",
        "target_paths": ["docs/x.md"],
        "allowed_paths": ["docs/x.md", "tests/test_x.py"],
        "blocked_paths": ["core/**", "AGENTS.md"],
        "scope_summary": f"scope {sid}",
        "acceptance_checks": [f"python -m unittest tests.test_{sid}"],
        "priority": priority,
        "dependencies": deps or [],
        "status": "pending",
        "preferred_model": None,
    }


_PARENT_FRAME = {
    "parent_ticket_id": "BATCH-MVP-03",
    "goal": "Build prompt builder and mock runner for batch MVP",
    "must_read": ["04_Workflows/tickets/BATCH-MVP-03_state.md"],
}


class TestBatchPromptBuilder(unittest.TestCase):
    def test_prompt_shape_and_role(self) -> None:
        prompt = build_implementer_prompt(_st("A"), _PARENT_FRAME)
        self.assertTrue(prompt.get("ok"))
        self.assertEqual(prompt["role"], "implementer")
        self.assertIn("prompt builder", prompt["goal_statement"].lower())
        self.assertIn(
            "04_Workflows/tickets/BATCH-MVP-03_state.md",
            prompt["must_read"],
        )
        self.assertIn(".cursor/rules/multi_chat_roles.mdc", prompt["must_read"])
        self.assertIn("AGENTS.md", prompt["must_read"])
        self.assertIn("docs/x.md", prompt["allowed_paths"])
        self.assertIn("core/**", prompt["blocked_paths"])
        self.assertIn("unittest", prompt["acceptance_checks_summary"])

    def test_prompt_falls_back_to_scope_when_no_goal(self) -> None:
        prompt = build_implementer_prompt(_st("B"), {})
        self.assertTrue(prompt.get("ok"))
        self.assertEqual(prompt["role"], "implementer")
        self.assertIn("B", prompt["goal_statement"])
        self.assertIn("scope B", prompt["goal_statement"])
        self.assertIn(
            "04_Workflows/tickets/BATCH-MVP-03_state.md",
            prompt["must_read"],
        )


class TestBatchRunnerMock(unittest.TestCase):
    def test_all_success_with_concurrency(self) -> None:
        subs = [_st("A"), _st("B"), _st("C"), _st("D")]
        results = run_subtasks_mock(
            subs,
            concurrency_limit=2,
            failure_ratio=0.0,
            base_latency_ms=2.0,
            parent_frame=_PARENT_FRAME,
        )
        self.assertEqual(len(results), 4)
        self.assertTrue(all(isinstance(r, ExecutionResult) for r in results))
        self.assertTrue(all(r.ok for r in results))
        self.assertEqual([r.subtask_id for r in results], ["A", "B", "C", "D"])
        self.assertTrue(all(r.prompt and r.prompt.get("role") == "implementer" for r in results))

    def test_force_failures(self) -> None:
        subs = [_st("A"), _st("B"), _st("C")]
        results = run_subtasks_mock(
            subs,
            concurrency_limit=2,
            force_failures=["B"],
            build_prompt=False,
            base_latency_ms=0.0,
        )
        by_id = {r.subtask_id: r for r in results}
        self.assertTrue(by_id["A"].ok)
        self.assertFalse(by_id["B"].ok)
        self.assertEqual(by_id["B"].status, "failed")
        self.assertTrue(by_id["C"].ok)

    def test_failure_ratio(self) -> None:
        subs = [_st("A"), _st("B"), _st("C"), _st("D")]
        results = run_subtasks_mock(
            subs,
            concurrency_limit=2,
            failure_ratio=0.5,
            build_prompt=False,
            base_latency_ms=0.0,
        )
        failed = [r for r in results if not r.ok]
        self.assertEqual(len(failed), 2)
        self.assertEqual({r.subtask_id for r in failed}, {"A", "B"})


if __name__ == "__main__":
    unittest.main()
