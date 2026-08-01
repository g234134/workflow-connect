# TICKET STATE · FP-G2-T4-graphrag-jobs-state-machine-v1 · graphrag_jobs 状态机设计

> Full-Phase G2 · P2 · **doc-only** · 非 P0 · blocked-but-worth-planning  
> 對齊：`W-MASTER-full-phase-plan_state.md#G2` · `LANE-A` A-G2-T4  
> 母票：`FP-G2-index-job_state.md` · 上游 gap：`docs/phase2-index-contract-gap-audit-v1.md` **GAP-GRAPH**

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange-only · frame_ready -->

- Goal: 產出 **graphrag_jobs** 状态机设计 doc（queued／running／succeeded／failed 等）與 observability 掛鉤點，供未來 index／GraphRAG 票消費；**本票不**做 DB migration／生產跑批。
- Scope:
  - MUST：新建 `docs/phase2-graphrag-jobs-state-machine-v1.md`，至少含：
    - 状态转移图（或等价表）+ 字段表
    - 鏈 WA-T1 contract · gap-audit **GAP-GRAPH** · observability `index_cases`／知識層 GraphRAG 邊界
    - **blocked／defer** 标注：生产 GraphRAG 跑批待 index hook／infra 解阻
    - `non_claims`：设计 doc ≠ GraphRAG 主路 · ≠ 已跑批验收
  - MUST：本票 B_REPORT／验证命令（rg）
  - MAY：`WORKFLOW_INDEX.md` §1.24 一句交叉引用
  - MAY：`docs/index.md` 导航一行
- NonScope:
  - DB migration · 生产 GraphRAG 跑批 · 改 `core/**`／selector
  - 宣称 GraphRAG 已验收 · Phase% 上调 · workflows
  - E2E LLM synthesis（→ T3）· smoke_corpus 扩档（→ T5）
  - 暗部 §7 · 金鑰 · human-blocked
- AllowedPaths:
  - `docs/phase2-graphrag-jobs-state-machine-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（仅 §1.24 一句 MAY）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G2-T4-graphrag-jobs-state-machine-v1_state.md`（B_REPORT）
- BlockedPaths:
  - `core/**` · `tests/**`（除唯读引用）· 暗部
  - `.github/workflows/**` · Dashboard Phase%
  - 治理母本 · Progress 历史段 · 宪法 §7 类型
  - 其他票 FRAME／STATE（除本票 B_REPORT）
- Dependencies:
  - 无硬阻塞；建议读 T2 gap-audit **GAP-GRAPH** · WA-T1 · knowledge-layer GraphRAG 行
  - 可与 T3 并行（不同 artifact）
- AcceptanceCriteria:
  - AC-1：doc 含状态转移图（或等价表）+ 字段表
  - AC-2：doc 链 WA-T1 与／或 observability index 相关引用 + **GAP-GRAPH**
  - AC-3：doc 含 blocked／defer 标注与 `non_claims`
  - AC-4：`rg "graphrag_jobs|queued|running|succeeded|failed|non_claims|GAP-GRAPH" docs/phase2-graphrag-jobs-state-machine-v1.md` 命中
  - AC-5（MAY）：INDEX §1.24 一句命中本 doc

### Wave Master 擴展

- wave_id: null
- group_id: G2
- lifecycle_phase: B
- phase_targets: [P2]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: ["生产 GraphRAG 跑批／DB（本票不交付）"]
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [WA-T1-phase2-knowledge-indexing-contract-v1, FP-G2-T2-phase2-index-contract-gap-audit-v1]
  - downstream_waves: []
  - blocks_if_missing: []
- risks:
  - id: RSK-G2-T4-01
    description: 过早施工 runtime／migration
    likelihood: M
    impact: H
    mitigation: NonScope + blocked 标注 · AllowedPaths 仅 doc
    residual: accept
- observability:
  - verify_commands:
    - "rg \"graphrag_jobs|queued|running|non_claims|GAP-GRAPH\" docs/phase2-graphrag-jobs-state-machine-v1.md"
  - evidence_artifacts:
    - docs/phase2-graphrag-jobs-state-machine-v1.md
  - trace_fields: []
  - success_signals: [状态机 doc 存在 · 无 core／DB 变更]
  - failure_signals: [migration · 宣称 GraphRAG 主路]
