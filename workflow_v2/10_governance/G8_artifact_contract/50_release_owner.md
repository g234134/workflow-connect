# G8 — Release Owner Artifact Contract（v0.1）

> **票号**：G8-5（与 G8-B 合并交付 Release 轨）  
> **状态**：v0.1 草案；可被 G8 总览与 G10 rulebook 引用  
> **权威母本**：`G7_state_machine/20_entry_conditions.md` §4 IMP-RELEASE-*；`30_exit_and_transitions.md` §3；`04_Workflows/OPS_CYCLE.md` §3–§4；`AGENTS.md` §封存协议（并行域，非 release gate）  
> **不覆盖**：PM 观测计划正文（见 `10_pm.md` **ART-PM-OBS-PLAN**）；QA verdict 定义；**完整 release gate 闸机**（字段级裁决 only）；production code

---

## 1. 轨定位

**ART-REL-*** 定义 **release owner**（G7-2 §3.2 `entry_owner_role: release`）在 QA 收口之后、观测期结束之前必须产出的**发布裁决、执行确认与观测收口**交付物。Release 轨**消费** **ART-QA-REV**（`verdict` ∈ {`accepted`, `accepted_with_gaps`}），**不**替代 checker 验收或 Eng Work Report。

**边界声明（v0.1）**：本档定义 artifact 字段与 IMP 门槛；**不写** prod 流量切换阈值、canary 比例、K-2 rollout 等完整 gate——此类细则另票引用 `docs/k2_deployment_governance.md` 等，G10 可引用本档 ID。

**命名对账**：G7-2 entry 曾用占位 **ART-REL-RECORD**；本档正式 ID 为 **ART-REL-EXEC**（执行记录）。对账票 `G8-RECON-IMP` 须更新 G7-2 §4 表。

---

## 2. G7 占位状态（待对账）

| 占位别名 | Release 语义 | 建议正式态（G7-1） |
|----------|--------------|-------------------|
| `IMP-ARCHIVE-PENDING` | QA 通过、待发布裁决窗口 | 并行 `IMP-RELEASE-DECISION`（见 G7-2 §6） |
| `IMP-ARCHIVED` | 战报 append | ops 并行；**不**等同 `IMP-RELEASED` |
| — | 发布裁决 | `IMP-RELEASE-DECISION` |
| — | 发布执行确认 | `IMP-RELEASED` |
| — | 观测收口 | `IMP-OBSERVING` exit |

正式名 ↔ 占位映射 **待 G7-2／G7-3 对账**。

---

## 3. 核心 Artifact 一览

| ID | 名称 | 载体 | 主要来源 |
|----|------|------|----------|
| **ART-REL-DEC** | Release Decision（发布裁决） | JSON 或 Markdown 表 | G7-2 §4 IMP-RELEASE-DECISION |
| **ART-REL-EXEC** | Release Execution Record（执行记录） | JSON 或 Markdown 表 | G7-2 §4 IMP-RELEASED entry；G7-3 §3 IMP-RELEASED exit |
| **ART-REL-OBS** | Observation Close-out（观测收口） | JSON 或 Markdown 表 | G7-3 §3 IMP-OBSERVING exit |

---

## 4. 分 Artifact 契约

### 4.1 ART-REL-DEC — Release Decision

**目的**：记录在 `IMP-RELEASE-DECISION` 的发布／拒发布裁决；须含范围、受众与回退策略草案。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `artifact_id` | ✓ | 与 PM scope 一致 |
| `ticket_id` | ✓ | 关联票号 |
| `release_id` | ✓ | 本 artifact 发布批次稳定 ID |
| `decision` | ✓ | `approve` \| `deny` \| `defer` |
| `release_scope` | ✓ | 纳入本次发布的产物摘要（对齐 Eng WR §1） |
| `target_audience_or_env` | ✓ | 受众或环境逻辑名（如 `staging`、`doc-authority`、`internal-dev` — **无 secret**） |
| `rollback_strategy_draft` | ✓ | 回退步骤摘要或显式「仅 forward-fix」+ 理由 |
| `qa_verdict_ref` | ✓ | 指向 **ART-QA-REV**（`verdict` + `ticket_id`） |
| `p0_blockers` | ✓ | 裁决时未解决 P0；`approve` 时须为 `[]` |
| `defer_reason` | 条件 | `decision: defer` 时必填 |
| `message` | ✓ | 一句给 PM／Eng／尚書省 |

| 类别 | 规则 |
|------|------|
| **blocker** | `decision: approve` 但 **ART-QA-REV** 为 `rejected`／`blocked`；缺 `rollback_strategy_draft` 且 `CHG-HIGH-RISK`；`p0_blockers` 非空却 approve；queue 票 `DONE` **作为**唯一发布证据 |
| **IMP 门槛** | **`IMP-RELEASE-DECISION` exit 至 `IMP-RELEASED` 前**须 `decision: approve`；`deny` → `IMP-REWORK`（G7-3 §5.1） |
| **确认方** | **release owner** 必须；**PM（`pm`）** 对 `release_scope` 与 **ART-PM-SCOPE** 一致性知情 |

