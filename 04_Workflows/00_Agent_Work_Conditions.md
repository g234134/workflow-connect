# 00 Agent Work Conditions

## 目的

本檔為「大唐三省六部」多 Agent 協作的全域工作規範。  
所有 Cursor Agent / Chat Agent 在開始工作前，必須先閱讀本檔，並依本檔約束執行。

## 文件定位、適用範圍與版本慣例

### 文件定位

- 本檔為**長期有效**的總部層規則：約定邊界、責任、協作紀律、交付與禁止事項等**原則**。
- 本檔**不**承載快速過期的實作細節；細節應落在程式碼與各 Agent 的 `brief.md` / `notes.md` 中。

### 適用範圍

- 適用於所有在本 repo 內因任務而被指派的 Cursor / Chat Agent（單次或多輪協作皆同）。
- 若使用者當次指令與本檔衝突，以使用者**明確指令**為準，但負責該任務的一方須在自身的 `progress.md` 或 `notes.md` 留下**簡要紀錄**（偏離原因與影響範圍），避免後續 session 失憶。

### 長期制度與短期階段資訊

- **應留在本檔（Conditions）**：不隨迭代改寫的原則，例如角色邊界、目錄層級意義、禁止事項、DoD 類別、fallback 與回報格式等。
- **應放在 `04_Workflows/00_Agent_Work_Progress.md`**：當前迭代目標、任務拆解、進度打勾、短期阻塞與「誰承擔哪一項」。
- **應放在 `project_status/master_status.md`、`project_status/handoff.md`（若專案有啟用）**：跨 Agent 的執行快照、交接給下一個 chat 的上下文、最後一次已知良好（last known good）狀態。
- 本檔後段的**當前總目標／階段說明**屬**短命資訊**，僅作對照；里程碑變更後，應將其中仍成立的**事實與決策摘要**同步寫回 Progress 或 handoff，並在該狀態檔標註**修訂日期**，避免過期敘述被誤當制度。

### 版本慣例

- 條文變更以**小步、可 review 的 diff**為主：標題層級盡量穩定、列表扁平，避免大段無意義搬移。
- 本檔結構或重大意涵調整時，維護者應在 commit／PR 說明（或同資料夾註記）留**一句話 Changelog 摘要**，方便其他 chat 引用時對齊版本認知。

---

## 當前總目標

本輪目標是建立「四大板塊 × 四個 Agent」的可執行協作框架，並讓它們在不破壞現有 Phase1 基線的前提下開始工作。

目前已知已驗證可用的基線：

- PostgreSQL 已可連線。
- Qdrant 已可連線。
- `.env` 已與實際 DB 狀態對齊。
- `DATABASE_URL` 已可成功執行 `pg_ok`。
- `phase1_verify.py` 已成功跑出 `ASSERT: OK` 與 `OK: verify passed`。

### 當前階段說明（更新）

- 第一階段目標（已完成）：  
  - 建立四個 Agent 的骨架（Infra / Data / RAG / Governance）。  
  - 建立 core SDK（infra_health / data_pipeline / rag_backend / orchestrator）的最小可執行版本。  
  - 打通 Phase1 的 Postgres + Qdrant + phase1_verify 程式化健康檢查（Infra Agent 的 all_ok 已可為 True）。

- 第二階段目標（進行中）：  
  - 由 Data Agent 將 ingest_batch() 從 skeleton 實作為真實 ingest pipeline。  
  - 由 RAG Agent 將 answer_question() 連接 Qdrant / Postgres / LLM，完成 Phase1 的實際問答能力。  
  - 由 Governance Agent 將「健康檢查 → ingest → verify」包裝為一鍵工作流，並自動更新 master_status / handoff。

---

## 角色與責任邊界（Infra / Data pipeline / RAG / Orchestration·Governance）

以下以**檔案歸屬**為準；除本檔另有規定或使用者明確授權外，**不得**修改其他角色負責的 `core/*.py`、對應 department agent 腳本，或他人 `agent_workspace/*` 內文件。

### Agent A：Infra（基礎設施健康檢查）

- **擁有（可改）**：`core/infra_health.py`、`Departments/04_Infrastructure/agents/infra_health_agent.py`、自身 `agent_workspace/infra_agent/*`。
- **負責**：PostgreSQL / Qdrant / `phase1_verify` 相關之**健康檢查與診斷輸出**（僅限讀取／呼叫既有驗證流程所需；不變更驗證腳本本體，細節依後文禁止事項）。
- **不負責**：ingest／批次資料語意、向量索引內容、RAG 檢索與生成策略、orchestrator 業務流程編排。
- **Observability（輕量）**：健康檢查回傳 `dict` 應便於上層聚合，至少能表達**檢查項 id、ok、message、關鍵耗時或錯誤碼**之一組合（欄位名稱與後端無強制，但同一 repo 內應一致、可 grep）。

