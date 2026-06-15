# W7-T2 · Increase Agent Run Mode Coverage v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 7 — Agent-run 標準線 run 覆蓋擴大  
> **建立日期**: 2026-06-10  
> **狀態**: accepted_with_gaps · Orchestrator 關票

---

## FRAME

### Goal
在 Agent 標準線 v1 基礎上提高 `--mode run` 覆蓋率：demo_phase 為主要 run 實驗場；sampleco 在受控條件下可跑至 cleaning 並在 delivery 前停於 Checkpoint B；所有 run path 具 HITL / safeguard 與 outbox 記錄。

### Scope
- [x] `scripts/run_agent_standard_case_experiment.py` — preview/run 路徑分離 + per-case run_path_profile + 工具執行
- [x] `scripts/run_agent_standard_case_regression.py` — `--run-mode run-all-allowed`
- [x] `docs/agent-run-experiment-eval-guide-v1.md` — 擴大 run 覆蓋成功條件與命令
- [x] `tests/test_agent_standard_case_experiment.py` — demo_phase / sampleco run 測試
- [x] `tests/test_agent_standard_case_regression.py` — run-all-allowed 測試
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引

### NonScope
- 不改主鏈 / UI / Gov / 既有 E2E
- 不移除 preview 模式（仍為預設）
- 不對非 allowlist case 開 run 模式

### BlockedPaths（未修改）
- `scripts/run_mvp_mainline_regression.py`
- `scripts/run_case_e2e_validation.py`
- `scripts/new_cleaning_case.py`
- `app/local_ui.py`
- `core/routing_policy_loader.py`

---

## STATE

```yaml
overall_status: accepted_with_gaps
current_owner: orchestrator
next_action: closed — 後續追蹤：CI nightly run-all-allowed（W10-T1 helper 排程）、production v2 default run mode（需批文）、extended fixtures run 覆蓋（W8-T1；見 C_REPORT gaps）
last_updated: 2026-06-15 · orchestrator

status_by_role:
  orchestrator: done
  implementer: done
  reviewer: done
  scribe: done

deliverables:
  orchestrator: scripts/run_agent_standard_case_experiment.py
  regression: scripts/run_agent_standard_case_regression.py
  docs: docs/agent-run-experiment-eval-guide-v1.md
  tests:
    - tests/test_agent_standard_case_experiment.py
    - tests/test_agent_standard_case_regression.py
  state: 04_Workflows/tickets/W7-T2-increase-agent-run-mode-coverage-v1_state.md
```

---

## B_REPORT（Implementer）

### Implementation Plan

- [x] `_RUN_PATH_PROFILES` per-case stop_at / tools_to_run / stop_before_delivery（demo_phase · sampleco）
- [x] experiment CLI preview/run 路徑分離 + live tool execution + outbox 記錄
- [x] regression `--run-mode run-all-allowed` 映射 allowlist 全 run
- [x] eval guide §2.4 擴大 run 覆蓋成功條件與命令
- [x] unittest 覆蓋 demo_phase run-to-bundle · sampleco run-to-checkpoint_b · run-all-allowed regression
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引更新

### changed_files

| 路徑 | 變更摘要 |
|------|----------|
| `scripts/run_agent_standard_case_experiment.py` | `_RUN_PATH_PROFILES` · `get_run_path_profile` · run 路徑工具執行 · `_resolve_final_status` |
| `scripts/run_agent_standard_case_regression.py` | `--run-mode run-all-allowed` · `_resolve_case_mode` · per-case mode 映射 |
| `docs/agent-run-experiment-eval-guide-v1.md` | §2.4 擴大 run 覆蓋錨點案型與驗收條件 |
| `tests/test_agent_standard_case_experiment.py` | demo_phase / sampleco run 路徑與 CP-B 止步測試 |
| `tests/test_agent_standard_case_regression.py` | `run-all-allowed` · `run` 僅 demo_phase · outbox artifact 測試 |
| `04_Workflows/WORKFLOW_INDEX.md` | W7-T2 索引與 run-all-allowed 命令錨點 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Wave 7 進度與 W7-T2 deliverable 列舉 |

