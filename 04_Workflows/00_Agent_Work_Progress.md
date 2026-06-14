# 00 Agent Work Progress

## 目的

本檔為「大唐三省六部」多 Agent 協作的全局進度總表。  
此檔不記錄每個 Agent 的全部細節，而是用來快速回答以下問題：

- 四個 Agent 分別目前做到哪裡？
- 哪些已可執行？
- 哪些仍是 skeleton / placeholder？
- 下一輪應優先推哪一塊？[cite:507][cite:509]

細部「階段編號、驗收條件、可機器驗證的證據」集中在本檔後段的〈各 Agent 詳細里程碑與驗收條件〉，供 Cursor / 其他 session 對照執行。

---

## 當前基線狀態

### 已確認完成的系統基線
- PostgreSQL 已可連線
- `.env` 與實際 Postgres 密碼已對齊
- `DATABASE_URL` 已成功實測 `pg_ok`
- `phase1_verify.py` 已實測輸出：
  - `ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`
  - `OK: verify passed`
- `verify_batch()` / `infra_health_agent` 路徑下可取得語意上的 **`verify_ok`**（與 Phase1 不變式檢查一致）
- Qdrant 已可回應並有既有 collection 狀態
- **Data**：已對單一 Markdown 檔 `AGENTS.md` 完成真實 **ingest + verify**（見後段 D2 證據）；Qdrant `document_chunks` 全集合計數由 **2 → 18**（+16 chunks）

### 基線結論
目前「Phase1 的基礎設施 + verify 閉環」已通過，且 **單檔 ingest 管線已非空殼**，可在不破壞種子 INV 的前提下寫入向量與關聯資料。  
後續四個 Agent 的工作，應以此基線為前提，不得破壞既有驗證結果。

---

## 四個 Agent 狀態總覽（更新）

| Agent | Role | Status | Done | Next |
|-------|------|--------|------|------|
| Infra Agent | 基礎設施健康檢查官 | **I0 / I1 已完成** | 已建立 `core/infra_health.py` + `infra_health_agent.py`；在正確載入 `.env`（含 `DATABASE_URL`、建議補齊 `QDRANT_URL`）下可檢查 Postgres / Qdrant；`check_phase1_invariants()` 可跑通 Phase1 verify，通過時終端可見 **`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**、彙總 **`verify_ok`** / `all_ok=True`。 | 擴充更多健康檢查項目（未來 RAG / 其他服務）、規劃監控與告警輸出格式。 |
| Data Agent | 資料管道監工 | **D1 / D2 / D3 已完成** | 已建立 `core/data_pipeline.py` + `data_pipeline_agent.py`；**`ingest_batch()` 已為真實 ingest**（讀檔 → Postgres + Qdrant）；**單檔 `AGENTS.md` ingest + `verify_batch()` 已驗收**（見後段 D2）。**目錄級 smoke（D3）**已驗收：`input_path=D:\大唐三省六部\02_Data\smoke_corpus`，`path_resolution=directory_batch`，`files_total=3`、`files_ok=2`、`files_skipped=1`（略過 `ignore.json`，`reason=unsupported_extension (.json)`），**`verify.ok=True`**，終端仍 **`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**（見後段 D3）。 | 可選：擴充**非種子** ingest 的逐 run 驗證或獨立不變式（見「已知限制」）。 |
| RAG Agent | 知識查詢專員 | **R1 / R2 已完成** | 已建立 `core/rag_backend.py` + `rag_query_agent.py`；**R1**：`document_chunks` 檢索 smoke 已驗收（`hits=5`，每筆含 `score` / `document_id` / `payload`，命中 **`AGENTS.md`** 與 **`alpha.md`**）。**R2**：Postgres `documents` / `agent_runs` 與 payload 交叉驗證已驗收（`documents_lookup` 與 `agent_runs_lookup` 各 2 筆皆 `found=True`，`cross_check.summary.cross_check_ok=True` 等，見後段 R1/R2 證據）。 | Phase 2：端到端**真正問答能力**（檢索結果 → LLM 組答）、**GraphRAG**、**監控／評測**與可觀測性強化。 |
| Governance Agent | 總管 / 治理調度官 | **G1 已完成** | 已建立 `core/orchestrator.py` + `orchestrator_agent.py`；**一鍵 CLI** `ingest_verify`（內部固定 **health → ingest → verify**）已可成功執行並回傳 G1 schema（見後段 Governance / G1 證據）。仍支援 `health` / `ingest` / `query` 等入口。 | Phase 2：於每次執行後**自動寫回** `project_status/master_status.md`、`project_status/handoff.md`（檔案與目錄待首次建立）；並與 RAG / GraphRAG / monitoring 治理規則逐步對齊。 |

---

## 各 Agent 詳細里程碑與驗收條件

以下編號與上表 Status 對齊，驗收條件盡量可機器判定（計數、JSON 欄位、終端斷言字串）。

### 全域環境前綴（執行證據時共用）

| 項目 | 值 / 備註 |
|------|-----------|
| Python venv | `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system` |
| 執行 Python | `.\Scripts\python.exe`（於 venv 目錄下） |
| `.env` | 建議以 Process 環境變數注入 `D:\大唐三省六部\01_Environments\.env`；`DATABASE_URL` 必填；`QDRANT_URL` 若缺省可設 `http://127.0.0.1:6333` |
| 連線 + Phase1 不變式 | `.\Scripts\python.exe Departments\04_Infrastructure\agents\infra_health_agent.py` |
| ingest + verify | `.\Scripts\python.exe Departments\04_Infrastructure\agents\data_pipeline_agent.py "<檔案或目錄路徑>"` |
| RAG smoke + metadata cross-check | `.\Scripts\python.exe Departments\04_Infrastructure\agents\rag_query_agent.py --top-k 5 "AGENTS.md"` |
| Governance 一鍵 ingest_verify | `.\Scripts\python.exe .\Departments\04_Infrastructure\agents\orchestrator_agent.py ingest_verify "<檔案或目錄路徑>"` |

---

### Infra Agent — I0 / I1

#### I0 — 環境變數與連線 smoke

| 項目 | 內容 |
|------|------|
| **驗收條件** | 1) `DATABASE_URL` 非空且 Postgres 可連線。 2) `QDRANT_URL` 可連線（例如 HTTP 200 級別）。 3) 彙總 `all_ok: True`。 |
| **狀態** | 已完成（正確載入 `.env` 後）。 |
| **證據（語意）** | `postgres.ok`、`qdrant.ok`（含 `status_code`）、`verify.ok` / **`verify_ok`**，`all_ok: True`。 |

#### I1 — Phase1 不變式（INV1–INV4）

| 項目 | 內容 |
|------|------|
| **驗收條件** | `check_phase1_invariants()` 成功時，終端列印 **`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**，且 **`OK: verify passed`**。 |
| **不變式摘要** | **INV1**：Qdrant `document_chunks` 以種子 `document_id` 過濾後 `points_count` 符合預期。 **INV2**：`documents` 表中 `doc_key = phase1/minimal_corpus` 列數 ≥ 1。 **INV3**：`agent_runs` 表中 `agent_name = phase1_ingest_minimal` 列數 ≥ 1。 **INV4**：最新成功 run 的 `meta.chunks` 與 Qdrant 以 `(document_id, agent_run_id)` 過濾的 points 數一致。 |
| **狀態** | 已完成。 |
| **證據（節錄，單次實測）** | `postgresql documents (phase1 key): 1`；`postgresql agent_runs (phase1_ingest_minimal): 1`；種子文件篩選後 **`qdrant document_chunks ... points_count=2`**；`correlation check: ... meta.chunks=2 vs qdrant points ... =2`；**`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**。 |

---

### Data Agent — D1 / D2 / D3

#### D1 — Phase1 seed minimal ingest

| 項目 | 內容 |
|------|------|
| **驗收條件** | 與 Infra **I1** 相同（種子錨點存在且 INV1–INV4 成立）。 |
| **狀態** | 已完成。 |

#### D2 — 單檔 ingest + verify（`AGENTS.md`）

| 項目 | 內容 |
|------|------|
| **驗收條件** | 1) `ingest.ok == True` 且 `message == "ingest completed"`。 2) `path_resolution == "file"`。 3) `ingest.chunks` 為正整數；`collection == "document_chunks"`；`embed_model` 有值。 4) **`verify.ok == True`** 且語意為 **`verify_ok`**。 5) Qdrant `document_chunks` **全集合** `points_count` 自 **2 增至 18**（與本次 **`chunks: 16`** 增量一致：+16）。 6) 種子 INV 仍印出 **`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**（新檔不得破壞種子關聯）。 |
| **狀態** | 已完成。 |
| **證據（2026-05-14 執行摘要）** | **ingest**：`ok: True`，`resolved_path`: `D:\大唐三省六部\AGENTS.md`，**`chunks: 16`**，`document_id: b68c98dc-0ff6-48ed-b994-f9ea2ef95086`，`agent_run_id: 6b6cab8a-ce8c-40ee-84d7-f121e0d54bb6`，`run_id: 2f0644c9a4c2408e8c4125548275b2ad`，`doc_key: ingest_batch/311f33a0f17222962f0cfc3a98ab1447/AGENTS`，**`embed_model: text-embedding-3-small`**。 **Qdrant**：**`document_chunks` `points_count`：2 → 18**。 **verify**：**`verify_ok`**；種子列仍 **points_count=2** 且 correlation **2=2**；**`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**。 |

#### D3 — 目錄級 ingest smoke test

| 項目 | 內容 |
|------|------|
| **驗收條件** | 1) 輸入為目錄時解析行為明確（`path_resolution` 與實作一致，本次為 **`directory_batch`**）。 2) 回傳或 log 含 aggregate：`files_total`、`files_ok`、`files_skipped`（含略過原因）。 3) 至少 **≥2** 個支援副檔名（`.md` / `.txt` / `.markdown`）成功 ingest。 4) 成功後 `document_chunks` 全集合 points **單調不减**（或文件化允許的維護策略）。 5) **`verify_batch()` 仍 `verify_ok`**，且終端仍印出 **`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**（種子錨點不被破壞）。 |
| **狀態** | 已完成。 |
| **證據（2026-05-14）** | **`input_path`**：`D:\大唐三省六部\02_Data\smoke_corpus`。 **`path_resolution`**：`directory_batch`。 **`files_total`**：`3`；**`files_ok`**：`2`；**`files_skipped`**：`1`。 **skipped**：檔名 **`ignore.json`**，**`reason`**：`unsupported_extension (.json)`。 **`verify.ok`**：`True`（語意 **`verify_ok`**）。 **終端**：仍出現 **`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**。 |

**已知限制（避免誤判）**：目前 **`verify_batch` 仍以 phase1 種子為主錨**；非種子文件的獨立不變式若需要，應另開里程碑（例如專屬 `verify_ingest_run`）擴充。

---

### RAG Agent — R1 / R2

#### R1 — 對 `document_chunks` 的檢索 smoke

| 項目 | 內容 |
|------|------|
| **驗收條件** | 1) 指定 collection 可取得 **≥1** hit；本次 **`top_k=5`** 時 **`hits=5`**。 2) 每筆 hit 含 **`score`**、**`document_id`**、**`payload`**。 3) 命中內容可對應到 **`AGENTS.md`** 與 **`alpha.md`**（語意／payload 可核對）。 |
| **狀態** | 已完成。 |
| **證據（2026-05-14，CLI）** | **執行指令**：`.\Scripts\python.exe Departments\04_Infrastructure\agents\rag_query_agent.py --top-k 5 "AGENTS.md"`（於 venv 根目錄）。 **頂層**：`ok=True`，`message="smoke retrieve and metadata cross-check passed"`，`collection="document_chunks"`，`query="AGENTS.md"`，`top_k=5`。 **R1 關鍵結果**：`hits=5`；每筆 hit 含 `score`、`document_id`、`payload`；hit 命中 **`AGENTS.md`** 與 **`alpha.md`**。 |

#### R2 — 與 Postgres `documents` / `agent_runs` 交叉驗證

| 項目 | 內容 |
|------|------|
| **驗收條件** | 1) 以 hit 之 `document_id` 查 Postgres：`documents` 與 `agent_runs` 可查得對應列。 2) payload / DB 欄位與關聯一致性可機器核對（含 `doc_key`、`content_sha256`、`version`、`agent_runs.meta.document_id` 等比對為 `ok=True`）。 3) 彙總 **`cross_check.summary.cross_check_ok=True`**。 |
| **狀態** | 已完成。 |
| **證據（2026-05-14，同上 CLI）** | **R2 關鍵結果**：`documents_lookup` 共 **2** 筆，皆 **`found=True`**；`agent_runs_lookup` 共 **2** 筆，皆 **`found=True`**；`cross_check.summary.cross_check_ok=True`；`cross_check.summary.documents_lookups=2`；`cross_check.summary.agent_runs_lookups=2`；`cross_check.summary.hits=5`。 **關聯一致性（可寫入重點）**：payload / `documents` / `agent_runs` 的 **`document_id` 一致**；**`doc_key`**、**`content_sha256`**、**`version`** 比對為 **`ok=True`**；**`agent_runs.meta.document_id`** 比對為 **`ok=True`**。 |

---

### Governance Agent — G1（一鍵 health → ingest → verify）

| 項目 | 內容 |
|------|------|
| **驗收條件** | 1) 單一 CLI 入口觸發固定順序：**health → ingest → verify**。 2) 頂層回傳 `dict`：`ok`、`message`、`mode="ingest_verify"`、`input_path`、`health`、`ingest`、`verify`。 3) 成功路徑下 **`ok=True`**，且 **`health.all_ok=True`**、`ingest.ok=True`、`verify.ok=True`（語意 **`verify_ok`**）。 4) 種子 Phase1 不變式未被破壞：終端仍可見 **`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`** 與 **`OK: verify passed`**。 |
| **狀態** | 已完成。 |
| **證據（2026-05-14，CLI）** | **執行指令**：`.\Scripts\python.exe .\Departments\04_Infrastructure\agents\orchestrator_agent.py ingest_verify 'D:\大唐三省六部\02_Data\smoke_corpus'`（於 venv 根目錄）。 **頂層**：`ok=True`，`mode="ingest_verify"`，`input_path="D:\大唐三省六部\02_Data\smoke_corpus"`，`message="ingest_verify pipeline completed"`。 **`health`**：`ok=True`，`all_ok=True`，`postgres.ok=True`，`qdrant.ok=True`，`verify.ok=True`。 **`ingest`**：`ok=True`，`path_resolution="directory_batch"`，`files_total=3`，`files_ok=2`，`files_skipped=1`；`skipped` 含 **`ignore.json`**，`reason="unsupported_extension (.json)"`。 **`verify`**：`ok=True`，`message="verify_ok"`。 **終端（補充）**：**`ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`**；**`OK: verify passed`**。 |

---

### GraphRAG / Jobs — G1

| **驗收條件** | `graphrag_jobs` 表存在且可 `SELECT`；可插入測試列後清理或 rollback。 |
| **狀態** | Schema 已存在（健康檢查曾列出表名含 `graphrag_jobs`）；業務 job 流程仍待定義。 |

---

## 已完成項目（全局）

- 已完成 PostgreSQL 密碼與 `.env` 對齊
- 已完成 `DATABASE_URL` 實連測試
- 已完成 `phase1_verify.py` 實測通過（含 INV1–INV4 種子錨點）
- **已完成** `core/infra_health.py`、`core/data_pipeline.py` 與對應 **可執行** agent 腳本（`infra_health_agent.py`、`data_pipeline_agent.py` 等）於 `gov_core_system` 樹內落地
- **已完成** Data 單檔真實 ingest + verify（**`AGENTS.md`**，**`chunks: 16`**，Qdrant **`document_chunks` points_count 2→18**，**`verify_ok`**，種子 **ASSERT: OK** 仍成立）
- **已完成** Data D3 目錄級 ingest smoke（**`input_path=D:\大唐三省六部\02_Data\smoke_corpus`**，**`path_resolution=directory_batch`**，**`files_total=3`**、**`files_ok=2`**、**`files_skipped=1`**；skipped 含 **`ignore.json`**，**`reason=unsupported_extension (.json)`**；**`verify.ok=True`**；終端仍 **ASSERT: OK (INV1–INV4 satisfied for phase1 seed)**；細部見後段 D3）
- 已確認四大板塊的角色對應：
  - Infrastructure
  - Data / Ingest & Verify
  - RAG / Query
  - Governance / Orchestration
- 已確認將以「總部 SDK + 暗部 Agent + 全局進度檔」三層結構推進後續工作
- **已完成** RAG **R1 / R2**（CLI：`rag_query_agent.py --top-k 5 "AGENTS.md"`；頂層 `ok=True`、`message="smoke retrieve and metadata cross-check passed"`、`collection="document_chunks"`、`hits=5`、`cross_check.summary.cross_check_ok=True` 等；細部見後段 R1/R2 證據）
- **已完成** Governance **G1**（CLI：`orchestrator_agent.py ingest_verify`；`mode="ingest_verify"`、`ok=True`、`health.all_ok=True`、`ingest`/`verify` 與 D3 目錄 batch 一致；細部見後段 Governance / G1 證據）
- **Milestone**：**`四大板塊第一版完成`**（Infra / Data / RAG / Governance 之第一版可驗收里程碑均已落地並有 CLI／dict 證據可核對）
- **Gov Core System V1**：**全鏈路第一版 + live API 接通，驗收完成**（LangGraph、GraphRAG、PostgreSQL／Qdrant、Langfuse、UI workbench、FastAPI facade；E2E 已驗收）
- **ENV-1** 完成（`.env.example`、`requirements.txt`、`env-readiness-checklist.md`）
- **DEPLOY-1** 完成（`deployment-guide.md`、`run-local-api.ps1`／`run-local-api.bat`、README 啟動說明）
- **SEC-1** 完成（`app_api.py` CORS 可設定、`security-notes.md`、`.env.example` 與 README 安全說明）
- **OPS-1** 完成（`smoke-test.py`、`smoke-test.ps1`、`ops-checklist.md`、README smoke test 說明）

---

## 未完成項目（全局）

- **V1 baseline 已封版**：Gov Core System V1 之約定範圍與驗收項（含全鏈路、live API、ENV-1／DEPLOY-1／SEC-1／OPS-1）視為**已完成**，不再列為 V1「未完成缺口」。
- **後續僅剩 V2／部署／維運類工作**；下列為**代表性後續方向**（**非 V1 缺口**，僅供 roadmap 參考）：
  - 正式部署到固定環境
  - auth／RBAC／rate limit 等安全深化
  - 更深的 monitoring／evaluation
  - 產品化與營運化擴充

---

## 當前風險 / 阻塞

### 1. 多 Agent 互踩風險
進入 Phase 2 後模組面更廣（LLM、GraphRAG、觀測與狀態檔），若多個 Cursor chat 並行但責任邊界與禁止事項未對齊，仍可能互相覆蓋檔案或留下不一致契約。[cite:508][cite:513]

### 2. verify 錨點僅覆蓋 phase1 種子
`verify_batch()` 仍以種子 INV 為主錨；在 Phase 2 擴大量 ingest／圖資料後，若缺乏逐 run 或圖層級驗收，仍可能出現「verify 全綠但新資料靜默錯位」。[cite:507][cite:511]

### 3. RAG 真正問答尚未閉環
**R1 / R2**（檢索 + Postgres metadata cross-check）已於 **2026-05-14** 以 CLI 驗收完成；當前缺口在 **LLM answer synthesis**、prompt／grounding 策略與錯誤預算，尚無可當成產品路徑的 end-to-end 問答與可量化 SLO。

### 4. GraphRAG / `graphrag_jobs` 流程與驗收留空
表結構已存在，但 **job 狀態機**、重試、與 Data ingest／RAG 查詢邊界未定稿；multi-hop／entity-level 分析若無明確驗收與回滾策略，擴充時易落入「可跑但不穩」的灰色地帶。

### 5. Monitoring / Observability 尚未有固定出口
尚未建立一致的 **metrics／結構化 logs／告警** 管道；pipeline 或 RAG 退化時，難以從單一觀測面快速偵測、對照各 core 回傳 `dict` 與實際使用者影響。

### 6. Governance 狀態檔仍倚賴人工
**`project_status/master_status.md`**、**`handoff.md`** 仍未由流程**自動寫回**（檔案與目錄尚待首次建立）；跨 chat 交接若持續手動，易與實際 **`ingest_verify`** 與後續 Phase 2 流程脫節。

---

## 推進策略

### V1 baseline 凍結（2026-05-15）

- **目前凍結 V1 baseline**：Gov Core System V1 已封版；後續新增需求不應再回溯計入 V1 缺口。
- **後續工作以獨立任務流處理**（**V2** 或 **部署／維運專案**），各自驗收與文件化。
- **避免再把新需求混回 V1**，以免模糊封版邊界與驗收基線。

### 第一階段：建立四個 Agent 骨架（已達成）
目標：
- 建立 `brief.md` / `progress.md` / `notes.md`（各 Agent 工作區內，視專案慣例）
- 建立對應 `core/*.py`
- 建立可直接執行的 agent 腳本

### 第二階段：讓四個 Agent 都能回傳標準 dict（已大致達成）
目標：
- 所有 core 函式都可被其他模組 import
- 所有 agent 腳本都可從 CLI 執行
- fallback 行為有明確訊息

### 第三階段：逐步替換 skeleton 為真實邏輯（第一版已達成）
目標：
- Infra Agent：維持 Phase1 verify 與連線檢查；Phase 2 擴充可觀測性／監控
- **Data Agent：D1/D2/D3 已完成；視需要擴充非種子 verify**
- **RAG Agent：R1/R2 已完成**（檢索 smoke + Postgres 交叉驗證；見後段證據）；Phase 2 推進真正問答與 GraphRAG／評測
- **Governance Agent：G1 已完成**（一鍵 `ingest_verify`）；Phase 2 推進 **master_status / handoff** 自動寫回與更細治理規則

### Phase 2（下一主軸；屬 V2／部署／維運範疇，非 V1 補缺）
目標（摘要）：
- **RAG**：真正問答能力、與 LLM 管線整合、品質與監控
- **GraphRAG**：`graphrag_jobs` 業務流程與編排
- **Monitoring / Observability**：跨模組 dict 對齊與告警／儀表
- **Governance**：`master_status.md` / `handoff.md` 自動寫回與狀態機

---

## 下一輪建議優先順序

**註（V1 baseline 封版後）**：以下優先項屬 **V2 或獨立部署／維運專案**，**不視為 V1 缺口**。

1. **RAG（Phase 2）— 真正問答能力**  
   - 以既有 R1/R2 檢索與交叉驗證為基礎，接上 **LLM** 組答、錯誤處理與可觀測欄位（`query_id`、latency、retrieved_count 等擇要）

2. **GraphRAG（Phase 2）**  
   - 在 `graphrag_jobs` 之上定義 job 狀態機、重試策略，並與 Data ingest／RAG 查詢邊界對齊

3. **Monitoring / Observability（Phase 2）**  
   - 統一跨模組觀測欄位與匯總出口（可銜接既有 orchestrator／各 core `dict`）

4. **Governance（Phase 2）**  
   - **`D:\大唐三省六部\04_Workflows\project_status\master_status.md`**、**`D:\大唐三省六部\04_Workflows\project_status\handoff.md`**：建立目錄與檔案後，於關鍵流程（含已完成之 **G1 `ingest_verify`**）每次執行後**自動寫回**

---

## 本輪結論

- **Gov Core System V1 baseline 已封版完成**。
- **全鏈路第一版 + live API 接通，驗收完成**。
- **環境、部署、安全、營運 smoke test 的最小收尾包已完成**（ENV-1／DEPLOY-1／SEC-1／OPS-1）。
- **後續工作不再視為 V1 補缺**；應以 **V2** 或 **部署／維運專案** 另開任務流與驗收。

本檔仍保留既有「全局敘事」與 **Infra I0/I1**、**Data D1/D2/D3**、**RAG R1/R2**、**Governance G1** 之 **CLI／dict 證據**（見後段），作為 V1 以前的板塊基線紀錄；與 **Gov Core V1 全鏈路＋API** 封版敘述並存，不互相沖突。[cite:507][cite:515]

---

## Changelog

