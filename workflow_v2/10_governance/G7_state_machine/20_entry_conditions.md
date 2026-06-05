# G7-2 — IMP-* Entry Conditions

> **票号**：G7-2  
> **范围**：为 G7-1 所列 **10 个 IMP-*** 状态定义 **进入前提**、最少必备 artifact／evidence、**owner**、**blockers**。  
> **不含**：exit 条件、合法迁移边（→ G7-3）；机读 enforcement 代码（→ Wave 2+）。  
> **上游**：`10_workflow_states.md`（G7-1，状态名冻结）  
> **下游**：G7-3、G8 各轨、G10 rulebook、release gate 应引用本档 **§4** 分状态表与 **§3** 全局规则。

---

## 1. 文档边界（与平行命名空间）

| 域 | 字段／字汇 | 本档关系 |
|----|------------|----------|
| **IMP-* 主线** | `imp_state`（建议机读字段名，见 §2） | **本档定义 entry** |
| **queue 施工票** | `Status`: `TODO`／`DOING`／`BLOCKED`／`DONE` | 票 `DOING` **不证明** artifact 已进入某 IMP-*；仅表示治理施工票进度 |
| **battle_report** | `status`: `draft`／`done`／`blocked`／`partial` | 单轮战报封口；**不得**写入 `imp_state` |
| **route** | `assignable`、`block_reason`、`phase_gates` | 派工门闸；`assignable:true` **不证明**已满足 IMP entry |
| **intake** | `accept`／`reject`／`defer` | 可**触发**进入 `IMP-SCOPE-DRAFT`，但 **禁止**把 intake 字面量写入 `imp_state` |
| **guard** | `verdict`: `allow`／`deny`／`stop_work` | 派工裁决；**不**替代 IMP 状态名 |
| **CHG-*** | `primary_change_class` | 进入 `IMP-AI-READY` 及之后须已记录；**不**替代 IMP 名 |

**禁止**：在 `imp_state` 或 entry evidence 中写入 `DOING`、`done`、`assignable:false`、`accepted`（checker verdict）等异域值。

---

## 2. 机读字段建议（供 G7-3／G8／tooling 引用）

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `imp_state` | ✓ | 取值 **仅** G7-1 §2 正式名 |
| `artifact_id` | ✓ | 单次 AI 导入 artifact 稳定 ID（与 `ticket_id` 可同可异，须在 PM 轨对账） |
| `ticket_id` | ✓ | 关联施工票或任务卡 |
| `primary_change_class` | 自 `IMP-AI-READY` 起 ✓ | G6-1 **CHG-*** |
| `entry_evidence_refs` | ✓ | 满足 entry 的 **ART-*** ID 列表（可含占位，见 §6） |
| `entry_owner_role` | ✓ | 本态 **主责** owner（§3.2 枚举） |
| `entry_recorded_at` | 建议 | ISO-8601；谁写入由 tooling 定 |
| `rework_record` | 仅 `IMP-REWORK` | 失败关口、`rework_target`、`rework_reason`（形状见 G7-3 §5） |

本档 **不** 定义 exit 字段（如 `exit_criteria_met`）→ G7-3。

---

## 3. 全局 Entry 规则

### 3.1 适用全体 IMP-*

1. **状态名**：仅 G7-1 正式名；禁止 G8 占位别名写入 `imp_state`（映射见 §6）。  
2. **证据**：`entry_evidence_refs` 须能指向可检索载体（文件路径语义、JSON 附件 ID、Work Report 节号）；**禁止**用自然语言 alone 代替 artifact 引用。  
3. **CHG 记录**：自 `IMP-AI-READY` 起，`primary_change_class` 必填且须与票面允许动作一致（G6-2）。  
4. **高险**：`CHG-HIGH-RISK` 或票面 `guard_verdict_id` 要求时，须有 **guard `allow`**（或尚書省书面 override 留痕）方可进入 `IMP-AI-READY` 及之后任何态。  
5. **并行维度**：queue／battle_report／route 仅作 **blocker 输入**，其值 **不得** 拷贝进 `imp_state`。

### 3.2 Owner 角色枚举（entry 主责）

| `entry_owner_role` | 职责摘要 |
|--------------------|----------|
| `pm` | 范围、澄清、观测期窗口 |
| `design` | 规格、评审包、设计缺口 |
| `engineering` | AI 施工、Work Report、证据包 |
| `governance` | 风险校验、禁区／override 对账 |
| `qa` | checker 验收、smoke 收口 |
| `release` | 发布裁决与执行确认 |
| `orchestrator` | 多轨对齐、拆票、queue 结构票 meta |

一人可兼多角；**主责**仅一位写入 `entry_owner_role`，协作方写入 artifact 元数据。

### 3.3 全局 Blockers（未解除则**任何**前向 IMP 均不可进入）

