# TICKET STATE · W4-T1 · Phase 7.5 Intake Gate MVP（accept / defer / reject）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4 - Commercialization

---

## FRAME

- Title: Phase 7.5 Intake Gate MVP（accept / defer / reject）
- Goal: 通用 intake_schema_v1 進入啟發式 Gate，輸出結構化 GateScores 與 work_order_id 生命週期狀態。
- Scope:
  - 實作 intake_gate_scorer.py（或收口既有）：ROI / risk / cost 打分
  - CLI：驗證 intake JSON → gate_verdict + scores
  - 狀態機：auto_rejected | pending_review | accepted
  - 測試覆蓋 5 類 request_type 最小欄位
- NonScope:
  - ML 分類器
  - 與 Phase 7 成本帳本硬連動
  - 前端 UI
- AllowedPaths:
  - core/intake_gate_scorer.py
  - tests/test_intake_decider.py
  - 04_Workflows/fixtures/intake_*.json
- BlockedPaths:
  - AGENTS.md
  - 04_Workflows/00_Agent_Work_Progress.md
- Dependencies:
  - 04_Workflows/SPEC_phase7_5_min_loop.md
  - W3-T2（accept 後可進 tool selector）
- Risks:
  - request_type=other 預設嚴格 → 大量 pending_review
  - deadline_hint 僅排序用，不作 SLA
- Observability:
  - logs: gate_verdict、reject_reason
  - metrics: intake_accept_rate
  - traces: gate 決策寫入 task_runs.metadata.gate
- OutputArtifacts:
  - core/intake_gate_scorer.py
  - tests/test_intake_decider.py
  - 04_Workflows/fixtures/intake_*.json 擴充
- AcceptanceCriteria:
  - fixture intake → 穩定 gate_verdict
  - 缺必填欄位 → ok: false + 欄位級錯誤
  - python -m unittest tests.test_intake_decider -v 全綠
  - 輸出 dict 含 work_order_id、gate_scores、next_action
- VerificationCommands:
  - `python -m unittest tests.test_intake_decider -v`
    - 預期：全綠；5 request_type

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

- [ ] 實作/收口 intake_gate_scorer ROI/risk/cost
- [ ] CLI validate intake → gate_verdict
- [ ] 狀態機三態
- [ ] fixtures + tests 五類 request_type

### Files To Touch

- core/intake_gate_scorer.py
- tests/test_intake_decider.py
- 04_Workflows/fixtures/

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

- gate 決策 metadata 寫入路徑文檔化

### Rollout / Ops Notes

- gate 決策 metadata 寫入路徑文檔化

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
