# G6-1 — AI Change Classes（CHG-*）

> **票号**：G6-1  
> **下游**：G6-2（每类允许动作）、G10-1／G10-2（边界与禁止情境须**引用**本表，不重定义）  
> **权威位阶**：尚書省当次指令 ＞ 憲法 ＞ 工程合約 ＞ 本表 ＞ 任务卡局部 brief  
> **本文件定义**：AI 导入工作流中，**一次施工意图**的变更**类别**（what kind of change），**不**定义可否执行（见 G6-2）、**不**定义裁決结果（见 G10）、**不**定义队列生命周期（见 G7／`90_run_queue.md`）。

---

## 1. 用途

1. 给 coordinator／governance-guard／worker 共用一套 **CHG-*** 词汇，描述「这张票在改什么性质的东西」。  
2. 给 G6-2 挂载 **allowed actions**（读／写／派工／验证）时提供稳定主键。  
3. 给 G10 写「禁止盲信 AI 输出」时引用 **class**，避免与 deny／gate 混名。  

**使用方式（本票范围外，仅索引）**：

- 任务卡或 coordinator 输出应声明 **主 class**（一个）与可选 **secondary class**（多个时须说明为何拆票）。  
- `governance-guard` 的 `proposal_type: scope_change` **不等于** CHG-*；guard 裁決后，父 agent 仍须用 CHG-* 标注实际变更性质（见 §3.3）。  
- `04_Workflows/OPS_CYCLE.md` 的 `bugfix`／`doc_clarification`／`governance_test` 是 **Cursor 协作链工单类型**，与 CHG-* **可映射但不同命名空间**（见 §6）。

---

## 2. 命名空间与三条边界（必读）

### 2.1 CHG-* ≠ deny type（裁決／拒绝类型）

| 维度 | CHG-*（本文件） | deny type（他模块） |
|------|-----------------|---------------------|
| **回答的问题** | 变更的**性质**是什么？ | 提案是否**被拒绝**、为何拒绝？ |
| **典型载体** | 任务卡 `change_class`、coordinator 计划 | `governance-guard` → `verdict: deny\|stop_work`；G10-2 禁止情境 |
| **例子** | `CHG-IMPL-SINGLE` | `deny` + `violations[].rule_ref: 合約Rule-5` |
| **关系** | 同一票可在 **CHG-HIGH-RISK** 下仍被 `allow`（条件满足时） | `deny` 不反向定义 CHG；禁止的是**动作**，不是 class 名 |

**禁止混用**：不得用 `CHG-DENY-*`；不得把 `verdict` 写入 CHG 枚举。

### 2.2 CHG-* ≠ gate type（门控／相位类型）

| 维度 | CHG-* | gate type |
|------|-------|-----------|
| **回答的问题** | 改什么？ | 当前 Phase／路由是否**放行派工**？ |
| **典型载体** | G6 本表 | `TASK_ROUTING` → `assignable`／`block_reason`；憲法 §5.2 DarkOps；`phase_gates` |
| **例子** | `CHG-IMPL-CROSS` | `DarkOps-Worker: blocked` → `assignable=false` |
| **关系** | `CHG-IMPL-*` 可指向 dark 域，但 **class 不编码 blocked** | gate 变化本身若只改路由表／门控文档 → 常标 `CHG-RULEBOOK` 或 `CHG-GOV-DOC`，**不是** `CHG-HIGH-RISK` 充分条件 |

**禁止混用**：不得用 `CHG-GATE-*`；不得以 `assignable` 真假作为 class 名。

### 2.3 CHG-* ≠ queue status（队列／状态机字汇）

| 维度 | CHG-* | queue status |
|------|-------|----------------|
| **回答的问题** | 变更内容性质？ | 票／工件在流程中**到哪一步**？ |
| **典型载体** | 本表 | `90_run_queue.md` → `TODO\|DOING\|BLOCKED\|DONE`；G7-1 终态（另册） |
| **例子** | `CHG-QUEUE-STRUCT` | 某行 `Status: DOING` |
| **关系** | 改 `90` **栏位 schema 或增删行** → `CHG-QUEUE-STRUCT`；仅改本票 `Status/Notes` → 多为 **meta**，主 class 仍看正文产物 | `DONE` 只表示票关闭，**不**表示 CHG 类别 |

