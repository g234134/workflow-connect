# G7-1 — AI 导入主线状态列表（IMP-*）

> **票号**：G7-1  
> **范围**：定义 **AI 导入 artifact 生命周期** 的主线状态名与语义边界。  
> **不含**：entry / exit 条件（→ G7-2 / G7-3）；代码实现；施工票队列状态。  
> **下游引用**：G7-2、G7-3、G8 artifact contract、G10 rulebook 应引用本档 **IMP-*** 正式名，不得自造同义别名。

---

## 1. 命名空间说明

workflow v2 并存多套「状态／phase／verdict」字汇。**禁止混用列名或把 A 域的值写入 B 域字段。**

| 命名空间 | 前缀 / 字段 | 权威来源 | 描述对象 | 典型取值 |
|----------|-------------|----------|----------|----------|
| **IMP-* 主线状态** | `IMP-` | **本档** | 单次 **AI 导入 artifact** 从范围草案到发布观测的生命周期 | `IMP-SCOPE-DRAFT` … `IMP-OBSERVING` |
| **queue 施工票状态** | （无统一前缀） | `workflow_v2/90_run_queue.md` | **治理施工票**（G6/G7/G8/G10 等）在 run queue 中的派工进度 | `TODO` / `DOING` / `BLOCKED` / `DONE` |
| **battle_report status** | JSON 字段 `status` | `04_Workflows/ops_cycle_schema.json` → `battle_report.status_values` | **单轮战报 JSON** 是否已封口、是否阻塞 | `draft` / `done` / `blocked` / `partial` |
| **route verdict / assignable** | `assignable` / `blocked` / `block_reason` | `04_Workflows/TASK_ROUTING.md`；`task_routing_table.json` → `phase_gates` | **副官路由**对某 `task_type` 当前 Phase 是否可派工 | `assignable: true|false`；`block_reason: str|null` |

### 1.1 相关但不得当作 IMP-* 主线的字汇

以下仅作**子域参考**或**并行维度**，**不得**直接当作 IMP-* 状态名，也不得在 artifact 元数据里用其值覆盖 `imp_state`（字段名 G7-2 再定）。

| 来源 | 字汇 | 为何不是 IMP-* |
|------|------|----------------|
| `ops_cycle_schema.json` → `cycle_states` | `open` / `active` / `archive_pending` / `archived` / `reviewed` | 描述 **ops 周期会话**，不是导入 artifact 阶段 |
| Coordinator JSON → `phases[].exit_criteria` | 字符串列表 | 描述 **单票内 subagent 阶段** 的完成条件，不是 artifact 生命周期态 |
| `00_Agent_Work_Progress.md` | 「已完成」「未完成」「阻塞」、里程碑叙述 | **战史叙事**字汇，非机读主线态 |
| Intake gate（暗部 `intake_schema` / min-loop gate） | `accept` / `reject` / `defer`；`lifecycle_status` 如 `accepted` / `auto_rejected` | **入站门禁子域**；最多触发 IMP 迁移，**不等于** IMP 状态名 |
| Wave / Phase 编号 | `Wave 0` / `Wave 1`；`Phase 1`–`Phase 4` | **项目阶段**（E1/G6/G7… 或企业 Phase），不是单 artifact 主线态 |
| G8 早期占位（若存在） | 如 `IMP-OPEN` / `IMP-ACTIVE` 等 | 施工草案别名；**须**在 G7-1 定稿后对账映射到本表正式名（见 §4 风险） |

### 1.2 使用规则（G7-1 冻结）

1. 描述「这份 AI 导入 artifact 现在处于导入流程哪一步」→ 只用 **IMP-***。  
2. 描述「G7-1 这张票有没有写完」→ 只用 **queue** 四态。  
3. 描述「这轮战报 JSON 是否定稿」→ 只用 **battle_report.status**。  
4. 描述「能不能派 dark.infra 施工」→ 只看 **route** 的 `assignable` / `block_reason` / `phase_gates`。  
5. **禁止**在 IMP-* 字段写入 `DOING`、`done`、`assignable:false` 等异域字面量。

---

## 2. IMP-* 状态总览

主线为 **artifact 生命周期**（非施工票、非战报、非路由裁决）。状态顺序为 **逻辑阶段**；具体允许跳转由 G7-2 / G7-3 定义。

