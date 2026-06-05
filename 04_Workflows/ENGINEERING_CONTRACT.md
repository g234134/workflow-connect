# 工程合約

> **角色**：執行層行為合約（可移植層）。  
> **對照**：W0 索引 `04_Workflows/_PORTABLE_CORE_INDEX.md`；憲法邊界見 `HARNESS_CONSTITUTION.md`；實例 runner／DB 見 `INSTANCE_ANCHOR_TANG.md`。  
> **版本**：由尚書省裁決；本文不自標定稿號。

---

## 1. 文件定位

| 項目 | 說明 |
|------|------|
| **層級** | 戰車「執行層」——如何讀、如何改、如何交、如何停 |
| **與憲法** | 憲法定邊界與國家結構；本合約定工程節奏與驗收 |
| **與 AGENTS.md** | 接戰／封存／糧草紅線以 AGENTS 為**戰車接戰入口**；本合約不取代其職責 |
| **與 DEPARTMENT_MAP** | 組織全表見地圖檔；本文僅交叉引用，**不複製全表** |

---

## 2. 總則

### 2.1 目的

將多 Agent 協作收斂為**可重複、可驗收、可交接**之共同節奏，降低互踩、假完成、無證據交付與無聲擴 scope。

### 2.2 基本承諾

- **先理解，後動手**：未完成 Context-Driven 與 Source-Driven 盤點前，不提交程式變更方案。  
- **先骨架，後血肉**：允許 skeleton，須在交付物中**明確標示**。  
- **先證據，後結論**：以可重跑命令輸出、`dict` 欄位或斷言字串為準。  
- **回傳可機器讀**：核心路徑回傳 `dict`；人讀說明寫入 Work Report 或 notes。

### 2.3 不做的事

- 不將推測存在的檔案、API、環境變數寫成既成事實。  
- 不把整理草稿冒充已跑過的驗收證據。  
- 不在單次任務中夾帶無關重構。  
- 不起草 `.cursor/rules`（Phase 2，見 §8）。

---

## 3. 與 W0 及三件套交叉引用

### 3.1 必讀清單（依任務裁剪）

| 優先 | 材料 | 目的 |
|------|------|------|
| P0 | 尚書省當次指令 | 任務邊界 |
| P0 | `HARNESS_CONSTITUTION.md` | 禁區類型、Phase 門檻 |
| P0 | 本合約 | 行為節奏 |
| P1 | `00_Agent_Work_Conditions.md` 相關章 | 細部制度 |
| P1 | `00_Agent_Work_Progress.md` 相關里程碑 | 當前完成度 |
| P2 | 目標模組 `brief.md`／`notes.md` | 局部契約 |
| P2 | `Master_Map.json` 之 runners／別名 | 執行入口（**不複製 JSON 全文**） |
| P2 | `AGENTS.md`（涉接戰／封存／糧草時） | 戰車紅線 |

### 3.2 引用句式

「路徑解析見 `Master_Map.json`（權威索引，非本文）。當前迭代見 `00_Agent_Work_Progress.md`。」

---

## 4. 四大工程流派

四流派為**並行姿態**（非嚴格時間先後）；新任務須在四者均有最低覆蓋後，方可標記「可交付」（W0：C25）。

### 4.1 Context-Driven Engineering

| 維度 | 內容 |
|------|------|
| **定義** | 改動前建立制度與迭代上下文 |
| **最低要求** | 起手式含角色、可碰範圍、禁區確認（2–5 行）；禁區僅引用憲法 §7 **類型**，不列實例路徑 |
| **產出** | 已讀清單 + 狀態依據句（1–3 句）；重大行動前另給 2–5 行計畫 |

### 4.2 Source-Driven Engineering

| 維度 | 內容 |
|------|------|
| **定義** | 以 repo 內真實檔案為準；**未讀不改** |
| **最低要求** | 列舉將讀／將改檔案；路徑對齊 `gov_paths` 與地圖邏輯名；源檔不存在則 fallback |
| **產出** | 變更清單與依據（哪個檔、哪段邏輯） |

### 4.3 Incremental Engineering

