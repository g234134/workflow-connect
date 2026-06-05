# G8 — Design Artifact Contract（v0.1）

> **票号**：G8-2（与 G8-B 合并交付 Design 轨）  
> **状态**：v0.1 草案；可被 G8 总览与 G10 rulebook 引用  
> **权威母本**：`G7_state_machine/20_entry_conditions.md` §4；`30_exit_and_transitions.md` §3；`workflow_upgrade/01_context-entry/40_navigation_map_template.md`（规格层字段写法）；`04_Workflows/ENGINEERING_CONTRACT.md` Rule 4（结构化 `dict` 精神）  
> **不覆盖**：PM 范围票（见 `10_pm.md`）；Eng Work Report 全文；QA verdict；完整 release gate；production code

---

## 1. 轨定位

**ART-DES-*** 定义 **design owner**（G7-2 §3.2 `entry_owner_role: design`）在澄清、评审关口必须产出的**规格与评审**交付物。Design 轨**消费** **ART-PM-SCOPE**，为 **ART-ENG-WR** 与 peer review 提供可审载体；**禁止**将 A4 navigation map 实例全文复制进 spec（仅引用 `entry_refs` 逻辑名）。

**角色边界**：本档使用 G7 owner 枚举 `design`；peer reviewer 可为同票指定的只读审阅者，**不**必须是暗部或 HQ 编制角色。

---

## 2. G7 占位状态（待对账）

| 占位别名 | Design 语义 | 建议正式态（G7-1） |
|----------|-------------|-------------------|
| — | 规格与开放问题 | `IMP-SPEC-CLARIFY` |
| — | 产出齐套待审 | `IMP-REVIEW-READY` |
| — | 评审结论 | `IMP-REVIEW-READY` exit → `IMP-RISK-VALIDATION` |
| `IMP-ACTIVE` | 施工窗口内设计增量 | 并行 `IMP-AI-READY` … `IMP-REVIEW-READY`（见 G7-3 §1.3） |

正式名 ↔ 占位映射 **待 G8-RECON-IMP** 与 Eng／QA §2 一并更新。

---

## 3. 核心 Artifact 一览

| ID | 名称 | 载体 | 主要来源 |
|----|------|------|----------|
| **ART-DES-SPEC** | Design Spec（设计规格） | Markdown 或 JSON | G7-2 §4 IMP-SPEC-CLARIFY |
| **ART-DES-REVIEW-PKG** | Review Package（评审包） | Markdown + 附件索引 | G7-2 §4 IMP-REVIEW-READY（可选） |
| **ART-DES-REV** | Design Review Verdict（设计评审结论） | 结构化 JSON 或表 | G7-3 §3 IMP-REVIEW-READY exit |

---

## 4. 分 Artifact 契约

### 4.1 ART-DES-SPEC — Design Spec

**目的**：将 PM scope 转化为可施工、可验收的规格草案；承载 open questions 与依赖，直至澄清闭环。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `artifact_id` | ✓ | 与 **ART-PM-SCOPE** 一致 |
| `ticket_id` | ✓ | 关联票号 |
| `spec_summary` | ✓ | 2–8 条要点（人读） |
| `open_questions` | ✓ | 与 **ART-PM-CLARIFY** 可对账的同一列表或显式 `sync_ref` |
| `dependencies` | ✓ | 硬依赖：`ticket_id`／artifact／runbook；含 `status`（`ok` \| `blocked` \| `TBD`） |
| `acceptance_criteria_draft` | ✓ | 验收口径草案（可引用 runbook §、runner 逻辑名、`acceptance_commands`） |
| `interface_sketch` | — | 核心路径预期 `dict` 键或 API 形状摘要（**不**在此档新增 collection 名并宣称为已验收） |
| `navigation_refs` | — | 若涉 context 派工：有序 `entry_refs` 逻辑名（对齐 A4 §4.1） |
| `out_of_design` | — | 明确不属于本 spec 的项（防 scope creep） |

| 类别 | 规则 |
|------|------|
| **blocker** | 缺 `acceptance_criteria_draft`；`dependencies` 含 `blocked` 却未写入 PM clarify 阻塞；与 **ART-PM-SCOPE** `out_scope` 冲突且无 override |
| **IMP 门槛** | **`IMP-SPEC-CLARIFY` entry 前**须草案就绪；**`IMP-AI-READY` entry 前**须与 PM clarify 同步（open questions 闭环） |
| **确认方** | **design owner** 产出；**PM（`pm`）** 对 scope 边界会签 |

---

### 4.2 ART-DES-REVIEW-PKG — Review Package

**目的**：在 `IMP-REVIEW-READY` 向 peer／design reviewer 提供**齐套、可检索**的评审材料索引；可与 **ART-ENG-WR** 合并呈现，但须独立可 grep。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `artifact_id` | ✓ | 与 spec 一致 |
| `review_targets` | ✓ | 待审产出列表（如 WR 草案路径语义、diff 范围、spec 版本） |
| `spec_ref` | ✓ | 指向 **ART-DES-SPEC** 版本或锚点 |
| `eng_wr_ref` | ✓ | 指向 **ART-ENG-WR**（草案即可） |
| `known_gaps` | ✓ | 已知 skeleton／placeholder；无则 `[]` |
| `reviewer_notes` | — | 派工给 peer 的焦点问题（≤5 条） |

