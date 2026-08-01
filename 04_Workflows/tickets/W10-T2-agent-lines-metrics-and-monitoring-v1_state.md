# W10-T2 · Agent Lines Metrics & Monitoring v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 10 — Agent Lines Observability (offline)  
> **建立日期**: 2026-06-10  
> **狀態**: implementer done · Reviewer pending

---

## FRAME

### Goal
在現有 outbox / regression JSON 基礎上，為 Tabular Agent 標準線 + Non-tabular preview 增加離線指標抽取工具（CSV/JSON），不引入外部監控系統。

### Scope
- [x] `scripts/analyze_agent_lines_metrics.py`
- [x] `tests/test_analyze_agent_lines_metrics_v1.py`
- [x] `docs/agent-lines-metrics-and-monitoring-v1.md`
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引更新

### NonScope
- 不連接外部 DB / Prometheus / PG ingest
- 不改現有 outbox 寫入邏輯
- 不取代 W6-T7 eval guide 驗收門檻

### AllowedPaths
- `scripts/analyze_agent_lines_metrics.py`
- `tests/test_analyze_agent_lines_metrics_v1.py`
- `docs/agent-lines-metrics-and-monitoring-v1.md`
- `outbox/agent_metrics/`（輸出目錄）
- `04_Workflows/WORKFLOW_INDEX.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md`

### BlockedPaths（未修改）
- `scripts/run_agent_standard_case_regression.py`
- `scripts/run_non_tabular_experiment_preview.py`
- `scripts/run_mvp_mainline_regression.py`
- Observability / monitoring_service 暗部模組

### Dependencies
- W6-T8 regression artifacts（`outbox/agent_experiment_regression/`）
- W9-T4 non-tabular preview artifacts（`outbox/non_tabular_experiment/`）
- W10-T1 `docs/agent-lines-ci-suite-v1.md`（尚未交付；本票不依賴）

### AcceptanceCriteria
- [AC-1] CLI 掃描三個 outbox 目錄（缺失目錄優雅跳過）
- [AC-2] 輸出 `metrics_summary.json` + `metrics_summary.csv`
- [AC-3] 統計 error rate、CP-A/B 觸發率、duration（有 timestamp 時）
- [AC-4] unittest 以 fake outbox 驗證計數
- [AC-5] 文檔描述 schema 與用法
- [AC-6] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 已更新

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
- `scripts/analyze_agent_lines_metrics.py`（新建）
- `tests/test_analyze_agent_lines_metrics_v1.py`（新建）
- `docs/agent-lines-metrics-and-monitoring-v1.md`（新建）
- `04_Workflows/tickets/W10-T2-agent-lines-metrics-and-monitoring-v1_state.md`（新建）
- `04_Workflows/WORKFLOW_INDEX.md`（W10-T2 條目追加）
- `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 10 / W10-T2 行追加）

### verification
```bash
python -m unittest tests.test_analyze_agent_lines_metrics_v1 -v
python scripts/analyze_agent_lines_metrics.py
python scripts/analyze_agent_lines_metrics.py --format json
```

### behavior_notes
- 只讀本地 JSON；`_checkpoint_scratch` 目錄跳過
- `outbox/agent_ci/` 不存在時 `exists: false`，不報錯
- Non-tabular preview 不計 CP-A/B rate（per-run 欄位為 null）
- Duration：`written_at − regression_meta.timestamp`（或檔名前綴 timestamp）

### deferred_items
- W10-T1 agent-lines CI suite 整合（待 W10-T1 交付後可追加 scan root 規則）
- Per-run CSV export（v2 可選）

---

## C_REPORT

- conclusion: pending
- blocking_issues: 無（待 Reviewer）
- checks_summary: pending
- risk_level: low
- suggestions: 無

---

## D_REPORT

- docs_updates: 本票已交付 `docs/agent-lines-metrics-and-monitoring-v1.md`
- progress_entry: pending
- followup_suggestions: W10-T1 CI suite 完成後可將 CI outbox 納入 dashboard 範例
