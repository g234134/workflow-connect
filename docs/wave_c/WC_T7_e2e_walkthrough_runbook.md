# WC-T7 — Control Plane M2 E2E Walkthrough Runbook (v0.4)

> **性质**：Control Plane 端到端手工／半自动验收 runbook。  
> **用途**：M2/M3 Wave C Control Plane 链本地走通（eligibility → dispatch cards → comms → order intake → **sandbox payment**）。  
> **重要**：本 runbook **不等于** INT Tier-A regression gate。Control Plane E2E pass **不**代表 INT pass；两者职责见文末 §INT gate 对齐。  
> **版本**：v0.4（2026-06-24 · P9 sandbox payment §4+ · WC-M3 closure scope）

**票号**：`WC-T7`  
**建议 demo 票**：`WC-DEMO-1`（勿用生产票如 `W1-T*`）  
**隔离产物根**：`artifacts/e2e/<ticket_id>/`  
**交叉引用**：`docs/wave_c/WC_T1_eligibility.md` · `WC_T2_comms_minimal.md` · `WC_T4_order_ledger_design.md` · [`WC_M3_payment_closure_scope_v1.md`](WC_M3_payment_closure_scope_v1.md) · [`WC_M2_INT_HITL_alignment_matrix_v1.md`](WC_M2_INT_HITL_alignment_matrix_v1.md) §4+ · [`04_Workflows/tickets/WH-P9-PROD-payment-happy-path-execute-v1_state.md`](../../04_Workflows/tickets/WH-P9-PROD-payment-happy-path-execute-v1_state.md) · [`WH-P9-M2-runner-step6-payment-v1_state.md`](../../04_Workflows/tickets/WH-P9-M2-runner-step6-payment-v1_state.md)（runner step 6 · `--include-payment`）· `docs/control_plane_dispatch_executor.md`

---

## 执行路径分工（三种模式 · demo / 非 prod）

> **诚实边界**：以下三种路径均为 **demo skeleton / 非 production E2E**；**未**接入 merge-blocking CI（见 §6.5）。写 live `04_Workflows/tickets/*_state.md` 仍属 WC-T5 `wc.m2.state.write_ticket` **forbidden**；runner **不会**自动写 live STATE。

| 模式 | 命令 | 适用场景 | HITL | 产物 |
|------|------|----------|------|------|
| **Dry-run 编排骨架** | `--dry-run` | 本地预览步骤命令；不写业务档 | 打印 HITL 提示 | 可选空目录；**不**写 `orders.jsonl` / comms |
| **Manual HITL walkthrough** | `--execute`（默认） | 真人走通 §1–§4；M2/M3 验收 | **须**手工编辑 live STATE（§3/§4） | 依赖 `before_review.md` + live state；comms / order 写入 `artifacts/e2e/<ticket>/` |
| **Demo fixture execute** | `--execute --use-hitl-fixtures` | 本地或 CI advisory（`p9-wc-m2-fixture-execute` · Wave-G）；无真人 HITL（P9-T2） | 跳过；从 `tests/fixtures/e2e_walkthrough/` 复制快照 | **仅** `artifacts/e2e/<ticket>/` 内 demo comms + `orders.jsonl`；**不写** live STATE |

**关键区分**

- **Manual HITL** 是唯一会触及 live `*_state.md` 的路径（人工编辑；runner 只读）。
- **Fixture execute** 自动化 comms + order 步骤，但仍是 **demo skeleton**，**不等于** production HITL gate 或 INT Tier-A pass。
- **Dry-run** 纯编排草图；允许建立空 `artifacts/e2e/<ticket>/` 目录，但不写业务档（WD-P9-T1 Orchestrator 裁決）。

详情与命令示例见 **§6.3**（dry-run）· **§6.5**（fixture execute）· **§1–§4**（manual HITL）。

---

## 前置条件

| 项 | 要求 |
|----|------|
| 工作目录 | repo 根 |
| Demo 票 | `04_Workflows/tickets/<ticket_id>_state.md` 已按 §1 创建；推荐 `<ticket_id>=WC-DEMO-1` |
| 隔离目录 | `artifacts/e2e/<ticket_id>/` 已创建（comms outbox 与 order ledger 共用父目录） |
| Python | 战车主舱或已配置 `sys.path` 的 shell（脚本位于 `scripts/`） |
| 涉及 CLI | `run_ticket_eligibility.py` · `run_dispatch_cards.py` · `run_ticket_state_update_with_comms.py` · `run_order_intake.py` |

**CLI 约束（只读 ticket state，不写 `*_state.md`）**

| 步骤 | 脚本 | 关键 flags |
|------|------|------------|
| Eligibility + 指令卡 | `scripts/run_dispatch_cards.py` | `--refresh-plan` · `--ticket` · `--role implementer` · `--eligibility-gate block` · 可选 `--force-eligibility` |
| Comms JSONL | `scripts/run_ticket_state_update_with_comms.py` | `--before` · `--after` · `--outbox-dir` |
| Order intake | `scripts/run_order_intake.py` | `create` / `lookup` / `transition` / `pay` · `--jsonl-path`（顶层 flag，写在子命令之前） |