| 維度 | 內容 |
|------|------|
| **定義** | 最小可驗收增量；允許 skeleton，禁止假完成 |
| **最低要求** | 單次 diff 僅服務任務明示範圍；skeleton／placeholder 分欄標示；不擅自改他人 `core` |
| **產出** | 可執行之最小增量 + 明確未完成列表 |

### 4.4 Debugging-Driven Engineering

| 維度 | 內容 |
|------|------|
| **定義** | 以可重跑驗證支撐「完成」宣稱 |
| **最低要求** | 使用任務定義之 runner／命令（邏輯名見 `Master_Map.json`）；金鑰類僅解讀 `[OK]`／`[FAILED]` |
| **產出** | 命令（或 runner 邏輯名）+ 關鍵輸出語意；失敗則轉阻塞 |

### 4.5 四流派交付閘門

僅當 §4.1–§4.4 均已滿足各節最低要求後，方可標記任務「可交付」。缺任一流派覆蓋不得關閉工單。

---

## 5. 12-rule 行為合約

> 以下十二條為執行層**強制規則**；違反任一條不得宣稱任務完成（W0：C26）。

| # | 規則 | 要點 |
|---|------|------|
| 1 | 起手確認 | Context：角色、可碰、禁區；重大行動前 2–5 行計畫 |
| 2 | 先讀後寫 | Source-Driven 讀取後再改 |
| 3 | 最小觸及 | 僅改任務明示範圍 |
| 4 | dict 契約 | 核心路徑回傳結構化 `dict`（形狀見附錄 B） |
| 5 | 禁區紅線 | 不擅自碰憲法 §7 禁區**類型**；DarkOps Blocked 時不改暗部根 |
| 6 | 路徑權威 | 禁硬編磁碟路徑；刑部經 `xing_bu` 別名 |
| 7 | 誠實標示 | skeleton／placeholder 分欄 |
| 8 | 邊界尊重 | 不改非本人 `core` 或他人 workspace 三件套 |
| 9 | fallback 不崩潰 | `ok:false` + message；寫 progress／notes |
| 10 | 阻塞必錄 | Progress 或自身 progress 末尾 |
| 11 | 驗證後宣稱 | 無證據則未完成或阻塞 |
| 12 | override 留痕 | 衝突時先指出；執行後於 progress／notes 或 Progress **末尾**留痕 |

**衝突位階**（W0：C28）：尚書省指令 ＞ 憲法 ＞ 本合約（高風險禁區須先警示）。

---

## 6. 標準工作流程

### 6.1 起手式（任務受理）

1. **Context**：讀 Conditions／Progress／憲法／本合約／任務相關 brief。  
2. **邊界**：確認 HQ／Dark／Chariot／Tools 與禁區類型。  
3. **Source**：列將讀／將改檔案；執行必要讀取。  
4. **計畫**：2–5 行說明做法、最小交付、驗證方式。  
5. **確認**：尚書省喊停或默認繼續後進入實作。

### 6.2 實作期

- 最小增量（Incremental + Source）；保持 `dict` 回傳形狀穩定。  
- 跨模組依賴僅記錄契約需求，不越權實作他人 `core`。

### 6.3 驗收期

- 執行任務定義之 runner／命令（Debugging-Driven）。  
- 蒐集可重跑證據；失敗則轉阻塞。

### 6.4 收尾

- 填寫 Work Report（附錄 A）。  
- 里程碑變更由授權方在 Progress **末尾追加**；本合約不新增里程碑編號（W0：C29）。

### 6.5 與四流派對照

| 階段 | 對應流派 |
|------|----------|
| 6.1 | Context + Source |
| 6.2 | Source + Incremental |
| 6.3 | Debugging-Driven |
| 6.4 | 全流派收斂 + §4.5 閘門 |

---

## 7. 交付物定義與審稿／裁決

### 7.1 單次任務 DoD（W0：C29）

- [ ] Context + Source 盤點可追溯  
- [ ] 變更符合 Rule 3、8  
- [ ] 核心路徑回傳 `dict`  
- [ ] Work Report 已填  
- [ ] skeleton／placeholder 已分欄  
- [ ] 已完成任務定義驗證，或已標阻塞  
- [ ] 無未留痕之憲法／合約違反  
- [ ] 四流派最低覆蓋已滿足（§4.5）

