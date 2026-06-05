# HARNESS 憲法

> **角色**：治理主檔（可移植層）。  
> **對照**：條目索引見 `04_Workflows/_PORTABLE_CORE_INDEX.md`（W0）；實例路徑見 `04_Workflows/INSTANCE_ANCHOR_TANG.md`（W5）。  
> **版本**：由尚書省裁決；本文不自標定稿號。

---

## 1. 文件定位

| 項目 | 說明 |
|------|------|
| **名稱** | HARNESS 憲法 |
| **層級** | 戰車總部層**長期制度** |
| **適用** | 本 repo 內所有因任務被指派的 Cursor / Chat Agent、HQ 協作輪 worker |
| **不做的事** | 不取代運維黑板與接戰入口；不承載快速過期實作細節 |

### 1.1 與其他文件的關係（主檔 vs 運維黑板）

| 檔名 | 職責 | 與本檔關係 |
|------|------|------------|
| `04_Workflows/00_Agent_Work_Conditions.md` | 長期制度之母本、HQ／暗部角色邊界 | **對齊**；本檔蒸餾其憲法級條文，不刪除其維護責任 |
| `04_Workflows/00_Agent_Work_Progress.md` | 當前迭代、里程碑、阻塞、QA 列 | **對齊**；短命狀態以 Progress 為準 |
| `AGENTS.md` | 副官接戰／封存、初始化校準、戰車級紅線 | **對齊**；口令與初始化細節以 AGENTS 為執行入口 |
| `04_Workflows/ENGINEERING_CONTRACT.md` | 工程交付、審稿、Work Report | 本檔定邊界與禁區類型；合約定如何交、如何驗收 |
| `04_Workflows/DEPARTMENT_MAP.md` | 組織拓撲、cabin 角色、六部與四 Agent | 本檔定原則；地圖定結構與上下游 |
| `04_Workflows/_PORTABLE_CORE_INDEX.md` | W0 可移植條目索引（38＋23） | **對照**；本檔主責條目見附錄 |
| `04_Workflows/Master_Map.json` | 相對路徑、runners、cabins 權威索引 | 路徑解析**見地圖，非本文** |
| `04_Workflows/INSTANCE_ANCHOR_TANG.md` | 本戰車實例錨點 | 禁區具體路徑、venv 進入方式、帳本檔名與 env 鍵**僅在 W5** |

**引用句式**：只寫檔名＋一句職責；不複製長文、不寫磁碟絕對路徑。

---

## 2. HARNESS 是什麼

**HARNESS** 指：以**文件定邊界**、以**黑板末尾留痕**、以可程式化 **`dict` 串接模組**的多 Agent 治理框架。

**目的**：建立清晰責任邊界與可接手上下文，使後續 session／worker 能接手而不失憶、不互踩。

**工作節奏**：先文件後程式；先可執行 skeleton，再替換真實邏輯（細則見 `ENGINEERING_CONTRACT.md`）。

---

## 3. 國家結構四域

| 域 | 代稱 | 職責摘要 |
|----|------|----------|
| **HQ（總部）** | 尚書省／治理層 | 全局規範、黑板、地圖索引、知識沉澱、戰車 runner |
| **Dark（暗部）** | Gov Core System | 統包艙內 `core`、Departments、`dark_ops`、`output`；與 HQ 工具層 venv **隔離** |
| **Chariot（戰線）** | 六部執行態 | 環境、Agent 核心、RAG 庫、工作流、刑部暫存、出口 |
| **Tools（工具層）** | HQ Tools | 工具／MCP／服務盤點與索引；**嚴禁**向暗部 venv 安裝 HQ 工具套件 |

暗部工作區根、專案根等**實例路徑**見 `INSTANCE_ANCHOR_TANG.md`（W0：I01–I02）。

---

## 4. 可移植邊界（方案 A）

