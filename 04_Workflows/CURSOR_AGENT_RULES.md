# 工程執行規則（Cursor / Agent 機器版）

> **性質**：`ENGINEERING_CONTRACT.md` 的條文化、可驗證化執行層規則。  
> **適用**：本 repo 內被指派的 Cursor / IDE / Chat Agent、HQ 協作輪 worker。  
> **不取代**：憲法邊界、合約正文、`AGENTS.md` 接戰入口。  
> **實例解析**：具體路徑、venv、DB、env 鍵見 `INSTANCE_ANCHOR_TANG.md` 與 `Master_Map.json`（本檔不出現實例值）。

---

## §0 元資料與適用邊界

### [META-0.1] 規則檔角色

- **MUST**：將本檔視為「執行層行為約束」；遇禁區類型、四域結構、Phase 門檻時，以 `HARNESS_CONSTITUTION.md` 為準並僅引用其條號。
- **FORBID**：用本檔重新定義憲法 §7 禁區類型表、四域結構或國家組織全表。
- **CHECKPOINT**：審稿時確認禁區描述是否寫成「引用憲法 §7」而非自創類型表。
- **violation_example**：在規則檔內複製一整張 Z-ENV／Z-VENV 類型表並宣稱為本檔定義。
- **來源**：合約 §1；憲法 §1、§12

### [META-0.2] 適用對象

- **MUST**：凡因任務被指派之 Cursor / Chat Agent、HQ 協作輪 worker，開工前須聲明已讀本規則檔（或等價之 `ENGINEERING_CONTRACT.md`）。
- **FORBID**：以「未收到規則檔」為由跳過合約節奏（除非尚書省當次指令明確豁免且留痕）。
- **CHECKPOINT**：起手式中是否出現「已讀 ENGINEERING_CONTRACT／本規則檔」。
- **來源**：合約 §1；憲法 §1

### [META-0.3] 權威位階

- **MUST**：衝突時依序適用：尚書省當次指令 ＞ 憲法 ＞ `ENGINEERING_CONTRACT.md`／本規則檔 ＞ 任務局部 `brief.md`／`notes.md`。
- **MUST**：觸及高風險禁區（憲法 §7 類型，尤其環境／密鑰類）時，即使尚書省 override，仍須**先明示風險**再執行。
- **FORBID**：以本規則檔或任務 brief 覆蓋憲法硬禁區而無 override 留痕。
- **CHECKPOINT**：回答中是否標註「依據哪一層權威」及是否有 override 留痕。
- **來源**：合約 §5 末段；憲法 §5.3、§7.2

### [META-0.4] 可移植邊界

- **MUST**：本規則檔正文、Work Report、起手式中，路徑一律使用 repo 相對路徑或 `Master_Map.json` 邏輯名／別名。
- **FORBID**：在規則檔、回報、程式變更說明中寫入本機實體根路徑、venv 實際路徑、`DEFAULT_DB` 名、`.db` 檔名、env 鍵原文、具體禁區磁碟路徑。
- **CHECKPOINT**：全文搜尋是否出現磁碟代號式絕對路徑或具體環境值。
- **violation_example**：在規則或回報中寫死本機 venv 的 `python` 絕對路徑或具名 DB 檔。
- **來源**：合約 §1、§12；憲法 §4

### [META-0.5] 與 AGENTS.md 分工

- **MUST**：涉接戰、封存、糧草驗證時，以 `AGENTS.md` 為執行入口；本規則檔定工程節奏，不取代其口令與初始化細節。
- **FORBID**：在 AGENTS 已規定之紅線上另立較寬標準。
- **來源**：合約 §1、§3.1；憲法 §12

---

## §1 Context 控制（起手必讀）

### [CTX-1.1] P0 必讀

- **MUST**：動任何檔案前，在回答中列出已閱讀之 P0 材料：（1）尚書省當次指令或任務卡邊界；（2）`HARNESS_CONSTITUTION.md`（禁區類型、Phase、衝突位階）；（3）`ENGINEERING_CONTRACT.md` 或本規則檔。
- **FORBID**：未列 P0 已讀清單即提交變更方案或 patch。
- **CHECKPOINT**：回答開頭是否有「已讀清單」區塊。
- **violation_example**：直接改 `core` 卻未提及憲法或合約。
- **來源**：合約 §3.1；Rule 1

### [CTX-1.2] P1 條件必讀

