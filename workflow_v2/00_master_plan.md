# Workflow v2 — Master Plan（最终 AI 导入工作流）

> **角色（E1 · Wave 0 总控）**：定义 Wave 目标、模块边界、依赖顺序、并行原则与本轮不做项。  
> **不取代**：战车根 `00_master_plan.md`（企业化补强战役）、`workflow_upgrade/`（Context Entry Sprint）。  
> **派工黑板**：`workflow_v2/90_run_queue.md`  
> **依赖图**：`workflow_v2/02_dependency_map.md`  
> **并行制度**：`workflow_v2/03_parallel_execution_rules.md`  
> **快照**：`workflow_v2/99_latest_status.md`

---

## 1. 总体目标（v2）

在**不改 production code、不做 UI** 的前提下，为「最终 AI 导入工作流 v2」建立**可派工、可并行、可验收**的治理文字层：

- Wave 0：E1 总体治理骨架（目录、队列、依赖、三角色 chat 规则）；
- Wave 1：G6 / G7 / G8 / G10 治理定义层（各模块正文由**施工 chat** 按票填写，总控不写正文）。

原则：**文件优先、总控编排骨架、模块增量交付**。

---

## 2. Wave 0 — E1 总体治理骨架初始化

| 项 | 说明 |
|----|------|
| **目标** | 建立 v2 目录、master plan、run queue schema、依赖图、并行规则、状态快照；使后续 chat 可从 `90_run_queue.md` 单票接手。 |
| **模块** | **E1**（仅此一波内的总控模块） |
| **产出目录** | `workflow_v2/` 根下总控五件套 + `01_wave0_e1/`（E1 补充说明，可选） |
| **出口 DoD** | E1-1～E1-5 队列项状态可追溯；`02`/`03`/`90`/`99` 存在且互相引用一致；**未**宣称 G6–G10 正文已完成 |

### 2.1 E1 任务清单（Wave 0）

| ID | 标题 | 预期产物 |
|----|------|----------|
| E1-1 | 更新 master plan 结构 | `workflow_v2/00_master_plan.md` |
| E1-2 | 更新 run queue schema | `workflow_v2/90_run_queue.md`（栏位 + Wave 0/1 表） |
| E1-4 | 定义模块依赖与阶段顺序 | `workflow_v2/02_dependency_map.md` |
| E1-5 | 定义协调 / 施工 / checker chat 规则 | `workflow_v2/03_parallel_execution_rules.md` |

> **说明**：E1-3 保留编号空位（历史对齐），本轮不挂票。

---

## 3. Wave 1 — 治理定义层（G6 / G7 / G8 / G10）

| 模块 | 代号 | 职责（高层） | 产物目录（施工 chat 拥有） |
|------|------|--------------|---------------------------|
| **Scope Control** | G6 | AI change classes；每类允许动作 | `workflow_v2/10_governance/G6_scope_control/` |
| **State Machine** | G7 | 全状态列表；每状态 entry / exit 条件 | `workflow_v2/10_governance/G7_state_machine/` |
| **Artifact Contract** | G8 | PM / Design / Eng / QA / Release owner 五类 artifact 契约 | `workflow_v2/10_governance/G8_artifact_contract/` |
| **Governance Rulebook** | G10 | AI usage boundary；禁止直接信任 AI output 的情境 | `workflow_v2/10_governance/G10_governance_rulebook/` |

### 3.1 Wave 1 任务清单（仅编排骨架；正文待施工）

| 模块 | ID | 标题 | 预期产物（文件名由施工票定，下列为建议） |
|------|-----|------|------------------------------------------|
| G6 | G6-1 | 定义 AI change classes | `G6_scope_control/10_change_classes.md` |
| G6 | G6-2 | 定义每类 change 的允许动作 | `G6_scope_control/20_allowed_actions.md` |
| G7 | G7-1 | 定义全状态列表 | `G7_state_machine/10_workflow_states.md` |
| G7 | G7-2 | 定义每个状态 entry 条件 | `G7_state_machine/20_entry_conditions.md` |
| G7 | G7-3 | 定义每个状态 exit 条件 | `G7_state_machine/30_exit_and_transitions.md` |
| G8 | G8-1 | PM artifact contract | `G8_artifact_contract/10_pm.md` |
| G8 | G8-2 | Design artifact contract | `G8_artifact_contract/20_design.md` |
| G8 | G8-3 | Engineering artifact contract | `G8_artifact_contract/30_engineering.md` |
| G8 | G8-4 | QA artifact contract | `G8_artifact_contract/40_qa.md` |
| G8 | G8-5 | Release owner artifact contract | `G8_artifact_contract/50_release_owner.md` |
| G10 | G10-1 | 定义 AI usage boundary | `G10_governance_rulebook/10_ai_usage_boundary.md` |
| G10 | G10-2 | 定义禁止直接信任 AI output 的情境 | `G10_governance_rulebook/20_no_blind_trust.md` |

### 3.2 Wave 1 出口 DoD（高層）

