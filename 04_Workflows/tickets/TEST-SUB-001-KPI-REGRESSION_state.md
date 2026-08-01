# TICKET STATE · TEST-SUB-001-KPI-REGRESSION · KPI-only 路由回歸測

> **授權**：尚書省「全授權」A3 · 2026-07-29  
> **上游**：Cursor Subagents `TEST-SUB-001` accepted_with_gaps（建議補 KPI-only regression）

---

## FRAME

- Goal: 補一條僅含 KPI 關鍵字（無 `/monitoring/`、無 task_type／tags）的 ROUTE-MON-1 回歸測。
- Scope:
  - MUST：`tests/test_context_subagent_routing.py` 單測
- NonScope: 改 `context_routing.py` regex（已有 `\bkpi?s?\b`）· 暗部 · CI 默升
- AllowedPaths:
  - `tests/test_context_subagent_routing.py`
  - `04_Workflows/tickets/TEST-SUB-001-KPI-REGRESSION_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
- AcceptanceCriteria:
  - AC-1：`goal` 含 `KPI` 字樣 → `monitoring_subagent` + `ROUTE-MON-1`
  - AC-2：既有四測仍綠

---

## STATE

- **overall_status**: `done`
- **last_updated**: 2026-07-29T00:45+08:00
- **next_action**: closed

---

## B_REPORT

- changed_files: `tests/test_context_subagent_routing.py`
- verification: `python -m unittest tests.test_context_subagent_routing -v`
