# G6-2 — Allowed Actions per CHG-*

> **票号**：G6-2  
> **上游**：`10_change_classes.md`（G6-1）— **class 含义与选型仅以 G6-1 为准**  
> **下游**：G10-1／G10-2（引用本表动作列，不重定义 CHG）；G7 entry／exit（可写「requires allowed_actions satisfied」）；Cursor `DISPATCH_GUIDE.md` 派工对齐  
> **本文件定义**：给定 `primary_change_class`（CHG-*）时，**谁可做什么**（角色 × 动作 × 路径模式），**不**定义 class（G6-1）、**不**定义 guard `verdict` 枚举（G10／guard JSON）、**不**定义 queue `Status`（G7／`90_run_queue.md`）。

---

## 1. 用途与读法

1. **主键**：下表每行 **CHG-*** 与 G6-1 §3 一一对应；不得新增 class。  
2. **动作**：§2 的 **ACT-*** 动词表；禁止把 `allow`／`deny`／`TODO`／`DONE` 当作动作主键。  
3. **角色**：v2 三角色（`03_parallel_execution_rules.md`）+ Cursor Subagents 别名（括号内）。  
4. **直接 DONE**：指施工票在 **`90_run_queue.md` 标 `DONE`** 前是否可跳过 checker；**不等于** artifact 主线态或 guard 放行。  
5. **任务卡字段（建议）**：`primary_change_class`、`allowed_paths`、`primary_target`（IMPL 票）、`guard_verdict_id`（若适用）。

---

## 2. 动作词表（ACT-*）

| ACT-ID | 含义 | 典型执行者 |
|--------|------|------------|
| **ACT-READ** | 只读源档／runbook／地图索引 | 任意角色 |
| **ACT-PLAN** | 分解 phase、列 `allowed_paths`、验收标准（无 diff） | orchestrator、coordinator |
| **ACT-PATCH** | 按票面路径写入正文或代码 diff | worker（implementation-worker） |
| **ACT-VERIFY** | 跑 runner／unittest／`_ops_cycle.py validate-report` | checker（checker-reviewer）、父 agent |
| **ACT-GUARD** | 输出 `verdict` JSON，不施工 | guard（governance-guard） |
| **ACT-QUEUE-META** | 仅改 **本施工票** 一行 `Status`／`Notes` | worker |
| **ACT-QUEUE-STRUCT** | 改 `90`／`02`／`03`／`00` 骨架或批量依赖 | orchestrator |
| **ACT-RISK-NOTE** | 只读盘点后写 `[RISK]` 摘要 | checker |
| **ACT-HANDOFF** | 向尚書省／总控提交裁決或拆票建议（无擅自施工） | guard、coordinator、checker |

**禁止**：用 ACT 名承载 `verdict` 或 queue 状态；裁決仍用 guard 输出字段，队列仍用 G7 字汇。

---

## 3. 角色与 Subagent 对齐

| v2 角色 | Cursor Subagent（若用） | 默认可执行 ACT |
|---------|-------------------------|----------------|
| **orchestrator** | 父 agent／coordinator（只读计划） | ACT-PLAN、ACT-QUEUE-STRUCT、ACT-READ；**不** ACT-PATCH 模块正文 |
| **worker** | implementation-worker | ACT-PATCH、ACT-QUEUE-META、ACT-READ |
| **checker** | checker-reviewer | ACT-READ、ACT-VERIFY、ACT-RISK-NOTE |
| **guard** | governance-guard | ACT-READ、ACT-GUARD、ACT-HANDOFF |

---

## 4. 主表：CHG-* → Allowed Actions

> **列说明**  
> - **允许角色**：可发起或完成该 class 下 **主要交付** 的角色；`·` 表示辅助／条件可参与。  
> - **路径模式**：票面 `allowed_paths` 须 **落入** 模式子集；超出即 scope 扩张 → §5。  
> - **必 guard / 必 checker**：`Y` 必过、`R` 推荐、`N` 可免（须 Notes 明示豁免理由）。  
> - **直接 DONE**：`N` = 标 `DONE` 前须有 checker 或等效 ACT-VERIFY 证据（合約 Rule 11）。

