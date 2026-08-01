"""Schema checks for intake routing catalog v1 (W2-T1)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_PATH = _REPO_ROOT / "routing" / "intake_routing_catalog_v1.yaml"

_REQUIRED_TOP = frozenset({"schema_version", "catalog_revision", "description", "tool_families", "routes"})
_REQUIRED_ROUTE_FIELDS = frozenset(
    {
        "task_type",
        "preferred_tool_family",
        "tool_ids",
        "eval_profile",
    }
)
_KNOWN_FAMILIES = frozenset(
    {
        "tabular_mvp",
        "gov_registry",
        "product_skill_card",
        "phase_8_8_spec",
        "hq_ops",
        "hq_routing",
        "h_line_context",
        "h_line_subagent",
    }
)
_FAMILY_ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "tabular_mvp": re.compile(r"^(intake|validate|clean|export|orchestrate|index|lookup|plan|ui)\."),
    "gov_registry": re.compile(r"^(obs|kb)\."),
}
_FORBIDDEN_TOOL_ID_PREFIXES = ("skill-clean", "llm.")


def _load_catalog() -> dict:
    text = _CATALOG_PATH.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ImportError:
        raise unittest.SkipTest("pyyaml not installed; skip YAML parse test")
    if not isinstance(data, dict):
        raise AssertionError("catalog root must be a mapping")
    return data


class TestIntakeRoutingCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _CATALOG_PATH.is_file():
            raise unittest.SkipTest(f"missing catalog: {_CATALOG_PATH}")
        cls.catalog = _load_catalog()
        cls.routes = cls.catalog["routes"]

    def test_catalog_file_exists(self) -> None:
        self.assertTrue(_CATALOG_PATH.is_file())

    def test_top_level_schema(self) -> None:
        missing = _REQUIRED_TOP - set(self.catalog)
        self.assertFalse(missing, msg=f"missing top-level keys: {sorted(missing)}")
        self.assertEqual(self.catalog["schema_version"], "intake_routing_catalog_v1")
        self.assertIsInstance(self.catalog["routes"], list)
        self.assertGreaterEqual(len(self.catalog["routes"]), 2)

    def test_tool_families_known(self) -> None:
        families = set(self.catalog.get("tool_families") or {})
        unknown = families - _KNOWN_FAMILIES
        self.assertFalse(unknown, msg=f"unknown tool_families keys: {sorted(unknown)}")

    def test_task_types_unique(self) -> None:
        types = [r["task_type"] for r in self.routes]
        self.assertEqual(len(types), len(set(types)), msg=f"duplicate task_type: {types}")

    def test_each_route_has_required_fields(self) -> None:
        for route in self.routes:
            with self.subTest(task_type=route.get("task_type")):
                missing = _REQUIRED_ROUTE_FIELDS - set(route)
                self.assertFalse(missing, msg=f"missing fields: {sorted(missing)}")
                family = route["preferred_tool_family"]
                self.assertIn(family, _KNOWN_FAMILIES)
                self.assertIsInstance(route["tool_ids"], list)

    def test_no_forbidden_tool_id_families(self) -> None:
        for route in self.routes:
            for tid in route.get("tool_ids") or []:
                with self.subTest(task_type=route["task_type"], tool_id=tid):
                    for prefix in _FORBIDDEN_TOOL_ID_PREFIXES:
                        self.assertFalse(
                            str(tid).startswith(prefix),
                            msg=f"forbidden tool_id family prefix {prefix!r}",
                        )

    def test_tool_ids_match_preferred_family_pattern(self) -> None:
        for route in self.routes:
            family = route["preferred_tool_family"]
            pattern = _FAMILY_ID_PATTERNS.get(family)
            if pattern is None:
                continue
            for tid in route.get("tool_ids") or []:
                with self.subTest(task_type=route["task_type"], tool_id=tid):
                    self.assertRegex(str(tid), pattern.pattern)

    def test_tabular_mvp_route_present(self) -> None:
        by_type = {r["task_type"]: r for r in self.routes}
        self.assertIn("tabular.cleaning.mvp", by_type)
        route = by_type["tabular.cleaning.mvp"]
        self.assertEqual(route["preferred_tool_family"], "tabular_mvp")
        self.assertIn("validate.eligibility", route["tool_ids"])
        self.assertIn("clean.phase_demo", route["tool_ids"])
        self.assertIn("export.delivery_bundle", route["tool_ids"])
        self.assertEqual(route["entrypoint"], "scripts/run_case_e2e_validation.py")

    def test_gov_eval_route_present(self) -> None:
        by_type = {r["task_type"]: r for r in self.routes}
        self.assertIn("gov.observability.eval", by_type)
        route = by_type["gov.observability.eval"]
        self.assertEqual(route["preferred_tool_family"], "gov_registry")
        tool_ids = route["tool_ids"]
        self.assertTrue(any(t.startswith("obs.eval.") for t in tool_ids))

    def test_kb_index_route_present(self) -> None:
        by_type = {r["task_type"]: r for r in self.routes}
        self.assertIn("kb.index.bootstrap", by_type)
        route = by_type["kb.index.bootstrap"]
        self.assertIn("kb.index.bootstrap", route["tool_ids"])
        self.assertIn("kb.index.rag_smoke", route["tool_ids"])
        forbidden = route.get("forbidden_tool_ids") or []
        self.assertIn("kb.index.selector_gate", forbidden)


if __name__ == "__main__":
    unittest.main()
