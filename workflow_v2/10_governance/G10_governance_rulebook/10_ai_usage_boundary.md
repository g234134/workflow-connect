# G10-1 — AI Usage Boundary（v0.1）

> **票号**：G10-1  
> **上游**：`G6_scope_control/10_change_classes.md`（G6-1）、`20_allowed_actions.md`（G6-2）  
> **下游**：`20_no_blind_trust.md`（G10-2，**本档不覆盖**「禁止盲信」情境清单）  
> **权威位阶**：尚書省当次指令 ＞ 憲法 ＞ 工程合約 ＞ **G6（CHG／ACT）** ＞ 本档 ＞ 任务卡 brief  
> **本文件定义**：在 v2 导入工作流中，**AI（含 Cursor worker／父 agent 施工面）宜参与什么、不宜主导什么、何时必须有人类或制度角色把关**，以及 **哪些权不能下放给 worker**。  
> **本文件不定义**：CHG-* 枚举（G6-1）、每类允许动作表（G6-2）、guard `verdict`、queue `Status`、IMP-* 状态迁移（G7）、完整 release gate（G8-5／G7 `IMP-RELEASE-*`）、「禁止盲信 AI 输出」情境表（G10-2）。

---

## 1. 用途与读法

1. **给派工方**：在标 `primary_change_class` 后，判断可否派 `implementation-worker` 或仅派 researcher／guard／checker。  
2. **给施工 AI**：在 G6-2 允许的 **ACT-*** 集合内施工；越界则升级 class 或 `ACT-HANDOFF`，不得自行扩权。  
3. **给 G7／G8**：`IMP-AI-READY` 起对照本档「宜参与」；`IMP-RISK-VALIDATION` 起叠加 G10-2（占位至 G10-2 定稿）。  
4. **与 repo 母法对齐**：行为红线与角色边界以 `AGENTS.md`、`ENGINEERING_CONTRACT.md`、`HARNESS_CONSTITUTION.md` 为准；本档为 **workflow_v2 可移植摘要**，不取代母法全文。

**读者顺序**：G6-1 选型 → G6-2 动作天花板 → **本档**（AI 参与边界）→ G10-2（输出信任边界，另册）。

---

## 2. 命名边界（引用 G6，不重定义）

| 字汇 | 归属 | 本档用法 |
|------|------|----------|
| **CHG-*** | G6-1 | 仅 **引用**；描述「变更性质」 |
| **ACT-*** | G6-2 | 仅 **引用**；描述「允许动词」 |
| **guard `verdict`** | governance-guard／G10-2 | 本档写「须 guard／须 allow 后施工」，**不**定义 `deny` 枚举 |
| **queue `Status`** | `90_run_queue.md`、G7 | 本档写「标 DONE 前须 checker」，**不**把 `DONE` 当 CHG |
| **IMP-*** | G7-1 | 本档索引态门槛，**不**新增状态名 |
| **owner** | G7 entry、`G8` ART-* | 指 **人类制度角色**（`pm`／`engineering`／`governance`／`qa`／`release`），**不是** Cursor subagent 文件名 |

**禁止**：在本档新增 `CHG-AI-*`、把「不宜 AI 主导」写成新的 change class。

---

## 3. AI 适合参与的工作（宜）

> **原则**：在票面 **`allowed_paths`** 与 G6-2 对应行 **允许角色** 内，AI 可承担 **起草、检索、增量实现、验证执行、风险摘要**；交付认定仍须 **checker／owner**（见 §5–§6）。

### 3.1 按活动类型（与 CHG 正交）

| 活动 | 典型执行者 | 说明 |
|------|------------|------|
| **读档与索引** | 任意 AI（ACT-READ） | runbook、`Master_Map.json` 索引、brief／notes、tests 先例；**不**贴 env 原文 |
| **计划与分解** | coordinator／orchestrator（ACT-PLAN） | phase、`allowed_paths`、验收标准；**无 diff** |
| **只读盘点** | checker／guard（ACT-RISK-NOTE、ACT-GUARD） | `[RISK]`、`verdict` JSON；主 class 常为 **CHG-OBS-ONLY** |
| **说明性文档起草** | worker（CHG-GOV-DOC） | `workflow_v2` 模块规格、runbook 按章澄清；路径须在票面集合内 |
| **规则档修订（已放行）** | worker（CHG-RULEBOOK） | **仅** guard `allow`／`conditional` 满足后；含 G10 正文票 |
| **单文件实现** | worker（CHG-IMPL-SINGLE） | `primary_target` 单文件；近 §7 时须 guard **R→Y** |
| **多文件实现（票面授权）** | worker（CHG-IMPL-CROSS） | 须 guard **Y** + checker **Y**；禁止制度+实现捆绑 |
| **专测增量** | worker（CHG-TEST-ONLY） | 仅测试路径；同票不得改 production |
| **队列 meta** | worker | 仅 **本施工票** `Status`／`Notes`（ACT-QUEUE-META）；**不**改 `90` 骨架 |
| **队列结构** | orchestrator（CHG-QUEUE-STRUCT） | `00`／`02`／`03`／`90` 结构；worker **不可**主交付 |
| **验证命令执行** | checker（ACT-VERIFY） | unittest、runner、`_ops_cycle.py validate-report`；证据入 Work Report §4 |
| **H 线上下文组装** | 实现路径经 `build_rooted_context` | 见 `AGENTS.md` H 线；Monitoring Graph **仅 L0** observability |

