# Ticket Schema Master v1

> **SSOT 票**：`W5-T2-wave-master-ticket-template-v1` · **Full-Phase 扩展**：`W-MASTER-full-phase-plan_state.md` §Shared Ticket Schema  
> **Machine template**：`04_Workflows/tickets/_templates/ticket_state.template.md` · `wave_master_frame_block.template.yaml`  
> **Commands 消费**：`.cursor/commands/ticket-*.md` · `wave-master-*.md`  
> **Playbook 细则**：`docs/wave-master-ticketing-playbook.md` §3 · `docs/full-phase-master-planning-playbook.md` §4

---

## 用途

本文件为 **唯一 ticket 字段主版本**。Wave Master · Full-Phase · Multi-Chat 四角色 **must** 使用下列栏位名与语义 — **禁止**平行 schema 或自造别名。

| 文档 | 角色 |
|------|------|
| **本文件** | 字段名 · 枚举 · 必填规则 · B/C/D/O 映射 |
| `docs/wave-master-ticket-template-v1.md` | Wave 5 索引 · 消费路径 |
| `04_Workflows/tickets/_templates/*` | 机器复制模板 |

---

## FRAME 标准栏（所有票）

| 栏位 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **Goal** | string | yes | 一句话 · 可验证 · **不含**「提升 Phase%」 |
| **Scope** | string[] | yes | MUST 条列 |
| **NonScope** | string[] | yes | 明确不做 · deferred |
| **AllowedPaths** | string[] | yes | repo 相对路径 |
| **BlockedPaths** | string[] | yes | 宪章 §7 类型引用 |
| **Dependencies** | string[] | yes | 票 ID / human 前置；无则 `无` |
| **relay_mode** | `same_chat`\|`multi_chat` | yes（Multi-Chat／Wave 子票） | 同轮快车 vs 真分 Chat；语义见 `.cursor/skills/multi-chat-ticket-workflow/SKILL.md`「relay_mode」（不复制全文） |
| **AcceptanceCriteria** | string[] | yes | 可执行判定或 honest blocked |

**`relay_mode` 语义（摘要）**：`same_chat` = 同一对话内 O→B→C→D；`multi_chat` = 分 chat 交棒，以本票 `*_state.md` 为 SSOT。禁止自造别名（如 `single_chat`／`parallel`）。

---

## FRAME 扩展栏（Wave Master + Full-Phase）

| 栏位 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **wave_id** | `W1`\|`W2`\|`W3`\|`W4`\|`W5`\|`null` | Wave 子票 yes | P7+ 执行票；Foundation 票 `null` |
| **group_id** | `G1`…`G10` | Full-Phase yes | 10-Group 任务盘；Wave-only 票可省略 |
| **lifecycle_phase** | `B`\|`C`\|`D`\|`O` | yes | 与 B/C/D/O 施工阶段对齐 |
| **phase_targets** | string[] | yes | 只列 Dashboard Phase 名（如 `P7.5`）· **不写 %** |
| **estimated_cycles** | `1`\|`2` | Wave 子票 yes | 超过须拆票 |
| **mvp_allowed** | bool | Wave 子票 yes | `true` 时 AC 分 MVP vs stretch |
| **human_only_prereqs** | string[] | yes | 无则 `[]` |
| **infra_only_prereqs** | string[] | yes | 无则 `[]` |
| **security_only_prereqs** | string[] | yes | 无则 `[]` |
| **dependencies_detail** | object | Wave 子票 yes | 见 §dependencies_detail |
| **risks** | object[] | Wave 子票 yes | id · description · likelihood · impact · mitigation · residual |
| **observability** | object | Wave 子票 yes | 见 §observability |
| **non_claims** | string[] | yes | global + 票专属 |
| **ticket_class** | enum | Full-Phase yes | 见 §ticket_class |
| **evidence_tier** | enum | Full-Phase yes | 见 `docs/evidence-tier-contract-v1.md` |
| **parallel_ok** | bool | Full-Phase yes | 对照 Parallelization Plan |

---

## dependencies_detail

```yaml
dependencies_detail:
  upstream_tickets: []      # *_state.md 或票 ID
  downstream_waves: []      # W1–W5（Wave Master）
  downstream_groups: []     # G1–G10（Full-Phase）
  blocks_if_missing: []     # item · owner · if_missing
```

---

## observability

```yaml
observability:
  verify_commands: []       # Reviewer 可重跑 · **Wave 子票必填**
  evidence_artifacts: []    # 逻辑路径 / B_REPORT 指针
  trace_fields: []          # 须引用 trace SSOT 字段名（如 intake_decision_id · case_ref）
  success_signals: []
  failure_signals: []
```

**P7.5 upstream trace**：`trace_fields` 必须来自 `docs/p75-intake-gate-control-plane-trace-v1.md` §A–D。

---

## ticket_class

| Class | 含义 | 可直接 B/C/D/O |
|-------|------|----------------|
| **build** | 代码/配置/测试 | 是（FRAME 冻结后） |
| **doc/spec** | 文档/契约/索引 | 是（C=doc diff） |
| **scribe/ops** | Progress/closure · GA 回填 | **O 重** · 常 human-only |
| **blocked/planning** | 值得规划但 AC honest blocked | **B only** |