**禁止混用**：不得用 `CHG-TODO`／`CHG-DONE`；不得把 repo 既有 `phase`／`master_status` 里程碑旗标并入 CHG 枚举（见 §5）。

---

## 3. 主枚举表（CHG-*）

| ID | 简述 | 对齐线索（索引，非穷举） |
|----|------|---------------------------|
| **CHG-GOV-DOC** | 治理／工作流 **说明性文档** 增量 | OPS `doc_clarification`；合約 Rule 3 最小触及 |
| **CHG-IMPL-SINGLE** | **单文件** 实现／配置（非制度 tier） | OPS `bugfix`；TEST-SUB-001 |
| **CHG-IMPL-CROSS** | **多文件／多模块** 实现，仍在任务明示边界内 | coordinator 多路径；Rule 8 不接管他人 core |
| **CHG-QUEUE-STRUCT** | **队列／依赖／编排骨架** 结构变更 | E1-*；`90`／`02`／`03` 结构 |
| **CHG-OBS-ONLY** | **只读可观测** 输出，不改变行为契约 | checker `[RISK]`；Monitoring Graph L0 |
| **CHG-TEST-ONLY** | **仅测试／验收脚本**（不含生产逻辑） | 专测票；checker 跑 unittest |
| **CHG-RULEBOOK** | **权威规则 tier** 正文 | 憲法／合約／AGENTS／`.cursor/rules`／路由表 |
| **CHG-HIGH-RISK** | 触 **§7 禁区类型** 或等效高风险 **意图** | Rule 5；guard `scope_change`；Z-* |

---

## 4. 各类定义

### CHG-GOV-DOC

**定义**  
在任务卡 **明示路径** 内，增补或修订 **说明性、可移植** 的治理／工作流文档（含 `workflow_v2/10_governance/*` 模块规格、runbook 澄清段落、Work Report 模板说明），**不**升格为全 repo 权威规则 tier（见 CHG-RULEBOOK）。

**典型范围**

- 单模块、单文件 md 正文（如 `G6_scope_control/10_change_classes.md`）。  
- `workflow_upgrade/` 下 runbook **按章澄清**（OPS `doc_clarification` 范式）。  
- checker 在 `99_latest_status.md` 或票 **Notes** 写风险摘要（正文仍属 OBS 交付物，**施工 intent** 若只改 Notes 可标 OBS；若 worker 写模块规格则为本类）。

**非典型但允许的例子**

- 同一票内 **两个** `workflow_v2` 子目录的 md，但均为「写规格、无 production 代码」（总控拆票更佳）。  
- 在 `brief.md`／`notes.md`（任务明示）追加接口需求说明。

**明确不属于它的情形**

