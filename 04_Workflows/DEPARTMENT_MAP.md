# 部門地圖

> **角色**：組織拓撲主檔（可移植層）。  
> **對照**：W0 `04_Workflows/_PORTABLE_CORE_INDEX.md`；憲法見 `HARNESS_CONSTITUTION.md`；合約見 `ENGINEERING_CONTRACT.md`；實例路徑見 `INSTANCE_ANCHOR_TANG.md`。  
> **版本**：由尚書省裁決；本文不自標定稿號。

---

## 1. 文件定位

本檔描述**誰負責什麼、與誰上下游對接**，不含磁碟絕對路徑、venv 啟動指令、DB 檔名或 env 鍵值。

| 需求 | 去哪裡 |
|------|--------|
| 相對路徑、runner 檔名、cabin 實例 | `Master_Map.json`、`INSTANCE_ANCHOR_TANG.md` |
| 禁區類型與後果 | `HARNESS_CONSTITUTION.md` §7 |
| 怎麼交付、怎麼驗收 | `ENGINEERING_CONTRACT.md` |
| 當輪 Done／Blocked | `00_Agent_Work_Progress.md` |

---

## 2. 拓撲總覽

與憲法 §3 **四域**對齊：**HQ**／**Tools**／**Chariot**／**Dark**；**Cabins** 為跨域之 venv／用途域抽象（非第五國，見 §6）。

```text
                    ┌─────────────────────────────────────┐
                    │  HQ（尚書省協作輪 · 五角色）           │
                    │  Coordinator / Governance / Tooling  │
                    │  DarkOps* / QA                       │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │  Tools（工具層 · 與暗部 venv 隔離）  │
                    │  cursor / tools / mcp / services   │
                    └──────────────┬──────────────────────┘
                                   │ 授權、黑板、地圖索引
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│ Chariot（戰車六部）│    │ Cabins（三艙 · 抽象）  │    │ Dark（暗部六部）  │
│ 01–06 相對部門鍵  │    │ 主／副／統包           │    │ 01–06 Departments│
└────────┬────────┘    └──────────┬───────────┘    └────────┬────────┘
         │                          │                          │
         │                          │                          ▼
         │                          │               ┌──────────────────────┐
         │                          └──────────────►│ 暗部四 Agent（執行層）  │
         │                                         │ Infra·Data·RAG·Gov    │
         └────────────────────────────────────────►└──────────────────────┘
```

\* DarkOps 第一階段預設 **Blocked**（見憲法 §5）。  
**Tools 與 Chariot**：runners 索引在 `04_Workflows`／`Master_Map.json`（W0：C32）；HQ 工具套件**不得**裝入暗部 venv（見 §10、憲法 §3 Tools 列）。

---

## 3. 戰車六部（Chariot）

六部鍵為路徑解析之一級單位（W0：C33）；邏輯別名見地圖 `aliases`，**非第二套根**（W0：C34）。

| 部門鍵 | 傳統別名 | 職責 | 典型上下游 |
|--------|----------|------|------------|
| **01_Environments** | 吏部 `li_bu` | Python venv 域、`.env` 承載、`config` 工具層 | → 各艙啟動；← HQ-Tooling 盤點 |
| **02_Agents_Core** | 兵部 `bing_bu` | `Base_Agent`、`gov_paths`、共用 SDK（含 pipeline_meta） | → 04 工作流腳本；← 暗部 `core` import |
| **03_RAG_Database** | 戶部 `hu_bu` | 向量庫、快照、核心知識庫目錄語意 | ← Data ingest；→ RAG 檢索 |
| **04_Workflows** | （戰車指揮所） | `Master_Map`、Status、registry、runners、黑板 | ← HQ 全輪；→ 06 報告出口 |
| **05_Temp_Cache** | 刑部 `xing_bu` | 生料 `raw_inbound`、隔離 `quarantine`、清洗樣本 | ← 偵察／inbound；→ Data 管線 |
| **06_Exports_Output** | 工部 `gong_bu` | 最終出口、歸檔、戰報與 quota 狀態類產物 | ← Wave／精煉；→ 尚書省驗收 |

**路徑解析規則**：`tang_gov_root` 為空時，以地圖檔所在 `04_Workflows` 的上一層為根（W0：C36）。程式經 `gov_paths`／`get_path`，禁止硬編磁碟字串。

**刑部別名**：`xing_bu` → `05_Temp_Cache`（生料／暫存皆由此解析）。

---

## 4. 暗部 Departments 01–06（統包艙內）

暗部業務編排在 **gov_core_system** 統包艙之 `Departments/` 下（艙角色見 §6）。與戰車六部**不同命名空間**。

