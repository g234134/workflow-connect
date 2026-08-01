# Wave Master Ticketing Playbook

> **编排 SSOT**：`04_Workflows/tickets/W-MASTER-wave-plan_state.md`  
> **战术线（P7/P8.5/P9）**：`04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md`  
> **角色边界**：`.cursor/rules/multi_chat_roles.mdc` · `docs/phase4-multi-agent-collaboration-contract-v1.md`  
> **Phase% SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md`（2026-06-23 基准）

---

## 1. 本輪規劃目標

**Wave Master Orchestrator** 已建立总控制平面；**本輪（Planner 阶段）** 的目标是：

1. **不施工功能** — 只产出 Wave 1–5 的 **planned ticket 清单**（ID + 目的 + 依赖 + blocked 标注）与子票 FRAME 草稿（可选另建 `*_state.md`）。
2. **补齐关键能力规划** — 对照 Dashboard 与 `W-MASTER` §Current Baseline，每 Wave **优先** blocking / cross-wave glue / 80% 边界缺口。
3. **不做微优化** — 不为 lint、rename、polish 开票；不重做 Phase ≥80% 且无关键缺口的 Phase。
4. **诚实标注 human/infra/security** — 不得把 ops/Infra/Security 前置包装成 AI 已完成。
5. **可并行** — Chat 1–5 各写各 Wave 區塊；Master Reviewer **最后**统一验收规划质量。

**本輪不做**：Wave 1–5 具体代码 diff · Phase% 上调 · required CI 升格 · prod/staging 执行。

---

## 2. 後續 Chat 1–5 如何讀取 State File

### 2.1 共通開讀順序（所有 Chat）

```
1. AGENTS.md §初始化校準（至少 1–4 步 + multi_chat_roles 若 Multi-Chat）
2. ENGINEERING_CONTRACT.md 或 .cursor/rules/engineering-contract.mdc（执行层）
3. docs/wave-master-ticketing-playbook.md（本檔）
4. 04_Workflows/tickets/W-MASTER-wave-plan_state.md（全文）
5. docs/WAVE_PROGRESS_DASHBOARD.md — 仅读己 Wave 相关 Phase 列 + §Wave-next 敘事
6. 04_Workflows/tickets/README.md — ticket state 机制
7. （可选）W-ORCH-wave-next-control-plane-v1 — 若己 Wave 涉 P7/P8.5/P9
```

### 2.2 各 Chat 專屬讀寫

| Chat | Wave | 必读 § | 唯一可写区 |
|------|------|--------|------------|
| **Chat 1** | Wave 1 · P7.5 / Intake | Baseline P7.5 · Cross-wave W1→W2 · Priority heuristic | `W-MASTER` → `## Wave 1 — Planned Tickets` |
| **Chat 2** | Wave 2 · P7 / Notify | Baseline P7 · human blocked 表 · matrix G-1–G-5 | `## Wave 2 — Planned Tickets` |
| **Chat 3** | Wave 3 · P8 / P8.9 | Baseline P8/P8.9 · >80% rule · W3→W4 依赖 | `## Wave 3 — Planned Tickets` |
| **Chat 4** | Wave 4 · P8.5 / P9 | Baseline P8.5/P9 · human GA/CI · W-ORCH P9/P85 lanes | `## Wave 4 — Planned Tickets` |
| **Chat 5** | Wave 5 · P10 / P10.5 | Baseline P10 · CI governance 批文 · rollup | `## Wave 5 — Planned Tickets` |

### 2.3 起手口令模板

```text
角色：Wave N Planner（Chat N）
Wave：WN
State SSOT：04_Workflows/tickets/W-MASTER-wave-plan_state.md
Playbook：docs/wave-master-ticketing-playbook.md
任务：只规划 ## Wave N — Planned Tickets；不施工；不修改其他 Wave 區塊
```

### 2.4 规划产出格式（写在 Wave N 區塊内）