| CHG-* | 允许角色（主交付） | 允许路径模式（票面须 ⊆） | 必 guard | 必 checker | 直接 DONE | 升级 / blocked / handoff |
|-------|-------------------|---------------------------|----------|------------|-----------|---------------------------|
| **CHG-GOV-DOC** | worker · orchestrator（仅 E1 编排票） | `workflow_v2/10_governance/<G*>/**`（**不含** G10 正文成品）；`workflow_upgrade/**` 按章澄清；任务明示 `brief.md`／`notes.md`；**单票≤票面列出的 md 路径集合** | R（≥2 文件或边界不清） | Y | N | 拟改 `AGENTS`／憲法／合約／`.cursor/rules`／`task_routing_table.json` → **升级** `CHG-RULEBOOK` + guard **Y**；未授权扩路径 → **blocked** + `ACT-HANDOFF` |
| **CHG-IMPL-SINGLE** | worker | 票面 **`primary_target` 单文件**；可选 **同文件** 直连测试（票面列出）；战車根 `core/`、`subagents/`、暗部 `core/`（**单文件**，域与 `task_type` 一致） | R（近 §7 或 `dark.*`） | Y | N | 第二生产文件 → **升级** `CHG-IMPL-CROSS` 或拆票；触 §7 → secondary `CHG-HIGH-RISK` + guard **Y**；`assignable=false` 仍要改暗部 → **blocked** |
| **CHG-IMPL-CROSS** | worker · coordinator（多 phase） | 票面 **`allowed_paths` 显式多文件列表**（建议 ≤6 路径）；跨战車根+暗部须票面授权且各域 **≤1–2 文件**；**禁止** 他人 `core`／他人 workspace 三件套（合約 Rule 8） | **Y** | Y | N | 制度档+实现捆绑 → guard `stop_work` + **handoff** 尚書省拆票；`out_of_scope` 被实施 → **blocked**；路由 `assignable=false` → **blocked** 暗部施工 |
| **CHG-QUEUE-STRUCT** | orchestrator | `workflow_v2/00_master_plan.md`；`workflow_v2/02_dependency_map.md`；`workflow_v2/03_parallel_execution_rules.md`；`workflow_v2/90_run_queue.md`（**结构**：栏位、新行、Depends）；`workflow_v2/99_latest_status.md`（结构段） | N（改路由表则见 RULEBOOK） | R（CHK 盘点） | **Y**（仅 orchestrator E1 票且 Notes 写清） | worker **仅** ACT-QUEUE-META **不** 标本类；改 `task_routing_table.json` → **升级** `CHG-RULEBOOK`；依赖环 → orchestrator 修 `02` 后 **handoff** |
| **CHG-OBS-ONLY** | checker · guard · orchestrator | `workflow_v2/99_latest_status.md`（§4 风险表）；**本票** `90` Notes（`[RISK]`）；只读 CLI 输出写入战报；H 线 L0 观测字段（**票面+env 授权**，不改 selector） | R（审查提案时）；提案触 §7 → **Y** | Y（主交付）；纯 guard 无 diff → checker **Y** | **Y**（无 repo diff、仅 ACT-RISK-NOTE／ACT-GUARD 时） | 任何 production 逻辑修改 → **升级** IMPL-*；observability 升格 L1+ → **handoff** 尚書省另票 `CHG-HIGH-RISK` |
| **CHG-TEST-ONLY** | worker | `tests/**`、`**/test_*.py`、`**/tests/**`（票面列举）；测试 fixture／golden（仅服务测试） | N（改生产则否） | **Y**（须 ACT-VERIFY） | N | 同票改 production → **升级** IMPL-SINGLE／CROSS；改 smoke **制度 tier** → GOV-DOC 或 RULEBOOK |
| **CHG-RULEBOOK** | worker（guard **allow** 后）· guard（ACT-GUARD 交付） | `04_Workflows/HARNESS_CONSTITUTION.md`；`04_Workflows/ENGINEERING_CONTRACT.md`；`AGENTS.md`；`.cursor/rules/**`；`.cursor/agents/**`；`04_Workflows/TASK_ROUTING.md`；`04_Workflows/task_routing_table.json`；`Master_Map.json`（逻辑结构）；`workflow_v2/10_governance/G10_governance_rulebook/**`（G10 票） | **Y** | **Y** | N | guard `deny`／`stop_work` → **blocked**，`allowed_worker=none`；`conditional` 未满足 → **blocked**；须 **handoff** 尚書省 + Progress／notes override 留痕（Rule 12） |
| **CHG-HIGH-RISK** | guard（主）· worker（**仅** post-allow）· orchestrator | **无默认写路径**；`affected_paths` 由提案列出，且须尚書省 **`override`** 或 guard `allow`／`conditional` 逐条限定 | **Y** | **Y**（若有 diff）；仅审查无 diff 同 OBS | N | `scope_change` 未裁決前 **blocked** 一切 ACT-PATCH；`stop_work` → **handoff** 尚書省；DarkOps blocked → **禁止** 派 implementation-worker；路径与地图冲突 → **blocked** |

