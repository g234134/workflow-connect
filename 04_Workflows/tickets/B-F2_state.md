# TICKET STATE · B-F2 · Agent Roles / Engineering Contract 明文化

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME
<!-- Orchestrator 填：票的邊界與驗收標準；開票時寫，施工前凍結 -->

- Goal:
  - 將 Multi-Chat 四角色（Orchestrator/Implementer/Reviewer/Scribe）的實戰經驗（C1-P1、B-F1）抽成正式規則文件，完成 `multi_chat_roles.mdc` 四角色章節、更新 `tickets/README.md` 與模板、補 AGENTS.md 引用。
- Scope:
  - 更新 `.cursor/rules/multi_chat_roles.mdc`：為四角色各增加 responsibilities / forbidden actions / allowed_paths 類型描述 / blocked_paths 類型 / 與 ENGINEERING_CONTRACT 關係。
  - 更新 `04_Workflows/tickets/README.md`：補「角色×可改區塊」表格、Multi-Chat 流程順序（B→C→D→O）、可重跑情境（need_changes）。
  - 檢查並更新 `tickets/_templates/*.template.md`：確保四角色模板都引用 `multi_chat_roles.mdc` 與 `ENGINEERING_CONTRACT`。
  - 更新 `AGENTS.md` 第10步：補上「多 chat 角色定義詳見 `multi_chat_roles.mdc`」引用。
- NonScope:
  - 不改 `ENGINEERING_CONTRACT.md`、`HARNESS_CONSTITUTION.md` 正文（僅引用）。
  - 不改 `core/*`、`skills/*`、`config/*`、`observability/*`。
  - 不改 `00_Agent_Work_Progress.md`（Scribe 工作）。
  - 不改其他票 state（C1-P1、B-F1 等保留原樣）。
- AllowedPaths:
  - `.cursor/rules/multi_chat_roles.mdc`
  - `04_Workflows/tickets/README.md`
  - `04_Workflows/tickets/_templates/orchestrator_instruction.template.md`
  - `04_Workflows/tickets/_templates/implementer_instruction.template.md`
  - `04_Workflows/tickets/_templates/reviewer_instruction.template.md`
  - `04_Workflows/tickets/_templates/scribe_instruction.template.md`
  - `AGENTS.md`（僅第10步段落）
  - `04_Workflows/tickets/B-F2_state.md` 的 B_REPORT 區塊
- BlockedPaths:
  - `ENGINEERING_CONTRACT.md`、`HARNESS_CONSTITUTION.md` 正文
  - `core/*`、`skills/*`、`config/*`、`observability/*`
  - `00_Agent_Work_Progress.md`
  - 其他票 state 檔（C1-P1、B-F1 等）
- Dependencies:
  - 參考 C1-P1、B-F1 的實際操作模式（作為成功樣板）。
- AcceptanceCriteria:
  - `multi_chat_roles.mdc` 四角色小節均含：responsibilities、forbidden actions、allowed_paths 類型描述、blocked_paths 類型、與 CONTRACT 關係說明。
  - `tickets/README.md` 含角色×可改區塊表格、流程順序 B→C→D→O、可重跑情境說明。
  - 四個 template.md 均引用 `multi_chat_roles.mdc` 與 `ENGINEERING_CONTRACT`。
  - `AGENTS.md` 第10步補充對 `multi_chat_roles.mdc` 詳細章節的引用。
  - Reviewer 判定 conclusion ∈ {accepted, accepted_with_gaps}。

---

## STATE
<!-- Orchestrator 維護：當前進度與下一棒；每次角色交棒後更新 -->

- overall_status: accepted_with_gaps
- current_owner: orchestrator
- next_action: closed
- last_updated: 2026-06-07 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT
<!-- Implementer 填：施工結果；只寫本區塊，不改 FRAME / STATE -->

- changed_files:
  - `.cursor/rules/multi_chat_roles.mdc`
  - `04_Workflows/tickets/README.md`
  - `04_Workflows/tickets/_templates/orchestrator_instruction.template.md`
  - `04_Workflows/tickets/_templates/implementer_instruction.template.md`
  - `04_Workflows/tickets/_templates/reviewer_instruction.template.md`
  - `04_Workflows/tickets/_templates/scribe_instruction.template.md`
  - `AGENTS.md`
