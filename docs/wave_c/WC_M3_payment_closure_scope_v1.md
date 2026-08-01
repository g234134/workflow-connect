# WC-M3 · Payment Closure Scope v1 (Sandbox)

> **性質**：P9 prod 金流閉環 **制度錨點**（doc-only SSOT）；**非** prod API 啟用批文。  
> **票號**：`WH-P9-PROD-payment-closure-bootstrap-v1`  
> **版本**：v1 · 2026-06-24  
> **上游**：`WH-P9-M2-INT-alignment-v1` · `WD-P9-T1` · `WD-P9-T2` · WC-T4 order ledger v0.1

---

## 1. Goal（一句話）

在 **demo/sandbox 護欄** 內，定義 order 金流 happy-path 狀態機（DRAFT→PENDING_PAYMENT→PAID→可選 REFUNDED）、mock payment adapter 契約，以及與 M2 walkthrough 的銜接步驟；**不接真實 provider、不寫 prod ledger**。

---

## 2. Order 狀態機（sandbox / demo）

### 2.1 狀態定義

| 狀態 | 語意 | 進入條件 |
|------|------|----------|
| `DRAFT` | order create 後初始態（WC-T4 v0.1 預設） | `create_order_for_ticket` 成功 |
| `PENDING_PAYMENT` | 已提交收款、等待 sandbox/mock provider 回應 | 合法 transition 自 DRAFT |
| `PAID` | sandbox charge 成功 | 合法 transition 自 PENDING_PAYMENT，或 adapter happy path |
| `REFUNDED` | （可選）sandbox refund dry-run/execute | 合法 transition 自 PAID |

### 2.2 合法轉移表

```
DRAFT ──► PENDING_PAYMENT ──► PAID ──► REFUNDED (optional)
```

| From | To | 允許 |
|------|-----|------|
| `DRAFT` | `PENDING_PAYMENT` | ✅ |
| `PENDING_PAYMENT` | `PAID` | ✅ |
| `PAID` | `REFUNDED` | ✅（可選 · sandbox only） |
| 任意其他跳轉 | — | ❌ fail-closed · `ok: false` |

### 2.3 JSONL audit 欄位（transition 落盤）

每次 transition append 一行 JSONL（latest-wins reload），**至少**含：

| 欄位 | 說明 |
|------|------|
| `order_status` | 新狀態 |
| `transitioned_at` | UTC ISO8601 |
| `actor` | 操作者標識（如 `cli` · `sandbox-adapter`） |
| `reason` | 人讀原因（如 `manual_transition` · `sandbox_charge_ok`） |
| `provider_ref` | （可選）mock provider 參考 id；**禁止**真實 API key 或 secret |

---

## 3. Sandbox payment adapter 契約

### 3.1 Env gate

| 變數 | 預設 | 語意 |
|------|------|------|
| `GOV_PAYMENT_SANDBOX_ENABLED` | `0` | `1` 才允許 mock `charge` / `refund` |
| `GOV_PAYMENT_SANDBOX_SIMULATE` | （空） | 可選 `decline` · `timeout` 故障注入 |

**禁止**：讀取 Stripe/真實金流 API key；adapter 僅回 mock `provider_ref`（如 `SANDBOX-REF-<order_id>`）。

### 3.2 `charge(order_id, amount_minor, …)` 回傳形狀

```json
{
  "ok": true,
  "message": "charge_succeeded",
  "payment_result": {
    "status": "paid",
    "provider_ref": "SANDBOX-REF-ORD-WC-DEMO-1",
    "simulated": true
  }
}
```

- **Happy path**：`status=paid` + mock `provider_ref`；可串 order transition → `PAID`。
- **Decline / timeout**：`ok: false`；order **停留** `PENDING_PAYMENT`。

### 3.3 Idempotency · fail-closed

- 重複 charge 已 `PAID` order → `ok: true` · `message: already_paid`（replay）。
- gate off（`GOV_PAYMENT_SANDBOX_ENABLED≠1`）→ `ok: false` · `message: sandbox_disabled`。
- 非法狀態（如 DRAFT 直接 charge）→ `ok: false` · 明確 `message`。

---

## 4. 與 M2 alignment matrix 的銜接

> 主矩陣：[`WC_M2_INT_HITL_alignment_matrix_v1.md`](WC_M2_INT_HITL_alignment_matrix_v1.md)

### 4.1 Prod closure **前**（M2 已交付 · P9-T1/T2）

| step | 現況 | order_status |
|------|------|--------------|
| §4 create | fixture/manual execute → `orders.jsonl` | **DRAFT** |
| §4 lookup / replay | 可稽核 create 記錄 | DRAFT |
| CI fixture execute | step 3/4 ok · advisory only | DRAFT |

### 4.2 Prod closure **後**（本 WC-M3 sandbox 鏈 · 2026-06-24 起）

