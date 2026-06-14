# WC-T5 · Control Plane Automation Coverage & Risk Boundary Contract

> **票号**：WC-T5  
> **版本**：v0.1 · 2026-06-13  
> **SSOT**：`04_Workflows/tickets/WC-T5_state.md` FRAME  
> **契约测试**：`tests/test_wc_t5_automation_coverage_contract_v1.py`

---

## 1. 目的

为 Wave C M2 Control Plane 链（eligibility → dispatch cards → comms → order intake）建立**可机器引用的自动化覆盖率与风险边界契约**：

- 每条路径标注 `automation_tier`：`auto` · `HITL` · `forbidden`
- 每条路径标注 `risk_class`：`low` · `medium` · `high`
- 每条 `auto` 路径绑定可重跑 `verification_command`
- **默认语义**：optional · non-blocking · investigation-only

与 Tabular MVP S1–S15 全链（`ninety-five-percent-automation-blueprint-v2.md`）**分轨**；本契约仅覆盖 Control Plane CLI。

---

## 2. 默认只读与写入边界

| 组件 | 默认行为 | 写 STATE |
|------|----------|----------|
| `run_ticket_eligibility.py` | 只读 `*_state.md` | **禁止** |
| `run_dispatch_cards.py` | 只读 FRAME/STATE；写 `artifacts/control_plane/cards/` | **禁止** 写 `*_state.md` |
| `run_ticket_state_update_with_comms.py` | 读 before/after 快照；写 comms JSONL | **禁止** 写 live `*_state.md` |
| `run_order_intake.py` | 只读 ticket state；写 order JSONL | **禁止** 写 `*_state.md` |

任何**写 live `04_Workflows/tickets/*_state.md` STATE 区块**的路径必须标 `forbidden` 或 `HITL-only`（Orchestrator 人工编辑）。

---

## 3. 禁止假设（必读）

本契约**不得**被解读为：

- PR required / prod blocking CI gate 授权
- prod SLA 或自动关票授权
- 可绕过 Reviewer / Scribe 的 silent automation 许可
- INT Tier-A regression 的替代验收

治理升格（WC-PRE-06/07 L2）须尚書省 `approval_status=approved` 后另票；本契约不改变现有 gate pass/fail。

---

## 4. 路径矩阵

