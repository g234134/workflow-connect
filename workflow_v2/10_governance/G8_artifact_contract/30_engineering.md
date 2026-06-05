# G8 — Engineering Artifact Contract（v0.1）

> **票号**：G8-3（与 G8-A 合并交付 Eng 轨）  
> **状态**：v0.1 草案；可被 G8 总览与 G10 rulebook 引用  
> **权威母本**：`04_Workflows/ENGINEERING_CONTRACT.md` 附录 A、§7.1–§7.2、§10.4（C10–C11）；`AGENTS.md` §封存协议  
> **不覆盖**：PM / Design / Release 轨；`battle_report` JSON 全文（见 QA 轨 `ART-QA-BR`）；release gate

---

## 1. 轨定位

**ART-ENG-*** 定义施工 worker（含 `implementation-worker`、暗部 Agent、HQ worker）在单票生命周期内必须产出的**工程交付物**。人读主载体为 **Work Report**；机读摘要可嵌入 checker 外层 JSON 或 battle report 的 `results` 字段，但**不得**用 battle report 替代 Work Report 七节正文。

---

## 2. G7 占位状态（并行索引 · G7-1 已冻结）

**G7-1 状态名已冻结**（见 `G7_state_machine/10_workflow_states.md` §2）。下列 **IMP-* 占位别名**保留作 Eng/QA 轨施工票级并行索引；**禁止**写入 `imp_state`。正式态 entry/exit 权威见 G7-2／G7-3；对账票 **G8-RECON-IMP**（W2-1-ENG）已更新交叉引用。

| 占位别名 | 语义 | 对账参考 |
|----------|------|----------|
| `IMP-OPEN` | 接战／票已受理，尚未动档 | `ops_cycle_schema.json` → `cycle_states.open` |
| `IMP-ACTIVE` | 施工中（Context → Incremental） | G7-2 §4 **IMP-AI-READY** … G7-3 **IMP-REVIEW-READY** 并行窗口 |
| `IMP-VERIFY` | 自称完成，证据已收集，待 checker | G7-2 §4 **IMP-QA-READY**（G7-1 正式名） |
| `IMP-ARCHIVE-PENDING` | 通过 QA 收口，待封存 append | G7-2 §4 **IMP-RELEASE-DECISION** 并行窗口 |
| `IMP-ARCHIVED` | 战报已 append Progress | ops `cycle_states.archived`；**≠** `IMP-OBSERVING` |

---

## 3. 核心 Artifact 一览

| ID | 名称 | 载体 | 主要来源 |
|----|------|------|----------|
| **ART-ENG-CTX** | Context Brief（起手式） | chat 首段或 Work Report 前言 | 合約 Rule 1；四流派 CD |
| **ART-ENG-WR** | Work Report | Markdown（合約附录 A 七节） | `ENGINEERING_CONTRACT.md` 附录 A |
| **ART-ENG-FIVE** | C11 五要素摘要 | Work Report 内嵌或 chat 收口段 | 合約 §10.4（C11） |
| **ART-ENG-EVD** | 验证证据包 | Work Report §4 + 可选 `metrics` | 合約 §4.4 DB 流派；Rule 11 |
| **ART-ENG-DOD** | 单票 DoD 自检 | Work Report §2–§7 或 checklist 块 | 合约 §7.1 FLOW-6.5 |
| **ART-ENG-BOARD** | 暗部板块本轮 DoD（可选） | workspace 三件套 + progress 四栏 | 合約 §7.2（C10） |

---

## 4. 分 Artifact 契约

### 4.1 ART-ENG-CTX — Context Brief

**目的**：施工前声明角色、可碰范围、禁区类型（引用宪法 §7 类型，不列实例路径）。

| 类别 | 字段 / 内容 |
|------|-------------|
| **必填** | `role`（执行角色）；`allowed_scope`（可碰模块／路径语义）；`forbidden_zone_types`（禁区别名或宪法 §7 类型引用）；`ticket_id` |
| **建议** | `plan_summary`（2–5 行重大行动前计划） |
| **blocker** | 缺 `role`／`allowed_scope`／`forbidden_zone_types` 任一即不得进入 `IMP-ACTIVE` 改档 |
| **IMP 门槛** | **`IMP-ACTIVE` 入口前**必须就绪 |
| **确认方** | **施工 worker** 自检；**checker-reviewer** 抽检（`dod_checklist.context_source`） |

