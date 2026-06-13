# WC-T4 · Order Ledger Intake (v0.1)

> **票号**：WC-T4  
> **实现**：`04_Workflows/order_ledger/`  
> **CLI**：`scripts/run_order_intake.py`  
> **Schema**：`shared/schemas/order_ledger_v1.json`  
> **依赖**：`04_Workflows/dispatch_executor.py`（只读解析 `TicketRecord`）

---

## 1. 目的

在 Multi-Chat **ticket state markdown** 与 Wave 8 商务 Order 模型之间，提供最小 **order intake 台账**：

- 输入：ticket id + 金额（`amount_minor`）+ 币别（`currency`）
- 门禁：`ready_for_order` gate（`next_action` 关键字 **或** `overall_status ∈ {review, done}`）
- 输出：结构化 `OrderRecord` + JSONL 持久化
- **不**写入 `*_state.md`、**不**调用支付网关、**不**实现完整 Order 状态机

与 W4-T3（完整 milestone / transition）**分层**：本票仅 **intake 建档**；状态转移、手动金流登记另票。

---

## 2. 已拍板策略

| 项 | 裁決 |
|----|------|
| **一 ticket 一 order（A）** | 同一 `ticket_id` 仅允许一条 order；重复 `create` 返回已有记录（`replay: true`） |
| **ready_for_order gate** | 主路径：`next_action` 含关键字；备选：`overall_status ∈ {review, done}` |
| **存储** | v0.1：`InMemoryOrderLedgerStore` + `JsonlFileStore`（append-only JSONL） |
| **范围** | dataclass、gate、create、lookup/list CLI、基本 unittest |

---

## 3. 数据来源（SSOT）

| 层级 | 路径 | 说明 |
|------|------|------|
| Ticket state | `04_Workflows/tickets/<ticket_id>_state.md` | FRAME + STATE |
| 解析器 | `dispatch_executor.parse_ticket_state_markdown` | → `TicketRecord` |
| Order 台账 | `artifacts/order_ledger/orders.jsonl`（默认） | append-only JSONL |
| Schema | `shared/schemas/order_ledger_v1.json` | 对外 JSON 形状 |

---

## 4. ready_for_order gate

### 4.1 关键字（主路径）

`next_action`（大小写不敏感）匹配任一：

| 关键字 | 说明 |
|--------|------|
| `ready_for_order` | 主关键字 |
| `ready for order` | 空格变体 |
| `order intake` | intake 语义 |
| `create order` | 显式开单 |
| `开单` / `開單` | 中文 shorthand |

### 4.2 状态备选（次路径）

当 `next_action` **未**命中关键字时，若 `overall_status` 为 `review` 或 `done`，仍视为 ready（便于 reviewer 收尾或 scribe 前开单）。

### 4.3 返回形状

```python
{
    "ready": bool,
    "gate": "keyword" | "status_alt" | "not_ready",
    "reasons": ["..."]
}
```

---

## 5. Order 数据模型（v1 最小）

```json
{
  "schema_version": "order_ledger_v1",
  "order_id": "ORD-WC-T4",
  "ticket_id": "WC-T4",
  "ticket_ref": "04_Workflows/tickets/WC-T4_state.md",
  "amount_minor": 10000,
  "currency": "TWD",
  "order_status": "DRAFT",
  "created_at": "2026-06-13T12:00:00Z",
  "idempotency_key": "WC-T4"
}
```

| 字段 | 说明 |
|------|------|
| `order_id` | 默认 `ORD-{ticket_id}`（一 ticket 一 order） |
| `amount_minor` | 最小货币单位整数（> 0） |
| `currency` | ISO 4217 三字码（大写） |
| `order_status` | v0.1 固定 `DRAFT`（无状态机） |
| `idempotency_key` | 默认等于 `ticket_id` |

完整 JSON Schema 见 `shared/schemas/order_ledger_v1.json`。

---

## 6. 模块布局

| 模块 | 路径 | 职责 |
|------|------|------|
| 模型 | `order_ledger/models.py` | `OrderRecord` dataclass |
| 门禁 | `order_ledger/gates.py` | `is_ready_for_order`, `validate_currency`, `validate_amount_minor` |
| 服务 | `order_ledger/service.py` | `create_order_for_ticket`, `lookup_order`, `list_orders` |
| 存储 | `order_ledger/store.py` | `InMemoryOrderLedgerStore`, `JsonlFileStore` |
| CLI | `scripts/run_order_intake.py` | `create` / `lookup` / `list` / `--dry-run` |

