# TICKET STATE · C2-P1 · 一般表格清洗與品質報告 · Product Definition v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal:
  - 把「一般表格型（CSV/Excel）資料清洗與品質報告」寫成一份對外可用的產品說明（Product Spec v1），可作為接案介紹與 C2-P2 runbook 的前置基礎。
- Scope (IN SCOPE):
  - 新建 1 份產品說明文件：`docs/PRODUCT_TABULAR_CLEANING.md`
  - 產品說明至少包含（結構對齊 C1-P1 §1–§7）：
    - 服務介紹（用戶視角）：缺失／重複／異常／格式四類問題與適用場景
    - 客戶需提供的輸入（input requirements）：CSV／Excel、欄位說明、主鍵、可缺失欄
    - 服務輸出內容（deliverables）：清洗後檔案、品質報告（前後指標、決策規則）
    - 適用場景與限制：單表／小量多表清洗、基本 join／欄位標準化；誠實標註能力邊界
    - 粗略流程概覽（Intake → Profiling → Cleaning → Quality Check → Report；C2-P2 詳化）
    - 文件索引與後續（Wave 6 CLEAN、C2-P2、與 C1／Wave B 鄰接關係）
  - Implementer 可依 Wave 6/7 CLEAN 規格與 C1-P1 範本撰寫初稿；重點結構完整、不誇大能力。
- NonScope (OUT OF SCOPE):
  - 不改任何程式碼／測試／CI／config。
  - 不修改其他 docs 主幹（含 C1 Product Spec、`docs/WAVE_C_EXECUTION_PLAN.md`；僅允許引用）。
  - 不承諾定價、SLA、7×24 託管、一鍵 pipeline／自助入口。
  - 不定義 runbook 細節（CLI、戰報模板留 C2-P2）。
  - 不定義完整商業流程（接案／合約／收款）；僅聚焦技術服務內容。
  - 不涵蓋數據倉儲建置、OCR、複雜 NLP、CLEAN-ENRICH 外部 API enrich（可於 spec 標為 ❌ 或另議）。
- AllowedPaths:
  - `docs/PRODUCT_TABULAR_CLEANING.md`
  - `04_Workflows/tickets/C2-P1_state.md`（B_REPORT／C_REPORT／D_REPORT 區塊；FRAME／STATE 由 Orchestrator）
- BlockedPaths:
  - `core/*`
  - `skills/*`
  - `config/*`
  - `tests/*`
  - `docs/*`（**除外**：`docs/PRODUCT_TABULAR_CLEANING.md`）
  - `04_Workflows/00_Agent_Work_Progress.md`
  - `04_Workflows/tickets/*`（**除外**：`04_Workflows/tickets/C2-P1_state.md`）
  - `AGENTS.md`、`.cursor/rules/*`、`.github/workflows/*`
  - `observability/*.py`
- Dependencies:
  - C1-P1 Product Spec v1（`docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`）作為結構範本。
  - Wave 6/7 CLEAN 產品線規格（`WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md` 等，DRAFT-v0.1）作為能力基線參考。
- AcceptanceCriteria:
  - `docs/PRODUCT_TABULAR_CLEANING.md` 存在，§1–§7 結構完整。
  - 涵蓋四類清洗（缺失／重複／異常／格式）與品質報告前後指標；明示非 SLA、非 7×24、非全自動。
  - §4.3 能力表誠實標註 Wave 6 CLEAN 已交付／未交付（如 CLEAN-BASIC vs ENRICH、OCR、一鍵 pipeline）。
  - 文案不誇大（不宣稱 v1 未承諾能力）。
  - Reviewer 判定 `conclusion ∈ {accepted, accepted_with_gaps}`（無阻擋項）。

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: Orchestrator 解鎖 C2-D1（dependency:C2-P1 已收口）
- last_updated: 2026-06-07 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `docs/PRODUCT_TABULAR_CLEANING.md`（新建）
- artifacts:
  - Product Spec v1 初稿（§1–§7：服務介紹、輸入、交付物、範圍限制、流程概覽、文件索引、版本後續）
