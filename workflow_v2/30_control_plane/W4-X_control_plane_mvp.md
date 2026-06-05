# W4-X-CONTROL-PLANE-MVP — Control Plane MVP（最小控制面骨架）

> **目标**：为 Wave 4 / Wave 5 路线补上最小控制面骨架，使系统具备：
>
> 1) 总调度（Supervisor / HQ Orchestrator）  
> 2) 多 chat / 多子任务分流（lane 模型）  
> 3) 独立代码检查员（Reviewer / Code Inspector）
>
> **执行原则**：先做 MVP，不追求一次做成全自动多代理平台；先把角色、责任边界、最小工作流、上下文卡机制落盘，确保后续 W4-A / W4-B / W4-C / Wave 5 都能挂在这层控制面上。

---

## 0. Out of Scope（本票刻意不做）

以下内容 **明确留给 Wave 5+**（本票只写成“未来能力”，不实现）：

- 自动开 chat、自动并行调度、自动选择/升级 lane
- 自动 merge 决策（含“通过即合并”式流水线）
- 更复杂 reviewer pipeline（多阶段、打分、准入门槛等）
- deny engine runtime 新增/启用（见 `00_master_plan.md` §15.6 / Wave 5+ 分界）

---

## 1. 角色（最小职责边界）

### 1.1 Supervisor（HQ Orchestrator / 总调度）

**负责什么（MVP）**：

- 读取 Ticket Memory / Context Card（模板见 `workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`）
- 决定：
  - 开哪张票（ticket id）
  - 读 Ticket Memory 的 `lane` / `priority`，决定走哪条工作流与并行排程顺序
  - 分配给哪个角色（planner / executor / reviewer / doc-sync）
  - 何时进入 review、何时进入 doc-sync、是否退回
- 维护控制面“挂点”：
  - 在 `workflow_v2/90_run_queue.md` 为票建立状态行（或更新本票 Status/Notes）
  - 在 `workflow_v2/99_latest_status.md` 追加阶段性摘要（只写“发生了什么/下一步”，不代写实现）

**不负责什么（硬边界）**：

- 不在一个大上下文里同时做：规划 + 实装 + 审核 + 文档回写
- 不代写模块正文（例如 `workflow_v2/10_governance/*`）
- 不触碰暗部脚本/环境树、不新增/启用 deny engine runtime

### 1.2 Planner（Planning lane owner）

**负责**：把 ticket 的目标、约束、读写集合、DoD 写清楚，并输出可交付的“最小计划”（lane 输入输出可复用）。

**不负责**：落地 runtime 改动、替 reviewer “放行”、替 doc-sync 回写全局黑板。

### 1.3 Executor（Runtime Implementation lane owner）

**负责**：在严格 `read_set/write_set` 范围内做最小实现增量，并提供可重跑验证证据（若本票是文档票，则 executor 可为空）。

**不负责**：在 runtime lane 内改写 `00_master_plan.md` / `90_run_queue.md` / `99_latest_status.md` 的全局语义（这属于 doc-sync lane）。

### 1.4 Reviewer（Review / Code Inspector）

**负责（只读）**：

- 边界检查：
  - 是否越界到 Wave 5 自动化（例如自动调度/自动 merge/deny runtime）
  - 是否修改了禁止文件或触及禁区（暗部脚本、禁区类型见战车憲法）
  - 是否违反 frozen constraints（票面声明的“不得改”）
- 一致性检查：
  - runtime 与文档语义是否冲突（若本票仅文档，则检查跨文档一致性）
  - 是否漏了必要 doc-sync（`00/90/99` 挂点、模板引用、状态回写）
- 输出：**退回 / 放行建议**（不写主功能、不代写实现）

#### 1.4.1 Reviewer 最小检查清单（可复用）

每张票进入 Review lane 时，Reviewer **至少**逐项核对（任一项不通过 → `request_changes` 或 `block`，并写明原因）：

