# TICKET STATE · FP-G6-T1-required-ci-unblock-frame-v1 · WC-PRE-07 mandatory CI FRAME

> Full-Phase G6 · P6 · **blocked/planning** · arrange 2026-07-10
> 對齊：`W-MASTER-full-phase-plan_state.md#G6`
> 收口標籤：`branch_ai_closed`（AI 可達段）≠ Phase closure；`branch_human_gated`（批文／GA）另掛

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange-only · 不代跑 Implementer -->

- Goal: 為 WC-PRE-07 mandatory／required CI 產出 **blocked_on_approval** FRAME；批文前僅占位，不改 workflows。
- Scope:
  - MUST（批文後）：`docs/wc-pre-07-required-ci-unblock-frame-v1.md`
  - MUST：解阻條件 · 與 FP-G6-required-ci／WC-PRE 關係 · non_claims
  - 本輪 arrange：STATE=`blocked` · **不派** Implementer · **不改** `.github/workflows`
- NonScope:
  - 無批文改 required CI · branch protection · Phase% · 宣稱 INT Tier-A
- AllowedPaths:
  - `docs/wc-pre-07-required-ci-unblock-frame-v1.md`（解阻後）
  - `04_Workflows/tickets/FP-G6-T1-required-ci-unblock-frame-v1_state.md`
- BlockedPaths:
  - `core/**` · `scripts/**`／`tests/**`（除唯讀引用）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格 · branch protection
  - 治理母本（`HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`）全文改寫
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）· `master_status.md`／`handoff.md`（Governance）
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票 B_REPORT）
- Dependencies:
  - **blocked_on**：尚書省 WC-PRE-07 批文（串行 FP-G1-T2 approved）
  - 相關：FP-G6-required-ci NOT_PLANNED · WC-PRE-approval
- AcceptanceCriteria:
  - AC-1：解阻條件與批文交付物寫清
  - AC-2：STATE 維持 blocked 直至批文
  - AC-3：non_claims：FRAME ≠ required CI 已掛
  - AC-4：本輪僅 QUEUE 占位

### Wave Master 擴展

- wave_id: null
- group_id: G6
- lifecycle_phase: B
- phase_targets: [P6]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: ["尚書省 WC-PRE-07 批文"]
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [FP-G1-T2-wc-pre-06-07-approval-tracker-v1]
  - downstream_waves: [FP-G6-required-ci]
  - blocks_if_missing: [WC-PRE-approval]
- risks:
  - id: RSK-G6-T1-01
    description: 無批文誤改 workflows／required
    likelihood: M
    impact: H
    mitigation: non_claims 置頂 · 僅 doc AllowedPaths · Orchestrator arrange-only
    residual: accept
- observability:
  - verify_commands:
    - "rg "WC-PRE-07|required|non_claims" docs/wc-pre-07-required-ci-unblock-frame-v1.md"
  - evidence_artifacts:
    - docs/wc-pre-07-required-ci-unblock-frame-v1.md（解阻後）
  - trace_fields: []
  - success_signals: [FRAME doc 存在 · 無 workflows／Phase%／core 變更]
  - failure_signals: [改 workflows · 宣稱 Phase closure／批文已齊]
- non_claims:
  - blocked FRAME ≠ required CI 已落地 · ≠ INT Tier-A · ≠ P6 closure
  - ≠ Phase closure
- ticket_class: blocked/planning
- evidence_tier: L-local
- parallel_ok: false
- closure_tags:
  - branch_ai_closed: 否 · human_gated
  - branch_human_gated: 等 WC-PRE-07 批文
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: blocked
- lifecycle_phase: B
- current_owner: orchestrator
- next_action: 占位 · 等 WC-PRE-07／FP-G1-T2 approved 後再升 READY
- last_updated: 2026-07-10 · O（arrange · Branch-G1/G5/G6 整組入 QUEUE）
- status_by_role:
  - orchestrator: done
  - implementer: n/a
  - reviewer: pending
  - scribe: pending
- orch_notes: >-
  arrange-only · 3 分支交棒（G1／G5／G6）· 不代跑 Implementer · 不 commit 功能碼。
  本票收口僅可標 branch_ai_closed（若 AI 段完成）或維持 branch_human_gated；**禁止**標 Phase closure。
- blocked_reason: WC-PRE-07 批文未齊（branch_human_gated）· 串行 G1-T2
- unblock_when: 尚書省批文 + FP-G1-T2 tracker approved
- note_g6_wave0: FP-G6-T2/T3/T4 已 DONE（AI 可達段已 branch_ai_closed）；本票仍 human_gated


---

## B_REPORT

- changed_files: （待 Implementer）
- artifacts: 無
- verification: 無
- behavior_notes: 無
- deferred_items: 無

---

## C_REPORT

- conclusion: （待 Reviewer）
- blocking_issues: 無
- checks_summary: 無
- risk_level: （待填）
- suggestions: 無

---

## D_REPORT

- docs_updates: 無
- progress_entry: 無
- followup_suggestions: 無

