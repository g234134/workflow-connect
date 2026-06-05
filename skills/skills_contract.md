# J-Line Skills Contract (v0.1)

> **Scope**: Skill-side observability seed only. Does not modify `ask_pipeline`, `langgraph_flow`, or agent graphs.  
> **Authority**: `metrics/metrics_schema.json`, `reliability/retry_policy.md`, `observability/logging_adapter.py`

---

## 1. Purpose

Provide a **single wrapper pattern** so every skill/tool invocation automatically records:

- D1 reliability (`retry_count`, `error_type`)
- M-line task metrics (`MetricsCollector`)
- D4 trace steps (optional `TraceContext` + span)
- D5 hook for `external_call_count`

Future skills should copy `skills/skill_runner.py` instead of ad-hoc logging.

---

## 2. Minimal constraints (every skill)

| Requirement | Rule |
|-------------|------|
| Entry signature | `run_skill_<name>(task_id, *, params..., collector=None, trace_ctx=None, **context)` |
| Return shape | `{ ok, result, error_type, retry_count, metadata }` |
| `task_id` | Required non-empty string; ties to M-line task record |
| `error_type` | On failure: one of `metrics_schema.json` → `error_type_enum`; on success: `null` |
| `retry_count` | Must match `run_with_retry` output (retries after initial attempt) |
| `metadata` | Must include `skill_name`; SHOULD include `agent_name` / `call_site` when invoked by an agent |
| Collector | Injectable `MetricsCollector`; default `get_collector()` |
| Trace | Optional `TraceContext`; when absent, skill still writes M-line metrics if `task_id` is started |

---

## 3. Standard call flow

```
run_skill_x(task_id, params..., collector?, trace_ctx?)
  → _ensure_task(collector, task_id)          # M-line start_task if missing
  → start_span / log_event (if trace_ctx)   # D4
  → run_with_retry(core_fn)                 # P-line
       core_fn:
         record_external_call + log_metric   # D5 hook
         optional simulated ReliabilityError # tests / drills
         return business result
  → end_span + structured return dict
```

Core business logic stays in a **private** `_mock_*` or `_perform_*` function; the public `run_skill_*` is the metrics façade.

---

## 4. Alignment with D1 / D3 / D4

### D1 (reliability / success rollups)

- `retry_count` and `error_type` come from `reliability.run_with_retry`.
- Classify failures via `ReliabilityError(error_type=...)` or exception taxonomy in `classify_error`.
- Do not invent retry counts in `metadata` alone — the top-level `retry_count` field is authoritative.

### D3 (handoff / caller context)

- When an agent invokes a skill, pass:
  - `agent_name` → stored in `metadata.agent_name` and used as M-line `agent_name` when starting a standalone task
  - `call_site` → e.g. `"ask_pipeline.retrieve_node"`, `"data_agent.tool_loop"`
- Handoffs between agents remain on the **agent** layer (`record_handoff`); skills only annotate caller context in `metadata`.

### D4 (trace completeness)

- If the caller already opened `start_trace` / `agent_run_trace`, pass `trace_ctx` so the skill emits:
  - `start_span` / `end_span` for the skill step
  - `log_event` for `{skill_name}_start` / `_end`
  - `log_metric("external_call_count", 1)` when touching external systems (mock or real)
- Standalone skill calls without `trace_ctx` still update `MetricsCollector` (steps via retry error logs).

---

## 5. External systems hook (D5 reserved)

Inside `core_fn` (via `run_metrics_aware_skill`):

1. `collector.record_external_call(task_id, count=1)` per outbound call
2. Optional `log_metric("external_call_count", 1, trace_ctx=...)` when a trace is active

Real HTTP/DB/Qdrant clients must not be imported in v0.1 seeds — use mocks until infra tickets land.

---

## 6. v0.1 seed skills

| Skill | Module | Mock backend | Retry demo |
|-------|--------|--------------|------------|
| Vector retrieve | `example_skill_retrieve.py` | `_mock_qdrant_search` | `simulate_first_failure=True` → `timeout`, 1 retry |
| PG business query | `example_skill_pg_query.py` | `_mock_pg_lookup` | Same flag for tests |

---

## 7. Adding a new skill (checklist)

1. Implement `_perform_<op>(...)` with no metrics side effects.
2. Add `run_skill_<op>(task_id, *, ..., collector=None, trace_ctx=None)` calling `run_metrics_aware_skill`.
3. Set unique `SKILL_NAME` and `step_name` for spans.
4. Document params in this file or module docstring.
5. Add tests under `tests/test_skills_metrics.py` (success + optional retry path).
6. Do **not** wire into `ask_pipeline` until a separate integration ticket.

