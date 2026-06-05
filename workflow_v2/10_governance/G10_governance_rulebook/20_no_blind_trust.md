# G10-2 — No Blind Trust（禁止盲信 · v0.1）

> **票号**：G10-2  
> **上游**：`10_ai_usage_boundary.md`（G10-1）；`G6_scope_control/10_change_classes.md`（G6-1）、`20_allowed_actions.md`（G6-2）；`workflow_upgrade/01_context-entry/30_ignore_deny_rules.md`（A-3）；`.cursor/agents/governance-guard.md`、`.cursor/agents/checker-reviewer.md`  
> **下游**：G7 `IMP-RISK-VALIDATION` exit（`30_exit_and_transitions.md` §3）；G8 **ART-GOV-RISK**（`G8_artifact_contract/60_gov_risk.md`）、**ART-QA-REV**／**ART-REL-*** blocker 对账；CHK-W1 只读盘点  
> **权威位阶**：尚書省当次指令 ＞ 憲法 ＞ 工程合約 ＞ **G6（CHG／ACT）** ＞ G10-1 ＞ **本档** ＞ 任务卡 brief  
> **本文件定义**：在 v2 导入工作流中，**哪些输出不能直接当作事实、验收、发布或 owner 裁決依据**；哪些 guard／checker／observability／eval 结果**仅作辅助证据**；哪些情境**必须人类或制度 owner 确认**；以及 **deny／stop_work／rejected／blocked** 出现后**绝对禁止**的后续动作。  
> **本文件不定义**：CHG-* 枚举（G6-1）、每类允许动作表（G6-2）、guard／checker `verdict` 枚举、queue `Status`、IMP-* 状态迁移（G7）、完整 release gate（G8-5）、artifact 字段表（G8）、AI **宜参与／不宜主导** 边界（G10-1 §3–§4）。

---

## 1. 范围与目的

### 1.1 与 G10-1 的分工

| 维度 | G10-1（AI Usage Boundary） | G10-2（本档） |
|------|------------------------------|---------------|
| **核心问题** | AI **能不能做**、**谁必须把关** | 某输出 **能不能直接信**、**信到什么程度** |
| **典型读者** | 派工方、施工 AI | guard、checker、**IMP-RISK-VALIDATION** owner、父 agent |
| **与 CHG 关系** | 索引 CHG 下宜／不宜 | 索引 CHG 下**证据等级**与**盲信禁区** |
| **重叠处理** | §4「不宜主导」= **禁止 AI 单方决策** | 本档 **不重复** §4 表；仅 **交叉引用** + 补「输出信任」细则 |

**读者顺序**：G6-1 → G6-2 → G10-1 → **本档** → G7 entry／exit → G8 artifact。

### 1.2 用途

1. **IMP-RISK-VALIDATION**：对照 §2–§3 清单，确认无「盲信 AI／侧车／局部证据」即跳关（G7-3 §3 **IMP-RISK-VALIDATION** exit ②）。  
2. **guard／checker**：裁決时用 **`rule_ref` + 本档节号** 说明「不可盲信对象」，**不**用 CHG 名代替 `deny`（G6-1 §2.1）。  
3. **父 agent**：合并 subagent JSON 时，区分 **辅助证据** vs **可关票证据**（合約 Rule 11）。  
4. **H 线 runtime**：observability／deny metadata **不得**被误读为 QA 通过或 release 批准（对齐 A-3 §2、AGENTS Monitoring L0）。  
5. **实现层 QA checklist**：checker 可勾选步骤与 **ART-QA-REV** 推荐字段 → `workflow_v2/20_pilot/W2-2_tooling_notes.md` §4–§4.1；契约裁决指引 → `G8_artifact_contract/40_qa.md` §5（**不**改变本节 NBT-* 规则语义）。

### 1.3 命名边界（引用 G6，不重定义）

