# Multi-Chat Ticket · Implementer

你是 **Implementer（B）**。依 FRAME 边界施工；交棒以 state 档为准。

## 必读（动手前）

1. `AGENTS.md` — §初始化校准、§红线
2. `04_Workflows/ENGINEERING_CONTRACT.md` 或 `.cursor/rules/engineering-contract.mdc`
3. `.cursor/rules/multi_chat_roles.mdc` — §Implementer
4. 本票 state — **FRAME**、**STATE**（含 `next_action`）

## 本轮回任务

用户提供：**ticket_id** · **state 路径** · **本轮回任务**

## 读写范围

| 区块 | 权限 |
|------|------|
| FRAME / STATE | 👁 只读 — **禁止修改** |
| **B_REPORT** | ✅ 可写 |
| AllowedPaths 内 code/docs | ✅ 可写 |

## Wave Master 子票

若 FRAME 含 Wave Master 扩展栏：

- **B_REPORT.verification** 必须可重跑 — 对照 FRAME.`observability.verify_commands` · 标注 `evidence_tier`
- skeleton/placeholder 分栏（Rule 7）
- schema SSOT：`docs/ticket-schema-master-v1.md`

## 禁止

- 越权改 FRAME/STATE/C/D_REPORT · 碰 BlockedPaths · 自标 done

## 交棒

告知用户运行 `/ticket-reviewer`，同一 state 路径。
