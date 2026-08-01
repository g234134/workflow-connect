# TICKET STATE · FP-G1-T2-wc-pre-06-07-approval-tracker-v1 · WC-PRE-06/07 批文追踪 SSOT

> Full-Phase G1 · P3.5/P10 · **doc/spec** · arrange 2026-07-10
> 對齊：`W-MASTER-full-phase-plan_state.md#G1`
> 收口標籤：`branch_ai_closed`（AI 可達段）≠ Phase closure；`branch_human_gated`（批文／GA）另掛

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange-only · 不代跑 Implementer -->

- Goal: 建立 WC-PRE-06/07 批文狀態機 SSOT（design_ready → pending_approval → approved）；**human-only 關 approved**。
- Scope:
  - MUST：新建 `docs/wc-pre-06-07-approval-tracker-v1.md`（兩票狀態枚舉 + 轉換條件）
  - MUST：`blocks_if_missing` 列 G6 required CI · W4-GUARD G2–G4 · WC-IMPL-L2
  - MUST：關票交付物 = 批文 ID／sign-off 占位；STATE 標 human 關票邊界
  - MAY：INDEX／docs/index 一句
- NonScope:
  - 修改 branch protection · 升格 PR required · 假設批文已獲 · 施工 WC-IMPL-L2
  - AI 代填「已批准」
- AllowedPaths:
  - `docs/wc-pre-06-07-approval-tracker-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G1-T2-wc-pre-06-07-approval-tracker-v1_state.md`（B_REPORT）
- BlockedPaths:
  - `core/**` · `scripts/**`／`tests/**`（除唯讀引用）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格 · branch protection
  - 治理母本（`HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`）全文改寫
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）· `master_status.md`／`handoff.md`（Governance）
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票 B_REPORT）
- Dependencies:
  - 無硬阻塞（design_ready 資產可引用）；∥ FP-G1-T1／T5
  - 下游：FP-G1-T3 · FP-G6-T1（批文後）
- AcceptanceCriteria:
  - AC-1：兩票狀態枚舉 + 轉換條件（僅 human 可關 approved）
  - AC-2：blocks_if_missing 含 G6 required CI · GUARD G2–G4 · WC-IMPL-L2
  - AC-3：關票交付物占位符明確
  - AC-4：`rg "WC-PRE-06|WC-PRE-07|approved|non_claims" docs/wc-pre-06-07-approval-tracker-v1.md` 命中
  - AC-5：未改 workflows／Phase%／core

### Wave Master 擴展

- wave_id: null
- group_id: G1
- lifecycle_phase: B
- phase_targets: [P3.5, P10]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: ["尚書省 WC-PRE-06/07 批文 sign-off（關 approved 僅 human）"]
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W5-WC-PRE-06-governance-spec-v1]
  - downstream_waves: [FP-G1-T3-guard-schema-ratio-escalation-frame-v1, FP-G6-T1-required-ci-unblock-frame-v1]
  - blocks_if_missing: []
- risks:
  - id: RSK-G1-T2-01
    description: AI 代填已批准或與 Wave5 design 票雙份混淆
    likelihood: M
    impact: H
    mitigation: non_claims 置頂 · 僅 doc AllowedPaths · Orchestrator arrange-only
    residual: accept
- observability:
  - verify_commands:
    - "rg "WC-PRE-06|WC-PRE-07|non_claims" docs/wc-pre-06-07-approval-tracker-v1.md"
  - evidence_artifacts:
    - docs/wc-pre-06-07-approval-tracker-v1.md
  - trace_fields: []
  - success_signals: [FRAME doc 存在 · 無 workflows／Phase%／core 變更]
  - failure_signals: [改 workflows · 宣稱 Phase closure／批文已齊]
- non_claims:
  - tracker doc ≠ 批文已獲 · ≠ required CI 已掛
  - ≠ Phase closure
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true
- closure_tags:
  - branch_ai_closed: tracker doc AI 可達
  - branch_human_gated: approved 關票仍 human
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: done
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无 · branch_ai_closed（tracker）；approved 关票仍 branch_human_gated
- last_updated: 2026-07-10 · O（B→C→D 收口）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  Branch-G1 execute · T2 tracker SSOT 收口 · AI 段 branch_ai_closed；
  **禁止** AI 代填 approved · **禁止**标 Phase closure。T3 仍 BLOCKED。
- reviewer_notes: >-
  AC-1..AC-5 PASS；conclusion=accepted；交棒 scribe。

---

## B_REPORT
<!-- Implementer 填 -->

- changed_files:
  - docs/wc-pre-06-07-approval-tracker-v1.md（新建）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.5 MAY · G1 批文指针）
  - docs/index.md（导航 + changelog）
  - 04_Workflows/tickets/FP-G1-T2-wc-pre-06-07-approval-tracker-v1_state.md（B_REPORT）
- artifacts:
  - docs/wc-pre-06-07-approval-tracker-v1.md — 状态机 · blocks_if_missing · 关票占位
- verification:
  - cmd: `rg "WC-PRE-06|WC-PRE-07|approved|non_claims" docs/wc-pre-06-07-approval-tracker-v1.md`
  - result: ok · 命中状态枚举／仅 human approved／G6·GUARD·WC-IMPL
  - cmd: `rg "wc-pre-06-07-approval" 04_Workflows/WORKFLOW_INDEX.md docs/index.md`
  - result: ok · MAY 交叉引用命中
- behavior_notes: doc-only；两票保持 design_ready；不代填 approved
- deferred_items: human sign-off → approved；其后才可解阻 T3／G6-T1／WC-IMPL-L2

---

## C_REPORT
<!-- Reviewer 填 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  AC-1 PASS：design_ready→pending_approval→approved；仅 human 关 approved。
  AC-2 PASS：blocks_if_missing 含 G6 required CI · GUARD G2–G4 · WC-IMPL-L2。
  AC-3 PASS：关票交付物占位符明确。
  AC-4 PASS：rg 命中。
  AC-5 PASS：未改 workflows／Phase%／core。
- risk_level: low
- suggestions: 与 Wave5 design 票分界已写 non_claims；勿双份混淆

---

## D_REPORT
<!-- Scribe 填 -->

- docs_updates:
  - docs/wc-pre-06-07-approval-tracker-v1.md（本票正文）
  - docs/index.md 导航 + changelog
  - WORKFLOW_INDEX §1.5 一句
- progress_entry: |
  2026-07-10 · FP-G1-T2 done · WC-PRE-06/07 tracker · Reviewer accepted · approved 仍 human
- followup_suggestions:
  - 勿 execute FP-G1-T3／FP-G6-T1／required-CI 直至 human approved
  - 勿 AI 代填批文 ID