---

## 5. 例外与升级规则

### 5.1 Class 升级（重标 `primary_change_class`，不拆 ACT 表）

| 从 | 升级到 | 触发 |
|----|--------|------|
| CHG-GOV-DOC | CHG-RULEBOOK | 拟改权威规则 tier（G6-1 §4 CHG-GOV-DOC） |
| CHG-GOV-DOC | CHG-IMPL-* | 出现 production／subagents 代码 diff |
| CHG-IMPL-SINGLE | CHG-IMPL-CROSS | 第二生产文件或第二逻辑模块 |
| CHG-IMPL-* | CHG-HIGH-RISK | 触憲法 §7 类型、scope 扩张、制度+实现捆绑 |
| CHG-QUEUE-STRUCT | CHG-RULEBOOK | 改 `task_routing_table.json` 或 HQ 路由权威 |
| CHG-OBS-ONLY | CHG-GOV-DOC | checker／worker 需写模块规格正文 |
| CHG-TEST-ONLY | CHG-IMPL-* | 同票修改 production |

升级后 **重新套用** §4 目标行；已执行的 guard verdict 若路径集变化则 **作废**，须重跑 ACT-GUARD。

### 5.2 Blocked（停工，不得 ACT-PATCH）

| 条件 | 谁标记 | 恢复 |
|------|--------|------|
| guard `verdict: deny` 或 `stop_work` | guard → 父 agent Notes | 尚書省改票／拆票／书面 override |
| `_route_task` → `assignable: false` 且意图暗部施工 | guard ACT-GUARD | 换 `task_type`、解禁 DarkOps 票，或取消施工 |
| diff ⊄ `allowed_paths` 或超出 §4 路径模式 | checker 或 guard | 缩 scope 或升级 class + 重审 |
| 依赖未 `DONE`（`90` Depends） | worker → `BLOCKED` | 前置票 `DONE` |
| 同文件双 chat 施工 | orchestrator | 保留一方，另一方 `BLOCKED` |

`blocked` 为 **queue Status**（G7），**不是** CHG-* 名。

### 5.3 Handoff（移交，未必 blocked）

| 情境 | 移交对象 | 产出 |
|------|----------|------|
| TEST-SUB-003 类多制度+实现捆绑 | 尚書省 | 拆票 + 各票 CHG-* |
| CHG-HIGH-RISK 需禁区操作 | 尚書省 | override 批文 + 留痕指针 |
| G6/G10 术语对账 | orchestrator | 对账票或 Notes 冻结表（checker 只标 `[RISK]`） |
| implementation 需他人 `core` | 对应模块 owner | notes 记接口需求（Rule 8） |

