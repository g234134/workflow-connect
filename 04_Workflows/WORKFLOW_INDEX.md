# WORKFLOW_INDEX — Workflow & Smoke Test Map（v0.1）

本文件是 Gov Core / HQ 的「工作流地圖首頁」。
目標：讓人類與 Agent 進場時，能先知道有哪些主要工作流、對應的 runbook 與 smoke test 戰史。

---

## 0. 文件定位

- 位置：`04_Workflows/WORKFLOW_INDEX.md`
- 角色：工作流與 smoke test 索引首頁。
- 關係：
  - 結構層：`HARNESS_CONSTITUTION.md`（國家架構與禁區）
  - 行為層：`ENGINEERING_CONTRACT.md`（四大流派與 12-rule）
  - 實例層：`INSTANCE_ANCHOR_TANG.md`（路徑、runner、禁區清單）
  - 操作層：各 workflow runbook + smoke test 戰報（本文件即為入口）

---

## 1. 已定義的核心工作流（v0.1）

### 1.1 Gov Core V1 最小 Smoke Test（Infra → Data → Governance）

- Runbook（TODO）：
  - 建議檔名：`04_Workflows/Runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md`
- 簡述：
  - 驗證「Gov Core V1 底盤是否活著」：
    - Infra health → 單檔 ingest（AGENTS.md）→ Governance ingest_verify → master_status。
- 主要入口與檔案：
  - `core/infra_health.py`
  - `core/data_pipeline.py`
  - `core/orchestrator.py`
  - `Departments/04_Infrastructure/agents/data_pipeline_agent.py`
  - `Departments/04_Infrastructure/agents/orchestrator_agent.py`
- Smoke Test 標準：
  - 見：`00_Agent_Work_Conditions.md` 中「Gov Core V1 最小 Smoke Test」條目。
- 最近一次通過紀錄：
  - 見：`00_Agent_Work_Progress.md` 中 `2026-05-17 — Gov Core V1 最小 Smoke Test` 條目。
  - 另有：`04_Workflows/project_status/master_status.md` 之 `## 2026-05-17 — ingest_verify 里程碑（AGENTS.md）`。

---

### 1.2 RAG_Smoke_Test（Gov Core V1 / document_chunks / AGENTS.md）

- Runbook（TODO）：
  - 建議檔名：`04_Workflows/Runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md`
- 簡述：
  - 在 `AGENTS.md` 已被 ingest 至 `document_chunks` 的前提下，驗證：
    - 能對該 collection 發出 RAG 查詢；
    - 能檢索到至少一筆 AGENTS 相關 chunk；
    - answer 模式可以產出 grounded 回覆。
- 主要入口與檔案：
  - `core/rag_backend.py`
  - `Departments/04_Infrastructure/agents/rag_query_agent.py`
- Smoke Test 標準：
  - 見：`00_Agent_Work_Conditions.md` 中「Gov Core V1 — RAG Smoke Test 標準（v0.1）」條目。
- 最近一次通過紀錄：
  - 見：`00_Agent_Work_Progress.md` 中 `2026-05-17 — RAG_Smoke_Test（Gov Core V1）` 條目。

---

### 1.3 Phase 5 Probe — `task_runs` / `seed_pg` 鎖排查與 shortest-path 驗收

- Runbook：
  - `01_Environments/python_venvs/gov_core_system/Departments/05_Data_Vault/README.md`
- 簡述：
  - `05_Data_Vault/README.md`：Phase 5 probe、`task_runs` / `seed_pg` 鎖排查與 shortest-path 驗收 Runbook。
- 主要入口與檔案：
  - `Departments/05_Data_Vault/phase5_live_pg_soak.py`（`--probe`；工作目錄：`gov_core_system` 根；API `http://127.0.0.1:8000`）
  - `output/phase5_probe_report.json`（probe 報告）
- 觸發時機：
  - probe 卡在 `seed_pg`；PG `lock wait` / `idle in transaction` 涉及 `task_runs`；或 `failed_stage` 為 `seed_pg_from_asks` / `monitoring`。
- 驗收標準：
  - 終端 JSON：`ok: true`、`report_kind: probe_complete`、`failed_stage: null`、`message: probe shortest path ok`（細節見 README §4–§5）。

---

### 1.4 Phase 8.6 — Minimal Intake Browser Bridge（6.5 + 7.5 + 8.5 + 8.6 / 8.6a）