| 字汇 | 归属 | 本档用法 |
|------|------|----------|
| **CHG-*** | G6-1 | 标注**情境关联 class**；**不**表示裁決结果 |
| **ACT-*** | G6-2 | 标注**禁止或必须**的动作；**不**承载 `verdict` |
| **guard `verdict`** | governance-guard JSON | `allow`／`conditional`／`deny`／`stop_work` — 本档写**盲信禁区与停工后禁止动作**，**不**扩枚举 |
| **checker `verdict`** | ART-QA-REV | `accepted`／`accepted_with_gaps`／`rejected`／`blocked` — 本档写**不可盲信与跳关禁止** |
| **queue `Status`** | `90_run_queue.md` | **`DONE`／`BLOCKED` 不是验收结论**（G7-2 §3） |
| **deny type** | A-3 §5、`metadata.deny` | Context Entry **内容／行为**禁止类；**≠** guard `deny` 但 **同工单 spirit** |
| **gate** | `_route_task` `assignable` | **路由门控**；`assignable:true` **≠** 可跳过 guard／checker |

**禁止**：新建 `CHG-DENY-*`、把 `TODO`／`DONE` 当作 trust tier、把 queue 态当作 IMP 态。

---

## 2. 不可盲信对象

> **原则**：下列对象 **可进入** Work Report、战报、侧车 JSON 或 prompt **作为线索**；**不可单独**支撑：事实认定、scope 合法性、验收通过、IMP 前进、发布批准、override 有效性。  
> **证据等级**：**E0** = 仅线索；**E1** = 须交叉验证；**E2** = 可支撑 checker／owner **在完整证据链下** 裁決（仍 **不** 替代 owner）。

### 2.1 AI 施工与协作输出

| ID | 对象 | 默认等级 | 不能直接当作 | 关联 CHG-*（G6-1） | 索引 |
|----|------|----------|----------------|-------------------|------|
| **NBT-AI-01** | implementation-worker **`ok: true`**／自然语言「已完成」 | E0 | checker `accepted`；queue `DONE`；IMP exit | 全部交付类 CHG-* | G10-1 §5.2；合約 Rule 11 |
| **NBT-AI-02** | worker **Work Report** 自评（§2 skeleton／§3 placeholder 为空或未测却称完成） | E0 | DoD 通过；**ART-ENG-DOD** 四键为真 | CHG-IMPL-*、CHG-GOV-DOC、CHG-RULEBOOK | G8-3；checker `dod_checklist` |
| **NBT-AI-03** | **repo-researcher** 路径／契约结论（未附父 agent Read 或源档引用） | E1 | `allowed_paths` 合法性；「文件不存在／存在」终局认定 | 任意（调研前置） | DISPATCH_GUIDE §3 |
| **NBT-AI-04** | **coordinator** phase 计划、`allowed_paths` 草案 | E1 | 已批准的 scope；guard `allow` 等价物 | ACT-PLAN | G10-1 §6.3 handoff |
| **NBT-AI-05** | 父 agent **合并摘要**（压缩 subagent JSON 后丢失 `evidence`／`violations`） | E0 | 风险 sign-off；省略 checker 必填字段 | — | 合約 Rule 4 |
| **NBT-AI-06** | AI 生成的 **风险对照表**／「已对照 G10」勾选（无 command／artifact 指针） | E0 | **IMP-RISK-VALIDATION** exit ② | CHG-OBS-ONLY 交付物若仅 AI 自述 | G7-3 §3 RISK exit |
| **NBT-AI-07** | **RAG retrieve hits**／模型引用的 chunk 内容 | E1 | 憲法／合約／runbook **条文事实**；禁区分型 | — | A-3 `rag_hit_with_secrets`；须源档 Read |
| **NBT-AI-08** | 模型 **推断** 的 Progress／里程碑／`master_status` 状态 | E0 | 当前战史或里程碑完成度 | — | 憲法 §6.2–§6.3 |