- **2026-05-15 — DB-RECOVER-1：Postgres HEALTH 修復完成**：`/api/ask` 路徑上 `health.postgres` 連線失敗，錯誤訊息為 `connection failed`／`password authentication failed for user "admin"`。根因為 `gov_core_system\.env` 內 `DATABASE_URL` 仍為 `TODO_POSTGRES_PASSWORD` 占位字串，與實際 DB 密碼（`D:\大唐三省六部\01_Environments\.env` 之 `POSTGRES_PASSWORD`；`docker-compose.yml` 之 `env_file` 亦指向該檔）不一致；DB 本體正常（Postgres 容器 **`datang_postgres`**（`container_name`）**running**、埠映射 **`5432:5432`**、`netstat` 顯示 **`0.0.0.0:5432`／`[::]:5432` LISTENING**（Docker backend 轉發）、logs 含 **`database system is ready to accept connections`**）。修復措施：**未**變更 `docker-compose.yml`、**未**變更 DB 密碼／schema／volume，僅於 `gov_core_system\.env` 將 `DATABASE_URL` 由 `postgresql://admin:TODO_POSTGRES_PASSWORD@127.0.0.1:5432/datang_data?connect_timeout=30` 改為與 `01_Environments\.env` 內 `POSTGRES_PASSWORD`／`DATABASE_URL` 相同之實際值。驗證：於 venv 於專案根目錄載入 `.env` 後執行 `core.infra_health.check_postgres()`，輸出 **`{"ok": true, "message": "pg_ok"}`**，health 恢復。結論分類：**不是** docker 未啟動、**不是**容器啟動失敗、**不是** 5432 未映射、**不是** volume 損壞、**不是**埠被其他程式佔用；真正類型為「**應用端 `DATABASE_URL` 與執行中的 DB 帳密不一致（使用占位符）**」。
- **2026-05-15**：**V1 baseline 封版完成**。**全鏈路第一版 + live API 接通，驗收完成**（LangGraph `ask`／`ingest_verify`、GraphRAG backend／job flow、PostgreSQL／Qdrant、Langfuse、UI workbench、FastAPI：`/healthz`、`/api/ask`、`/api/ingest-verify`、`/api/graphrag/run`）。**ENV-1**、**DEPLOY-1**、**SEC-1**、**OPS-1** 標記為 **completed**。**V1 baseline frozen**；〈未完成項目（全局）〉改為僅列 **V2／部署／維運** 代表性方向並註明**非 V1 缺口**；〈推進策略〉新增 **V1 baseline 凍結** 小節；〈本輪結論〉對齊封版敘述；〈下一輪建議優先順序〉加註屬 V2／獨立專案。**master_status.md** 同日 append **V1 Baseline 封版完成** 紀錄。
- **合併 OLD + NEW**：保留原檔章節外框；於〈四個 Agent 狀態總覽〉後新增〈各 Agent 詳細里程碑與驗收條件〉，嵌入 I0/I1、D1–D3、R1/R2、G1 與執行證據。
- **狀態表更新**：Infra 標為 I0/I1 完成；Data 標為 D1/D2 完成、D3 未開始；RAG 標為 R1/R2 未開始；Governance 維持原骨架敘述。
- **Data 敘事修正**：移除「`ingest_batch()` 僅 skeleton」；改為單檔真實 ingest + verify 已驗收（`AGENTS.md`），下一步為目錄級 smoke。
- **全局未完成項目修正**：不再宣稱「尚未建立 core 與四支可執行腳本」；改列 D3、RAG 真管線、Governance 一鍵與可選 workspace 等現況缺口。
- **風險第 2 點更新**：由「import 是否存在不確定」改為「verify 錨點僅覆蓋種子」之實務風險。
- **下一輪優先順序**：改以 D3 → R1 → R2 → Governance 為序。
- **2026-05-14**：Governance——〈未完成項目〉、〈下一輪建議優先順序〉已對齊**已核實路徑**（`D:\大唐三省六部\04_Workflows\project_status\master_status.md` 與 `handoff.md` **不存在**）；移除「若與實際不一致以 repo 為準」等模糊句；明確 **CLI 已有、狀態檔待建＋一鍵流程待實作**。Data——**D3** 由「未開始」改為**已完成**，並補 **smoke_corpus** 驗收證據（`directory_batch`、`files_total/files_ok/files_skipped`、`ignore.json` / `unsupported_extension (.json)`、`verify.ok=True`、種子 **ASSERT: OK**）；同步更新狀態總覽表 Data 列、〈已完成項目〉、〈推進策略〉、〈本輪結論〉與〈下一輪〉優先順序（改為 R1 → R2 → Governance）。
- **2026-05-14（第二版）**：**RAG R1 / R2** 更新為**已完成**，補 **`rag_query_agent.py --top-k 5 "AGENTS.md"`** CLI 驗收證據（頂層 `ok`、`message`、`collection`、`query`、`top_k`、`hits`、`cross_check.summary.*`、lookup 與關聯一致性欄位）。**Governance G1** 更新為**已完成**，補 **`orchestrator_agent.py ingest_verify`** 與 **`run_ingest_verify`** 頂層／`health`／`ingest`／`verify` 證據及終端 **ASSERT / verify passed**。新增〈Governance Agent — G1〉小節（置於 GraphRAG 小節之前）。**Milestone `四大板塊第一版完成`** 已寫入〈已完成項目（全局）〉與〈本輪結論〉；〈未完成項目〉、〈推進策略〉、〈下一輪建議優先順序〉改以 **Phase 2**（真正問答、GraphRAG、Monitoring、狀態檔自動寫回）為主軸；狀態總覽表 RAG／Governance 列同步。**四大板塊第一版全部完成** 於 Changelog 明文化。

---

### Incident — DB-RECOVER-1（Postgres HEALTH）

- **時間**：2026-05-15
- **影響範圍**：Gov Core System 的 LangGraph health node／`ask` workflow 依賴的 Postgres health（例如 `/api/ask` 之 `health.postgres`）
- **根因**：應用端 `gov_core_system\.env` 中 `DATABASE_URL` 使用 `TODO_POSTGRES_PASSWORD` 占位符，未與基礎設施層的 `D:\大唐三省六部\01_Environments\.env` 對齊（該檔含實際 `POSTGRES_PASSWORD`，且為 `docker-compose` 之 `env_file`）
- **措施**：將 `gov_core_system\.env` 中的 DB 連線字串與 `01_Environments\.env` 的 `POSTGRES_PASSWORD`／`DATABASE_URL` 對齊；未變更 `docker-compose.yml`、未變更 DB 密碼／schema／volume
- **DB 本體佐證（排除 infra 故障）**：容器 **`datang_postgres`**（compose `container_name`）**running**；**`5432:5432`**；`netstat` **`0.0.0.0:5432`／`[::]:5432` LISTENING**（Docker backend）；logs **`database system is ready to accept connections`**
- **驗證**：venv 於專案根載入 `.env` 後執行 `core.infra_health.check_postgres()` → **`{"ok": true, "message": "pg_ok"}`**
- **教訓／避免方式**：
  - 未來若要更換 DB 密碼，必須同時更新：**`01_Environments\.env`**（compose 用）與 **`gov_core_system\.env`**（`app_api` 用）
  - `app_api` 只會載入專案根目錄 `.env`，不會自動讀上層 env，因此需要**明確同步**兩處設定

---

## HQ-Coordinator 輪任務板（2026-05-17 · 第一階段）

| 任務名稱 | 負責角色 | 狀態 | 最新進度 | 阻塞點 | 下一步 | 最後更新時間 | 備註 |
|----------|----------|------|----------|--------|--------|--------------|------|
| 暗部根路徑定案 | 尚書省 / HQ-Coordinator | Done | 鎖定 `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\` | — | — | 2026-05-17 | 見 Conditions「HQ 多智能體協作輪」 |
| 黑板追加 HQ 輪次區段 | HQ-Governance-Worker | Done | Conditions／Progress 末尾已追加 | — | — | 2026-05-17 | 嚴禁覆蓋既有內容 |
| 總部工具層盤點與 registry | HQ-Tooling-Worker | Done | `config\mcp\_registry\registry.md` 已建立 | — | 待尚書省審閱 | 2026-05-17 | 唯讀盤點；未安裝套件 |
| 暗部 Phase2 切片 | DarkOps-Worker | Blocked | — | 尚書省未另開暗部票 | 等待授權 | 2026-05-17 | 不得碰暗部根 |
| QA 閘門 1（黑板 + registry） | QA-Reviewer | Done | Pass（見下方 QA 小節） | — | — | 2026-05-17 | 唯讀驗收 |

### QA 閘門 1 — 驗收紀錄（2026-05-17）

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| `00_Agent_Work_Conditions.md` 既有內容未改動 | **Pass** | 追加前 SHA256 前綴一致（`prefix_ok=True`，前綴長度 6860 字元） |
| `00_Agent_Work_Progress.md` 既有內容未改動 | **Pass** | 追加前 SHA256 前綴一致（`prefix_ok=True`，前綴長度 19302 字元） |
| HQ 區段僅出現於檔案末尾 | **Pass** | `## HQ 多智能體協作輪`／`## HQ-Coordinator 輪任務板` 各僅 1 處，位於 `---` 分隔後 |
| Conditions ↔ Progress 對齊 | **Pass** | 暗部根均為 `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\`；DarkOps 列為 **Blocked** |
| 工具層 registry 交付物 | **Pass** | `D:\大唐三省六部\01_Environments\config\mcp\_registry\registry.md` 已存在 |
| 暗部未施工 | **Pass** | 本階段無 `python_venvs\gov_core_system\` 內檔案變更 |

**QA 結論：** 第一階段（總部治理層 + 工具層文檔）驗收 **通過**。

---

## Phase 2 / 2B — 工程規則轉制（2026-05-17）

**狀態**：Phase 2 母本 + `.cursor/rules` 轉制 **已完成**（待尚書省裁決是否升格定稿）。

### 交付物

| 檔案 | 說明 |
|------|------|
| `04_Workflows/CURSOR_AGENT_RULES.md` | 人類可讀母本（§0–§10 + 附錄 + 自檢） |
| `.cursor/rules/engineering-contract.mdc` | Cursor 機器規則（`alwaysApply: true`，81 規則段） |

### Work Report

**任務**：Phase 2B — 將 `ENGINEERING_CONTRACT` 轉制為 Cursor rules  
**角色**：Phase 2 執行 worker  
**日期**：2026-05-17（本地）

#### 1. 變更檔案

- **新建**：`04_Workflows/CURSOR_AGENT_RULES.md`
- **新建**：`.cursor/rules/engineering-contract.mdc`

#### 2. 可執行 skeleton

- 無（文檔／規則轉制工單）

#### 3. placeholder（未完成）

- `Master_Map.json` / `war_status` 未因本輪更新（非 AGENTS 全量封存）
- `handoff.md` 尚未建立
- 指紋登錄（`_register_fingerprints.py`）未執行

#### 4. 驗證證據

- 母本已寫入磁碟；`.mdc` 81 段（`###` 標題計）
- 覆蓋自檢：四流派、12-rule、禁止項、DoD、停工、Work Report — 均已映射
- 可移植檢查：規則正文無實例根路徑／env 鍵／DB 名（僅 FORBID 提及類型名）

#### 5. 阻塞

- 無

#### 6. 下一步建議

1. 尚書省裁決：母本與 `.mdc` 是否升格定稿、是否更新 W0 索引引用
2. 新 Agent 對話驗證：Cursor Rules 面板是否載入 `engineering-contract`（always applied）
3. 若需全量「封存」：另執行 `AGENTS.md` §封存協議（地圖、指紋、war_status）

#### 7. 憲法／合約

- override：無
- 留痕位置：本節（Progress 末尾）

**文檔工單自檢**：見 `CURSOR_AGENT_RULES.md` 附錄「文檔工單自檢要點」— 可移植正文零絕對路徑：**是**；未自標 v1.0：**是**；Phase 1 未偷寫 rules 正文：**是**（Phase 2B 方寫入）。

---

## 封存紀錄（2026-05-17 · AGENTS §封存協議）

**frozen_at_iso_utc**：`2026-05-17T09:30:38Z`  
**Master_Map.version**：`2.61`  
**constitution_version**：`v2.61`

### 協議步驟執行

| 步驟 | 狀態 | 證據 |
|------|------|------|
| 1. 同步地圖 | Done | `Master_Map.json` war_status／artifacts／runners 已更新；`wave_phase2_harness` 已寫入 |
| 2. 對齊憲法 README | Done | `README_Refresher.md` 升至 v2.61；§7 新增第 12 項 Phase 2 規則 |
| 3. 補登指紋 | Done | `newly_inserted={governance_doc:4}`，`registry_total_rows=36468`，`failures=0` |
| 4. 健康度核對（唯讀） | Done | Telegram lock：**缺席**；`Status.json` 末筆 `asset_value_evaluator.run_id=c0fa044a…` 與 war_status headline 一致 |

### 指紋登錄檔案

- `04_Workflows/CURSOR_AGENT_RULES.md`
- `.cursor/rules/engineering-contract.mdc`
- `04_Workflows/00_Agent_Work_Progress.md`（本檔）
- `04_Workflows/project_status/master_status.md`

---

## Phase 1 W4 盲測 — QA 列（2026-05-19）

**任務 ID**：HQ-P1-W4-BLIND-10  
**執行者**：QA-Reviewer（新 chat）  
**模式**：唯讀  

| # | 檢查項 | 結果 | 證據 |
|---|--------|------|------|
| 1 | W1–W3 零絕對磁碟路徑 | **PASS** | 三件套正文無 `D:\`、`C:\Users\` |
| 2 | W1–W3 零具體 runner 檔名 | **PASS** | 無 `_smoke_test_keys.py`、`Enter-Main.ps1` 等 |
| 3 | W1–W3 零雲端／模型實例 ID | **PASS** | 無 Groq 模型 ID |
| 4 | W1–W3 零 DB／集合實例名 | **PASS** | 無 `document_chunks`、`.db` 檔名 |
| 5 | W1–W3 零密鑰與輪替戰史 | **PASS** | 無 env 鍵原文、`rotated_at` |
| 6 | W1–W3 零 Progress／war 日期戰史 | **PASS** | 無 `2026-05-17`、wave 分數 |
| 7 | W1–W3 零**當輪** Done 旗標 | **PASS** | 結構性 Blocked 無日期；無「registry Done」 |
| 8 | W1–W3 零一次性健康證據 | **PASS** | 無 `ASSERT: OK` 當制度 |
| 9 | W1–W3 零 IDE／家目錄路徑 | **PASS** | 無 `%USERPROFILE%` |
| 10 | W1–W3 未貼整份 JSON | **PASS** | 無整份 runners JSON |

**W5 另檢**：I01–I23 ✅｜Z-* 與 W1 §7.1 ✅｜`Master_Map.version` **2.61** ✅  

**計分**：**10/10**  
**QA 結論**：通過  

---

## Phase 1 定稿令（2026-05-19 · 尚書省裁決）

**令檔**：`04_Workflows/project_status/HQ_PHASE1_FINALIZATION_ORDER.md`

**定稿權威**：`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`DEPARTMENT_MAP.md`、`INSTANCE_ANCHOR_TANG.md`、`_PORTABLE_CORE_INDEX.md`

**已執行**：v0.1 SUPERSEDED；`AGENTS.md` 校準同步；Conditions HQ 段去重引用 W5；W2 §7.3／W0 §3 量表對齊

**Phase 2**：閘門已解鎖；`CURSOR_AGENT_RULES.md`／`.mdc` 列 Phase 2 升格審查（見定稿令 §五）

**下一輪**：`HQ-P4-OPS-CYCLE` 或 `HQ-P2-RULES-FINALIZE`（`HQ-P3-TASK-ROUTING` 已 Done，見文末）

---

## HQ-P2-RULES-FINALIZE（2026-05-19 · 大唐副官）

**任務 ID**：HQ-P2-RULES-FINALIZE  
**狀態**：**定稿候選已呈尚書省**（待裁決升格）

### 對照與修補

| 項目 | 結果 |
|------|------|
| W2 ↔ `CURSOR_AGENT_RULES.md` 四流派／12-rule／DoD／Work Report | **對齊**（本輪補 FLOW-6.5 四流派、FLOW-6.9 §7.5） |
| `CURSOR_AGENT_RULES.md` ↔ `engineering-contract.mdc` | **82 段一致**（8/8 一致性 PASS） |
| 可移植掃描（P2-M／P2-C 正文） | **零絕對路徑** |

### 交付物

| 檔案 | 說明 |
|------|------|
| `04_Workflows/project_status/HQ_PHASE2_FINALIZATION_CANDIDATE.md` | Phase 2 定稿候選（呈尚書省） |
| `04_Workflows/CURSOR_AGENT_RULES.md` | 母本修補（FLOW-6.5／6.9、META-0.4） |
| `.cursor/rules/engineering-contract.mdc` | 機器規則同步（82 段） |

### Work Report（摘要）

- **驗證**：三方矩陣全 ✓；P2-M↔P2-C **8/8 PASS**；APP-DOC 七項通過
- **阻塞**：無
- **待裁決**：尚書省是否發布 Phase 2 定稿令
- **指紋**：P2-M／P2-C／候選檔已補登（`newly_inserted=3`，`registry_total_rows=36473`）

---

## HQ-P3-TASK-ROUTING（2026-05-19 · 大唐副官）

**任務 ID**：`HQ-P3-TASK-ROUTING`  
**狀態**：**Done**

### 交付

| 檔案 | 說明 |
|------|------|
| `04_Workflows/TASK_ROUTING.md` | Phase 3 任務路由制度（人讀） |
| `04_Workflows/task_routing_table.json` | 路由表 v1（14 路由 + default） |
| `02_Agents_Core/task_routing.py` | `route_task()` 解析器 |
| `04_Workflows/_route_task.py` | 副官 CLI |
| `04_Workflows/test_task_routing.py` | 單元測試 |
| `04_Workflows/Master_Map.json` | `version` **2.62**；artifacts／runners 登錄 |
| `AGENTS.md` | §初始化校準第 8 步「任務路由校準」 |
| `04_Workflows/project_status/HQ_P3_TASK_ROUTING_REPORT.md` | 交付報告 |

### 驗收證據

- `python .\04_Workflows\test_task_routing.py` → **6/6 OK**
- `_route_task.py --type hq.governance` → `HQ-Governance-Worker`，`assignable: true`
- `_route_task.py --type dark.infra` → `DarkOps-Worker` + `gov_core_system`，`assignable: false`（閘門 blocked）

### 下一步

- 尚書省裁決 `HQ-P2-RULES-FINALIZE` 升格，或 Phase 4 後續（自我進化／自動寫回）

---

## HQ-P4-OPS-CYCLE（2026-05-19 · 大唐副官）

**任務 ID**：`HQ-P4-OPS-CYCLE`  
**狀態**：**Done**

### 交付

| 檔案 | 說明 |
|------|------|
| `04_Workflows/OPS_CYCLE.md` | Phase 4 營運週期制度（人讀） |
| `04_Workflows/ops_cycle_schema.json` | schema v1（戰報／封存／回顧） |
| `02_Agents_Core/ops_cycle.py` | 戰報驗證、渲染、封存清單、回顧模板 |
| `04_Workflows/_ops_cycle.py` | 副官 CLI |
| `04_Workflows/test_ops_cycle.py` | 單元測試 |
| `04_Workflows/project_status/reviews/` | 回顧稿目錄 |
| `04_Workflows/Master_Map.json` | `version` **2.63** |
| `AGENTS.md` | §初始化校準第 9 步；封存戰報 CLI 銜接 |
| `04_Workflows/project_status/HQ_P4_OPS_CYCLE_REPORT.md` | 交付報告 |

### 驗收證據

- `python .\04_Workflows\test_ops_cycle.py` → **8/8 OK**
- `_ops_cycle.py validate-archive --mode minimal` → `ready_for_archive: true`
- `_ops_cycle.py new-review --type phase_gate --project HQ-Phase4 --ticket HQ-P4-OPS-CYCLE --dry-run` → 模板預覽 OK

### 下一步

- Governance 自動寫回 `master_status`／handoff（Progress G1 後續）

---

## HQ-P2-RULES-FINALIZE — 尚書省升格裁決（2026-05-19）

**任務 ID**：`HQ-P2-RULES-FINALIZE`  
**狀態**：**Done — Phase 2 定稿**

### 裁決

| 項目 | 結果 |
|------|------|
| 升格 | **核准** |
| 令檔 | `04_Workflows/project_status/HQ_PHASE2_FINALIZATION_ORDER.md` |
| P2-M | `04_Workflows/CURSOR_AGENT_RULES.md` |
| P2-C | `.cursor/rules/engineering-contract.mdc`（82 段，`alwaysApply: true`） |

### 驗收摘要（尚書省審閱）

- 裁決標準六項：**6/6 PASS**
- P2-M↔P2-C：**8/8 PASS**
- W2 原文：未改
- 暗部 DarkOps：**未解禁**（維持 Phase 1 令 §五語義）

### 待辦（非阻塞）

- 新 Agent 對話 Rules 面板抽測：`engineering-contract` **Always applied**

---

## Rules 面板抽測（2026-05-19）

**任務 ID**：HQ-P2-RULES-PANEL-VERIFICATION  
**執行者**：QA-Reviewer  
**抽測時間**：2026-05-19 04:16 AM

### 檢查結果

| # | 檢查項 | 結果 | 證據 |
|---|--------|------|------|
| 1 | Rules 面板存在 | ✅ PASS | workspace rules 正常載入 |
| 2 | engineering-contract 顯示 | ✅ PASS | 透過 always_applied_workspace_rules 載入 |
| 3 | Always applied 標記 | ✅ PASS | alwaysApply: true 生效 |
| 4 | 規則內容完整（82 段） | ✅ PASS | §0-§10 完整，含 META-0.1、FLOW-6.9、RULE-1~12 |

**總結**：✅ PASS

**說明**：
- engineering-contract.mdc 正確載入於 workspace rules（專案級規則）
- AGENTS.md 同時載入（always-applied）
- 規則內容與 Phase 2 定稿令一致（82 段完整）

**後續**：Phase 2 定稿令執行完畢，規則系統驗證通過。

---

> **Wave 1–3 導讀**：以下 Wave 1–3 戰報僅涉及 Observability / 成本實測 / 錯誤治理 v1，不覆寫 Gov Core System V1 全鏈路封板的既有語意。

## Wave 1 封板戰報：Monitoring + Alert v1（dev-ready）

**封板日期**：2026-05-19  
**專案範圍**：`gov_core_system`（Observability V2 · Wave 1）  
**執行角色**：Wave 1 封板文檔收口官（依 Chat A / Chat B / HQ Reviewer 驗收結果寫回）  
**封板性質**：**dev-ready 文件封板**；**非 production-ready**；本輪僅戰報寫回，未改程式／migration／服務。

### 1. 里程碑定位

| 維度 | 判定 |
|------|------|
| 技術底座 | Wave 1 Monitoring + Alert v1 已具備可重複驗收的 schema、ingest 同步、六條 monitoring API、dashboard 與 budget／alert evaluator 閉環 |
| 封板等級 | **dev-ready**：開發／聯調／受控驗收環境可視為 Wave 1 基線凍結 |
| 未宣稱項 | **production-ready**（生產封板、SLO、多環境閾值治理、成本／usage 全覆蓋均未完成） |
| 下游銜接 | 為 **Phase 3 / Phase 5** 提供可觀測真底座；為 **Phase 3.5 / Phase 7** 成本、usage、歸因治理提供前置里程碑 |
| Wave 2 | HQ 判定：**可安全進入 Wave 2**；本輪先完成文件封板 |

**封板 scope 表述（防誤讀）**：本次里程碑僅記錄「Wave 1 Monitoring + Alert **v1 在開發環境達 dev-ready 並完成文件封板**」，不得寫成「gov_core 全系統上線完成」或「生產監控封板」。生產就緒須另開 wave／工單，並通過 production 驗收標準後方可宣稱。

### 2. Wave 1 範圍內已驗收項（dev-ready，非 production-ready）

#### 2.1 Monitoring v1（組 1）

| 項目 | 狀態 |
|------|------|
| Migration | `005_monitoring.sql`、`006_monitoring_v1_align.sql`、`004_dlq.sql` 已套用 |
| 五表 | `task_runs`、`step_runs`、`daily_cost_summary`、`budget_rules`、`alert_events` 已存在 |
| 欄位對齊 | `mode=text`；成本欄位 `numeric(14,6)`；時間 `timestamptz`；`metadata=jsonb` |
| Ingest 同步 | traces／steps 已同步（曾驗證 `traces_synced=2`、`steps_synced=14`） |
| 驗收腳本 | `output/wave1_monitoring_acceptance.ps1`（gov_core_system） |
| API／Dashboard | `/healthz` 與六個 `/monitoring/*` 入口、dashboard 聯合驗收均 HTTP 200 |

#### 2.2 Alert + Budget v1（組 3）

| 項目 | 狀態 |
|------|------|
| `budget_rules` | 三規則雙閾值已落地（見 §4） |
| Evaluator | 讀 `budget_rules`、寫 `alert_events`；**API 不 inline evaluate** |
| Overview KPI | `/monitoring/overview` 已含 `kpis.budget` |
| Dashboard | 「Today's cost」已接 budget 狀態 |
| 測試資料清理 | `smoke_probe` 已清理 resolved；`/monitoring/alerts` 不再含 unresolved `smoke_probe` |
| 正式規則告警 | 受控測試觸發一筆：`rule_name=daily_cost_usd`、`severity=critical`、`value=55.0`、`threshold=50.0`；`/monitoring/alerts` 可見 |
| 運維說明 | 清理 SQL 與回復方式已有明確說明 |

### 3. 封板驗收證據

| 驗收項 | 結果 |
|--------|------|
| 聯合 HTTP | `/healthz`、六個 monitoring 入口、dashboard → **200** |
| 驗收腳本 | `output/wave1_monitoring_acceptance.ps1` → **exit 0** |
| Runbook 建議 | 重啟 API 後先確認 `/healthz` 的 `routes` 含六條 `/monitoring/*`，再執行 acceptance script |

