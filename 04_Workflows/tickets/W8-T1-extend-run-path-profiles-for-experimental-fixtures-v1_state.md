# W8-T1 · Extend Run Path Profiles for Experimental Fixtures v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 8 — Agent Standard Line Run Path Extension  
> **建立日期**: 2026-06-10  
> **狀態**: implementer done · Reviewer pending

---

## FRAME

### Goal
在維持 Wave 7 錨點案型（demo_phase / sampleco）行為穩定的前提下，為 W7-T1 實驗 fixture（additional_demo / sandbox_client）補上受控 `run_path_profile`：允許 C/D 在 `--mode run` 下執行至受控 stopping point，具 CP-A/B、output_guard 與止步 safeguard。

### Scope
- [x] `scripts/run_agent_standard_case_experiment.py` — C/D `_RUN_PATH_PROFILES`
- [x] `scripts/run_agent_standard_case_regression.py` — `run-all-allowed` 含 C/D run + `experimental_run` summary
- [x] `docs/agent-run-experiment-eval-guide-v1.md` §2.5 + CLI
- [x] `docs/agent-standard-line-v1-summary.md` §2.1 run coverage
- [x] `docs/skill-cards-v2.md` · `docs/skill-map-v2.md` — C/D maturity
- [x] unittest 擴充
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD

### NonScope
- 不改主鏈 / UI / Gov / `run_mvp_mainline_regression.py`
- 不更動 demo_phase / sampleco run path 邊界
- 不改 W5-T1 production decision allowlist

### BlockedPaths（未修改）
- `scripts/run_mvp_mainline_regression.py`
- `scripts/new_cleaning_case.py`
- `app/local_ui.py`
- `routing/intake_decision_rules_v1.py`

---

## STATE

```yaml
overall_status: implementer_done
current_owner: reviewer
last_updated: 2026-06-10

status_by_role:
  orchestrator: done
  implementer: done
  reviewer: pending
  scribe: pending
```

---

## B_REPORT（Implementer）

### run_path_profile 摘要（四 fixture）

| case_ref | stop_at | tools | experimental |
|----------|---------|-------|--------------|
| `demo_phase` | `bundle` | gate → clean → bundle | no |
| `sampleco/2026-0001` | `checkpoint_b` | gate → clean | no |
| `additional_demo` | `checkpoint_b` | gate → clean (force) | **yes** |
| `sandbox_client` | `cleaning_preview` | gate only | **yes** |

### changed_files
- `scripts/run_agent_standard_case_experiment.py`
- `scripts/run_agent_standard_case_regression.py`
- `tests/test_agent_standard_case_experiment.py`
- `tests/test_agent_standard_case_regression.py`
- `docs/agent-run-experiment-eval-guide-v1.md`
- `docs/agent-standard-line-v1-summary.md`
- `docs/skill-cards-v2.md`
- `docs/skill-map-v2.md`
- `04_Workflows/WORKFLOW_INDEX.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md`
- `04_Workflows/tickets/W8-T1-extend-run-path-profiles-for-experimental-fixtures-v1_state.md`（本檔）

### verification
```bash
python -m unittest tests.test_agent_standard_case_experiment -v
python -m unittest tests.test_agent_standard_case_regression -v
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --include-extended-fixtures --auto-approve-intake --format json
```

### behavior_notes
- demo_phase / sampleco profile 與 W7-T2 一致（未改數值）
- sandbox `cleaning_preview`：mock output_guard · CP-B 不評估
- regression summary 新增 `experimental_run` · `run_path_stop_at`

---

## C_REPORT (Reviewer)

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **FRAME/Scope ✅**: 唯讀 spot-check `scripts/run_agent_standard_case_experiment.py` — `additional_demo`/`sandbox_client` profile 含 `experimental` 標記；`demo_phase`/`sampleco` 錨點 profile 未改數值
  - **BlockedPaths ✅**: `test_does_not_modify_mainline_regression_script` · `test_module_does_not_import_forbidden_modules` 通過
  - **AC run path ✅**: `test_run_all_allowed_extended_fixtures_experimental_run` · sandbox `cleaning_preview` / additional_demo `checkpoint_b` 止步測試通過
  - **unittest ✅**: 2026-06-15 複驗 `python -m unittest tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression -v` → **33/33 OK**
- risk_level: low
- suggestions:
  - deferred：`.github/workflows/*` nightly `run-all-allowed --include-extended-fixtures` 排程留 W10-T1/WB-T4 follow-up
  - deferred：`sandbox_client` live guard 與 W11-T1/W12-T1 升格路徑由後續票承接（本票僅 experimental run profile）

---

*W8-T1 · extend-run-path-profiles-for-experimental-fixtures-v1 · 2026-06-10*