| 編號 | 名稱 | 職責 | 上下游 |
|------|------|------|--------|
| **01_Orchestration** | 編排 | LangGraph 工作流、checkpoint 語意、smoke／main 入口 | → 02、03；← Governance 串接 |
| **02_Brain_GraphRAG** | 圖腦 | GraphRAG 知識圖譜（Phase 2+ 主戰場） | ← Data／RAG；→ 03 觀測 |
| **03_Observability** | 觀測 | 追蹤、評測、Langfuse 類整合掛點 | ← 01、02、04 執行態 |
| **04_Infrastructure** | 基設 | docker-compose（Postgres／Qdrant）、四 Agent 腳本、Phase1 健康驗證域 | → 05 資料庫；← Infra／Data Agent |
| **05_Data_Vault** | 資料庫 | 管線元資料帳本目錄、清洗戰役交付物 | ← 04、06；帳本制度見憲法 §8 |
| **06_Strategy** | 戰略 | 碼源清洗戰役 v2 規格、策略 README | → 全艦 pipeline 命名與事件語意 |

**暗部根語意**：venv 與業務同樹；**不得**假設暗部根在戰車根直下之錯誤路徑（實例見 W5 I02）。

---

## 5. HQ 五角色

| 角色 | 說了算什麼 | 可碰範圍（抽象） | 第一階段 |
|------|------------|------------------|----------|
| **HQ-Coordinator** | 任務卡、驗收定義、Phase 門檻 | 唯讀為主；不直接改 code | 活躍 |
| **HQ-Governance-Worker** | 黑板、地圖（授權時）、知識沉澱 | Conditions／Progress **末尾追加**；`07_Knowledge` | 活躍 |
| **HQ-Tooling-Worker** | 工具／MCP／服務索引 | `01_Environments/config` 下 services／tools／mcp | 活躍 |
| **DarkOps-Worker** | 暗部 `core`、Departments、`dark_ops`、`output` | 暗部根內實作 | **Blocked** |
| **QA-Reviewer** | 唯讀驗證、W4 盲測協助 | 全樹唯讀；Progress QA 列 | 活躍 |

**誰說了算（衝突時）**：尚書省 > 憲法 > 合約 > Progress 當期敘述 > 單一 Agent notes。

---

## 6. Cabins：角色與用途（抽象）

> **分流**：本文僅 **角色名 + 用途一句**；venv 路徑、`Scripts/python.exe`、**Enter-*.ps1** 等進入指令**不在本文**（W0：C35↔I16；實例見 `INSTANCE_ANCHOR_TANG.md` §3）。

| 艙鍵 | 角色 | 用途（一句） | 套件邊界 |
|------|------|--------------|----------|
| **gov_main** | 主艙 | 工廠主線：清洗、恢復、索引、Telegram 監聽、資產評估、Wave runner | **禁止** crewai／langchain 等重套件 |
| **gov_agency** | 副艙 | 偵察、Wave 級任務、BeautifulSoup／Playwright、agency-agents | 與主艙職責分離 |
| **gov_core_system** | 統包艙 | 暗部 Departments 01–06、docker-compose、四 Agent 與 `core` SDK | **禁止** HQ 工具層 pip 混入 |

**地圖表達**：`Master_Map.json` 的 `cabins` 記錄「哪個艙對應哪個用途域」；禁止在程式寫死絕對路徑。

---

## 7. 暗部四 Agent

執行層位於 `Departments/04_Infrastructure/agents/`；擁有權以 **檔案歸屬** 為準（W0：C03–C04）。

| Agent | 板塊 | 擁有（語意） | 負責 | 不負責 | 建議順序 |
|-------|------|--------------|------|--------|----------|
| **Infra** | 基設 | `infra_health`、infra agent、infra workspace | Postgres／Qdrant／Phase1 健康驗證 `dict` | ingest、RAG、orchestrator 編排 | ① |
| **Data** | 資料 | `data_pipeline`、data agent、data workspace | ingest／verify 契約、批次邊界 | infra 連線、RAG prompt | ② |
| **RAG** | 檢索 | `rag_backend`、rag agent、rag workspace | 查詢、retrieval、LLM 組裝 | ingest 主流程、orchestrator 狀態機 | ③ |
| **Governance** | 治理 | `orchestrator`、gov agent、gov workspace；**預設** master_status／handoff 寫入權 | health→ingest→verify 一鍵流；步驟級摘要 | 取代其他 core 領域邏輯 | ④ |

**並行規則**：並行時各 Agent 僅改本人範圍；Governance 須容忍 fallback；跨模組欄位由 Governance 一次性對齊（W0：C16–C17）。

**三層結構**（暗部內）：總部 SDK `core` → `agent_workspace` → Departments 執行層（W0：C12）。

---

## 8. 執行態錨點類型（非具體檔名）

以下為**類型名**，實例檔名見 `Master_Map.json` → `artifacts` 與 W5（W0：C37）。