### 7.2 暗部板塊「本輪完成」DoD（W0：C10）

在單次 DoD 之上：三份 workspace 文 + 可執行 agent + 對應 `core` + progress 四欄（完成／未完成／阻塞／下一步）。**里程碑編號以 Progress 為準**，本合約不新增編號。

### 7.3 審稿與裁決流程

| 階段 | 責任方 | 產出 | 通過條件 |
|------|--------|------|----------|
| **起草** | 執行 worker（W1–W5 等） | 檔案路徑 + 每檔 3–8 條變更摘要 + 自檢清單（§10） | 尚書省受理審稿 |
| **W0 對照** | worker 或 QA | 38 可移植／23 實例分流正確；附錄 C 主責條目可追溯 | 無實例洩漏進 W1–W3 正文 |
| **盲測** | **W4**（QA-Reviewer） | Progress 末尾 **QA 列**：10 項可移植邊界檢查，逐項 PASS／FAIL | **10/10 全 PASS** 方可進 Phase 2 |
| **裁決** | 尚書省 | 版本號、是否升格定稿、是否觸發 rules 轉制 | 以裁決為準；worker **不得**自宣 Phase 2 解鎖 |

**W4 盲測 10/10 定義**（可移植邊界，對象為 Phase 1 交付集 W1+W2+W3+W5）：

