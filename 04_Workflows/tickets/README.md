# Multi-Chat Ticket State

輕量 handoff 機制：四角色 **直接讀寫同一份** `*_state.md`，人工只負責「開下一個 chat + 指定角色」，不再搬運 REPORT 區塊。

## 這是做什麼的

- **單一真相來源（SSOT）**：每張票一份 `04_Workflows/tickets/<ticket_id>_state.md`。
- **直接讀寫**：各角色 chat 用 Cursor 讀檔／改檔，只寫自己被允許的區塊。
- **handoff 摘要**：state 是交棒精簡版，不是完整工作日誌；詳細 reasoning 留在 chat。
- **純 markdown**：無 DB、無腳本、無 Web UI。

角色邊界詳見 `.cursor/rules/multi_chat_roles.mdc`；**Phase 4 contract SSOT** 見 `docs/phase4-multi-agent-collaboration-contract-v1.md`（routing、关口、STATE 写入冻结）。本目錄提供 state 格式與各角色 instruction 模板。

### Contract 与 ticket state 对齐

| 层级 | 路径 | 与 state 的关系 |
|------|------|-----------------|
| **Phase 4 contract** | `docs/phase4-multi-agent-collaboration-contract-v1.md` | **冻结** FRAME/STATE/B/C/D 写入权限（§5）；O→B→C→D 关口不可绕过 |
| **Machine rules** | `.cursor/rules/multi_chat_roles.mdc` | 各角色 FORBID/MUST；与 contract 冲突时 **machine rule 优先** |
| **State 模板** | `_templates/ticket_state.template.md` | FRAME/STATE/B_REPORT/C_REPORT/D_REPORT 区块结构；**不改模板结构** |
| **W5-T0 spec/runbook/replay** | `docs/multi-agent-*.md` | 操作层细节；文首 §0 指针指回 contract |

开 Multi-Chat 票时：Orchestrator 依 contract §4 routing 决策树判断是否需 governance-guard；Implementer **must_not** 改 FRAME/STATE；Reviewer **C_REPORT** 为关票前置；Scribe 收尾须 contract ↔ `multi_chat_roles.mdc` 双向 cross-ref。

## 標準流程（主流程）

### 基本順序（B → C → D → O）

```
需求討論（任意 chat）
    ↓
Orchestrator 建 state 檔 → 填 FRAME、初始化 STATE
    ↓
[Step B] Implementer 讀 state → 施工 → 直接回寫 B_REPORT
    ↓
[Step C] Reviewer 讀 state → 審查 → 直接回寫 C_REPORT
    ↓
[Step D] Scribe 讀 state → 整理 → 直接回寫 D_REPORT
    ↓
[Step O] Orchestrator 讀各 REPORT → 更新 STATE → 關票（overall_status: done）
```

### 可重跑情境（loop back）

| 情境 | C_REPORT 結論 | 下一步 | 說明 |
|------|--------------|--------|------|
| 一次通過 | `accepted` 或 `accepted_with_gaps` | B → C → D → O | 無阻擋問題，流程繼續至 Scribe |
| 需修改 | `needs_changes` | **回到 B** | Reviewer 列出修改項，Implementer 重跑 Step B（更新 B_REPORT），再進 C |
| 嚴重問題 | `rejected` | Orchestrator 介入 | 可能重開票或調整 FRAME，重新走 B → C → D → O |
| Scribe 發現 | （Scribe 不回傳結論，但可標註） | 回報 Orchestrator | 若 Scribe 發現實作問題，回報 O，O 決定是否退回 B |

*重跑 B/C/D 時，**不刪除**既有 REPORT，而是在原區塊追加或更新內容，保留歷史。*

### 人工要做的事（僅此）