- non_claims:
  - 设计 doc ≠ GraphRAG 已落地／已验收
  - 本票 ≠ P2 closure · ≠ 生产跑批
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- implementation_status: doc_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无 · 票已关；勿宣称 GraphRAG 主路／P2 closure；T5 仍 PM-blocked
- last_updated: 2026-07-10 · O/B/C/D（同轮 execute 收口 · 并行保留 T3 DONE）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  同轮 O→B→C→D：状态机设计 doc 交付；AC-1–AC-5 PASS；Reviewer accepted；
  QUEUE 仅更新本票→DONE，并修正并行 T3 条目为 DONE（STATE 已 done）；
  未改 core／workflows／Phase%；未碰 T5／human-blocked。

---

## B_REPORT
<!-- Implementer 填 · 2026-07-10 -->

- changed_files:
  - `docs/phase2-graphrag-jobs-state-machine-v1.md`（新建）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.24 一句 MAY；保留 T3 行）
  - `docs/index.md`（导航一行 + 更新记录；保留 T3 行）
- artifacts: `docs/phase2-graphrag-jobs-state-machine-v1.md`（状态转移图／表 · 字段表 · GAP-GRAPH · WA-T1／obs 边界 · blocked／defer · non_claims）
- verification: |
    AC-1：§2 转移图+表 · §3 字段表 — PASS
    AC-2：链 WA-T1 · knowledge-layer · observability index_cases · **GAP-GRAPH** — PASS
    AC-3：§0 non_claims · §5 blocked／defer — PASS
    AC-4：`rg "graphrag_jobs|queued|running|succeeded|failed|non_claims|GAP-GRAPH" docs/phase2-graphrag-jobs-state-machine-v1.md` — 命中 PASS
    AC-5：`rg "phase2-graphrag-jobs-state-machine" 04_Workflows/WORKFLOW_INDEX.md` — 命中 PASS
    未改 core/** · .github/workflows/** · Phase% · T3/T5 正文
- behavior_notes: >-
  纯设计；MVP 四态 queued/running/succeeded/failed；cancelled/deferred 为 stretch；
  明确 index_cases ≠ graphrag_jobs SSOT；生产跑批 blocked on index hook／infra。
- deferred_items:
  - DB migration／强制 status enum（infra／data）
  - 生产 GraphRAG 跑批 runtime
  - run_id↔agent_runs 真接线（contract §6.4）
  - smoke_corpus → T5（PM）

---

## C_REPORT
<!-- Reviewer 填 · 2026-07-10 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
    FRAME 边界：仅 doc／INDEX／index；无 core／migration／workflows／Phase%。
    AC-1–AC-5：状态机+字段表、WA-T1／GAP-GRAPH／obs 边界、non_claims／blocked、rg 命中、INDEX 交叉引用 — 全 PASS。
    并行：未覆盖 T3 INDEX／index 行；未改 T3 STATE。
    non_claims 诚实：设计 ≠ GraphRAG 主路／已验收／P2 closure。
- risk_level: low
- suggestions: 未来 runtime 票须另开 FRAME；勿把本 doc 当 DDL 权威。

---

## D_REPORT
<!-- Scribe 填 · 2026-07-10 -->

- docs_updates:
  - `docs/phase2-graphrag-jobs-state-machine-v1.md`（本票产物）
  - `04_Workflows/WORKFLOW_INDEX.md` §1.24
  - `docs/index.md` 导航／更新记录
- progress_entry: >-
  2026-07-10 · FP-G2-T4 done · graphrag_jobs 状态机设计 doc · Reviewer accepted ·
  未改 core／workflows／Phase% · 勿宣称 GraphRAG 主路／P2 closure
- followup_suggestions:
  - 可选：GraphRAG runtime／migration 另开票（须解阻）
  - T5 仍 blocked on PM；勿无 FRAME 扩 smoke_corpus
