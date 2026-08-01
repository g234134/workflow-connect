# WH-P9-PROD-order-status-transition-impl-v1 — Ticket State

> handoff 摘要檔；P9 **demo/sandbox order 狀態機** execution/impl 票。  
> 目的：在 demo ledger 實作最小 order 狀態機（DRAFT→PENDING_PAYMENT→PAID）；擴充 order_ledger service + CLI。

---

## FRAME

### Goal

對齊 **`WH-P9-PROD-payment-closure-bootstrap-v1`** SSOT，在 sandbox/demo path 落地合法狀態轉移表與 audit JSONL 欄位；非法轉移 fail-closed。

### 核心 checklist

- [x] 擴充 `OrderRecord.order_status` 合法轉移表（對齊 bootstrap SSOT）。
- [x] 新增 CLI：`transition --to pending_payment|paid`（或等價 subcommand）；非法轉移 → `ok: false`。
- [x] JSONL 落盤保留 audit 欄位（`transitioned_at` · `actor` · `reason`）。
- [x] unittest：`tests.test_order_ledger_transition`（6 cases）。
- [x] 更新 WC-T4 design §10 deferred 表（payment 仍 deferred · 狀態機 **partial implemented**）。
- [x] 確認仍只寫 `artifacts/e2e/` 或明確 sandbox path，不碰 prod `artifacts/order_ledger/`。

### Non-goals

- ❌ 不接入真實支付 provider。
- ❌ 不寫 prod order ledger · 不擴大非 `WC-DEMO-*` 護欄。
- ❌ 不升格 CI required check。

### AllowedPaths

- order ledger 模組與 CLI（路徑見 `Master_Map.json` · WC-T4）
- `tests/test_order_ledger*.py`（或等價）
- `docs/wave_c/WC_T4_order_ledger_design.md`（§10 deferred 表 · 裁決）
- `04_Workflows/tickets/WH-P9-PROD-order-status-transition-impl-v1_state.md`

### Acceptance Criteria

- **AC-1**：合法轉移綠 · 非法 → `ok: false` · ≥6 unittest cases。
- **AC-2**：audit 欄位可 inspect JSONL。
- **AC-3**：sandbox path 護欄未放寬。

---

## STATE

- **overall_status**: `implementer_done_pending_review`
- **current_owner**: reviewer
- **next_action**: Reviewer 確認 transition unittest + happy-path 證據
- **last_updated**: 2026-06-24 · P9 payment sandbox execution agent
- **wave**: Wave-P9 · order status impl
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開票
  - **Implementer (B)**: done — 2026-06-24 狀態機 + CLI + 6 unittest
  - **Reviewer (C)**: pending
  - **Scribe (D)**: pending
- **notes**:
  - **depends_on**：`WH-P9-PROD-payment-closure-bootstrap-v1` scope SSOT ✅
  - 解鎖 payment adapter 與 happy-path execute ✅

---

## B_REPORT (Implementer)

- **status**: done
- **written_date**: 2026-06-24
- **purpose**: demo ledger DRAFT→PENDING_PAYMENT→PAID 狀態機 + CLI + unittest。
- **changed_files**:
  - `04_Workflows/order_ledger/models.py` — `ALLOWED_TRANSITIONS` · audit 欄位
  - `04_Workflows/order_ledger/store.py` — `update()` append JSONL · latest-wins reload
  - `04_Workflows/order_ledger/service.py` — `transition_order()`
  - `scripts/run_order_intake.py` — `transition` subcommand
  - `tests/test_order_ledger_transition.py` — 6 cases
  - `docs/wave_c/WC_T4_order_ledger_design.md` — §10 partial implemented
- **verification**:
  - `python -m unittest tests.test_order_ledger_transition -v` → **6/6 OK**
  - `python -m unittest tests.test_order_ledger tests.test_order_ledger_integration -v` → **14/14 OK**（無回歸）

---

## C_REPORT (Reviewer)

- **verdict**: `accepted_with_gaps`
- **review_date**: 2026-06-24
- **core**: sandbox order 狀態機 partial landing；非法轉移 fail-closed；≠ prod ledger。
- **gaps**: runner step_id=6-payment 仍 skeleton；REFUNDED 僅 adapter refund 路徑驗證 · 非 E2E 主链。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**: `WH-P9-PROD-payment-closure-bootstrap-v1` · WC-T4 order ledger v0.1
- **unlocks**:
  - `WH-P9-PROD-payment-sandbox-adapter-v1` — done
  - `WH-P9-PROD-payment-happy-path-execute-v1` — done_with_gaps