1. **三件套正文**（本檔、`ENGINEERING_CONTRACT.md`、`DEPARTMENT_MAP.md`）不得出現任何本機實體根路徑、venv 實際路徑、cabin 進入指令、禁區具體路徑、帳本具體檔名、env 鍵原文或 DB 實際落點。
2. 上述實例資訊**一律**寫入 `INSTANCE_ANCHOR_TANG.md`，或該檔「本戰車錨點」總結節。
3. 程式與 Agent **禁止硬編磁碟路徑**；須經 `gov_paths` 與 `Master_Map.json` 解析（W0：C32、C36）。
4. 路徑、runner、cabin 的**邏輯名稱**可出現於三件套；**具體相對路徑字串表**不複製整份地圖 JSON（W0 §3 禁止清單）。

---

## 5. Phase 與工單門檻

### 5.1 Phase 分層

| Phase | 範圍 | 本階段約束 |
|-------|------|------------|
| **Phase 1** | 起草可移植三件套 + 實例錨點 W5；對齊 W0 | 並行工單 W1／W2／W3／W5；**不得**起草 `.cursor/rules` 或 Phase 2 實作細則 |
| **Phase 2** | `.cursor/rules` 規則轉制 | **僅在** W4 盲測 **10/10 通過**後觸發（見 `ENGINEERING_CONTRACT.md` §8） |
| **後續** | GraphRAG job、Monitoring、狀態檔自動寫回等 | 以 `00_Agent_Work_Progress.md`「下一輪優先」為準；本憲法不展開驗收細節 |

### 5.2 工單與授權

- 施工前須收到**尚書省明確授權**（任務卡或當次指令）。
- **DarkOps-Worker** 在第一階段預設 **Blocked**；解禁須另開票。
- 偏離本憲法時：以尚書省**當次明確指令**為準，但須在 progress／notes 或 Progress 黑板**末尾**留痕（原因、影響、是否一次性）。

### 5.3 衝突位階

尚書省當次指令 ＞ 本憲法 ＞ `ENGINEERING_CONTRACT.md`（高風險禁區仍須先警示，見 §7）。

---

## 6. HQ 協作輪與黑板紀律

### 6.1 HQ 五角色（職責摘要）

| 角色 | 職責 | Phase 1 預設 |
|------|------|----------------|
| **HQ-Coordinator** | 規劃、任務卡、驗收定義；不直接改 code | 活躍 |
| **HQ-Governance-Worker** | 黑板末尾追加、`Master_Map.json`／`AGENTS.md`（授權時）、`07_Knowledge` 知識沉澱 | 活躍 |
| **HQ-Tooling-Worker** | 工具層盤點與索引文檔 | 活躍 |
| **DarkOps-Worker** | 暗部根內實作 | **Blocked** |
| **QA-Reviewer** | 唯讀驗證；Progress 末尾 QA 列 | 活躍 |

組織拓撲與上下游見 `DEPARTMENT_MAP.md`。

### 6.2 黑板規則（W0：C14）

- `00_Agent_Work_Conditions.md`、`00_Agent_Work_Progress.md`：**僅允許末尾追加**。
- 禁止覆蓋、刪除、重排既有段落。
- 阻塞以「待確認項目」格式寫入 Progress（格式由 Progress 維護）。

### 6.3 全局狀態檔職責分離（W0：C38）

| 載體 | 壽命 | 內容 |
|------|------|------|
| Conditions | 長期制度 | 原則、邊界、禁止事項 |
| Progress | 短命迭代 | 里程碑、阻塞、當輪 Done／Blocked |
| `project_status/master_status.md` | 跨 agent 快照 | 預設 **Governance Agent 獨占寫入**（W0：C18） |
| `project_status/handoff.md` | 交接上下文 | 同上；他方僅回報 |

---

## 7. 禁區：類型、制度與後果

> **分流**：本文只定**類型**與制度；**具體路徑清單**見 `INSTANCE_ANCHOR_TANG.md`（W0：C22↔I03）。