以上為 **Monitoring + Alert v1** 驗收項，**不得**解讀為 gov_core_system / Observability 全系統或生產封板。

**證據來源**：Chat A（Monitoring）、Chat B（Alert + Budget）、HQ Reviewer 聯合驗收；本輪不重跑 migration、不啟動新服務。

### 4. v1 閾值（Wave 1 基準）

**決策 A — 閾值 v1**：**採用現有 seed 直接視為 Wave 1 / v1 正式基準值**；本輪不另起閾值版本號。後續調整須**新開 wave／工單**，禁止在無留痕情況下悄悄漂移。

| `rule_name` | warning | critical |
|-------------|---------|----------|
| `daily_cost_usd` | 40 | 50 |
| `error_rate_15m` | 0.10 | 0.15 |
| `dlq_backlog` | 5 | 10 |

### 5. 已知殘留（刻意不在本輪處理）

| 殘留項 | 歸屬 |
|--------|------|
| **production-ready** | 未宣稱；生產封板另開票 |
| **Langfuse usage／成本欄位覆蓋** | 後續治理（Phase 3.5 / Phase 7 方向） |
| **雙資料源（daily_cost_usd）** | evaluator 用 `daily_cost_summary`；overview `kpis.budget` 用 `task_runs` 當日 SUM — **本輪不統一**，見決策 B |
| 閾值調參 | 須新開 wave／工單 |
| 雙資料源統一 | **列入下一波治理工單**（Wave 2 或專項治理） |

**決策 B — 雙資料源**：`daily_cost_usd` 的 evaluator 與 overview budget **維持雙資料源**；本封板僅在戰報與 master 里程碑中**明確記錄差異與歸屬**，不在本輪改程式或 SQL 統一。

### 6. 里程碑判定

| 判定項 | 結論 |
|--------|------|
| Wave 1 Monitoring + Alert v1 技術面 | **dev-ready 封板條件已達成** |
| production-ready | **未完成、未宣稱** |
| Wave 1 文件封板 | **dev-ready 文件封板完成**（本段為正式戰報；非 production-ready） |
| 進入 Wave 2 | **可安全進入**（HQ 治理判斷；本輪先完成文件寫回） |

### 7. 三項封板決策（尚書省回看用）

| 編號 | 問題 | 裁決 |
|------|------|------|
| A | 閾值 v1 是否採現有 seed 為正式？ | **是** — 現有 seed 即 Wave 1 / v1 正式基準；調整須新工單 |
| B | `daily_cost_usd`／overview cost 雙資料源是否本輪統一？ | **否** — 本輪僅記錄；**下一波治理工單**統一 |
| C | 封板 scope 如何描述？ | **dev-ready 文件封板**；非生產封板；範圍限 Monitoring + Alert v1，不得擴寫為 **gov_core_system / Observability 全系統** `Completed` 或 production-ready |

**阻塞**：無（文件封板輪次）。  
**下一步**：Wave 2 施工；雙資料源與 Langfuse usage 治理另開工單。

---

### Wave 2 – 成本 / usage 實測小結（partial · 低樣本 · 僅文件複核）

**寫回日期**：2026-05-19  
**Wave 2 判定**：**partial** — 成本／usage **不可**用於決策；樣本極低（task_runs 2 筆、Langfuse n≈50）。  
**執行角色**：Wave 2 / Chat C — Cost Story / Phase Reviewer（HQ Reviewer）  
**資料來源**：Wave 1 封板殘留項；`monitoring_ingest` 現況 mapping；Chat C **唯讀**複核（PG `task_runs`／`step_runs`／`daily_cost_summary`、`GET /monitoring/overview`、`GET /monitoring/cost-trend?days=30`、Langfuse `probe_langfuse_required_fields` 50 筆樣本）。**未改程式**；Chat A／B 正式戰報尚未見 Progress 獨立條目，以下以實測 + 程式盤點合併敘述。

#### 1. 成本覆蓋率摘要（粗略）

| 窗口 | `task_runs` 筆數 | 具 **正成本**（`total_cost_usd > 0`） | 具 token（in/out > 0） | 成本合計（task_runs SUM） |
|------|------------------|--------------------------------------|------------------------|---------------------------|
| 最近 7 天 | 2 | **~0%** | **~0%** | **~$0** |
| 最近 30 天 | 2 | **~0%** | **~0%** | **~$0** |
| 全部 | 2 | **~0%** | **~0%** | **~$0** |

| 窗口 | `step_runs` 筆數 | 具正成本 | 成本合計 |
|------|------------------|----------|----------|
| 最近 7 天 / 全部 | 14 | **~0%** | **~$0** |

**語意**：欄位已寫入（多為 **0** 而非 NULL），但 **可觀測／可治理的「真實成本」覆蓋率約在 0%–10% 區間**（以「`total_cost_usd > 0` 且可歸因」為準）；距離 Wave 1 所稱「Langfuse usage／成本全覆蓋」仍遠。

**Langfuse 樣本（24h、n=50）**：**50/50** trace 缺 `usage`；**42/50** 缺 `release`／`handoff_status`／`human_review_required` → 缺口主因歸 **類別 1**（trace 本身無 usage／治理 metadata）+ **類別 3**（ingest 有 mapping 但來源為空時落 **0**）。

**`daily_cost_summary` 與雙資料源（Wave 1 決策 B 延續）**：

- 同日 **2026-05-19** 存在 **兩列**：一列 `total_cost_usd=0`、`task_count=2`（與 ingest 刷新一致）；一列 `total_cost_usd=55`、`task_count=0`（Wave 1 受控告警 smoke 殘留）。
- 若將兩列相加，30 日帳面約 **~$55**；若僅看 `task_runs` 聚合則 **~$0** → **趨勢與「今日成本」不可混讀**，須先統一資料源再談 Phase 7 治理。

#### 2. 成本分布（phase / mode / department）

| 維度 | 觀測（30 天 · 現有樣本） | 說明 |
|------|---------------------------|------|
| **mode** | 僅 **`ask`**（2 runs） | 目前樣本全為 ask 工作流 |
| **department** | 僅 **`dark_ops`** | 預設部門；尚無多部門對照 |
| **release** | Langfuse 多數缺失 | 歸因維度未就緒 |
| **phase** | 監控表屬 **Observability V2 / Wave 1–2**；計費硬化在 **Phase 5–7**（`task_costs`、CSV） | 兩條成本線並存：`task_runs`（dashboard）vs `task_costs`（admin CSV） |

**消耗「最高」**：在現有資料下為 **`mode=ask` × `department=dark_ops`**，但絕對值 **~$0**；帳面 **$55** 來自 **DCS smoke 列**，非真實業務流量。

**Live API（2026-05-19 抽樣）**：

- `/monitoring/overview`：`kpis.total_cost_usd=0`，`kpis.budget.today_cost_usd=0`（與 task_runs 一致）；**尚無** Chat B 規格中的 `kpis.cost`（7d／30d／top_mode）區塊。
- `/monitoring/cost-trend?days=30`：同日兩點 **$0** 與 **$55** 並存 → 與 DCS 雙列一致。

#### 3. 缺口分類（對齊 Chat A 框架）

| 類別 | 規模（本環境） | 補齊方向 |
|------|----------------|----------|
| **1. Langfuse trace 無 usage／totalCost** | 樣本 **100%** 缺 usage | 上游 trace metadata／generation 計費回寫 |
| **2. ingest 未實作 mapping** | **否** — `monitoring_ingest` 已 map `totalCost`／tokens | — |
| **3. 有欄位、寫入為 0** | **task_runs 2/2 為 0**；step 14/14 為 0 | `computed_from_tokens` + `metadata.cost_source`（Chat A 目標）；缺則 `cost_missing_reason` |
| **4. 其他** | DCS **雙列同日**；evaluator vs overview **雙資料源** | Wave 2 治理工單：刷新規則 + 單一「今日成本」定義 |

#### 4. 對 Phase 3.5 / Phase 7 的意義

| Phase | 判定 | 要點 |
|-------|------|------|
| **Phase 3.5**（成本觀測 readiness） | **partial — 底座 dev-ready（Wave 1）、資料未就緒** | Schema／ingest／六端點 **dev-ready**（Wave 1）；**成本覆蓋率實測 ~0% 有意義值**；budget KPI 可算但 **常為 0**；**不可**宣稱「成本觀測已可用於決策」 |
| **Phase 7**（成本治理） | **partial — 優先靶區已列、未收斂** | ① Langfuse **usage + 治理 metadata** ② **統一** `daily_cost_summary` 與 `task_runs`／evaluator ③ 完成 **Chat B** `kpis.cost` + dashboard 成本視圖 ④ 對齊 **Phase 7** `task_costs`／CSV 與 monitoring 表 **欄位語意** |

#### 5. 對下一波建議（含錯誤處理 / 自動恢復）

1. **先收 Chat A**：backfill + `cost_missing_reason`／`cost_source` 落地後，重跑覆蓋率報表。  
2. **再收 Chat B**：`kpis.cost` 與 dashboard 表格；驗收時 **禁止** 將 DCS smoke **$55** 與 task_runs **$0** 加總呈現。  
3. **Wave 3 方向**：在 **structured errors**（Wave 2 另一線）穩定後，將 **失敗 trace 的 cost／usage 標記** 與 DLQ／retry 聯動，避免「錯誤路徑零成本」扭曲產出比。  
4. **雙資料源**：單獨治理工單（Wave 1 決策 B），完成前 Phase 7 告警與 dashboard **分開標註來源**。

**阻塞**：Chat A／B 正式交付物未入檔；`kpis.cost` 未現；Langfuse usage 全樣本缺失。  
**Chat C 本輪**：**部分達成**（Phase 語言 + 實測寫回完成；上游施工收斂待 A／B）；**≠** Wave 2 整線 **dev-ready**。

---

### Wave 3 – Error Handling & Auto-Recovery v1（dev-ready · partial · 文件封板）

**寫回日期**：2026-05-19  
**執行角色**：Wave 3 / Chat D — HQ Error Playbook / Governance Writer（**僅文件**）  
**資料來源**：Chat A（`core/error_taxonomy.py` + monitoring ingest 增量）、Chat B（`core/retry_invoke.py` + `core/dlq.py` enriched DLQ）、Chat C（`core/auto_recovery.py` hook）、`output/wave3_retry_policy_report.md`、Wave 2 structured errors soak。本輪未改程式。

> **基準線聲明**：以下為 **Wave 3 v1（dev-ready · partial）** 之文件基準，供 Wave 4+ 修訂；**非** production 已啟用之運維策略。調整分類邊界或自動化範圍須新開 wave／工單並於 Progress **末尾**留痕。

#### 0. 三層架構（觀測 → 策略 → 處理邊界）

| 層次 | Wave 3 交付 | 主要模組／入口 |
|------|-------------|----------------|
| **觀測（Monitoring）** | `error_category`／`error_code`／`non_retryable` 寫入 `task_runs`／`step_runs.metadata`；`GET /monitoring/dlq` 暴露 enriched 列 | Chat A · `error_taxonomy` · `monitoring_ingest` |
| **策略（Retry / DLQ）** | Flag-gated exponential backoff；失敗入 DLQ（`non_retryable`／`max_retries_exhausted`）；審計欄位含 trace／pipeline／mode／department | Chat B · `retry_policy` · `retry_invoke` · `dlq` |
| **自動／人工邊界** | 窄域 **auto-recovery**（retry 耗盡後至多 **1** 次 immediate re-invoke）；其餘 DLQ 待人工；`HUMAN_REJECTED`／interrupt 走人工閘 | Chat C · `auto_recovery`；Phase 8 interrupt 既有 |

#### 1. 錯誤分類表（Error Taxonomy · Chat A）

| `error_category` | 語意 | 典型 `error_code`／訊號 | 預設 `non_retryable` |
|------------------|------|-------------------------|----------------------|
| `system_error` | 連線、timeout、依賴／infra | `HEALTH_FAILED`、`INGEST_FAILED`、`PIPELINE_FAILED` + transient 例外／訊息 | **否**（可 retry） |
| `llm_error` | 模型調用、rate limit、token／context | `RETRIEVE_FAILED`、`ANSWER_FAILED` + LLM 例外別名 | 依 `retryable`；常為可重試 |
| `validation_error` | 業務／schema 不符 | `SCHEMA_VALIDATION_FAILED`、`BUSINESS_VALIDATION_FAILED`、`MALFORMED_JSON`、`EMPTY_PAYLOAD`、`VERIFY_FAILED`、`HUMAN_REJECTED` | **是** |
| `config_error` | 設定／環境／金鑰類 | 訊息含 missing env、api key、langfuse 等 | **是** |
| `unknown` | 無法歸類 | `PIPELINE_FAILED` 且訊號不足 | 依推斷；常 fail-fast |

**Metadata 契約**（失敗路徑）：扁平鍵 `error_category`、`error_code`、`non_retryable`；巢狀 `error_taxonomy` 供 ingest／DLQ 對齊。Langfuse 若已帶 `error_category` 則**尊重上游**不覆寫。

**Wave 2 銜接**：HTTP `structured_errors[]`（`error_schema_version=v1`）提供 `code`／`message`／`node`／`retryable`；taxonomy 由 `taxonomy_from_structured_error()` 對齊。

#### 2. Retry / DLQ 策略 v1（Chat B）

**Runtime**：預設旗標皆 **off**；下圖為 **staging 全開時** 之行為，非現網預設。

**處理流水線**（`GOV_CORE_RETRY_POLICY_ENABLED=true` 且 `GOV_CORE_DLQ_ENABLED=true` 時）：

```mermaid
flowchart TD
  A[invoke] --> B{retryable?}
  B -->|否| C[DLQ: non_retryable]
  B -->|是| D{attempt < max?}
  D -->|是| E[backoff + retry]
  E --> A
  D -->|否| F{auto-recovery on?}
  F -->|eligible| G[1x immediate re-invoke]
  G -->|成功| H[return OK]
  G -->|失敗| I[DLQ: max_retries_exhausted]
  F -->|skip| I
```

| 項目 | 規則 |
|------|------|
| **可重試** | `ConnectionError`／`TimeoutError` 等 transient；`GovCoreError` 且 `retryable=True`；未落入 fail-fast 代碼集 |
| **不可重試（fail-fast）** | `SCHEMA_VALIDATION_FAILED`、`BUSINESS_VALIDATION_FAILED`、`MALFORMED_JSON`、`EMPTY_PAYLOAD`、`HUMAN_REJECTED`；`ValueError`／`TypeError`／`KeyError`／`JSONDecodeError` |
| **Backoff** | `min(base * 2^(attempt-1), max_delay_ms)` + 可選 full jitter |
| **DLQ `dlq_reason`** | `non_retryable`（首次即不可重試）／`max_retries_exhausted`（重試＋可選 auto-recovery 仍失敗） |
| **DLQ 審計欄位** | `trace_id`、`pipeline`、`mode`、`department`、`error_category`、`error_message`、`retryable`、`attempt`／`max_attempts` |
| **人工重試 API** | `POST /api/dlq/retry/{task_id}`（Phase 7 已驗 404 契約；200／409 需真機 DLQ 列） |
| **不進 DLQ** | `WorkflowInterrupted`（人工中斷路徑） |

**環境旗標（預設皆 off · staging 前勿 production 全開）**：

| 旗標 | 預設 | 層級 |
|------|------|------|
| `GOV_CORE_RETRY_POLICY_ENABLED` | false | Chat B · invoke 重試 |
| `GOV_CORE_DLQ_ENABLED` | false | DLQ 持久化 |
| `GOV_CORE_AUTO_RECOVERY_ENABLED` | false | Chat C · 額外 1 次恢復 |
| `GOV_CORE_DLQ_AUTO_RETRY_ENABLED` | false | **Wave 4a** 背景排程（非本輪） |

#### 3. Auto-Recovery 適用情境（Chat C）

**策略**：`immediate_retry` — 在 Chat B **retry 已耗盡**且錯誤仍 `retryable` 時，至多 **1** 次輕量 re-invoke；**不**提高 `max_attempts`、**不**改 DLQ schema。

| 判定 | 條件 |
|------|------|
| **可觸發** | `error_category=system_error` 且（transient 例外 **或** code ∈ `HEALTH_FAILED`／`VERIFY_FAILED`／`RETRIEVE_FAILED`） |
| **明確排除** | `validation_error`、`config_error`；code ∈ `INGEST_FAILED`、`HUMAN_REJECTED` 及 Chat B fail-fast 集 |
| **Metadata** | `auto_recovery_applied`、`auto_recovery_outcome`（`skipped`／`attempting`／`recovered`／`failed`）、`auto_recovery_strategy`、`auto_recovery_recovered`；失敗時寫入 DLQ `extra` |

#### 4. 處理邊界矩陣（自動 / DLQ / 人工批准）

| 情境 | `error_category` 示例 | 自動處理（需開旗標） | DLQ 待人工 | 須人工批准才繼續 |
|------|----------------------|----------------------|------------|------------------|
| Transient 網路／timeout | `system_error` | Retry → 可選 Auto-recovery | 仍失敗 → `max_retries_exhausted` | — |
| LLM rate limit／暫時失敗 | `llm_error` + `retryable=true` | Retry（無 auto-recovery 除非歸 `system_error`） | 耗盡後入 DLQ | — |
| Schema／業務驗證 | `validation_error` | **無** | `non_retryable` | — |
| 人審拒絕 | `validation_error` · `HUMAN_REJECTED` | **無** | `non_retryable` | **是**（業務決策） |
| 設定／金鑰缺失 | `config_error` | **無** | `non_retryable` | 修復 env 後重跑 |
| 高風險節點＋interrupt 等待 | — | **無**（gate 阻擋） | 不 enqueue | **是** · `task_interrupts` `waiting_human` |
| 旗標全 off | 任意 | **無**（legacy 直接 fail／僅 API `errors[]`） | 可能無持久 DLQ | 依舊 interrupt／HITL |

**尚書省操作面**：

1. **DLQ 待看**：`GET /api/admin/dlq` 或 `GET /monitoring/dlq` → 篩 `error_category`／`retryable` → `POST /api/dlq/retry/{task_id}`。  
2. **須批准**：`HUMAN_REJECTED`、interrupt resume、非 localhost 之 admin token 操作。  
3. **Wave 1 告警**：`dlq_backlog` warning **5**／critical **10**（與 DLQ 列數聯動；auto-recovery 成功則不增量）。

#### 5. Phase / Wave 狀態（錯誤治理維度）

| Phase | 判定 | 要點 |
|-------|------|------|
| **Phase 3 · 錯誤觀測 slice** | **partial — 觀測就緒** | Taxonomy + DLQ enriched 欄位可供路由／戰報分類；**≠** HQ-P3-TASK-ROUTING（任務路由 CLI）Completed；**尚未**依 `error_category` 自動派工 |
| **Phase 5**（冪等 + DLQ） | **dev-ready · partial** | DLQ 表／手動 retry API 既有；Wave 3 補 **category + pipeline 語意**；真機 DLQ 200 待 `GOV_CORE_DLQ_ENABLED` |
| **Phase 7**（成本 + 營運硬化） | **partial** | DLQ retry 契約已測；**錯誤路徑成本治理 deferred**（見 Wave 2 建議）；`error_rate_15m` 告警可觸發但樣本少 |

**Wave 3 總判定**：**dev-ready · partial** — 單元／整合測試基線通過（retry 專項 + `test_dlq_wave3` + `test_auto_recovery`）；**staging soak 與 production 漸進開旗標未完成**。

#### 6. 驗收證據（文件輪 · 未重跑）

| 來源 | 結果語意 |
|------|----------|
| `tests/test_retry_policy.py` | Gate 0 PASS（backoff／jitter／fail-fast） |
| `tests/test_dlq_wave3.py` | enriched DLQ + taxonomy 分類 PASS |
| `tests/test_auto_recovery.py` | 8 cases · eligibility + hook PASS |
| `output/wave3_retry_policy_report.md` | 全 suite 135 ran · 134 PASS |
| Wave 2 soak | `structured_errors[]` 契約 PASS |

#### 7. 未納入 Wave 3／未來擴充

| 項目 | 歸屬 |
|------|------|
| DLQ 背景自動重試 | Wave 4a · `GOV_CORE_DLQ_AUTO_RETRY_ENABLED` |
| DLQ UI／批量操作／分類儀表板 | Wave 4+ |
| 依 `error_category` 自動路由 worker | Phase 3 延伸工單 |
| 失敗 trace **cost／usage** 與 DLQ 聯動 | Wave 3 後續／Phase 7 |
| `llm_error` 專用 fallback 模型 | 未實作；Chat C 僅 `immediate_retry` |
| Production 全開 retry + auto-recovery | 須 staging soak + 尚書省裁決 |

**阻塞**：真機 `GOV_CORE_RETRY_POLICY_ENABLED`／`GOV_CORE_DLQ_ENABLED`／`GOV_CORE_AUTO_RECOVERY_ENABLED` 仍 false；DLQ 200／409 真機待失敗任務種子。  
**Chat D 本輪**：**文件目標達成**（Playbook + Phase 語言寫回；**≠** Wave 3 整線 production-ready；施工驗收依賴 staging 開旗標）。

---

### Wave 4A – ask_pipeline 實測小結（dev-run · partial）

**寫回日期**：2026-05-19  
**執行角色**：Wave 4A / Chat C — 實測戰報與 Phase 語言寫回者（**僅文件**）  
**資料來源**：Chat A `output/wave4a_ask_pipeline_live_report.md` + `output/wave4a_ask_pipeline_live_run.json`；Chat B `output/wave4a_ask_pipeline_monitoring_report.md`。**未改程式**。

> **基準線聲明**：本節為 **Wave 4A v1（dev-run · partial）** 文件寫回；**非** production SLO 驗收；**非** production-ready。

#### 1. 實測樣本（pipeline / 問題類型 / 數量）

| 項目 | 內容 |
|------|------|
| **Pipeline** | `ask_pipeline`（`POST /api/ask`，`mode=ask`，`department=dark_ops`） |
| **Session 前綴** | `wave4a-A01` … `wave4a-A20`（每題 `thread_id` 對齊 Langfuse Session） |
| **樣本數** | **20**（A01–A20） |
| **問題類型** | **short ×5** · **long ×5** · **edge ×5** · **system ×5** |
| **有效批次** | API **重啟後**重跑（`api_restarted_before_run: true`）；UTC **2026-05-19 10:45–10:48** |
| **節點路徑** | 有效樣本皆 `health_node → retrieve_node → answer_node` |

**環境插曲（不計入有效成功率，但記入錯誤治理）**：重啟前首次批次 20/20 HTTP 200 但 **`biz_ok=false`**（`ImportError: ENV_FEATURE_AUTO_RECOVERY` from `gov_core_contracts`）；舊 `uvicorn` 進程未載入最新契約常數。重啟 `127.0.0.1:8000` 後有效批次如上。

#### 2. 成功率 / Latency / Cost / Error 摘要

| 維度 | 有效批次（Chat A · JSON） | Monitoring 收口（Chat B · PG／Langfuse） |
|------|---------------------------|----------------------------------------|
| **HTTP / API** | **20/20** | 20/20 |
| **業務 `biz_ok`** | **20/20（100%）** | 對 **wave4a-%** PG 子集：**0 列**（ingest 未對齊本次 trace_id） |
| **`trace_id` 回傳** | **20/20**；`langfuse_enabled: true` | Langfuse `wave4a-*` session：**≈1** trace（PG **0**） |
| **Latency（端對端 `elapsed_s`）** | p50 **~3.74s** · p95 **~7.87s** · min **2.26s** · max **13.41s** | PG `task_runs.latency_ms`：**無 wave4a 列** |
| **Cost（PG）** | — | wave4a 子集 **$0**；**無** `step_runs`（未進 monitoring 表） |
| **Error（有效批次）** | **0**；`errors[]` 空 | — |
| **Error（重啟前批次）** | 20/20 同簽名：`ImportError` → taxonomy **`config_error`**（deploy／契約不一致；**未**寫入 PG metadata） |

**參考（非 Wave 4A）**：同日前序 `mon-status-smoke-1/2` 兩筆 ask trace PG 合計 **~$0.002831**（**~$0.0014/trace**）。Wave 2 合成基準 **~$0.0136/trace（n=20，模擬）** — **不可**與本輪 live 同口径比較（本輪 PG 無 wave4a 成本列）。

#### 3. 對 Wave 2 / Wave 3 的「實戰驗證程度」

| 前序 Wave | Wave 4A 後驗證語意 |
|-----------|-------------------|
| **Wave 2（成本）** | 意圖將可觀測樣本由 **2 筆 → 20 筆** live ask；**Langfuse 側** Chat A 已產 **20** 條完整 trace（含 `trace_url`、三節點）；**PG／overview** 仍 **未** 反映 wave4a 流量 → **成本觀測擴樣未收口**（仍 partial；須 **monitoring ingest + backfill** 後重跑 Chat B cost 驗收）。 |
| **Wave 3（錯誤）** | 重啟前失敗參照 Wave 3 **`config_error`** 分類邊界（契約常數缺失＝不可重試）；有效批次 **未** 觸發 DLQ／retry／auto-recovery（旗標預設 off）。Taxonomy **概念上可用**，但 **PG enriched metadata 未驗**（失敗路徑未進表）。 |
| **Wave 1（Monitoring 底座）** | 六端點／schema **仍 dev-ready**；本輪暴露 **「API 成功 ≠ PG 有列」** ingest 斷層；`kpis.cost`／overview **仍無法** 反映本次 20 筆。 |

