# TICKET STATE · W10-T1 · integrate-agent-lines-into-ci-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- **Goal**: 在不改主鏈 existing regression 的前提下，為 Tabular Agent Standard Line 與 Non-Tabular Experiment Preview 新增可選 CI 入口；合併 JSON 報告供 Reviewer / SRE 追蹤。

- **Scope**:
  1. `scripts/run_agent_lines_ci_suite.py`（`--scope` · `--format` · merged `outbox/agent_ci/` summary）
  2. Tabular scope → `run_agent_standard_case_regression.py`（`run-all-allowed` + `auto-approve-intake`）
  3. Non-tabular scope → `run_non_tabular_experiment_preview.py`（NT-A / NT-B stubs）
  4. `tests/test_agent_lines_ci_suite_v1.py`
  5. `docs/agent-lines-ci-suite-v1.md`
  6. WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引更新
  7. NT stub fixtures（`cases/_experiment_samples/nt_docu_stub` · `nt_log_stub`）— 文檔已引用、CI 執行前置

- **NonScope**:
  - ❌ 不改 `scripts/run_mvp_mainline_regression.py` 行為邏輯
  - ❌ 不改主鏈 E2E / UI / Gov Core smoke
  - ❌ 不將本 helper 強制併入既有 mainline regression unittest
  - ❌ 不執行 non-tabular heavy tools

- **AllowedPaths**:
  - `scripts/run_agent_lines_ci_suite.py`
  - `tests/test_agent_lines_ci_suite_v1.py`
  - `docs/agent-lines-ci-suite-v1.md`
  - `cases/_experiment_samples/nt_docu_stub/intake.json`
  - `cases/_experiment_samples/nt_log_stub/intake.json`
  - `04_Workflows/tickets/W10-T1-integrate-agent-lines-into-ci-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`

- **AcceptanceCriteria**:
  - [AC-1] `--scope tabular|non_tabular|all` 可選執行
  - [AC-2] 合併 JSON 寫入 `outbox/agent_ci/<timestamp>_ci_summary.json`
  - [AC-3] Tabular 使用 `run-all-allowed` + `auto-approve-intake`
  - [AC-4] Non-tabular 對 NT-A/NT-B stub 執行 preview
  - [AC-5] unittest 全綠；未改 mainline regression / UI / Gov

---

## STATE

- **overall_status**: implementer_done
- **current_owner**: implementer
- **next_action**: Reviewer 審查 CI helper 與 unittest
- **last_updated**: 2026-06-10 · Implementer
- **status_by_role**:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

### 初始實作（2026-06-10）

- **changed_files**:
  - `scripts/run_agent_lines_ci_suite.py`（新增）
  - `tests/test_agent_lines_ci_suite_v1.py`（新增）
  - `docs/agent-lines-ci-suite-v1.md`（新增）
  - `cases/_experiment_samples/nt_docu_stub/intake.json`（新增 stub）
  - `cases/_experiment_samples/nt_log_stub/intake.json`（新增 stub）
  - `04_Workflows/tickets/W10-T1-integrate-agent-lines-into-ci-v1_state.md`（本檔）
  - `04_Workflows/WORKFLOW_INDEX.md`（W10-T1 條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 10 區塊）

- **verification**:
  - `python -m unittest tests.test_agent_lines_ci_suite_v1 -v`
  - `python scripts/run_agent_lines_ci_suite.py --scope all --format json`

- **behavior_notes**:
  - optional CI helper；主鏈 regression 未修改
  - tabular outbox → `outbox/agent_experiment_regression/`；NT → `outbox/non_tabular_experiment/`；merged → `outbox/agent_ci/`

### Follow-up: NT fixtures 升格 real（2026-06-15）

**Goal**: 將 NT-A/NT-B 從 stub 改為使用 W9-T5/T6 真實 fixtures，保留 stub 作為本地開發 fallback。

