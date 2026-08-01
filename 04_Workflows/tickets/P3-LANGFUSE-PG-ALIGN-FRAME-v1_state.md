# TICKET STATE · P3-LANGFUSE-PG-ALIGN-FRAME-v1 · Langfuse↔PG 對齊 FRAME（僅設計）

> Wave C 前置 · 2026-07-15 · Multi-Chat O→B same_chat  
> 對齊：`plans/multi-phase-near-100-p1-p6-execution-plan.md` §P3 #2 · `docs/langfuse-pg-alignment-deferred-index-v1.md`  
> **切換**：原派 `P1-OPS-CHECKLIST-CLOSURE-v1` 與已封 `P1-GOV-RESIDUAL-CHECKOFF-v1` 重複 → 改開本票

---

## FRAME
<!-- Orchestrator 填：2026-07-15 凍結 -->

- Goal: 產出 Langfuse↔PG 對齊的 **honest planning FRAME**（欄位對照 · MVP/stretch · 解阻閘門 · 實作票占位）；**不接真 PG／不真接 Langfuse**。
- Scope:
  - MUST：`docs/p3-langfuse-pg-align-frame-v1.md`（含 non_claims · D-01–D-04 對照 · `trace_id` 主鍵 · 解阻清單 · 切換原因）
  - MUST：`tests/test_p3_langfuse_pg_align_frame_v1.py`（薄測 · 無 PG I/O）
  - MUST：`04_Workflows/tickets/P1-OPS-CHECKLIST-CLOSURE-v1_state.md` stub（`superseded` + 切換原因）
  - MAY：`docs/langfuse-pg-alignment-deferred-index-v1.md` 或 `docs/observability.md` 一行 cross-ref
- NonScope:
  - ≠ 真接 Langfuse API／改暗部 observability
  - ≠ 連真 PG／soak／migration／DSN
  - ≠ 實作 `P3-LANGFUSE-PG-ALIGN-IMPL-v1`
  - ≠ Dashboard Phase% apply · mandatory CI · 人卡項（H2–H5／濕墨）
  - ≠ Monitoring Graph L1／L2／selector 升格（D-04）
- AllowedPaths:
  - `docs/p3-langfuse-pg-align-frame-v1.md`
  - `tests/test_p3_langfuse_pg_align_frame_v1.py`
  - `04_Workflows/tickets/P3-LANGFUSE-PG-ALIGN-FRAME-v1_state.md`（B／C／D_REPORT；FRAME／STATE 僅 O）
  - `04_Workflows/tickets/P1-OPS-CHECKLIST-CLOSURE-v1_state.md`（stub only）
  - `docs/langfuse-pg-alignment-deferred-index-v1.md`（MAY · 一行 cross-ref）
  - `docs/observability.md`（MAY · 一行 cross-ref）
- BlockedPaths:
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 暗部 `core/**`、`.env`、venv 樹、runtime checkpoints
  - `.github/workflows/**` · branch protection · mandatory CI
  - Dashboard Phase% 數字格 · `_phase_pct_apply.py --authorize`
  - 治理母本全文改寫（`HARNESS_CONSTITUTION.md`／`ENGINEERING_CONTRACT.md`）
  - `00_Agent_Work_Progress.md`／`master_status.md`／`handoff.md`（Scribe／Governance）
  - 其他票 FRAME／STATE（除本票報告區與 P1 stub）
- Dependencies:
  - `FP-G3-T3-langfuse-pg-alignment-deferred-index-v1`（done）
  - `P3-TRACE-LOCAL-HARDEN-v1`（done · 本地錨點）
  - `P1-GOV-RESIDUAL-CHECKOFF-v1`（done · 觸發切換）
- relay_mode: same_chat
- phase_targets: [P3]
- baseline_pct: 82
- proposed_delta_pct: +0～+1
- evidence_gate: L-local · unittest + doc rg
- apply_phase_pct: false
- ticket_class: doc/spec
- evidence_tier: L-local
- non_claims:
  - ≠ Langfuse↔PG 已對齊完成
  - ≠ 真接 Langfuse／真 PG
  - ≠ P3 closure／Phase% apply
  - ≠ selector／SLO 升格（D-04）
- AcceptanceCriteria:
  - AC-1: `docs/p3-langfuse-pg-align-frame-v1.md` 含 MVP/stretch · `trace_id` · D-01/D-04 · non_claims · 切換原因
  - AC-2: `python -m unittest tests.test_p3_langfuse_pg_align_frame_v1 -v` 全綠
  - AC-3: P1 stub `overall_status: superseded` 且指向本票
  - AC-4: `apply_phase_pct: false`；無真 PG 連線／無暗部 core 變更
  - AC-5: ticket_class 為 doc/spec · planning；NonScope 明示不接真 PG

---

## STATE

- overall_status: done
- current_owner: scribe
- next_action: 無（已封存）；下一刀待尚書省派票（≠ 無批文開 IMPL）
- last_updated: 2026-07-15 · D（Scribe 封存）
- ops_checklist: 無
- status_by_role:
  - orchestrator: done — 切換裁決 + FRAME 凍結
  - implementer: done — FRAME doc + 薄測 + P1 stub
  - reviewer: done — accepted（AC-1～5）
  - scribe: done — D_REPORT + Progress 末尾 append
