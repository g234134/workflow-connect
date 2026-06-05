# 可移植核心索引（W0）

> **角色**：HQ-Coordinator / HQ-Governance-Worker 產出。  
> **用途**：從母本蒸餾「換根目錄、換雲供應商仍成立」之條目 vs「本戰車錨點」；供 W1–W3 三件套正文去實例化時對照。  
> **母本（唯讀）**：`00_Agent_Work_Conditions.md`、`AGENTS.md`、`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`Master_Map.json`（結構面）。歷史草稿 `*_v0.1.md` 已 SUPERSEDED（見 `project_status/HQ_PHASE1_FINALIZATION_ORDER.md`）。

---

## 1. 可移植核心條目表

| 條號 | 來源檔 | 簡述 | 未來歸入 |
|------|--------|------|----------|
| C01 | Conditions | 總部層文件承載**長期原則**（邊界、責任、協作紀律、禁止事項、DoD 類別）；不承載快速過期實作細節 | W1 |
| C02 | Conditions | 使用者**當次明確指令**優先於制度；偏離須在 progress／notes／Progress 黑板**留痕**（原因、影響、是否一次性） | W1 |
| C03 | Conditions | 四暗部板塊（Infra／Data／RAG／Governance）以**檔案歸屬**定責；不得越權改他人 `core`、department agent、他人 workspace | W1 |
| C04 | Conditions | 各板塊**擁有／負責／不負責**三分法（健康檢查、ingest 契約、RAG 組裝、orchestrator 串接） | W1 |
| C05 | Conditions | 核心函式與 agent CLI 須回傳**結構化 `dict`**，不可僅 `print`；須可被 orchestrator 匯總 | W2 |
| C06 | Conditions | **先文件後程式**；各 agent workspace 至少 `brief`／`progress`／`notes` | W2 |
| C07 | Conditions | **先 skeleton 後血肉**；placeholder 不得冒充完成 | W2 |
| C08 | Conditions | 全域禁止：改 `.env`、刪 `phase1_verify`、搬移既有目錄結構、覆蓋他人三件套 workspace 文、混寫四 agent、編造路徑／API／環境變數 | W1 |
| C09 | Conditions | **fallback**：依賴缺失 → 最小 skeleton 或 `ok:false` + message；寫入自身 progress／notes；不崩潰、不接管他人檔案 | W2 |
| C10 | Conditions | **DoD**：三份 workspace 文 + 可執行 agent + 對應 `core` + progress 四欄（完成／未完成／阻塞／下一步） | W2 |
| C11 | Conditions | **回報格式**五項：變更清單、skeleton、placeholder、阻塞、下一步 | W2 |
| C12 | Conditions | 暗部三層：**總部 SDK `core`**／**agent_workspace**／**Departments 執行層**；HQ 與暗部職責分離 | W1 |
| C13 | Conditions | HQ 協作輪角色表：Coordinator（規劃驗收不改 code）、Governance-Worker（黑板／地圖／知識）、Tooling-Worker（工具層盤點）、DarkOps（暗部實作）、QA（唯讀＋Progress QA 列） | W1 |
| C14 | Conditions | 黑板（Conditions／Progress）**僅末尾追加**；禁止覆蓋、刪除、重排 | W1 |
| C15 | Conditions | **停工條件**：未授權、碰硬禁區、路徑與權威地圖衝突無授權、DarkOps 未開票 | W1 |
| C16 | Conditions | 暗部四 agent **建議順序**（Infra→Data→RAG→Governance）；並行時 Governance 容忍 fallback | W2 |
| C17 | Conditions | 跨模組觀測欄位歧義 → **Governance 匯總處**一次性對齊並記 handoff／notes | W2 |
| C18 | Conditions | `master_status`／`handoff` 預設由 **Governance 獨占寫入**；他方僅回報 | W1 |
| C19 | HARNESS | HARNESS 定義：文件定邊界、黑板留痕、`dict` 串接之多 Agent 治理框架 | W1 |
| C20 | HARNESS | 國家結構四域：**HQ（總部）**／**Dark（暗部業務根）**／**Chariot（戰線執行態）**／**Tools（工具層，與暗部 venv 隔離）** | W1 |
| C21 | HARNESS | 雙艙＋統包艙**概念**：主艙（工廠主線）、副艙（偵察／Wave 級）、統包艙（暗部 Departments）；職責分離、禁混裝重套件 | W3 |
| C22 | HARNESS | 尚書省 override 與**高風險禁區先警示**（`.env`、venv 樹、清算類腳本） | W1 |
| C23 | HARNESS | 版本層級：憲法（長期）／Conditions（長期制度）／Progress（短命迭代）／地圖 `version`（路徑與 runner 權威）／`war_status`（封存快照） | W1 |
| C24 | HARNESS | 指紋治理：**單一 registry**（禁止新建 `hashes.txt`） | W1 |
| C25 | CONTRACT | 四大工程流派：Context／Source／Incremental／Debugging-Driven；交付前四者最低覆蓋 | W2 |
| C26 | CONTRACT | **12-rule**：起手確認、先讀後寫、最小觸及、dict 契約、禁區紅線、路徑權威、誠實標示、邊界尊重、fallback 不崩潰、阻塞必錄、驗證後宣稱、override 留痕 | W2 |
| C27 | CONTRACT | 標準流程：起手式 → 實作（最小增量）→ 驗收（可重跑證據）→ Work Report | W2 |
| C28 | CONTRACT | 衝突位階：尚書省指令 > 憲法 > 合約（高風險禁區須先警示） | W1 |
| C29 | CONTRACT | 單次任務 DoD 與暗部「本輪完成」DoD 分層；里程碑編號**以 Progress 為準** | W2 |
| C30 | AGENTS | **接戰／封存**口令語義；初始化四段：掛載地圖、讀取律法（Base_Agent／run_id／get_path）、檢查糧草（盲測不洩密）、現況審核（Status／刑部件數） | W1 |
| C31 | AGENTS | **紅線**：禁印 `.env`／金鑰、禁硬編磁碟路徑、禁雙 Telegram 監聽、禁主艙裝 crewai／langchain 等、禁新建 `hashes.txt` | W1 |
| C32 | AGENTS | 路徑與 runner **索引歸地圖**；程式經 `gov_paths`／`get_path` 解析 | W3 |
| C33 | Master_Map | **六部鍵**（01–06 相對部門）為路徑解析一級單位 | W3 |
| C34 | Master_Map | **aliases**（含刑部 `xing_bu`→暫存部）為邏輯別名，非第二套根 | W3 |
| C35 | Master_Map | **cabins** 表達「哪個 venv／用途域」；**禁止**在程式寫死絕對路徑 | W3 |
| C36 | Master_Map | `tang_gov_root` 空則以地圖檔上層為根——**可移植根解析規則** | W3 |
| C37 | Master_Map | `artifacts` 類（status、registry、plan）為**執行態錨點類型名**，非具體檔案實例 | W3 |
| C38 | Conditions | Conditions／Progress／`master_status`／`handoff` **職責分離**（制度 vs 迭代 vs 跨 agent 快照） | W1 |

---

## 2. 實例錨點條目表

| 條號 | 來源檔 | 簡述 | 歸入 |
|------|--------|------|------|
| I01 | Conditions | 專案根 `D:\大唐三省六部\` | 本戰車錨點 |
| I02 | Conditions | 暗部唯一工作區根 `...\gov_core_system\` 及「不得假設 `gov_core_system\` 於戰車根」 | 本戰車錨點 |
| I03 | Conditions | 暗部硬禁區、總部清算腳本之**完整絕對路徑清單** | W5 |
| I04 | Conditions | 當前總目標／階段說明（Phase1 基線、第二階段進行中、Postgres／Qdrant 已驗證） | W5 |
| I05 | Conditions | HQ 輪「2026-05-17 定案」、DarkOps **Blocked** 狀態 | W5 |
| I06 | Conditions | 各 worker **可碰絕對路徑**表（Governance／Tooling／config 子樹） | W5 |
| I07 | HARNESS | 文中 `D:\...` 專案根、暗部根、硬禁區逐條路徑 | W5 |
| I08 | HARNESS | `Master_Map.version` **2.60**、Gov Core V1 封版、Phase2 未展開等**進度錨點** | W5 |
| I09 | HARNESS | Progress 里程碑代號完成度（I0/I1、D1–D3、R1/R2、G1） | W5 |
| I10 | AGENTS | 交接句內嵌 `D:\大唐三省六部\AGENTS.md` | 本戰車錨點 |
| I11 | AGENTS | 具體 runner 表：Enter-Main、`_smoke_test_keys.py`、`_factory_wave_01.py` 等 | W5 |
| I12 | AGENTS | 封存步驟內 `cd D:\大唐三省六部`、README SOP 版本號 | W5 |
| I13 | AGENTS | 初始化回報欄位之**具體檔名**（`.telegram_listener.lock`、`Status.json`） | W5 |
| I14 | Master_Map | `version` 字串、description 內 v2.51–v2.60 **戰史 changelog** | W5 |
| I15 | Master_Map | `runners` 全表具體相對路徑與腳本檔名 | W5 |
| I16 | Master_Map | `cabins.*.python` 指向 `Scripts/python.exe` 之 OS 路徑 | W5 |
| I17 | Master_Map | `pipeline_meta_db`、`groq_quota_state`、docker-compose 等**實際落點** | W5 |
| I18 | Master_Map | `war_status`（as_of、milestones、wave_*、run_id 樣本、headline） | W5 |
| I19 | Master_Map | `secrets_status.rotated_at`、供應商輪替狀態 | W5 |
| I20 | Master_Map | `model_registry.yaml`、Groq 模型 ID、429 換模順序、RPM/RPD 護欄 | W5 |
| I21 | Master_Map | Wave／精煉分數、Asset_Value_Evaluator 統計、business_metrics 數值 | W5 |
| I22 | CONTRACT | 驗證範例中的 `collection: document_chunks`、`pg_ok` 等**實作鍵名錨點**（形狀可留 W2，鍵名對照源碼放 W5） | W5 |
| I23 | AGENTS | 三鑰盲測具體供應商名（OpenAI／Groq／Telegram）與 `[OK]` 判準 | W5 |

---

## 3. 禁止帶入三件套正文的類型清單

以下類型**不得**寫入 `HARNESS_CONSTITUTION`、`ENGINEERING_CONTRACT`、`DEPARTMENT_MAP` 正文；應改落實例層或 runbook。

| 類型 | 說明 | 應落在 |
|------|------|--------|
| 絕對磁碟路徑 | `D:\...`、`C:\Users\...`、venv 內 `Scripts\python.exe` | W5「本戰車錨點」；地圖 `runners`／`cabins` |
| 具體腳本／Runner 檔名與 CLI | `_smoke_test_keys.py`、`Enter-Main.ps1`、`phase1_verify.py` 等完整命令列 | W5 runbook；`Master_Map.runners` |
| 雲端／模型實例 ID | Groq 模型名、OpenAI deployment、供應商 API 端點 | W5；`model_registry.yaml` |
| 資料庫／集合實例名 | `pipeline_meta.DEFAULT_DB` 路徑、`document_chunks`、compose 服務名與埠 | W5；暗部 infra 文檔 |
| 密鑰與輪替戰史 | `.env` 鍵名原文、`rotated_at`、哪日輪替成功 | W5 `secrets_status`；盲測腳本說明 |
| Progress／war 日期戰史 | `2026-05-17`、里程碑逐條、wave 分數、run_id 樣本 | `00_Agent_Work_Progress.md`；`Master_Map.war_status` |
| **當輪** Blocked／Done 旗標 | 「registry Done」、某輪施工完成敘述等**帶日期之狀態** | Progress 黑板末尾 |
| Phase 制度性角色預設 | 如「第一階段 DarkOps-Worker Blocked」（**無日期**） | 憲法 §5／§6、地圖 §5（**非**本列禁止） |
| 健康檢查一次通過之證據 | `ASSERT: OK`、某次 `pg_ok` 成功敘述 | Progress／Work Report；非憲法 |
| 使用者家目錄與 IDE 路徑 | `%USERPROFILE%\.cursor\mcp.json`、plugins 落地路徑 | W5 工具盤點 |
| 排程與 OS 任務名 | `Tang_Chariot_Auto_Refine`、每日 03:00 | W5；scheduler runbook |
| 交接口令全文 | 含磁碟路徑的「接戰一句話」 | `AGENTS.md`（戰車實例層，非三件套） |
| 六部／別名之**具體相對路徑字串表** | 可保留「六部鍵＋別名語義」；不可複製整份 `departments`/`runners` JSON | `DEPARTMENT_MAP` 僅邏輯拓撲；細節在 `Master_Map.json` |

---

## 4. 交叉引用約定

三件套正文引用外部文件時：**只寫檔名＋一句職責**，不寫磁碟路徑、不複製長文。

| 檔名 | 職責（一句） |
|------|----------------|
| `00_Agent_Work_Conditions.md` | 長期制度與 HQ／暗部角色邊界之母本 |
| `00_Agent_Work_Progress.md` | 當前迭代目標、里程碑、阻塞與 QA 列之黑板 |
| `AGENTS.md` | 副官接戰／封存、初始化校準與戰車級紅線 |
| `Master_Map.json` | 相對路徑、六部、aliases、cabins、runners 之唯一權威索引 |
| `README_Refresher.md` | 日常 SOP 與點火細節（戰車實例操作，非憲法正文） |

**引用句式（範例）**：「路徑解析見 `Master_Map.json`（權威索引，非本文）。當前迭代見 `00_Agent_Work_Progress.md`。」

**分工提醒**：W1 憲法 ← C01–C24、C28、C30–C31；W2 合約 ← C05–C11、C16–C17、C25–C29；W3 部門圖 ← C21、C32–C37（邏輯拓撲，無實例路徑表）。

---

## 5. 尚書省審稿用：邊界模糊條目（2–3 條）

| 條號 | 模糊點 | 建議 |
|------|--------|------|
| **C35 ↔ I16** | 「cabins 概念」可進 W3，但 `venv_dir`／`python.exe` 是否允許**相對**路徑留在 W3 尚無定案 | 建議 W3 只保留 cabin **角色名與用途一句**；一切 `Scripts/python.exe` 落 W5 |
| **C22 ↔ I03** | 「硬禁區」作**類別**（venv 樹、.env、清算腳本）屬 W1；逐條絕對路徑必須 W5 | 三件套只列禁區**類型表**；實例清單單獨 `FORBIDDEN_ZONES_W5.md`（若需要） |
| **C37 ↔ I17** | `artifacts`／`pipeline_meta` 作**治理帳本類型**可移植；具體 `.db` 檔名與 `DEFAULT_DB` 為實例 | W3 寫「須有 pipeline 元資料帳本」；W5 寫實際檔與 env 鍵 |

---

*W0 產出；條目計數：核心 **38** 條｜實例 **23** 條。*