每条 planned ticket **至少**一行表格式条目：

```markdown
| Ticket ID | 目的（一行） | lifecycle_phase | Phase | estimated_cycles | blocked / human |
|-----------|--------------|-----------------|-------|------------------|-----------------|
| W1-P75-GAP-xxx-v1 | … | B | P7.5 | 1 | 无 |
```

若需 FRAME 细节，复制 `_templates/ticket_state.template.md` 为 `04_Workflows/tickets/<id>_state.md`，并在 Wave N 區塊 **链接** 该路径 — **勿**在 Master 票重复全文。

---

## 3. Ticket 欄位填寫規範

### 3.1 标准 FRAME（来自 template）

| 欄位 | 要求 |
|------|------|
| **Goal** | 一句話 · 可验证 · 不含「提升 Phase%」 |
| **Scope** | MUST 条列 · 可在一个 Implementer 会话完成的主体 |
| **NonScope** | Explicit 不做 · 含 deferred 项 |
| **AllowedPaths** | repo 相对路径 · 对齐 `Master_Map.json` |
| **BlockedPaths** | 含 `.github/workflows` / `core` / env 若未授权 |
| **Dependencies** | 上游票 ID · human 前置 · **无则写「无」** |
| **relay_mode** | `same_chat` \| `multi_chat` · 见 `docs/ticket-schema-master-v1.md` FRAME 表 + skill「relay_mode」 |
| **AcceptanceCriteria** | 每条对应可执行验证或 honest blocked |

### 3.2 Wave Master 扩展（必填）

| 欄位 | 填写规则 |
|------|----------|
| **wave_id** | `W1`…`W5` · 与 Chat 一致 |
| **lifecycle_phase** | 开票时通常 `B`；施工票从 `B` 进入 |
| **phase_targets** | 只列 Dashboard Phase 名（如 `P7.5`）· **不写 %** |
| **estimated_cycles** | `1` 或 `2` · 超过必须拆票 |
| **mvp_allowed** | `true` 时 AC 须分 MVP vs stretch |
| **human_only_prereqs** | 列负责方 + 交付物（批文/run URL/sign-off）· 无则 `[]` |
| **infra_only_prereqs** | 例：staging slot · endpoint · allowlist |
| **security_only_prereqs** | 例：外部 POST 审查 |
| **non_claims** | 复制适用 global non-claims + 票专属 |

### 3.2.1 STATE：`awaiting_ops`／`ops_checklist`／`current_owner: ops`

> **字段权威**：`docs/ticket-schema-master-v1.md` STATE 节；本小节只写填写规范。

| 欄位 | 填写规则 |
|------|----------|
| **overall_status: awaiting_ops** | AI 段已验收、仅差 human／Ops（push、dispatch、贴 run_url）。**勿**当 `done`；**勿**重开 Implementer 做新功能 |
| **ops_checklist** | `awaiting_ops` 时条列可勾选项；否则写 `无`。勾完后再交棒 Scribe／关票 |
| **current_owner: ops** | 棒在 Ops／尚书省本人；与 `awaiting_ops` 常成对 |

**状态流（一句）**：`frame_ready` → `in_progress` → `review` →（仅差 ops）`awaiting_ops` → `scribe`／`done`｜`done_with_gaps`。

### 3.3 B/C/D/O 与 REPORT 对应

| 阶段 | state 区块 | 必填内容 |
|------|------------|----------|
| **B** Build spec | FRAME + STATE | AC · paths · `relay_mode` · 扩展栏齐全 |
| **C** Code/Config | B_REPORT | `changed_files` · `verification`（命令+结果） |
| **D** Debug/Verify | C_REPORT | `conclusion` · `checks_summary` 逐条 AC |
| **O** Observe/Trace | D_REPORT + STATE | Progress 建议 · `lifecycle_phase: O` · Orchestrator 关票；若仅差 ops 则先 `awaiting_ops` |

---

