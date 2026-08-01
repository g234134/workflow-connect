"""Contract tests for Tool Catalog and Selector SSOT (WB-T1)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from tools.non_tabular_tool_selector_v1 import select_non_tabular_tools
from tools.tabular_tool_selector import select_tabular_tools

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "tool-catalog-and-selector-contract-v1.md"
_TABULAR_CATALOG = _REPO_ROOT / "tools" / "tabular_tool_catalog_v1.json"
_NT_CATALOG = _REPO_ROOT / "tools" / "non_tabular_tool_catalog_v1.json"
_DEMO_PHASE = _REPO_ROOT / "cases" / "demo_phase"

_TABULAR_CATEGORY_PREFIXES = (
    "intake.",
    "validate.",
    "clean.",
    "export.",
    "orchestrate.",
    "index.",
    "lookup.",
    "plan.",
    "ui.",
)
_FORBIDDEN_TABULAR_PREFIXES = ("obs.", "kb.", "llm.", "skill-clean", "nt.", "non_tabular.")

_TABULAR_SELECTOR_TOP = frozenset(
    {"ok", "message", "selector_rule_id", "plan_only", "candidate_tools"}
)
_TABULAR_CANDIDATE_KEYS = frozenset(
    {"tool_id", "reason", "requires_force", "human_review_required"}
)
_NT_SELECTOR_TOP = frozenset(
    {
        "ok",
        "message",
        "selector_rule_id",
        "plan_only",
        "flow_family",
        "profile_tier",
        "planned_tools",
    }
)
_NT_PLANNED_KEYS = frozenset(
    {"tool_id", "reason", "input_kind", "output_kind", "maturity", "symbolic_only"}
)


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


class TestToolCatalogAndSelectorContractV1(unittest.TestCase):
    """Structural contract: four tracks, namespaces, catalog JSON, selector shapes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = _CONTRACT.read_text(encoding="utf-8")
        cls.tabular = _load_json(_TABULAR_CATALOG)
        cls.nt = _load_json(_NT_CATALOG)
        cls.tabular_ids = {t["tool_id"] for t in cls.tabular["tools"]}
        cls.nt_ids = {t["tool_id"] for t in cls.nt["tools"]}

    def test_contract_file_exists(self) -> None:
        self.assertTrue(_CONTRACT.is_file())

    def test_required_sections_present(self) -> None:
        for section in (
            "## §1 适用范围",
            "## §2 四轨对照表",
            "## §3 tool_id 命名规则",
            "## §4 Selector 输入 / 输出 dict 形状",
            "## §5 与 Wave A P4 角色边界交叉引用",
            "## §6 Wave C 假设",
        ):
            self.assertIn(section, self.contract, msg=f"missing {section}")

    def test_ssot_paths_documented(self) -> None:
        self.assertIn("tools/tabular_tool_catalog_v1.json", self.contract)
        self.assertIn("tools/non_tabular_tool_catalog_v1.json", self.contract)
        self.assertIn("governed_by", self.contract)

    def test_four_tracks_and_plan_only_documented(self) -> None:
        for track in ("tabular_mvp", "non_tabular_shadow", "gov_registry", "phase_8.8_spec"):
            self.assertIn(track, self.contract, msg=f"missing governed_by track {track}")
        self.assertIn("plan_only", self.contract)
        self.assertIn("phase4-multi-agent-collaboration-contract-v1.md", self.contract)

    def test_tabular_catalog_schema(self) -> None:
        self.assertEqual(self.tabular["schema_version"], "tabular_tool_catalog_v1")
        self.assertIsInstance(self.tabular["tools"], list)
        self.assertGreater(len(self.tabular["tools"]), 0)
        for tool in self.tabular["tools"]:
            self.assertIn("tool_id", tool)
            self.assertIn("enabled", tool)

    def test_non_tabular_catalog_schema(self) -> None:
        self.assertEqual(self.nt["schema_version"], "non_tabular_tool_catalog_v1")
        self.assertIsInstance(self.nt["tools"], list)
        self.assertGreaterEqual(len(self.nt["tools"]), 4)
        for tool in self.nt["tools"]:
            self.assertIn("tool_id", tool)
            self.assertIn("input_kind", tool)
            self.assertIn("output_kind", tool)

    def test_tabular_tool_ids_use_allowed_namespace(self) -> None:
        for tool_id in self.tabular_ids:
            with self.subTest(tool_id=tool_id):
                self.assertTrue(
                    any(tool_id.startswith(p) for p in _TABULAR_CATEGORY_PREFIXES),
                    msg=f"tabular tool_id outside allowed category prefixes: {tool_id}",
                )
                for forbidden in _FORBIDDEN_TABULAR_PREFIXES:
                    self.assertFalse(
                        tool_id.startswith(forbidden),
                        msg=f"forbidden prefix in tabular catalog: {tool_id}",
                    )

    def test_no_llm_or_gov_ids_in_tabular_json(self) -> None:
        for tool_id in self.tabular_ids:
            with self.subTest(tool_id=tool_id):
                self.assertFalse(tool_id.startswith("obs."))
                self.assertFalse(tool_id.startswith("kb."))
                self.assertFalse(tool_id.startswith("llm."))

    def test_no_cross_track_id_collision(self) -> None:
        overlap = self.tabular_ids & self.nt_ids
        self.assertFalse(overlap, msg=f"tool_id collision between catalogs: {sorted(overlap)}")
        for nt_id in self.nt_ids:
            with self.subTest(tool_id=nt_id):
                self.assertNotIn(nt_id, self.tabular_ids)
                for prefix in _TABULAR_CATEGORY_PREFIXES:
                    self.assertFalse(
                        nt_id.startswith(prefix),
                        msg=f"NT tool_id looks like tabular prefix: {nt_id}",
                    )

    def test_nt_tool_ids_not_in_tabular_namespace(self) -> None:
        expected_nt = {"text_extractor", "doc_classifier", "log_parser", "anomaly_summarizer"}
        self.assertTrue(expected_nt.issubset(self.nt_ids))

    def test_tabular_selector_output_required_keys(self) -> None:
        with (_DEMO_PHASE / "intake.json").open(encoding="utf-8") as fh:
            intake = json.load(fh)
        result = select_tabular_tools(
            str(_DEMO_PHASE),
            "clean",
            intake=intake,
            gate_notes=["phase_like", "phase_demo"],
        )
        missing = _TABULAR_SELECTOR_TOP - set(result)
        self.assertFalse(missing, msg=f"missing tabular selector keys: {sorted(missing)}")
        self.assertTrue(result["ok"])
        self.assertTrue(result["plan_only"])
        for item in result["candidate_tools"]:
            missing_c = _TABULAR_CANDIDATE_KEYS - set(item)
            self.assertFalse(missing_c, msg=f"missing candidate keys: {sorted(missing_c)}")
            self.assertIn(item["tool_id"], self.tabular_ids)

    def test_non_tabular_selector_output_required_keys(self) -> None:
        result = select_non_tabular_tools(
            "non_tabular.document.extract",
            "docu-corp",
        )
        missing = _NT_SELECTOR_TOP - set(result)
        self.assertFalse(missing, msg=f"missing NT selector keys: {sorted(missing)}")
        self.assertTrue(result["ok"])
        self.assertTrue(result["plan_only"])
        self.assertEqual(result["flow_family"], "non_tabular")
        for item in result["planned_tools"]:
            missing_p = _NT_PLANNED_KEYS - set(item)
            self.assertFalse(missing_p, msg=f"missing planned_tools keys: {sorted(missing_p)}")
            self.assertIn(item["tool_id"], self.nt_ids)
            self.assertTrue(item["symbolic_only"])

    def test_wave_c_assumptions_section(self) -> None:
        section6 = self._section_text("## §6", "## §7")
        self.assertIn("candidate_tools", section6)
        self.assertIn("prod INT gate", section6)
        self.assertRegex(section6, r"不得假设|不得假设")

    def test_trace_concatenation_rule_documented(self) -> None:
        section4 = self._section_text("## §4", "## §5")
        self.assertIn("case_ref", section4)
        self.assertIn("selector_rule_id", section4)
        self.assertIn("catalog_tool_count", section4)
        self.assertIn("selector_candidate_count", section4)

    def _section_text(self, start: str, end: str) -> str:
        start_idx = self.contract.index(start)
        end_idx = self.contract.index(end, start_idx)
        return self.contract[start_idx:end_idx]


if __name__ == "__main__":
    unittest.main()