- verification:
  - **C2-P1 ↔ C1-P1 結構對照**：
    - §1 服務介紹 ↔ C1 §1（1.1 這是什麼／1.2 適合誰／1.3 服務性質聲明）
    - §2 輸入需求 ↔ C1 §2（2.1 必備／2.2 建議／2.3 不需提供／2.4 前置假設）
    - §3 交付物 ↔ C1 §3（3.1 標準包／3.2 可選／3.3 不屬 v1）
    - §4 範圍與限制 ↔ C1 §4（4.1 做什麼／4.2 不做什麼／4.3 能力邊界表）
    - §5 流程概覽 ↔ C1 §5（mermaid + 5 high-level steps；明示 C2-P2 詳化，非 runbook）
    - §6 文件索引 ↔ C1 §6（Wave 6/7 CLEAN 權威 + C1／Wave B 鄰接關係）
    - §7 版本與後續 ↔ C1 §7（C2-P2／定價／案例庫路線圖）
  - **誠實基線對照**：交叉閱讀 `WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`、`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`；§4.3 ✅／❌／⚪ 對齊 CLEAN-BASIC 與 ENRICH 邊界；Excel 標為個案支援並註多 sheet 限制
  - **FRAME AcceptanceCriteria 自檢**：四類清洗（缺失／重複／異常／格式）、品質報告前後指標、非 SLA 聲明均已覆蓋
- existing_behavior:
  - 本票為**新增**對外產品說明文件；**未修改**任何 `core`／`skills`／`config`／`tests` 或 C1 主幹文件
  - 不改變既有 CLEAN pipeline、Wave B eval 工具或 C1 健檢服務的 runtime 行為
- deferred_items:
  - **C2-P2**：Execution Plan／runbook（Intake → Profiling → Cleaning → Quality Check → Report 的 CLI、檢查清單、戰報模板）
  - **C2-P3（建議）**：定價與交付邊界分級（最小／標準／含多表）
  - **範例案例庫**：去識別化訂單／問卷／營運報表前後對照樣本
  - **自助入口／一鍵 pipeline**：客戶自助上傳與自動化編排（未納入 v1 承諾）
  - **Wave B eval 與清洗 job metadata 標準對接**：內部輔助品質閘，待 C2-P2 或獨立票定義契約

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues:
  - 無
- checks_summary:
  - boundary: "B_REPORT `changed_files` 僅含 `docs/PRODUCT_TABULAR_CLEANING.md`，落在 FRAME.AllowedPaths；未觸及 BlockedPaths（`core/*`、`skills/*`、`config/*`、`tests/*`、C1 主幹 docs、`00_Agent_Work_Progress.md`、其他 ticket state）。文書票，無程式／CI 變更。"
  - alignment: "產品檔 §1–§7 完整對齊 C1-P1 結構與 FRAME Scope：§1 四類清洗＋適用場景＋§1.3 非 SLA／非 7×24／非全自動；§2 必備／建議／不需／前置假設；§3 標準包＋可選＋不屬 v1；§4 What we do／don't do＋§4.3 能力表；§5 mermaid 五步骨架並明示 C2-P2 詳化；§6–§7 索引與路線圖。FRAME AcceptanceCriteria（四類清洗、品質指標、誠實能力表）均已覆蓋。Goal（對外 Product Spec v1）達成。"
  - honesty: "§1.3、§4.2、§3.3、§5 執行分工均明示專案制、人工確認點、不保證全捕獲；§4.3 與 §7 將一鍵 pipeline／自助入口標 ❌ 或「未納入 v1」；ENRICH／OCR 標 ❌；Wave B eval 標 ⚪ 內部輔助。未暗示客戶可自助上傳或全自動無人值守 pipeline 已存在。§4.3 CSV ✅ 用語為「對齊 Wave 6 CLEAN-BASIC 規格意圖」，§6 註明 Wave 6/7 為 DRAFT-v0.1，與誠實基線一致。"
  - docs: "對外可讀性良好：§2 輸入表、§3 交付物與指標表、§4 限制表、§5 流程清單分工清楚。§6 區分對外 Product Spec／對內 C2-P2／Wave 6 技術權威／C1 鄰接產品，避免與 C1 runbook 混淆。輕微 gaps（非阻擋）：§4.3 Excel ✅（個案）略強於 Wave 6 矩陣主格式（CSV／NDJSON）表述，但 §2.4／§4.3 備註已限縮；§3.1 指標命名（如 `duplicate_rows_found`）與 `WAVE6_CLEAN_DELIVERABLE_TEMPLATES` 欄位（如 `dedup_*`）尚未逐欄對照——留 C2-P2 或 Scribe 統一。"
