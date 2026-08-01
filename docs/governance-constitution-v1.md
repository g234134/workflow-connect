# Governance Constitution v1 — Active Snapshot

> **版本**：`v1.0-active`  
> **狀態**：active snapshot（收斂視圖，**非**母本定稿號）  
> **維護票**：W1-T1B · 治理合約與禁區規則收斂  
> **日期**：2026-06-09  
> **完整來源追溯**：`04_Workflows/tickets/W1-T1B_governance_consolidation.md` → Sources Index

---

## §0 Document Meta

### 0.1 本文件是什麼

本檔是 **目前實際生效** 之治理、工程合約、禁區規則與 Wave／Ticket 運作的 **收斂視圖（active snapshot）**。

| 項目 | 說明 |
|------|------|
| **目的** | 讓 Reviewer／Agent 讀 **一份檔** 即可對齊 no-go、預設約定與開票流程 |
| **不是** | 憲法／合約母本的全文替換；新审批制度；repo 結構重設計 |
| **與母本衝突時** | **以母本為準**；本檔標 `[待確認]` 或差異說明 |

### 0.2 與並列／母本文件的關係

| 檔案 | 定位 | 本檔對其處置 |
|------|------|--------------|
| `docs/governance.md` | Phase 1 **分支／提交／環境**規範 | **並列**；分支命名、commit type 見該檔，不在此重複 |
| `04_Workflows/HARNESS_CONSTITUTION.md` | 憲法母本（禁區**類型**、四域、Phase） | **引用**，不重定義 §7 類型表 |
| `04_Workflows/ENGINEERING_CONTRACT.md` | 工程合約母本（四流派、12-rule、DoD） | **引用**，正文為摘要 |
| `.cursor/rules/engineering-contract.mdc` | 合約機器執行層 | **對齊**；Cursor Agent 自動載入 |
| `AGENTS.md` | 接戰／封存入口、戰車級紅線 | **引用**；口令與初始化細節以 AGENTS 為準 |
| **本檔** `docs/governance-constitution-v1.md` | 治理／合約／禁區／Wave **active snapshot** | — |

Phase 1 正式權威三件套 + W0/W5 見 `04_Workflows/project_status/HQ_PHASE1_FINALIZATION_ORDER.md`。

### 0.3 權威位階

```
尚書省當次指令 ＞ HARNESS_CONSTITUTION.md ＞ ENGINEERING_CONTRACT.md ＞ 本檔 ＞ brief.md / notes.md
```

高風險禁區 override 須**先明示風險**，再執行並於 Progress／notes **末尾**留痕。

### 0.4 Sources Index（精簡）

完整表見 `04_Workflows/tickets/W1-T1B_governance_consolidation.md`。Top 來源：

| # | 來源 | 納入章節 | 處置 |
|---|------|----------|------|
| 1 | `HARNESS_CONSTITUTION.md` | §2, 附錄 A | 引用 |
| 2 | `ENGINEERING_CONTRACT.md` | §1 | 引用摘要 |
| 3 | `AGENTS.md` | §2, §3, §5 | 纳入摘要 |
| 4 | `INSTANCE_ANCHOR_TANG.md` | §2.7 | 引用 |
| 5 | `tickets/README.md` | §4 | 纳入 |
| 6 | `OPS_CYCLE.md` | §4.6 | 纳入 |
| 7 | `multi_chat_roles.mdc` | §3.8, §5.5 | 纳入 |
| 8 | `GOVERNANCE_ONBOARDING_v1.md` | §3.1, §5 | 引用 |
| 9 | `context/context_entry_contract.md` | §3.5, §5 | 引用 |

---

## §1 Engineering Contract (Active)

> 母本：`04_Workflows/ENGINEERING_CONTRACT.md` · 機器層：`.cursor/rules/engineering-contract.mdc`

### 1.1 四流派最低要求 `[DEFAULT]`

四流派**並行**；任務須在四者均有最低覆蓋後，方可標「可交付」。

| 流派 | 最低要求 | 產出 |
|------|----------|------|
| **Context-Driven** | 起手含角色、可碰、禁區（2–5 行）；重大行動前 2–5 行計畫 | 已讀清單 + 狀態依據句 |
| **Source-Driven** | 列將讀／將改檔；**未讀不改**；路徑對齊 `gov_paths`／`Master_Map.json` | 變更清單與依據 |
| **Incremental** | 最小可驗收增量；skeleton／placeholder **分欄**；不改他人 `core` | 可執行增量 + 未完成列表 |
| **Debugging-Driven** | 任務定義 runner／命令；金鑰類僅 `[OK]`／`[FAILED]` | 命令 + 關鍵輸出語意 |

