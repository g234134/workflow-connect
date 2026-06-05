# G8 — Governance Risk Artifact Contract（v0.1）

> **票号**：G8-6（GOV 轨；与 W2-3 总控规格同批交付）  
> **状态**：v0.1 定稿（契约层）；**无** runtime／CI enforcement（→ `20_pilot/W2-3_minimal_gate_design.md`；施工票 W2-3-MINIMAL-GATE-*）  
> **上游**：`G10_governance_rulebook/20_no_blind_trust.md`（G10-2 §2–§4、§6.3）；`G6_scope_control/`（CHG-*）；`G7_state_machine/`（`IMP-RISK-VALIDATION`）  
> **下游**：G10-2 §5.3／§6.3；最小治理 gate（文档层）；案卷 `ART-GOV-RISK` 实例（→ W2-3-GOV-RISK-PILOT）  
> **不覆盖**：Work Report 七节全文（**ART-ENG-WR**）；验证命令原文（**ART-ENG-EVD**）；checker verdict（**ART-QA-REV**）；完整 release gate（G8-5 out of scope）

---

## 1. 轨定位

**ART-GOV-RISK** 是 **G8 GOV 轨** 在 `IMP-RISK-VALIDATION` 的**结构化治理风险摘要**：把 G10-2 的 no-blind-trust、高风险情境与停工矩阵，折叠为 **tooling／gate／governance owner** 可机读消费的字段集。

| 维度 | **ART-ENG-WR** | **ART-GOV-RISK**（本档） |
|------|----------------|--------------------------|
| **目的** | 单票人读交付（合約附录 A 七节） | 风险态 **sign-off** 与 gate 输入 |
| **载体** | Markdown 表或 JSON 块 | **JSON 推荐**；Markdown 表须与 §4 字段 1:1 |
| **证据** | §4 命令／runner 叙述；§7 override 叙事 | **指针** `evidence_refs[]`；**不**重复粘贴命令全文 |
| **NBT 对照** | 可含自然语言说明 | **必填** `nbt_validation`（§4.6）对齐 G10-2 §6.3 |
| **消费方** | checker 对照七节 | **governance** owner；**IMP-RISK-VALIDATION** exit；文档层 gate |

**原则**：WR 可携带 evidences／narratives；**不得**用 WR §4／§7 **单独** 代替本 artifact 作为 `IMP-RISK-VALIDATION` exit 的**唯一**机读依据（G10-2 §6.3；存在本 artifact 时 **优先** 读本档）。

---

## 2. G7 挂钩

| IMP-* | 本档用法 |
|-------|----------|
| **`IMP-RISK-VALIDATION` entry** | 可读 **草案**（`status: draft`）；blocker 见 §5 |
| **`IMP-RISK-VALIDATION` exit** | 须 `status: signed` + §4 必填齐全 + `nbt_validation.all_required: true` |
| **`IMP-QA-READY` entry** | 建议已 `signed`；若仅 WR fallback，须 `fallback_used: true` 且票面授权 |
| **`IMP-RELEASE-DECISION` entry** | gate **可选** 再验本 artifact 未回退为 `draft`／`stale` |

**与 G10-2**：§2.5 汇总、§3 **NBT-H-***、§4 停工矩阵 → 映射见 §4.3–§4.5、§6。

---

## 3. 核心 Artifact

| ID | 名称 | 载体 |
|----|------|------|
| **ART-GOV-RISK** | Governance Risk Summary（治理风险摘要） | JSON（推荐）或 Markdown 表 |

本轨 v0.1 **仅** 定义上述单一 artifact；不拆分多文件 ID。

---

## 4. ART-GOV-RISK — 字段契约

### 4.1 元数据（必填）

| 字段 | 必填 | 类型 | 说明 |
|------|:----:|------|------|
| `artifact_id` | ✓ | string | 固定 **`ART-GOV-RISK`** |
| `schema_version` | ✓ | string | 本档版本，v0.1 填 **`0.1`** |
| `ticket_id` | ✓ | string | 关联 queue／案卷票号 |
| `artifact_instance_id` | ✓ | string | 本票内稳定实例 ID（如 `W2-1-RISK-001`） |
| `imp_state_at_signoff` | ✓ | string | sign-off 时 **IMP-***（G7-1 名）；须为 `IMP-RISK-VALIDATION` 或 exit 前一刻 |
| `status` | ✓ | enum | `draft` \| `signed` \| `stale` |
| `signed_at` | 条件 | ISO-8601 | `status: signed` 时必填 |
| `signed_by_role` | 条件 | string | `governance` \| `engineering`（票面授权 governance 优先） |
| `message` | ✓ | string | 一句治理结论（供 gate 日志） |

### 4.2 风险类型与触发情境