---

## 8. Ask mainline wiring (I-ask-skills-wire)

> **Scope**: `gov_core_system` LangGraph ask graph only. Does not change `/api/ask` response keys.

### Insertion layer

| Layer | Choice | Rationale |
|-------|--------|-----------|
| LangGraph node | **Yes** | `retrieve_node` / `answer_node` are the stable tool call sites |
| `tool_executor` | **Yes** (`rag.retrieve` only) | `ask_pipeline` runner → `tool_executor_skills_bridge` |
| Pipeline wrapper | Via I-bridge | `run_ask_with_ibridge_v0` still owns `build_rooted_context` + `agent_run_trace`; nodes call skills inside the trace |

Bridge module: `gov_core_system/core/ask_skills_wire.py` → repo-root `skills/skill_*_for_ask.py` → `run_metrics_aware_skill`.

### Wired skills

| skill_name | Module | call_site | Input (core_fn closure) | Output (unchanged) |
|------------|--------|-----------|---------------------------|-------------------|
| `skill_retrieve_for_ask` | `skill_retrieve_for_ask.py` | `langgraph_flow.retrieve_node`; `tool_executor.ask_pipeline` (`rag.retrieve`) | `perform_retrieve_query(query, top_k)` via `core.retrieve_core` | retrieve dict (`ok`, `message`, `hits`, …) |
| `skill_answer_for_ask` | `skill_answer_for_ask.py` | `langgraph_flow.answer_node` | `rag_answer` via `invoke_with_model_fallback` | answer dict (`ok`, `message`, `answer`, …) |

`task_id`: `_ibridge_task_id` when I-bridge active, else `integration_hooks.resolve_run_id(state)` (`thread_id` / `session_id` / UUID).

Simulated retrieve retry (I-bridge drills): `_ibridge_simulate_retrieve_retry` → `simulate_first_failure` on retrieve skill only.

### Metrics mapping (D1 / D3 / D4 / D5)

| Domain | Fields / events |
|--------|-----------------|
| **D1** | Top-level `retry_count`, `error_type`; M-line `record.retry_count` |
| **D3** | `metadata.agent_name` (`ask_pipeline`), `metadata.call_site` |
| **D4** | Spans `retrieve` / `execute`; events `{skill_name}_start` / `_end` when `trace_ctx` active |
| **D5** | `record.external_call_count`; `log_metric("external_call_count", 1)` per attempt |

### Tool executor bridge (J-tool-executor-bridge)

| Entry | Module | Skill | call_site | task_id source |
|-------|--------|-------|-----------|----------------|
| T6 `execute_selected_tools` → `rag.retrieve` | `gov_core_system/core/tool_executor_skills_bridge.py` | `skill_retrieve_for_ask` (via `ask_skills_wire.run_retrieve_via_skill`) | `tool_executor.ask_pipeline.rag.retrieve` | `context.task_id` / `run_id` / `thread_id` / `trace_id` / `decision_id` / `work_order_id` |
| T6 `execute_selected_tools` → `llm.ask` | same bridge | `skill_answer_for_ask` (via `run_answer_via_skill` + `perform_direct_answer`) | `tool_executor.ask_pipeline.llm.ask` | same as retrieve row |
| LangGraph `retrieve_node` | `langgraph_flow` + `ask_skills_wire` | same | `langgraph_flow.retrieve_node` | `_ibridge_task_id` or `resolve_run_id(state)` |

Shared retrieve core: `gov_core_system/core/retrieve_core.perform_retrieve_query` (stub or `document_chunks_smoke_retrieve_and_verify`).

Executor row shape unchanged: top-level `ok` / `status` / `output_summary`; retrieve payload nested under `output_summary.retrieve`; answer payload nested under `output_summary.answer` (§11).

Drill flag: `context["simulate_retrieve_retry"]=True` → `simulate_first_failure` on the retrieve skill (same semantics as I-bridge `_ibridge_simulate_retrieve_retry`).

### Tests (§8 retrieve + bridge)

- Unit: `tests/test_skills_ask_wire.py` (repo root), `gov_core_system/tests/test_ask_skills_wire_e2e.py`
- Tool executor bridge: `gov_core_system/tests/test_tool_executor_skills_bridge.py`（`rag.retrieve` + `llm.ask`）
- I-bridge regression: `gov_core_system/tests/test_ask_pipeline_ibridge_v0.py`

