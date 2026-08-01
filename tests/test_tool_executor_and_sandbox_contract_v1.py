"""Structural contract tests for docs/tool-executor-and-sandbox-safety-contract-v1.md (WB-T2)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "tool-executor-and-sandbox-safety-contract-v1.md"
_OUTBOX_SPEC = _REPO_ROOT / "docs" / "tabular-tool-outbox-spec.md"

_EXECUTION_MODES = frozenset({"dry_run", "plan_only", "execute", "sandbox_end_to_end"})
_ALLOWLIST_CASE_REFS = frozenset(
    {"demo_phase", "sampleco/2026-0001", "additional_demo", "sandbox_client"}
)
_SANDBOX_E2E_ALLOWLIST = frozenset({"additional_demo"})

_FORBIDDEN_DARK_PATHS = (
    "core/tool_executor.py",
    "orchestration_bridge_outbox",
    "Langfuse",
)

_REQUIRED_SECTIONS = (
    "## §1 范围与分轨",
    "## §2 四级 `execution_mode` 与 case allowlist",
    "## §3 `execute_tabular_tool` 回传契约",
    "## §4 Tabular outbox 写入条件",
    "## §5 Sandbox 安全边界",
    "## §6 Observability 与 join 规则",
    "## §7 最小示例（可复制）",
    "## §8 PR CI 与 WA-T3 P3.5 对齐",
    "## §9 验证命令",
)

_REQUIRED_RESULT_KEYS = frozenset(
    {"ok", "message", "tool_id", "execution_mode", "side_effects"}
)


class TestToolExecutorAndSandboxContractV1(unittest.TestCase):
    """Contract SSOT: modes, allowlist, return shape, outbox rules, dark-path ban."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _CONTRACT.read_text(encoding="utf-8")

    def test_contract_file_exists(self) -> None:
        self.assertTrue(_CONTRACT.is_file(), f"missing contract: {_CONTRACT}")

    def test_required_sections_present(self) -> None:
        for section in _REQUIRED_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, self.text)

    def test_four_execution_modes_documented(self) -> None:
        section2 = self._section_text("## §2", "## §3")
        for mode in _EXECUTION_MODES:
            with self.subTest(mode=mode):
                self.assertIn(f"`{mode}`", section2)

    def test_allowlist_case_refs_in_matrix(self) -> None:
        section2 = self._section_text("## §2", "## §3")
        for case_ref in _ALLOWLIST_CASE_REFS:
            with self.subTest(case_ref=case_ref):
                self.assertIn(f"`{case_ref}`", section2)

    def test_sandbox_e2e_only_additional_demo(self) -> None:
        section2 = self._section_text("## §2", "## §3")
        self.assertIn("`additional_demo`", section2)
        self.assertIn("SANDBOX_E2E_ALLOWLIST", section2)
        # sandbox_client and demo_phase must be blocked for sandbox_end_to_end
        self.assertRegex(section2, r"sandbox_end_to_end.*❌|❌.*sandbox_end_to_end")

    def test_sandbox_allowlist_matches_delivery_module(self) -> None:
        from delivery.sandbox_delivery_bundle_v1 import SANDBOX_E2E_ALLOWLIST

        self.assertEqual(set(SANDBOX_E2E_ALLOWLIST), _SANDBOX_E2E_ALLOWLIST)

    def test_experiment_allowlist_matches_orchestrator(self) -> None:
        import importlib.util

        script = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
        spec = importlib.util.spec_from_file_location("agent_exp", script)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(set(mod._ALLOWLIST_CASE_REFS), _ALLOWLIST_CASE_REFS)

    def test_execute_tabular_tool_required_keys(self) -> None:
        section3 = self._section_text("## §3", "## §4")
        for key in _REQUIRED_RESULT_KEYS:
            with self.subTest(key=key):
                self.assertIn(f'"{key}"', section3)

    def test_outbox_write_only_execute_modes(self) -> None:
        section4 = self._section_text("## §4", "## §5")
        self.assertIn("dry_run", section4)
        self.assertRegex(section4, r"dry_run.*否|否.*dry_run")
        self.assertRegex(section4, r"plan_only.*否|否.*plan_only")
        self.assertIn("execute", section4)
        self.assertIn("sandbox_end_to_end", section4)

    def test_forbidden_dark_paths_documented(self) -> None:
        section1 = self._section_text("## §1", "## §2")
        for path in _FORBIDDEN_DARK_PATHS:
            with self.subTest(path=path):
                self.assertIn(path, section1)

    def test_contract_forbids_import_dark_tool_executor(self) -> None:
        self.assertRegex(
            self.text,
            r"禁止.*import.*core\.tool_executor|FORBID.*core\.tool_executor",
        )

    def test_sandbox_safety_subprocess_cwd_and_traversal(self) -> None:
        section5 = self._section_text("## §5", "## §6")
        self.assertIn("timeout", section5)
        self.assertIn("cwd", section5)
        self.assertIn("..", section5)
        self.assertRegex(section5, r"case_dir_out_of_bounds|逃逸")

    def test_dry_run_example_command_copyable(self) -> None:
        section7 = self._section_text("## §7", "## §8")
        self.assertIn(
            "python scripts/run_tabular_intake_tool_path.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json",
            section7,
        )

    def test_p35_execute_optional_not_mandatory_pr_gate(self) -> None:
        section8 = self._section_text("## §8", "## §9")
        self.assertIn("optional", section8)
        self.assertIn("phase3-5-cost-model-governance-contract-v1.md", section8)
        self.assertRegex(section8, r"禁止.*--execute|不得.*execute")

    def test_outbox_spec_has_contract_pointer(self) -> None:
        content = _OUTBOX_SPEC.read_text(encoding="utf-8")
        self.assertIn("tool-executor-and-sandbox-safety-contract-v1.md", content)

    def test_phase_88_completion_anchor(self) -> None:
        self.assertIn("58%", self.text)
        self.assertIn("82%", self.text)

    def _section_text(self, start: str, end: str) -> str:
        pattern = re.escape(start) + r".*?(?=" + re.escape(end) + r")"
        match = re.search(pattern, self.text, flags=re.DOTALL)
        self.assertIsNotNone(match, f"section {start} not found")
        return match.group(0)


if __name__ == "__main__":
    unittest.main()
