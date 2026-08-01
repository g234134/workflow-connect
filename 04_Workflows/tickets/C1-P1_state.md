# TICKET STATE · C1-P1 · AI Workflow 偵錯與健檢服務 · Product Definition v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal:
  - 把「AI Workflow 偵錯與健檢服務」這個主打服務，寫成一份對外可用的產品說明（Product Spec v1），可以未來直接用來介紹服務、作為接戰基礎。
- Scope (IN SCOPE):
  - 新建或更新 1 份產品說明文件，路徑暫定：
    - docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md
  - 產品說明中至少包含：
    - 服務介紹（用戶視角）
    - 客戶需提供的輸入（input requirements）
    - 服務輸出內容（deliverables）
    - 適用場景與限制（what we do / what we don't do）
    - 粗略流程概覽（high-level execution steps，會在 C1-P2 詳化）
  - B chat 可根據現有 Wave A/B 能力與 docs 寫初稿文字，不需要完美，重點是結構完整、不要誇大能力。
- NonScope (OUT OF SCOPE):
  - 不改任何程式碼 / 測試 / CI 設定。
  - 不承諾具體價格與保證結果（pricing / SLA 可留待後續票）。
  - 不定義完整的商業流程（接案 / 合約 / 收款），僅聚焦「技術服務內容」。
- AllowedPaths:
  - docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md
  - docs/WAVE_C_EXECUTION_PLAN.md        <!-- 如需引用，可追加段落，但不改既有 Wave B 描述 -->