### 2.2 Guard／Checker／派工裁決（辅助证据，非 owner 替代）

| ID | 对象 | 默认等级 | 不能直接当作 | 须谁补裁決 | 索引 |
|----|------|----------|----------------|------------|------|
| **NBT-GC-01** | guard **`allow`**（proposal 已变：路径集／class／DarkOps 态与裁決时不一致） | E0 | 当前 scope 仍合法 | **重跑 ACT-GUARD** | G6-2 §5.1 升级作废 verdict |
| **NBT-GC-02** | guard **`conditional`** 文本（条件未逐条验证） | E0 | ACT-PATCH 许可 | guard 或尚書省确认条件满足 | G6-2 §4 RULEBOOK／HIGH-RISK 行 |
| **NBT-GC-03** | checker **`accepted_with_gaps`**（未读 `gaps[]`） | E1 | 无 gap 交付；IMP-QA exit | **qa owner**／尚書省对 gaps | G8-4 §4.1 |
| **NBT-GC-04** | checker **`[RISK]`** 摘要（`99_latest_status` §4） | E1 | 模块定稿；CHK-W1 替代 | orchestrator／尚書省 | G6-2 CHG-OBS-ONLY |
| **NBT-GC-05** | **ART-DES-REV** `approved_with_gaps`（gaps 未写入 WR §3） | E0 | **IMP-RISK-VALIDATION** 入口 | design owner | G8-2 §4.2 blocker |
| **NBT-GC-06** | guard **`route_task.assignable: true`** | E1 | 暗部施工合法；§7 禁区可碰 | 仍须 CHG 行 + guard（若 Y） | G6-1 §2.2 gate ≠ class |
| **NBT-GC-07** | checker 产出的 **battle_report_json_draft**（未跑 `validate-report`） | E1 | OPS 封存完成 | checker `exit_ok` + validate | G8-4 §4.3 |

### 2.3 Observability／Monitoring／Eval（侧车，非业务 contract）

| ID | 对象 | 默认等级 | 不能直接当作 | 索引 |
|----|------|----------|----------------|------|
| **NBT-OBS-01** | **`monitoring_graph`**／`ibridge_v0.monitoring_graph`（L0） | E0 | selector／answer 正确性；SLO 达标；release 批准 | AGENTS Monitoring Graph L0；**禁止 L1+ 盲信** |
| **NBT-OBS-02** | **`monitoring_executor`**／`_monitoring_executor_result`（含 stub／fallback） | E0 | Infra 已接管；monitoring API 健康 | AGENTS O-2；`executor=v0.1-stub` |
| **NBT-OBS-03** | **`metadata.deny.observability`**（deny 闸审计） | E1 | prompt 无 deny 类内容；**GateRunner 通过** 的充分条件 | A-3 §7；须 pre/post gate 断言 |
| **NBT-OBS-04** | **`metadata.trim`／`trimming_applied`** | E0 | 上下文完整＝任务所需源已读 | A-3 §2.1 ignore |
| **NBT-OBS-05** | **eval 样本／离线指标**（未脱敏、无方法论、无对照 baseline） | E0 | prod 质量 sign-off；K-2 主答案切换 | A-3 `eval_sample_raw`；`docs/k2_deployment_governance.md` |
| **NBT-OBS-06** | **Smoke 子集通过**（未覆盖票面 acceptance_commands 全集） | E1 | **ART-QA-REV** `accepted` | G8-4 §4.4；Rule 11 |
| **NBT-OBS-07** | HTTP **`expose_monitoring_graph`** 响应中的 observability 字段 | E0 | 客户 SLA；业务逻辑依赖字段存在 | runbook §6.7 Observability 闸門 |

### 2.4 路由、队列与局部证据