### 3.2 按 CHG 快速索引（细节以 G6-2 §4 为准）

| CHG-* | AI 宜参与（摘要） |
|-------|-------------------|
| CHG-GOV-DOC | 起草 md 规格；≥2 文件或触规则 tier → guard **R** 或升级 |
| CHG-IMPL-SINGLE | 单文件 PATCH；第二文件 → 升级 CROSS |
| CHG-IMPL-CROSS | 多文件 PATCH；**必** guard + checker |
| CHG-QUEUE-STRUCT | **仅** orchestrator；AI worker 不做结构主编 |
| CHG-OBS-ONLY | guard／checker 主交付；无 diff 盘点可直 DONE（G6-2） |
| CHG-TEST-ONLY | 测试 PATCH + **必** ACT-VERIFY |
| CHG-RULEBOOK | guard **allow** 后 worker PATCH；**必** checker |
| CHG-HIGH-RISK | guard 审查为主；worker **仅** post-allow 且路径逐条限定 |

### 3.3 与 Cursor Subagents 对齐（索引）

| Subagent | 宜用情境 |
|----------|----------|
| **repo-researcher** | 路径不明、契约／runner 对照、并行搜证 |
| **implementation-worker** | §3.2 中 worker 行 + 直派条件（`DISPATCH_GUIDE.md` §4） |
| **governance-guard** | §5.1 必 guard 触发 |
| **checker-reviewer** | §5.2 必 checker；宣稱可交付前 |
| **coordinator** | 多 phase、scope 分解；**不** ACT-PATCH 模块正文 |

---

## 4. AI 不宜直接主导的工作（不宜）

> **不宜** = AI **不得**作为唯一决策方推进；须 **尚書省**、**orchestrator**、或 **G7 owner 角色** 明示裁決或留痕。  
> **不等于**「禁止 AI 起草」：可先出草案，再由人／guard／checker 收口。

| # | 情境 | 理由（索引） | 典型处置 |
|---|------|--------------|----------|
| 1 | **发布／上线裁決** | G7 `IMP-RELEASE-DECISION`→`IMP-RELEASED`；G8-5 **ART-REL-*** | owner=`release`；AI 可填草案，**不可**自批 publish |
| 2 | **里程碑编号与 Progress 正文改写** | 憲法 §6.2、合約 C29；Conditions／Progress **仅末尾追加** | Governance／尚書省；worker 不得重排里程碑 |
| 3 | **`master_status`／`handoff` 写入** | 憲法 §6.3、W0 C18 | **Governance 独占**；AI 仅可提案 diff |
| 4 | **§7 禁区类型施工意图** | 憲法 §7.1 Z-*；CHG-HIGH-RISK | guard **Y** + 尚書省 override；`stop_work` → 停工 |
| 5 | **scope 扩张**（diff ⊄ `allowed_paths`） | G6-2 §5.2；合約 Rule 3 | 升级 class 或拆票；禁止静默加路径 |
| 6 | **制度档 + 实现捆绑** | TEST-SUB-003；G6-2 CHG-IMPL-CROSS | guard `stop_work` + **ACT-HANDOFF** |
| 7 | **路由／DarkOps gate 绕过** | `assignable:false` 仍改暗部 | **blocked**；换票或解禁 |
| 8 | **他人 `core`／他人 workspace 三件套** | 合約 Rule 8、憲法 §9 | notes 记需求；**不**接管实现 |
| 9 | **队列全局结构** | CHG-QUEUE-STRUCT | **仅** orchestrator |
| 10 | **自标验收通过／关票** | 合約 Rule 11、GATE-3.5.1 | **必** checker；implementation-worker 不可终审 |
| 11 | **K-2 prod 流量切换** | `docs/k2_deployment_governance.md` | 须尚書省批文；AI 不得自订 rollout |
| 12 | **Monitoring Graph L1+／selector 升格** | `AGENTS.md` L0–L2 表 | **handoff** 另票 HIGH-RISK |

---

## 5. 必须 guard／checker／owner 的情形