## 4. 依賴 / 風險 / Observability 欄位怎樣算合格

### 4.1 `dependencies_detail`

**合格示例**

```yaml
dependencies_detail:
  upstream_tickets:
    - P75-G4-intake-gate-notify-and-upstream-entry-v1_state.md  # notify 已落地
  downstream_waves:
    - W2  # P7 consume intake.gate_decision
  blocks_if_missing:
    - item: "P75-G2 outbox record path"
      owner: "Wave 1"
      if_missing: "defer W2 notify integration ticket"
```

**不合格**：「依赖 P7」无票号 · 「等 staging 好」无负责方 · 「无依赖」却需 human GA。

### 4.2 `risks`

每条 risk **must** 含：`id` · `description` · `likelihood` (L/M/H) · `impact` (L/M/H) · `mitigation` · `residual` (accept/block)。

**合格示例**

```yaml
risks:
  - id: RSK-W4-01
    description: Scenario2 GA 无 run URL 则 closure 票无法关
    likelihood: M
    impact: H
    mitigation: 仅开 evidence/runbook 票 · AC 要求 URL 占位符回填
    residual: block
```

**不合格**：「可能有风险」 · 无 mitigation · 把 human 风险标成 AI 可消。

### 4.3 `observability`

**合格标准**：Reviewer 不跑代码也能判断票是否完成。

```yaml
observability:
  verify_commands:
    - "python -m unittest tests.test_xxx -v"
    - "python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json"
  evidence_artifacts:
    - "outbox/verification/<case>/multi_phase_smoke_run.json"
    - "子票 B_REPORT verification 段"
  trace_fields:
    - "run_id"
    - "ga_run.url"           # 若涉 CI/GA
    - "notifications_failed_ack_count"
  success_signals:
    - "smoke ok=true 七步全绿"
    - "C_REPORT conclusion=accepted*"
  failure_signals:
    - "ok=false 任一步"
    - "blocked 无 next_action"
```

**P7.5 upstream example (Wave 1 · W1-P75-TRACE)**:

```yaml
observability:
  verify_commands:
    - "python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json"
    - "python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json"
    - "rg intake.gate_decision docs/p75-intake-gate-control-plane-trace-v1.md"
  evidence_artifacts:
    - "outbox/verification/demo_phase/multi_phase_smoke_run.json"
    - "docs/p75-intake-gate-control-plane-trace-v1.md"
  trace_fields:
    - "intake.gate_decision"
    - "decision"
    - "reason_codes"
    - "p75_policy_decision"
    - "multi_phase_smoke_run.steps[].ok"
    - "notifications_failed_ack_count"
  success_signals:
    - "MP-SMOKE steps gate_preview + gate_run_notify ok=true on demo_phase"
    - "metrics notifications_failed_ack_count=0 post-smoke"
  failure_signals:
    - "phi_demo smoke ok=true (deny should fail-closed)"
    - "doc claims G-1–G-5 runtime covered"
```

**不合格**：「测试通过」无命令 · 「CI 绿」无 run URL · 无 failure_signals。

### 4.4 `human_only` / `infra_only` / `security_only`

| 类型 | 必须写清 |
|------|----------|
| **human_only** | 谁 dispatch · 什么控制台 · 交付 run URL/批文 ID |
| **infra_only** | slot/endpoint/DNS · 环境名（逻辑名）· flip 授权 |
| **security_only** | 审查类型 · sign-off 记录位置 |

**禁止**：AC 写「staging 集成完成」而 prereqs 仍 open。

---

## 5. Reviewer 如何驗收整個 Wave 規劃

### 5.1 触发条件

- Chat 1–5 **全部**完成各自 `## Wave N — Planned Tickets`
- 或 Orchestrator 宣告「规划截止」进入 Master Plan Review

### 5.2 Reviewer 只读范围

