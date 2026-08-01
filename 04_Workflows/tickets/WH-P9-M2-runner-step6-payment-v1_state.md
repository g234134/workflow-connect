# WH-P9-M2-runner-step6-payment-v1 — Ticket State

> handoff 摘要檔；P9 **M2 walkthrough runner step 6-payment** impl 票 · sandbox-only。  
> 目的：在 `run_wc_m2_e2e_walkthrough.py` 内建 `step_id=6-payment`，使 fixture execute 可一鍵 DRAFT→PAID；**≠ prod 金流**。

---

## META

| 欄位 | 值 |
|------|-----|
| **Phase** | P9 |
| **Lane** | M2 runner · Wave-C Control Plane |
| **Parent wave** | Wave-P9 · payment sandbox follow-up |
| **Owner** | orchestrator |
| **Ticket type** | impl · runner extension |

---

## FRAME

### Goal（一行目的）

在 M2 E2E walkthrough runner 新增 **`step_id=6-payment`**（transition → sandbox `pay` → PAID lookup），使 `--execute --use-hitl-fixtures` 无需手工 CLI 即可跑完 sandbox payment 链。

### 核心 checklist

- [x] 新增 Step `6-payment`：`transition --to pending_payment` → `GOV_PAYMENT_SANDBOX_ENABLED=1 pay` → `lookup` 验 `order_status=PAID`。
- [x] dry-run 输出 step 6 命令预览；execute 在 step 4 order create 成功后串接。
- [x] 护栏不变：仅 `WC-DEMO-*` · artifacts 限 `artifacts/e2e/<ticket>/` · 不写 prod ledger。
- [x] `--use-hitl-fixtures` 路径：step 4→6 自动 ok；manual HITL 路径 step 6 仍可在 order DRAFT 后执行。
- [x] 扩展 `tests/test_run_wc_m2_e2e_walkthrough.py`：step 6 存在 · fixture execute 至 PAID · 无 secret 原文断言。
- [ ] alignment matrix §5.1 速查表补 `6-payment` 行 cross-ref（或 Scribe 另票）。
- [x] 诚实 non-claim：**≠ prod 金流** · **≠ INT Tier-A** · **≠ required CI**。

### Non-goals

- ❌ 不接入真实 payment provider · 不改 prod order ledger 路径。
- ❌ 不把 runner step 6 宣称为 INT Tier-A 或 merge-blocking gate。
- ❌ 不修改 live `*_state.md` · 不替代 manual HITL 验收语义。

### AllowedPaths

- `scripts/run_wc_m2_e2e_walkthrough.py`
- `tests/test_run_wc_m2_e2e_walkthrough.py`
- `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md`（§5.1 一行 cross-ref · 裁決）
- `04_Workflows/tickets/WH-P9-M2-runner-step6-payment-v1_state.md`

### Acceptance Criteria

- **AC-1**：fixture execute `WC-DEMO-1` → runner `ok: true` · step 6 `ok` · final `order_status=PAID`。
- **AC-2**：dry-run 含 step 6 预览 · 护栏拒绝非 demo 票不变。
- **AC-3**：unittest 扩展绿 · 无 secret 原文 · 诚实 non-claim 留痕。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: 可选 alignment matrix §5.1 cross-ref · prod provider 另票
- **last_updated**: 2026-06-24 · Wave-next-1 驗收落檔代理
- **wave**: Wave-P9 · M2 runner step 6-payment
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-24 开 follow-up FRAME
  - **Implementer (B)**: done — 2026-06-24 step 6-payment + unittest 15/15 OK
  - **Reviewer (C)**: done — 2026-06-24 · `accepted_with_gaps`（Owner 驗收對照實測）
  - **Scribe (D)**: pending
- **notes**:
  - 上游 happy-path execute 票已手工 CLI 验证 DRAFT→PAID；本票收编为 runner 内建步
  - 父上下文：`WD-P9-T1` · `WH-P9-PROD-payment-happy-path-execute-v1`

---