- 上表 12 张施工票均有对应文件且 `90_run_queue.md` 标 `DONE`；
- G6–G10 文件互相引用一致（由 checker chat 只读盘点）；
- **仍不**包含：production 实现、hooks、自动化 enforcement 代码。

### 3.3 Wave 1 完成范围（CHK-W1 · 2026-05-27）

| 项 | 状态 | 说明 |
|----|------|------|
| **施工票** | **12/12 DONE** | G6×2、G7×3、G8×5、G10×2；均为 v0.1 实质正文 |
| **CHK-W1** | **PASS-WITH-NOTES** | 治理定义层语义可对齐；**非**零债务封板 |
| **Wave 1 总态** | **DONE-WITH-NOTES** | 可派工；封板前须 `G8-RECON-IMP` + `E1-6`（见 `99` §3） |
| **已交付能力** | v0.1 文字层 | 8×`CHG-*`、10×`IMP-*`、六轨 `ART-*`（含 **ART-GOV-RISK**）、`NBT-*` 禁止盲信表 |
| **未交付（Wave 2+）** | 见 §8.1 | `imp_state` CI enforcement、`wf_gov_gate`、GOV 案卷实例、完整 release gate |

**完成范围边界**：本轮交付的是**可派工、可并行、可交叉引用的治理文字层**；不宣称 runtime／tooling／自动化 gate 已上线。

---

## 4. 依赖关系（摘要）

详见 `02_dependency_map.md`。核心顺序：

```
Wave 0: E1-1 → E1-2 → E1-4 → E1-5
Wave 1: E1-5 完成后
        ├─ G6-1 → G6-2
        ├─ G7-1 → G7-2 → G7-3
        ├─ G8-1 … G8-5（五轨可并行，见 §5）
        └─ G10-1 → G10-2（建议晚于 G6 草案可读）
```

**软依赖（建议，非硬阻塞）**：

- G7 状态机宜知悉 G8 artifact 名称后再定稿 exit 条件（可并行草案，合并票对账）；
- G10 宜引用 G6 change class 与 G7 终态命名。

---

## 5. 可并行 / 不可并行原则

| 可并行 | 不可并行 |
|--------|----------|
| G8-1～G8-5 五份 artifact contract（不同施工 chat，不同子目录） | 同一子目录同一文件双 chat 同时写 |
| G6 与 G7 在 E1-5 完成后可各开一线（注意命名对账） | G6-2 先于 G6-1 定稿 |
| G7-2 与 G7-3 可并行**若** G7-1 状态列表已冻结 | G7-2/G7-3 在 G7-1 未 `DONE` 时标 `DONE` |
| 多个 checker chat 只读不同模块 | checker 改模块正文或扩 scope |
| — | 总控 chat 代写 G6/G7/G8/G10 正文 |

细则 → `03_parallel_execution_rules.md`。

---

## 6. 三角色 Chat 分工（索引）

| 角色 | 拥有 | 禁止 |
|------|------|------|
| **总控（orchestrator）** | `00`/`02`/`03`/`90`/`99`；队列结构与依赖 | 各 `10_governance/G*` 模块正文 |
| **施工（worker）** | 指派模块子目录 + 本票 `90` 行 Status/Notes | 他模块目录；总控五件套（除非 E1 票明示） |
| **检查员（checker）** | 只读盘点、风险摘要写 `99` 或票 Notes | 改模块正文；自行 `DONE` 施工票 |

全文 → `03_parallel_execution_rules.md`（E1-5 产物）。

---

## 7. 与战車根既有能力（只索引）

| 既有产物 | 关系 |
|----------|------|
| `04_Workflows/ENGINEERING_CONTRACT.md` | v2 治理层不得放宽 12-rule / 禁区 |
| `04_Workflows/HARNESS_CONSTITUTION.md` | 禁区**类型**引用憲法 §7，不重定义 |
| `AGENTS.md` | 接战／封存；Cursor subagent 派工见 `.cursor/agents/DISPATCH_GUIDE.md` |
| `workflow_upgrade/` | **不同**目录；Context Entry 规格，非 v2 导入主线 |
| 根 `00_master_plan.md` | H/I/J/K 战役封存；v2 为**导入工作流**治理，不覆盖 H 线合同 |

---

## 8. Explicit Out of Scope

### 8.1 Wave 0 / Wave 1 全程不适用（硬边界 · 仍有效）

- **不改** `core/`、暗部、`hooks`、connector、dashboard、production env；
- **不合并** `workflow_upgrade/` 与 `workflow_v2/` 目录或队列；
- **不替** 施工 chat 将 placeholder 标为 `DONE`（CHK-W1 已确认 R4 关闭）。

### 8.2 Wave 1 已完成 · 自 §8 移除

- ~~不写 G6 / G7 / G8 / G10 模块正文~~ → **已完成**（12 票 v0.1 正文；CHK-W1 PASS-WITH-NOTES）。

### 8.3 Wave 1 未宣称 · **保留到 Wave 2+**

