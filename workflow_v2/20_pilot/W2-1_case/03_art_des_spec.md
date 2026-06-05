# ART-DES-SPEC — W2-1 试点 Design Spec

> **artifact_id**：`W2-1-G8-RECON-PILOT`  
> **ticket_id**：`W2-1-PM-DES`  
> **G8 契约**：`10_governance/G8_artifact_contract/20_design.md` §4.1  
> **sync_ref**：`02_art_pm_clarify.md` → `open_questions`

---

## 字段

| 字段 | 值 |
|------|-----|
| `artifact_id` | `W2-1-G8-RECON-PILOT` |
| `ticket_id` | `W2-1-PM-DES` |

---

## spec_summary

1. **目标**：在 `10_governance/` 三处目标文件内完成 G7↔G8 交叉引用对账，使读者可沿 G7-1 正式 IMP 名与 G8 五轨 ART ID 跳转，不再依赖已交付轨的「待 G8-x」占位句。
2. **G7-2 §4 IMP-RELEASED**：`ART-REL-RECORD` 占位 → **ART-REL-EXEC**（引用 G8-5 §命名对账）。
3. **G7-3 §1.2／§2.3／§3 分状态表**：已交付 G8 轨（PM G8-1、Design G8-2、Release G8-5）的「待 G8-*」→ 指向对应 `10_pm.md`／`20_design.md`／`50_release_owner.md` 节号；G10-2 风险对照 → `G10_governance_rulebook/20_no_blind_trust.md` §5.3。
4. **G8-3 `30_engineering.md` §2**：表头说明改为「G7-1 已冻结；占位别名仅作并行索引」；`对账参考` 列改链 `G7_state_machine/10_workflow_states.md` §2；删除 `10_states.md` 错误路径。
5. **不变更**：各文件 §4 契约字段定义、G6 change class 表、G10 NBT 规则正文、IMP exit 条件逻辑。
6. **Design review**：本票 trivial → **ART-DES-REVIEW-PKG**／**ART-DES-REV** = N/A（见 **ART-PM-GAPS**）。

---

## open_questions

与 **ART-PM-CLARIFY** 同步；`sync_ref: 02_art_pm_clarify.md#open_questions` — 全部 **closed**。

---

## dependencies

| ref | status | note |
|-----|--------|------|
| `01_art_pm_scope.md` | **ok** | scope 边界 |
| `02_art_pm_clarify.md` | **ok** | 澄清闭环 |
| `G8_artifact_contract/50_release_owner.md` | **ok** | ART-REL-EXEC 命名 |
| `G7_state_machine/10_workflow_states.md` | **ok** | IMP 正式名 |
| `G10_governance_rulebook/20_no_blind_trust.md` | **ok** | §5.3 风险对照锚点 |
| `W2-1-ENG` | **TBD** | 实质 diff 施工 |

---

## acceptance_criteria_draft

| # | 准则 | 验证方式 |
|---|------|----------|
| AC-1 | G7-2 §4 `IMP-RELEASED` entry 引用 **ART-REL-EXEC**，无 `ART-REL-RECORD` 残留 | `rg ART-REL-RECORD workflow_v2/10_governance/G7_state_machine/20_entry_conditions.md` → 0 命中 |
| AC-2 | G7-2／G7-3 中已交付轨无 stale「待 G8-1／2／5」无替换句 | 人工 spot-check + `rg "待 G8-[125]"` 限定 G7 目录 |
| AC-3 | G7-3 `IMP-RISK-VALIDATION` 引用 G10-2 §5.3（非「待 G10-2」裸占位） | 读 §3 IMP-RISK-VALIDATION exit 行 |
| AC-4 | `30_engineering.md` §2 引用 `10_workflow_states.md`；无 `10_states.md` | `rg 10_states workflow_v2/10_governance/G8_artifact_contract/30_engineering.md` → 0 命中 |
| AC-5 | 治理语义未变：G7-3 §2.1 跳关表、G6 CHG 定义无 diff | checker diff 范围审查 |
| AC-6 | 案卷 `20_pilot/W2-1_case/` 01–10 文件可被索引 | README 链接检查 |

---

## interface_sketch

（本票无 API／`dict` 产出；N/A）

---

## navigation_refs

（不涉及 context-entry 派工；N/A）

---

## out_of_design

- G8 `10_pm.md`／`20_design.md` §1–§7 契约定义改写（附录实例除外）。
- 新增 IMP 状态或 CHG 类别。
- production／暗部代码路径修改。
- **ART-GOV-RISK** 正式 artifact 结构（W2-3）。

---

## 确认

| 项 | 值 |
|----|-----|
| design owner | `design` |
| PM 会签 | scope 边界一致 ✓（2026-05-27） |