**閘門 `[DEFAULT]`**：缺任一流派最低覆蓋 → **不得**關票或標完成。

### 1.2 12 Rules 速查

| # | 規則 | 標籤 | 要點 |
|---|------|------|------|
| 1 | 起手確認 | `[DEFAULT]` | 角色、可碰、禁區；計畫 2–5 行 |
| 2 | 先讀後寫 | `[SHOULD]` | Source-Driven：讀後再改 |
| 3 | 最小觸及 | `[SHOULD]` | 僅改任務明示範圍 |
| 4 | dict 契約 | `[DEFAULT]` | 核心路徑回傳結構化 `dict` |
| 5 | 禁區紅線 | `[NO-GO]` | 不擅自碰憲法 §7 類型；DarkOps Blocked 不改暗部根 |
| 6 | 路徑權威 | `[NO-GO]` | 禁硬編磁碟路徑；刑部經 `xing_bu` 別名 |
| 7 | 誠實標示 | `[SHOULD]` | skeleton／placeholder 分欄 |
| 8 | 邊界尊重 | `[NO-GO]` | 不改非本人 `core` 或他人 workspace 三件套 |
| 9 | fallback 不崩潰 | `[DEFAULT]` | `ok: false` + `message`；寫 progress／notes |
| 10 | 阻塞必錄 | `[SHOULD]` | Progress 或自身 progress **末尾** |
| 11 | 驗證後宣稱 | `[NO-GO]` | 無 runner／命令證據 → 未完成或阻塞 |
| 12 | override 留痕 | `[SHOULD]` | 衝突先指出；執行後末尾留痕 |

### 1.3 標準執行節奏 `[DEFAULT]`

1. **起手**：Context → 邊界 → Source 列檔 → 計畫 → 尚書省確認（若需要）  
2. **實作**：最小增量；`dict` 形狀穩定；遵守 Rule 3、8  
3. **驗收**：執行 runner／命令；蒐集可重跑證據  
4. **收尾**：Work Report 七節（見 §1.4）

### 1.4 Work Report 與 DoD `[DEFAULT]`

**Work Report 七節**（詳細格式見 `04_Workflows/CURSOR_AGENT_RULES.md`）：

| 節 | 內容 |
|----|------|
| §1 | 變更檔案（無改檔寫「無檔案變更」） |
| §2 | skeleton |
| §3 | placeholder |
| §4 | 驗證證據（命令／runner、關鍵結果） |
| §5 | 阻塞 |
| §6 | 下一步 |
| §7 | override 與留痕位置 |

**單次任務 DoD 自檢**：

- [ ] Context + Source 可追溯  
- [ ] 符合 Rule 3、8  
- [ ] 核心路徑回傳 `dict`  
- [ ] Work Report 已填  
- [ ] skeleton／placeholder 已分欄  
- [ ] 已驗證或已標阻塞  
- [ ] 四流派最低覆蓋已滿足  

### 1.5 核心路徑契約 `[DEFAULT]`

- 對外介面回傳穩定結構化 `dict`（慣用鍵：`ok`、`message` 或專案契約鍵）。  
- 禁止以自然語言 alone 代替機器可讀回傳。  
- 形狀詳見 `ENGINEERING_CONTRACT.md` 附錄 B 與 repo `core` 實作。

### 1.6 Fallback 與 Stop Work

| 情況 | 動作 | 標籤 |
|------|------|------|
| 依賴不存在 | skeleton 或 `ok: false` + message；寫 notes | `[DEFAULT]` |
| 他方 core 未就緒 | 不接管；notes 記介面需求 | `[SHOULD]` |
| 未授權碰硬禁區 | **立即停工**；回報禁區類型與票號 | `[NO-GO]` |
| DarkOps Blocked 且需改暗部根 | 停工；另開票 | `[NO-GO]` |
| 路徑與 `Master_Map.json` 衝突無授權 | 停工 | `[NO-GO]` |
| 未收到尚書省施工授權 | 不得開工 | `[NO-GO]` |

---

## §2 Forbidden Zones & Red Lines

