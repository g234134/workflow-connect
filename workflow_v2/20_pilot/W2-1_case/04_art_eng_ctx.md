# ART-ENG-CTX — W2-1 试点 Context Brief

> **artifact_id**：`W2-1-G8-RECON-PILOT`  
> **ticket_id**：`W2-1-ENG`  
> **G8 契约**：`10_governance/G8_artifact_contract/30_engineering.md` §4.1  
> **imp_state 登记时态**：`IMP-AI-READY` entry

---

## 必填字段

| 字段 | 值 |
|------|-----|
| `role` | **engineering**（W2-1-ENG worker；大唐副官 Eng 轨） |
| `ticket_id` | `W2-1-ENG` |
| `primary_change_class` | **CHG-GOV-DOC**（G6-1；票面无 secondary） |
| `allowed_scope` | `workflow_v2/10_governance/G7_state_machine/20_entry_conditions.md`；`30_exit_and_transitions.md`；`G8_artifact_contract/30_engineering.md` §2；`G8_artifact_contract/README.md`；`20_pilot/W2-1_case/` Eng artifact（04–05） |
| `forbidden_zone_types` | 憲法 §7 全类型（Z-ENV、Z-VENV-TREE、Z-RUNTIME-CP、Z-ORCH-DESTRUCT、Z-DARK-OPS、Z-HQ-LIQUIDATION、Z-HQ-ENV-EDIT）；**不**改 G6/G7/G8/G10 **治理条文语义**；**不**改 production／暗部 `core` |

---

## plan_summary（2–5 行）

1. 读 PM scope／Design spec／G6 allowed actions；确认 **CHG-GOV-DOC** + 三文件 in_scope。
2. G7-2：替换已交付 G8/G10 stale 占位句；`ART-REL-RECORD` → **ART-REL-EXEC**；保留 **ART-GOV-RISK** defer（W2-3）。
3. G7-3：同上原则；`IMP-RISK-VALIDATION` exit ② 改引 G10-2 §5.3；§6 ART 索引更新。
4. G8-3 §2：改引 G7-1 `10_workflow_states.md`；标注 G7-1 已冻结。
5. 跑 AC grep 验证 → 写 Work Report + 推进 `IMP-QA-READY`。

---

## G6-2 拟执行 ACT

| ACT | 适用 | 说明 |
|-----|------|------|
| ACT-READ | ✓ | PM/Design artifact、G6/G7/G8 源档 |
| ACT-PATCH | ✓ | 票面 allowed_scope 内 md |
| ACT-VERIFY | ✓ | grep spot-check（→ ART-ENG-EVD） |
| ACT-GUARD | — | 本票 trivial 单域 doc；guard 推荐（R）未强制 |

---

## 确认

| 项 | 值 |
|----|-----|
| 登记方 | engineering（W2-1-ENG） |
| 登记日期 | 2026-05-27 |
| scope 对齐 | **ART-PM-SCOPE**／**ART-DES-SPEC** 一致 ✓ |
