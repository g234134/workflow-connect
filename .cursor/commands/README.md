# Multi-Chat Ticket Commands — SSOT Index

> **Authority ticket**：`W5-T1-multi-chat-commands-v1`  
> **Schema SSOT**：`docs/ticket-schema-master-v1.md`（主版本）· `docs/wave-master-ticket-template-v1.md`（Wave 5 索引）  
> **Evidence tier**：`docs/evidence-tier-contract-v1.md` · FRAME.`evidence_tier`  
> **Role boundaries**：`.cursor/rules/multi_chat_roles.mdc`  
> **Workflow skill**：`.cursor/skills/multi-chat-ticket-workflow/SKILL.md`

在 Cursor Agent chat 输入 `/` 选择下列命令。命令名 = 文件名（不含 `.md`）。

## Multi-Chat 四角色（票级 B→C→D→O）

| Command | 角色 | 用途 |
|---------|------|------|
| `/ticket-orchestrator` | Orchestrator (O) | 开票 · 冻结 FRAME/STATE · 交棒 |
| `/ticket-implementer` | Implementer (B) | 依 FRAME 施工 · 写 B_REPORT |
| `/ticket-reviewer` | Reviewer (C) | 唯读审查 · 写 C_REPORT |
| `/ticket-scribe` | Scribe (D) | 文档/Progress · 写 D_REPORT |

## Wave Master 编排（Master CP）

| Command | 角色 | 用途 |
|---------|------|------|
| `/wave-master-orchestrator` | Master Orchestrator | 维护 W-MASTER · 开 Chat 1–5 · 关票 |
| `/wave-master-planner` | Wave N Planner | 只写 `## Wave N — Planned Tickets` |
| `/wave-master-implementer` | Wave N Implementer | Wave 执行子票施工（消费 W5-T2 schema） |

## 起手参数（所有 ticket 命令）

用户应在命令后补充：

```
ticket_id: <TICKET-ID>
state 路径: 04_Workflows/tickets/<TICKET-ID>_state.md
本轮回任务: <一句话>
```

## 不覆盖

- 不取代 `AGENTS.md` 接战/封存
- 不宣稱 commands 已覆盖所有 future cases
- Wave-next 战术线另用 `docs/wave-next-playbook.md` 的 `/orchestrate-wave-next` 等（待 W-ORCH commands-builder 对齐）

*W5-T1 MVP · 2026-06-26*
