# TICKET STATE · C1-P2 · AI Workflow 偵錯與健檢服務 · Execution Plan / Runbook

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME
<!-- Orchestrator 填：票的邊界與驗收標準；開票時寫，施工前凍結 -->

- Goal:
  - 把「AI Workflow 偵錯與健檢服務」從 Product Spec (C1-P1) 變成可實際操作的對內流程指南（Execution Plan / Runbook），讓執行者能依步驟從接案到交付。
- Scope (IN SCOPE):
  - 新建或更新 `docs/WAVE_C_EXECUTION_PLAN.md`：描述 case 從接單到交付的完整步驟（Step 0–4），含 tool_id/route_id、輸入輸出、Product Spec 章節對應
  - 輕修 `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` 的 §5/§6/§7：加 Execution Plan 連結、對內/對外分界、與 Wave B/C docs 的索引
  - 建立 `04_Workflows/tickets/C1-P2_state.md` B_REPORT：記錄變更檔案、驗證對照、誠實基線、延期項目
- NonScope (OUT OF SCOPE):
  - 不改任何 `core/*`、`skills/*`、`config/*` 程式碼
  - 不改 `04_Workflows/00_Agent_Work_Progress.md`（Scribe 工作）
  - 不改其他 ticket state 檔
  - 不承諾未實作的能力（如自動接 prod selector、一鍵 pipeline）
- AllowedPaths:
  - `docs/WAVE_C_EXECUTION_PLAN.md`（新建或更新）
  - `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` 的 §5/§6/§7（輕修：連結、索引、分界說明）
  - `04_Workflows/tickets/C1-P2_state.md` 的 B_REPORT 區塊
- BlockedPaths:
  - `core/*`、`skills/*`、`config/*`
  - `04_Workflows/00_Agent_Work_Progress.md`
  - 其他 ticket state 檔（C1-P1、B-F1、B-F2、B-F3 等）
  - `AGENTS.md`、`.cursor/rules/*`、`ENGINEERING_CONTRACT.md`
- Dependencies:
  - C1-P1 Product Spec v1 已定稿（accepted_with_gaps）
  - B-F1 Skill Catalog / Gov Tool Registry v1 已定義 11 個 tool_id
  - B-F3 Routing Policy v1 已定義 `wave_b.eval_report`、`wave_b.kb_index_bootstrap` 路由
- AcceptanceCriteria:
  - `docs/WAVE_C_EXECUTION_PLAN.md` 存在，含 Step 0–4：Intake、工具選擇、Wave B 工具執行、彙整戰報、Internal Review
  - 每一步標註：相關 tool_id/route_id、輸入/輸出、對應 Product Spec 章節
  - Product Spec §5 保留 high-level 描述，但明確指向 Execution Plan 作為「對內詳細指南」
  - B_REPORT 驗證欄位說明：各 step 能否用現有工具與 CLI 實際落地
  - deferred_items 列明未來自動化項目（如 CI 整合、一鍵 pipeline）

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
  - `docs/WAVE_C_EXECUTION_PLAN.md`（新建）
  - `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`（§5/§6/§7 輕修：加連結、索引、分界說明）
- artifacts:
  - Wave C1 Execution Plan v0.1：Step 0–4 runbook，含 tool_id/route_id、輸入輸出、CLI 範例
  - Product Spec §5 新增指向 Execution Plan 的明確連結與「對內/對外」分界說明
  - Product Spec §6/§7 補充與 Wave B/C docs 的交叉索引
