# Tool Layer v1 — Runbook

> **版本**：`tool_layer_v1` · **狀態**：可本地重跑驗證 · **非 production-ready**  
> **權威設計**：`04_Workflows/SPEC_tool_catalog_and_selector_v1.md`（T1–T3 細節）· 本檔為 **操作／驗收／交接** 入口。  
> **實作根**：暗部 cabin `gov_core_system`（路徑見 `Master_Map.json` → cabins）。

---

## 1. Purpose / 範圍

### 1.1 Tool Layer v1 解決什麼

- 在 **有限靜態工具池** 上，依工單（`ToolSelectionRequest`）與 Gate 分數 **表驅動選工具**（S1–S12）。
- 將選擇結果寫入 **可審計** 的 `tool_decision_log_v1`（JSONL append-only）。
- **依序執行** 已選工具（fail-fast），附 Langfuse child span + `step_runs`（軟失敗不阻斷工具結果）。
- 執行後 **回寫** ledger 的 `actual_*` 與 `structured_error_refs`（T6c patch）。

### 1.2 本 runbook 涵蓋

| 包含 | 不包含 |
|------|--------|
| T1–T6 切片模組、命名、本地 unittest | `app_api` / LangGraph 生產接線 |
| E2E／bridge 測試怎麼跑 | 動態工具註冊、venv 安裝新套件 |
| 已知限制與下一步 | 改 catalog JSON 以外的核心邏輯 |

### 1.3 切片（T1–T6）

| 切片 | 職責 | 主要模組 | 測試模組 |
|------|------|----------|----------|
| **T1** | Wire JSON schema（catalog + decision log） | `shared/schemas/tool_catalog_v1.json`、`tool_decision_log_v1.json` | `tests.test_tool_layer_schemas` |
| **T2** | 載入／校驗 catalog | `core/tool_catalog.py`、`core/schemas/tool_catalog.py` | 同上 |
| **T3** | 表驅動選工具 + params | `core/tool_selector.py`、`core/tool_params.py` | `tests.test_tool_selector` |
| **T4** | JSONL 決策帳本（冪等 `decision_id`） | `core/tool_decision_log.py` | `tests.test_tool_decision_log` |
| **T5** | Selector 觀測（span + `task_runs.metadata`） | `core/tool_selector_observability.py` | `tests.test_tool_selector_observability` |
| **T6a** | Executor 骨架（runner registry） | `core/tool_executor.py` | `tests.test_tool_executor` |
| **T6b** | Executor 觀測（span + `step_runs`） | `core/tool_executor_observability.py` | `tests.test_tool_executor_observability` |
| **T6c** | Ledger `actual_*` 回寫 | `core/tool_decision_log_patch.py` | `tests.test_tool_decision_log_actuals` |
| **Facade** | 一鍵四步鏈 | `core/tool_flow_bridge.py` → `run_tool_flow()` | `tests.test_tool_flow_bridge` |
| **E2E** | select → execute → patch（tmpdir + mock） | 跨模組 | `tests.test_tool_layer_e2e` |

靜態 catalog 目前 **8** 個 `tool_id`（見 `load_catalog()` 驗收）。

---

## 2. Architecture 概覽

```text
tool_catalog_v1.json
        │
        ▼
   load_catalog() ──► catalog index
        │
        ▼
   select_tools(request) ──► tool_decision_log row (in-memory)
        │                      │
        │                      ▼
        │              append_tool_decision_log() ──► runtime/tool_decisions.jsonl
        │                      │
        ▼                      ▼
   (T5 observability)    execute_selected_tools(selection_result, context?)
        │                      │
        │                      ├──► Langfuse: tool_executor.{safe_id}
        │                      └──► step_runs.step_name: tool.{safe_id}
        │                      │
        ▼                      ▼
   task_runs.metadata     patch_tool_decision_log_with_actuals()
                          └── actual_outcome, actual_tools_used,
                              structured_error_refs, actual_latency_ms
```

**編排捷徑**（給 bridge / orchestrator）：

```python
from core.tool_flow_bridge import run_tool_flow

summary = run_tool_flow(selection_request, trace_id="optional-trace")
# summary keys: ok, message, decision_id, selection_result,
#               append_result, execution_result, patch_result
```

`run_tool_flow` 順序：`select_tools` → `append_tool_decision_log` → `execute_selected_tools` → `patch_tool_decision_log_with_actuals`。  
頂層 `summary["ok"]` 為 **全流程** 成功（含 execution 全綠）；部分工具失敗時 execution 可 `ok: false` 但 patch 仍可能成功（見 E2E）。