- 改 `AGENTS.md`、`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`.cursor/rules` → **CHG-RULEBOOK**。  
- 改 `core/`、暗部 `core/`、subagents 实现 → **CHG-IMPL-***。  
- 只跑测试、只读盘点无正文 → **CHG-TEST-ONLY**／**CHG-OBS-ONLY**。  
- 未授权扩路径的 `scope_change` → 先 **CHG-HIGH-RISK** 意图，guard 未 `allow` 前不得标为本类「已完成」。

---

### CHG-IMPL-SINGLE

**定义**  
**单一** `primary_target` 内的实现或配置变更（战車根或暗部 **单文件**），逻辑变更局限在该文件及其直接测试，**不**改制度 tier、**不**改队列结构。

**典型范围**

- 单文件 bugfix（如 `subagents/context_routing.py` 一处 regex）。  
- 单模块内单文件配置（任务卡列死路径）。

**非典型但允许的例子**

- 同文件内多 hunk，但仍 **一个** `primary_target`。  
- 附带 **仅** 更新该文件头部注释（无行为变更）— 主 class 仍为本类；若全票仅注释且任务写明「无行为变更」，可改标 **CHG-GOV-DOC** 并 Notes 说明。

**明确不属于它的情形**

- 第二生产文件（含同目录另一模块）→ **CHG-IMPL-CROSS** 或拆票。  
- 改 tests **且** 改 production → 主 class 取 production 侧（常为 **CROSS** 或 **SINGLE** 以 production 为准）；**仅 tests** → **CHG-TEST-ONLY**。  
- 触憲法 §7 类型 → **CHG-HIGH-RISK**（可与 IMPL 并存为 secondary，见 §5.2）。

---

### CHG-IMPL-CROSS

**定义**  
**多个** 实现路径或 **多个逻辑模块** 的协同变更，仍在任务卡／尚書省 **明示边界** 内，且遵守合約 Rule 8（不接管他人 `core`／workspace 三件套）。

**典型范围**

- 协调层列出的多文件 patch（如 API + adapter + 单测，路径均在 `allowed_paths`）。  
- `workflow_v2` 内 **两文件** 但一为 `10_*.md` 一为 `20_*.md` **且** 含 production 引用示例代码于暗部 — 若票授权暗部+战車根实现，主 class 为本类。

**非典型但允许的例子**

- 「一主文件 + 仅 generated lock／快照」若任务卡授权。  
- 跨 **战車根** 与 **暗部** 各 **一** 文件，共 2 文件，均在票面。

**明确不属于它的情形**

- 单文件 → **CHG-IMPL-SINGLE**。  
- 改制度档 + 实现捆绑（TEST-SUB-003 反例）→ **CHG-HIGH-RISK** + guard `stop_work`；不得用本类洗白 scope。  
- 仅文档多文件、无代码 → **CHG-GOV-DOC**。  
- coordinator `out_of_scope` 所列路径若被实施 → 非本类合法完成态，属越权。

---

### CHG-QUEUE-STRUCT

**定义**  
变更 **任务编排骨架**：run queue schema、依赖图、并行规则、Wave／模块表结构，以及 **增删改队列行／依赖边**（非单票 Status 翻转）。

**典型范围**

- `workflow_v2/90_run_queue.md` 栏位说明、新票行、Depends 调整（**orchestrator**／E1 票）。  
- `workflow_v2/02_dependency_map.md`、`03_parallel_execution_rules.md` 结构修订。  
- `workflow_v2/00_master_plan.md` 的 Wave／模块表（总控）。

**非典型但允许的例子**

- 批量将多票 `Depends` 对齐（仍属编排，非施工正文）。  
- 在 `90` 新增 **Future** 占位段（无正文规格）。

**明确不属于它的情形**

- 施工 worker **仅** 改本票一行 `Status`／`Notes` → **不是** 本类（meta 操作；主 class 看 Output File 正文类型）。  
- 写 G6/G7/G8/G10 **模块规格正文** → **CHG-GOV-DOC**（除非票面标题明确为 E1 队列票）。  
- 改 `04_Workflows/00_Agent_Work_Progress.md` 战报 append → **CHG-OBS-ONLY** 或战报制度（非 v2 队列）；勿标本类。  
- 改 `task_routing_table.json` → **CHG-RULEBOOK**（路由权威表）。

---

### CHG-OBS-ONLY

**定义**  
**只读** 产生的可观测输出：不改变生产行为契约、不写实现、不写规则 tier 正文；用于盘点、侧车、摘要、风险标记。

**典型范围**

- checker **只读** 扫描后在 `99_latest_status.md` 或 Notes 写 `[RISK]`（`03_parallel_execution_rules.md` §4）。  
- H 线 Monitoring Graph **L0** 暴露（`monitoring_graph` 键、ibridge sidecar）；**不** 改 selector／answer。  
- governance-guard 仅输出 `verdict` JSON、无施工。  
- OPS `governance_test` 仅 guard 裁決、不派 worker。

**非典型但允许的例子**

- 开发环境 HTTP 双闸門下 **额外** 返回 observability 字段（票面授权、默认关）。  
- 只读 `route_task` 解读写进战报（无表结构变更）。

**明确不属于它的情形**

- 任何 production `core`／subagents **逻辑** 修改 → **CHG-IMPL-***。  
- 写模块规格 md 正文 → **CHG-GOV-DOC**。  
- 专跑 unittest 且改测试代码 → **CHG-TEST-ONLY**。  
- 把 observability 升格为 selector 输入（L1+）→ **CHG-HIGH-RISK** 意图 + 另票；**不是** 本类。

---

### CHG-TEST-ONLY

**定义**  
变更 **仅** 落在测试、验收脚本、fixture 或 CI 用例（路径在任务 `allowed_paths` 内），**不** 改 production 实现或规则 tier。

**典型范围**

- 新增／修改 `tests.test_*` 单测。  
- checker-reviewer 票：只跑验证命令、无 repo diff（无文件变更 — 见 §5.3）。

**非典型但允许的例子**

- 测试内 **读** 生产模块（import 被测对象）而不改生产文件。  
- 快照／golden 文件仅服务于测试。

**明确不属于它的情形**

- 测试 + 生产同票 → 主 class **不以** 本类为准；取 **CHG-IMPL-SINGLE** 或 **CHG-IMPL-CROSS**。  
- 只读盘点无 diff → **CHG-OBS-ONLY**。  
- 改 smoke runbook **制度** 条文 → **CHG-GOV-DOC** 或 **CHG-RULEBOOK**（视文件 tier）。

---

### CHG-RULEBOOK

**定义**  
修改 **全 repo 或全域流程** 的权威规则与路由制度正文，改变「谁可做、何物禁、如何派工」的 **规范层**（非单次任务说明）。

**典型范围**

- `HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`AGENTS.md`。  
- `.cursor/rules`、`.cursor/agents/*.md`（subagent 制度）。  
- `04_Workflows/TASK_ROUTING.md`、`task_routing_table.json`、`OPS_CYCLE.md` **制度表**、 `Master_Map.json` 逻辑结构。  
- `workflow_v2/10_governance/G10_*` 的 **AI 边界／禁止盲信** 正文（G10 票）。