- artifacts:
  - Multi-Chat 四角色正式規則文件（含責任/禁區/路徑邊界/合約關係）
  - tickets/README.md 角色×可改區塊對照表與流程順序說明
  - 四個角色指令模板（引用 multi_chat_roles.mdc 與 CONTRACT）
- verification:
  - cross-check: `multi_chat_roles.mdc` 四角色小節結構完整
    - Orchestrator: 含 allowed_paths（FRAME/STATE/制度計畫檔）、blocked_paths（程式碼/核心制度/他人 REPORT）
    - Implementer: 含 allowed_paths（FRAME.AllowedPaths/B_REPORT/本人 workspace）、blocked_paths（他人 core/憲法/全局狀態/其他 REPORT）
    - Reviewer: 含 allowed_paths（C_REPORT/唯讀）、blocked_paths（任何程式碼或文檔實體）
    - Scribe: 含 allowed_paths（D_REPORT/Progress 末尾追加/docs 整理）、blocked_paths（程式碼/FRAME/其他 REPORT）
  - cross-check: `tickets/README.md` 表格與 C1-P1/B-F1 實際操作一致
    - Implementer 僅寫 B_REPORT（與 C1-P1、B-F1 的 B_REPORT 實際由 Implementer 填寫一致）
    - Reviewer 僅寫 C_REPORT（與 C1-P1、B-F1 的 C_REPORT 實際由 Reviewer 填寫一致）
    - Scribe 僅寫 D_REPORT（與 C1-P1、B-F1 的 D_REPORT 實際由 Scribe 填寫一致）
    - Orchestrator 寫 FRAME/STATE（與既有流程一致）
- behavior_notes:
  - 本次為「明文化既有實務」，所有邊界與禁區均對齊 C1-P1/B-F1 實際操作，無放寬核心禁區。
  - `multi_chat_roles.mdc` 明確標註「上位規則：ENGINEERING_CONTRACT.md 與 HARNESS_CONSTITUTION.md 為憲法級上位文件」，衝突時向上裁決。
  - 四角色均明確標註與 CONTRACT Rule 3/6/8/11 的對應關係。
- deferred_items:
  - 若發現需改動 `ENGINEERING_CONTRACT.md` 或 `HARNESS_CONSTITUTION.md` 正文，需另開 governance 票，不在本票範圍。
  - tickets/README.md 中「模板索引」表格連結待 B-F3 或後續票完善（非本票阻擋）。

---

## C_REPORT
<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: accepted_with_gaps
- blocking_issues:
  - 無
- checks_summary:
  - boundary: "B_REPORT `changed_files` 與 FRAME.AllowedPaths 一致（`multi_chat_roles.mdc`、`tickets/README.md`、四份 `_templates/*.template.md`、`AGENTS.md`）；獨立 `git diff AGENTS.md` 僅新增第 10 步與收尾句（單 chat 九步／Multi-Chat 十步），未觸及 BlockedPaths（`ENGINEERING_CONTRACT.md`／`HARNESS_CONSTITUTION.md` 正文、`core/*`、`skills/*`、`config/*`、`observability/*`、`00_Agent_Work_Progress.md`）。Reviewer 本次僅寫 C_REPORT，符合角色邊界。"
  - alignment: "四角色小節均含 responsibilities／forbidden actions／allowed_paths／blocked_paths／與 CONTRACT 關係；`tickets/README.md` 具區塊讀寫表、角色×可改區塊表、B→C→D→O 主流程與 `needs_changes` 回 B 迴圈；四份 instruction 模板均引用 `multi_chat_roles.mdc` 與 `ENGINEERING_CONTRACT.md`。與 C1-P1／B-F1 實際操作一致：Implementer 僅 B_REPORT、Reviewer 僅 C_REPORT、Scribe 僅 D_REPORT、Orchestrator 僅 FRAME/STATE。"
  - honesty: "未暗示 Reviewer 可改 code 或 Scribe 可寫 FRAME/STATE/B/C_REPORT；`tickets/README.md` §「人工要做的事」明列開 chat＋貼模板，非全自動。B_REPORT `verification` 為結構自檢、無 runner 輸出——文書票可接受，但證據強度偏弱（見 suggestions）。"
  - docs: "`multi_chat_roles.mdc` 權威位階、上位裁決與 B_REPORT `deferred_items` 均明示改 `ENGINEERING_CONTRACT`／`HARNESS_CONSTITUTION` 正文需另開 governance 票；`AGENTS.md` 第 10 步已指向 `multi_chat_roles.mdc` 各 `§<role>`。輕微矛盾：`§Implementer` Blocked Paths 括註「除非明示授權如 B-F2」易誤讀為本票可改合約正文，與 FRAME.NonScope 及同檔 Orchestrator／Scribe 小節衝突；Orchestrator 對 Progress「Scribe 建議、O 確認後追加」與 Scribe「可直接末尾追加」／`AGENTS.md` §封存協議略不一致。"