| 步驟 | 人工 | Agent |
|------|------|-------|
| 開票 | 開 Orchestrator chat，貼 orchestrator 模板 + ticket_id | 建檔、填 FRAME/STATE |
| 施工 | 開 Implementer chat，貼 implementer 模板 + **state 路徑** | 讀 FRAME/STATE、施工、**寫 B_REPORT** |
| 審查 | 開 Reviewer chat，貼 reviewer 模板 + **state 路徑** | 讀 FRAME/STATE/B_REPORT、**寫 C_REPORT** |
| 文檔 | 開 Scribe chat，貼 scribe 模板 + **state 路徑** | 讀 B/C、**寫 D_REPORT** |
| 關票 | 開 Orchestrator chat（或原 chat 續跑） | 讀 REPORT、**更新 STATE**、標 done |

**不需要**：把 B_REPORT / C_REPORT / D_REPORT 從 chat 複製貼回 state 檔（除非 agent 無法寫檔時的備援，見下方）。

### 啟動下一張真實票（3 步）

1. **Orchestrator**：複製 `_templates/ticket_state.template.md` → `04_Workflows/tickets/<ticket_id>_state.md`；新 chat 貼 `_templates/orchestrator_instruction.template.md`，填 `ticket_id` 與本輪任務。
2. **Implementer / Reviewer / Scribe**：每棒新 chat 只貼對應 instruction 模板 + **同一 state 路徑** + 簡短本輪任務；agent 自行 Read／Write state。
3. **Orchestrator 收口**：讀 state 內 B/C/D_REPORT，更新 STATE（`current_owner`、`next_action`、`overall_status`）。

## 檔名慣例

```
04_Workflows/tickets/B-F3_state.md
04_Workflows/tickets/C1-P1_state.md
```

## 區塊與讀寫權限

| 區塊 | 維護者 | 讀 | 寫 |
|------|--------|----|----|
| FRAME | Orchestrator | 全角色 | 僅 Orchestrator |
| STATE | Orchestrator | 全角色 | 僅 Orchestrator |
| B_REPORT | Implementer | 全角色 | 僅 Implementer |
| C_REPORT | Reviewer | 全角色 | 僅 Reviewer |
| D_REPORT | Scribe | 全角色 | 僅 Scribe |

各角色 **必須直接更新 state 檔**，不可只在 chat 輸出 REPORT 全文代替寫檔。

## 角色 × 可改區塊對照表

