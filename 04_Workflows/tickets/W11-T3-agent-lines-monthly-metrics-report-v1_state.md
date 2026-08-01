# W11-T3 · Agent Lines Monthly Metrics Report v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 11 — Agent Lines Reporting (offline)  
> **建立日期**: 2026-06-10  
> **狀態**: implementer done · Reviewer pending

---

## FRAME

### Goal
在 W10-T2 `metrics_summary.json` 基礎上，新增離線月度 Markdown 報表工具，按月匯總 Tabular / Non-tabular 指標，方便人類閱讀。

### Scope
- [x] `scripts/generate_agent_lines_monthly_report.py`
- [x] `tests/test_generate_agent_lines_monthly_report_v1.py`
- [x] `docs/agent-lines-metrics-and-monitoring-v1.md`（月度報表章節）
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引更新

### NonScope
- 不發送任何通知 / email
- 不連接外部服務（PG / Prometheus / Langfuse 等）
- 不重新掃描 outbox（僅讀 `metrics_summary.json` / `runs[]`）
- 不改 W10-T2 extractor 或 outbox 寫入邏輯

### AllowedPaths
- `scripts/generate_agent_lines_monthly_report.py`
- `tests/test_generate_agent_lines_monthly_report_v1.py`
- `docs/agent-lines-metrics-and-monitoring-v1.md`
- `outbox/agent_metrics/monthly_report_*.md`（輸出）
- `04_Workflows/WORKFLOW_INDEX.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md`

### BlockedPaths（未修改）
- `scripts/analyze_agent_lines_metrics.py`（W10-T2；本票僅消費其輸出）
- Observability / monitoring_service 暗部模組
- 任何 notify / webhook / email 發送器

### Dependencies
- W10-T2 `metrics_summary.json` schema（`runs[]` per-run records）
- `docs/agent-standard-line-governance-view-v2.md`（審計路徑語意參考）

### AcceptanceCriteria
- [AC-1] CLI 讀取預設或指定 `metrics_summary.json`
- [AC-2] 按 `written_at` 月份聚合 total_runs / error_rate / CP-A/B rate / non-tabular preview 數
- [AC-3] 產出 `outbox/agent_metrics/monthly_report_YYYY-MM.md`
- [AC-4] unittest 以 fake summary 驗證 Markdown 內容與計數
- [AC-5] 文檔新增「月度報表」章節
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
- `scripts/generate_agent_lines_monthly_report.py`（新建）
- `tests/test_generate_agent_lines_monthly_report_v1.py`（新建）
- `docs/agent-lines-metrics-and-monitoring-v1.md`（§8 月度報表）
- `04_Workflows/tickets/W11-T3-agent-lines-monthly-metrics-report-v1_state.md`（新建）
- `04_Workflows/WORKFLOW_INDEX.md`（W11-T3 條目追加）
- `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 11 / W11-T3 行追加）

### verification
```bash
python -m unittest tests.test_generate_agent_lines_monthly_report_v1 -v
python scripts/generate_agent_lines_monthly_report.py --no-write --format json
```

### behavior_notes
- 僅讀 `metrics_summary.json`；無 `written_at` 的 run 跳過月度桶
- Tabular = `agent_experiment_regression` + `agent_ci`；Non-tabular = `non_tabular_experiment`
- CP-A/B rate 僅對 Tabular 有意義；報表 Non-tabular 欄顯示 `—`
- 不發通知、不連外部系統

### deferred_items
- 多月份合併單檔 PDF / HTML export（v2 可選）
- 與 W10-T1 CI suite 排程串接（需另票）

---

## C_REPORT

- conclusion: pending
- blocking_issues: 無（待 Reviewer）
- checks_summary: pending
- risk_level: low
- suggestions: 無

---

## D_REPORT

- docs_updates: 本票已更新 `docs/agent-lines-metrics-and-monitoring-v1.md` §8
- progress_entry: pending
- followup_suggestions: 可選排程：先跑 W10-T2 再跑 W11-T3 產月度報表
