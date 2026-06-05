# G7 — State Machine

> **定位**：AI 导入 **artifact 生命周期** 主线状态（`IMP-*`），非施工票 queue 态、非 battle_report 态、非 route verdict。

## 产物

| 文件 | 票号 | 状态 |
|------|------|------|
| `10_workflow_states.md` | G7-1 | **DONE** — IMP-* 列表与命名空间 |
| `20_entry_conditions.md` | G7-2 | **DONE** — 10 态 entry + 全局规则 + G8 占位对账 §6 |
| `30_exit_and_transitions.md` | G7-3 | **DONE** — exit 条件、合法/禁止迁移、IMP-REWORK |
| `40_imp_state_field_v0.1.md` | （附录） | **v0.1** — `imp_state` 字段载体与更新约定（**不**改 G7-1～3 语义） |

## 阅读顺序

1. `10_workflow_states.md` — 状态名与语义（G7-1 冻结）  
2. `20_entry_conditions.md` — 每态 entry（G7-2，可与 G7-3 并行）  
3. `30_exit_and_transitions.md` — 每态 exit、迁移矩阵、REWORK（G7-3）  
4. `40_imp_state_field_v0.1.md` — 案卷 `imp_state` 写入（W2-2；完整规格见 `20_pilot/W2-2_imp_state_schema.md`）

## 权威引用

- 主线状态名：**本目录 `10_workflow_states.md`**
- entry 条件：**本目录 `20_entry_conditions.md`**
- exit／迁移：**本目录 `30_exit_and_transitions.md`**
- queue 四态 → `workflow_v2/90_run_queue.md`
- battle_report → `04_Workflows/ops_cycle_schema.json`
- route / assignable → `04_Workflows/TASK_ROUTING.md`