- [ ] **Wave 5 越界**：变更是否引入或依赖 §0 Out of Scope 能力（自动开 chat、自动并行调度、自动 merge、deny engine runtime 新增/启用、多阶段 reviewer pipeline 等）？
- [ ] **禁止触及范围**：是否修改了票面 `frozen_constraints` 或全局禁止项（含 G7/G8 正文语义、prod rollout 流程、暗部脚本/环境树、`.env`/金鑰、未授权的 `tools/`/`CI`/runtime 配置）？
- [ ] **读写边界**：diff 是否超出 Ticket Memory 的 `read_set` / `write_set`；runtime lane 是否擅自改写 `00/90/99` 全局语义？
- [ ] **doc-sync 完整性**：是否遗漏必要的 doc-sync 票或步骤（`00_master_plan.md` 能力挂点、`90_run_queue.md` 票行 Status/Notes、`99_latest_status.md` 阶段摘要、模板/交叉引用）？
- [ ] **语义一致性**：runtime 实现（若有）是否与主文档、contract、`done_definition` 一致；纯文档票是否跨文档自相矛盾？
- [ ] **证据与 DoD**：是否具备可重跑验证证据（或合规的 `ok:false` + 阻塞说明）；是否将 skeleton/placeholder 冒充为已验收能力？

> **Verdict 约定**：全部通过 → `approve`；可修复项 → `request_changes`；触禁区或不可在本票收敛 → `block`。

### 1.5 Doc-sync（Doc Sync lane owner）

**负责**：

- 将“已发生的事实”回写到 v2 控制面挂点：
  - `workflow_v2/00_master_plan.md`：能力挂点（小节级）
  - `workflow_v2/90_run_queue.md`：票行的 Status/Notes（不删历史）
  - `workflow_v2/99_latest_status.md`：阶段摘要（不夸大、不过度承诺）
- 确保 Ticket Memory 模板与各票引用一致

**不负责**：替实现补功能、替 reviewer 做“实装修复”。

---

## 2. 多 chat / 多 lane 分流模型（四类 lane）

> **原则**：implementation 票默认不读全局 `00/90/99`；这些属于 doc-sync lane 的职责（除非票面明确授权）。

下面每个 lane 都以“输入/读写集合/完成定义”固定为可复用契约。

### 2.1 Planning lane

- **输入**：
  - `ticket`（票号/标题）
  - 现有基准（必要时只读：`00_master_plan.md` 的相关小节、`90_run_queue.md` 对应行、邻接 runbook/规范）
- **允许读**：
  - 本票相关的 v2 文档（`workflow_v2/*` 中与本票目标直接相关者）
  - 约束类（战车 `AGENTS.md`、工程合约、憲法）在需要确认边界时只读引用
- **允许改**：
  - Ticket Memory（新增/更新该票的 context card）
  - 本票主文档草案（若票是文档/规范类）
- **完成定义**：
  - 产出一份可执行的 Ticket Memory（含 frozen constraints 与 done_definition）
  - 明确把工作拆到后续 lane：runtime / review / doc-sync（每个 lane 的输入输出齐全）

### 2.2 Runtime Implementation lane

- **输入**：
  - Planning lane 产出的 Ticket Memory（`mode=runtime-only`）
- **允许读**：
  - `read_set` 中列出的代码/文档/测试（以票面为准）
- **允许改**：
  - **仅** `write_set` 中列出的文件（以票面为准）
- **完成定义**：
  - 最小可验收增量已落地
  - 已提供可重跑验证证据（或声明阻塞并给出 `ok:false`/fallback 方案）

### 2.3 Review / Code Inspection lane

- **输入**：
  - runtime lane 的 diff 或文档变更集合
  - ticket 的 frozen constraints / done_definition
- **允许读**：
  - 变更涉及的文件 + 票面约束引用（必要时只读 `00/90/99` 对账）
- **允许改**：
  - **默认不改代码/文档正文**；只写 review 结论与建议（可落在 ticket notes 或专门 review 记录段）
- **完成定义**：
  - 给出明确 verdict：`approve` / `request_changes` / `block`（并列出原因与回退建议）

### 2.4 Doc-sync lane

