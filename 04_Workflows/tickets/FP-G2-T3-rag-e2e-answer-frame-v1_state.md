# TICKET STATE · FP-G2-T3-rag-e2e-answer-frame-v1 · RAG E2E 问答 FRAME

> Full-Phase G2 · P2 · **doc/spec · planning only** · 非本 sprint 施工 LLM／selector  
> 對齊：`W-MASTER-full-phase-plan_state.md#G2` · `LANE-A` A-G2-T3  
> 母票：`FP-G2-index-job_state.md` · 上游 gap：`docs/phase2-index-contract-gap-audit-v1.md` **GAP-E2E**

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange-only · frame_ready -->

- Goal: 為 **RAG E2E 问答／LLM synthesis** 大缺口產出 **honest planning FRAME doc**：MVP vs stretch、依賴（T2 gap + index 就緒）、驗收邊界與 **non_claims**；**本票不實作** runtime／不跑未定義 E2E。
- Scope:
  - MUST：新建 `docs/phase2-rag-e2e-answer-frame-v1.md`，至少含：
    - MVP vs stretch（何謂「可驗收 E2E 问答」vs GraphRAG／K-2 主答案升格）
    - 串行依賴：引用 `FP-G2-T2` gap 表 **GAP-E2E**（及相關 GAP-SCHED／GAP-GRAPH 邊界一句）
    - baseline：現有 rag smoke／retrieve 命令（僅引用，不擴跑未定義套件）
    - 解阻條件：index hook／infra／PM（若需）· 後續實作票建議 ID 占位
    - `non_claims`：FRAME ≠ demo 问答已驗收 · ≠ P2 closure · ≠ K-2 prod 主答案
  - MUST：本票 B_REPORT（doc 交付後）／驗證命令（rg + 可選 INDEX 一句）
  - MAY：`WORKFLOW_INDEX.md` §1.24 一句交叉引用本 FRAME doc
  - MAY：`docs/index.md` 導航一行
- NonScope:
  - LLM synthesis 實作 · prod RAG selector／ask 管線改線 · LangGraph 新圖
  - 宣稱 demo／E2E 问答已驗收 · Phase% 上調 · 改 `.github/workflows/**`
  - GraphRAG 生產跑批／DB migration（→ T4）· smoke_corpus 擴檔（→ T5）
  - K-2 prod 主答案／partial rollout（見 `docs/k2_deployment_governance.md`；本票僅分軌 non_claim）
  - 暗部 §7 · 金鑰 · human-blocked 六項 · 改 `core/**`
- AllowedPaths:
  - `docs/phase2-rag-e2e-answer-frame-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（僅 §1.24 一句 MAY）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G2-T3-rag-e2e-answer-frame-v1_state.md`（B_REPORT 區塊）
- BlockedPaths:
  - `core/**` · `tests/**`（除唯讀引用既有 rag／contract 測試名）· 暗部
  - `.github/workflows/**` · Dashboard Phase% 數字格
  - 治理母本（`HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`）
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）· 憲法 §7 類型
  - 其他票 FRAME／STATE（除本票 B_REPORT）
  - 未授權 runtime checkpoint／env／venv
- Dependencies:
  - **硬**：`FP-G2-T2-phase2-index-contract-gap-audit-v1`（**done**）· 必讀 gap-audit **GAP-E2E**
  - 建議讀：WA-T1 contract · LANE-A A-G2-T3 · T1 hook doc（index 就緒敘事）
  - **不**阻塞於 T4／T5；與 T4 可并行（不同 artifact）
- AcceptanceCriteria:
  - AC-1：doc 含明確 **MVP vs stretch** 分欄（可驗收定義 + 明確不做）
  - AC-2：doc **引用** T2 gap-audit（至少 `GAP-E2E`）與建議後續票邊界
  - AC-3：`ticket_class` 敘事為 **doc/spec · planning**（或 blocked/planning）；**無** runtime 變更
  - AC-4：doc 含 `non_claims`（FRAME ≠ E2E 已驗收 · ≠ P2 closure · ≠ K-2 主答案）
  - AC-5：`rg "phase2-rag-e2e-answer-frame|MVP|stretch|GAP-E2E|non_claims" docs/phase2-rag-e2e-answer-frame-v1.md` 命中
  - AC-6（MAY）：`rg "phase2-rag-e2e-answer-frame" 04_Workflows/WORKFLOW_INDEX.md` 命中（若做 INDEX 一句）

### Wave Master 擴展

- wave_id: null
- group_id: G2
- lifecycle_phase: B
- phase_targets: [P2]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: ["E2E 问答 runtime／LLM 接線另票；本票不交付"]
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [FP-G2-T2-phase2-index-contract-gap-audit-v1, WA-T1-phase2-knowledge-indexing-contract-v1]
  - downstream_waves: []
  - blocks_if_missing: [FP-G2-T2-phase2-index-contract-gap-audit-v1]