| Blocker ID | 条件 | 解除方向 |
|------------|------|----------|
| `BLK-NO-ARTIFACT-ID` | 无 `artifact_id` | PM 轨登记 |
| `BLK-INTAKE-REJECT` | intake 子域 `reject`／`auto_rejected` 且未开新 artifact | 新 artifact 或 intake 复核 |
| `BLK-ROUTE-PHASE` | 本 artifact 所需 `task_type` 的 `assignable:false` | 解除 phase_gate 或改 task_type／拆票 |
| `BLK-GUARD-STOP` | `stop_work` 或 `deny` 且无 override 留痕 | guard 重审或尚書省裁決 |
| `BLK-QUEUE-TICKET` | 关联施工票 `BLOCKED` **且** 该阻塞列为本 artifact 硬依赖 | 前置票 `DONE` 或拆依赖 |

---

## 4. 分状态 Entry 条件

> 每表列：**进入前提**｜**最少 artifact／evidence**｜**owner**｜**态内 blockers**（未解除则**不可**标称已进入该态）。

### IMP-SCOPE-DRAFT

| 项 | 内容 |
|----|------|
| **进入前提** | （A）新注册 AI 导入 artifact；或（B）intake `accept` 后首次挂入主线（**不**把 `accept` 写入 `imp_state`）；或（C）自 `IMP-REWORK` 回退目标为范围重拟（回退边 → G7-3）。**无**要求前序 `imp_state`。 |
| **最少 artifact／evidence** | **ART-PM-SCOPE**（见 G8-1 `10_pm.md` §4.1）：`import_intent`、`target_artifact_kind`、粗粒度 `in_scope`／`out_scope`；`ticket_id`；可选 `secondary_change_classes` |
| **owner** | `pm`（尚書省可代行，须记入 evidence） |
| **态内 blockers** | 无法陈述「导入什么」；`BLK-INTAKE-REJECT`；同一 `artifact_id` 重复开户无治理批注 |

---

### IMP-SPEC-CLARIFY

| 项 | 内容 |
|----|------|
| **进入前提** | 前序 `imp_state` 为 `IMP-SCOPE-DRAFT`，或 `IMP-REWORK` 且 G7-3 指定回到澄清（目标态在 rework 记录中）。 |
| **最少 artifact／evidence** | **ART-PM-SCOPE** 已更新；**ART-DES-SPEC**（见 G8-2 `20_design.md` §4.1）：`open_questions` 列表、`dependencies[]`、`acceptance_criteria_draft`；G8 五轨字段缺口清单（可引用 G8 README 索引） |
| **owner** | `pm` · `design`（主责 `pm`） |
| **态内 blockers** | `import_intent` 仍为空；硬依赖票 queue `BLOCKED` 未解；开放问题未**列举**（禁止静默缺口） |

---

### IMP-AI-READY

| 项 | 内容 |
|----|------|
| **进入前提** | 前序 `IMP-SPEC-CLARIFY`；澄清闭环：**全部** `open_questions` 已关闭，或每项已登记 `owner`+`defer_reason`+目标态；`primary_change_class` 已填；G6-2 拟执行 **ACT-*** 与 class 行一致。 |
| **最少 artifact／evidence** | **ART-ENG-CTX**（G8-3）：`role`、`allowed_scope`、`forbidden_zone_types`、`ticket_id`；**ART-PM-SCOPE**／**ART-DES-SPEC** 与 class 边界一致；若票面要求：**guard `allow`** 或 override 留痕 |
| **owner** | `engineering` |
| **态内 blockers** | 缺 ART-ENG-CTX 必填项；`BLK-GUARD-STOP`；`BLK-ROUTE-PHASE`（拟派 `dark.*` 等）；G10 禁止情境命中且无人工裁決（见 G10-2 `20_no_blind_trust.md` §5.3）；**禁止**将 queue `DOING` 当作本态证据 |

**G8 占位对账**：Eng 轨 `IMP-ACTIVE` 入口门槛 **对齐本态**（非 `IMP-SPEC-CLARIFY` 施工中态）。

---

### IMP-REVIEW-READY

| 项 | 内容 |
|----|------|
| **进入前提** | 前序 `IMP-AI-READY`；AI／人工混合产出已**齐套**待审（不要求评审已通过）。 |
| **最少 artifact／evidence** | **ART-ENG-WR** 草案（G8-3 §4.2 七节齐全或显式「无」）；**ART-ENG-FIVE**；变更清单 §1 与实 diff 一致；可选 **ART-DES-REVIEW-PKG**（占位） |
| **owner** | `design`（主责）；`engineering` 维护 WR |
| **态内 blockers** | 有 diff 但 §1 为空；§3 placeholder 未分栏却宣称完成；评审包缺 peer 可见载体 |