- orch_notes: >-
    MUST #3：P1-OPS 與 P1-GOV-RESIDUAL-CHECKOFF（done）範圍重複 → superseded stub；
    改開本 P3 FRAME。apply_phase_pct=false；不碰人卡。

---

## B_REPORT

- changed_files:
  - `docs/p3-langfuse-pg-align-frame-v1.md`（新建）
  - `tests/test_p3_langfuse_pg_align_frame_v1.py`（新建）
  - `04_Workflows/tickets/P3-LANGFUSE-PG-ALIGN-FRAME-v1_state.md`（新建）
  - `04_Workflows/tickets/P1-OPS-CHECKLIST-CLOSURE-v1_state.md`（superseded stub）
  - `docs/langfuse-pg-alignment-deferred-index-v1.md`（MAY · §4 cross-ref）
  - `docs/observability.md`（MAY · §7 一行 cross-ref）
- artifacts:
  - P3 Langfuse↔PG planning FRAME doc
  - P1-OPS superseded stub（切換留痕）
- verification:
  - `python -m unittest tests.test_p3_langfuse_pg_align_frame_v1 -v` → Ran 5 tests · OK
  - `rg "non_claims|MVP|stretch|trace_id|D-01|apply_phase_pct" docs/p3-langfuse-pg-align-frame-v1.md` → 命中
- behavior_notes:
  - doc-only + 薄測；零 PG I/O；複用 FP-G3-T3 deferred 索引，不重寫對齊實作
  - proposed P3 +0～+1 僅敘事 · 未 apply
- deferred_items:
  - `P3-LANGFUSE-PG-ALIGN-IMPL-v1`（須批文）
  - P1 R4 INDEX 輕修（仍 explicit defer · ≠ 本票）
---

## C_REPORT
<!-- Reviewer 填：2026-07-15 · C · same_chat -->

- conclusion: **accepted**
- blocking_issues: 無
- checks_summary: |
    AC-1 PASS：`docs/p3-langfuse-pg-align-frame-v1.md` 含 non_claims · MVP/stretch · `trace_id` · D-01/D-04 · 切換原因 · `apply_phase_pct=false`。
    AC-2 PASS：重跑 `python -m unittest tests.test_p3_langfuse_pg_align_frame_v1 -v` → Ran 5 tests · OK（C 親跑）。
    AC-3 PASS：`P1-OPS-CHECKLIST-CLOSURE-v1_state.md` → `overall_status: superseded` 且指向本票。
    AC-4 PASS：票 FRAME `apply_phase_pct: false`；薄測僅 Path 讀檔＋字串斷言，無 psycopg／DSN／connect；B_REPORT 變更均在 AllowedPaths（含 MAY 一行 cross-ref）。
    AC-5 PASS：`ticket_class: doc/spec` · NonScope／§0 non_claims 明示不接真 PG／≠ 真對齊／≠ Phase% apply／≠ D-04。
    邊界：設計-only；IMPL 占位 `P3-LANGFUSE-PG-ALIGN-IMPL-v1` 標「須批文」；未觸憲法 §7 類型。
- risk_level: low
- suggestions: |
    next=scribe（請 D 收口：Progress 末尾 + D_REPORT；Phase 影響：proposed +0～+1 · 實際上調=否／待 W-PROG）。
    下一無批文薄刀（非人卡／非真 PG IMPL）：建議 `P1` R4 INDEX 假陰性輕修（仍 explicit defer 敘事收斂 · doc-only），或另開 Wave C 下一張 P3/P* **doc/spec FRAME**（同樣 `apply_phase_pct=false`）。
    **禁止**無批文直接開 `P3-LANGFUSE-PG-ALIGN-IMPL-v1`。
- next_owner_hint: scribe

---

## D_REPORT
<!-- Scribe 填：2026-07-15 · D · same_chat 封存 -->

- docs_updates:
  - 本輪無新增 docs 改寫（B 已交 `docs/p3-langfuse-pg-align-frame-v1.md` + MAY cross-ref；C accepted）
  - Progress 末尾 append 本票戰報（憲法 §6.2）
- progress_entry: >
    2026-07-15 · P3-LANGFUSE-PG-ALIGN-FRAME-v1 · done · Reviewer accepted ·
    Langfuse↔PG planning FRAME（doc/spec）封存；P1-OPS superseded stub；
    Phase 實際上調=否／待 W-PROG；non_claims：≠ 真 PG · ≠ IMPL · ≠ Phase% uplift
- followup_suggestions:
  - 可派：P1 R4 INDEX 假陰性輕修（doc-only · explicit defer），或 Wave C 下一張 P3/P* doc/spec FRAME（`apply_phase_pct=false`）
  - **禁止**無批文開 `P3-LANGFUSE-PG-ALIGN-IMPL-v1`；**禁止** `--authorize`／Dashboard Phase% 數字格
- phase_impact:
  - 影響 Phase: P3
  - baseline: 82
  - proposed_delta: +0～+1
  - 實際上調: 否／待 W-PROG
  - non_claims: ≠ 真 PG · ≠ IMPL（`P3-LANGFUSE-PG-ALIGN-IMPL-v1`）· ≠ Phase% uplift · ≠ Langfuse↔PG 已對齊完成 · ≠ D-04／selector 升格
