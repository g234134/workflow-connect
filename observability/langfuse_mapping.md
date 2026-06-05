# Langfuse mapping (D4 ↔ M-line)

> **Authority**: `metrics/metrics_schema.json` (`langfuse_hints`), `gov_core_system/shared/schemas/langfuse_metadata.json`  
> **Runtime**: `observability/logging_adapter.py` → `metrics/metrics_collector.py`  
> **Dark部既有**: `gov_core_system/core/observability.py`, `core/observability_v2.py`（不取代 SDK，只做欄位對齊）

---

## 1. 概念對照

| 本專案 | Langfuse | M-line (`metrics_collector`) |
|--------|----------|------------------------------|
| **trace** | Trace（root） | `start_task` / `end_task` → 一筆 task record |
| **span** | Span（child） | `log_step` → `steps[]` 一項 |
| **session** | `session_id` / thread | `task_id`（建議 1:1） |
| **generation / observation** | LLM 子觀測 | step metadata + `token_delta` → `context_token_usage` |

---

## 2. 生命週期映射

### 2.1 `start_trace(agent_name, task_id?, trace_id?)`

| 動作 | Langfuse（目標） | M-line |
|------|------------------|--------|
| 建立 root | `langfuse.trace()` 或 `propagate_attributes(session_id=task_id)` | `collector.start_task(task_id, agent_name, trace_id=...)` |
| 結構化 log | — | `event=trace_start` JSON line |
| 回傳 | `trace_id` 寫入 Langfuse trace id 欄 | `record.trace_id`, `record.task_id` |

**Metadata（root，允許鍵見 `langfuse_metadata.json`）**

| Langfuse key | M-line 欄位 |
|--------------|-------------|
| `trace_schema_version` | 常數 `agent-metrics-v1` |
| `task_id` | `task_id` |
| `agent_name` | `agent_name` |
| `trace_id` | `trace_id` |
| `session_id` | 同 `task_id`（建議） |

### 2.2 `start_span` / `end_span`

| 動作 | Langfuse | M-line |
|------|----------|--------|
| span 開始 | `span.start(name, metadata)` | `event=span_start` |
| span 結束 | `span.end()` + usage | `log_step(name, duration_ms, token_delta, metadata)` |
| 子 agent | metadata `agent` | `step.metadata.agent` |

### 2.3 `end_trace(success, error_type?, ...)`

| 動作 | Langfuse | M-line |
|------|----------|--------|
| 關閉 root | 更新 trace metadata + tags | `collector.end_task(...)` |
| 失敗 | `level=ERROR` 或 score `0` | `error_type`, `success=false` |
| 完整度 | 可選 score | `trace_completeness.score`（D4） |

**Tags 模板**（來自 schema `langfuse_hints.tags_template`）

```
gov-core
agent:{agent_name}
success:{true|false}
```

**Trace metadata 鍵**（schema `langfuse_hints.trace_metadata_keys`）

- `task_id`, `agent_name`, `success`, `retry_count`, `step_count`
- `handoff_count`, `memory_hit_rate`, `error_type`, `external_call_count`
- `trace_completeness.score`（扁平鍵名建議：`trace_completeness_score` 若需進 allowlist 須擴 schema）

### 2.4 `log_event` / `log_metric`

| API | Langfuse | M-line |
|-----|----------|--------|
| `log_event` | `event` 或 span annotation | 可選 `log_step`（`as_step=True`） |
| `log_metric` | 自定義 observation metadata | `log_step("metric:{name}")` + `custom_metrics` flush |

---

## 3. Usage（token）映射

Schema `langfuse_hints.usage_mapping`:

| Langfuse usage | M-line path |
|----------------|-------------|
| `input` / `prompt_tokens` | `context_token_usage.prompt_tokens` |
| `output` / `completion_tokens` | `context_token_usage.completion_tokens` |
| `total` / `total_tokens` | `context_token_usage.total_tokens` |

每個 span 的 `token_delta` 在 `end_span` 時累加入 task 級 `context_token_usage`。

---

## 4. 維度 D1–D5 → Langfuse 儀表

| 維度 | 主要指標 | Langfuse 建議 |
|------|----------|---------------|
| D1 | `success_rate`, `retry_count`, `step_count` | trace metadata + 聚合 |
| D2 | `context_token_usage`, `memory_hit_rate` | generation usage + metadata |
| D3 | `handoff_count` | metadata |
| D4 | `trace_completeness.score` | metadata / 自訂 score |
| D5 | `error_type`, `external_call_count` | metadata + `level` |

---

## 5. 接線順序（實作期）

1. Agent 入口：`with agent_run_trace("my_agent"):`（強制 `trace_start` / `agent_run_*` / `trace_end` log）。
2. 每 graph node / tool：`start_span` … `end_span` 或 `log_event(..., as_step=True)`。
3. Langfuse SDK 包在 `gov_core_system/core/observability.py` 內讀 M-line `record` 寫 metadata（失敗不阻斷主流程）。
4. PG ingest：`task_runs` ← `record` 子集（見 `metric_definition.md` §6.4）。

---

## 6. 合規

- 不輸出 `.env`、token、secret；metadata 走 `sanitize_langfuse_metadata`（暗部 v2）。
- `langfuse_metadata.json` 為允許鍵上限；新增鍵須擴 schema 與測試。
- 雙寫時以 **M-line record 為準**，Langfuse 為投影層。
