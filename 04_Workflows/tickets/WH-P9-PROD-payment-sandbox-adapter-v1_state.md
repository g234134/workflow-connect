# WH-P9-PROD-payment-sandbox-adapter-v1 — Ticket State

> handoff 摘要檔；P9 **mock payment provider adapter** execution/impl 票 · sandbox-only。  
> 目的：接收 `order_id` + amount，回傳結構化 `payment_result` dict；happy path 與 deterministic failure。

---

## FRAME

### Goal

sandbox-only mock payment adapter；env gate default off；與 order status transition 串一條 integration test。

### 核心 checklist

- [x] 新增 payment sandbox 模組：`04_Workflows/order_ledger/payment_adapter.py` — `charge` · `refund` dry-run/execute。
- [x] Env gate `GOV_PAYMENT_SANDBOX_ENABLED=1`（default 0）；**禁止** 真實 API key。
- [x] Happy path：`charge` → `status=paid` + `provider_ref` mock id。
- [x] Failure inject：`GOV_PAYMENT_SANDBOX_SIMULATE=decline|timeout` 或 `--simulate` → order 停留 PENDING_PAYMENT。
- [x] unittest 6（≥5）；與 order transition 串一條 integration test。
- [ ] Runbook 段：與 WC-T7 §4 對照（仍非 prod gate）— **skeleton** · 见 alignment matrix §4+。

### Non-goals

- ❌ 不接入 Stripe/真實金流 API。
- ❌ 不把 adapter 宣稱為 prod gate 或 INT Tier-A。
- ❌ 不寫 prod order ledger。

### AllowedPaths

- payment sandbox 腳本/模組（路徑見 Implementer 裁決 · 對齊 bootstrap 契約）
- `tests/test_*payment*`（或等價）
- `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`（對照段 · 裁決）
- `04_Workflows/tickets/WH-P9-PROD-payment-sandbox-adapter-v1_state.md`

### Acceptance Criteria

- **AC-1**：default off · enabled happy path 綠 · failure inject deterministic。
- **AC-2**：≥5 unittest + 1 integration with order transition。
- **AC-3**：無 secret 原文 · 無 prod path 寫入。

---

## STATE

- **overall_status**: `implementer_done_pending_review`
- **current_owner**: reviewer
- **next_action**: Reviewer 確認 adapter unittest + happy-path charge 證據
- **last_updated**: 2026-06-24 · P9 payment sandbox execution agent
- **wave**: Wave-P9 · payment sandbox adapter
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開票
  - **Implementer (B)**: done — 2026-06-24 adapter + pay CLI + 6 unittest
  - **Reviewer (C)**: pending
  - **Scribe (D)**: pending
- **notes**:
  - **depends_on**：`WH-P9-PROD-order-status-transition-impl-v1` ✅
  - bootstrap SSOT 定義 adapter 契約 ✅

---

## B_REPORT (Implementer)

- **status**: done
- **written_date**: 2026-06-24
- **purpose**: mock payment provider sandbox adapter · charge/refund · env gate · unittest。
- **changed_files**:
  - `04_Workflows/order_ledger/payment_adapter.py` — `charge` · `refund` · env gate
  - `scripts/run_order_intake.py` — `pay` subcommand
  - `04_Workflows/order_ledger/__init__.py` — exports
  - `tests/test_payment_sandbox_adapter.py` — 6 cases incl. integration
- **verification**:
  - `python -m unittest tests.test_payment_sandbox_adapter -v` → **6/6 OK**
  - Happy-path execute：`GOV_PAYMENT_SANDBOX_ENABLED=1` + `pay --order-id ORD-WC-DEMO-1` → `charge_succeeded` · `order_status=PAID`

---

## C_REPORT (Reviewer)

- **verdict**: `accepted_with_gaps`
- **review_date**: 2026-06-24
- **core**: sandbox mock payment 可重跑；fail-closed；≠ prod provider。
- **gaps**: WC-T7 runbook §4+ payment 步仍 skeleton（alignment matrix 已 cross-ref）；无 advisory CI step。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**: `WH-P9-PROD-payment-closure-bootstrap-v1` · `WH-P9-PROD-order-status-transition-impl-v1`
- **unlocks**: `WH-P9-PROD-payment-happy-path-execute-v1` — done_with_gaps