### run_path_profile 摘要

| case_ref | stop_at | tools_to_run | stop_before_delivery |
|----------|---------|--------------|----------------------|
| `demo_phase` | `bundle` | validate.eligibility → clean.phase_demo → export.delivery_bundle | no |
| `sampleco/2026-0001` | `checkpoint_b` | validate.eligibility → clean.phase_demo | yes |

### verification

**2026-06-15 · implementer 複驗**

| 命令 | 結果 |
|------|------|
| `python -m unittest tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression -v` | **OK** — 31 tests, 0 failures, ~5.4s |
| `python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --auto-approve-intake --format json` | **ok: true** — `summary.passed: 2/2` |

**regression CLI 關鍵欄位（20260615T045025Z）**

| case_ref | mode | final_status | checkpoint_b_status | run_path_stop_at |
|----------|------|--------------|---------------------|------------------|
| `demo_phase` | run | `waiting_for_human` | skipped | bundle |
| `sampleco/2026-0001` | run | `stopped_at_checkpoint_b` | stopped_before_delivery | checkpoint_b |

### behavior_notes

- **preview**：plan-only；mock output_guard；Checkpoint B planned；不寫 checkpoint state（預設）
- **run + auto-approve-intake**：依 `run_path_profile` 執行工具；live output_guard；Checkpoint B 整合層可寫 outbox
- **final_status**：`run_complete`、`stopped_at_checkpoint_b`、`waiting_for_human`（依 profile 與 guard 結果）
- **regression `--run-mode run`**：仍僅 `demo_phase` 進 run；其餘 preview
- **`--run-mode run-all-allowed`**：凡有 `run_path_profile` 的 allowlist case 皆 run（W7-T2 錨點：demo_phase + sampleco）
- **非 allowlist case**：run 模式亦 `blocked`；主鏈 / UI / Gov 未觸及

### deferred_items（非阻塞）

- CI nightly `run-all-allowed` job（W10-T1 helper 已存在；W7-T2 範圍外排程）
- production v2 default run mode（v2 設計見 W7-T4；尚無尚書省批文升格）
- extended fixtures（`additional_demo` / `sandbox_client`）run 覆蓋屬 W8-T1；本票僅錨點兩案

---

## C_REPORT (Reviewer)

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC run path 隔離 ✅**: `test_does_not_modify_mainline_regression_script` · `test_module_does_not_import_forbidden_modules` 全綠；BlockedPaths 未觸
  - **AC allowlist ✅**: 非 allowlist run 仍 blocked（experiment + regression tests）
  - **AC unittest ✅**: 2026-06-15 複驗 31/31 OK
  - **AC run-all-allowed ✅**: CLI `ok:true` · demo_phase `waiting_for_human` · sampleco `stopped_at_checkpoint_b`
- risk_level: low
- suggestions: CI nightly `run-all-allowed` 與 extended fixtures run 覆蓋留 deferred（非 blocking）

---

## D_REPORT (Scribe)

- docs_updates: 藍圖/run 覆蓋已索引於 `docs/agent-run-experiment-eval-guide-v1.md` §2.4；Wave docs 更新留 Orchestrator Step 5
- progress_entry: W7-T2 implementer_done → **accepted_with_gaps** — run path profile（demo_phase bundle · sampleco CP-B）+ `--run-mode run-all-allowed` + 31 tests OK
- followup_suggestions: W8-T1 extended fixtures run · W10-T1 CI nightly helper 排程

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | scribe | W7-T2 Reviewer→Scribe 收口 · accepted_with_gaps |
| 2026-06-15 | orchestrator | STATE 關票 · overall_status accepted_with_gaps · next_action deferred 索引 |