**G8 占位对账**：`IMP-VERIFY` **入口**须已有 WR 草案 + 证据 → 对应本态后期／`IMP-QA-READY` 前段；**不得**将 checker `accepted` 当作本态 entry。

---

### IMP-RISK-VALIDATION

| 项 | 内容 |
|----|------|
| **进入前提** | 前序 `IMP-REVIEW-READY`；评审包已提交（结论可为待决）。 |
| **最少 artifact／evidence** | **ART-ENG-WR**；**ART-GOV-RISK**（占位，待 G10／guard 合并）：`change_class`、禁区类型对照、`override`+留痕位置（合約 Rule 12）；票面要求时 **guard JSON** 或 `governance-guard` 输出引用 |
| **owner** | `governance` |
| **态内 blockers** | `CHG-HIGH-RISK` 无 guard 结论；触 §7 禁区类型无 override；`scope_check.within_ticket:false`（QA 轨语义，entry 前即应可见）；**禁止**用 route `assignable:false` 代替风险校验完成 |

---

### IMP-QA-READY

| 项 | 内容 |
|----|------|
| **进入前提** | 前序 `IMP-RISK-VALIDATION`；风险关口 **已通过**（留痕：risk sign-off 或 guard／尚書省等效记录 — exit 细节 G7-3）。 |
| **最少 artifact／evidence** | **ART-ENG-EVD** + **ART-ENG-DOD**（G8-3）；**ART-ENG-WR** §4 非空（若宣称为可交付路径）；可选 **ART-QA-SMOKE** 预填（占位） |
| **owner** | `qa`（checker-reviewer 执行） |
| **态内 blockers** | 风险未通过仍跳态；§4 `commands` 为空却宣称可交付；`BLK-GUARD-STOP`；battle_report `partial` **不**满足本态（战报域独立） |

**G8 占位对账**：`IMP-VERIFY` **正式映射**为本态；checker 开工 entry 见 G8-4 §4.1。

---

### IMP-RELEASE-DECISION

| 项 | 内容 |
|----|------|
| **进入前提** | 前序 `IMP-QA-READY`；QA 收口完成。 |
| **最少 artifact／evidence** | **ART-QA-REV**：`verdict` ∈ {`accepted`, `accepted_with_gaps`}；**ART-QA-DOD** 四键无 false；**ART-REL-DEC**（见 G8-5 `50_release_owner.md` §4.1）：发布范围、受众／环境、回退策略草案 |
| **owner** | `release` |
| **态内 blockers** | `verdict` ∈ {`rejected`, `blocked`}；`accepted:true` 但 evidence `exit_ok:false`；smoke 门禁票 Fail（**ART-QA-SMOKE**）；queue 票 `DONE` **不**证明可发布 |

**G8 占位对账**：`IMP-ARCHIVE-PENDING` **对齐本态**（QA 通过、待发布裁决／封存前窗口）。

---

### IMP-RELEASED

| 项 | 内容 |
|----|------|
| **进入前提** | 前序 `IMP-RELEASE-DECISION`；**发布裁决 = approve**（载体 G8-5）。 |
| **最少 artifact／evidence** | **ART-REL-EXEC**（见 G8-5 `50_release_owner.md` §4.2）：`release_id`、`target_audience_or_env`、`published_at`；执行证据（文档版本号、配置生效摘要、tag 等 — 不贴 secret） |
| **owner** | `release` |
| **态内 blockers** | 裁决 pending／reject；`CHG-HIGH-RISK` 无回退 playbook；目标环境未确认生效 |

---

### IMP-OBSERVING

| 项 | 内容 |
|----|------|
| **进入前提** | 前序 `IMP-RELEASED`；发布已在目标受众／环境**确认**。 |
| **最少 artifact／evidence** | **ART-PM-OBS-PLAN**（占位）：观测窗口、`signals[]`、退出观测条件草案；基线指标或「无指标」声明 |
| **owner** | `pm` |
| **态内 blockers** | 发布未确认；观测窗口未定义；在本态开展**新 scope** 施工（应新 artifact 或 `IMP-REWORK`） |

**G8 占位对账**：`IMP-ARCHIVED`（战报已 append）**不等于**本态；append 可在 `IMP-RELEASE-DECISION` 后并行发生，**不**替代 `imp_state` 前进至观测。

---

### IMP-REWORK