- verification:
  - **WAVE_C_EXECUTION_PLAN ↔ Product Spec 對照**：
    - Step 0 Intake ↔ §2 Input Requirements（確認必備/建議輸入）
    - Step 1 工具選擇 ↔ §3.1 Deliverables（對應標準交付包 tool_id）
    - Step 2 執行 Wave B 工具 ↔ §5 high-level steps（詳化為可操作 CLI）
    - Step 3 彙整戰報 ↔ §3.1 WF 健康總覽、§3.1 Flagged 個案追查
    - Step 4 Internal Review ↔ §1.3 服務性質、§4.2 限制（人工判讀標註）
  - **WAVE_C_EXECUTION_PLAN ↔ WAVE_B_EXECUTION_PLAN 對照**：
    - Step 2 工具執行對應 Wave B P1–P3 已交付 CLI（eval_export、eval_report、correlate、trace_query、wf_status_summary、kb_index_bootstrap、rag_smoke）
    - 所有 tool_id 均來自 B-F1 `skills/gov_cards/*.json`，無捏造
  - **WAVE_C_EXECUTION_PLAN ↔ SKILL_CATALOG_OVERVIEW 對照**：
    - 引用 11 個 Gov tool_id（obs.eval.* ×6、obs.trace.query、obs.wf.status_summary、kb.index.* ×3）
    - `kb.index.selector_gate` 標 skeleton（未納入 runbook 執行步驟，僅 reference）
  - **WAVE_C_EXECUTION_PLAN ↔ ROUTING_POLICY_GUIDE 對照**：
    - 引用 `wave_b.eval_report`、`wave_b.kb_index_bootstrap` 內建路由
    - 說明 policy 為「描述層編排」，非自動執行
  - **落地性驗證**：
    - 所有 Step 2 工具均有 `verify_command` 可重跑（unittest）
    - CLI 範例均來自 WAVE_B_EXECUTION_PLAN 或 catalog card `cli_invocation`
    - 「人工判讀」步驟明確標註（無自動化誇大）
- behavior_notes:
  - 本 runbook 僅描述「人工執行 CLI」流程，未宣稱自動化 pipeline
  - `kb.index.selector_gate`（skeleton）未放入 Step 2 執行列表，僅在「進階選項」提及並標示 Wave C 留項
  - 所有路徑均用相對路徑或 `Master_Map.json` 邏輯名，無硬編磁碟絕對路徑
  - 無碰觸 `core/*`、`skills/*` 程式碼，僅建立/更新 docs
- deferred_items:
  - **C1-P3 或 Wave C2**：一鍵 pipeline 自動化（將 Step 2 多個 CLI 包成單一 runner）
  - **CI 整合票**：將 eval_export → eval_report → wf_status_summary 鏈接入 nightly CI
  - **Dashboard 票**：Grafana/HTML 視覺化（Wave C 留項，見 Product Spec §3.3）
  - **Prod Selector 接線票**：`kb.index.selector_gate` 實際接入 ask_rag_selector（Wave C 留項，見 B-F1 skeleton 標註）
  - **戰報模板票**：標準化 Progress／OPS_CYCLE 欄位（與 `04_Workflows/OPS_CYCLE.md` 對齊）

---

## C_REPORT
<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: accepted_with_gaps
- blocking_issues: 無
- checks_summary:
    - boundary: "符合 FRAME.AllowedPaths：僅審查並更新本 state 檔 C_REPORT 區塊，未修改 FRAME/STATE/B_REPORT/D_REPORT，未觸及 docs/code/config/tests 或其他 ticket state 檔。"
    - alignment: "WAVE_C_EXECUTION_PLAN.md 與 Product Spec / Wave B / B-F1 / B-F3 對齊良好。Step 0-4 每步均有目的、Product Spec 對應、tool_id/route_id、輸入輸出、CLI 範例。所有 tool_id 均來自 B-F1 catalog（11 tools），所有 route_id 均來自 B-F3（wave_b.eval_report、wave_b.kb_index_bootstrap）。CLI 範例均引用 WAVE_B_EXECUTION_PLAN.md 已交付命令。`kb.index.selector_gate` 標示為 skeleton 未納入執行步驟，Routing Policy 定位為描述層編排（非自動驅動 prod selector），與 B-F3 §1.1 架構邊界一致。"
    - executability: "對於具備 Wave B 工具的人，本 runbook 足以逐步執行：Step 0 有輸入檢查清單；Step 1 有工具組合對照表；Step 2 每個子步（2.1-2.4）均有可複製貼上的 CLI 命令與 verify_command（unittest）；Step 3 有戰報草稿結構；Step 4 有 Review Checklist。所有 verify_command 均指向已存在的測試模組。"
    - honesty: "誠實標示尚未自動化項目：§FAQ Q3 明確回答「目前 v0.1 為人工執行 CLI」；`kb.index.selector_gate` 在附錄 A 標 **skeleton only**，Step 2 未納入；自動化 pipeline、CI nightly、Dashboard、prod selector 接線均列於 B_REPORT deferred_items 與 Product Spec §7 路線圖，非本票交付。無「一鍵自動 pipeline」誇大宣稱。"
    - docs: "Product Spec §5 已從純 high-level 改為明確指向 WAVE_C_EXECUTION_PLAN 作為「對內執行細節」，並保留對外敘述輕量化。§6 文件關係表列出讀者／用途／更新頻率，交叉引用 Wave B Plan / Skill Catalog / Routing Guide / Execution Plan。§7 路線圖錨點誠實標示 Wave C 能力為後續票（C1-P3、Wave C1/C2）。術語統一：§1.1 已改用「confidence 等級／樣本數 N」，§4.1 已改用 `obs.trace.query`。"