---

### 4.2 ART-ENG-WR — Work Report

**目的**：单票人读交付主文档；七节结构为 G8 Eng 轨** normative 形状**。

| 节 | 标题 | 必填 | 说明 |
|----|------|:----:|------|
| 元数据 | 任务／角色／日期 | ✓ | 合約附录 A 表头三行 |
| §1 | 变更档案 | ✓ | 新建／修改列表；无改档须写「无档案变更」 |
| §2 | 可执行 skeleton | ✓ | 无则写「无」 |
| §3 | placeholder（未完成） | ✓ | 无则写「无」；**不得**与 §2 混栏 |
| §4 | 验证证据 | ✓ | 命令／runner + 关键结果（含 `ok` 语义） |
| §5 | 阻塞 | ✓ | 无则写「无」 |
| §6 | 下一步建议 | ✓ | 至少一条或「无」 |
| §7 | 宪法／合约 | ✓ | `override`（无／有）+ `留痕位置` |

| 类别 | 规则 |
|------|------|
| **blocker** | §1–§7 任一缺失；§4 在宣称为可交付时为空；§3 非空但未在 §4 标为未验证；§7 有 override 但无留痕位置 |
| **IMP 门槛** | **`IMP-VERIFY` 入口前**必须草案就绪；**`IMP-ARCHIVE-PENDING` 入口前**须定稿（checker 可引用） |
| **确认方** | **checker-reviewer** 对照附录 A 七节；**尚書省** 仅在高风险 override 时裁決 |

---

### 4.3 ART-ENG-FIVE — C11 五要素摘要

**目的**：满足 Conditions C11／合約 §10.4 最低回报名；可与 Work Report 合并呈现，但五要素须**可 grep**。

| 必填要素 | 对应 Work Report |
|----------|------------------|
| 变更清单 | §1 |
| skeleton 状态 | §2 |
| placeholder 状态 | §3 |
| 阻塞 | §5 |
| 下一步 | §6 |

| 类别 | 规则 |
|------|------|
| **blocker** | 有 diff 但变更清单为空；placeholder 未分栏却宣称为完成 |
| **IMP 门槛** | **`IMP-ARCHIVE-PENDING` 入口前** |
| **确认方** | **checker-reviewer**（与 `ART-ENG-WR` 同步验） |

---

### 4.4 ART-ENG-EVD — 验证证据包

**目的**：Debugging 流派可审计证据；形状对齐合約附录 B 之 `ok`／`message` 语义，**不**在此档重定义 collection 名。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `commands` | ✓ | 实际执行之命令／runner 列表 |
| `key_results` | ✓ | 每条命令之关键输出语义（含结构化 `ok`） |
| `blocked` | — | 若验证不可跑，须 `true` 且附 `blocked_reason` |
| `metrics` | — | 可选；对齐 smoke runbook 之 `RUNTIME_METRIC` |

**Smoke 票附加**（引用 runbook §6／§9）：须含 Pass／Partial／Fail 判定及 runbook 要求之结构化摘要（如 Gov Core：`health.all_ok`、`ingest.ok`；RAG：`len(sources) >= 1` 等）。

| 类别 | 规则 |
|------|------|
| **blocker** | 宣称为可交付但 `commands` 为空；`key_results` 无 `ok` 语义；runner 失败却未写入 §5 阻塞 |
| **IMP 门槛** | **`IMP-VERIFY` 入口前**（与 ART-ENG-WR §4 同步） |
| **确认方** | **checker-reviewer** 重跑 `acceptance_commands` 或等价 runner；**不**由 worker 单方标 PASS |

---

### 4.5 ART-ENG-DOD — 单票 DoD 自检

**目的**：合約 §7.1 FLOW-6.5 可勾选清单；协调官无改档票可简化为「无档案变更」声明。

