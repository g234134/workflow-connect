"""Tests for batch Worker API + worker_api runner (P8 toward-100)."""

from __future__ import annotations

import json
import os
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
from _batch_orchestrator.cli import run_batch_pipeline  # noqa: E402
from _batch_orchestrator.runner_worker_api import (  # noqa: E402
    run_subtasks_worker_api,
)
from _batch_orchestrator.worker_api import (  # noqa: E402
    ENV_WORKER_API_URL,
    WorkerAPIServer,
    handle_worker_run,
)

_SAMPLE = _REPO_ROOT / "tests" / "fixtures" / "sample_manifest.json"


class TestWorkerAPIHandler(unittest.TestCase):
    def test_handle_success(self) -> None:
        result = handle_worker_run(
            {
                "subtask_id": "S1",
                "subtask": {"subtask_id": "S1", "goal": "demo"},
                "parent_frame": {"parent_ticket_id": "BATCH-MVP-05"},
            }
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["subtask_id"], "S1")
        self.assertIsInstance(result["prompt"], dict)
        self.assertFalse(result["writes_ticket_state"])

    def test_handle_force_fail(self) -> None:
        result = handle_worker_run(
            {"subtask_id": "S2", "subtask": {"subtask_id": "S2"}, "force_fail": True}
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "failed")


class TestWorkerAPIHttp(unittest.TestCase):
    def test_runner_against_live_server(self) -> None:
        with WorkerAPIServer() as server:
            results = run_subtasks_worker_api(
                [
                    {"subtask_id": "A", "goal": "one"},
                    {"subtask_id": "B", "goal": "two"},
                ],
                concurrency_limit=2,
                worker_base_url=server.base_url,
                parent_frame={"parent_ticket_id": "T"},
            )
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.ok for r in results))
        self.assertTrue(all(r.extras.get("external_http") for r in results))

    def test_missing_url_fail_close(self) -> None:
        old = os.environ.pop(ENV_WORKER_API_URL, None)
        try:
            results = run_subtasks_worker_api(
                [{"subtask_id": "X"}],
                worker_base_url=None,
            )
        finally:
            if old is not None:
                os.environ[ENV_WORKER_API_URL] = old
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].ok)
        self.assertEqual(results[0].status, "blocked")

    def test_pipeline_worker_api_mode(self) -> None:
        self.assertTrue(_SAMPLE.is_file())
        with WorkerAPIServer() as server:
            with tempfile.TemporaryDirectory() as tmp:
                result = run_batch_pipeline(
                    manifest_path=_SAMPLE,
                    mode="worker_api",
                    limit=2,
                    concurrency_limit=2,
                    worker_base_url=server.base_url,
                    output_dir=Path(tmp),
                )
        self.assertTrue(result["ok"], msg=result.get("message"))
        self.assertEqual(result["mode"], "worker_api")
        self.assertTrue(result["external_http"])
        self.assertFalse(result["writes_ticket_state"])
        self.assertEqual(result["batch_result"]["summary"]["success"], 2)

    def test_cli_worker_api(self) -> None:
        with WorkerAPIServer() as server:
            code = cli_main(
                [
                    "run",
                    "--manifest",
                    str(_SAMPLE),
                    "--mode",
                    "worker_api",
                    "--worker-url",
                    server.base_url,
                    "--limit",
                    "2",
                ]
            )
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