### 5.1 必须 governance-guard（G6-2「必 guard = Y」）

| 触发 | 关联 CHG-* |
|------|------------|
| **CHG-IMPL-CROSS** | 主行 **Y** |
| **CHG-RULEBOOK** | 主行 **Y** |
| **CHG-HIGH-RISK** | 主行 **Y** |
| 拟改 `AGENTS`／憲法／合約／`.cursor/rules`／`task_routing_table.json` | 常 **CHG-RULEBOOK** 或升级自 GOV-DOC |
| `proposal_type: scope_change` | 主 **CHG-HIGH-RISK** |
| 制度 + 实现捆绑 | guard `stop_work` |

**AI 规则**：`verdict` 为 `deny`／`stop_work` 时 **零 ACT-PATCH**；`conditional` 未满足同 **blocked**。

### 5.2 必须 checker-reviewer（G6-2「必 checker = Y」）

| 触发 | 说明 |
|------|------|
| 全部 CHG-* **交付票**（除 §5.3 例外） | 标 `90` **DONE** 前须有 ACT-VERIFY 证据 |
| 宣稱「可交付」 | 合約 GATE-3.5.1；Work Report §4 |
| **CHG-IMPL-***／GOV-DOC／TEST-ONLY／RULEBOOK** | 主表 **Y** |
| guard 仅输出、无 diff 的审查票 | **仍建议** checker 写 `[RISK]` |

**AI 规则**：worker 回传 `ok: true` **不**等于 checker `accepted`；父 agent 不得跳过 checker 关票（除非尚書省书面豁免并 Notes 留痕）。

### 5.3 可直接 DONE 的例外（仍非「AI 自决」）

| 条件 | 谁标 DONE |
|------|----------|
| **CHG-QUEUE-STRUCT** 且 orchestrator E1 票 | orchestrator |
| **CHG-OBS-ONLY** 且无 repo diff | checker／guard 交付后 |

### 5.4 必须 owner（G7 entry 主责角色）

| 关口 | owner | AI 边界 |
|------|-------|---------|
| `IMP-SCOPE-DRAFT` | `pm` | AI 可草拟 **ART-PM-SCOPE**，**不可**单方面关闭开放问题 |
| `IMP-AI-READY` | `engineering` | AI 施工前须有 **ART-ENG-CTX** + `primary_change_class` |
| `IMP-RISK-VALIDATION` | `governance` | AI 可产 WR／风险对照；**不可**替代 governance sign-off |
| `IMP-QA-READY` | `qa` | checker 执行；**主责≠施工 worker**（Rule 11 精神） |
| `IMP-RELEASE-DECISION` | `release` | AI **不可**批 publish |
| `IMP-REWORK` | `engineering`（主） | 须 `rework_record`；自 QA 失败进入须 checker 确认计划 |

---

## 6. 不得下放给 worker 的权（写入／审批／handoff）

> **worker** = `implementation-worker` 及同等写权限的 Cursor 施工 subagent；**不含** guard／checker（只读裁決）。

### 6.1 写入权（AI worker 不得独自完成）

| 对象 | 制度依据 | worker |
|------|----------|--------|
| `project_status/master_status.md` | 憲法 §6.3 | **禁止** |
| `project_status/handoff.md` | 同上 | **禁止** |
| `04_Workflows/00_Agent_Work_Conditions.md` 正文覆写 | 憲法 §6.2 | **禁止**（仅末尾追加由授权角色） |
| `04_Workflows/00_Agent_Work_Progress.md` 覆写／重排 | 憲法 §6.2 | **禁止** |
| `task_routing_table.json`、HQ 路由权威 | G6-2 → CHG-RULEBOOK | **禁止**（无 guard allow） |
| 憲法／合約／`AGENTS.md`／`.cursor/rules` | CHG-RULEBOOK | **禁止**（无 guard allow） |
| `90_run_queue.md` **结构**（栏位、Depends 批量） | CHG-QUEUE-STRUCT | **禁止** |
| 他人 `core`、他人 workspace 三件套 | 合約 Rule 8 | **禁止** |
| §7 类型路径（env、venv 树、checkpoint 等） | 憲法 §7 | **禁止**（无 override） |
| `.env` 或金鑰原文输出 | `AGENTS.md` 红线 | **禁止** |

**允许**：本票 `90` 行 **Status／Notes**（ACT-QUEUE-META）；票面 `allowed_paths` 内 PATCH。

### 6.2 审批权（AI worker 不得行使）