- **MUST**：任務涉及全局制度、里程碑、阻塞時，裁剪閱讀 `00_Agent_Work_Conditions.md`、`00_Agent_Work_Progress.md` 之相關章，並列入已讀清單。
- **FORBID**：在需對齊當前迭代時，僅憑記憶假設 Progress 狀態。
- **CHECKPOINT**：已讀清單是否含 Conditions／Progress（若任務相關）。
- **來源**：合約 §3.1

### [CTX-1.3] P2 條件必讀

- **MUST**：改特定模組前，讀該模組 `brief.md`／`notes.md`；需執行 runner 時，查 `Master_Map.json` 之 runners／別名（**不複製 JSON 全文**）。
- **MUST**：涉接戰／封存／糧草時，將 `AGENTS.md` 列入已讀。
- **FORBID**：把 `Master_Map.json` 整份貼進回報代替索引引用。
- **來源**：合約 §3.1、§3.2

### [CTX-1.4] 引用句式

- **MUST**：指向路徑權威時，使用合約標準句式：「路徑解析見 `Master_Map.json`（權威索引，非本文）。當前迭代見 `00_Agent_Work_Progress.md`。」
- **FORBID**：在無地圖依據下自創路徑字串並寫死於程式或規則。
- **來源**：合約 §3.2；Rule 6

### [CTX-1.5] 狀態來源聲明

- **MUST**：在已讀清單後，用 1–3 句說明「從哪份檔得知當前狀態／阻塞／里程碑」。
- **FORBID**：聲稱「專案已完成某里程碑」而無 Progress 或任務卡依據。
- **CHECKPOINT**：是否有「狀態依據」句。
- **來源**：合約 §2.1；Rule 1、2

---

## §2 操作原則 — 總則（四大承諾）

### [GEN-2.1] 先理解，後動手

- **MUST**：未完成 Context-Driven 與 Source-Driven 最低盤點前，不提交程式變更方案。
- **FORBID**：跳過盤點直接大規模改檔。
- **CHECKPOINT**：變更方案前是否已有 §1 已讀清單 + §3 四流派最低覆蓋聲明。
- **來源**：合約 §2.1、§2.2

### [GEN-2.2] 先骨架，後血肉

- **MUST**：允許交付 skeleton 時，在 Work Report 與回覆中**明確標示**哪些為骨架、哪些為真實邏輯。
- **FORBID**：將 skeleton 或 placeholder 描述為已驗收完成之功能。
- **CHECKPOINT**：Work Report §2／§3 是否分欄填寫。
- **來源**：合約 §2.2；Rule 7

### [GEN-2.3] 先證據，後結論

- **MUST**：以可重跑命令輸出、`dict` 欄位或斷言字串作為完成依據；人讀說明寫入 Work Report 或 notes。
- **FORBID**：以整理草稿、推測、未執行之命令冒充驗收證據。
- **CHECKPOINT**：宣稱「完成」時是否附命令與關鍵結果語意。
- **violation_example**：「應該可以跑過」但無 runner 輸出。
- **來源**：合約 §2.2；Rule 11

### [GEN-2.4] 回傳可機器讀

- **MUST**：核心路徑回傳結構化 `dict`；不可僅 `print` 代替契約回傳。
- **FORBID**：在對外／對下游介面以純自然語言代替 `dict` 結果。
- **來源**：合約 §2.2；Rule 4

### [GEN-2.5] 總則禁止（與 §5 呼應）

- **FORBID**：將推測存在的檔案、API、環境變數寫成既成事實。
- **FORBID**：單次任務夾帶無關重構或無聲擴大 scope。
- **FORBID**：把整理草稿冒充已跑過的驗收證據。
- **來源**：合約 §2.3

---

## §3 四大工程流派

> 四流派為**並行姿態**；新任務須在四者均有最低覆蓋後，方可標記「可交付」。

### 3.1 Context-Driven Engineering

#### [CD-3.1.1] 何時啟用

- **MUST**：每個新任務、新 session 起手時啟用；改動前建立制度與迭代上下文。
- **來源**：合約 §4.1

#### [CD-3.1.2] 最低要求

- **MUST**：在起手式產出 2–5 行：角色、可碰範圍、禁區確認（引用憲法 §7 類型，不列實例路徑）。
- **MUST**：重大行動（多檔重構、改 `core`、觸及驗證 runner）前，先給 2–5 行計畫。
- **CHECKPOINT**：回答是否含「角色／可碰／禁區」三要素。
- **來源**：合約 §4.1；Rule 1

