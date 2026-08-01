# TICKET STATE · DEMO-1 · 建立 ticket state 基礎設施（示範票）

> **示範用途**：虛構票，展示「多角色直接讀寫同一份 state 檔」模式。  
> 各角色用 Cursor Read 開本檔，只改自己被允許的區塊；**不需**人工把 chat 輸出貼回本檔。

---

## FRAME

- Goal: 建立 Multi-Chat ticket state 模板與使用說明，並升級為角色直接讀寫 state 檔的操作方式。
- Scope:
  - `ticket_state.template.md` 與四角色 instruction 模板
  - `README.md` 說明直接讀寫流程
  - 本 DEMO 檔展示 B_REPORT 已填與 STATE 交棒欄位
- NonScope:
  - 不引入 DB / 腳本 / CI / Web UI
  - 不轉換既有真實票
  - 不改 core、skills、AGENTS.md
- AllowedPaths:
  - `04_Workflows/tickets/**`
- BlockedPaths:
  - `core/*`、`skills/*`、`.cursor/rules/*`、`AGENTS.md`
- Dependencies: 無
- AcceptanceCriteria:
  - 四 instruction 模板明確：讀哪些區塊、寫哪些區塊、必須直接更新 state 檔
  - README 主流程為直接讀寫；手動 copy/paste 僅列備援
  - DEMO 展示 B_REPORT 與 STATE 交棒語意

---

## STATE

- overall_status: done
- current_owner: scribe
- next_action: 無（示範票已收口；可作 multi-role template 參考）
- last_updated: 2026-06-07 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

> **交棒說明（示範）**：Implementer 施工後**直接改寫**下方 B_REPORT；`current_owner` / `next_action` / `status_by_role.implementer` 由 Orchestrator 在下一棒讀 B_REPORT 後更新（本 DEMO 預填為「待 Reviewer」狀態）。

---

## B_REPORT

<!-- 由 Implementer 直接寫入本區塊；以下為示範已填內容 -->

- changed_files:
  - `04_Workflows/tickets/_templates/orchestrator_instruction.template.md`
  - `04_Workflows/tickets/_templates/implementer_instruction.template.md`
  - `04_Workflows/tickets/_templates/reviewer_instruction.template.md`
  - `04_Workflows/tickets/_templates/scribe_instruction.template.md`
  - `04_Workflows/tickets/README.md`
  - `04_Workflows/tickets/DEMO-1_state.md`
- artifacts: 四角色 instruction（直接讀寫模式）、README 主流程、本 DEMO
- verification: 人工檢查 — 各模板含「先 Read state → 只寫允許區塊 → 直接更新檔案」；README 含 3 步開票與人工/agent 分工表
- behavior_notes: 主流程不再要求使用者複製 REPORT 區塊；copy/paste 降為備援
- deferred_items: 無

---

## C_REPORT

- verdict: accepted
- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    - **AC-1**：四 instruction 模板均含「先 Read state → 只寫允許區塊 → 直接更新檔案」語意 — 滿足。
    - **AC-2**：README 主流程為直接讀寫；copy/paste 降為備援 — 滿足。
    - **AC-3**：DEMO 展示 B_REPORT 已填與 STATE 交棒語意 — 滿足。
    - **輕微 gap（非阻塞）**：B_REPORT `changed_files` 未列 `ticket_state.template.md`（模板檔存在但未列入 changed_files）。
- risk_level: low
- suggestions: |
    - Scribe 補 D_REPORT，並在 Progress 註記 DEMO-1 作為 multi-role template 的示範票。
    - 可選：Implementer follow-up 將 `ticket_state.template.md` 補入 changed_files（非阻塞）。

---

## D_REPORT

- docs_updates:
  - `04_Workflows/tickets/_templates/orchestrator_instruction.template.md`
  - `04_Workflows/tickets/_templates/implementer_instruction.template.md`
  - `04_Workflows/tickets/_templates/reviewer_instruction.template.md`
  - `04_Workflows/tickets/_templates/scribe_instruction.template.md`
  - `04_Workflows/tickets/README.md` — 主流程為直接讀寫 state；copy/paste 降為備援
  - `04_Workflows/tickets/DEMO-1_state.md` — 本示範票（FRAME / STATE / B_REPORT / C_REPORT / D_REPORT 完整範例）
- verification:
  - 人工檢查（Reviewer）：四 instruction 模板均含「先 Read state → 只寫允許區塊 → 直接更新檔案」→ **通過**
  - README 主流程為直接讀寫；3 步開票與人工/agent 分工表 → **通過**
  - DEMO 展示 B_REPORT 已填與 STATE 交棒語意 → **通過**
- behavior_notes:
  - 主流程**不再**要求使用者複製 REPORT 區塊回 state；各角色用 Cursor Read 開票檔、只改允許區塊
  - B_REPORT `changed_files` 未列 `ticket_state.template.md`（檔案存在）— Reviewer 列為**輕微 gap，非阻塞**
  - 示範票**不**引入 DB／腳本／CI／Web UI；既有真實票不轉換
- progress_entry: |
    DEMO-1 收口：Multi-Chat ticket state 基礎設施就緒 — 四角色 instruction 模板 + `tickets/README.md` 直接讀寫流程 + 本 DEMO 票作完整 state 範例。後續真實票可依 `ticket_state.template.md` 開票，各角色只寫 FRAME／STATE／B／C／D 對應區塊。
- followup_suggestions:
  - **可選 hygiene**：將 `ticket_state.template.md` 補入 B_REPORT `changed_files`（非阻塞）
  - **實戰票**：Orchestrator 開票時複製 DEMO 模式；Scribe 輪依本票 D_REPORT 格式填 verification／behavior_notes／followup_suggestions
