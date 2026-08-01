# TICKET STATE · C2-P2 · Tabular Cleaning · Execution Plan / Runbook

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal:
  - 把 C2-P1 Product Spec §5 五步骨架詳化為**對內可執行** Tabular Cleaning Execution Plan / Runbook，供執行者依案操作（Intake → Cleaning → Quality Report → Delivery）。
- Scope (IN SCOPE):
  - 新建 `docs/C2-P2_RUNBOOK.md`：四階段流程、各階段檢查清單、**4 個人工簽核點**、附錄 A（C2-P1 §3.1 ↔ Wave 6 指標對照）、附錄 B（C2-D1 demo 錨點路徑）
  - 新建 `notebooks/csv_cleaning/run_tabular_cleaning_plan.py`：pseudo CLI，僅列出 runbook 階段／檢查清單（**不執行清洗**）
  - 輕修 `docs/PRODUCT_TABULAR_CLEANING.md` **§6／§7 僅**：加 C2-P2 runbook 索引、對內／對外分界、路線圖狀態
  - 更新 `docs/CASE_REPORTS/C2-D1_PHASE_CLEANING_REPORT.md`：交叉引用 C2-P2 runbook 與 demo 錨點
  - Implementer B_REPORT：記錄變更檔案、驗證對照、行為邊界、延期項目
- NonScope (OUT OF SCOPE):
  - **不實作 production CLEAN pipeline**、自助入口、一鍵自動化編排
  - 不改 `core/*`、`skills/*`、`config/*`、`tests/*`
  - 不改 C2-P1 Product Spec **核心敘事**（§1–§5 主體；§6／§7 僅允許索引／路線圖輕修）
  - 不改 `AGENTS.md`、`.cursor/rules/*`、`04_Workflows/00_Agent_Work_Progress.md`
  - 不改其他 ticket state 檔（C2-P1、C2-D1 等）
  - 不承諾 SLA、7×24、全自動無人值守
- AllowedPaths:
  - `docs/C2-P2_RUNBOOK.md`
  - `notebooks/csv_cleaning/run_tabular_cleaning_plan.py`
  - `docs/PRODUCT_TABULAR_CLEANING.md`（**僅 §6／§7**）
  - `docs/CASE_REPORTS/C2-D1_PHASE_CLEANING_REPORT.md`
  - `04_Workflows/tickets/C2-P2_state.md`（B_REPORT／C_REPORT／D_REPORT 區塊；FRAME／STATE 由 Orchestrator）
- BlockedPaths:
  - `core/*`、`skills/*`、`config/*`、`tests/*`
  - `AGENTS.md`、`.cursor/rules/*`、`.github/workflows/*`
  - `04_Workflows/00_Agent_Work_Progress.md`
  - `04_Workflows/tickets/*`（**除外**：`04_Workflows/tickets/C2-P2_state.md`）
  - `docs/PRODUCT_TABULAR_CLEANING.md`（**除外 §6／§7**；§1–§5 禁改）
- Dependencies:
  - C2-P1 `docs/PRODUCT_TABULAR_CLEANING.md`（accepted_with_gaps）
  - C2-D1 demo 錨點（`cases/demo_phase/`、`clean_phase_demo.py`、C2-D1 導覽／case 戰報）
  - `04_Workflows/WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`
  - `04_Workflows/WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`
- AcceptanceCriteria:
  - `docs/C2-P2_RUNBOOK.md` 存在，含**四階段**（A Intake → B Cleaning → C Quality Report → D Delivery）與 **4 個人工簽核點**
  - 附錄 A：`product_metrics` ↔ Wave 6 欄位對照（消化 C2-P1 Reviewer gap：§3.1 指標 vs `dedup_*`）
  - 附錄 B：C2-D1 路徑與指標與 `cases/demo_phase/` 一致
  - 明示 **INTERNAL USE ONLY · NOT A PROD PIPELINE · NON-SLA**；人工確認為必經
  - `run_tabular_cleaning_plan.py --stage all --case demo_phase` → `ok: true`
  - `run_tabular_cleaning_plan.py --stage intake` → `ok: true`
  - Reviewer 判定 `conclusion ∈ {accepted, accepted_with_gaps}`（無阻擋項）