- **输入**：
  - 已通过 review 的变更结论（或明确的退回原因）
- **允许读**：
  - `00_master_plan.md` / `90_run_queue.md` / `99_latest_status.md` + 本票主文档与模板
- **允许改**：
  - 仅文档挂点与状态文件（按本 lane 的 write_set）
- **完成定义**：
  - `00/90/99` 已有正式挂点与一致引用
  - Ticket Memory 模板可复用，且本票引用正确

---

## 3. Ticket Memory / Context Card（模板约定）

- 模板文件：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`
- 每张票至少要能被 Supervisor 用“最小上下文”重建工作面：
  - `lane` + `priority` 决定**走哪条工作流**与**并行排程顺序**
  - `mode` 描述本张 Context Card 所服务的执行切片（应与 `lane` 对齐）
  - `read_set/write_set` 决定允许触及范围
  - `frozen_constraints/done_definition` 决定 reviewer 判定依据（见 §1.4.1 最小检查清单）

### 3.1 `lane`（工作流分流）

| 取值 | Supervisor 用途 | 典型派工 |
|------|-----------------|----------|
| `planning` | 补齐/修订 Ticket Memory、拆后续 lane | Planner |
| `runtime` | 在 `write_set` 内做最小实现或文档正文（以票面为准） | Executor |
| `review` | 只读边界与一致性检查 | Reviewer（§1.4.1） |
| `doc-sync` | 回写 `00/90/99` 与控制面挂点 | Doc-sync |

- **与 `mode` 的关系**：`lane` 为调度主字段；`mode` 与之对齐（`runtime` ↔ `runtime-only`）。Supervisor 开并行多 chat 时，以各子票的 `lane` 分流，避免在同一上下文混做规划+实装+审核+回写。
- **多票并行**：同一时刻可有多张票处于不同 `lane`；Supervisor 按票号与依赖图分别派发，**不得**因并行而合并读写边界。

### 3.2 `priority`（排程与抢占）

| 取值 | 含义（MVP 默认） |
|------|------------------|
| `P0` | 阻塞主线或安全/禁区相关；优先开工、可抢占低优先级 slot |
| `P1` | 主线增量（默认） |
| `P2` | 可延后、文档澄清、非阻塞跟进 |

- **用途**：多票并行时决定**开工顺序**与**资源抢占**（先 `P0`，再 `P1`，再 `P2`）。
- **同优先级**：按 `90_run_queue.md` 的 `Depends on`、票面阻塞状态、以及 Supervisor 对 W4 软顺序（如 index 不晚于 canary）的裁决胜出。
- **不写 runtime**：`priority` 仅存在于 Ticket Memory / 队列 Notes；本 MVP **不**实现自动调度器。

---

## 4. MVP 最小闭环流程（步骤版）

1. **Supervisor** 读取本票 Ticket Memory（若缺失则先派发 Planning lane 补齐）
2. 派发 **Planning lane**：产出可执行 Ticket Memory（含 read/write/frozen/DoD）
3. 派发 **Runtime lane**：在 `write_set` 内实现最小增量并给出证据
4. 派发 **Review lane**：只读检查边界/禁区/冲突，给出 verdict
5. 若通过，进入 **Doc-sync lane**：回写 `00/90/99` 挂点与状态（不夸大、不 retro）
6. Supervisor 在 `90_run_queue.md` 更新本票 Status/Notes，并在 `99_latest_status.md` 追加一条“本轮发生了什么/下一步”

---

## 5. 交付物与挂点（本票 DoD）

- [ ] 有一份明确的控制面 MVP 文档（本文）
- [ ] Supervisor / Planner / Executor / Reviewer / Doc-sync 五角色职责边界明确
- [ ] 多 lane 分流规则明确（输入/读写集合/完成定义）
- [ ] Ticket Memory / Context Card 模板可复用
- [ ] `00_master_plan.md` / `90_run_queue.md` / `99_latest_status.md` 已挂上正式锚点
- [ ] 明确写出留给 Wave 5+ 的自动化能力（见 §0）

