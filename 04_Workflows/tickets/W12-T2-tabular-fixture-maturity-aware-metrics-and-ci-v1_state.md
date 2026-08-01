# W12-T2 · Tabular Fixture Maturity Aware Metrics & CI v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 12 — Fixture maturity observability  
> **建立日期**: 2026-06-10  
> **狀態**: implementer done · Reviewer pending

---

## FRAME

### Goal
在不改現有 `metrics_summary.json` schema 的前提下，讓 Tabular Agent 線 metrics / CI / 月度報表能按 fixture maturity tier 聚合，Reviewer 可快速分辨 stable vs controlled_experimental regression。

### Scope
- [x] `scripts/analyze_agent_lines_metrics.py` — `by_fixture_maturity` + per-run `fixture_maturity`
- [x] `scripts/run_agent_lines_ci_suite.py` — case 欄位 + text 聚合
- [x] `scripts/generate_agent_lines_monthly_report.py` — tier 表格
- [x] unittest 擴充（有/無 fixture_maturity fallback）
- [x] metrics / CI 文檔更新
- [x] 本票 state

### NonScope
- 不改 `metrics_summary.json` 既有欄位語意
- 不增加外部系統依賴
- 不改 regression / experiment 寫入邏輯

### AllowedPaths
- `scripts/analyze_agent_lines_metrics.py`
- `scripts/run_agent_lines_ci_suite.py`
- `scripts/generate_agent_lines_monthly_report.py`
- `tests/test_analyze_agent_lines_metrics_v1.py`
- `tests/test_agent_lines_ci_suite_v1.py`
- `tests/test_generate_agent_lines_monthly_report_v1.py`
- `docs/agent-lines-metrics-and-monitoring-v1.md`
- `docs/agent-lines-ci-suite-v1.md`
- `04_Workflows/WORKFLOW_INDEX.md`

### BlockedPaths（未修改）
- `scripts/run_agent_standard_case_regression.py`
- `scripts/run_agent_standard_case_experiment.py`
- `scripts/run_mvp_mainline_regression.py`

### Dependencies
- W10-T1 CI suite
- W10-T2 metrics extractor
- W11-T1 fixture maturity 定義
- W11-T3 monthly report

### AcceptanceCriteria
- [AC-1] `metrics_summary.json` 新增 `by_fixture_maturity`（向後兼容）
- [AC-2] CI summary 每個 tabular case 含 `fixture_maturity`；text 模式有 tier 聚合
- [AC-3] monthly report 含 tier 表格
- [AC-4] 無 fixture_maturity 舊資料平滑退化（case_ref lookup 或 `unknown`）
- [AC-5] unittest 全綠

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

### changed_files
- `scripts/analyze_agent_lines_metrics.py`
- `scripts/run_agent_lines_ci_suite.py`
- `scripts/generate_agent_lines_monthly_report.py`
- `tests/test_analyze_agent_lines_metrics_v1.py`
- `tests/test_agent_lines_ci_suite_v1.py`
- `tests/test_generate_agent_lines_monthly_report_v1.py`
- `docs/agent-lines-metrics-and-monitoring-v1.md`
- `docs/agent-lines-ci-suite-v1.md`
- `04_Workflows/WORKFLOW_INDEX.md`
- `04_Workflows/tickets/W12-T2-tabular-fixture-maturity-aware-metrics-and-ci-v1_state.md`（本檔）

### behavior_notes
- Tabular runs only：`by_fixture_maturity` 不含 non-tabular preview。
- 舊 artifact 無 `fixture_maturity` 時，metrics 透過 `get_fixture_maturity(case_ref)` 解析；monthly report 缺欄位時歸 `unknown`。
- `schema_version` 維持 `agent_lines_metrics_v1`（additive section）。

### verification
```bash
python -m unittest tests.test_analyze_agent_lines_metrics_v1 tests.test_agent_lines_ci_suite_v1 tests.test_generate_agent_lines_monthly_report_v1 -v
# 24 tests OK

python scripts/analyze_agent_lines_metrics.py --format text
# by_fixture_maturity: stable=8 · controlled_experimental=4 · unknown=1

python scripts/generate_agent_lines_monthly_report.py --month 2026-06
# monthly_report_2026-06.md includes tier rollup table
```

### deferred_items
- 無