**可选 runner（编排骨架，不替代手工 STATE 编辑）**

```bash
python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run
python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute
python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures
```

> **`--use-hitl-fixtures`（CI / 无真人 HITL）**：见下文 **§HITL fixture 模式**；仍 **demo-only**，不写 live `04_Workflows/tickets/*_state.md`。

> ⚠️ **重要：demo / 非 prod 流程**
> - `--execute` 模式仅允许 `WC-DEMO-*` ticket，拒绝生产票（如 `W1-T*`）。
> - 产物写入隔离目录 `artifacts/e2e/<ticket_id>/`，不污染正式 `artifacts/order_ledger/`。
> - 本流程不调用真实支付／金流 API；§4 order create 默认止于 `DRAFT`；**sandbox** 金流 happy-path（DRAFT→PENDING_PAYMENT→PAID）见 **§4+ Payment**（WC-M3 · mock adapter only）。
> - `REFUNDED` 与 prod provider 仍 deferred；§4+ **不** 宣称为 prod 金流闭环。

---

## 6. E2E Runner 执行范例（`--execute` 模式）

> **警告**：本节所示 `--execute` 为 **demo 级本地验证**，非生产金流闭环。

### 6.1 标准执行（以 WC-DEMO-1 为例 · manual HITL 路径）

> 默认 `--execute` **不含** `--use-hitl-fixtures` 时，§3/§4 仍须 **手工编辑 live STATE**（HITL 步骤为 `hitl` / `skipped`）。完整无 HITL 自动化见 **§6.5 fixture execute**。

```bash
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --execute \
  --json
```

**预期输出（JSON 摘要）**：

```json
{
  "ok": true,
  "mode": "execute",
  "ticket_id": "WC-DEMO-1",
  "artifact_dir": "artifacts/e2e/WC-DEMO-1",
  "runbook": "docs/wave_c/WC_T7_e2e_walkthrough_runbook.md",
  "steps": [
    {"step_id": "0", "title": "Environment check", "status": "ok"},
    {"step_id": "2", "title": "Dispatch cards + eligibility gate", "status": "ok"},
    {"step_id": "3-hitl", "title": "HITL: edit STATE to review/reviewer", "status": "hitl"},
    {"step_id": "3", "title": "Comms JSONL", "status": "skipped", "reason": "missing prerequisite: ..."},
    {"step_id": "4-hitl", "title": "HITL: edit STATE to ready_for_order", "status": "hitl"},
    {"step_id": "4", "title": "Order create + lookup + replay", "status": "ok"},
    {"step_id": "5", "title": "Module unittest cross-check", "status": "ok"}
  ]
}
```

### 6.2 生产票阻止示例

```bash
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket W1-T2 \
  --artifacts-root artifacts/e2e \
  --execute \
  --json
```

**预期输出（拒绝）**：

```json
{"ok": false, "message": "ticket_id must start with 'WC-DEMO-' ... refusing to run on production tickets"}
```

### 6.3 Dry-run 对照（不写入业务档 · 三种路径之一）

> 另见档头 **「执行路径分工」**；dry-run 为纯编排骨架，与 manual HITL / fixture execute 并列。

```bash
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --dry-run \
  --json
```

**预期输出**：`"mode": "dry_run"`，且不会创建 `artifacts/e2e/WC-DEMO-1/orders.jsonl`。`--dry-run` 允許建立空的 `artifacts/e2e/<ticket_id>/` 目錄，但不寫業務檔（WD-P9-T1 Orchestrator 裁決）。

### 6.4 产物验证

执行成功后，检查隔离目录产物：

```bash
cat artifacts/e2e/WC-DEMO-1/orders.jsonl | head -1 | python -m json.tool
```

**预期字段（order_ledger_v1 schema）**：

```json
{
  "order_id": "ORD-WC-DEMO-1",
  "ticket_id": "WC-DEMO-1",
  "ticket_ref": "04_Workflows/tickets/WC-DEMO-1_state.md",
  "amount_minor": 10000,
  "currency": "TWD",
  "order_status": "DRAFT",
  "created_at": "2026-06-19T12:00:00Z",
  "idempotency_key": "WC-DEMO-1",
  "schema_version": "order_ledger_v1"
}
```

> **注意**：M2 fixture execute 与 runner step 4 默认 `order_status` 止于 **DRAFT**。完整 sandbox payment 链（DRAFT→PENDING_PAYMENT→PAID）须加 **`--include-payment`** 跑 §4+ runner step 6，或按 §4+.2 逐步 CLI；**≠ prod 金流** · **≠ INT Tier-A**。

### 6.5 HITL fixture 模式（`--use-hitl-fixtures` · demo-only · 非 prod E2E）

> **定位**：demo skeleton 自动化（WD-P9-T2）；**不**移除 runbook §3/§4 的手工 HITL 说明；**不**写 live `04_Workflows/tickets/<ticket_id>_state.md`。Fixture execute **不等于** production HITL gate。

**用途**

