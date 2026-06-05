# eval_gate rules (v0.1)

> **Module**: `observability/eval_gate.py` → `evaluate_task_record(record)`  
> **Inputs**: M-line `metrics_record` or `ibridge_record` (`dict`)  
> **Outputs**: `{ pass, tags, reasons }` — `pass=True` only when `tags` is empty

---

## Pass semantics

| `pass` | Meaning |
|--------|---------|
| `True` | No review tags; treat as normal for CI / sampling |
| `False` | At least one tag; **suggest human review** (not a hard pipeline block in v0.1) |

---

## Rules

### HIGH_RETRY

| Field | Value |
|-------|-------|
| **Tag** | `high_retry` |
| **Condition** | `retry_count >= 2` |
| **Dimension** | **D1** (reliability / retry pressure) |
| **Tuning** | Raise threshold if transient provider blips are expected; pair with `success=true` allowlist in v0.2 |

---

### CONTEXT_HEAVY

| Field | Value |
|-------|-------|
| **Tag** | `context_heavy` |
| **Condition** | `context_token_usage.total_tokens > 0.8 × MAX_TOTAL_TOKEN_BUDGET` (102_400 when budget = 128_000) |
| **Dimension** | **D2** (context cost / budget pressure) |
| **Tuning** | Per-workflow budgets; trim-aware runs may need a lower ratio (e.g. 0.7) |

---

### MANY_HANDOFFS

| Field | Value |
|-------|-------|
| **Tag** | `many_handoffs` |
| **Condition** | `handoff_count >= 3` |
| **Dimension** | **D3** (multi-agent coordination risk) |
| **Tuning** | Orchestrator graphs with fixed stages may use `>= 4`; single-agent pipelines can disable |

---

### INFRA_RISK

| Field | Value |
|-------|-------|
| **Tag** | `infra_risk` |
| **Condition** | `error_type in {"context_overflow", "timeout"}` |
| **Dimension** | **D1** + **D5** (failure class with infra / capacity signal) |
| **Tuning** | Add `llm_error` / `tool_error` when replay policy is defined in eval_pipeline §3 |

---

### OBSERVABILITY_GAP

| Field | Value |
|-------|-------|
| **Tag** | `observability_gap` |
| **Condition** | `trace_completeness.score < 0.8` |
| **Dimension** | **D4** (trace field completeness) |
| **Tuning** | Align with eval_pipeline S4 (`>= 0.875`) once gate is wired to verdict pipeline; v0.1 uses 0.8 for review sampling |

---

## D1–D4 coverage

| Dimension | Rules |
|-----------|-------|
| D1 | `HIGH_RETRY`, `INFRA_RISK` (partial) |
| D2 | `CONTEXT_HEAVY` |
| D3 | `MANY_HANDOFFS` |
| D4 | `OBSERVABILITY_GAP` |

D5 (`error_type` enum beyond infra set) is not fully covered in v0.1; extend via new tags in v0.2.

---

## Constants (code)

| Constant | Default |
|----------|---------|
| `MAX_TOTAL_TOKEN_BUDGET` | 128_000 |
| `CONTEXT_HEAVY_RATIO` | 0.8 |
| `HIGH_RETRY_THRESHOLD` | 2 |
| `MANY_HANDOFFS_THRESHOLD` | 3 |
| `TRACE_COMPLETENESS_THRESHOLD` | 0.8 |
