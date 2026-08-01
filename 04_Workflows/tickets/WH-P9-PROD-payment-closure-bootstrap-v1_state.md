# WH-P9-PROD-payment-closure-bootstrap-v1 — Ticket State

> handoff 摘要檔；P9 **WC-M3 / prod 金流閉環入口** bootstrap/gov 票 · **doc-only**。  
> 目的：定義 happy-path 邊界、護欄、與 WC-T4/M2 分層；**不啟用真實支付 API**。

---

## FRAME

### Goal

WC-M3 prod 金流閉環 **制度錨點**：DRAFT→PENDING_PAYMENT→PAID→（可選 REFUNDED）scope SSOT；sandbox adapter 契約；下游 impl/execute 票索引。

### 核心 checklist

- [x] 起草 `docs/wave_c/WC_M3_payment_closure_scope_v1.md`（或 WC-T7 新節）：狀態機與 non-goals。
- [x] 明確 non-goals：無 Stripe/prod ledger · 仍拒絕非 `WC-DEMO-*` 無批文 prod 票。
- [x] 對照 `WC_M2_INT_HITL_alignment_matrix_v1.md` 更新 §order 步驟 prod closure 前/後欄位。
- [x] 定義 sandbox payment adapter 契約（mock provider · idempotency · fail-closed）。
- [x] 列出下游 impl/execute 票索引 + Wave 依賴（order service · CLI · E2E runner 擴充）。
- [ ] Scribe：Progress 一行 P9 prod closure 入口（可選 · B 完成後）。

### Non-goals

- ❌ 不啟用真實支付 API · 不寫 prod order ledger。
- ❌ 不把 demo skeleton 宣稱為 INT Tier-A 或 required CI pass。
- ❌ 不改 runner / tests / workflows（本票 doc-only）。

### AllowedPaths

- `docs/wave_c/WC_M3_payment_closure_scope_v1.md`（建議新建）
- `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md`（§order 欄位 cross-ref · 裁決）
- `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`（新節 cross-ref · 裁決）
- `04_Workflows/tickets/WH-P9-PROD-payment-closure-bootstrap-v1_state.md`
- `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append only**）

### Acceptance Criteria

- **AC-1**：WC-M3 scope SSOT 可審計 · non-goals 明示。
- **AC-2**：對齊矩陣 order 步驟已更新或 cross-ref。
- **AC-3**：下游 ≥3 張 impl/execute 票索引。

---

## STATE

- **overall_status**: `design_accepted`
- **current_owner**: reviewer
- **next_action**: Reviewer 確認 scope doc · 下游 impl 票已串接
- **last_updated**: 2026-06-24 · P9 payment sandbox execution agent
- **wave**: Wave-P9 · prod payment closure bootstrap
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開票
  - **Implementer (B)**: done — 2026-06-24 WC_M3 scope doc + alignment matrix §4+ cross-ref
  - **Reviewer (C)**: pending
  - **Scribe (D)**: pending
- **notes**:
  - 上游 **`WH-P9-M2-INT-alignment-v1`** · WD-P9-T1/T2 · WC-T4/T7
  - P9 Phase 60% → 上行 **制度錨點** · 非 prod 金流啟用

---

## B_REPORT (Implementer · doc)

- **status**: done
- **written_date**: 2026-06-24
- **purpose**: WC-M3 payment closure scope SSOT · 護欄 · sandbox adapter 契約 · 下游票索引。
- **deliverable_path**: `docs/wave_c/WC_M3_payment_closure_scope_v1.md`
- **core_checklist_summary**: 狀態機 DRAFT→PENDING_PAYMENT→PAID（+REFUNDED 可選）· non-goals 明示 · alignment matrix §4+ 三行 · adapter env gate 契約 · 下游 3 impl/execute 票索引
- **verification**: doc-only · 對照 WC-T4 §10 partial implemented · alignment matrix cross-ref

---

## C_REPORT (Reviewer)

- **verdict**: `accepted_with_gaps`
- **review_date**: 2026-06-24
- **core**: P9 prod 金流閉環入口 SSOT 已落盤；sandbox/demo 邊界誠實；≠ prod API。
- **gaps**: Progress 末尾索引待 Scribe；下游 impl 由 execution agent 同輪交付。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**: `WH-P9-M2-INT-alignment-v1` · `WD-P9-T1` · `WD-P9-T2` · WC-T4/T7
- **unlocks**:
  - `WH-P9-PROD-order-status-transition-impl-v1` — **impl_done**
  - `WH-P9-PROD-payment-sandbox-adapter-v1` — **impl_done**
  - `WH-P9-PROD-payment-happy-path-execute-v1` — **done_with_gaps**
- **索引**: `docs/wave_c/WC_M3_payment_closure_scope_v1.md` · alignment matrix §4+

---

### 附錄：Reviewer memo（2026-06-24）

### P9 payment sandbox 線現況（2026-06-24）

**Summary**：P9 payment 線已完成 **sandbox happy-path 首輪** — `WC-DEMO-*` 票在 `artifacts/e2e/<ticket>/` 隔離目錄內，經 order transition + sandbox adapter 可稽核地跑通 **DRAFT→PENDING_PAYMENT→PAID**；order_ledger / payment_sandbox 相關 unittest **25/25 綠**。此為 mock adapter 演練，**不是 prod 金流閉環**。

| 向外可說 | 嚴格不可以說 |
|----------|--------------|
| Sandbox payment happy-path 可重跑、lookup 可稽核；有 **25/25** unittest 證據；`WC_M3_payment_closure_scope_v1` + alignment matrix §4+ 已定 sandbox 邊界。 | **Prod 金流閉環**、**真 payment provider**（Stripe 等）、**prod order ledger** 已接入或已驗收。 |
| 三張 follow-up 票（runner step 6 / runbook §4+ / advisory CI）**FRAME 已就緒**，後續可施工補齊一鍵 fixture execute、可复制 runbook 正文、non-blocking CI 觀測。 | **INT Tier-A**、**merge-blocking / required CI gate**；宣稱 **WC-M3 prod closure 完成** 或 **manual HITL payment 驗收已過**。 |
| 現階段可誠實描述為「P9 sandbox payment 首條 happy-path 已落地 · Reviewer `accepted_with_gaps`」。 | 把 sandbox CI green（即使後續 advisory job 上線）等同 **prod-ready** 或 **客戶-facing 金流 SLA**。 |

**Follow-up 四票角色**：
- **`WH-P9-M2-runner-step6-payment-v1`**（`frame_ready`）：在 M2 walkthrough runner 内建 `step_id=6-payment`，使 `--execute --use-hitl-fixtures` 一鍵跑至 PAID；收编現有手工 CLI 链。
- **`WH-P9-WC-T7-runbook-payment-section-v1`**（`frame_ready`）：将 happy-path 命令升格为 `WC_T7_e2e_walkthrough_runbook.md` **§4+ Payment（sandbox）** 可复制正文，含 non-claims cross-ref。
- **`WH-P9-CI-payment-sandbox-smoke-v1`**（`frame_ready`）：设计 **advisory · non-blocking** CI job（建议 `p9-payment-sandbox-smoke`）；**≠ required check**，依赖 runner step 6 或等价 CLI 链。
- **`WH-P9-PROD-real-provider-v1`**（`blocked`）：prod 真 provider + prod ledger 升格入口；**等待尚书省 prod 金流批文**，批文前不得施工。
