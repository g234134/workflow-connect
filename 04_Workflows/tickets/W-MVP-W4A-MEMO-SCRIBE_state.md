# TICKET STATE · W-MVP-W4A-MEMO-SCRIBE · lookup 文档与交叉引用

> handoff 摘要档；跨 chat 交棒以本档为准，不是完整工作日志。  
> Wave：Wave 4A · W-MVP — MEMO Scribe（**仅说明层**；**不改**任何 `.py`）

---

## FRAME

> 冻结来源：`W-MVP-W4A-MEMO-ORCH_state.md` · 实现依据：`W-MVP-W4A-MEMO-LOOKUP_state.md`（B_REPORT）

- Goal: 把已实现的 lookup 功能（`cases/index.json` + `lookup_case_history` CLI）写进文档与 `cases/README`，使「先查再建案」成为接案默认动作。
- Scope:
  - `cases/README.md` 新增「查历史案例（lookup）」小节与建案 checklist 第 0 步
  - `docs/MVP_CASE_E2E_DoD_v0.1.md` 前置条件与脚本索引交叉引用
  - `docs/C2-P2_RUNBOOK.md` 阶段 A checklist 推荐项
  - 本票 state（D_REPORT / scribe_note）
- NonScope:
  - 不改 `scripts/lookup_case_history.py`、不改 CLI 输出格式
  - 不宣称 lookup 为「智能推荐引擎」或「自动决策系统」
  - 不扩展到 RAG／长记忆描述
  - 不改 `core/*`、gate／cleaning／bundle 主链
- AllowedPaths:
  - `cases/README.md`
  - `docs/MVP_CASE_E2E_DoD_v0.1.md`
  - `docs/C2-P2_RUNBOOK.md`
  - `04_Workflows/tickets/W-MVP-W4A-MEMO-SCRIBE_state.md`
- BlockedPaths:
  - `scripts/*` · `tests/*` · `cases/index.json`（逻辑层）
  - `core/*` · `AGENTS.md` · `.cursor/rules/*`
- Dependencies:
  - `W-MVP-W4A-MEMO-LOOKUP`（implementer done · B_REPORT 含 cli_usage）
  - `W-MVP-W4A-MEMO-ORCH`（FRAME）
- AcceptanceCriteria:
  - `cases/README.md` 含 lookup 说明、2–3 条 CLI 示例、stdout 形状说明
  - DoD 与 runbook 各有一处「推荐先 lookup」交叉引用（非 hard gate）
  - D_REPORT 列出变更文件与 scope_out；`status_by_role.scribe: done`

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: Orchestrator 可视情况更新 Progress Wave 4 状态表（lookup 文档已就绪）；推进 Wave 4B 护栏与 4C demo 收口
- last_updated: 2026-06-08 · scribe
- status_by_role:
  - orchestrator: pending
  - implementer: n/a
  - reviewer: n/a
  - scribe: done

---

## B_REPORT

<!-- Implementer n/a；lookup 实现见 W-MVP-W4A-MEMO-LOOKUP_state.md -->

---

## C_REPORT

<!-- Reviewer n/a（本票仅文档） -->

### scribe_note

**变更文件（仅文案与交叉引用，未改任何逻辑）：**

| 文件 | 要点 |
|------|------|
| `cases/README.md` | 新增 §查历史案例（lookup）；建案 Checklist 第 0 步「先查再建」 |
| `docs/MVP_CASE_E2E_DoD_v0.1.md` | §2 前置条件增加推荐 lookup 行；§6 脚本索引补 LOOKUP 票 |
| `docs/C2-P2_RUNBOOK.md` | §2 权威索引、§7.1 checklist 推荐项、§7.2 命令示例 |

**定位声明：** lookup 文档化为**只读历史案例索引**；不接 gate、不触发清洗、不做策略推荐。

**Orchestrator 提醒：** Wave 4A 在 Scribe 角度已 **done**；可更新 Progress「Wave 4 partial」中「尚无轻量索引」表述，并继续 **4B 护栏** 与 **4C demo 收口**。

### scope_out（Scribe 边界）

- 不更改 lookup CLI 的代码或输出格式。
- 不在文档中宣称 lookup 是「智能推荐引擎」或「自动决策系统」，只说是「历史案例索引」。
- 不扩展到任何 RAG／长记忆描述。
- 未改 `04_Workflows/00_Agent_Work_Progress.md`（留 Orchestrator 末尾更新 Wave 表）。

---

## D_REPORT

- docs_updates:
  - `cases/README.md` — lookup 小节 + checklist step 0
  - `docs/MVP_CASE_E2E_DoD_v0.1.md` — §2 推荐前置、§6 脚本表
  - `docs/C2-P2_RUNBOOK.md` — §7.1 推荐 checklist、§7.2 示例命令
- progress_entry: Wave 4A lookup 已文档化：接案推荐先跑 `lookup_case_history`；索引维护见 `build_cases_index.py`。Scribe 票完成，无 `.py` 变更。
- followup_suggestions: Wave 4A 就绪，可继续推进 4B 护栏与 4C demo 收口；Progress Wave 4 行可由 Orchestrator 标为 lookup 文档 done／记忆层 partial→进展中。