| 审批项 | 行使方 |
|--------|--------|
| guard **`allow`** 前的制度／HIGH-RISK 施工 | governance-guard → 尚書省 |
| checker **`accepted`／`accepted_with_gaps`** | checker-reviewer |
| **`IMP-RELEASED`** 发布批准 | `release` owner + **ART-REL-***（G8-5） |
| 憲法 §7 **override** 有效性 | 尚書省 + Progress／notes 留痕 |
| DarkOps **解禁**后继续暗部施工 | 尚書省另票 |
| Wave 1 模块「已定稿」宣告 | 尚書省／CHK-W1；worker **禁止** |
| K-2 **prod** 流量策略 | 尚書省 playbook 批文 |

### 6.3 handoff 权（移交裁決）

| 行为 | 谁可发起 | worker 限制 |
|------|----------|-------------|
| **ACT-HANDOFF** 至尚書省 | guard、coordinator、checker | worker **可请求**，**不可**假定已批准而继续 PATCH |
| 拆票（TEST-SUB-003 类） | 尚書省 | worker 遇捆绑须 **停工** 交 guard |
| 跨模块接口需求 | 对应 module owner | worker 仅 notes，**不**越权实现 |
| **override** 后施工 | 尚書省书面 + 留痕指针 | 无留痕 **禁止** PATCH |

---

## 7. 如何引用 CHG-* 作为治理边界（操作步骤）

```text
1) 任务卡声明 primary_change_class（G6-1 §5.1）
      ↓
2) 打开 G6-2 §4 对应行 → 得到：允许角色、路径模式、必 guard/checker、升级条件
      ↓
3) 本档 §3–§4：判断 AI 宜参与 vs 不宜主导（不新增 CHG）
      ↓
4) 若触 §5.1：先 ACT-GUARD，再视 verdict 决定是否 ACT-PATCH
      ↓
5) 施工 → IMP-REVIEW-READY（WR 草案）→ IMP-RISK-VALIDATION（+ G10-2 占位）
      ↓
6) 必 checker：ACT-VERIFY → 方可 queue DONE / 宣稱可交付
```

**组合 class**：secondary `CHG-HIGH-RISK` 时，以 **更严** 行的 guard／checker 为准（G6-2 §5.1 升级后重套表）。

**与 OPS 工单类型**：`bugfix`→IMPL-SINGLE、`doc_clarification`→GOV-DOC 等 **映射**见 G6-1 §5.2；AI 派工前先映射再查 G6-2。

**与 G7 态**：`IMP-AI-READY` entry 要求 `primary_change_class` 已填且拟执行 ACT ⊆ G6-2 允许集（`20_entry_conditions.md` §4、§7）。

**禁止用法**：

- 用 CHG 名代替 `deny` 理由 → 用 `rule_ref` + 情境（G10-2）。  
- 用 CHG 名代替 `IMP-*` 状态 → 用 G7-1。  
- 用「本档不宜」新建 `CHG-DENY-*` → **禁止**（G6-1 §2.1）。

---

## 8. 与母法语义对齐（索引）

| 来源 | 本档承接点 |
|------|------------|
| **AGENTS.md** | 接战／封存；Subagents 派工三原则；H 线 `context_entry`；Monitoring L0 only；红线 |
| **ENGINEERING_CONTRACT** | 四流派最低覆盖；Rule 3 最小触及、Rule 8 边界、Rule 11 验证后宣稱、Rule 12 override 留痕 |
| **HARNESS_CONSTITUTION** | §7 禁区**类型**；§6.2–§6.3 黑板与 status／handoff；§5.2 施工授权 |
| **_PORTABLE_CORE_INDEX** | C08 全局禁止、C18 写入独占、C25–C26 四流派与 12-rule、C29 里程碑位阶 |
| **DISPATCH_GUIDE.md** | §4 直派、§5 必 guard、§6 必 checker |
| **G7-2** | `IMP-AI-READY`／`IMP-RISK-VALIDATION` entry；G10-2 占位 |
| **G8-3／G8-4** | ART-ENG-WR、ART-QA-REV；验收载体，非本档重定义 |

---

## 9. 风险与 TODO（本票）

| ID | 项 | 严重度 | 处理 |
|----|-----|--------|------|
| T1 | G10-2 未定稿，`IMP-RISK-VALIDATION` 仍引用占位 | 中 | G10-2 票闭合后更新 G7-3 交叉引用 |
| T2 | G8-5 **ART-REL-*** 未定稿，发布权 §6.2 仅索引 | 中 | G8-5 后补 ART ID |
| T3 | CHK-W1 未跑，与 G6/G7 交叉引用未独立验证 | 低 | Wave 1 checker 只读盘点 |
| T4 | 本档 **不** 含 CI／gate 实现 | 低 | Enforcement 另开 Wave 2+ |

---

## 10. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G10-1 v0.1 初版：AI 宜／不宜、guard/checker/owner、三权限制、CHG 引用步骤 |