---

## 3. 命名契約

實作權威：`core/tool_executor_observability.py`。

| 用途 | 規則 | 範例 `llm.ask` |
|------|------|----------------|
| `safe_tool_id(tool_id)` | `.` → `_` | `llm_ask` |
| Langfuse span / `structured_errors.node` | `tool_executor.{safe_tool_id}` | `tool_executor.llm_ask` |
| `step_runs.step_name` | `tool.{safe_tool_id}` | `tool.llm_ask` |

Selector 側（T5）固定 span 語意：`tool_selector`（見 `core/observability_spans.py` 常量）。

**禁止**：在程式或文檔中自創第三套 span 前綴；擴充工具時只改 catalog `tool_id`，命名由 `safe_tool_id` 衍生。

---

## 4. 主要模組與檔案位置

路徑均相對 **gov_core_system** cabin 根。

| 模組 | 路徑 | 對外入口（dict 回傳） |
|------|------|------------------------|
| Catalog | `core/tool_catalog.py` | `load_catalog()`, `get_tool_by_id()` |
| Pydantic 模型 | `core/schemas/tool_catalog.py` | `ToolCatalogV1`, `ToolSelectionRequest`, … |
| Selector | `core/tool_selector.py` | `select_tools(request: dict)` |
| Params | `core/tool_params.py` | `build_tool_params()`（selector 內部） |
| Ledger | `core/tool_decision_log.py` | `append_tool_decision_log()`, `tool_decisions_jsonl_path()` |
| Executor | `core/tool_executor.py` | `execute_selected_tools()`, `register_executor_handler()` |
| Executor 觀測 | `core/tool_executor_observability.py` | `observe_tool_execution()`, `safe_tool_id()` |
| Actuals patch | `core/tool_decision_log_patch.py` | `patch_tool_decision_log_with_actuals()` |
| Selector 觀測 | `core/tool_selector_observability.py` | `record_tool_selection_observability()` |
| Flow facade | `core/tool_flow_bridge.py` | `run_tool_flow()` |

**Wire contract**：

- `shared/schemas/tool_catalog_v1.json`
- `shared/schemas/tool_decision_log_v1.json`

**執行期 ledger 預設**：`runtime/tool_decisions.jsonl`（測試可覆寫，見 §5.3）。

---

## 5. 如何本地驗證

### 5.1 前置

1. 工作目錄切到 gov_core cabin：

```powershell
Set-Location 01_Environments\python_venvs\gov_core_system
```

2. 使用該 cabin 的 Python（見 `04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md` §3）。

3. 不需 Postgres／Langfuse 即可跑 Tool Layer unittest（觀測路徑已 mock 或 soft-fail）。

### 5.2 模組測試（建議順序）

> **注意**：`tests.test_tool_catalog` **不存在**。Catalog／schema 測試請用 **`tests.test_tool_layer_schemas`**。

```powershell
# T1 + T2 — schema 檔存在、load_catalog、8 tools、decision log 初始無 actual_*
python -m unittest tests.test_tool_layer_schemas -v

# T3 — S1–S12 表驅動
python -m unittest tests.test_tool_selector -v

# T4 — JSONL 冪等
python -m unittest tests.test_tool_decision_log -v

# T5
python -m unittest tests.test_tool_selector_observability -v

# T6a / T6b
python -m unittest tests.test_tool_executor -v
python -m unittest tests.test_tool_executor_observability -v

# T6c
python -m unittest tests.test_tool_decision_log_actuals -v

# Facade
python -m unittest tests.test_tool_flow_bridge -v
```

### 5.3 Tool Layer 全量回歸（一鍵）

```powershell
Set-Location 01_Environments\python_venvs\gov_core_system
python -m unittest discover -s tests -p "test_tool*.py" -v
```

預期：**45 tests, OK**（截至 2026-05-22 驗收）。

### 5.4 E2E：`tests/test_tool_layer_e2e.py`

**驗什麼**

1. `select_tools()` 真實跑 selector（`force_tool_ids`: `llm.ask`, `code.runner`）。
2. 以固定 `decision_id` 寫入 tmpdir JSONL，再 `execute_selected_tools` + `patch_tool_decision_log_with_actuals`。
3. 斷言：`llm.ask` stub 成功；`code.runner` `not_implemented` + `TOOL_EXECUTION_NOT_IMPLEMENTED`；`actual_outcome == partial`。
4. Mock 觀測：span 名 `tool_executor.llm_ask` / `tool_executor.code_runner`；step `tool.llm_ask` / `tool.code_runner`；`structured_error_refs[].node == tool_executor.code_runner`。