- VerificationCommands:
  - `python notebooks/csv_cleaning/run_tabular_cleaning_plan.py --stage all --case demo_phase`
    - 預期：`ok: true`
  - `python notebooks/csv_cleaning/run_tabular_cleaning_plan.py --stage intake`
    - 預期：`ok: true`

---

## STATE

- overall_status: accepted_with_gaps
- implementation_status: accepted_with_gaps
- current_owner: scribe
- next_action: Scribe 填 D_REPORT；將 C_REPORT 結論同步至 Progress / Wave docs
- last_updated: 2026-06-15 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `docs/C2-P2_RUNBOOK.md`（新建 · 四階段 runbook、4 簽核點、附錄 A/B/C）
  - `notebooks/csv_cleaning/run_tabular_cleaning_plan.py`（新建 · pseudo CLI，僅列步驟／檢查清單）
  - `docs/PRODUCT_TABULAR_CLEANING.md`（**僅 §6／§7** · C2-P2 索引、對內／對外分界、路線圖狀態）
  - `docs/CASE_REPORTS/C2-D1_PHASE_CLEANING_REPORT.md`（更新 · C2-P2 runbook 交叉引用、demo 錨點對齊）
- artifacts:
  - C2-P2 Runbook v0.1-draft：`docs/C2-P2_RUNBOOK.md`（§0 邊界聲明 → §19 四階段細節 → 附錄 A 指標對照 → 附錄 B C2-D1 錨點）
  - Pseudo CLI planner：`notebooks/csv_cleaning/run_tabular_cleaning_plan.py`（stages: intake / cleaning / quality / delivery / all）
  - Product Spec 索引更新：§6 文件關係表、§7 路線圖 C2-P2 狀態
- verification:
  - **閱讀自檢**：
    - 四階段（A Intake → B Cleaning → C Quality Report → D Delivery）完整，對應 C2-P1 §5 五步
    - **4 個人工簽核點**（#1 規則矩陣 → #2 閾值／去重 → #3 qa_status → #4 Lead 交付）均已標註
    - **附錄 A**：C2-P1 §3.1 `product_metrics` ↔ Wave 6 欄位對照（含 `duplicate_rows_found` vs `dedup_*` 語意說明）
    - **C2-D1 路徑一致**：附錄 B 與 `cases/demo_phase/`、`clean_phase_demo.py`、case 戰報路徑對齊
  - **CLI**：
    - `python notebooks/csv_cleaning/run_tabular_cleaning_plan.py --stage all --case demo_phase` → `ok: true`
    - `python notebooks/csv_cleaning/run_tabular_cleaning_plan.py --stage intake` → `ok: true`
- behavior_notes:
  - **刻意不實作 prod pipeline**；pseudo CLI 僅列 runbook 步驟與檢查清單，實際清洗仍走 `clean_phase_demo.py`（C2-D1 demo scope）或人工流程
  - **未改 C2-P1 Spec 核心敘事**（§1–§5）；僅 §6／§7 加索引與路線圖狀態
  - **未觸** `core/`、`AGENTS.md`、`.cursor/rules/` 或制度檔
  - runbook 全文標 **INTERNAL USE ONLY · NOT A PROD PIPELINE · NON-SLA**
- deferred_items:
  - **C2-P3（建議）**：定價與交付邊界分級（最小／標準／含多表）
  - **production CLEAN pipeline／自助入口**：客戶上傳即跑（未納入 v1；runbook 僅描述專案制流程）
  - **`report.json` JSON Schema 落盤與 CI 回歸**
  - **異常 flag 外顯 sidecar**（C2-D1 僅 JSON 內部；交付 CSV 不外顯）
  - **欄位字典與決策矩陣**完整落盤
  - **Wave B eval ↔ 清洗 job metadata 標準對接**（內部品質閘；獨立票）