- risk_level: low
- suggestions:
  - **解鎖 C2-D1**：Orchestrator 更新 dispatch 後 C2-D1 可從 dependency:C2-P1 解除阻塞。
  - **C2-P2 · Execution Plan**：詳化 §5 五步為 runbook；對照 `WAVE6_CLEAN_DELIVERABLE_TEMPLATES` 欄位命名（§3.1 指標 vs `dedup_*` gap）。
  - **C2-P3（建議）**：定價與交付分級（最小單表／標準／含小量多表 join），仍不出 SLA。
  - **範例案例庫票**：去識別化訂單／問卷／營運報表前後對照（C2-D1/C2-D2）。
  - **Scribe**：填 D_REPORT + Progress 摘要（D_REPORT 草稿已預填，可收口）。

---

## D_REPORT

- docs_updates:
  - **`docs/PRODUCT_TABULAR_CLEANING.md`（C2-P1 新建 · Product Spec v1）**
    - §1–§7 結構對齊 C1-P1（`docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`）：服務介紹、輸入需求、交付物、範圍限制、流程概覽、文件索引、版本後續。
    - §1 定義「一般表格型資料清洗與品質報告」：四類問題（缺失／重複／異常／格式）、適用場景（訂單／問卷／營運報表等）、§1.3 非 SLA／非 7×24／非全自動聲明。
    - §2 輸入契約：必備（CSV／Excel、欄位說明、主鍵、可缺失欄、清洗目標）、建議項、不需提供項、前置假設（單檔約百萬列／1 GB、多 sheet 需明示）。
    - §3 交付物：清洗後資料檔 + 品質報告（`report.json`／`report.md`）+ 決策規則紀錄 + 執行證據索引；§3.1 前後指標表（`total_rows`、`accepted_rows`、`duplicate_rows_found` 等）；§3.3 明示不屬 v1（倉儲、OCR、NLP、ENRICH、SLA）。
    - §4 能力邊界：§4.3 誠實對齊 Wave 6 CLEAN — CSV／四類清洗／品質報告 ✅；Excel 個案 ✅（有限）；ENRICH／OCR／一鍵 pipeline ❌；Wave B eval ⚪ 內部輔助。
    - §5 五步骨架（Intake → Profiling → Cleaning → Quality Check → Report）+ mermaid；明示 C2-P2 詳化 runbook，非對外執行細節。
    - §6 文件索引：區分對外 Product Spec／對內 C2-P2／Wave 6/7 CLEAN 技術權威／C1 鄰接產品／Wave B eval 內部品質複查；避免與 C1 runbook 混淆。
    - §7 路線圖：C2-P2 runbook、C2-P3 定價、範例案例庫、自助入口未納入 v1。
  - **可選交叉引用（另票／C2-P2 順手）**
    - `04_Workflows/WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md` 文首加一句：對外說明見 `docs/PRODUCT_TABULAR_CLEANING.md`。
    - §3.1 指標命名（如 `duplicate_rows_found`）與 `WAVE6_CLEAN_DELIVERABLE_TEMPLATES` 欄位（如 `dedup_*`）逐欄對照 — Reviewer 列為非阻擋 gap，留 C2-P2 或輕修票。