**tmpdir / mock 做法**

| 機制 | 用途 |
|------|------|
| `tempfile.TemporaryDirectory` + `set_tool_decisions_jsonl_path_for_tests(path)` | 隔離 JSONL，不污染 `runtime/tool_decisions.jsonl` |
| `patch("core.tool_selector_observability.record_tool_selection_observability")` | Selector 觀測 no-op |
| `patch tool_executor_span` / `upsert_step_run` / `is_monitoring_pg_enabled` | 不連真 PG／Langfuse |
| `patch utc_now` | 穩定 `latency_ms` |

```powershell
python -m unittest tests.test_tool_layer_e2e -v
```

### 5.5 與 Phase 7.5 橋接回歸（可選）

改 Tool Layer 後建議順跑 intake 橋，避免破壞既有 min loop：

```powershell
python -m unittest tests.test_intake_min_loop_gate tests.test_minimal_orchestration_bridge -v
```

（命令來源：`SPEC_tool_catalog_and_selector_v1.md` §9。）

---

## 6. Executor 行為速查（T6a）

| `executor_binding.runner` | 現狀 |
|---------------------------|------|
| `ask_pipeline` | stub 成功（`llm.ask`） |
| `browser_runner` | stub 成功 |
| `interrupt_service` | `human.review_checkpoint` 流程節點 |
| `chariot.factory`, `dark.data`, `gov_paths`, `notification_dispatcher` | `not_implemented` |
| 未註冊 runner | 同上，穩定 `TOOL_EXECUTION_NOT_IMPLEMENTED` |

擴充真實執行：`register_executor_handler(runner, handler)`，勿改 selector 契約。

---

## 7. 已知限制

1. **T1–T6 + `run_tool_flow()` v1 已完成且有測試**（見 §5.2–§5.3）。**Bridge 白名單**已接入 `minimal_orchestration_bridge`（`info_query` + `accepted` + `tool_flow` + 無 browser plan）；測試見 `tests.test_minimal_orchestration_bridge_tool_flow`。尚未接入：`app_api` 對外 opt-in、`LangGraph` 生產圖。
2. **JSON Schema 與執行後欄位**：`actual_tools_used`、`structured_error_refs` 的 wire 形狀與 `tool_decision_log_v1.json` 仍待完全對齊（實作以 pydantic + patch 為準）。
3. **Executor**：多數 runner 為 stub／`not_implemented`；`code.runner` 等綁定尚未接真實 pipeline。
4. **Catalog 熱更新**：v1 不支援；改 JSON 需重載進程或 bump `catalog_revision`。
5. **白名單範圍**：僅 `info_query` + `lifecycle_status == accepted`；其他 `request_type`／lifecycle 仍走 legacy bridge。詳見 `SPEC_tool_catalog_and_selector_v1.md` §10。

---

## 8. 下一步建議

| 優先 | 項目 | 說明 |
|------|------|------|
| P0 | **擴大 Tool Flow 覆蓋** | 新增 `request_type`／`lifecycle_status` 白名單條件，或在 `app_api` 暴露 `tool_flow` opt-in 入口；不再是「是否接線」 |
| P1 | **Schema 對齊** | `tool_decision_log_v1.json` ↔ patch 輸出；CI 可加 schema validate on patched row |
| P2 | **上層 orchestration** | `POST /api/orchestration/bridge`（或等價）對外文件化 `tool_flow` 區塊與 `decision_id` / `actual_outcome` |
| P3 | **Executor 實作** | 按 catalog `executor_binding.runner` 逐個替換 stub |
| 文檔 | Bridge §10 | 白名單條件與 ASCII 見 `SPEC_tool_catalog_and_selector_v1.md` §10 |

---

## 9. 相關索引

| 文件 | 用途 |
|------|------|
| `04_Workflows/SPEC_tool_catalog_and_selector_v1.md` | S1–S12、catalog 欄位、決策 log 欄位語意 |
| `04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md` | cabin 進場、Python 入口 |
| `AGENTS.md` | 接戰／封存；runner 索引見 `Master_Map.json` |

---

*Tool Layer v1 runbook · 文檔工單 · 零核心程式變更*
