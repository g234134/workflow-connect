# TICKET STATE · FP-G5-T2-grafana-pg-soak-placeholder-index-v1 · Grafana/PG soak deferred 索引

> Full-Phase G5 · P5 · **doc/spec** · arrange 2026-07-10
> 對齊：`W-MASTER-full-phase-plan_state.md#G5`
> 收口標籤：`branch_ai_closed`（AI 可達段）≠ Phase closure；`branch_human_gated`（批文／GA）另掛

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange-only · 不代跑 Implementer -->

- Goal: 產出 Grafana／PG soak **deferred 索引** + infra 解阻條件（planning；本票可寫 doc，不執行 soak）。
- Scope:
  - MUST：新建 `docs/grafana-pg-soak-deferred-index-v1.md`（Landed vs Deferred · 解阻條件）
  - MUST：標 infra-only 前置；non_claims：索引 ≠ soak 已跑
  - MAY：INDEX／docs/index 一句
- NonScope:
  - 實際 Grafana 部署 · PG soak 執行 · 改 infra · Phase%
- AllowedPaths:
  - `docs/grafana-pg-soak-deferred-index-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G5-T2-grafana-pg-soak-placeholder-index-v1_state.md`（B_REPORT）
- BlockedPaths:
  - `core/**` · `scripts/**`／`tests/**`（除唯讀引用）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格 · branch protection
  - 治理母本（`HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`）全文改寫
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）· `master_status.md`／`handoff.md`（Governance）
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票 B_REPORT）
- Dependencies:
  - ∥ FP-G5-T1；infra 解阻另線（本票僅索引）
- AcceptanceCriteria:
  - AC-1：Landed vs Deferred 表 + infra 解阻條件
  - AC-2：non_claims 置頂
  - AC-3：`rg "Grafana|soak|deferred|infra|non_claims" docs/grafana-pg-soak-deferred-index-v1.md` 命中
  - AC-4：未改 infra／core／Phase%

### Wave Master 擴展

- wave_id: null
- group_id: G5
- lifecycle_phase: B
- phase_targets: [P5]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: ["Grafana/PG soak 執行與部署另線；本票僅 deferred 索引"]
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: []
  - downstream_waves: []
  - blocks_if_missing: []
- risks:
  - id: RSK-G5-T2-01
    description: deferred 索引被讀成 soak 已完成
    likelihood: M
    impact: H
    mitigation: non_claims 置頂 · 僅 doc AllowedPaths · Orchestrator arrange-only
    residual: accept
- observability:
  - verify_commands:
    - "rg "deferred|soak|non_claims" docs/grafana-pg-soak-deferred-index-v1.md"
  - evidence_artifacts:
    - docs/grafana-pg-soak-deferred-index-v1.md
  - trace_fields: []
  - success_signals: [FRAME doc 存在 · 無 workflows／Phase%／core 變更]
  - failure_signals: [改 workflows · 宣稱 Phase closure／批文已齊]
- non_claims:
  - deferred 索引 ≠ Grafana／soak 已落地
  - ≠ Phase closure
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true
- closure_tags:
  - branch_ai_closed: deferred 索引 AI 可達
  - branch_human_gated: 實際 soak 仍 infra
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: done
- implementation_status: doc_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 無 · 本票已關；實際 soak／Grafana 仍 infra／branch_human_gated
- last_updated: 2026-07-10 · D（scribe_closed · overall done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  Branch-G5 execute · planning/deferred 索引完成。收口 branch_ai_closed（索引）+ branch_human_gated（實際 soak）。
- reviewer_notes: >-
  AC-1..AC-4 PASS；conclusion=accepted；交棒 scribe。
- closure_tag: branch_ai_closed

---

## B_REPORT
<!-- Implementer 填 -->

- changed_files:
  - docs/grafana-pg-soak-deferred-index-v1.md（新建）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.5 MAY 一句）
  - docs/index.md（导航一行 + changelog）
  - 04_Workflows/tickets/FP-G5-T2-grafana-pg-soak-placeholder-index-v1_state.md（B_REPORT）
- artifacts:
  - docs/grafana-pg-soak-deferred-index-v1.md — Landed L-01…L-05 + Deferred D-01…D-06 · infra 解阻条件
- verification:
  - cmd: `rg "Grafana|soak|deferred|infra|non_claims" docs/grafana-pg-soak-deferred-index-v1.md`
  - result: ok · 命中 non_claims／Landed／Deferred／infra／soak
  - cmd: `rg "grafana-pg-soak-deferred" 04_Workflows/WORKFLOW_INDEX.md docs/index.md`
  - result: ok · MAY 交叉引用命中
- behavior_notes: doc-only planning；不执行 soak、不改 infra／core／Phase%
- deferred_items: D-01…D-06 仍须 infra／批文／另票

---

## C_REPORT
<!-- Reviewer 填 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  AC-1 PASS：Landed + Deferred + infra 解阻条件齐全。
  AC-2 PASS：non_claims 置顶。
  AC-3 PASS：rg 命中。
  AC-4 PASS：未改 infra／core／Phase%。
- risk_level: low
- suggestions: 遇「soak 已通过」句式链本档 §3 Deferred 阅读规则

---

## D_REPORT
<!-- Scribe 填 -->

- docs_updates:
  - docs/grafana-pg-soak-deferred-index-v1.md（本票正文）
  - docs/index.md 导航 + changelog
  - WORKFLOW_INDEX §1.5 一句
- progress_entry: |
  2026-07-10 · FP-G5-T2 done · Grafana/PG soak deferred 索引 · Reviewer accepted · 实际 soak 仍 infra
- followup_suggestions:
  - 勿把 deferred 当已验收；勿改 Phase%／真接 PG
