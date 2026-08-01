# [W1-T1B] 治理合約與禁區規則收斂

| 欄位 | 值 |
|------|-----|
| **票號** | W1-T1B |
| **標題** | 治理合約與禁區規則收斂 |
| **Wave** | Wave 1（治理 + 可觀測 + 測試底座） |
| **狀態** | `done`（Reviewer `accepted_with_gaps` · Scribe 收口 · 2026-06-10） |
| **SSOT 路徑** | 本檔 |
| **角色** | Implementer（主）／Reviewer（驗收）／Scribe（來源追溯）／Orchestrator（Wave／票流程對照） |

> **與 W1-T1 區隔**：`W1-T1`（`W1-T1_state.md`）=「治理入口收口 + OPS 一鍵自檢」，**done**（2026-06-07）。本票 **W1-T1B** 為獨立收斂票，勿混淆票號。

---

## Objective

整理並統一**目前實際生效**的工程合約、禁區規則與 Wave 運作方式，產出一份高可信度、可被 Agent 復用的治理「憲法」**收斂視圖**，減少規則分散與版本不一致。

**成功標準（一句話）**：Reviewer 只讀新文件即可理解現行治理與 Wave／Ticket 運作；後續 Agent 票可直接引用「For Agents: Read This First」，無需全 repo 掃描。

---

## Why now

1. **Wave 1 定位**：先把治理 + 可觀測 + 測試底座打穩，再推進多 Agent、Tool Layer 與自動接單。
2. **現狀痛點**：工程合約、禁區規則、Wave 流程分散在多個檔案與票據 state 中——已「可用」，但不方便 Agent 快速理解與遵守。
3. **不做此票的代價**：後續 Agent 票會重複問相同問題、重複掃上下文，增加 token 消耗與出錯機率。

---

## Scope

### In Scope

- 以**「目前實際在用的行為」**為準（非理想藍圖），收斂現有：
  - 工程合約（Engineering Contract）
  - 憲法／Harness 制度
  - 禁區規則（no-go）
  - Wave 1–N 運作慣例與近期票務流程
- 在新文件中**明確分類**：
  - **硬性禁止（no-go）** → 標 `[NO-GO]`
  - **強烈建議／預設約定** → 標 `[SHOULD]` / `[DEFAULT]`
- 撰寫簡明操作說明：**如何開新 Wave／如何開新票**（面向人類）。
- 撰寫 Agent 入口：**「For Agents: Read This First」**（指向權威段落與權威檔，避免全 repo 掃描）。

### Out of Scope

- 不設計新的治理流程或新增複雜審批制度。
- 不重構整個 repo 結構；僅在現有檔案基礎上整理與補充。
- 不一次性解決所有歷史遺留矛盾；衝突以「當前實際做法」為主，矛盾**另開票**處理。
- **不修改** `.cursor/rules`、不替換既有母本檔全文（本票產出為**收斂視圖**，非取代憲法原文）。
- **不合併** `docs/governance.md`（Phase 1 分支／提交規範）；與交付物**並列**，關係在 Document Meta 中說明。

---

## Inputs / Dependencies

> Implementer 接票後第一步：掃描下列路徑，產出「納入／引用／legacy／待確認」清單。**Step 1 已完成**（見本票 §Step 1 Inventory Summary）。

### P0 — 治理母本與執行層

| 占位 | 實際路徑 | 處置 |
|------|----------|------|
| HARNESS_CONSTITUTION | `04_Workflows/HARNESS_CONSTITUTION.md` | 引用 |
| ENGINEERING_CONTRACT | `04_Workflows/ENGINEERING_CONTRACT.md` | 引用 |
| CURSOR_RULES_EXEC | `.cursor/rules/engineering-contract.mdc` | 引用 |
| AGENTS_ENTRY | `AGENTS.md` | 纳入 |
| INSTANCE_ANCHOR | `04_Workflows/INSTANCE_ANCHOR_TANG.md` | 引用 |
| DEPARTMENT_MAP | `04_Workflows/DEPARTMENT_MAP.md` | 引用 |
| MASTER_MAP | `04_Workflows/Master_Map.json` | 引用 |