| ID | 对象 | 默认等级 | 不能直接当作 | 索引 |
|----|------|----------|----------------|------|
| **NBT-RT-01** | **`90_run_queue.md` 本票 `DONE`** | E0 | IMP 前进；发布执行；artifact 定稿 | G7-2 §3；G8-5 **ART-REL-DEC** blocker |
| **NBT-RT-02** | **`assignable: false`** 的 **解读**（无 guard JSON） | E1 | 「绝对不能做」的终局（可能可换 task_type） | 须 ACT-GUARD 或尚書省 |
| **NBT-RT-03** | **单条** `acceptance_commands` 通过（其余未跑） | E0 | checker `accepted: true` | checker-reviewer §Completion |
| **NBT-RT-04** | **部分 diff**／父 agent 未 Read 的路径变更 | E0 | `scope_check.within_ticket` | G8-4 scope_check |
| **NBT-RT-05** | **queue `Notes`** 中的 worker 自述验收 | E0 | ACT-VERIFY 证据 | G6-2 ACT-QUEUE-META |
| **NBT-RT-06** | **`_ops_cycle.py checklist`** 通过（无本票 diff 验证） | E1 | 本票可交付 | 须叠加本票 acceptance |

### 2.5 汇总：永远不能单独作为 release／IMP exit 依据

以下 **任一项单独出现** 时，**不得** 支撑 `IMP-QA-READY` → `IMP-RELEASE-DECISION`、`IMP-RELEASE-DECISION` → `IMP-RELEASED`，或等价「可发布」声明：

1. NBT-AI-01、NBT-AI-02、NBT-RT-01、NBT-RT-03、NBT-RT-05  
2. NBT-OBS-01–05（ observability／eval ** alone**）  
3. guard `allow` 若同时存在未关闭的 **NBT-GC-01**／**conditional** 未满足  
4. checker `accepted` 若 **NBT-GC-03** gaps 未 owner 处理且票面要求零 gap  

**完整 release 证据链** 仍 **唯一** 权威在 G8 **ART-REL-*** + G7-3；本档 **不写** gate 阈值。

---

## 3. 必须人工确认的情境

> **人工** = 尚書省、G7 **entry owner 角色**（`pm`／`engineering`／`governance`／`qa`／`release`）、或制度授权的 **Governance** 写入角色 — **不是** Cursor subagent 文件名（G10-1 §2）。  
> AI **可起草** 对照表或 artifact 草案；**不可** 单方完成下列确认。

| ID | 情境 | 确认方 | 留痕载体 | 与 G10-1 关系 |
|----|------|--------|----------|---------------|
| **NBT-H-01** | **憲法 §7** 禁区类型施工（含 override） | 尚書省 + guard `allow`／`conditional` | **ART-GOV-RISK** `override_ref`（首选）；Progress／notes **末尾**；**fallback**：WR §7 | G10-1 §4 #4、§6.2 override |
| **NBT-H-02** | **`IMP-RISK-VALIDATION` exit**（风险清单 closed／accepted） | **governance** owner + guard 记录 | **ART-GOV-RISK** `status: signed`（首选）；guard `verdict_id`；**fallback**：WR §4+§7 | G10-1 §5.4；G7-3 RISK exit |
| **NBT-H-03** | **`IMP-RELEASE-DECISION` → `IMP-RELEASED`** | **release** owner | **ART-REL-DEC**（G8-5） | G10-1 §4 #1、§6.2 |
| **NBT-H-04** | checker **`accepted_with_gaps`** 是否可进入 release 轨道 | **尚書省** 或 qa owner | Notes／**ART-QA-REV** `gaps` | G8-4 §4.1 |
| **NBT-H-05** | **scope 扩张**（diff ⊄ `allowed_paths`）继续施工 | 尚書省（拆票／升级 class） | 新票 CHG-*；guard 重审 | G10-1 §4 #5 |
| **NBT-H-06** | **DarkOps 解禁**后继续暗部施工 | 尚書省另票 | override + 新 task_type | G10-1 §6.2 |
| **NBT-H-07** | **K-2 prod 流量**／主答案切换 | 尚書省 playbook 批文 | 部署治理文档；**非** AI 阈值 | G10-1 §4 #11；合約 REF-9.7 |
| **NBT-H-08** | **Monitoring Graph L1+**／selector 升格 | 尚書省 + **CHG-HIGH-RISK** 票 | handoff；runbook §6.8 | AGENTS L0–L2 |
| **NBT-H-09** | **里程碑／Conditions／Progress** 正文变更 | Governance／尚書省 | **仅末尾追加** | G10-1 §4 #2、§6.1 |
| **NBT-H-10** | **`master_status`／`handoff` 写入** | Governance 独占 | 对应 artifact | G10-1 §4 #3 |
| **NBT-H-11** | guard **`stop_work`** 后恢复施工 | 尚書省拆票／override | 新 proposal + 新 guard | TEST-SUB-003 |
| **NBT-H-12** | **IMP-REWORK** 自 QA 失败后的 **`rework_target`** | 失败关口 owner + **checker**（若自 QA 进入） | `rework_record` | G7-3 §3 REWORK |
| **NBT-H-13** | **design review `rejected`** 后的方向变更 | design owner | **ART-DES-REV**；→ REWORK | G8-2 |
| **NBT-H-14** | **Context deny 命中**后的「仍继续注入／施工」 | 尚書省 | deny `message` + Progress | A-3 §2.2；憲法 §7.2 |