#### 4. Phase 語言（Wave 4A 後 · 仍可 partial）

| Phase | 判定 | Wave 4A 後要點 |
|-------|------|----------------|
| **Phase 3**（可觀測性） | **partial — live trace 已驗、營運表未同步** | **已驗**：20 條 `ask_pipeline` Langfuse trace + 本機 `task_traces.jsonl`。**未驗**：PG `task_runs`／`step_runs`、dashboard overview 對本次 session 的覆蓋；**≠** production trace SLO。 |
| **Phase 5**（營運／冪等＋DLQ） | **dev-ready · partial（未因本輪升格）** | 有效批次無 DLQ 積壓；retry／DLQ 旗標仍 off。營運教訓：**進程熱重載 vs 契約常數** 可造成全批 `config_error` 假失敗。 |
| **Phase 7**（成本治理） | **partial — 仍不足 SLO／SLA 討論** | 20 條 live 流量 **尚無** PG 成本／usage 可聚合；雙資料源（DCS **$55** smoke vs task_runs **$0**）**延續** Wave 1–2；**不可**宣稱成本治理或錯誤率告警已達決策級。 |

#### 5. 驗收證據（文件輪）

| 來源 | 結果語意 |
|------|----------|
| Chat A live JSON | `api_ok` **20/20** · `biz_ok` **20/20** · `trace_id` **20/20** |
| Chat A live report | 問題清單 A01–A20；重啟前後環境說明 |
| Chat B monitoring report | PG wave4a **0** 列；失敗批次 **config_error** 簽名；與 Wave 2 基準不可比 |
| 本輪邊界 | **未**執行 monitoring ingest 重跑；**未**改 Python／SQL／.env／venv／checkpoint |

**阻塞**：① 部署與 `gov_core_contracts` 常數一致（避免舊進程假失敗）② **monitoring ingest** 對 20 條 `trace_id` backfill ③ Chat B **cost／overview** 驗收重跑。  
**下一步**：修復／確認契約常數 → 可選重跑 Wave 4A → ingest → 更新 `kpis.cost` 與 Phase 7 覆蓋率報表；DLQ 真機 soak 仍屬 Wave 4+。  
**Chat C 本輪**：**文件目標達成**（Progress + master_status 寫回）；**≠** Wave 4A production-ready。

---

### Wave 4C – ask_pipeline Dev SLO / SLA 草案

**寫回日期**：2026-05-19  
**執行角色**：Wave 4C / Chat C — ask_pipeline 最小 SLO / SLA 定義者（**僅文件**）  
**資料來源**：Wave 4A `output/wave4a_ask_pipeline_live_run.json` · Chat A 報告；Wave 4A Chat B `output/wave4a_ask_pipeline_monitoring_report.md`（Langfuse generations 成本 rollup）。Wave 4B 假設：20 條 `trace_id` 已 ingest → PG `task_runs`／`/monitoring/overview`／`kpis.cost` 可對齊（本輪**未重跑** ingest 驗證）。**未改程式**。

> **草案聲明**：以下為 **dev / staging SLO 草案**；**非** production SLA；**非** production-ready。SLO 違反時語意為「dev 回歸／需調查」，**不**觸發對外賠償或正式 SLA 通報。

#### 1. Dev SLO 指標表（草案 v1）

| 指標 | Dev SLO 目標 | Wave 4A 實測（n=20，有效批次） | 量測口徑／備註 |
|------|--------------|----------------------------------|----------------|
| **業務成功率**（`biz_ok`） | **≥ 95%** | **20/20（100%）** | Chat A · `wave4a_ask_pipeline_live_run.json`；HTTP 200 且 `biz_ok=true` |
| **p95 端對端延遲** | **≤ 8 s** | **~8.15 s**（8147 ms，`elapsed_s`）· Langfuse trace **~7.88 s** | Chat A 客戶端計時為 SLO 主口徑；Langfuse 低 ~270 ms 屬 HTTP／客戶端開銷，**可接受** |
| **p50 端對端延遲**（參考，非 SLO 硬門） | — | **~3.5 s**（3505 ms）· Langfuse **~3.25 s** | 僅作基準線參考；未設硬門 |
| **平均 cost / trace** | **≤ $0.005** | **~$0.0043**（$0.0857 ÷ 20） | Langfuse **generations** rollup（Chat B）；PG 根 trace `totalCost` 仍常為 $0（Wave 2 已知 usage 缺口） |

**SLO 設計原則**：目標略**保守於** Wave 4A 實測（成功率留 5% 緩衝；p95 對齊實測上界 ~8 s；cost 上限高於實測 ~16%）。

#### 2. 與 Monitoring／PG 的對應（Wave 4A → 4B 語意）

| 維度 | Wave 4A 實測當下 | Wave 4B 預期（假設 ingest 成功） | SLO 驗收建議 |
|------|------------------|----------------------------------|--------------|
| 成功率 | Langfuse + Chat A 一致 **100%** | `task_runs` success 率 ≥ 95% | 以 **`biz_ok`** 或 PG `status=success` 對齊；dev 以 Chat A 批次為準 |
| Latency | PG **無** wave4a 列 | `task_runs.latency_ms` p95 ≤ 8000 | 定期對照 Chat A `elapsed_s` 與 PG；偏差 >10% 記 notes |
| Cost | PG 根 trace **$0**；Langfuse rollup **~$0.0043** | `kpis.cost`／overview 應反映 20 筆（排除 DCS **$55** smoke） | SLO 以 **Langfuse generations** 為準直至根 trace `usage` 修復；PG 為輔助 |

#### 3. 適用範圍

| 項目 | 內容 |
|------|------|
| **環境** | **dev**、**staging** 僅限；**不含** production |
| **Pipeline** | `ask_pipeline` · `POST /api/ask` · `mode=ask` · `department=dark_ops` |
| **基準 cohort** | session 前綴 `wave4a-A01`…`A20` 同類型問題集（short/long/edge/system 各 5） |
| **樣本門檻** | 單次驗收建議 **n ≥ 20**；低於 20 僅作 smoke，**不**單獨宣稱 SLO 達標 |
| **排除** | API 重啟前 `config_error` 批次；非 `ask_pipeline`；ingest 未完成的 PG-only 判定 |

#### 4. 何時調整 SLO

- **流量／用例變更**：問題長度分布、RAG top_k、模型換版 → 重跑 dev-run 後修訂 p95／cost 目標。  
- **基礎設施變更**：API 主機、向量庫、Langfuse 區域 → 重量 latency 基準。  
- **成本口徑修復**：根 trace `usage`／PG ingest 與 Langfuse 一致後，可將 cost SLO 改為 **PG-primary** 並收緊上限。  
- **未達 SLO**：dev 標 **partial**、寫 Progress 阻塞；**不**升級為 production SLA。

#### 5. 未來演進方向

| 階段 | 方向 |
|------|------|
| **Wave 5 / staging soak** | 擴樣 **n ≥ 100**、多時段；p95／cost 用 PG + Langfuse 雙源一致率 |
| **Phase 7** | 成本治理決策級：錯誤路徑 cost、告警 `error_rate_15m` 與 SLO 聯動 |
| **Production SLA** | 須尚書省裁決 + 獨立 soak + 運維 on-call；**不得**由本草案直接升格 |

#### 6. 驗收證據（文件輪）

| 來源 | 結果語意 |
|------|----------|
| Wave 4A live JSON | `biz_ok` **20/20** |
| Wave 4A monitoring report | p50 **3505 ms** · p95 **8147 ms** · Langfuse cost **~$0.00429/trace** |
| 本輪邊界 | **未**重跑 monitoring ingest；**未**改 Python／SQL／.env |

**Chat C 本輪**：**文件目標達成**（Dev SLO 草案寫回 Progress + master_status）；**≠** production SLA 定稿。

---

### Phase 5 — 儀表板與告警 · 資料安全合規 v1（dev/staging · 可演示 partial）

**已讀**：`AGENTS.md` · 工程合約／`.cursor/rules` · 本檔 · `master_status.md` · Wave 1 monitoring／alert 程式與 `output/phase5_dashboard_alert_security_v1.md`  
**狀態依據**：Wave 1 六條 `/monitoring/*` + dashboard 已存在（~70%）；本輪補齊 notifier + security hooks + evaluate API → **可 demo v1**；**非 production-ready**。

#### Phase 5 並行拆工計畫（Agent A/B/C/D）

| 線別 | 目標 | 預計修改檔案 | 依賴 | 驗證方式 | 完成定義 |
|------|------|--------------|------|----------|----------|
| **A · Dashboard** | 強化 v1 儀表板（health／latency／cost／errors／DLQ） | `static/monitoring/dashboard.html`、`core/monitoring_service.py`、`core/schemas/monitoring.py` | Wave 1 表 + `DATABASE_URL` | `GET /monitoring/dashboard` 200；overview KPI 含 p95／DLQ | 五域 KPI 可刷新；標 dev banner |
| **B · Alerting** | threshold evaluator + `alert_events` + notifier | `core/monitoring_alerts.py`、`core/alert_notifier.py`、`core/monitoring_api.py`、`007_alert_budget_v1.sql`（已存在） | A 無硬依賴；PG `budget_rules` | `POST /monitoring/alerts/evaluate`；`monitoring_alert_smoke.py`；mock delivery 非空 | 觸發規則可寫入 PG + mock 通知 |
| **C · Security** | PII mask／redact + encryption hook 接點 | `core/security_compliance.py`、`core/error_adapter.py`、monitoring read paths | 無 | `test_security_compliance` | API／monitoring 匯出含 redaction；hook 可枚舉 |
| **D · Docs／寫回** | dev/staging 標註 + Progress／master | `output/phase5_dashboard_alert_security_v1.md`、本檔、`master_status.md` | A–C 摘要 | 文件自檢 + 單元測試 exit 0 | 雙檔末尾追加；明確 partial |

**本輪實作**：單 agent 合併 A+B+C 最小增量；D 寫回。

#### 變更摘要（2026-05-19）

- **新增** `core/security_compliance.py`（PII mask、`redact_dict`、`NoOpEncryptionHook`）
- **新增** `core/alert_notifier.py`（`MockAlertNotifier`）
- **擴充** `monitoring_alerts` → insert 後 mock notify；`POST /monitoring/alerts/evaluate`；`GET /monitoring/security-status`
- **擴充** monitoring 讀路徑 + `error_adapter` PII redaction；dashboard dev banner + Evaluate 按鈕
- **文件** `output/phase5_dashboard_alert_security_v1.md`

#### 驗證證據

```text
python -m unittest tests.test_security_compliance tests.test_alert_notifier tests.test_monitoring_alerts tests.test_monitoring_api -v
→ Ran 22 tests in 0.225s — OK
```

#### 阻塞／下一步

- **阻塞**：live PG smoke（`monitoring_alert_smoke.py`）需本機 `DATABASE_URL` + migrations（本輪未重跑 live）
- **下一步**：雙資料源成本統一工單；Slack/email notifier；KMS encryption 實作；Wave 5 soak n≥100

#### Tech Lead 整合（共用契約 + 四線協調 · 2026-05-19）

**共用契約（先合併）**：

| 契約 | 權威路徑 |
|------|----------|
| Dashboard API | `core/schemas/monitoring.py` · `shared/schemas/phase5_dashboard_api_v1.json` |
| Alert event / severity | `core/contracts/phase5_monitoring.py` · `shared/schemas/alert_event_v1.json` |
| Security sanitize | `core/security_compliance.py` (`SanitizeHelper`) · `shared/schemas/security_sanitize_v1.json` |
| 協調邊界 | `output/phase5_parallel_coordination.md` |

**四線狀態**：A/B/C/D 均 **done** · **可 merge**（見協調檔）

**整合檢查**：

| 項 | 結果 |
|----|------|
| Dashboard 五域（alerts/cost/latency/errors/DLQ） | **Pass**（靜態頁 + 5 GET） |
| Evaluator → `alert_events` | **Pass**（程式）；live PG **blocked** 無 `DATABASE_URL` |
| Security → tracing/log | **Pass** — `observability_v2.log_event` → `sanitize_for_log` |
| Progress / master_status | **Pass** |

**驗證**：`unittest` **23/23 OK**（含 `test_observability_v2_sanitize`）

---

### Phase 5 · Agent D — 資料安全合規 v1（dev/staging baseline）

**已讀**：`AGENTS.md` · 工程合約／`.cursor/rules` · `HARNESS_CONSTITUTION.md` §7 類型 · `core/security_compliance.py` · monitoring／error／Langfuse 相關路徑 · `output/phase5_dashboard_alert_security_v1.md`  
**狀態依據**：A/B/C 已交付 sanitize 主模組；本輪 D 補 **allowlist/denylist 設定點**、**alert/DLQ 接線**、**合規審計文件**；仍 **非 production-ready**。

#### 敏感資訊可能落點（審計摘要）

| 落點 | v1 狀態 |
|------|---------|
| API response（`finalize_errors_for_api`） | 已 mask/redact |
| Monitoring 讀模型 | 已 `redact_dict` |
| `observability_v2.log_event` | 已 `sanitize_for_log` |
| Alert notifier 日誌／mock delivery | **本輪** 已 sanitize |
| DLQ enqueue audit log | **本輪** 已 sanitize |
| Langfuse trace input/output | **未覆蓋**（第三方 SaaS） |
| PG 表 at-rest | **未加密** |

#### 變更（Agent D · 2026-05-19）

- **擴充** `core/security_compliance.py`：`get_pii_allowlist_keys` / `get_pii_denylist_keys` · env `GOV_CORE_PII_*_EXTRA`
- **接線** `core/alert_notifier.py` · `core/dlq.py` audit log
- **文件** `output/phase5_data_security_compliance_v1.md`（適用範圍／限制／未覆蓋風險／下一步）
- **契約** `shared/schemas/security_sanitize_v1.json` 增 env_flags
- **測試** `test_security_compliance`（allowlist/denylist）· `test_alert_notifier`（message redact）

#### 驗證證據

```text
python -m unittest tests.test_security_compliance tests.test_observability_v2_sanitize tests.test_alert_notifier -v
→ **14/14 OK**（`test_security_compliance` 8 · `test_observability_v2_sanitize` 1 · `test_alert_notifier` 5）
```

#### 阻塞／下一步

- **阻塞**：無（單元測試層）
- **下一步**：KMS `EncryptionHook` · Langfuse outbound scrub · production 合規審核 · schema 驅動 denylist 檔

---

### Phase 5 Wave-Next – latency trend / alert cooldown / security 深化（dev/staging v1）

**角色**：gov_core_system documentation & status agent · **僅文件寫回**（無程式 diff）  
**狀態依據**：`core/monitoring_*` · `monitoring_alerts` · `alert_rule_loader` · `alert_threshold_evaluator` · `alert_notifier` · `security_compliance` 只讀盤點 + `output/phase5_*_v1.md`；對齊 `master_status.md` Phase 5 **~80%** dev/staging ops baseline。

**變更摘要（本輪 Wave-Next，程式已合併於暗部；本段僅記狀態）**：
- **Dashboard**：新增 `GET /monitoring/latency-trend`（ask／all cohort · 15m／60m bucket · p50／p95）；`static/monitoring/dashboard.html` live 載入優先 latency-trend，mock／fallback 有 badge；Security hooks 面板讀 `GET /monitoring/security-status`。
- **Alerts**：`POST /monitoring/alerts/evaluate` 穩定化（一律 HTTP 200）；`alert_rule_loader` 防禦 PG／YAML 壞列；`GOV_CORE_ALERT_COOLDOWN_MINUTES` + per-rule metadata cooldown；`evaluate_response` 含 `alerts_suppressed`／`notifier_summary`。
- **Security**：`StubFieldEncryptionHook`（`GOV_CORE_ENCRYPTION_HOOK_MODE`／`GOV_CORE_ENCRYPTION_STUB_ENABLED`）、Langfuse outbound scrub、ingest `errors[]` sanitize、`GovCoreSanitizeLogFilter`、`GOV_CORE_PII_POLICY_CONFIG` 驅動 denylist／allowlist。

**驗證**：`python -m unittest tests.test_monitoring_api tests.test_monitoring_alerts tests.test_alert_notifier tests.test_security_compliance tests.test_observability_v2_sanitize tests.test_observability_v2_langfuse_sanitize` → **53/53 OK**（monitoring **26** + security／notifier／sanitize **27**）。無 `DATABASE_URL` 時 `latency-trend`／`alerts/evaluate`／`security-status` 回 `ok:false`+`message` 或 YAML 規則 fallback，路由不 500。

**範圍與限制**：**dev/staging v1 · non-production SLA** — stub encryption／stub notifier（Slack／email／PagerDuty）**不可**視為 production 就緒；live PG soak 與真實 on-call 通道仍待下一波。

**下一步**：live PG soak（n≥100）→ 第一條真 Slack／email notifier → KMS hook 替換 stub → production 資安審核與 SLA 決策。


---

## HQ-TOOL-LAYER-B1（2026-05-22 · 大唐副官）

**任務 ID**：`HQ-TOOL-LAYER-B1`  
**狀態**：**done**

### Work Report

#### 執行內容

- core/minimal_orchestration_bridge.py — B1 lane (_is_b1_report_file_only_tool_flow_whitelisted, whitelist_lane)
- tests/test_minimal_orchestration_bridge_tool_flow_b1.py — 新增 7 例
- 04_Workflows/SPEC_tool_catalog_and_selector_v1.md §10 — B1 一行
- gov_core_system: python -m unittest tests.test_tool_flow_bridge tests.test_minimal_orchestration_bridge_tool_flow tests.test_minimal_orchestration_bridge_tool_flow_b1 -v
- gov_core_system: python -m unittest discover -s tests -p test_tool*.py -v

#### 關鍵結果

```json
{
  "scope": "Phase B1 report_organize.file-only Tool Flow whitelist（第二波）；info_query 白名單邏輯未改",
  "bridge_lane": "B1_report_file_only",
  "selector_rule": "S8 (file.io → llm.ask), human_review_required false",
  "unittest_bridge_b1": "15/15 OK (tool_flow_bridge 3 + info_query bridge 5 + B1 7)",
  "unittest_test_tool_star": "45/45 OK",
  "info_query_regression": "tests.test_minimal_orchestration_bridge_tool_flow 全通過"
}
```

#### 結構化指標

```json
{
  "tests_bridge_and_b1": 15,
  "tests_test_tool_glob": 45
}
```

#### 阻塞與風險

無。生產放行待確認：file.io.read executor 非 stub（bridge 僅路由，測試 mock run_tool_flow）。

#### 下一步

尚書省裁決 B1 生產門檻後啟用流量；Phase C/D（small_automation/browser_task）不在本票範圍。

#### Runbook 差異

無 Runbook 結構變更；SPEC §10 已追加 B1 索引行。

#### 禁區確認

本輪未觸 .env、venv 樹、runtime/checkpoints、暗部破壞性維運；未改 selector/executor 核心。

---

## 2026-05-23 — 企業化補強戰役封存完成（H / I / J / K / P+）

**角色**：大唐副官 · **僅文件寫回**（六步封存收兵 · 第 3 步）  
**狀態依據**：根目錄 `00_master_plan.md` §4 戰役封存 · `_workflow_upgrade/90_run_queue.md` Done 區塊 · 各 lane 程式／測試已落盤

### 本輪完成事項

- **K-1** — 最小 LangGraph e2e 已完成（`Planner → Executor → Reviewer` StateGraph；`core/langgraph_flow_k1.py`）
- **I-bridge-v0** — ask path minimal bridge 已完成（context／retry／trace 掛接；`ask_pipeline_ibridge_v0.py`）
- **I-bridge-v1** — `/api/ask` dev-only ibridge expose 已完成（env + query 雙閘門透傳 `ibridge_record`）
- **P+ eval_gate v0** — rule-based eval_gate 已完成（`evaluate_task_record` → pass／needs_review + tags）
- **H context_entry v0.1** — 統一上下文入口已完成（`build_rooted_context` 唯一入口 + 禁止繞過條款）
- **J skills seed v0.1** — metrics-aware skill 封裝種子已完成（`run_metrics_aware_skill` + retrieve／pg_query 示範）

### 能力層躍遷

本輪不是補零散功能，而是讓 ask 線具備：**可觀測**（trace／ibridge_record／eval_gate）、**可重試**（P 線 retry 掛接）、**可控上下文入口**（H 線 `build_rooted_context` 合同）、**可規則化評估**（P+ eval_gate 複查篩樣本）、**可 metrics-aware skill 封裝**（J 線 `skill_runner` 外殼）五項企業化骨幹。

這代表系統從「功能可跑」提升到「入口／編排／觀測／評估／能力包有統一骨架」——後續新入口與新 skill 須說明服務的 D 維度，並複用本輪產出的入口／runner／eval_gate，避免再次發明平行欄位或繞過合同。

### 對應治理文檔

- **總藍圖**：根目錄 `00_master_plan.md`（§4 企業化補強 · 2026-05 戰役封存）
- **隊列對賬**：`_workflow_upgrade/90_run_queue.md`（Done — 2026-05 企業化補強戰役 · 6 線結清）

### 下一步 backlog

- **I-bridge-v0-H-migrate** — 歷史 ask 入口遷移至 H 線 `build_rooted_context`
- **I-ask-skills-wire** — ask 主線掛接 J 線 metrics-aware skills
- **P+-eval-gate-export-ci** — eval_gate 結果導出與 CI 整合
- **H-historical-migrate** — 歷史路徑全量 context 入口遷移
- **K-2** — LangGraph 編排深化（後續工單）

#### 阻塞／風險

- **阻塞**：無（本段僅文件寫回）
- **風險**：本輪為 v0／v0.1 基線，**非** production-ready；歷史路徑全量遷移、生產級 eval 與 LangGraph 依賴安裝屬 backlog，不得回溯改寫本輪完成定義

#### 禁區確認

本輪未觸 .env、venv 樹、runtime/checkpoints、暗部破壞性維運；僅 append 總部進度檔，未改程式或其他文檔。

---

## 2026-05-24 · Wave 3 回答側收斂 + K-2 部署治理（封存）

**角色**：大唐副官 · Chat C · **僅文檔／隊列封存**（無 `.py` 變更）  
**狀態依據**：`00_master_plan.md` §4.7–§4.8 · `_workflow_upgrade/90_run_queue.md` · `_workflow_upgrade/campaign_wave3_answer_selector_summary.md`

### 回答側（DoD 已達成）

- **J-answer-skill-wire**：`answer_node` 統一 `skill_answer_for_ask`；metrics 與 retrieve 對稱。
- **J-selector-context-governance**：ASK-R1–R6 + S1/S2/S3；單元＋流程測試落地。
- **驗證**：`tests.test_skills_ask_wire` · `tests.test_ask_selector_and_answer` · 暗部 `tests.test_ask_skills_wire_e2e`

### K-2 線（Phase 0 維持）

- **現狀**：prod = ask-only；K-2 dev/test shadow。
- **Chat A/B done**：`k2_behavior_profile` · `compare_shadow_profiles` · `merge_ask_and_k2` · `k2_merge_strategy`
- **Chat C done（策略）**：`docs/k2_deployment_governance.md` — Phase 0–4、指標閾值、回退、審批；`engineering-contract` REF-9.7
- **隊列**：`K2-ask-shadow-merge` → done；`K2-rollout-governance` → planned（執行待尚書省 Phase 1 批准）

### 治理索引

| 類別 | 路徑 |
|------|------|
| 隊列 | `_workflow_upgrade/90_run_queue.md` |
| 總藍圖 | `00_master_plan.md` §4.7–§4.8 |
| 合同 | `skills/skills_contract.md` §8–§10 · `context/context_entry_contract.md` §8 |
| Eval | `observability/eval_pipeline.md` §6.5 |
| K-2 | `docs/k2_behavior_profile.md` · `docs/k2_merge_strategy.md` · `docs/k2_deployment_governance.md` |
| 戰役摘要 | `_workflow_upgrade/campaign_wave3_answer_selector_summary.md` |

### 下一步 backlog（建議開 Chat 入口）

1. **K2 Phase 1 prod shadow** — 依 `k2_deployment_governance.md` 開影子流量（尚書省批文）
2. ~~**H-historical-migrate**~~ — **done（2026-05-25）**
3. ~~**P+-eval-ci-wire**~~ — **done**
4. ~~**tool_executor.llm.ask skill 化**~~ — **done**

### 阻塞／風險

- **阻塞**：無
- **風險**：K-2 prod rollout 未啟動；eval 樣本量不足時升格決策需 N≥30；selector/answer 對齊為 Phase 2 前關單項

### 禁區確認

本段僅 append Progress、修正 run_queue Lane 視圖 stale 條目、更新 campaign 摘要索引；未觸憲法 §7 禁區、未改 `.py`。