| 项 | 说明 | 占位票 |
|----|------|--------|
| **导入管线 runbook（操作细则层）** | 阶段 SOP 自动化、机读 intake 边 | W2-2（W2-1 以试点案卷 + 轻量索引验证全链） |
| **G7 ↔ tooling 对齐** | `imp_state` 机读字段、intake→IMP 机读边、IMP-ACTIVE 子态 | W2-2 |
| ~~**`ART-GOV-RISK` G8 轨**~~ | ~~未定稿~~ → **G8-6 契约 v0.1**（`60_gov_risk.md`） | W2-3 **契约 DONE** |
| **GOV 案卷实例 + gate 脚本** | 设计 `W2-3_minimal_gate_design.md`；无 CI | W2-3 子票／W3 |
| **完整 release gate** | G8-5／G7-3 已声明 out of scope | W3+ |
| **deny engine runtime** | G10-2 T3；覆盖 A-3 全表 | W3+ |
| **Enforcement 自动化** | `wf_gov_gate` CI job | **W3-C**（`W2-3` 原型已交付；CI 接线 → `W3-C-CI-GATE-WIRE`） |
| **Rollout / canary** | K-2 shadow + internal canary | **W3-A**（邻接根 plan §4.8；非 v2 正文） |
| **Repo index（AI-READY 前置）** | 案卷可查 index 状态 | **W3-B** |
| **零债务定稿宣称** | Wave 1 = DONE-WITH-NOTES；非 production 验收或上线 | — |

---

## 9. Wave 2 — W2-1 最小闭环 Sprint

| 项 | 说明 |
|----|------|
| **目标** | 用 **一条真实但很小** 的导入案件，走通 PM → Design → Eng → QA → Release → Observing；验证 Wave 1 治理层（G6/G7/G8/G10）可支撑 artifact 与 IMP 状态记录，**不**上 production、**不**做 MCP／connector、**不**做完整 canary／shadow pipeline。 |
| **试点标题** | **W2-1 试点：G7↔G8 交叉引用 cleanup（G8-RECON-IMP 全链走通）** |
| **实质交付** | 执行既有 **G8-RECON-IMP** 范围：`ART-REL-RECORD`→`ART-REL-EXEC` 对账、去除 G7-2/3 stale「待 G8-x／待 G10-2」、Eng `30_engineering.md` §2 改引 G7-1；产物仍落在 `10_governance/` 既有路径。 |
| **试点案卷目录** | `workflow_v2/20_pilot/W2-1_case/`（施工 chat 写入 **ART-***；总控只建索引与 IMP 流说明） |
| **IMP 状态路径** | 见 §9.1；明细 artifact 对照 → `20_pilot/W2-1_imp_flow_and_artifacts.md` |
| **primary_change_class** | **CHG-GOV-DOC**（secondary 无；不触 §7 禁区） |
| **施工票** | `W2-1-PM-DES` → `W2-1-ENG` → `W2-1-QA-REL`（见 `90_run_queue.md` Wave 2 节） |
| **与 G8-RECON-IMP 关系** | Wave 1 P0 票 **G8-RECON-IMP** 正文施工并入 **W2-1-ENG**；G8-RECON-IMP 行保留为历史索引，Status 由 W2-1-ENG 收口时 Notes 回填。 |

### 9.1 IMP 状态路径（本案件）

```text
IMP-SCOPE-DRAFT → IMP-SPEC-CLARIFY → IMP-AI-READY → IMP-REVIEW-READY
  → IMP-RISK-VALIDATION → IMP-QA-READY → IMP-RELEASE-DECISION
  → IMP-RELEASED → IMP-OBSERVING
```

| IMP 状态 | 本案件主要 ART-* | 负责轨 |
|----------|------------------|--------|
| `IMP-SCOPE-DRAFT` | **ART-PM-SCOPE** | PM |
| `IMP-SPEC-CLARIFY` | **ART-PM-CLARIFY** + **ART-DES-SPEC** | PM + Design |
| `IMP-AI-READY` | **ART-ENG-CTX**（含 CHG-*／allowed_paths） | Eng |
| `IMP-REVIEW-READY` | **ART-ENG-WR** 草案 + **ART-ENG-FIVE** | Eng |
| `IMP-RISK-VALIDATION` | **ART-GOV-RISK**（G8-6）；**fallback** WR §4+§7（票面授权） | Eng + governance |
| `IMP-QA-READY` | **ART-ENG-EVD** + **ART-ENG-DOD** | Eng |
| `IMP-RELEASE-DECISION` | **ART-QA-REV** + **ART-REL-DEC** | QA + Release |
| `IMP-RELEASED` | **ART-REL-EXEC**（内部 doc-authority 生效即可） | Release |
| `IMP-OBSERVING` | **ART-PM-OBS-PLAN** + **ART-REL-OBS**（轻量版） | PM + Release |

**涉及 G8 轨**：PM／Design／Eng／QA／Release（五轨）+ **GOV**（`60_gov_risk.md` · W2-3 契约，W2-1 案卷仍用 WR fallback）。**不修改** G6/G7/G10 核心语义；G8 仅 **补充** GOV 轨与 G10-2 引用。

### 9.2 W2-1 出口 DoD（高層）