- `W-MASTER-wave-plan_state.md` 全文
- 五 Wave 區塊 + 抽样 ≥2 个子票 FRAME（若有独立 `*_state.md`）
- `docs/WAVE_PROGRESS_DASHBOARD.md` 相关 Phase 列（对照 over-claim）
- `wave-next-code-inspector-v1.md` §Non-claims（若涉 P7/P8.5/P9）

### 5.3 Master Plan Review Checklist

| # | 检查项 | Blocking |
|---|--------|----------|
| 1 | 每 Wave ≥1 条 planned ticket 或 explicit「本 Wave 仅 blocked/解阻」说明 | Y |
| 2 | 所有 ticket ID 前缀与 Wave 一致 · 无跨 Wave ID 篡改 | Y |
| 3 | 每条 ticket `estimated_cycles` ≤2 或已拆票 | Y |
| 4 | Phase ≥80% 的票仅补 AC 缺口 · 无重开大工程 | Y |
| 5 | human/infra/security prereqs 完整 · 无伪完成 AC | Y |
| 6 | `dependencies_detail` / `risks` / `observability` 抽样合格（§4） | Y |
| 7 | 无 Phase% 上调 · 无 required CI 升格（无批文） | Y |
| 8 | Cross-wave 依赖与 `W-MASTER` §Cross-wave dependencies 一致 | N |
| 9 | 与 `W-ORCH` 战术线子票 STATE 无 hard conflict | Y |

### 5.4 Verdict 与写入

Reviewer 写 `W-MASTER-wave-plan_state.md` → **C_REPORT**：

```markdown
## Master Plan Review Verdict

- **reviewer_date**: YYYY-MM-DD
- **verdict**: PLAN_READY | PLAN_WITH_GAPS | PLAN_REJECT
- **waves_reviewed**: W1–W5
- **summary**: （2–4 句）
- **blocking_issues**: 无 | （列项）
- **over_claims_found**: 无 | （列项）
- **per_wave_notes**:
  - W1: …
  - …
- **next_action**: 开执行 Implementer chats | 退回 Planner 修订
```

Orchestrator 更新 STATE：`planning_status` · `reviewer_verdict` · `next_action`。

### 5.5 PLAN_REJECT 典型原因

- 把 human GA/CI 标成 Implementer AC 已完成
- Wave 2 在 Infra 未齐时开「staging execute 完成」票
- 单票覆盖整 Phase 重构
- 修改他 Wave 區塊或 ticket ID
- observability 全无 verify_commands

---

## 6. 与 Multi-Chat 四角色关系

| Wave Master 概念 | Multi-Chat 角色 |
|------------------|-----------------|
| 规划阶段 Chat N | Planner 兼任 **Orchestrator** 写 FRAME 草稿 |
| 执行阶段 B→C | **Implementer** |
| 执行阶段 D | **Reviewer** |
| 执行阶段 O | **Scribe** + **Orchestrator** 关票 |

规划阶段 **跳过** B_REPORT verification；执行阶段 **不得**跳过 C_REPORT。

---

## 7. 相关索引

| 类型 | 路径 |
|------|------|
| Master state | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` |
| Ticket README | `04_Workflows/tickets/README.md` |
| State 模板 | `04_Workflows/tickets/_templates/ticket_state.template.md` |
| **Wave Master schema SSOT（W5-T2）** | `docs/wave-master-ticket-template-v1.md` · `_templates/wave_master_frame_block.template.yaml` |
| **Multi-Chat commands SSOT（W5-T1）** | `.cursor/commands/README.md` |
| Wave-next playbook | `docs/wave-next-playbook.md` |
| Multi-Chat skill | `.cursor/skills/multi-chat-ticket-workflow/SKILL.md` |
| 80% 整合计划 | `04_Workflows/plans/multi-phase-80-percent-execution-plan.md` |
| Reviewer checklist | `04_Workflows/review_checklists/wave-next-code-inspector-v1.md` |

---

*版本：v1 · 2026-06-26 · Wave Master Orchestrator 首建 · 规划阶段 playbook*