### 7.1 禁區類型表

| 類型 | 說明 | 典型範圍（抽象） |
|------|------|------------------|
| **Z-ENV** | 環境與密鑰 | `.env`、`.env.example`（除非單獨開票） |
| **Z-VENV-TREE** | 解釋器與套件樹 | 暗部 venv 的 `Scripts`／`Lib`／`Include`／`share` |
| **Z-RUNTIME-CP** | 執行態檢查點 | 暗部 `runtime/checkpoints/`（未授權不得改寫） |
| **Z-ORCH-DESTRUCT** | 編排破壞性腳本 | 特定 checkpoint／prune 模組與腳本 |
| **Z-DARK-OPS** | 暗部維運腳本 | `dark_ops` 下保留／清理類腳本 |
| **Z-HQ-LIQUIDATION** | 總部清算類 | `04_Workflows` 下清算／破壞測試腳本 |
| **Z-HQ-ENV-EDIT** | 全域禁止 | 擅自修改根 `.env`、刪 `phase1_verify`、搬移既有目錄結構 |

### 7.2 違規後果

| 情況 | 後果 |
|------|------|
| 未授權觸及硬禁區 | **立即停工**；回報禁區類型與任務卡編號 |
| 尚書省 override 仍要求執行 | 須**先明示風險**（尤其 Z-ENV、Z-HQ-LIQUIDATION），再執行並留痕 |
| 路徑與 `Master_Map.json` 衝突且無授權 | 停工；要求更新地圖或改任務 |
| DarkOps Blocked 且任務需改暗部根 | 停工；要求開票解禁 |

### 7.3 戰車級紅線（與 AGENTS 對齊）

- 嚴禁輸出金鑰原文；糧草驗證僅解讀盲測 `[OK]`／`[FAILED]`。
- 嚴禁同時兩個 Telegram 監聽器（以 lock 檔為準，實例名見 W5）。
- 嚴禁在主艙安裝 crewai／langchain 等重套件（統包艙職責，見 DEPARTMENT_MAP）。
- 嚴禁新建 `hashes.txt`；指紋只走 **Chariot_Registry** 類帳本（W0：C24）。

---

## 8. Pipeline 元資料帳本（制度）

> **分流**：帳本**制度**在本節；帳本具體檔名、env 鍵、磁碟落點見 `INSTANCE_ANCHOR_TANG.md`（W0：C37↔I17）。

### 8.1 帳本是什麼

**Pipeline 元資料帳本**指：記錄長時間管線（如碼源清洗戰役）之 **jobs** 與 **events** 的 SQLite 類持久化存儲，供 crash-safety、稽核與跨模組觀測對齊。

可移植層只承認：戰車**須有**此類帳本類型；具體檔名與 SDK 入口以 W5 與 `Master_Map.json` 的 `artifacts`／`runners` 為準。

### 8.2 誰記錄、何時記錄

| 時機 | 責任方 | 記錄內容 |
|------|--------|----------|
| 管線啟動 | 執行該管線的 Agent／腳本（經 SDK `start_job`／`job_run`） | `pipeline_started`、job 狀態 `running` |
| 關鍵節點 | 同上 | 自由 `event_type`（掃描開始／結束、wave、錯誤歸檔等） |
| 正常結束 | 同上 | `pipeline_finished`、job `success`／`partial` |
| 例外崩潰 | SDK context manager | `pipeline_aborted`、job `failed` |
| 跨 agent 摘要 | **Governance**（或授權之 HQ-Governance-Worker） | 將可機器讀摘要同步至 Progress **末尾**（非取代帳本） |

### 8.3 與 Progress／黑板對齊

1. **帳本** = 細粒度、可 SQL 查詢之執行態真相。  
2. **Progress** = 人類與 Agent 快速讀取之迭代敘事與里程碑。  
3. 宣稱「管線本輪完成」時：Progress 須有一句話指向帳本 job_id 或查詢入口；不得僅寫自然語言無證據。  
4. 禁止在 Progress 複製整表 events；只追加摘要列。

