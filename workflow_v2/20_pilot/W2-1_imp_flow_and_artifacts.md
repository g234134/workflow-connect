# W2-1 — IMP 状态流与 ART-* 对照（试点案）

> **角色**：W2-1 总控 orchestrator 附属索引；施工 chat **消费** G7/G8 权威正文，不在此档重定义契约。  
> **试点标题**：G7↔G8 交叉引用 cleanup（G8-RECON-IMP 全链走通）  
> **案卷目录**：`workflow_v2/20_pilot/W2-1_case/`（各 **ART-*** 实例文件由施工票写入）  
> **primary_change_class**：**CHG-GOV-DOC**

---

## 1. 本案件 IMP 状态流

```text
IMP-SCOPE-DRAFT
    → IMP-SPEC-CLARIFY
    → IMP-AI-READY
    → IMP-REVIEW-READY
    → IMP-RISK-VALIDATION
    → IMP-QA-READY
    → IMP-RELEASE-DECISION
    → IMP-RELEASED
    → IMP-OBSERVING
```

**合法回退**：`IMP-REWORK`（见 G7-3）；本试点预期 **不触发**，若 QA `rejected` 则按 G7-3 回 Eng。

---

## 2. 状态 → Artifact 对照表

| IMP 状态 | 进入时须具备（entry 摘要） | 本状态产出 / 更新 **ART-*** | G8 权威 |
|----------|---------------------------|------------------------------|---------|
| **IMP-SCOPE-DRAFT** | 任务卡／尚書省指令 | **ART-PM-SCOPE** | `10_pm.md` §4.1 |
| **IMP-SPEC-CLARIFY** | ART-PM-SCOPE 已登记 | **ART-PM-CLARIFY**、**ART-PM-GAPS**（若需）、**ART-DES-SPEC** | `10_pm.md` §4.2–4.3；`20_design.md` §4.1 |
| **IMP-AI-READY** | 澄清 closed；`primary_change_class` 落定 | **ART-ENG-CTX**；CHG-* + allowed_paths 写入 CTX | `30_engineering.md` §4.1 |
| **IMP-REVIEW-READY** | CTX + guard 允许（若触制度边界） | **ART-ENG-WR**（草案）、**ART-ENG-FIVE** | `30_engineering.md` §4.2、§4.3 |
| **IMP-RISK-VALIDATION** | WR 草案齐备 | 风险对照：**暂** WR §4 + §7（对照 G10-2 NBT-*）；**ART-GOV-RISK** 正式轨 → W2-3 | G10-2；G7-3 §3 RISK exit |
| **IMP-QA-READY** | RISK exit ② 满足 | **ART-ENG-EVD**、**ART-ENG-DOD**；可选 **ART-DES-REV** `approved` | `30_engineering.md` §4.4–4.5；`20_design.md` §4.2 |
| **IMP-RELEASE-DECISION** | DoD 四键为真；EVD 可重跑 | **ART-QA-REV**（checker）；**ART-REL-DEC**（release owner） | `40_qa.md`；`50_release_owner.md` §4.1 |
| **IMP-RELEASED** | REL-DEC = `approve` | **ART-REL-EXEC**（内部 doc-authority 生效） | `50_release_owner.md` §4.2 |
| **IMP-OBSERVING** | EXEC 已记录 | **ART-PM-OBS-PLAN**、**ART-REL-OBS**（轻量：7 日无 P0 + 交叉引用 spot-check） | `10_pm.md` §4.4；`50_release_owner.md` §4.3 |

---

## 3. 施工票与 IMP 推进边界

| 票 ID | 推进至 IMP 状态（exit） | 写入 `20_pilot/W2-1_case/` 的 ART |
|-------|-------------------------|-----------------------------------|
| **W2-1-PM-DES** | → **IMP-SPEC-CLARIFY** exit（可含 Design peer review 就绪） | ART-PM-SCOPE、ART-PM-CLARIFY、ART-DES-SPEC |
| **W2-1-ENG** | → **IMP-QA-READY** | ART-ENG-CTX、ART-ENG-WR、ART-ENG-FIVE、ART-ENG-EVD、ART-ENG-DOD；**plus** `10_governance/` 实质 diff |
| **W2-1-QA-REL** | → **IMP-OBSERVING**（或 OBS exit 轻量收口） | ART-QA-REV、ART-REL-DEC、ART-REL-EXEC、ART-PM-OBS-PLAN、ART-REL-OBS |

---

## 4. 本案件 in_scope / out_scope（索引）

**in_scope**（Eng 实质，来自 G8-RECON-IMP）：

- `G7_state_machine/20_entry_conditions.md`、`30_exit_and_transitions.md`：`ART-REL-RECORD` → **ART-REL-EXEC**；去 stale「待 G8-x／待 G10-2」。
- `G8_artifact_contract/30_engineering.md` §2：改引 `10_workflow_states.md` +「G7-1 已冻结」。

**out_scope**：

- 改 G6/G7/G8/G10 **治理条文**（change class 定义、IMP exit 规则、NBT 表等 **正文语义**）。
- production code、hooks、CI enforcement、`imp_state` 字段（W2-2）。
- **ART-GOV-RISK** G8 轨定稿（W2-3）。

---

## 5. 案卷文件命名建议（非强制）

| ART ID | 建议路径 |
|--------|----------|
| ART-PM-SCOPE | `W2-1_case/01_art_pm_scope.md` |
| ART-PM-CLARIFY | `W2-1_case/02_art_pm_clarify.md` |
| ART-DES-SPEC | `W2-1_case/03_art_des_spec.md` |
| ART-ENG-CTX | `W2-1_case/04_art_eng_ctx.md` |
| ART-ENG-WR | `W2-1_case/05_art_eng_wr.md` |
| ART-QA-REV | `W2-1_case/06_art_qa_rev.json` |
| ART-REL-DEC | `W2-1_case/07_art_rel_dec.json` |
| ART-REL-EXEC | `W2-1_case/08_art_rel_exec.json` |
| ART-PM-OBS-PLAN | `W2-1_case/09_art_pm_obs_plan.md` |
| ART-REL-OBS | `W2-1_case/10_art_rel_obs.json` |

---

## 6. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W2-1 总控：试点 IMP 流 + ART 对照 + 施工票边界 |
