"""Consistency checks: routing eval cases v1 vs intake routing catalog (W2-T2)."""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_PATH = _REPO_ROOT / "routing" / "intake_routing_catalog_v1.yaml"
_CASES_PATH = _REPO_ROOT / "routing" / "routing_eval_cases_v1.yaml"

_REQUIRED_CASE_FIELDS = frozenset(
    {
        "id",
        "task_type",
        "input_summary",
        "expected_families",
        "expected_tool_ids",
    }
)


def _load_yaml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise unittest.SkipTest("pyyaml not installed; skip YAML parse test") from exc
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise AssertionError(f"{path.name} root must be a mapping")
    return data


def _allowed_tool_ids_for_route(route: dict) -> set[str]:
    allowed: set[str] = set(route.get("tool_ids") or [])
    allowed.update(route.get("optional_tool_ids") or [])
    allowed.update(route.get("chains") or [])
    orch = route.get("orchestration_tool_id")
    if orch:
        allowed.add(str(orch))
    return allowed


class TestRoutingEvalCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _CASES_PATH.is_file():
            raise unittest.SkipTest(f"missing cases file: {_CASES_PATH}")
        if not _CATALOG_PATH.is_file():
            raise unittest.SkipTest(f"missing catalog: {_CATALOG_PATH}")
        cls.cases_doc = _load_yaml(_CASES_PATH)
        cls.catalog = _load_yaml(_CATALOG_PATH)
        cls.routes_by_type = {r["task_type"]: r for r in cls.catalog["routes"]}
        cls.cases = cls.cases_doc.get("cases") or []

    def test_cases_file_schema(self) -> None:
        self.assertEqual(self.cases_doc.get("schema_version"), "routing_eval_cases_v1")
        self.assertIsInstance(self.cases, list)
        self.assertGreaterEqual(len(self.cases), 2)

    def test_case_ids_unique(self) -> None:
        ids = [c["id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate case id: {ids}")

    def test_each_case_has_required_fields(self) -> None:
        for case in self.cases:
            with self.subTest(case_id=case.get("id")):
                missing = _REQUIRED_CASE_FIELDS - set(case)
                self.assertFalse(missing, msg=f"missing fields: {sorted(missing)}")

    def test_task_types_exist_in_catalog(self) -> None:
        for case in self.cases:
            task_type = case["task_type"]
            with self.subTest(case_id=case["id"], task_type=task_type):
                self.assertIn(
                    task_type,
                    self.routes_by_type,
                    msg=f"task_type {task_type!r} not in intake catalog",
                )

    def test_expected_families_match_catalog(self) -> None:
        for case in self.cases:
            route = self.routes_by_type[case["task_type"]]
            catalog_family = route["preferred_tool_family"]
            with self.subTest(case_id=case["id"]):
                self.assertIn(
                    catalog_family,
                    case["expected_families"],
                    msg=f"expected_families should include {catalog_family!r}",
                )

    def test_expected_tool_ids_subset_of_catalog(self) -> None:
        for case in self.cases:
            route = self.routes_by_type[case["task_type"]]
            allowed = _allowed_tool_ids_for_route(route)
            acceptable_orch = set(case.get("acceptable_orchestration_tool_ids") or [])
            optional = set(case.get("optional_tool_ids") or [])
            allowed |= acceptable_orch | optional
            for tid in case.get("expected_tool_ids") or []:
                with self.subTest(case_id=case["id"], tool_id=tid):
                    self.assertIn(
                        tid,
                        allowed,
                        msg=f"tool_id {tid!r} not in catalog route allowed set",
                    )

    def test_tabular_mvp_case_present(self) -> None:
        tabular = [c for c in self.cases if c["task_type"] == "tabular.cleaning.mvp"]
        self.assertGreaterEqual(len(tabular), 1)
        demo = next((c for c in tabular if c["id"] == "tabular_demo_phase_clean"), None)
        self.assertIsNotNone(demo)
        self.assertIn("validate.eligibility", demo["expected_tool_ids"])

    def test_gov_eval_case_present(self) -> None:
        gov = [c for c in self.cases if c["task_type"] == "gov.observability.eval"]
        self.assertEqual(len(gov), 1)
        case = gov[0]
        self.assertIn("gov_registry", case["expected_families"])
        self.assertTrue(any(t.startswith("obs.eval.") for t in case["expected_tool_ids"]))


if __name__ == "__main__":
    unittest.main()