#### [CD-3.1.3] 常見違規

- **FORBID**：未確認禁區類型即修改環境樹、venv 樹、runtime checkpoint、暗部維運腳本等（類型見憲法 §7）。
- **violation_example**：未讀憲法即宣稱「可以改 .env 試一下」。
- **來源**：合約 §4.1；Rule 5

### 3.2 Source-Driven Engineering

#### [SD-3.2.1] 何時啟用

- **MUST**：列舉將讀／將改檔案之前、每一次實作增量之前啟用。
- **來源**：合約 §4.2

#### [SD-3.2.2] 最低要求

- **MUST**：明確列出將讀、將改之檔案清單；**未讀不改**。
- **MUST**：路徑須對齊 `gov_paths` 與 `DEPARTMENT_MAP.md`／`Master_Map.json` 邏輯，禁止硬編磁碟路徑。
- **MUST**：源檔不存在時，走 fallback（§8），不得假裝已讀。
- **CHECKPOINT**：變更清單中每個路徑是否可追溯至已讀聲明。
- **來源**：合約 §4.2；Rule 2、6

#### [SD-3.2.3] 常見違規

- **FORBID**：修改從未讀取之檔案。
- **FORBID**：憑推測建立「應該存在」的 import 或路徑常數。
- **violation_example**：patch `foo.py` 但已讀清單無 `foo.py`。
- **來源**：合約 §4.2、§2.3；Rule 2

### 3.3 Incremental Engineering

#### [IN-3.3.1] 何時啟用

- **MUST**：整個實作期持續；每次提交增量前自問是否為「最小可驗收增量」。
- **來源**：合約 §4.3

#### [IN-3.3.2] 最低要求

- **MUST**：優先最小可驗收增量；skeleton 與 placeholder 在 Work Report 分欄標示。
- **MUST**：不擅自修改非本人負責之 `core` 模組或他人 agent workspace 三件套（`brief`／`progress`／`notes`）。
- **CHECKPOINT**：diff 範圍是否超出任務明示範圍。
- **來源**：合約 §4.3；Rule 3、7、8

#### [IN-3.3.3] 常見違規

- **FORBID**：借任務之名重構無關模組、統一風格、順手修 lint 全庫。
- **FORBID**：接管他人 `core` 實作因其「尚未就緒」。
- **violation_example**：任務是修單一 API，卻改動四個部門之 `core`。
- **來源**：合約 §4.3、§2.3；Rule 3、8

### 3.4 Debugging-Driven Engineering

#### [DB-3.4.1] 何時啟用

- **MUST**：宣稱完成、標記可交付、關閉阻塞前啟用；健康檢查與管線驗證亦同。
- **來源**：合約 §4.4

#### [DB-3.4.2] 最低要求

- **MUST**：使用 repo 既有驗證入口（任務定義之 runner／命令，名見 `Master_Map.json`）。
- **MUST**：金鑰／糧草類驗證僅解讀 `[OK]`／`[FAILED]`，**嚴禁輸出金鑰原文**（憲法 §7.3、§12）。
- **MUST**：宣稱完成須附：執行之命令（或 runner 邏輯名）+ 關鍵輸出語意（非必須全文逐字，但須可審計）。
- **CHECKPOINT**：Work Report §4 是否填寫。
- **來源**：合約 §4.4；Rule 11

#### [DB-3.4.3] 常見違規

- **FORBID**：無 runner 執行即標「已驗證通過」。
- **FORBID**：在回報中貼出 secret、token、完整連線字串。
- **violation_example**：「邏輯上應該沒問題」取代實際跑驗證。
- **來源**：合約 §4.4、§2.3；Rule 11

### 3.5 四流派交付閘門

#### [GATE-3.5.1] 可交付標記

- **MUST**：僅當 Context、Source、Incremental、Debugging 四流派均已滿足各節最低要求後，方可標記任務「可交付」。
- **FORBID**：缺驗證證據或缺已讀盤點即標可交付。
- **CHECKPOINT**：收尾時是否逐項勾選四流派（可在 Work Report 或自檢句中一句帶過）。
- **來源**：合約 §4 段首（C25）；§7.1

---

## §4 12-rule 行為合約

### [RULE 1] 起手確認

