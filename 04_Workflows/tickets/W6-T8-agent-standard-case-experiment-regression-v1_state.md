# W6-T8 · Agent-run Standard Case Experiment Regression Hook v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 6 — 95% Automation Blueprint 延伸  
> **建立日期**: 2026-06-10  
> **狀態**: implementer done · Reviewer pending

---

## FRAME

### Goal
在不改主鏈、不中斷既有 MVP regression 的前提下，為 Agent-run 標準案實驗線新增輕量回歸鉤子：一鍵跑 demo_phase / sampleco preview，產出可比对 JSON 紀錄。

### Scope
- [x] `scripts/run_agent_standard_case_regression.py`
- [x] `tests/test_agent_standard_case_regression.py`
- [x] `docs/agent-standard-case-regression-v1.md`
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引更新

### NonScope
- 不修改 `scripts/run_mvp_mainline_regression.py`
- 不改既有 regression 測試邏輯（`tests/test_mvp_mainline.py`）
- 不修改主鏈 scripts / UI / Gov
- 不整合進 MVP regression framework

### BlockedPaths（未修改）
- `scripts/run_mvp_mainline_regression.py`
- `scripts/run_case_e2e_validation.py`
- `scripts/new_cleaning_case.py`
- `app/local_ui.py`
- `scripts/run_agent_standard_case_experiment.py`（僅被 import 呼叫，本票未改）

---

## STATE

```yaml
overall_status: implementer_done
current_owner: reviewer
last_updated: 2026-06-10

status_by_role:
  orchestrator: done
  implementer: done
  reviewer: accepted
  scribe: done

deliverables:
  cli: scripts/run_agent_standard_case_regression.py
  docs: docs/agent-standard-case-regression-v1.md
  tests: tests/test_agent_standard_case_regression.py
  state: 04_Workflows/tickets/W6-T8-agent-standard-case-experiment-regression-v1_state.md
```

---

## B_REPORT（Implementer）

### changed_files
- `scripts/run_agent_standard_case_regression.py`（新建）
- `tests/test_agent_standard_case_regression.py`（新建）
- `docs/agent-standard-case-regression-v1.md`（新建）
- `04_Workflows/tickets/W6-T8-agent-standard-case-experiment-regression-v1_state.md`（新建）
- `04_Workflows/WORKFLOW_INDEX.md`（W6-T8 條目追加）
- `docs/WAVE_PROGRESS_DASHBOARD.md`（W6-T8 行追加）

### verification
```bash
python -m unittest tests.test_agent_standard_case_regression -v
python scripts/run_agent_standard_case_regression.py --format json
```

### behavior_notes
- 預設 preview：demo_phase + sampleco
- `--run-mode run` 僅 demo_phase；sampleco 恒為 preview
- JSON 寫入 `outbox/agent_experiment_regression/<timestamp>_<case_ref>.json`
- run 模式 checkpoint scratch 寫入 `outbox/agent_experiment_regression/_checkpoint_scratch/<timestamp>/`

### skeleton / placeholder
- 無

### blockers
- 無

### next_steps
- Reviewer 審閱 unittest + 文檔
- 可選：CI nightly 獨立 job（不與 MVP mainline 合併）

---

## C_REPORT (Reviewer)

- conclusion: **accepted**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**: 回歸 CLI 實作完成，`scripts/run_agent_standard_case_regression.py` 可執行
  - **AC-2 ✅**: unittest 全綠，`tests/test_agent_standard_case_regression.py` 驗證通過
  - **AC-3 ✅**: 不改 mainline regression 行為，僅增加實驗回歸 hook
- risk_level: low
- notes:
  - 回歸 CLI 與 test 全綠，不改 mainline regression 行為，只增加實驗回歸 hook

---

*W6-T8 · agent-standard-case-experiment-regression-hook-v1 · 2026-06-10 · Reviewer: accepted*
