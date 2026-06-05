# W2-2 — `imp_state` 字段约定 v0.1

> **角色**：Wave 2 总控规格（**不**实现 CI／机读 enforcement）。  
> **权威**：IMP-* 状态名与迁移语义 → `10_governance/G7_state_machine/`（G7-1／G7-3）；命名空间边界 → G7-1 §1–§1.2。  
> **试点实例**：`20_pilot/W2-1_case/W2-1_case.md` §2（`IMP-OBSERVING`）。  
> **下游施工票**：`90_run_queue.md` → W2-2-IMP-FIELD／W2-2-HELPER-SCRIPTS／W2-2-QA-CHECKLIST。

---

## 1. 字段定义

| 属性 | 约定 |
|------|------|
| **字段名** | `imp_state`（小写 snake_case；**禁止**别名 `IMP_state`、`lifecycle_status` 覆盖本字段） |
| **类型** | 字符串；取值 **必须** 为 G7-1 §2 正式 **IMP-*** 名之一，或过渡登记时的上一态 + 迁移注记（见 §4） |
| **语义** | 「本 **AI 导入 artifact** 当前处于导入主线哪一步」— **不是** queue `Status`、不是 `battle_report.status`、不是 `assignable` |
| **版本** | `imp_state_schema_version: "0.1"`（可选写在案卷 front matter；v0.1 未强制 JSON 外壳） |

---

## 2. 字段位置（写入优先级）

| 优先级 | 载体 | 路径模式 | 必填时机 | 说明 |
|:------:|------|----------|----------|------|
| **P0** | **案卷工单** | `20_pilot/<CASE>_case/<CASE>_case.md` §「当前 IMP 状态」表 | 建案即写；每态迁移 **同日** 更新 | **人类可读权威**；W2-1 模板 |
| **P1** | **IMP 迁移日志** | 同上案卷 §「IMP 迁移日志」表 | 每次 **合法** 前进／进入 REWORK 追加一行 | 含 `from`→`to`、票号、证据指针 |
| **P2** | **结构化 QA／Release** | `*_art_qa_rev.json`、`*_art_rel_*.json` 可选键 `imp_state_at_review` | QA／Release 票收口时 | **快照**；不替代 P0 当前态 |
| **P3** | **run queue Notes** | `90_run_queue.md` 施工票 Notes | 票 **DONE** 时写一句「IMP exit → …」 | **索引 only**；禁止把 `DONE` 写入 `imp_state` |
| **P4** | **总控快照** | `99_latest_status.md` | 波次／模块级摘要 | 不得作为单案 lifecycle 机读源 |

**禁止**：在 `90_run_queue.md` **Status** 栏或 IMP 字段写入 `TODO`／`DOING`／`DONE`／`BLOCKED`（G7-1 §1.2）。

---

## 3. 合法取值（引用 G7-1）

取值列表 **唯一权威**：`10_governance/G7_state_machine/10_workflow_states.md` §2。

| 类别 | 允许值 |
|------|--------|
| **主线（顺序态）** | `IMP-SCOPE-DRAFT` … `IMP-OBSERVING`（见 G7-1 状态总览） |
| **返工** | `IMP-REWORK`（须配合 `rework_target`／`rework_from` 见 §5） |
| **禁止** | queue 四态、`done`／`draft`、`assignable:*`、`IMP-OPEN`／`IMP-ACTIVE` 等 G7-1 §1.1 非主线字汇 **作为 `imp_state` 值** |

---

## 4. 更新原则

### 4.1 谁可以写

| 动作 | 写入角色 | 留痕 |
|------|----------|------|
| 前进至下一 **IMP-*** | 该态 **entry owner**（G7-2／G7-3 角色表）或指派施工 worker **在 artifact owner 监督下** | P0 表 + P1 日志行；Eng／QA artifact 内 `ticket_id` |
| 进入 **IMP-REWORK** | 失败关口 owner + 记录 | `rework_from`、`rework_target`、`rework_reason`（案卷 §2 或 JSON） |
| 自 REWORK 回退 | 失败关口 owner；自 QA 失败须 **checker** 确认 plan | P1 日志；不得无 `rework_target` 离开 REWORK（G7-3） |
| **guard** `stop_work`／`deny` | **不** 写 `imp_state`；可 **block** 迁移 | guard JSON；Progress 阻塞（G7-3 §2） |

### 4.2 何时写

1. **建案**：`imp_state = IMP-SCOPE-DRAFT`（或接战时已明确的更高态须注明依据）。  
2. **每个关口 exit 满足后**：**先** 落盘本态 **ART-***／EVD，**再** 更新 `imp_state` 至 G7-3 **合法下一态**（单步前进，除 REWORK）。  
3. **施工票 DONE**：queue Notes 仅写「本票 IMP exit → `IMP-…`」；**不** 用 queue DONE 代替 P0 更新。  
4. **观测期**：`IMP-OBSERVING` 期间 **不** 因新 scope 前进；新需求 → 新 artifact／新案卷。

### 4.3 禁止直接跳状态

与 G7-3 §2.1 禁止跳转表一致；v0.1 **不新增** 状态名，仅要求案卷记录与 G7-3 对齐。典型禁止（节选）：

| 禁止跳转 | 须经由 |
|----------|--------|
| `IMP-SCOPE-DRAFT` → `IMP-AI-READY` 及之后 | `IMP-SPEC-CLARIFY` |
| `IMP-AI-READY` → `IMP-QA-READY`／`IMP-RELEASE-*` | `IMP-REVIEW-READY` → `IMP-RISK-VALIDATION` |
| `IMP-QA-READY` → `IMP-RELEASED` | `IMP-RELEASE-DECISION` |
| `IMP-RELEASED` → 终局冻结 | `IMP-OBSERVING`（或 REWORK） |
| `IMP-OBSERVING` → 任意前进态（除 REWORK） | 新案卷 |

**违规处理**：checker 标 `rejected` 或 `blocked`；`imp_state` 回滚至最后合法 P1 记录态，并追加纠正行（不删历史行）。

---

## 5. 推荐案卷 §2 表头（模板）

复制自 W2-1；新案卷 **应** 包含：

```markdown
## 2. 当前 IMP 状态

| 项 | 值 |
|----|-----|
| **`imp_state`（本记录）** | `IMP-…` |
| **entry_owner_role（本态）** | `pm` / `engineering` / `qa` / `release` / … |
| **entry_evidence_refs（本态）** | 指向本态 ART 路径 |
| **rework_target** | （仅 `IMP-REWORK` 时必填） |
| **imp_state_updated_at** | ISO 日期 |
| **imp_state_updated_by_ticket** | 如 `W2-x-ENG` |
```

---

## 6. 与 tooling 的关系（v0.1）

| 能力 | v0.1 | 施工票 |
|------|------|--------|
| 人工／半自动更新 P0+P1 | **是**（制度 + 模板） | W2-2-IMP-FIELD |
| AC grep helper | **是**（脚本 + runbook） | W2-2-HELPER-SCRIPTS |
| QA no-blind-trust 清单 | **是**（文档） | W2-2-QA-CHECKLIST |
| CI 校验 `imp_state` 合法性 | **否** | W2-3+ |
| intake→IMP 机读边 | **否**（仅索引） | 未来票 |

---

## 7. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | v0.1 初稿（W2-2 总控）；对齐 W2-1 试点与 G7-1／G7-3 |