### 3.1 按 CHG-* 的快速索引（须人工确认触发，细节见 G6-2 §4）

| CHG-* | 典型须 NBT-H-* |
|-------|-----------------|
| CHG-RULEBOOK | H-01（若近 §7）、H-02、guard allow 前 **零** PATCH |
| CHG-HIGH-RISK | H-01、H-06、H-11 |
| CHG-IMPL-CROSS | H-05（scope）、H-02（bundle 风险） |
| CHG-OBS-ONLY | H-02（若盘点结论上升为 scope 变更） |
| CHG-QUEUE-STRUCT | H-09（若动 Conditions／Progress 误触） |

---

## 4. deny／stop_work／rejected／blocked 后的禁止动作

> 本节 **不** 定义 verdict 枚举；列出裁決 **一旦成立** 时，AI／父 agent／worker **绝对不得** 继续的动作。  
> **`blocked`** 含：guard `deny`／`stop_work`、checker `blocked`、G6-2 §5.2 停工条件、queue `Status: BLOCKED`、IMP 态内 blocker（G7-2 §3）。

### 4.1 裁決类型 → 禁止动作矩阵

| 裁決来源 | 值 | **禁止**（零例外，除非尚書省书面 override + 留痕） | 允许 |
|----------|-----|-----------------------------------------------------|------|
| **guard** | `deny` | ACT-PATCH；派 implementation-worker 施工；标 queue **DONE**；宣称 IMP 前进 | ACT-HANDOFF；ACT-GUARD 重审（新 proposal）；ACT-READ |
| **guard** | `stop_work` | 同上 + **协调层继续拆同一捆绑 scope** | **ACT-HANDOFF** 尚書省拆票；guard 只读 |
| **guard** | `conditional`（未满足） | ACT-PATCH；视同 **blocked** | 满足 `conditions[]` 后 **重跑 guard** |
| **checker** | `rejected` | 标 **DONE**；IMP-QA exit；**ART-REL-DEC** approve | → **IMP-REWORK** 路径；新 implementation 票 |
| **checker** | `blocked` | 标 `accepted`；隐瞒未跑命令 | 写 Progress 阻塞；ACT-HANDOFF |
| **design** | **ART-DES-REV** `rejected` | → **IMP-RISK-VALIDATION** | REWORK → SPEC／AI |
| **release** | **ART-REL-DEC** `deny` | → **IMP-RELEASED** | REWORK → QA 或 RISK |
| **route gate** | `assignable: false` + 暗部施工意图 | ACT-PATCH 暗部；绕过 `_route_task` | 换 task_type、解禁票、取消施工 |
| **Context deny** | A-3 命中／`metadata.deny` blocked | 将 deny 内容注入 prompt；**ignore 裁掉 deny 类** | 脱敏／拒绝／停工（憲法 §7.2） |
| **queue** | `BLOCKED` | ACT-PATCH（本票）；改 Depends 外票 | 待 Depends **DONE** 或 orchestrator 解阻 |

