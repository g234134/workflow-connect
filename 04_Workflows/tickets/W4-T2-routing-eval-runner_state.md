# TICKET STATE · W4-T2 · Routing Eval Runner

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4-COORD · Tabular MVP · Routing eval automation

---

## FRAME

- Title: W4-T2 · Routing Eval Runner（consume `routing_eval_cases`）
- Goal: 新增本地 routing eval runner，讀 `routing_eval_cases_v1.yaml`，對每個 case 做 plan/對照，產出結構化報告；v1 不做 LLM 判分、不讀 Langfuse、不接 CI。
- Scope:
  - 新增 `scripts/run_routing_eval.py` — `--dry-run`（預設）、`--case-id`、`--execute`（可選）、`--format json|table`
  - 新增 `docs/routing-eval-runner-v1.md` — runner spec
  - 新增 `tests/test_routing_eval_runner.py` — dry-run 全案 + 錯誤 case + execute mock
  - Tabular case：透過 W4-T1 `plan_tabular_route` + tabular catalog 校驗
  - Gov case：透過 `core.routing_policy_loader` 只讀 resolve policy steps
- NonScope:
  - **不**改既有 router / skills / 主鏈 / `config/routing_policy.yaml`
  - **不**改 `tests/test_routing_eval_cases.py`
  - **不**改 `scripts/run_case_e2e_validation.py`、`scripts/run_mvp_mainline_regression.py`
  - **不**接 GitHub Actions / CI
  - **不**實作 LLM judge 或 Langfuse 解析
- AllowedPaths:
  - `scripts/run_routing_eval.py`
  - `docs/routing-eval-runner-v1.md`
  - `tests/test_routing_eval_runner.py`
  - `04_Workflows/tickets/W4-T2-routing-eval-runner_state.md`
  - 唯讀引用：`routing/*`、`tools/tabular_tool_catalog_v1.json`、`config/routing_policy.yaml`、`core/routing_policy_loader.py`
- BlockedPaths:
  - `scripts/run_case_e2e_validation.py`
  - `scripts/run_mvp_mainline_regression.py`
  - `tools/tabular_tool_selector.py` / `tools/tabular_tool_executor.py` / tabular outbox consumer
  - `config/routing_policy.yaml`
  - Gov routing 代碼（除只讀 import loader）
  - `tests/test_routing_eval_cases.py`
  - `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md` · `AGENTS.md` · `.cursor/rules/*`
- Dependencies:
  - **W2-T1** · intake routing catalog
  - **W2-T2** · routing eval cases YAML
  - **W3-TL-T1** · tabular tool catalog
  - **W4-T1** · `plan_tabular_route` glue
  - **B-F3** · `routing_policy_loader`（只讀）
- Risks:
  - cases / catalog 漂移 → runner 回 `mismatched_tools` + `ok: false`
  - `--execute` 誤用 → v1 僅 allowlist `tabular_mainline_regression`
- Observability:
  - logs: CLI stdout（json / table）
  - metrics: N/A
  - traces: per-case `notes[]`
- OutputArtifacts:
  - `scripts/run_routing_eval.py`
  - `docs/routing-eval-runner-v1.md`
  - `tests/test_routing_eval_runner.py`
- AcceptanceCriteria:
  - **AC-1**：`python scripts/run_routing_eval.py --dry-run` 對 YAML 全部 case 產生結果且不崩潰
  - **AC-2**：Tabular `planned_tools` ⊇ `expected_tool_ids`；Gov policy steps ⊇ `expected_tool_ids`
  - **AC-3**：未修改禁改 router / 主鏈 / Gov policy；runner 只讀檔案與 glue
  - **AC-4**：`python -m unittest tests.test_routing_eval_runner -v` 全綠
  - **AC-5**：`python scripts/run_mvp_mainline_regression.py -v` 仍 6/6 OK
- VerificationCommands:
  - `python scripts/run_routing_eval.py --dry-run --format json`
    - 預期：4/4 aligned，exit 0
  - `python -m unittest tests.test_routing_eval_runner -v`
    - 預期：全綠
  - `python scripts/run_mvp_mainline_regression.py -v`
    - 預期：6/6 OK，exit 0

---

## STATE

- overall_status: done
- current_owner: scribe
- next_action: W4-T3／T4 可選：Local UI 展示 eval 報告、CI 掛 dry-run（見 C_REPORT G1–G3）
- last_updated: 2026-06-10 · reviewer + scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `scripts/run_routing_eval.py`
  - `docs/routing-eval-runner-v1.md`
  - `tests/test_routing_eval_runner.py`
  - `04_Workflows/tickets/W4-T2-routing-eval-runner_state.md`
- artifacts: `docs/routing-eval-runner-v1.md`
- verification:
  - `python -m unittest tests.test_routing_eval_runner -v` → **12/12 OK**
  - `python scripts/run_routing_eval.py --dry-run --format json` → **4/4 aligned**, exit 0
  - `python scripts/run_mvp_mainline_regression.py -v` → **6/6 OK**, exit 0