| step | 命令要點 | order_status 鏈 |
|------|----------|-----------------|
| §4+ transition | `run_order_intake.py transition --to pending_payment` | DRAFT → PENDING_PAYMENT |
| §4+ sandbox charge | `GOV_PAYMENT_SANDBOX_ENABLED=1` + `pay` 或 adapter `charge` | PENDING_PAYMENT → PAID |
| §4+ lookup inspect | JSONL 含 `transitioned_at` · `actor` · `reason` | 全鏈可稽核 |
| §4+ refund（可選） | sandbox `refund` dry-run | PAID → REFUNDED |

**護欄不變**：僅 `WC-DEMO-*` · JSONL 限 `artifacts/e2e/<ticket>/` · **不寫** `artifacts/order_ledger/` 預設 prod 路徑。

### 4.3 誠實邊界（non-claims）

- sandbox happy-path **≠** prod 金流閉環 · **≠** INT Tier-A · **≠** required CI check。
- fixture execute **預設** 止于 DRAFT；加 runner **`--include-payment`** 可 sandbox 一鍵至 **PAID**（`step_id=6-payment` · WC-DEMO-* only · mock adapter）。
- Wave-G `p9-wc-m2-fixture-execute` advisory CI **仍不覆盖** payment 步；payment CI 待 `WH-P9-CI-payment-sandbox-smoke-v1` 施工轮（**frame_ready · 未施工**）。
- 真人 HITL runbook **不**被 sandbox adapter 取代。

---

## 5. Non-goals（明示）

- ❌ **不**接入 Stripe / 真實支付 provider / prod ledger。
- ❌ **不**對非 `WC-DEMO-*` 票放寬護欄（無批文 prod 票仍拒絕）。
- ❌ **不**把 demo skeleton 宣稱為 INT Tier-A 或 merge-blocking gate。
- ❌ **不**回寫 live `04_Workflows/tickets/*_state.md` order 欄位（仍人工 / Orchestrator）。
- ❌ **不**在本 scope 啟用 REST payment API 或 outbox 聯動（W4-T3 deferred）。

---

## 6. 下游 impl / execute 票索引

| 票 id | 類型 | 狀態（2026-06-24） | 交付 |
|-------|------|-------------------|------|
| `WH-P9-PROD-payment-closure-bootstrap-v1` | bootstrap/gov | design_accepted | 本檔 SSOT |
| `WH-P9-PROD-order-status-transition-impl-v1` | impl | `implementer_done_pending_review` | 狀態機 + CLI + unittest |
| `WH-P9-PROD-payment-sandbox-adapter-v1` | impl | `implementer_done_pending_review` | mock adapter + env gate |
| `WH-P9-PROD-payment-happy-path-execute-v1` | execute | **`done_with_gaps`** | DRAFT→PAID 演練 + 戰報 |
| `WH-P9-M2-runner-step6-payment-v1` | impl | **`done_with_gaps`** | runner `step_id=6-payment` · **`--include-payment`** |
| `WH-P9-WC-T7-runbook-payment-section-v1` | doc | **`done_with_gaps`** | WC-T7 runbook §4+ payment 正文 |
| `WH-P9-CI-payment-sandbox-smoke-v1` | CI 设计 | `frame_ready` | advisory smoke（**未施工**） |
| `WH-P9-PROD-real-provider-v1` | prod | **`blocked`** | 真 provider · **等待尚书省批文** |

**2026-06-24 sandbox 里程碑**：WC-DEMO-* · DRAFT→PAID · **25/25** tests · runner **`--include-payment`** 一鍵 walkthrough OK · runbook §4+ 完整。**non-claims 仍有效**：非 prod 金流 · 非真 provider · 非 INT Tier-A · 非 required CI。

**Wave 依賴**：WC-T4 order ledger · M2 runner（P9-T1/T2）· 本 scope **不**依賴暗部 `core` 或 INT gate 升格。

---

## 7. 交叉引用

| 文档 | 用途 |
|------|------|
| [`WC_T4_order_ledger_design.md`](WC_T4_order_ledger_design.md) | order intake v0.1 · §10 deferred 更新 |
| [`WC_M2_INT_HITL_alignment_matrix_v1.md`](WC_M2_INT_HITL_alignment_matrix_v1.md) | M2 逐步 × payment 後欄位 |
| [`WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md) | E2E 命令 · §4 order 步 |
| [`04_Workflows/tickets/WH-P9-PROD-payment-closure-bootstrap-v1_state.md`](../../04_Workflows/tickets/WH-P9-PROD-payment-closure-bootstrap-v1_state.md) | bootstrap 票 state |

---

*WC-M3 Payment Closure Scope v1 · sandbox-only · WH-P9-PROD-payment-closure-bootstrap-v1*