**非典型但允许的例子**

- 单票 **仅** 改 `DISPATCH_GUIDE.md` 派工表。  
- 澄清 **合約** 附录（仍属规则 tier）。

**明确不属于它的情形**

- 仅 `workflow_v2` 某模块 **首版规格**（从无正文到有正文）→ 施工票常用 **CHG-GOV-DOC**；若票面写「升格规则」且经尚書省授权，才标本类。  
- runbook **操作步骤** 澄清（不改变 AGENTS／合約）→ **CHG-GOV-DOC**。  
- 实现代码 → **CHG-IMPL-***。  
- 触 §7 但未授权 → **CHG-HIGH-RISK**，guard `deny`／`stop_work`。

---

### CHG-HIGH-RISK

**定义**  
变更 **意图** 触及憲法 **§7 禁区类型**（Z-ENV、Z-VENV-TREE、Z-RUNTIME-CP、Z-ORCH-DESTRUCT、Z-DARK-OPS、Z-HQ-LIQUIDATION、Z-HQ-ENV-EDIT），或等同高风险：**scope 扩张**、跨制度档捆绑、DarkOps `assignable=false` 仍要施工、路径与 `Master_Map.json` 冲突、合約 Rule 5／12 场景。

**典型范围**

- `governance-guard` 输入 `proposal_type: scope_change`。  
- 提案改 `.env`、venv 树、checkpoint、暗部 `dark_ops`、清算脚本。  
- TEST-SUB-003 类：单票捆 AGENTS + 合約 + rules + selector + 暗部。  
- 未授权改暗部根（DarkOps Blocked）。

**非典型但允许的例子**

- **尚書省已授权** 的禁区工单：class 仍标本类，Notes 须 `override` 留痕指针（动作见 G6-2）。  
- 仅 **审查** 高风险提案、无 diff → secondary 标本类 + 主 **CHG-OBS-ONLY**。

**明确不属于它的情形**

- 仅在 §7 **类型** 意义上 **只读** 对照、无改意图 → **CHG-OBS-ONLY**。  
- 普通单文件 bugfix 无禁区 → **CHG-IMPL-SINGLE**。  
- 队列加一行 TODO → **CHG-QUEUE-STRUCT**（非高风险充分条件）。  
- `assignable=false` **本身** 不是 class；是否高风险看 **拟改路径** 是否触 Z-*。

---

## 5. 组合、映射与禁止合并

