"""
Unit tests for K-2 prod shadow worker (spool append + merge path).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from core.k2_prod_shadow_worker import append_shadow_spool_line, execute_prod_shadow_from_ask


class TestK2ProdShadowWorker(unittest.TestCase):
    def test_append_shadow_spool_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spool = Path(tmp) / "k2_shadow_spool.jsonl"
            line = {"case_name": "unit", "k2_summary": {"pipeline": "k2", "ok": True}}
            result = append_shadow_spool_line(line, spool_path=spool)
            self.assertTrue(result.get("ok"))
            rows = [json.loads(r) for r in spool.read_text(encoding="utf-8").strip().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["case_name"], "unit")

    @mock.patch("core.langgraph_flow_k2.run_k2_flow")
    def test_execute_prod_shadow_from_ask(self, mock_k2: mock.MagicMock) -> None:
        mock_k2.return_value = {
            "ok": True,
            "message": "k2 ok",
            "state": {"final_result": {"ok": True, "status": "success"}, "error_type": None},
            "record": {
                "task_id": "t-k2",
                "trace_id": "tr-k2",
                "end_time": "2026-05-25T12:00:00Z",
                "success": True,
                "retry_count": 0,
                "handoff_count": 0,
                "context_token_usage": {"total_tokens": 10},
                "trace_completeness": {"score": 1.0},
            },
            "eval_metadata": {"eval_gate": {"tags": []}},
        }
        ask_snapshot: dict[str, Any] = {
            "ok": True,
            "answer": {"answer": "ask answer"},
            "executed_nodes": ["a", "b"],
            "errors": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            spool = Path(tmp) / "spool.jsonl"
            result = execute_prod_shadow_from_ask(
                ask_snapshot,
                query="q",
                top_k=2,
                spool_path=spool,
            )
            self.assertTrue(result.get("ok"))
            self.assertEqual(result.get("primary_source"), "ask")
            self.assertTrue(spool.is_file())
            row = json.loads(spool.read_text(encoding="utf-8").strip())
            self.assertEqual(row.get("schema"), "k2_prod_shadow/v1")
            self.assertEqual(row.get("primary_source"), "ask")
            self.assertIn("k2_merge", row)
