# TICKET STATE · W4-T3-A · Intake · Tabular Tool Path（獨立 CLI · 預演）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4-COORD · Tabular MVP · Intake Tool Path 預演（版本 A · dry-run only）

---

## FRAME

- Title: W4-T3-A · Intake · Tabular Tool Path（獨立 CLI · 預演）
- Goal: 在 **不改** `new_cleaning_case` / Local UI / 主鏈 E2E 預設行為的前提下，新增獨立 CLI `scripts/run_tabular_intake_tool_path.py`，針對 Tabular family（`tabular.cleaning.mvp`、`tabular.cleaning.regression`、`tabular.intake.new_case`）與 allowlist fixture（`cases/demo_phase`、`cases/sampleco/2026-0001`），串接 W4-T1 glue → W3-TL Selector → Executor **plan**（`dry_run=True` 語意，不 spawn subprocess、不寫 outbox），輸出結構化 JSON「路徑預演」。
- Scope:
  - 新增 `scripts/run_tabular_intake_tool_path.py` — `--task-type` / `--case-dir` / `--json`
  - 新增 `docs/tabular-intake-tool-path-v1.md` — CLI 介面、JSON schema、與既有 flow 關係
  - 新增 `tests/test_tabular_intake_tool_path.py` — demo_phase / sampleco / unsupported / 無磁碟寫入
  - 更新 `04_Workflows/WORKFLOW_INDEX.md`、`docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 4 → 3/4 done 草稿）
- NonScope:
  - **不**改 `scripts/new_cleaning_case.py`
  - **不**改 `app/local_ui.py`
  - **不**改 `scripts/run_case_e2e_validation.py`、`scripts/run_mvp_mainline_regression.py`
  - **不**改 `tools/tabular_tool_selector.py`、`tools/tabular_tool_executor.py`
  - **不**改 `config/routing_policy.yaml` 及任一 Gov routing code（不 import `routing_policy_loader`）
  - **不**寫入 `outbox/` 實體檔、不更動 `cases/*/reports/*`
  - **不**改憲法 / ENGINEERING_CONTRACT / AGENTS / `.cursor/rules/*`
  - 版本 B（單步 execute / outbox）留待 W4-T3-B
- AllowedPaths:
  - `scripts/run_tabular_intake_tool_path.py`
  - `docs/tabular-intake-tool-path-v1.md`
  - `tests/test_tabular_intake_tool_path.py`
  - `04_Workflows/tickets/W4-T3-intake-tabular-tool-path_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（Wave 4 索引條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 4 狀態草稿）
  - 唯讀引用：`routing/intake_to_tabular_glue.py`、`tools/tabular_tool_selector.py`、`tools/tabular_tool_catalog_v1.json`、`routing/intake_routing_catalog_v1.yaml`
- BlockedPaths:
  - `scripts/new_cleaning_case.py`
  - `app/local_ui.py`
  - `scripts/run_case_e2e_validation.py`
  - `scripts/run_mvp_mainline_regression.py`
  - `tools/tabular_tool_selector.py`
  - `tools/tabular_tool_executor.py`
  - `config/routing_policy.yaml`
  - `core/routing_policy_loader.py`
  - `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md` · `AGENTS.md` · `.cursor/rules/*`
- Dependencies:
  - **W4-T1** · `routing/intake_to_tabular_glue.py` → `plan_tabular_route`
  - **W3-TL-T2** · `tools/tabular_tool_selector.py` → `select_tabular_tools`（唯讀呼叫）
  - **W3-TL-T1** · `tools/tabular_tool_catalog_v1.json`（planned_command / artifacts）
  - **W2-T1** · `routing/intake_routing_catalog_v1.yaml`
- Risks:
  - Selector per-step intent 與 glue `planned_tools` 漂移 → unittest 靜態對照 + notes
  - 誤觸 Executor 寫 outbox → 本票不 import executor；dry-run plan 本地組裝
- Observability:
  - stdout JSON / table；`notes[]` 供人工審計
- OutputArtifacts:
  - `scripts/run_tabular_intake_tool_path.py`
  - `docs/tabular-intake-tool-path-v1.md`
  - `tests/test_tabular_intake_tool_path.py`
- AcceptanceCriteria:
  - **AC-1**：`task_type=tabular.cleaning.mvp` + `case_dir=cases/demo_phase`，CLI dry-run 輸出 JSON 含 glue plan / selector candidates / planned command / expected artifacts
  - **AC-2**：不寫入 `outbox/` 實體檔，不修改 `cases/demo_phase` 或 `cases/sampleco/2026-0001` 任何檔案
  - **AC-3**：`tabular.cleaning.mvp` 以外 family（如 `gov.observability.eval`）→ `ok: false`, `message: unsupported_family`
  - **AC-4**：禁改檔案無 diff；CLI 不 import 政策 loader 或 Gov routing code
  - **AC-5**：`python -m unittest tests.test_tabular_intake_tool_path -v` 全綠；`run_mvp_mainline_regression.py -v` 仍 6/6 OK
- VerificationCommands:
  - `python -m unittest tests.test_tabular_intake_tool_path -v`
    - 預期：全綠
  - `python scripts/run_tabular_intake_tool_path.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json`
    - 預期：`ok: true`，含 `glue_plan` / `selector_view` / `executor_plan`
  - `python scripts/run_mvp_mainline_regression.py -v`
    - 預期：6/6 OK，exit 0

---

## Minimal Read Set

| # | 路徑 | 用途 |
|---|------|------|
| 1 | `docs/governance-constitution-v1.md` | 治理邊界 |
| 2 | `.cursor/rules/engineering-contract.mdc` | 工程合約 |
| 3 | `AGENTS.md` | 接戰紅線 |
| 4 | `docs/mvp-standard-trace-path.md` | demo_phase trace |
| 5 | `docs/mvp-mainline-regression.md` | 主鏈回歸 |
| 6 | `scripts/run_case_e2e_validation.py` | 主鏈邊界（唯讀） |
| 7 | `scripts/run_mvp_mainline_regression.py` | 主鏈守護（唯讀） |
| 8 | `docs/intake-routing-catalog-v1.md` | W2 routing |
| 9 | `routing/intake_routing_catalog_v1.yaml` | route SSOT |
| 10 | `docs/routing-eval-guide-v1.md` | eval 邊界 |
| 11 | `routing/routing_eval_cases_v1.yaml` | eval cases |
| 12 | `docs/tabular-tool-catalog-v1.md` | Tabular catalog |
| 13 | `tools/tabular_tool_catalog_v1.json` | tool_id / cli_invocation |
| 14 | `docs/tabular-tool-selector-spec.md` | Selector 語意 |
| 15 | `tools/tabular_tool_selector.py` | `select_tabular_tools`（唯讀呼叫） |
| 16 | `docs/tabular-tool-outbox-spec.md` | Executor 邊界 |
| 17 | `docs/tabular-outbox-consumer-spec.md` | outbox 邊界 |
| 18 | `docs/routing-tool-layer-glue-v1.md` | W4-T1 glue |
| 19 | `routing/intake_to_tabular_glue.py` | `plan_tabular_route` |
| 20 | `docs/routing-eval-runner-v1.md` | W4-T2 runner |
| 21 | `scripts/run_routing_eval.py` | eval CLI 模式參考 |
| 22 | `scripts/new_cleaning_case.py` | intake 現狀（唯讀） |
| 23 | `app/local_ui.py` | UI 現狀（唯讀） |

---

## STATE

- overall_status: done
- current_owner: scribe
- next_action: W4-T4 CI gate 或 W4-T3-B 單步 execute（可選）
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
| `scripts/run_tabular_intake_tool_path.py` | 独立 CLI dry-run 路径预演 |
| `docs/tabular-intake-tool-path-v1.md` | spec v1 |
| `tests/test_tabular_intake_tool_path.py` | unittest（8 tests） |
| `04_Workflows/tickets/W4-T3-intake-tabular-tool-path_state.md` | 本票 state |

### verification

- `python -m unittest tests.test_tabular_intake_tool_path -v` → **8/8 OK**
- `python scripts/run_tabular_intake_tool_path.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json` → **ok: true**，含 glue_plan / selector_view / executor_plan
- `python scripts/run_mvp_mainline_regression.py -v` → **6/6 OK**, exit 0

- changed_files:
  - `scripts/run_tabular_intake_tool_path.py`
  - `docs/tabular-intake-tool-path-v1.md`
  - `tests/test_tabular_intake_tool_path.py`
  - `04_Workflows/tickets/W4-T3-intake-tabular-tool-path_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- behavior_notes: 不 import Executor / Gov routing；不写 outbox；禁改档无 diff
- deferred_items: W4-T3-B 单步 execute / outbox；Local UI 展示 preview JSON

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: **none**
- risk_level: **low**
- checks_summary:
  - **AC-1** ✅：`tabular.cleaning.mvp` + `cases/demo_phase`／`cases/sampleco/2026-0001` CLI `--json` → `ok: true`；`glue_plan.planned_tools` 與 W4-T1 glue／W2 routing catalog 一致（`validate.eligibility` → `clean.phase_demo` → `export.delivery_bundle`）；`selector_view` 含 overall `candidates` 與 `per_step`（gate_only／clean／bundle intent）；`executor_plan[]` 每步 `dry_run: true`、`planned_command` 非空、`expected_artifacts` 結構合理；sampleco 額外驗證 `inferred_gate_notes` 與 `human_review_required`。
  - **AC-2** ✅：預設 `mode: dry_run_preview`；不 import Executor、不寫 `outbox/`；`test_no_disk_writes_to_case_or_outbox` 對 demo_phase／sampleco 樹狀 mtime 快照前後一致。
  - **AC-3** ✅：`gov.observability.eval` → `ok: false`、`message: unsupported_family`；subprocess CLI exit **0**（`test_unsupported_family_subprocess_exit_zero`）。
  - **AC-4** ✅：禁改檔（`new_cleaning_case.py`、`local_ui.py`、主鏈 runner、Selector／Executor、`routing_policy.yaml`、`routing_policy_loader`）本票 diff 為空；AST 檢查無 `routing_policy_loader`／`tabular_tool_executor`／`run_routing_eval` import。
  - **AC-5** ✅：`python -m unittest tests.test_tabular_intake_tool_path -v` → **8/8 OK**；`python scripts/run_mvp_mainline_regression.py -v` → **6/6 OK**，exit 0。
- suggestions:
  - **G1**（AC-5 延伸）：僅覆蓋 `tabular.cleaning.mvp`；`tabular.cleaning.regression`／`tabular.intake.new_case` 無專項 unittest（FRAME 列為支援 family）。
  - **G2**（AC-1 延伸）：`selector_view` 僅 assert `clean.phase_demo` ∈ candidates；未對全 `planned_tools` per_step 候選或 `selector_rule_id` 做更嚴格靜態對照。
  - **G3**（可移植性）：`planned_command` 以 `sys.executable` 展開為本機絕對路徑（Windows 實測 `C:\Python314\python.exe`）；審計 JSON 跨機器複製時路徑字串不同，屬 informational gap。
  - **G4**（維護）：`_EXPECTED_ARTIFACTS`／`_SELECTOR_INTENT_BY_TOOL` 在 CLI 本地複製，與 catalog／glue 漂移風險見 FRAME Risks；後續可併入 W4-T3-B 或 catalog 單一來源。

---

## D_REPORT

- docs_updates:
  - 本票交付 spec：`docs/tabular-intake-tool-path-v1.md`（CLI 介面、JSON schema、與既有 flow 關係）。
  - 工作流索引：`04_Workflows/WORKFLOW_INDEX.md` §1.5／§1.6 確認 Wave 4 · W4-T3-A intake tool path CLI 入口。
  - 進度 Dashboard：`docs/WAVE_PROGRESS_DASHBOARD.md` Wave 4 維持 **3/4 done**（W4-T3 Reviewer 收口）。
- deliverables_summary:
  - `scripts/run_tabular_intake_tool_path.py` — 獨立 CLI · dry-run 預演（glue → Selector → 本地 executor plan）。
  - `docs/tabular-intake-tool-path-v1.md` — CLI／JSON schema／與主鏈／eval runner 邊界。
  - `tests/test_tabular_intake_tool_path.py` — 8 tests（demo_phase、sampleco、unsupported family、禁 import、無磁碟寫入）。
- purpose:
  - Tabular family 任務（至少 `cases/demo_phase`、`cases/sampleco/2026-0001`）可在**不改** `new_cleaning_case`／Local UI／主鏈 E2E 的前提下，預演 W4-T1 glue + W3-TL Selector + executor 計畫，輸出可審計 JSON。
- boundaries:
  - 不寫 `outbox/`、不 spawn subprocess、不改 `cases/*/reports/*`。
  - 不掛進 intake／UI；不實作版本 B 單步 `execute_tabular_tool`。
- progress_entry:
  - **W4-T3-A · Intake Tabular Tool Path CLI**（2026-06-10）— Reviewer **`accepted_with_gaps`**；交付 `scripts/run_tabular_intake_tool_path.py`、`docs/tabular-intake-tool-path-v1.md`、`tests/test_tabular_intake_tool_path.py`（8/8）。用途：Tabular `task_type` + case_dir 路徑預演（glue → Selector → executor_plan）。邊界：dry-run only，不改主鏈。驗證：unittest 8/8；CLI demo_phase `ok: true`；主鏈回歸 6/6。Gaps：G1–G4 見 C_REPORT。
- followup_suggestions:
  - **W4-T3-B**：可選單步 `execute_tabular_tool(dry_run=False)` + outbox；Local UI 展示 preview JSON。
  - **W4-T4**：CI smoke 可掛 `run_tabular_intake_tool_path.py --json` on `cases/demo_phase`。
  - 可選補測：`tabular.cleaning.regression`／`tabular.intake.new_case`（G1）；強化 selector_view 靜態對照（G2）。

---

## O_NOTES

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator | 開 W4-T3-A intake tool path 票 | 本檔 |
| 2026-06-10 | implementer | CLI + spec + tests 第一輪 | 本檔 B_REPORT |
| 2026-06-10 | reviewer | AC-1〜AC-5 驗收 → `accepted_with_gaps`（G1–G4） | 本檔 C_REPORT |
| 2026-06-10 | scribe | 填 D_REPORT；更新 WORKFLOW_INDEX + WAVE_PROGRESS_DASHBOARD | 本檔 |