| 模式 | 适用场景 | HITL | 产物 |
|------|----------|------|------|
| `--dry-run` | 本地预览命令 | 打印 HITL 提示 | 不写业务档 |
| `--execute`（默认） | 真人 walkthrough | 须手工编辑 STATE | 依赖 `before_review.md` + live state |
| `--execute --use-hitl-fixtures` | CI / nightly smoke | 跳过；从 fixture 复制快照 | `artifacts/e2e/<ticket>/` 内 comms + orders |

**Fixture 文件清单**（权威路径：`tests/fixtures/e2e_walkthrough/`）

| Fixture 源文件 | Materialize 目标 | 对应 runbook 步骤 |
|----------------|------------------|-------------------|
| `<ticket_id>_before_review.md` | `artifacts/e2e/<ticket_id>/before_review.md` | §3 变更前快照 |
| `<ticket_id>_state_review.md` | `artifacts/e2e/<ticket_id>/state_review.md` | §3 comms `--after` |
| `<ticket_id>_state_ready_for_order.md` | `artifacts/e2e/<ticket_id>/state_ready_for_order.md` | §4 order `--ticket-path` |

**WC-DEMO-1 示例 fixture 集**

- `tests/fixtures/e2e_walkthrough/WC-DEMO-1_before_review.md` — `in_progress` / implementer
- `tests/fixtures/e2e_walkthrough/WC-DEMO-1_state_review.md` — `review` / reviewer（comms diff）
- `tests/fixtures/e2e_walkthrough/WC-DEMO-1_state_ready_for_order.md` — `next_action` 含 `ready_for_order`

**Demo fixture execute 命令（demo-only · 本地验证 · 非 merge gate）**

> **诚实声明**：此命令适合本地或 CI advisory step（见下文 **CI advisory**）；**不**接入任何 required / merge-blocking check（AC-7 仍为 optional deferred · demo skeleton · 非 prod E2E）。

```bash
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --execute \
  --use-hitl-fixtures \
  --json

python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v
```

**预期**：`ok: true`；step 3 comms 与 step 4 order 为 `ok`（非 skip）；产物限于 `artifacts/e2e/WC-DEMO-1/`（comms JSONL + `orders.jsonl`）。

**护栏（与 `--execute` 相同）**

- 仅 `WC-DEMO-*` ticket；`artifacts-root` 必须在 `artifacts/e2e/` 下。
- 不写入 `artifacts/order_ledger/` 或默认 comms outbox。
- `--use-hitl-fixtures` 必须与 `--execute` 同用；不能与 `--dry-run` 组合。

**CI advisory（Wave-G · `p9-wc-m2-fixture-execute` · demo skeleton · non-blocking）**

Workflow：`.github/workflows/p9-wc-m2-fixture-execute.yml`；job 名 **`p9-wc-m2-fixture-execute`**。

| 项 | 说明 |
|----|------|
| **触发** | `schedule`（每两日 UTC 06:00）· `workflow_dispatch` · 可选 path-filtered `pull_request` |
| **命令** | 与上文 Demo fixture execute 命令块相同（`WC-DEMO-1` · `--execute --use-hitl-fixtures --json`） |
| **附加** | 默认再跑 `python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v`（11 tests） |
| **写入范围** | **仅** `artifacts/e2e/WC-DEMO-1/`（comms JSONL · `orders.jsonl` · materialized HITL 快照） |
| **不写** | live `04_Workflows/tickets/*_state.md` · 默认 comms outbox · `artifacts/order_ledger/` |
| **性质** | **advisory / demo-only / non-prod**；job 设 `continue-on-error: true`；**不是** required check 或 merge gate |

> **截至 v0.3 + Wave-G**：CI advisory 已接入，但仍是 **demo skeleton** 观测轨；fixture execute **不等于** production HITL gate 或 INT Tier-A pass。升格为 blocking gate 须尚書省批文。

---

## 0. 环境与目录

1. 确认当前目录为 repo 根。
2. 创建隔离目录：`artifacts/e2e/<ticket_id>/`。

**预期输出**：目录存在且为空或仅含本 walkthrough 产物。  
**失败诊断**：若路径不在 `artifacts/e2e/` 下，停止——避免污染默认 `artifacts/ticket_comms/` 或 `artifacts/order_ledger/`。

---

## 1. 准备初始 `*_state.md`（`in_progress` / `implementer`）

1. 复制模板：`04_Workflows/tickets/_templates/ticket_state.template.md` → `04_Workflows/tickets/<ticket_id>_state.md`。
2. 填写 **FRAME**（至少 `Title` · `AllowedPaths` · `Dependencies: 无` · `VerificationCommands` 指向本 runbook）。
3. 填写 **STATE** 为 implementer 可接单态，例如：
   - `overall_status: in_progress`
   - `implementation_status: in_progress`（可选，与 WC-T2 fixture 对齐）
   - `current_owner: implementer`
   - `next_action: Implementer runs M2 E2E smoke`
   - `status_by_role.implementer: in_progress` · `reviewer: pending`
4. **B_REPORT / C_REPORT / D_REPORT** 可留空或占位；dispatch / eligibility 只读 FRAME + STATE。

