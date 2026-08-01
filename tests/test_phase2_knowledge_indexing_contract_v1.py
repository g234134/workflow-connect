"""Structure / cross-ref checks for phase2-knowledge-indexing-contract-v1 (WA-T1).

Doc-only contract: no live PG/Qdrant required.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "phase2-knowledge-indexing-contract-v1.md"
_KNOWLEDGE_LAYER = _REPO_ROOT / "docs" / "knowledge-layer.md"
_WORKFLOW_INDEX = _REPO_ROOT / "04_Workflows" / "WORKFLOW_INDEX.md"
_INDEXING_SCRIPT = _REPO_ROOT / "04_Workflows" / "_indexing_and_audit.py"
_TICKET_STATE = (
    _REPO_ROOT / "04_Workflows" / "tickets" / "WA-T1-phase2-knowledge-indexing-contract-v1_state.md"
)

_REQUIRED_SECTIONS = (
    "## §1 收录定义",
    "## §2 双 Pipeline 边界",
    "## §3 Metadata Schema v0.1",
    "## §4 命名与路径规则",
    "## §5 Wave / Phase 标注规则",
    "## §6 登记流程",
    "## §7 验收命令",
)

_THREE_STATES = ("indexed", "catalogued", "excluded")
_FRONT_MATTER_FIELDS = ("phase_tag", "wave_tag", "content_class", "index_tier")
_CONTENT_CLASS_VALUES = ("governance", "spec", "runbook", "skill", "experiment")
_INDEX_TIER_VALUES = ("A", "B", "draft")


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing required file: {path.relative_to(_REPO_ROOT)}")
    return path.read_text(encoding="utf-8")


class TestPhase2KnowledgeIndexingContractV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = _read(_CONTRACT)
        cls.knowledge_layer = _read(_KNOWLEDGE_LAYER)
        cls.workflow_index = _read(_WORKFLOW_INDEX)

    def test_contract_file_exists(self) -> None:
        self.assertTrue(_CONTRACT.is_file())

    def test_all_required_section_headings_present(self) -> None:
        missing = [h for h in _REQUIRED_SECTIONS if h not in self.contract]
        self.assertEqual(missing, [], f"missing section headings: {missing}")

    def test_three_indexing_states_defined(self) -> None:
        for state in _THREE_STATES:
            with self.subTest(state=state):
                self.assertIn(f"**`{state}`**", self.contract)

    def test_dual_pipeline_collections_named(self) -> None:
        self.assertIn("document_chunks", self.contract)
        self.assertIn("repo_chunks", self.contract)
        self.assertIn("graphrag_jobs", self.contract)
        self.assertIn("excluded from primary retrieval", self.contract)

    def test_front_matter_fields_in_yaml_sample(self) -> None:
        yaml_block = re.search(r"```yaml\s*(.*?)```", self.contract, re.DOTALL)
        self.assertIsNotNone(yaml_block, "expected YAML front-matter sample block")
        sample = yaml_block.group(1)
        for field in _FRONT_MATTER_FIELDS:
            with self.subTest(field=field):
                self.assertIn(f"{field}:", sample)

    def test_content_class_and_index_tier_enums_in_contract(self) -> None:
        for value in _CONTENT_CLASS_VALUES:
            with self.subTest(content_class=value):
                self.assertIn(value, self.contract)
        for tier in _INDEX_TIER_VALUES:
            with self.subTest(index_tier=tier):
                self.assertRegex(self.contract, rf"\b{tier}\b")

    def test_knowledge_layer_cross_ref_to_contract(self) -> None:
        self.assertIn("phase2-knowledge-indexing-contract-v1", self.knowledge_layer)

    def test_workflow_index_contains_wa_t1_entry(self) -> None:
        self.assertIn("WA-T1", self.workflow_index)
        self.assertIn("phase2-knowledge-indexing-contract-v1", self.workflow_index)

    def test_contract_prioritizes_over_draft_knowledge_layer_paragraph(self) -> None:
        self.assertIn("以本 contract 为准", self.contract)
        self.assertIn("knowledge-layer.md", self.contract)

    def test_indexing_and_audit_script_exists(self) -> None:
        self.assertTrue(_INDEXING_SCRIPT.is_file(), "_indexing_and_audit.py must exist for §7 reference")

    def test_ticket_state_file_exists(self) -> None:
        self.assertTrue(_TICKET_STATE.is_file())

    def test_unittest_module_named_in_contract_section_7(self) -> None:
        self.assertIn("tests.test_phase2_knowledge_indexing_contract_v1", self.contract)


class TestPhase2ContractVerificationCommand(unittest.TestCase):
    """Smoke: the documented unittest command exits 0 (subset run)."""

    def test_documented_unittest_command_runs(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.test_phase2_knowledge_indexing_contract_v1.TestPhase2KnowledgeIndexingContractV1",
                "-v",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"unittest failed:\nstdout={proc.stdout}\nstderr={proc.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
