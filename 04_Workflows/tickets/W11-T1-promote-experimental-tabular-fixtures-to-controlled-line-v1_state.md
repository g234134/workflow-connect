# W11-T1 · Promote Experimental Tabular Fixtures to Controlled Line v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 11 — Agent Standard Line Controlled Experimental Promotion  
> **建立日期**: 2026-06-10  
> **狀態**: implementer done · Reviewer pending

---

## FRAME

### Goal
在不改 demo_phase / sampleco 行為的前提下，將 C/D fixture（additional_demo / sandbox_client）從「純實驗」升格為「受控準正式線」`controlled_experimental`：C 允許 run 至 CP-B 前（cleaning+outbox）；D 允許 cleaning 完整 preview 與 live guard，保留保守 stop。

### Scope
- [x] `scripts/run_agent_standard_case_experiment.py` — maturity · D cleaning · `regression_bundle_probe`
- [x] `scripts/run_agent_standard_case_regression.py` — summary 欄位 · guard sanity
- [x] `docs/skill-cards-v2.md` · `docs/skill-map-v2.md` · `docs/ninety-five-percent-automation-blueprint-v2.md`
- [x] `docs/agent-standard-line-governance-view-v2.md` · `docs/agent-standard-line-v1-summary.md`
- [x] unittest 擴充
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD

### NonScope
- 不改 demo_phase / sampleco run_path 行為
- 不改主鏈 / UI / Gov / `run_mvp_mainline_regression.py`
- C/D 不標為 production fixture

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

### run_path / maturity 摘要（四 fixture）

| case_ref | stop_at | tools | maturity | W11-T1 增量 |
|----------|---------|-------|----------|------------|
| `demo_phase` | `bundle` | gate → clean → bundle | stable | 不變 |
| `sampleco/2026-0001` | `checkpoint_b` | gate → clean | stable | 不變 |
| `additional_demo` | `checkpoint_b` | gate → clean + outbox | **controlled_experimental** | regression `bundle_probe` |
| `sandbox_client` | `cleaning_preview` | gate → clean | **controlled_experimental** | live guard · CP-B 不評估 |

### changed_files
- `scripts/run_agent_standard_case_experiment.py`
- `scripts/run_agent_standard_case_regression.py`
- `tests/test_agent_standard_case_experiment.py`
- `tests/test_agent_standard_case_regression.py`
- `docs/skill-cards-v2.md`
- `docs/skill-map-v2.md`
- `docs/ninety-five-percent-automation-blueprint-v2.md`
- `docs/agent-standard-line-governance-view-v2.md`
- `docs/agent-standard-line-v1-summary.md`
- `04_Workflows/WORKFLOW_INDEX.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md`
- `04_Workflows/tickets/W11-T1-promote-experimental-tabular-fixtures-to-controlled-line-v1_state.md`（本檔）

### verification
```bash
python -m unittest tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression -v
# 27 tests OK

python scripts/run_agent_standard_case_regression.py \
  --run-mode run-all-allowed --include-extended-fixtures --auto-approve-intake --format json
# ok: true · C/D fixture_maturity=controlled_experimental
```

### anchor_unchanged
- demo_phase: `stop_at=bundle` · `fixture_maturity=stable` · unittest `test_demo_phase_run_mode_executes_to_bundle` 通過
- sampleco: `stop_at=checkpoint_b` · `fixture_maturity=stable` · unittest `test_sampleco_run_mode_stops_at_checkpoint_b` 通過

---

## C_REPORT (Reviewer)

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC maturity 升格 ✅**: spot-check `_RUN_PATH_PROFILES` — C/D `maturity=controlled_experimental`；`demo_phase`/`sampleco` 仍 `stable`
  - **AC anchor 不變 ✅**: `test_demo_phase_run_mode_executes_to_bundle` · `test_sampleco_run_mode_stops_at_checkpoint_b` 通過（含於 33-test suite）
  - **AC additional_demo ✅**: `regression_bundle_probe` 與 W11 增量一致；`test_run_all_allowed_extended_fixtures_experimental_run` 通過
  - **AC sandbox_client ✅**: `test_sandbox_client_run_mode_stops_at_cleaning_preview` · live guard · CP-B 不評估路徑通過
  - **unittest ✅**: 2026-06-15 複驗 experiment+regression → **33/33 OK**（B_REPORT 27 tests 基線已擴至含 W12 sandbox tests）
  - **docs ✅**: skill-cards/skill-map/blueprint/governance-view 變更列於 B_REPORT changed_files
- risk_level: low
- suggestions:
  - deferred：C/D 仍非 production fixture — W12-T2 maturity-aware CI metrics 應引用 `controlled_experimental` 標籤
  - deferred：`regression_bundle_probe` 僅測試用途；真實 sandbox e2e bundle 由 W12-T1 `--sandbox-end-to-end` 承接