| 类别 | 规则 |
|------|------|
| **blocker** | 有 diff 但 `review_targets` 为空；缺 peer 可见载体（仅 chat 口头）；`known_gaps` 与 WR §3 不一致 |
| **IMP 门槛** | **`IMP-REVIEW-READY` entry 前**（强烈建议）；纯 trivial 票可标 `N/A` 并记入 **ART-PM-GAPS** |
| **确认方** | **design owner** 维护；**engineering owner** 保证 WR 引用有效 |

**触发**：票面含设计评审、跨模块接口、或 G6 `CHG-HIGH-RISK` 时 **不得** 标 `N/A`。

---

### 4.3 ART-DES-REV — Design Review Verdict

**目的**：记录 peer／design review 结论；支撑 `IMP-REVIEW-READY` exit → `IMP-RISK-VALIDATION`。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `artifact_id` | ✓ | 与 spec 一致 |
| `ticket_id` | ✓ | 关联票号 |
| `verdict` | ✓ | `approved` \| `approved_with_gaps` \| `rejected` |
| `reviewer_role` | ✓ | 固定语义 `peer` 或 `design`（**不**写 HQ 职位名） |
| `gaps` | ✓ | 无则 `[]`；`approved_with_gaps` 须非空 |
| `p0_blockers` | ✓ | 无则 `[]`；非空则 **不得** `approved` |
| `wr_section3_delta` | 条件 | 若 gaps 须写入 Eng WR §3，列已同步字段 |
| `message` | ✓ | 一句收口给 PM／Eng |

| 类别 | 规则 |
|------|------|
| **blocker** | `verdict: rejected` 却推进 `IMP-RISK-VALIDATION`；`approved_with_gaps` 但 gaps 未写入 WR §3；`p0_blockers` 非空却 `approved` |
| **IMP 门槛** | **`IMP-REVIEW-READY` exit 前** |
| **确认方** | **peer reviewer** 或 **design owner**（二者不得与施工 worker 同人，合約 Rule 11 精神）；**PM** 对 scope 级 reject 知情 |

**verdict 与 IMP 关系（v0.1）**

| verdict | 可 exit REVIEW-READY | 说明 |
|---------|:--------------------:|------|
| `approved` | ✓ | 无 P0 |
| `approved_with_gaps` | ✓ | gaps 已入 WR §3 |
| `rejected` | ✗ | → `IMP-REWORK`（G7-3 §5.1） |

---

## 5. Design 轨 Blocker 字段汇总

| Artifact | Blocker 字段／条件 |
|----------|-------------------|
| ART-DES-SPEC | 缺 acceptance／dependencies；与 PM scope 冲突 |
| ART-DES-REVIEW-PKG | 有产出无 review_targets；gaps 与 WR 不一致 |
| ART-DES-REV | rejected 却跳关；P0 未关闭却 approved |

---

## 6. 与 Eng／QA 的边界

| 关系 | 规则 |
|------|------|
| Design → Eng | **ART-DES-SPEC** `acceptance_criteria_draft` 须可被 **ART-ENG-EVD** 与 **ART-QA-EVD** 重跑验证 |
| Design → QA | checker **不**代替 design review；**ART-QA-REV** 消费 Eng 证据，**不**覆盖 **ART-DES-REV** |
| A4 nav map | `navigation_refs` 仅列逻辑路径；字段定义见 A4 §4，**不**在本档复制 deny 细则 |
| skeleton | 设计层 placeholder 须与 WR §2–§3 分栏一致（合約 Rule 7） |

---

## 7. 引用索引

| 主题 | 路径 |
|------|------|
| PM 轨 | 本目录 `10_pm.md` |
| Eng 轨 | 本目录 `30_engineering.md` |
| QA 轨 | 本目录 `40_qa.md` |
| A4 模板 | `workflow_upgrade/01_context-entry/40_navigation_map_template.md` |
| G7 exit（review） | `workflow_v2/10_governance/G7_state_machine/30_exit_and_transitions.md` §3 IMP-REVIEW-READY |

---

## 8. 修订记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-05-27 | v0.1 | G8-B 首版 Design 轨；IMP-* 占位待 G7 对账 |

---

## 附录 A — W2-1 试点实例索引（非 normative）

> **性质**：施工实例；**不**修改 §4 契约定义。  
> **artifact_id**：`W2-1-G8-RECON-PILOT`  
> **案卷**：`workflow_v2/20_pilot/W2-1_case/`

| ART ID | 实例路径 | IMP 态挂钩 | 状态 |
|--------|----------|------------|------|
| **ART-DES-SPEC** | `20_pilot/W2-1_case/03_art_des_spec.md` | `IMP-SPEC-CLARIFY` entry／`IMP-AI-READY` entry 前同步 | W2-1-PM-DES ✓ |
| **ART-DES-REVIEW-PKG** | — | `IMP-REVIEW-READY` entry | **N/A**（trivial 票；见 ART-PM-GAPS） |
| **ART-DES-REV** | — | `IMP-REVIEW-READY` exit | **N/A**（trivial 票） |

**实例要点（ART-DES-SPEC）**：6 条 spec_summary + 6 条 `acceptance_criteria_draft`（grep spot-check）；`open_questions` 经 `sync_ref` 与 **ART-PM-CLARIFY** 对账；无 `interface_sketch`／`navigation_refs`（纯文档票）。