| 類型 | 用途 |
|------|------|
| `master_map` | 路徑與 runner 權威 |
| `status_json` | 最後管線／評估狀態摘要 |
| `chariot_registry` | 內容指紋 SHA256 帳本 |
| `current_plan` | 當前計畫快照 |
| `pipeline_meta`（類） | jobs／events 元資料帳本（制度見憲法 §8；實例檔名見 W5） |
| `runners`（索引類） | 戰車 ps1／py 入口之邏輯名稱表（W0：C32；**不複製** JSON 全文） |

---

## 9. 與憲法／合約的對照

### 9.1 憲法 §3–§4 分工（本檔承擔部分）

| 憲法條 | 內容 | 本檔落點 |
|--------|------|----------|
| §3 四域 | HQ／Dark／Chariot／Tools | §2 拓撲、§5、§10 |
| §4 可移植邊界 | 三件套零實例路徑；邏輯名可出現 | §1、§6 分流、§8 類型名 |
| §3 Tools 列 | 嚴禁 HQ 工具混入暗部 venv | §6 統包艙邊界、§10 |
| §3 Dark 列 | 統包艙內 core／Departments | §4、§6 `gov_core_system`、§7 |

### 9.2 三件套分工表（與 `ENGINEERING_CONTRACT.md` §12 對齊）

| 主題 | 憲法 | 合約 | 本地圖 |
|------|------|------|--------|
| 國家四域、Phase 門檻 | ✓ §3、§5 | §8 引用 | 拓撲 §2、§10 |
| 禁區**類型** | ✓ §7 | Rule 5 | —（路徑見 W5） |
| 六部 + 暗部六部 + 四 Agent | §9 摘要 | — | ✓ §3–§4、§7 |
| Cabin **角色／用途** | §7.3 紅線呼應 | §9 W3 約束 | ✓ §6 |
| HQ 五角色 | ✓ §6.1 | §7 審稿 | ✓ §5 |
| 12-rule、Work Report | — | ✓ §5–§6、§10 | 引用 |
| 誰寫 master_status／handoff | ✓ §6.3、C18 | — | §7 Governance |
| 誰寫 pipeline events | ✓ §8 | — | §4 部 05 + §7 Data／Governance |
| 路徑權威 | ✓ §4.3、C32 | Rule 6 | §3、§8 |

---

## 10. Tools 層與暗部隔離

對應憲法 §3 **Tools 域**（W0：C20）：與 **Dark** 共用業務樹但 **venv／pip 邊界分離**。

| 層 | 職責 | 限制 |
|----|------|------|
| **HQ Tools** | `01_Environments/config` 下 `cursor`、`tools`、`mcp`、`services` | 盤點與索引；**禁止**向暗部 venv `pip install` HQ 工具套件 |
| **Chariot runners** | `04_Workflows` 下 ps1／py 入口（邏輯名） | 權威索引在 `Master_Map.json` → `runners`（W0：C32）；本文不列檔名 |
| **Dark core** | 暗部 `core` + Departments + `agent_workspace` | DarkOps Blocked 時僅讀或停工；不得改 HQ Tools 樹 |
| **Cabin 邊界** | 主／副／統包三艙 | 主艙禁 crewai／langchain；統包艙禁 HQ 工具層套件混入（§6） |

---

## 11. 接戰與封存（執行入口）

口令與四段初始化（地圖、律法、糧草、現況）以 **`AGENTS.md`** 為準；本檔不複製步驟全文。

| 口令 | 行為 |
|------|------|
| 接戰 | 初始化校準 → 健康度綠／黃／紅 |
| 封存 | 同步 `war_status`、指紋登錄 |

---

## 附錄：W0 可移植條目對照（地圖主責）

本檔主責吸收 W0：**C21、C32–C37**（詳表見 `_PORTABLE_CORE_INDEX.md` §1）。

| W0 | 條文摘要 | 本文落點 | 自檢 |
|----|----------|----------|------|
| **C21** | 主／副／統包三艙；職責分離、禁混裝重套件 | §6 表 + 套件邊界欄 | 是 |
| **C32** | 路徑／runner 索引歸地圖；`gov_paths`／`get_path` | §2 末段、§3、§8 `runners`、§10 | 是 |
| **C33** | 六部鍵 01–06 為路徑解析一級單位 | §3 全表 | 是 |
| **C34** | `aliases`／`xing_bu` 為邏輯別名，非第二套根 | §3 刑部別名段 | 是 |
| **C35** | cabins＝用途域；禁程式寫死絕對路徑 | §6（無 venv 路徑、無 Enter-*.ps1） | 是 |
| **C36** | `tang_gov_root` 空則地圖檔上層為根 | §3 路徑解析規則 | 是 |
| **C37** | `artifacts` 為執行態錨點**類型名** | §8 表（含 `pipeline_meta` 類） | 是 |

**涵蓋自檢**：戰車六部 ✓｜暗部 Departments 01–06 ✓｜HQ 五角色 ✓｜暗部四 Agent ✓｜cabin 角色／用途 ✓｜Tools 隔離 ✓｜拓撲與 §2 四域一致 ✓