```text
IMP-SCOPE-DRAFT
    → IMP-SPEC-CLARIFY
    → IMP-AI-READY
    → IMP-REVIEW-READY
    → IMP-RISK-VALIDATION
    → IMP-QA-READY
    → IMP-RELEASE-DECISION
    → IMP-RELEASED
    → IMP-OBSERVING

IMP-REWORK  （可自多态回退；entry/exit → G7-2 / G7-3）
```

| 状态 ID | 中文名 | 阶段摘要 |
|---------|--------|----------|
| `IMP-SCOPE-DRAFT` | 范围草案 | 导入意图与边界初稿 |
| `IMP-SPEC-CLARIFY` | 规格澄清 | 缺口、依赖、验收口径对齐 |
| `IMP-AI-READY` | AI 就绪 | 输入 artifact 满足 AI 辅助施工前置 |
| `IMP-REVIEW-READY` | 评审就绪 | 产出物齐备，待人审／peer review |
| `IMP-RISK-VALIDATION` | 风险校验 | 治理／风险／scope 合规校验 |
| `IMP-QA-READY` | QA 就绪 | 验证包齐备，待 QA 收口 |
| `IMP-RELEASE-DECISION` | 发布裁决 | 发布责任人裁决窗口 |
| `IMP-RELEASED` | 已发布 | 已按裁决进入目标受众／环境 |
| `IMP-OBSERVING` | 观测中 | 发布后观测期（非施工） |
| `IMP-REWORK` | 返工 | 未通过关口，需回修 artifact |

---

## 3. 分状态定义

### IMP-SCOPE-DRAFT

| 项 | 说明 |
|----|------|
| **中文名** | 范围草案 |
| **用途** | 记录 AI 导入目标的**初稿范围**：变更意图、目标 artifact 类型、粗粒度 in/out scope、关联票号。允许信息不完整，但须可识别「导入什么」。 |
| **不等于什么** | ≠ queue `TODO`（票未开工）；≠ battle_report `draft`（战报草稿）；≠ intake `defer`（入站暂缓）；≠ `IMP-SPEC-CLARIFY`（尚未进入澄清闭环）。 |

### IMP-SPEC-CLARIFY

| 项 | 说明 |
|----|------|
| **中文名** | 规格澄清 |
| **用途** | 对范围草案做**结构化澄清**：补齐 G8 五轨所需字段缺口、依赖票、验收口径、open questions 关闭或显式登记。 |
| **不等于什么** | ≠ Coordinator `phases[].exit_criteria` 已满足（那是派工计划，不是 artifact 态）；≠ `IMP-AI-READY`（澄清未闭合）；≠ Progress「阻塞」叙述（战史，非主线态）。 |

### IMP-AI-READY

| 项 | 说明 |
|----|------|
| **中文名** | AI 就绪 |
| **用途** | 输入 artifact 与治理上下文已满足 **AI 辅助导入／生成** 的前置条件（change class、允许动作、上下文入口等由 G6/G10 约束；细节 G7-2）。可启动 AI 施工，但**不**表示产出已通过人审或 QA。 |
| **不等于什么** | ≠ queue `DOING`（仅表示某张**施工票**正在写）；≠ route `assignable:true`（仅表示**路由**允许派工，不证明 artifact 已 AI-ready）；≠ `IMP-REVIEW-READY`（AI 产出尚未齐套待审）。 |

### IMP-REVIEW-READY

| 项 | 说明 |
|----|------|
| **中文名** | 评审就绪 |
| **用途** | AI／人工混合产出已**齐套**，进入人审、design review 或 peer review 队列；review 结论尚未写入 artifact 主线。 |
| **不等于什么** | ≠ battle_report `done`（战报封口 ≠ 评审通过）；≠ checker `accepted`（Cursor 验收 verdict，属 QA 子域）；≠ `IMP-RISK-VALIDATION`（尚未进入治理风险校验）。 |

### IMP-RISK-VALIDATION

| 项 | 说明 |
|----|------|
| **中文名** | 风险校验 |
| **用途** | 对 artifact 做 **治理与风险关口**：G6 change class 边界、G10 禁止盲信情境、禁区类型、override 留痕等。通过后方可进入 QA 就绪。 |
| **不等于什么** | ≠ governance-guard `stop_work`（Cursor 派工裁决，不写入 IMP 字段）；≠ route `assignable:false`（Phase 门闸，非 artifact 风险态）；≠ intake `reject` / `auto_rejected`（入站拒绝，非导入主线态名）。 |

### IMP-QA-READY