---

### 4.2 ART-REL-EXEC — Release Execution Record

**目的**：证明发布已在 `target_audience_or_env` **确认生效**；支撑 `IMP-RELEASED` entry 与 exit → `IMP-OBSERVING`。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `release_id` | ✓ | 与 **ART-REL-DEC** 一致 |
| `artifact_id` | ✓ | 与 scope 一致 |
| `decision_ref` | ✓ | 指向 **ART-REL-DEC** |
| `target_audience_or_env` | ✓ | 须与裁决一致或附 `scope_delta` |
| `published_at` | ✓ | ISO-8601 或日期 + 时区语义 |
| `execution_evidence` | ✓ | 文档版本号、tag、配置生效摘要、runbook 切换记录等（**不贴 secret**） |
| `rollback_path_valid` | ✓ | 布尔；`false` 为 blocker |
| `ops_cycle_ref` | — | 若并行 append 战报：battle report `ticket_id` 或 validate 引用 |

| 类别 | 规则 |
|------|------|
| **blocker** | 裁决 `pending`／`deny` 却登记执行；`target_audience_or_env` 与裁决不一致无说明；无 `execution_evidence`；`rollback_path_valid: false` |
| **IMP 门槛** | **`IMP-RELEASED` entry 前**；**`IMP-OBSERVING` entry 前**须 execution 已确认 |
| **确认方** | **release owner**；**checker** 可只读核对 evidence 与 QA 结果不矛盾（**不**扩 scope 跑功能测试） |

---

### 4.3 ART-REL-OBS — Observation Close-out

**目的**：观测窗口正常或异常结束时的收口记录；与 **ART-PM-OBS-PLAN** 对账。**不**定义观测期内的 incident 响应 runbook。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `release_id` | ✓ | 与执行记录一致 |
| `artifact_id` | ✓ | 与 scope 一致 |
| `obs_plan_ref` | ✓ | 指向 **ART-PM-OBS-PLAN** |
| `observation_outcome` | ✓ | `clean` \| `with_incidents` \| `aborted` |
| `window_met` | ✓ | 是否满足计划窗口 |
| `incidents_summary` | 条件 | `with_incidents` 或 `aborted` 时必填；P0 须链 `rework_record` 或 follow-up 票 |
| `feedback_archived` | ✓ | 布尔或 follow-up 票列表 |
| `follow_up_tickets` | ✓ | 无则 `[]` |
| `freeze_recommendation` | — | 是否建议终局／冻结（细则 **待 G10**；本档仅记录建议） |

| 类别 | 规则 |
|------|------|
| **blocker** | 窗口未结束却 `observation_outcome: clean`（无 waiver）；P0 incident 未记录却标 clean；缺 `obs_plan_ref` |
| **IMP 门槛** | **`IMP-OBSERVING` 正常 exit 前** |
| **确认方** | **release owner** 主责；**PM** 确认反馈归档策略 |

**异常路径**：P0／安全事件 → `IMP-REWORK`（G7-3 §5.4），**不**以本 artifact 标「正常 close-out」。

---

## 5. Release 轨 Blocker 字段汇总

| Artifact | Blocker 字段／条件 |
|----------|-------------------|
| ART-REL-DEC | QA rejected 却 approve；无 rollback；P0 未清 |
| ART-REL-EXEC | 无执行证据；rollback 无效；与裁决环境不一致 |
| ART-REL-OBS | 窗口未满足却 clean；P0 未链 rework |

---

## 6. 与 QA／OPS／PM 的边界

| 关系 | 规则 |
|------|------|
| QA → Release | 无 **ART-QA-REV** `accepted*` 不得 **approve** |
| OPS 封存 | battle report append 可与 `IMP-RELEASE-DECISION` **并行**；**不**替代 **ART-REL-EXEC** |
| PM 观测 | **ART-PM-OBS-PLAN** = entry；**ART-REL-OBS** = exit；二者 `release_id` 须一致 |
| 完整 gate | canary／shadow／prod 阈值 **不在** 本档；Release owner artifact 仅记录**已发生**裁决与证据 |

---

## 7. 引用索引

| 主题 | 路径 |
|------|------|
| PM 观测计划 | 本目录 `10_pm.md` §4.4 |
| QA verdict | 本目录 `40_qa.md` §4.1 |
| G7 entry（release） | `workflow_v2/10_governance/G7_state_machine/20_entry_conditions.md` §4 |
| G7 exit（release） | `workflow_v2/10_governance/G7_state_machine/30_exit_and_transitions.md` §3 |
| 封存并行域 | `04_Workflows/OPS_CYCLE.md`；`AGENTS.md` §封存协议 |

---

## 8. 修订记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-05-27 | v0.1 | G8-B 首版 Release 轨；ART-REL-RECORD→ART-REL-EXEC 待 G7-2 对账 |