- risk_level: low
- suggestions:
    - "已達成本票目標（將 Product Spec §5 high-level steps 詳化為可執行 runbook）。建議 conclusion 為 `accepted_with_gaps`，剩餘 gaps 為非阻擋性改進項目，建議轉為後續票："
    - "**C1-P3: 自動化 Pipeline CLI** — 將 Step 2 多個獨立 CLI 包裝成單一 runner（如 `python -m workflow_v2.c1_diagnostic --config case_config.yaml`），減少人工 context switch。scope：新增 orchestrator 模組、維持既有工具不動、輸出統一戰報 JSON。"
    - "**C1-P4: 標準戰報模板與 OPS_CYCLE 對齊** — 定義戰報標準欄位（`case_id`, `investigation_target`, `gate_status`, `index_status`, `trace_hit_rate`, `recommendations[]`），與 `04_Workflows/OPS_CYCLE.md` JSON schema 對齊，使戰報可通過 `_ops_cycle.py append-report` 自動封存。scope：schema 定義、template 生成器、validate 命令。"
    - "**C1-P5: CI 整合與 Nightly 健檢** — 將 `wave_b.eval_report` 路由接入 CI nightly job，自動產生 `wf_status_summary` 並上傳 artifact；可選接入 Grafana/HTML dashboard（Wave C 留項）。scope：`.github/workflows/nightly-diagnostic.yml`、artifact 留存策略、簡易趨勢比較。"
    - "**Wave C2: Prod Selector 接線** — `kb.index.selector_gate` skeleton → prod（`GOV_KB_INDEX_SELECTOR_HOOK_ENABLED`），須另開實作票。"

---

## D_REPORT
<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- docs_updates:
    - **Product Spec v1 → Execution Plan 落實對齊**：
        - C1-P1 Product Spec v1 §5 提供 high-level 流程骨架（Step 0-4），C1-P2 透過新建 `docs/WAVE_C_EXECUTION_PLAN.md` 將其詳化為可執行的 CLI 操作手冊
        - 每個 Step 明確標註：目的、對應 Product Spec 章節、相關 tool_id/route_id、輸入/輸出、CLI 範例、人工判讀點
        - Product Spec §5 新增註解：「對外文件保留 high-level 骨架，對內執行細節參見 `docs/WAVE_C_EXECUTION_PLAN.md`」，建立清晰的對外/對內分界
    - **與 Wave B 執行計畫對齊**：
        - WAVE_C_EXECUTION_PLAN.md Step 2 所有 CLI 範例均引用 WAVE_B_EXECUTION_PLAN.md 已交付的可重跑命令
        - 對應關係：Step 2.1 (Eval 健檢) ↔ Wave B P1-EVAL-GATE-REPORT-BOOTSTRAP；Step 2.2 (Trace 追查) ↔ Wave B P2-EVAL-TRACE-CORRELATE；Step 2.3 (Index 健檢) ↔ Wave B P1-REPO-INDEX-GOV-SCOPE-LIVE
    - **與 Skill Catalog 對齊**：
        - WAVE_C_EXECUTION_PLAN.md 附錄 A 列出全部 11 個 Gov tool_id 及其 `verify_command`，直接引用 B-F1 `docs/SKILL_CATALOG_OVERVIEW.md`
        - 明確標註 `kb.index.selector_gate` 為 skeleton（未納入 Step 2 執行列表），與 Catalog flags 一致
    - **與 Routing Policy 對齊**：
        - WAVE_C_EXECUTION_PLAN.md 附錄 B 列出 `wave_b.eval_report` 與 `wave_b.kb_index_bootstrap` 兩條 route_id，引用 B-F3 `docs/ROUTING_POLICY_GUIDE.md`
        - 說明 policy 目前為「描述層編排」，非自動執行，與 Routing Policy v1 架構邊界一致
    - **建議文檔調整（若 C_REPORT 無異議）**：
        - WAVE_C_EXECUTION_PLAN.md §FAQ Q3 已說明「目前 v0.1 為人工執行 CLI」，建議在 Step 2 每個子節標題旁加 `[MANUAL]` 標籤，強化「尚未自動化」視覺提示
        - 建議在附錄 C（文件關係圖）加入 `04_Workflows/00_Agent_Work_Progress.md` 與 `04_Workflows/OPS_CYCLE.md`，標示戰報最終寫入位置

