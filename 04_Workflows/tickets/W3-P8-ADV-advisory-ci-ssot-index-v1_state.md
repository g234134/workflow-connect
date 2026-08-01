# TICKET STATE · W3-P8-ADV-advisory-ci-ssot-index-v1 · P8/P8.9 Advisory CI SSOT

> Wave 3 · P8 / P8.9 · **doc-only** · 消除 advisory / prod gate 混淆  
> Schema SSOT：`docs/ticket-schema-master-v1.md` · `W5-T2`

---

## FRAME

- Goal: Reviewer / Planner 能從單一索引分辨 P8/P8.9 **advisory CI** 與 **非 prod gate / 非 required check** 路徑，消除「CI 綠 = 可發 prod」誤讀。
- Scope:
  - `docs/P8_P89_ADVISORY_CI_INDEX.md`（SSOT 正文）
  - `04_Workflows/WORKFLOW_INDEX.md` §1.46「P8 / P8.9 · Advisory vs gate」
  - `docs/phase-8-operator-backlog-v1.md` · `docs/p8_9-verification-bundle-v1.md` 各一句 advisory 腳注
  - 交叉引用 inspector §3.2 · P7 分線 §1.45
- NonScope:
  - 不改 `.github/workflows/**` · 不升格 required · 不跑 GA · 不造 run URL
  - 不重寫 P7 / P8.5 / P9 主敘事 · 不改 smoke 行為 · 不上調 Phase%
- AllowedPaths:
  - `docs/P8_P89_ADVISORY_CI_INDEX.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/phase-8-operator-backlog-v1.md`
  - `docs/p8_9-verification-bundle-v1.md`
  - `04_Workflows/tickets/W3-P8-ADV-advisory-ci-ssot-index-v1_state.md`
- BlockedPaths:
  - `.github/workflows/**`
  - `core/**` · `tests/**`
  - Dashboard Phase% 數字格
- Dependencies:
  - W2-P7-advisory（分線 · 已 done）
  - WH-P85-CI-LAND · MP-SMOKE · CI-SMOKE · W-ORCH §P8.5
- AcceptanceCriteria:
  - AC-1：WORKFLOW_INDEX ≥3 條 P8/P8.9 CI/smoke · 每條 advisory 或 local-gate 標籤
  - AC-2：bridge-smoke 寫清 landing ≠ GA pass · Scenario 遠端另見 P8.5 ops-run
  - AC-3：run_ci_smoke_check 標 repo local release sanity · ≠ GitHub required
  - AC-4：對照 inspector §3.2 無反向敘事

### Wave Master 擴展

- wave_id: W3
- group_id: G8
- lifecycle_phase: B
- phase_targets: [P8, P8.9]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W2-P7-advisory-ci-ssot-index-v1, WH-P85-CI-LAND-v1, MP-SMOKE-std-case-multi-phase-smoke-v1]
  - downstream_waves: [W4-P85-S2-GA-RUNBOOK-v1 僅引用]
  - blocks_if_missing: []
- risks:
  - id: RSK-W3-ADV-01
    description: 讀者將 run_ci_smoke_check exit 1 誤當 GitHub blocking
    likelihood: M
    impact: H
    mitigation: 標 local script · 無 required 綁定
    residual: accept
  - id: RSK-W3-ADV-02
    description: bridge 索引與 P8.5 runbook 雙 SSOT
    likelihood: L
    impact: M
    mitigation: 本票只寫角色/advisory · 細節 defer runbook
    residual: accept
- observability:
  - verify_commands:
    - "rg \"advisory|local-only|local-gate|required\" 04_Workflows/WORKFLOW_INDEX.md"
    - "rg \"P8_P89_ADVISORY\" docs/P8_P89_ADVISORY_CI_INDEX.md"
  - evidence_artifacts:
    - docs/P8_P89_ADVISORY_CI_INDEX.md
    - WORKFLOW_INDEX §1.46
  - trace_fields: [ci_class]
  - success_signals: [三類路徑均有 advisory 或 local 標籤]
  - failure_signals: [條目寫 merge gate / required 而無批文]
- non_claims:
  - 非 prod-ready / INT Tier-A
  - 非 required CI 升格
  - 非 GA pass
  - 非 Phase% 上調
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
- last_updated: 2026-07-09 · Orchestrator（同輪 B→C→D→O）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  同輪開票並關票。AC-1–AC-4 PASS。未改 workflows / Phase%。

---

## B_REPORT

- changed_files:
  - `docs/P8_P89_ADVISORY_CI_INDEX.md`（新建）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.46）
  - `docs/phase-8-operator-backlog-v1.md`（腳注）
  - `docs/p8_9-verification-bundle-v1.md`（腳注）
  - `04_Workflows/tickets/W3-P8-ADV-advisory-ci-ssot-index-v1_state.md`
- artifacts:
  - P8/P8.9 advisory 索引表（bridge-smoke · run_ci_smoke_check · run_multi_phase_smoke）
- verification:
  - `rg "advisory|local-only|local-gate|required" 04_Workflows/WORKFLOW_INDEX.md` → §1.46 命中
  - `rg "P8_P89_ADVISORY|landing.*≠.*GA|local release sanity" docs/P8_P89_ADVISORY_CI_INDEX.md` → 命中
  - 人工對照 inspector §3.2：無反向敘事（仍標 advisory / non-required）
- behavior_notes: 純 doc；P7 分線保留 §1.45
- deferred_items: 無

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
  AC-1 PASS（INDEX ≥3 條 · 標籤齊）· AC-2 PASS（landing ≠ GA）·
  AC-3 PASS（local sanity ≠ required）· AC-4 PASS（§3.2 無反向）。
  risk=low · AllowedPaths 內 · 未改 workflows。
- risk_level: low
- suggestions: 無

---

## D_REPORT

- docs_updates:
  - WORKFLOW_INDEX §1.46 · P8_P89_ADVISORY_CI_INDEX · 兩份 docs 腳注
- progress_entry: |
  2026-07-09 · W3-P8-ADV done · P8/P8.9 advisory SSOT 索引 · C=accepted
- followup_suggestions:
  - Downstream：`W3-P89-SSOT-state-dashboard-alignment-v1` · W4 GA 票僅引用本索引

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-07-09 | orch+B+C+D | 同輪開票關票 |