### P1 — 運作慣例與 Wave／票務

| 占位 | 實際路徑 | 處置 |
|------|----------|------|
| WORK_PROGRESS | `04_Workflows/00_Agent_Work_Progress.md` | 引用 |
| WORK_CONDITIONS | `04_Workflows/00_Agent_Work_Conditions.md` | 引用 |
| OPS_CYCLE | `04_Workflows/OPS_CYCLE.md` | 纳入 |
| TASK_ROUTING | `04_Workflows/TASK_ROUTING.md` | 纳入 |
| WORKFLOW_INDEX | `04_Workflows/WORKFLOW_INDEX.md` | 引用 |
| W0_PORTABLE_INDEX | `04_Workflows/_PORTABLE_CORE_INDEX.md` | 引用 |
| RUN_QUEUE | `_workflow_upgrade/90_run_queue.md` | 引用 |
| WAVE_B_PLAN | `docs/WAVE_B_EXECUTION_PLAN.md` | 引用 |
| WAVE_C_PLAN | `docs/WAVE_C_EXECUTION_PLAN.md` | 引用 |
| DISPATCH_GUIDE | `.cursor/agents/DISPATCH_GUIDE.md` | 纳入 |
| MULTI_CHAT_ROLES | `.cursor/rules/multi_chat_roles.mdc` | 纳入 |

### P2 — 票務 state／報告

| 占位 | 實際路徑 | 處置 |
|------|----------|------|
| TICKETS_DIR | `04_Workflows/tickets/` | 引用 |
| TICKETS_README | `04_Workflows/tickets/README.md` | 纳入 |
| B/C/D_REPORT | 各 `*_state.md` 內 REPORT 區 | 引用 |
| MASTER_STATUS | `04_Workflows/project_status/master_status.md` | 引用 |
| handoff | `project_status/handoff.md` | **TBD**（憲法提及但檔案不存在） |

### P3 — 可選補充

| 占位 | 實際路徑 | 處置 |
|------|----------|------|
| GOV_ONBOARDING | `docs/GOVERNANCE_ONBOARDING_v1.md` | 引用 |
| CONTROL_PLANE_DOC | `docs/control_plane_dispatch_executor.md` | 引用 |
| CONTEXT_ENTRY_CONTRACT | `context/context_entry_contract.md` | 引用 |
| K2_DEPLOYMENT | `docs/k2_deployment_governance.md` | 引用 |

### 依賴與阻塞

- **人類確認關卡**：Step 2 大綱確認後，Implementer 再撰寫 `docs/governance-constitution-v1.md`。
- **權威位階**（收斂時不得改寫，僅引用）：尚書省當次指令 ＞ 憲法 ＞ 合約／規則 ＞ brief／notes。

---

## Deliverables

### D1 — 單一權威 Markdown 文件（收斂視圖）

**路徑（已定）**：`docs/governance-constitution-v1.md`

**與 `docs/governance.md` 關係（並列，不合併）**：

| 檔案 | 定位 |
|------|------|
| `docs/governance.md` | Phase 1 **分支／提交／環境**規範 |
| `docs/governance-constitution-v1.md` | **當前**治理／合約／禁區／Wave 運作之 **active snapshot**（收斂視圖） |

**文件必含章節**：見本票 §Step 2 Outline（待人類確認後實作）。

### D2 — 票內來源追溯表

Implementer／Scribe 於本票末尾 **Sources Index** 維護。

### D3 — （可選）輕量入口指針

若尚書省同意，可在不改母本前提下新增指針（非必須；可能觸 governance-guard）：

- `AGENTS.md` 增一句指向 `docs/governance-constitution-v1.md`
- 或 `04_Workflows/tickets/README.md` 增連結

---

## Definition of Done