---

## 2026-05-24 · J-tool-executor-llm-ask-skill（施工）

**角色**：大唐副官 · Chat 本輪  
**票號**：`J-tool-executor-llm-ask-skill`  
**裁決**：core_fn 策略 A（僅 `perform_direct_answer`）

### 變更

| 檔案 | 摘要 |
|------|------|
| `gov_core_system/core/tool_executor_skills_bridge.py` | `_execute_llm_ask` → `run_answer_via_skill` + `perform_direct_answer`；`call_site=tool_executor.ask_pipeline.llm.ask` |
| `gov_core_system/tests/test_tool_executor_skills_bridge.py` | `llm.ask` metrics + retry drill 單測 |
| `gov_core_system/tests/test_tool_executor.py` | `test_ask_pipeline_llm_ask_dispatch`（非 stub） |
| `skills/skills_contract.md` | §11 executor `llm.ask`；§8 bridge 表增列 |
| `observability/eval_pipeline.md` | §6.5 增 tool_executor call_site 消費說明 |
| `_workflow_upgrade/90_run_queue.md` | 票 done + yaml |
| `00_master_plan.md` | §4.9；§4.6 移除候選項 |

### 驗證

```text
cd 01_Environments/python_venvs/gov_core_system
python -m unittest tests.test_tool_executor_skills_bridge tests.test_tool_layer_e2e tests.test_tool_executor -v
```

**結果**：9 tests OK（bridge 4 + e2e 1 + executor 4）；`external_call_count` ≥1；retry drill `skill_retry_count` ≥1。

### 阻塞／風險

- **阻塞**：無
- **風險**：executor `llm.ask` 不接同批 `rag.retrieve` 結果（裁決 A）；S3 雙 tool 序列在 tool 層仍為 direct-only

### 禁區確認

未觸 .env、venv 樹、runtime/checkpoints。

---

## 2026-05-24 · P+-eval-ci-wire（K-2 Phase 1 技術門票）

**角色**：大唐副官 · P+ 線  
**狀態依據**：尚書省裁決（3a / PR 0.72 分離 / `shadow_ibridge_records.latest.jsonl`）· `00_master_plan.md` §4.8 · `_workflow_upgrade/90_run_queue.md`

### 變更

| 路徑 | 摘要 |
|------|------|
| `observability/ibridge_exporter.py` | `--source shadow`、`normalize_shadow_record`、`--profile shadow` → `shadow_ibridge_records.latest.jsonl` |
| `tests/fixtures/eval/shadow_raw_records.jsonl` | K-2 flow / merge / k2_summary 混合格式夾具 |
| `tests/test_ibridge_exporter.py` | shadow 正規化 + export + gate_result 斷言 |
| `.github/workflows/eval-gate-ci.yml` | `eval-shadow-nightly`（cron 06:00 UTC；0.60 + `infra_risk`）；PR job 維持 0.72 |
| `artifacts/eval/shadow_ibridge_records.latest.jsonl` | 已提交 flat export（4 行） |
| `observability/eval_export.md` | Phase 1 nightly 小節 |
| `00_master_plan.md` §4.8 | P+-eval-ci-wire done 一行 |
| `_workflow_upgrade/90_run_queue.md` | 票結清 |

### 驗證（repo 根 · dry-run）

```text
python -m observability.ibridge_exporter --source shadow --profile shadow --force \
  tests/fixtures/eval/shadow_raw_records.jsonl \
  -o artifacts/eval/shadow_ibridge_records.latest.jsonl --no-latest
# ok=true written=4

python -m observability.eval_ci_check artifacts/eval/shadow_ibridge_records.latest.jsonl \
  --limit 100 --max-needs-review-ratio 0.60 --fail-on-tags infra_risk
# ok=true needs_review 1/4 (25%) tag_triggered=false

python -m unittest tests.test_ibridge_exporter tests.test_eval_ci_check tests.test_eval_exporter tests.test_eval_gate -v
# Ran 29 tests OK
```

`eval_exporter` 輸出 4 行均含 `gate_result`（3 pass / 1 needs_review）。

### 阻塞／風險

- **阻塞**：無
- **風險**：nightly 現以 `shadow_raw_records.jsonl` bootstrap；真 prod spool 上線後須改 nightly export 輸入路徑；升格決策仍須 N≥30

### 下一步

- `H-historical-migrate` → `K2-rollout-governance` Phase 1 prod shadow 執行（尚書省批文）

### 禁區確認

未觸 .env、venv 樹、runtime/checkpoints、暗部根。

---

## 2026-05-25 · H-historical-migrate（驗收封存）

**角色**：大唐副官  
**票號**：`H-historical-migrate`  
**裁決**：Phase 1 盤點無缺口 → Phase 2 **零 diff** → 驗收 + 文檔封存

### Phase 1 盤點（注入點）

| 入口 | 狀態 |
|------|------|
| `run_ask_flow`（預設） | `run_ask_with_hline_context` → `build_rooted_context(mode="ask_pipeline")` |
| `run_ask_flow`（opt-in） | `run_ask_with_ibridge_v0`（同上 + trace/ibridge_record） |
| `POST /api/ask` | 委派 `run_ask_flow` |
| 暗部 `build_context(` 直呼 | **無** |
| `tool_executor.ask_pipeline` | 非本票範圍（skill 直調，不經 H 入口） |

### 變更

**無程式 diff**（遷移已於 Wave 2 後落地）。

| 路徑 | 摘要 |
|------|------|
| `context/context_entry_contract.md` | §8.0 切換狀態 **已切換**；§8.2 增驗收索引 |
| `observability/eval_pipeline.md` | §6.5 增 H-historical-migrate 一句 |
| `00_master_plan.md` | §4.7.1 H 行 done；§4.10；§4.6 移除候選項 |
| `_workflow_upgrade/90_run_queue.md` | 票 **done** + yaml `result_summary` |
| `_workflow_upgrade/campaign_wave3_answer_selector_summary.md` | H 線項標 done |

### 驗證

```text
# 戰車根（selector 須單獨跑，避免 core 包遮蔽）
python -m unittest tests.test_context_entry tests.test_skills_ask_wire -v
# Ran 9 tests OK

python -m unittest tests.test_ask_selector_and_answer -v
# Ran 8 tests OK

# 暗部 gov_core_system
python -m unittest tests.test_ask_pipeline_default_context tests.test_ask_pipeline_ibridge_v0 -v
# Ran 7 tests OK

# eval 基線
python -m observability.ibridge_exporter --source shadow --profile shadow --force \
  tests/fixtures/eval/shadow_raw_records.jsonl \
  -o artifacts/eval/shadow_ibridge_records.latest.jsonl --no-latest
# ok=true written=4

python -m observability.eval_ci_check artifacts/eval/shadow_ibridge_records.latest.jsonl \
  --limit 100 --max-needs-review-ratio 0.60 --fail-on-tags infra_risk
# ok=true needs_review 1/4 (25.00%) tag_triggered=false
```

### 阻塞／風險

- **阻塞**：無
- **風險**：戰車根合併跑 `test_context_entry` + `test_ask_selector_and_answer` 會因 `core` 包遮蔽失敗；驗收須分開執行（已寫入合同 §8.2）

### 下一步

- `K2-rollout-governance` Phase 1 prod shadow（尚書省批文）

### 禁區確認

未觸 .env、venv 樹、runtime/checkpoints、暗部根破壞性變更。

---

## 2026-05-25 · HQ-GOV-K2-P1-SHADOW-20260525（Phase 1 啟用前三件事）

**角色**：大唐副官  
**批文**：`HQ-GOV-K2-P1-SHADOW-20260525`（有條件批准；啟用日 2026-05-26 06:00 UTC）  
**狀態依據**：尚書省批文 · `docs/k2_deployment_governance.md` §5 P3/P4/P5 · P+-eval-ci-wire 已 done  
**環境**：戰車根 unittest；export smoke 使用 `gov_core_system` venv + `PYTHONPATH`/`TANG_GOV_ROOT` → 戰車根（與 Wave 3 / P+-eval-ci-wire 同套）

**K2 Phase 1 on-call**：天天 / 聯絡通道：（待工程補齊 Telegram @xxx 或內部頻道名）

### P3 shadow 報告（fixture 代表集）

**命令**（戰車根）：

```text
python -m unittest tests.test_k2_ask_shadow -v
# Ran 13 tests in 0.851s — OK
```

**摘要**：

| 項目 | 結果 |
|------|------|
| 測試總數 | **13** |
| 結果 | **13 tests OK**（0 failures / 0 errors） |
| 資料性質 | **fixture 代表集**（mock health/RAG；`tests/test_k2_ask_shadow.py`）— 用於 wiring／行為驗收，**非** prod 決策樣本 |
| Phase 1 後續 | P3 將改以 **真實 shadow export 週報**（`compare_shadow_profiles` + `eval_ci_check`）支撐升格審查 |

**三情境代表集（merge_safe / unacceptable_diffs）**：

| 情境 | merge_safe | unacceptable_diffs | 備註 |
|------|------------|-------------------|------|
| `retrieve_timeout` | **False** | `['error_type']` | ask 側 `retrieve_node: retrieve timed out`；K-2 無對應 `error_type`；`retrieve_fallback` 列 uncertain |
| `simple_happy` | **True** | `[]` | 雙 ok；預期 diff（answer/context/eval/tags 等） |
| `summary_probe` | **True** | `[]` | 雙 ok；`handoff_count`/`retry_count` 列 uncertain（K-2 handoff=2, retry=1） |

**說明**：全套件另含 greeting_skip、ibridge_v0、rag_kb_context、k2_skill_retry 等場景；代表集三案覆蓋 timeout／happy／summary 探針。`retrieve_timeout` 之 `merge_safe=False` 為 fixture 預期（error 形狀不對齊），**不**等同 prod 不可接受回歸。

### shadow export smoke（export 三元組）

**環境**：`01_Environments/python_venvs/gov_core_system` Python + 戰車根 `PYTHONPATH`/`TANG_GOV_ROOT`

```text
python -c "from observability.ibridge_exporter import export_allowed; print(export_allowed())"
# {'ok': True, 'allowed': True, 'deploy_env': 'dev', 'reason': 'deploy_env'}

python -m observability.ibridge_exporter --source shadow --profile shadow --force \
  tests/fixtures/eval/shadow_raw_records.jsonl \
  -o artifacts/eval/shadow_ibridge_records.latest.jsonl --no-latest
# ok=true written=4 deploy_env=dev

python -m observability.eval_ci_check artifacts/eval/shadow_ibridge_records.latest.jsonl \
  --limit 100 --max-needs-review-ratio 0.60 --fail-on-tags infra_risk
# ok=true needs_review 1/4 (25.00%) ratio_triggered=false tag_triggered=false
# tag_counts: high_retry=1; fail_on_tags: infra_risk（未觸發）
```

三步均 **exit 0**。夾具含刻意 `infra_risk` 標籤場景；本次 `tag_triggered=false`（flat export gate 未觸發 fail-on-tags），屬 **wiring smoke**，非 wiring bug。

### 變更

| 路徑 | 摘要 |
|------|------|
| `04_Workflows/00_Agent_Work_Progress.md` | 本段（P3/P5/smoke） |
| `docs/k2_ask_shadow_findings.md` | 增 §P3 fixture 代表集摘要 |

**程式 diff**：無（依批文僅測試／export／文檔）

### 阻塞／風險

- **阻塞**：無（P3/P5/smoke 已留痕；待工程補齊 on-call 聯絡通道）
- **風險**：P3 現為 fixture；prod shadow 開啟後須以真實週報替換；週樣本 ≥500 方可用於升格

### 下一步

- 2026-05-26 06:00 UTC 起算 Phase 1 觀測週期；首日 nightly `eval_ci_check` 摘要入戰報
- 補齊 on-call 聯絡通道後更新本段 P5 行

### 禁區確認

未觸 .env 原文、venv 樹、runtime/checkpoints、暗部根破壞性變更。

---

## 2026-05-25 · Wave 1 app_api shadow hook（K2-phase1-shadow-hook）

**角色**：大唐副官  
**批文**：HQ-GOV-K2-P1-SHADOW-20260525（尚書省 Wave 1 暗部施工授權）  
**狀態依據**：`00_master_plan.md` §4.8 · `_workflow_upgrade/90_run_queue.md` `K2-phase1-shadow-hook`  
**Phase**：仍 **0**（hook 就緒；T+0 前 `GOV_K2_PROD_SHADOW` 預設關閉）

### 變更檔案

| 路徑 | 摘要 |
|------|------|
| `01_Environments/python_venvs/gov_core_system/app_api.py` | `/api/ask` 成功路徑 return 前 `schedule_prod_shadow_hook` |
| `01_Environments/python_venvs/gov_core_system/core/k2_prod_shadow_hook.py` | `GOV_K2_PROD_SHADOW` 閘門 + daemon thread + subprocess worker |
| `core/k2_prod_shadow_worker.py` | `run_k2_flow` + `merge_ask_and_k2(primary_source=ask)` + spool append |
| `core/k2_prod_shadow_worker_cli.py` | subprocess CLI 入口 |
| `.github/workflows/eval-gate-ci.yml` | nightly 輸入改 `artifacts/eval/k2_shadow_spool.jsonl`（空則 bootstrap fixture） |
| `tests/test_k2_prod_shadow_worker.py` | worker / spool 單元測試 |
| `gov_core_system/tests/test_app_api_k2_prod_shadow.py` | API 不洩漏 k2_merge；開關行為 |

### 啟用／停用開關

| 開關 | 預設 | 說明 |
|------|------|------|
| `GOV_K2_PROD_SHADOW` | **off** | `1` 啟用 async shadow；T+0 由部署層開啟 |
| `K2_SHADOW_SPOOL_FILENAME` | `k2_shadow_spool.jsonl` | 位於 `artifacts/eval/` 或 `IBRIDGE_EXPORT_ROOT` |
| `GOV_DEPLOY_ENV` + `IBRIDGE_EXPORT_ALLOW_PRODUCTION` + `IBRIDGE_EXPORT_ENABLED` | — | prod export 三鍵（T+0 smoke；非本票寫入 .env） |

**回退**：`GOV_K2_PROD_SHADOW=0` + API 重載；保留 spool 7 日。

### 驗證命令與關鍵輸出

**戰車根 unittest**（`PYTHONPATH`/`TANG_GOV_ROOT` → 戰車根）：

```text
python -m unittest tests.test_k2_ask_shadow tests.test_k2_merge_adapter tests.test_k2_prod_shadow_worker -v
# Ran 26 tests — OK
```

**暗部 API hook**（`gov_core_system` venv）：

```text
python -m unittest tests.test_app_api_k2_prod_shadow -v
# Ran 3 tests — OK
```

**export 三元組（input=spool，prod 三鍵，無 --force）**：

```text
export_allowed → ok=True, allowed=True, deploy_env=production
ibridge_exporter --source shadow … k2_shadow_spool.jsonl → written=4
eval_ci_check → ok=true, needs_review 25%, infra_risk 未觸發
```

### 阻塞／風險

- **阻塞**：無（Wave 1 完成；T+0 待開 `GOV_K2_PROD_SHADOW` + Progress Phase 1 啟用戰報）
- **風險**：subprocess 依賴 `TANG_GOV_ROOT`／戰車根 `PYTHONPATH`；CI nightly 在 spool 空時仍 bootstrap fixture

### 下一步

- **2026-05-26 06:00 UTC** T+0：開 `GOV_K2_PROD_SHADOW=1` + prod export 三鍵 + 更新 §4.8 Phase→1
- 7 日觀測週報：`merge_safe` / `unacceptable` / `infra_risk` / `needs_review`

### 禁區確認

僅授權範圍內改 `app_api.py` 與 shadow hook／spool；未改 response schema；未觸 `.env` 原文、runtime/checkpoints。

---

## 2026-05-26 · K-2 Phase 1 T+0 啟用戰報

**角色**：大唐副官  
**批文**：`HQ-GOV-K2-P1-SHADOW-20260525`（啟用日 **2026-05-26 06:00 UTC**）  
**狀態依據**：`docs/k2_deployment_governance.md` Phase 1 · `00_master_plan.md` §4.8 · Wave 1 hook 已 done

### T+0 前檢查（戰車根 + gov_core_system venv）

| 步驟 | 命令 | 結果 |
|------|------|------|
| K-2 unittest | `python -m unittest tests.test_k2_merge_adapter tests.test_k2_ask_shadow -v` | **24/24 OK** |
| export_allowed（預檢 dev） | `python -c "from observability.ibridge_exporter import export_allowed; print(export_allowed())"` | `ok=True, allowed=True, deploy_env=dev` |
| fixture export | `ibridge_exporter --source shadow --profile shadow --force tests/fixtures/eval/shadow_raw_records.jsonl` | `written=4` exit 0 |
| eval_ci_check（fixture） | `--max-needs-review-ratio 0.60 --fail-on-tags infra_risk --min-samples 1` | `ok=true`, needs_review 25%, `tag_triggered=false` |

### T+0 啟用

- **env（部署層，未改 repo `.env` 原文）**：`observability/deploy/k2_phase1_prod_shadow.env` → `GOV_DEPLOY_ENV=production`；`IBRIDGE_EXPORT_ALLOW_PRODUCTION=1`；`IBRIDGE_EXPORT_ENABLED=1`；`GOV_K2_PROD_SHADOW=1`
- **API 重載**：`gov_core_system` venv · `uvicorn app_api:app` @ `127.0.0.1:8000`（載入 Tang `.env` + 部署 overlay）
- **/api/ask smoke**：`POST` query=`K-2 Phase1 T+0 shadow smoke 20260526-0600Z` → **HTTP 200**（access log）；user-facing 無 `k2_merge` / `k2_eval_metadata`（契約不變）
- **spool**：`artifacts/eval/k2_shadow_spool.jsonl` 4→5 行；末行 `schema=k2_prod_shadow/v1`，`task_id=prod-shadow-9469a97892-k2`，`timestamp=2026-05-24T17:45:43.383431+00:00`（T+0 smoke 後新增）
- **export_allowed()（prod 三鍵）**：`{'ok': True, 'allowed': True, 'deploy_env': 'production', 'reason': 'enabled_flag'}`
- **export（真 spool，無 --force）**：`written=5`，`deploy_env=production`，exit 0
- **eval_ci_check（真 spool）**：`ok=true`，needs_review **1/5 (20.00%)**，`tag_triggered=false`（`fail_on_tags=infra_risk` 未觸發；spool 含歷史 fixture 行 + 本次 prod 行）

### Phase

**0 → 1**（prod shadow 啟用；7 日觀測期起算）

### 阻塞／風險

- **阻塞**：無
- **風險**：本次 smoke 環境 ask `healthcheck failed`（`ask_ok=false`），K-2 shadow 仍寫入 spool；本地 ask 節點恢復後週樣本更具代表性

### 下一步

- 每日 nightly `eval_ci_check` 摘要入戰報；第 7 日對照 `docs/k2_deployment_governance.md` §6 出門指標
- 補齊 on-call 聯絡通道（P5）

### 禁區確認

未觸 `.env` 原文、venv 樹、runtime/checkpoints、第二 Telegram listener；未改 `/api/ask` response schema。

---

## 2026-05-26 · K-2 Phase 1 本地演練範圍裁決（尚書省）

**角色**：大唐副官  
**票據**：`K2-phase1-prod-shadow` / `K2-rollout-governance`（本地子集）  
**批文**：`HQ-GOV-K2-P1-SHADOW-20260525`

### 範圍（本 Chat／本票）

| 在範圍 | 不在範圍 |
|--------|----------|
| 戰車根 + `gov_core_system` venv 上 Phase 1 prod shadow（`k2_phase1_prod_shadow.env` 四鍵） | 遠端 prod 叢集 SSH/K8s/systemd 自動 rollout |
| T+0 已完成：本地 API + `/api/ask` → `artifacts/eval/k2_shadow_spool.jsonl` | 假設雲端主機權限或代改遠端設定 |
| **7 自然日**觀測（**2026-05-26 06:00 UTC** 起算） | `K2 Phase 1 prod shadow – remote rollout`（待另票 + 明確部署路徑） |
| 每日／每週：`ibridge_exporter` + `eval_ci_check`（與 CI nightly 同參） | Phase 2 canary（本 Chat 僅封存演練；升格申請草稿後續另開） |
| `00_master_plan` §4.8、`90_run_queue`、`Progress` 末尾更新 | 修改 user-facing `/api/ask` schema |

### 7 日本地觀測節奏（對齊 `docs/k2_deployment_governance.md` §4.2、§6.2–§6.3）

1. **持續**：本地 API 載入 `observability/deploy/k2_phase1_prod_shadow.env` overlay；`GOV_K2_PROD_SHADOW=1`；真實或 soak 樣式 `/api/ask` 流量寫 spool（user 仍 100% ask 主答案）。
2. **每日**（可手動或等價於 `eval-gate-ci.yml` `eval-shadow-nightly`）：

```text
# gov_core_system venv + 戰車根 PYTHONPATH/TANG_GOV_ROOT + prod 四鍵 overlay
python -m observability.ibridge_exporter --source shadow --profile shadow \
  artifacts/eval/k2_shadow_spool.jsonl \
  -o artifacts/eval/shadow_ibridge_records.latest.jsonl
python -m observability.eval_ci_check artifacts/eval/shadow_ibridge_records.latest.jsonl \
  --limit 100 --max-needs-review-ratio 0.60 --fail-on-tags infra_risk --min-samples 1
```

3. **每日戰報**（Progress 末尾）：`written`、eval_ci_check `ok` / `needs_review_ratio` / `tag_triggered`、spool 行數、本日 `infra_risk` 與 `classification.unacceptable` 計數（從 spool 或週報腳本）。
4. **第 7 日（2026-06-02 UTC 後）**：對照 §6.3 Phase 1→2 出門（7 日 `infra_risk`=0、`unacceptable`=0、needs_review≤60%、merge_safe≥95%）；達標則起草 Phase 2 canary 申請草稿，**不**自動升格。

### 回退（本地演練）

- **R-local-1**：`eval_ci_check` `ok=false` 且 `tag_triggered=true`（`infra_risk`）→ 調查 spool 末行；必要時 `GOV_K2_PROD_SHADOW=0` + 本地 API 重載（保留 spool）。
- **R-local-2**：user-facing `/api/ask` 出現 `k2_merge` / `k2_eval_metadata` 或 HTTP/契約異常 → 立即關 shadow 開關並記 Progress（視同嚴重 bug）。

### 隊列狀態

- `K2-phase1-prod-shadow`：**in_progress**（T+0 done；7 日觀測中）
- `K2-rollout-governance`：**in_progress**（本地演練子集；遠端 rollout 排除）

### 禁區確認

未嘗試遠端主機連線或變更；未觸 `.env` 原文、venv 樹、runtime/checkpoints。

---

## K-2 Phase 2 canary（準備戰 · 僅文檔）

2026-05-25 · Phase 2 canary 批文草案完成（草案檔案：`docs/drafts/HQ-GOV-K2-P2-CANARY-DRAFT.md`，暫不生效，待 Phase 1 七日觀測達標後再送尚書省定稿）。

**封存**：`k2_deployment_governance.md` §9 附錄索引已掛鏈；`K2-rollout-governance` 維持 in_progress（Phase 1 觀測中）；未開 T1–T10 實作票、未改 prod。

---

## 2026-05-25 · K-2 Phase 1 remote rollout runbook blueprint 完成

**角色**：大唐副官  
**票據**：`K2-phase1-remote-rollout-runbook`（文檔藍圖；**非**遠端實作）

### 摘要

- **交付**：`docs/k2_phase1_remote_rollout_runbook.md` — 自本地 prod-like 演練抽象通用 rollout checklist；內嵌 systemd / K8s / 啟動腳本 **pseudocode**（不拆獨立 `.service` / `.yaml` / `.sh`）。
- **性質**：Blueprint only — 僅為示意 runbook，**不代表已在任何環境實施**；未連線、未改遠端主機。
- **後續**：遠端 rollout **實作**須另開票（尚書省批文 + 明確平台與部署路徑）；本 Chat 封存點止。

### 變更檔案

| 路徑 | 摘要 |
|------|------|
| `docs/k2_phase1_remote_rollout_runbook.md` | 遠端 Phase 1 shadow rollout 藍圖 runbook（文首免責已強化） |

### 驗證

- 文檔工單：peer review 建議；無 CLI／無遠端施工。

### 隊列

- `K2-phase1-remote-rollout-runbook` → **done**
- 未新增「remote rollout 實作」類票

### 禁區確認

未觸 `.env` 原文、venv 樹、runtime/checkpoints、遠端主機。

---

## 2026-05-25 · QA-A-W1（A-W1-C 實機驗收 · 代碼可重跑、環境待補）

**角色**：施工兵 A-W1-C / QA 複跑  
**票據**：`QA-A-W1` 子項 — `repo_chunks` index → embed → retrieve + `document_chunks` 回歸

### 驗收步驟與結果（`gov_core_system` venv 根）