> 禁區**類型**權威：`04_Workflows/HARNESS_CONSTITUTION.md` §7.1（**本節引用，不重定義**）  
> 具體路徑清單：`04_Workflows/INSTANCE_ANCHOR_TANG.md`（W5）

### 2.1 禁區類型表（引用母本）

| 類型 | 說明 | 典型範圍（抽象） |
|------|------|------------------|
| **Z-ENV** | 環境與密鑰 | `.env`、`.env.example`（除非單獨開票） |
| **Z-VENV-TREE** | 解釋器與套件樹 | 暗部 venv 的 `Scripts`／`Lib`／`Include`／`share` |
| **Z-RUNTIME-CP** | 執行態檢查點 | 暗部 `runtime/checkpoints/`（未授權不得改寫） |
| **Z-ORCH-DESTRUCT** | 編排破壞性腳本 | 特定 checkpoint／prune 模組與腳本 |
| **Z-DARK-OPS** | 暗部維運腳本 | `dark_ops` 下保留／清理類腳本 |
| **Z-HQ-LIQUIDATION** | 總部清算類 | `04_Workflows` 下清算／破壞測試腳本 |
| **Z-HQ-ENV-EDIT** | 全域禁止 | 擅自改根 `.env`、刪 `phase1_verify`、搬移既有目錄結構 |

### 2.2 違規後果 `[NO-GO]`

| 情況 | 後果 |
|------|------|
| 未授權觸及硬禁區 | **立即停工**；回報禁區類型與任務卡編號 |
| 尚書省 override 仍要求執行 | **先明示風險**（尤其 Z-ENV、Z-HQ-LIQUIDATION），再執行並留痕 |
| 路徑與 `Master_Map.json` 衝突且無授權 | 停工；要求更新地圖或改任務 |
| DarkOps Blocked 且任務需改暗部根 | 停工；要求開票解禁 |

### 2.3 AGENTS 戰車級紅線 `[NO-GO]`

（詳見 `AGENTS.md` §紅線；以下為 active 摘要）

| # | 規則 | 違反動作 |
|---|------|----------|
| R1 | **嚴禁**印出 `.env` 內容或任何金鑰原文 | 停工；驗證走 `_smoke_test_keys.py`，僅解讀 `[OK]`／`[FAILED]` |
| R2 | **嚴禁**程式中寫死磁碟路徑 | 改用 `gov_paths` 與 `Master_Map.json` |
| R3 | **嚴禁**同時起兩個 Telegram 監聽器 | 以 `04_Workflows/.telegram_listener.lock` 為準 |
| R4 | **嚴禁**在主艙 (`gov_main`) 安裝 crewai／langchain 等重套件 | 統包艙職責；見 `DEPARTMENT_MAP.md` |
| R5 | **嚴禁**新建 `hashes.txt` | 指紋只走 `04_Workflows/Chariot_Registry.db` |

### 2.4 DarkOps 預設 Blocked `[NO-GO]`

| 項 | 規則 |
|----|------|
| 制度 | **DarkOps-Worker** Phase 1 預設 **Blocked**；解禁須另開票 |
| 路由 | `python 04_Workflows/_route_task.py --type dark.infra` → 預期 `assignable: false` |
| 施工 | `assignable: false` 或 `blocked` 時 **不得**派工改暗部根；checklist 以 blocked 預期 **pass**（非假綠） |
| 驗證 | Wave 1 checklist 含 `darkops_route_gate`；見 `docs/GOVERNANCE_ONBOARDING_v1.md` Step 10 |

### 2.5 黑板與狀態檔寫入權 `[NO-GO]`

| 載體 | 規則 |
|------|------|
| `00_Agent_Work_Conditions.md` | 長期制度；**僅末尾追加**（禁覆蓋／刪除／重排） |
| `00_Agent_Work_Progress.md` | 短命迭代；**僅末尾追加** |
| `project_status/master_status.md` | 預設 **Governance 獨占寫入**；他方僅回報 |
| `project_status/handoff.md` | 同上 `[待確認]`：憲法提及但檔案可能不存在 |

### 2.6 跨模組邊界 `[NO-GO]`

- 不得修改**非本人** `core/*.py`、他人 department agent、他人 `agent_workspace/*` 三件套。  
- 跨模組需求寫 notes；**不接管**他人模組解阻塞。  
- 檔案歸屬母本：`00_Agent_Work_Conditions.md`；憲法 §9 為摘要。

### 2.7 實例路徑索引 `[DEFAULT]`

