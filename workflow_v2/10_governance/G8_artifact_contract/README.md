# G8 — Artifact Contract

> **状态**：v0.1 **六轨**就绪（Eng + QA + PM + Design + Release + **GOV**）；G7-1 正式 IMP 名 **已对账**（G8-RECON-IMP · W2-1-ENG）。  
> **Wave**：W1 · 模块 G8  
> **对账**：G7 entry／exit ↔ 本目录 artifact ID（G7-1 状态名已冻结）

---

## 产物索引

| 文件 | 票号 | 状态 | 轨 |
|------|------|------|-----|
| `10_pm.md` | G8-1 | **v0.1 DONE**（G8-B） | **ART-PM-*** |
| `20_design.md` | G8-2 | **v0.1 DONE**（G8-B） | **ART-DES-*** |
| `30_engineering.md` | G8-3 | **v0.1 DONE**（G8-A） | **ART-ENG-*** |
| `40_qa.md` | G8-4 | **v0.1 DONE**（G8-A） | **ART-QA-*** |
| `50_release_owner.md` | G8-5 | **v0.1 DONE**（G8-B） | **ART-REL-*** |
| `60_gov_risk.md` | G8-6 | **v0.1 DONE**（W2-3 契约） | **ART-GOV-RISK** |

---

## v0.1 已定义轨摘要

### PM（`10_pm.md`）

| ID | 一句话 |
|----|--------|
| ART-PM-SCOPE | 导入范围：intent／in-out scope／CHG 草案 |
| ART-PM-CLARIFY | 澄清记录：open questions 闭环与 defer |
| ART-PM-GAPS | 五轨必填字段缺口清单 |
| ART-PM-OBS-PLAN | 发布后观测窗口与 signals |

### Design（`20_design.md`）

| ID | 一句话 |
|----|--------|
| ART-DES-SPEC | 设计规格：依赖、验收口径草案、open questions |
| ART-DES-REVIEW-PKG | 评审包：WR／spec 齐套索引（条件触发） |
| ART-DES-REV | 设计评审结论：approved／gaps／rejected |

### Engineering（`30_engineering.md`）

| ID | 一句话 |
|----|--------|
| ART-ENG-CTX | 起手式：角色／可碰／禁区类型 |
| ART-ENG-WR | Work Report 七节（合約附录 A） |
| ART-ENG-FIVE | C11 五要素摘要 |
| ART-ENG-EVD | 验证证据包（§4 + `ok` 语义） |
| ART-ENG-DOD | 单票 DoD 自检（FLOW-6.5） |
| ART-ENG-BOARD | 暗部 C10 四栏（条件触发） |

### QA（`40_qa.md`）

| ID | 一句话 |
|----|--------|
| ART-QA-REV | checker 验收 verdict 外层 JSON |
| ART-QA-DOD | 四键 dod_checklist |
| ART-QA-EVD | 重跑命令 evidence 数组 |
| ART-QA-SMOKE | smoke runbook 判定摘要 |
| ART-QA-BR | battle report 内层扁平 JSON |

### Release（`50_release_owner.md`）

| ID | 一句话 |
|----|--------|
| ART-REL-DEC | 发布裁决：approve／deny、范围、回退草案 |
| ART-REL-EXEC | 执行记录：环境生效证据与 rollback 有效 |
| ART-REL-OBS | 观测收口：窗口、incident、follow-up |

### Governance（`60_gov_risk.md`）

| ID | 一句话 |
|----|--------|
| ART-GOV-RISK | 治理风险摘要：`IMP-RISK-VALIDATION` sign-off；NBT §6.3 机读对照；与 WR 区隔 |

---

## IMP 占位状态（六轨共用 · 并行索引）

> G7-1 正式态已冻结；下列占位 **禁止** 写入 `imp_state`。映射权威见 G7-2 §6、G7-3 §1.3；W2-1-ENG 已完成 G7↔G8 交叉引用 cleanup。

| 占位 | 含义 | 建议正式态（G7-1） |
|------|------|-------------------|
| `IMP-OPEN` | 接战 | → `IMP-SCOPE-DRAFT` |
| `IMP-ACTIVE` | 施工窗口 | `IMP-AI-READY` … `IMP-REVIEW-READY` |
| `IMP-VERIFY` | 待 checker | `IMP-QA-READY` |
| `IMP-ARCHIVE-PENDING` | QA 通过、待发布裁决 | 并行 `IMP-RELEASE-DECISION` |
| `IMP-ARCHIVED` | 战报 append | ops 并行；≠ `IMP-OBSERVING` |

正式映射见 `G7_state_machine/20_entry_conditions.md` §6、`30_exit_and_transitions.md` §1.3／§6；对账票 **`G8-RECON-IMP`**（W2-1-ENG ✓）。

---

## 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G8-RECON-IMP（W2-1-ENG）：IMP 正式名对账状态更新 |
| 2026-05-27 | G8-6（W2-3）：GOV 轨 **ART-GOV-RISK** v0.1 契约入表 |

---

## 边界声明

- **不**在本目录写完整 release gate 闸机（canary／prod 阈值等另票）；Release 轨仅字段级 artifact。
- **不**将 `battle_report` JSON 当作 Eng 轨全部正文；人读权威为 Work Report，机读 append 权威为 `ART-QA-BR` + schema。
- G10 rulebook 宜引用本目录 artifact ID，而非重复字段表。

---

## 引用

| 主题 | 路径 |
|------|------|
| 队列 | `workflow_v2/90_run_queue.md` |
| 依赖对账 | `workflow_v2/02_dependency_map.md` §4 |
| G7 entry | `workflow_v2/10_governance/G7_state_machine/20_entry_conditions.md` |
| G7 exit | `workflow_v2/10_governance/G7_state_machine/30_exit_and_transitions.md` |
| 工程母本 | `04_Workflows/ENGINEERING_CONTRACT.md` |
| 营运周期 | `04_Workflows/OPS_CYCLE.md` |
