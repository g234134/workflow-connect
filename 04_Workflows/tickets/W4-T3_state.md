# TICKET STATE · W4-T3 · Order／Milestone 追蹤 + 手動金流台帳

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4 - Commercialization

---

## FRAME

- Title: Order／Milestone 追蹤 + 手動金流台帳
- Goal: 商務層 order_status 與技術層 orch_status 可映射；財務可手動登記收款／里程碑。
- Scope:
  - 實作最小 order_ledger 模組：JSONL 或 SQLite（邏輯路徑見 Master_Map）
  - 資料模型對齊 WAVE8_CLEAN_ORDER_MODEL_v0.1.md
  - CLI：order create / order transition / billing record-manual
  - 與 run_summary、outbox work_order.delivered 事件聯動
- NonScope:
  - Stripe/支付閘道
  - 自動開發票
  - 客戶門戶 UI
- AllowedPaths:
  - core/order_ledger.py
  - 04_Workflows/_order_ledger.py
  - shared/schemas/order_ledger_v1.json
  - docs/ORDER_TRACKING_MANUAL_BILLING.md
  - tests/test_order_ledger.py
- BlockedPaths:
  - AGENTS.md
- Dependencies:
  - W4-T2 delivery 事件
  - W3-T4 outbox 事件
  - WAVE8_CLEAN_BILLING_FIELDS_v0.1.md
- Risks:
  - 技術 DONE 但商務未驗收 → 保持 DELIVERED 不自動 CLOSED
  - 雙幣別手動輸入錯誤 → 校驗 ISO 4217
- Observability:
  - logs: 每次 transition from/to/actor
  - metrics: orders_in_progress
  - traces: order_id 寫入 outbox payload
- OutputArtifacts:
  - core/order_ledger.py 或 04_Workflows/_order_ledger.py
  - shared/schemas/order_ledger_v1.json
  - docs/ORDER_TRACKING_MANUAL_BILLING.md
  - tests + 樣本 JSONL
- AcceptanceCriteria:
  - CLEAN job 完成後可 order transition DELIVERED → CLOSED
  - 手動金流記錄含 amount、currency、recorded_by、work_order_id
  - 查詢 CLI 輸出完整追蹤鏈
  - 測試覆蓋非法狀態轉移拒絕
- VerificationCommands:
  - `python -m unittest tests.test_order_ledger -v`
    - 預期：全綠
  - `order transition CLI`
    - 預期：非法轉移拒絕

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

- [ ] 實作 order_ledger 模組 + schema
- [ ] CLI create/transition/billing record-manual
- [ ] 聯動 run_summary 與 outbox delivered
- [ ] tests + ORDER_TRACKING 文檔

### Files To Touch

- core/order_ledger.py
- shared/schemas/order_ledger_v1.json
- docs/ORDER_TRACKING_MANUAL_BILLING.md
- tests/test_order_ledger.py

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

- 手動金流無 API；DELIVERED→CLOSED 需人工確認

### Rollout / Ops Notes

- 手動金流無 API；DELIVERED→CLOSED 需人工確認

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
