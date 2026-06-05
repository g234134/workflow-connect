# Agent Role Map — 角色边界与职责（D3）

> **版本**：v0.1  
> **契约**：`agent_contract.md` · **交接**：`handoff_spec.md`  
> **实现 stub**：`base_agent.py`（`ROLE_ID` 常量）

---

## 1. 角色一览

| 角色 ID | 类名（建议） | 在流水线中的位置 |
|---------|--------------|------------------|
| `planner_agent` | `PlannerAgent` | 入口规划 |
| `executor_agent` | `ExecutorAgent` | 执行 |
| `reviewer_agent` | `ReviewerAgent` | 验收 / 闸门 |

---

## 2. `planner_agent`

### 负责（MUST）

- 理解 `goal`，产出**可执行、可排序**的步骤或子目标列表（`result.plan` / `result.steps`）。  
- 识别依赖、风险与约束，写入 `notes.assumptions`、`notes.risks`。  
- 在计划可冻结时 handoff 至 `executor_agent`（`status: need_handoff`）。  
- 当执行方反馈计划不可行时，接收 handoff 并**修订计划**（不直接改生产数据）。

### 不负责（MUST NOT — 避免 overlap）

- **不**执行 shell、API 调用、数据库写入、文件 ingest。  
- **不**做最终验收裁决（不输出「通过/不通过」终审）。  
- **不**修改他人 `core` 或 Governance 状态文件。  
- **不**发明 `next_agent` 路由表之外的下游。

### 典型输出 `result` 形状

```json
{
  "plan_id": "string",
  "steps": [{ "id": "1", "action": "string", "acceptance": "string" }],
  "frozen": true
}
```

---

## 3. `executor_agent`

### 负责（MUST）

- 按 `context.handoff_payload` 或 `prior_outputs` 中最新 plan **执行**步骤。  
- 将执行产物写入 `result`（结构化：计数、run_id、子系统 `ok` 等）。  
- 执行完成后 handoff 至 `reviewer_agent`，或 `success`（若流程无独立 reviewer 且 goal 已含验收）。  
- 遇阻塞时 `notes` 标明 `blocker`；可 handoff 回 `planner_agent` 重规划。

### 不负责（MUST NOT）

- **不**从零拆解用户意图（无 plan 时应 `fail` 或 handoff 至 `planner_agent`）。  
- **不**单方面宣布任务终审通过（`status: success` 仅当 goal 明确包含执行且**无** reviewer 节点）。  
- **不**覆盖 `prior_outputs` 历史。  
- **不**跳过 `validate_output` 或将 prose 作为唯一 `result`。

### 典型输出 `result` 形状

```json
{
  "executed_steps": ["1", "2"],
  "artifacts": { "run_id": "string", "subsystem": { "ok": true, "message": "token" } },
  "partial": false
}
```

---

## 4. `reviewer_agent`

### 负责（MUST）

- 对照 `handoff_payload.verify_criteria` 或 plan 中的 `acceptance` **独立验收**。  
- 输出 `result.verdict`：`accept` | `reject` | `needs_info`。  
- `accept` → `status: success`；`reject` → `need_handoff` 至 `executor_agent` 或 `fail`（不可恢复）。  
- 在 `notes` 中列出未满足项与证据引用（逻辑名 / run_id，非密钥）。

### 不负责（MUST NOT）

- **不**执行新的 ingest / 大规模写操作（仅只读复验；修复由 executor 重做）。  
- **不**重写全盘计划（应 handoff 至 `planner_agent`）。  
- **不**在 `reject` 时仍标 `success`。  
- **不**省略 `prior_outputs` 中 executor 产物即做裁决。

### 典型输出 `result` 形状

```json
{
  "verdict": "accept",
  "checks": [{ "id": "INV1", "ok": true, "message": "string" }],
  "evidence_refs": ["run_id:..."]
}
```

---

## 5. 重叠防护矩阵

| 活动 | planner | executor | reviewer |
|------|:-------:|:--------:|:--------:|
| 拆目标 / 排步骤 | ✓ | — | — |
| 调工具 / 写数据 | — | ✓ | — |
| 独立验收 | — | — | ✓ |
| 终审通过宣告 | — | △* | ✓ |
| 改计划 | ✓ | — | — |
| 路由 handoff | ✓ | ✓ | ✓ |

\* executor 仅当编排图**无** reviewer 节点且 goal 已含执行+验收合一。

---

## 6. 扩展角色

新增角色须：

1. 在本表增加一节（负责 / 不负责 / `result` 形状）。  
2. 更新 `handoff_spec.md` §4 路由边表。  
3. 由 Governance 对齐全局观测字段名（合約 C16–C17）。

---

## 7. 与暗部四 Agent 的关系

本文件定义 **D3 协调层** 逻辑角色（planner / executor / reviewer），与 Infra / Data / RAG / Governance 四舱 **正交**：

- 四舱 agent 可作为 `executor_agent` 的**实现绑定**（按任务类型路由，见 `04_Workflows/TASK_ROUTING.md`）。  
- 不得让四舱各自定义冲突的 handoff 字段名；以本契约为准。
