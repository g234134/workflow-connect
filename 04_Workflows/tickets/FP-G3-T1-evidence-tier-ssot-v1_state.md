# TICKET STATE · FP-G3-T1-evidence-tier-ssot-v1 · Evidence tier 統一 SSOT

> Full-Phase · group_id **G3** · **doc/spec** · execute 2026-07-10
> 對齊：`W-MASTER-full-phase-plan_state.md#G3` · QUEUE Batch-3
> 收口：`branch_ai_closed` ≠ Phase closure

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 -->

- Goal: 將 L-local／CI-advisory／GA-remote 證據 tier 契約標為 Full-Phase G3 SSOT 並對齊既有 index。
- Scope:
  - MUST：對齊／升格 `docs/evidence-tier-contract-v1.md`（三 tier 固定命名 · non_claims）
  - MUST：修正過時「OBS 待建」交叉引用（若有）
  - MAY：`docs/index.md` 導航一行 · WORKFLOW_INDEX 一句（若有對應節）
- NonScope:
  - 改三 tier 定義發明新名
  - 代跑 GA／改 Phase%
  - 改 workflows
- AllowedPaths:
  - `docs/evidence-tier-contract-v1.md`
  - `04_Workflows/tickets/FP-G3-T1-evidence-tier-ssot-v1_state.md`（B/C/D_REPORT）
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
  - AC-1：contract 含三 tier + non_claims + ticket 歸因
  - AC-2：`rg "L-local|CI-advisory|GA-remote|non_claims" docs/evidence-tier-contract-v1.md` 命中
  - AC-3：未改 Phase%／workflows／core

### Wave Master 擴展

- wave_id: null
- group_id: G3
- lifecycle_phase: O
- phase_targets: [P3]
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
  Batch-3 execute · FP-G3-T1-evidence-tier-ssot-v1 doc/spec 同輪 O→B→C→D 收口。既有 2026-06-26 正文保留；本輪升格 Full-Phase G3。
- reviewer_notes: >-
  AC PASS；conclusion=accepted；交棒 scribe。
- closure_tag: branch_ai_closed

---

## B_REPORT

- changed_files:
  - docs/evidence-tier-contract-v1.md（SSOT 歸因＋OBS 交叉引用）
  - 04_Workflows/tickets/FP-G3-T1-evidence-tier-ssot-v1_state.md
- artifacts:
  - docs/evidence-tier-contract-v1.md
- verification:
  - cmd: `rg "L-local|CI-advisory|GA-remote|non_claims|FP-G3-T1" docs/evidence-tier-contract-v1.md`
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
  - docs/evidence-tier-contract-v1.md
  - docs/index.md（MAY）
- progress_entry: |
  2026-07-10 · FP-G3-T1-evidence-tier-ssot-v1 done · Evidence tier 統一 SSOT · Reviewer accepted · branch_ai_closed ≠ Phase closure
- followup_suggestions:
  - 勿把本 doc 當 prod／GA／required CI 已落地