| path_id | 描述 | automation_tier | risk_class | cli_entry | verification_command |
|---------|------|-----------------|------------|-----------|------------------------|
| `wc.m2.eligibility.check` | 检查票是否可接单（无角色上下文） | auto | low | `scripts/run_ticket_eligibility.py` | `python scripts/run_ticket_eligibility.py --ticket W1-T2 --format json` |
| `wc.m2.eligibility.check_role` | 带 `requested_role` 的 eligibility 检查 | auto | low | `scripts/run_ticket_eligibility.py` | `python scripts/run_ticket_eligibility.py --ticket W1-T2 --requested-role reviewer --format json` |
| `wc.m2.eligibility.serve` | 启动最小 REST eligibility 服务（本地 dev） | HITL | medium | `scripts/run_ticket_eligibility.py` | `python scripts/run_ticket_eligibility.py --serve 8765`（人工启动/停止） |
| `wc.m2.dispatch.cards_generate` | 从 dispatch plan 生成指令卡（默认 eligibility block） | auto | low | `scripts/run_dispatch_cards.py` | `python scripts/run_dispatch_cards.py --limit 3 --pretty` |
| `wc.m2.dispatch.refresh_and_cards` | 刷新 plan 后生成卡 | auto | medium | `scripts/run_dispatch_cards.py` | `python scripts/run_dispatch_cards.py --refresh-plan --dry-run --pretty` |
| `wc.m2.dispatch.eligibility_gate_warn` | eligibility gate warn 模式（仍写卡） | auto | low | `scripts/run_dispatch_cards.py` | `python scripts/run_dispatch_cards.py --eligibility-gate warn --dry-run --pretty` |
| `wc.m2.dispatch.force_eligibility_override` | Orchestrator 强制 override ineligible 票写卡 | HITL | medium | `scripts/run_dispatch_cards.py` | `python scripts/run_dispatch_cards.py --force-eligibility --dry-run --pretty` |
| `wc.m2.comms.state_transition` | before/after STATE 快照 → comms JSONL | auto | low | `scripts/run_ticket_state_update_with_comms.py` | `python scripts/run_ticket_state_update_with_comms.py --before tests/fixtures/ticket_comms/wc_t2_before_state.md --after tests/fixtures/ticket_comms/wc_t2_after_state.md` |
| `wc.m2.comms.state_transition_dry_run` | comms dry-run（不写 outbox） | auto | low | `scripts/run_ticket_state_update_with_comms.py` | `python scripts/run_ticket_state_update_with_comms.py --before tests/fixtures/ticket_comms/wc_t2_before_state.md --after tests/fixtures/ticket_comms/wc_t2_after_state.md --dry-run` |
| `wc.m2.order.create` | 为 ticket 创建 order 记录（dry-run 默认隔离） | auto | medium | `scripts/run_order_intake.py` | `python scripts/run_order_intake.py create --ticket WC-T4-INT --amount-minor 10000 --currency TWD --ticket-path tests/fixtures/order_ledger/WC-T4-INT_state.md --dry-run` |
| `wc.m2.order.lookup` | 按 order_id 或 ticket_id 查询 order | auto | low | `scripts/run_order_intake.py` | `python scripts/run_order_intake.py lookup --ticket-id WC-T4-INT --jsonl-path artifacts/order_ledger/orders.jsonl` |
| `wc.m2.order.list` | 列出 ledger 中全部 order | auto | low | `scripts/run_order_intake.py` | `python scripts/run_order_intake.py list --jsonl-path artifacts/order_ledger/orders.jsonl` |
| `wc.m2.loop.order_handoff` | eligibility + dispatch context + order + order comms 单票闭环 | auto | medium | `scripts/run_control_plane_order_handoff.py` | `python scripts/run_control_plane_order_handoff.py --ticket WC-T4 --amount-minor 10000 --currency TWD --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md --dry-run` |
| `wc.m2.comms.order_event` | order intake 结果 → comms JSONL（created/replay/rejected） | auto | low | `scripts/run_control_plane_order_handoff.py` | `python -m unittest tests.test_control_plane_order_handoff.TestOrderCommsPayload -v` |
| `wc.m2.state.write_ticket` | 自动写 live `*_state.md` STATE 区块 | forbidden | high | — | —（禁止自动化；仅 Orchestrator HITL 手工编辑） |
| `wc.m2.chat.open_cursor` | 调用 Cursor API 自动开 chat | forbidden | high | — | —（禁止；Multi-Chat 仍人工开 chat） |

---

## 5. 交叉引用

| 文档 | 用途 |
|------|------|
| `docs/wave_c/WC_T1_eligibility.md` | eligibility 判定规则 SSOT |
| `docs/wave_c/WC_T2_comms_minimal.md` | comms payload schema |
| `docs/wave_c/WC_T4_order_ledger_design.md` | order intake v0.1 |
| `docs/wave_c/overview.md` §M2 End-to-End | 手工 E2E walkthrough |
| `docs/phase4-multi-agent-collaboration-contract-v1.md` | 四角色写入冻结 |
| `.cursor/rules/multi_chat_roles.mdc` | Multi-Chat 角色边界 |

---

## 6. 验收命令（契约级）

```bash
python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v
python -m unittest tests.test_ticket_eligibility tests.test_dispatch_cards tests.test_ticket_comms tests.test_order_ledger -v
```

---

## 附录 A · 机器可读路径注册表（`wc_t5_paths_v0.1`）