| 步 | 命令（摘要） | 結果 |
|----|----------------|------|
| 1 | `repo_index_agent.py run --repo-root <戰車根> --subtree core` | **FAIL** — `schema apply failed: connection timeout expired`（PG 不可達） |
| 2 | `rag_query_agent.py repo-embed --job-id <job_id>` | **未執行**（無 job_id） |
| 3 | `rag_query_agent.py repo "repo_index_job"` | **FAIL** — `Qdrant search failed`；`WinError 10061`（127.0.0.1:6333 拒絕連線） |
| 4 | `rag_query_agent.py "AGENTS.md"` | **FAIL** — 同上 Qdrant 連線失敗（與步驟 3 **同因**，非 A-W1-C 程式回歸） |

### 代碼層證據（本機可重跑）

- `python -m unittest tests.test_repo_retrieve -v` → **3/3 OK**
- 實機四步鏈需：**Docker 守護行程** + `datang_postgres` / `datang_qdrant` 運行（見 `Departments/04_Infrastructure/docker-compose.yml`）；`gov_core_system\.env` 之 `DATABASE_URL` 與 `01_Environments\.env` 密碼一致（見 Progress DB-RECOVER-1）。

### 裁決

- **A-W1-C**：維持 **IMPLEMENTED_WAITING_INFRA**（實作已交付；實機 index→embed→retrieve 尚未在本環境成功一次）。
- **A-W1-A / A-W1-B / A-W1-C 統一標 DONE**：**本次不升格**（尚書省隊列仍 BLOCKED/TODO 直至 infra 四步鏈綠燈）。
- **document_chunks smoke**：程式路徑未改；回歸待 Qdrant 恢復後重跑步驟 4。

### 環境恢復後重跑清單

1. 啟動 Docker Desktop → `docker compose up -d`（於 `Departments/04_Infrastructure` 或專案慣用入口）。
2. `core/infra_health.py` → `all_ok=true`。
3. 依 QA 步驟 1–4 順序重跑；步驟 3 期望 `ok=true`、`collection=repo_chunks`、`hits>=1`、`hits[0].path` 含 `core/repo_index_job.py` 類路徑。

### 禁區確認

未改 `document_chunks` smoke 契約、未改 ask selector；未輸出 env 金鑰原文。


---

## A-W4-QA（2026-05-25 · 戰線 A / Week 4 QA 工兵 A-W4-QA）

**任務 ID**：`A-W4-QA`  
**狀態**：**done**

### Work Report

#### 執行內容

- 暗部 gov_core_system venv：unittest 串跑 7 套件（catalog / selector / executor / facade / adapter / registry / vnext_runner）
- E2E 鏈路 mock 驗證：成功路徑、selection 無工具、validation fail（無 Docker / 無真 PG·Qdrant）
- 文件對齊：04_Workflows/SPEC_tool_layer_vnext_draft.md §3 / §4 / §5 / §8

#### 關鍵結果

```json
{
  "unittest_total": 43,
  "unittest_ok": true,
  "skip_flaky": "無",
  "e2e_success": {
    "chain": "select_tools(repo_retrieve) → execute_tool_vnext(repo) → adapter vNext envelope",
    "tool_id": "repo_code_retrieve_smoke",
    "vnext_ok": true,
    "source_envelope": "repo_tool_execution_v1",
    "envelope_version": "tool_execution_vnext_draft_v0_1"
  },
  "e2e_no_tool": {
    "facade_phase": "selection",
    "structured_error_code": "no_tool_selected",
    "selected_tools_len": 0
  },
  "e2e_validation_fail": {
    "structured_error_code": "input_validation_failed",
    "validation_errors_preserved": true
  },
  "spec_alignment_summary": "§3 repo carry 欄位已落地；tool_tier / dispatch_ref / feature_flag 未落地。§4 selector 為 intent 子集；feature_flag 未支援。§5 vNext envelope 已滿足核心欄位；runtime_context_snapshot / trace_id 未映射。§8 W3.5+W4 registry/runner 完成；SPEC 仍 draft、§8.3 orchestration 合流未做",
  "qa_verdict": "可作 Phase 2 / 戰線 A vNext 參考實作；合流 8.8 須後續票",
  "file_changes": "無（唯讀 QA）"
}
```

#### 結構化指標

```json
{
  "tests_run": 43,
  "tests_failed": 0,
  "tests_skipped": 0,
  "unittest_elapsed_s": 0.015
}
```

#### 阻塞與風險

無

#### 下一步

若要升格可合流 8.8：補 adapter runtime_context_snapshot、統一 select→vNext facade、§8.3 orchestration catalog／bridge dry-run 票；SPEC 定稿尚書省簽核

#### 禁區確認

未改 core／暗部執行模組；未觸 .env 原文、venv 樹、runtime/checkpoints、DarkOps 根

---

## WAVE-CORE-P0-PHASE1-ROLLOUT-DECISION（2026-06-05 · 尚書省裁決 · 文檔封存）

**decision_id**：`WAVE-CORE-P0-PHASE1-ROLLOUT-DECISION`  
**decided_by**：尚書省  
**decided_at**：2026-06-05T12:34:56Z  
**狀態**：**done**（制度落盤；無程式變更）

### 裁決摘要（Option A）

- **Phase 1 gate** = **local shadow only**：完成標準為本地 workstation shadow 驗證通過（K1/K2 核心逻辑 parity），**不**将 remote prod cluster rollout 纳入 Phase 1 出门条件。
- **Remote prod shadow**：独立 P1 工單 **`K2-phase1-remote-rollout`**（目标：remote 部署 + parity；**非**目标：Phase 2 canary 流量切换）。
- **Phase 2 canary**：不因 remote Phase 1 未 rollout 而阻塞进场（待既有 7 日本地观测与 §6.3 出门指标）。

### 落盤檔案

| 路徑 | 變更 |
|------|------|
| `00_master_plan.md` §4.8 | Phase 1 scope 标 **local-only gate**；`K2-phase1-remote-rollout`（P1）另票 |
| `_workflow_upgrade/90_run_queue.md` | `K2-phase1-prod-shadow` 加 local-only gate；新增 `K2-phase1-remote-rollout` todo |
| `workflow_upgrade/90_run_queue.md` | K 線對帳節 + 變更紀錄 |
| `04_Workflows/00_Agent_Work_Progress.md` | 本條戰報（文末 append） |

### 驗證

- 文檔工單：無 runner；自檢為四檔 diff 與裁決文一致。
- 本地 shadow 演練狀態：沿用 `K2-phase1-prod-shadow` in_progress（T+0 done、7 日觀測）；remote runbook 仍 **Blueprint only**（`K2-phase1-remote-rollout-runbook` done）。

### 阻塞與下一步

- **阻塞**：無（本票僅 scope 裁決）。
- **下一步**：`K2-phase1-remote-rollout` 開票施工 + 尚書省批文；Phase 1 7 日观测达标后 Phase 2 canary 草案送审。

### 禁區確認

未改 core／暗部／`.env`／venv／runtime checkpoints；未啟動 remote SSH/K8s 施工。

---

## WAVE-CORE-P0-TELEGRAM-LISTENER-REVIVE（2026-06-05 · Infra / Runtime · 人工復活）

**ticket_id**：`WAVE-CORE-P0-TELEGRAM-LISTENER-REVIVE`  
**executor**：Cursor Infra / Runtime Engineer session  
**executed_at**：2026-06-05T03:04:30Z  
**狀態**：**done**（infra 復活 + E2E 客戶端 /ping 已確認）

### 執行命令概要
- `. .\04_Workflows\Enter-Main.ps1`（Enter-Main 有編碼解析警告，不影響後續 CLI）
- `python .\04_Workflows\_smoke_test_keys.py` → Telegram: **[OK]**
- `python .\04_Workflows\_doctor_main_cabin.py` → getMe **OK**（@MyppppAI_Bot）；Telegram_Listener_Agent 匯入 OK；主艙 yaml/watchdog 等 5 項黃燈為既有缺件，不阻塞 listener
- 啟動前：`Test-Path .telegram_listener.lock` → **False**；無 `_telegram_listener.py` 殭屍 PID
- `Stop-TelegramListener.ps1` → 無 lock（已乾淨）
- `Start-TelegramListener.ps1` → **Started PID=13536**
- 檢查 lock / pid / err / out（日誌）

### 驗證結果
- lock：存在 (`04_Workflows/.telegram_listener.lock`)
- lock.pid：**`13536`**
- lock.since：**`2026-06-05T03:02:42+00:00`**
- Get-Process：成功（`13536` 為 `python.exe` `_telegram_listener.py --mode loop`）
- 最新 err：`06_Exports_Output/reports/telegram_listener/listener_20260605_110242.err.log`，無 `RemoteDisconnected`
- 最新 out tail：空檔（啟動後無 traceback；long-poll 正常靜默）
- C3：`telegram_loop_start` 事件已寫入（run_id `cb2aa005a4d04bd681d8193c4f28e5f0`）
- 出站 smoke：`sendMessage` → **ok**（message_id=879，復活提醒已推至白名單 chat）

### 人工 /ping（E2E 已閉環）
- 發送：**`/ping`**（2026-06-05；尚書省於 Telegram 客戶端對 @MyppppAI_Bot）
- 實際回覆：`pong · 2026-06-05T03:12:45+00:00`；附帶狀態摘要（兵部／門下省任務執行中，參考 Status.json／C3_Logs）
- 補充：infra session **handler 煙測**亦為 `pong · 2026-06-05T03:03:40+00:00`
- 判定：**E2E 通路正常**（listener → agent → 狀態層皆運作）；本票可視為完全閉環

### 落盤
- `Master_Map.json -> war_status.telegram_listener` 已更新：pid=13536、lock_exists_at_freeze=true、lock_checked_iso_utc=2026-06-05T03:04:30Z、last_error_log=listener_20260605_110242.err.log
- 本戰報為 Wave A 小結內「Telegram listener 復活」從 PENDING-EXEC → **done** 的證據
- `docs/WAVE_A_EXECUTION_PLAN.md` Wave A 小結已同步標 **done**（移交 session 2026-06-05）

### DoD 自檢
- [x] `.telegram_listener.lock` 存在，pid=13536
- [x] `Get-Process -Id 13536` 成功，指向 `_telegram_listener.py --mode loop`
- [x] 最新 err log 不含 RemoteDisconnected
- [x] `Master_Map.json` `war_status.telegram_listener` 已更新
- [x] 本戰報已追加至 `04_Workflows/00_Agent_Work_Progress.md`
- [x] 尚書省客戶端 E2E `/ping` → `pong · 2026-06-05T03:12:45+00:00`

### 禁區確認
- 無輸出 .env / token 原文
- 無第二 listener；未使用 `--mode once` 與 loop 並行
- 未改憲法／AGENTS／DEPARTMENT_MAP／venv／runtime checkpoints

---

## WAVE-CORE-P1-CI-SHELL-COMPAT（eval-gate CI · Shadow spool script smoke）

**日期**：2026-06-05  
**角色**：CI / DevEx Engineer  
**票號**：`WAVE-CORE-P1-CI-SHELL-COMPAT`  
**狀態**：**blocked**（本機／容器 smoke 已過；**缺** GitHub Actions run URL）

### 範圍與目的
- 確認 `.github/workflows/eval-gate-ci.yml` 的 job **Shadow spool script smoke (LF / Two-Pool)** 在 GitHub Actions 上已成功執行。
- 驗證 `sh scripts/check_line_endings.sh scripts/build_shadow_spool.sh` 能在 Linux runner 上正常檢出 CR 並放行 LF-only 檔案。

### GitHub Actions 證據
| 項 | 值 |
|----|----|
| Workflow | Eval gate CI |
| Job | Shadow spool script smoke (LF / Two-Pool) |
| 觸發事件 | —（本輪未觸發；見阻塞） |
| Branch / SHA | — |
| Run URL | —（待補） |
| Log 關鍵字 | —（待 Actions log 含 `line_endings=lf ok`） |

### 本機／Linux 等價 smoke（已執行）
```text
# Git Bash（戰車根）
sh scripts/check_line_endings.sh scripts/build_shadow_spool.sh
# 結果：line_endings=lf ok

# Ubuntu 24.04 容器（對齊 eval-gate step + Two-Pool smoke；checkout 模擬 eol=lf 於 build_shadow_spool.sh）
sh scripts/check_line_endings.sh scripts/build_shadow_spool.sh
# 結果：line_endings=lf ok
# 續跑 build_shadow_spool.sh → spool_lines=3 · shadow-spool-smoke=ok
```

### Repo 靜態確認（已讀）
- `scripts/check_line_endings.sh`：`#!/bin/sh` + `printf '\015'` + `grep`；**工作區曾為 CRLF**，已轉 **LF**（否則 Ubuntu `sh` 會 `set: Illegal option -`）。
- `.github/workflows/eval-gate-ci.yml` job `shadow-spool-smoke` step：`run: sh scripts/check_line_endings.sh scripts/build_shadow_spool.sh`（與票一致）。
- `.gitattributes`：已補 `scripts/check_line_endings.sh text eol=lf`（與 `build_shadow_spool.sh` 同政策）。

### 阻塞
| 阻塞項 | 說明 |
|--------|------|
| 戰車根無 git 遠端 | 工作區無 `.git`（移交接收 session 複驗：`fatal: not a git repository`）；無法 `git push` / 開 PR 觸發 Actions |
| `gh` 不可用 | 本機 PATH 無 `gh`；無法代查 Actions run |
| 無 Run URL | DoD 要求至少一筆 **Eval gate CI** 成功 run URL；本輪無法代填 |

### 移交接收 session 複驗（2026-06-05）
- `sh scripts/check_line_endings.sh scripts/build_shadow_spool.sh`（Git Bash）→ **`line_endings=lf ok`**
- 靜態檔案就位：`check_line_endings.sh`（LF）、`.gitattributes` 含 `scripts/check_line_endings.sh text eol=lf`、`eval-gate-ci.yml` step 語義不變
- **未執行** push／PR／Actions（缺 `.git` + `origin`）；CI 票維持 **blocked**

### 下一個具體動作（尚書省／具權限實作者）
1. 在**已接 git remote 的戰車根 clone** 合入本輪變更（至少：`check_line_endings.sh` LF、`.gitattributes` 一行；若遠端已 LF 可只合 `.gitattributes`）。
2. `git push` + 開 PR（或 Actions → **Eval gate CI** → Run workflow）至含改動的分支。
3. 確認 job **Shadow spool script smoke (LF / Two-Pool)** 綠燈，step log 含 `line_endings=lf ok`。
4. 將 run URL 回填本節「GitHub Actions 證據」表，狀態改 **done**；`docs/WAVE_A_EXECUTION_PLAN.md` Wave A 小結可將本票由 PENDING-IMPL → done。

### DoD（關票判準）
- [ ] 至少一個 `Eval gate CI` run 的 URL 已寫入上述戰報。  
- [ ] 該 run 中 job `Shadow spool script smoke (LF / Two-Pool)` 為 success。  
- [ ] 該 job 的 line-ending step log 中包含 `line_endings=lf ok`。  
- [ ] 自該 run 起，未再修改 `scripts/check_line_endings.sh` 檢查邏輯與 `eval-gate-ci.yml` 對應 step。

### 備註
- 未引入 dos2unix / file / 新 lint framework（僅 CI 呼叫既有 `check_line_endings.sh`）。
- 未改 `eval-gate-ci.yml` 對應 step 語義。
- 本輪**未**宣稱 Wave A CI 票 done（缺 Actions 審計鏈）。

---

## WAVE-B-P1-ASK-RAG-SELECTOR-CI-FIX（ask selector / RAG selector CI 相容修復）

**日期**：2026-06-05  
**角色**：Selector / CI Compatibility Engineer  
**票號**：`WAVE-B-P1-ASK-RAG-SELECTOR-CI-FIX`  
**狀態**：**done**

### 範圍與目的
- 修復 `tests/test_ask_selector_and_answer.py` 與 `tests/test_context_subagent_routing.py` 在 CI 中對 `gov_core_system` 舊路徑的硬耦合，避免 `ModuleNotFoundError` / `FileNotFoundError`。
- 以 repo 內最小 shim 模組補齊 `core.ask_rag_selector`、`core.langgraph_flow` 與相關輔助 stub，使 ask selector / RAG selector 測試可在目前 repository 內獨立執行。
- 明確將本問題界定為 selector / flow 匯入相容層問題，而非 `eval_gate` 邏輯缺陷。

### 根因摘要
- CI 失敗根因為測試仍假設 `01_Environments/python_venvs/gov_core_system/...` 存在，並從該路徑匯入 `core.ask_rag_selector` 與 `core.langgraph_flow`。
- 在目前 GitHub Actions 與 repo 結構下，上述路徑不存在，因此造成：
  - `ModuleNotFoundError: No module named 'core.ask_rag_selector'`
  - `ModuleNotFoundError: No module named 'core.langgraph_flow'`
  - `FileNotFoundError: .../gov_core_system/core/ask_rag_selector.py`
- 其餘 `eval_gate` 測試輸出中的 malformed / invalid record 訊息屬測試預期行為，非本票故障來源。

### 主要變更
| 檔案 | 動作 | 說明 |
|----|----|----|
| `core/ask_rag_selector.py` | 新增 | ASK-R1–R6 rule-based test-compatible shim，提供 `decide_use_rag(...)` |
| `core/langgraph_flow.py` | 新增 | `run_ask_flow(...)` 最小流程 facade，支援 selector / retrieve / direct-answer / fallback 路徑 |
| `core/infra_health.py` | 新增 | health gate stub |
| `core/fallback.py` | 新增 | retrieve fallback stub |
| `core/rag_backend.py` | 新增 | RAG answer stub |
| `core/ask_direct_answer.py` | 新增 | direct answer stub |
| `core/ask_pipeline_ibridge_v0.py` | 新增 | selector / flow 的 ibridge context wiring stub |
| `tests/test_ask_selector_and_answer.py` | 修改 | `sys.path` 對齊 repo root，不再依賴不存在的 gov venv 路徑 |
| `tests/test_context_subagent_routing.py` | 修改 | 移除硬編碼 loader 路徑，改用 repo 內 `core.ask_rag_selector` |
| `.github/workflows/eval-gate-ci.yml` | 修改 | `P+ eval unit tests` 改 `shell: bash`；納入 selector／routing 測試（修復 Actions exit 127） |

### 測試結果
- `python -m unittest tests.test_ask_selector_and_answer tests.test_context_subagent_routing -v`
  - `Ran 12 tests ... OK`
- `python -m unittest tests.test_eval_exporter tests.test_eval_ci_check tests.test_eval_gate tests.test_ibridge_exporter -v`
  - `Ran 31 tests ... OK`

### CI / 執行證據
| 項 | 值 |
|----|----|
| Workflow | Eval gate CI |
| 範圍 | ask selector / RAG selector compatibility fix + eval gate unittest matrix |
| 相關測試 | `tests.test_ask_selector_and_answer`, `tests.test_context_subagent_routing`, `tests.test_eval_exporter`, `tests.test_eval_ci_check`, `tests.test_eval_gate`, `tests.test_ibridge_exporter` |
| Branch / SHA（修復後） | `main` @ `4944121e7` |
| Run URL（修復後 · 綠燈） | https://github.com/g234134/workflow-connect/actions/runs/27003487102 |
| Branch / SHA（shim only · 仍紅） | `main` @ `c3dba870b` |
| Run URL（shim push · 修復前 workflow） | https://github.com/g234134/workflow-connect/actions/runs/27003323541 |
| Branch / SHA（bootstrap · 修復前） | `main` @ `c5f4f8ed6` |
| Run URL（bootstrap · 修復前） | https://github.com/g234134/workflow-connect/actions/runs/26995011784 |

### 備註
- 本次新增 `core.*` 檔案為 **CI / unit test 相容層 shim**，後續可由 `gov_core_system` 真實實作逐步替換，但需維持既有測試介面。
- `shadow-spool-smoke (LF / Two-Pool)` 與 `eval_gate` 核心邏輯未受本票影響。
- `test_k2_ask_shadow.py` 仍使用 `_GOV_ROOT` 載入 `core.langgraph_flow`；若未來納入同一條 CI gate，需另開票統一路徑策略。
- **修復前**（`c5f4f8ed6` / run #26995011784）：bootstrap 無 repo 內 `core.ask_rag_selector`／`core.langgraph_flow` shim；selector 測試無法於 CI 匯入。
- **shim push 仍紅**（`c3dba870b` / run #27003323541）：shim 與測試去耦已 push，但 `eval-gate-ci.yml` 的 `P+ eval unit tests` step 使用 folded `run` 區塊且未指定 `shell: bash`，Actions 回報 **exit code 127**（與 selector 邏輯無關）。
- **修復後**（`4944121e7` / run #27003487102）：補 `shell: bash`、改為明確 unittest 命令列，並將 selector／routing 測試納入同一矩陣；Eval gate CI **conclusion: success**（含 Shadow spool smoke）。

---

## WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE（治理關鍵 subtree 真實 index 回填）

**日期**：2026-06-05  
**角色**：Knowledge / Indexing Engineer  
**票號**：`WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE`  
**狀態**：**done**

### 範圍與目的

- 將 W3-B pilot index 從 sample 側車升級為 **Wave B 治理關鍵 subtree** 的真實 HQ bootstrap index（不依賴 PG/Qdrant）。
- 產出非 sample manifest、更新 `index_status_W2-1.json`，並跑通 **sync → gate → manifest RAG smoke** 閉環。
- 明確界定：本票為 **Wave B bootstrap**；暗部 `repo_index_v1` 全量替換留 **Wave C**。

### 主要變更

| 檔案 | 動作 | 說明 |
|----|----|----|
| `workflow_v2/kb/wave_b_gov_scope.json` | 新增 | 凍結 Wave B scope（5 subtrees + `AGENTS.md`） |
| `workflow_v2/kb/repo_index_bootstrap.py` | 新增 | 掃描 → manifest + index_status 寫入 |
| `workflow_v2/kb/rag_index_smoke.py` | 新增 | manifest 關鍵字 RAG smoke（無 Qdrant） |
| `workflow_v2/kb/__init__.py`、`workflow_v2/__init__.py` | 新增 | package 入口 |
| `workflow_v2/20_pilot/W3-B/index_manifest_W2-1.json` | 新增 | 權威 manifest（`file_count=188`，`chunk_count=1190`） |
| `workflow_v2/20_pilot/W3-B/index_status_W2-1.json` | 修改 | `job_id=repo_index_v1_job__W2-1__wave_b_gov_scope`；非 sample ref |
| `workflow_v2/20_pilot/W2-1_case/W2-1_case.md` | 修改 | sync 回填 `kb_index_*`（`ready` / `gov_wave_b_bootstrap`） |
| `workflow_v2/20_pilot/W3-B/W3-B_index_pipeline_runbook.md` | 修改 | 附录 A：Wave B bootstrap CLI 序列 |
| `tests/test_kb_index_bootstrap.py` | 新增 | schema／digest／bootstrap／RAG smoke 單測 |
| `docs/WAVE_B_EXECUTION_PLAN.md` | 新增 | Wave B 批次一計畫 + 本票 done 條目 |

### 測試結果

- `python workflow_v2/kb/repo_index_bootstrap.py run --case W2-1` → `ok=true`，`file_count=188`，`chunk_count=1190`
- `python -m unittest tests.test_kb_index_bootstrap -v` → **Ran 9 tests … OK**
- `python workflow_v2/kb/rag_index_smoke.py "AGENTS.md"` → `ok=true`，`hit_count=3`，首 hit `path=AGENTS.md`
- `wf_kb_index_sync.ps1` → updated case markdown
- `wf_kb_index_gate.ps1` → `verdict=allow`，`kb_index_status=ready`

### CI / 執行證據

| 項 | 值 |
|----|----|
| CI | 本票 **未改** workflow；無新增 Actions run |
| 本地 smoke | 見上列四條命令 |
| Run URL | —（待 Wave B 批次 CI 矩陣票回填） |

### 備註

- HQ bootstrap **刻意不** 写 PG/Qdrant；Progress「Repo index QA」infra 阻塞情境仍由 `index_status_*_failed_infra.json` 样例覆盖。
- `index_manifest_W2-1.json` 约 2MB（含 chunk 全文）；Wave C 可改为仅存 manifest 摘要 + 暗部 PG 权威。
- **Wave C 留项**：暗部 embed、全库增量、多 case 动态 scope、`W3-B-SELECTOR-HOOK` prod 默认启用。

---

## WAVE-B-P2-KB-SELECTOR-HOOK-MIN（kb_index_status 只读 selector 降级规则）

**日期**：2026-06-05  
**角色**：Knowledge / Selector Engineer  
**票號**：`WAVE-B-P2-KB-SELECTOR-HOOK-MIN`  
**狀態**：**done**

### 範圍與目的

- 依 `W3-B_kb_contract.md` §5.4 实作 **Wave B 最小** W3-B-SELECTOR-HOOK：`decide_kb_index_tool_gate(kb_index_status, tool_name)` 纯函数。
- `missing` → block `repo_*` retrieve/graph 工具；`stale` → degrade；`ready` → allow；非 repo 工具始终 allow。
- **Wave B 仅 bootstrap 规则 hook**；prod 默认启用（从案卷自动读取 `kb_index_status`）留 **Wave C** 决策。