### 4.2 共通禁止（所有上表「禁止」行叠加）

1. **不得** 用 **NBT-AI-*** 或 **NBT-OBS-*** 替代上表裁決。  
2. **不得** 用 **CHG-* 改名** 绕过（例：将 `stop_work` 改标 CHG-GOV-DOC 继续 PATCH — G6-1 §2.1）。  
3. **不得** 用 **queue `DONE`** 覆盖 checker `rejected`／guard `deny`。  
4. **不得** 在 **无 Rule 12 留痕** 下 override 继续施工（NBT-H-01、H-11、H-14）。  
5. **不得** 让 **implementation-worker** 兼任 guard `allow` 或 checker `accepted`（G10-1 §5–§6）。

### 4.3 恢复施工的最小路径（索引 G6-2 §5.2–§5.3）

```text
deny / stop_work / rejected / blocked
  → ACT-HANDOFF（或 Progress 阻塞条）
  → 尚書省：拆票 / 缩 scope / 书面 override / 新 guard proposal
  → [若 scope 或 class 变] 重跑 ACT-GUARD
  → [若已 PATCH] 新 implementation 票 + ACT-VERIFY
  → checker accepted* → 方可 queue DONE / IMP 前进
```

---

## 5. 引用关系（CHG-*、G10-1、G7／G8）

### 5.1 与 G6 的操作步骤（不重定义 CHG／ACT）

```text
1) 任务卡 primary_change_class（G6-1）
      ↓
2) G6-2 §4：必 guard／checker、blocked 条件
      ↓
3) G10-1 §3–§4：AI 宜参与 vs 不宜主导
      ↓
4) 本档 §2：拟采纳的证据是否落入 NBT-* 盲信区
      ↓
5) 本档 §3：是否触发 NBT-H-* 须人工确认
      ↓
6) 若 §4 裁決成立 → 停工矩阵；否则 IMP-AI-READY → … → IMP-RISK-VALIDATION
      ↓
7) IMP-RISK-VALIDATION exit：对照 §2.5 + §3 + guard allow + **ART-GOV-RISK**（首选）；**fallback**：WR §4+§7（仅 GOV artifact 缺失且票面授权）
      ↓
8) IMP-QA-READY：checker ART-QA-REV（G8-4）；禁止 §2.1 NBT-AI-01/02 跳关
```

**组合 class**：secondary **CHG-HIGH-RISK** 时，§3 **NBT-H-01**、§4 停工规则 **从严**（G6-2 §5.1）。

### 5.2 与 G10-1 的交叉引用

| G10-1 节 | 本档承接 |
|----------|----------|
| §4 不宜主导 #1–#12 | §3 NBT-H-* 人工确认；**不**重复不宜表 |
| §5 guard／checker 必须 | §2.2 不可盲信 guard/checker **输出本身** |
| §6 三权限制 | §4 禁止用 AI 输出 **行使** 审批权 |
| §7 CHG 引用步骤 | §5.1 扩展 **信任链** 步骤 |

### 5.3 与 G7 IMP-* 的挂钩