### Not wired (post Wave 3 · executor llm.ask)

| Tool / path | Reason |
|------|--------|
| `health_node` / `run_full_healthcheck` | Infra gate, not outbound business tool |
| `example_skill_pg_query` | PG reads are inside `document_chunks_smoke_retrieve_and_verify` (R2), not a separate ask node |
| K-2 executor / reviewer agents | K-2 uses stub agents; answer skill merge via `ASK_MERGE_INTERFACE` shadow path (K2-ask-shadow-merge) |

---

## 9. Answer-side skills (回答侧 skills)

> **Scope**: Ask mainline answer path only (`skill_answer_for_ask`). Retrieve-side contract remains §8.

### 9.1 Entry point

| Item | Value |
|------|-------|
| Public API | `run_skill_answer_for_ask(task_id, *, core_fn, collector?, trace_ctx?, agent_name?, call_site?, simulate_first_failure?)` |
| Bridge | `gov_core_system/core/ask_skills_wire.py` → `run_answer_via_skill(core_fn, *, task_id, simulate_first_failure?, call_site?)` |
| Default `call_site` | `langgraph_flow.answer_node` |
| Default `agent_name` | `ask_pipeline` |
| Span `step_name` | `execute` (aligns with I-bridge execute span) |

### 9.2 Input / output

**Input (via bridge closure)**

- `core_fn`: zero-arg callable returning answer dict from `rag_answer` + `invoke_with_model_fallback`
- `task_id`: non-empty; from `_ibridge_task_id` or `integration_hooks.resolve_run_id(state)`
- Optional `simulate_first_failure`: drills only; first attempt raises `ReliabilityError(timeout)` then retries

**Output (unchanged downstream shapes)**

- Skill wrapper: `{ ok, result, error_type, retry_count, metadata }` per §2
- Bridge returns `(answer_dict, retry_meta)` where `answer_dict` matches legacy `rag_answer` keys (`ok`, `message`, `answer`, …)
- `/api/ask` response schema unchanged; skill metrics live in M-line record / optional `ibridge_record`

**`retry_meta` keys**: `retry_count`, `error_type`, `skill_name`, `call_site`, `external_call_count`

### 9.3 D-dimension coverage

| Domain | Answer-side fields |
|--------|-------------------|
| **D1** | `retry_count`, `error_type` on skill result; M-line `record.retry_count` |
| **D3** | `metadata.agent_name`, `metadata.call_site` |
| **D4** | Span `execute`; events `skill_answer_for_ask_start` / `_end` when `trace_ctx` active |
| **D5** | `record.external_call_count` incremented per LLM attempt inside skill |

### 9.4 call_site convention

| Path | `call_site` |
|------|-------------|
| LangGraph `answer_node` | `langgraph_flow.answer_node` |
| I-bridge execute span | same (skill runs inside `ibridge_execute_span`) |
| Tool executor `llm.ask` | `tool_executor.ask_pipeline.llm.ask`（§11；core_fn = `perform_direct_answer` only） |

### 9.5 Tests

- Unit: `tests/test_skills_ask_wire.py` — success, simulated retry, `llm_error` exhaustion
- E2E: `gov_core_system/tests/test_ask_skills_wire_e2e.py` — legacy + ibridge; asserts `execute` step and `external_call_count`

---

## 10. Ask RAG selector (selector 收敛 · Chat B)

> **Scope**: Ask LangGraph mainline only (`selector_node` → retrieve or direct answer). Tool-layer `tool_selector` (S1–S12) unchanged.

### 10.1 Entry point

| Item | Value |
|------|-------|
| Module | `gov_core_system/core/ask_rag_selector.py` |
| API | `decide_use_rag(query, *, context_payload=None, task_input=None) -> dict` |
| Graph node | `langgraph_flow.selector_node` (after `health_node`) |
| Direct answer | `gov_core_system/core/ask_direct_answer.py` → `perform_direct_answer` |

### 10.2 Decision rules (ASK-R1 … ASK-R6)

| Rule | Condition | `use_rag` |
|------|-----------|-----------|
| **ASK-R1** | `selector_hints.force_no_rag` / `force_rag` | forced off / on |
| **ASK-R2** | Empty query; greeting/chitchat (`你好`, `hello`, `好的`, …) | `false` |
| **ASK-R3** | Short query (`len < 10`) without KB signals | `false` |
| **ASK-R4** | H-line KB: `context_refs`, tags `rag`/`knowledge`, or semantic memory | `true` |
| **ASK-R5** | Knowledge-seeking patterns (`pipeline`, `如何`, `explain`, …) | `true` |
| **ASK-R6** | Default substantive ask query | `true` |

