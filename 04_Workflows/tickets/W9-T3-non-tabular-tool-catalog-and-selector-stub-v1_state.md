# TICKET STATE · W9-T3 · non-tabular-tool-catalog-and-selector-stub-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- **Goal**: 為 non-tabular shadow flow v1 補上工具 catalog 草稿與 selector stub（僅 symbolic mapping，不執行 heavy tools）
- **Scope**:
  1. 新增 `tools/non_tabular_tool_catalog_v1.json`（NT-A ×2 + NT-B ×2 工具）
  2. 新增 `tools/non_tabular_tool_selector_v1.py` → `select_non_tabular_tools(...)`
  3. 新增 `tests/test_non_tabular_tool_selector_v1.py`
  4. 更新 WORKFLOW_INDEX、WAVE_PROGRESS_DASHBOARD
- **NonScope**:
  - ❌ 不實際執行非 Tabular heavy tools
  - ❌ 不接外部系統 / API
  - ❌ 不修改 Tabular 主鏈
  - ❌ 不新建 cases/ fixture
- **AllowedPaths**:
  - `tools/non_tabular_tool_catalog_v1.json`
  - `tools/non_tabular_tool_selector_v1.py`
  - `tests/test_non_tabular_tool_selector_v1.py`
  - `04_Workflows/tickets/W9-T3-non-tabular-tool-catalog-and-selector-stub-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- **BlockedPaths**:
  - `scripts/run_mvp_mainline_regression.py` 等 Tabular 主鏈
  - `.github/workflows/`
  - `cases/`
- **Dependencies**:
  - W8-T4 藍圖 · W9-T1 routing catalog spec · W9-T2 decision rules v2 non-tabular helper
- **AcceptanceCriteria**:
  - [AC-1] Catalog 含 4 工具（NT-A ×2、NT-B ×2），字段含 tool_id / description / input_kind / output_kind / maturity
  - [AC-2] Selector 返回 `planned_tools` symbolic 列表，不執行工具
  - [AC-3] NT-A → document 工具；NT-B → log 工具；非 non_tabular family → error
  - [AC-4] unittest 全綠
  - [AC-5] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 已更新

---

## STATE

- **overall_status**: accepted_with_gaps
- **current_owner**: orchestrator
- **next_action**: closed — 後續追蹤：W9-T4 glue 整合、W9-T5/T6 fixtures、executor/outbox 實作票（見 C_REPORT gaps）
- **last_updated**: 2026-06-15 · orchestrator
- **status_by_role**:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- **changed_files**:
  - `tools/non_tabular_tool_catalog_v1.json`（新增）
  - `tools/non_tabular_tool_selector_v1.py`（新增）
  - `tests/test_non_tabular_tool_selector_v1.py`（新增）
  - `04_Workflows/tickets/W9-T3-non-tabular-tool-catalog-and-selector-stub-v1_state.md`（新增）
  - `04_Workflows/WORKFLOW_INDEX.md`（追加 §1.12 W9-T3）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（追加 Wave 9 / W9-T3 行）
- **artifacts**: 無（JSON + stub selector + tests）
- **verification**: `python -m unittest tests.test_non_tabular_tool_selector_v1 -v` → OK
- **behavior_notes**:
  - Selector 對齊 `routing/intake_decision_rules_v2.py` task_type（`non_tabular.*`）與 W9-T1 routing doc（`non-tabular.*` alias）
  - `routing/non_tabular_routing_catalog_v1.yaml` 若不存在則 fallback 至 embedded default_tools mapping
  - 所有 planned_tools 標記 `symbolic_only: true`
- **deferred_items**:
  - W9-T4 glue layer `plan_non_tabular_route()`
  - W9-T5/T6 fixtures
  - executor / outbox 實作
- **reviewer_reverification**: 2026-06-15 · `python -m unittest tests.test_non_tabular_tool_selector_v1 -v` → 9/9 OK

---

## C_REPORT

- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無
- **checks_summary**:
  - **AC-1 ✅**: catalog 4 工具（NT-A ×2 + NT-B ×2）含 tool_id / description / input_kind / output_kind / maturity
  - **AC-2 ✅**: selector 返回 symbolic `planned_tools` · 不執行 heavy tools
  - **AC-3 ✅**: NT-A → document tools · NT-B → log tools · 非 non_tabular → error（6 tests）
  - **AC-4 ✅**: unittest 9/9 · Reviewer 複驗 2026-06-15
  - **AC-5 ⚠**: WORKFLOW_INDEX / Dashboard 索引 implementer 已改；本輪 Orchestrator 未複驗 docs patch（Step 5 草稿）
- **risk_level**: low
- **gaps**:
  - symbolic_only stub · 無 executor / outbox
  - catalog YAML fallback embedded mapping（routing catalog 非強制）
  - real fixtures 未建（W9-T5/T6）
- **suggestions**: W9-T4 preview CLI 已消費 selector；executor 留後續 Wave

---

## D_REPORT

- **docs_updates**: catalog JSON + selector stub 已交付；WORKFLOW_INDEX / Dashboard 註解留 Step 5
- **progress_entry**: W9-T3 implementer done → **accepted_with_gaps** — `non_tabular_tool_catalog_v1.json` + selector stub + 9/9 tests OK
- **followup_suggestions**: W9-T4 glue 整合 · W9-T5/T6 fixtures · executor/outbox 實作票

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | scribe | W9-T3 Reviewer→Scribe 收口 · accepted_with_gaps · D_REPORT filled based on reviewer acceptance |
| 2026-06-15 | orchestrator | STATE 關票 · overall_status accepted_with_gaps · Dashboard/Progress 收口 |