- 三张施工票均 `DONE`，且 `20_pilot/W2-1_case/` 可索引全部 **ART-***；
- G8-RECON-IMP 实质 diff 已合并至 `10_governance/` 目标路径；
- IMP 终态 **`IMP-OBSERVING`** 或轻量收口至 **`IMP-OBSERVING` exit**（见 G7-3）；
- **仍不**宣称：`imp_state` CI enforcement、`wf_gov_gate` 脚本、案卷 **ART-GOV-RISK** 实例（→ W2-2 子票／W2-3 施工票）。

### 9.3 状态字段约定（W2-2 v0.1）

| 项 | 说明 |
|----|------|
| **字段** | `imp_state` — 单次 AI 导入 artifact 的 **IMP-*** 主线态（**非** queue `Status`） |
| **取值权威** | `10_governance/G7_state_machine/10_workflow_states.md`（G7-1）；**禁止**自造状态名 |
| **迁移权威** | `10_governance/G7_state_machine/30_exit_and_transitions.md`（G7-3）；禁止跳关 |
| **完整规格** | `20_pilot/W2-2_imp_state_schema.md` |
| **G7 附录** | `10_governance/G7_state_machine/40_imp_state_field_v0.1.md` |
| **写入载体** | 案卷 `20_pilot/<CASE>_case/<CASE>_case.md` §2（`imp_state_current`）+ §3（`imp_state_transitions`）；queue Notes 仅索引（P3） |
| **标准模板** | `20_pilot/_TEMPLATE_case/`（**W2-2-IMP-FIELD DONE**）；试点对齐见 `W2-1_case/W2-1_case.md` |
| **helper** | `tools/wf_check_cross_ref.ps1` + `20_pilot/W2-2_tooling_notes.md`（AC grep + 最小 NBT 清单） |
| **未交付** | CI 校验 `imp_state`、intake→IMP 机读边（→ W2-3+） |

---

## 10. Wave 2 — W2-2 imp_state + tooling（规格 Sprint）

| 项 | 说明 |
|----|------|
| **目标** | 在不引入重型 CI 前提下，统一 **`imp_state` 字段约定** 与 **可复用 helper**（AC grep、最小 no-blind-trust 清单），供后续每条导入任务复用。 |
| **本波交付（总控）** | `W2-2_imp_state_schema.md`、`W2-2_tooling_notes.md`、`tools/wf_check_cross_ref.ps1`、G7 附录 `40_imp_state_field_v0.1.md`；`00` §9.3；`90` 子票占位。 |
| **依赖** | W2-1 最小闭环 **DONE**（`IMP-OBSERVING` 试点已走通） |
| **施工子票** | `W2-2-IMP-FIELD` **DONE**；`W2-2-HELPER-SCRIPTS`／`W2-2-QA-CHECKLIST` 待定（见 `90_run_queue.md`） |
| **案卷约定** | Wave 2+ **新导入 case** 须复制 `20_pilot/_TEMPLATE_case/`；§2／§3 为必填 IMP 区块 |
| **硬边界** | 不改 G6/G7/G8/G10 核心条文语义；不改 production code；不新增 IMP-* 名 |

---

## 11. Wave 2 — W2-3 ART-GOV-RISK + minimal gate（规格 Sprint）

| 项 | 说明 |
|----|------|
| **目标** | 正式 **ART-GOV-RISK** G8 GOV 轨契约；G10-2 首选 GOV artifact；文档层最小 gate 设计供 W3／CI 施工 |
| **本波交付（总控）** | `G8_artifact_contract/60_gov_risk.md`；G8 README 六轨；G10-2 §6.3／§5 引用更新；`20_pilot/W2-3_minimal_gate_design.md`；`90` 子票占位 |
| **依赖** | W2-1 最小闭环 **DONE**（RISK 阶段曾 WR fallback） |
| **硬边界** | 不改 production code；不实现 gate 脚本；不改 G6/G7 核心条文 |
| **施工子票** | `W2-3-GOV-RISK-CONTRACT`（契约，总控已合并）／`W2-3-GOV-RISK-PILOT`／`W2-3-MINIMAL-GATE-DESIGN`（设计，总控已合并）／`W2-3-MINIMAL-GATE-IMPL`（→ W3 建议） |

---

## 12. 后续 Wave（索引）

| Wave | 方向 | 队列 ID | 状态（2026-05-27） |
|------|------|---------|-------------------|
| Wave 1 收尾 | 总控索引对齐 | E1-6 | TODO |
| Wave 2 | **最小闭环 Sprint** | **W2-1-*** | **DONE**（`IMP-OBSERVING`） |
| Wave 2 | **imp_state + helper tooling** | **W2-2-*** | 总控 + IMP-FIELD **DONE**；HELPER／QA-CHECKLIST 待定 |
| Wave 2 | **ART-GOV-RISK + minimal gate** | **W2-3-*** | 总控 + 契约 + gate 设计 + `wf_gov_gate` 原型 **DONE**；pilot 待定 |
| **Wave 3** | **rollout／canary + 知识层基建 + 治理接入** | **W3-*** | **设计定稿／出口封口**（见 §13；实装 → §15） |
| **Wave 4** | **W3 设计接入主工作流与 CI（implementation v1）** | **W4-*** | **规划已开盘**（见 §15；`90` Wave 4 三节主票） |
| Wave 5+ | 稳定化／治理收敛／全量扩面／deny runtime 等 | — | 占位（见 §15.5） |

