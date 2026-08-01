"""P4 regression: scout_last_pipeline local_similarity_pct must not be all null after sync."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "04_Workflows"


def _load_sync_mod():
    path = WF / "_sync_wave_to_scout_pipeline.py"
    spec = importlib.util.spec_from_file_location("_sync_wave_to_scout_pipeline", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(WF))
    sys.path.insert(0, str(ROOT / "02_Agents_Core"))
    spec.loader.exec_module(mod)
    return mod


class TestP4LocalSimilaritySync(unittest.TestCase):
    def test_ensure_similarity_fills_null(self):
        mod = _load_sync_mod()
        rep = {
            "run_id": "test",
            "top_tags": {"type:python": 3, "funcs:1": 2},
            "by_type": {"python": 5},
            "rows": [],
        }
        top = [
            {
                "name": "foo.py",
                "source_path": "x/foo.py",
                "local_score": 8.0,
                "final_score": 8.0,
                "grade": "A",
                "local_similarity_pct": None,
            }
        ]
        with mock.patch.object(mod, "_resolve_blob", return_value="preview_lines=[\"import foo\"]\nfunctions=[\"bar\"]"):
            enriched, filled = mod._ensure_similarity_on_rows(str(ROOT), rep, top)
        self.assertEqual(filled, 1)
        self.assertIsNotNone(enriched[0]["local_similarity_pct"])
        self.assertIsInstance(enriched[0]["local_similarity_pct"], float)

    def test_persist_writes_eval_rows(self):
        mod = _load_sync_mod()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "asset_value_eval_test.json"
            rep = {
                "rows": [
                    {
                        "name": "foo.py",
                        "source_path": "x/foo.py",
                        "grade": "A",
                        "local_similarity_pct": None,
                    }
                ]
            }
            enriched = [
                {
                    "name": "foo.py",
                    "source_path": "x/foo.py",
                    "local_similarity_pct": 42.5,
                }
            ]
            n = mod._persist_similarity_into_eval(str(path), rep, enriched)
            self.assertEqual(n, 1)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["rows"][0]["local_similarity_pct"], 42.5)
            self.assertIn("local_similarity_enriched_at", data)


if __name__ == "__main__":
    unittest.main()