---

## evidence_tier

**权威定义**：`docs/evidence-tier-contract-v1.md` · `docs/p8_p89_evidence_index_v1.md` §1。

| 合法值 | 说明 |
|--------|------|
| **L-local** | 本机 unittest / CLI smoke |
| **CI-advisory** | Advisory workflow landing 或 completed run（仍 non-gate） |
| **GA-remote** | 远端 completed run + **run_url** + **run_id** |
| **n/a** | 纯规划/doc · 无 runtime 证据 |

**禁止别名**：`L-GA-remote` · `M` · `H` · 自创第四 tier 名。`prod` **不是** evidence tier — 用 `non_claims` 表述 prod gap。

---

## STATE 建议栏

```yaml
overall_status: draft|frame_ready|in_progress|review|scribe|awaiting_ops|done|blocked|done_with_gaps
lifecycle_phase: B|C|D|O
current_owner: orchestrator|implementer|reviewer|scribe|ops
next_action: ""
last_updated: YYYY-MM-DD
ops_checklist: 无 | # awaiting_ops 时条列 human／ops；否则写「无」
  - [ ] commit／push
  - [ ] workflow_dispatch → 贴 run_url
status_by_role:
  orchestrator: pending|done|n/a
  implementer: pending|in_progress|done|n/a
  reviewer: pending|in_progress|done|n/a
  scribe: pending|in_progress|done|n/a
```

| 栏位／枚举 | 说明 |
|------------|------|
| **`awaiting_ops`**（`overall_status`） | AI 施工段结束；等人 commit／push／dispatch／贴 URL。**不是** `done`，也**不是**重开完整 O→B→C。细则见 skill「awaiting_ops」。 |
| **`ops_checklist`** | `awaiting_ops` 时必填勾选清单；否则 `无`。禁止未勾完标 Phase closure。 |
| **`current_owner: ops`** | 棒在 human／Ops（非四角色 AI）；与 `awaiting_ops` 常成对出现。 |

**状态流（一句）**：`frame_ready` → `in_progress` → `review` →（仅差 human ops 时）`awaiting_ops` → `scribe`／`done`｜`done_with_gaps`；或 `blocked`。

---

## B / C / D / O REPORT 区块

| 阶段 | 区块 | Implementer / Reviewer / Scribe |
|------|------|--------------------------------|
| **B** | FRAME + STATE | Orchestrator 冻结 |
| **C** | B_REPORT | Implementer：`changed_files` · `verification`（可重跑） |
| **D** | C_REPORT | Reviewer：`conclusion` · `checks_summary` 逐条 AC |
| **O** | D_REPORT + STATE | Scribe：Progress append 建议 · Orchestrator 关票 |

---

## B/C/D/O 落实在 commands 中的映射

| Command | 角色 | lifecycle_phase | 可写区块 |
|---------|------|-----------------|----------|
| `/ticket-orchestrator` | Orchestrator | B→交棒 | FRAME · STATE |
| `/ticket-implementer` | Implementer | C | B_REPORT · AllowedPaths |
| `/ticket-reviewer` | Reviewer | D | C_REPORT |
| `/ticket-scribe` | Scribe | O | D_REPORT |
| `/wave-master-orchestrator` | Master Orch | B | W-MASTER STATE |
| `/wave-master-planner` | Wave Planner | B | Wave N planned tickets |
| `/wave-master-implementer` | Wave Implementer | C | 子票 B_REPORT（消费本 schema） |

---

## 消费规则

1. **新开票**：复制 `ticket_state.template.md` → 填 FRAME + 扩展栏 → 字段名 **must** 与本文件一致。
2. **Wave 1–4**：只消费 · **不维护** 本 schema 主版本（Wave 5 SSOT）。
3. **Full-Phase FP-* 票**：必须含 `group_id` + `ticket_class` + `evidence_tier`。
4. **禁止**在 commands / instruction 中发明未列栏位（如 `lane_id` 作 FRAME 必填 — 用 `group_id` + playbook lane map）。

---

## Non-Goals

- 不覆盖 `multi_chat_roles.mdc` 角色边界
- 不替代 Master Reviewer checklist（W5-T4）
- 不宣稱 schema 已覆盖所有 future ticket 类型

---

## Changelog

| 日期 | 变更 |
|------|------|
| 2026-07-12 | W5-T6：FRAME 正式纳入 `relay_mode`；STATE 纳入 `awaiting_ops`／`ops_checklist`／`current_owner` 含 `ops`；与 `_templates/ticket_state.template.md` 对齐。**non_claims**：≠ Phase%／Round-2 GO／历史票已回填 |
| 2026-06-26 | v1 · Lane A G4：合并 W5-T2 + Full-Phase Shared Schema + evidence_tier 对齐 |

---

## Sub-block readiness（Lane A · 2026-06-26）

| 子区块 | 状态 |
|--------|------|
| **Ticket schema + commands 对齐** | **`ready`** (~98%) — 本文件 + template + `.cursor/commands` 字段一致；Wave 1 只消费 |

---

*Ticket Schema Master v1 · W5-T2 + Full-Phase · 2026-06-26*