本檔正文**僅寫禁區類型**。下列實例資訊 **一律**查 W5：

- 硬禁區絕對路徑清單  
- venv 進入方式、cabin 路徑  
- DB 落點、env 鍵名、帳本檔名  

→ `04_Workflows/INSTANCE_ANCHOR_TANG.md`

---

## §3 Strong Defaults

### 3.1 接戰初始化（10 步摘要） `[DEFAULT]`

對齊 `AGENTS.md` §初始化校準；逐步細節見 `docs/GOVERNANCE_ONBOARDING_v1.md`。

| Step | 做什麼 | 讀／跑 |
|:----:|--------|--------|
| 1 | 憲法校準 | `HARNESS_CONSTITUTION.md` |
| 2 | 合約校準 | `ENGINEERING_CONTRACT.md` 或 `.cursor/rules/engineering-contract.mdc` |
| 3 | 條件校準 | `00_Agent_Work_Conditions.md` |
| 4 | 地圖校準 | `WORKFLOW_INDEX.md` |
| 5 | 路線校準 | `runbooks/GOV_CORE_OPERATING_MAP_v0.1.md` |
| 6 | 工作流校準 | 任務對應 runbook |
| 7 | 戰史校準 | `00_Agent_Work_Progress.md` 末段 |
| 8 | 任務路由 | `_route_task.py --type hq.governance` |
| 9 | 營運週期 | `OPS_CYCLE.md` |
| 10 | 一鍵自檢 | `_ops_cycle.py checklist --mode full` |

Multi-Chat 模式追加第 10 步：讀 `.cursor/rules/multi_chat_roles.mdc`。

### 3.2 路徑解析 `[DEFAULT]`

- 邏輯名、runners、cabins → `04_Workflows/Master_Map.json`  
- 程式解析 → `gov_paths`／暗部 `core/repo_paths.py` → `find_repo_root()`  
- **禁止**硬編磁碟絕對路徑（Rule 6）  
- W0 可移植 vs 實例分流 → `_PORTABLE_CORE_INDEX.md`

### 3.3 驗證與 runner `[DEFAULT]`

- 使用任務 FRAME／Master_Map 定義之 runner（邏輯名，非自創路徑）  
- 宣稱完成須附可重跑命令與關鍵 `ok` 語意  
- 糧草／金鑰：**僅** `[OK]`／`[FAILED]`，禁輸出 secret 原文  

### 3.4 OPS 一鍵自檢 `[DEFAULT]`

`python 04_Workflows/_ops_cycle.py checklist --mode full`

Wave 1 四檢（預期全 pass）：

| id | 檢查 |
|----|------|
| `smoke_keys` | 三鑰盲測 |
| `routing_policy_validate` | routing policy validate |
| `eval_gate_ci_subset` | eval-gate CI fixture 子集 |
| `darkops_route_gate` | DarkOps blocked 預期 pass |

Gate 分类 SSOT（mandatory / optional / shadow-only）：`docs/phase3-5-cost-model-governance-contract-v1.md` §2（WA-T3；**不改** 本節 checklist 定義）。

Schema 樣本：`artifacts/ops/checklist_full.sample.json`

### 3.5 Context Entry（H 線） `[DEFAULT]`

| 項 | 規則 |
|----|------|
| 入口 | 新 ask-like／LangGraph 長任務 **必須** `core/context_entry.py` → `build_rooted_context` |
| 禁止 | 入口手寫 `root_context`／`working_context`／`long_term_memory` 繞開 context 包 |
| 契約 | `context/context_entry_contract.md` |
| 示範 | `core/langgraph_flow_k1.py` 已對齊 |

### 3.6 Monitoring Graph `[DEFAULT]`

- **現況僅 L0**（observability-only）；`GOV_MONITORING_GRAPH_ENABLED` 預設 **0**  
- **禁止** L1 shadow selector／L2 SLO gate 參與 production 決策（未批文、未實作）  
- 詳見 `AGENTS.md` Monitoring Graph 節  

### 3.7 Repo path bootstrap `[DEFAULT]`

暗部 `app_api`／unittest：戰車根須在 `sys.path`；**單一權威** `core/repo_paths.py` → `ensure_repo_root_on_path()`。禁止第二套 parent-walk 邏輯。

### 3.8 Multi-Chat 四角色 `[DEFAULT]`

