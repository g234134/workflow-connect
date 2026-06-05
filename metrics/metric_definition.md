# Agent Metrics Schema (v1)

> 權威 JSON Schema：`metrics/metrics_schema.json`  
> 採集 stub：`metrics/metrics_collector.py`  
> 維度對照：D1–D5（可記錄、可統計、可對接 Langfuse / 結構化 logging）

---

## 1. 設計目標

將 agent 系統的觀測需求收斂為**單筆 task 記錄** + **維度映射**，使：

1. 執行期可由 `MetricsCollector` 寫入記憶體（或日後 PG / JSONL）。
2. 聚合期可按 D1–D5 出 KPI（成功率、token、handoff、trace 完整度、錯誤分類）。
3. 觀測期可將同名字段寫入 Langfuse trace metadata / generation usage，無需二次發明欄位名。

---

## 2. 維度映射（Dimension Mapping）

| 維度 | 語意 | 指標 | 來源欄位 |
|------|------|------|----------|
| **D1** | 可靠性與執行深度 | `success_rate`, `retry_count`, `step_count` | `success`, `retry_count`, `step_count` |
| **D2** | 上下文與記憶效率 | `context_token_usage`, `memory_hit_rate` | `context_token_usage`, `memory_hit_rate` |
| **D3** | 多 agent 協調 | `handoff_count` | `handoff_count` |
| **D4** | Trace 完整度 | `trace_completeness` | 必填欄位**存在性**（見下） |
| **D5** | 失敗分類與外部 I/O | `error_type`, `external_call_count` | `error_type`, `external_call_count`, `errors[]` |

### D4 — trace completeness

以**欄位是否已填且非空**計分，不評判業務對錯：

- 必填集合（預設）：`task_id`, `agent_name`, `start_time`, `end_time`, `success`, `step_count`, `context_token_usage`, `trace_id`
- `score = len(present) / len(required)`，範圍 `[0, 1]`
- 由 `compute_trace_completeness()` / `end_task()` 自動寫入 `trace_completeness`

### D1 — success_rate

- **Task 級**：`success_rate = 1.0`（成功）或 `0.0`（失敗），在 `end_task()` 設定。
- **窗口聚合**：`MetricsCollector.aggregate_success_rate()` → 已結束 task 的算術平均。

---

## 3. 欄位定義

### 3.1 識別與時間

| 欄位 | 類型 | 說明 |
|------|------|------|
| `task_id` | string | 單次 agent 任務唯一 ID；可對齊 Langfuse session / thread。 |
| `agent_name` | string | 邏輯 agent 或 workflow 名（如 `ask_pipeline`）。 |
| `start_time` | ISO 8601 UTC | `start_task()` 時寫入。 |
| `end_time` | ISO 8601 UTC \| null | `end_task()` 時寫入；進行中為 null。 |

### 3.2 結果與執行（D1）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `success` | bool | 業務是否成功完成。 |
| `success_rate` | float 0–1 | 衍生；單 task 為 0/1。 |
| `retry_count` | int ≥ 0 | 重試次數；`log_error(..., increment_retry=True)` 可累加。 |
| `step_count` | int ≥ 0 | 邏輯步驟數；每次 `log_step()` 遞增。 |

### 3.3 上下文與記憶（D2）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `context_token_usage` | object | `{ prompt_tokens, completion_tokens, total_tokens }` 累計。 |
| `memory_hit_rate` | float 0–1 | 記憶/RAG 命中率；**未接真實記憶層前預設 0.0（mock）**。 |

### 3.4 協調（D3）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `handoff_count` | int ≥ 0 | agent 或階段交接次數；`record_handoff()`。 |

### 3.5 觀測完整度（D4）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `trace_completeness` | object | `{ score, present[], missing[], required_fields[] }` |
| `trace_id` | string \| null | Langfuse trace id，供 UI 與 PG ingest 對齊。 |
| `steps` | array | 逐步事件，供回放與完整度輔助。 |

### 3.6 錯誤與外部調用（D5）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `error_type` | enum \| null | `llm_error` \| `tool_error` \| `context_overflow` \| `timeout` \| `unknown`；成功時 null。 |
| `external_call_count` | int ≥ 0 | 預留：非 LLM 供應商的 HTTP/tool/API 次數。 |
| `errors` | array | `{ timestamp, error_type, message, step_index?, retryable? }` |

---

## 4. 計算方式

### 4.1 Token 累計

每次 `log_step(..., token_delta={...})`：

```
context_token_usage[k] += token_delta[k]   # k ∈ prompt|completion|total
```

若未提供 `total_tokens`，以 `prompt + completion` 補齊 step 級 delta。

### 4.2 Step 計數

```
step_count = len(steps)
```

### 4.3 Memory hit rate（mock → 真實）