| 字段 | 必填 | 类型 | 说明 |
|------|:----:|------|------|
| `primary_change_class` | ✓ | string | G6-1 **CHG-***（与 **ART-ENG-CTX** 一致） |
| `secondary_change_classes` | ✓ | array | 无则 `[]`；含 **CHG-HIGH-RISK** 时 gate 从严 |
| `risk_types` | ✓ | array | §4.2.1 枚举子集，至少 1 项 |
| `trigger_context` | ✓ | object | §4.3；映射 CHG／NBT／IMP |

#### 4.2.1 `risk_types` 枚举（v0.1）

| 值 | 含义 | 典型 G10-2 来源 |
|----|------|-----------------|
| `blind_trust_evidence` | 盲信区证据被当作关票依据 | §2.1–§2.4；§2.5 |
| `unconfirmed_nbt_h` | **NBT-H-*** 未确认 | §3 |
| `active_denial` | guard／checker／design／release 裁決未关闭 | §4.1 |
| `forbidden_zone_touch` | 憲法 §7 类型触达 | §3 **NBT-H-01**；CHG-HIGH-RISK |
| `scope_expansion` | scope 外施工意图 | **NBT-H-05** |
| `observability_misread` | 侧车／L0 观测被误作业务依据 | §2.3 |
| `release_exit_blocked` | §2.5 单列证据试图支撑发布 | §2.5 |

### 4.3 `trigger_context` 对象

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `imp_state` | ✓ | 触发对照时的 IMP（通常 `IMP-RISK-VALIDATION`） |
| `chg_refs` | ✓ | `{ "primary": "CHG-*", "secondary": [] }` |
| `nbt_rule_refs` | ✓ | 本票触发的 **G10-2§NBT-*** 或 **NBT-H-*** ID 列表 |
| `g10_sections` | ✓ | 如 `["§2.5", "§3", "§4.1", "§6.3"]` |
| `guard_verdict_ref` | 条件 | 指向 guard JSON：`verdict` + `verdict_id`（**不**贴全文） |
| `imp_transition_target` | — | 拟 exit 目标态（如 `IMP-QA-READY`） |

### 4.4 风险项清单 `risk_items[]`

每项为 object，**至少 0 项**；非零时每项必填：

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `risk_id` | ✓ | 稳定 ID（票内唯一） |
| `risk_type` | ✓ | §4.2.1 枚举之一 |
| `severity` | ✓ | `low` \| `medium` \| `high` \| `critical` |
| `summary` | ✓ | 一句结构化描述（**非**长叙事） |
| `nbt_refs` | ✓ | 关联 NBT-ID 数组 |
| `disposition` | ✓ | `closed` \| `accepted` \| `open` \| `not_applicable` |
| `owner` | ✓ | `governance` \| `pm` \| `engineering` \| `qa` \| `release` \| `shangshu` |
| `evidence_ref` | 条件 | 指向 **ART-ENG-EVD**／guard／**ART-QA-REV** 的指针（路径或 `artifact_instance_id`） |

**blocker**：`disposition: open` 且 `severity` ∈ {`high`, `critical`} → **不得** `status: signed`。

### 4.5 升级、停工与 override

| 字段 | 必填 | 类型 | 说明 |
|------|:----:|------|------|
| `must_stop_work` | ✓ | boolean | **true** = 命中 §4 停工矩阵或 `critical` 未关闭项；**禁止** IMP 前进（除非 override 生效） |
| `escalation_path` | ✓ | array | 有序步骤，如 `["governance_owner", "shangshu"]` |
| `override_allowed` | ✓ | boolean | 是否允许 Rule 12 书面 override |
| `override_ref` | 条件 | object | `override_allowed: true` 且已 override 时：`{ "rule": "Rule-12", "trace_ref": "<Progress|notes 末尾锚点>" }` |
| `override_effective` | ✓ | boolean | 当前 override 是否已生效且留痕 |

| 组合 | 规则 |
|------|------|
| `must_stop_work: true` + `override_effective: false` | gate **`deny`**（见 W2-3 gate 设计） |
| `must_stop_work: true` + `override_effective: true` | gate **`require-human-override`** 或票面 **`allow`**（尚書省已批） |
| `CHG-HIGH-RISK` ∈ secondary | `override_allowed` 默认 **false**，除非 `override_effective: true` |

### 4.6 `nbt_validation` — G10-2 §6.3 机读对照

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `checklist_id` | ✓ | 固定 **`G10-2-§6.3-v0.1`** |
| `items` | ✓ | 数组；每项 `{ "item_key", "passed", "nbt_ref", "notes" }` |
| `all_required` | ✓ | boolean；**全部** `passed: true` 方可 signed |
| `fallback_used` | ✓ | boolean；**true** = 未产出本 artifact 完整字段、改由 WR 对照（仅过渡） |

**§6.3 最小项 `item_key`（v0.1）**：