| 角色 | 可寫 | 禁止 |
|------|------|------|
| **Orchestrator** | FRAME、STATE | 程式碼；繞過 Reviewer 標 done |
| **Implementer** | B_REPORT + FRAME.AllowedPaths 內檔 | FRAME、STATE、C/D_REPORT；他人 core |
| **Reviewer** | C_REPORT | **任何** code/docs 實體修改 |
| **Scribe** | D_REPORT；Progress **末尾**追加 | core、tests、config；FRAME/STATE |

詳見 `.cursor/rules/multi_chat_roles.mdc` · `04_Workflows/tickets/README.md`

### 3.9 Cursor Subagents v0.1 `[DEFAULT]`

| 情境 | 做法 |
|------|------|
| 單檔／單模組、AllowedPaths 內 | researcher（可選）→ implementation-worker → checker-reviewer |
| 觸及 AGENTS、合約、`.cursor/rules`、暗部 core、跨多檔 | **必經** governance-guard |
| guard 回 `stop_work` / `allowed_worker=none` | **不得**派 worker |

詳見 `.cursor/agents/DISPATCH_GUIDE.md` · `AGENTS.md` Cursor Subagents 節

### 3.10 任務路由 `[DEFAULT]`

1. `python 04_Workflows/_route_task.py --type <task_type>` 或 `--text "..."`  
2. 讀 `assignable`、`blocked`、`worker`、`cabin`  
3. `assignable: false` → 停工或回報尚書省（**不假綠**）  

制度：`04_Workflows/TASK_ROUTING.md`

---

## §4 Wave & Ticket Operations (For Humans)

### 4.1 Wave 是什麼

| 項 | 說明 |
|----|------|
| **Wave** | 主題批次（如 Wave 1 治理+可觀測、Wave B Index/Eval）+ Execution Plan + 票隊列 |
| **不是** | 新的審批層級或自動開票系統 |
| **索引** | `docs/WAVE_*_EXECUTION_PLAN.md` · `_workflow_upgrade/90_run_queue.md` · Progress 末尾戰報 |

### 4.2 如何開新 Wave `[待確認]`

> **標記**：repo 內**無**單一正式「開 Wave SOP」；以下為近期**實際慣例**摘要，非新制度。

1. **尚書省裁決** Wave 主題、範圍與優先級  
2. **撰寫 Execution Plan**（例：`docs/WAVE_B_EXECUTION_PLAN.md`）— 票號、依賴、驗收命令  
3. **更新任務隊列** — `_workflow_upgrade/90_run_queue.md` 新增／結清條目  
4. **Progress 末尾追加** — 一句話宣告 Wave 起訖與阻塞  
5. **開票** — 依 §4.3 為 Wave 內各項建 `tickets/<id>_state.md`  

**不做**：本收斂票不新增正式 SOP 檔；缺口 follow-up 見 §6.4。

### 4.3 如何開新票 `[DEFAULT]`

1. Orchestrator 複製 `04_Workflows/tickets/_templates/ticket_state.template.md`  
2. 另存為 `04_Workflows/tickets/<ticket_id>_state.md`  
3. 填 **FRAME**：Goal、Scope、NonScope、AllowedPaths、BlockedPaths、AcceptanceCriteria、VerificationCommands  
4. 填 **STATE**：`overall_status: draft`、`current_owner: orchestrator`、`next_action`  
5. 依序執行：**B（Implementer）→ C（Reviewer）→ D（Scribe）→ O（Orchestrator 關票）**  
6. 各角色**直接讀寫**同一 state 檔對應 REPORT 區；**不**只在 chat 輸出代替寫檔  

範例：`04_Workflows/tickets/DEMO-1_state.md`

### 4.4 Multi-Chat 開 chat `[DEFAULT]`

1. Orchestrator 建 state + FRAME/STATE  
2. 每角色**新 chat**：貼 `_templates/<role>_instruction.template.md` + **同一 state 路徑**  
3. Implementer 只寫 B_REPORT；Reviewer 只寫 C_REPORT；Scribe 只寫 D_REPORT  
4. Orchestrator 讀 REPORT 更新 STATE → `overall_status: done`  

### 4.5 Dispatch / Control plane（可選） `[DEFAULT]`

- 計畫快照：`artifacts/control_plane/dispatch_plan.latest.md`  
- 執行說明：`docs/control_plane_dispatch_executor.md`  
- Cursor cards：`artifacts/control_plane/cards/`  
- **plan 不覆寫** ticket FRAME 的 AllowedPaths／BlockedPaths  