```json
{
  "schema_version": "wc_t5_paths_v0.1",
  "paths": [
    {
      "path_id": "wc.m2.eligibility.check",
      "description": "Check ticket eligibility without role context",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_ticket_eligibility.py",
      "verification_command": "python scripts/run_ticket_eligibility.py --ticket W1-T2 --format json"
    },
    {
      "path_id": "wc.m2.eligibility.check_role",
      "description": "Check ticket eligibility with requested_role",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_ticket_eligibility.py",
      "verification_command": "python scripts/run_ticket_eligibility.py --ticket W1-T2 --requested-role reviewer --format json"
    },
    {
      "path_id": "wc.m2.eligibility.serve",
      "description": "Start minimal REST eligibility server (local dev)",
      "automation_tier": "HITL",
      "risk_class": "medium",
      "cli_entry": "scripts/run_ticket_eligibility.py",
      "verification_command": "python scripts/run_ticket_eligibility.py --serve 8765"
    },
    {
      "path_id": "wc.m2.dispatch.cards_generate",
      "description": "Generate dispatch instruction cards from plan",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_dispatch_cards.py",
      "verification_command": "python scripts/run_dispatch_cards.py --limit 3 --pretty"
    },
    {
      "path_id": "wc.m2.dispatch.refresh_and_cards",
      "description": "Refresh dispatch plan then generate cards",
      "automation_tier": "auto",
      "risk_class": "medium",
      "cli_entry": "scripts/run_dispatch_cards.py",
      "verification_command": "python scripts/run_dispatch_cards.py --refresh-plan --dry-run --pretty"
    },
    {
      "path_id": "wc.m2.dispatch.eligibility_gate_warn",
      "description": "Generate cards with eligibility gate warn mode",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_dispatch_cards.py",
      "verification_command": "python scripts/run_dispatch_cards.py --eligibility-gate warn --dry-run --pretty"
    },
    {
      "path_id": "wc.m2.dispatch.force_eligibility_override",
      "description": "Orchestrator force override for ineligible tickets",
      "automation_tier": "HITL",
      "risk_class": "medium",
      "cli_entry": "scripts/run_dispatch_cards.py",
      "verification_command": "python scripts/run_dispatch_cards.py --force-eligibility --dry-run --pretty"
    },
    {
      "path_id": "wc.m2.comms.state_transition",
      "description": "Emit comms JSONL for STATE transition snapshots",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_ticket_state_update_with_comms.py",
      "verification_command": "python scripts/run_ticket_state_update_with_comms.py --before tests/fixtures/ticket_comms/wc_t2_before_state.md --after tests/fixtures/ticket_comms/wc_t2_after_state.md"
    },
    {
      "path_id": "wc.m2.comms.state_transition_dry_run",
      "description": "Dry-run comms emission without writing outbox",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_ticket_state_update_with_comms.py",
      "verification_command": "python scripts/run_ticket_state_update_with_comms.py --before tests/fixtures/ticket_comms/wc_t2_before_state.md --after tests/fixtures/ticket_comms/wc_t2_after_state.md --dry-run"
    },
    {
      "path_id": "wc.m2.order.create",
      "description": "Create order record for ticket (dry-run for isolation)",
      "automation_tier": "auto",
      "risk_class": "medium",
      "cli_entry": "scripts/run_order_intake.py",
      "verification_command": "python scripts/run_order_intake.py create --ticket WC-T4-INT --amount-minor 10000 --currency TWD --ticket-path tests/fixtures/order_ledger/WC-T4-INT_state.md --dry-run"
    },
    {
      "path_id": "wc.m2.order.lookup",
      "description": "Lookup order by order_id or ticket_id",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_order_intake.py",
      "verification_command": "python scripts/run_order_intake.py lookup --ticket-id WC-T4-INT --jsonl-path artifacts/order_ledger/orders.jsonl"
    },
    {
      "path_id": "wc.m2.order.list",
      "description": "List all orders in JSONL ledger",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_order_intake.py",
      "verification_command": "python scripts/run_order_intake.py list --jsonl-path artifacts/order_ledger/orders.jsonl"
    },
    {
      "path_id": "wc.m2.loop.order_handoff",
      "description": "Single-ticket handoff: eligibility + dispatch context + order + comms",
      "automation_tier": "auto",
      "risk_class": "medium",
      "cli_entry": "scripts/run_control_plane_order_handoff.py",
      "verification_command": "python scripts/run_control_plane_order_handoff.py --ticket WC-T4 --amount-minor 10000 --currency TWD --ticket-path tests/fixtures/order_ledger/ticket_ready_for_order.md --dry-run"
    },
    {
      "path_id": "wc.m2.comms.order_event",
      "description": "Emit comms JSONL for order intake outcomes",
      "automation_tier": "auto",
      "risk_class": "low",
      "cli_entry": "scripts/run_control_plane_order_handoff.py",
      "verification_command": "python -m unittest tests.test_control_plane_order_handoff.TestOrderCommsPayload -v"
    },
    {
      "path_id": "wc.m2.state.write_ticket",
      "description": "Automated write to live ticket STATE block",
      "automation_tier": "forbidden",
      "risk_class": "high",
      "cli_entry": null,
      "verification_command": null
    },
    {
      "path_id": "wc.m2.chat.open_cursor",
      "description": "Call Cursor API to auto-open chat",
      "automation_tier": "forbidden",
      "risk_class": "high",
      "cli_entry": null,
      "verification_command": null
    }
  ]
}
```