| # | 檢查項 | FAIL 典型 |
|---|--------|-----------|
| 1 | 三件套（W1–W3）正文零絕對磁碟路徑 | 出現 `D:\`、`C:\Users\` |
| 2 | 三件套零具體 runner 檔名與完整 CLI | 內嵌 `_smoke_test_keys.py` 等可執行檔名 |
| 3 | 三件套零雲端／模型實例 ID | Groq／OpenAI 模型名寫入可移植正文 |
| 4 | 三件套零 DB／集合實例名 | collection 名、`.db` 檔名寫入 W1–W3 |
| 5 | 三件套零密鑰與輪替戰史 | `.env` 鍵原文、`rotated_at` 敘述 |
| 6 | 可移植正文零 Progress／war 日期戰史 | 嵌入 `2026-05-17`、wave 分數等 |
| 7 | 可移植正文零**當輪** Blocked／Done 旗標 | 帶日期之 Done／「registry Done」等 Progress 戰史寫入三件套。**PASS**：Phase 制度性「DarkOps Blocked」（無日期，見憲法 §5.2／§6.1） |
| 8 | 憲法級正文零一次性健康證據 | 某次 `ASSERT: OK` 當制度 |
| 9 | 三件套零使用者家目錄／IDE 路徑 | `%USERPROFILE%\.cursor\` 等 |
| 10 | 三件套未複製整份 `departments`／`runners` JSON | 長表貼入取代索引引用 |

**計分**：10 項皆 PASS → **10/10**；任一 FAIL → 退回起草方修補，**不解鎖** Phase 2。盲測腳本與糧草判準之實例細節見 `INSTANCE_ANCHOR_TANG.md`（W0：I23）；本合約不重複。

### 7.4 協調官 DoD

任務卡與驗收條件完成；若僅協調無改檔，Work Report 須註明「無檔案變更」。

### 7.5 暗部協作順序與欄位對齊（W0：C16–C17）

| 主題 | 規則 |
|------|------|
| **建議順序** | 暗部四 Agent 解禁後：Infra → Data → RAG → Governance |
| **並行** | 各 Agent 僅改本人範圍；Governance 須容忍他方 fallback |
| **欄位歧義** | 跨模組觀測欄位不一致時，由 **Governance** 一次性對齊，並記 handoff／notes；他方不各自發明全域欄位名 |

組織拓撲與四 Agent 職責表見 `DEPARTMENT_MAP.md` §7；憲法 §9 為制度母本。

---

## 8. Phase 2 觸發條件（W4 閘門）

| 條件 | 說明 |
|------|------|
| **前置** | Phase 1 三件套 + `INSTANCE_ANCHOR_TANG.md` 已對齊 W0 |
| **閘門** | **W4 盲測 10/10 通過**（定義見 §7.3；QA 列寫入 Progress 末尾） |
| **允許** | 起草／轉制 `.cursor/rules`（母本見 `CURSOR_AGENT_RULES.md`，Phase 2 工單） |
| **禁止（Phase 1）** | 本工單不得寫 rules 正文或 Phase 2 實作細則 |

**並行說明**：W1–W3–W5 起草可與 W4 盲測準備並行；**通過 10/10 之前**不得將 `.cursor/rules` 定稿為強制制度。worker 交付時須聲明「待 W4 10/10」而非「Phase 2 已開」。

---

## 9. 並行工單：W1–W3–W5 與 W4 盲測

| 工單 | 產出 | 並行關係 |
|------|------|----------|
| W1 | `HARNESS_CONSTITUTION.md` | 與 W2、W3、W5 並行；正文零實例路徑 |
| W2 | 本檔 | 同上 |
| W3 | `DEPARTMENT_MAP.md` | 同上；cabin 僅角色／用途 |
| W5 | `INSTANCE_ANCHOR_TANG.md` | 收斂 23 條實例錨點 |
| W4 | 盲測 | **不依賴**三件套定稿即可準備；**10/10 通過**後才解鎖 Phase 2 |

並行時禁止：在 W1–W3 偷帶 W5 才該有的路徑；在 W5 重寫憲法級可移植原則而無 W1 對應條文。

---

## 10. Worker 回報格式（路徑＋摘要＋自檢）

尚書省驗收 Phase 1 起草時，worker **缺一不可**：

### 10.1 檔案路徑

列出實際寫入／更新的路徑（相對戰車根即可）。

### 10.2 變更摘要

每檔 **3–8 條**要點：新增章節、解決 W0 哪幾條邊界（如 C35↔I16、C22↔I03、C37↔I17）。

### 10.3 自檢清單（APP-DOC 七項）

> **APP-DOC**：文檔工單適用之七項可移植檢查；逐項答「是／否 + 一句證據」。W2 工單以本表為準（與 `CURSOR_AGENT_RULES.md` 附錄「文檔工單自檢要點」對齊）。

| # | 檢查項 | 是／否 + 證據 |
|---|--------|----------------|
| 1 | 正文零本機絕對路徑 | |
| 2 | 組織／職責引用地圖，未複製全表 | |
| 3 | Cabin 僅角色／用途（具體 venv 在 W5） | |
| 4 | 禁區僅類型（具體路徑在 W5） | |
| 5 | Pipeline 制度在可移植層；DB／env 在 W5 | |
| 6 | 已對齊 W0；未與 Conditions／Progress／AGENTS 衝突 | |
| 7 | 未寫 `.cursor/rules`；未自標 v1.0 定稿號 | |

### 10.4 與全 Agent 回報的關係（W0：C11）

| 任務類型 | 回報準則 |
|----------|----------|
| **Phase 1 文檔工單** | §10.1–§10.3（APP-DOC 七項） |
| **暗部／實作工單** | 五項：變更清單、skeleton、placeholder、阻塞、下一步；並附 Work Report（附錄 A） |

---

## 11. fallback 與停工

### 11.1 fallback（可繼續但降級）（W0：C09）

| 條件 | 行為 |
|------|------|
| 依賴不存在 | skeleton 或 `ok:false` + message |
| 他方 core 未就緒 | 不接管；notes 記錄介面需求 |
| 驗證腳本不可用 | 標阻塞，列替代方案 |

### 11.2 停工

未授權碰硬禁區；DarkOps Blocked；地圖衝突無授權；無法滿足 Rule 5／6 且無 override；未收到尚書省施工授權。

---

## 12. 與憲法分工表

| 主題 | 憲法 | 本合約 |
|------|------|--------|
| 國家結構、禁區類型 | ✓ | 引用 |
| 四大板塊邊界 | ✓ | 引用 |
| 四大流派、12-rule | — | ✓ |
| 起手式、Work Report、審稿流程 | — | ✓ |
| W4 10/10 閘門 | 引用 §5.1 | ✓ §7.3、§8 |
| AGENTS 接戰／封存 | 銜接 | 驗證時引用 |

---

## 附錄 A：Work Report 模板

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

---

## 附錄 B：結構化回傳形狀（可移植）

> **分流**（W0：I22）：本附錄僅定 **JSON 形狀**（巢狀 `ok`／`message`、可選計數與子物件）；**具體 collection 名、驗證狀態鍵名、斷言字串與源碼對照**見 `INSTANCE_ANCHOR_TANG.md` §6。實際必填欄位以 repo 內 `core` 實作為準，不得憑空新增並宣稱已驗收。

### B.1 成功（業務語意摘要）

```json
{
  "ok": true,
  "message": "<human_readable_summary>",
  "path_resolution": "<logical_scope>",
  "primary_result": {
    "ok": true,
    "count": 0,
    "resource": "<logical_resource_name>"
  },
  "verify": {
    "ok": true,
    "message": "<status_token>"
  }
}
```

### B.2 fallback（依賴缺失）

```json
{
  "ok": false,
  "message": "dependency not found: <module_or_path_semantic>"
}
```

### B.3 健康檢查（多子系統摘要）

```json
{
  "ok": true,
  "all_ok": true,
  "subsystem_a": { "ok": true, "message": "<status_token>" },
  "subsystem_b": { "ok": true, "message": "<status_token>" },
  "verify": { "ok": true, "message": "<status_token>" }
}
```

---

## 附錄 D：H 線 — 上下文入口合同（Context Entry）

> **詳細合同**：`context/context_entry_contract.md`  
> **實作**：`core/context_entry.py` → `build_rooted_context`

### D.1 強制條款（新入口）

- **MUST**：所有**新建** ask-like 流程、LangGraph 長任務首節點、規劃中的對外 API 上下文組裝，須呼叫 `core.context_entry.build_rooted_context` 作為唯一上下文入口。  
- **FORBID**：在入口處手寫或拼接 `root_context` / `working_context` / `long_term_memory`；禁止為繞過 N 線而跳過 `context.build_context` 底層組裝。  
- **MUST**：擴展僅透過 `task_input` 鍵或返回後追加欄位；**不得**修改 `build_context` 函數簽名以適配新入口。  
- **MAY**：v0.1 示範對齊一條既有路徑（如 K-1）；歷史路徑遷移須單開工單，本票不要求全庫替換。

### D.2 驗收

- 單元：`python -m unittest tests.test_context_entry -v`  
- 可選：`python -m unittest tests.test_langgraph_flow_k1 -v`（K-1 已對齊入口時）

### D.3 與 N 線分工

| 層級 | 職責 |
|------|------|
| N 線 `context/` | 分層模型、路由規則、`build_context` 裁剪與 mock 檢索 |
| H 線 `context_entry` | 入口合同、ID 預設、頂層欄位標準化、`mode` trace |
| 工程合約 Rule 4 | 核心路徑仍回傳結構化 `dict`（形狀見附錄 B + 合同 §2.2） |

---

## 附錄 C：W0 可移植條目對照（合約主責）

本檔主責吸收 W0：**C05–C11、C16–C17、C25–C29**（索引見 `_PORTABLE_CORE_INDEX.md` §1）。

| 條號 | 簡述 | 本檔對應 |
|------|------|----------|
| C05 | 核心回傳結構化 `dict` | §2.2、§5#4、附錄 B |
| C06 | 先文件後程式；workspace 三件套 | §6.1、§7.2 |
| C07 | 先 skeleton 後血肉 | §2.2、§7.1 |
| C08 | 全域禁止（引用憲法） | §5#5；細則見憲法 §7 |
| C09 | fallback 不崩潰 | §11.1、§5#9 |
| C10 | 暗部本輪 DoD 四欄 | §7.2 |
| C11 | 回報格式五項／文檔 §10 | §10.4 |
| C16 | 暗部建議順序與並行容忍 | §7.5 |
| C17 | 跨模組欄位 Governance 對齊 | §7.5 |
| C25 | 四大工程流派 | §4 |
| C26 | 12-rule | §5 |
| C27 | 起手→實作→驗收→Work Report | §6 |
| C28 | 衝突位階 | §5 末段 |
| C29 | 單次 DoD vs 板塊 DoD；里程碑以 Progress 為準 | §7.1–§7.2 |

**W2 定稿自檢**：上表 14 條均可指向本檔章節；附 §10.3 APP-DOC 七項通過後，方可提交尚書省審稿。
