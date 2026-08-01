# TICKET STATE · W3-T2 · Tool Selector + Decision Log（決策依據可審計）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 - Tool Layer

---

## FRAME

- Title: Tool Selector + Decision Log（決策依據可審計）
- Goal: select_tools() 產出 tool_decision_log_v1 列，含規則 ID、候選池、拒絕原因，並掛 Langfuse child span。
- Scope:
  - 實作/收口 core/tool_selector.py：select_tools(request) -> dict
  - 實作 core/tool_decision_log.py：append-only JSONL，decision_id 冪等
  - 寫入 task_runs.metadata.tool_decision_summary（摘要）
  - 對齊 04_Workflows/TOOL_LAYER_V1_RUNBOOK.md T4
- NonScope:
  - ML ranker
  - 改 retry/DLQ schema
  - prod 預設開啟（dev flag）
- AllowedPaths:
  - core/tool_selector.py
  - core/tool_decision_log.py
  - shared/schemas/tool_decision_log_v1.json
  - tests/test_tool_selector.py
  - tests/test_tool_decision_log.py
- BlockedPaths:
  - AGENTS.md
  - 暗部 ask_pipeline 預設路徑
- Dependencies:
  - W3-T1 catalog
  - Phase 7.5 GateScores 欄位（可選輸入）
  - Wave 1 monitoring metadata 路徑
- Risks:
  - request_type=other 無匹配 → 空選集 + human_review_required: true
  - risk_level=critical 且 ROI 低 → 規則拒絕須可解釋
- Observability:
  - logs: rule_id、rejected_tools[]
  - metrics: tool_decisions_total
  - traces: Langfuse span tool_selector；decision_id 入 trace metadata
- OutputArtifacts:
  - core/tool_selector.py、core/tool_decision_log.py
  - shared/schemas/tool_decision_log_v1.json
  - runtime/tool_decisions.jsonl（邏輯名樣本）
- AcceptanceCriteria:
  - 固定 fixture request → 穩定 selected_tools[] + rule_id
  - 重複 decision_id append 不重複寫
  - unittest test_tool_selector、test_tool_decision_log 全綠
  - 輸出 JSONL 列可通過 schema validate
- VerificationCommands:
  - `python -m unittest tests.test_tool_selector tests.test_tool_decision_log -v`
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

- [ ] 實作 select_tools 規則引擎
- [ ] 實作 append-only decision log + 冪等
- [ ] 寫 metadata 摘要 hook
- [ ] 對齊 runbook T4 + tests

### Files To Touch

- core/tool_selector.py
- core/tool_decision_log.py
- shared/schemas/tool_decision_log_v1.json
- tests/test_tool_selector.py
- tests/test_tool_decision_log.py

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

- dev flag 預設關；decision log 邏輯路徑見 Master_Map

### Rollout / Ops Notes

- dev flag 預設關；decision log 邏輯路徑見 Master_Map

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