### Agent B：Data pipeline（資料管道）

- **擁有（可改）**：`core/data_pipeline.py`、`Departments/04_Infrastructure/agents/data_pipeline_agent.py`、自身 `agent_workspace/data_agent/*`。
- **負責**：ingest／verify 相關之**資料流契約**（輸入輸出欄位、批次邊界、錯誤語意）、與 pipeline 直接相關之包裝與 CLI 入口。
- **不負責**：infra 連線檢查實作細節、RAG 查詢與 prompt 策略、orchestrator 一鍵工作流（除非使用者明確指派跨檔修補，且仍應在 notes 記錄）。
- **Observability（輕量）**：ingest／verify 回傳應帶有**可追蹤 run 的識別**（例如 `batch_id` / `job_id` 或等價欄位）與**列級或檔級統計**（成功／失敗計數等擇一），供 Governance 匯總與除錯。

### Agent C：RAG（檢索與問答後端）

- **擁有（可改）**：`core/rag_backend.py`、`Departments/04_Infrastructure/agents/rag_query_agent.py`、自身 `agent_workspace/rag_agent/*`。
- **負責**：查詢入口、retrieval、與 LLM 呼叫之**後端組裝**（含對 Qdrant／Postgres 的讀取路徑，以本專案既有設計為限）。
- **不負責**：ingest 主流程與離線批次清洗、infra health 檢查、orchestrator 步驟狀態機。
- **Observability（輕量）**：問答路徑應能留下**可查 log 或 dict 欄位**（例如 `query_id`、`retrieved_count`、`model`、`latency_ms` 擇要），避免「只有自然語言 print」而無法被 orchestrator 匯總。

### Agent D：Orchestration·Governance（編排與治理）

- **擁有（可改）**：`core/orchestrator.py`、`Departments/04_Infrastructure/agents/orchestrator_agent.py`、自身 `agent_workspace/governance_agent/*`；以及依專案慣例維護之 `project_status/master_status.md`、`project_status/handoff.md`（與後文「全局狀態檔」一致時，以**單一寫入權責**為原則：預設由此角色更新，其他角色僅回報、不直接改寫）。
- **負責**：將健康檢查、ingest、verify、RAG 呼叫等步驟**串成可重跑的工作流**；統一錯誤語意與步驟命名；在 handoff 寫入「下一 chat 需要知道什麼」。
- **不負責**：取代其他三個 `core` 模組內的領域邏輯實作（僅呼叫與組裝，不在此擴寫業務細節）。
- **Observability（輕量）**：orchestrator 應對外給出**步驟級摘要**（例如 `step`、`ok`、`duration_ms`、`error_code` 擇要），並在失敗時把**可定位指紋**寫進 handoff（依賴哪個下層 `message`／`job_id`／`query_id` 擇一可追溯即可）；**metrics backend**（Prometheus 等）非本檔範圍，但若專案啟用，由此角色定義「從上述 dict 如何對應到監控欄位」之單一出口，避免各模組各自發明格式。

### 互踩防護（共通）

- 需要改動非本人擁有之 `core` 檔案時：**先停**，改以 fallback／介面 stub／或在自身 workspace 提出「所需契約」與阻塞；除非使用者明確授權並要求在 notes 留痕。
- 與監控／除錯相關之**跨模組欄位命名**若有歧義，以 **Governance 匯總處**為準做一次性對齊，並在 `handoff.md` 或 `notes.md` 記錄約定，避免各 Agent 各自改名造成觀測斷裂。

---

## 全域目錄規範

### 總部層（HQ / Core）
以下屬於總部層共用模組：
- `core/__init__.py`
- `core/infra_health.py`
- `core/data_pipeline.py`
- `core/rag_backend.py`
- `core/orchestrator.py`

這些檔案是全系統共用 SDK。  
各暗部 Agent 可以 import 使用，但不可越權改動不屬於自己責任的檔案。[cite:508][cite:511]

### 暗部層（Agent Workspace）
每個 Agent 都應有自己的工作空間：
- `agent_workspace/infra_agent/`
- `agent_workspace/data_agent/`
- `agent_workspace/rag_agent/`
- `agent_workspace/governance_agent/`

每個工作空間至少包含：
- `brief.md`
- `progress.md`
- `notes.md`

### 執行層（Department Agents）
實際可執行的 agent 腳本放於：
- `Departments/04_Infrastructure/agents/`