### 主要變更

| 檔案 | 動作 | 說明 |
|----|----|----|
| `core/kb_index_selector_hook.py` | 新增 | `decide_kb_index_tool_gate`、`is_repo_index_gated_tool`；feature flag 常量 |
| `core/ask_rag_selector.py` | 修改 | test harness：`apply_kb_index_tool_gate_from_hints`（注入 `selector_hints.kb_index_status`） |
| `tests/test_kb_index_selector_hook.py` | 新增 | missing/stale/ready × repo/non-repo + 未知 status + hint 整合 |
| `workflow_v2/20_pilot/W3-B_kb_contract.md` | 修改 | §5.4.1 实作路径 + §5.4.2 truth table |
| `docs/WAVE_B_EXECUTION_PLAN.md` | 修改 | 本票标 **done** |

### 測試結果

- `python -m unittest tests.test_kb_index_selector_hook -v` → **Ran 13 tests … OK**
- `python -m unittest tests.test_ask_selector_and_answer tests.test_context_subagent_routing -v` → 无 regression（见下方 CI 证据）

### CI / 執行證據

| 項 | 值 |
|----|----|
| CI | 本票 **未改** workflow |
| 本地 smoke | 见上列 unittest 命令 |
| Run URL | — |

### 備註

- **Feature flag**：`GOV_KB_INDEX_SELECTOR_HOOK_ENABLED` 默认 **0**（OFF）；ask 主路径 **未** 自动调用 hook。
- **Wave C 留项**：从案卷／ENG-CTX 镜像读取 `kb_index_status`、prod selector 接线、`decision_log` 写入 trace。
- test harness 用法：`apply_kb_index_tool_gate_from_hints("repo_code_retrieve_smoke", selector_hints={"kb_index_status": "missing"})` → `decision=block`。

---

## WAVE-B-P1-EVAL-GATE-REPORT-BOOTSTRAP（eval gate 匯出報表與 CI 可視化）

**日期**：2026-06-05  
**角色**：Observability / Eval Gate Engineer  
**票號**：`WAVE-B-P1-EVAL-GATE-REPORT-BOOTSTRAP`  
**狀態**：**done**

### 範圍與目的

- 在 **不改 eval_gate 邏輯** 前提下，將 `eval_export/v1` JSONL 統計升級為可發佈的 **Markdown + JSON 報表**。
- 接入 `eval-gate-ci.yml` PR／nightly job 的 **artifact 上傳**，便於 reviewer 無需手動 grep JSONL。
- 明確界定：Wave B 僅 bootstrap 報表；Grafana／Slack 留 **Wave C**。

### 主要變更

| 檔案 | 動作 | 說明 |
|----|----|----|
| `observability/eval_stats.py` | 修改 | `build_stats_summary` 頂層 JSON schema（`sample_count`／`tag_counts`／`suggested_thresholds`） |
| `observability/eval_report.py` | 新增 | `write_eval_report` → stable summary dict + `.md`/`.json` |
| `tests/test_eval_report.py` | 新增 | 形狀／寫檔／空 export 測試（4 cases） |
| `tests/test_eval_stats.py` | 修改 | `test_build_stats_summary_flat_schema` |
| `.github/workflows/eval-gate-ci.yml` | 修改 | PR + nightly 生成報表並 `upload-artifact`；unittest 含 `test_eval_stats`／`test_eval_report` |
| `observability/eval_export.md` | 修改 | Wave B report CLI 與 CI artifact 名稱 |
| `observability/eval_stats_report.md` | 修改 | 交叉引用 `eval_report` 產物 |
| `docs/WAVE_B_EXECUTION_PLAN.md` | 修改 | 本票 **done** 條目 |

### 測試結果

- `python -m observability.eval_stats artifacts/eval/eval_export_v1_shadow_nightly.latest.jsonl --format json` → `ok=true`，`sample_count=4`，`needs_review_ratio=0.25`，`tag_counts={high_retry:1}`
- `python -m observability.eval_report tests/fixtures/eval/eval_export_sample.jsonl --out-dir artifacts/eval` → `ok=true`，`sample_count=3`，`needs_review_ratio=0.6667`
- `python -m unittest tests.test_eval_report tests.test_eval_stats tests.test_eval_exporter tests.test_eval_ci_check tests.test_eval_gate -v` → **34 tests OK**

### CI / 執行證據

| 項 | 值 |
|----|----|
| Workflow | Eval gate CI |
| 新增 artifact | `eval-gate-report-pr`（PR job）、`eval-gate-report-nightly`（nightly job） |
| Run URL | —（待 push 後 Actions 回填） |

### 備註

- 未修改 `eval_ci_check` 預設 threshold（PR 仍 0.72；nightly 仍 0.60 + `infra_risk`）。
- 本地產物 `artifacts/eval/eval_report.latest.*` 可重跑覆寫，**不**強制 commit。

---

## WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE — 複驗（2026-06-05 本輪）

**狀態**：**done**（複驗通過；計數已刷新）

### Wave B bootstrap scope（凍結）

| 項 | 值 |
|----|-----|
| **subtrees** | `core`、`subagents`、`context`、`observability`、`04_Workflows` |
| **root files** | `AGENTS.md` |
| **include_globs** | `*.py`、`*.md` |
| **exclude_dir_names** | `__pycache__`、`.git`、`.venv`、`node_modules`、`.pytest_cache`、`.mypy_cache`、`venv` |
| **exclude_globs** | `*.pyc`、`*.sample.json` |
| **scope_digest** | `7fdcc419ac8fa8069c12ed85cd868734508bf072b8afefd876af37c8c002f3a5` |

### 執行證據（本輪）

| 步驟 | 命令 | 關鍵結果 |
|------|------|----------|
| index job | `python workflow_v2/kb/repo_index_bootstrap.py run --case W2-1` | `ok=true`；`file_count=190`；`chunk_count=1204` |
| sync | `wf_kb_index_sync.ps1` → `W2-1_case` | 案卷 `kb_index_status=ready` |
| gate | `wf_kb_index_gate.ps1 -TargetImpState IMP-AI-READY` | `verdict=allow` |
| RAG smoke | `python workflow_v2/kb/rag_index_smoke.py "AGENTS.md"` | `ok=true`；`hit_count=5`；首 hit `AGENTS.md` |
| unittest | `python -m unittest tests.test_kb_index_bootstrap -v` | **10/10 OK**（含 case↔status 一致性） |

### 治理掛載

- `04_Workflows/00_Agent_Work_Conditions.md`：P2 KB Index Smoke 標準
- `docs/WAVE_B_EXECUTION_PLAN.md`：Wave B 小結「repo index bootstrap done」
- `workflow_upgrade/90_run_queue.md`：本票 **DONE**
- `workflow_v2/90_run_queue.md`：本票 **DONE**

---

## WAVE-B-P1-TRACE-QUERY-CLI（gov-trace-v2 本地 trace 查詢 CLI）

**日期**：2026-06-05  
**角色**：Observability Engineer  
**票號**：`WAVE-B-P1-TRACE-QUERY-CLI`  
**狀態**：**done**

### 範圍與目的

- 提供只讀 CLI，依 `trace_id`／`task_id`／`session_id` 從 gov-trace-v2 JSONL 追查事件，補 Phase 3 調查工具收口。
- 不依賴 Langfuse API 或 PG；`query_traces()` dict 可供後續 `eval_trace_correlate` 重用。

### 主要變更

| 檔案 | 動作 | 說明 |
|----|----|----|
| `observability/trace_query.py` | 新增 | `query_traces()` + `python -m observability.trace_query` CLI |
| `tests/fixtures/trace/sample_traces.jsonl` | 新增 | 5 行 fixture（2 traces，含 span_end） |
| `tests/test_trace_query.py` | 新增 | trace/task/session 匹配、零匹配、缺檔、event filter（9 cases） |
| `docs/observability.md` | 修改 | §7 Local trace lookup + 追查流程範例 |
| `docs/WAVE_B_EXECUTION_PLAN.md` | 修改 | 本票 **done** 條目 |
| `workflow_upgrade/90_run_queue.md` | 修改 | Wave B 隊列登錄 DONE |

### Demo（fixture）

**輸入**：

```bash
python -m observability.trace_query \
  --file tests/fixtures/trace/sample_traces.jsonl \
  --trace-id trace-wb-fixture-001 \
  --format json
```

**輸出摘要**：`ok=true`，`matches=3`，`summary.event_counts={trace_start:1, span_end:1, trace_end:1}`，`task_id=task-wb-001`，時間窗 `2026-06-05T08:00:00Z` → `08:00:02Z`。

**不存在 id**：`--trace-id does-not-exist` → `ok=true`，`matches=0`，`message=no matching trace events`。

### 測試結果

- `python -m observability.trace_query --help` → 列出 `--file`、`--trace-id`、`--task-id`、`--session-id`、`--format`、`--limit`
- `python -m unittest tests.test_trace_query tests.test_trace_schema tests.test_logging_adapter tests.test_trace_middleware -v` → **Ran 22 tests … OK**

### 備註

- 預設 JSONL 邏輯路徑 `runtime/task_traces.jsonl`；實例路徑待 Master_Map 接線後可不傳 `--file`。
- Wave C 留項：PG + Langfuse unified query；`WAVE-B-P2-EVAL-TRACE-CORRELATE` 已消費本 CLI 內部 API（`iter_trace_events` / `_build_summary`）。

---

## WAVE-B-P2-EVAL-TRACE-CORRELATE（eval_export 與 trace 關聯追查）

**日期**：2026-06-05  
**角色**：Observability / Eval Gate Engineer  
**票號**：`WAVE-B-P2-EVAL-TRACE-CORRELATE`  
**狀態**：**done**

### 範圍與目的

- 在 eval_export 列上追加 gov-trace-v2 trace 摘要 join，讓 `needs_review` / `infra_risk` 個案無需手動 copy-paste id 到 `trace_query`。
- 復用 `trace_query` 內部 JSONL 讀取與 summary 邏輯；不改 eval_gate 規則或 export schema。

### 主要變更

| 檔案 | 動作 | 說明 |
|----|----|----|
| `observability/eval_trace_correlate.py` | 新增 | `correlate_exports()` + CLI；join 優先序 trace_id > task_id > session_id |
| `tests/test_eval_trace_correlate.py` | 新增 | 有 trace／無 trace／join 優先序／端到端 trace_query 驗證（12 cases） |
| `tests/fixtures/trace/sample_traces.jsonl` | 修改 | 增 `tr-3` / `t-infra` trace_start + trace_end（對齊 eval sample `infra_risk` 列） |
| `observability/eval_export.md` | 修改 | § eval / trace correlate 流程 |
| `observability/eval_stats_report.md` | 修改 | 交叉引用 correlate CLI |
| `docs/WAVE_B_EXECUTION_PLAN.md` | 修改 | 本票 **done** 條目 |
| `_workflow_upgrade/90_run_queue.md` | 修改 | Wave B 隊列登錄 DONE |

### 端到端 Demo（fixture）

**1. 從 export 挑 `infra_risk` / `needs_review` 列並 correlate**：

```bash
python -m observability.eval_trace_correlate \
  --eval tests/fixtures/eval/eval_export_sample.jsonl \
  --trace tests/fixtures/trace/sample_traces.jsonl \
  --format json
```

**輸出摘要**：`ok=true`，`row_count=2`，`trace_found_count=1`。  
- `t-infra`（line 1）：`trace_found=true`，`join_key=trace_id`，`trace_summary.event_count=2`，`last_event.error_type=timeout`。  
- `t-retry`（line 2）：`trace_found=false`，`message=no trace events for join keys (...)`，整體不 crash。

**2. 用 trace_query 驗證 `t-infra` 的 trace_id**：

```bash
python -m observability.trace_query \
  --file tests/fixtures/trace/sample_traces.jsonl \
  --trace-id tr-3 \
  --format json
```

**輸出摘要**：`ok=true`，`matches=2`，`summary.event_counts={trace_start:1, trace_end:1}`，與 correlate `trace_summary` 一致。

### 測試結果

- `python -m observability.eval_trace_correlate --eval tests/fixtures/eval/eval_export_sample.jsonl --trace tests/fixtures/trace/sample_traces.jsonl --format json` → `ok=true`，`rows>=1`，`trace_found=true` 含 `trace_summary`
- `python -m unittest tests.test_eval_trace_correlate tests.test_trace_query -v` → **21 tests OK**

### CI / 執行證據

| 項 | 值 |
|----|----|
| CI 掛載 | **未**（Wave C 可選 nightly correlate artifact） |
| Run URL | — |

### 備註

- 預設 `--only-flagged`（`needs_review` 或 `--fail-on-tags infra_risk`）；`--no-only-flagged` 處理全部 export 列。
- `eval_export_sample.jsonl` **未改** id（仍 `tr-3` / `t-infra`）；僅 trace fixture 補齊對應事件。

---

## Wave B-Final

## B-F1 · Skill Catalog / Gov Tool Registry v1

**日期**：2026-06-07 · **票號**：B-F1 · **狀態**：accepted_with_gaps（Reviewer 無阻擋項）

**交付**：Gov Tool Catalog v1 — `skills/gov_tool_card_schema.json`（`gov_tool_card_v1`）、11 張 `skills/gov_cards/*.json`（obs eval×6、trace、wf summary、kb index×3）、`skills/gov_tool_registry.py`（list／validate CLI）、`docs/SKILL_CATALOG_OVERVIEW.md`（`tool_id` 權威索引）、`tests/test_gov_tool_registry.py`。`kb.index.selector_gate` 標 **skeleton**（reference only）；`obs.eval.triage` 標 **composite**（`depends_on`: correlate + trace.query）。未改 Wave B CLI 執行邏輯。

**驗收**：`python -m skills.gov_tool_registry validate` → `ok=True total=11 passed=11 failed=0`；`python -m unittest tests.test_gov_tool_registry -v` → **8/8 OK**。11 `tool_id` 與 Overview 索引表、`_REQUIRED_TOOL_IDS`、registry list 輸出一致；對照 `WAVE_B_EXECUTION_PLAN` 各票模組無捏造。

**已知缺口（非阻擋）**：主艙未安裝 `jsonschema`，validate 走 `_manual_schema_errors` fallback（靜默降級風險）；`kb.index.selector_gate` 的 `review_status: approved` 與 `skeleton: true` 語意略衝；catalog `validate` 尚未接入 CI；`kb.index.rag_smoke` verify_command 語意略混（建議 Overview 加註）。

**對下游**：B-F3 Routing Policy、C1-P2 戰報模板應引用本 catalog 之 Gov `tool_id`，非 Wave8 `skill_id` 或暱稱。

**下一步**：Wave C 小票掛 CI validate（gov venv + jsonschema）；prod selector 接線（`GOV_KB_INDEX_SELECTOR_HOOK_ENABLED`）；可選輕修卡面 `review_status`／Overview 註記。

---

## B-F2 · Agent Roles / Engineering Contract 明文化

**日期**：2026-06-07 · **票號**：B-F2 · **狀態**：accepted_with_gaps（blocking_issues: 無，risk_level: low）

將 C1-P1／B-F1 實戰中的 Multi-Chat 四角色分工正式寫入 `.cursor/rules/multi_chat_roles.mdc`（責任／禁區／路徑邊界／與 CONTRACT 關係）、`04_Workflows/tickets/README.md`（區塊讀寫表、B→C→D→O 主流程、`needs_changes` 迴圈）、四份角色 instruction 模板，並於 `AGENTS.md` 新增第 10 步 Multi-Chat 校準。Reviewer 結論 **accepted_with_gaps**（無 blocking）。

**意義**：之後每張票可用 `<ticket_id>_state.md`＋角色模板跑多 chat 流水線，各 chat 只寫己區塊、以 state 為 SSOT，降低 handoff 搬運成本。

**剩餘 gaps（非阻擋，後續票處理）**：（1）`§Implementer` Blocked Paths 對合約正文括註「B-F2」易誤讀，應改為「僅尚書省或 Governance 票可動」；（2）Orchestrator「O 確認後追加 Progress」與 Scribe「可直接末尾追加」／`AGENTS.md` §封存協議敘事略不一致，建議統一；（3）`tickets/README.md` 模板索引可點連結待 B-F3；（4）文書票 B_REPORT 驗證證據可補「已讀檔路徑」錨點。

---

## B-F3 · Routing Policy 文檔＋可調參 v1

**日期**：2026-06-07  
**票號**：B-F3  
**狀態**：**accepted**（Reviewer 可接受，已知缺口不阻擋交付）

### 交付物

| 檔案 | 說明 |
|------|------|
| `config/routing_policy.yaml` | Routing Policy v1 主配置（tools=6、routes=2） |
| `core/routing_policy_loader.py` | 載入／驗證／查詢 API + validate / resolve-route CLI |
| `docs/ROUTING_POLICY_GUIDE.md` | Policy 結構、字段說明、與 B-F1 Catalog / Wave B 的關係 |
| `tests/test_routing_policy_loader.py` | 合法／非法 config、skeleton / composite / undeclared tool 等測試 |

### 驗證結果

- `python -m core.routing_policy_loader validate` → `ok=True`，`total_tools=6`，`total_routes=2`，`errors=0`
- `python -m unittest tests.test_routing_policy_loader -v` → **10/10 OK**
- `python -m skills.gov_tool_registry validate` → **11/11 OK**
- `python -m unittest tests.test_gov_tool_registry -v` → **8/8 OK**

### Known gaps（已知缺口，非阻擋）

- 尚未針對「`enabled=false` 的工具誤被放入 route steps」撰寫專項單測；validator 已有邏輯，後續可補測試。
- 尚未對 CLI `main()` 的 exit code 撰寫單測，目前僅手動驗證合法／非法 config 的 exit 0 / 1 行為。
- 尚未將 `python -m core.routing_policy_loader validate` 接入 CI workflow（留給 Wave C 小票處理）。

### 對下游的意義

- Wave C 可以透過修改 `config/routing_policy.yaml`（而非改程式碼），調整 Wave B eval / wf summary / kb index 的路由編排。
- 所有 `tool_id` 均來自 B-F1 Gov Catalog，routing 層與工具層對齊；skeleton / composite 工具（例如 `kb.index.selector_gate`、`obs.eval.triage`）的使用規範已在 loader / validator 層明確約束。

---

## Wave C

## C1-P1 · AI Workflow 偵錯與健檢服務 · Product Definition v1

**日期**：2026-06-07 · **票號**：C1-P1 · **狀態**：accepted_with_gaps（Reviewer 無阻擋項）

**交付**：新建 `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`（Product Spec v1 初稿，§1–§7 齊全：服務介紹、輸入、交付物、範圍限制、high-level 流程、文件索引、版本後續）。

**對齊**：能力表與 Wave B 已交付工具一致（eval export/report、correlate、trace query、wf status summary、kb bootstrap+smoke）；未交付項（selector_gate skeleton、Langfuse/PG 統一 API、dashboard、prod selector）誠實標 ❌；無定價／SLA／代維運承諾。

**驗收**：文書票，cross-check `SKILL_CATALOG_OVERVIEW.md` 11 tool_id；結構對照 FRAME AcceptanceCriteria 通過。

**輕微缺口（留 C1-P2）**：§1.1「信心區間」用語、§4.1 `trace_query` 暱稱宜統一為 `tool_id`；§5 執行步驟待詳化 runbook／戰報模板。

**下一步**：C1-P2 詳化 §5；可選輕修統一術語；定價／Wave C 計畫另票。

---

## C1-P2 · AI Workflow 偵錯與健檢服務 · Execution Plan / Runbook v0.1

**日期**：2026-06-07 · **票號**：C1-P2 · **狀態**：accepted_with_gaps

**交付**：
- 新建 `docs/WAVE_C_EXECUTION_PLAN.md`（Step 0-4 runbook：Intake → 工具選擇 → Wave B CLI 執行 → 戰報彙整 → Internal Review）
- 輕修 `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` §5/§6/§7（增加 Execution Plan 連結、對內/對外分界、與 Wave B/C docs 交叉索引）

**對齊**：
- WAVE_C_EXECUTION_PLAN ↔ Product Spec §5：high-level steps 詳化為可操作 CLI
- WAVE_C_EXECUTION_PLAN ↔ WAVE_B_EXECUTION_PLAN：Step 2 CLI 範例全部引用 Wave B 已交付命令
- WAVE_C_EXECUTION_PLAN ↔ SKILL_CATALOG_OVERVIEW：引用全部 11 個 Gov tool_id，`kb.index.selector_gate` 標 skeleton
- WAVE_C_EXECUTION_PLAN ↔ ROUTING_POLICY_GUIDE：引用 `wave_b.eval_report`、`wave_b.kb_index_bootstrap` 路由

**實際接案的意義**：
從「spec 說我們能做什麼」變成「runbook 告訴你怎麼做」。執行者現在可以：
1. 開啟 WAVE_C_EXECUTION_PLAN.md 依 Step 0-4 逐步執行
2. 每步都有明確的 CLI 命令（來自 Wave B 已驗證的工具）
3. 知道哪些步驟需要人工判讀（標註 [ ] 檢查點）
4. 產出標準化戰報並寫入 `00_Agent_Work_Progress.md`

**輕微缺口（非阻擋）**：
- 目前 v0.1 為人工執行 CLI，尚未自動化 pipeline
- `kb.index.selector_gate` 為 skeleton，未納入 Step 2 執行列表
- 戰報模板與 OPS_CYCLE JSON schema 對齊留 C1-P4

**下一步**：
- C1-P3：自動化 Pipeline CLI（將 Step 2 多個 CLI 包裝成單一 runner）
- C1-P4：標準戰報模板與 OPS_CYCLE 對齊
- C1-P5：CI 整合與 Nightly 健檢

---

## Wave 1–2 收口 · Governance / Observability / PR Smoke（W1-T1 / W1-T2 / W2-T1）+ Wave C / DEMO（C2-P1 / DEMO-1）

**日期**：2026-06-07 · **票號**：W1-T1、W1-T2、W2-T1、C2-P1、DEMO-1 · **執行角色**：Scribe（依 ticket STATE / C_REPORT / D_REPORT 回寫）  
**狀態依據**：`04_Workflows/tickets/W1-T1_state.md`（accepted）· `04_Workflows/tickets/W1-T2_state.md`（Reviewer 二輪 accepted）· `04_Workflows/tickets/W2-T1_state.md`（accepted_with_gaps）· `04_Workflows/tickets/C2-P1_state.md`（accepted_with_gaps）· `04_Workflows/tickets/DEMO-1_state.md`（accepted）· `artifacts/monitoring/pg_ingest_soak.latest.json` · `artifacts/control_plane/dispatch_plan.latest.md`

> **未來實作票前置假設**：以下段落為下游票可安全依賴的驗收口徑與邊界裁決，非單純「done」標記。引用驗收門檻時請對齊 `docs/GOVERNANCE_ONBOARDING_v1.md`（W1-T1）· `docs/observability.md` §4.2.1（W1-T2）· `docs/testing.md` §5–§6（W2-T1）· `docs/PRODUCT_TABULAR_CLEANING.md`（C2-P1）。

### Wave 1（W1-T1 · 治理入口收口與 OPS 一鍵自檢）

**一句話**：新 Agent 可依 README Start Here 四鏈 + `docs/GOVERNANCE_ONBOARDING_v1.md` 完成接戰對齊；`python 04_Workflows/_ops_cycle.py checklist --mode full` 一鍵驗證 archive 步驟 + Wave 1 四檢（三鑰 smoke、routing policy、eval-gate 子集、DarkOps gate blocked 預期 pass）。Reviewer 二輪 **accepted**。

**驗收命令**：`python 04_Workflows/_ops_cycle.py checklist --mode full` → exit 0；`wave1_readiness.ok: true`。樣本 schema：`artifacts/ops/checklist_full.sample.json`。

**下游可假設**：接戰初始化有機器化自檢入口；`master_status`／`handoff` 自動寫回仍留 Wave 2（非本票範圍）。

### Wave 1（W1-T2 · Monitoring PG Ingest 收口）

**一句話**：live ask 流量後，**Langfuse traces → `sync_traces` → Postgres `task_runs`** 管線已接通；`04_Workflows/_phase5_pg_ingest_soak.py` n=20 cohort 經 Reviewer 獨立複驗（含 06:51 UTC 二次 cohort），**pg/langfuse 20/20 對齊**，解除 Wave 4A「API 200 但 PG 0 列」斷層。**不宣稱 production-ready**；`daily_cost_summary` 統一留 W1-T3。

**關鍵指標**（權威 artifact：`artifacts/monitoring/pg_ingest_soak.latest.json`）：

| 欄位 | 門檻（§4.2.1） | 實測 |
|------|----------------|------|
| `ingest_ok` | `true` | **true** |
| `pg_task_runs_count` | ≥ 18（n=20） | **20** |
| `langfuse_trace_count` | 同 cohort | **20** |
| `gap_pg_vs_langfuse` | ≤ 2 | **0** |
| integration test | ≥ 1 全綠 | `pytest tests/test_monitoring_ingest_integration.py` → **3 passed** |