- [x] 存在 `docs/governance-constitution-v1.md`，路徑在戰報中明確記錄。
- [x] 文件含 **no-go** 與 **should/default** 兩類清晰分類。
- [x] 文件含 **「如何開新 Wave／新票」** 操作步驟。
- [x] 文件含 **「For Agents: Read This First」**（含 §5.5 Minimal Read Set by Task Type）。
- [x] 本票 **Sources Index** 列出納入的舊檔／state／報告。
- [x] Step 2 大綱已獲人類確認；Step 3 Draft 完成。
- [x] Reviewer 驗收通過（Acceptance Checks · `accepted_with_gaps`）。
- [x] Work Report 七節齊全（Implementer 自檢；見本票 Work Report）。

---

## Acceptance Checks

| # | 檢查項 | 驗證方式 | 通過標準 |
|---|--------|----------|----------|
| AC-1 | 單檔可讀性 | Reviewer **只讀** `docs/governance-constitution-v1.md` | 能說清 no-go、預設約定、Wave／Ticket 流程 |
| AC-2 | 人類可操作 | Scribe／Orchestrator 依 §Wave & Ticket 操作 | 與近期 Progress／票務實際一致 |
| AC-3 | Agent 可引用 | 新 Agent prompt 僅貼「For Agents」+ 本文件路徑 | 優先讀對權威檔，不全 repo 掃 |
| AC-4 | 分類清晰 | 抽查 ≥5 條 no-go、≥5 條 should | 每條有 `[NO-GO]` 或 `[SHOULD]`／`[DEFAULT]` |
| AC-5 | 來源可追溯 | 對照 Sources Index | 主要規則能對回至少一個輸入檔 |
| AC-6 | 未越 scope | diff 審查 | 無新審批流程、無 repo 大重構、未改母本 |

---

## Execution Plan

| Step | 名稱 | 狀態 | 說明 |
|------|------|------|------|
| 1 | Context & Inventory | **done** | 只读扫描；来源清单已确认 |
| 2 | Draft Outline | **done** | 2026-06-09 人类确认 |
| 3 | Human gate | **done** | 七章 + §5.5 追加已确认 |
| 4 | Draft | **done** | `docs/governance-constitution-v1.md` 已创建 |
| 5 | Self-check | **done** | DoD/AC 自查见本票 Work Report |
| 6 | Review | **done** | Reviewer AC-1～AC-6 全 pass · `accepted_with_gaps` |
| 7 | Close | **done** | Scribe C/D_REPORT + Progress 末尾战报 |

---

## Roles & Handoff

| 角色 | 責任 |
|------|------|
| **Implementer** | 扫描、大纲、撰写 D1、自检 DoD |
| **Reviewer** | AC-1～AC-6 |
| **Scribe** | D2 来源表；封存战报 |
| **Orchestrator** | AC-2 Wave／票流程对照 |

**Implementer 禁止**：未经确认重写母本；擅自改 `AGENTS.md`／宪法／`.cursor/rules`（除非票主明示扩 scope）。

---

## Notes for Cursor

1. **先列档，再方案，再改档**。
2. **保留现行规则优先**；不确定标 `[待確認]` 或 `[LEGACY]`。
3. **勿扩 scope**；缺口仅记「后续建议」。
4. **禁区与秘密**：正文仅写禁区**类型**；具体路径引用 `INSTANCE_ANCHOR_TANG.md`。
5. **权威位阶**：本交付物是**收敛视图**；与母本冲突时以母本为准，并标注差异。

---

## Step 1 Inventory Summary（2026-06-09 · 已确认）

- P0 母本 7 项 + legacy v0.1 2 项 + 补充 3 项 → 见 chat / 本票 Inputs 表。
- **待確認保留项**：`project_status/handoff.md` 不存在；`workflow_v2/10_governance/**` 与 HQ 三件套关系；`docs/governance.md` 边界已在 Document Meta 裁決为并列。

---

## Step 2 Outline（**confirmed** · 2026-06-09）

§0–§6 + 附录 A/B；§5.5 Minimal Read Set by Task Type 已追加。交付物：`docs/governance-constitution-v1.md`。

---

## 後續建議（本票不實作）

- 将 `docs/governance-constitution-v1.md` 链入 Cursor rules `@agent_requestable`（需 governance-guard 票）。
- 对 `[待確認]` 项开 **W1-T1B-FOLLOWUP** 澄清票。
- Sources Index 自动化（Tool Layer，Wave 1 后续）。

