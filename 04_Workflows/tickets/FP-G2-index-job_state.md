# TICKET STATE · FP-G2-index-job · Full-Phase G2 Index Job（母票 · arrange）

> Full-Phase **G2** 母票 · **arrange-only** · 不直接施工 runtime  
> SSOT 正文：`W-MASTER-full-phase-plan_state.md#G2` · `LANE-A-full-phase-plan.md` Group 2  
> Schema：`docs/ticket-schema-master-v1.md` · W5-T2

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · 母票僅拆票／索引 -->

- Goal: 將 `FP-G2-index-job`（NOT_PLANNED 大範圍）拆成可派工子票，凍結 AllowedPaths／AC／依賴，並指定下一張最小可驗收增量。
- Scope:
  - MUST：盤點 G2 已落地（DNR）與缺口；產出子票分工表（T1–T5）
  - MUST：為可開工子票建立 `*_state.md` FRAME；更新 QUEUE／SESSION；Progress 末尾 append
  - MUST：優先開並（可選同輪關）最小 doc 票 `FP-G2-T2-phase2-index-contract-gap-audit-v1`
  - MAY：為 `FP-G2-T1` 凍結 FRAME（frame_ready · 下輪 execute）
- NonScope:
  - 本母票不改 `core/**`、不部署 cron、不跑全庫 re-ingest、不上調 Phase%
  - 不碰 human-blocked（P7 Round-2／P8.5 GA／P9 CI／WC-PRE／P6 nightly）
  - 不實作 GraphRAG／E2E LLM synthesis／smoke_corpus 擴檔