包导入（`04_Workflows` 在 `sys.path`）：

```python
from order_ledger import create_order_for_ticket, is_ready_for_order
from order_ledger.store import JsonlFileStore
```

---

## 7. CLI 用法

```bash
# 默认：从 04_Workflows/tickets/<ticket_id>_state.md 读取 STATE（无需 --ticket-path）
python scripts/run_order_intake.py create \
  --ticket WC-T4-INT \
  --amount-minor 10000 \
  --currency TWD

# 覆盖 ticket state 路径（fixture / 本地实验）
python scripts/run_order_intake.py create \
  --ticket WC-T4 \
  --amount-minor 10000 \
  --currency TWD \
  --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md

# 仅预览，不写盘
python scripts/run_order_intake.py create ... --dry-run

# 查询
python scripts/run_order_intake.py lookup --order-id ORD-WC-T4
python scripts/run_order_intake.py lookup --ticket-id WC-T4

# 列表
python scripts/run_order_intake.py list
```

---

## 8. 服务返回形状

### create_order_for_ticket

```python
{
    "ok": True,
    "message": "order_created",
    "replay": False,
    "order": { ... OrderRecord dict ... }
}
```

失败示例：

| `message` | 条件 |
|-----------|------|
| `not_ready_for_order` | gate 未通过 |
| `invalid_currency` | 币别非法 |
| `invalid_amount_minor` | `amount_minor <= 0` |
| `dry_run` | `--dry-run` 成功预览 |

幂等：`replay: true` + 已有 `order` dict。

---

## 9. 测试覆盖（v0.1）

| 用例 | 说明 |
|------|------|
| ready keyword | `next_action` 含 `ready_for_order` |
| not ready | draft + assign implementer |
| invalid currency | 非 ISO 三字码 |
| amount_minor <= 0 | 金额校验 |
| normal create | 完整建档 |
| idempotent replay | 同 ticket 二次 create |
| JSONL round-trip | 落盘再加载 lookup |
| **integration** | 真实 ticket state fixture → create → JSONL → lookup（含 CLI subprocess） |

```bash
python -m unittest tests.test_order_ledger -v
python -m unittest tests.test_order_ledger_integration -v
```

---

## 10. v0.1 实装状态

**已交付（2026-06-13）**

| 能力 | 状态 |
|------|------|
| `TicketRecord` 解析 | 复用 `dispatch_executor.parse_ticket_state_markdown` |
| `ready_for_order` gate | keyword + `overall_status ∈ {review, done}` 备选 |
| `create_order_for_ticket` / `lookup_order` / `list_orders` | `04_Workflows/order_ledger/service.py` |
| JSONL 持久化 | `JsonlFileStore` → 默认 `artifacts/order_ledger/orders.jsonl` |
| CLI 默认 ticket path | 无 `--ticket-path` 时读 `04_Workflows/tickets/<ticket_id>_state.md` |
| 真实 ticket state → order 最小路径 | integration fixture `tests/fixtures/order_ledger/WC-T4-INT_state.md` + `tests/test_order_ledger_integration.py` |

**仍 deferred（不在 v0.1）**

| 项 | 说明 |
|----|------|
| Outbox / run_summary 联动 | W4-T3 deferred |
| REST API | CLI only |
| 支付 / Stripe / 真金流 | 另票 |
| Order 状态机（DRAFT→CONFIRMED→…） | WAVE8 / W4-T3 |
| `*_state.md` 回写 | ticket STATE 仍人工 / Orchestrator |
| milestone / billing_events | WAVE8 billing 数组 |
| SQLite store | 可选后续 |

---

## 11. 与 Wave 8 Order Model 关系

- 本票 `order_status=DRAFT` 对应 `WAVE8_CLEAN_ORDER_MODEL_v0.1` 草稿态
- `amount_minor` + `currency` 对齐 `WAVE8_CLEAN_BILLING_FIELDS_v0.1` 价格要素（整数 minor units 为 v0.1 简化）
- 完整 milestone / jobs 数组 **不在** v0.1 scope

---

*WC-T4 Order Ledger Intake · `docs/wave_c/WC_T4_order_ledger_design.md`*
