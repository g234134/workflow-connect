# G10 — Governance Rulebook

> **状态**：G10-1／G10-2 v0.1 已定稿。  
> **禁止**：总控 chat 覆写模块正文（除对账修正票）。

## 产物

| 文件 | 票号 | 状态 |
|------|------|------|
| `10_ai_usage_boundary.md` | G10-1 | v0.1（AI 宜参与／不宜主导；guard／checker／owner；三权限制；CHG 引用步骤） |
| `20_no_blind_trust.md` | G10-2 | v0.1（NBT-* 不可盲信清单；NBT-H-* 人工确认；deny/stop_work/rejected/blocked 禁止动作；IMP-RISK-VALIDATION 对照） |

## 实现落点（W2-2 · 索引）

| 主题 | 路径 |
|------|------|
| **QA 可勾选 checklist**（NBT-T01～T07） | `workflow_v2/20_pilot/W2-2_tooling_notes.md` §4–§4.1 |
| **ART-QA-REV 推荐字段** `tooling_checks` | `G8_artifact_contract/40_qa.md` §5 |
| AC grep 脚本 | `workflow_v2/tools/wf_check_cross_ref.ps1` |

> G10-2 定 **不可盲信** 规则；上表为 checker **怎么做** 的 tooling 层，**不** 扩 G10-2 枚举或语义。

## 阅读顺序

1. **G6-1** — `primary_change_class` 是什么。  
2. **G6-2** — 谁可 PATCH、何时必 guard／checker。  
3. **G10-1** — AI **参与边界**（本目录）。  
4. **G10-2** — 禁止**盲信** AI 输出的情境（另册，不重复 G10-1）。

## 上游／下游

| 模块 | 关系 |
|------|------|
| G6 | CHG-*／ACT-* 权威；G10 **只引用** |
| G7 | `IMP-AI-READY` 起宜满足 G10-1；`IMP-RISK-VALIDATION` 叠加 G10-2 |
| G8 | **ART-GOV-RISK**（`IMP-RISK-VALIDATION`）；ART-ENG-WR、ART-QA-REV、ART-REL-* 为验收与发布载体 |
| CHK-W1 | Wave 1 只读对账（依赖 G10-2 完成后盘点更完整） |
