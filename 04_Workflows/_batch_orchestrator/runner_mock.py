"""Mock subtask runner for batch orchestrator (BATCH-MVP-03).

Simulates worker execution with concurrency control. Does not call real Worker
APIs or write ticket state / Progress.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


@dataclass
class ExecutionResult:
    """Structured result for one mock-executed subtask."""

    subtask_id: str
    ok: bool
    status: str  # success | failed | blocked | timeout
    latency_ms: float = 0.0
    message: str = ""
    prompt: dict[str, Any] | None = None
    error: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def _subtask_id(subtask: Mapping[str, Any], index: int) -> str:
    sid = str(subtask.get("subtask_id") or "").strip()
    return sid or f"anon-{index}"


def _decide_outcome(
    index: int,
    *,
    force_failures: Sequence[str] | None,
    failure_ratio: float,
    total: int,
    subtask_id: str,
) -> tuple[bool, str, str | None]:
    """Return (ok, status, error)."""
    if force_failures and subtask_id in set(force_failures):
        return False, "failed", f"forced failure for {subtask_id}"

    if failure_ratio <= 0:
        return True, "success", None

    # Deterministic: first floor(n * ratio) items (by index) fail when no force list.
    fail_count = int(total * failure_ratio)
    if index < fail_count:
        return False, "failed", f"simulated failure ({failure_ratio=})"
    return True, "success", None


def _run_one(
    subtask: Mapping[str, Any],
    index: int,
    *,
    parent_frame: Mapping[str, Any] | None,
    force_failures: Sequence[str] | None,
    failure_ratio: float,
    total: int,
    base_latency_ms: float,
    build_prompt: bool,
) -> ExecutionResult:
    # Local import keeps runner usable even if prompt_builder is mid-edit.
    from .prompt_builder import build_implementer_prompt

    sid = _subtask_id(subtask, index)
    started = time.perf_counter()

    # Tiny sleep so latency_ms is measurable under concurrency without slowing tests.
    if base_latency_ms > 0:
        time.sleep(min(base_latency_ms, 50.0) / 1000.0)

    ok, status, error = _decide_outcome(
        index,
        force_failures=force_failures,
        failure_ratio=failure_ratio,
        total=total,
        subtask_id=sid,
    )

    prompt: dict[str, Any] | None = None
    if build_prompt:
        prompt = build_implementer_prompt(dict(subtask), dict(parent_frame or {}))

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return ExecutionResult(
        subtask_id=sid,
        ok=ok,
        status=status,
        latency_ms=round(elapsed_ms, 3),
        message="mock success" if ok else (error or "mock failure"),
        prompt=prompt,
        error=error,
    )


def run_subtasks_mock(
    subtasks: list[dict],
    concurrency_limit: int = 2,
    *,
    failure_ratio: float = 0.0,
    force_failures: Sequence[str] | None = None,
    base_latency_ms: float = 1.0,
    parent_frame: Mapping[str, Any] | None = None,
    build_prompt: bool = True,
) -> list[ExecutionResult]:
    """Run subtasks under a concurrency cap; return ExecutionResult list.

    Parameters
    ----------
    subtasks:
        Loader/scheduler-shaped subtask dicts.
    concurrency_limit:
        Max parallel mock workers (>=1).
    failure_ratio:
        Fraction of subtasks (by index order) that fail when force_failures is unset.
    force_failures:
        Explicit subtask_id list that must fail (overrides ratio for those ids).
    base_latency_ms:
        Artificial per-task sleep budget (capped at 50ms in mock).
    parent_frame:
        Optional FRAME mapping passed into prompt builder.
    build_prompt:
        When True, attach build_implementer_prompt output on each result.
    """
    if not isinstance(subtasks, list):
        return [
            ExecutionResult(
                subtask_id="invalid",
                ok=False,
                status="failed",
                message="subtasks must be a list",
                error="subtasks must be a list",
            )
        ]

    limit = max(1, int(concurrency_limit or 1))
    total = len(subtasks)
    if total == 0:
        return []

    results_by_index: dict[int, ExecutionResult] = {}

    def _job(idx: int, item: dict) -> tuple[int, ExecutionResult]:
        if not isinstance(item, Mapping):
            return idx, ExecutionResult(
                subtask_id=f"anon-{idx}",
                ok=False,
                status="failed",
                message="subtask must be a mapping",
                error="subtask must be a mapping",
            )
        return idx, _run_one(
            item,
            idx,
            parent_frame=parent_frame,
            force_failures=force_failures,
            failure_ratio=float(failure_ratio or 0.0),
            total=total,
            base_latency_ms=float(base_latency_ms or 0.0),
            build_prompt=build_prompt,
        )

    with ThreadPoolExecutor(max_workers=limit) as pool:
        futures = [pool.submit(_job, i, st) for i, st in enumerate(subtasks)]
        for fut in as_completed(futures):
            idx, result = fut.result()
            results_by_index[idx] = result

    return [results_by_index[i] for i in range(total)]


def run_subtasks_mock_as_dicts(
    subtasks: list[dict],
    concurrency_limit: int = 2,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Convenience wrapper returning list[dict] instead of ExecutionResult."""
    return [r.to_dict() for r in run_subtasks_mock(subtasks, concurrency_limit, **kwargs)]
