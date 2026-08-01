# TICKET STATE · W5-T4-wave-plan-reviewer-checklist-v1 · Master Plan Review Checklist

> Master CP · Wave 5 · Reviewer checklist + rollup inspector + 附頁模板  
> Schema SSOT：`docs/ticket-schema-master-v1.md` · `W5-T2`  
> **注意**：舊檔 `W5-T4_state.md` 為 Phase 10.5 觀測歷史票 · **本檔**為 QUEUE / W-MASTER 所指 checklist 票。

---

## FRAME

- Goal: Master Reviewer 驗收 Chat 1–5 規劃質量時有專用 SSOT（playbook §5.3），並可 spot-check 跨 Wave 依賴與 observability；與戰術 `wave-next-code-inspector` 並列不混用。
- Scope:
  - `04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md`（§5.3 九項 + observability 抽樣）
  - `04_Workflows/review_checklists/wave-cross-rollup-inspector-v1.md`（引用 W5-T3 trace_fields · 不重定義）
  - `04_Workflows/tickets/_templates/ticket_reviewer_checklist.template.md`（AC 逐條 · 對齊 W5-T2 模板欄位）
  - `wave-next-code-inspector-v1.md` 文首 cross-ref（1–2 句）
- NonScope:
  - 不跑 prod/staging · 不改 workflow yml · 不替代人工 verdict
  - 不修改 W-MASTER 他 Wave 區塊 · 不擴 ticket_state.template 主 schema
- AllowedPaths:
  - `04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md`
  - `04_Workflows/review_checklists/wave-cross-rollup-inspector-v1.md`
  - `04_Workflows/review_checklists/wave-next-code-inspector-v1.md`（文首 only）
  - `04_Workflows/tickets/_templates/ticket_reviewer_checklist.template.md`
  - `04_Workflows/tickets/W5-T4-wave-plan-reviewer-checklist-v1_state.md`
- BlockedPaths:
  - `.github/workflows/**`
  - `core/**` · Dashboard Phase%
  - `W-MASTER-wave-plan_state.md` 他 Wave 正文結構
- Dependencies:
  - playbook §4 · §5
  - W5-T2（模板欄位）· W5-T3（rollup cross-ref · 本輪已交付）
- AcceptanceCriteria:
  - AC-1：plan-reviewer 含 §5.3 全部 9 項（blocking 一致）
  - AC-2：observability 合格／不合格示例各 ≥1（YAML）
  - AC-3：rollup inspector 引用 W5-T3 trace_fields · 無重複定義
  - AC-4：僅讀 checklist 可填 Master Plan Verdict 段
  - AC-5：ticket_reviewer_checklist.template 存在 · AC 逐條 · verification 占位 · over-claim · cross-ref W5-T2

### Wave Master 擴展

- wave_id: W5
- group_id: G4
- lifecycle_phase: B
- phase_targets: [P10]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W5-T2-wave-master-ticket-template-v1, W5-T3-evidence-ingestion-observer-v1]
  - downstream_waves: [Master Plan Review 使用]
  - blocks_if_missing: []
- risks:
  - id: RSK-W5-T4-01
    description: 與 wave-next-code-inspector 職責重疊
    likelihood: M
    impact: M
    mitigation: 文首職責分表 · 不同檔名
    residual: accept
  - id: RSK-W5-T4-02
    description: Wave 1–4 未完成時 rollup 無內容
    likelihood: H
    impact: L
    mitigation: rollup 標「執行階段啟用」
    residual: accept
- observability:
  - verify_commands:
    - "rg \"PLAN_READY|PLAN_REJECT\" 04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md"
    - "rg \"observability\" 04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md"
    - "rg \"wave-evidence-ingestion-spec|trace_fields\" 04_Workflows/review_checklists/wave-cross-rollup-inspector-v1.md"
  - evidence_artifacts:
    - wave-master-plan-reviewer-v1.md
    - wave-cross-rollup-inspector-v1.md
    - ticket_reviewer_checklist.template.md
  - trace_fields: [reviewer_verdict, blocking_issues, per_wave_notes]
  - success_signals: [checklist 與 playbook §5.3 項數一致]
  - failure_signals: [缺 blocking 標註 · 重定義 W5-T3 fields]
- non_claims:
  - 不替代 Master Reviewer 人工 verdict
  - 非 P10 runtime
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
  同輪開票關票。依賴 W5-T3 已交付。AC-1–AC-5 PASS。舊 W5-T4_state.md 未改。

---

## B_REPORT

- changed_files:
  - `04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md`
  - `04_Workflows/review_checklists/wave-cross-rollup-inspector-v1.md`
  - `04_Workflows/review_checklists/wave-next-code-inspector-v1.md`（文首分界）
  - `04_Workflows/tickets/_templates/ticket_reviewer_checklist.template.md`
  - `04_Workflows/tickets/W5-T4-wave-plan-reviewer-checklist-v1_state.md`
- artifacts:
  - Master Plan 9 項 checklist · rollup inspector · Reviewer 附頁模板
- verification:
  - `rg "PLAN_READY|PLAN_REJECT" 04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md` → 命中
  - `rg "observability" 04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md` → 命中合格/不合格 YAML
  - `rg "wave-evidence-ingestion-spec|W5-T3" 04_Workflows/review_checklists/wave-cross-rollup-inspector-v1.md` → 引用不重定義
  - 人工：§5.3 表 9 行 · blocking 標註與 playbook 一致
- behavior_notes: doc-only；rollup 標執行階段啟用
- deferred_items: 無

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
  AC-1–AC-5 PASS。§5.3 九項齊 · observability 雙示例 ·
  rollup 引用 W5-T3 · Verdict 模板可填 · 附頁模板存在。
  risk=low。
- risk_level: low
- suggestions: 無

---

## D_REPORT

- docs_updates:
  - review_checklists 三檔 · tickets/_templates 附頁
- progress_entry: |
  2026-07-09 · W5-T4 done · Master Plan Review checklist + rollup inspector · C=accepted
- followup_suggestions:
  - Master Plan Review 時使用本 checklist 填 W-MASTER C_REPORT
  - Downstream：W3-P89-SSOT 可排

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-07-09 | orch+B+C+D | 同輪開票關票 · 消費 W5-T3 |
