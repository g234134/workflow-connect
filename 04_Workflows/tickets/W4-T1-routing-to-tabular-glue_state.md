# TICKET STATE · W4-T1 · Routing → Tabular Tool Layer Glue

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4-COORD · Tabular MVP · Routing ↔ Tool Layer 銜接層

---

## FRAME

- Title: W4-T1 · Routing → Tabular Tool Layer Glue
- Goal: 為 Tabular MVP 任務建立一層**純 mapping glue**，從 W2 的 `task_type` 映射到 W3-TL Selector `task_type` intent 與 `planned_tools` 計畫；預設只做「plan」，不改 E2E driver 行為。
- Scope:
  - 新增 `routing/intake_to_tabular_glue.py` → `plan_tabular_route(task_type, case_dir) -> dict`
  - 新增 `docs/routing-tool-layer-glue-v1.md` — 輸入／輸出、規則表、與 Selector 關係
  - 新增 `tests/test_routing_tabular_glue.py` — demo_phase / sampleco / unsupported task_type
  - v1 支援 Tabular 家族 `task_type`：`tabular.cleaning.mvp`、`tabular.cleaning.regression`（及 `tabular.intake.new_case` 若對齊 catalog）
  - 從 `case_dir` 只讀 `intake.json` / `cases/index.json` 推斷 fixture profile（demo_phase / sampleco）
  - Feature flag `TABULAR_ROUTING_GLUE_ENABLED`（預設 **0** / off）；本票**不**接入主鏈
- NonScope:
  - **不**實作通用 routing engine
  - **不**改主鏈 CLI（`run_case_e2e_validation.py`、`run_mvp_mainline_regression.py`）
  - **不**改 Gov routing（`config/routing_policy.yaml`、`_route_task.py`、`core/routing_policy_loader.py`）
  - **不**合併 Catalog 命名空間（Gov / Tabular / Product card 仍分軌）
  - **不**直接呼叫 Selector / Executor（只產 plan dict）
  - **不**改 `tools/tabular_tool_selector.py` / `tools/tabular_tool_executor.py`
- AllowedPaths:
  - `routing/intake_to_tabular_glue.py`
  - `docs/routing-tool-layer-glue-v1.md`
  - `tests/test_routing_tabular_glue.py`
  - `04_Workflows/tickets/W4-T1-routing-to-tabular-glue_state.md`
  - 唯讀引用：`routing/intake_routing_catalog_v1.yaml`、`tools/tabular_tool_catalog_v1.json`、`cases/index.json`、`cases/*/intake.json`
- BlockedPaths:
  - `scripts/run_case_e2e_validation.py`
  - `scripts/run_mvp_mainline_regression.py`
  - `tools/tabular_tool_selector.py`
  - `tools/tabular_tool_executor.py`
  - `config/routing_policy.yaml`
  - `core/routing_policy_loader.py`
  - `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md` · `AGENTS.md` · `.cursor/rules/*`
- Dependencies:
  - **W2-T1** · `routing/intake_routing_catalog_v1.yaml`
  - **W3-TL-T1** · `tools/tabular_tool_catalog_v1.json`
  - **W3-TL-T2** · Selector spec（對齊 `selector_task_type` 語意，本票不 import selector）
  - W1-T2 · `docs/mvp-standard-trace-path.md`
  - W1-T3B · `docs/mvp-mainline-regression.md`
- Risks:
  - W2 route `tool_ids` 與 W3 catalog 漂移 → glue 啟動時雙 catalog 校驗
  - 未知 case_dir → `ok: false` + message，不猜 tool
- Observability:
  - logs: N/A（純函式；未接主鏈）
  - metrics: N/A
  - traces: plan dict 欄位 `notes[]` 供人工審計
- OutputArtifacts:
  - `routing/intake_to_tabular_glue.py`
  - `docs/routing-tool-layer-glue-v1.md`
  - `tests/test_routing_tabular_glue.py`
- AcceptanceCriteria:
  - **AC-1**：`task_type=tabular.cleaning.mvp` + `cases/demo_phase` / `cases/sampleco/2026-0001` → plan dict 的 `planned_tools` 與 routing catalog + tabular tool catalog 一致
  - **AC-2**：glue 輸出之 `selector_task_type` + `planned_tools` 可對齊 `select_tabular_tools` 語意（gate_only / clean / bundle / e2e）；本票不呼叫 Selector
  - **AC-3**：Feature flag 關閉（預設）；主鏈 `python scripts/run_mvp_mainline_regression.py -v` 仍 6/6 OK
  - **AC-4**：未修改禁改檔案
  - **AC-5**：`python -m unittest tests.test_routing_tabular_glue -v` 全綠；覆蓋 demo_phase / sampleco / unsupported task_type