**可选预检（eligibility 应返回 eligible）**

```bash
python scripts/run_ticket_eligibility.py --ticket <ticket_id> --requested-role implementer --format json
```

**预期输出**：JSON 中 `eligible: true`（或项目惯用等价键）。  
**失败诊断**：检查 STATE `overall_status` / `status_by_role` / FRAME `Dependencies` 是否阻塞；勿对生产票强行 `--force-eligibility`。

---

## 2. Dispatch cards + eligibility gate

1. 刷新 dispatch plan 并生成 Implementer 指令卡：

```bash
python scripts/run_dispatch_cards.py \
  --refresh-plan \
  --ticket <ticket_id> \
  --role implementer \
  --eligibility-gate block \
  --out-dir artifacts/e2e/<ticket_id>/cards/ \
  --json-summary artifacts/e2e/<ticket_id>/dispatch_cards_run.json \
  --pretty
```

2. 若 demo 票因依赖 / blocked 被 gate 拦截、但仍需验证写卡路径，Orchestrator 可 **一次性** override（须留痕）：

```bash
python scripts/run_dispatch_cards.py \
  --refresh-plan \
  --ticket <ticket_id> \
  --role implementer \
  --eligibility-gate block \
  --force-eligibility \
  --out-dir artifacts/e2e/<ticket_id>/cards/ \
  --pretty
```

3. **Dry-run 对照**（不写卡，只看 summary）：

```bash
python scripts/run_dispatch_cards.py \
  --refresh-plan \
  --ticket <ticket_id> \
  --role implementer \
  --eligibility-gate block \
  --dry-run \
  --pretty
```

**预期输出**：`cards_generated >= 1`；`artifacts/e2e/<ticket_id>/cards/<ticket_id>__implementer.cursor.md` 存在；summary 无 `eligibility_blocked`（除非 STATE 不满足 gate）。  
**失败诊断**：先跑 `--dry-run` 看 `eligibility_blocked` 原因；必要时一次性 `--force-eligibility` 并记入战报。

---

## 3. STATE → `review` / `reviewer` + comms JSONL

> WC-T2 CLI **不写入** live state；先快照再改文件，再对比 before/after。  
> **顺序**：本步全部完成后再进入 §4；勿与 `ready_for_order` 编辑并行，否则 comms diff 会混入开单态字段。

1. 保存变更前快照：

```bash
cp 04_Workflows/tickets/<ticket_id>_state.md artifacts/e2e/<ticket_id>/before_review.md
```

（Windows PowerShell：`Copy-Item 04_Workflows/tickets/<ticket_id>_state.md artifacts/e2e/<ticket_id>/before_review.md`）

2. **手工编辑** `04_Workflows/tickets/<ticket_id>_state.md` 的 **STATE** 为 reviewer 关口，例如：
   - `overall_status: review`
   - `implementation_status: in_review`
   - `current_owner: reviewer`
   - `next_action: Reviewer validates comms JSONL`
   - `status_by_role.implementer: done` · `reviewer: in_progress`

3. 生成 comms（append JSONL）：

```bash
python scripts/run_ticket_state_update_with_comms.py \
  --before artifacts/e2e/<ticket_id>/before_review.md \
  --after 04_Workflows/tickets/<ticket_id>_state.md \
  --outbox-dir artifacts/e2e/<ticket_id>/comms
```

4. **Dry-run**（不写 JSONL）：

```bash
python scripts/run_ticket_state_update_with_comms.py \
  --before artifacts/e2e/<ticket_id>/before_review.md \
  --after 04_Workflows/tickets/<ticket_id>_state.md \
  --dry-run
```

**预期输出**：stdout `ok: true` · `sent: true`；`artifacts/e2e/<ticket_id>/comms/ticket_comms.jsonl` 新增一行 `ticket_comms_v0.1`（`overall_status`：`in_progress` → `review`）。  
**失败诊断**：确认 `before`/`after` 路径正确且 STATE 字段确有差异；用 `--dry-run` 查看 payload 再决定是否写 JSONL。

---

## 4. `ready_for_order` + order create + lookup

1. **手工编辑** **STATE** 为开单就绪（主路径：`next_action` 含 `ready_for_order`），例如：
   - `overall_status: review`（或 `done`；见 WC-T4 §4.2 备选）
   - `current_owner: orchestrator`
   - `next_action: ready_for_order — create order for <ticket_id> E2E demo`
   - `status_by_role.reviewer: done`

2. 创建 order（使用隔离 JSONL）：

```bash
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/<ticket_id>/orders.jsonl \
  create \
  --ticket <ticket_id> \
  --amount-minor 10000 \
  --currency TWD
```

3. Lookup 验证：

```bash
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/<ticket_id>/orders.jsonl \
  lookup \
  --ticket-id <ticket_id>
```

4. 幂等 replay（同 ticket 再次 create 应返回 `replay: true`）：

```bash
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/<ticket_id>/orders.jsonl \
  create \
  --ticket <ticket_id> \
  --amount-minor 10000 \
  --currency TWD
```

