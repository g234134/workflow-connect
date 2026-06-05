# ART-PM-SCOPE — W2-1 试点 Scope Brief

> **artifact_id**：`W2-1-G8-RECON-PILOT`  
> **ticket_id**：`W2-1-PM-DES`（关联：`W2-1-ENG`、`W2-1-QA-REL`）  
> **G8 契约**：`10_governance/G8_artifact_contract/10_pm.md` §4.1  
> **imp_state 登记时态**：`IMP-SCOPE-DRAFT` → 本 artifact 就绪后进入 `IMP-SPEC-CLARIFY`

---

## 字段

| 字段 | 值 |
|------|-----|
| `artifact_id` | `W2-1-G8-RECON-PILOT` |
| `ticket_id` | `W2-1-PM-DES` |
| `import_intent` | 以一条极小治理文档票走通 Wave 2 导入全链，并完成 G8-RECON-IMP 实质：G7↔G8 交叉引用对账与 stale 占位清理。 |
| `target_artifact_kind` | governance doc delta（`10_governance/` 既有路径内的 Markdown 引用修正） |
| `primary_change_class` | **CHG-GOV-DOC** |
| `secondary_change_classes` | （无） |
| `intake_ref` | `00_master_plan.md` §9；`90_run_queue.md` Wave 2；前置票 `W2-1-ORCH`（DONE） |

---

## in_scope

1. **G7-2** `G7_state_machine/20_entry_conditions.md`：占位 `ART-REL-RECORD` → 正式 **ART-REL-EXEC**；去除或替换 stale「待 G8-x／待 G10-2」类占位句（**不改** entry 规则语义）。
2. **G7-3** `G7_state_machine/30_exit_and_transitions.md`：同上原则的对账与 stale 引用清理（**不改** exit／迁移规则语义）。
3. **G8-3** `G8_artifact_contract/30_engineering.md` §2：占位 IMP 表改引 **G7-1** `10_workflow_states.md`，并标注「G7-1 已冻结」；修正错误路径 `10_states.md` → `10_workflow_states.md`。
4. **试点案卷** `20_pilot/W2-1_case/`：按 G8 契约写入本链 **ART-*** 实例（PM／Design／Eng／QA／Release 各轨）。
5. **内部 doc-authority 发布**：Release 轨以 repo 内 `workflow_v2/10_governance/` 为受众；无 production／无 CI gate。

---

## out_scope

1. 修改 G6／G7／G8／G10 **治理条文正文语义**（change class 定义、IMP exit 规则、NBT 表、artifact 契约 §4 字段定义等）。
2. production code、hooks、venv、`.env`、runtime checkpoint、暗部 `core`。
3. `imp_state` 机读字段与 enforcement（→ **W2-2**）。
4. **ART-GOV-RISK** G8 轨定稿与 CI／guard gate（→ **W2-3**）。
5. 新建 CHG-*／IMP-*／ART-* ID（仅使用总控已指定 ID）。
6. G8 `10_pm.md`／`20_design.md` **契约 §1–§7 定义**变更（本票仅可在附录追加 W2-1 实例索引）。

---

## 确认

| 项 | 值 |
|----|-----|
| 登记方 | PM 轨（`pm`） |
| 登记日期 | 2026-05-27 |
| orchestrator 抽检 | queue 票号与 `artifact_id` 对齐 ✓ |
