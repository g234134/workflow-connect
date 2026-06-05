# ENGINEERING_CONTRACT v0.1

> **SUPERSEDED（2026-05-19）**：本檔已由 `04_Workflows/ENGINEERING_CONTRACT.md` 取代。僅供歷史稽核；接戰與施工請讀正式檔。裁決見 `project_status/HQ_PHASE1_FINALIZATION_ORDER.md`。

> **來源**：`04_Workflows/00_Agent_Work_Conditions.md`（共同原則、禁止事項、fallback、DoD、回報格式）、`04_Workflows/00_Agent_Work_Progress.md`（驗收與證據習慣）、`AGENTS.md` 紅線、本 session 協調官起手式／Work Report 約定、戰車既有「先文件後程式」「最小可執行」紀律。  
> **性質**：本稿為依現有材料蒸餾之草稿；四大流派名稱採本 session 已定名；12-rule 由上述材料歸納，**非**來自既存獨立檔案之逐字複製。

---

## 文件定位

| 項目 | 說明 |
|------|------|
| **名稱** | ENGINEERING_CONTRACT v0.1 |
| **層級** | 戰車「執行層」行為合約 |
| **適用對象** | 所有執行實作、除錯、驗收之 Agent 與 worker（含被授權代寫之協調官） |
| **與憲法分工** | 憲法定**邊界與國家結構**；本合約定**如何讀、如何改、如何交、如何停** |
| **修訂原則** | 與憲法衝突時，以尚書省當次指令為準，但須留痕；合約修訂不得弱化憲法禁區 |

---

## 1. 總則

### 1.1 目的

- 將多 Agent 協作中的工程行為收斂為**可重複、可驗收、可交接**之共同節奏。
- 降低互踩、假完成、無證據交付與無聲擴 scope 之風險。

### 1.2 基本承諾

- **先理解，後動手**：未完成 Context-Driven 與 Source-Driven 盤點前，不提交程式變更方案。
- **先骨架，後血肉**：Incremental Engineering 允許 skeleton，但須在交付物中**明確標示**。
- **先證據，後結論**：Debugging-Driven Engineering 以可重跑之命令輸出、`dict` 欄位或斷言字串為準，不以自然語言代替驗收。
- **回傳可機器讀**：核心路徑回傳 `dict`；僅供人閱讀之說明寫入 Work Report 或 notes。

### 1.3 不做的事

- 不將「推測存在」的檔案、API、環境變數寫入實作或文件為既成事实。
- 不把整理性草稿冒充為已跑過之驗收證據。
- 不在單次任務中夾帶與任務無關之重構（Incremental 之最小變更原則）。

---

## 2. 四大工程流派

> 四流派為**並行姿態**，非嚴格時間先後；新任務須在四者均有最低覆蓋後，方可標記為「可交付」。

### 2.1 Context-Driven Engineering（上下文驅動）

**定義**：在改動任何產物前，先建立與任務相關之**制度與迭代上下文**。

**必讀清單（依任務裁剪，不得憑空省略）**：

| 優先級 | 材料 | 目的 |
|--------|------|------|
| P0 | 尚書省當次指令 | 任務邊界 |
| P0 | `HARNESS_Constitution_v0.1`（本憲法） | 禁區與角色 |
| P0 | 本合約 | 行為節奏 |
| P1 | `00_Agent_Work_Conditions.md` 相關章 | 細部制度 |
| P1 | `00_Agent_Work_Progress.md` 相關里程碑 | 當前完成度與阻塞 |
| P2 | 目標模組之 `brief.md` / `notes.md` | 局部契約 |
| P2 | `Master_Map.json` 之 `runners` / 路徑別名 | 執行入口 |
| P2 | `AGENTS.md`（若涉接戰／封存／糧草） | 戰車級紅線 |

**產出**：起手式中的「角色／可碰路徑／禁區」確認（2～5 行）；若上下文不足，標記阻塞而非假設。

---

### 2.2 Source-Driven Engineering（源碼／源檔驅動）

**定義**：在撰寫或修改實作前，**已讀取**將觸及之真實檔案內容，並以 repo 內實物為準。

**規則**：

- 列舉**將讀／將改**檔案清單；未讀不改（協調官唯讀盤點時除外）。
- import 路徑、函式簽名、設定鍵名須與源碼一致；不可用記憶或猜測代替 `Read`／搜尋。
- 路徑解析須對齊 `gov_paths` 與 `Master_Map.json`，禁止硬編 `D:\...`。
- 若源檔不存在：走 fallback，**不**虛構實作。

**產出**：變更清單與依據（哪個檔、哪段邏輯）；必要時附最小重現命令。

---

### 2.3 Incremental Engineering（增量交付）

**定義**：以**最小可驗收增量**推進；允許 skeleton，禁止假完成。

**規則**：

- 單次 diff 僅服務當次任務明示範圍；不順手重構未點名檔案。
- 第一輪優先：結構、邊界、可執行入口、回傳 `dict` 形狀；第二輪再填業務邏輯。
- skeleton 須在 Work Report 之「可執行 skeleton」與「placeholder」分欄標示。
- 跨模組需求以**介面契約**或 notes 描述，不擅自改他人 `core`。