队列表见 `90_run_queue.md` **Wave 2**／**Wave 3**／**Wave 4** 节；依赖见 `02_dependency_map.md` §8。

---

## 13. Wave 3 — rollout / canary + 知识层基建 + 治理接入

| 项 | 说明 |
|----|------|
| **总控票** | **W3-0-ORCH**（本節落盘）；三条主线各 **W3-*-ORCH** 首张长上下文票 |
| **前置** | Wave 1 **DONE-WITH-NOTES**；W2-1 **IMP-OBSERVING**；W2-2／W2-3 总控规格与 gate/helper 原型已交付 |
| **硬边界** | 不改 G6/G7/G8/G10 正文语义；不改 production code（本波总控票仅文档／队列）；不宣称远端 prod 全自动或完整 release gate |
| **邻接权威（只读）** | 战车根 `00_master_plan.md` §4.8（K-2 rollout Phase）；`docs/k2_deployment_governance.md`（shadow／canary 角色矩阵，**非** v2 正文） |

### 13.1 W3-A — Rollout / Canary

| 项 | 说明 |
|----|------|
| **业务链默认** | **K-2 × ask**（v2 导入工作流试点默认组合；**非**唯一合法路径，亦不排除纯 ask 或未来合流变体） |
| **最低完成** | **shadow** 跑通至少 1 次（对照 ask 主答案／metadata，留 diff 或 spool 索引）；**internal canary**（约 **5–10%** 流量或等价 cohort）至少 1 次试点；产出 **ART-REL** 风格记录（`ART-REL-RECORD`／`ART-REL-EXEC` 或案卷内 release 观测块，见 G8-5） |
| **施工票（索引）** | `W3-A-ORCH` → `W3-A-SHADOW-PILOT` → `W3-A-CANARY-PILOT`；`W3-A-REMOTE-ENV` 支撑 canary；`W3-A-REL-ARTIFACT` 收口 release 记录 |
| **out-of-scope** | 远端 **prod** 全自动 rollout；K-2 **Phase 3+** 扩面（见根 plan §4.8）；**完整 release gate**（G8-5 已声明延续）；L1+ monitoring 参与 selector／SLO |

**W3-A 出口最低要求（Wave 3 口径）**：K-2×ask shadow 与 internal canary 均至少 1 次试点且可索引 run 记录与 ART-REL 风格发布记录；远端 prod 自动 rollout 与 K-2 Phase 3+ 扩面由 Wave 4+ 接续负责。

### 13.2 W3-B — 知识层 / Repo Indexing

| 项 | 说明 |
|----|------|
| **最低完成** | **repo index** 成为 **`IMP-AI-READY` 前置**（案卷 §2／**ART-ENG-CTX** 可声明 `index_status` 或等价字段）；案卷与 Eng context 可**查** index 状态（ready／stale／missing），不宣称全库实时一致 |
| **施工票（索引）** | `W3-B-ORCH` → `W3-B-KB-CONTRACT` → `W3-B-INDEX-PIPELINE` → `W3-B-SELECTOR-HOOK`；`W3-B-GRAPHRAG-MIN` 为可选最小 GraphRAG 探针（不阻塞主线 DoD） |
| **软依赖** | index pipeline 宜在 W3-A shadow 前或并行就绪（见 `02` §8：`W3-B-INDEX-PIPELINE` -.-> `W3-A-SHADOW-PILOT`） |
| **out-of-scope** | 全库**实时增量**索引；多 **tenant KB** 产品化；**替换**现有 RAG 主路径或 ask selector 生产默认 |

**W3-B 出口最低要求（Wave 3 口径）**：W3-B KB 字段契约与 index pipeline runbook/队列 wiring 已落盘，使案卷与 ENG-CTX 可查 `ready/stale/missing` 并作为 `IMP-AI-READY` 前置口径；将 index pipeline 真正接到生产 ORCH／扩面到所有 case 或全量 repo 由 Wave 4+ 接续负责。

### 13.3 W3-C — 治理自动化闭环

| 项 | 说明 |
|----|------|
| **最低完成** | `workflow_v2/tools/wf_gov_gate.ps1` + `wf_check_cross_ref.ps1` **接入一条真实 pipeline**（CI job 或 **nightly** 均可）；至少 **响过一次**并留下可索引指标（pass/fail 计数、案卷路径、run id／artifact 链接） |
| **施工票（索引）** | `W3-C-ORCH` → `W3-C-GOV-RISK-PILOT` → `W3-C-CI-GATE-WIRE`；`W3-C-AGENT-SOP`／`W3-C-IMP-STATE-LINT` 为并行增强（非 Wave 3 出口硬依赖） |
| **前置** | `W2-3-MINIMAL-GATE-IMPL`（gate 原型）→ `W3-C-CI-GATE-WIRE`；`W2-1-QA-REL` → `W3-C-GOV-RISK-PILOT`；`W2-2-IMP-FIELD` → `W3-B-KB-CONTRACT`（契约字段对齐） |
| **out-of-scope** | **deny engine runtime**（G10-2 T3）；**全 IMP** 状态机机读 enforcement；**95%** 无人值守治理 |