- progress_entry: |
    ## C2-P1 · 一般表格清洗與品質報告 · Product Definition v1

    **日期**：2026-06-07 · **票號**：C2-P1 · **狀態**：accepted_with_gaps（Reviewer 無阻擋項）

    **交付**：新建 `docs/PRODUCT_TABULAR_CLEANING.md`（Product Spec v1 初稿，§1–§7 齊全：服務介紹、輸入、交付物、範圍限制、high-level 流程、文件索引、版本後續）。

    **內容**：定義「一般表格型（CSV/Excel）資料清洗與品質報告」服務 — 四類清洗（缺失／重複／異常／格式）、清洗前後品質指標、決策規則紀錄；輸入含欄位說明與主鍵；輸出含清洗檔 + `report.json`／`report.md`；誠實標註 Wave 6 CLEAN-BASIC ✅、ENRICH／OCR／一鍵 pipeline ❌、Wave B eval ⚪ 內部輔助。

    **對系統意義**：Wave C 第二條對外產品線就緒（姊妹於 C1 AI workflow 健檢）；未來所有表格清洗案可對齊本 spec 接案、交付與驗收，C2-P2 runbook 以前置基礎已具。

    **驗收**：文書票，結構對照 C1-P1 與 FRAME AcceptanceCriteria 通過；能力表交叉 `WAVE6_CLEAN_PRODUCT_MATRIX`／`WAVE6_CLEAN_DELIVERABLE_TEMPLATES`（DRAFT-v0.1）。

    **輕微缺口（留 C2-P2／案例庫）**：§3.1 指標命名與 deliverable templates 欄位尚未逐欄對照；§4.3 Excel ✅（個案）略強於矩陣主格式表述（§2.4 已限縮）；§5 執行步驟待詳化 runbook／戰報模板；Wave B eval 與清洗 job metadata 標準對接待獨立票。

    **下一步**：C2-P2 詳化 §5 為 Execution Plan（Step 0–4）；C2-P3 定價分級；範例案例庫（C2-D1/C2-D2 去識別化樣本）。
- verification:
  - 文書票：Reviewer 結構對照 C1-P1（`docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`）§1–§7 → **通過**
  - 能力表交叉 `WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`／`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`（DRAFT-v0.1）→ **誠實基線對齊**
  - FRAME AcceptanceCriteria：四類清洗、品質指標、非 SLA 聲明、§4.3 能力表 → **均已覆蓋**
  - `changed_files` 僅含 `docs/PRODUCT_TABULAR_CLEANING.md`；未觸 BlockedPaths
- behavior_notes:
  - 本票為**新增**對外 Product Spec；**未修改** core／skills／config／tests 或 C1 主幹
  - §4.3 Excel ✅（個案）略強於 Wave 6 矩陣主格式（CSV／NDJSON）表述；§2.4 已限縮 — Reviewer 列為**非阻擋 gap**
  - §3.1 指標命名（如 `duplicate_rows_found`）與 deliverable templates `dedup_*` 尚未逐欄對照 — 留 C2-P2
  - §5 為 high-level 五步骨架；runbook／CLI 細節**非** v1 承諾（C2-P2 詳化）
- followup_suggestions:
  - **C2-P2 · Execution Plan／runbook**（票面已列）：詳化 §5 五步為對內 runbook（輸入檢查清單、profiling 產物、`report.json`／`report.md` 章節對照 `WAVE6_CLEAN_DELIVERABLE_TEMPLATES`、人工判讀點、戰報模板）；參照 `docs/WAVE_C_EXECUTION_PLAN.md` Step 0–4 格式；順手消化 §3.1 指標命名與 templates 欄位對照（Reviewer gaps）。
  - **C2-P3 · 定價與交付分級**（建議新票）：在 Product Spec 基礎上補服務包分級（最小單表／標準／含小量多表 join）、按資料量／欄位數／複雜度粗估；仍不出 SLA，與 §1.3 NonScope 對齊。
  - **範例案例庫票（C2-D1／C2-D2）**：去識別化訂單／問卷／營運報表前後對照樣本，掛於 Product Spec §7 或獨立附錄，供新客戶參考；補強對外說服力（B_REPORT `deferred_items` 已列）。
  - **Wave B eval ↔ 清洗 job metadata 對接**（可獨立票）：定義清洗 job 可匯出 metadata 契約，供 `obs.eval.report`／`obs.eval.stats` 內部品質閘複查；非客戶必備輸入，與 §6 索引說明一致。
  - **可選輕修**：`WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md` 文首交叉引用本 Product Spec
