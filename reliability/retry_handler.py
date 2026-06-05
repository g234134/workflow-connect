"""
D1 reliability: classify failures, apply retry policy, mock checkpoints.

No external services. Records retries via ``metrics.get_collector()`` when
``task_id`` is provided.

Usage::

    from reliability.retry_handler import run_with_retry, ReliabilityError

    def step():
        ...

    out = run_with_retry(step, task_id="t1", step_name="retrieve")
    assert "ok" in out
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Final, Literal, TypeVar

from metrics.metrics_collector import ERROR_TYPES, ErrorType, MetricsCollector, get_collector

T = TypeVar("T")

Action = Literal["retry", "shrink_and_retry", "fallback_or_skip", "fail"]

POLICY_TABLE: Final[dict[ErrorType, dict[str, Any]]] = {
    "llm_error": {"action": "retry", "max_retries": 2, "retryable": True},
    "context_overflow": {"action": "shrink_and_retry", "max_retries": 1, "retryable": True},
    "tool_error": {"action": "fallback_or_skip", "max_retries": 0, "retryable": False},
    "timeout": {"action": "retry", "max_retries": 1, "retryable": True},
    "unknown": {"action": "fail", "max_retries": 0, "retryable": False},
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReliabilityError(Exception):
    """Raised when the caller knows the failure category."""

    def __init__(self, message: str = "", *, error_type: ErrorType = "unknown") -> None:
        super().__init__(message)
        self.error_type: ErrorType = error_type if error_type in ERROR_TYPES else "unknown"


class MockCheckpointStore:
    """In-memory checkpoint store (see ``checkpoint_design.md``)."""

    def __init__(self) -> None:
        self._records: dict[str, dict[int, dict[str, Any]]] = {}

    def save(
        self,
        task_id: str,
        step_index: int,
        state: dict[str, Any],
        *,
        step_name: str = "",
        status: str = "in_progress",
    ) -> dict[str, Any]:
        tid = (task_id or "").strip()
        if not tid:
            return {"ok": False, "message": "task_id required"}
        bucket = self._records.setdefault(tid, {})
        record = {
            "task_id": tid,
            "step_index": int(step_index),
            "step_name": step_name,
            "timestamp": _utc_now_iso(),
            "state": deepcopy(state),
            "status": status,
        }
        bucket[int(step_index)] = record
        return {"ok": True, "message": "checkpoint saved", "record": deepcopy(record)}

    def load(self, task_id: str, step_index: int) -> dict[str, Any] | None:
        tid = (task_id or "").strip()
        record = self._records.get(tid, {}).get(int(step_index))
        return deepcopy(record) if record else None

    def load_latest(self, task_id: str) -> dict[str, Any] | None:
        tid = (task_id or "").strip()
        bucket = self._records.get(tid)
        if not bucket:
            return None
        latest_index = max(bucket.keys())
        return deepcopy(bucket[latest_index])

    def mark_completed(self, task_id: str, step_index: int) -> dict[str, Any]:
        tid = (task_id or "").strip()
        record = self._records.get(tid, {}).get(int(step_index))
        if not record:
            return {"ok": False, "message": f"no checkpoint for step {step_index}"}
        record["status"] = "completed"
        record["timestamp"] = _utc_now_iso()
        return {"ok": True, "message": "checkpoint completed", "record": deepcopy(record)}

    def list_steps(self, task_id: str) -> dict[str, Any]:
        tid = (task_id or "").strip()
        bucket = self._records.get(tid, {})
        ordered = [deepcopy(bucket[i]) for i in sorted(bucket.keys())]
        return {"ok": True, "message": "ok", "task_id": tid, "checkpoints": ordered}


_default_checkpoint_store: MockCheckpointStore | None = None


def get_checkpoint_store() -> MockCheckpointStore:
    global _default_checkpoint_store
    if _default_checkpoint_store is None:
        _default_checkpoint_store = MockCheckpointStore()
    return _default_checkpoint_store


def reset_checkpoint_store() -> None:
    global _default_checkpoint_store
    _default_checkpoint_store = MockCheckpointStore()


def classify_error(exc: BaseException) -> ErrorType:
    """Map an exception to ``metrics_schema`` error_type (see ``failure_taxonomy.md``)."""
    if isinstance(exc, ReliabilityError):
        return exc.error_type

    msg = str(exc).lower()
    name = type(exc).__name__.lower()

    if isinstance(exc, TimeoutError) or "timeout" in msg or "timed out" in msg or "deadline exceeded" in msg:
        return "timeout"

    overflow_markers = (
        "context overflow",
        "context length",
        "maximum context",
        "max context",
        "token limit",
        "too many tokens",
        "context window",
    )
    if any(marker in msg for marker in overflow_markers):
        return "context_overflow"

    tool_markers = ("tool", "subprocess", "command failed", "file not found")
    if "tool" in name or any(marker in msg for marker in tool_markers):
        return "tool_error"

    llm_markers = (
        "rate limit",
        "ratelimit",
        "openai",
        "anthropic",
        "llm",
        "model",
        "completion",
        "api error",
        "503",
        "502",
        "429",
    )
    if any(token in name for token in ("llm", "openai", "anthropic", "rate")) or any(
        marker in msg for marker in llm_markers
    ):
        return "llm_error"

    return "unknown"


def _policy_for(error_type: ErrorType, *, max_llm_retries: int) -> dict[str, Any]:
    base = dict(POLICY_TABLE.get(error_type, POLICY_TABLE["unknown"]))
    if error_type == "llm_error":
        base["max_retries"] = max(0, int(max_llm_retries))
    return base


def _failure_result(
    *,
    ok: bool,
    message: str,
    result: Any = None,
    error_type: ErrorType | None,
    retry_count: int,
    attempts: int,
    used_fallback: bool = False,
    skipped: bool = False,
    checkpoint_saved: bool = False,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "message": message,
        "result": result,
        "error_type": error_type,
        "retry_count": retry_count,
        "attempts": attempts,
        "used_fallback": used_fallback,
        "skipped": skipped,
        "checkpoint_saved": checkpoint_saved,
    }


def run_with_retry(
    fn: Callable[[], T],
    *,
    task_id: str | None = None,
    step_name: str = "step",
    step_index: int | None = None,
    checkpoint_state: dict[str, Any] | None = None,
    checkpoint_store: MockCheckpointStore | None = None,
    collector: MetricsCollector | None = None,
    context: dict[str, Any] | None = None,
    shrink_context: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    fallback_fn: Callable[[BaseException], Any] | None = None,
    allow_tool_skip: bool = False,
    max_llm_retries: int = 2,
) -> dict[str, Any]:
    """
    Execute ``fn`` with taxonomy-based retry policy.

    Returns a stable dict (see ``retry_policy.md``). On success, ``result`` holds
    the return value of ``fn`` (or fallback output).
    """
    col = collector if collector is not None else get_collector()
    store = checkpoint_store if checkpoint_store is not None else get_checkpoint_store()
    tid = (task_id or "").strip() or None

    retry_count = 0
    attempts = 0
    checkpoint_saved = False
    last_error_type: ErrorType | None = None
    last_message = ""

    retries_by_type: dict[ErrorType, int] = {k: 0 for k in POLICY_TABLE}

    def _maybe_checkpoint(status: str = "in_progress") -> None:
        nonlocal checkpoint_saved
        if tid is None or step_index is None or checkpoint_state is None:
            return
        out = store.save(
            tid,
            step_index,
            checkpoint_state,
            step_name=step_name,
            status=status,
        )
        checkpoint_saved = checkpoint_saved or bool(out.get("ok"))

    def _log_failure(exc: BaseException, error_type: ErrorType, *, increment_retry: bool) -> None:
        if not tid:
            return
        col.log_error(
            tid,
            error_type,
            str(exc) or type(exc).__name__,
            step_index=step_index,
            retryable=POLICY_TABLE[error_type]["retryable"],
            increment_retry=increment_retry,
        )

    while True:
        attempts += 1
        _maybe_checkpoint("in_progress")
        try:
            value = fn()
            if tid and step_index is not None:
                store.mark_completed(tid, step_index)
            return _failure_result(
                ok=True,
                message="ok",
                result=value,
                error_type=None,
                retry_count=retry_count,
                attempts=attempts,
                checkpoint_saved=checkpoint_saved,
            )
        except BaseException as exc:
            error_type = classify_error(exc)
            last_error_type = error_type
            last_message = str(exc) or type(exc).__name__
            policy = _policy_for(error_type, max_llm_retries=max_llm_retries)
            action: Action = policy["action"]
            max_retries: int = int(policy["max_retries"])

            if action == "retry":
                if retries_by_type[error_type] < max_retries:
                    _log_failure(exc, error_type, increment_retry=True)
                    retries_by_type[error_type] += 1
                    retry_count += 1
                    continue
                _log_failure(exc, error_type, increment_retry=False)
                break

            if action == "shrink_and_retry":
                if retries_by_type[error_type] < max_retries and shrink_context and context is not None:
                    _log_failure(exc, error_type, increment_retry=True)
                    retries_by_type[error_type] += 1
                    retry_count += 1
                    shrink_context(context)
                    continue
                _log_failure(exc, error_type, increment_retry=False)
                break

            if action == "fallback_or_skip":
                if fallback_fn is not None:
                    try:
                        fb_result = fallback_fn(exc)
                        if tid and step_index is not None:
                            store.mark_completed(tid, step_index)
                        return _failure_result(
                            ok=True,
                            message="fallback applied",
                            result=fb_result,
                            error_type=error_type,
                            retry_count=retry_count,
                            attempts=attempts,
                            used_fallback=True,
                            checkpoint_saved=checkpoint_saved,
                        )
                    except BaseException as fb_exc:
                        last_message = str(fb_exc) or type(fb_exc).__name__
                        last_error_type = classify_error(fb_exc)
                        _log_failure(fb_exc, last_error_type, increment_retry=False)
                        break
                if allow_tool_skip:
                    if tid and step_index is not None:
                        store.mark_completed(tid, step_index)
                    return _failure_result(
                        ok=True,
                        message="tool step skipped",
                        result=None,
                        error_type=error_type,
                        retry_count=retry_count,
                        attempts=attempts,
                        skipped=True,
                        checkpoint_saved=checkpoint_saved,
                    )
                _log_failure(exc, error_type, increment_retry=False)
                break

            # fail (unknown or unhandled)
            _log_failure(exc, error_type, increment_retry=False)
            break

    if tid and step_index is not None and checkpoint_state is not None:
        store.save(tid, step_index, checkpoint_state, step_name=step_name, status="failed")

    return _failure_result(
        ok=False,
        message=last_message or "execution failed",
        result=None,
        error_type=last_error_type,
        retry_count=retry_count,
        attempts=attempts,
        checkpoint_saved=checkpoint_saved,
    )
