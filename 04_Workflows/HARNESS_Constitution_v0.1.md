# HARNESS 憲法 v0.1

> **SUPERSEDED（2026-05-19）**：本檔已由 `04_Workflows/HARNESS_CONSTITUTION.md` 取代。僅供歷史稽核；接戰與施工請讀正式檔。裁決見 `project_status/HQ_PHASE1_FINALIZATION_ORDER.md`。

> **來源**：`04_Workflows/00_Agent_Work_Conditions.md`、`04_Workflows/00_Agent_Work_Progress.md`、`AGENTS.md`（接戰／封存／紅線）、`04_Workflows/Master_Map.json`（v2.60 敘述）、本 session 已整理之 HARNESS 骨架。  
> **性質**：本稿為依現有材料蒸餾之草稿；未單獨讀取 `ENGINEERING_CONTRACT_v0.1.md` 實體檔（該檔由本 session 同步起草）。

---

## 文件定位

| 項目 | 說明 |
|------|------|
| **名稱** | HARNESS 憲法 v0.1 |
| **層級** | 戰車「總部層」長期制度文件 |
| **適用對象** | 所有在本 repo 內因任務被指派的 Cursor / Chat Agent、HQ 協作輪各 worker |
| **與其他文件關係** | 本檔定**原則與邊界**；實作節奏與工程紀律見 `ENGINEERING_CONTRACT_v0.1.md`；當前迭代進度見 `00_Agent_Work_Progress.md`；路徑權威見 `Master_Map.json`；接戰／封存見 `AGENTS.md` |
| **修訂原則** | 條文變更採小步可 review 之 diff；結構性調整須附一句話 Changelog |

---

## 1. 總則

### 1.1 本系統是什麼

- **HARNESS**（本憲法所稱之治理框架）指：大唐三省六部戰車內，以**文件定邊界、以黑板留痕、以可程式化 `dict` 串接模組**之多 Agent 協作制度。
- **目的**：建立清晰責任邊界與可接手上下文，使後續 session / worker 能接手而不失憶、不互踩。
- **工作節奏**：先文件後程式；先做可執行 skeleton，再逐步替換為真實邏輯（與 `ENGINEERING_CONTRACT` 對齊）。

### 1.2 本系統不做什麼

- 不追求單次對話內完成所有功能。
- 不以 placeholder 冒充已完成之真功能。
- 不編造不存在的路徑、函式、環境變數或資料流程。
- 不擅自修改 `.env`、不刪除 `phase1_verify.py`、不搬移既有資料夾結構。
- 不覆蓋其他 Agent 的 `brief.md` / `progress.md` / `notes.md`。
- 不把四個暗部板塊 Agent 混寫於單一檔案。
- 未經尚書省授權，不對暗部硬禁區寫入、不啟動 DarkOps 施工（第一階段預設 **Blocked**）。

### 1.3 衝突與 override

- 尚書省**當次明確指令**優先於本憲法條文。
- 發生偏離時，執行方須於自身 `progress.md` 或 `notes.md`（或 Progress 黑板末尾）留下**簡要紀錄**：偏離原因、影響範圍、是否為一次性 override。
- 觸及**高風險禁區**（`.env`、暗部 venv 樹、清算類腳本）時，即使收到 override，仍須先**明示風險**再執行。

---

## 2. 國家結構：總部 / 暗部 / 戰線 / 工具

### 2.1 總部（HQ）