### 4.6 戰報與封存 `[DEFAULT]`

對齊 `AGENTS.md` §封存協議 + `04_Workflows/OPS_CYCLE.md`：

1. 保留 CLI 輸出與結構化 `ok` 結果  
2. 組裝戰報 JSON → `_ops_cycle.py validate-report`  
3. `append-report`（可先 `--dry-run`）  
4. Scribe／Implementer 將摘要 **append** 至 `00_Agent_Work_Progress.md` **末尾**  
5. 里程碑涉及 Gov Core → 確認 `project_status/master_status.md`（Governance 權限）

### 4.7 里程碑寫回 `[NO-GO]` / `[DEFAULT]`

| 項 | 規則 |
|----|------|
| `master_status.md` | 預設 Governance 獨占寫入 `[NO-GO]` 他方擅自改 |
| 里程碑編號 | 以 Progress 為準；worker **不自創**編號 |
| `handoff.md` | 同上；檔案存在性 `[待確認]` |

### 4.8 驗收鏈 `[DEFAULT]`

| 步驟 | 規則 |
|------|------|
| Implementer | **不自標** done；填 B_REPORT + verification |
| Reviewer | C_REPORT `conclusion` ∈ `{accepted, accepted_with_gaps, needs_changes, rejected}` |
| `needs_changes` | 回到 B；**不刪**歷史 REPORT |
| Orchestrator | 讀 B/C/D → 更新 STATE → `overall_status: done` |

---

## §5 For Agents: Read This First

### 5.1 接戰口令

| 口令 | 動作 |
|------|------|
| **接戰** | 執行 `AGENTS.md` §初始化校準（Multi-Chat 加第 10 步） |
| **封存** | 執行 `AGENTS.md` §封存協議 + OPS validate/append |

### 5.2 P0 必讀（每次有施工任務）

1. 尚書省**當次指令**／任務票 FRAME  
2. `04_Workflows/HARNESS_CONSTITUTION.md` — 禁區類型、四域  
3. `04_Workflows/ENGINEERING_CONTRACT.md` 或 `.cursor/rules/engineering-contract.mdc`  
4. **本檔** `docs/governance-constitution-v1.md` — §2 no-go、§3 defaults  
5. 若有票：`04_Workflows/tickets/<id>_state.md` FRAME（AllowedPaths／BlockedPaths 為硬邊界）

### 5.3 P1 按任務裁剪

| 任務類型 | 追加閱讀 |
|----------|----------|
| 首次接戰 | `docs/GOVERNANCE_ONBOARDING_v1.md` |
| 跑 CLI／runner | `04_Workflows/Master_Map.json` → `runners` |
| 工作流／smoke | `04_Workflows/WORKFLOW_INDEX.md` + 對應 runbook |
| 路由／派工 | `04_Workflows/TASK_ROUTING.md` |
| 上下文／ask H 線 | `context/context_entry_contract.md` + `AGENTS.md` §一致上下文入口 |
| Multi-Chat | `.cursor/rules/multi_chat_roles.mdc` |
| Subagents 派工 | `.cursor/agents/DISPATCH_GUIDE.md` |
| 分支／提交規範 | `docs/governance.md`（**非**本檔重複範圍） |

### 5.4 權威來源表（不必全 repo 掃）

| 優先 | 文件 | 一句職責 |
|:----:|------|----------|
| P0 | `AGENTS.md` | 接戰／封存、紅線、初始化 |
| P0 | `HARNESS_CONSTITUTION.md` | 憲法、禁區類型、Phase |
| P0 | `ENGINEERING_CONTRACT.md` | 四流派、12-rule、DoD |
| P0 | **本檔** | active snapshot：no-go + Wave/Ticket |
| P0 | `tickets/<id>_state.md` | 當次票邊界（有票時） |
| P1 | `Master_Map.json` | 路徑、runners、cabins |
| P1 | `GOVERNANCE_ONBOARDING_v1.md` | 接戰 10 步 |
| P1 | `context/context_entry_contract.md` | H 線上下文入口合同（**Agent 讀取上下文必對齊**） |
| P1 | `INSTANCE_ANCHOR_TANG.md` | 實例禁區路徑、venv、DB（類型細節） |
| P2 | `docs/governance.md` | 分支／提交／環境規範 |
| P2 | `docs/WAVE_*_EXECUTION_PLAN.md` | Wave 批次計畫 |
| P2 | `_workflow_upgrade/90_run_queue.md` | 任務隊列對賬 |

