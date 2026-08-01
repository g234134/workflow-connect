# TICKET STATE · FP-G1-T1-governance-dual-unblock-frame-v1 · governance_dual 解阻 FRAME

> Full-Phase G1 · P1/P3.5/P7 · **doc/spec** · arrange 2026-07-10
> 對齊：`W-MASTER-full-phase-plan_state.md#G1`
> 收口標籤：`branch_ai_closed`（AI 可達段）≠ Phase closure；`branch_human_gated`（批文／GA）另掛

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange-only · 不代跑 Implementer -->

- Goal: 產出 governance_dual 解阻 FRAME（五頂要件 checklist · 負責方／交付物／關票條件）；**不負責**取得真批文。
- Scope:
  - MUST：新建 `docs/governance-dual-unblock-checklist-v1.md`（五頂：真批文 · Infra staging · Security POST · allowlist · receiver）
  - MUST：每項含 owner（human/infra/security）· 交付物 · blocked 時 defer 規則 · 鏈 Wave 2 票 ID
  - MUST：`non_claims`：FRAME ≠ Round-2 GO · ≠ 批文已齊
  - MAY：`WORKFLOW_INDEX.md` 一句 · `docs/index.md` 一行
- NonScope:
  - 真批文取得 · staging POST execute · prod endpoint flip
  - 改 `.github/workflows` required · Phase% 上調 · DarkOps
- AllowedPaths:
  - `docs/governance-dual-unblock-checklist-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G1-T1-governance-dual-unblock-frame-v1_state.md`（B_REPORT）
- BlockedPaths:
  - `core/**` · `scripts/**`／`tests/**`（除唯讀引用）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格 · branch protection
  - 治理母本（`HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`）全文改寫
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）· `master_status.md`／`handoff.md`（Governance）
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票 B_REPORT）
- Dependencies:
  - 無硬阻塞；必讀：`W-MASTER-wave-plan` Wave 2 staging · Dashboard P7 Round-2 敘事
  - ∥ FP-G1-T2／T4／T5
- AcceptanceCriteria:
  - AC-1：checklist 含五頂前置，每項有 owner · 交付物 · defer 規則
  - AC-2：每項鏈 Wave 2 票 ID 或 blocked/planning 占位
  - AC-3：`non_claims` 明確 FRAME ≠ Round-2 GO
  - AC-4：`rg "governance_dual|五頂|non_claims" docs/governance-dual-unblock-checklist-v1.md` 命中
  - AC-5：未改 core／workflows／Phase%

### Wave Master 擴展

- wave_id: null
- group_id: G1
- lifecycle_phase: B
- phase_targets: [P7, P3.5]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: []
  - downstream_waves: [W2-T1, W2-T2]
  - blocks_if_missing: []
- risks:
  - id: RSK-G1-T1-01
    description: checklist 被誤標為批文已齊／Round-2 GO
    likelihood: M
    impact: H
    mitigation: non_claims 置頂 · 僅 doc AllowedPaths · Orchestrator arrange-only
    residual: accept
- observability:
  - verify_commands:
    - "rg "governance_dual|non_claims" docs/governance-dual-unblock-checklist-v1.md"
  - evidence_artifacts:
    - docs/governance-dual-unblock-checklist-v1.md
  - trace_fields: []
  - success_signals: [FRAME doc 存在 · 無 workflows／Phase%／core 變更]
  - failure_signals: [改 workflows · 宣稱 Phase closure／批文已齊]
- non_claims:
  - FRAME ≠ P7 Round-2 GO · ≠ governance_dual 真批文已齊
  - ≠ Phase closure
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true
- closure_tags:
  - branch_ai_closed: 本票 AI 可達（doc）
  - branch_human_gated: 真批文仍掛 W2／Round-2
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: done
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无 · branch_ai_closed（本票）；真批文仍 branch_human_gated／W2
- last_updated: 2026-07-10 · O（B→C→D 收口）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  Branch-G1 execute · T1 doc checklist 收口 · 可标 branch_ai_closed；
  **禁止**标 Phase closure／Round-2 GO。未碰 T3／workflows／Phase%／core。
- reviewer_notes: >-
  AC-1..AC-5 PASS；conclusion=accepted；交棒 scribe。

---

## B_REPORT
<!-- Implementer 填 -->

- changed_files:
  - docs/governance-dual-unblock-checklist-v1.md（新建）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.5 MAY 一句 · G1 解阻指针）
  - docs/index.md（导航 + changelog）
  - 04_Workflows/tickets/FP-G1-T1-governance-dual-unblock-frame-v1_state.md（B_REPORT）
- artifacts:
  - docs/governance-dual-unblock-checklist-v1.md — 五顶 checklist · owner／交付物／defer · Wave 2 链
- verification:
  - cmd: `rg "governance_dual|五顶|non_claims" docs/governance-dual-unblock-checklist-v1.md`
  - result: ok · 命中 non_claims／五顶／governance_dual／W2-T1／W2-T2
  - cmd: `rg "governance-dual-unblock" 04_Workflows/WORKFLOW_INDEX.md docs/index.md`
  - result: ok · MAY 交叉引用命中
- behavior_notes: doc-only；不取得真批文；不宣称 Round-2 GO
- deferred_items: 五顶真交付仍 human／infra／security（W2-T1／T2 等）

---

## C_REPORT
<!-- Reviewer 填 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  AC-1 PASS：五顶均有 owner · 交付物 · defer。
  AC-2 PASS：链 W2-T1／W2-T2 + planning/blocked 占位。
  AC-3 PASS：non_claims 置顶 · FRAME ≠ Round-2 GO。
  AC-4 PASS：rg 命中。
  AC-5 PASS：未改 core／workflows／Phase%。
- risk_level: low
- suggestions: Reviewer 遇「Round-2 GO」句式可链本档 §2

---

## D_REPORT
<!-- Scribe 填 -->

- docs_updates:
  - docs/governance-dual-unblock-checklist-v1.md（本票正文）
  - docs/index.md 导航 + changelog
  - WORKFLOW_INDEX §1.5 G1 指针一句
- progress_entry: |
  2026-07-10 · FP-G1-T1 done · governance_dual 五顶 checklist · Reviewer accepted · branch_ai_closed · ≠ Round-2 GO
- followup_suggestions:
  - 勿把本档当批文已齐；真批文仍挂 W2-T1／Round-2
  - 勿 execute FP-G1-T3（仍 BLOCKED）

