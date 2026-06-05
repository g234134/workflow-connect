# Checkpoint Design (mock, D1)

> In-memory only; no DB, Redis, or filesystem persistence. Suitable for unit tests and local agent loops.

## Purpose

Long tasks run as a sequence of **steps**. If step *k* fails with a retryable error, we want to resume from the last good state instead of restarting the whole task.

Phase 1 delivers a **mock store** in `retry_handler.MockCheckpointStore` so callers can wire real persistence later without changing `run_with_retry` signatures.

## Record shape

```json
{
  "task_id": "task-abc",
  "step_index": 2,
  "step_name": "retrieve",
  "timestamp": "2026-05-23T12:00:00+00:00",
  "state": { "cursor": 10, "partial_results": [] },
  "status": "in_progress | completed | failed"
}
```

| Field | Description |
|-------|-------------|
| `task_id` | Correlates with `MetricsCollector.start_task` |
| `step_index` | Monotonic step number (0-based) |
| `step_name` | Logical step label (matches `log_step` name when used) |
| `state` | Opaque JSON-serializable dict owned by the caller |
| `status` | Lifecycle marker for resume logic |

## API (mock)

| Method | Behavior |
|--------|----------|
| `save(task_id, step_index, state, *, step_name, status)` | Upsert checkpoint for `(task_id, step_index)` |
| `load(task_id, step_index)` | Return record or `None` |
| `load_latest(task_id)` | Highest `step_index` for task |
| `mark_completed(task_id, step_index)` | Set `status=completed` |
| `list_steps(task_id)` | All checkpoints ordered by `step_index` |

## Integration with `run_with_retry`

Optional kwargs:

- `task_id` — metrics + checkpoint key  
- `step_index` / `step_name` — which step is executing  
- `checkpoint_state` — dict written before each attempt  
- `checkpoint_store` — defaults to process-wide mock singleton  

Flow:

```
before attempt → save(state, status=in_progress)
on success     → mark_completed(step_index)
on final fail  → save(state, status=failed)  # last known state for inspection
```

## Resume (future)

Not implemented in the mock beyond `load_latest`. Callers can:

1. `load_latest(task_id)`  
2. Restore `state` into their pipeline  
3. Continue from `step_index + 1`

## Metrics

Checkpoints do not replace trace events; pair with `log_step` on the same `task_id` for D4 completeness.

## Non-goals (this phase)

- Cross-process durability  
- Encryption or PII scrubbing  
- Automatic resume inside `run_with_retry` (caller-driven only)