---

## 共同工作原則

1. 先文件，後程式。  
   每個 Agent 先建立 `brief.md`、`progress.md`、`notes.md`，再開始寫 code。[cite:507][cite:515]

2. 只改自己負責的範圍。  
   每個 Agent 只能修改自己職責範圍內的檔案。若依賴其他檔案不存在，應 fallback 並在 progress / notes 中記錄，不可擅自接管別人的工作。[cite:506][cite:508]

3. 先做可執行 skeleton，再做完整功能。  
   第一輪重點是建立結構、責任邊界與可執行骨架，不強求一次完成所有真實邏輯。[cite:510][cite:515]

4. 所有核心函式回傳 `dict`。  
   不可只 `print()`，必須能被其他 Agent / Orchestrator 程式呼叫。

5. 所有 Agent 腳本必須可直接執行。  
   執行方式預設為 Python CLI，必要時可自行補 `sys.path` 讓 `core` 可被 import。

6. 任何阻塞都要寫進 progress.md。  
   不能默默跳過，也不能假裝完成。[cite:507][cite:509]

---

## 禁止事項

以下事項所有 Agent 一律禁止：

- 不可修改 `.env`
- 不可刪除既有 `phase1_verify.py`
- 不可搬移既有資料夾結構
- 不可覆蓋其他 Agent 的 `brief.md / progress.md / notes.md`
- 不可把四個 Agent 混成一個檔案
- 不可把 placeholder 假裝成已完成真功能
- 不可編造不存在的路徑、函式、環境變數或資料流程
- 不可未經確認就重構既有 verify / ingest 主流程

這些限制是為了避免多 Agent 協作時互踩與上下文污染。[cite:508][cite:513]

---

## fallback 規則

若 Agent 依賴的內容尚不存在：

- 可以建立最小可執行 skeleton
- 可以用 `try/except import` 做防呆
- 可以回傳：
  - `{"ok": False, "message": "dependency not found: ..."}`
- 必須同步寫入：
  - 自己的 `progress.md`
  - 自己的 `notes.md`

不可因依賴缺失而直接崩潰，也不可直接接管別的 Agent 的檔案。[cite:507][cite:511]

---

## Definition of Done（全域）

一個 Agent 若要被標記為「本輪完成」，至少需同時滿足：

- 已建立自己的 `brief.md`
- 已建立自己的 `progress.md`
- 已建立自己的 `notes.md`
- 已建立至少一個可直接執行的 agent 腳本
- 已建立或維護對應的 `core/*.py`
- `progress.md` 已寫入：
  - 已完成項
  - 未完成項
  - 阻塞
  - 下一步

---

## 回報格式

每個 Agent 完工回報時，至少要包含：

1. 新建 / 修改了哪些檔案  
2. 哪些檔案是可執行 skeleton  
3. 哪些功能仍是 placeholder  
4. 當前阻塞  
5. 下一步建議

---

## 全局狀態檔

以下兩份檔案屬於全局層：

- `04_Workflows/00_Agent_Work_Conditions.md`：本規範檔
- `04_Workflows/00_Agent_Work_Progress.md`：全局進度總表

此外，治理層可另維護：
- `project_status/master_status.md`
- `project_status/handoff.md`

---

## 工作順序建議

建議順序如下：

1. Infra Agent
2. Data Agent
3. RAG Agent
4. Governance Agent

若必須並行，則：
- 各 Agent 僅能在自己責任範圍內工作
- Governance Agent 需容忍其他模組尚未完成的 fallback 狀態

---

## 最後原則

所有 Agent 的工作重點不是「一次做完所有東西」，而是：
- 建立清晰邊界
- 穩定保留上下文
- 讓後續 session / 後續 agent 能接手而不失憶。[cite:507][cite:515]

---

## HQ 多智能體協作輪（修訂 2026-05-17 · 尚書省定案）

### 本輪總目標

- 暗部根路徑定案；多 worker 依黑板協作；第一階段僅總部治理層與工具層施工，暗部維持 Blocked。
- 施工前須收到尚書省明確授權（本輪已授權：治理黑板追加 + 工具層盤點文檔）。

### 專案根與暗部根（定案）

- **實例路徑**：見 `04_Workflows/INSTANCE_ANCHOR_TANG.md` §2（I01–I02）。
- **制度**：不得假設暗部根在戰車根直下之錯誤路徑；遷移須另開戰役並更新 `04_Workflows/Master_Map.json` 與 Progress 黑板。

### 暗部硬禁區（只讀、不寫）

