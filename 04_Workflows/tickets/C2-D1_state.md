# TICKET STATE · C2-D1 · Demo 表格清洗與品質報告（PRODUCT_TABULAR_CLEANING v1）



> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。



---



## FRAME



- Goal:

  - 為 `docs/PRODUCT_TABULAR_CLEANING.md`（C2-P1）製作**可帶客戶看的 demo**：樣本表格 + 清洗流程 + 品質戰報樣例；承諾不超出 C2-P1 誠實邊界。

- Scope (IN SCOPE):

  - 匿名化 mock 樣本：`cases/demo_phase/Phase.csv`

  - 可重跑 demo 腳本：`notebooks/csv_cleaning/clean_phase_demo.py`

  - 清洗產物：`Phase_cleaned.csv`

  - 品質戰報：`report.json`（C2-P1 §3.1 + Wave 6 骨架）、`report.md`、`cleaning_stats.json`

  - 文檔：導覽 `docs/C2-D1_DEMO_WALKTHROUGH.md`、case 戰報、模板樣例 `docs/CASE_REPORTS/C2-D1_QUALITY_REPORT_SAMPLE.md`

  - 四類清洗示範：缺失／重複／異常／格式（對齊 C2-P1 §1.1）

- NonScope (OUT OF SCOPE):

  - 不動 `core/*`、`skills/*`、`config/*`、`tests/*`、`AGENTS.md`

  - 不改 C2-P1 Spec 主體、其他 ticket state、Progress

  - 不建 production pipeline、自助入口、ENRICH／OCR

  - 不宣稱 SLA、7×24、全自動無人值守

  - 異常 flag 不在交付 CSV 外顯（僅 JSON 內部；留 C2-P2）

- AllowedPaths:

  - `cases/demo_phase/*`

  - `notebooks/csv_cleaning/*`

  - `docs/C2-D1_DEMO_WALKTHROUGH.md`

  - `docs/CASE_REPORTS/*`（C2-D1 相關）

  - `04_Workflows/tickets/C2-D1_state.md`（B_REPORT 區塊）

- BlockedPaths:

  - `core/*`、`skills/*`、`config/*`、`tests/*`

  - `AGENTS.md`、`.cursor/rules/*`、`.github/workflows/*`

  - `04_Workflows/00_Agent_Work_Progress.md`

  - 其他 ticket state 檔

  - `docs/PRODUCT_TABULAR_CLEANING.md`（C2-P1 主體）

- Dependencies:

  - C2-P1 `docs/PRODUCT_TABULAR_CLEANING.md`（accepted_with_gaps）

  - `04_Workflows/WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`

  - `04_Workflows/WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`

- AcceptanceCriteria:

  - demo 表格 + 清洗流程 + 品質戰報樣例均可在 repo 找到，路徑列於 B_REPORT

  - 指標命名對齊 C2-P1 §3.1（`total_rows`、`duplicate_rows_found`、`missing_rate_by_field` 等）

  - 承諾未超出 C2-P1；未觸禁區

  - 腳本可重跑：`python notebooks/csv_cleaning/clean_phase_demo.py` → `ok: true`



---



## STATE



- overall_status: accepted_with_gaps

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

  - `notebooks/csv_cleaning/clean_phase_demo.py`（增 `report.json`／`report.md` 產出；C2-P1 §3.1 `product_metrics`）

  - `docs/C2-D1_DEMO_WALKTHROUGH.md`（新建 · demo 導覽與五步流程）

  - `docs/CASE_REPORTS/C2-D1_QUALITY_REPORT_SAMPLE.md`（新建 · 品質戰報模板樣例）

  - `docs/CASE_REPORTS/C2-D1_PHASE_CLEANING_REPORT.md`（更新 · C2-P1 交叉引用、§4.1 指標表）

  - `04_Workflows/tickets/C2-D1_state.md`（FRAME 對齊 C2-P1 demo 目標；本 B_REPORT）

- artifacts:

  - **樣本表格**：`cases/demo_phase/Phase.csv`（7 列 mock，含缺失／重複／異常／格式髒資料）

  - **清洗產物**：`cases/demo_phase/Phase_cleaned.csv`（5 列）

  - **品質戰報（機讀）**：`cases/demo_phase/report.json` — `product_metrics` + Wave 6 `summary`/`stats`/`errors` 骨架

  - **品質戰報（人讀）**：`cases/demo_phase/report.md`（腳本產出精簡摘要）

  - **剖析統計**：`cases/demo_phase/cleaning_stats.json`（before/after profiling）

  - **導覽文檔**：`docs/C2-D1_DEMO_WALKTHROUGH.md`

  - **模板樣例**：`docs/CASE_REPORTS/C2-D1_QUALITY_REPORT_SAMPLE.md`

  - **case 戰報**：`docs/CASE_REPORTS/C2-D1_PHASE_CLEANING_REPORT.md`

