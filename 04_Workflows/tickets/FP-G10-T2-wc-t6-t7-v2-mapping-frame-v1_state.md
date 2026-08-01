# TICKET STATE · FP-G10-T2-wc-t6-t7-v2-mapping-frame-v1 · WC-T6/T7 v2 path_id mapping FRAME

> Full-Phase · group_id **G10** · **doc/spec** · execute 2026-07-10
> 對齊：`W-MASTER-full-phase-plan_state.md#G10` · QUEUE Batch-3
> 收口：`branch_ai_closed` ≠ Phase closure

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 -->

- Goal: 產出 WC-T6/T7 v2 全量 path_id mapping 的 planning FRAME（不碰 distill runtime）。
- Scope:
  - MUST：新建 `docs/wc-t6-t7-v2-mapping-frame-v1.md`
  - MAY：`docs/index.md` 導航一行 · WORKFLOW_INDEX 一句（若有對應節）
- NonScope:
  - 改 distill runtime
  - LLM distillation
  - --execute 寫 live STATE
- AllowedPaths:
  - `docs/wc-t6-t7-v2-mapping-frame-v1.md`
  - `04_Workflows/tickets/FP-G10-T2-wc-t6-t7-v2-mapping-frame-v1_state.md`（B/C/D_REPORT）
  - `docs/index.md`（MAY）
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
- BlockedPaths:
  - `core/**` · `scripts/**`／`tests/**`（除唯讀）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格 · branch protection
  - 治理母本全文改寫 · `master_status.md`／`handoff.md`（Governance）
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票報告區）
- Dependencies: 見 QUEUE · Batch-3 arrange
- AcceptanceCriteria:
  - AC-1：mapping 範圍表 + NonScope
  - AC-2：non_claims 含 ≠ runtime
  - AC-3：rg 命中 path_id|wc.m2|planning|non_claims

### Wave Master 擴展

- wave_id: null
- group_id: G10
- lifecycle_phase: O
- phase_targets: [P10.5]
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true
- non_claims:
  - doc 就緒 ≠ Phase closure／prod flip／required CI
  - ≠ Round-2 GO · ≠ WC-PRE approved · ≠ GA 已跑
- closure_tags:
  - branch_ai_closed: true
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: done
- implementation_status: doc_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 無 · 本票已關；human-gated 項仍見 QUEUE human_ops_sequence
- last_updated: 2026-07-10 · D（scribe_closed · overall done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  Batch-3 execute · FP-G10-T2-wc-t6-t7-v2-mapping-frame-v1 doc/spec 同輪 O→B→C→D 收口。
- reviewer_notes: >-
  AC PASS；conclusion=accepted；交棒 scribe。
- closure_tag: branch_ai_closed

---

## B_REPORT

- changed_files:
  - docs/wc-t6-t7-v2-mapping-frame-v1.md（新建）
  - 04_Workflows/tickets/FP-G10-T2-wc-t6-t7-v2-mapping-frame-v1_state.md
- artifacts:
  - docs/wc-t6-t7-v2-mapping-frame-v1.md
- verification:
  - cmd: `rg "path_id|wc.m2|distill|planning|non_claims" docs/wc-t6-t7-v2-mapping-frame-v1.md`
  - result: ok · 關鍵詞命中（見本輪 verify 輸出）
- behavior_notes: doc-only；未改 core／workflows／Phase%／暗部
- deferred_items: human-gated／runtime 大缺口仍見 QUEUE global_blocked

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  對照 FRAME AC 全 PASS；non_claims 置頂；未越權改 workflows／Phase%／core。
- risk_level: low
- suggestions: 遇 over-claim 句式鏈本檔 non_claims

---

## D_REPORT

- docs_updates:
  - docs/wc-t6-t7-v2-mapping-frame-v1.md
  - docs/index.md（MAY）
- progress_entry: |
  2026-07-10 · FP-G10-T2-wc-t6-t7-v2-mapping-frame-v1 done · WC-T6/T7 v2 path_id mapping FRAME · Reviewer accepted · branch_ai_closed ≠ Phase closure
- followup_suggestions:
  - 勿把本 doc 當 prod／GA／required CI 已落地