- behavior_notes: 預設 `--dry-run`；`--execute` 僅 `tabular_mainline_regression` allowlist；Gov policy route 以 policy_route_id 對照，entrypoint 僅 note
- deferred_items: CI 接入、Langfuse trace diff、LLM judge

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: **none**
- risk_level: **low**
- checks_summary:
  - **AC-1** ✅：`python scripts/run_routing_eval.py --dry-run --format json` → **4/4 aligned**，exit 0；`run_eval(dry_run=True)` 對 YAML 全部 4 case 產生 per-case 結果；未知 `case_id`／缺失 route／缺 `case_dir` 路徑回 `ok: false` 不崩潰（unittest 覆蓋）。
  - **AC-2** ✅：Tabular cases 經 W4-T1 `plan_tabular_route` → `planned_tools` ⊇ `expected_tool_ids`（含 `tabular_demo_phase_clean`、`tabular_sampleco_e2e`、`tabular_mainline_regression`）；`expected_entrypoint` 與 intake catalog `entrypoint` 一致。Gov `gov_obs_eval_gate` 經只讀 `resolve_route_tool_ids(wave_b.eval_report)` → policy steps 覆蓋 `obs.eval.export`／`obs.eval.report`／`obs.wf.status_summary`；`optional_tool_ids` 缺失不判 fail。
  - **AC-3** ✅：預設 `--dry-run` 僅讀 catalog／glue／policy；未呼叫 Selector／Executor／HQ `_route_task`；`--execute` 僅 allowlist `tabular_mainline_regression` 且須顯式旗標（subprocess smoke 於 unittest mock 驗證）；禁改 router／skills／`routing_policy.yaml` 本票 diff 為空。
  - **AC-4** ✅：`python -m unittest tests.test_routing_eval_runner -v` → **12/12 OK**；覆蓋 dry-run 全案、Tabular／Gov 對齊、錯誤 case、execute mock、table／JSON 輸出、temp cases 路徑。
  - **AC-5** ✅：`python scripts/run_mvp_mainline_regression.py -v` → **6/6 OK**，exit 0（主鏈守護）。
- suggestions:
  - **G1**（NonScope）：dry-run 尚未接入 GitHub Actions／CI；建議 **W4-T4** 掛 `--dry-run` 為 Wave 4 eval gate。
  - **G2**（Scope 邊界）：`--execute` 僅 `tabular_mainline_regression` → `run_mvp_mainline_regression.py -v` smoke；未擴充其他 E2E allowlist 或 tool 層 execute。
  - **G3**（AC-2 延伸）：本 runner 對照 glue **plan** 層，**未**以 `select_tabular_tools` 實跑 cross-check `candidate_tools`；可留 W4-T3 或 Selector 整合票。
  - **G4**（NonScope）：LLM judge、Langfuse trace diff 未實作；cases 擴充留後續票。

---

## D_REPORT

- docs_updates:
  - 本票交付 spec：`docs/routing-eval-runner-v1.md`（CLI、case 類型、輸出 JSON、與 Wave 1–4 關係）。
  - 工作流索引：`04_Workflows/WORKFLOW_INDEX.md` §1.5／§1.6 增列 Wave 4 · W4-T2 eval runner 入口。
  - 進度 Dashboard：`docs/WAVE_PROGRESS_DASHBOARD.md` Wave 4 更新為 **2/4 done**（W4-T1 + W4-T2）。
- progress_entry:
  - **W4-T2 · Routing Eval Runner**（2026-06-10）— Reviewer **`accepted_with_gaps`**；交付 `scripts/run_routing_eval.py`、`docs/routing-eval-runner-v1.md`、`tests/test_routing_eval_runner.py`（12/12）。用途：消費 `routing/routing_eval_cases_v1.yaml`，自動對照 intake catalog、W4-T1 glue plan、Gov `routing_policy_loader` resolve，產出 dry-run 結構化報告（4/4 aligned）。邊界：不實作 routing engine、不做 LLM judge、不讀 Langfuse、不接 CI。驗證：runner unittest 12/12；dry-run CLI 4/4；主鏈回歸 6/6。Gaps：G1–G4 見 C_REPORT。
- followup_suggestions:
  - **W4-T4**：CI 接入 `python scripts/run_routing_eval.py --dry-run`。
  - **W4-T3**（Tabular MVP Wave 4 預留）：Local UI 或 E2E driver 展示 eval 報告／glue plan。
  - 可選：擴充 `routing_eval_cases_v1.yaml`；細化 `--execute` allowlist；`select_tabular_tools` 實跑比對（G3）。

---

## O_NOTES

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator | 開 W4-T2 routing eval runner 票 | 本檔 |
| 2026-06-10 | implementer | runner + spec + tests 第一輪 | 本檔 |
| 2026-06-10 | reviewer | AC-1〜AC-5 驗收 → `accepted_with_gaps`（G1–G4） | 本檔 C_REPORT |
| 2026-06-10 | scribe | 填 D_REPORT；更新 WORKFLOW_INDEX + WAVE_PROGRESS_DASHBOARD | 本檔 |
