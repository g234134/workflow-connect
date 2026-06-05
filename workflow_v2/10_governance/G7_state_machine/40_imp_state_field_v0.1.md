# G7 附录 — `imp_state` 机读字段约定 v0.1

> **性质**：**附录**；**不**修改 G7-1／G7-2／G7-3 主体语义、不新增 IMP-* 状态名。  
> **完整规格**：`workflow_v2/20_pilot/W2-2_imp_state_schema.md`  
> **状态名权威**：本目录 `10_workflow_states.md`  
> **迁移权威**：本目录 `30_exit_and_transitions.md`

---

## 1. 为何单独成附录

G7-1 §1.2 已规定「不得在 artifact 元数据用异域字汇覆盖 `imp_state`」，但 **字段载体与更新节奏** 在 Wave 1 未展开。W2-2 v0.1 将试点案卷（W2-1）经验固化为可复用约定，供后续每条导入任务引用。

---

## 2. 摘要（指向 W2-2 schema）

| 项 | 约定 |
|----|------|
| **字段名** | `imp_state` |
| **取值** | 仅 G7-1 正式 **IMP-***（含 `IMP-REWORK`） |
| **主写入** | `20_pilot/<case>/<case>_case.md` §2 + 迁移日志 |
| **禁止** | queue `TODO`/`DONE`、Eng `ok:true`、route `assignable` 写入本字段 |
| **更新** | 单步合法迁移；禁止 G7-3 §2.1 跳关 |
| **tooling** | `workflow_v2/tools/wf_check_cross_ref.ps1`（交叉引用 AC，**非** imp_state 校验器） |

---

## 3. 与 G7 正文的关系

- **G7-1**：命名空间与 IMP 列表 — **不变**  
- **G7-2／G7-3**：entry／exit／禁止跳转 — **不变**；本附录要求案卷 `imp_state` **对齐** 这些规则  
- **enforcement**：v0.1 **无** CI；非法值由 checker 人工拒收（G8-4 **ART-QA-REV**）

---

## 4. 案卷与 queue 中的实际用法（W2-2-IMP-FIELD）

### 4.1 写在哪里

| 优先级 | 位置 | 逻辑块 | 说明 |
|:------:|------|--------|------|
| **P0** | `20_pilot/<CASE>_case/<CASE>_case.md` **§2** | `imp_state_current` | 字段名 **`imp_state`**；人类可读当前态权威 |
| **P1** | 同上 **§3** | `imp_state_transitions` | 迁移日志表：`at`／`from`／`to`／`by`／`reason / artifact_refs` |
| **P3** | `90_run_queue.md` 施工票 **Notes** | — | 仅写「IMP exit → `IMP-…`」索引；**禁止**把 `TODO`／`DONE` 写入 `imp_state` |

标准骨架：`20_pilot/_TEMPLATE_case/`（`README.md` + `_TEMPLATE_case.md`）。完整表头与更新节奏 → `20_pilot/W2-2_imp_state_schema.md` §2／§4／§5。

### 4.2 示例（W2-1 试点 · 文本引用）

- **§2 当前态**：`20_pilot/W2-1_case/W2-1_case.md` → `imp_state` = **`IMP-OBSERVING`**；`entry_evidence_refs` 指向 `09_art_pm_obs_plan.md`、`08_art_rel_exec.json`。  
- **§3 迁移**：同文件 11 行自 `IMP-SCOPE-DRAFT` 至 `IMP-OBSERVING`（含 `IMP-SPEC-CLARIFY` 内 **exit** 留痕行）；每步 `by` 对应 `W2-1-PM-DES`／`W2-1-ENG`／`W2-1-QA-REL`。  
- **queue Notes**（P3）：例如 `W2-1-QA-REL` Notes「IMP → **IMP-OBSERVING**」— 须与案卷 §2 一致，不可替代 §2 更新。

新案：**复制** `_TEMPLATE_case/` → `20_pilot/<CASE>_case/`，建案日写 §2=`IMP-SCOPE-DRAFT` 与 §3 首行；每关口 **先** ART 落盘 **再** 更新 §2 并 **追加** §3。

---

## 5. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | v0.1 附录新增（W2-2 总控） |
| 2026-05-27 | §4 案卷／queue 用法 + W2-1 引用（W2-2-IMP-FIELD） |
