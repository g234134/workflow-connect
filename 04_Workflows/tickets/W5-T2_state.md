# TICKET STATE · W5-T2 · Phase 8.5 Browser Automation MVP Runner

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 5 - Browser + Skill Distillation

---

## FRAME

- Title: Phase 8.5 Browser Automation MVP Runner
- Goal: browser_task 類 intake 可產出 DOM 步驟計畫並執行最小 dry-run，結果寫入 tool decision actuals。
- Scope:
  - 實作 browser_runner MVP：解析 browser_plan → dry-run 模擬
  - 對齊 PHASE8_5_BROWSER_AUTOMATION_MVP_v0.1.md
  - 接入 W3 run_tool_flow（executor_binding: browser_runner）
  - 測試用 mock DOM，不預設真瀏覽器
- NonScope:
  - Playwright 生產級穩定
  - 反爬／驗證碼
  - 並行多 tab
- AllowedPaths:
  - core/browser_runner.py
  - tests/test_browser_runner.py
  - 04_Workflows/PHASE8_5_BROWSER_AUTOMATION_MVP_v0.1.md（狀態更新）
- BlockedPaths:
  - AGENTS.md
  - 01_Environments/config/tools/cloakbrowser/**
- Dependencies:
  - W3-T3 executor actuals
  - W4-T1 intake gate
  - Phase 8.5 spec
- Risks:
  - 真瀏覽器依賴缺失 → 回退 dry-run 標 degraded
  - 非法 selector → 執行前校驗拒絕
- Observability:
  - logs: 每步 step_id、status
  - metrics: browser_steps_failed_total
  - traces: span browser_runner
- OutputArtifacts:
  - core/browser_runner.py
  - tests + fixture plans
  - Phase 8.5 spec 標 MVP delivered
- AcceptanceCriteria:
  - browser_task fixture → steps_planned ≥1，dry_run_ok: true
  - 失敗步驟寫入 structured_error_refs
  - Phase 7.5 request_type=browser_task 欄位校驗通過
  - unittest 全綠
- VerificationCommands:
  - `python -m unittest tests.test_browser_runner -v`
    - 預期：全綠

---

## STATE

- overall_status: draft
- current_owner: orchestrator
- next_action: Assign to Implementer — 依 B_REPORT Implementation Plan 開工
- last_updated: 2026-06-07 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: pending
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

> **C 區（Orchestrator 預填）**：Implementer 施工時更新下方欄位，保留 Implementation Plan 歷史。

### Implementation Plan (initial)

- [ ] 實作 browser_runner dry-run MVP
- [ ] 接入 run_tool_flow
- [ ] mock DOM tests
- [ ] 更新 Phase 8.5 spec 狀態

### Files To Touch

- core/browser_runner.py
- tests/test_browser_runner.py

- changed_files: <!-- Implementer 填 -->
- artifacts: <!-- Implementer 填 -->
- verification: <!-- Implementer 填：執行 VerificationCommands 結果 -->
- behavior_notes: <!-- Implementer 填 -->
- deferred_items: <!-- Implementer 填；無則「無」 -->

---

## C_REPORT

- conclusion: <!-- Reviewer 填：accepted | accepted_with_gaps | needs_changes | rejected -->
- blocking_issues: <!-- Reviewer 填；無則「無」 -->
- checks_summary: <!-- Reviewer 填：對照 FRAME 邊界與 AcceptanceCriteria -->
- risk_level: <!-- Reviewer 填：low | medium | high -->
- suggestions: <!-- Reviewer 填；無則「無」 -->

---

## D_REPORT

- docs_updates: <!-- Scribe 填 -->
- progress_entry: <!-- Scribe 填：建議寫入 Progress 末尾 1–3 句 -->
- followup_suggestions: <!-- Scribe 填；無則「無」 -->

---

## O_NOTES

> **O 區**：Orchestrator 維護 run log 與戰報連結；Observe / Operate 計畫。

### Observability Plan

- 預設 dry-run；真瀏覽器需另票

### Rollout / Ops Notes

- 預設 dry-run；真瀏覽器需另票

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