| 自检项 | 必填 | blocker 条件 |
|--------|:----:|--------------|
| Context + Source 已读可追溯 | ✓ | 否 → 不得 `IMP-VERIFY` |
| 核心路径回传结构化 `dict`（若适用） | ✓ | 适用却缺失 → blocker |
| Work Report 已填 | ✓ | 否 → blocker |
| skeleton／placeholder 已分栏 | ✓ | 混栏 → blocker |
| 已验证或已标阻塞 | ✓ | 无证据却标完成 → blocker |
| 无未留痕违宪／违合约 | ✓ | 有 override 无留痕 → blocker |
| 四流派最低覆盖 | ✓ | 缺 Debugging 证据 → blocker |

| IMP 门槛 | **`IMP-VERIFY` 入口前** worker 自检；**`IMP-ARCHIVE-PENDING` 入口前** checker 复验 |
| 确认方 | **checker-reviewer** 映射至 `dod_checklist`（见 `40_qa.md`） |

---

### 4.6 ART-ENG-BOARD — 暗部板块本轮 DoD（C10 · 条件触发）

**触发**：票涉及暗部四 Agent 板块整轮交付（合約 §7.2 C10）。

| 必填 | 说明 |
|------|------|
| workspace 三件套 | `brief.md`／`notes.md`／`progress.md`（或等价三件套） |
| 可执行 agent | 对应 department agent 可启动 |
| 对应 `core` | 板块 `core` 模块就位 |
| progress 四栏 | 完成／未完成／阻塞／下一步 |

| 类别 | 规则 |
|------|------|
| **blocker** | 四栏缺一；宣称为板块完成但 agent 不可执行 |
| **IMP 门槛** | 板块级 **`IMP-ARCHIVE-PENDING` 前** |
| **确认方** | **Governance Agent** 或 **checker-reviewer**（只读验收）；里程碑编号以 Progress 为准，本档不新增编号 |

---

## 5. Eng 轨 Blocker 字段汇总

| Artifact | Blocker 字段／条件 |
|----------|-------------------|
| ART-ENG-CTX | 缺 `role`／`allowed_scope`／`forbidden_zone_types` |
| ART-ENG-WR | §1–§7 任一缺失；§4 空却宣称交付 |
| ART-ENG-FIVE | 有 diff 无变更清单；placeholder 未诚实分栏 |
| ART-ENG-EVD | 无 `commands`／`key_results`；失败未标阻塞 |
| ART-ENG-DOD | 任一项 FLOW-6.5 为否却推进状态 |
| ART-ENG-BOARD | C10 四栏或三件套不齐（仅 C10 票） |

---

## 6. 与 battle_report 的边界

| 关系 | 规则 |
|------|------|
| Work Report → battle report | `executed`／`results`／`blockers`／`next_steps` 可**摘要映射**自 Work Report §1／§4／§5／§6；**不**替代七节正文 |
| 字段权威 | battle report **必填**见 `ops_cycle_schema.json` → `battle_report.required_fields`；渲染标题见 `section_titles` |
| 封存 | 全量封存步骤见 schema `archive_protocol.full_steps`；Eng 轨负责备好 Work Report 与证据，**不**定义 archive 闸机 |

---

## 7. 引用索引

| 主题 | 路径 |
|------|------|
| Work Report 模板 | `04_Workflows/ENGINEERING_CONTRACT.md` 附录 A |
| C10／C11 | 合約 §7.2、§10.4；`_PORTABLE_CORE_INDEX.md` C10–C11 |
| QA 收口 | 本目录 `40_qa.md` |
| G7 状态（待对账） | `workflow_v2/10_governance/G7_state_machine/` |
| Smoke 验收 | `04_Workflows/runbooks/*_SMOKE_TEST_RUNBOOK_v0.1.md` §6、§9 |

---

## 8. 修订记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-05-27 | v0.1 | G8-A 首版 Eng 轨；IMP-* 占位待 G7 对账 |
| 2026-05-27 | v0.1.1 | G8-RECON-IMP（W2-1-ENG）：§2 改引 G7-1 `10_workflow_states.md`；占位表作并行索引 |