**预期输出**：create → `ok: true` · `message: order_created` · `order.order_id` 为 `ORD-<ticket_id>`；lookup 返回同 order；replay → `replay: true`。  
**失败诊断**：确认 `--jsonl-path` 在子命令 **之前**；STATE `next_action` 含 `ready_for_order`；JSONL 路径在 `artifacts/e2e/<ticket_id>/` 下。

---

## 4+. Payment（sandbox DRAFT→PAID）

> **定位**：WC-M3 sandbox payment happy-path 可复制正文；命令与 [`WH-P9-PROD-payment-happy-path-execute-v1`](../../04_Workflows/tickets/WH-P9-PROD-payment-happy-path-execute-v1_state.md) B_REPORT 一致。  
> **前提**：§4 order create 已完成 · `orders.jsonl` 中已有 `order_status: DRAFT` 行。  
> **护栏**：仅 `WC-DEMO-*` · JSONL 限 `artifacts/e2e/<ticket_id>/` · **不写** `artifacts/order_ledger/` 默认 prod 路径。

### 4+.1 前置假设

| 项 | 要求 |
|----|------|
| Demo 票 | `<ticket_id>` 必须以 `WC-DEMO-` 开头（示例：`WC-DEMO-1`） |
| 前置链 | §4 create 成功 · `order_id` 为 `ORD-<ticket_id>` · 当前态 **DRAFT** |
| 隔离 JSONL | `artifacts/e2e/<ticket_id>/orders.jsonl`（与 §4 相同路径） |
| Sandbox gate | 执行 `pay` 前须 `GOV_PAYMENT_SANDBOX_ENABLED=1`（默认 `0` · fail-closed） |
| Provider | **无**真实 Stripe／金流 API；adapter 仅回 mock `provider_ref`（如 `SANDBOX-REF-ORD-WC-DEMO-1`） |
| 可选 bootstrap | 若尚无 DRAFT，可先跑 fixture execute（§6.5）至 step 4 order `ok` |

**与 runner step 6 关系**：runner 已内建 `step_id=6-payment`（`--include-payment`）；**默认不启用**，需明确加 flag。Manual / Reviewer 审计可按 §4+.2 逐步 CLI；fixture execute 加 `--include-payment` 可一键至 PAID。**non-claims 不变**（sandbox-only · `WC-DEMO-*` · 不触 prod ledger）。

### 4+.2 步骤清单（可复制命令链）

#### 一键 runner（推荐 · fixture execute + payment）

> **范围**：仅 `WC-DEMO-*` ticket；仅触 sandbox adapter / `artifacts/e2e/<ticket>/` 目录；**不触** prod ledger。

```bash
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --execute \
  --use-hitl-fixtures \
  --include-payment \
  --json
```

**预期输出**：`ok: true` · step `6-payment` 为 `ok` · `order_status: PAID` · orders JSONL 含 DRAFT → PENDING_PAYMENT → PAID 三行。

#### 重跑 / 清理（操作注意 · non-claims）

若 `WC-DEMO-*` 对应 sandbox artifacts 目录中**已有 PAID 订单**，再次执行含 step 6 的 walkthrough 时，transition 步骤可能报 `invalid_transition`，但最终 lookup 仍会看到 PAID。建议在每次完整 walkthrough 前：

- 使用新的 `WC-DEMO-*` ticket，或
- 清理 `artifacts/e2e/<ticket>/` 目录。

本节仅说明操作注意；**不**宣称为 prod 金流或 INT 验收。

#### 逐步 CLI（Manual / Reviewer 审计）

**Step 0（可选）— fixture execute 至 DRAFT**

若本地尚无 §4 产物，先 materialize comms + order（仍 demo-only · 不写 live STATE）：

```bash
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --execute \
  --use-hitl-fixtures \
  --json
```

**Step 1 — DRAFT → PENDING_PAYMENT**

```bash
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl \
  transition \
  --order-id ORD-WC-DEMO-1 \
  --to pending_payment \
  --actor cli \
  --reason sandbox_walkthrough
```

**预期输出**：`ok: true` · `message: order_transitioned` · `order.order_status` 为 `PENDING_PAYMENT` · JSONL append 含 `transitioned_at` · `actor` · `reason`。

**Step 2 — sandbox adapter charge → PAID**

Bash / macOS / Linux：

```bash
GOV_PAYMENT_SANDBOX_ENABLED=1 python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl \
  pay \
  --order-id ORD-WC-DEMO-1
```

Windows PowerShell：

```powershell
$env:GOV_PAYMENT_SANDBOX_ENABLED="1"
python scripts/run_order_intake.py `
  --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl `
  pay `
  --order-id ORD-WC-DEMO-1
```

**预期输出**：`ok: true` · `message: charge_succeeded` · `order.order_status` 为 `PAID` · `provider_ref` 前缀 `SANDBOX-REF-` · **无** API key／secret 原文。

**Step 3 — lookup inspect（终态审计）**

```bash
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl \
  lookup \
  --order-id ORD-WC-DEMO-1
