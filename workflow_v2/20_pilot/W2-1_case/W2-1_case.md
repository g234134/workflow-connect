# W2-1 试点案 — 工单与 IMP 状态（PM+Design+Eng+QA/Release 轨）

> **artifact_id**：`W2-1-G8-RECON-PILOT`  
> **试点标题**：G7↔G8 交叉引用 cleanup（G8-RECON-IMP 全链走通）  
> **primary_change_class**：**CHG-GOV-DOC**  
> **IMP 流索引**：`../W2-1_imp_flow_and_artifacts.md`  
> **imp_state_schema_version**：`0.1`  
> **总控**：`00_master_plan.md` §9

---

## 1. 任务描述

用一条极小但真实的治理文档变更，走通 Wave 2 导入生命周期（PM → Design → Eng → QA → Release → Observing），验证 G6/G7/G8/G10 治理层可支撑 **ART-*** 落盘与 **IMP-*** 状态记录。

**实质交付**（Eng 阶段执行）：G7-2／G7-3 stale 引用对账；G8-3 §2 改引 G7-1；`ART-REL-RECORD` → **ART-REL-EXEC**。不上 production、不做 MCP／CI enforcement。

---

## 2. 当前 IMP 状态（`imp_state_current`）

| 项 | 值 |
|----|-----|
| **`imp_state`（本记录）** | **`IMP-OBSERVING`** |
| **entry_owner_role（本态）** | `pm` |
| **entry_evidence_refs（本态）** | `09_art_pm_obs_plan.md` + `08_art_rel_exec.json` |
| **rework_target** | — |
| **imp_state_updated_at** | `2026-05-27` |
| **imp_state_updated_by_ticket** | `W2-1-QA-REL` |

### KB / Repo Index（`kb_index_current` · W4-B backfill）

> 说明：本段为 **W4-B-INDEX-INTEGRATION** 对接所需的“运行态前置”记录区，**不**改变 W2-1 在 2026-05-27 的历史迁移结论；仅用于让 ORCH/主工作流能在 `IMP-AI-READY` 前读取 `kb_index_*` 并形成可阻断行为。

| Field | Value |
|-------|-------|
| **`kb_index_status`** | `ready` |
| **`kb_index_source`** | `repo_index_v1` |
| **`kb_index_last_updated`** | `2026-05-29T10:30:00Z` |
| **`kb_index_job_id`** | `repo_index_v1_job__W2-1__main_repo__sample` |
| **`kb_index_scope_kind`** | `repo_subtree` |
| **`kb_index_subtree`** | `core` |
| **`kb_index_baseline_ref`** | `unpinned` |
| **`kb_index_stale_ack`** | `false` |
| **`kb_index_stale_reason`** | `-` |
| **`kb_index_reindex_ticket`** | `W4-B-INDEX-INTEGRATION` |
| **`kb_index_blocker`** | `-` |
| **`kb_index_evidence_refs`** | `workflow_v2/20_pilot/W3-B/index_status_W2-1.json` |

### Queue 索引（非 `imp_state` 字段 · 历史留痕）

| 项 | 值 |
|----|-----|
| **queue：W2-1-PM-DES** | **DONE**（2026-05-27） |
| **queue：W2-1-ENG** | **DONE**（2026-05-27） |
| **queue：W2-1-QA-REL** | **DONE**（2026-05-27） |

---

## 3. IMP 迁移日志（`imp_state_transitions`）

> 历史记录自 W2-1 试点整理入标准表头；**未删改**事件语义。禁止跳关见 G7-3。

| at | from | to | by | reason / artifact_refs |
|----|------|-----|-----|------------------------|
| 2026-05-27 | — | `IMP-SCOPE-DRAFT` | `W2-1-ORCH` / `pm` | W2-1-ORCH 建案卷；总控索引就绪 |
| 2026-05-27 | `IMP-SCOPE-DRAFT` | `IMP-SPEC-CLARIFY` | `W2-1-PM-DES` / `pm` | **ART-PM-SCOPE** 登记 |
| 2026-05-27 | `IMP-SPEC-CLARIFY` | `IMP-SPEC-CLARIFY` | `W2-1-PM-DES` / `pm` | **ART-PM-CLARIFY** + **ART-PM-GAPS** + **ART-DES-SPEC** 就绪 |
| 2026-05-27 | `IMP-SPEC-CLARIFY` | `IMP-SPEC-CLARIFY` | `W2-1-PM-DES` / `pm` | **exit**：澄清闭环；五轨缺口已列 |
| 2026-05-27 | `IMP-SPEC-CLARIFY` | `IMP-AI-READY` | `W2-1-ENG` / `engineering` | **ART-ENG-CTX** 登记（04） |
| 2026-05-27 | `IMP-AI-READY` | `IMP-REVIEW-READY` | `W2-1-ENG` / `engineering` | **ART-ENG-WR** 草案 + **ART-ENG-FIVE**（05） |
| 2026-05-27 | `IMP-REVIEW-READY` | `IMP-RISK-VALIDATION` | `W2-1-ENG` / `engineering` | **entry**：WR §4+§7 临时对照 G10-2 §5.3；**ART-GOV-RISK** defer W2-3 |
| 2026-05-27 | `IMP-RISK-VALIDATION` | `IMP-QA-READY` | `W2-1-ENG` / `engineering` | **exit**：**ART-ENG-EVD** + **ART-ENG-DOD**；G7/G8 实质 diff 完成 |
| 2026-05-27 | `IMP-QA-READY` | `IMP-RELEASE-DECISION` | `W2-1-QA-REL` / `qa` | **ART-QA-REV**（06）+ **ART-QA-DOD**（06.dod_checklist） |
| 2026-05-27 | `IMP-RELEASE-DECISION` | `IMP-RELEASED` | `W2-1-QA-REL` / `release` | **ART-REL-DEC** approve（07） |
| 2026-05-27 | `IMP-RELEASED` | **`IMP-OBSERVING`** | `W2-1-QA-REL` / `release` | **ART-REL-EXEC**（08）+ **ART-PM-OBS-PLAN**（09）+ **ART-REL-OBS** day-0（10） |

