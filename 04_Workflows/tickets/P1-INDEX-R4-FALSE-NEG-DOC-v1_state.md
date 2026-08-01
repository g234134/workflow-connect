# TICKET STATE · P1-INDEX-R4-FALSE-NEG-DOC-v1 · P1 R4 INDEX 假陰性輕修

> near-100 · Wave 2／無批文薄刀 · 2026-07-15 · Multi-Chat O→B same_chat  
> 上游：`P1-GOV-RESIDUAL-CHECKOFF-v1` R4 **explicit defer** → 本票清 defer

---

## FRAME

- Goal: 以 **doc-only** 輕修消除 `WORKFLOW_INDEX` ↔ 既有 runbooks／thin 入口的**假陰性**（INDEX 宣稱缺入口但檔案已存在），並將 P1 checkoff R4 改為 **done**。
- Scope:
  - MUST：新建 `docs/p1-index-r4-false-neg-doc-v1.md`（假陰性清單 · 修正對照 · non_claims · 驗收命令）
  - MUST：輕修 `04_Workflows/WORKFLOW_INDEX.md` **§2／§2.1**（及既有 GraphRAG 索引句最小交叉引用）；**禁止**全文重寫
  - MUST：更新 `docs/p1-gov-residual-checkoff-v1.md` R4 → **done** + 本票證據
  - MUST：薄測 `tests/test_p1_index_r4_false_neg_doc_v1.py`
- NonScope:
  - ≠ 新建正式 GraphRAG Job Smoke runbook／戰報
  - ≠ DarkOps 解禁／§2.2 改寫為可跑
  - ≠ Dashboard Phase%／`apply_phase_pct`／W-PROG authorize
  - ≠ 改憲法／合約正文、core、CI、暗部根
  - ≠ P2 sandbox execute／RAG E2E／P5 真 PG soak／prod webhook