**W3-C 出口最低要求（Wave 3 口径）**：GOV-RISK pilot 有完整案卷与 note；CI 接线方案已设计并经 nightly 固定响铃设计自检；实际接入真 CI 与 fail‑on‑deny 由 Wave 4 接续负责。

### 13.4 Wave 3 出口 DoD（checklist）

- [ ] **W3-A**：shadow + internal canary **各至少 1 次**（有 run 记录与 ART-REL 风格 artifact／status）
- [ ] **W3-B**：**AI-READY** 前 index **可查**（案卷或 ENG-CTX 可回答 ready／stale／missing）
- [ ] **W3-C**：gate 在 **CI 或 nightly 至少真实响过一次**（附指标或日志索引，非仅本地手跑）
- [ ] **三条线均有可索引 artifact / status 记录**（`90` 票 Notes + `99` 战报 + 案卷或 `20_pilot/W3-*` 目录）

### 13.5 AI 使用原则 / 成本策略

| 原则 | 说明 |
|------|------|
| **ORCH 首张票** | 每条主线（A/B/C）**第一张**施工协调票 = **长上下文／大总控**模式（读 `00`§13、`02`§8、`90` 全表、邻接 K-2 文档摘要） |
| **子票默认** | **小上下文／窄 diff**；仅读本票 Output + Depends 产物 + 必要案卷 |
| **禁止** | 在子票中**重开** G6–G10 **全文**治理讨论（争议 → 单开 governance 票或 `99` 阻塞项） |
| **Wave 3 粗估 token** | 总量约 **2×10⁶–3×10⁶**（含三轮 ORCH + 子票 + checker）；费用为**量级估计**（例如数十至低百 USD 档，视模型与重读次数而定），**不**写成精确报价或采购承诺 |

### 13.6 与 Wave 4／Wave 5 分界（明确留后）

以下事项 **不在 Wave 3 宣称完成**；其中 **第一版实装** 由 **Wave 4**（§15）承接，**最终平台完成度** 留 **Wave 5+**：

| 留 Wave 4（implementation v1） | 留 Wave 5+（稳定化／扩面） |
|-------------------------------|---------------------------|
| K-2×ask shadow／internal canary → **可重复 rollout 节奏**（W4-A） | K-2 **Phase 3–4**、远端 **prod** 自动 rollout |
| KB 契约 + index pipeline → **ORCH／主工作流接线**（W4-B） | 全库实时增量、多 tenant KB、替换 RAG 主路径 |
| gate／cross-ref／JSONL／artifact → **PR／nightly／manual 真 CI**（W4-C） | **fail-on-deny** 默认全 PR hard fail；deny engine runtime |
| — | **95% 自动化**、全 IMP 机读 enforcement、完整 release gate |

Wave 3 出口语句（§13.1–§13.3 **W3-* 出口最低要求**）**冻结**；Wave 4 仅在其后**接续实装**，不 retro 改写口径。

---

## 15. Wave 4 — Implementation（W3 设计接入主工作流与 CI）

| 项 | 说明 |
|----|------|
| **总控票** | **W4-A-K2-ROLLOUT-INTEGRATION**／**W4-B-INDEX-INTEGRATION**／**W4-C-CI-INTEGRATION**（见 `90_run_queue.md` Wave 4 节） |
| **前置** | Wave 3 三条主线 **contract／runbook／gate／metrics 设计已定稿**（§13.1–§13.3 出口语句不变） |
| **硬边界** | 本轮规划票 **仅文档／队列**；**不**在本波总控轮修改 `.github/workflows/*`、暗部脚本、deny engine runtime；**不**改 G6/G7/G8/G10 正文语义 |

> **Wave 4 目标**：将 W3-A / W3-B / W3-C 在 Wave 3 已定稿的 contract / runbook / gate / metrics 设计正式接入主工作流与 CI，建立可观测、可回滚、可持续运转的第一版实装。

**W4-A** 承接 W3-A：把 K-2×ask **shadow** 与 **internal canary** 从试点文档升格为**可重复执行的 rollout integration**（release 节奏、gate checklist、rollback／override 准则）；**不等于**全量 prod rollout。

**W4-B** 承接 W3-B：把 KB 字段契约与 index pipeline runbook **真正接入 ORCH／主工作流**，先覆盖**主 case／主 repo**；使 `kb_index_*` 回填与 `ready`／`stale`／`missing` 成为 **IMP-AI-READY** 的运行前置；**不要求**一次扩面到所有 repo／所有 case。

