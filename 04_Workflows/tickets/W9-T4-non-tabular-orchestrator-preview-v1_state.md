# TICKET STATE · W9-T4 · non-tabular-orchestrator-preview-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- **Goal**: 為 non-tabular shadow flow v1 落地 preview-only orchestrator CLI，串接 v2 decision（non-tabular 分支）、routing catalog、selector stub，輸出 decision / planned_route / planned_tools / risk，寫入 sandbox outbox。

- **Scope**:
  1. `scripts/run_non_tabular_experiment_preview.py` CLI（`--task-type` · `--case-dir` · `--format`）
  2. 調用 v2 decision helper、non-tabular glue、selector stub（preview only）
  3. 寫入 `outbox/non_tabular_experiment/<timestamp>_<case_stub>.json`
  4. 文檔 `docs/non-tabular-orchestrator-preview-v1.md`
  5. unittest `tests/test_non_tabular_orchestrator_preview_v1.py`
  6. WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引更新

- **NonScope**:
  - ❌ 不改 Tabular 相關 `*.py`（`tabular_tool_*`、`intake_to_tabular_glue` 等）
  - ❌ 不寫入主鏈 outbox / cases
  - ❌ 不實際執行 heavy tools
  - ❌ 不影響 Agent 標準線 / mainline regression

- **AllowedPaths**:
  - `scripts/run_non_tabular_experiment_preview.py`
  - `routing/intake_to_non_tabular_glue.py`
  - `routing/non_tabular_routing_catalog_v1.yaml`
  - `tools/non_tabular_tool_catalog_v1.json`
  - `tools/non_tabular_tool_selector_v1.py`
  - `docs/non-tabular-orchestrator-preview-v1.md`
  - `tests/test_non_tabular_orchestrator_preview_v1.py`
  - `04_Workflows/tickets/W9-T4-non-tabular-orchestrator-preview-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`

- **AcceptanceCriteria**:
  - [AC-1] CLI 支援 `non_tabular.document.*` / `non_tabular.log.*` preview
  - [AC-2] 輸出含 decision、planned_route、planned_tools、risk/notes
  - [AC-3] Sandbox outbox JSON 寫入正確路徑
  - [AC-4] 非 non_tabular task_type → blocked
  - [AC-5] unittest 全綠；未修改 Tabular 主鏈檔案

---

## STATE

- **overall_status**: accepted_with_gaps
- **current_owner**: orchestrator
- **next_action**: closed — 後續追蹤：W9-T5/T6 real fixtures、heavy tool executor、主鏈/orchestrator 預設路徑整合（見 C_REPORT gaps）
- **last_updated**: 2026-06-15 · orchestrator
- **status_by_role**:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- **changed_files**:
  - `scripts/run_non_tabular_experiment_preview.py`（新增 preview orchestrator CLI）
  - `routing/intake_to_non_tabular_glue.py`（新增 glue planner）
  - `routing/non_tabular_routing_catalog_v1.yaml`（NT-A / NT-B routes）
  - `tools/non_tabular_tool_catalog_v1.json`（shadow tool catalog）
  - `tools/non_tabular_tool_selector_v1.py`（selector stub）
  - `docs/non-tabular-orchestrator-preview-v1.md`（新增）
  - `tests/test_non_tabular_orchestrator_preview_v1.py`（新增）
  - `04_Workflows/tickets/W9-T4-non-tabular-orchestrator-preview-v1_state.md`（本檔）
  - `04_Workflows/WORKFLOW_INDEX.md`（W9-T4 條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（W9-T4 行）

- **verification**:
  - `python -m unittest tests.test_non_tabular_orchestrator_preview_v1 -v` → **11 tests OK**
  - Reviewer 複驗 2026-06-15 · combined Wave 9 suite 35/35 OK

- **behavior_notes**:
  - preview-only；heavy tools 標記 `planned_only` / `execution=stub`
  - outbox 僅寫 `outbox/non_tabular_experiment/`
  - Tabular `*.py` 未修改

- **deferred_items**:
  - heavy tools 實際執行
  - 主鏈 / Agent 標準線整合
  - real docu-corp / log-analytics fixtures（W9-T5/T6）
  - optional metadata extraction 僅 allowlist stub

---

## C_REPORT

- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無
- **checks_summary**:
  - **AC-1 ✅**: NT-A / NT-B preview JSON structure + CLI subprocess（4 tests）
  - **AC-2 ✅**: 輸出含 decision / planned_route / planned_tools / risk notes
  - **AC-3 ✅**: sandbox outbox 路徑寫入（`test_outbox_path_written` · `test_outbox_includes_processing_summary`）
  - **AC-4 ✅**: 非 non_tabular task_type → blocked（`test_non_non_tabular_task_type_blocked`）
  - **AC-5 ✅**: unittest 11/11 · Tabular 主鏈檔案未改 · Reviewer 複驗 2026-06-15
- **risk_level**: low
- **gaps**:
  - preview-only · execution=stub
  - stub fixtures / allowlist metadata extraction
  - 不接主鏈 outbox / orchestrator 預設路徑
- **suggestions**: W9-T5/T6 real fixtures · W10-T1 CI helper 可選整合

---

## D_REPORT

- **docs_updates**: `docs/non-tabular-orchestrator-preview-v1.md` 已交付；Dashboard/Progress 註解留 Step 5
- **progress_entry**: W9-T4 implementer done → **accepted_with_gaps** — preview CLI + glue + sandbox outbox + 11/11 tests OK
- **followup_suggestions**: W9-T5/T6 fixtures · heavy tool executor · mainline 整合留後續票

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | scribe | W9-T4 Reviewer→Scribe 收口 · accepted_with_gaps · D_REPORT filled based on reviewer acceptance |
| 2026-06-15 | orchestrator | STATE 關票 · overall_status accepted_with_gaps · Dashboard/Progress 收口 |