**專項治理（不升 P0 主表）**：K-2 prod 流量 → `docs/k2_deployment_governance.md`

### 5.5 Minimal Read Set by Task Type

> 下列為**最小必讀**；實際票 FRAME 可能追加 AllowedPaths 內檔案。

#### 一般 Implementer 票

| # | 必讀 |
|---|------|
| 1 | 本檔 §2、§3、§1.2–§1.4 |
| 2 | `tickets/<id>_state.md` — FRAME + STATE + AllowedPaths |
| 3 | `ENGINEERING_CONTRACT.md`（或 `.mdc`）— 四流派 + Rule 3/8/11 |
| 4 | 將改檔案之 `brief.md`／`notes.md`（若存在） |
| 5 | `Master_Map.json` — 僅任務相關 runners |

#### Reviewer 票

| # | 必讀 |
|---|------|
| 1 | 本檔 §2、§4.8、§1.4 |
| 2 | `tickets/<id>_state.md` — FRAME + B_REPORT + 變更檔 spot-check |
| 3 | `multi_chat_roles.mdc` §Reviewer — **唯讀不寫** code/docs |
| 4 | FRAME.VerificationCommands — 逐條對照 B_REPORT.verification |

#### Scribe 票

| # | 必讀 |
|---|------|
| 1 | 本檔 §4.6、§1.4 |
| 2 | `tickets/<id>_state.md` — B_REPORT + C_REPORT |
| 3 | `OPS_CYCLE.md` — 戰報欄位 |
| 4 | `00_Agent_Work_Progress.md` **末尾** — append 格式 |
| 5 | **禁止**改 core／tests／config；僅 D_REPORT + Progress 末尾 |

#### 治理票（觸及制度／憲法邊界／AGENTS）

| # | 必讀 |
|---|------|
| 1 | 本檔全文 + `HARNESS_CONSTITUTION.md` |
| 2 | `ENGINEERING_CONTRACT.md` + `HQ_PHASE1_FINALIZATION_ORDER.md` |
| 3 | `AGENTS.md` + `_PORTABLE_CORE_INDEX.md` |
| 4 | `.cursor/agents/DISPATCH_GUIDE.md` — **governance-guard** 必經 |
| 5 | 票 FRAME 明示 BlockedPaths（通常含憲法／合約／`.cursor/rules`） |

#### Orchestrator / Wave 票

| # | 必讀 |
|---|------|
| 1 | 本檔 §4 全節 + §5.4 |
| 2 | `tickets/README.md` + `_templates/orchestrator_instruction.template.md` |
| 3 | `multi_chat_roles.mdc` §Orchestrator |
| 4 | `_workflow_upgrade/90_run_queue.md` + 相關 `docs/WAVE_*_EXECUTION_PLAN.md` |
| 5 | `00_Agent_Work_Progress.md` 末段 + `artifacts/control_plane/dispatch_plan.latest.md`（若用 control plane） |
| 6 | `OPS_CYCLE.md` — 關票前 checklist／戰報制度 |

### 5.6 禁止行為速查（Top 10 `[NO-GO]`）

1. 輸出 `.env`／金鑰原文  
2. 硬編磁碟絕對路徑  
3. 未授權改憲法 §7 禁區類型對應資源  
4. DarkOps Blocked 時改暗部根  
5. 改他人 `core` 或他人 workspace 三件套  
6. 無 runner 證據宣稱完成  
7. 覆蓋／刪除 Progress／Conditions 既有段  
8. 擅自寫 `master_status`／`handoff`（非 Governance 授權）  
9. 雙 Telegram 監聽；主艙裝 crewai／langchain  
10. 新建 `hashes.txt`  

### 5.7 驗證命令索引 `[DEFAULT]`

| 用途 | 命令（HQ 戰車根相對） |
|------|----------------------|
| OPS 一鍵自檢 | `python 04_Workflows/_ops_cycle.py checklist --mode full` |
| 三鑰盲測 | `python 04_Workflows/_smoke_test_keys.py` |
| 任務路由 | `python 04_Workflows/_route_task.py --type <type>` |
| 路由策略 | `python -m core.routing_policy_loader validate` |
| 戰報驗證 | `python 04_Workflows/_ops_cycle.py validate-report --json <file>` |

完整 runner 索引 → `04_Workflows/Master_Map.json`

### 5.8 本檔 anchor 地圖