**W4-C** 承接 W3-C：把 `ci_gate_wire.md` 定义的 PR／nightly／manual 接线**正式接入 CI**（observability 落点、`jsonlPath`、artifact 上传、`continue-on-error`／吞 exit 策略）；**fail-on-deny** 仅作分阶段治理议题，**不得**默认变成所有 PR hard fail。

Wave 4 **不追求**最终平台完成度；重点是 **「接上去、跑起来、可观测、可回滚」**。稳定化、治理收敛、性能／成本优化与全量扩面 → **Wave 5+**（§15.5）。

### 15.1 W4-A — K-2 Rollout Integration

| 项 | 说明 |
|----|------|
| **最低完成** | rollout **runbook** + gate **checklist** + rollback／override 准则；shadow／canary 与 release 节奏可索引、可重复触发 |
| **施工票** | `W4-A-K2-ROLLOUT-INTEGRATION`（`90`） |
| **依赖** | W3-A 出口（`30_rollout/`、`20_pilot/W3-A_case/`、shadow／canary 试点记录） |
| **out-of-scope** | 远端 prod 全自动；K-2 Phase 3+ 扩面；完整 release gate |

**已实装挂点（minimal v1 · 2026-05-29 · doc-sync）**

W4-A 已完成一条**固定试点 release 流** **`W4-A-PILOT-RELEASE-STREAM-v0.1`**（配置：`20_pilot/W3-A/rollout_pipeline_config.json`；流指针：`20_pilot/W3-A_case/W4-A_release_stream.json`）。该流在**主 case／主 scope** `20_pilot/W3-A_case/` 上可重复执行，**不修改** prod CI workflow 或 `merge_ask_and_k2` adapter。

| 能力 | 说明 |
|------|------|
| **K2 shadow** | unittest（`k2_merge` + `k2_ask_shadow`）→ `ibridge_exporter --source shadow` → `eval_ci_check`；user-facing 仍为 ask-only |
| **internal canary** | 5% cohort 模拟（`staging-internal` 逻辑名）；产出 `07_art_rel_dec.json`／`08_art_rel_exec.json` |
| **rollback / override** | `-Phase rollback` 将 cohort 置 0；`-Phase override` 需 allowlist 角色 + reason 文本 |
| **入口 helper** | `workflow_v2/tools/wf_k2_rollout_run.ps1`（`-Phase full\|shadow\|canary\|rollback\|override`） |
| **可重跑证据** | `20_pilot/W3-A_case/run_records/**`（含 `rollout_trace.jsonl`、`shadow_state.json`、shadow/canary run 摘要） |
| **Runbook / Gate** | 权威正文 `20_pilot/W3-A/W4-A_rollout_runbook.md`；Gate `20_pilot/W3-A_case/W4-A_gate_checklist.md` |

**口径**：当前仅为 **minimal v1／固定试点流**；**未**扩展到 prod 主流、多管道或多 cohort 策略。**全量 rollout、CI 集成、多 cohort、多 repo 扩面** → **Wave 5+**（§15.5；候选票 `W5-A-K2-ROLLOUT-EXPANSION`）。

### 15.2 W4-B — Index / ORCH Integration

| 项 | 说明 |
|----|------|
| **最低完成** | 主 case／主 repo 上 **ORCH** 可触发 index 回填；案卷 §2／ENG-CTX 的 `kb_index_*` 与 `ready`／`stale`／`missing` **运行时可查** |
| **施工票** | `W4-B-INDEX-INTEGRATION`（`90`） |
| **依赖** | `W3-B_kb_contract.md`、`W3-B_index_pipeline_runbook.md`、W3-B 出口字段契约 |
| **out-of-scope** | 全库实时增量；多 tenant KB；替换 RAG prod 主路径 |

### 15.3 W4-C — CI / Observability Integration

| 项 | 说明 |
|----|------|
| **最低完成** | `wf_check_cross_ref` + `wf_gov_gate` 接入 **PR／nightly／manual** 之一条真实 pipeline；`gov-metrics-0.1` JSONL + artifact **至少响过一次** |
| **施工票** | `W4-C-CI-INTEGRATION`（`90`） |
| **依赖** | `20_pilot/W3-C/ci_gate_wire.md`、`W3-C_metrics_schema.md`、`W3-C-CI-GATE-WIRE` 设计收口 |
| **out-of-scope** | deny engine runtime；未经治理批准的 **全 PR fail-on-deny** |

### 15.4 Wave 4 出口 DoD（checklist · 实际完成）

- [x] **W4-A**：rollout integration runbook + checklist 可执行索引（**minimal v1** · 固定试点流 `W4-A-PILOT-RELEASE-STREAM-v0.1`；非全量 prod rollout）
- [x] **W4-B**：主 case／主 repo ORCH 接线 + index 状态可查且阻塞 **IMP-AI-READY**（`missing`/`blocker` 硬阻断，`stale` 需显式 ack+flag）
- [x] **W4-C**：真 CI workflow（`.github/workflows/gov-gate-metrics.yml`）PR／nightly／manual 三场景 + JSONL（`gov-gate-metrics` artifact）已响铃
- [x] **W4-X**：控制面 MVP 文档（`30_control_plane/W4-X_control_plane_mvp.md`）+ Ticket Memory 模板（`40_ticket_memory/_TEMPLATE_ticket_memory.md`）已交付
- [x] **三条线**均有 `90` 票 Notes + `99` 战报 + 可复盘命令／run id
- **整体 Wave 4 状态**：**DONE-WITH-KNOWN-GAPS**（已知缺口不阻擋 Wave 5 開工；詳見 `90`/`99` 與 CHK-W4 Memory）