**現狀**：`start_task()` 使用 `DEFAULT_MEMORY_HIT_RATE = 0.0`，或呼叫方傳入 `memory_hit_rate`。

**未來**：

```
memory_hit_rate = memory_hits / max(memory_lookups, 1)
```

由 RAG / agent memory 模組在每次 lookup 後回報增量，collector 只做加總與除法。

### 4.4 窗口 KPI 範例

| KPI | 公式 |
|-----|------|
| 成功率（D1） | `avg(success_rate)` over tasks in window |
| 平均重試（D1） | `avg(retry_count)` |
| 平均步數（D1） | `avg(step_count)` |
| 平均 token（D2） | `avg(context_token_usage.total_tokens)` |
| 平均 handoff（D3） | `avg(handoff_count)` |
| Trace 完整度（D4） | `avg(trace_completeness.score)` |
| 錯誤分布（D5） | `count(*) group by error_type` |

---

## 5. Python Collector API

```python
from metrics import get_collector

col = get_collector()
col.start_task("t1", "ask_pipeline", trace_id="lf-trace-abc")
col.log_step("t1", "retrieve", token_delta={"prompt_tokens": 120, "completion_tokens": 0, "total_tokens": 120})
col.log_error("t1", "tool_error", "qdrant timeout", increment_retry=True)
col.record_handoff("t1")
col.end_task("t1", success=False, error_type="tool_error")
```

| 方法 | 作用 |
|------|------|
| `start_task(task_id, agent_name, ...)` | 建立 task 記錄 |
| `end_task(task_id, success=..., ...)` | 結束並計算 `success_rate`、`trace_completeness` |
| `log_step(task_id, step_name, ...)` | 追加 step、累計 token |
| `log_error(task_id, error_type, message, ...)` | 追加錯誤、可選增加 retry |
| `record_handoff` / `record_external_call` | D3 / D5 計數輔助 |
| `aggregate_success_rate()` | D1 窗口聚合 stub |

所有方法回傳 **`dict`**，含 `ok`、`message`，成功時含 `record` 或 `task_id`。

---

## 6. 對接 Langfuse（未來）

與 `gov_core_system` 既有 `core/observability.py` 並行，不取代 Langfuse SDK，只做**欄位契約對齊**。

### 6.1 Trace 建立時（`start_task`）

- `propagate_attributes(session_id=task_id)` 或沿用既有 `thread_id` 規則。
- Root span metadata（扁平鍵，見 `metrics_schema.json` → `langfuse_hints.trace_metadata_keys`）：
  - `task_id`, `agent_name`, `trace_schema_version`（建議 `agent-metrics-v1`）

### 6.2 每個 step（`log_step`）

- Child span 名稱 = `step_name`。
- `generation` / observation 上報 `usage`：
  - `input` ← `prompt_tokens`
  - `output` ← `completion_tokens`
- metadata 附 `step_index`, `duration_ms`。

### 6.3 結束時（`end_task`）

- 更新 root metadata：`success`, `retry_count`, `step_count`, `handoff_count`, `memory_hit_rate`, `error_type`, `trace_completeness.score`。
- Tags：`gov-core`, `agent:{agent_name}`, `success:{true|false}`（模板見 schema `langfuse_hints.tags_template`）。
- 若 `success` 為 false，寫入 `level=ERROR` 或 Langfuse score（0/1）供儀表板過濾。

### 6.4 與 PG monitoring ingest

`task_runs` / `step_runs`  ingest 可映射：

| PG 概念 | metrics 欄位 |
|---------|----------------|
| `status` | `success` |
| `latency_ms` | `end_time - start_time` |
| `total_tokens` | `context_token_usage.total_tokens` |
| `metadata` JSON | 整包 `record` 或 D4/D5 子集 |

### 6.5 實作順序建議

1. 在 graph node / tool executor 邊界呼叫 `log_step` / `log_error`（僅記憶體 + JSON log）。
2. `end_task` 回傳的 `record` 併入 API `observability` dict（與現有 `trace_id` 並列）。
3. Langfuse `observe` wrapper 內讀 `record` 寫 metadata（單向，失敗不阻斷主流程）。
4. 批次 exporter 將 ended tasks 寫入 JSONL 或 `task_runs`（Phase 7+）。

---

## 7. 結構化 Logging

無 Langfuse 時，可將 `record` 以單行 JSON 寫入 logger `gov_core.metrics`：

```json
{"event":"task_end","task_id":"...","agent_name":"...","success":true,"trace_completeness":{"score":1.0}}
```

與 `core/observability_v2.log_event` 相同模式：不輸出 secret，不貼 `.env`。

---

## 8. 版本與變更

- **v1.0.0**：初版 schema + in-memory collector；`memory_hit_rate` mock；`external_call_count` 預留。
- 變更欄位名稱須同步：`metrics_schema.json`、`metric_definition.md`、Langfuse metadata 允許清單、dashboard contract。
