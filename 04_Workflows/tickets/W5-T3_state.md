# TICKET STATE · W5-T3 · Memory+1 工單結案沉澱（Learning 種子）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 5 - Browser + Skill Distillation

---

## FRAME

- Title: Memory+1 工單結案沉澱（Learning 種子）
- Goal: 每筆 delivered 工單追加一條結構化 memory（JSONL），供 selector/skill 重用只讀消費。
- Scope:
  - 實作 append_work_order_memory()
  - 掛接 W4 delivery 與 W3 outbox delivered 事件
  - 對齊 SPEC_phase7_5_min_loop.md Memory+1 節
  - CLI：memory list --work-order-id
- NonScope:
  - 線上訓練／Learning Mode
  - 向量庫自動 ingest
  - PII 長期存儲
- AllowedPaths:
  - core/work_order_memory.py
  - shared/schemas/work_order_memory_v1.json
  - tests/test_work_order_memory.py
- BlockedPaths:
  - AGENTS.md
- Dependencies:
  - W4-T2 delivery
  - W3-T4 outbox
  - W3-T3 actual_tools_used
- Risks:
  - memory 含敏感內容 → 僅存邏輯 ID 與摘要
  - 磁碟滿 → append 失敗不阻斷 delivery（ok: false sidecar）
- Observability:
  - logs: memory_appended、work_order_id
  - metrics: work_order_memory_total
  - traces: memory 條目含 trace_id 引用
- OutputArtifacts:
  - core/work_order_memory.py
  - shared/schemas/work_order_memory_v1.json
  - runtime/work_order_memory.jsonl 樣本
- AcceptanceCriteria:
  - CLEAN job 後 JSONL 追加 1 列，schema_version 正確
  - 重複 delivery 事件不雙寫（冪等）
  - 查詢 CLI 可讀回 dict
  - unittest 覆蓋 append/query/duplicate
- VerificationCommands:
  - `python -m unittest tests.test_work_order_memory -v`
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

- [ ] 實作 work_order_memory append/query
- [ ] 掛接 delivery + outbox 事件
- [ ] CLI memory list
- [ ] tests append/query/duplicate

### Files To Touch

- core/work_order_memory.py
- shared/schemas/work_order_memory_v1.json
- tests/test_work_order_memory.py

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

- JSONL 邏輯路徑見 Master_Map；無 PII 長存

### Rollout / Ops Notes

- JSONL 邏輯路徑見 Master_Map；無 PII 長存

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