- verification:

  - 命令：`python notebooks/csv_cleaning/clean_phase_demo.py`

  - 結果：`{"ok": true, "input_rows": 7, "output_rows": 5, "report_json": "cases/demo_phase/report.json"}`

  - `report.json` → `product_metrics.total_rows=7`、`accepted_rows=5`、`rejected_rows=1`、`duplicate_rows_found=2`、`duplicate_rows_removed=1`

  - `report.json` → `summary.sku=CLEAN-BASIC`、`qa_status=pass_with_warnings`

  - 目視：`Phase_cleaned.csv` 五列；Phase 4 之 105.0 保留未截斷

- existing_behavior:

  - 本案為 **demo scope**；僅新增／更新 `cases/demo_phase/`、`notebooks/csv_cleaning/`、`docs/C2-D1_*`、`docs/CASE_REPORTS/C2-D1_*`

  - **未修改** `core`、`skills`、`config`、`tests`、`AGENTS.md` 或 C2-P1 主體

  - 不影響既有 production CLEAN pipeline runtime

- deferred_items:

  - C2-P2：Execution Plan／runbook、異常 flag 外顯 sidecar、欄位字典與決策矩陣

  - 訂單／問卷第二份 mock 樣本（C2-D2）

  - `report.json` JSON Schema 落盤與 CI 回歸

  - Wave 6 `w6://` 正式交付 URI（demo 使用相對路徑）



---



## C_REPORT

<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->



- conclusion: accepted_with_gaps

- blocking_issues:

  - 無

- risk_level: low

- checks_summary:

  - **AC-1 ✅**：demo 樣本 `cases/demo_phase/raw/Phase.csv` 存在（7 列 mock，含缺失／重複／異常／格式髒資料）；清洗產物與導覽／case 戰報路徑可於 repo 定位。

  - **AC-2 ✅**：清洗腳本可重跑：`python notebooks/csv_cleaning/clean_phase_demo.py --force` → `ok: true`（7→5 列；`report_json` 路徑正確）。**註**：裸跑 `clean_phase_demo.py` 現會被 P2 eligibility gate 攔下（`review_needed`）；demo 重跑須 `--force` 或 `--skip-eligibility`（Walkthrough 待 Scribe 對齊，**非** blocking）。

  - **AC-3 ✅**：`cases/demo_phase/reports/report.json` 含 `product_metrics`（`total_rows=7`、`accepted_rows=5`、`rejected_rows=1`、`duplicate_rows_found=2` 等）與 Wave 6 `summary`/`stats`/`errors` 骨架。

  - **AC-4 ✅**：指標命名與 C2-P1 §3.1 一致；未觸 `core/*`、`AGENTS.md` 等禁區；承諾未超出 C2-P1 誠實邊界。

- gaps:

  - **`report.json` JSON Schema 標準化與 CI 回歸** — **deferred**（留 C2-P2／未來票；**非**本輪完成項）

  - **Wave 6 `w6://` 正式交付 URI** — **deferred**（demo 使用相對路徑）

  - **第二份 mock 樣本（C2-D2）** — **deferred / optional**

  - **異常 flag 外顯 sidecar** — **deferred**（僅 JSON 內部；交付 CSV 不外顯，與 C2-P1 一致）

  - **demo CLI 與 eligibility gate 文檔對齊** — **deferred**（`C2-D1_DEMO_WALKTHROUGH.md` 仍寫裸跑命令；須補 `--force`／gate 說明）

- suggestions:

  - 與 C2-P2 合併 Scribe 歸檔；Walkthrough 補 eligibility gate 重跑說明（doc-only）。

  - C2-P2 runbook 附錄 B 已引用本 demo 錨點，兩票可一併 Progress 收口。



---



## D_REPORT

<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->



- docs_updates:

  - **Scribe TODO**：將 C_REPORT 結論同步至 `docs/wave_c/overview.md` C2 表、`docs/C2-D1_DEMO_WALKTHROUGH.md`（eligibility gate 重跑說明）。

- progress_entry:

  - **Scribe TODO**：Progress 末尾追加 C2-D1 Reviewer `accepted_with_gaps` 摘要（demo 錨點 + report.json；deferred 項見 C_REPORT gaps）。

- followup_suggestions:

  - 與 C2-P2 D_REPORT 合併歸檔；可選 C2-D2 第二 mock 樣本留未來票。