| IMP-* | 本档用法 |
|-------|----------|
| `IMP-AI-READY` | 施工前 **不得** 仅信 NBT-AI-04 计划；须有 **ART-ENG-CTX** + class |
| `IMP-REVIEW-READY` | **不得** 仅信 NBT-AI-02 WR 自评进入 RISK |
| **`IMP-RISK-VALIDATION`** | **主消费档**：§2.5 + §3 + §4；exit ② 产出／读取 **ART-GOV-RISK**（G8-6）；本档为 normative 对照源 |
| `IMP-QA-READY` | checker **不得** 盲信 NBT-AI-01；须 **ART-QA-EVD** |
| `IMP-RELEASE-DECISION` | **不得** 盲信 NBT-OBS-*、NBT-RT-01 |
| `IMP-REWORK` | §4 `rejected`／`deny` 后的 **合法** 回退 |

### 5.4 与 G8 ART-* 的挂钩

| ART-* | 本档 blocker 对齐 |
|-------|-------------------|
| **ART-ENG-WR** §2–§3 | NBT-AI-02；honest skeleton／placeholder |
| **ART-GOV-RISK** | **IMP-RISK-VALIDATION** 主 artifact；`nbt_validation` ↔ §6.3；`must_stop_work` ↔ §4 |
| **ART-ENG-WR** §7 | NBT-H-01 override 留痕（**fallback** 当 GOV artifact 缺失） |
| **ART-ENG-WR** §4 | 验证证据（**非** GOV sign-off 唯一依据） |
| **ART-DES-REV** | NBT-GC-05；NBT-H-13 |
| **ART-QA-REV** | §2.2、§4.1 checker 行；NBT-GC-03；可选 `tooling_checks` → W2-2 §4.1、G8-4 §5 |
| **ART-REL-DEC** | NBT-RT-01；NBT-OBS-* 不能作 approve 依据 |

### 5.5 与 deny／observability 治理（A-3、H 线）

| 来源 | 本档对齐 |
|------|----------|
| A-3 **deny** vs **ignore** | §2.3 NBT-OBS-03/04；**deny ＞ ignore**（L1） |
| `context_entry_contract.md` §2.4 `metadata.deny` | 观测 **≠** 通过；须 GateRunner 断言 |
| AGENTS Monitoring **L0 only** | §2.3 NBT-OBS-01/02；§3 NBT-H-08 |
| `30_ignore_deny_rules.md` §7 coverage | **不得** 宣称 runtime 已覆盖全表即 **NBT-H-14** 可免 |

### 5.6 与 Cursor Subagents（ enforcement 索引）

| Subagent | 本档节 |
|----------|--------|
| governance-guard | §2.2、§4.1 guard 行；输出 `violations[].rule_ref` 可引 **`G10-2§NBT-*`** |
| checker-reviewer | §2.1–§2.2、§4.1 checker 行 |
| implementation-worker | §2.1 **NBT-AI-01/02** |
| repo-researcher | **NBT-AI-03** |
| coordinator | **NBT-AI-04** |

**禁止用法**（延续 G10-1 §7、G6-1 §2）：

- 用 `CHG-IMPL-SINGLE` **解释** guard `deny` → 用 **`rule_ref` + NBT-ID**。  
- 用 checker `accepted` **解释** release approve → 用 **ART-REL-DEC** + release owner。  
- 用 **`DONE`** **解释** IMP archived → 用 G7 + G8 battle report。

---

## 6. 例外与升级路径

### 6.1 尚書省书面 override（Rule 12）

| 条件 | 允许突破 | 仍 **不可** 突破 |
|------|----------|------------------|
| 书面 override + Progress／notes **末尾**留痕 | §4 部分停工（按批文范围） | NBT-OBS-01/02 作 SLA；checker `rejected` **改** `accepted` 无新证据 |
| 单次 checker 豁免（G10-1 §5.2） | 跳过 checker **须 Notes 明示** | Rule 11 永久豁免 **禁止** |

### 6.2 升级路径（不新造 class）