- **MUST**：起手完成 Context 盤點：角色、可碰範圍、禁區（2–5 行）；重大行動前再給 2–5 行計畫。
- **FORBID**：無計畫即跨多模組改動。
- **CHECKPOINT**：審稿首段是否含起手三要素與計畫。
- **來源**：合約 Rule 1

### [RULE 2] 先讀後寫

- **MUST**：Source-Driven：列檔 → 讀取 → 再改。
- **FORBID**：對未讀檔案直接 patch。
- **CHECKPOINT**：已讀清單是否覆蓋所有將改路徑。
- **來源**：合約 Rule 2

### [RULE 3] 最小觸及

- **MUST**：僅修改任務明示範圍內檔案與邏輯；必要擴張須先說明並獲任務邊界內默許。
- **FORBID**：順手重構、無關格式化全庫、無聲增加功能。
- **CHECKPOINT**：變更清單每項是否對應任務卡條目。
- **來源**：合約 Rule 3

### [RULE 4] dict 契約

- **MUST**：核心路徑（對外介面、agent 主流程、健康檢查等）回傳結構化 `dict`，形狀穩定。
- **FORBID**：以非結構化輸出代替契約回傳；擅自新增必填欄位並宣稱已驗收（具體欄位以 repo 內 `core` 與合約附錄 B 為準）。
- **CHECKPOINT**：是否說明回傳 `dict` 之 `ok`／`message` 或專案慣用鍵。
- **來源**：合約 Rule 4；附錄 B

### [RULE 5] 禁區紅線

- **MUST**：改動前對照憲法 §7 禁區**類型**；觸及須有尚書省授權或明確 override 流程（§8）。
- **FORBID**：擅自修改環境與密鑰類、venv 套件樹、未授權 runtime checkpoint、暗部破壞性維運腳本、總部清算類腳本等（完整類型表見憲法 §7.1，本檔不重複）。
- **FORBID**：DarkOps-Worker 預設 Blocked 狀態下改暗部根內實作（憲法 §5.2、§6.1）。
- **CHECKPOINT**：變更是否觸及 Z-* 類型；觸及是否有授權／留痕。
- **violation_example**：未開票即改 `.env` 或暗部 `dark_ops` 保留腳本。
- **來源**：合約 Rule 5；憲法 §7

### [RULE 6] 路徑權威

- **MUST**：路徑經 `gov_paths` 與 `Master_Map.json` 解析；刑部相關經約定別名（如 `xing_bu`）。
- **FORBID**：在程式、規則、回報中硬編磁碟絕對路徑。
- **CHECKPOINT**：diff 中是否出現硬編路徑常數。
- **來源**：合約 Rule 6；憲法 §4

### [RULE 7] 誠實標示

- **MUST**：skeleton 與 placeholder 在 Work Report 分欄列出，並在回覆中明說未完成部分。
- **FORBID**：placeholder 當完成品交付。
- **CHECKPOINT**：Work Report §2、§3 非空或明確寫「無」。
- **來源**：合約 Rule 7

### [RULE 8] 邊界尊重

- **MUST**：僅改本人負責之 `core` 與本人 workspace；跨模組需求寫入 notes，不接管。
- **FORBID**：修改他人 `core` 或他人 agent workspace 三件套。
- **CHECKPOINT**：變更路徑是否落在任務指派之 agent／模組邊界內。
- **來源**：合約 Rule 8；憲法 §9.1–§9.2

### [RULE 9] fallback 不崩潰

- **MUST**：依賴缺失時回傳 `ok: false`（或專案等價鍵）+ 可讀 `message`；或交付標示清楚之 skeleton；並寫入自身 `progress`／`notes`。
- **FORBID**：因依賴缺失而崩潰、靜默失敗、或假裝成功。
- **CHECKPOINT**：fallback 回傳是否含 message 與留痕位置。
- **來源**：合約 Rule 9；§11.1

### [RULE 10] 阻塞必錄

- **MUST**：無法繼續時，將阻塞寫入 `00_Agent_Work_Progress.md`（待確認格式）或自身 agent `progress` **末尾**。
- **FORBID**：口頭稱阻塞卻不寫入任何 progress 載體。
- **CHECKPOINT**：Progress 或自身 progress 末尾是否有阻塞條目。
- **來源**：合約 Rule 10；§11.1

### [RULE 11] 驗證後宣稱

- **MUST**：無可審計證據則標「未完成」或「阻塞」，不得標「完成」。
- **FORBID**：無 runner／命令輸出即關閉任務。
- **CHECKPOINT**：Work Report §4 與完成聲明是否一致。
- **來源**：合約 Rule 11；§7.1

