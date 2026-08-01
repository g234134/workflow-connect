"""Unit tests for W3-B kb_index selector hook (WAVE-B-P2-KB-SELECTOR-HOOK-MIN)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.kb_index_selector_hook import (  # noqa: E402
    decide_kb_index_tool_gate,
    is_repo_index_gated_tool,
    kb_index_selector_hook_enabled,
)
from core.ask_rag_selector import apply_kb_index_tool_gate_from_hints  # noqa: E402

_REPO_TOOL = "repo_code_retrieve_smoke"
_GRAPH_TOOL = "repo_graph_manifest_read"
_NON_REPO_TOOL = "chat_generic"


class TestIsRepoIndexGatedTool(unittest.TestCase):
    def test_repo_retrieve_tool_is_gated(self) -> None:
        self.assertTrue(is_repo_index_gated_tool(_REPO_TOOL))

    def test_repo_graph_tool_is_gated(self) -> None:
        self.assertTrue(is_repo_index_gated_tool(_GRAPH_TOOL))

    def test_non_repo_tool_not_gated(self) -> None:
        self.assertFalse(is_repo_index_gated_tool(_NON_REPO_TOOL))

    def test_repo_index_job_not_gated(self) -> None:
        self.assertFalse(is_repo_index_gated_tool("repo_index_v1_job"))


class TestDecideKbIndexToolGate(unittest.TestCase):
    def test_missing_repo_tool_blocks(self) -> None:
        out = decide_kb_index_tool_gate("missing", _REPO_TOOL)
        self.assertTrue(out["ok"])
        self.assertEqual(out["decision"], "block")
        self.assertIn("missing", out["message"])
        self.assertIn("decision:block", out["audit_tags"])

    def test_stale_repo_tool_degrades(self) -> None:
        out = decide_kb_index_tool_gate("stale", _REPO_TOOL)
        self.assertTrue(out["ok"])
        self.assertEqual(out["decision"], "degrade")
        self.assertIn("stale", out["message"])
        self.assertIn("cost_class:high", out["audit_tags"])

    def test_ready_repo_tool_allows(self) -> None:
        out = decide_kb_index_tool_gate("ready", _REPO_TOOL)
        self.assertTrue(out["ok"])
        self.assertEqual(out["decision"], "allow")
        self.assertIn("ready", out["message"])

    def test_non_repo_tool_always_allows(self) -> None:
        for status in ("missing", "stale", "ready", "bogus"):
            out = decide_kb_index_tool_gate(status, _NON_REPO_TOOL)
            self.assertTrue(out["ok"])
            self.assertEqual(out["decision"], "allow")
            self.assertIn("gate:skipped_non_repo_tool", out["audit_tags"])

    def test_unknown_status_blocks_repo_tool(self) -> None:
        out = decide_kb_index_tool_gate("unexpected", _REPO_TOOL)
        self.assertFalse(out["ok"])
        self.assertEqual(out["decision"], "block")
        self.assertIn("kb_index:unknown", out["audit_tags"])

    def test_status_normalization(self) -> None:
        out = decide_kb_index_tool_gate(" READY ", _REPO_TOOL)
        self.assertEqual(out["decision"], "allow")


class TestAskSelectorHintIntegration(unittest.TestCase):
    def test_apply_from_selector_hints(self) -> None:
        out = apply_kb_index_tool_gate_from_hints(
            _REPO_TOOL,
            selector_hints={"kb_index_status": "missing"},
        )
        self.assertEqual(out["decision"], "block")

    def test_apply_without_status_skips_gate(self) -> None:
        out = apply_kb_index_tool_gate_from_hints(_REPO_TOOL, selector_hints={})
        self.assertTrue(out["ok"])
        self.assertEqual(out["decision"], "allow")
        self.assertIn("gate:skipped_no_kb_index_status", out["audit_tags"])


class TestFeatureFlagDefault(unittest.TestCase):
    def test_prod_flag_default_off(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertFalse(kb_index_selector_hook_enabled())


if __name__ == "__main__":
    unittest.main()
