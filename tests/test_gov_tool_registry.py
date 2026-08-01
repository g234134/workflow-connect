"""Unit tests for Gov Tool Catalog registry v1 (B-F1)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.gov_tool_registry import (  # noqa: E402
    default_cards_dir,
    load_gov_tool_cards,
    load_schema,
    validate_all_gov_tool_cards,
    validate_gov_tool_card,
)

_REQUIRED_TOOL_IDS = frozenset(
    {
        "obs.eval.export",
        "obs.eval.ci_check",
        "obs.eval.stats",
        "obs.eval.report",
        "obs.eval.correlate",
        "obs.trace.query",
        "obs.wf.status_summary",
        "kb.index.bootstrap",
        "kb.index.rag_smoke",
        "kb.index.selector_gate",
        "obs.eval.triage",
    }
)


class TestGovToolRegistry(unittest.TestCase):
    def test_load_production_cards(self) -> None:
        cards = load_gov_tool_cards(repo_root=_REPO_ROOT)
        tool_ids = {str(c["tool_id"]) for c in cards}
        self.assertEqual(tool_ids, _REQUIRED_TOOL_IDS)
        self.assertEqual(len(cards), 11)

    def test_validate_all_production_cards_ok(self) -> None:
        result = validate_all_gov_tool_cards(repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"], msg=json.dumps(result, indent=2))
        self.assertEqual(result["total"], 11)
        self.assertEqual(result["passed"], 11)
        self.assertEqual(result["failed"], 0)

    def test_composite_card_allows_null_module_path(self) -> None:
        schema = load_schema(repo_root=_REPO_ROOT)
        triage = next(
            c for c in load_gov_tool_cards(repo_root=_REPO_ROOT) if c["tool_id"] == "obs.eval.triage"
        )
        known = {str(c["tool_id"]) for c in load_gov_tool_cards(repo_root=_REPO_ROOT)}
        result = validate_gov_tool_card(triage, repo_root=_REPO_ROOT, schema=schema, known_tool_ids=known)
        self.assertTrue(result["ok"], msg=result.get("errors"))
        self.assertEqual(triage["entry_kind"], "composite")
        self.assertIsNone(triage["module_path"])
        self.assertIsNone(triage["entrypoint"])

    def test_selector_gate_is_skeleton_reference(self) -> None:
        gate = next(
            c for c in load_gov_tool_cards(repo_root=_REPO_ROOT) if c["tool_id"] == "kb.index.selector_gate"
        )
        self.assertTrue(gate.get("skeleton"))
        self.assertEqual(gate["entry_kind"], "python_module")
        self.assertEqual(gate["entrypoint"], "decide_kb_index_tool_gate")

    def test_duplicate_tool_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cards_dir = Path(tmp)
            card_a = {
                "schema_version": "gov_tool_card_v1",
                "tool_id": "obs.eval.export",
                "title": "dup a",
                "brief": "test",
                "domain": "obs",
                "module_path": "observability/eval_exporter.py",
                "entry_kind": "python_cli",
                "entrypoint": "main",
                "cli_invocation": "python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl",
                "inputs": ["x"],
                "outputs": ["y"],
                "verify_command": "python -m unittest tests.test_eval_exporter -v",
                "wave_ticket": "TEST",
                "review_status": "approved",
            }
            (cards_dir / "a.json").write_text(json.dumps(card_a), encoding="utf-8")
            (cards_dir / "b.json").write_text(json.dumps(card_a), encoding="utf-8")

            result = validate_all_gov_tool_cards(cards_dir, repo_root=_REPO_ROOT)
            self.assertFalse(result["ok"])
            self.assertEqual(result["failed"], 2)

    def test_missing_module_path_fails(self) -> None:
        schema = load_schema(repo_root=_REPO_ROOT)
        bad = {
            "schema_version": "gov_tool_card_v1",
            "tool_id": "obs.eval.export",
            "title": "bad",
            "brief": "bad",
            "domain": "obs",
            "module_path": "observability/does_not_exist.py",
            "entry_kind": "python_cli",
            "entrypoint": "main",
            "cli_invocation": "python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl",
            "inputs": ["x"],
            "outputs": ["y"],
            "verify_command": "python -m unittest tests.test_eval_exporter -v",
            "wave_ticket": "TEST",
            "review_status": "approved",
        }
        result = validate_gov_tool_card(bad, repo_root=_REPO_ROOT, schema=schema, known_tool_ids={"obs.eval.export"})
        self.assertFalse(result["ok"])
        self.assertTrue(any("module_path not found" in err for err in result["errors"]))

    def test_unknown_depends_on_fails(self) -> None:
        schema = load_schema(repo_root=_REPO_ROOT)
        bad = {
            "schema_version": "gov_tool_card_v1",
            "tool_id": "obs.eval.export",
            "title": "bad dep",
            "brief": "bad",
            "domain": "obs",
            "module_path": "observability/eval_exporter.py",
            "entry_kind": "python_cli",
            "entrypoint": "main",
            "cli_invocation": "python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl",
            "inputs": ["x"],
            "outputs": ["y"],
            "verify_command": "python -m unittest tests.test_eval_exporter -v",
            "wave_ticket": "TEST",
            "review_status": "approved",
            "depends_on": ["obs.missing.tool"],
        }
        result = validate_gov_tool_card(bad, repo_root=_REPO_ROOT, schema=schema, known_tool_ids={"obs.eval.export"})
        self.assertFalse(result["ok"])
        self.assertTrue(any("depends_on references unknown" in err for err in result["errors"]))

    def test_default_cards_dir_under_repo(self) -> None:
        path = default_cards_dir(_REPO_ROOT)
        self.assertTrue(path.is_dir())
        self.assertEqual(path.name, "gov_cards")


if __name__ == "__main__":
    unittest.main()