| item_key | 对应 G10-2 §6.3 勾选项 |
|----------|-------------------------|
| `no_blind_trust_release_basis` | 无 §2.5 单列证据作为唯一 release／QA 依据 |
| `nbt_h_confirmed_or_na` | §3 情境均已 NBT-H 留痕或 N/A |
| `no_active_denial` | 无未关闭 §4.1 deny／stop_work／rejected／blocked |
| `g6_guard_checker_met` | G6-2 必 guard／checker 已满足 |
| `context_deny_handled` | Context deny 已按 NBT-H-14 处理 |

### 4.7 证据指针（不重复 WR 正文）

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `evidence_refs` | ✓ | 数组；元素 `{ "artifact_id", "section_or_field", "instance_ref" }` |
| `wr_fallback` | 条件 | `fallback_used: true` 时：`{ "wr_section_4": true, "wr_section_7": true, "reason": "<string>" }` |

**示例指针**（非规范正文）：

```json
"evidence_refs": [
  { "artifact_id": "ART-ENG-EVD", "section_or_field": "commands", "instance_ref": "W2-1-EVD-001" },
  { "artifact_id": "ART-ENG-WR", "section_or_field": "§7", "instance_ref": "W2-1-WR-001" }
]
```

---

## 5. Blocker 与 IMP 门槛

| 类别 | 规则 |
|------|------|
| **blocker** | `status: signed` 但 `nbt_validation.all_required: false`；`must_stop_work: true` 且 `override_effective: false`；`risk_items` 含 `open`+`high`/`critical`；缺 `trigger_context`／`risk_types` |
| **IMP exit** | **`IMP-RISK-VALIDATION` → `IMP-QA-READY`** 前须 `status: signed` **或** 明示 `fallback_used: true`（W2-3 pilot 过渡窗 **须** 票面 Notes 授权） |
| **确认方** | **governance** owner（主）；**checker** 只读核对与 **ART-QA-REV** 不矛盾 |

---

## 6. 与 G10-2 字段折叠索引

| G10-2 节 | 折叠至 ART-GOV-RISK |
|----------|---------------------|
| §2.5 汇总 | `risk_types` 含 `release_exit_blocked`；`nbt_validation.no_blind_trust_release_basis` |
| §3 NBT-H-* | `trigger_context.nbt_rule_refs`；`risk_items[].nbt_refs`；`nbt_validation.nbt_h_confirmed_or_na` |
| §4.1 矩阵 | `must_stop_work`；`risk_types: active_denial`；`nbt_validation.no_active_denial` |
| §6.3 清单 | `nbt_validation.items[]`（§4.6） |
| §6.1 override | `override_*` 字段；指针 **ART-ENG-WR** §7 |

---

## 7. 最小 JSON 形状示例（节选）

```json
{
  "artifact_id": "ART-GOV-RISK",
  "schema_version": "0.1",
  "ticket_id": "W2-3-GOV-RISK-PILOT",
  "artifact_instance_id": "W2-3-RISK-001",
  "imp_state_at_signoff": "IMP-RISK-VALIDATION",
  "status": "signed",
  "signed_at": "2026-05-27T12:00:00+08:00",
  "signed_by_role": "governance",
  "message": "NBT §6.3 satisfied; no stop-work blockers",
  "primary_change_class": "CHG-GOV-DOC",
  "secondary_change_classes": [],
  "risk_types": ["blind_trust_evidence"],
  "trigger_context": {
    "imp_state": "IMP-RISK-VALIDATION",
    "chg_refs": { "primary": "CHG-GOV-DOC", "secondary": [] },
    "nbt_rule_refs": ["NBT-AI-06"],
    "g10_sections": ["§2.5", "§3", "§6.3"],
    "imp_transition_target": "IMP-QA-READY"
  },
  "risk_items": [],
  "must_stop_work": false,
  "escalation_path": ["governance_owner"],
  "override_allowed": true,
  "override_effective": false,
  "nbt_validation": {
    "checklist_id": "G10-2-§6.3-v0.1",
    "all_required": true,
    "fallback_used": false,
    "items": [
      { "item_key": "no_blind_trust_release_basis", "passed": true, "nbt_ref": "§2.5", "notes": "" }
    ]
  },
  "evidence_refs": [
    { "artifact_id": "ART-ENG-WR", "section_or_field": "§7", "instance_ref": "pilot-wr-001" }
  ]
}
```

---

## 8. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G8-6 v0.1：GOV 轨 **ART-GOV-RISK** 契约；对齐 G10-2 §6.3；WR 区隔与 fallback 规则 |

---

## 9. 引用

| 主题 | 路径 |
|------|------|
| G10-2 NBT | `G10_governance_rulebook/20_no_blind_trust.md` |
| G7 RISK exit | `G7_state_machine/30_exit_and_transitions.md` §3 |
| 最小 gate 设计 | `workflow_v2/20_pilot/W2-3_minimal_gate_design.md` |
| 队列 | `workflow_v2/90_run_queue.md`（W2-3-*） |