---

## 9. 暗部四 Agent 與三層結構

### 9.1 三層（暗部）

| 層級 | 路徑語意（相對暗部根） | 規則 |
|------|------------------------|------|
| 總部 SDK | `core/*.py` | 可 import；**不可越權改**非本人模組 |
| Agent 工作區 | `agent_workspace/{infra,data,rag,governance}_agent/` | 至少 `brief`／`progress`／`notes` |
| 執行層 | `Departments/04_Infrastructure/agents/` | 可執行 CLI |

### 9.2 四板塊職責（摘要）

| Agent | 擁有（語意） | 負責 | 不負責 |
|-------|--------------|------|--------|
| **Infra** | `infra_health`、infra agent、infra workspace | Postgres／Qdrant／Phase1 verify 類健康檢查之 `dict` 輸出 | ingest 語意、RAG 策略、orchestrator 編排 |
| **Data** | `data_pipeline`、data agent、data workspace | ingest／verify 契約、批次邊界與 CLI 入口 | infra 連線實作、RAG prompt |
| **RAG** | `rag_backend`、rag agent、rag workspace | 查詢、retrieval、LLM 組裝 | ingest 主流程、orchestrator 狀態機 |
| **Governance** | `orchestrator`、gov agent、gov workspace；**預設** master_status／handoff 寫入權 | health→ingest→verify 一鍵流；步驟級摘要與 handoff | 取代其他 `core` 內領域邏輯 |

拓撲細表見 `DEPARTMENT_MAP.md` §7；檔案歸屬以 Conditions 為母本，本節為憲法級摘要（W0：C03–C04）。

**建議順序**（解禁後）：Infra → Data → RAG → Governance；並行時 Governance 須容忍 fallback（W0：C16）。

**互踩防護**：改非本人 `core` 須先停；跨模組欄位歧義由 Governance 一次性對齊（W0：C17）。

### 9.3 共通契約

- 核心函式回傳 **`dict`**（不可僅 `print`）。
- 全域禁止事項見 §7 與 Conditions（改 `.env`、假完成 placeholder 等，W0：C08）。

---

## 10. 版本層級與 Master_Map

| 層級 | 載體 | 壽命 |
|------|------|------|
| 憲法 | 本檔 | 長期 |
| Conditions | `00_Agent_Work_Conditions.md` | 長期制度 |
| Progress | `00_Agent_Work_Progress.md` | 短命迭代 |
| 戰車地圖 | `Master_Map.json` → `version` | 路徑／runner／封存快照權威 |
| 封存標 | `war_status.constitution_version` | 封存時與 README／AGENTS 對齊 |

`Master_Map.version` 變更須反映於 `war_status.milestones`；指紋統一由 registry 類帳本管理。

---

## 11. 停工條件（憲法層）

- 未收到尚書省施工授權。  
- 任務需碰 §7 硬禁區且無 override。  
- 路徑與地圖衝突且無授權。  
- DarkOps 未另開票。  

fallback 原則：依賴缺失 → 最小 skeleton 或 `ok:false` + message；寫入自身 progress／notes；不崩潰、不接管他人檔案（W0：C09–C10）。

---

## 12. 與 AGENTS.md 的銜接

| 憲法概念 | 執行入口 |
|----------|----------|
| 接戰 | `AGENTS.md` §初始化校準 |
| 封存 | `AGENTS.md` §封存協議 → 同步 `war_status`、指紋登錄 |
| 糧草 | 盲測 runner（名見 W5）；嚴禁輸出金鑰 |
| 路徑 | `gov_paths` + `Master_Map.json` |

### 12.1 接戰四段（摘要，W0：C30）

口令與逐步細則以 `AGENTS.md` 為準；憲法層只固定四段語意：