| 角色 | 可寫區塊 | 可寫檔案類型（典型） | 禁止寫入 |
|------|----------|---------------------|----------|
| **Implementer (B)** | B_REPORT | FRAME.AllowedPaths 內檔案（如 `docs/*.md`、`skills/*`、`tests/test_*.py`、`.cursor/rules/*.mdc` 等，依票而定） | FRAME、STATE、C_REPORT、D_REPORT；`core/*`（非本人）、`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`04_Workflows/00_Agent_Work_Progress.md` |
| **Reviewer (C)** | C_REPORT | 唯讀不寫：可讀 FRAME、STATE、B_REPORT、變更檔案 spot-check，但**不改任何 code/docs** | 任何程式碼或文檔實體；FRAME、STATE、B_REPORT、D_REPORT；Progress、master_status |
| **Scribe (D)** | D_REPORT | `docs/*.md`（術語統一、交叉引用）、`04_Workflows/00_Agent_Work_Progress.md`（**僅末尾追加**） | 任何 `core/*`、`skills/*`、`tests/*`、`config/*`；FRAME、STATE、B_REPORT、C_REPORT；`.github/workflows/*` |
| **Orchestrator (O)** | FRAME、STATE | 新建/更新 `<ticket_id>_state.md`、制度計畫檔（流程改進） | 程式碼與測試（`core/*`、`skills/*`、`tests/*`）；B_REPORT、C_REPORT、D_REPORT 內容；`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`（僅 Governance 票） |

*詳細責任/禁區/與 CONTRACT 關係見 `.cursor/rules/multi_chat_roles.mdc` 各角色小節。*

## 備援：手動 copy/paste（次要）

僅在 agent **無法寫檔**（權限、離線、非 Agent 模式）時：

- 開 chat 時可手動貼該角色需讀的區塊（見舊版對照表）。
- 角色完成後，人工把 REPORT 貼回 state 對應區塊。

正常 Cursor Agent 施工應走「直接讀寫 state 檔」，不以此為主流程。

## 簡短範例（DEMO-1）

見 `DEMO-1_state.md`：示範多角色**依序直接回寫**同一份 state；B_REPORT 已填，STATE 展示交棒欄位。

## 注意事項

- state 是 **handoff 摘要**，不是完整日誌；跨角色交棒以 state 為準。
- 不要把既有真實票批量轉檔；從**下一張新票**開始用即可。
- Implementer 不自標 done；Reviewer 通過後由 Orchestrator 關票。
- 不取代 `AGENTS.md` 接戰／封存或 `ENGINEERING_CONTRACT.md` Work Report；Scribe 的 D_REPORT 可對齊 Progress 末尾格式。

## Wave B Toolchain 票務索引（WB-T*）

> **分轨**：`WB-T*` = Toolchain Wave B；`WAVE-B-P*` = Observability Wave B（`docs/WAVE_B_EXECUTION_PLAN.md`）；`W3-TL-*` = Tabular 实现层。

### state 路徑

| 票号 | state 路徑 | 狀態 |
|------|------------|------|
| WB-T1 | `04_Workflows/tickets/WB-T1-tool-catalog-and-selector-contract-v1_state.md` | done · accepted_with_gaps |
| WB-T2 | `04_Workflows/tickets/WB-T2-tool-executor-and-sandbox-safety-contract-v1_state.md` | done · accepted_with_gaps |
| WB-T3 | `04_Workflows/tickets/WB-T3-outbox-and-feedback-layer-contract-v1_state.md` | done · accepted_with_gaps |
| WB-T4 | `04_Workflows/tickets/WB-T4-agent-lines-ci-and-metrics-dashboard-v1_state.md` | done · accepted_with_gaps |
| WB-T5 | `04_Workflows/tickets/WB-T5-audit-quickview-and-case-history-spec-v1_state.md` | done · accepted_with_gaps |
| WB-T6 | `04_Workflows/tickets/WB-T6-wave-b-bottom-layer-readme-and-phase-progress-alignment-v1_state.md` | done · accepted_with_gaps |
| WB-T7 | `04_Workflows/tickets/WB-T7-phase6-toolchain-smoke-matrix-extension-v1_state.md` | done · accepted |
| WB-T8 | `04_Workflows/tickets/WB-T8-toolchain-wave-b-review-and-progress-closure-v1_state.md` | done · accepted_with_gaps（closure handoff） |

### Implementer 派工順序（建議）

```
WB-T1（catalog/selector contract）
  → WB-T2（executor/sandbox · 依赖 T1）
  → WB-T3（outbox/feedback · 依赖 T1+T2）
  → WB-T4（health dashboard · 可與 T1 部分並行）
  → WB-T5（audit quickview spec · 依赖 T3）
  → WB-T7（smoke matrix YAML · 依赖 T4 + WA-T6）
  → WB-T6（readme + Dashboard 收口 · 依赖 T1–T7 B_REPORT）
  → WB-T8（review-and-progress closure handoff · 依赖 T1–T7 C_REPORT）
```

**快速入口**：`docs/wave-b-toolchain-readme-v1.md` · **执行计划**：`docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` · **Phase% SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md`

---

## Wave C PRE 票務索引（WC-PRE-*）

> **定位**：Wave C 前置清理／impl gap 承接；**不阻塞** Wave C C1 契约层引用。doc-only 与 impl 票分轨；WC-PRE-06/07 需尚書省批文方可改 CI required / SLA。

| 票号 | state 路徑 | 狀態 | 摘要 |
|------|------------|------|------|
| WC-PRE-01 | `04_Workflows/tickets/WC-PRE-01-wave-b-doc-hygiene-and-closure-index-v1_state.md` | **accepted** | Wave B 文档/票务 hygiene · D_REPORT 补齐 · Dashboard/索引对齐 |
| WC-PRE-02 | `04_Workflows/tickets/WC-PRE-02-selector-plan-only-key-implementation-v1_state.md` | **accepted** | Selector 返回 dict 显式 `plan_only` 键（32/32 OK） |
| WC-PRE-03 | `04_Workflows/tickets/WC-PRE-03-executor-subprocess-timeout-implementation-v1_state.md` | **accepted** | Executor subprocess `timeout=600s` 实装（23/23 OK） |
| WC-PRE-04 | `04_Workflows/tickets/WC-PRE-04-audit-quickview-investigation-view-cli-v1_state.md` | **accepted_with_gaps** | Audit CLI 原生 investigation view 输出（20/20 OK；text formatter 待补） |
| WC-PRE-05 | `04_Workflows/tickets/WC-PRE-05-toolchain-smoke-matrix-runtime-runner-v1_state.md` | **accepted_with_gaps** | Runtime smoke runner 消费 smoke matrix YAML（19/19 OK；未接 CI） |
| WC-PRE-06 | `04_Workflows/tickets/WC-PRE-06-toolchain-observability-governance-upgrade-v1_state.md` | **design_ready · pending_approval** · **需批文** | P3.5 `OG-TOOLCHAIN-HEALTH` 等治理升级（设计稿：`docs/toolchain-observability-governance-upgrade-v1.md`） |
| WC-PRE-07 | `04_Workflows/tickets/WC-PRE-07-p6-toolchain-smoke-mandatory-ci-runner-v1_state.md` | **design_draft · blocked_on_approval** · **需批文** | P6 smoke mandatory CI runner（无批文不得改 PR required） |

**建议执行顺序**：C0/C1 优先 WC-PRE-01/02/05 → C1 期间 WC-PRE-03/04 → C1 之后 WC-PRE-06/07（批文后）。

---

## Wave C IMPL 票務索引（WC-IMPL-* · Lane B Phase 2）

> **定位**：WC-PRE-06/07 批文后的实施票；L1 = advisory / non-blocking；L2 = selective mandatory **草案/FRAME only**，未改 branch protection。

| 票号 | state 路径 | 状态 | 说明 |
|------|------------|------|------|
| WC-IMPL-L1 | `04_Workflows/tickets/WC-IMPL-L1_state.md` | **done** | snapshot advisory · MissingSignalRules v1 · artifact + log |
| WC-IMPL-SMOKE-CI-L1 | `04_Workflows/tickets/WC-IMPL-SMOKE-CI-L1_state.md` | **frame_ready · blocked_on_approval** | optional_ci smoke CI 接线 · CH-32～34 |
| WC-IMPL-L2 | `04_Workflows/tickets/WC-IMPL-L2_state.md` | **frame_frozen_pending_governance** | L2 hard assert 草案 · 设计稿 `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md` |

**Rollout SSOT**：`docs/governance/WC_PRE_06_07_rollout_plan.md` §3.6 · §8

---

## Wave C C1 票務索引（WC-C1-*）

> **定位**：Wave C Toolchain **C1 核心票**；developer-facing、**local only**、**optional** quickview；**非** PR required / CI gate。依賴 Wave B + WC-PRE-02～05；gate/CI 升格仍走 WC-PRE-06/07 或新票。

| 票号 | 标题 | Phase | 狀態 | owner | state 路徑 |
|------|------|-------|------|-------|------------|
| WC-C1-01 | toolchain-local-gaps-quickview-v1 | Wave C C1 | **accepted_with_gaps** | orchestrator | `04_Workflows/tickets/WC-C1-01-toolchain-local-gaps-quickview-v1_state.md` |

**快速入口**：`docs/toolchain-local-gaps-quickview-v1.md` · CLI：`scripts/run_toolchain_local_gaps_quickview.py`

---

## 最小接案 MVP Wave 4 票務索引（Lane A · W4-*）

> **定位**：轻量 case 记忆索引 + 真样本护栏升格；**≠** Tabular MVP Wave 4 routing glue。计划 SSOT：`docs/wave4-lane-a-execution-plan-v0.1.md`

| 票号 | state 路径 | 状态 | 说明 |
|------|------------|------|------|
| **W4-MEM-01** | `04_Workflows/tickets/W4-MEM-01_state.md` | **implementer done · Reviewer pending** | 只读 case 记忆 enriched 字段 · `docs/case-history-lookup-spec-v0.1.md` |
| **W4-GUARD-01** | `04_Workflows/tickets/W4-GUARD-01_state.md` | **design draft** | 护栏升格 **提案 only**；IMPL 待 `W4-GUARD-01-IMPL` + 尚書省裁定 T1–T3 |

**快速验证**

```bash
python scripts/build_cases_index.py --json
python scripts/lookup_case_history.py --client-ref sampleco --verbose
python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v
```

---

## Wave C Control Plane 票務索引（WC-T* · Lane C）

> **定位**：智能接单 / dispatch 指令卡 / comms / order intake / M3 契约；**optional · non-gating**；E2E ≠ INT Tier-A。总览：`docs/wave_c/overview.md`

| 票号 | state 路径 | 状态 | 说明 |
|------|------------|------|------|
| **WC-T1** | `docs/wave_c/WC_T1_eligibility.md` | **done** | `04_Workflows/ticket_eligibility.py` · `scripts/run_ticket_eligibility.py` |
| **WC-T1-INTEGRATION** | `04_Workflows/tickets/WC-T1-INTEGRATION_state.md` | **implementer done · Reviewer pending** | eligibility gate 接入 `_dispatch_cards.py` |
| **WC-T2** | `docs/wave_c/WC_T2_comms_minimal.md` | **done** | `04_Workflows/ticket_comms/*` · `scripts/run_ticket_state_update_with_comms.py` |
| **WC-T3** | `04_Workflows/tickets/W-next-DISPATCH-CARDS-MVP_state.md` | **done · accepted** | `04_Workflows/_dispatch_cards.py` · `scripts/run_dispatch_cards.py` |
| **WC-T4** | `docs/wave_c/WC_T4_order_ledger_design.md` | **done** | `scripts/run_order_intake.py` · order JSONL ledger |
| **WC-T5** | `04_Workflows/tickets/WC-T5_state.md` | **done · accepted** | `docs/wave_c/WC_T5_automation_coverage_contract.md` |
| **WC-T6** | `04_Workflows/tickets/WC-T6_state.md` | **done · accepted_with_gaps** | `scripts/distill_control_plane_skills_lite.py` |
| **WC-T7** | `04_Workflows/tickets/WC-T7_state.md` | **done · accepted_with_gaps** | `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` · `scripts/run_wc_m2_e2e_walkthrough.py` |
| **WC-SMOKE-M2-NIGHTLY** | `04_Workflows/tickets/WC-SMOKE-M2-NIGHTLY_state.md` | **done** | `scripts/run_wave_c_nightly_smoke.sh`（**optional** 本地晚间） |

**快速入口**：`docs/control_plane_dispatch_executor.md` · `docs/wave_c/overview.md` §M2 E2E

---

## 模板索引

| 檔案 | 用途 |
|------|------|
| `_templates/ticket_state.template.md` | 票 state 主模板 |
| `_templates/orchestrator_instruction.template.md` | Orchestrator — 讀整份、寫 FRAME/STATE |
| `_templates/implementer_instruction.template.md` | Implementer — 讀 FRAME/STATE、寫 B_REPORT |
| `_templates/reviewer_instruction.template.md` | Reviewer — 讀 FRAME/STATE/B_REPORT、寫 C_REPORT |
| `_templates/scribe_instruction.template.md` | Scribe — 讀 FRAME/STATE/B/C、寫 D_REPORT |

---

## 多 Lane 收口索引（2026-06-14）

> **SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md` §多 Lane 本輪收口（分票四欄表）· `docs/wave_c/overview.md` v0.3 · Progress 末尾 2026-06-14 条目。  
> **用语**：implemented · tested · reviewer pending · blocked_on_approval · accepted_with_gaps · optional / non-gating — 与各 `*_state.md` 一致，**禁止 overclaim** gate 升格或 mandatory CI。