Overrides via `task_input.selector_hints` or `context_payload.task_input.selector_hints`.

### 10.3 Scenarios (regression)

| ID | Scenario | Expected path | Primary test |
|----|----------|---------------|--------------|
| **S1** | KB context + knowledge question | `selector` → `retrieve` → `answer` (RAG) | `TestAskSelectorFlowIntegration.test_s1_flow_with_context_runs_retrieve_and_answer_skills` |
| **S2** | Greeting / no retrieve | `selector` → `answer` (direct); answer skill + metrics | `TestAskSelectorFlowIntegration.test_s2_greeting_skips_retrieve_answer_skill_still_runs` |
| **S3** | Retrieve failure | `retrieve` fail → `answer` direct fallback; `retrieve_fallback` + `error_type` on answer / `ibridge_v0.selector_decision` | `TestAskSelectorFlowIntegration.test_s3_retrieve_failure_falls_back_to_direct_answer_with_tags` |

Test file: `tests/test_ask_selector_and_answer.py` (repo root).

### 10.4 Observability

| Signal | Where |
|--------|-------|
| Langfuse span | `ask_rag_selector` (`selector_node`) |
| Trace event | `ask_rag_selector_decision` |
| M-line step | `ask_rag_selector` on task record |
| I-bridge expose | `ibridge_v0.selector_decision` (`use_rag`, `selector_rule_id`, `answer_mode`, `retrieve_fallback`) |
| Answer payload | optional `answer_mode`, `retrieve_fallback`, `retrieve_error_type` (schema: `RagAnswerResult`) |

### 10.5 Graph routing (ask)

```
health → selector → [use_rag? retrieve → answer : answer] → END
```

Retrieve failure (S3) always continues to `answer_node` with `answer_mode=direct_fallback`.

---

## 11. Tool executor `llm.ask` wiring（J-tool-executor-llm-ask-skill）

> **Scope**: `execute_selected_tools` → `ask_pipeline` runner → catalog `llm.ask` only. Does not change LangGraph `answer_node` (§9) or tool_selector rules.

### 11.1 Entry point

| Item | Value |
|------|-------|
| Handler | `gov_core_system/core/tool_executor_skills_bridge.py` → `_execute_llm_ask` |
| Skill | Reuse `skill_answer_for_ask` via `ask_skills_wire.run_answer_via_skill` |
| Core | `perform_direct_answer(query_text)` only（裁決 A：不接同批 retrieve 上下文） |
| `call_site` | `tool_executor.ask_pipeline.llm.ask` |
| Drill | `context["simulate_answer_retry"]=True` → `simulate_first_failure` on answer skill |

### 11.2 Input / output

**Input**

- `params.query_text` (required)
- `task_id` from executor `context`（同 §8 bridge：`task_id` / `run_id` / `thread_id` / `trace_id` / `decision_id` / `work_order_id`）

**Output (executor row)**

- Top-level `ok` / `status` unchanged
- `output_summary`: `stub=False`, nested `answer` dict, `skill_name`, `skill_retry_count`, `call_site`
- Langfuse span name remains `tool_executor.llm_ask`（observability 层不变）

### 11.3 D-dimension coverage

| Domain | Fields |
|--------|--------|
| **D1** | `skill_retry_count` on row; M-line `record.retry_count` |
| **D3** | `metadata.agent_name=ask_pipeline`, `metadata.call_site` |
| **D4** | Tool span `tool_executor.llm_ask` + skill events when `trace_ctx` active |
| **D5** | `record.external_call_count` per answer skill attempt |

### 11.4 Tests

- `gov_core_system/tests/test_tool_executor_skills_bridge.py` — `test_llm_ask_uses_skill_metrics`, `test_llm_ask_simulated_retry_increments_metrics`
- `gov_core_system/tests/test_tool_executor.py` — `test_ask_pipeline_llm_ask_dispatch`

---

## 12. References

- M-line: `metrics/metrics_collector.py`, `metrics/metrics_schema.json`
- P-line: `reliability/retry_handler.py`
- O-line: `observability/logging_adapter.py`
- Prior art: `core/langgraph_flow_k1.py`, `gov_core_system/core/ask_skills_wire.py`