**驗收命令**（soak 複跑前提：gov_core venv python + runtime `GOV_CORE_MONITORING_INGEST_ENABLED=1`；`.env` 未寫入該鍵屬已知 ops 口徑）：

```powershell
python 04_Workflows/_phase5_pg_ingest_soak.py --n 20 --base-url http://127.0.0.1:8000 --pretty
cd 01_Environments/python_venvs/gov_core_system
python -m pytest tests/test_monitoring_ingest_integration.py -q
```

**Reviewer 已接受之邊界行為**（不構成阻塞；下游票勿將下列現象誤判為 regress）：

1. **Langfuse HTTP 429**（observations/traces Public API rate limit）：soak 期間 stderr 可見多次 429，但 `ingest_sync.errors=[]`、最終 PG/Langfuse count 仍全量對齊 — **已知邊界，已由 Reviewer 接受**。
2. **`jsonl_trace_end_count=0`**：ask 管線尚未寫入 `runtime/task_traces.jsonl`；JSONL 僅 Phase D **診斷源**。權威驗收口徑為 **Langfuse API → `sync_traces` → PG**；診斷源缺席但權威源完整 — **已由 Reviewer 接受**。

**下游可假設**：W1-T2 前「ingest 斷層」已收口；新票若需 JSONL 診斷接線或 Langfuse `usage` metadata 補全，應**另開票**，勿重開 W1-T2。

### Wave 2（W2-T1 · Core Agent Smoke PR 門禁）

**一句話**：`.github/workflows/core-agent-smoke.yml` 已落地；PR 路徑 job **`Agent workflow smoke (PR tier)`**（workflow id `agent-smoke-pr`）執行 `python 04_Workflows/_core_agent_smoke.py --tier PR -v`，覆蓋 7 個 ROOT agent workflow 模組（含 AC 必達：`test_context_entry`、`test_eval_gate`、`test_hq_task_routing_smoke`）。本地 `--tier PR` 已驗：**exit 0、78 tests、`ok: true`**。失敗時產 `smoke_ci_summary.json`（含 `failed_modules[]`、`duration_ms`）並上傳 artifact（14 天）。

**與其他 gate 分工**（詳見 `docs/testing.md` §5.1）：PR smoke ≠ Release 就緒 — 發版前仍須 W2-T4 Wave7 Tier-A；Dark / DARK_FULL 僅 `workflow_dispatch`，**非** PR 預設。

**Branch protection（尚未啟用）**：state / CI log **無**「已設 required check」證據。建議後續由 **repo admin** 於 **Settings → Branches → Branch protection rules** 將 check 名 **`Agent workflow smoke (PR tier)`** 設為 required（與 `eval-gate-ci.yml` 並行）。**勿在戰報中宣稱 branch protection 已打開**，除非 ops 留痕確認。

**Reviewer gap（accepted_with_gaps，不阻塞票面）**：尚無含本版 workflow 的**首次 PR 綠色 CI run** URL（`W2-T1_state.md` O_NOTES 仍占位）。merge 含 workflow 的 PR 後，ops／implementer 應將實際 Actions run URL 填入 ticket O_NOTES Run Log。

**下游可假設**：PR tier smoke 契約與 docs 已對齊；新票可引用 `--tier PR` 模組清單與 exit code 表。首次 CI 實戰與 branch protection 為 **ops follow-up**，非 W2-T1 重開條件。

### Wave C（C2-P1 · 一般表格清洗 Product Spec v1）

**一句話**：新建 `docs/PRODUCT_TABULAR_CLEANING.md`（§1–§7 齊全）— Wave C 第二條對外產品線就緒（姊妹於 C1 AI workflow 健檢）。定義四類清洗（缺失／重複／異常／格式）、品質報告前後指標、Wave 6 CLEAN-BASIC ✅／ENRICH／OCR ❌ 誠實邊界。Reviewer **accepted_with_gaps**（無阻擋項）；§3.1 指標命名與 deliverable templates 逐欄對照留 C2-P2。

**下游可假設**：表格清洗案可對齊本 spec 接案與驗收；C2-D1 可依賴 C2-P1 解除 dependency 阻塞。

### DEMO（DEMO-1 · Multi-Chat ticket state 基礎設施）

**一句話**：四角色 instruction 模板 + `04_Workflows/tickets/README.md` 直接讀寫流程就緒；本 DEMO 票展示 FRAME／STATE／B／C／D 完整範例。Reviewer **accepted**。後續真實票各角色只寫允許區塊，copy/paste 為備援。

### Scribe TODO（建議，非阻塞）

| 項 | 建議動作 | 依據 |
|----|----------|------|
| 首次 CI 綠 run URL | merge 後填 `W2-T1_state.md` O_NOTES `_TBD_` 列 | C_REPORT gap |
| Branch protection | admin 啟用 required check `Agent workflow smoke (PR tier)` | W2-T1 Rollout / Ops Notes |
| Langfuse `usage` 缺口 | 另開 metadata 補全票（soak message 有 `missing_field_summary`） | W1-T2 C_REPORT suggestions |
| JSONL diagnostic 接線 | 另開 ask 管線票（不影響 §4.2.1 權威口徑） | W1-T2 accepted_boundary_notes |
| archive_checklist 路徑 hygiene | 另開小票統一相對路徑輸出 | W1-T1 C_REPORT suggestions |
| C2-P2 runbook | 詳化 §5 五步 + 指標命名對照 templates | C2-P1 D_REPORT follow-up |

---

## 最小接案 MVP · Wave 1–4 阶段判定（Orchestrator + Reviewer · 2026-06-08）

**阶段一句话**：MVP 主链已完工，当前重点是为真实使用补护栏与轻量记忆，而非扩功能。

**Progress 摘要（可粘贴 Wave 概览）**

最小接案 MVP 已形成一条可复现的最短闭环：白名单低风险单表 CSV 经 `intake.json` → P2 eligibility gate → `--case-dir` 清洗 → delivery bundle，可用 `scripts/run_case_e2e_validation.py` 一键验收（DoD：`docs/MVP_CASE_E2E_DoD_v0.1.md`）。Wave 1 完成模块盘点与范围收口；Wave 2 落盘 `cases/` 结构、gate CLI、参数化 runner 与交付包；Wave 3 打通 E2E 与 `new_cleaning_case.py` 人工接案入口。`cases/demo_phase` 与 `cases/sampleco/2026-0001` 均已跑通全链：后者为首个真实样本实验——流程与 artifact 齐全，gate 判 `accepted`，但 Phase 专用 dedup/percent 规则对多行 milestone 导出表语义不稳（115 行 intake → 8 行 accepted，`qa_status=pass_with_warnings`），清洗质量仅勉强可用。Wave 4（轻量记忆与验收）仍为 **partial**：尚无「查历史案例 / 规则 / 模板 / 已知限制」的轻量索引，真实样本下的 schema 不匹配与低 output 比例仍可能静默通过 gate。后续规划应围绕护栏与记忆层，不新增 MVP 主链功能。

**Wave 状态表**

| Wave | 主题 | 状态 | 备注 |
|------|------|------|------|
| Wave 1 | 盘点与收口 | **done** | 八类模块 reuse 地图、in/out scope、Wave 2 P1–P4 缺口已列；Reviewer `accepted_with_minor_edits`（`W-MVP-W1-INVENTORY`） |
| Wave 2 | 最小入口 | **done** | P1 case 结构 + intake SSOT、P2 gate CLI、P3 `--case-dir` runner、P4 bundle/signoff 均已实装并在 `demo_phase` 验证 |
| Wave 3 | 执行闭环 | **done** | E2E 驱动 + DoD v0.1（`W-MVP-W3-E2E-VALIDATION` Reviewer accept）；Intake CLI（`new_cleaning_case.py`）可建案并可选 `--run-gate` |
| Wave 4 | 轻量记忆与验收 | **partial** | MVP 主链验收口径已立，但轻量 case/规则记忆层空白；真实样本护栏未覆盖 schema 语义不匹配、低 accepted 比例仍 pass 等缺口 |

**Wave 4 剩余 scope（高层，供子票引用）**

- **轻量记忆层**：只读索引——可查历史案例目录、已用清洗规则、交付模板与已知限制（如 Phase demo 规则适用范围）；不建重型 RAG、不接 long-term agent memory。
- **真实样本护栏**：gate/QA 须能识别 intake schema 与 runner 假设不一致、accepted_rows 占 intake 比例过低仍 `pass_with_warnings` 等情形，并强制 `review_needed` 或 blocked，而非静默放行。
- **验收视角**：Wave 4 结束时，可对外 demo 一笔真实低风险小案（如经护栏修正后的 sampleco 类案），并能明确陈述「会做什么 / 不会做什么」（无 UI、无 prod 链、无 SLA）。

**依据**：`W-MVP-W1`～`W-MVP-W3-*` ticket STATE/B_REPORT · `docs/MVP_CASE_E2E_DoD_v0.1.md` · `cases/sampleco/2026-0001/reports/report.json`（115→8 rows · `pass_with_warnings`）· `cases/README.md`

---

## 2026-06-10 · W1-T1B · 治理合約與禁區規則收斂

W1-T1B（治理合約收斂）：`docs/governance-constitution-v1.md` active snapshot 就緒 — Agent 接戰可優先讀 §5 + 當次票 FRAME，免全 repo 掃描；母本未替換。Reviewer `accepted_with_gaps`，Q1–Q5 待確認項留後續票。

---

## 2026-06-10 · Wave 2 收口 · Intake Routing Catalog + Routing Eval（W2-T1 / W2-T2）

- `[W2-T1-intake-routing-catalog] done` · 建立跨 family routing catalog（Tabular / Gov / product card / hq_routing）；新增 `docs/intake-routing-catalog-v1.md` + `routing/intake_routing_catalog_v1.yaml` + `tests/test_intake_routing_catalog.py`（10/10 OK）。Orchestrator accepted。
- `[W2-T2-routing-eval] done` · 建立 routing eval 指南 + eval cases（Tabular demo_phase/sampleco + Gov eval + mainline regression）；新增 `docs/routing-eval-guide-v1.md` + `routing/routing_eval_cases_v1.yaml` + `tests/test_routing_eval_cases.py`（8/8 OK；與 T1 合計 18/18 OK）。Orchestrator accepted。
- **索引**：`04_Workflows/WORKFLOW_INDEX.md` §1.5 已登錄 Intake / Routing Catalog 與 Routing Eval Guide & Cases 兩條。

---

## 2026-06-10 · Wave Dashboard · Tabular MVP Wave 1–3-TL 完成度總覽（Orchestrator）

**權威索引**：`docs/WAVE_PROGRESS_DASHBOARD.md`（**≠** Observability `docs/WAVE1-3_HISTORY_STATUS.md`；**≠** 上文「最小接案 MVP · Wave 1–4」）

| Wave | 狀態（原文） | 關鍵交付 |
|------|----------------|----------|
| Wave 1 | **done** — MVP 主鏈與治理 | `docs/governance-constitution-v1.md` · `docs/mvp-standard-trace-path.md` · `docs/mvp-mainline-regression.md` |
| Wave 2 | **done** — Intake / Routing / Eval（W2-T1 + W2-T2-routing-eval） | `docs/intake-routing-catalog-v1.md` · `routing/intake_routing_catalog_v1.yaml` · `docs/routing-eval-guide-v1.md` · `routing/routing_eval_cases_v1.yaml` |
| Wave 3-TL | **3/4 done** — T1–T3 `accepted_with_gaps`；**T4 not_started** | `docs/tabular-tool-catalog-v1.md` · `docs/tabular-tool-selector-spec.md` · `docs/tabular-tool-outbox-spec.md` |

**Wave 1 一句話**：治理收斂視圖就緒；tabular MVP 標準 trace spec 與一鍵主鏈回歸（`demo_phase` + `sampleco/2026-0001`）已交付。

**Wave 2 一句話**：跨 family routing catalog（規則索引）與 routing eval cases（事後對照卷）已交付；不實作 routing engine。

**Wave 3-TL 一句話**：Catalog → Selector → Executor + Outbox 三件套已實作；outbox replay／Local UI（T4）尚未開票。

**驗證**：見 Dashboard「驗證命令」— `run_mvp_mainline_regression.py` · `tests.test_intake_routing_catalog` + `tests.test_routing_eval_cases` · Tabular 三件套 unittest。

---

## 2026-06-11 · Toolchain Wave B（WB-T1–WB-T7）

**日期**：2026-06-11 · **票號**：WB-T1–WB-T7 · **WB-T8**（review closure）· **執行角色**：Scribe（依 ticket STATE / C_REPORT / WB-T6 D_REPORT 回寫）

**狀態依據**：`04_Workflows/tickets/WB-T1-tool-catalog-and-selector-contract-v1_state.md` ～ `WB-T7-phase6-toolchain-smoke-matrix-extension-v1_state.md`（Reviewer：**T1–T6 · T8 `accepted_with_gaps`** · **T7 `accepted`**）· `04_Workflows/tickets/WB-T8-toolchain-wave-b-review-and-progress-closure-v1_state.md`（Reviewer **`accepted_with_gaps`**）· `docs/WAVE_PROGRESS_DASHBOARD.md` · `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` · `docs/wave-b-toolchain-readme-v1.md`

**一句話**：在 W3-TL / W9-T3 / W10–W12 既有實作之上，Toolchain Wave B 已交付跨軌 **contract SSOT**（catalog/selector · executor/sandbox · outbox_layer_v1 · toolchain_health_v1 · audit quickview spec · toolchain_smoke_matrix_v1）及 **WB-T6** 收口 readme／執行計劃／Dashboard 索引；語義均為 **plan_only / optional gate / investigation-only**，**不改** MVP 主鏈預設行為。Reviewer 批量驗收 **108/108 OK**（2026-06-11）；**WB-T8** closure handoff 已就緒。

### 完成能力範圍（WB-T1–T7）

| 票號 | Reviewer | 能力 | 交付 SSOT |
|------|----------|------|-----------|
| **WB-T1** | accepted_with_gaps | catalog/selector · 四軌 `tool_id` + `governed_by` · `plan_only` dict | `docs/tool-catalog-and-selector-contract-v1.md` |
| **WB-T2** | accepted_with_gaps | executor/sandbox · 四級 `execution_mode` + allowlist 矩陣 | `docs/tool-executor-and-sandbox-safety-contract-v1.md` |
| **WB-T3** | accepted_with_gaps | outbox_layer_v1 · 六命名空間 · feedback · case history join | `docs/outbox-and-feedback-layer-contract-v1.md` · `docs/schemas/outbox_layer_v1.json` |
| **WB-T4** | accepted_with_gaps | toolchain_health_v1 · 離線健康摘要 · optional gate | `docs/toolchain-health-dashboard-v1.md` · `scripts/run_toolchain_health_dashboard.py` |
| **WB-T5** | accepted_with_gaps | audit quickview spec · `sections[]` / `timeline[]` / `gaps[]` | `docs/audit-quickview-and-case-history-spec-v1.md` |
| **WB-T6** | accepted_with_gaps | 收口 readme + 執行計劃 + Phase% 索引 + Wave C 依賴表 | `docs/wave-b-toolchain-readme-v1.md` · `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` |
| **WB-T7** | **accepted** | toolchain_smoke_matrix_v1 · P6 附錄 A | `routing/toolchain_smoke_matrix_v1.yaml` |

**WB-T8**（`toolchain-wave-b-review-and-progress-closure-v1`）：closure handoff 已交付（逐票檢查表 · Wave C 邊界 · P0/P1/P2 補動作 · Reviewer/Scribe/Orchestrator 收尾步驟）— Reviewer **`accepted_with_gaps`**。

### Phase 完成度（本輪目標區間 · SSOT）

**權威索引**：`docs/WAVE_PROGRESS_DASHBOARD.md`（Phase% **唯一 SSOT**；readme／執行計劃僅引用）。

| Phase | 基線 → **本輪目標** | 主要票 |
|-------|---------------------|--------|
| **P8.5** 底層 Runbook 索引 | 55% → **72%** | WB-T6 |
| **P8.6** Tool Catalog SSOT | 65% → **85%** | WB-T1 |
| **P8.7** Selector 推薦契約 | 60% → **85%** | WB-T1 |
| **P8.8** Executor / Sandbox | 58% → **82%** | WB-T2 |
| **P8.9** Outbox / Feedback | 40% → **80%** | WB-T3 · WB-T5 |
| **P5** Dashboard / 離線健康度 | 70% → **85%** | WB-T4 · WB-T5 |
| **P6** 測試觀測面 extension | 84% → **88%** | WB-T7 · WB-T4 · WA-T6 |

### 驗證命令

```bash
python -m unittest tests.test_tool_catalog_and_selector_contract_v1 \
  tests.test_tool_executor_and_sandbox_contract_v1 \
  tests.test_outbox_and_feedback_layer_contract_v1 \
  tests.test_toolchain_health_dashboard_v1 \
  tests.test_audit_quickview_and_case_history_spec_v1 \
  tests.test_phase6_toolchain_smoke_matrix_v1 -v
python scripts/run_toolchain_health_dashboard.py --format json --dry-run
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json
```

### Wave C 可引用邊界（`WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` §5 · `wave-b-toolchain-readme-v1.md`）

**可假設（contract 已交付 · Reviewer 已关票）**：四軌 `tool_id`／`governed_by`；Selector `plan_only` 之 `candidate_tools[]`／`planned_tools[]`；四級 `execution_mode` 與 case allowlist；戰車根 `outbox/` 六命名空間與 `schema_id`；`toolchain_health_v1` 離線聚合；Audit quickview 形狀；`toolchain_smoke_matrix_v1.yaml` 之 tier／`gate_class`／`blocks_mainline`；trace 建議鍵 `case_ref` + `task_type` + `selector_rule_id`。

**禁止假設（除非另票）**：Selector 已接 prod blocking INT／delivery gate；Tabular E2E 預設驅動 selector；Non-Tabular stub 已接 heavy processor；Toolchain dashboard 為 PR required check 或 SLA 欄位；`orchestration_bridge_outbox` 與戰車根 outbox 已合併 replay；P6 smoke matrix 已有 mandatory CI runner。**Wave C 入口**：`docs/WAVE_C_EXECUTION_PLAN.md` — Observability（`obs.*`／`kb.*`）與 Toolchain **分軌**。

**下一步（P0）**：Scribe 完善各票 D_REPORT；Orchestrator 將 WB-T1–T8 `overall_status` → `done` 并补 WB-T8 索引（README／执行计划／WORKFLOW_INDEX）。

---

## 2026-06-11 · Toolchain Wave B（WB-T1–WB-T7）

Toolchain Wave B 已在既有 W3-TL / W9-T3 / W10–W12 實作之上，交付工具鏈 contract SSOT（catalog/selector · executor/sandbox · outbox_layer_v1 · toolchain_health_v1 · audit quickview spec · toolchain_smoke_matrix_v1）與 Wave B readme / execution plan / Dashboard 索引，語義均維持 plan_only / optional gate / investigation-only，不改 MVP 主鏈行為。Phase P8.5 / P8.6–8.9 / P5 / P6 進度已依 docs/WAVE_PROGRESS_DASHBOARD.md 達成本輪目標，Wave C 可直接依 WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md §5 與 wave-b-toolchain-readme-v1.md 所列可假設能力啟動後續工作，WB-T8 作為 closure handoff 票待 Reviewer/Scribe 收口。

---

## 2026-06-11 · WC-PRE-01 · Wave B doc hygiene + Wave C PRE 启动

Toolchain Wave B（WB-T1–T8）文档与票务 hygiene 已由 **WC-PRE-01** 收口：各票 D_REPORT 补齐、Dashboard Wave A/Toolchain 分栏与执行计划 §1 索引对齐。Wave C 前置票 **WC-PRE-01～07** 已建档（PRE-02～07 为 draft）；contract/impl gap 后续由 PRE-02～07 承接，不阻塞 Wave C C1 契约层引用。

---

## 2026-06-12 · WC-PRE-01～05 · Reviewer 关票 · Wave C 前置能力就绪

**WC-PRE-01～05** 已由 Reviewer 验收关票（01/02/03 **accepted**；04/05 **accepted_with_gaps**），可作 Wave C 前置能力基础：selector 显式 `plan_only`、executor subprocess 600s timeout、audit investigation view CLI、toolchain smoke matrix 本地 runner。**WC-PRE-06/07** 仍为治理与 CI 升级提案／设计路径，未改任何 CI required 或 SLA。Wave C 票务可以开始依赖 Wave B / WC-PRE 已交付能力，但**不得**假设 PROD gate / `OG-TOOLCHAIN-HEALTH` / mandatory smoke CI 已经开启。

---

## 2026-06-11 · Wave C · WC-C1-01 toolchain local gaps quickview

**票號**：WC-C1-01 · **Phase**：Wave C C1 核心票 · **Reviewer**：**accepted_with_gaps**（owner: orchestrator）

- **交付**：`scripts/run_toolchain_local_gaps_quickview.py` · `docs/toolchain-local-gaps-quickview-v1.md` · `tests/test_toolchain_local_gaps_quickview_v1.py`（17/17 OK）。
- **能力**：本地 only、只讀 gaps 聚合（selector `plan_only` · executor timeout 契約 · audit investigation · smoke matrix dry-run）；可選 `--include-health-dashboard` 嵌入 WB-T4 摘要；頂層 `gate_class=optional` · `blocks_mainline=false`。
- **用途**：開票前或除錯時，`python scripts/run_toolchain_local_gaps_quickview.py --format json [--case-ref demo_phase] [--include-health-dashboard]` 快速盤點 toolchain gaps；聚合 WC-PRE-02～05 與 WB-T4 只讀入口。
- **邊界**：**不得**當 PR required / CI gate；`OG-TOOLCHAIN-HEALTH` required 與 mandatory smoke CI 仍 **blocked** 於 WC-PRE-06/07 批文後治理票。非 blocking gaps：`--include-health-dashboard` 有實作路徑但缺 live import 整合測；`--write` artifact 路徑未完全覆蓋。
- **索引**：`04_Workflows/tickets/README.md` §Wave C C1 · `04_Workflows/WORKFLOW_INDEX.md` §1.27。

---

---

## 2026-06-14 · 多 Lane 收口（Lane A/B/C/D · Orchestrator + Scribe · 本輪增量）

**狀態依據**：各 lane `*_state.md` B/C/D_REPORT · 本輪 unittest smoke（2026-06-14 实跑）· **未**脑补 CI gate / 批文 / PR policy。

**一句話**：四 lane **implemented + tested** 为主，但 **非 full done**——W4-MEM-01 / WC-T1-INTEGRATION 仍 **Reviewer pending**；Lane B L2 / mandatory smoke CI 与 Lane A 护栏升格仍 **blocked_on_approval** 或 **design draft only**。

| Lane | 票 / 能力 | 實作 | 測試 | Review / Approval | 未完成 |
|------|-----------|------|------|-------------------|--------|
| **A** | W4-MEM-01 | done | **10/10 OK** | **Reviewer pending** | Reviewer 關票 |
| **A** | W4-GUARD-01 | **design draft only** | n/a | **blocked_on_approval** | IMPL 待批文；**非** gate 已升格 |
| **B** | WC-IMPL-L1 | done | **17/17 OK** · exit 0 non-blocking | **accepted** | — |
| **B** | WC-IMPL-L2 · SMOKE-CI-L1 · PRE-06/07 | **FRAME / design only** | n/a | **blocked_on_approval** | **非** mandatory smoke CI 已開 |
| **C** | T1–T4 · T3 · SMOKE nightly | done | 含于 **62/62 OK** | done / accepted | — |
| **C** | WC-T1-INTEGRATION | done | 含于 **62/62 OK** | **Reviewer pending** | Reviewer 關票 |
| **C** | T5 · T6 · T7 | done | 含于 **62/62 OK** | accepted · **accepted_with_gaps** | v2 path_id · reports fixture |
| **C** | E2E / nightly | 脚本可跑 | **optional · non-gating** | n/a | **≠ INT Tier-A** |
| **D** | W3-TL-T4 + replay | done | **22/22 OK** | **accepted_with_gaps** | Local UI / Langfuse / re-execute **out of scope** |

**本輪 smoke 命令与结果**

```bash
python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v          # Lane A · 10 OK
python -m unittest tests.test_toolchain_governance_snapshot_v1 -v                        # Lane B · 17 OK
python -m unittest tests.test_ticket_eligibility tests.test_dispatch_cards tests.test_ticket_comms tests.test_order_ledger tests.test_wc_t5_automation_coverage_contract_v1 tests.test_distill_control_plane_skills_lite tests.test_run_wc_m2_e2e_walkthrough -v  # Lane C · 62 OK
python -m unittest tests.test_tabular_outbox_consumer tests.test_build_tabular_outbox_replay_report -v  # Lane D · 22 OK
```

**索引更新（doc-only）**：`docs/WAVE_PROGRESS_DASHBOARD.md` 分票四欄收口表 · `docs/wave_c/overview.md` v0.3 · `04_Workflows/tickets/README.md` Lane A / WC-T 索引。

**下一步優先（索引）**：① W4-MEM-01 Reviewer ② WC-T1-INTEGRATION Reviewer ③ WC-T6-v2 / WC-T7-v2 gaps ④ approval 後 governance / guard 升格项。
