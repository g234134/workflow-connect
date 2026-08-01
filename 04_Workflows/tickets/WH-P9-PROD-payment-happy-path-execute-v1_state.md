# WH-P9-PROD-payment-happy-path-execute-v1 — Ticket State

> handoff 摘要檔；P9 **prod closure 入口 happy-path 演練** execution 票 · sandbox adapter · demo ticket。  
> 目的：create → pending → pay → paid → lookup 可稽核；**≠ prod 金流** · **≠ INT Tier-A**。

---

## FRAME

### Goal

首條 sandbox 金流 happy-path 可重跑演練：M2 runner + order transition + sandbox adapter charge；Progress 戰報。

### 核心 checklist

- [x] 選定 `WC-DEMO-*` ticket；`artifacts/e2e/<ticket>/` 隔離目錄。
- [x] 執行 M2 runner `--execute --use-hitl-fixtures` 至 order create（DRAFT）。
- [x] CLI transition → PENDING_PAYMENT → sandbox adapter charge → PAID。
- [x] `lookup` / JSONL inspect 確認狀態鏈 + 無 secret 原文。
- [x] 擴充 walkthrough runner step（`step_id=6-payment` · `--include-payment`）— 见 **`WH-P9-M2-runner-step6-payment-v1`** · sandbox 实测通过。
- [x] Progress append 戰報；可選 advisory CI step（**non-blocking** · 仿 Wave-G）— Progress only · 无 CI 变更。
- [x] 明確聲明：**≠ prod 金流** · **≠ INT Tier-A** · **≠ required check**。

### Non-goals

- ❌ 不接入真實支付 API · 不寫 prod ledger。
- ❌ 不升格 fixture CI 為 required check。
- ❌ 不宣稱 WC-M3 prod 閉環完成（sandbox happy-path only）。

### AllowedPaths

- `artifacts/e2e/**`（demo 隔離）
- M2 walkthrough runner（execute 路徑 · 現有護欄）
- payment/order CLI（bootstrap + impl 票交付物）
- `04_Workflows/tickets/WH-P9-PROD-payment-happy-path-execute-v1_state.md`
- `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append only**）

### Acceptance Criteria

- **AC-1**：DRAFT→PENDING_PAYMENT→PAID 鏈可重跑 · lookup 可稽核。
- **AC-2**：Progress 戰報已 append · 誠實 non-claim 明示。
- **AC-3**：无 secret 原文 · 非 prod path。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: prod provider / INT / required CI 另票 · Scribe Progress append
- **last_updated**: 2026-06-24 · Wave-next-1 驗收落檔代理
- **wave**: Wave-P9 · payment happy-path execute
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開票
  - **Implementer (B)**: done — 2026-06-24 happy-path 演練 + 證據
  - **Reviewer (C)**: done — 2026-06-24 · `accepted_with_gaps`
  - **Scribe (D)**: pending — Progress append
- **notes**:
  - **P9 完成感事件**：sandbox happy-path 首條可重跑 + 戰報 ✅
  - 上游 WD-P9-T1/T2 runner 護欄不變

---

## B_REPORT (Implementer / Ops)

- **status**: done
- **written_date**: 2026-06-24
- **purpose**: sandbox payment happy-path 演練 DRAFT→PAID + Progress 戰報。
- **ticket**: `WC-DEMO-1`
- **artifact_dir**: `artifacts/e2e/WC-DEMO-1/`
- **execution_steps**:
  1. `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures --json` → `ok: true` · step 4 order `DRAFT`
  2. `python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl transition --order-id ORD-WC-DEMO-1 --to pending_payment --actor p9-happy-path --reason sandbox_execute` → `order_transitioned` · `PENDING_PAYMENT`
  3. `GOV_PAYMENT_SANDBOX_ENABLED=1 python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl pay --order-id ORD-WC-DEMO-1` → `charge_succeeded` · `PAID`
  4. `lookup --order-id ORD-WC-DEMO-1` → `order_status=PAID` · `provider_ref=SANDBOX-REF-*` · 无 API key/secret
- **evidence_path**: `artifacts/e2e/WC-DEMO-1/orders.jsonl`（3 行：DRAFT · PENDING_PAYMENT · PAID + audit 欄位）
- **non_claims**: **≠ prod 金流** · **≠ INT Tier-A** · **≠ required CI** · 无真人 HITL · 无真 provider
- **verification**: unittest **25/25 OK**（order_ledger + transition + payment_sandbox + integration）

---

## C_REPORT (Reviewer)

- **verdict**: `accepted_with_gaps`
- **review_date**: 2026-06-24
- **core**: P9 sandbox payment happy-path 可審計可重跑；≠ prod · ≠ INT · ≠ required CI。
- **gaps**:
  - runner step 6-payment 已在 **`WH-P9-M2-runner-step6-payment-v1`** 中实作并通过 sandbox 测试（`--include-payment` 一键 DRAFT→PAID）；**本票 gap 聚焦 prod provider / 金流线**，不再把 runner 能力列为未交付。
  - 仍无真 provider / 真人 HITL · WC-T7 runbook §4+ 已正文更新（见 `WH-P9-WC-T7-runbook-payment-section-v1`）。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**:
  - `WH-P9-PROD-payment-closure-bootstrap-v1`
  - `WH-P9-PROD-order-status-transition-impl-v1`
  - `WH-P9-PROD-payment-sandbox-adapter-v1`
  - `WD-P9-T1` · `WD-P9-T2`（runner 基線）
- **unlocks**:
  - P9 可誠實宣稱「sandbox payment happy-path 首條可重跑（DRAFT→PAID）」
  - `WD-P9-T1` · `WD-P9-T2` gap 縮至「无真人 HITL / 无真 provider / 无 required CI」· runner step 6 已关闭
  - WC-M3 後續 prod provider / prod ledger 票開路
