# TICKET STATE · FP-PHASE-IMPACT-protocol-v1 · Phase Progress Impact Protocol

> Governance doc · **doc/spec** · same_chat O→B→C→D · 2026-07-13  
> 對齊：`docs/progress-dashboard-append-protocol-v1.md` · `docs/lane-progress-append-template-v1.md`

---

## FRAME
<!-- Orchestrator 凍結 · 2026-07-13 -->

- Goal: 落地 Phase 影響協議 v1：普通票只提案 Δ；僅授權 W-PROG 可寫 Dashboard Phase% 數字格。
- Scope:
  - MUST：新建 `docs/phase-progress-impact-protocol-v1.md`（FRAME 五欄 · B/C/D/Progress「Phase 影響」· 寫入規則）
  - MUST：更新 lane 模板 · progress-dashboard 協議（提案 Δ vs 寫入 %）· `multi_chat_roles.mdc` O/D · role-prompts O/B/C/D
  - MAY：WORKFLOW_INDEX 一句索引
- NonScope:
  - 改 Dashboard Phase% 數字（本票 `apply_phase_pct: false`）· core／tests／workflows · 暗部 · .env
- AllowedPaths:
  - `docs/phase-progress-impact-protocol-v1.md`
  - `docs/lane-progress-append-template-v1.md`
  - `docs/progress-dashboard-append-protocol-v1.md`
  - `.cursor/rules/multi_chat_roles.mdc`
  - `.cursor/skills/multi-chat-ticket-workflow/role-prompts.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `04_Workflows/tickets/FP-PHASE-IMPACT-protocol-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（Scribe 末尾 append only）
- BlockedPaths:
  - `core/**` · `tests/**` · `scripts/**`（除唯讀）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格
  - 治理母本全文改寫 · `master_status.md`／`handoff.md`
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
- Dependencies:
  - FP-G1-T5 · FP-G5-T3（互鏈）
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：協議含 FRAME 五欄（含 `apply_phase_pct: false` 預設）
  - AC-2：B/C/D/Progress「Phase 影響」必填語義齊
  - AC-3：普通票只提案；唯一寫數字格=W-PROG／Governance
  - AC-4：互鏈 progress-dashboard + lane 模板
  - AC-5：`rg "apply_phase_pct|proposed_delta_pct|Phase 影響|non_claims" docs/phase-progress-impact-protocol-v1.md` 命中
  - AC-6：未改 Dashboard 數字／core／workflows

### Wave Master 擴展

- wave_id: null
- group_id: G1
- lifecycle_phase: O
- phase_targets: [P1, P5]
- baseline_pct: "n/a（協議票 · 不改 %）"
- proposed_delta_pct: "0"
- evidence_gate: L-local
- apply_phase_pct: false
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [FP-G1-T5-constitution-progress-append-protocol-v1, FP-G5-T3-progress-append-template-v1]
  - downstream_waves: [W-PROG-phase-progress-refresh-2026-07-13]
  - blocks_if_missing: []
- risks:
  - id: RSK-PHASE-IMPACT-01
    description: 協議被誤讀為可改 Phase%
    likelihood: M
    impact: H
    mitigation: apply_phase_pct 預設 false · non_claims 置頂 · Reviewer 檢查
    residual: accept
- observability:
  - verify_commands:
    - 'rg "apply_phase_pct|proposed_delta_pct|Phase 影響|non_claims" docs/phase-progress-impact-protocol-v1.md'
    - 'rg "提案 Δ|写入 %|Phase 影響" docs/progress-dashboard-append-protocol-v1.md docs/lane-progress-append-template-v1.md'
  - evidence_artifacts:
    - docs/phase-progress-impact-protocol-v1.md
  - success_signals: [協議存在 · roles／prompts 含 Phase 影響 MUST]
  - failure_signals: [改 Dashboard 數字 · 宣稱 Phase closure]
- non_claims:
  - 協議 doc ≠ 已改 Dashboard／master_status 數字
  - ≠ Phase closure · ≠ prod／required CI
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- lifecycle_phase: O
- current_owner: none
- next_action: 無 · 協議已落地；消費方見 W-PROG-2026-07-13
- last_updated: 2026-07-13 · O（same_chat B→C→D 收口）
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - docs/phase-progress-impact-protocol-v1.md（新建）
  - docs/lane-progress-append-template-v1.md（Phase 影響欄）
  - docs/progress-dashboard-append-protocol-v1.md（提案 Δ vs 寫入 %）
  - .cursor/rules/multi_chat_roles.mdc（O／D MUST）
  - .cursor/skills/multi-chat-ticket-workflow/role-prompts.md（O／B／C／D 檢查）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.55 一句）
  - 04_Workflows/tickets/FP-PHASE-IMPACT-protocol-v1_state.md
- artifacts:
  - phase-progress-impact-protocol-v1.md
- verification:
  - cmd: `rg "apply_phase_pct|proposed_delta_pct|Phase 影響|non_claims" docs/phase-progress-impact-protocol-v1.md`
  - result: ok（預期命中）
  - cmd: `rg "提案 Δ|写入 %|Phase 影響" docs/progress-dashboard-append-protocol-v1.md docs/lane-progress-append-template-v1.md`
  - result: ok（預期命中）
- behavior_notes: doc-only；未改 Dashboard 數字格
- deferred_items: 無

### Phase 影響

- **影響 Phase**：P1／P5（治理／Dashboard 寫入邊界敘事）
- **baseline**：n/a
- **proposed_delta**：0
- **實際上調**：否（`apply_phase_pct: false`）
- **non_claims**：≠ Dashboard 數字變更 · ≠ Phase closure

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
  AC-1 PASS：FRAME 五欄 + 協議正文齊。
  AC-2 PASS：B/C/D/Progress 形狀與 lane／append 協議已互鏈。
  AC-3 PASS：寫入規則明確（僅 W-PROG）。
  AC-4 PASS：互鏈 progress-dashboard + lane。
  AC-5／AC-6：rg 預期命中；未改數字格／core／workflows。
- risk_level: low
- suggestions: W-PROG 票消費本協議時於 STATE 標「已授權寫入」

### Phase 影響

- **影響 Phase**：P1／P5
- **baseline**：n/a
- **proposed_delta**：0
- **實際上調**：否
- **non_claims**：Reviewer 確認未寫入 Phase%

---

## D_REPORT

- docs_updates:
  - docs/phase-progress-impact-protocol-v1.md（本票正文）
  - lane／append 協議互鏈
  - WORKFLOW_INDEX §1.55 一句
- progress_entry: |
  2026-07-13 · FP-PHASE-IMPACT-protocol-v1 done · Phase 影響協議 v1 · Reviewer accepted · apply_phase_pct 預設 false · 僅 W-PROG 可寫 %
- followup_suggestions:
  - 消費票：W-PROG-phase-progress-refresh-2026-07-13

### Phase 影響

- **影響 Phase**：P1／P5
- **baseline**：n/a
- **proposed_delta**：0
- **實際上調**：否
- **non_claims**：≠ Phase% uplift
