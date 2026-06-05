# <CASE> — 工单与 IMP 状态

> **artifact_id**：`<ARTIFACT-ID>`  
> **试点／变更标题**：`<简短标题>`  
> **primary_change_class**：`CHG-GOV-DOC` / `CHG-…`  
> **IMP 流索引**：（可选）`../<CASE>_imp_flow_and_artifacts.md`  
> **imp_state_schema_version**：`0.1`  
> **模板**：`20_pilot/_TEMPLATE_case/`（复制后删除本行说明）

---

## 1. 任务描述

（本 artifact 范围、交付物摘要、硬边界。）

---

## 2. 当前 IMP 状态（`imp_state_current`）

| 项 | 值 |
|----|-----|
| **`imp_state`（本记录）** | `IMP-SCOPE-DRAFT` |
| **entry_owner_role（本态）** | `pm` |
| **entry_evidence_refs（本态）** | （指向本态 ART，如 `01_art_pm_scope.md`） |
| **rework_target** | （仅 `IMP-REWORK` 时填写目标态） |
| **imp_state_updated_at** | `YYYY-MM-DD` |
| **imp_state_updated_by_ticket** | `<CASE>-ORCH` |

---

## 3. IMP 迁移日志（`imp_state_transitions`）

> 每次合法迁移 **追加** 一行；禁止删除或改写历史行。禁止跳关（见 G7-3 §2.1）。

| at | from | to | by | reason / artifact_refs |
|----|------|-----|-----|------------------------|
| YYYY-MM-DD | — | `IMP-SCOPE-DRAFT` | `<CASE>-ORCH` / `pm` | 建案卷；总控索引就绪 |

---

## 4. 已完成的 ART-*

（按施工票分表登记 ART ID、路径、摘要。）

---

## 5. 案卷文件索引

| # | 文件 | ART | 负责票 |
|---|------|-----|--------|
| 01 | `01_…` | ART-… | … |

---

## 6. 施工票状态

| 票 ID | Status | IMP exit（Notes 索引，非 imp_state 字段） |
|-------|--------|------------------------------------------|
| `<CASE>-ORCH` | TODO | （索引） |

---

## 7. 修订记录

| 日期 | 变更 |
|------|------|
| YYYY-MM-DD | 建案：自 `_TEMPLATE_case` 复制 |
