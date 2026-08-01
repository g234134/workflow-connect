# TICKET STATE · FP-G1-T5-constitution-progress-append-protocol-v1 · Progress/Dashboard 寫入邊界協議

> Full-Phase G1 · P1/P10 · **doc/spec** · arrange 2026-07-10
> 對齊：`W-MASTER-full-phase-plan_state.md#G1`
> 收口標籤：`branch_ai_closed`（AI 可達段）≠ Phase closure；`branch_human_gated`（批文／GA）另掛

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange-only · 不代跑 Implementer -->

- Goal: 為 Multi-Chat Scribe／lane chat 提供 Progress／Dashboard／master_status **append-only** 與 Governance 獨占字段 SSOT。
- Scope:
  - MUST：新建 `docs/progress-dashboard-append-protocol-v1.md`（誰可寫 · 末尾模板 · 禁改 Phase%）
  - MUST：模板含 evidence_tier · run_url · group_id · blocked/next
  - MUST：鏈 OPS_CYCLE · 憲法 §6.2–§6.3 · inspector
  - MAY：INDEX／docs/index 一句
- NonScope:
  - 修改 Dashboard Phase% 數字 · 寫 master_status 正文 · 替代 `_ops_cycle.py`
- AllowedPaths:
  - `docs/progress-dashboard-append-protocol-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G1-T5-constitution-progress-append-protocol-v1_state.md`（B_REPORT）
- BlockedPaths:
  - `core/**` · `scripts/**`／`tests/**`（除唯讀引用）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格 · branch protection
  - 治理母本（`HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`）全文改寫
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）· `master_status.md`／`handoff.md`（Governance）
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票 B_REPORT）
- Dependencies:
  - ∥ FP-G1-T2 · FP-G5-T3（可交叉引用）
- AcceptanceCriteria:
  - AC-1：誰可寫 Progress/Dashboard/master_status 表
  - AC-2：Progress 末尾條目模板（evidence_tier · blocked/next）
  - AC-3：lane chat 禁止改 Phase% 的 enforcement 句
  - AC-4：`rg "append-only|evidence_tier|Phase%|non_claims" docs/progress-dashboard-append-protocol-v1.md` 命中
  - AC-5：未改 Phase%／master_status／core

### Wave Master 擴展

- wave_id: null
- group_id: G1
- lifecycle_phase: B
- phase_targets: [P1, P10]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: []
  - downstream_waves: [FP-G5-T3-progress-append-template-v1]
  - blocks_if_missing: []
- risks:
  - id: RSK-G1-T5-01
    description: 模板被當成可改 Phase% 授權
    likelihood: M
    impact: H
    mitigation: non_claims 置頂 · 僅 doc AllowedPaths · Orchestrator arrange-only
    residual: accept
- observability:
  - verify_commands:
    - "rg "append-only|evidence_tier|non_claims" docs/progress-dashboard-append-protocol-v1.md"
  - evidence_artifacts:
    - docs/progress-dashboard-append-protocol-v1.md
  - trace_fields: []
  - success_signals: [FRAME doc 存在 · 無 workflows／Phase%／core 變更]
  - failure_signals: [改 workflows · 宣稱 Phase closure／批文已齊]
- non_claims:
  - 協議 doc ≠ 已改 Dashboard／master_status
  - ≠ Phase closure
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true
- closure_tags:
  - branch_ai_closed: 協議 doc AI 可達
  - branch_human_gated: 無（本票）
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: done
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无 · branch_ai_closed
- last_updated: 2026-07-10 · O（B→C→D 收口）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  Branch-G1 execute · T5 append 协议收口 · branch_ai_closed；
  **禁止**标 Phase closure · **禁止**改 Phase%／master_status。
- reviewer_notes: >-
  AC-1..AC-5 PASS；conclusion=accepted；交棒 scribe。

---

## B_REPORT
<!-- Implementer 填 -->

- changed_files:
  - docs/progress-dashboard-append-protocol-v1.md（新建）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.5 MAY · G1 写入边界指针）
  - docs/index.md（导航 + changelog）
  - 04_Workflows/tickets/FP-G1-T5-constitution-progress-append-protocol-v1_state.md（B_REPORT）
- artifacts:
  - docs/progress-dashboard-append-protocol-v1.md — 权限表 · 末尾模板 · Phase% enforcement
- verification:
  - cmd: `rg "append-only|evidence_tier|Phase%|non_claims" docs/progress-dashboard-append-protocol-v1.md`
  - result: ok · 命中 append-only／evidence_tier／Phase% 禁止／non_claims
  - cmd: `rg "progress-dashboard-append" 04_Workflows/WORKFLOW_INDEX.md docs/index.md`
  - result: ok · MAY 交叉引用命中
- behavior_notes: doc-only；链 §6.2–§6.3／OPS_CYCLE；不改 Dashboard／master_status
- deferred_items: FP-G5-T3 可消费本协议作 lane 模板（并行／下游）

---

## C_REPORT
<!-- Reviewer 填 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  AC-1 PASS：谁可写 Progress／Dashboard／master_status 表齐全。
  AC-2 PASS：末尾模板含 evidence_tier · run_url · group_id · blocked/next。
  AC-3 PASS：lane 禁止改 Phase% enforcement 句明确。
  AC-4 PASS：rg 命中。
  AC-5 PASS：未改 Phase%／master_status／core。
- risk_level: low
- suggestions: 与 FP-G5-T3 模板交叉引用即可；本档为边界 SSOT

---

## D_REPORT
<!-- Scribe 填 -->

- docs_updates:
  - docs/progress-dashboard-append-protocol-v1.md（本票正文）
  - docs/index.md 导航 + changelog
  - WORKFLOW_INDEX §1.5 一句
- progress_entry: |
  2026-07-10 · FP-G1-T5 done · Progress/Dashboard append 协议 · Reviewer accepted · 禁改 Phase%
- followup_suggestions:
  - lane／Scribe 一律 append-only；Phase% 仅 Governance 票