### 5.4 与 governance-guard `proposal_type`

| proposal_type | 建议先标 CHG-* | guard | worker 开工条件 |
|---------------|----------------|-------|-----------------|
| `plan` | 按 phase 分解各 CHG | R | 各 phase 满足对应行 |
| `patch_intent` | IMPL-* 或 GOV-DOC | R–Y | `allow` + `allowed_worker` 含 implementation-worker |
| `scope_change` | **CHG-HIGH-RISK**（主） | **Y** | `allow` 或满足 `conditions`；否则 **blocked** |
| `route_request` | OBS 或 RULEBOOK | R | 只解读 gate；改表 → RULEBOOK 行 |

### 5.5 与 OPS_CYCLE 工单类型（动作层）

| OPS 类型 | 典型流水线（ACT） | §4 主行 |
|----------|-------------------|---------|
| `bugfix` | ACT-READ → [ACT-GUARD] → ACT-PATCH → ACT-VERIFY | CHG-IMPL-SINGLE |
| `doc_clarification` | ACT-READ → [ACT-GUARD] → ACT-PATCH → ACT-VERIFY | CHG-GOV-DOC（升 RULEBOOK 则换行） |
| `governance_test` | ACT-GUARD [→ ACT-RISK-NOTE] | CHG-OBS-ONLY 或 CHG-HIGH-RISK |

### 5.6 `90` 本票 Status／Notes（meta）

| 操作 | 归类 | 允许角色 |
|------|------|----------|
| 本票 `TODO`→`DOING`→`DONE` | **queue meta**（非 CHG） | worker（施工票）；orchestrator（E1 票） |
| 仅改 Notes 验收要点 | ACT-QUEUE-META | worker |

标 `DONE` 时 **主 class** 仍由 **Output File 正文类型** 决定（G6-1 §2.3），不得以 meta 操作改 class。

---

## 6. 必 guard / 必 checker 汇总

| 必 guard（Y） | 必 checker（Y） | 可直接 DONE（例外） |
|-------------|---------------|---------------------|
| CHG-IMPL-CROSS | 除纯 orchestrator 的 CHG-QUEUE-STRUCT 外，**全部 CHG-*** | CHG-QUEUE-STRUCT（orchestrator E1）；CHG-OBS-ONLY（无 diff 盘点票） |
| CHG-RULEBOOK | | |
| CHG-HIGH-RISK | | |
| CHG-HIGH-RISK 审查型（无 diff）同 OBS | | |

**推荐 guard（R）**：CHG-GOV-DOC（多文件）、CHG-IMPL-SINGLE（近禁区／`dark.*`）、CHG-OBS-ONLY（仅当提案可能升 HIGH-RISK）。

**checker 豁免**（须父 agent + Notes 明示）：纯 `ACT-PLAN` coordinator 票；纯 `ACT-GUARD` 且 `verdict` 已交付无 diff — **仍建议** 由 checker 写 `[RISK]` 摘要。

---

## 7. 下游引用契约（G10 / G7 / 派工）

- **G10-1**：写 AI usage boundary 时 **引用** §4 列「允许角色／路径」，写禁止行为时用 **情境 + `rule_ref`**，不新建 CHG。  
- **G10-2**：写「禁止盲信」情境时 **引用** CHG-* + 本表「必 checker／必 guard」列，**不** 用 CHG 名表示 `deny`。  
- **G7**：entry／exit 可写「`primary_change_class` ∈ {…} 且 guard `verdict=allow`（若 Y）」；**不得** 用 CHG 代替 `IMP-*` 状态名。  
- **DISPATCH_GUIDE §4–§6**：直派 worker 条件 ⊂ **CHG-IMPL-SINGLE** 且 guard N/R + 路径单文件；必过 guard ⊂ **CHG-RULEBOOK**、**CHG-HIGH-RISK**、**CHG-IMPL-CROSS**。

---

## 8. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G6-2 初版：8×CHG-* allowed actions 表 + §5 例外／升级 |