- BlockedPaths:
  - core/*
  - .observatory/*
  - observability/*.py
  - workflow_v2/kb/*.py
  - skills/*
  - .cursor/rules/*
  - AGENTS.md
  - .github/workflows/*
- Dependencies:
  - Wave B-Final 已完成（B-F1/B-F2/B-F3），作為服務可用能力基礎。
  - 現有 docs（如果已存在）中對 eval / trace / kb index 能力的描述。
- AcceptanceCriteria:
  - docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md 存在，且結構完整（含服務介紹 / input / output / scope & limitation / high-level steps）。
  - 文案不誇大能力（不宣稱目前沒有的功能），與現有 Wave B 能力相符。
  - Reviewer 判定 conclusion ∈ {accepted, accepted_with_gaps}（無阻擋項）。

---

## STATE

- overall_status: accepted_with_gaps
- current_owner: implementer
- next_action: implementer_work
- last_updated: 2026-06-07T04:52:00
- status_by_role:
  - orchestrator: done
  - implementer: not_started
  - reviewer: not_started
  - scribe: done

---

## B_REPORT

- changed_files:
  - `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`
- artifacts:
  - Product Spec v1 初稿（§1–§7：服務介紹、輸入、交付物、範圍限制、流程概覽、文件索引、版本後續）
- verification:
  - 文書票 OUT OF SCOPE 程式／測試；結構自檢對照 AcceptanceCriteria 五節齊全
  - 對照 `docs/WAVE_B_EXECUTION_PLAN.md`、`docs/SKILL_CATALOG_OVERVIEW.md`、`docs/observability.md`、`docs/ROUTING_POLICY_GUIDE.md` 撰寫
- behavior_notes:
  - 刻意標註 dev/staging、investigation-only；§4.3 能力表 ✅／❌ 對齊 Wave B 已交付工具
  - `kb.index.selector_gate`、Langfuse 統一 API、dashboard 標為未納入 v1；Routing Policy 僅描述編排
  - 未改 `docs/WAVE_C_EXECUTION_PLAN.md`（票面可選；產品檔以 Wave B 計畫交叉引用）
- deferred_items:
  - C1-P2：執行 runbook、戰報模板、`tool_id`／`route_id` 對照表（§5 high-level 留待詳化）

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues:
  - 無
- checks_summary:
  - boundary: "B_REPORT changed_files 僅含 `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`，落在 FRAME.AllowedPaths；未觸及 BlockedPaths（core、observability/*.py、skills、AGENTS.md、CI 等）。未改可選 `docs/WAVE_C_EXECUTION_PLAN.md`（repo 內亦尚無此檔），符合票面。"
  - alignment: "產品檔 §1–§5 覆蓋 FRAME Scope 五節；Goal（對外 Product Spec v1）達成。§4.3 與 §3.3 誠實標示 Wave B 已交付（eval export/report、trace query JSONL、correlate、wf status summary、kb bootstrap+smoke）與未交付（selector_gate skeleton、Langfuse/PG 統一 API、dashboard、prod selector 接線）。NonScope 遵守：無定價/SLA/代維運/商業流程承諾；§1.3、§4.2 明示 investigation-only。"
  - verification: "文書票，無程式驗證；cross-check `SKILL_CATALOG_OVERVIEW.md` 11 tool_id 與產品檔 §3.1 對照一致；`kb.index.selector_gate` skeleton reference 與 §3.3/§4.3 敘述一致。"
  - existing_behavior: "§5 流程為 high-level 骨架並明示 C1-P2 詳化；內部 validate 命令標為內部自檢（§5 Step 0、內部編排備註），未冒充完整 runbook。trace 缺失時 wf summary soft degrade 與 observability 基線一致。"
  - docs: "結構清晰（輸入 §2、輸出 §3、限制 §4、流程 §5）；外部讀者可理解必備輸入、標準交付包與 v1 邊界。§6 技術權威索引可接戰。輕微用語：§1.1「信心區間」實際對應 eval report/stats 的 confidence 等級（high/low/n/a），非統計區間；§4.1 偶用 `trace_query` 暱稱，與 catalog `obs.trace.query` 略不一致——建議 C1-P2 或 Scribe 統一 tool_id 用語。"
- risk_level: low
- suggestions:
  - Implementer 未將 B_REPORT 回寫本 state 檔（本次 Reviewer 依 chat Work Report 還原 B_REPORT 供審查）；Orchestrator 應更新 STATE 交棒至 reviewer/scribe。
  - C1-P2 詳化 §5 時補 `route_id`／CLI 參數範例，並統一全文 `tool_id` 命名（避免 trace_query 等暱稱）。
  - §1.1 Gate 價值列可改為「confidence 等級／樣本數 N」以精準對齊 `obs.eval.report` 輸出欄位。
  - 若對外發布前需 Wave C 路線圖錨點，可另票建 `docs/WAVE_C_EXECUTION_PLAN.md` 並在 §7 交叉引用（非本票阻擋）。

---

## D_REPORT

- docs_updates:
  - **`docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`（C1-P2 或輕修票）**
    - §1.1 Gate 價值列：「信心區間」→「confidence 等級（high/low/n/a）／樣本數 N」，對齊 `obs.eval.report` 實際欄位。
    - §4.1 場景表：「`trace_query`」→「`obs.trace.query`」，全文統一 Gov `tool_id`，避免暱稱與 catalog 不一致。
    - §6 索引：可加一行指向本檔為「對外 Product Spec」、技術權威仍見列舉四檔（自指清晰）。
  - **`docs/SKILL_CATALOG_OVERVIEW.md`（可選交叉引用）**
    - 文首或 Wave B 小節加一句：對外服務說明見 `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`；catalog 仍為 `tool_id` 權威。
  - **`docs/WAVE_B_EXECUTION_PLAN.md`（可選）**
    - B-Final 收口段或附錄加 Product Spec 連結，標「C1-P1 對外敘事已就緒」。
  - **`docs/observability.md`（可選）**
    - investigation-only 聲明處加反向連結至 Product Spec §1.3／§4.2，避免兩份文件各說各話。
  - **`docs/ROUTING_POLICY_GUIDE.md`（可選）**
    - 補一句：Product Spec §5 引用 route 僅為**描述層編排**，policy 不自動驅動客戶 prod 路由（與 §4.2 對齊）。
  - **另票（非本票小修）**：`docs/WAVE_C_EXECUTION_PLAN.md` 尚不存在；若對外需 Wave C 路線圖錨點，應獨立建檔後在 Product Spec §7 交叉引用。
- progress_entry: |
    ## C1-P1 · AI Workflow 偵錯與健檢服務 · Product Definition v1

    **日期**：2026-06-07 · **票號**：C1-P1 · **狀態**：accepted_with_gaps（Reviewer 無阻擋項）

    **交付**：新建 `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`（Product Spec v1 初稿，§1–§7 齊全：服務介紹、輸入、交付物、範圍限制、high-level 流程、文件索引、版本後續）。

    **對齊**：能力表與 Wave B 已交付工具一致（eval export/report、correlate、trace query、wf status summary、kb bootstrap+smoke）；未交付項（selector_gate skeleton、Langfuse/PG 統一 API、dashboard、prod selector）誠實標 ❌；無定價／SLA／代維運承諾。

    **驗收**：文書票，cross-check `SKILL_CATALOG_OVERVIEW.md` 11 tool_id；結構對照 FRAME AcceptanceCriteria 通過。

    **輕微缺口（留 C1-P2）**：§1.1「信心區間」用語、§4.1 `trace_query` 暱稱宜統一為 `tool_id`；§5 執行步驟待詳化 runbook／戰報模板。

    **下一步**：C1-P2 詳化 §5；可選輕修統一術語；定價／Wave C 計畫另票。
- followup_suggestions:
  - **C1-P2 · 執行 runbook 與戰報模板**（票面已列）：詳化 §5 各步 CLI／`route_id` 參數範例、標準 Progress／OPS_CYCLE 戰報欄位、`tool_id`／`route_id` 對照表；順手消化 §1.1／§4.1 術語統一（Reviewer 已列 gaps）。
  - **C1-P3 · 定價與交付邊界**（建議新票）：在 Product Spec 基礎上補服務包分級（最小／標準／含 Index）、工時粗估、不含項清單；仍不出 SLA 保證，與 §1.3 NonScope 對齊。
  - **Wave C Execution Plan 票**（可並行排程）：建立 `docs/WAVE_C_EXECUTION_PLAN.md`（dashboard、nightly correlate artifact、prod selector 接線），供 Product Spec §7 與對外路線圖引用；與 C1-P2 無硬依賴。