- **類型**：見 `HARNESS_CONSTITUTION.md` §7.1（Z-*）。
- **本戰車逐條路徑**：見 `INSTANCE_ANCHOR_TANG.md` §4（I03、I07）；**禁止**在 Conditions 複製長路徑清單以免與 W5 雙源。

### 角色與邊界（HQ 輪）

| 角色 | 職責 |
|------|------|
| HQ-Coordinator | 規劃、任務卡、驗收定義；不直接改 code |
| HQ-Governance-Worker | 黑板末尾追加、`Master_Map.json`／`AGENTS.md`（授權時）、`07_Knowledge\` |
| HQ-Tooling-Worker | `01_Environments/config` 下 `services`／`tools`／`mcp` 盤點與索引（實例路徑見 W5 §5） |
| DarkOps-Worker | 暗部根下 `core\`、`Departments\`、`dark_ops\`、`output\`（**第一階段 Blocked**） |
| QA-Reviewer | 唯讀驗證；可於 Progress 末尾追加 QA 結論列 |

### 各 worker 可碰路徑（第一階段）

- **HQ-Governance-Worker**：`00_Agent_Work_Conditions.md`、`00_Agent_Work_Progress.md`（僅末尾追加）
- **HQ-Tooling-Worker**：`01_Environments/config` 下 services／tools／mcp（見 `INSTANCE_ANCHOR_TANG.md` §5）
- **DarkOps-Worker**：**Blocked**（不得對暗部根內任何檔案新增／修改／刪除）
- **QA-Reviewer**：全樹唯讀；Progress 末尾 QA 列（追加）

**絕對路徑表**（I06）：僅維護於 `INSTANCE_ANCHOR_TANG.md` §5，本檔不重複。

### 協作規則

- 黑板僅末尾追加，禁止覆蓋、刪除或重排既有段落。
- 阻塞以「待確認項目」六行格式寫入 `00_Agent_Work_Progress.md`。

### 停工條件

- 未收到尚書省施工授權；需碰暗部硬禁區；路徑與 `Master_Map.json` 衝突且無授權；DarkOps 未另開票。

---

### Gov Core V1 最小 Smoke Test（標準）

- 目的：定義「系統活著」的最低驗收標準。
- 路徑：Infra health → 單檔 ingest/verify（AGENTS.md） → orchestrator ingest_verify。
- 判定條件（節錄）：
  - infra_health all_ok: true（含 pg_ok、qdrant_ok、verify_ok）
  - data_ingest: chunks > 0、collection=document_chunks、ingest.ok=true
  - orchestrator_ingest_verify: ok=true、mode=ingest_verify、master_status.ok=true
- 詳細一次成功案例：見 `00_Agent_Work_Progress.md` 內 2026-05-17 條目。


---

### Gov Core V1 — RAG Smoke Test 標準（v0.1）

- 入口：`Departments/04_Infrastructure/agents/rag_query_agent.py answer`
- collection：`document_chunks`（須已含 AGENTS.md ingest）
- 驗收條件：
  - `ok: true`
  - `len(sources) >= 1`
  - 至少一筆 `sources[].doc_key` 或相關欄位顯示為 AGENTS ingest（例如 `.../AGENTS`）
  - `RUNTIME_METRIC.duration_ms` 有值
- retrieve-only 模式（非必要但建議）：
  - `len(hits) >= 1`
  - `hits[0].payload` 或 `documents_lookup` 能清楚看出來自 AGENTS.md
- 詳細一次成功案例：見 `00_Agent_Work_Progress.md` 中 2026-05-17 RAG_Smoke_Test 條目。

---

### Phase 2 — KB Index Smoke Test（Wave B · v0.1）

- 入口：`workflow_v2/kb/repo_index_bootstrap.py`；manifest RAG smoke：`workflow_v2/kb/rag_index_smoke.py`
- scope 權威：`workflow_v2/kb/wave_b_gov_scope.json`；runbook 見 `workflow_v2/20_pilot/W3-B/W3-B_index_pipeline_runbook.md` 附錄 A
- 單測：`python -m unittest tests.test_kb_index_bootstrap -v`
- 判定條件（節錄）：
  - `index_status_*`：`status=succeeded`；`file_count>0`；`chunk_count>0`；`manifest_ref` 非 `.sample.`
  - `wf_kb_index_sync.ps1` 回填後案卷 `kb_index_status=ready`
  - `wf_kb_index_gate.ps1 -TargetImpState IMP-AI-READY` → `verdict=allow`
  - manifest RAG smoke：`ok=true` 且 `hit_count>=1`
- 詳細成功案例：見 `00_Agent_Work_Progress.md` 中 `WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE` 條目。

