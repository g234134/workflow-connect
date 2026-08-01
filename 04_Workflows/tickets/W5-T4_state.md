# TICKET STATE · W5-T4 · Phase 10.5 圖可對賬觀測（health → selector → retrieve|answer）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 5 - Browser + Skill Distillation

---

## FRAME

- Title: Phase 10.5 圖可對賬觀測（health → selector → retrieve|answer）
- Goal: ask 主線與 K-2/Tool Flow 節點決策可在單一觀測視圖對賬，支援自動化回歸與 skill 重用決策。
- Scope:
  - 擴充 eval export/ibridge：phase10_5_node_trace 欄位
  - 更新 workflow_upgrade/01_context-entry/A0_context_entry_overview.md §4.3
  - 對照 CLI：ibridge JSONL → phase10.5 對賬 Markdown
  - 與 W1 eval report 整合 Graph alignment 一節
- NonScope:
  - 改 Phase 10.5 路由表
  - L1/L2 monitoring graph 升格
  - K-2 prod canary
- AllowedPaths:
  - observability/eval_exporter.py
  - observability/phase10_5_reconcile.py
  - observability/eval_report.py
  - workflow_upgrade/01_context-entry/A0_context_entry_overview.md
  - tests/test_phase10_5_reconcile.py
- BlockedPaths:
  - AGENTS.md
  - core/monitoring_graph.py L1/L2
- Dependencies:
  - W1-T3 eval export
  - H-line context entry（已完成）
  - W3-T2 selector decision log
- Risks:
  - 舊 ibridge 無新欄位 → 對賬標 n/a 非崩潰
  - K-2 shadow 與 ask 主線並行 → 對賬僅主答案路徑
- Observability:
  - logs: 每節點 node、ok
  - metrics: phase10_5_skip_rag_rate
  - traces: ibridge + gov-trace 雙寫對齊
- OutputArtifacts:
  - eval export optional 欄位 + schema bump 文檔
  - observability/phase10_5_reconcile.py
  - artifacts/eval/phase10_5_reconcile.latest.md
  - 更新 A0 overview §4.3
- AcceptanceCriteria:
  - fixture ibridge 產出對賬表，四節點皆有 entered 布林
  - selector skip-RAG 場景 retrieve entered=false 可辨識
  - unittest 覆蓋 S1/S2/S3 場景
  - 不破壞既有 eval_export/v1 消費者（僅 optional 欄位）
- VerificationCommands:
  - `python -m unittest tests.test_phase10_5_reconcile -v`
    - 預期：全綠；S1/S2/S3
  - `python -m observability.phase10_5_reconcile ...`
    - 預期：產出 phase10_5_reconcile.latest.md

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

- [ ] 擴充 eval export optional phase10_5_node_trace
- [ ] 實作 phase10_5_reconcile CLI
- [ ] 更新 A0 overview §4.3
- [ ] eval report Graph alignment 一節
- [ ] tests S1/S2/S3

### Files To Touch

- observability/eval_exporter.py
- observability/phase10_5_reconcile.py
- workflow_upgrade/01_context-entry/A0_context_entry_overview.md
- tests/test_phase10_5_reconcile.py

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

- optional 欄位向後相容；K-2 shadow 不納入主對賬

### Rollout / Ops Notes

- optional 欄位向後相容；K-2 shadow 不納入主對賬

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