---

## C_REPORT

<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: accepted_with_gaps
- blocking_issues:
  - 無
- checks_summary:
  - **AC-1 ✅**：`docs/C2-P2_RUNBOOK.md` 存在，含四階段（A Intake → B Cleaning → C Quality Report → D Delivery）與 **4 個人工簽核點**（#1 規則矩陣 → #4 Lead 交付）；全文標 **INTERNAL USE ONLY · NOT A PROD PIPELINE · NON-SLA**。
  - **AC-2 ✅**：附錄 A 已建立 C2-P1 §3.1 `product_metrics` ↔ Wave 6 欄位對照（含 `duplicate_rows_found` vs `dedup_*` 語意說明）。
  - **AC-3 ✅**：附錄 B C2-D1 demo 錨點與 `cases/demo_phase/`、`clean_phase_demo.py`、case 戰報路徑一致。
  - **AC-4 ✅**：pseudo CLI 可重跑：`python notebooks/csv_cleaning/run_tabular_cleaning_plan.py --stage all --case demo_phase` → `ok: true`；`--stage intake` → `ok: true`（2026-06-15 Reviewer 重跑）。
- risk_level: low
- gaps:
  - **`report.json` JSON Schema 落盤與 CI 回歸** — **deferred**（未來票；非本輪 scope）
  - **異常 flag 外顯 sidecar** — **deferred**（C2-D1 刻意不在 CSV 外顯；交付 sidecar 留後續票）
  - **production CLEAN pipeline／自助入口** — **out of scope**（runbook 僅描述專案制人工流程；**不得**宣稱已交付 prod pipeline）
  - **欄位字典與決策矩陣完整落盤** — **deferred**（C2-P3 或後續票）
  - **Wave B eval ↔ 清洗 job metadata 標準對接** — **deferred**（獨立票）
- suggestions:
  - Scribe 填 D_REPORT + Progress 末尾條目；`docs/PRODUCT_TABULAR_CLEANING.md` §7 路線圖可在 Reviewer 收口後標 **accepted_with_gaps**。
  - 後續 **C2-P3** 可展開定價／交付邊界分級（見 B_REPORT deferred_items）。

---

## D_REPORT

<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- docs_updates:
  - **Scribe TODO**：將 C_REPORT 結論同步至 `docs/WAVE_PROGRESS_DASHBOARD.md` Wave C 索引、`docs/wave_c/overview.md` C2 表、`docs/PRODUCT_TABULAR_CLEANING.md` §7 C2-P2 狀態。
- progress_entry:
  - **Scribe TODO**：Progress 末尾追加 C2-P2 Reviewer `accepted_with_gaps` 摘要（四階段 runbook + pseudo CLI；deferred 項見 C_REPORT gaps）。
- followup_suggestions:
  - 與 C2-D1 合併 Scribe 歸檔；Wave 2 接案 MVP 可引用 C2-P2 為對內執行 SSOT（仍 **非** prod pipeline）。

---

## O_NOTES

> Orchestrator 維護：開票與交棒紀錄。

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 新建 C2-P2 FRAME／STATE；落入 Implementer B_REPORT 草稿；交棒 Reviewer | 本檔 |
| 2026-06-15 | reviewer | C_REPORT `accepted_with_gaps`；AC-1～AC-4 通過；gaps 見 C_REPORT；交棒 Scribe | 本檔 |

### Handoff

- **前置**：C2-P1 accepted_with_gaps；C2-D1 demo 錨點就緒
- **本輪**：Implementer 已完成 runbook + pseudo CLI + §6/§7 索引；`implementation_status: in_review`
- **下一棒**：Reviewer 依 FRAME AcceptanceCriteria 驗收；通過後 Scribe 填 D_REPORT + Progress
