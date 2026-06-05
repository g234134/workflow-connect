# Handoff Specification — 代理交接规范（D3）

> **版本**：v0.1  
> **契约**：`agent_contract.md`  
> **角色路由**：`agent_role_map.md`

---

## 1. 什么是 handoff

**Handoff** 指：当前 agent 以 `status: need_handoff` 结束，并将**可重放的最小上下文包**交给 `next_agent`，由编排器启动下一节点。

一次 handoff 计为 D3 指标 **`handoff_count`** 加 1（`metrics/metrics_collector.py` → `record_handoff(task_id)`）。

---

## 2. 何时允许 handoff

| 条件 | 说明 |
|------|------|
| H1 — 角色边界 | 当前工作超出本角色职责（见 `agent_role_map.md`「不负责」列）。 |
| H2 — 可验收分界 | 上游产出已**冻结**（如 plan 已定、ingest 已跑完），下游只需验收或执行下一阶段。 |
| H3 — 显式路由 | `next_agent` 在 `agent_role_map.md` 的允许边表中（见 §4）。 |
| H4 — 无静默降级 | 不得因「懒得做完」而 handoff；`notes` 必须写明交接原因与下游待办。 |

### 2.1 禁止 handoff

- 本节点 `goal` 尚未达成且未记录为**可分割**的 partial result。  
- `next_agent` 未定义或不在角色表中。  
- `context.prior_outputs` 未包含当前节点完整 `AgentOutput`（见 §3）。  
- 校验失败（`validate_output` 未通过）。  
- 需要人类裁決的高风险禁區（憲法 §7）— 应 `status: fail` 并阻塞，而非 handoff 给自动 agent。

---

## 3. Handoff 必带字段

下游 `input` 在 handoff 时 **必须**满足：

### 3.1 顶层（继承 `AgentInput`）

| 字段 | 要求 |
|------|------|
| `task_id` | 与上游相同（全链路不变） |
| `goal` | **重写**为下游单一目标（非复制上游 goal） |
| `context` | 见下表 |

### 3.2 `context` 交接包（`HandoffContext`）

| 字段 | 必填 | 说明 |
|------|------|------|
| `prior_outputs` | **是** | 数组；**追加**当前节点完整输出（含 `result`、`status`、`notes`、`next_agent`）。顺序 = 时间序。 |
| `handoff_payload` | **是** | 对象；仅含下游**必需**字段（计划步骤、文件逻辑名、验证标准等）。禁止整包复制无关上游日志。 |
| `metadata.handoff_index` | **是** | 整数，从 0 递增 |
| `metadata.source_agent` | **是** | 交出方角色 id |
| `metadata.target_agent` | **是** | 接收方 = `next_agent` |
| `artifacts` | 推荐 | 可执行引用（run_id、batch_id、collection 逻辑名） |
| `constraints` | 推荐 | 继承并**追加**新约束，不删除旧约束除非在 `notes` 说明 |

### 3.3 当前节点输出（`AgentOutput`）

| 字段 | handoff 时要求 |
|------|----------------|
| `status` | 必须为 `need_handoff` |
| `next_agent` | 非空，且与 `metadata.target_agent` 一致 |
| `notes` | 含 `reason`、`downstream_goal_hint`、`open_questions`（键名固定，见示例） |
| `result` | 含 `partial` 或等价结构，标明已完成与未完成 |

### 3.4 示例

```json
{
  "task_id": "task-20260523-001",
  "goal": "验收 ingest 结果是否满足 INV1–INV4",
  "context": {
    "prior_outputs": [
      {
        "result": { "steps": ["ingest", "verify"], "plan_id": "p1" },
        "status": "need_handoff",
        "next_agent": "reviewer_agent",
        "notes": {
          "reason": "planner 不执行 verify",
          "downstream_goal_hint": "对照 runbook 断言",
          "open_questions": []
        },
        "ok": false,
        "message": "handoff to reviewer_agent"
      }
    ],
    "handoff_payload": {
      "verify_criteria": ["INV1", "INV2", "INV3", "INV4"],
      "ingest_run_id": "run-abc"
    },
    "metadata": {
      "handoff_index": 1,
      "source_agent": "planner_agent",
      "target_agent": "reviewer_agent"
    },
    "artifacts": { "ingest_run_id": "run-abc" },
    "constraints": ["只读验收，不触发新 ingest"]
  }
}
```

---

## 4. 允许的角色路由边（默认流水线）

```mermaid
flowchart LR
  P[planner_agent] -->|plan frozen| E[executor_agent]
  E -->|execution done| R[reviewer_agent]
  E -->|blocked / policy| P
  R -->|reject| E
  R -->|accept| END[success]
```

| 从 | 到 | 典型触发 |
|----|-----|----------|
| `planner_agent` | `executor_agent` | 计划已列出且通过自检 |
| `executor_agent` | `reviewer_agent` | 执行完成待验收 |
| `executor_agent` | `planner_agent` | 发现计划不可执行需重规划 |
| `reviewer_agent` | `executor_agent` | 验收失败需修复重跑 |
| `reviewer_agent` | — | `success` 结束，无 `next_agent` |

其他边须 Governance 书面追加至本表，禁止各 agent 私自发明路由。

---

## 5. 如何避免信息丢失

| 策略 | 说明 |
|------|------|
| **完整链** | `prior_outputs` 只追加、不覆盖；编排器禁止在中间节点丢弃历史。 |
| **最小必要** | `handoff_payload` 只放下游必需字段；大对象用 `artifacts` 引用 id，不嵌套全文。 |
| **目标重写** | 下游 `goal` 必须可独立验收；不得假设下游读过上游对话。 |
| **开放问题** | `notes.open_questions` 非空时，下游 `notes` 须回应或升级为 `fail`。 |
| **指标留痕** | 每次 handoff 调用 `record_handoff(task_id)`；战报写 `handoff_index` 与 `source`→`target`。 |
| **校验闸门** | 编排器在 dispatch 前调用 `validate_output()`；失败不启动下游。 |

---

## 6. 编排器职责（非 agent 实现）

1. 校验 `next_agent` 在允许边表中。  
2. 构造下游 `AgentInput`（§3）。  
3. 递增 `handoff_index` 并记录 metrics。  
4. `fail` 时停止图；`success` 时按流程决定是否进入 reviewer。

---

## 7. 与 Governance `handoff.md` 的关系

- **本 spec**：运行时 agent 之间的结构化包（机器可读）。  
- **`04_Workflows/project_status/handoff.md`**：跨 session / 跨 chat 的人类交接（Governance 独占写回）。  
- 机器 handoff 摘要可同步进战报，但不可替代 `prior_outputs` 数组。
