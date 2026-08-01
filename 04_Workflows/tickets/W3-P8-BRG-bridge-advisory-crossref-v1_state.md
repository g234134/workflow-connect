# TICKET STATE · W3-P8-BRG-bridge-advisory-crossref-v1 · Bridge advisory cross-ref

> Wave 3 · P8 / P8.5(ref) · **doc-only** · minimal bridge ↔ P8 交付鏈邊界清晰（advisory · 非 prod gate）  
> Schema SSOT：`docs/ticket-schema-master-v1.md` · `W5-T2` · FRAME 對齊 `W-MASTER-wave-plan_state.md#W3-P8-BRG-bridge-advisory-crossref-v1`

---

## FRAME
<!-- Orchestrator 填：凍結於 2026-07-10 · 對齊 W-MASTER §BRG -->

- Goal: P8 operator / MP-SMOKE 敘事與 P8.5 bridge smoke **邊界清晰**：bridge 為 **optional advisory 側線** · in-memory stub · **≠** Phase 8 release gate · **不阻塞** P8/P8.9 80% 敘事。
- Scope:
  - MUST：`docs/phase-8-operator-backlog-v1.md` §Related／Release sanity — bridge advisory 脚注；明示 **bridge ≠ operator 前置** · **≠** Phase 8 release gate
  - MUST：`04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md` 脚注一句 bridge advisory；batch／webhook deferred 不變
  - MUST：`04_Workflows/WORKFLOW_INDEX.md` §1.4 P8.5 bridge ↔ Phase 8 Operator Backlog **雙向各一句**
  - MUST：`P8-T2`／`P8-API` STATE 僅 `cross_refs`／notes **append**
  - MUST：本票 STATE（B_REPORT／C_REPORT／D_REPORT）
- NonScope:
  - 不改暗部 bridge core、`app_api` bridge、`.github/workflows/**`、`core/**`、`tests/**`
  - 不把 bridge 併入 MP-SMOKE；不填 GA；不宣稱 Scenario1/2 GA
  - 不寫「bridge smoke required for Phase 8 release」；不上調 Phase%／Dashboard 數字
  - 不改治理母本／憲法 §7 路徑
