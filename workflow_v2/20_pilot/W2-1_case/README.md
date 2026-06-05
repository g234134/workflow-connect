# W2-1 试点案卷 — G7↔G8 交叉引用 cleanup



> **artifact_id**：`W2-1-G8-RECON-PILOT`  

> **ticket_id**：W2-1-PM-DES / W2-1-ENG / W2-1-QA-REL  

> **IMP 流索引**：`../W2-1_imp_flow_and_artifacts.md`  

> **工单摘要**：[`W2-1_case.md`](W2-1_case.md)  

> **当前 IMP**：**`IMP-OBSERVING`**（W2-1 最小闭环已走通）  
> **W2-2 tooling**：AC grep → `../../tools/wf_check_cross_ref.ps1`；`imp_state` 约定 → `../W2-2_imp_state_schema.md`  
> **W2-3 GOV pilot**：本案 **IMP-RISK-VALIDATION** 阶段曾用 WR §4／§7 临时对照；结构化 **ART-GOV-RISK**  retroactive 实例见 [`../W2-3_case/art_gov_risk.json`](../W2-3_case/art_gov_risk.json)（**不改变** 本案 verdict／IMP 历史）。



---



## ART 实例索引



| ART ID | 文件 | 票 | 状态 |

|--------|------|-----|------|

| ART-PM-SCOPE | [`01_art_pm_scope.md`](01_art_pm_scope.md) | W2-1-PM-DES | ✓ |

| ART-PM-CLARIFY | [`02_art_pm_clarify.md`](02_art_pm_clarify.md) | W2-1-PM-DES | ✓ |

| ART-PM-GAPS | [`02_art_pm_clarify.md`](02_art_pm_clarify.md) §ART-PM-GAPS | W2-1-PM-DES | ✓ |

| ART-DES-SPEC | [`03_art_des_spec.md`](03_art_des_spec.md) | W2-1-PM-DES | ✓ |

| ART-ENG-CTX | [`04_art_eng_ctx.md`](04_art_eng_ctx.md) | W2-1-ENG | ✓ |

| ART-ENG-WR | [`05_art_eng_wr.md`](05_art_eng_wr.md) | W2-1-ENG | ✓ |

| ART-QA-REV | [`06_art_qa_rev.json`](06_art_qa_rev.json) | W2-1-QA-REL | ✓ |

| ART-REL-DEC | [`07_art_rel_dec.json`](07_art_rel_dec.json) | W2-1-QA-REL | ✓ |

| ART-REL-EXEC | [`08_art_rel_exec.json`](08_art_rel_exec.json) | W2-1-QA-REL | ✓ |

| ART-PM-OBS-PLAN | [`09_art_pm_obs_plan.md`](09_art_pm_obs_plan.md) | W2-1-QA-REL | ✓ |

| ART-REL-OBS | [`10_art_rel_obs.json`](10_art_rel_obs.json) | W2-1-QA-REL | ✓ |



G8 契约附录实例索引见 `10_governance/G8_artifact_contract/10_pm.md` 附录 A、`20_design.md` 附录 A。