---

## 4. 已完成的 ART-*

### W2-1-PM-DES（2026-05-27）

| ART ID | 路径 | 摘要 |
|--------|------|------|
| **ART-PM-SCOPE** | `01_art_pm_scope.md` | CHG-GOV-DOC；in/out scope；G8-RECON-IMP 三文件 |
| **ART-PM-CLARIFY** | `02_art_pm_clarify.md` | 5 项 OQ 全 closed；3 项 defer；验收引用对齐 |
| **ART-PM-GAPS** | `02_art_pm_clarify.md` §ART-PM-GAPS | 五轨缺口已派 owner；Design review N/A |
| **ART-DES-SPEC** | `03_art_des_spec.md` | 6 条 spec + 6 条 AC；无 interface |

### W2-1-ENG（2026-05-27）

| ART ID | 路径 | 摘要 |
|--------|------|------|
| **ART-ENG-CTX** | `04_art_eng_ctx.md` | CHG-GOV-DOC；allowed_scope；禁区类型 |
| **ART-ENG-WR** | `05_art_eng_wr.md` | Work Report 七节 |
| **ART-ENG-FIVE** | `05_art_eng_wr.md` §ART-ENG-FIVE | C11 五要素 |
| **ART-ENG-EVD** | `05_art_eng_wr.md` §4 | grep AC-1–AC-4 Eng 侧 |
| **ART-ENG-DOD** | `05_art_eng_wr.md` §ART-ENG-DOD | FLOW-6.5 七项是 |

### W2-1-QA-REL（2026-05-27）

| ART ID | 路径 | 摘要 |
|--------|------|------|
| **ART-QA-REV** | `06_art_qa_rev.json` | verdict **accepted_with_gaps**；AC-1–AC-4 独立复验 |
| **ART-QA-DOD** | `06_art_qa_rev.json` → `dod_checklist` | 四键全 true |
| **ART-QA-EVD** | `06_art_qa_rev.json` → `evidence[]` | checker 重跑 grep + 人工 diff 审查 |
| **ART-REL-DEC** | `07_art_rel_dec.json` | decision **approve**；internal-doc-authority |
| **ART-REL-EXEC** | `08_art_rel_exec.json` | 四份 governance md 视为 repo 内权威 |
| **ART-PM-OBS-PLAN** | `09_art_pm_obs_plan.md` | 7 日轻量观测；4 信号 |
| **ART-REL-OBS** | `10_art_rel_obs.json` | day-0 interim；No incident observed |

**未产出（刻意 N/A 或下游票）**

| ART ID | 原因 |
|--------|------|
| ART-DES-REVIEW-PKG / ART-DES-REV | trivial 票 N/A |
| ART-GOV-RISK | defer → W2-3 |
| ART-QA-SMOKE / ART-QA-BR | CHG-GOV-DOC 票无 smoke runbook 门禁 |

---

## 5. 案卷文件索引

| # | 文件 | ART | 负责票 |
|---|------|-----|--------|
| 01 | `01_art_pm_scope.md` | ART-PM-SCOPE | W2-1-PM-DES ✓ |
| 02 | `02_art_pm_clarify.md` | ART-PM-CLARIFY + GAPS | W2-1-PM-DES ✓ |
| 03 | `03_art_des_spec.md` | ART-DES-SPEC | W2-1-PM-DES ✓ |
| 04 | `04_art_eng_ctx.md` | ART-ENG-CTX | W2-1-ENG ✓ |
| 05 | `05_art_eng_wr.md` | ART-ENG-WR + FIVE + EVD + DOD | W2-1-ENG ✓ |
| 06 | `06_art_qa_rev.json` | ART-QA-REV + DOD + EVD | W2-1-QA-REL ✓ |
| 07 | `07_art_rel_dec.json` | ART-REL-DEC | W2-1-QA-REL ✓ |
| 08 | `08_art_rel_exec.json` | ART-REL-EXEC | W2-1-QA-REL ✓ |
| 09 | `09_art_pm_obs_plan.md` | ART-PM-OBS-PLAN | W2-1-QA-REL ✓ |
| 10 | `10_art_rel_obs.json` | ART-REL-OBS | W2-1-QA-REL ✓ |

---

## 6. 施工票状态

| 票 ID | Status | IMP exit |
|-------|--------|----------|
| W2-1-ORCH | DONE | （索引） |
| W2-1-PM-DES | **DONE** | → IMP-SPEC-CLARIFY exit |
| W2-1-ENG | **DONE** | → **IMP-QA-READY** |
| W2-1-QA-REL | **DONE** | → **IMP-OBSERVING** |

---

## 7. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W2-1-PM-DES：PM+Design artifact 落盘；IMP 推进至 AI-READY 入口 |
| 2026-05-27 | W2-1-ENG：G7/G8 实质 diff + Eng artifact；IMP → **IMP-QA-READY** |
| 2026-05-27 | W2-1-QA-REL：QA 独立复验 + internal doc-authority release；IMP → **IMP-OBSERVING** |
| 2026-05-27 | W2-2-IMP-FIELD：§2／§3 对齐 `_TEMPLATE_case`；queue 行移入 §2 子节；章节 4–7 顺延 |