| 段次 | 目的 |
|------|------|
| 1. 掛載地圖 | 載入 `Master_Map.json`，確認路徑權威與 cabin 語意 |
| 2. 讀取律法 | `Base_Agent`／`run_id`／`get_path` 等執行契約就緒 |
| 3. 檢查糧草 | 金鑰盲測僅解讀 `[OK]`／`[FAILED]`，**嚴禁**輸出金鑰原文 |
| 4. 現況審核 | Status 與刑部暫存件數等執行態摘要（具體檔名見 W5） |

### 12.2 戰車級紅線（W0：C31）

與 §7.3 及 `AGENTS.md` 對齊：禁硬編磁碟路徑、禁雙 Telegram 監聽、禁主艙重套件（crewai／langchain 等）、禁新建 `hashes.txt`（指紋走 registry 類帳本）。

---

## 附錄：W0 可移植條目對照（憲法主責）

本檔主責吸收 W0 條目：**C01–C04、C08、C12–C15、C18–C24、C28、C30–C31、C38**（母表見 `_PORTABLE_CORE_INDEX.md` §1）。

| 條號 | 吸收章節 | 自檢 |
|------|----------|------|
| C01 | §1 | 是 — 長期原則承載，短命狀態外推 |
| C02 | §5.2 | 是 — 尚書省指令優先＋偏離末尾留痕 |
| C03 | §9.1–§9.3 | 是 — 檔案歸屬與互踩防護 |
| C04 | §9.2 | 是 — 四 Agent 擁有／負責／不負責三分法 |
| C08 | §7.1 Z-HQ-ENV-EDIT、§9.3 | 是 — 全域禁止事項與 placeholder 禁令 |
| C12 | §9.1 | 是 — 暗部三層結構 |
| C13 | §6.1 | 是 — HQ 五角色表 |
| C14 | §6.2 | 是 — 黑板僅末尾追加 |
| C15 | §5.2、§11 | 是 — 停工條件與授權 |
| C18 | §6.3 | 是 — master_status／handoff 預設 Governance 獨占寫 |
| C19 | §2 | 是 — HARNESS 定義 |
| C20 | §3 | 是 — 國家結構四域 |
| C22 | §7.1–§7.2 | 是 — 禁區類型表＋override 先警示 |
| C23 | §10 | 是 — 版本層級 |
| C24 | §7.3 | 是 — 單一 registry，禁 `hashes.txt` |
| C28 | §5.3 | 是 — 衝突位階 |
| C30 | §12、§12.1 | 是 — 接戰／封存銜接＋四段摘要 |
| C31 | §7.3、§12.2 | 是 — 戰車級紅線 |
| C38 | §6.3 | 是 — Conditions／Progress／status／handoff 職責分離 |

**W1 定稿候選自檢（ENGINEERING_CONTRACT §10.3，適用本檔）**

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 正文零本機絕對路徑 | 是 | 全文無磁碟根路徑字面；僅相對檔名與抽象語意 |
| 正文零 venv 實際路徑 | 是 | 僅「暗部 venv」「Scripts／Lib」等**類別**語意，無進入指令 |
| 正文零帳本檔名／env 鍵 | 是 | §4.1、§8 分流至 W5；正文不列具體鍵名 |
| §5 Phase 門檻 | 是 | Phase 1／2 分層、授權、DarkOps Blocked、W4 閘門引用 |
| §6 黑板 | 是 | 五角色、末尾追加、四載體職責分離 |
| §7 Z-* 類型表 | 是 | 七類禁區＋後果＋紅線 |
| §8 Pipeline 制度 | 是 | 帳本定義、記錄責任、與 Progress 對齊 |
| §9 四 Agent 完整 | 是 | 三層＋四板塊擁有／負責／不負責＋順序與互踩 |
| 未寫 `.cursor/rules`；未自標 v1.0 | 是 | Phase 2 僅引用；檔首無定稿號 |
