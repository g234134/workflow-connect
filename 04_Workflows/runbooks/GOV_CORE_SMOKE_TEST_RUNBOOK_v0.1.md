# GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1

本文件定義 Gov Core V1 的最小 Smoke Test 操作手冊。  
目標：驗證「Infra → Data → Governance」這條最小生命線在當前環境下是否可運作、可重跑、可回報。

---

## 0. 文件定位

- 位置：`04_Workflows/Runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md`
- 角色：Gov Core 最小生命線操作手冊。
- 對應標準：
  - `00_Agent_Work_Conditions.md` 中「Gov Core V1 最小 Smoke Test」條目。
- 對應戰報：
  - `00_Agent_Work_Progress.md` 中 `2026-05-17 — Gov Core V1 最小 Smoke Test`。
  - `04_Workflows/project_status/master_status.md` 中 `2026-05-17 — ingest_verify 里程碑（AGENTS.md）`。

---

## 1. 目的

本 runbook 用於驗證 Gov Core V1 的最小底盤是否正常：

1. Infra health 可用
2. Data pipeline 可 ingest 單一測試檔案
3. Governance orchestrator 可串起 `health → ingest → verify`
4. 結果可被記錄在 `master_status.md` 與 `00_Agent_Work_Progress.md`

---

## 2. 適用範圍

適用於：

- Gov Core V1 基本健康檢查
- Smoke test / 交接前基礎驗證
- 大幅修改前的底盤確認

不適用於：

- GraphRAG job 驗證
- Telegram / 外部 listener 驗證
- DarkOps 業務邏輯驗證

---

## 3. 前置條件

執行前應確認：

- 已讀：
  - `HARNESS_CONSTITUTION.md`
  - `ENGINEERING_CONTRACT.md`
  - `INSTANCE_ANCHOR_TANG.md`
  - `00_Agent_Work_Conditions.md`
  - `WORKFLOW_INDEX.md`
- Python 環境存在：
  - `01_Environments/python_venvs/gov_core_system/Scripts/python.exe`
- 服務就緒：
  - Postgres / Qdrant 可用
- `.env` 僅唯讀載入，不可修改
- 測試檔案可用：
  - 建議使用 `D:\大唐三省六部\AGENTS.md`

---

## 4. 執行入口

工作目錄建議：

- `01_Environments/python_venvs/gov_core_system`

主要入口：

- Infra：
  - `core/infra_health.py`
- Data：
  - `Departments/04_Infrastructure/agents/data_pipeline_agent.py`
- Governance：
  - `Departments/04_Infrastructure/agents/orchestrator_agent.py`

---

## 5. 操作步驟

### Step 0：必要時確認基礎設施

可選：

```powershell
docker compose -f Departments/04_Infrastructure/docker-compose.yml ps
```

若服務未啟動，可在不修改 `.env` 的前提下：

```powershell
docker compose -f Departments/04_Infrastructure/docker-compose.yml up -d
```

### Step 1：Infra health

```powershell
Scripts\python.exe core\infra_health.py
```

期望結果：

- `all_ok: true`
- `postgres.message = "pg_ok"`
- `qdrant.message = "qdrant_ok"`
- `verify.message = "verify_ok"`

### Step 2：Data ingest（單檔）

```powershell
Scripts\python.exe Departments\04_Infrastructure\agents\data_pipeline_agent.py "D:\大唐三省六部\AGENTS.md"
```

期望結果：

- `chunks > 0`
- `collection = "document_chunks"`
- `ingest.ok = true`
- `verify.ok = true`

### Step 3：Governance ingest_verify

```powershell
Scripts\python.exe Departments\04_Infrastructure\agents\orchestrator_agent.py ingest_verify "D:\大唐三省六部\AGENTS.md"
```

期望結果：

- `ok = true`
- `mode = "ingest_verify"`
- `health.all_ok = true`
- `ingest.ok = true`
- `verify.ok = true`
- `master_status.ok = true`

---

## 6. 驗收標準

判定為 Pass 時，至少應滿足：

- Infra health 通過
- 單檔 ingest 有 chunk
- orchestrator ingest_verify 通過
- `master_status.md` 新增對應區塊或確認寫入成功
- 終端輸出中有結構化結果與 `RUNTIME_METRIC`

---

## 7. 已知限制

- `verify_batch()` 目前主要驗的是 Phase1 種子不變量，不等於逐檔驗證本輪 ingest 檔案內容。
- 重複對同一個檔案 ingest，可能產生多個 run 或向量條目。
- 單檔情境下 `master_status` 某些計數欄位可能顯示不完整。

---

## 8. 禁區與停工條件

遇到以下情況需停工 + 留痕：

- 需要修改 `.env`
- 需要碰 `runtime/checkpoints/**`
- 需要啟動 DarkOps
- 需要執行 GraphRAG job
- 需要大規模新增測試語料

停工後應於 Progress / notes 中記錄：

- 卡在哪裡
- 已確認的事實
- 建議下一步

---

## 9. 輸出與回報

完成後應至少留下：

- 命令清單
- 結構化結果摘要
- 是否 Pass / Partial / Fail
- 若成功：
  - `master_status.md` 證據
  - `00_Agent_Work_Progress.md` 對應戰報

---

## 10. 更新規則

需更新本 runbook 的情況：

- 主要入口改名或移動
- ingest / verify / orchestrator 流程改動
- Conditions 中的 Gov Core smoke 標準變更
- 新版 workflow 取代本流程

若僅補充說明，可升 `v0.1.1`；若流程本身變動，應升 `v0.2`。
