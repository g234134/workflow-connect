# TICKET STATE · OBS-GATE-1 · HTTP observability umbrella env

> **授權**：尚書省「全授權」A1 · 2026-07-29  
> **L0 only** · **≠** L1／L2 · **≠** selector／SLO gate

---

## FRAME

- Goal: 新增 `GOV_CORE_API_EXPOSE_OBSERVABILITY` umbrella env；舊雙閘門（MONITORING_GRAPH／IBRIDGE）仍相容；每 surface 仍須 query opt-in。
- Scope:
  - MUST：暗部 `app_api.py` umbrella + helper
  - MUST：`tests/test_app_api_observability_umbrella_expose.py`
  - MUST：runbook §6.7 一句更新 · `90_run_queue.md` OBS-GATE-1 狀態
- NonScope:
  - L1 shadow／L2 SLO · 合併為單一 query 參數（本票不做）
  - prod 預設開閘 · required CI
- AllowedPaths:
  - `01_Environments/python_venvs/gov_core_system/app_api.py`
  - `01_Environments/python_venvs/gov_core_system/tests/test_app_api_observability_umbrella_expose.py`
  - `workflow_upgrade/01_context-entry/50_context_entry_runbook.md`（§6.7 相關）
  - `workflow_upgrade/90_run_queue.md`（OBS-GATE-1 列）
  - `04_Workflows/tickets/OBS-GATE-1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
- BlockedPaths: 憲法 §7 · DarkOps · L1／L2 升格程式
- AcceptanceCriteria:
  - AC-1：umbrella=1 + 對應 query → 該 surface 暴露
  - AC-2：umbrella alone（無 query）→ 不暴露
  - AC-3：legacy per-surface env 仍綠

---

## STATE

- **overall_status**: `done`
- **current_owner**: closed
- **last_updated**: 2026-07-29T00:45+08:00
- **next_action**: closed · L0 only

---

## B_REPORT

- changed_files: 見 AllowedPaths 實作項
- verification: `python -m unittest tests.test_app_api_observability_umbrella_expose -v`（gov_core_system cwd）
- non_claims: ≠ L1／L2 · ≠ prod 默開