### [RULE 12] override 留痕

- **MUST**：發現與憲法／合約／地圖衝突時，**先指出**再依尚書省指令執行；執行後於 progress／notes 或 Progress 黑板**末尾**留痕（原因、影響、是否一次性）。
- **FORBID**：靜默違反後不記錄。
- **CHECKPOINT**：Work Report §7 是否填 override 與留痕位置。
- **來源**：合約 Rule 12；憲法 §5.2

---

## §5 禁止項（FORBID 彙總）

> 本章為快速審查用彙總；各 RULE／流派條目仍保留具體 FORBID，兩者並存。

### [BAN-5.1] 事實與證據

- **FORBID**：推測寫死（檔案、API、env 存在性）。
- **FORBID**：草稿、計畫、腦內測試冒充驗收證據。
- **FORBID**：無證據宣稱完成。
- **來源**：合約 §2.3；Rule 11

### [BAN-5.2] 範圍與誠實

- **FORBID**：單次任務無關重構、無聲擴 scope。
- **FORBID**：skeleton／placeholder 冒充完成。
- **來源**：合約 §2.3；Rule 3、7

### [BAN-5.3] 禁區與暗部（引用憲法）

- **FORBID**：未授權觸及憲法 §7 所列禁區**類型**。
- **FORBID**：DarkOps Blocked 時改暗部根內實作（須另開票解禁）。
- **FORBID**：輸出金鑰原文；糧草驗證僅解讀 `[OK]`／`[FAILED]`。
- **來源**：合約 Rule 5；憲法 §5.2、§7、§7.3

### [BAN-5.4] 路徑與地圖

- **FORBID**：硬編磁碟路徑；與 `Master_Map.json` 衝突且無授權之路徑寫法。
- **FORBID**：在可移植規則／三件套正文中寫實例根路徑、venv、DB 名、env 鍵。
- **來源**：合約 Rule 6；憲法 §4

### [BAN-5.5] 邊界與接管

- **FORBID**：改非本人 `core`；改他人 workspace 三件套；接管他人未完成介面。
- **來源**：合約 Rule 8；§11.1

### [BAN-5.6] 黑板與狀態檔（引用憲法）

- **FORBID**：覆蓋、刪除、重排 `00_Agent_Work_Conditions.md`、`00_Agent_Work_Progress.md` 既有段落（僅允許**末尾追加**）。
- **FORBID**：未授權寫入 `project_status/master_status.md`、`handoff.md`（預設 Governance 獨占，憲法 §6.3）。
- **來源**：憲法 §6.2、§6.3、§9.2

### [BAN-5.7] 戰車級紅線（引用憲法／AGENTS）

- **FORBID**：同時兩個 Telegram 監聽器（以 lock 檔為準，實例名見實例錨點）。
- **FORBID**：在主艙安裝 crewai／langchain 等重套件（統包艙職責）。
- **FORBID**：新建 `hashes.txt`；指紋須走 registry 類帳本。
- **來源**：憲法 §7.3；合約 §3.1（AGENTS）

### [BAN-5.8] 規則檔／合約體系

- **FORBID**：在本規則檔內重寫憲法全文或複製 `DEPARTMENT_MAP.md` 全表。
- **FORBID**：把 `ENGINEERING_CONTRACT` 原文整段貼入規則檔代替條文化。
- **來源**：合約 §1、§12

---

## §6 Review / Plan / Loop 節奏

### [FLOW-6.1] 起手式（標準步驟 1）

- **MUST**：依序完成：Context 盤點 → 任務邊界確認 → Source 列檔 → 2–5 行計畫 → 必要時尚書省確認後再動手。
- **FORBID**：跳過起手式直接實作。
- **CHECKPOINT**：第一輪回覆是否完成五步中至少前四步。
- **來源**：合約 §6 步驟 1；§6 全節

### [FLOW-6.2] 實作期（標準步驟 2）

- **MUST**：最小增量交付；保持 `dict` 回傳形狀穩定；持續遵守 Rule 3、8。
- **FORBID**：長時間無中間產出仍宣稱接近完成。
- **來源**：合約 §6 步驟 2

### [FLOW-6.3] 驗收期（標準步驟 3）

- **MUST**：執行任務定義之 runner／命令；結果寫入 Work Report §4。
- **FORBID**：略過驗收期進入收尾。
- **來源**：合約 §6 步驟 3

