# Failure Taxonomy (D1 / D5)

> Aligns with `metrics/metrics_schema.json` → `error_type_enum` and `metrics.metrics_collector.ErrorType`.

## Categories

| `error_type` | Meaning | Typical signals | Default retryable |
|--------------|---------|-----------------|-------------------|
| `llm_error` | Provider / model call failed | `RateLimitError`, `APIError`, HTTP 5xx from LLM, message contains `rate limit`, `model` | yes (1–2 retries) |
| `tool_error` | Tool or local I/O step failed | `ToolException`, subprocess exit, missing file for tool | fallback / skip |
| `context_overflow` | Prompt or window exceeds budget | `context length`, `maximum context`, `token limit exceeded` | shrink + 1 retry |
| `timeout` | Wall-clock or RPC timeout | `TimeoutError`, `timed out`, `deadline exceeded` | 1 retry |
| `unknown` | Unclassified | Anything else | no retry |

## Classification order

`retry_handler.classify_error()` applies rules in this order (first match wins):

1. `TimeoutError` or timeout keywords in message  
2. Context / token overflow keywords  
3. Explicit `ReliabilityError` with `error_type`  
4. Tool-related type names or `tool_error` in message  
5. LLM-related type names or provider keywords  
6. `unknown`

## Explicit tagging

Raise `ReliabilityError` when the caller already knows the category:

```python
from reliability.retry_handler import ReliabilityError

raise ReliabilityError("qdrant unreachable", error_type="tool_error")
```

## Metrics wiring

Each classified failure should be recorded via `MetricsCollector.log_error`:

- `error_type` — one of the enum values above  
- `increment_retry=True` when a retry is actually attempted (not on final fatal log only)  
- `retryable` — mirrors policy table `Default retryable`

Task-level rollup uses `retry_count` on the task record (D1).

## Related docs

- Retry actions: `reliability/retry_policy.md`  
- Step persistence: `reliability/checkpoint_design.md`  
- Implementation: `reliability/retry_handler.py`
