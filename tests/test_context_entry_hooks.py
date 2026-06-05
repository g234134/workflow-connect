"""Sprint 1 B-1: optional context entry hooks."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from core.context_entry import build_rooted_context
from hooks.context_entry_hooks import (
    ENV_CONTEXT_ENTRY_HOOKS,
    context_entry_hooks_enabled,
)


class TestContextEntryHooks(unittest.TestCase):
    def test_hooks_disabled_by_default(self) -> None:
        self.assertFalse(context_entry_hooks_enabled({}))
        out = build_rooted_context({"goal": "no hooks"}, mode="ask_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        meta = out.get("metadata") or {}
        self.assertNotIn("hooks", meta)

    def test_hooks_enabled_via_task_input_flag(self) -> None:
        out = build_rooted_context(
            {"goal": "hooks on", "_context_entry_hooks": True},
            mode="k1_pipeline",
        )
        self.assertTrue(out.get("ok"), out.get("message"))
        hooks = (out.get("metadata") or {}).get("hooks") or {}
        self.assertTrue(hooks.get("post_ran"))
        self.assertEqual(hooks.get("version"), "context-entry-hooks-b1-v0.1")
        self.assertIs(hooks.get("ok"), True)

    @patch.dict(os.environ, {ENV_CONTEXT_ENTRY_HOOKS: "1"}, clear=False)
    def test_hooks_enabled_via_env(self) -> None:
        out = build_rooted_context({"query": "env hooks"}, mode="ask_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        hooks = (out.get("metadata") or {}).get("hooks") or {}
        self.assertTrue(hooks.get("post_ran"))

    def test_hooks_off_existing_contract_unchanged(self) -> None:
        """Regression: disabled hooks must not alter deny / layer contract."""
        out = build_rooted_context(
            {
                "query": "bypass",
                "root_context": {"version": "hand"},
            },
            mode="ask_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertTrue(deny.get("denied"))
        self.assertNotIn("hooks", out.get("metadata") or {})


if __name__ == "__main__":
    unittest.main()
