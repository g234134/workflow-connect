# Phase 7.5 — 智慧接單判斷層 MVP（資料清洗 intake / gate）

> **版本**：v0.1 · **範圍**：僅「資料清洗類工作」接單閘道；不接 RAG／GraphRAG／通用 HQ 協調。  
> **權威**：本檔（規格）· 實作 `gov_core_system/core/intake_decider.py` · 契約 `core/schemas/intake.py`

---

## 1. 目標

在暗部 `gov_core_system` 提供**可重跑、結構化 `dict`** 的接單閘道：

1. **Intake**：校驗請求形狀（Pydantic）。
2. **Gate**：判定 `accept` / `reject` / `defer`，並標註 `work_category`（本 MVP 僅對 `data_cleaning` 給出明確 accept 路徑）。

**非目標（v0.1 不做）**：接線 `app_api`、寫入 `pipeline_meta` DB、改 `task_routing_table.json`、DarkOps 解禁、實際啟動 wave runner。

---

## 2. 與既有制度的關係

| 既有資產 | 關係 |
|----------|------|
| `04_Workflows/task_routing_table.json` | `chariot.factory` / `dark.data` 關鍵字為 gate **建議路由** 依據（邏輯內嵌，不 import HQ `task_routing.py`） |
| `Departments/06_Strategy/code_cleaning_pipeline_v2.md` | 資料清洗域定義（raw_inbound → cleaned_full / format_error） |
| `Master_Map` `code_cleaning_pipeline_v2` | accept 時建議 `suggested_pipeline` |
| Phase 7（成本治理） | **無直接依賴**；本層為接單前閘道 |

---

## 3. 檔案落點

| 路徑 | 動作 | 職責 |
|------|------|------|
| `04_Workflows/PHASE7_5_INTAKE_GATE_MVP_PLAN_v0.1.md` | **新增** | 本規格 |
| `gov_core_system/core/schemas/intake.py` | **新增** | Pydantic 請求／回應模型 |
| `gov_core_system/core/intake_decider.py` | **新增** | 關鍵字評分 + gate 規則 + `decide_intake_gate()` |
| `gov_core_system/tests/test_intake_decider.py` | **新增** | 單元測試（無 DB／無 .env） |
| `gov_core_system/shared/schemas/intake_gate_v1.json` | **新增** | 跨模組 JSON 契約（request／result／gate_checks） |
| `gov_core_system/core/intake_phase6_5_mapping.py` | **新增** | accept／defer／reject → Phase 6.5 前置狀態與欄位映射 |

**不修改**：`.env`、`runtime/checkpoints/**`、`task_routing_table.json`（下一波可選同步關鍵字）。

---

## 4. 請求契約（`IntakeGateRequest`）

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `description` | str | 與 `tags`/`explicit_task_type` 至少其一 | 自然語言任務描述 |
| `tags` | list[str] | 同上 | 標籤（如 `raw_inbound`、`wave`） |
| `explicit_task_type` | str | 同上 | 若已知路由類型（如 `chariot.factory`） |
| `source_channel` | str | 否 | `telegram` / `cli` / `watchdog` / `unknown` |
| `file_extension_hints` | list[str] | 否 | 副檔名提示（`.py`、`.json` 等） |
| `inbound_path_hint` | str | 否 | 邏輯路徑提示（不得為磁碟絕對路徑；gate 會拒絕 `:\` 與 leading `/`） |
| `batch_size_hint` | int | 否 | 預估批次量；≤0 視為無效信號 |

---

## 5. Gate 判定（v0.1 規則摘要）

### 5.1 一律 reject

- 請求形狀無效（Pydantic）。
- `description` / `tags` / `explicit_task_type` 全空。
- `inbound_path_hint` 含硬編絕對路徑特徵（`\` 磁碟根、`:/`）。
- **強非清洗信號**且無清洗信號：例如僅 RAG／ingest_verify／graphrag／master_status 等（見程式 `OUT_OF_SCOPE_KEYWORDS`）。

### 5.2 defer（需澄清）

- 有泛用詞但清洗分數不足（例如「處理檔案」無副檔名／無 inbound／無 wave 語境）。
- 清洗與非清洗分數接近（模糊帶）。

### 5.3 accept（資料清洗）

滿足其一：

- `explicit_task_type` ∈ `{chariot.factory, dark.data}`；或
- 清洗關鍵字分數 ≥ 門檻 **且** 強於非清洗分數；或
- 出現 `code_cleaning_pipeline_v2` / `pipeline_meta` 等產線錨點。

Accept 回傳建議：

- `suggested_task_type`：`chariot.factory`（HQ 工廠艙）或 `dark.data`（暗部 metadata／ingest 語境）
- `suggested_pipeline`：`code_cleaning_pipeline_v2`

---

## 6. 回應契約（`decide_intake_gate` → `dict`）

| 欄位 | 說明 |
|------|------|
| `ok` | 解析成功為 `true`；形狀錯誤為 `false` |
| `decision` | `accept` \| `reject` \| `defer` |
| `work_category` | `data_cleaning` \| `other` \| `unknown` |
| `confidence` | 0.0–1.0（啟發式，非 ML） |
| `message` | 人讀摘要 |
| `suggested_task_type` | accept 時建議路由 |
| `suggested_pipeline` | accept 時建議產線名 |
| `gate_checks` | `{id, passed, detail}[]` 可審計清單 |
| `reasons` | 判定理由字串列表 |
| `schema_version` | `intake_gate_v1`（權威 JSON：`shared/schemas/intake_gate_v1.json`） |
| `phase6_5_pre_state` | Phase 6.5 對齊包（見下表） |

### 6.1 Phase 6.5 決策對齊（`phase6_5_pre_state`）

| gate `decision` | lead | requirement_profile | order |
|-----------------|------|---------------------|-------|
| **accept** | pre `draft` → next `qualified` · event `lead.qualified` | pre `draft` → next `active` · event `requirement_profile.created` | pre `draft` → next `draft` · event *null*（待 `order.placed`） |
| **defer** | pre `draft` → next `draft` · event `lead.created` | *null*（尚未物化） | *null* |
| **reject** | pre `draft` → next `archived` · event `lead.archived` | pre `draft` → next `closed` | pre `draft` → next `cancelled` · event `order.cancelled` |

**欄位映射（節錄）**：`intake.description` → `requirement_profile.summary`；`intake.tags` → `requirement_profile.constraints.tags`；`intake.source_channel` → `lead.source`；`intake.batch_size_hint` → `order.line_items[0].quantity`；`intake.suggested_pipeline` → `order.line_items[0].sku`。

---

## 7. 驗收

```text
cd <gov_core_system 根>
python -m unittest tests.test_intake_decider -v
```

預期：涵蓋 accept（factory／關鍵字／pipeline 錨點）、reject（空請求／越界 RAG／絕對路徑）、defer（模糊描述）、驗證失敗路徑。

---

## 8. 下一波（非 MVP）

- HTTP：`POST /api/intake/gate`（`app_api.py`）。
- 與 `02_Agents_Core/task_routing.py` 合併呼叫（accept 後自動 `route_task`）。
- `WORKFLOW_INDEX.md` §1.4 登錄本工作流。
- `shared/schemas/intake_gate_v1.json`（若需跨語言契約）。
