"""Unit tests for Non-Tabular Tool Selector v1 stub (W9-T3)."""

from __future__ import annotations

import unittest

from tools.non_tabular_tool_selector_v1 import select_non_tabular_tools

_REQUIRED_TOP_KEYS = frozenset(
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
_REQUIRED_PLANNED_KEYS = frozenset(
    {
        "tool_id",
        "reason",
        "input_kind",
        "output_kind",
        "maturity",
        "symbolic_only",
    }
)


def _assert_result_shape(result: dict) -> None:
    missing = _REQUIRED_TOP_KEYS - set(result)
    assert not missing, f"missing top-level keys: {sorted(missing)}"
    assert isinstance(result["ok"], bool)
    assert isinstance(result["message"], str)
    assert isinstance(result["selector_rule_id"], str)
    assert result["plan_only"] is True
    assert result["flow_family"] == "non_tabular"
    assert isinstance(result["planned_tools"], list)
    for item in result["planned_tools"]:
        missing_p = _REQUIRED_PLANNED_KEYS - set(item)
        assert not missing_p, f"missing planned_tools keys: {sorted(missing_p)}"


class TestNonTabularToolSelectorV1(unittest.TestCase):
    def test_result_dict_has_required_keys_nt_a(self) -> None:
        result = select_non_tabular_tools(
            "non_tabular.document.extract",
            "docu-corp",
        )
        _assert_result_shape(result)

    def test_nt_a_task_type_returns_document_tools(self) -> None:
        result = select_non_tabular_tools(
            "non_tabular.document.extract",
            "docu-corp",
            max_tools=3,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["profile_tier"], "NT-A")
        self.assertGreaterEqual(len(result["planned_tools"]), 1)
        self.assertLessEqual(len(result["planned_tools"]), 2)
        input_kinds = {item["input_kind"] for item in result["planned_tools"]}
        self.assertEqual(input_kinds, {"document"})
        tool_ids = {item["tool_id"] for item in result["planned_tools"]}
        self.assertTrue(tool_ids.issubset({"text_extractor", "doc_classifier"}))
        for item in result["planned_tools"]:
            self.assertTrue(item["symbolic_only"])
            self.assertEqual(item["maturity"], "experimental")

    def test_nt_a_hyphenated_task_type_alias(self) -> None:
        result = select_non_tabular_tools(
            "non-tabular.document.clean_and_annotate",
            "docu-corp",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["profile_tier"], "NT-A")
        tool_ids = [item["tool_id"] for item in result["planned_tools"]]
        self.assertIn("text_extractor", tool_ids)

    def test_nt_b_task_type_returns_log_tools(self) -> None:
        result = select_non_tabular_tools(
            "non_tabular.log.analyze",
            "log-analytics-co",
            max_tools=3,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["profile_tier"], "NT-B")
        self.assertGreaterEqual(len(result["planned_tools"]), 1)
        self.assertLessEqual(len(result["planned_tools"]), 2)
        input_kinds = {item["input_kind"] for item in result["planned_tools"]}
        self.assertEqual(input_kinds, {"log"})
        tool_ids = {item["tool_id"] for item in result["planned_tools"]}
        self.assertTrue(tool_ids.issubset({"log_parser", "anomaly_summarizer"}))

    def test_nt_b_hyphenated_task_type_alias(self) -> None:
        result = select_non_tabular_tools(
            "non-tabular.log.parse_and_summarize",
            "log-analytics-co",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["profile_tier"], "NT-B")
        tool_ids = [item["tool_id"] for item in result["planned_tools"]]
        self.assertIn("log_parser", tool_ids)

    def test_max_tools_limits_output(self) -> None:
        result = select_non_tabular_tools(
            "non_tabular.document.extract",
            "docu-corp",
            max_tools=1,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["planned_tools"]), 1)
        self.assertEqual(result["planned_tools"][0]["tool_id"], "text_extractor")

    def test_non_non_tabular_family_returns_error(self) -> None:
        result = select_non_tabular_tools(
            "tabular.cleaning.mvp",
            "demo_phase",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.not_non_tabular_family")
        self.assertEqual(result["planned_tools"], [])
        self.assertIn("not non_tabular family", result["message"])

    def test_gov_task_type_returns_error(self) -> None:
        result = select_non_tabular_tools(
            "gov.observability.eval",
            "ops",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["planned_tools"], [])

    def test_unknown_non_tabular_profile_returns_error(self) -> None:
        result = select_non_tabular_tools(
            "non_tabular.generic.transform",
            "unknown-client",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.unknown_non_tabular_profile")
        self.assertEqual(result["planned_tools"], [])


if __name__ == "__main__":
    unittest.main()
