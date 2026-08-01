# TICKET STATE · W3-T3 · Tool Executor actual_* 回填與執行契約

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 - Tool Layer

---

## FRAME

- Title: Tool Executor actual_* 回填與執行契約
- Goal: 執行後回填 actual_tools_used、actual_latency_ms、actual_cost_usd、structured_error_refs，與計畫選擇可 diff。
- Scope:
  - 收口 run_tool_flow：select → append log → execute → patch actuals
  - 實作 core/tool_decision_log_patch.py
  - 對齊 tests.test_tool_executor、tests.test_minimal_orchestration_bridge_tool_flow
  - 更新 TOOL_LAYER_V1_RUNBOOK.md T6c 驗收命令
- NonScope:
  - 新 executor 類型（僅既有 binding）
  - 改 structured_errors schema version
  - file.io.read 非 stub 生產放行
- AllowedPaths:
  - core/tool_decision_log_patch.py
  - core/tool_executor.py
  - 04_Workflows/TOOL_LAYER_V1_RUNBOOK.md
  - tests/test_tool_executor.py
  - tests/test_minimal_orchestration_bridge_tool_flow.py
- BlockedPaths:
  - AGENTS.md
- Dependencies:
  - W3-T2 decision log
  - core/tool_executor.py、bridge 模組
  - Wave 3 structured_errors（既有）
- Risks:
  - 部分執行成功部分失敗 → actual_tools_used 為子集
  - stub executor 空 cost → 標 cost_level: unknown 非 0 冒充
- Observability:
  - logs: per-tool call_site、external_call_count
  - metrics: actual_cost_usd 加總
  - traces: executor span 掛於同一 decision_id
- OutputArtifacts:
  - core/tool_decision_log_patch.py
  - 更新 runbook + tests
  - patched JSONL fixture
- AcceptanceCriteria:
  - 端到端：選 llm.ask → mock 執行 → patched 列含 actual_*
  - planned_tools vs actual_tools_used diff 可輸出
  - 失敗路徑寫入 structured_error_refs，retryable 與 catalog 一致
- VerificationCommands:
  - `python -m unittest tests.test_tool_executor tests.test_minimal_orchestration_bridge_tool_flow -v`
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

- [ ] 收口 run_tool_flow 端到端
- [ ] 實作 tool_decision_log_patch
- [ ] 擴充 executor tests
- [ ] 更新 runbook T6c

### Files To Touch

- core/tool_decision_log_patch.py
- core/tool_executor.py
- 04_Workflows/TOOL_LAYER_V1_RUNBOOK.md
- tests/test_tool_executor.py

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

- actual_* 與 planned diff 納入 debug 輸出

### Rollout / Ops Notes

- actual_* 與 planned diff 納入 debug 輸出

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