**產出**：可執行之最小增量 + 明確未完成列表。

---

### 2.4 Debugging-Driven Engineering（除錯／驗證驅動）

**定義**：以**可重跑之驗證**支撐「完成」宣稱。

**規則**：

- 優先使用 repo 既有驗證入口（如 `phase1_verify`、`infra_health_agent`、`_smoke_test_keys.py`、各 agent CLI），不另發明未登記之「假測試」。
- 金鑰類驗證僅解讀 `[OK]`/`[FAILED]` 與 HTTP code；**不**輸出或記錄金鑰原文。
- 宣稱通過時，Work Report 須含：**命令（或 runner 名）** + **關鍵輸出語意**（如 `verify_ok`、`ASSERT: OK`），非僅「已測試」。
- 失敗時：保留錯誤語意、標記阻塞、不掩蓋為成功。

**產出**：驗證證據摘要；若無法驗證，不得標記任務完成。

---

## 3. 12-rule 行為合約

> 以下十二條為執行層**強制規則**；違反任一條不得宣稱任務完成。

**Rule 1 — 起手確認**  
每次新任務開始，須先完成 Context-Driven 之角色、可碰路徑、禁區確認；重大行動前以 2～5 行說明計畫，供尚書省中途喊停。

**Rule 2 — 先讀後寫**  
未對將修改之檔案執行 Source-Driven 讀取（或等價之定向搜尋並核對命中）前，不得提交變更。

**Rule 3 — 最小觸及**  
僅修改任務明示要求之檔案與邏輯；其餘發現以「後續建議」列入 Work Report，不夾帶實作。

**Rule 4 — dict 契約**  
核心路徑函式與 agent CLI 結果須回傳結構化 `dict`（或 JSON 可序列化物件）；不可僅以 `print` 作為唯一交付。

**Rule 5 — 禁區紅線**  
不得擅自修改 `.env`、暗部硬禁區、清算類腳本；不得對 `gov_core_system` venv 樹執行未授權之 pip／寫入。

**Rule 6 — 路徑權威**  
禁止在程式中硬編磁碟路徑；須經 `gov_paths` 與 `Master_Map.json`；刑部暫存經別名 `xing_bu` 解析。

**Rule 7 — 誠實標示**  
skeleton 與 placeholder 須在 Work Report 分欄列出；**禁止**將 placeholder 標為完成。

**Rule 8 — 邊界尊重**  
不得修改非本人擁有之 `core/*.py` 或他人 `brief.md` / `progress.md` / `notes.md`；需改時先停、開票或取得授權並留痕。

**Rule 9 — fallback 不崩潰**  
依賴缺失時回傳 `{"ok": false, "message": "..."}` 並寫入 progress／notes；禁止未處理例外導致整鏈沉默失敗。

**Rule 10 — 阻塞必錄**  
任何阻塞須寫入 progress 或 Progress 黑板（末尾追加）；禁止默默跳過或假裝完成。

**Rule 11 — 驗證後宣稱**  
完成宣稱前須滿足 Debugging-Driven 之最低證據；無證據則狀態為未完成或阻塞。

**Rule 12 — override 留痕**  
當尚書省指令與憲法／本合約衝突時，須先一句話指出衝突點；若仍執行，須在 progress／notes 或 Work Report 記錄 override 原因與影響範圍。

---

## 4. 標準工作流程

### 4.1 起手式（任務受理）

1. **Context**：讀 Conditions／Progress／憲法／本合約／任務相關 brief。  
2. **邊界**：確認 HQ／Dark／Chariot／Tools 與禁區。  
3. **Source**：列將讀／將改檔案；執行必要讀取。  
4. **計畫**：2～5 行說明做法、最小交付、驗證方式。  
5. **確認**：尚書省喊停或默認繼續後進入實作。

### 4.2 實作期（Incremental + Source）

- 按最小增量修改；保持 `dict` 回傳形狀穩定。  
- 跨模組依賴僅記錄契約需求，不越權實作。

### 4.3 驗收期（Debugging-Driven）

- 執行任務定義之驗證命令或 runner。  
- 蒐集可重跑證據；失敗則轉阻塞。

### 4.4 收尾（Work Report）

- 依附錄 A 填寫 Work Report。  
- 若涉里程碑變更，由 Governance 或授權方末尾追加 Progress（本合約不代寫內容）。

---

## 5. fallback 與停工規則

### 5.1 fallback（可繼續但降級）

| 條件 | 行為 |
|------|------|
| 依賴模組／檔案不存在 | 最小 skeleton 或 `ok: false` + message |
| 他方 `core` 未就緒 | 不接管；notes 記錄所需介面 |
| 驗證腳本不可用 | 標記阻塞，列出替代驗證或所需修復 |

### 5.2 停工（不得繼續實作）