| 项 | 说明 |
|----|------|
| **中文名** | QA 就绪 |
| **用途** | 验证证据包（runner、断言、Work Report §4 等）已齐备，**等待 QA 执行**与 checker 收口；尚未发布。 |
| **不等于什么** | ≠ battle_report `partial`（战报部分完成，非 QA 关口）；≠ queue `DONE`（施工票完成 ≠ artifact 可发布）；≠ `IMP-RELEASE-DECISION`（QA 尚未给出可发布结论）。 |

### IMP-RELEASE-DECISION

| 项 | 说明 |
|----|------|
| **中文名** | 发布裁决 |
| **用途** | 发布责任人（G8 Release owner artifact）对**是否发布、发布范围、回退策略**做裁决窗口；裁决结果将驱动 `IMP-RELEASED` 或 `IMP-REWORK`。 |
| **不等于什么** | ≠ Phase gate `ruling`（阶段闸门回顾，属 ops review）；≠ `IMP-RELEASED`（尚未执行发布）；≠ enterprise Phase 升格（项目 Phase，非单 artifact）。 |

### IMP-RELEASED

| 项 | 说明 |
|----|------|
| **中文名** | 已发布 |
| **用途** | artifact 已按 Release 裁决进入**目标受众或目标环境**（文档定稿、配置生效、runbook 切换等——具体载体 G8-5 定义）。 |
| **不等于什么** | ≠ ops `cycle_states.archived`（周期封存，非发布）；≠ queue 全票 `DONE`（Wave 完成 ≠ 单 artifact 发布）；≠ `IMP-OBSERVING`（尚未进入发布后观测）。 |

### IMP-OBSERVING

| 项 | 说明 |
|----|------|
| **中文名** | 观测中 |
| **用途** | 发布后的**观测期**：收集反馈、SLO／质量信号、 incident 线索；不承载新 scope 施工（新 scope 新开 artifact 或经 `IMP-REWORK` 回流，G7-3 定义）。 |
| **不等于什么** | ≠ monitoring graph L0 observability 开关（运行时观测能力，非导入主线终态）；≠ Progress 里程碑「已完成」叙述；≠ `cycle_states.reviewed`（周期回顾完成，非 artifact 观测态）。 |

### IMP-REWORK

| 项 | 说明 |
|----|------|
| **中文名** | 返工 |
| **用途** | 评审、风险、QA 或发布裁决**未通过**，artifact 需回修。标记「主线曾失败一次关口」；回退目标态由 G7-3 定义（常见回到 `IMP-SPEC-CLARIFY` 或 `IMP-AI-READY`）。 |
| **不等于什么** | ≠ queue `BLOCKED`（施工票被依赖或环境阻塞）；≠ battle_report `blocked`（战报声明阻塞，非 artifact 生命周期态）；≠ intake `reject`（入站拒绝子域）；≠ 永久废弃（废弃策略 G8/G10 另定，本态仅表示可修复回退）。 |

---

## 4. 与既有字汇的对照（只读索引，非 IMP 名）

| 既有字汇 | 与 IMP-* 关系 |
|----------|----------------|
| queue `TODO` / `DOING` / `BLOCKED` / `DONE` | 并行维度：同一张 G7 施工票可 `DOING`，而其描述的 artifact 可处于 `IMP-SPEC-CLARIFY` |
| battle_report `draft` / `done` / `blocked` / `partial` | 每轮 chat 封口状态；**不**映射 1:1 到 IMP-* |
| route `assignable` + `phase_gates` | 能否派某类 worker；**不**替代 `IMP-RISK-VALIDATION` |
| Coordinator `phases[].exit_criteria` | 计划内检查项；达成后可**建议**迁移 IMP，但不自动等同 |
| Progress「已完成／阻塞」 | 人读战史；机读 IMP 以本表为准 |
| intake `accept` / `reject` / `defer` | 入站门禁；`accept` 可**触发**进入 `IMP-SCOPE-DRAFT` 或后续态，但**不得**把 `accept` 写入 IMP 字段 |

---

## 5. 文档边界

| 本档（G7-1） | 后续票 |
|--------------|--------|
| IMP-* 列表与命名空间 | G7-2：每状态 **entry** 条件 |
| 语义与「不等于」 | G7-3：每状态 **exit** 条件与合法迁移 |
| 与 G8 artifact 类型**名称**对齐索引 | G8 各轨：artifact 必填字段与 IMP 态挂钩 |
| — | 机读字段名（如 `imp_state`）与 enforcement：Wave 2+ |

---

## 6. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G7-1 初版：10 个 IMP-* 状态 + 命名空间说明 |