- AllowedPaths:
  - `04_Workflows/tickets/FP-G2*_state.md`
  - `04_Workflows/command_queue/QUEUE.yaml`
  - `04_Workflows/command_queue/SESSION.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - 子票 AllowedPaths（見各子票 FRAME）
- BlockedPaths:
  - 憲法 §7 類型 · `.github/workflows/**` · 暗部 core · 治理母本
  - Dashboard Phase% 數字格 · `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`
- Dependencies:
  - DNR-G2-01/02/03（ingest_verify · RAG smoke · WA-T1 contract）
  - `docs/phase2-knowledge-indexing-contract-v1.md` · `docs/full-phase-lane-map-v1.md` L2
- AcceptanceCriteria:
  - AC-1：子票表含 T1–T5 ID · AllowedPaths · AC 摘要 · 依賴 · 建議角色
  - AC-2：至少一張子票 `*_state.md` FRAME 凍結且 QUEUE 可派
  - AC-3：母票 STATE 標 `arranged`；Progress 有安排戰報
  - AC-4：未改 workflows／Phase%／金鑰

### Wave Master 擴展

- wave_id: null
- group_id: G2
- lifecycle_phase: O
- phase_targets: [P2]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [WA-T1-phase2-knowledge-indexing-contract-v1]
  - downstream_waves: [FP-G2-T1, FP-G2-T2, FP-G2-T3, FP-G2-T4, FP-G2-T5]
  - blocks_if_missing: []
- risks:
  - id: RSK-FP-G2-01
    description: 母票被當成 runtime 施工票導致無 FRAME 大改
    likelihood: M
    impact: H
    mitigation: ticket_class=scribe/ops · NonScope 明示 · 僅子票施工
    residual: accept
- observability:
  - verify_commands:
    - "rg \"FP-G2-T[1-5]\" 04_Workflows/tickets/FP-G2-index-job_state.md"
    - "rg \"overall_status\" 04_Workflows/tickets/FP-G2-T2*_state.md"
  - evidence_artifacts:
    - 04_Workflows/tickets/FP-G2-index-job_state.md
    - 04_Workflows/command_queue/QUEUE.yaml
  - trace_fields: []
  - success_signals: [子票 PLANNED/DONE · priority_next 指向可 execute 子票]
  - failure_signals: [仍 NOT_PLANNED 且無子票 STATE]
- non_claims:
  - arrange ≠ P2 closure · ≠ 规模化 index job 已落地
  - 母票 done/arranged ≠ GraphRAG／E2E 已驗收
- ticket_class: scribe/ops
- evidence_tier: L-local
- parallel_ok: false

---

## 現況盤點（2026-07-10 · Orchestrator）

### FP-G2 是什麼

Full-Phase **G2 — Knowledge · Index · RAG Corpus**（P2 · Dashboard **65%**）。QUEUE 別名 `FP-G2-index-job` 指向「规模化 index job · GraphRAG E2E」整包缺口，**不是**單檔 bugfix。

### 為何 NOT_PLANNED／大範圍

| 原因 | 說明 |
|------|------|
| 多能力捆綁 | index 排程 hook + contract gap + E2E 问答 + GraphRAG 状态机 + corpus 扩展 |
| 已有契約無排程 | WA-T1 contract **done**；Dashboard／lane-map 明示「本轮无新 index job」 |
| 部分 blocked | T5 需 PM verify；T3 串行 T2；T4 可規劃但不宜當 P0 runtime |
| 無子票 STATE | 僅 W-MASTER／LANE-A 草案表 · QUEUE 無法 execute |

### 已落地（DNR · 不可重做）

| ID | 能力 | 證據 |
|----|------|------|
| DNR-G2-01 | Phase1 ingest_verify · INV1–INV4 | Progress D2/D3 |
| DNR-G2-02 | R1/R2 retrieve + PG cross-check | rag smoke |
| DNR-G2-03 | WA-T1 knowledge indexing contract | `docs/phase2-knowledge-indexing-contract-v1.md` · unittest 13 OK |

### 依賴與阻塞

- **硬依賴**：WA-T1（已滿足）
- **軟依賴／串行**：T3←T2；T5←T1+PM
- **非本母票阻塞**：human-blocked 線（P7／P8.5／P9／WC-PRE／P6 nightly）— **不碰**
- **infra**：规模化排程落地可能需 infra／PM（寫入 T1 non_claims／解阻條件）

---

## 分工範圍表（子票草案 · 凍結）

| 子票 ID | 目的 | 類型 | AllowedPaths（摘要） | BlockedPaths（摘要） | AC（摘要） | 依賴 | 建議角色 | 本輪 |
|---------|------|------|----------------------|----------------------|------------|------|----------|------|
| **FP-G2-T2-phase2-index-contract-gap-audit-v1** | WA-T1 vs 實際能力 gap 審計 | doc/spec | `docs/phase2-index-contract-gap-audit-v1.md` · INDEX §1.24 · 本票 STATE | core · workflows · Phase% | gap 表+verify+non_claims | WA-T1 | B→C→D | **同輪關** |
| **FP-G2-T1-index-job-scheduler-hook-v1** | index job hook 設計 + skeleton CLI | build | `docs/phase2-index-job-hook-v1.md` · `scripts/run_index_job_hook_v1.py` · `tests/test_index_job_hook_v1.py` | 生產 cron · 重寫 ingest · GraphRAG 全量 | dry-run dict · unittest≥3 · 不寫生產 index | WA-T1；∥T2 | B→C→D | **FRAME 凍結 · 下輪派 B** |
| **FP-G2-T3-rag-e2e-answer-frame-v1** | RAG E2E 问答 FRAME（planning） | doc/spec | `docs/phase2-rag-e2e-answer-frame-v1.md` | LLM 實作 · selector 改線 | MVP vs stretch · 引用 T2 | **串行 T2** | B（planning） | **done（2026-07-10）** |
| **FP-G2-T4-graphrag-jobs-state-machine-v1** | graphrag_jobs 状态机设计 | doc/spec | `docs/phase2-graphrag-jobs-state-machine-v1.md` | DB migration · 生產跑批 | 状态图+字段 · 鏈 WA-T1 | ∥T1/T2 | B→C | **FRAME 凍結 · frame_ready（非 P0）** |
| **FP-G2-T5-smoke-corpus-expansion-v1** | smoke_corpus 扩展 FRAME | blocked/planning | `docs/phase2-smoke-corpus-expansion-frame-v1.md` | 實際擴檔 | PM 裁定項 · blocked until T1+PM | **串行 T1** · PM | B only | BLOCKED planning |

---

## STATE

- overall_status: arranged
- implementation_status: arrange_done · T1_T2_T3_done · T4_frame_ready · T5_blocked_PM
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 可選 execute `FP-G2-T4`（graphrag 状态机 doc）；T5 仍 PM-blocked
- last_updated: 2026-07-10 · Orchestrator（T3 done 收口）
- status_by_role:
  - orchestrator: done
  - implementer: n/a
  - reviewer: n/a
  - scribe: n/a
- orch_notes: >-
  母票 arranged。T1/T2/T3 done；T4 frame_ready；T5 仍 BLOCKED（PM）。
  未碰 human-blocked · workflows · Phase% · core。

---

## B_REPORT
<!-- 母票無 Implementer 施工 -->

- changed_files: 見本輪子票／QUEUE（母票僅 arrange）
- artifacts: 分工表（上節）
- verification: AC-1–AC-4 由 Orchestrator 自檢
- behavior_notes: 無 runtime 變更
- deferred_items: T4 doc 施工 · T5 待 PM

---

## C_REPORT
<!-- 母票無獨立 Reviewer；子票 T2 見其 C_REPORT -->

- conclusion: n/a
- blocking_issues: 無
- checks_summary: arrange 產出以 QUEUE + 子票 STATE 為準
- risk_level: low
- suggestions: 無

---

## D_REPORT
<!-- 母票戰報由 Progress append 承擔 -->

- docs_updates: 見 T2 gap-audit · T3 E2E FRAME · INDEX
- progress_entry: 2026-07-10 · FP-G2 · T1/T2/T3 done · T4 frame_ready
- followup_suggestions: execute `FP-G2-T4`；勿開 T5 直至 PM；勿宣稱 P2 closure／E2E 已驗收
