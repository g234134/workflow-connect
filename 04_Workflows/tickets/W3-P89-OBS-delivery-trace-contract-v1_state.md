# TICKET STATE · W3-P89-OBS-delivery-trace-contract-v1 · P8/P8.9 Delivery Observability

> Wave 3 · P8 / P8.9 · **doc-only** · trace 欄位 + artifact 地圖  
> Schema SSOT：`docs/ticket-schema-master-v1.md` · `W5-T2`

---

## FRAME

- Goal: 實作者與 Reviewer 能從固定 artifact 路徑與 JSON 鍵追蹤 gate → notify → consumer → backlog 主鏈。
- Scope:
  - `docs/p8_p89_delivery_observability_contract_v1.md`（必建）
  - `docs/p8_9-verification-bundle-v1.md` · `docs/phase-8-operator-backlog-v1.md` 各 §Observability cross-ref
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` 一列 trace 契約
  - `04_Workflows/WORKFLOW_INDEX.md` MP-SMOKE / P8.9 各一行 observability 連結
- NonScope:
  - 不改 producer/consumer 程式 · 不新增 metrics 欄位 · 不建 Grafana
  - 不把 bridge HTTP 納入 mandatory MP-SMOKE · 不宣稱 prod SLO
  - 不上調 Phase% · 不改 `.github/workflows/**`
- AllowedPaths:
  - `docs/p8_p89_delivery_observability_contract_v1.md`
  - `docs/p8_9-verification-bundle-v1.md`
  - `docs/phase-8-operator-backlog-v1.md`
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `04_Workflows/tickets/W3-P89-OBS-delivery-trace-contract-v1_state.md`
- BlockedPaths:
  - `.github/workflows/**` · `core/**` · `tests/**` · `scripts/**`（行為）
  - Dashboard Phase% 數字格
- Dependencies:
  - MP-SMOKE · P8.9-REGRESSION · MP-METRICS · W3-P8-ADV · W3-P89-EVD
- AcceptanceCriteria:
  - AC-1：Contract ≥6 `trace_fields`（含 case_ref · run_id/experiment_id · multi_phase_smoke.ok · events_summary.count · acks_summary.pending_count · notifications_failed_ack_count）
  - AC-2：Artifact 地圖覆蓋 MP-SMOKE 1–7 與 P8.9 四檔
  - AC-3：每個 failure_signal 對應可執行 CLI
  - AC-4：WORKFLOW_INDEX MP-SMOKE / P8.9 各一行 observability 連結

### Wave Master 擴展

- wave_id: W3
- group_id: G9
- lifecycle_phase: B
- phase_targets: [P8, P8.9]
- estimated_cycles: 1
- mvp_allowed: true
- non_claims:
  - 非 prod SLO / alert
  - 非程式／metrics 欄位新增
  - 非 Phase% 上調
- ticket_class: doc/spec
- evidence_tier: L-local

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · D_scribe_done · orch_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无（本票收口完成）
- last_updated: 2026-07-10 · Orchestrator（同輪 B→C→D→O）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  同輪開票並關票。AC-1–AC-4 PASS。未改 scripts 行為 / Phase% / workflows。

---

## B_REPORT

- changed_files:
  - `docs/p8_p89_delivery_observability_contract_v1.md`（新建）
  - `docs/p8_9-verification-bundle-v1.md`（§Observability cross-ref）
  - `docs/phase-8-operator-backlog-v1.md`（§Observability cross-ref）
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`（§7.4.2）
  - `04_Workflows/WORKFLOW_INDEX.md`（MP-SMOKE / P8.9 observability 行）
  - `04_Workflows/tickets/W3-P89-OBS-delivery-trace-contract-v1_state.md`
- verification:
  - `rg "trace_fields|multi_phase_smoke|events_summary|notifications_failed_ack" docs/p8_p89_delivery_observability_contract_v1.md` → 命中
  - `rg "p8_p89_delivery_observability_contract" 04_Workflows/WORKFLOW_INDEX.md docs/p8_9-verification-bundle-v1.md docs/phase-8-operator-backlog-v1.md` → 命中
  - 人工：六個 AC 欄位 + 七步表 + 四檔 + failure↔CLI 齊
- behavior_notes: 純 doc；`run_id` 誠實對齊既有 `experiment_id`/`run_at`（MP 摘要無獨立 run_id 鍵）
- deferred_items: 無

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
  AC-1 PASS（≥6 trace_fields）· AC-2 PASS（MP 1–7 + 四檔）·
  AC-3 PASS（S_* / F_* ↔ CLI）· AC-4 PASS（INDEX 兩行）。
  risk=low · AllowedPaths 內 · 無 prod SLO over-claim。
- risk_level: low
- suggestions: 無

---

## D_REPORT

- docs_updates:
  - contract + bundle/backlog/matrix/INDEX cross-refs
- progress_entry: |
  2026-07-10 · W3-P89-OBS done · delivery observability contract · C=accepted
- followup_suggestions:
  - Downstream：`W3-P89-SSOT` 引用本 contract 填 observability.verify_commands

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-07-10 | orch+B+C+D | 同輪開票關票 |