### 5.1 主 class 与 secondary class

- 每票 **必须** 有且仅有 **一个** `primary_change_class`（CHG-*）。  
- 若同时触及多性质，允许 `secondary_change_class: []`，但须在 Notes 说明 **为何未拆票**。  
- 常见组合：  
  - `CHG-IMPL-CROSS` + secondary `CHG-HIGH-RISK`（跨模块且近禁区）  
  - `CHG-OBS-ONLY` + secondary `CHG-HIGH-RISK`（guard 审查票）

### 5.2 与 OPS_CYCLE 工单类型（映射，非等同）

| OPS / 协作类型 | 常见 primary CHG-* | 说明 |
|----------------|-------------------|------|
| `bugfix`（单档） | `CHG-IMPL-SINGLE` | 直派 worker 前仍可能需 guard |
| `doc_clarification` | `CHG-GOV-DOC` | 若改 AGENTS／合約 → 改 `CHG-RULEBOOK` |
| `governance_test` | `CHG-OBS-ONLY` 或 `CHG-HIGH-RISK` | 仅 guard 时主 OBS；提案触禁区时主 HIGH-RISK |

### 5.3 与 governance-guard `proposal_type`

| proposal_type | 与 CHG-* 关系 |
|---------------|----------------|
| `plan` | 不单独映射；计划内各 phase 对应不同 CHG |
| `patch_intent` | 多为 IMPL-* 或 GOV-DOC |
| `scope_change` | **强烈建议** primary `CHG-HIGH-RISK` 或 `CHG-IMPL-CROSS`；**不是** deny type |
| `route_request` | 解读 `assignable` 属 gate；若拟改路由表 → `CHG-RULEBOOK` |

### 5.4 与 TASK_ROUTING（索引）

- `route_task()` 的 `assignable`／`block_reason` → **gate**，用于判断是否可派 `implementation-worker`。  
- `task_type`（如 `hq.governance`、`dark.infra`）→ **派工域**，不替代 CHG-*。  
- `allowed_worker: none` → **deny 侧**，不在 CHG 枚举中重复。

### 5.5 禁止与外部 phase／status 合并

以下 **不得** 并入 CHG-* 枚举：

| 外部字汇 | 所属模块 |
|----------|----------|
| `TODO`／`DOING`／`BLOCKED`／`DONE` | `90_run_queue.md`、G7 |
| `assignable`／`blocked`／`phase_gates` | TASK_ROUTING、憲法 §5.2 |
| `allow`／`deny`／`stop_work`／`conditional` | governance-guard |
| `phase1_verify`、Progress 里程碑编号 | Conditions／Progress |
| `accepted`／`accepted_with_gaps` | checker 验收口语（入战报，非 CHG） |

---

## 6. 选型决策（简图）

```text
拟变更是否只读、无规格/实现正文？
  是 → CHG-OBS-ONLY
  否 ↓
是否仅测试路径？
  是 → CHG-TEST-ONLY
  否 ↓
是否只改 90/02/03/00 队列骨架？
  是 → CHG-QUEUE-STRUCT
  否 ↓
是否触 §7 类型或 scope_change／跨制度捆绑？
  是 → CHG-HIGH-RISK（再判 IMPL／RULEBOOK 作 secondary）
  否 ↓
是否权威规则 tier？
  是 → CHG-RULEBOOK
  否 ↓
是否仅 workflow/runbook 说明性文档？
  是 → CHG-GOV-DOC
  否 ↓
实现文件数量？
  1 → CHG-IMPL-SINGLE
  ≥2 → CHG-IMPL-CROSS
```

---

## 7. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G6-1 初版：8 类 CHG-* + 命名边界 §2 |

---

## 8. 下游引用契约（给 G6-2 / G10）

- **G6-2** `20_allowed_actions.md` **必须** 以本章 ID 为表主键；不得重新定义 class 含义。  
- **G10-2** 写「禁止情境」时 **引用** `CHG-*`，写 **deny 理由** 用 `rule_ref`／情境叙述，**不** 新建 `CHG-DENY-*。  
- **G7** 状态名与 CHG 正交；exit 条件可写「requires change_class X recorded」，但不得用 CHG 代替状态名。
