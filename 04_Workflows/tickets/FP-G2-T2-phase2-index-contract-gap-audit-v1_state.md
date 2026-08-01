# TICKET STATE · FP-G2-T2-phase2-index-contract-gap-audit-v1 · Phase2 index contract gap audit

> Full-Phase G2 · P2 · **doc-only** · WA-T1 vs 實際 ingest／index 能力 gap 審計  
> 對齊：`W-MASTER-full-phase-plan_state.md#G2` · `LANE-A` A-G2-T2  
> 母票：`FP-G2-index-job_state.md`

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 -->

- Goal: 產出 **schema／能力漂移清單**：`docs/phase2-knowledge-indexing-contract-v1.md`（WA-T1）對照當前 ingest_verify · repo index · observability `index_cases`／`kb_index_status` 實際能力，每條 gap 附 verify 引用與建議後續票。
- Scope:
  - MUST：新建 `docs/phase2-index-contract-gap-audit-v1.md`（gap 表 · 優先級 · 建議票 · `non_claims`）
  - MUST：`WORKFLOW_INDEX.md` §1.24 追加本 audit 交叉引用一句
  - MUST：本票 B／C／D_REPORT
  - MAY：`docs/index.md` 導航一行（可選）
- NonScope:
  - 修復所有 gap · 新 mandatory index job · 改 `core/**`／tests 行為
  - Phase% 上調 · workflows · GraphRAG 升主路 · 宣稱 gap 已修
- AllowedPaths:
  - `docs/phase2-index-contract-gap-audit-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.24 一句）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G2-T2-phase2-index-contract-gap-audit-v1_state.md`
- BlockedPaths:
  - `core/**` · `tests/**`（唯讀可跑 unittest）· `.github/workflows/**`
  - Dashboard Phase% · 治理母本 · 憲法 §7 · 暗部
- Dependencies:
  - DNR-G2-03 WA-T1；唯讀 `docs/knowledge-layer.md` · `docs/observability.md` §index
- AcceptanceCriteria:
  - AC-1：gap 表含欄位：id · 期望（contract）· 實際 · 優先級 · 建議票
  - AC-2：每條 gap 有 verify 命令或 artifact 路徑引用
  - AC-3：文檔含 `non_claims`：審計 ≠ 已修復 · ≠ P2 closure
  - AC-4：`python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v` 仍 OK（回歸）
  - AC-5：`rg "phase2-index-contract-gap-audit" 04_Workflows/WORKFLOW_INDEX.md` 命中

### Wave Master 擴展

- wave_id: null
- group_id: G2
- lifecycle_phase: B
- phase_targets: [P2]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [WA-T1-phase2-knowledge-indexing-contract-v1]
  - downstream_waves: [FP-G2-T3-rag-e2e-answer-frame-v1, FP-G2-T1-index-job-scheduler-hook-v1]
  - blocks_if_missing: []
- risks:
  - id: RSK-G2-T2-01
    description: 審計被讀成「已修復／可上調 Phase%」
    likelihood: M
    impact: M
    mitigation: non_claims 置頂 · Reviewer 檢查
    residual: accept
- observability:
  - verify_commands:
    - "python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v"
    - "rg \"GAP-|non_claims|phase2-index-contract-gap-audit\" docs/phase2-index-contract-gap-audit-v1.md"
    - "rg \"phase2-index-contract-gap-audit\" 04_Workflows/WORKFLOW_INDEX.md"
  - evidence_artifacts:
    - docs/phase2-index-contract-gap-audit-v1.md
  - trace_fields: []
  - success_signals: [gap 表非空 · INDEX 交叉引用 · unittest OK]
  - failure_signals: [宣稱已修復 · 改 core]
- non_claims:
  - gap audit ≠ 已修復所列 gap
  - 本票 ≠ 新 index job 落地 · ≠ Phase% 上調
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · D_scribe_done · orch_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无（本票收口）· 下游派 `FP-G2-T1`
- last_updated: 2026-07-10 · Orchestrator（同輪 O→B→C→D）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  arrange 同輪最小 doc 票關完。AC-1–AC-5 PASS。未改 core／workflows／Phase%。

---

## B_REPORT

- changed_files:
  - `docs/phase2-index-contract-gap-audit-v1.md`（新建）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.24 交叉引用）
  - `docs/index.md`（導航一行）
  - `04_Workflows/tickets/FP-G2-T2-phase2-index-contract-gap-audit-v1_state.md`
- artifacts:
  - `docs/phase2-index-contract-gap-audit-v1.md`
- verification: |
    - `python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v` → 13 tests OK
    - `rg "GAP-|non_claims" docs/phase2-index-contract-gap-audit-v1.md` → 命中
    - `rg "phase2-index-contract-gap-audit" 04_Workflows/WORKFLOW_INDEX.md` → 命中
- behavior_notes: 唯讀對照 contract／knowledge-layer／observability／Dashboard；不修 runtime。
- deferred_items: gap 修復交 T1／T3／T4／T5 與後續票

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    對照 FRAME：僅 AllowedPaths；gap 表含期望／實際／優先級／建議票；
    non_claims 明示審計≠修復；unittest 回歸綠；INDEX 交叉引用存在。
    未越權改 core／workflows／Phase%。
- risk_level: low
- suggestions: T1 施工時優先消費 GAP-SCHED／GAP-HOOK 列

---

## D_REPORT

- docs_updates:
  - `docs/phase2-index-contract-gap-audit-v1.md`（本票產物）
  - `WORKFLOW_INDEX` §1.24 · `docs/index.md` 導航
- progress_entry: 2026-07-10 · FP-G2-T2 gap-audit done · 建議下一動 FP-G2-T1
- followup_suggestions: 派 Implementer 執行 FP-G2-T1；T3 可在 T2 後開 FRAME
