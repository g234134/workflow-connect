"""Batch orchestrator MVP — schema-backed loading + scheduler + mock/worker_api E2E."""

from __future__ import annotations

from .collector import BatchResult, collect_results
from .loader import (
    default_schema_path,
    load_batch_document,
    load_batch_manifest,
    load_batch_manifest_from_path,
    load_subtask,
    load_subtasks_from_path,
    validate_batch_manifest,
    validate_subtask,
)
from .prompt_builder import build_implementer_prompt
from .reporter import render_batch_result_json, render_state_patch_suggestion
from .runner_mock import ExecutionResult, run_subtasks_mock, run_subtasks_mock_as_dicts
from .runner_worker_api import run_subtasks_worker_api, run_subtasks_worker_api_as_dicts
from .scheduler import plan_from_loader_data, plan_from_subtasks
from .worker_api import WorkerAPIServer, handle_worker_run

__all__ = [
    "BatchResult",
    "ExecutionResult",
    "WorkerAPIServer",
    "build_implementer_prompt",
    "collect_results",
    "default_schema_path",
    "handle_worker_run",
    "load_batch_document",
    "load_batch_manifest",
    "load_batch_manifest_from_path",
    "load_subtask",
    "load_subtasks_from_path",
    "plan_from_loader_data",
    "plan_from_subtasks",
    "render_batch_result_json",
    "render_state_patch_suggestion",
    "run_subtasks_mock",
    "run_subtasks_mock_as_dicts",
    "run_subtasks_worker_api",
    "run_subtasks_worker_api_as_dicts",
    "validate_batch_manifest",
    "validate_subtask",
]
