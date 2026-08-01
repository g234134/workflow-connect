"""Structural checks for docs/phase3-5-cost-model-governance-contract-v1.md (WA-T3)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "phase3-5-cost-model-governance-contract-v1.md"

_REQUIRED_SECTIONS = (
    "§1 范围与术语",
    "§2 Gate 分类总表",
    "§3 PR 路径",
    "§4 Nightly/schedule 路径",
    "§5 模型/K-2 流量角色",
    "§6 成本/风险字段",
    "§7 失败处置与 rollback 指针",
    "§8 验证命令",
)

_GATE_SUBSECTIONS = (
    "### 2.1 Mandatory（PR 必过）",
    "### 2.2 Shadow-only（nightly / 内部对比；不阻塞主链）",
    "### 2.3 Optional（推荐；非 PR 硬门禁 trio）",
)

_MANDATORY_MARKERS = (
    "eval-gate-ci.yml",
    "tests.test_eval_gate",
    "eval_ci_check",
    "core-agent-smoke",
    "eval_gate_ci_subset",
)

_SHADOW_MARKERS = (
    "eval-shadow-nightly",
    "GOV_ENF_BLOCKING_CANARY=0",
    "shadow-only",
)

_TABLE_ROW_PATTERN = re.compile(r"^\| `?[A-Z]{2}-[A-Z0-9-]+`? \|")


class TestPhase35GovernanceContractV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _CONTRACT.read_text(encoding="utf-8")

    def test_contract_file_exists(self) -> None:
        self.assertTrue(_CONTRACT.is_file(), f"missing contract: {_CONTRACT}")

    def test_required_sections_present(self) -> None:
        for section in _REQUIRED_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, self.text)

    def test_three_gate_class_subsections(self) -> None:
        for subsection in _GATE_SUBSECTIONS:
            with self.subTest(subsection=subsection):
                self.assertIn(subsection, self.text)

    def test_gate_table_at_least_twelve_rows(self) -> None:
        section_match = re.search(
            r"## §2 Gate 分类总表.*?(?=\n## §3 )",
            self.text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(section_match, "§2 section not found")
        section = section_match.group(0)
        rows = [line for line in section.splitlines() if _TABLE_ROW_PATTERN.match(line)]
        self.assertGreaterEqual(
            len(rows),
            12,
            f"expected >=12 gate rows, got {len(rows)}: {rows[:3]}...",
        )

    def test_mandatory_table_references_eval_gate_ci_yml(self) -> None:
        mandatory_block = self._subsection_block("### 2.1 Mandatory（PR 必过）")
        self.assertIn("eval-gate-ci.yml", mandatory_block)
        for marker in _MANDATORY_MARKERS:
            with self.subTest(marker=marker):
                self.assertIn(marker, mandatory_block)

    def test_shadow_table_references_enf_blocking_canary_zero(self) -> None:
        shadow_block = self._subsection_block(
            "### 2.2 Shadow-only（nightly / 内部对比；不阻塞主链）"
        )
        for marker in _SHADOW_MARKERS:
            with self.subTest(marker=marker):
                self.assertIn(marker, shadow_block)

    def test_phase35_does_not_authorize_prod_canary(self) -> None:
        self.assertIn("不包含", self.text)
        self.assertIn("GOV_ENF_BLOCKING_CANARY=1", self.text)
        self.assertRegex(
            self.text,
            r"(未授权|不包含).*(canary|Phase 2)",
        )

    def test_verification_commands_reference_unittest_module(self) -> None:
        self.assertIn("tests.test_phase3_5_governance_contract_v1", self.text)
        self.assertIn("_ops_cycle.py checklist --mode full", self.text)

    def _subsection_block(self, heading: str) -> str:
        start = self.text.index(heading)
        rest = self.text[start + len(heading) :]
        next_heading = re.search(r"\n### ", rest)
        end = start + len(heading) + (next_heading.start() if next_heading else len(rest))
        return self.text[start:end]


if __name__ == "__main__":
    unittest.main()
