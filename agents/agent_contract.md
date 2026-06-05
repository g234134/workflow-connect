# Agent Contract — 多代理统一输入/输出契约（D3）

> **版本**：v0.1（协议草案）  
> **关联**：`handoff_spec.md`、`agent_role_map.md`、`base_agent.py`  
> **指标**：D3 `handoff_count` 见 `metrics/metric_definition.md`  
> **母本对齐**：`04_Workflows/ENGINEERING_CONTRACT.md` 附录 B（`ok` / `message` 信封）

---

## 1. 目的

使任意两个 agent 之间的 **输入可解析、输出可校验、交接可审计**，为 LangGraph / 编排器提供稳定节点边界。

---

## 2. 输入契约（`AgentInput`）

每次调用 `run(input)` 时，`input` **必须**为 `dict`，且包含下列顶层键：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | `string` | 是 | 全链路唯一任务标识；同一 `task_id` 下允许多次 handoff，由编排器维护序号。 |
| `goal` | `string` | 是 | 本节点要完成的**单一**目标陈述（一句可验收描述）。 |
| `context` | `object` | 是 | 结构化上下文；**禁止**用自然语言整段代替 `context`。 |

### 2.1 `context` 推荐子结构（可扩展，键名由 Governance 统一）

| 子键 | 类型 | 说明 |
|------|------|------|
| `artifacts` | `object` | 上游产物引用（路径逻辑名、chunk id、run_id 等），非裸磁盘路径。 |
| `constraints` | `array` | 硬约束列表（禁改范围、超时、token 上限等）。 |
| `prior_outputs` | `array` | 上游 agent 的**完整**契约输出快照（handoff 时必填，见 `handoff_spec.md`）。 |
| `metadata` | `object` | 追踪字段：`trace_id`、`handoff_index`、`source_agent` 等。 |

### 2.2 输入示例

```json
{
  "task_id": "task-20260523-001",
  "goal": "将用户目标拆解为可执行步骤清单",
  "context": {
    "artifacts": {},
    "constraints": ["仅规划，不执行 shell"],
    "prior_outputs": [],
    "metadata": { "handoff_index": 0, "source_agent": "orchestrator" }
  }
}
```

---

## 3. 输出契约（`AgentOutput`）

`run(input)` **必须**返回 `dict`；经 `validate_output()` 校验后方可交给下游或 LangGraph。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `result` | `any` | 是 | 本节点业务结果（结构化；禁止仅返回 prose 而无结构）。 |
| `status` | `enum` | 是 | `success` \| `fail` \| `need_handoff` |
| `next_agent` | `string` \| `null` | 条件 | `status=need_handoff` 时**必填**；否则应为 `null` 或省略。 |
| `notes` | `string` \| `array` \| `object` | 是 | 审计说明：假设、风险、未完成项、给下游的指令。 |

### 3.1 与仓库信封字段（编排层附加）

实现类应在 `validate_output()` 通过后，由 `BaseAgent` 自动补全（见 `base_agent.py`）：

| 字段 | 说明 |
|------|------|
| `ok` | `status == "success"` → `true`；`fail` / `need_handoff` → `false` |
| `message` | 单行人类可读摘要（供 CLI / 战报） |

### 3.2 `status` 语义

| 值 | 含义 | 编排器行为 |
|----|------|------------|
| `success` | 本节点目标已达成 | 结束或进入 reviewer（若流程定义） |
| `fail` | 不可恢复失败 | 停止链路；记录 `error_type`（D5） |
| `need_handoff` | 本节点完成部分工作，需另一角色继续 | 路由至 `next_agent`；`handoff_count += 1` |

### 3.3 输出示例

**成功：**

```json
{
  "result": { "steps": ["ingest", "verify"], "estimated_risk": "low" },
  "status": "success",
  "next_agent": null,
  "notes": "计划已覆盖 D3 目录级 smoke 路径",
  "ok": true,
  "message": "planner: 2 steps"
}
```

**交接：**

```json
{
  "result": { "partial": { "ingest_ok": true } },
  "status": "need_handoff",
  "next_agent": "reviewer_agent",
  "notes": { "reason": "需要独立验收 ingest 不变式", "carry": ["verify_criteria"] },
  "ok": false,
  "message": "handoff to reviewer_agent"
}
```

---

## 4. 校验规则（`validate_output`）

1. 顶层键：`result`、`status`、`notes` 必须存在。  
2. `status` 仅允许三枚举值。  
3. `status == "need_handoff"` ⇒ `next_agent` 为非空字符串。  
4. `status != "need_handoff"` ⇒ `next_agent` 为 `null` 或缺失。  
5. `result` 不得为 `None`（可用空对象 `{}` 表示无产物）。  
6. 校验失败时返回 `ok: false` 的 **校验报告** `dict`，不得抛未捕获异常冒充成功。

---

## 5. 禁止事项

- 用纯自然语言作为唯一 `result`（须包在结构化字段内，如 `{ "summary": "..." }`）。  
- `need_handoff` 时不填 `next_agent`。  
- 在 `context` 中丢失 `prior_outputs` 导致下游无法重放决策（见 handoff spec）。  
- 输出 secret / token / 完整连接字符串（糧草仅 `[OK]` / `[FAILED]`）。

---

## 6. LangGraph 节点约定

- **状态键**：`agent_input`（`AgentInput`）、`agent_output`（`AgentOutput`）、`handoff_chain`（`array` of outputs）。  
- **节点函数**：调用 `BaseAgent.invoke_node(state)`，由 stub 写入 `agent_output` 并 append 至 `handoff_chain`。  
- **边条件**：`state["agent_output"]["status"]` 决定 `success` / `fail` / `handoff` 分支。

细节见 `base_agent.py` 中 `to_graph_state_patch` / `from_graph_state`。
