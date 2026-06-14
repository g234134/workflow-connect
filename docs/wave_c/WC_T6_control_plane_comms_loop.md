# WC-T6 · Control Plane Comms Loop (dispatch / order / ticket)

> **票号**：WC-T6（Lane C · 接单→开单→回报闭环轨）  
> **实现**：`04_Workflows/control_plane_loop/` · `04_Workflows/ticket_comms/order_events.py`  
> **CLI**：`scripts/run_control_plane_order_handoff.py`  
> **契约**：`docs/wave_c/WC_T5_automation_coverage_contract.md`（`wc.m2.loop.order_handoff` · `wc.m2.comms.order_event`）

> **命名说明**：repo 内另有 **WC-T6 skill distillation**（`WC_T6_skill_distillation_lite.md`）。本档为 **comms 闭环轨**，票号复用 WC-T6 子能力，不合并 skill distillation 实现。

---

## 1. 目的

在 WC-T1/T2/T3/T4 已交付的 Control Plane 模块之上，补齐 **单票最小商业 handoff 闭环**：

```
eligibility 检查 → dispatch 上下文（bucket/role）→ order intake → order-event comms JSONL
```

**提升**：Orchestrator 开单后自动写入结构化回报（comms outbox），无需手工拼装 order 摘要。

**不做**：支付网关、完整 Order 状态机、自动写 live `*_state.md`、REST 对外 API（属 WC-T7 外部 intake 轨）。

---

## 2. 模块布局

| 模块 | 路径 | 职责 |
|------|------|------|
| Handoff 编排 | `control_plane_loop/handoff.py` | `execute_order_handoff()` |
| Order comms | `ticket_comms/order_events.py` | `build_order_comms_payload()` · `emit_order_comms()` |
| CLI | `scripts/run_control_plane_order_handoff.py` | 本地验收入口 |

---

## 3. 返回形状（handoff）

```python
{
    "ok": True,
    "message": "order_handoff_complete",
    "ticket_id": "WC-T4",
    "dry_run": False,
    "eligibility": { "eligible": "eligible", ... },
    "dispatch_context": {
        "bucket": "runnable_now",
        "recommended_role": "orchestrator",
        "reason": "...",
    },
    "order": { "ok": True, "message": "order_created", "order": { ... } },
    "comms": {
        "event_type": "order_created",
        "sent": True,
        "payload": { ... },
        "send_result": { "artifact_path": "artifacts/ticket_comms/ticket_comms.jsonl" }
    }
}
```

### 3.1 Order comms `event_type`

| event_type | 条件 |
|------------|------|
| `order_created` | 首次建档成功 |
| `order_replay` | 同 ticket 幂等 replay |
| `order_rejected` | gate 未通过或校验失败 |
| `order_dry_run` | `--dry-run` 预览 |

Payload 沿用 `ticket_comms_v0.1` schema，新增可选字段：`event_type` · `order` · `order_result` · `gate`。

---

## 4. CLI 用法

```bash
# 完整闭环（fixture ticket，隔离 ledger/comms 建议用 --jsonl-path / --comms-outbox）
python scripts/run_control_plane_order_handoff.py \
  --ticket WC-T4 \
  --amount-minor 10000 \
  --currency TWD \
  --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md

# 预览（不写 ledger / comms）
python scripts/run_control_plane_order_handoff.py \
  --ticket WC-T4 --amount-minor 10000 --currency TWD \
  --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md \
  --dry-run

# gate 未过但需验证拒绝回报（Orchestrator override）
python scripts/run_control_plane_order_handoff.py \
  --ticket WC-T4 --amount-minor 5000 --currency TWD \
  --ticket-path tests/fixtures/order_ledger/ticket_not_ready.md \
  --skip-eligibility
```

---

## 5. 门禁与边界

| 项 | 行为 |
|----|------|
| Eligibility | 默认 `ineligible` 时 **阻断** handoff；`--skip-eligibility` 为 HITL override |
| `ready_for_order` gate | 仍由 `order_ledger.gates` 判定；与 eligibility **独立** |
| 写 STATE | **禁止** |
| 支付 | **禁止** |
| Comms 通道 | 默认 `FileLogSender` → `ticket_comms.jsonl` |

---

## 6. 测试

```bash
python -m unittest tests.test_control_plane_order_handoff -v
python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v
```

| 用例 | 说明 |
|------|------|
| full loop | ready ticket → order + comms JSONL |
| ineligible block | not-ready + implementer → 阻断 |
| skip + reject | not-ready + override → order_rejected comms |
| dry_run | 无 ledger 写盘 |
| replay | 二次 handoff → order_replay comms |

---

## 7. Deferred（v0.1 之后）

| 项 | 说明 |
|----|------|
| dispatch plan 快照写入 handoff 结果 | 仅内联 bucket/role，未附 plan JSON |
| STATE 变更 + order 事件合并 outbox | 仍分 `run_ticket_state_update_with_comms` 与 order handoff |
| Webhook / email sender | 扩展 `CommsSender` 协议 |
| 与 WC-T7 external intake API 对接 | 见 `WC_T7_external_intake_boundary.md`（规划） |

---

*WC-T6 Control Plane Comms Loop · `docs/wave_c/WC_T6_control_plane_comms_loop.md`*