- VerificationCommands:
  - `python -m unittest tests.test_routing_tabular_glue -v`
    - 預期：全綠
  - `python scripts/run_mvp_mainline_regression.py -v`
    - 預期：6/6 OK，exit 0（主鏈守護）

---

## Minimal Read Set

| # | 路徑 | 用途 |
|---|------|------|
| 1 | `docs/mvp-standard-trace-path.md` | demo_phase trace / gate notes |
| 2 | `docs/mvp-mainline-regression.md` | mainline regression fixtures |
| 3 | `docs/intake-routing-catalog-v1.md` | W2 routing 語意 |
| 4 | `routing/intake_routing_catalog_v1.yaml` | route `tool_ids` SSOT |
| 5 | `docs/routing-eval-guide-v1.md` | eval 邊界（不實作 engine） |
| 6 | `routing/routing_eval_cases_v1.yaml` | eval cases 參照 |
| 7 | `docs/tabular-tool-catalog-v1.md` | Tabular tool SSOT |
| 8 | `tools/tabular_tool_catalog_v1.json` | tool_id 校驗 |
| 9 | `docs/tabular-tool-selector-spec.md` | selector_task_type 對齊 |
| 10 | `docs/tabular-tool-outbox-spec.md` | Executor 邊界（本票不碰） |
| 11 | `config/routing_policy.yaml` | Gov routing 邊界（唯讀） |
| 12 | `docs/ROUTING_POLICY_GUIDE.md` 或 `04_Workflows/TASK_ROUTING.md` | HQ 派工 vs 本 glue 區隔 |

---

## STATE

- overall_status: done
- current_owner: scribe
- next_action: W4-T2 可選將 plan 與 `select_tabular_tools` 實跑 cross-check；或 eval runner 消費 plan dict
- last_updated: 2026-06-10 · reviewer + scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

### 新增文件

| 路径 | 说明 |
|------|------|
| `routing/intake_to_tabular_glue.py` | `plan_tabular_route` 纯 mapping glue |
| `docs/routing-tool-layer-glue-v1.md` | glue spec v1 |
| `tests/test_routing_tabular_glue.py` | unittest（demo_phase / sampleco / unsupported） |
| `04_Workflows/tickets/W4-T1-routing-to-tabular-glue_state.md` | 本票 state |

### plan_tabular_route 样例

**demo_phase + tabular.cleaning.mvp**

```python
plan_tabular_route("tabular.cleaning.mvp", "cases/demo_phase")
# ok=True, selector_task_type="e2e",
# planned_tools=["validate.eligibility","clean.phase_demo","export.delivery_bundle"]
```

**sampleco + tabular.cleaning.mvp**

```python
plan_tabular_route("tabular.cleaning.mvp", "cases/sampleco/2026-0001")
# ok=True, notes 含 human_review_required / multi_row_export / schema_ambiguous
```

- changed_files:
  - `routing/intake_to_tabular_glue.py`
  - `docs/routing-tool-layer-glue-v1.md`
  - `tests/test_routing_tabular_glue.py`
  - `04_Workflows/tickets/W4-T1-routing-to-tabular-glue_state.md`
- artifacts: `docs/routing-tool-layer-glue-v1.md`
- verification:
  - `python -m unittest tests.test_routing_tabular_glue -v` → **9/9 OK**
  - `python scripts/run_mvp_mainline_regression.py -v` → **6/6 OK**, exit 0