- risk_level: low
- suggestions:
  - 修正 `multi_chat_roles.mdc` §Implementer Blocked Paths：`ENGINEERING_CONTRACT.md`／`HARNESS_CONSTITUTION.md` 括註改為「僅尚書省或 Governance 票可動」，勿以 B-F2 為反例（B-F2 授權的是 `.cursor/rules` 與 `AGENTS.md` 第 10 步，非合約正文）。
  - 統一 Progress 追加流程敘事：建議 Orchestrator 小節改為「Scribe 依 `AGENTS.md` §封存協議末尾追加；Orchestrator 收口確認」，與 Scribe／README 對齊。
  - B-F3 或輕修票：補 `tickets/README.md` 模板索引表格可點連結（B_REPORT 已列 deferred，非阻擋）。
  - 高風險路徑（`ENGINEERING_CONTRACT`、`.cursor/rules` 全域、暗部 `core`）施工前，Orchestrator 應在 FRAME 明示是否需 `governance-guard`／專職 Reviewer spot-check；可於 `multi_chat_roles.mdc`「標準流水線」後加一句提醒（選做）。
  - Orchestrator 更新 STATE（`current_owner: scribe`、`next_action`、Reviewer `done`）；Implementer 未在 B_REPORT 附獨立 diff 清單以外的 spot-check 證據，後續文書票可要求列「已讀檔路徑」或關鍵段落錨點。

---

## D_REPORT
<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- docs_updates:
  - **`.cursor/rules/multi_chat_roles.mdc`（四角色明文化）**
    - **Orchestrator (A)**：排票／凍結 scope／指派 chat；唯寫 FRAME+STATE 與制度計畫檔；禁碰程式碼、核心制度正文、他人 B/C/D_REPORT；Progress 僅「Scribe 建議、O 確認後末尾追加」；上位裁決指向 CONTRACT §5。
    - **Implementer (B-*)**：依 FRAME.AllowedPaths 施工＋填 B_REPORT；禁越權改憲法／合約／`.cursor/rules`（票明示授權除外）、他人 core、FRAME/STATE/其他 REPORT；對齊 Rule 3/6/8/11。
    - **Reviewer (C)**：唯讀審查 diff 與 B_REPORT，僅寫 C_REPORT；禁改任何 code/docs 實體、FRAME/STATE/其他 REPORT、master_status/handoff；審查依據 CONTRACT 四流派＋12-rule。
    - **Scribe (D)**：依 B/C 整理 docs 與 Progress 末尾戰報，僅寫 D_REPORT；禁改程式碼、FRAME/STATE/B/C_REPORT、重排 Progress；對齊 CONTRACT Work Report 附錄 A 與 `AGENTS.md` §封存協議。
    - **共通**：檔首權威位階（低於憲法／合約、高於 brief）；與 DISPATCH_GUIDE Subagents 映射表；標準流水線 B→C→D→O。
  - **`04_Workflows/tickets/README.md`（流程與權限表）**
    - 新增「區塊與讀寫權限」表（FRAME/STATE/B/C/D 各區塊維護者）。
    - 新增「角色 × 可改區塊對照表」：各角色可寫區塊、典型檔案類型、禁止寫入清單。
    - 新增標準流程 **B → C → D → O** 圖示與「人工要做的事」表（開 chat＋貼模板，agent 直接讀寫 state）。
    - 新增可重跑情境：`needs_changes` 回 B 迴圈、`rejected` 由 O 介入；重跑時不刪既有 REPORT。
    - **B/C/D/O 最低欄位**：B_REPORT（`changed_files`／`artifacts`／`verification`／`behavior_notes`／`deferred_items`）；C_REPORT（`conclusion`／`blocking_issues`／`checks_summary`／`risk_level`／`suggestions`）；D_REPORT（`docs_updates`／`progress_entry`／`followup_suggestions`）；FRAME+STATE 由 O 維護。
    - 模板索引表列出五份 `_templates/*.template.md`（連結待 B-F3 補齊，見 deferred）。
  - **`04_Workflows/tickets/_templates/*.template.md`（角色指令約束）**
    - 四份 instruction 模板均於檔首引用 `multi_chat_roles.mdc` §對應角色與 `ENGINEERING_CONTRACT.md` 相關 Rule。
    - 統一「讀寫模式（必遵）」四步：先讀 state → 施工／審查／整理 → 直接回寫本角色 REPORT → 不碰其他區塊。
    - `ticket_state.template.md` 定義 FRAME/STATE/B/C/D 五區塊占位與最低欄位註解。
    - Reviewer 模板明列 `conclusion` 四值；Scribe 模板明列 D_REPORT 三欄；Implementer 模板禁自標 done。
  - **`AGENTS.md` §初始化校準第 10 步（Multi-Chat · B-F2）**
    - 單 chat 九步 → Multi-Chat **十步**：完成 1–9 後追加本步。
    - 觸發條件：尚書省或 Orchestrator 啟動平行對話時。
    - 讀取 `.cursor/rules/multi_chat_roles.mdc`；各角色見 `§Orchestrator`／`§Implementer`／`§Reviewer`／`§Scribe`。
    - 對齊聲明：Subagents 流水線仍依 `DISPATCH_GUIDE.md`；Multi-Chat 角色憲法以 `multi_chat_roles.mdc` 為準。
    - 收尾句更新為「單 chat 九步；Multi-Chat 十步」方可進暗部 CLI。
