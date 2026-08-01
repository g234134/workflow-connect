"""E2E mock tests for batch orchestrator CLI pipeline (BATCH-MVP-04)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from _batch_orchestrator.cli import main as cli_main  # noqa: E402
from _batch_orchestrator.cli import run_mock_pipeline  # noqa: E402
from _batch_orchestrator.collector import collect_results  # noqa: E402
from _batch_orchestrator.reporter import (  # noqa: E402
    render_batch_result_json,
    render_state_patch_suggestion,
)
from _batch_orchestrator.runner_mock import ExecutionResult  # noqa: E402

_SAMPLE = _REPO_ROOT / "tests" / "fixtures" / "sample_manifest.json"


class TestBatchCollectorReporter(unittest.TestCase):
    def test_collect_and_render_shapes(self) -> None:
        results = [
            ExecutionResult(subtask_id="S1", ok=True, status="success", message="ok"),
            ExecutionResult(subtask_id="S2", ok=False, status="failed", message="boom", error="boom"),
        ]
        batch = collect_results(results, batch_id="t-batch")
        self.assertEqual(batch.batch_id, "t-batch")
        self.assertEqual(batch.summary["total"], 2)
        self.assertEqual(batch.summary["success"], 1)
        self.assertEqual(batch.summary["failed"], 1)
        self.assertFalse(batch.ok)

        rendered = render_batch_result_json(batch)
        self.assertEqual(rendered["schema_version"], "batch_result_v1")
        self.assertEqual(len(rendered["subtask_results"]), 2)

        suggestion = render_state_patch_suggestion(batch, parent_ticket_id="BATCH-MVP-04")
        self.assertTrue(suggestion["suggestion_only"])
        self.assertFalse(suggestion["writes_ticket_state"])
        self.assertEqual(suggestion["parent_ticket_id"], "BATCH-MVP-04")
        self.assertEqual(suggestion["proposed_overall_status"], "needs_changes")


class TestBatchE2EMock(unittest.TestCase):
    def test_sample_manifest_pipeline(self) -> None:
        self.assertTrue(_SAMPLE.is_file(), f"missing fixture: {_SAMPLE}")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = run_mock_pipeline(
                manifest_path=_SAMPLE,
                limit=2,
                concurrency_limit=2,
                output_dir=out,
            )
            self.assertTrue(result["ok"], msg=result.get("message"))
            self.assertFalse(result.get("writes_ticket_state"))
            batch = result["batch_result"]
            self.assertEqual(batch["schema_version"], "batch_result_v1")
            self.assertEqual(batch["summary"]["total"], 2)
            self.assertEqual(batch["summary"]["success"], 2)
            self.assertEqual(len(batch["subtask_results"]), 2)
            suggestion = result["state_patch_suggestion"]
            self.assertTrue(suggestion["suggestion_only"])
            self.assertFalse(suggestion["writes_ticket_state"])

            batch_path = out / "batch_result.json"
            suggest_path = out / "state_patch_suggestion.json"
            self.assertTrue(batch_path.is_file())
            self.assertTrue(suggest_path.is_file())
            loaded_suggest = json.loads(suggest_path.read_text(encoding="utf-8"))
            self.assertTrue(loaded_suggest["suggestion_only"])

    def test_cli_run_exit_zero(self) -> None:
        code = cli_main(
            [
                "run",
                "--manifest",
                str(_SAMPLE),
                "--mode",
                "mock",
                "--limit",
                "2",
            ]
        )
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
