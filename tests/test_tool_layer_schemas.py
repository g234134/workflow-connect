"""Unit tests for Phase 8.8 tool catalog schema and loader."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.tool_catalog import (  # noqa: E402
    default_catalog_path,
    load_catalog,
    validate_catalog_document,
)


class TestToolLayerSchemas(unittest.TestCase):
    def test_load_production_catalog_happy_path(self) -> None:
        result = load_catalog(repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"], msg=json.dumps(result, indent=2))
        self.assertEqual(result["schema_version"], "tool_catalog_v1")
        self.assertGreaterEqual(result["tool_count"], 6)
        self.assertGreater(result["enabled_count"], 0)
        self.assertTrue(result["catalog_revision"])
        self.assertEqual(default_catalog_path(_REPO_ROOT), _REPO_ROOT / "shared/schemas/tool_catalog_v1.json")

    def test_duplicate_tool_id_fails(self) -> None:
        base = load_catalog(repo_root=_REPO_ROOT)
        self.assertTrue(base["ok"])
        doc = {
            "schema_version": "tool_catalog_v1",
            "catalog_revision": "test",
            "tools": [
                deepcopy(base["tools"][0]),
                deepcopy(base["tools"][0]),
            ],
        }
        result = validate_catalog_document(doc)
        self.assertFalse(result["ok"])
        self.assertIn("duplicate tool_id", result["message"])

    def test_missing_required_fields_fails(self) -> None:
        doc = {
            "schema_version": "tool_catalog_v1",
            "catalog_revision": "test",
            "tools": [{"tool_id": "incomplete.tool"}],
        }
        result = validate_catalog_document(doc)
        self.assertFalse(result["ok"])
        self.assertIn("missing required fields", result["message"])

    def test_missing_top_level_fields_fails(self) -> None:
        result = validate_catalog_document({"schema_version": "tool_catalog_v1"})
        self.assertFalse(result["ok"])
        self.assertIn("missing required fields", result["message"])

    def test_load_from_temp_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "shared/schemas"
            path.mkdir(parents=True)
            (path / "tool_catalog_v1.json").write_text("{ bad", encoding="utf-8")
            result = load_catalog(repo_root=root)
            self.assertFalse(result["ok"])
            self.assertIn("invalid JSON", result["message"])

    def test_enabled_false_still_loaded(self) -> None:
        result = load_catalog(repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"])
        disabled = [t for t in result["tools"] if t.get("enabled") is False]
        self.assertGreaterEqual(len(disabled), 1)
        self.assertEqual(result["tool_count"], result["enabled_count"] + len(disabled))


if __name__ == "__main__":
    unittest.main()