## B_REPORT (Implementer)

- **status**: done
- **written_date**: 2026-06-24
- **purpose**: M2 walkthrough runner 内建 sandbox payment 步（step 6-payment），一键 fixture execute 至 PAID。

### step6-payment 行为

| 项 | 说明 |
|----|------|
| **step_id** | `6-payment` |
| **标题** | Sandbox payment: transition → pay → PAID lookup (WC-M3 §4.2 · demo only) |
| **位置** | step 4（order create）之后 · step 5（unittest cross-check）之前 |
| **命令链** | `transition --to pending_payment` → `pay`（runner 注入 `GOV_PAYMENT_SANDBOX_ENABLED=1`）→ `lookup --order-id ORD-<ticket>` |
| **护栏** | 仅 `WC-DEMO-*` · JSONL 限 `artifacts/e2e/<ticket>/orders.jsonl` · 不写 prod ledger |

### CLI 介面

| 选项 / env | 默认 | 说明 |
|------------|------|------|
| `--include-payment` | **off** | 追加 step 6-payment；未设则 step 6 **不出现**（向后兼容） |
| `GOV_PAYMENT_SANDBOX_ENABLED` | runner 对 `pay` 子进程注入 `1` | 仅 `--include-payment` 时生效；不依赖 shell 前缀 |

### 示例 walkthrough（Owner 驗收命令 · sandbox-only · `WC-DEMO-*` only）

```bash
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --execute \
  --use-hitl-fixtures \
  --include-payment \
  --json
```

> **sandbox-only · `WC-DEMO-*` only**：此命令仅作用于 demo ticket 与 `artifacts/e2e/<ticket>/` 隔离目录；触 sandbox adapter，**不触** prod ledger。

### 验证

- `python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v` → **15/15 OK**（含 `test_execute_with_include_payment_reaches_paid`）
- 新增测试：`test_dry_run_without_include_payment_omits_step6` · `test_dry_run_with_include_payment_previews_step6` · `test_execute_with_include_payment_reaches_paid`
- execute 结果 JSON 含 `include_payment: true` · `order_status: PAID`（step 6 lookup 后）· orders JSONL 反映 **DRAFT → PENDING_PAYMENT → PAID**

### non_claims

- **≠ prod 金流** · **≠ INT Tier-A** · **≠ required CI**
- sandbox only · 无真 provider · alignment matrix §5.1 行尚未补（Scribe/另票）

---

## C_REPORT (Reviewer)

- **verdict**: `accepted_with_gaps`
- **review_date**: 2026-06-24
- **core**: M2 runner 内建 sandbox payment 步（`step_id=6-payment` · `--include-payment`）；Owner 驗收實測 fixture execute 一鍵 DRAFT→PAID · unittest 15/15 OK；≠ prod · ≠ INT。
- **gaps**（Reviewer 專注誠實邊界，非功能未完成）:
  - **sandbox only** · **无 prod provider** · **无 required CI**
  - alignment matrix §5.1 `6-payment` 行待补（Scribe/另票）
  - 重跑时若 artifacts 已有 PAID，transition 可能 `invalid_transition`（见 runbook §4+.2 清理说明）

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**:
  - `WH-P9-PROD-payment-closure-bootstrap-v1`
  - `WH-P9-PROD-order-status-transition-impl-v1`
  - `WH-P9-PROD-payment-sandbox-adapter-v1`
  - `WH-P9-PROD-payment-happy-path-execute-v1`
  - `WD-P9-T1` · `WD-P9-T2`（runner 基线 · fixture execute）
- **unlocks**（预计升级 · 本票不修改他票）:
  - `WH-P9-PROD-payment-happy-path-execute-v1` — `done_with_gaps` → `done` 或 `accepted_with_gaps`（runner gap 关闭）
  - `WD-P9-T1-wc-m2-order-demo-e2e-v1` — gap 缩至 payment 外遗留项
  - `WH-P9-CI-payment-sandbox-smoke-v1` — CI job 可绑定 runner step 6 或等价链