| 项 | 内容 |
|----|------|
| **进入前提** | 自 `IMP-REVIEW-READY`／`IMP-RISK-VALIDATION`／`IMP-QA-READY`／`IMP-RELEASE-DECISION` 任一处**关口失败**（exit 定义 G7-3）；或 checker `rejected`／`blocked`；或 release 裁决 reject。 |
| **最少 artifact／evidence** | **`rework_record`**（G7-3 §5）：`failed_gate`、`rework_reason`、`rework_target`（∈ G7-3 §5.2 合法回退表）；失败关口 **ART-*** 引用（如 **ART-QA-REV**） |
| **owner** | `engineering`（主责回修）；`pm` 协调整体范围；自 `IMP-QA-READY` 进入须 **checker** 确认 rework plan（G7-3 §2.3） |
| **态内 blockers** | 无 `rework_record`；`rework_target` 为空或指向禁止跳关态；与 `BLK-INTAKE-REJECT` 混淆（入站拒绝 → 新 artifact，非返工） |

**不等于**：queue `BLOCKED`（票依赖）；battle_report `blocked`（战报域）。

---

## 5. Owner／Blocker 规则摘要

| 规则 | 说明 |
|------|------|
| **单主责** | 每态 entry 仅一个 `entry_owner_role`；副责写入 ART 元数据 |
| **主责≠验收方** | `engineering` 产 WR；`qa`／`governance` **不得**与 worker 同人兼任验收（合約 Rule 11 精神） |
| **blocker 优先** | §3.3 全局 blocker 优先于态内 blocker |
| **route 只拦不推** | `assignable:false` 阻止进入依赖该路由的态，**不**自动推进任一 IMP |
| **queue 只拦票** | 施工票 `BLOCKED` 仅当票面声明为本 artifact 硬依赖时生效 |
| **battle_report 不驱动** | `draft`／`done` 不触发 IMP 迁移；仅作 OPS 并行记录 |

---

## 6. G8 占位 IMP-* → 正式 IMP-*（待对账表）

> G8-A（Eng+QA）v0.1 使用下列占位；**禁止**写入 `imp_state`。G8-1／2／5 完成后由对账票更新各轨 md。

| G8 占位 | 建议正式态（G7-1） | Entry 权威段落 |
|---------|-------------------|----------------|
| `IMP-OPEN` | （非 G7 态）→ 触发 `IMP-SCOPE-DRAFT` | §4 IMP-SCOPE-DRAFT |
| `IMP-ACTIVE` | 并行窗口：`IMP-AI-READY` … `IMP-REVIEW-READY` | §4 IMP-AI-READY（≠ 单态；见 G7-3 §1.3） |
| `IMP-VERIFY` | `IMP-QA-READY` | §4 IMP-QA-READY；WR 草案门槛见 `IMP-REVIEW-READY` |
| `IMP-ARCHIVE-PENDING` | 并行：`IMP-RELEASE-DECISION` 前后 | §4 IMP-RELEASE-DECISION |
| `IMP-ARCHIVED` | 并行：ops `cycle_states.archived` | **不**映射 `IMP-OBSERVING`；观测 entry 见 §4 IMP-OBSERVING |

**待对账票建议**：`G8-RECON-IMP`（或 CHK-W1 子项）— 更新 `30_engineering.md`／`40_qa.md` §2 与本表一致。

---

## 7. 与 G6／G10／release gate 的挂钩（entry 侧）

| 模块 | entry 引用方式 |
|------|----------------|
| **G6-1** | `primary_change_class` 自 `IMP-AI-READY` 必填 |
| **G6-2** | 进入 `IMP-AI-READY` 前拟执行 ACT 须落在 class 允许集 |
| **G10** | `IMP-AI-READY` 起宜满足 AI usage boundary；`IMP-RISK-VALIDATION` 宜引用 no-blind-trust 清单（占位） |
| **release gate** | 仅 `IMP-RELEASE-DECISION`→`IMP-RELEASED` 消费 **ART-REL-***（G8-5） |

---

## 8. 风险与 TODO（本票）

| ID | 项 | 严重度 | 处理 |
|----|-----|--------|------|
| T1 | **ART-PM-***／**ART-DES-***／**ART-REL-*** 仍为占位 | 中 | G8-1／2／5 定稿后回填 §4 表 |
| T2 | G8 §2 仍写「待 G7-1」— 应改为引用 **本档** | 低 | **已解**（G8-RECON-IMP · W2-1-ENG） |
| T3 | `IMP-ACTIVE` 与「施工中」时间轴可能需 G7-3 子态或注释 | 低 | G7-3 exit／子状态讨论 |
| T4 | intake → `IMP-SCOPE-DRAFT` 触发边未机读 | 低 | Wave 2 tooling |
| T5 | CHK-W1 须验证 entry 与 G8 QA `verdict` 表无矛盾 | 中 | checker 只读 |

---

## 9. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G7-2 初版：10 态 entry + 全局规则 + G8 占位对账表 |
| 2026-05-27 | G8-RECON-IMP（W2-1-ENG）：G8-1/2/5、G10-2 §5.3 交叉引用；Release 执行记录 ID 对账为 **ART-REL-EXEC** |
