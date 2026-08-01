# Wave-next Multi-Chat Playbook

> **编排 SSOT**：`04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md`  
> **Reviewer checklist**：`04_Workflows/review_checklists/wave-next-code-inspector-v1.md`  
> **角色边界**：`.cursor/rules/multi_chat_roles.mdc`

---

## 概要

**Wave-next** = **control plane**（单票编排入口）+ **多 lanes 并行**（P7 / P8.5 / P9 等功能或 doc 线）+ **Reviewer 收口**（只读对照 checklist · 产出 verdict）。Orchestrator 在 control plane 票维护 lane 分派表与 non-claims；各 chat 读子票 FRAME 施工；**Reviewer 必须最后** — 读三 lane / Scribe 产出后给全局 verdict。**不宣稱 prod / GA / INT / required CI** 除非有 run URL + 子票证据。

---

## Commands 流程

在 Cursor 中可用 **slash commands**（或等价的 chat 起手模板）驱动 Wave-next 节奏：

1. **`/orchestrate-wave-next`** — 建/更新 control plane 与 lanes  
   - 读 `W-ORCH-wave-next-control-plane-v1_state.md` · `multi_chat_roles.mdc` · alignment checklist  
   - 产出/更新 lane 分派表 · non-claims · traversal 顺序  
   - **模型建议**：**Composer 2.5 Fast**

2. **`/implement-lane`** — 单一 lane 施工 / 收口  
   - 读 control plane B_REPORT 指定 lane 与子票 `*_state.md` FRAME  
   - 在 AllowedPaths 内施工（Implementer）或 doc 落档（Scribe lanes）  
   - **模型建议**：**Composer 2.5 Fast**

3. **`/review-wave-next`** — Reviewer 审查给 verdict  
   - 只读：子票 STATE/B_REPORT · Progress 末尾 · workflow yml · 新落档 runbook/playbook  
   - 写：C_REPORT / control plane 第三輪 verdict 段（**不改** FRAME/B_REPORT/overall_status）  
   - **模型建议**：**Kimi K2.5**（reasoning-first · 对照 SSOT）

**推荐 traversal**：

```
/orchestrate-wave-next  →  并行 /implement-lane（各 lane）  →  /review-wave-next（最后）
```

---

## 模型配置建议

| 角色 / command | 模型 | 说明 |
|----------------|------|------|
| Orchestrator · `/orchestrate-wave-next` | **Composer 2.5 Fast** | 编排骨架 · lane 表 · 索引更新 |
| Implementer / Scribe · `/implement-lane` | **Composer 2.5 Fast** | yml/索引/文档/doc 收口 · 快迭代 |
| Reviewer · `/review-wave-next` | **Kimi K2.5** | 只读 traversal · over-claim 拦截 · verdict |

**Wave-next Multi-Chat Workflow — 快速上手**：

- 开 **Orchestrator chat** → 贴 `/orchestrate-wave-next` 或 Orchestrator 角色 prompt → 确认 lane 与子票 path。  
- 对各 lane 开 **独立 chat** → `/implement-lane` + 子票号（例：`WH-P85-SMOKE-B-scenario2-ops-run-v1`）。  
- **human/ops** 项（P8.5 GA · P9 CI 首跑）依 `docs/internal/*_runbook.md` 手动 dispatch，**禁止 agent 伪造 run URL**。  
- 三 lane / Scribe 完成后开 **Reviewer chat** → `/review-wave-next` → 对照 `wave-next-code-inspector-v1.md` 填 verdict。  
- Scribe 只改 docs/Progress **末尾** · **不调 Phase% · 不改子票 overall_status**（除非 Orchestrator 授权）。

---

## 使用范例

| Lane | 映射 | 典型子票 / 产出 |
|------|------|-----------------|
| **P7** | staging Round-2 · bootstrap | `WH-P7-NOTIF-staging-integration-execute-v2`（**blocked**）· Round-1 local slot 已 validated |
| **P8.5** | Scenario2 GA · closure | `WH-P85-SMOKE-B-scenario2-ops-run-v1` · human runbook → `docs/internal/P85_Scenario2_GA_runbook.md` |
| **P9** | advisory payment CI | `WH-P9-CI-payment-sandbox-smoke-v1` · human runbook → `docs/internal/P9_payment_sandbox_CI_runbook.md` |
| **doc/SOP** | 一次性 Scribe | Dashboard 敘事 · playbook · internal runbooks · **无 Phase% 变更** |

**并行规则**：closure-scribe · dashboard-scribe · commands-builder 可并行；**code-inspector / Reviewer 必须最后**。

---

## 相关索引

| 类型 | 路径 |
|------|------|
| Control plane | `04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md` |
| Multi-Chat skill | `.cursor/skills/multi-chat-ticket-workflow/SKILL.md` |
| P85 human runbook | `docs/internal/P85_Scenario2_GA_runbook.md` |
| P9 human runbook | `docs/internal/P9_payment_sandbox_CI_runbook.md` |
| Phase% SSOT | `docs/WAVE_PROGRESS_DASHBOARD.md`（**06-23 基准 · Scribe 不重算**） |

---

*版本：v1 · 2026-06-25 · Wave-next doc/SOP Scribe 落档*