- **Flow key**：`minimal_intake_browser`（與 `run_minimal_orchestration_bridge()` 回應欄位 `flow` 一致）
- Runbook：
  - `04_Workflows/PHASE8_6_MINIMAL_ORCHESTRATION_BRIDGE_MVP_v0.1.md`
  - `04_Workflows/PHASE8_6A_MINIMAL_BRIDGE_API_ENDPOINT_MVP_v0.1.md`（HTTP：`POST /api/orchestration/bridge`）
- 簡述：
  - Minimal orchestration：intake（Phase 7.5）→ `phase6_5_pre_state`（Phase 6.5）→ optional DOM browser plan（Phase 8.5）；對外 **`POST /api/orchestration/bridge`** 轉交 `run_minimal_orchestration_bridge()`，回傳結構化 bridge `dict`（`schema_version: orchestration_bridge_v1`）。
- 主要入口與檔案：
  - `01_Environments/python_venvs/gov_core_system/core/minimal_orchestration_bridge.py`（`run_minimal_orchestration_bridge()`）
  - `01_Environments/python_venvs/gov_core_system/app_api.py`（`POST /api/orchestration/bridge`；本輪索引僅登錄，不改實作）
  - `01_Environments/python_venvs/gov_core_system/core/intake_decider.py`（Phase 7.5 `parse_and_decide`）
  - `01_Environments/python_venvs/gov_core_system/core/browser_runner.py`（Phase 8.5 `validate_plan` / `run_plan`）
  - `01_Environments/python_venvs/gov_core_system/shared/schemas/orchestration_bridge_v1.json`
- Smoke Test / 驗收（見上述 Runbook §驗收；工作目錄：`gov_core_system` 根）：
  - `python -m unittest tests.test_minimal_orchestration_bridge -v`
  - `python -m unittest tests.test_app_api_orchestration_bridge -v`
  - 建議回歸：`python -m unittest tests.test_intake_decider tests.test_browser_runner -v`
- 最近一次通過紀錄：
  - **TODO**：待於 `00_Agent_Work_Progress.md` 追加 Phase 8.6i 索引登錄戰報與通過證據。

---

## 2. 預留工作流（尚未正式定義 runbook）

以下工作流尚未有正式 runbook，僅作為未來規劃列出：

### 2.1 GraphRAG Job Smoke Test（預留）

- 目標（草案）：
  - 驗證 GraphRAG job 能對一小批文件建圖、完成任務、輸出基礎圖統計，並支援一個最小的圖上 query。
- 狀態：
  - **TODO**：待完成 RAG_Smoke_Test v0.1 穩定後，另立 runbook 與 smoke 戰報。

### 2.2 DarkOps Minimal Task Smoke Test（預留）

- 目標（草案）：
  - 在有限解禁的前提下，為暗部設計一個極小的、風險可控的任務驗證流程。
- 狀態：
  - **Blocked**：目前依憲法，DarkOps 為 Blocked；待尚書省明確解禁與 runbook 設計後再啟用。

---

## 3. 如何使用這份索引（給 Agent / 人類）

1. 若你要操作或修改任何 Gov Core / RAG / GraphRAG / DarkOps 工作流：
   - 先讀：
     - `HARNESS_CONSTITUTION.md`
     - `ENGINEERING_CONTRACT.md`
     - `DEPARTMENT_MAP.md`
     - `INSTANCE_ANCHOR_TANG.md`
     - `00_Agent_Work_Conditions.md`
     - 本檔 `WORKFLOW_INDEX.md`
2. 再依本檔所列，找到對應的 runbook：
   - 例如：Gov Core V1 → GOV_CORE_SMOKE_TEST_RUNBOOK…（完成後）
   - RAG → RAG_SMOKE_TEST_RUNBOOK…（完成後）
   - Phase 5 probe／`task_runs` 鎖 → `05_Data_Vault/README.md`（§1.3）
3. 如需了解最近一次實際執行狀態與細節：
   - 查 `00_Agent_Work_Progress.md` 中相對應日期條目。
   - 必要時查 `04_Workflows/project_status/master_status.md`。

---

## 4. 更新規則（v0.1）

- 當以下任一情況發生時，需更新本索引：
  - 新增一條正式 runbook。
  - 既有工作流的主要入口 / 路徑 / 命名發生變更。
  - 某條 smoke test 被宣告 deprecated 或被新版本取代。
- 更新流程建議：
  - 先在 `00_Agent_Work_Progress.md` 中記錄變更背景。
  - 再同步更新：
    - 本檔 `WORKFLOW_INDEX.md`
    - 對應 runbook
    - `00_Agent_Work_Conditions.md`（如涉及驗收標準）
- 版本命名：
  - 索引本身以 `v0.x` 管理；runbook 以各自版本管理（如 `GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1`）。
