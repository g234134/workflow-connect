"""Contract tests for Phase 4 multi-agent collaboration SSOT."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "phase4-multi-agent-collaboration-contract-v1.md"
_TEMPLATE = _REPO_ROOT / "04_Workflows" / "tickets" / "_templates" / "ticket_state.template.md"
_W5_DOCS = (
    _REPO_ROOT / "docs" / "multi-agent-collaboration-spec-v1.md",
    _REPO_ROOT / "docs" / "multi-agent-handoff-runbook-v1.md",
    _REPO_ROOT / "docs" / "multi-agent-replay-guide-v1.md",
)
_POINTER = "phase4-multi-agent-collaboration-contract-v1.md"


class TestPhase4MultiAgentContractV1(unittest.TestCase):
    """Structural contract: sections, roles, gates, template fields, upstream pointers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _CONTRACT.read_text(encoding="utf-8")
        cls.template = _TEMPLATE.read_text(encoding="utf-8")

    def test_contract_file_exists(self) -> None:
        self.assertTrue(_CONTRACT.is_file())

    def test_required_sections_present(self) -> None:
        for section in (
            "## §1 适用范围",
            "## §2 四角色 Contract 表",
            "## §3 标准工作流",
            "## §4 Routing 决策树",
            "## §5 Handoff 与 STATE 字段",
            "## §6 与 Engineering Contract 映射",
            "## §7 验收与 Replay 入口",
            "## §8 禁止事项",
        ):
            self.assertIn(section, self.text, msg=f"missing {section}")

    def test_four_roles_with_contract_fields(self) -> None:
        roles = ("Orchestrator", "Implementer", "Reviewer", "Scribe")
        fields = ("may_do", "must_not", "inputs", "outputs", "done_when")
        for role in roles:
            self.assertIn(f"### 2.", self.text)
            role_block = self._role_section(role)
            self.assertTrue(role_block, msg=f"missing role block for {role}")
            for field in fields:
                self.assertIn(
                    f"**{field}**",
                    role_block,
                    msg=f"{role} missing {field}",
                )

    def test_orchestrator_must_not_bypass_reviewer(self) -> None:
        o_block = self._role_section("Orchestrator")
        self.assertRegex(
            o_block,
            r"must_not.*绕过.*Reviewer",
            msg="Orchestrator must_not bypass Reviewer",
        )
        self.assertIn("不可绕过", self.text)
        self.assertIn("P4-BAN-1", self.text)

    def test_implementer_must_not_modify_frame(self) -> None:
        b_block = self._role_section("Implementer")
        self.assertRegex(
            b_block,
            r"must_not.*FRAME",
            msg="Implementer must_not modify FRAME",
        )
        self.assertIn("P4-BAN-2", self.text)

    def test_workflow_sequence_o_b_c_d(self) -> None:
        self.assertIn("O → B → C → D", self.text)
        steps = ("[O]", "[B]", "[C]", "[D]")
        section3 = self._section_text("## §3", "## §4")
        for step in steps:
            self.assertIn(step, section3, msg=f"missing workflow step {step}")

    def test_two_typical_flows_documented(self) -> None:
        section3 = self._section_text("## §3", "## §4")
        self.assertIn("流程 (a)", section3)
        self.assertIn("流程 (b)", section3)
        self.assertTrue(
            "sequenceDiagram" in section3 or "并行" in section3,
            msg="expected mermaid or parallel flow description",
        )

    def test_routing_decision_tree_paths(self) -> None:
        section4 = self._section_text("## §4", "## §5")
        self.assertIn("直派 Implementer", section4)
        self.assertIn("governance-guard", section4)
        self.assertIn("stop_work", section4)
        self.assertIn("TEST-SUB-003", section4)

    def test_state_block_write_permissions_frozen(self) -> None:
        section5 = self._section_text("## §5", "## §6")
        for block in ("FRAME", "STATE", "B_REPORT", "C_REPORT", "D_REPORT"):
            self.assertIn(block, section5)
        self.assertIn("Orchestrator", section5)
        self.assertIn("Implementer", section5)
        self.assertIn("Reviewer", section5)
        self.assertIn("Scribe", section5)

    def test_ticket_template_fields_exist(self) -> None:
        for block in ("## FRAME", "## STATE", "## B_REPORT", "## C_REPORT", "## D_REPORT"):
            self.assertIn(block, self.template, msg=f"template missing {block}")

    def test_w5_t0_docs_have_upstream_contract_pointer(self) -> None:
        for path in _W5_DOCS:
            content = path.read_text(encoding="utf-8")
            self.assertIn(
                _POINTER,
                content,
                msg=f"{path.name} missing Phase 4 contract pointer",
            )

    def test_replay_entry_w4_t2_reference(self) -> None:
        section7 = self._section_text("## §7", "## §8")
        self.assertIn("W4-T2", section7)
        self.assertIn("test_phase4_multi_agent_contract_v1", section7)

    def _role_section(self, role: str) -> str:
        pattern = rf"### 2\.\d+ {re.escape(role)} \(.*?\)\n(.*?)(?=\n### 2\.|\n---\n|\n## §3)"
        match = re.search(pattern, self.text, re.DOTALL)
        return match.group(1) if match else ""

    def _section_text(self, start: str, end: str) -> str:
        start_idx = self.text.index(start)
        end_idx = self.text.index(end, start_idx)
        return self.text[start_idx:end_idx]


if __name__ == "__main__":
    unittest.main()
