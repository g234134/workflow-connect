"""Unit tests for P4 Multi-Chat smoke pack v1."""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

_REQUIRED_COMMANDS = (
    ".cursor/commands/ticket-orchestrator.md",
    ".cursor/commands/ticket-implementer.md",
    ".cursor/commands/ticket-reviewer.md",
    ".cursor/commands/ticket-scribe.md",
)

_REQUIRED_DOCS = (
    "docs/p4-multi-chat-smoke-pack-v1.md",
    "docs/phase4-multi-agent-collaboration-contract-v1.md",
    ".cursor/rules/multi_chat_roles.mdc",
    ".cursor/skills/multi-chat-ticket-workflow/SKILL.md",
    "04_Workflows/tickets/_templates/ticket_state.template.md",
    "04_Workflows/tickets/P4-MULTI-CHAT-SMOKE-PACK-v1_state.md",
)


class TestP4MultiChatSmokePackV1(unittest.TestCase):
    def test_required_assets_exist(self) -> None:
        missing = [
            rel
            for rel in (*_REQUIRED_COMMANDS, *_REQUIRED_DOCS)
            if not (_REPO_ROOT / rel).is_file()
        ]
        self.assertEqual(missing, [], msg=f"missing smoke-pack assets: {missing}")

    def test_runbook_has_walkthrough_and_non_claims(self) -> None:
        text = (_REPO_ROOT / "docs/p4-multi-chat-smoke-pack-v1.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("walkthrough", text.lower())
        self.assertIn("non_claims", text.lower())
        self.assertIn("ticket-orchestrator.md", text)
        self.assertIn("apply_phase_pct", text)
        self.assertIn("Orchestrator", text)
        self.assertIn("Implementer", text)

    def test_roles_rule_names_four_roles(self) -> None:
        text = (_REPO_ROOT / ".cursor/rules/multi_chat_roles.mdc").read_text(
            encoding="utf-8"
        )
        for role in ("Orchestrator", "Implementer", "Reviewer", "Scribe"):
            self.assertIn(role, text)

    def test_skill_mentions_o_b_c_d(self) -> None:
        text = (
            _REPO_ROOT / ".cursor/skills/multi-chat-ticket-workflow/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("O → B → C → D", text)
        self.assertIn("B_REPORT", text)
        self.assertIn("C_REPORT", text)

    def test_ticket_state_has_frame_and_ac(self) -> None:
        text = (
            _REPO_ROOT / "04_Workflows/tickets/P4-MULTI-CHAT-SMOKE-PACK-v1_state.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## FRAME", text)
        self.assertIn("AcceptanceCriteria", text)
        self.assertIn("## B_REPORT", text)


if __name__ == "__main__":
    unittest.main()