- AllowedPaths:
  - `docs/p1-index-r4-false-neg-doc-v1.md`
  - `docs/p1-gov-residual-checkoff-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（僅 §2／§2.1 與既有 GraphRAG 一行交叉引用）
  - `tests/test_p1_index_r4_false_neg_doc_v1.py`
  - `04_Workflows/tickets/P1-INDEX-R4-FALSE-NEG-DOC-v1_state.md`
- BlockedPaths:
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 數字格
  - `core/**`、暗部 root、`.env`／venv／`runtime/checkpoints/**`
  - `HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md` 正文
  - `.github/workflows/**`
  - 憲法 §7：Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION
  - 他人票 `*_state.md` 的 FRAME／C／D（本票 state 除外）
- Dependencies:
  - `P1-GOV-RESIDUAL-CHECKOFF-v1`（done · R4 defer）
  - 既有：`RAG_SMOKE_TEST_RUNBOOK_v0.1` · `P2-GRAPHRAG-THIN-RUNNER-v1` docs／CLI
- relay_mode: same_chat
- ticket_class: doc/spec
- evidence_tier: L-local
- estimated_cycles: 1
- phase_targets: [P1]
- baseline_pct: 90
- proposed_delta_pct: +1～+2
- evidence_gate: L-local
- impact_size: small
- apply_phase_pct: false
- non_claims:
  - ≠ GraphRAG 正式 smoke runbook 已立
  - ≠ Phase% uplift／Dashboard 數字格
  - ≠ DarkOps 解禁
  - ≠ INDEX 全文重排
- AcceptanceCriteria:
  - AC-1: `docs/p1-index-r4-false-neg-doc-v1.md` 存在，含假陰性表、修正對照、`non_claims`、`apply_phase_pct=false`
  - AC-2: `WORKFLOW_INDEX.md` §2.1 **不再**寫「待完成 RAG_Smoke_Test v0.1」；須指向 §1.2 runbook + GraphRAG thin runner doc
  - AC-3: `docs/p1-gov-residual-checkoff-v1.md` R4 Verdict = **done** 且引用本票
  - AC-4: `python -m unittest tests.test_p1_index_r4_false_neg_doc_v1 -v` → OK
  - AC-5: 文檔無本機絕對路徑／金鑰原文；未寫 Dashboard %

---

## STATE

- overall_status: done
- current_owner: none
- next_action: 無（本票封存完成；Phase% 待另開 W-PROG；禁止 authorize）
- last_updated: 2026-07-15 · D（Scribe 收口 · STATE→done）
- ops_checklist: 無
- status_by_role:
  - orchestrator: done — FRAME 凍結 · 選票理由見下
  - implementer: done — B_REPORT 已填
  - reviewer: done — C_REPORT accepted · risk=low
  - scribe: done — D_REPORT + Progress 末尾 append
- orch_notes: >-
    **收口**：C accepted · D_REPORT + Progress 末尾 append · apply_phase_pct=false · **未** authorize ·
    實際上調=否／待 W-PROG · non_claims：≠ GraphRAG 正式 smoke · ≠ P1 closure · ≠ Phase% uplift。

### 選票理由（O）

| 候選 | 裁決 |
|------|------|
| **1. P1 R4 INDEX 假陰性** | **本票** — checkoff R4 仍 `explicit defer`；INDEX §2.1 仍假稱 RAG 未就緒（實際 §1.2 runbook + GraphRAG thin 已存在） |
| 2. P5 soak 設計／stub CLI | 跳過 — `_phase5_pg_ingest_soak.py` 已存在；真 PG soak 屬授權票 |
| 3. P7.5 alert sink 本地串線 | 跳過 — G5→G6 + W3-SMOKE 已含 probe→sink |
| 4. P8.6–8.9 inspect→runtime | 跳過 — P868 inspect done；再進 runtime／execute 易碰 sandbox／批文邊界 |
| 5. 其他 | Wave A／P2-INDEX-OBS／P3-TRACE／GraphRAG thin／P1-GOV／P1-OPS 已封或 superseded |

---

## B_REPORT

- changed_files:
  - `docs/p1-index-r4-false-neg-doc-v1.md`（新建）
  - `docs/p1-gov-residual-checkoff-v1.md`（R4 → done + Suggested next）
  - `04_Workflows/WORKFLOW_INDEX.md`（§2／§2.1 假陰性修正 + GraphRAG thin 交叉引用）
  - `tests/test_p1_index_r4_false_neg_doc_v1.py`（新建）
  - `04_Workflows/tickets/P1-INDEX-R4-FALSE-NEG-DOC-v1_state.md`（FRAME／STATE／B_REPORT）
- artifacts:
  - R4 假陰性 SSOT：`docs/p1-index-r4-false-neg-doc-v1.md`
- verification:
  - `python -m unittest tests.test_p1_index_r4_false_neg_doc_v1 -v` → **Ran 7 tests · OK**
  - INDEX §2.1 無「待完成 RAG_Smoke_Test」；含 `RAG_SMOKE_TEST_RUNBOOK_v0.1.md` + `phase2-graphrag-thin-runner-v1.md`
  - checkoff R4 = **done** · 引用本票
  - `apply_phase_pct=false` · **未**寫 Dashboard % · 無金鑰／本機絕對路徑
- behavior_notes:
  - 僅清敘事假陰性；正式 GraphRAG Job Smoke runbook 仍誠實預留
  - §2.2 DarkOps 維持 Blocked（真阻塞，非假陰性）
  - proposed P1 +1～+2 · **未** apply
- deferred_items:
  - 正式 GraphRAG Job Smoke runbook／戰報（另票）
  - W-PROG P1 Δ authorize
  - R5 K-2／R6 Phase2 rules（仍 explicit defer）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    已讀 FRAME／B_REPORT／`docs/p1-index-r4-false-neg-doc-v1.md`／checkoff R4／INDEX §2–§2.2／薄測；
    重跑 `python -m unittest tests.test_p1_index_r4_false_neg_doc_v1 -v` → **Ran 7 tests · OK**。
    AC-1：假陰性 SSOT 含 FN 表、修正對照、`non_claims`、`apply_phase_pct=false` — pass。
    AC-2：§2.1 無「待完成 RAG_Smoke_Test」；指向 `RAG_SMOKE_TEST_RUNBOOK_v0.1.md` + `phase2-graphrag-thin-runner-v1.md`；仍標正式 GraphRAG Job Smoke **預留** — pass。
    AC-3：checkoff R4 = **done** 且引用本票；R5／R6 仍 explicit defer — pass。
    AC-4：7 OK（與 B_REPORT 一致）— pass。
    AC-5：doc 無本機絕對路徑／金鑰；FRAME／doc 均 `apply_phase_pct=false`；B 未改 Dashboard 數字格 — pass。
    NonScope：§2.2 DarkOps 仍 Blocked；未宣稱 GraphRAG 正式 smoke／P1 closure／Phase% uplift — pass。
    邊界：changed_files ⊆ AllowedPaths；工作樹另有 `WAVE_PROGRESS_DASHBOARD.md` M（非本票 B 清單，不計本票灌 %）。
- risk_level: low
- suggestions: |
    O／Scribe 將 STATE → `scribe`（Reviewer 不寫 STATE）。
    Progress／D_REPORT 須標 Phase 影響：proposed +1～+2 · 實際上調=否／待 W-PROG · non_claims 照抄。
    無更多無批文薄刀建議；瓶頸＝人卡／時間門／批文（正式 GraphRAG smoke／W-PROG／R5–R6）。
    next=scribe

---

## D_REPORT

- scribe_date: 2026-07-15 · Scribe（D）
- verdict_echo: Reviewer `accepted` · risk=low · blocking 無 · AC-1～AC-5 對照 C_REPORT 通過
- docs_updates:
  - 已交付（B；本輪不重寫）：`docs/p1-index-r4-false-neg-doc-v1.md`
  - 已交付（B；本輪不重寫）：`docs/p1-gov-residual-checkoff-v1.md`（R4 → done）
  - 已交付（B；本輪不重寫）：`04_Workflows/WORKFLOW_INDEX.md` §2／§2.1 假陰性修正
  - 已交付（B；本輪不重寫）：`tests/test_p1_index_r4_false_neg_doc_v1.py`
  - **敘事邊界**：本票 D_REPORT／Progress **僅**認領 AllowedPaths 產物；**不**把工作區另線 dirty 寫入本條
- progress_entry: >-
    見 `04_Workflows/00_Agent_Work_Progress.md` 末尾 —
    **2026-07-15 · P1-INDEX-R4-FALSE-NEG-DOC-v1 · done**
- followup_suggestions:
  - 下一無批文薄刀：正式 GraphRAG Job Smoke runbook／戰報（另票 · ≠ 本票）；或 Wave C 下一張 P3/P* doc/spec FRAME（`apply_phase_pct=false`）
  - 仍 defer：R5 K-2／R6 Phase2 rules（checkoff explicit defer）
  - Phase%：proposed P1 +1～+2 僅敘事 · **待另開 W-PROG** 方可 apply
  - 勿碰：`_phase_pct_apply --authorize` · Dashboard 數字格 · DarkOps 解禁 · INDEX 全文重排 · P1 closure 宣稱
- Phase 影響:
  - 影響 Phase: P1
  - baseline: 90
  - proposed_delta: +1～+2
  - 實際上調: 否／待 W-PROG
  - apply_phase_pct: false（未 authorize）
- non_claims:
  - ≠ GraphRAG 正式 smoke／正式 Job Smoke runbook 已立
  - ≠ P1 closure
  - ≠ Phase% uplift／Dashboard 數字格寫入／`--authorize`
  - ≠ DarkOps 解禁 · ≠ INDEX 全文重排

### Work Report（七節）

1. **任務／角色／日期**：P1-INDEX-R4-FALSE-NEG-DOC-v1 · Scribe（D）· 2026-07-15
2. **變更檔案**：本票 `*_state.md`（STATE→done · D_REPORT）；`04_Workflows/00_Agent_Work_Progress.md`（末尾 append only）
3. **skeleton**：無
4. **placeholder**：無
5. **驗證證據**：沿用 C_REPORT — unittest Ran 7 OK · AC-1～5 PASS；本輪 **未**跑 `--authorize`、**未**改 Dashboard %
6. **阻塞**：無（本票）；全局人卡 H2–H5／濕墨／P7 Round-2／正式 GraphRAG smoke 另票／W-PROG 仍在（≠ 本輪）
7. **override／留痕**：無；`apply_phase_pct=false` · 實際上調=否／待 W-PROG · **禁止** authorize
