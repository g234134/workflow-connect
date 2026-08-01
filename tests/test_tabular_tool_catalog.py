"""Unit tests for Tabular Tool Catalog v1 (W3-TL-T1)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_PATH = _REPO_ROOT / "tools" / "tabular_tool_catalog_v1.json"

_REQUIRED_TOP_LEVEL = frozenset({"schema_version", "catalog_revision", "description", "tools"})
_REQUIRED_TOOL_FIELDS = frozenset(
    {
        "tool_id",
        "type",
        "display_name",
        "module_path",
        "entry_kind",
        "entrypoint",
        "enabled",
        "cli_invocation",
        "applicable_conditions",
        "risk_notes",
        "verify_command",
    }
)
_ALLOWED_TYPES = frozenset(
    {"intake", "validation", "cleaning", "export", "orchestration", "helper"}
)
_ALLOWED_ENTRY_KINDS = frozenset({"python_cli", "python_module"})

# AC-1 minimum: MVP §2.3 hard entrypoints + §A auxiliary tools
_REQUIRED_TOOL_IDS = frozenset(
    {
        "intake.new_case",
        "validate.eligibility",
        "clean.phase_demo",
        "export.delivery_bundle",
        "orchestrate.e2e",
        "validate.output_guard",
        "index.cases",
        "lookup.history",
        "plan.cleaning_stages",
        "ui.local",
    }
)


def _load_catalog() -> dict:
    with _CATALOG_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


class TestTabularToolCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = _load_catalog()
        cls.tools = cls.catalog["tools"]
        cls.tool_by_id = {t["tool_id"]: t for t in cls.tools}

    def test_catalog_file_exists(self) -> None:
        self.assertTrue(_CATALOG_PATH.is_file())

    def test_top_level_schema(self) -> None:
        missing = _REQUIRED_TOP_LEVEL - set(self.catalog)
        self.assertFalse(missing, msg=f"missing top-level keys: {sorted(missing)}")
        self.assertEqual(self.catalog["schema_version"], "tabular_tool_catalog_v1")
        self.assertIsInstance(self.catalog["tools"], list)
        self.assertGreaterEqual(len(self.catalog["tools"]), len(_REQUIRED_TOOL_IDS))

    def test_each_tool_has_required_fields(self) -> None:
        for tool in self.tools:
            with self.subTest(tool_id=tool.get("tool_id")):
                missing = _REQUIRED_TOOL_FIELDS - set(tool)
                self.assertFalse(missing, msg=f"missing fields: {sorted(missing)}")
                self.assertIn(tool["type"], _ALLOWED_TYPES)
                self.assertIn(tool["entry_kind"], _ALLOWED_ENTRY_KINDS)
                self.assertIsInstance(tool["enabled"], bool)
                self.assertIsInstance(tool["applicable_conditions"], dict)
                self.assertIsInstance(tool["risk_notes"], list)
                self.assertTrue(tool["risk_notes"], msg="risk_notes must be non-empty")
                self.assertTrue(str(tool["verify_command"]).strip())

    def test_tool_ids_unique(self) -> None:
        ids = [t["tool_id"] for t in self.tools]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_minimum_tool_ids_present(self) -> None:
        present = {t["tool_id"] for t in self.tools}
        missing = _REQUIRED_TOOL_IDS - present
        self.assertFalse(missing, msg=f"missing required tool_ids: {sorted(missing)}")

    def test_enabled_tools_module_paths_exist(self) -> None:
        for tool in self.tools:
            if not tool.get("enabled"):
                continue
            module_path = tool.get("module_path")
            self.assertIsNotNone(module_path, msg=f"{tool['tool_id']}: module_path required when enabled")
            full = _REPO_ROOT / str(module_path)
            with self.subTest(tool_id=tool["tool_id"], path=module_path):
                self.assertTrue(full.is_file(), msg=f"module_path not found: {module_path}")

    def test_module_paths_under_allowed_roots(self) -> None:
        allowed_prefixes = ("scripts/", "notebooks/", "app/")
        for tool in self.tools:
            path = str(tool["module_path"])
            with self.subTest(tool_id=tool["tool_id"]):
                self.assertTrue(
                    path.startswith(allowed_prefixes),
                    msg=f"module_path must be under scripts/, notebooks/, or app/: {path}",
                )

    def test_no_gov_or_phase88_tool_ids(self) -> None:
        for tool in self.tools:
            tid = tool["tool_id"]
            with self.subTest(tool_id=tid):
                self.assertFalse(tid.startswith("obs."), msg="Gov Registry tool in tabular catalog")
                self.assertFalse(tid.startswith("kb."), msg="Gov Registry tool in tabular catalog")
                self.assertFalse(tid.startswith("llm."), msg="Phase 8.8 tool in tabular catalog")
                self.assertFalse(tid.startswith("skill-clean"), msg="Wave8 product card in tabular catalog")

    def test_orchestration_tools_flagged_non_single_step(self) -> None:
        for tool in self.tools:
            if tool["type"] != "orchestration":
                continue
            cond = tool["applicable_conditions"]
            with self.subTest(tool_id=tool["tool_id"]):
                self.assertTrue(
                    cond.get("non_single_step"),
                    msg="orchestration tools must set applicable_conditions.non_single_step=true",
                )

    def test_clean_phase_demo_risk_notes(self) -> None:
        tool = self.tool_by_id["clean.phase_demo"]
        joined = " ".join(tool["risk_notes"]).lower()
        self.assertIn("phase", joined)
        self.assertIn("demo", joined)


if __name__ == "__main__":
    unittest.main()