- **changed_files**:
  - `scripts/run_agent_lines_ci_suite.py`：
    - 新增 `_NT_REAL_FIXTURES`（指向 `cases/docu-corp/2026-0001`、`cases/log-analytics-co/2026-0001`）
    - 保留 `_NT_STUB_FIXTURES`（指向 `cases/_experiment_samples/nt_*_stub`）
    - 新增 `_get_nt_fixtures()` 函數：依環境變數 `AGENT_LINES_CI_USE_STUB_FIXTURES=1` 決定使用 stub
    - `run_non_tabular_ci_scope` 回傳新增 `fixture_source` 欄位（"real" 或 "stub"）
  - `tests/test_agent_lines_ci_suite_v1.py`：
    - 新增 `test_scope_non_tabular_uses_real_fixtures_by_default`：驗證默認使用 real fixtures
    - 新增 `test_scope_non_tabular_stub_fallback_via_env`：驗證環境變數切換到 stub
    - 更新 `test_scope_all_merged_summary`：驗證 `fixture_source` 欄位
  - `04_Workflows/tickets/W10-T1-integrate-agent-lines-into-ci-v1_state.md`（本檔 B_REPORT 追加）

- **verification**:
  - `python -m unittest tests.test_agent_lines_ci_suite_v1 -v` → **10/10 passed**
  - `python scripts/run_agent_lines_ci_suite.py --scope non_tabular --format json` → `fixture_source: "real"`, `case_dir` 指向 `cases/docu-corp/2026-0001` 與 `cases/log-analytics-co/2026-0001`，皆 `ok: true`
  - `AGENT_LINES_CI_USE_STUB_FIXTURES=1 python scripts/run_agent_lines_ci_suite.py --scope non_tabular --format json` → `fixture_source: "stub"`, `fixture_id` 為 `NT-A-stub`/`NT-B-stub`

- **behavior_notes**:
  - **默認行為**：NT-A 使用 `cases/docu-corp/2026-0001`（W9-T5）、NT-B 使用 `cases/log-analytics-co/2026-0001`（W9-T6）
  - **Fallback 機制**：設置 `AGENT_LINES_CI_USE_STUB_FIXTURES=1` 可切回 stub（本地開發或 CI 隔離模式）
  - **Tabular 無變化**：`run_tabular_ci_scope` 與相關測試完全未改動
  - **輸出結構穩定**：僅新增 `fixture_source` 欄位，不影響既有 `fixtures` / `summary` / `ok` 結構

- **deferred_items**:
  - 未對更多 NT fixtures 做擴展（僅支援 NT-A/NT-B）
  - stub fixtures 仍保留未刪除（後續可開 W9-T8 票 deprecate）
  - 未在 CI workflow 中強制使用 real fixtures（尚書省可視需要調整 `.github/workflows/*`）

---

## C_REPORT

- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無
- **checks_summary**:
  - **AC-1 scope ✅**: `--scope tabular|non_tabular|all` 由 unittest 覆蓋（10 tests）
  - **AC-2 merged JSON ✅**: `run_agent_lines_ci_suite.py` 寫入 `outbox/agent_ci/`；`test_scope_all_merged_summary` 通過
  - **AC-3 tabular ✅**: tabular scope 委派 `run-all-allowed` + `auto-approve-intake`（B_REPORT 與 regression tests 交叉驗證）
  - **AC-4 non-tabular ✅**: 2026-06-15 複驗 `python scripts/run_agent_lines_ci_suite.py --scope non_tabular --format json` → `ok: true` · `fixture_source: real` · NT-A/NT-B 指向 W9-T5/T6 fixtures
  - **AC-5 mainline 隔離 ✅**: `run_mvp_mainline_regression.py` 未改；`test_agent_lines_ci_suite_v1` → **10/10 OK**
  - **Follow-up 升格 ✅**: `AGENT_LINES_CI_USE_STUB_FIXTURES=1` stub fallback 有專測 `test_scope_non_tabular_stub_fallback_via_env`
- **risk_level**: low
- **suggestions**:
  - deferred：`.github/workflows/*` 尚未強制納入 `run_agent_lines_ci_suite`（B_REPORT 已標；建議 WB-T4 或尚書省 CI 票排程 `--scope all`）
  - deferred：stub fixtures 保留未刪 — 建議 W9-T8 或文檔票標記 deprecate 時機
  - deferred：僅 NT-A/NT-B；更多 NT fixture 擴展留 W9 線 follow-up

---

## D_REPORT

- **docs_updates**: pending

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | implementer (follow-up) | NT fixtures 升格：默認使用 W9-T5/T6 real fixtures (`cases/docu-corp/2026-0001`, `cases/log-analytics-co/2026-0001`)，保留 stub 為 `AGENT_LINES_CI_USE_STUB_FIXTURES=1` fallback；10/10 tests OK |