| 條件 | 行為 |
|------|------|
| 未授權且需碰暗部硬禁區 | 停工，一句話說明禁區 |
| DarkOps Blocked 且任務需改暗部根 | 停工，要求開票 |
| 路徑與 `Master_Map.json` 衝突無授權 | 停工，要求地圖更新或改任務 |
| 無法滿足 Rule 5／6 且無 override | 停工 |

### 5.3 提醒後遵從（override）

- 尚書省在知悉衝突後仍明確要求執行 → 依 Rule 12 留痕後執行。  
- 高風險禁區（`.env`、清算腳本）須**先警示**再執行。

---

## 6. 交付定義（DoD）

### 6.1 單次任務 DoD（執行 Agent）

至少同時滿足：

- [ ] 已完成 Context + Source 盤點（可追溯）  
- [ ] 變更範圍符合 Rule 3、8  
- [ ] 核心路徑回傳 `dict`（Rule 4）  
- [ ] Work Report 已填（附錄 A）  
- [ ] skeleton／placeholder 已分欄標示（Rule 7）  
- [ ] 已完成任務定義之驗證，或已標記阻塞與原因（Rule 11）  
- [ ] 無未留痕之憲法／合約違反（Rule 12）

### 6.2 暗部板塊 Agent「本輪完成」（對齊 Conditions）

在單次任務 DoD 之上，若宣稱板塊本輪完成，尚須：

- 已建立／維護 `brief.md`、`progress.md`、`notes.md`  
- 已建立至少一個可執行 agent 腳本與對應 `core/*.py`  
- `progress.md` 含：已完成、未完成、阻塞、下一步  

（具體里程碑編號以 Progress 為準，本合約 v0.1 不新增編號。）

### 6.3 協調官任務 DoD

- 任務卡、驗收條件、邊界檢查已完成；  
- 若未授權代寫，**無檔案變更**亦須交付 Work Report 說明「僅協調」。

---

## 7. 與憲法的分工

| 主題 | 憲法 | 本合約 |
|------|------|--------|
| 國家結構、禁區、角色 | ✓ 定義 | 引用執行 |
| 四大板塊職責邊界 | ✓ 定義 | 引用執行 |
| Master_Map.version 意義 | ✓ 定義 | 引用執行 |
| 四大工程流派 | — | ✓ 定義 |
| 12-rule | — | ✓ 定義 |
| 起手式、Work Report | — | ✓ 定義 |
| fallback／停工 | 原則 | ✓ 操作細則 |
| AGENTS 接戰／封存 | ✓ 銜接 | 驗證時引用 |

**衝突處理**：尚書省指令 > 憲法 > 本合約（除高風險禁區須先警示外）。

---

## 附錄 A：Work Report 模板

```markdown
## Work Report

**任務**：（一句話）
**角色**：（如 HQ-Coordinator / Data Agent / …）
**日期**：（UTC 或本地，擇一標註）

### 1. 變更檔案
- 新建：
- 修改：
- （若僅協調／唯讀：寫「無檔案變更」）

### 2. 可執行 skeleton
- （列項，或「無」）

### 3. placeholder（未完成）
- （列項，或「無」）

### 4. 驗證證據（Debugging-Driven）
- 命令／runner：
- 關鍵結果：（如 verify_ok、ASSERT 字串、[OK]/[FAILED]）

### 5. 阻塞
- （無則寫「無」）

### 6. 下一步建議
1.
2.

### 7. 憲法／合約
- override：（無／有，簡述）
- 留痕位置：（無／progress／notes／Progress 末尾）
```

---

## 附錄 B：最小結構化回傳範例

### B.1 成功（單檔 ingest 語意摘要）

```json
{
  "ok": true,
  "message": "ingest completed",
  "path_resolution": "file",
  "ingest": {
    "ok": true,
    "chunks": 16,
    "collection": "document_chunks"
  },
  "verify": {
    "ok": true,
    "message": "verify_ok"
  }
}
```

### B.2 fallback（依賴缺失）

```json
{
  "ok": false,
  "message": "dependency not found: core.data_pipeline.ingest_batch"
}
```

### B.3 健康檢查（Infra 語意摘要）

```json
{
  "ok": true,
  "all_ok": true,
  "postgres": { "ok": true, "message": "pg_ok" },
  "qdrant": { "ok": true, "message": "qdrant_ok" },
  "verify": { "ok": true, "message": "verify_ok" }
}
```

> 以上欄位為**形狀範例**；實際鍵名以 repo 內 `core` 實作為準，不得憑空新增未被源碼使用之必填欄位並宣稱已驗收。

---

## v0.1 定位

- 本檔為 **v0.1 草稿**：將 Conditions 中可執行之工程紀律與本 session 四大流派命名、12-rule 歸納合為單一合約，**不取代** `00_Agent_Work_Conditions.md`。
- **不涵蓋** Phase 2 以後之 GraphRAG job 狀態機、Monitoring 後端選型、產品化 SLO 等細節；該等目標以 Progress「下一輪優先順序」為準，待專票另訂驗收。
- 與憲法、Progress、`Master_Map.json`、`AGENTS.md` 並用；尚書省確認後方可升格為 repo 內正式檔案版本。