- AllowedPaths:
  - `docs/phase-8-operator-backlog-v1.md`
  - `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `04_Workflows/tickets/P8-T2-operator-pending-visibility-v1_state.md`
  - `04_Workflows/tickets/P8-API-operator-backlog-http-endpoint-v1_state.md`
  - `04_Workflows/tickets/W3-P8-BRG-bridge-advisory-crossref-v1_state.md`
  - QUEUE／SESSION／Progress 末尾（O／D 收口）
- BlockedPaths:
  - 暗部 bridge core · `app_api` bridge · `.github/workflows/**` · `core/**` · `tests/**`
  - Dashboard Phase% 數字格 · 治理母本 · 憲法 §7 類型路徑
  - MP-SMOKE 七步行為／腳本
- Dependencies:
  - 上游：`docs/phase8_5-bridge-smoke-runbook-v1.md` · `WH-P85-CI-LAND-v1` · P8-T2／P8-API STATE · `W3-P8-ADV-*`
  - 下游：W4 P8.5 closure 僅引用本 cross-ref
- AcceptanceCriteria:
  - AC-1：`rg "in-memory stub|bridge advisory|≠ prod" docs/phase-8-operator-backlog-v1.md` 命中；明示 ≠ Phase 8 release gate
  - AC-2：INDEX §1.4 與 Operator Backlog **互相可導航**
  - AC-3：`rg "bridge smoke required|required for Phase 8 release" docs/phase-8* 04_Workflows/plans/phase-8*` → 0 命中（或僅 non-claim／禁止句）
  - AC-4：plan 脚注含 bridge advisory；batch／webhook 仍 deferred
  - AC-5：P8-T2／P8-API STATE 有 cross_refs／notes 指向本票或 bridge runbook

### Wave Master 擴展

- wave_id: W3
- group_id: G8
- lifecycle_phase: B
- phase_targets: [P8]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W3-P8-ADV-advisory-ci-ssot-index-v1, W3-P89-SSOT-state-dashboard-alignment-v1]
  - downstream_waves: [W4-P85-S2-GA-RUNBOOK-v1 僅引用]
  - blocks_if_missing: []
- risks:
  - id: RSK-W3-BRG-01
    description: P8.5 Phase% 敘事污染 P8「已 80%」判斷
    likelihood: M
    impact: M
    mitigation: 分欄寫「P8 80% 不含 bridge prod」· bridge ≠ release gate
    residual: accept
  - id: RSK-W3-BRG-02
    description: cross-ref 被讀成「MP-SMOKE 須跑 bridge」
    likelihood: L
    impact: M
    mitigation: 寫 optional / post-MP 側線 · 明示 ≠ operator 前置
    residual: accept
- observability:
  - verify_commands:
    - "rg \"in-memory stub|bridge advisory|≠ prod\" docs/phase-8-operator-backlog-v1.md"
    - "rg \"bridge smoke required|required for Phase 8 release\" docs/phase-8* 04_Workflows/plans/phase-8*"
  - evidence_artifacts:
    - docs/phase-8-operator-backlog-v1.md
    - WORKFLOW_INDEX §1.4 + Operator Backlog 條目
  - trace_fields: [ci_class]
  - success_signals: [雙向 cross-ref · non-claims 保留 · ≠ release gate]
  - failure_signals: [Phase 8 doc 暗示 bridge GA 為發版 gate]
- non_claims:
  - bridge advisory ≠ Phase 8 release gate
  - in-memory stub ≠ prod browser
  - bridge smoke landing ≠ Scenario1/2 GA pass
  - 本票 ≠ MP-SMOKE 併入 bridge · ≠ Phase% 上調
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · D_scribe_done · orch_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无（本票收口完成）
- last_updated: 2026-07-10 · Orchestrator（同輪 B→C→D→O 關票）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  同輪開票並關票。AC-1–AC-5 PASS · C=accepted · Wave 3 G8 BRG 收口。
  未改 workflows / Phase% / bridge core。QUEUE → DONE。

---

## B_REPORT

- changed_files:
  - `docs/phase-8-operator-backlog-v1.md`（§Bridge advisory · Release sanity 脚注）
  - `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md`（§7 bridge advisory 脚注）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.4 ↔ Operator Backlog 雙向各一句）
  - `04_Workflows/tickets/P8-T2-operator-pending-visibility-v1_state.md`（cross_refs／notes append）
  - `04_Workflows/tickets/P8-API-operator-backlog-http-endpoint-v1_state.md`（cross_refs／notes append）
  - `04_Workflows/tickets/W3-P8-BRG-bridge-advisory-crossref-v1_state.md`
- artifacts: 無（純 doc／STATE append）
- verification:
  - AC-1：`rg "in-memory stub|bridge advisory|≠ prod" docs/phase-8-operator-backlog-v1.md` → 命中 Bridge advisory footnote（含 ≠ Phase 8 release gate）
  - AC-2：INDEX §1.4「Phase 8 Operator Backlog 邊界」↔ Operator Backlog「P8.5 bridge 邊界」互相可導航
  - AC-3：`rg "bridge smoke required|required for Phase 8 release" docs --glob "phase-8*" 04_Workflows/plans --glob "phase-8*"` → **0 命中**（exit 1）
  - AC-4：plan §7 脚注含 bridge advisory；文內 batch／webhook 仍標 deferred
  - AC-5：P8-T2／P8-API STATE `cross_refs` 指向本票 + `phase8_5-bridge-smoke-runbook-v1.md`
- behavior_notes: 純 doc-only；明示 bridge ≠ operator 前置 · ≠ Phase 8 release gate；未改 MP-SMOKE／workflows／Phase%
- deferred_items: 無（W4 P8.5 GA／Scenario 仍 human-blocked · 非本票）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: >-
  獨立重跑 AC-1–AC-5 全 PASS。AllowedPaths 未越界；無「bridge smoke required for Phase 8 release」宣稱；
  雙向 INDEX 可導航；P8-T2／P8-API 僅 append cross_refs；batch／webhook deferred 保留。
  對照 W-MASTER non-claims／RSK-W3-BRG-01/02 mitigation 已落地。
- risk_level: low
- suggestions: 無

---

## D_REPORT

- docs_updates:
  - 本票交付已含 Operator Backlog／plan／INDEX／子票 cross_refs；無需另開文檔票
- progress_entry: >-
  2026-07-10 · W3-P8-BRG · bridge advisory cross-ref doc-only · C=accepted ·
  bridge ≠ Phase 8 release gate · Wave 3 G8 BRG 收口
- followup_suggestions: >-
  Wave 3 執行票已齊；下一動 arrange unplanned（FP-G2）或 human-blocked Wave 4／P7 Round-2。
  勿開新大票重寫 bridge／MP-SMOKE。