| 項目 | 內容 |
|------|------|
| **專案根** | `D:\大唐三省六部\` |
| **職責** | 全局規範、黑板、地圖索引、知識沉澱、戰車 runner 與工作流 |
| **核心文件** | `04_Workflows/00_Agent_Work_Conditions.md`、`04_Workflows/00_Agent_Work_Progress.md`、`04_Workflows/Master_Map.json`、`AGENTS.md` |
| **可選狀態檔** | `04_Workflows/project_status/master_status.md`、`handoff.md`（目錄與自動寫回為 Phase 2 目標；v0.1 不強制已存在） |

### 2.2 暗部（Dark / Gov Core System）

| 項目 | 內容 |
|------|------|
| **唯一工作區根** | `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\` |
| **承載** | venv（環境層）與業務層（`core\`、`Departments\`、`dark_ops\`、`output\` 等） |
| **禁止假設** | 不得建立或搬移至 `D:\大唐三省六部\gov_core_system\`；遷移須另開戰役並更新 `Master_Map.json` |
| **第一階段** | DarkOps-Worker **Blocked**（僅總部治理層與工具層文檔施工，2026-05-17 基線） |

### 2.3 戰線（Chariot）

| 項目 | 內容 |
|------|------|
| **雙艙** | `gov_main`（工廠主線）、`gov_agency`（副艙／Wave／偵察等） |
| **六部** | `01_Environments` … `06_Exports_Output`（相對路徑以 `Master_Map.json` 為準） |
| **執行態** | `04_Workflows/Status.json`、`Chariot_Registry.db`、刑部 `05_Temp_Cache`（別名 `xing_bu`） |
| **口令** | 「接戰」→ `AGENTS.md` §初始化校準；「封存」→ §封存協議 |

### 2.4 工具（HQ Tools Layer）

| 項目 | 內容 |
|------|------|
| **根** | `01_Environments/config/`（`cursor`、`tools`、`mcp`、`services`） |
| **職責** | 工具盤點、索引、registry；**嚴禁**向 `gov_core_system` venv 安裝 HQ 工具套件 |
| **已知交付** | `config/mcp/_registry/registry.md`（第一階段唯讀盤點，2026-05-17） |

---

## 3. 多智能體協作輪：角色與分工

### 3.1 HQ 輪角色（2026-05-17 定案）

| 角色 | 職責 | 第一階段狀態 |
|------|------|----------------|
| **HQ-Coordinator** | 規劃、任務卡、驗收定義；不直接改 code | 活躍 |
| **HQ-Governance-Worker** | 黑板末尾追加、`Master_Map.json` / `AGENTS.md`（授權時）、`07_Knowledge\` | 活躍 |
| **HQ-Tooling-Worker** | `config/services`、`tools`、`mcp` 盤點與索引 | 活躍 |
| **DarkOps-Worker** | 暗部根下 `core`、`Departments`、`dark_ops`、`output` | **Blocked** |
| **QA-Reviewer** | 唯讀驗證；Progress 末尾追加 QA 列 | 活躍 |

### 3.2 協作紀律

- 黑板（Conditions / Progress）**僅允許末尾追加**；禁止覆蓋、刪除、重排既有段落。
- 阻塞以「待確認項目」格式寫入 `00_Agent_Work_Progress.md`（格式細節由 Progress 維護，v0.1 不另定六行 schema）。
- 需改動非本人擁有之 `core` 檔：**先停** → fallback 或 stub → 於 notes 記錄所需契約；除非尚書省明確授權。

### 3.3 停工條件

- 未收到尚書省施工授權。
- 任務需碰暗部硬禁區。
- 路徑與 `Master_Map.json` 衝突且無授權。
- DarkOps 未另開票。

### 3.4 暗部四 Agent 建議順序（解禁後）

1. Infra Agent  
2. Data Agent  
3. RAG Agent  
4. Governance Agent  

並行時：各 Agent 僅改本人範圍；Governance 須容忍其他模組之 fallback 狀態。

---

## 4. 檔案與目錄邊界規則

### 4.1 三層結構（暗部）

| 層級 | 路徑（相對暗部根） | 規則 |
|------|-------------------|------|
| **總部 SDK** | `core/*.py` | 全系統可 import；**不可越權修改**非本人模組 |
| **Agent 工作區** | `agent_workspace/{infra,data,rag,governance}_agent/` | 至少含 `brief.md`、`progress.md`、`notes.md` |
| **執行層** | `Departments/04_Infrastructure/agents/` | 可執行 CLI agent 腳本 |

### 4.2 各 worker 可碰路徑（HQ 第一階段）

| Worker | 可碰 | 限制 |
|--------|------|------|
| HQ-Governance-Worker | `00_Agent_Work_Conditions.md`、`00_Agent_Work_Progress.md` | 僅末尾追加 |
| HQ-Tooling-Worker | `01_Environments/config/services/`、`tools/`、`mcp/`、`mcp/_registry/` | 盤點與文檔為主 |
| DarkOps-Worker | 暗部根內 | **禁止**新增／修改／刪除 |
| QA-Reviewer | 全樹 | 唯讀；Progress 末尾 QA 列 |

### 4.3 暗部硬禁區（只讀、不寫）

- `gov_core_system/Scripts/`、`Lib/`、`Include/`、`share/`
- `gov_core_system/.env`（含 `.env.example`，除非單獨開票）
- `gov_core_system/runtime/checkpoints/`
- `Departments/01_Orchestration/scripts/prune_checkpoints.ps1`
- `Departments/01_Orchestration/workflow/checkpoint.py`
- `dark_ops/scripts/small_keepnewest.ps1`
- 總部清算類：`04_Workflows/Cleanup_Check.py`、`_cleanup_and_recovery.py`、`_execute_liquidation.py`、`_dry_run_liquidation.py`、`_destruction_test.py`

### 4.4 路徑解析

- **禁止**在程式中硬編磁碟路徑；須經 `gov_paths` 與 `Master_Map.json`。
- 刑部別名 `xing_bu` → `05_Temp_Cache`（生料／暫存）。

### 4.5 fallback（憲法層）

- 依賴缺失時：允許最小 skeleton、`try/except import`、回傳 `{"ok": false, "message": "..."}`。
- 必須寫入執行者自身 `progress.md` 與 `notes.md`。
- **不可**因依賴缺失崩潰，**不可**擅自接管他人檔案。

---

## 5. 四大板塊（Infra / Data / RAG / Governance）總職責

> 以下為**職責邊界**；里程碑完成度以 `00_Agent_Work_Progress.md` 為準（v0.1 基線：I0/I1、D1–D3、R1/R2、G1 已記錄完成；Gov Core V1 已封版）。

### 5.1 共通契約

- 核心函式回傳 **`dict`**（不可僅 `print`）。
- Agent 腳本須可 **CLI 直接執行**。
- 本輪完成（DoD）至少含：三份 workspace 文件、一個可執行 agent、對應 `core/*.py`、progress 記錄已完成／未完成／阻塞／下一步。

### 5.2 Infra Agent

| 項目 | 內容 |
|------|------|
| **擁有** | `core/infra_health.py`、`Departments/04_Infrastructure/agents/infra_health_agent.py`、自身 workspace |
| **負責** | Postgres / Qdrant / Phase1 verify；健康檢查 `dict` 含檢查項、ok、message、耗時或錯誤語意 |
| **不負責** | ingest 語意、向量內容、RAG 策略、orchestrator 業務編排 |

### 5.3 Data Agent

| 項目 | 內容 |
|------|------|
| **擁有** | `core/data_pipeline.py`、`data_pipeline_agent.py`、自身 workspace |
| **負責** | ingest / verify 資料流契約、批次邊界、錯誤語意；回傳含 run 識別與計數 |
| **不負責** | infra 連線實作、RAG prompt、一鍵工作流（除非明確授權並留痕） |

### 5.4 RAG Agent

| 項目 | 內容 |
|------|------|
| **擁有** | `core/rag_backend.py`、`rag_query_agent.py`、自身 workspace |
| **負責** | 查詢入口、retrieval、LLM 後端組裝；可觀測欄位（如 query_id、retrieved_count、latency） |
| **不負責** | ingest 主流程、infra health、orchestrator 狀態機 |

### 5.5 Governance Agent

| 項目 | 內容 |
|------|------|
| **擁有** | `core/orchestrator.py`、`orchestrator_agent.py`、自身 workspace；預設獨占更新 `master_status` / `handoff` |
| **負責** | 串接 health → ingest → verify 等步驟；步驟級摘要；失敗時可追溯指紋寫入 handoff |
| **不負責** | 取代其他三個 `core` 內領域邏輯（僅呼叫與組裝） |

### 5.6 互踩防護

- 跨模組觀測欄位命名歧義時，以 **Governance 匯總處**一次性對齊，並記錄於 handoff 或 notes。

---

## 6. 變更與版本：`Master_Map.version` 的意義

### 6.1 版本層級

| 層級 | 載體 | 壽命 |
|------|------|------|
| **憲法** | 本檔 HARNESS v0.x | 長期 |
| **Conditions** | `00_Agent_Work_Conditions.md` | 長期制度條文 |
| **Progress** | `00_Agent_Work_Progress.md` | 短命迭代 |
| **戰車地圖** | `Master_Map.json` → `version` | 路徑／runner／封存快照 |
| **憲法版本標** | `war_status.constitution_version` | 封存時與 README / AGENTS 對齊 |

### 6.2 `Master_Map.version`

- 為戰車**相對路徑與 runners 之唯一權威**版本號。
- 重大變更須反映於 `war_status.milestones`；指紋統一由 `Chariot_Registry.db` 管理（**禁止**新建 `hashes.txt`）。
- 封存時更新：`as_of`、`frozen_at_iso_utc`、`headline`、`next_priorities` 等（詳見 `AGENTS.md` §封存協議）。

### 6.3 封版與後續

- **Gov Core System V1** 已封版（Progress 記錄，2026-05-15）；後續需求歸 **V2 或部署／維運專案**，不混回 V1 缺口敘述。
- **Phase 2** 主軸（Progress 記錄）：真正 LLM 問答、GraphRAG job 流程、Monitoring、狀態檔自動寫回——本憲法 v0.1 **不展開**其驗收細節。

### 6.4 當前錨點（蒸餾時點）

- `Master_Map.version`：**2.60**（以 session 已讀地圖為準）
- HQ 第一階段：黑板 + registry **Done**；DarkOps **Blocked**

---

## 附錄 A：回報格式（全 Agent 共通）

完工回報至少包含：

1. 新建／修改檔案清單  
2. 哪些為可執行 skeleton  
3. 哪些仍為 placeholder  
4. 當前阻塞  
5. 下一步建議  

（與 `ENGINEERING_CONTRACT` 附錄 Work Report 對齊時，以合約模板為準。）

---

## 附錄 B：與 `AGENTS.md` 的銜接

| HARNESS 概念 | 戰車對應 |
|--------------|----------|
| 接戰 | `AGENTS.md` §初始化校準（地圖、律法、糧草盲測、Status、刑部件數） |
| 封存 | `AGENTS.md` §封存協議 → 同步 `Master_Map.war_status`、指紋登錄 |
| 糧草 | `_smoke_test_keys.py`；**嚴禁**輸出金鑰原文 |
| 路徑 | `gov_paths` + `Master_Map.json` |
| Telegram | 以 `.telegram_listener.lock` 為準；**嚴禁**雙監聽器 |
| 健康度回報 | 綠／黃／紅 + 待命 |

---

## v0.1 定位

- 本檔為 **v0.1 草稿**：將 `00_Agent_Work_Conditions.md` 中長期原則與 HQ 協作輪（2026-05-17）蒸餾為單一憲法入口，**不取代** Conditions 與 Progress 之維護責任。
- 未記載之 runner、工具 Phase、GraphRAG 驗收細節，以 `Master_Map.json` 與 Progress 當期條目為準。
- 與工程實作節奏、12-rule、四大流派之執行細則，以 `ENGINEERING_CONTRACT_v0.1.md` 為準。