### 15.5 与 Wave 5+ 分界

| 留 Wave 5+ | 说明 |
|------------|------|
| **95% 自动化** | 导入全链无人值守比例目标 |
| **deny engine runtime** | G10-2 T3 |
| **全 IMP 机读 enforcement** | 全状态 CI 硬阻断 + intake→IMP 机读边 |
| **K-2 Phase 3–4／远端 prod 自动 rollout** | 根 plan §4.8 后续 Phase |
| **知识层全库级产品化** | 实时增量、多 tenant KB、替换 RAG 主路径 |
| **完整 release gate** | G8-5 延续项 |
| **fail-on-deny 全 PR 默认** | 须经尚書省分阶段治理批文 |

### 15.6 Wave 4 / Wave 5 控制面（Control Plane）MVP（W4-X）

> **定位**：为 Wave 4 implementation 与 Wave 5 稳定化补上最小「控制面骨架」，将工作拆成多 lane（planning / runtime / review / doc-sync），避免在单一大上下文中同时做规划 + 实装 + 审核 + 文档回写。

| 项 | 说明 |
|----|------|
| **主票** | `W4-X-CONTROL-PLANE-MVP`（见 `90_run_queue.md`） |
| **交付物** | `workflow_v2/30_control_plane/W4-X_control_plane_mvp.md` + `workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md` |
| **硬边界** | 不 retro 改写 Wave 4 既有主票口径；不触碰暗部脚本；不新增/启用 deny engine runtime；不修改 G7/G8 正文语义 |
| **刻意留给 Wave 5+** | 自动开 chat／自动并行调度／自动 merge 决策／更复杂 reviewer pipeline（只在 MVP 文档中标注，不在本票实现） |

### 15.7 Wave 5 草案挂点（规划 · 未实施）

> **状态**：下列为 **Wave 5 候选大票** 的 planning 落盘；**不**表示已在实施或已完成。Wave 4 收口（含 CHK-W4）优先。

| 候选票 | 说明 | Ticket Memory |
|--------|------|----------------|
| **W5-A-K2-ROLLOUT-EXPANSION** | 在 W4-A 固定试点流 `W4-A-PILOT-RELEASE-STREAM-v0.1`（minimal v1）基础上，将 K-2 rollout **扩展**到 prod / CI 集成 / multi-cohort / multi-repo；含渐进交付、指标门槛、rollback/override SOP | `40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md` |

**与 W4-A 分界（重申）**：W4-A = 主 case 可重复 shadow + internal canary（5% 模拟）+ 最小 rollback/override，**≠** 全量 prod rollout。W5-A = 上述能力的 prod 级扩面；**不** retro 改写 W4-A DONE 口径。

---

## 14. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | Wave 0+1 总控初始化：E1 五件套 + G 模块队列与目录占位 |
| 2026-05-27 | Wave 1 总控收尾：CHK-W1 PASS-WITH-NOTES → DONE-WITH-NOTES；§3.3 完成范围；§8 分拆 Wave 2 保留项 |
| 2026-05-27 | Wave 2 W2-1 最小闭环 Sprint：§9 试点案 + IMP 路径；三张施工票入队 |
| 2026-05-27 | Wave 2 W2-2 规格：§9.3 状态字段约定 + §10 tooling Sprint；`imp_state` schema + cross-ref helper |
| 2026-05-27 | W2-2-IMP-FIELD：`_TEMPLATE_case` 标准案卷 + W2-1 结构对齐；G7 附录 §4 用法 |
| 2026-05-27 | Wave 2 W2-3 规格：§11 GOV 轨 **ART-GOV-RISK** + minimal gate 设计；G10-2 引用更新 |
| 2026-05-27 | **Wave 3 正式开盘**：§13 rollout／知识层／治理接入；`02`§8 + `90` Wave 3 区 + `99` 战报 |
| 2026-05-29 | **Wave 4 implementation 规划落盘**：§15 + `90` 三张主票（W4-A/B/C）；§12／§13.6 与 Wave 5+ 分界；不改 §13.1–§13.3 出口语句 |
| 2026-05-29 | **W4-X 控制面 MVP 开盘**：§15.6 控制面骨架挂点 + Ticket Memory 模板（不触实现） |
| 2026-05-29 | **W4-A minimal v1 实装 doc-sync**：§15.1 已实装挂点（固定试点流 shadow+canary+rollback/override）；§15.4 W4-A DoD 勾选；不改 runtime |
| 2026-05-29 | **W5-A planning 切片**：§15.7 草案挂点 + `40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`；**未**实施 runtime/CI |