```

**预期输出**：`order_status: PAID` · 含 audit 栏位；JSONL 共 **3 行**（DRAFT · PENDING_PAYMENT · PAID · latest-wins reload）。

**Step 4（可选）— idempotent pay replay**

对已 `PAID` order 再次 `pay` 应返回 `ok: true` · `message: already_paid`（不重复脏行）。

**Step 5（可选）— 模块单测交叉对照**

```bash
python -m unittest tests.test_order_ledger_transition tests.test_payment_sandbox_adapter tests.test_order_ledger_integration -v
```

**失败诊断**

| 症状 | 检查 |
|------|------|
| `sandbox_disabled` | `GOV_PAYMENT_SANDBOX_ENABLED` 未设为 `1` |
| `invalid_transition` / `ok: false` | 当前态非 `PENDING_PAYMENT`（勿从 DRAFT 直接 `pay`） |
| JSONL 路径错误 | `--jsonl-path` 须在子命令 **之前** · 路径在 `artifacts/e2e/<ticket>/` 下 |
| 非 demo 票 | transition / pay 仍须 `WC-DEMO-*` 隔离链；勿对 `W1-T*` 放宽 |

### 4+.3 验证与回滚

**JSONL 全链 inspect**

```bash
cat artifacts/e2e/WC-DEMO-1/orders.jsonl
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl \
  lookup \
  --order-id ORD-WC-DEMO-1