| 触发 | 动作 | 引用 |
|------|------|------|
| 盲信区证据被当作关票依据 | checker **`rejected`** + `rule_ref: G10-2§NBT-*` | §4.1 |
| scope 外 PATCH | 升级 **CHG-IMPL-CROSS**／**CHG-HIGH-RISK** + guard | G6-2 §5.1 |
| observability 升格参与决策 | **ACT-HANDOFF** + **NBT-H-08** | CHG-HIGH-RISK |
| 术语／重复定义争议 | **CHG-OBS-ONLY** 对账票；checker `[RISK]` | 99 §4 R2 |
| enforcement 自动化 | Wave 2+ 另票；本档 **不** 含 CI | G10-1 T4 |

### 6.3 IMP-RISK-VALIDATION 最小对照清单（v0.1）

施工方向 **进入 QA 前**，governance owner 或 checker **只读**勾选；**首选**写入 **ART-GOV-RISK** 字段 `nbt_validation`（`checklist_id: G10-2-§6.3-v0.1`，字段定义见 `G8_artifact_contract/60_gov_risk.md` §4.6）。

| item_key（ART-GOV-RISK） | 勾选项（本档语义） |
|--------------------------|-------------------|
| `no_blind_trust_release_basis` | 无 **§2.5** 单列证据作为唯一 release／QA 依据 |
| `nbt_h_confirmed_or_na` | **§3** 所列情境均已 **NBT-H-*** owner 留痕或 **不适用** |
| `no_active_denial` | 无未关闭 **§4.1** guard `deny`／`stop_work`／checker `rejected`／`blocked` |
| `g6_guard_checker_met` | G6-2 必 guard／checker 已满足（**不** 用本清单 **代替** ACT-VERIFY） |
| `context_deny_handled` | Context **deny** 命中已按 **NBT-H-14** 处理 |

**读取优先级**：

1. **ART-GOV-RISK** 存在 → `nbt_validation.all_required` 须为 **true** 且 `status: signed` 方可 exit。  
2. **GOV artifact 缺失** → **fallback**：WR §4+§7 人工对照上表 + `nbt_validation.fallback_used: true`（票面授权）；gate 输出 **`require-human-override`**（见 `20_pilot/W2-3_minimal_gate_design.md` §4）。

**未全勾**／`all_required: false`：**不得** exit **IMP-RISK-VALIDATION**（G7-3 §3）。

---

## 7. 风险与 TODO（本票）

| ID | 项 | 严重度 | 处理 |
|----|-----|--------|------|
| T1 | G7-3 正文仍含「待 G10-2」占位句 | 低 | CHK-W1 或 G7 对账票替换为 **本档 §5.3** 节号 |
| ~~T2~~ | ~~**ART-GOV-RISK** artifact 未在 G8 定稿~~ | — | **已关闭**（G8-6 `60_gov_risk.md` · W2-3） |
| T3 | deny engine v1 **未** 覆盖 A-3 全表（§7） | 中 | **NBT-OBS-03** 仍须 GateRunner 断言；勿盲信 observability |
| T4 | R2「G6 与 G10 重复」— 本档 **引用** CHG，不新建 deny class | 低 | CHK-W1 关闭 R2 |
| T5 | 本档 **不含** CI／自动 enforcement | 低 | 设计 → `20_pilot/W2-3_minimal_gate_design.md`；实现 → W2-3-MINIMAL-GATE-*／W3 |
| T6 | 案卷 **ART-GOV-RISK** 实例与 gate 脚本 | 中 | **W2-3-GOV-RISK-PILOT**；`wf_gov_gate` → W3 |

---

## 8. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G10-2 v0.1 初版：§2 NBT-* 不可盲信清单、§3 人工确认、§4 停工禁止动作、§5 G6/G10-1/G7/G8 引用 |
| 2026-05-27 | W2-3：§6.3 首选 **ART-GOV-RISK**；§5.3／§5.4／NBT-H 留痕载体更新；T2 关闭 |
| 2026-05-27 | W2-2-QA-CHECKLIST：§1.2 增加实现层索引（W2-2 §4、G8 QA §5）；规则语义未改 |