---

## Sources Index（Implementer · 2026-06-09）

| # | 來源 | 納入章節 | 處置 |
|---|------|----------|------|
| 1 | `04_Workflows/HARNESS_CONSTITUTION.md` | §2, 附錄 A | 引用 |
| 2 | `04_Workflows/ENGINEERING_CONTRACT.md` | §1 | 引用摘要 |
| 3 | `.cursor/rules/engineering-contract.mdc` | §1 | 引用 |
| 4 | `AGENTS.md` | §2, §3, §5 | 纳入摘要 |
| 5 | `04_Workflows/INSTANCE_ANCHOR_TANG.md` | §2.7 | 引用 |
| 6 | `04_Workflows/DEPARTMENT_MAP.md` | 附錄 A | 引用 |
| 7 | `04_Workflows/Master_Map.json` | §3.2, §5.7 | 引用 |
| 8 | `04_Workflows/_PORTABLE_CORE_INDEX.md` | §0.2, §3.2 | 引用 |
| 9 | `04_Workflows/project_status/HQ_PHASE1_FINALIZATION_ORDER.md` | §0.2, §6.1 | 引用 |
| 10 | `04_Workflows/00_Agent_Work_Conditions.md` | §2.6 | 引用摘要 |
| 11 | `04_Workflows/00_Agent_Work_Progress.md` | §4.1, 附錄 B | 引用 |
| 12 | `04_Workflows/OPS_CYCLE.md` | §4.6, §5.5 Scribe | 纳入 |
| 13 | `04_Workflows/TASK_ROUTING.md` | §3.10 | 纳入 |
| 14 | `04_Workflows/WORKFLOW_INDEX.md` | §5.3, 附錄 B | 引用 |
| 15 | `04_Workflows/CURSOR_AGENT_RULES.md` | §1.4 | 引用 |
| 16 | `04_Workflows/tickets/README.md` | §4.3–§4.4, §5.5 | 纳入 |
| 17 | `04_Workflows/tickets/_templates/*` | §4.3 | 引用 |
| 18 | `04_Workflows/tickets/DEMO-1_state.md` | §4.3 | 引用 |
| 19 | `04_Workflows/tickets/W1-T1_state.md` | §6.3 | 引用（票号对照） |
| 20 | `.cursor/rules/multi_chat_roles.mdc` | §3.8, §5.5 | 纳入 |
| 21 | `.cursor/agents/DISPATCH_GUIDE.md` | §3.9, §5.5 治理票 | 纳入 |
| 22 | `docs/GOVERNANCE_ONBOARDING_v1.md` | §3.1, §5 | 引用 |
| 23 | `docs/governance.md` | §0.2 | 并列引用 |
| 24 | `context/context_entry_contract.md` | §3.5, §5.4, §5.5 | 引用 |
| 25 | `docs/WAVE_A/B/C_EXECUTION_PLAN.md` | §4.1, 附錄 B | 引用 |
| 26 | `_workflow_upgrade/90_run_queue.md` | §4.1–§4.2, 附錄 B | 引用 |
| 27 | `docs/control_plane_dispatch_executor.md` | §4.5 | 引用 |
| 28 | `docs/k2_deployment_governance.md` | §5.4 专项 | 引用（不升主表） |
| 29 | `HARNESS_Constitution_v0.1.md` | §6.1 | legacy |
| 30 | `ENGINEERING_CONTRACT_v0.1.md` | §6.1 | legacy |

---

## B_REPORT（Implementer · Step 3–4 自檢）

| 節 | 內容 |
|----|------|
| §1 變更檔案 | **新增** `docs/governance-constitution-v1.md`；**新增** `04_Workflows/tickets/W1-T1B_governance_consolidation.md`（SSOT）。**未改**母本、AGENTS、`.cursor/rules` |
| §2 skeleton | 無 |
| §3 placeholder | §6.2 Q1–Q5 待確認项；§4.2 开 Wave 惯例标记 `[待確認]` |
| §4 驗證證據 | DoD 7/8 自检 pass（除 Reviewer 项）；AC-1–AC-5 Implementer 自查 pass；AC-6 diff 仅 2 新档 |
| §5 阻塞 | 無（Reviewer 驗收前為 pending；已收口） |
| §6 下一步 | Scribe 填 C/D_REPORT + Progress 末尾；Q1–Q5／D3 指针留 follow-up 票 |
| §7 override | 无 |