### [FLOW-6.4] 收尾期（標準步驟 4）

- **MUST**：提交 Work Report（§7）；里程碑變更僅由授權方在 Progress **末尾追加**。
- **FORBID**：自行在合約或規則檔新增里程碑編號（編號以 Progress 為準）。
- **來源**：合約 §6 步驟 4；§7.2（C29）

### [FLOW-6.5] 單次任務 DoD

- **MUST**：交付前自檢以下各項均已滿足或已標阻塞：
  - Context + Source 盤點可追溯
  - 變更符合 Rule 3、8
  - 核心路徑回傳 `dict`
  - Work Report 已填
  - skeleton／placeholder 已分欄
  - 已完成任務定義驗證，或已標阻塞
  - 無未留痕之憲法／合約違反
  - 四流派最低覆蓋已滿足（§3.5 / 合約 §4.5）
- **CHECKPOINT**：收尾回覆附 DoD 勾選或等價自檢表。
- **來源**：合約 §7.1

### [FLOW-6.6] 暗部板塊「本輪完成」DoD（加項）

- **MUST**：在 §7.1 之上，暗部 agent 任務另需：三份 workspace 文、可執行 agent、對應 `core`、progress 四欄（完成／未完成／阻塞／下一步）。
- **FORBID**：以本規則檔新增里程碑編號。
- **來源**：合約 §7.2（C10）

### [FLOW-6.7] 協調官 DoD

- **MUST**：HQ-Coordinator 類任務：任務卡與驗收條件完成；若僅協調無改檔，Work Report 須註明「無檔案變更」。
- **來源**：合約 §7.4

### [FLOW-6.9] 暗部協作順序與欄位對齊

- **MUST**：暗部四 Agent 解禁後，建議順序為 Infra → Data → RAG → Governance；並行時各 Agent 僅改本人範圍，Governance 須容忍他方 fallback。
- **MUST**：跨模組觀測欄位不一致時，由 **Governance** 一次性對齊，並記 handoff／notes。
- **FORBID**：他方各自發明全域欄位名。
- **CHECKPOINT**：暗部多 Agent 並行任務是否標註順序與欄位對齊責任方。
- **來源**：合約 §7.5（C16–C17）；組織表見 `DEPARTMENT_MAP.md` §7

### [FLOW-6.8] 審稿與裁決節奏

- **MUST**：起草方交付：檔案路徑 + 變更摘要 + 自檢清單；必要時對照 W0 可移植／實例分流；盲測與升格由尚書省／W4 流程裁決（執行 worker 不自行宣布 Phase 通過）。
- **FORBID**：worker 自標合約或規則檔「v1.0」定稿號。
- **來源**：合約 §7.3、§10

---

## §7 輸出與 Work Report

### [OUT-7.1] 每輪最小交付（全 Agent）

- **MUST**：每輪工作結束時，回覆或 Work Report 至少涵蓋：變更清單、skeleton 狀態、placeholder 狀態、阻塞、下一步建議（W0 C11）。
- **FORBID**：僅給自然語言結論無結構化五項。
- **來源**：合約 §10.4；§7.1

### [OUT-7.2] Work Report 必填欄

- **MUST**：使用下列結構填寫 Work Report：

```markdown
## Work Report

**任務**：（一句話）
**角色**：（如 HQ-Governance-Worker / Data Agent）
**日期**：（UTC 或本地，擇一標註）

### 1. 變更檔案
- 新建：
- 修改：

### 2. 可執行 skeleton
-

### 3. placeholder（未完成）
-

### 4. 驗證證據
- 命令／runner：
- 關鍵結果：

### 5. 阻塞
-

### 6. 下一步建議
1.

### 7. 憲法／合約
- override：（無／有）
- 留痕位置：
```

- **CHECKPOINT**：七個小節是否齊全或明確標「無」。
- **來源**：合約 附錄 A

### [OUT-7.3] 文檔工單額外要求

- **MUST**：若任務類型為「文檔工單」（如起草三件套、規則轉制），Work Report 或回報中須加一句：**「文檔工單自檢：見本規則附錄『文檔工單自檢要點』」**，並逐項簡答是／否 + 一句證據。
- **FORBID**：把 Phase 1 完整自檢表（§10.3 全表）硬塞進規則本體或每條 MUST。
- **來源**：合約 §10、§10.4

### [OUT-7.4] Worker 回報三件套（尚書省驗收用）