| 需求 | 段落 |
|------|------|
| no-go 清單 | §2 |
| 接戰／驗收預設 | §3 |
| 開票／封存 | §4 |
| Agent 必讀 | §5 |
| 待確認項 | §6 |

---

## §6 Legacy & Open Questions

### 6.1 `[LEGACY]` 文件

| 檔案 | 狀態 | 取代為 |
|------|------|--------|
| `04_Workflows/HARNESS_Constitution_v0.1.md` | SUPERSEDED | `HARNESS_CONSTITUTION.md` |
| `04_Workflows/ENGINEERING_CONTRACT_v0.1.md` | SUPERSEDED | `ENGINEERING_CONTRACT.md` |
| `workflow_v2/10_governance/**` | `[待確認]` | 與 HQ 三件套關係待裁決；**勿**默認為 P0 必讀 |

### 6.2 `[待確認]` 項

| # | 項 | 說明 |
|---|-----|------|
| Q1 | `project_status/handoff.md` | 憲法 §6.3 提及；repo 可能尚未建立 |
| Q2 | 開新 Wave 單一 SOP | 目前僅慣例（§4.2）；無正式檔 |
| Q3 | `workflow_v2/10_governance` vs HQ | 是否納入下一版 snapshot |
| Q4 | W1-T1 vs W1-T1B 票號 | W1-T1 = OPS 自检 done；W1-T1B = 本收敛票 |
| Q5 | `02_Agents_Core/ops_cycle.py` vs `_ops_cycle.py` | Wave1 檢查在 HQ `_ops_cycle.py`；schema 合併未做 |

### 6.3 票號歷史（避免混淆）

| 票號 | 標題 | 狀態 |
|------|------|------|
| W1-T1 | 治理入口收口 + OPS 一鍵自檢 | **done**（`W1-T1_state.md`） |
| W1-T1B | 治理合約與禁區規則收斂 | **in_progress**（本檔交付物） |

### 6.4 建議 follow-up（本票不實作）

- **W1-T1B-FOLLOWUP**：澄清 Q1–Q5  
- **governance-guard 票**：将本档链入 `@agent_requestable` rules 摘要  
- **handoff.md**：若 Governance 启用，补档并更新 §2.5  
- **Sources Index 自动化**：Tool Layer 后续  

---

## 附錄 A — 組織與四域（極簡）

> 詳表：`04_Workflows/DEPARTMENT_MAP.md` · 憲法 §3、§6、§9

### A.1 四域

| 域 | 代稱 | 職責摘要 |
|----|------|----------|
| **HQ** | 尚書省／治理層 | 全局規範、黑板、地圖、runner |
| **Dark** | Gov Core System | 暗部 `core`、Departments；與 HQ Tools venv **隔離** |
| **Chariot** | 六部執行態 | 環境、Agent 核心、RAG、工作流、出口 |
| **Tools** | HQ Tools | 工具／MCP 索引；**禁**向暗部 venv 裝 HQ 重套件 |

### A.2 HQ 協作輪（Phase 1 預設）

| 角色 | 預設 |
|------|------|
| HQ-Coordinator | 活躍 |
| HQ-Governance-Worker | 活躍 |
| HQ-Tooling-Worker | 活躍 |
| DarkOps-Worker | **Blocked** |
| QA-Reviewer | 活躍 |

---

## 附錄 B — Wave 索引（指針）

| 資源 | 路徑 |
|------|------|
| Wave A | `docs/WAVE_A_EXECUTION_PLAN.md` |
| Wave B · Observability | `docs/WAVE_B_EXECUTION_PLAN.md`（`WAVE-B-P*`） |
| Wave B · **Toolchain** | `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md`（`WB-T*`）· 快速入口 `docs/wave-b-toolchain-readme-v1.md` |
| Wave C | `docs/WAVE_C_EXECUTION_PLAN.md` |
| Phase% SSOT | `docs/WAVE_PROGRESS_DASHBOARD.md` |
| 任務隊列 | `_workflow_upgrade/90_run_queue.md` |
| 工作流入口 | `04_Workflows/WORKFLOW_INDEX.md` |
| 近期戰報 | `04_Workflows/00_Agent_Work_Progress.md` 末尾 |

---

*本檔為 W1-T1B 交付物 · active snapshot · 母本衝突以 `HARNESS_CONSTITUTION.md` / `ENGINEERING_CONTRACT.md` 為準*