---

## C_REPORT（Reviewer · AC 驗收）

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
    - **deliverable**: 新增 `docs/governance-constitution-v1.md`（v1.0-active 收斂視圖），整合 `[NO-GO]`／`[SHOULD]`／`[DEFAULT]` 分類、Wave／Ticket 人類操作（§4）、Agent 必讀與 §5.5 Minimal Read Set by Task Type；**未改** `HARNESS_CONSTITUTION.md`／`ENGINEERING_CONTRACT.md`／`.cursor/rules/*`／`AGENTS.md` 母本。
    - **AC-1～AC-6**: 全數通過 — Reviewer 僅讀新文件即可說清 no-go、預設約定、Wave／Ticket 流程；Sources Index 列 **30** 條來源可追溯；diff 審查確認無新審批流程、無 repo 大重構、未替換母本。
    - **boundary**: 符合 Out of Scope — 收斂視圖並列於 `docs/governance.md`，非取代憲法／合約原文。
    - **honesty**: §6.2 Q1–Q5 與 §4.2 開 Wave 慣例均誠實標 `[待確認]`，未冒充定稿。
- risk_level: low
- gaps（非阻塞）:
    - §3.1 接戰步驟編號與 `AGENTS.md` §初始化校準略有偏差（語意對齊、編號不一致）。
    - §4.2「如何開新 Wave」為慣例摘要並標 `[待確認]`，尚書省／Orchestrator 裁決口徑待 follow-up 票澄清。
    - §6.2 Q1–Q5 待確認項（含 `handoff.md` 缺席、`workflow_v2/10_governance/**` 與 HQ 三件套關係等）留 **W1-T1B-FOLLOWUP** 或等價票。
- suggestions:
    - 後續票可選 D3：於 `AGENTS.md` 或 `tickets/README.md` 增輕量指針（需 governance-guard 批文；本票刻意不做）。
    - 將 `[待確認]` 項逐條關閉後，可考慮 `@agent_requestable` 鏈入 Cursor rules（見本票「後續建議」）。

---

## D_REPORT（Scribe · 收口）

- docs_updates:
    - **active snapshot 就緒**：`docs/governance-constitution-v1.md` 為 Wave 1 治理／合約／禁區／票務運作之可引用收斂視圖；與 `docs/governance.md`（Phase 1 分支／提交規範）**並列**，關係見新文件 Document Meta。
    - **Agent 接戰捷徑**：新票 prompt 可僅貼「For Agents: Read This First」+ 本文件路徑 + 當次票 FRAME；優先讀 §5 與 §5.5 Minimal Read Set，免全 repo 掃描。
    - **本輪刻意不做**：未改 `AGENTS.md`／`tickets/README.md` 指針（D3 留 follow-up）；未動母本與 `.cursor/rules`。
- progress_entry: |
    W1-T1B（治理合約收斂）：`docs/governance-constitution-v1.md` active snapshot 就緒 — Agent 接戰可優先讀 §5 + 當次票 FRAME，免全 repo 掃描；母本未替換。Reviewer `accepted_with_gaps`，Q1–Q5 待確認項留後續票。
- followup_suggestions:
    - **W1-T1B-FOLLOWUP**：澄清 §3.1 步驟編號、§4.2 開 Wave 裁決口徑、§6.2 Q1–Q5。
    - **可選 D3 票**：`AGENTS.md` 或 `tickets/README.md` 增一句指向收斂視圖（需 governance-guard）。
    - Sources Index 自動化仍留 Tool Layer（Wave 1 後續）。

---

*票版本：W1-T1B · SSOT：`04_Workflows/tickets/W1-T1B_governance_consolidation.md`*
