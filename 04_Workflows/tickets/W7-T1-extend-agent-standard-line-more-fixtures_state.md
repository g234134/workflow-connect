# W7-T1 · Extend Agent Standard Line to More Tabular Fixtures v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 7 — Agent Standard Line Extension  
> **建立日期**: 2026-06-10  
> **狀態**: implementer done · Reviewer pending

---

## FRAME

### Goal
在保持現有 Agent 標準線 v1（`demo_phase` / `sampleco` 實驗線）穩定的前提下，將支援範圍擴展到更多 Tabular fixture（`additional_demo` / `sandbox_client`），並更新 Skill / 藍圖與 eval 規則。新增 fixture 標記為 **實驗線範圍**，不進 production contract。

### Scope
- [x] `cases/additional_demo/` · `cases/sandbox_client/` fixtures
- [x] `scripts/run_agent_standard_case_experiment.py` allowlist + mock profiles
- [x] `scripts/run_agent_standard_case_regression.py` `--include-extended-fixtures`
- [x] `docs/skill-cards-v1.md` Card C/D
- [x] `docs/agent-standard-line-v1-summary.md` Supported Cases
- [x] `docs/agent-run-experiment-eval-guide-v1.md` success matrix + CLI
- [x] `docs/ninety-five-percent-automation-blueprint-v1.md` allowlist note
- [x] `cases/index.json` experiment fixture entries
- [x] unittest updates
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD

### NonScope
- 不改主鏈 scripts / UI / Gov / `run_mvp_mainline_regression.py`
- 不改 W5-T1 production decision allowlist（`demo_phase` / `sampleco` only）
- 不改既有 `demo_phase` / `sampleco` orchestrator 行為

### BlockedPaths（未修改）
- `scripts/run_mvp_mainline_regression.py`
- `scripts/new_cleaning_case.py`
- `app/local_ui.py`
- `routing/intake_decision_rules_v1.py`（production allowlist 不變）

---

## STATE

```yaml
overall_status: implementer_done
current_owner: reviewer
last_updated: 2026-06-10

status_by_role:
  orchestrator: done
  implementer: done
  reviewer: accepted_with_gaps
  scribe: done

fixtures:
  - case_ref: additional_demo
    case_dir: cases/additional_demo
    scope: experiment_line_only
  - case_ref: sandbox_client
    case_dir: cases/sandbox_client
    scope: experiment_line_only
```

---

## B_REPORT（Implementer）

### changed_files
- `cases/additional_demo/`（intake.json, raw/Phase_extended.csv, delivery_signoff.md, cleaned/, reports/）
- `cases/sandbox_client/`（intake.json, raw/sandbox_milestone_export.csv, delivery_signoff.md, cleaned/, reports/）
- `cases/index.json`（experiment_fixture entries）
- `scripts/run_agent_standard_case_experiment.py`（allowlist, case_ref, gate/mock profiles）
- `scripts/run_agent_standard_case_regression.py`（`_EXTENDED_CASES`, `--include-extended-fixtures`）
- `tests/test_agent_standard_case_experiment.py`（+2 preview tests）
- `tests/test_agent_standard_case_regression.py`（+2 extended fixture tests）
- `docs/skill-cards-v1.md`（Card C/D）
- `docs/agent-standard-line-v1-summary.md`
- `docs/agent-run-experiment-eval-guide-v1.md`
- `docs/ninety-five-percent-automation-blueprint-v1.md`
- `04_Workflows/WORKFLOW_INDEX.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md`
- `04_Workflows/tickets/W7-T1-extend-agent-standard-line-more-fixtures_state.md`（本檔）

### verification
```bash
python -m unittest tests.test_agent_standard_case_experiment -v
python -m unittest tests.test_agent_standard_case_regression -v
```

### behavior_notes
- 預設 regression 仍僅 `demo_phase` + `sampleco`（向後相容）
- `--include-extended-fixtures` 追加 `additional_demo` + `sandbox_client`
- 新 fixture decision：`needs_review`（`unknown_fixture_profile`）；orchestrator allowlist 通過
- `demo_phase` / `sampleco` preview 輸出與 W6-T4/T8 一致（未改 mock profile 數值）

---

## C_REPORT (Reviewer)

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**: `additional_demo` / `sandbox_client` fixtures 已建立
  - **AC-2 ✅**: allowlist + mock profiles 已實作
  - **AC-3 ✅**: `--include-extended-fixtures` 選項正常運作
  - **AC-4 ✅**: unittest 更新完成，測試通過
- risk_level: low
- gaps:
  - extended fixtures C/D 已接入，決策邏輯經抽樣驗證
  - `experiment_line_only` 明確標記，不進 mainline
  - 未來 wave 可視需要增加更多 sample（非 blocking）
- suggestions:
  - 後續 Wave 可視實驗線穩定度，考慮將 C/D fixture 納入 production allowlist

---

*W7-T1 · extend-agent-standard-line-to-more-tabular-fixtures-v1 · 2026-06-10 · Reviewer: accepted_with_gaps*