- progress_entry: |
    **2026-06-07 · B-F2 · Agent Roles / Engineering Contract 明文化 · accepted_with_gaps**

    將 C1-P1／B-F1 實戰中的 Multi-Chat 四角色分工正式寫入 `.cursor/rules/multi_chat_roles.mdc`（責任／禁區／路徑邊界／與 CONTRACT 關係）、`04_Workflows/tickets/README.md`（區塊讀寫表、B→C→D→O 主流程、`needs_changes` 迴圈）、四份角色 instruction 模板，並於 `AGENTS.md` 新增第 10 步 Multi-Chat 校準。Reviewer 結論 **accepted_with_gaps**（無 blocking）。

    **意義**：之後每張票可用 `<ticket_id>_state.md`＋角色模板跑多 chat 流水線，各 chat 只寫己區塊、以 state 為 SSOT，降低 handoff 搬運成本。

    **剩餘 gaps（非阻擋，後續票處理）**：（1）`§Implementer` Blocked Paths 對合約正文括註「B-F2」易誤讀，應改為「僅尚書省或 Governance 票可動」；（2）Orchestrator「O 確認後追加 Progress」與 Scribe「可直接末尾追加」／`AGENTS.md` §封存協議敘事略不一致，建議統一；（3）`tickets/README.md` 模板索引可點連結待 B-F3；（4）文書票 B_REPORT 驗證證據可補「已讀檔路徑」錨點。
- followup_suggestions:
  - **Governance 票（若需改合約正文）**：調整 `ENGINEERING_CONTRACT.md` 或 `HARNESS_CONSTITUTION.md` 須另開票，FRAME 明示影響範圍與上位裁決，不可藉 B-F2 類文書票間接改正文。
  - **輕修票（B-F3 或 follow-up）**：修正 `multi_chat_roles.mdc` §Implementer 合約正文括註；統一 Progress 追加流程（建議：Scribe 依 `AGENTS.md` §封存協議末尾追加，Orchestrator 收口確認）；補 `tickets/README.md` 模板索引可點連結。
  - **高風險路徑雙重審查**：觸及 `ENGINEERING_CONTRACT`、`.cursor/rules` 全域、暗部 `core`、production config 的票，Orchestrator 應在 FRAME 明示是否需 `governance-guard` 或 specialized Reviewer spot-check；可於 `multi_chat_roles.mdc`「標準流水線」後加提醒句。
  - **角色最小回報清單**：後續可為 B/C/D/O 各增「照單勾選」自檢表（含已讀路徑、diff 錨點、runner 輸出語意），降低新人漏欄風險；與 `OPS_CYCLE.md` validate-report 欄位對齊。
  - **Orchestrator 本輪收尾**：更新 STATE（`current_owner: orchestrator`、`scribe: done`、`next_action: 讀 D_REPORT 關票`）；可選將本 `progress_entry` 末尾追加至 `00_Agent_Work_Progress.md`。