- progress_entry: |
    ## 2026-06-07 · C1-P2 · in_progress (Implementer done → Reviewer pending)

    **票號**: C1-P2 · AI Workflow 偵錯與健檢服務 · Execution Plan / Runbook v0.1

    **狀態**: Implementer 完成 B_REPORT，Reviewer 審查中

    **Runbook 結構**:
    - Step 0 — Intake（接案與輸入盤點）: 確認調查目標、時間窗、環境，檢查必備輸入，產出 Intake 摘要
    - Step 1 — 工具選擇與路徑規劃: 依調查目標選擇 tool_id/route_id 組合（品質退化調查/單案追溯/知識層就緒檢查/完整健檢）
    - Step 2 — 執行 Wave B 工具: 人工執行 CLI（Eval 健檢 → Trace 對齊 → Index 健檢 → 綜合總覽），每個子步驟含 `verify_command` 可重跑驗證
    - Step 3 — 彙整戰報草稿: 將 artifacts 整理成標準化戰報結構（Gate/Trace/Index/WF 總覽/建議分級）
    - Step 4 — Internal Review: Reviewer 依 Checklist 審查，產出最終報告與交付清單

    **實際接案的意義**:
    這張票將 C1-P1 Product Spec 的「概念」轉化為「可執行的 SOP」。現在接到一個「AI workflow 偵錯與健檢」案件時，執行者可以：
    1. 開啟 WAVE_C_EXECUTION_PLAN.md 依 Step 0-4 逐步執行
    2. 每步都有明確的 CLI 命令（來自 Wave B 已驗證的工具）
    3. 知道哪些步驟需要人工判讀（標註 [ ] 檢查點）
    4. 產出標準化戰報並寫入 `00_Agent_Work_Progress.md`
    從「spec 說我們能做什麼」變成「runbook 告訴你怎麼做」。

    **交付文件**:
    - `docs/WAVE_C_EXECUTION_PLAN.md` (新建，Step 0-4 runbook)
    - `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` §5/§6/§7 (輕修，增加 Execution Plan 連結與對內/對外分界)

- followup_suggestions:
    - **C1-P3: 自動化 Pipeline CLI** — 將 Step 2 的多個獨立 CLI (`obs.eval.export` → `obs.eval.report` → `obs.eval.correlate` → `obs.wf.status_summary`) 包裝成單一 runner（如 `python -m workflow_v2.c1_diagnostic --config case_config.yaml`），減少人工步驟間的 context switch。預估 scope：新增 orchestrator 模組、維持既有工具不動、輸出統一戰報 JSON。
    - **C1-P4: 標準戰報模板與 OPS_CYCLE 對齊** — 定義戰報標準欄位（`case_id`, `investigation_target`, `gate_status`, `index_status`, `trace_hit_rate`, `recommendations[]`），並與 `04_Workflows/OPS_CYCLE.md` 的 JSON schema 對齊，使戰報可通過 `python .\04_Workflows\_ops_cycle.py append-report --json <戰報.json>` 自動封存。預估 scope：schema 定義、template 生成器、validate 命令。
    - **C1-P5: CI 整合與 Nightly 健檢** — 將 `wave_b.eval_report` 路由接入 CI nightly job，自動產生 `wf_status_summary` 並上傳 artifact；可選接入 Grafana/HTML dashboard（Wave C 留項）。預估 scope：`.github/workflows/nightly-diagnostic.yml`、artifact 留存策略、簡易趨勢比較（與上一日/上週對比 needs_review 比例變化）。
