# ART-ENG-WR — W2-1 试点 Work Report

> **artifact_id**：`W2-1-G8-RECON-PILOT`  
> **ticket_id**：`W2-1-ENG`  
> **G8 契约**：`30_engineering.md` §4.2–§4.5（含 **ART-ENG-FIVE**、**ART-ENG-EVD**、**ART-ENG-DOD**）

---

## Work Report

**任务**：W2-1 G8-RECON-IMP — G7↔G8 交叉引用 cleanup（Eng 实质 diff）  
**角色**：W2-1-ENG / engineering worker  
**日期**：2026-05-27（本地）

### 1. 变更档案

**新建**

- `workflow_v2/20_pilot/W2-1_case/04_art_eng_ctx.md`（**ART-ENG-CTX**）
- `workflow_v2/20_pilot/W2-1_case/05_art_eng_wr.md`（本文件）

**修改**

- `workflow_v2/10_governance/G7_state_machine/20_entry_conditions.md` — G8-1/2/5、G10-2 §5.3 引用；`ART-REL-RECORD`→**ART-REL-EXEC**
- `workflow_v2/10_governance/G7_state_machine/30_exit_and_transitions.md` — stale「待 G8-*／待 G10-2」替换；§6 ART 索引更新
- `workflow_v2/10_governance/G8_artifact_contract/30_engineering.md` §2 — G7-1 已冻结；`10_workflow_states.md` 对账
- `workflow_v2/10_governance/G8_artifact_contract/README.md` — IMP 对账状态（D-3）
- `workflow_v2/20_pilot/W2-1_case/W2-1_case.md` — IMP 状态 + ART-ENG-* 登记

### 2. 可执行 skeleton

无

### 3. placeholder（未完成）

| 项 | 说明 | owner |
|----|------|-------|
| **ART-GOV-RISK** | G7-2 §4 `IMP-RISK-VALIDATION` entry 仍保留占位（defer W2-3）；本票用 WR §4+§7 + G10-2 §5.3 临时对照 | W2-3 |
| **imp_state 机读 enforcement** | 不在 W2-1 范围 | W2-2 |

### 4. 验证证据（ART-ENG-EVD）

**commands**

```powershell
# AC-1: 无 ART-REL-RECORD 残留（G7-2）
rg "ART-REL-RECORD" workflow_v2/10_governance/G7_state_machine/20_entry_conditions.md

# AC-2: 无 stale「待 G8-1/2/5」（G7 目录）
rg "待 G8-[125]" workflow_v2/10_governance/G7_state_machine/

# AC-3: IMP-RISK-VALIDATION 引用 G10-2 §5.3（非裸「待 G10-2」）
rg "待 G10-2" workflow_v2/10_governance/G7_state_machine/30_exit_and_transitions.md

# AC-4: 无错误路径 10_states.md（G8-3）
rg "10_states" workflow_v2/10_governance/G8_artifact_contract/30_engineering.md

# AC-4b: 正式路径存在
rg "10_workflow_states" workflow_v2/10_governance/G8_artifact_contract/30_engineering.md
```

**key_results**

| 命令 | 期望 | 结果 |
|------|------|------|
| AC-1 rg | 0 命中 | `ok: true` — 0 命中 |
| AC-2 rg | 0 命中 | `ok: true` — 0 命中 |
| AC-3 rg | 0 命中（§7 TODO 已标记已解） | `ok: true` — 0 命中 |
| AC-4 rg | 0 命中 | `ok: true` — 0 命中 |
| AC-4b rg | ≥1 命中 | `ok: true` — §2 含 `10_workflow_states.md` |

**blocked**：`false`

### 5. 阻塞

无（本票 Eng 轨范围内）

### 6. 下一步建议

1. **W2-1-QA-REL**：checker 只读 diff + 重跑 §4 命令 → **ART-QA-REV**。
2. Release 轨：内部 doc-authority → **ART-REL-EXEC**（受众 `workflow_v2/10_governance/`）。
3. W2-3：**ART-GOV-RISK** 定稿后更新 G7-2 §4 `IMP-RISK-VALIDATION` entry。

### 7. 宪法／合约

- **override**：无
- **留痕位置**：无

---

## ART-ENG-FIVE（C11 五要素 · 可 grep）

| 要素 | 摘要 |
|------|------|
| **变更清单** | G7-2、G7-3、G8-3 §2、G8 README、W2-1 case 04–05 + case 状态 |
| **skeleton** | 无 |
| **placeholder** | ART-GOV-RISK（W2-3）；imp_state enforcement（W2-2） |
| **阻塞** | 无 |
| **下一步** | W2-1-QA-REL checker；Release doc-authority |

---

## ART-ENG-DOD（FLOW-6.5 自检）

| 自检项 | 是／否 | 证据 |
|--------|:------:|------|
| Context + Source 已读可追溯 | **是** | 04_art_eng_ctx.md；已读 PM scope／DES spec／G6/G7/G8 |
| 核心路径结构化 `dict`（若适用） | **N/A** | 纯 CHG-GOV-DOC 文档票 |
| Work Report 已填 | **是** | 本文件 §1–§7 |
| skeleton／placeholder 已分栏 | **是** | §2「无」；§3 表 |
| 已验证或已标阻塞 | **是** | §4 EVD 全绿 |
| 无未留痕违宪／违合约 | **是** | §7 override 无 |
| 四流派最低覆盖 | **是** | CD（CTX）+ SD（列档已读）+ IN（diff）+ DB（§4 grep） |

**Eng DoD 结论**：`ok: true` — 可进入 **IMP-QA-READY** entry（待 checker 复验）。