- **MUST**：Phase 1 類文檔起草回報缺一不可：（1）檔案路徑列表；（2）每檔 3–8 條變更要點；（3）自檢清單（文檔工單用附錄要點）。
- **來源**：合約 §10.1–§10.3

### [OUT-7.5] 結構化回傳形狀

- **MUST**：說明成功／fallback／健康檢查之 `dict`／JSON **形狀**時，以合約附錄 B 與 repo 內 `core` 為準。
- **FORBID**：憑空新增 collection／必填鍵並宣稱已驗收；具體名稱僅可指向實例錨點與地圖，不寫入本規則正文。
- **來源**：合約 附錄 B

### [OUT-7.6] 無檔案變更

- **MUST**：協調、審稿、唯讀 QA 等無改檔任務，Work Report §1 明寫「無檔案變更」。
- **來源**：合約 §7.4

---

## §8 錯誤處理、Fallback 與停工

### [FB-8.1] 依賴不存在

- **MUST**：交付標示清楚之 skeleton，或回傳 `ok: false` + `message`；寫入自身 progress／notes。
- **FORBID**：假裝依賴已存在並接續實作。
- **來源**：合約 §11.1；Rule 9

### [FB-8.2] 他方 core 未就緒

- **MUST**：不接管他人 `core`；在 notes 記錄介面需求與阻塞。
- **FORBID**：越權實作他人模組以「解阻塞」。
- **來源**：合約 §11.1；Rule 8

### [FB-8.3] 驗證腳本不可用

- **MUST**：標記阻塞；列替代驗證方案或所需授權；不得宣稱完成。
- **FORBID**：略過驗證仍關閉任務。
- **來源**：合約 §11.1；Rule 11

### [STOP-8.4] 停工 — 硬禁區

- **MUST**：未授權碰憲法 §7 硬禁區時，**立即停工**；回報禁區**類型**與任務卡編號；請尚書省裁決。
- **FORBID**：繼續改檔或嘗試繞過。
- **來源**：合約 §11.2；憲法 §7.2、§11

### [STOP-8.5] 停工 — DarkOps Blocked

- **MUST**：任務需改暗部根內實作而 DarkOps-Worker 未解禁時，停工並要求另開票。
- **來源**：合約 §11.2；憲法 §5.2、§6.1

### [STOP-8.6] 停工 — 地圖衝突

- **MUST**：路徑與 `Master_Map.json` 衝突且無授權時，停工；要求更新地圖或修改任務範圍。
- **來源**：合約 §11.2；憲法 §7.2

### [STOP-8.7] 停工 — Rule 5／6 無法滿足

- **MUST**：無法滿足禁區紅線或路徑權威且無合法 override 時，停工請人類裁決。
- **來源**：合約 §11.2

### [STOP-8.8] 停工 — 無施工授權

- **MUST**：未收到尚書省明確授權（任務卡或當次指令）時，不得開始施工；已誤動手須立即停止並回報。
- **來源**：憲法 §5.2、§11

### [OV-8.9] Override 執行

- **MUST**：尚書省 override 後：高風險禁區先明示風險 → 執行 → 於 Progress／notes **末尾**留痕（原因、影響、是否一次性）。
- **FORBID**：override 後不留痕。
- **來源**：合約 Rule 12；憲法 §5.2、§7.2

---

## §9 與其他載體的引用索引

### [REF-9.1] 憲法

- **MUST**：禁區**類型**、四域、Phase 門檻、黑板紀律、Pipeline 帳本制度 → 引用 `HARNESS_CONSTITUTION.md` 對應 §，不在此重定義。
- **來源**：合約 §12；憲法 §1、§7、§8

### [REF-9.2] 工程合約

- **MUST**：四大流派、12-rule、起手式、Work Report、審稿節奏 → 以 `ENGINEERING_CONTRACT.md` 為母本；本規則檔為其機器執行版。
- **來源**：合約 §12

### [REF-9.3] 組織地圖

- **MUST**：組織拓撲、cabin 角色與用途 → `DEPARTMENT_MAP.md`；不在此複製全表。
- **來源**：合約 §1

### [REF-9.4] 路徑與 runner

- **MUST**：相對路徑、runners、cabins → `Master_Map.json`；邏輯名可述，不複製整份 JSON。
- **來源**：合約 §3.1；憲法 §10

### [REF-9.5] 實例錨點

