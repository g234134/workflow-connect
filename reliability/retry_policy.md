# Retry Policy (D1)

> Goal: improve long-task success rate without adding external dependencies or complex orchestration.

Policies are implemented in `reliability/retry_handler.py` (`POLICY_TABLE`). Metrics integration uses `metrics.get_collector().log_error(..., increment_retry=True)`.

## Policy matrix

| `error_type` | Action | Max extra attempts | Notes |
|--------------|--------|--------------------|-------|
| `llm_error` | **retry** same `fn` | 1–2 (default **2**) | Transient provider / rate-limit failures |
| `context_overflow` | **shrink context** then retry | 1 | Requires `shrink_context` callback; no shrink → fail fast |
| `tool_error` | **fallback** or **skip** | 0 retries | `fallback_fn` runs once; else optional `allow_tool_skip` |
| `timeout` | **retry** same `fn` | 1 | Single backoff-less retry (local stub) |
| `unknown` | **fail** | 0 | Log and surface; no blind retry |

## Attempt budget

- **Initial attempt** does not increment `retry_count`.  
- Each **policy-driven retry** increments `retry_count` via `log_error(..., increment_retry=True)`.  
- Total calls to `fn` ≤ `1 + max_retries` for that error class.

## `llm_error`

- Default `max_llm_retries=2` → up to 3 executions of `fn`.  
- Override per call: `run_with_retry(..., max_llm_retries=1)`.

## `context_overflow`

1. Invoke `shrink_context(context)` (mutates or returns slimmer dict).  
2. Retry `fn` once.  
3. If still overflowing, return `{ok: false, error_type: "context_overflow"}`.

## `tool_error`

1. If `fallback_fn` is set, call `fallback_fn(exc)` and return success with `used_fallback: true`.  
2. Else if `allow_tool_skip=True`, return `{ok: true, skipped: true}`.  
3. Else fail with `error_type: "tool_error"`.

## `timeout` / `unknown`

- `timeout`: one retry, then fail.  
- `unknown`: no retry (avoid retry storms).

## Checkpoint interaction

Before each `fn` invocation, `run_with_retry` may call `MockCheckpointStore.save` when `task_id` and `step_index` are provided. On success, latest checkpoint is marked completed (see `checkpoint_design.md`).

## Return shape

All paths return a stable `dict`:

```python
{
    "ok": bool,
    "message": str,
    "result": Any | None,
    "error_type": str | None,
    "retry_count": int,
    "attempts": int,
    "used_fallback": bool,
    "skipped": bool,
    "checkpoint_saved": bool,
}
```
