# RAG_SMOKE_TEST_RUNBOOK_v0.1

本文件定義 Gov Core V1 的基礎 RAG Smoke Test 操作手冊。  
目標：驗證 `document_chunks` 上的基礎 RAG 查詢能力是否可用，並確認 answer 模式可回傳 grounded 結果。

---

## 0. 文件定位

- 位置：`04_Workflows/Runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md`
- 角色：Gov Core 基礎 RAG 查詢操作手冊。
- 對應標準：
  - `00_Agent_Work_Conditions.md` 中「Gov Core V1 — RAG Smoke Test 標準（v0.1）」條目。
- 對應戰報：
  - `00_Agent_Work_Progress.md` 中 `2026-05-17 — RAG_Smoke_Test（Gov Core V1）`。

---

## 1. 目的

本 runbook 用於驗證：

1. `document_chunks` collection 中已有可檢索內容
2. RAG backend 能對已 ingest 的 AGENTS.md 做檢索
3. answer 模式能產生 grounded 回覆
4. retrieve-only 模式能提供 hits 與 cross-check 證據

---

## 2. 適用範圍

適用於：

- RAG 主線最小 smoke test
- RAG backend 基本健康確認
- answer / retrieve 入口可用性驗證

不適用於：

- GraphRAG job
- DarkOps 任務
- Telegram / listener / API server 整合驗證

---

## 3. 前置條件

執行前應確認：

- 已讀：
  - `HARNESS_CONSTITUTION.md`
  - `ENGINEERING_CONTRACT.md`
  - `INSTANCE_ANCHOR_TANG.md`
  - `00_Agent_Work_Conditions.md`
  - `WORKFLOW_INDEX.md`
- Gov Core V1 最小 Smoke Test 已至少有一次成功紀錄
- `AGENTS.md` 已被 ingest 至 `document_chunks`
- Python 環境存在：
  - `01_Environments/python_venvs/gov_core_system/Scripts/python.exe`
- `.env` 僅唯讀載入，不可修改

---

## 4. 執行入口

工作目錄建議：

- `01_Environments/python_venvs/gov_core_system`

主要入口：

- `core/rag_backend.py`
- `Departments/04_Infrastructure/agents/rag_query_agent.py`

建議主入口：

- answer 模式：
  - `rag_query_agent.py answer`
- retrieve-only 模式：
  - `rag_query_agent.py`（無 `answer` 子命令）

不建議主入口：

- `orchestrator_agent.py query`
  - 目前仍接到 skeleton 路徑，不應作為正式 RAG smoke 入口

---

## 5. 操作步驟

### Step 0：必要時先做 Infra health

```powershell
Scripts\python.exe core\infra_health.py
```

期望結果：

- `all_ok = true`
- `pg_ok`
- `qdrant_ok`
- `verify_ok`

### Step 1：answer 全鏈查詢

```powershell
Scripts\python.exe Departments\04_Infrastructure\agents\rag_query_agent.py answer --top-k 3 "這個系統裡有哪些 Agent 和角色？"
```

期望結果：

- `ok = true`
- `len(sources) >= 1`
- 至少一筆 `sources[].doc_key` 指向 AGENTS ingest
- 有 `answer`
- 有 `RUNTIME_METRIC.duration_ms`

### Step 2：retrieve-only 查詢（可選但建議）

```powershell
Scripts\python.exe Departments\04_Infrastructure\agents\rag_query_agent.py --top-k 3 "AGENTS.md 的開戰與封箱指令各是什麼？"
```

期望結果：

- `ok = true`
- `len(hits) >= 1`
- `cross_check_ok = true`（若有此欄位）
- `hits[0].payload` 或 `documents_lookup` 可證明命中 AGENTS.md

---

## 6. 驗收標準

判定為 Pass 時，至少應滿足：

- answer 模式：
  - `ok = true`
  - `len(sources) >= 1`
  - 至少一筆 source 指向 AGENTS ingest
- retrieve-only 模式（若執行）：
  - `len(hits) >= 1`
  - hits / documents_lookup 可對應 AGENTS.md
- 有 `RUNTIME_METRIC`
- 未違反憲法與合約禁區

---

## 7. 已知限制

- `orchestrator_agent.py query` 目前不應作為正式入口。
- LLM 回覆品質可能不完整，但只要 grounded 且結構合理，仍可視為 smoke pass。
- 本 runbook 驗的是「RAG 主線活著」，不是高品質 eval 或全面問答能力。

---

## 8. 禁區與停工條件

遇到以下情況需停工 + 留痕：

- 需要修改 `.env`
- 需要啟動 DarkOps
- 需要跑 GraphRAG job
- 需要大幅改動 RAG backend 才能讓 smoke 勉強通過
- 需要碰 `runtime/checkpoints/**`

停工後應記錄：

- 問題點
- 已確認的入口與現況
- 建議下一步（例如修正入口、補 runbook、設計新 smoke）

---

## 9. 輸出與回報

完成後應至少留下：

- 實際 query 文本
- answer 模式結果摘要
- retrieve-only 模式結果摘要（若有）
- 是否 Pass / Partial / Fail
- 相關 `RUNTIME_METRIC`
- 對應 Progress 戰報條目

---

## 10. 更新規則

需更新本 runbook 的情況：

- RAG 主入口變更
- collection / 檢索策略調整
- `orchestrator query` 被正式修通並取代現入口
- Conditions 中的 RAG smoke 標準變更

若僅補充說明，可升 `v0.1.1`；若流程本身變動，應升 `v0.2`。