```

**验收 checklist（Reviewer 可审计）**

- [ ] 三行 JSONL：`DRAFT` → `PENDING_PAYMENT` → `PAID`
- [ ] 每行 transition 含 `transitioned_at` · `actor` · `reason`（WC-M3 §2.3）
- [ ] `provider_ref` 为 mock 前缀 · stdout／JSONL **无** secret 原文
- [ ] 产物 **仅** 在 `artifacts/e2e/WC-DEMO-1/` · 默认 `artifacts/order_ledger/` 无 demo 行

**清理（与 §6 清理一致）**

- 删除 `artifacts/e2e/<ticket_id>/` 整目录（含 payment JSONL 行）
- 若误写默认 ledger，grep `<ticket_id>` 后手工剔除（仅本地 demo）

**可选 refund（sandbox · 非本 walkthrough 必跑）**

PAID → REFUNDED 见 [`WC_M3_payment_closure_scope_v1.md`](WC_M3_payment_closure_scope_v1.md) §2 · adapter `refund`；仍 **sandbox-only** · **≠ prod**。

### 4+.4 Non-claims（诚实边界）

本节 sandbox payment 链 **可以** 主张：

- 在 `WC-DEMO-*` demo 票与 `artifacts/e2e/<ticket>/` 隔离路径上，**可重跑、可审计** 的 DRAFT→PENDING_PAYMENT→PAID CLI 链（mock adapter · env gate）。
- 与 WC-M3 scope · alignment matrix §4+ · happy-path execute 票证据 **命令一致**。

本节 **明确不能** 主张：

- **≠ prod 金流闭环** · **≠** 真实 payment provider · **≠** 写入 prod order ledger。
- **≠ INT Tier-A** pass · **≠** merge-blocking / required CI（M2 fixture CI 仍 advisory · non-blocking）。
- **≠** production HITL gate · **不** 替代 §3/§4 真人 STATE 编辑验收语义。
- runner `--use-hitl-fixtures` **默认仍止于 DRAFT**；加 **`--include-payment`** 可内建 step 6 一键至 PAID（sandbox-only · `WC-DEMO-*` only）。

**索引**：WC-M3 SSOT · [`WC_M3_payment_closure_scope_v1.md`](WC_M3_payment_closure_scope_v1.md) · alignment matrix [`WC_M2_INT_HITL_alignment_matrix_v1.md`](WC_M2_INT_HITL_alignment_matrix_v1.md) §4+ 行 · execute 证据 [`WH-P9-PROD-payment-happy-path-execute-v1_state.md`](../../04_Workflows/tickets/WH-P9-PROD-payment-happy-path-execute-v1_state.md)。

---

## 5. 一键 unittest 对照（非 E2E 替代）

各模块单测仍应独立全绿；E2E 为跨 CLI 手工串联：

```bash
python -m unittest tests.test_ticket_eligibility tests.test_dispatch_cards tests.test_ticket_comms tests.test_ticket_state_update_cli tests.test_order_ledger tests.test_order_ledger_integration tests.test_order_ledger_transition tests.test_payment_sandbox_adapter -v
```

**预期输出**：全部 tests OK。  
**失败诊断**：定位失败模块单测后再重跑 E2E；单测失败时 E2E pass 不具说服力。

---

## 6. 清理（可选）

- 删除 `04_Workflows/tickets/<ticket_id>_state.md`（demo 票）
- 删除 `artifacts/e2e/<ticket_id>/` 整目录
- 若曾写入默认路径，检查 `artifacts/ticket_comms/ticket_comms.jsonl` 与 `artifacts/order_ledger/orders.jsonl` 是否误污染

**预期输出**：demo 票与隔离产物已移除；默认 outbox/ledger 无 demo 行。  
**失败诊断**：grep JSONL 中 `<ticket_id>`；发现污染则从默认 ledger 手工剔除或整文件重置（仅本地 demo 环境）。

---

## INT gate 对齐（草稿 · v0.1）

> **逐步矩阵 SSOT**：本节为改動類型摘要；**逐步** HITL × fixture × INT tier 对照见 [`WC_M2_INT_HITL_alignment_matrix_v1.md`](WC_M2_INT_HITL_alignment_matrix_v1.md)（`WH-P9-M2-INT-alignment-v1` · 设计 SSOT · 非实作票）。

> **职责分离**：Control Plane E2E 验证 **Wave C M2 CLI 链**在 demo 票上的可串联性；INT Tier-A 验证 **Wave 6/7 装配层** unittest 不变量。**两者互补，不可互相替代。**

| 改动类型 | 推荐验证 | 过 gate 含义 |
|----------|----------|--------------|
| Control Plane CLI（eligibility · dispatch cards · comms · order intake） | 本 runbook §1–§4 或 §5 单测 + 本 runbook 手工链 | Control Plane E2E **pass** |
| `ticket_eligibility` · `_dispatch_cards` · `order_ledger` 实现细节 | §5 对应模块 unittest | 模块回归 **pass**（非 INT） |
| envelope / manifest / QA / orchestrator / runner（Wave 6/7 装配） | `python 04_Workflows/_wave7_regression_gate.py --tier A` | INT Tier-A **pass** |
| Wave 8 M2 契约 / artifact storage / orch pipeline | 同上 Tier-A（见 `docs/phase6-int-regression-gate-contract-v1.md` §1） | INT Tier-A **pass** |
| PR merge 最低门槛 | `core-agent-smoke.yml`（PR smoke）+ `eval-gate-ci.yml` | PR CI **pass**（仍 **非** INT Tier-A） |

**明确声明**

1. **Control Plane E2E pass ≠ INT pass**：跑通本 runbook 不证明 Wave 6/7 装配未退化。
2. **INT Tier-A pass ≠ Control Plane E2E pass**：INT 不覆盖 dispatch cards / comms JSONL / order ledger 链。
3. 改 Control Plane 路径：至少跑 §5 单测；发版或 M2/M3 验收前跑本 runbook。
4. 改 Wave 6/7 装配路径：本地 **mandatory** 跑 INT Tier-A（见 `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md` §2.1）。
5. 升格 PR required / prod gate：须尚書省批文；本对齐表 **不**自动开启任何 blocking CI。

**索引**

- INT SSOT：`docs/phase6-int-regression-gate-contract-v1.md`
- 实现附录：`04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`
- Wave C 总览：`docs/wave_c/overview.md`

---

## 附录 · WC-T5 path_id 对照表

> **SSOT**：`docs/wave_c/WC_T5_automation_coverage_contract.md` §4 路径矩阵与附录 A JSON（`wc_t5_paths_v0.1`）。  
> **用途**：将本 runbook E2E 步骤与 T5 `wc.m2.*` path_id 及契约级 `verification_command` 对齐，便于 Scribe／Reviewer 交叉审计。  
> **边界**：下表 `verification_command` **逐字引用 T5 契约**（非 E2E 隔离路径变体）；跑通本 runbook **不等于** INT Tier-A pass，亦 **不** 构成 PR required / prod blocking CI 授权（见上文 §INT gate 对齐）。

### 表 A · E2E 步骤 ↔ path_id 映射

| Runbook § | E2E 步骤（摘要） | `wc.m2.path_id` | `automation_tier` | `verification_command`（T5 SSOT） |
|-----------|------------------|-----------------|-------------------|-----------------------------------|
| §1 | 可选 eligibility 预检（`--requested-role implementer`） | `wc.m2.eligibility.check_role` | auto | `python scripts/run_ticket_eligibility.py --ticket W1-T2 --requested-role reviewer --format json` |
| §1 | 手工创建／编辑初始 STATE（implementer 可接单态） | `wc.m2.state.write_ticket` | forbidden | —（禁止自动化；仅 Orchestrator HITL 手工编辑） |
| §2 | 刷新 dispatch plan + 生成指令卡（`--eligibility-gate block`） | `wc.m2.dispatch.refresh_and_cards` | auto | `python scripts/run_dispatch_cards.py --refresh-plan --dry-run --pretty` |
| §2 | Orchestrator 一次性 `--force-eligibility` override（须留痕） | `wc.m2.dispatch.force_eligibility_override` | HITL | `python scripts/run_dispatch_cards.py --force-eligibility --dry-run --pretty` |
| §2 | Dry-run 对照（不写卡，只看 summary） | `wc.m2.dispatch.refresh_and_cards` | auto | `python scripts/run_dispatch_cards.py --refresh-plan --dry-run --pretty` |
| §3 | 手工编辑 STATE → `review` / `reviewer` 关口 | `wc.m2.state.write_ticket` | forbidden | —（禁止自动化；仅 Orchestrator HITL 手工编辑） |
| §3 | before/after 快照 → comms JSONL（append outbox） | `wc.m2.comms.state_transition` | auto | `python scripts/run_ticket_state_update_with_comms.py --before tests/fixtures/ticket_comms/wc_t2_before_state.md --after tests/fixtures/ticket_comms/wc_t2_after_state.md` |
| §3 | comms dry-run（不写 JSONL） | `wc.m2.comms.state_transition_dry_run` | auto | `python scripts/run_ticket_state_update_with_comms.py --before tests/fixtures/ticket_comms/wc_t2_before_state.md --after tests/fixtures/ticket_comms/wc_t2_after_state.md --dry-run` |
| §4 | 手工编辑 STATE → `ready_for_order` 开单就绪 | `wc.m2.state.write_ticket` | forbidden | —（禁止自动化；仅 Orchestrator HITL 手工编辑） |
| §4 | order create（隔离 JSONL） | `wc.m2.order.create` | auto | `python scripts/run_order_intake.py create --ticket WC-T4-INT --amount-minor 10000 --currency TWD --ticket-path tests/fixtures/order_ledger/WC-T4-INT_state.md --dry-run` |
| §4 | order lookup（按 ticket_id） | `wc.m2.order.lookup` | auto | `python scripts/run_order_intake.py lookup --ticket-id WC-T4-INT --jsonl-path artifacts/order_ledger/orders.jsonl` |
| §4 | order create 幂等 replay（同 ticket 再次 create） | `wc.m2.order.create` | auto | `python scripts/run_order_intake.py create --ticket WC-T4-INT --amount-minor 10000 --currency TWD --ticket-path tests/fixtures/order_ledger/WC-T4-INT_state.md --dry-run` |
| §4+ | order → PENDING_PAYMENT（sandbox transition） | `wc.m2.order.transition` | auto | `python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl transition --order-id ORD-WC-DEMO-1 --to pending_payment --actor cli --reason sandbox` |
| §4+ | sandbox adapter charge → PAID | `wc.m2.order.pay_sandbox` | auto | `GOV_PAYMENT_SANDBOX_ENABLED=1 python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl pay --order-id ORD-WC-DEMO-1` |
| §4+ | payment 状态链 JSONL audit（lookup by order_id） | `wc.m2.order.lookup` | auto | `python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl lookup --order-id ORD-WC-DEMO-1` |
| §5 | 模块 unittest 对照（非 E2E 替代） | （多 path_id） | auto | 见 §5 命令块；单路径示例见 T5 `wc.m2.eligibility.check` · `wc.m2.dispatch.cards_generate` 等 |

### 表 B · 相关 path_id（本 runbook 未逐步展开）

| 说明 | `wc.m2.path_id` | `automation_tier` | `verification_command`（T5 SSOT） |
|------|-----------------|-------------------|-----------------------------------|
| 无角色上下文的 eligibility 检查 | `wc.m2.eligibility.check` | auto | `python scripts/run_ticket_eligibility.py --ticket W1-T2 --format json` |
| eligibility gate warn 模式（仍写卡） | `wc.m2.dispatch.eligibility_gate_warn` | auto | `python scripts/run_dispatch_cards.py --eligibility-gate warn --dry-run --pretty` |
| 列出 ledger 中全部 order | `wc.m2.order.list` | auto | `python scripts/run_order_intake.py list --jsonl-path artifacts/order_ledger/orders.jsonl` |
| T6 单票闭环（eligibility + dispatch + order + comms · 可选替代 §1–§4 手工链） | `wc.m2.loop.order_handoff` | auto | `python scripts/run_control_plane_order_handoff.py --ticket WC-T4 --amount-minor 10000 --currency TWD --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md --dry-run` |
| order intake 结果 → comms JSONL | `wc.m2.comms.order_event` | auto | `python -m unittest tests.test_control_plane_order_handoff.TestOrderCommsPayload -v` |
| 自动开 Cursor chat | `wc.m2.chat.open_cursor` | forbidden | —（禁止；Multi-Chat 仍人工开 chat） |

**读表说明**

1. **HITL / forbidden 行**：§1 · §3 · §4 中写 live `*_state.md` 的步骤对应 `wc.m2.state.write_ticket`（forbidden）；本 runbook **不** 提供 `--execute` 自动写 live STATE；`--use-hitl-fixtures` 仅 materialize 至 `artifacts/e2e/<ticket>/`（demo skeleton）。
2. **verification_command 与 E2E 命令差异**：E2E 使用 `artifacts/e2e/<ticket_id>/` 隔离路径与 demo 票；T5 契约命令用于 **模块级 / 契约级** 重跑，二者互补。
3. **职责分离（重申）**：本附录对齐 T5 覆盖率边界；**Control Plane E2E pass ≠ INT Tier-A pass**；契约与附录 **不** 授权 PR required 或 prod blocking gate。

**交叉引用**

- T5 契约全文：`docs/wave_c/WC_T5_automation_coverage_contract.md`
- T5 契约测试：`python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v`

---

*WC-T7 E2E Walkthrough Runbook · v0.4 · 2026-06-24 · §4+ sandbox payment (WC-M3) · HITL fixture (`--use-hitl-fixtures`) · runner 见 `scripts/run_wc_m2_e2e_walkthrough.py`*
