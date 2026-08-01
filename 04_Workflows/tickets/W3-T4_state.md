# TICKET STATE · W3-T4 · Outbox Replay CLI（orchestration_bridge_outbox）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 - Tool Layer

---

## FRAME

- Title: Outbox Replay CLI（orchestration_bridge_outbox）
- Goal: 工單事件可從 outbox JSONL 離線重播，支援除錯與冪等驗證，完成 Tool Layer 閉環。
- Scope:
  - 實作 replay_outbox_events()：按 event_id/work_order_id 過濾重放
  - CLI：python -m core.orchestration_bridge_outbox replay --file ... --dry-run
  - 事件契約對齊 orchestration_bridge_event_v1
  - 與 tool_decision_log 以 work_order_id join 文檔化
- NonScope:
  - 改 DLQ schema
  - 自動重新執行 production 流量（預設 dry-run）
  - UI 輪詢實作
- AllowedPaths:
  - core/orchestration_bridge_outbox.py
  - tests/test_orchestration_bridge_outbox_replay.py
  - docs/OUTBOX_REPLAY_RUNBOOK.md
  - 04_Workflows/SPEC_phase7_5_min_loop.md（§6 交叉引用）
- BlockedPaths:
  - AGENTS.md
  - 暗部 DLQ schema
- Dependencies:
  - W3-T3（actuals 存在時 replay 報告可含執行結果）
  - 暗部 orchestration_bridge_outbox.py
  - Phase 7.5 outbox 語意
- Risks:
  - 舊版 event schema 缺欄 → ok: false + message
  - live replay 誤觸外部 API → 預設 --dry-run；--execute 需 env 閘門
- Observability:
  - logs: 每事件 event_type、replay_result
  - metrics: outbox_replay_total
  - traces: replay 批次 batch_id 寫入戰報 JSON
- OutputArtifacts:
  - core/orchestration_bridge_outbox.py replay 子命令
  - tests/test_orchestration_bridge_outbox_replay.py
  - docs/OUTBOX_REPLAY_RUNBOOK.md
- AcceptanceCriteria:
  - dry-run replay 輸出 events_replayed、skipped_duplicate、errors[]
  - 重複 replay 不雙寫 side effect（冪等）
  - unittest ≥5 案例
  - SPEC_phase7_5_min_loop.md §6 交叉引用更新
- VerificationCommands:
  - `python -m unittest tests.test_orchestration_bridge_outbox_replay -v`
    - 預期：≥5 案例全綠
  - `python -m core.orchestration_bridge_outbox replay --dry-run ...`
    - 預期：結構化摘要

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

- [ ] 實作 replay_outbox_events + CLI
- [ ] 冪等與 dry-run 預設
- [ ] 撰寫 OUTBOX_REPLAY_RUNBOOK.md
- [ ] ≥5 unittest 案例

### Files To Touch

- core/orchestration_bridge_outbox.py
- tests/test_orchestration_bridge_outbox_replay.py
- docs/OUTBOX_REPLAY_RUNBOOK.md

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

- 預設 dry-run；--execute 需雙閘門 env

### Rollout / Ops Notes

- 預設 dry-run；--execute 需雙閘門 env

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