- **MUST**：禁區具體路徑、venv 進入方式、DB 落點、env 鍵、驗證鍵名 → 僅查 `INSTANCE_ANCHOR_TANG.md`；**禁止**寫入本規則正文。
- **來源**：合約 §1、§12；憲法 §4

### [REF-9.6] W0 索引

- **MUST**：可移植條目分流與主責對照 → `04_Workflows/_PORTABLE_CORE_INDEX.md`；審稿時對照 C/I 邊界，不把 W0 表貼入規則檔。
- **來源**：合約 §3、附錄 C

---

## §10 Phase 與規則檔自身邊界

### [PH-10.1] 本檔來歷

- **MUST**：認知本檔為 **Phase 2** 產物：在 Phase 1 三件套 + 實例錨點對齊 W0，且 **W4 盲測 10/10 通過** 後，方可起草／轉制 `.cursor/rules`。
- **FORBID**：在 Phase 1 工單中把本檔正文當作已定稿制度強制執行（除非尚書省明確提前授權）。
- **來源**：合約 §8；憲法 §5.1

### [PH-10.2] 不取代關係

- **MUST**：本規則檔**不取代**憲法、`ENGINEERING_CONTRACT.md`、`AGENTS.md`；衝突時依 §0.3 位階處理。
- **FORBID**：在規則檔內刪改或重寫憲法／合約條文；爭議以原檔為準。
- **來源**：合約 §1、§8；憲法 §5.1

### [PH-10.3] 維護責任

- **MUST**：本規則檔修訂須與合約同步審核；版本號與是否升格由尚書省裁決，worker 不自標 v1.0。
- **來源**：合約 §7.3、§10.3

### [PH-10.4] 檔頭識別

- **MUST**：轉制至 `.cursor/rules` 時，保留檔頭說明：Phase 2 產物、母本為 `ENGINEERING_CONTRACT.md`、憲法定邊界。
- **來源**：合約 §8；本 Phase 2 工單裁決

---

## 附錄：文檔工單自檢要點

> 任務類型為「文檔工單」時，Work Report 應參考本附錄逐項簡答（是／否 + 一句證據）。**非**日常實作任務之 MUST 條文。

- 正文（憲法／合約／地圖類可移植檔）是否**零**本機絕對路徑？
- 組織地圖是否涵蓋約定範圍（六部、暗部、HQ 角色等 — 以任務卡為準）？
- Cabin 描述是否僅角色／用途（具體 venv 進入方式是否在實例錨點）？
- 禁區是否僅寫**類型**（具體路徑是否在實例錨點）？
- Pipeline 制度是否在可移植層、DB／env 是否在實例錨點？
- 是否已對齊 W0 索引、未與 Conditions／Progress／AGENTS 衝突？
- 是否**未**在 Phase 1 偷寫 `.cursor/rules` 正文、未自標定稿版本號？

**來源**：合約 §10.3（要點化，非全文嵌入）

---

## 文末自檢清單（Phase 2 草案驗收）

| 檢查項 | 結果 |
|--------|------|
| **四大流派**是否均有「何時啟用／最低要求／常見違規」？ | ✓ §3.1–§3.4 + §3.5 閘門 |
| **12-rule**是否逐條具 MUST／FORBID／CHECKPOINT？ | ✓ §4 [RULE 1]–[RULE 12] |
| **禁止項**是否獨立成章且與各 RULE FORBID 並存？ | ✓ §5 |
| **DoD**是否覆蓋單次任務、暗部加項、協調官、暗部協作順序？ | ✓ §6 [FLOW-6.5]–[FLOW-6.7]、[FLOW-6.9] |
| **Work Report**最小欄位與模板是否完整？ | ✓ §7 [OUT-7.2]；文檔工單見附錄 |
| **停工條件**是否明列（硬禁區、DarkOps、地圖衝突、Rule 5/6、無授權）？ | ✓ §8 [STOP-8.4]–[STOP-8.8] |
| **每條規則**是否標註「來源：合約 §x / Rule x」？ | ✓ 全文條目均已標註 |
| **是否無**實例根路徑、venv 路徑、`DEFAULT_DB`、env 鍵、具體禁區磁碟路徑？ | ✓ 僅用邏輯名與「見實例錨點」表述 |
| **憲法**是否僅引用、未重定義禁區表與四域？ | ✓ §0、§5.3、§9.1 |
| **§10 Phase 邊界**是否保留？ | ✓ §10 |