- risks:
  - id: RSK-G2-T3-01
    description: FRAME 被讀成「可立即跑 E2E／已驗收问答」
    likelihood: M
    impact: H
    mitigation: non_claims 置頂 · ticket_class=planning · Reviewer 檢查無 core diff
    residual: accept
  - id: RSK-G2-T3-02
    description: 與 K-2 主答案／selector 升格混淆
    likelihood: M
    impact: H
    mitigation: NonScope + non_claims 分軌；引用 K-2 治理 doc 僅作邊界
    residual: accept
- observability:
  - verify_commands:
    - "rg \"MVP|stretch|GAP-E2E|non_claims\" docs/phase2-rag-e2e-answer-frame-v1.md"
    - "rg \"phase2-rag-e2e-answer-frame\" docs/phase2-rag-e2e-answer-frame-v1.md 04_Workflows/WORKFLOW_INDEX.md"
  - evidence_artifacts:
    - docs/phase2-rag-e2e-answer-frame-v1.md
  - trace_fields: []
  - success_signals: [FRAME doc 存在 · MVP/stretch · 引用 GAP-E2E · 無 core 變更]
  - failure_signals: [改 selector／core · 宣稱 E2E 已驗收 · 跑未定義 E2E 套件冒充 AC]
- non_claims:
  - 本票 FRAME／doc ≠ RAG E2E 问答已落地或已驗收
  - 本票 ≠ P2 closure · ≠ Phase% 上調
  - 本票 ≠ K-2 prod 主答案 · ≠ GraphRAG 主路
  - baseline rag smoke 引用 ≠ 本票新跑通 E2E
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true  # after T2 done；∥ T4

---

## STATE

- overall_status: done
- implementation_status: doc_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无 · 票已关；可选并行 execute `FP-G2-T4`；勿宣称 E2E／P2 closure
- last_updated: 2026-07-10 · O/B/C/D（同轮 execute 收口）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  同轮 O→B→C→D：planning doc 交付；AC-1–AC-6 PASS；Reviewer accepted；
  QUEUE T3→DONE；未改 core／selector／workflows／Phase%；未跑未定义 E2E。

---

## B_REPORT
<!-- Implementer 填 · 2026-07-10 -->

- changed_files:
  - `docs/phase2-rag-e2e-answer-frame-v1.md`（新建）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.24 一句 MAY）
  - `docs/index.md`（导航一行 MAY）
- artifacts: `docs/phase2-rag-e2e-answer-frame-v1.md`（MVP/stretch · GAP-E2E · baseline 引用 · 解阻 · non_claims · ticket_class=doc/spec·planning）
- verification: |
    AC-1–AC-4：doc 含 MVP vs stretch、引用 GAP-E2E、ticket_class=planning、non_claims 置顶 — PASS（人工对照 FRAME）
    AC-5：`rg "phase2-rag-e2e-answer-frame|MVP|stretch|GAP-E2E|non_claims" docs/phase2-rag-e2e-answer-frame-v1.md` — 命中 PASS
    AC-6：`rg "phase2-rag-e2e-answer-frame" 04_Workflows/WORKFLOW_INDEX.md` — 命中 PASS
    本票 diff 范围：上述三路径；未改本票范围内的 `core/**`／未跑未定义 E2E
- behavior_notes: >-
  仅 planning；baseline 命令只引用不执行；K-2／GraphRAG／corpus 分轨 non_claim；
  建议后续 runtime 占位 `FP-G2-T3b-rag-e2e-answer-runtime-v1`（非本票）。
- deferred_items:
  - E2E／LLM synthesis runtime（另开 FRAME）
  - GraphRAG 状态机正文 → T4
  - smoke_corpus 扩 → T5（PM）

---

## C_REPORT
<!-- Reviewer 填 · 2026-07-10 · 唯读 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
    FRAME 边界：AllowedPaths 内 doc + INDEX/index 一句；BlockedPaths 未触（本票未改 core／tests／workflows／Phase%/治理母本）。
    AC-1 MVP vs stretch 分栏 ✓ · AC-2 GAP-E2E + 后续票边界 ✓ · AC-3 ticket_class=doc/spec·planning ✓
    AC-4 non_claims（≠E2E 已验收 · ≠P2 closure · ≠K-2 主答案）✓ · AC-5/AC-6 rg 命中 ✓
    RSK-G2-T3-01/02：non_claims 置顶 + K-2 分轨 — 可接受。
- risk_level: low
- suggestions: 工作树另有既有 core／workflow 脏档与本票无关；关票时勿一并宣称本票改动。

---

## D_REPORT
<!-- Scribe 填 · 2026-07-10 -->

- docs_updates:
  - 主产物已落 `docs/phase2-rag-e2e-answer-frame-v1.md`
  - INDEX §1.24／`docs/index.md` 交叉引用已加
- progress_entry: 2026-07-10 · FP-G2-T3 done · planning FRAME doc · Reviewer accepted · ≠ E2E 已验收／P2 closure
- followup_suggestions: execute `FP-G2-T4`（可并行）；T5 仍 PM-blocked；runtime E2E 另开票；勿碰 human-blocked
