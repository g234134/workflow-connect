# TICKET STATE · FP-G5-T1-fleet-metrics-dashboard-doc-v1 · MC-METRICS fleet 视图 operator doc

> Full-Phase G5 · P5 · **doc/spec** · arrange 2026-07-10
> 對齊：`W-MASTER-full-phase-plan_state.md#G5`
> 收口標籤：`branch_ai_closed`（AI 可達段）≠ Phase closure；`branch_human_gated`（批文／GA）另掛

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange-only · 不代跑 Implementer -->

- Goal: 產出 MC-METRICS fleet 視圖 operator doc（如何讀／聚合／與既有 metrics HTTP 交叉引用）。
- Scope:
  - MUST：新建 `docs/fleet-metrics-dashboard-operator-v1.md`
  - MUST：鏈 MP-METRICS／MC-METRICS · metrics HTTP · Dashboard §Metrics（不寫 %）
  - MUST：non_claims：doc ≠ Grafana 已上線 · ≠ P5 closure
  - MAY：INDEX／docs/index 一句
- NonScope:
  - 新建 Grafana dashboard · 改 metrics runtime · Phase% · 暗部
- AllowedPaths:
  - `docs/fleet-metrics-dashboard-operator-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G5-T1-fleet-metrics-dashboard-doc-v1_state.md`（B_REPORT）
- BlockedPaths:
  - `core/**` · `scripts/**`／`tests/**`（除唯讀引用）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格 · branch protection
  - 治理母本（`HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`）全文改寫
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）· `master_status.md`／`handoff.md`（Governance）
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票 B_REPORT）
- Dependencies:
  - 無硬阻塞；∥ FP-G5-T2／T3；下游串行 FP-G5-T4
- AcceptanceCriteria:
  - AC-1：operator doc 含 fleet 讀法／聚合邊界
  - AC-2：鏈既有 metrics 腳本或 INDEX runner
  - AC-3：`rg "fleet|MC-METRICS|non_claims" docs/fleet-metrics-dashboard-operator-v1.md` 命中
  - AC-4：未改 core／workflows／Phase%

### Wave Master 擴展

- wave_id: null
- group_id: G5
- lifecycle_phase: B
- phase_targets: [P5]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [MP-METRICS-HTTP-std-case-metrics-endpoint-v1, MC-METRICS-multi-case-metrics-aggregation-v1]
  - downstream_waves: [FP-G5-T4-audit-quickview-fleet-extension-v1]
  - blocks_if_missing: []
- risks:
  - id: RSK-G5-T1-01
    description: doc 被讀成 Grafana／fleet 已上線
    likelihood: M
    impact: H
    mitigation: non_claims 置頂 · 僅 doc AllowedPaths · Orchestrator arrange-only
    residual: accept
- observability:
  - verify_commands:
    - "rg "fleet|MC-METRICS|non_claims" docs/fleet-metrics-dashboard-operator-v1.md"
  - evidence_artifacts:
    - docs/fleet-metrics-dashboard-operator-v1.md
  - trace_fields: []
  - success_signals: [FRAME doc 存在 · 無 workflows／Phase%／core 變更]
  - failure_signals: [改 workflows · 宣稱 Phase closure／批文已齊]
- non_claims:
  - operator doc ≠ Grafana 已部署 · ≠ P5 closure
  - ≠ Phase closure
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true
- closure_tags:
  - branch_ai_closed: operator doc AI 可達
  - branch_human_gated: 無（本票）
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: done
- implementation_status: doc_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 無 · 本票已關；解鎖 FP-G5-T4；勿標 Phase closure／Grafana 真接 PG
- last_updated: 2026-07-10 · D（scribe_closed · overall done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  Branch-G5 execute · T1→T4 串行解鎖。收口僅 branch_ai_closed；禁止 Phase closure。
- reviewer_notes: >-
  AC-1..AC-4 PASS；conclusion=accepted；交棒 scribe。
- closure_tag: branch_ai_closed

---

## B_REPORT
<!-- Implementer 填 -->

- changed_files:
  - docs/fleet-metrics-dashboard-operator-v1.md（新建）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.5 MAY 一句）
  - docs/index.md（导航一行 + changelog）
  - 04_Workflows/tickets/FP-G5-T1-fleet-metrics-dashboard-doc-v1_state.md（B_REPORT）
- artifacts:
  - docs/fleet-metrics-dashboard-operator-v1.md — fleet 读法／聚合边界 · 链 MP／MC／HTTP · non_claims 置顶
- verification:
  - cmd: `rg "fleet|MC-METRICS|non_claims" docs/fleet-metrics-dashboard-operator-v1.md`
  - result: ok · 命中 non_claims／fleet／MC-METRICS／聚合边界
  - cmd: `rg "fleet-metrics-dashboard-operator" 04_Workflows/WORKFLOW_INDEX.md docs/index.md`
  - result: ok · MAY 交叉引用命中
- behavior_notes: doc-only；不改 scripts／core／workflows／Phase%；不宣称 Grafana 已上线
- deferred_items: Grafana／PG soak → T2 deferred 索引；audit fleet 聚合 → T4

---

## C_REPORT
<!-- Reviewer 填 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  AC-1 PASS：含单 case→fleet 读法与聚合边界表。
  AC-2 PASS：链 export／HTTP／aggregate 与 INDEX §1.5。
  AC-3 PASS：rg 命中 fleet｜MC-METRICS｜non_claims。
  AC-4 PASS：未改 core／workflows／Phase%。
- risk_level: low
- suggestions: Reviewer 遇「Grafana 已上线」句式可链本档 non_claims + T2 deferred

---

## D_REPORT
<!-- Scribe 填 -->

- docs_updates:
  - docs/fleet-metrics-dashboard-operator-v1.md（本票正文）
  - docs/index.md 导航 + changelog
  - WORKFLOW_INDEX §1.5 一句
- progress_entry: |
  2026-07-10 · FP-G5-T1 done · fleet metrics operator doc · Reviewer accepted · 解锁 T4 · branch_ai_closed
- followup_suggestions:
  - 升 READY 并执行 FP-G5-T4
  - 勿宣称 Grafana／P5 closure