- behavior_notes: Feature flag `TABULAR_ROUTING_GLUE_ENABLED` 默认 off；未接主链；禁改档未动
- deferred_items: W4-T2+ 可选将 plan 喂给 Selector/Executor；Local UI 展示 plan

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: **none**
- risk_level: **low**
- checks_summary:
  - **AC-1** ✅：`tabular.cleaning.mvp` + `cases/demo_phase`／`cases/sampleco/2026-0001` 之 `planned_tools` 與 `routing/intake_routing_catalog_v1.yaml` 該 route 的 `tool_ids` **完全一致**（`validate.eligibility` → `clean.phase_demo` → `export.delivery_bundle`），且三個 `tool_id` 均存在於 `tools/tabular_tool_catalog_v1.json` 且 `enabled=true`；`routing_catalog_tool_ids` 欄位可審計對照。
  - **AC-2** ✅：`selector_task_type=e2e` 對齊 Selector spec §1 intent；`inferred_gate_notes` 於 demo_phase（`phase_like`/`phase_demo`）與 sampleco（`multi_row_export`/`schema_ambiguous`）符合 selector 規則表 §3／§3.1；逐步 intent（gate_only／clean／bundle）見 glue spec §4 與 unittest 靜態對照，**未**與 Selector 行為衝突。
  - **AC-3** ✅：`TABULAR_ROUTING_GLUE_ENABLED` 預設 `0`（`TABULAR_ROUTING_GLUE_ENABLED=False`）；`python scripts/run_mvp_mainline_regression.py -v` → **6/6 OK**，exit 0。
  - **AC-4** ✅：禁改檔（`run_case_e2e_validation.py`、`run_mvp_mainline_regression.py`、`tabular_tool_selector.py`、`tabular_tool_executor.py`、`config/routing_policy.yaml`、`core/routing_policy_loader.py`）本票 diff 為空；glue 模組 AST 檢查無 forbidden import。
  - **AC-5** ✅：`python -m unittest tests.test_routing_tabular_glue -v` → **9/9 OK**；覆蓋 demo_phase、sampleco、`tabular.cleaning.regression`、unsupported `gov.observability.eval`、feature flag、planned_tools ⊆ routing catalog、selector step 對照。
- suggestions:
  - **G1**（AC-2／spec §4）：本票僅文檔＋靜態對照，**未**以 `select_tabular_tools(case_dir, selector_task_type, gate_notes=...)` 實跑 cross-check；建議 **W4-T2** 用 glue plan 餵 Selector 並比對 `candidate_tools`。
  - **G2**（Scope／AC-5）：`tabular.intake.new_case`（`selector_task_type=gate_only`）已在 glue 支援但 **無** 專項 unittest；後續可補一條或併入 W4-T2。
  - **G3**（spec §5）：`glue_enabled` 僅出現在 plan dict，主鏈 CLI 尚未消費；屬設計邊界，接線留待後續票。

---

## D_REPORT

- docs_updates:
  - 本票交付 spec：`docs/routing-tool-layer-glue-v1.md`（輸入／輸出、規則表、與 Selector 關係、驗證命令）。
  - 工作流索引：`04_Workflows/WORKFLOW_INDEX.md` §1.5／§1.6 增列 Wave 4 · W4-T1 glue 入口。
  - 進度 Dashboard：`docs/WAVE_PROGRESS_DASHBOARD.md` 新增 Wave 4 總覽與 W4-T1 票列。
- progress_entry:
  - **W4-T1 · Routing → Tabular Tool Layer Glue**（2026-06-10）— Reviewer **`accepted_with_gaps`**；交付 `routing/intake_to_tabular_glue.py`（`plan_tabular_route`）、`docs/routing-tool-layer-glue-v1.md`、`tests/test_routing_tabular_glue.py`（9/9）。用途：自 W2 `task_type`（如 `tabular.cleaning.mvp`）映射至 W3-TL `selector_task_type` 與 `planned_tools` 計畫 dict；**plan_only**，`TABULAR_ROUTING_GLUE_ENABLED` 預設 off，未改主鏈。邊界：不實作 routing engine、不呼叫 Selector／Executor、不動 Gov routing／Phase 8.8。驗證：glue unittest 9/9；主鏈回歸 6/6。Gaps：G1–G3 見 C_REPORT。
- followup_suggestions:
  - **W4-T2**：glue plan → `select_tabular_tools` 比對與 optional Executor outbox 鏈。
  - **W4-T3／T4**：eval runner 或 Local UI 展示 plan dict（`notes[]`／`inferred_gate_notes`）。
  - 可選補測：`tabular.intake.new_case` unittest（G2）。

---

## O_NOTES

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator | 依 Wave 4-COORD FRAME 开 W4-T1 glue 票 | 本档 |
| 2026-06-10 | implementer | 实作 glue + spec + tests 第一轮 | 本档 |
| 2026-06-10 | reviewer | AC-1〜AC-5 验收 → `accepted_with_gaps`（G1–G3） | 本档 C_REPORT |
| 2026-06-10 | scribe | 填 D_REPORT；更新 WORKFLOW_INDEX + WAVE_PROGRESS_DASHBOARD | 本档 |
