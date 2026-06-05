# ART-PM-CLARIFY — W2-1 试点 Clarification Record

> **artifact_id**：`W2-1-G8-RECON-PILOT`  
> **sync_ref**：`01_art_pm_scope.md`  
> **G8 契约**：`10_governance/G8_artifact_contract/10_pm.md` §4.2

---

## open_questions

| id | question | status | resolution |
|----|----------|--------|------------|
| OQ-1 | G7-2 §4 IMP-RELEASED entry 是否保留 `ART-REL-RECORD` 占位名？ | **closed** | 改为 **ART-REL-EXEC**（对齐 G8-5 §命名对账）；Eng 在 W2-1-ENG 执行 diff。 |
| OQ-2 | G7-3 中「待 G8-1／待 G8-2／待 G8-5／待 G10-2」是否全部删除？ | **closed** | **否**。仅替换已交付轨的 stale 句为正式引用（G8-1 PM、G8-2 Design、G8-5 Release、G10-2 NBT §5.3）；未交付项（如 **ART-GOV-RISK**）保留 defer 并指向 W2-3。 |
| OQ-3 | `30_engineering.md` §2 是否整节重写为 G7-1 正式态表？ | **closed** | **否**。§2 保留占位别名表作历史索引，但 `对账参考` 列改引 G7-1 + 标注已冻结；删除错误文件名 `10_states.md`。 |
| OQ-4 | 本票是否需要 **ART-DES-REVIEW-PKG**／**ART-DES-REV**？ | **closed** | **N/A**（trivial 文档引用票）；记入 **ART-PM-GAPS** Design 轨 N/A；Eng 阶段 WR §3 若有 skeleton 由 checker 收口。 |
| OQ-5 | 验收是否要求 CI／`imp_state` tooling？ | **closed** | **否**（W2-2 范围）；本票验收 = grep spot-check + checker 只读对照 G8-RECON-IMP 清单。 |

---

## closed_summary

全部 open questions 已关闭：对账范围、保留／替换 stale 句的原则、Eng §2 改法、Design review 豁免、验收边界均已落定；`primary_change_class` = **CHG-GOV-DOC** 无变更。

---

## defer_items

| id | item | owner | defer_reason | target_state |
|----|------|-------|--------------|--------------|
| D-1 | **ART-GOV-RISK** G8 轨定稿 | W2-3 worker | 本试点用 WR §4+§7 临时对照 G10-2 | W2-3 完成后 `IMP-RISK-VALIDATION` 正式 entry |
| D-2 | `imp_state` 机读 enforcement | W2-2 worker | Wave 2 tooling 未就绪 | W2-2 |
| D-3 | G8 README「IMP 正式名 **待 G8-RECON-IMP**」 | W2-1-ENG | 实质 diff 由 Eng 票合并 | `IMP-QA-READY` 前 README 同步 |

---

## dependencies

| ref | type | status |
|-----|------|--------|
| `W2-1-ORCH` | ticket | **ok**（DONE） |
| `CHK-W1` | gate | **ok**（PASS-WITH-NOTES） |
| `G8-5` `50_release_owner.md` | artifact contract | **ok**（ART-REL-EXEC 命名权威） |
| `G7-1` `10_workflow_states.md` | state list | **ok**（IMP 正式名冻结） |
| `W2-1-ENG` | downstream ticket | **TBD**（本票 exit 后开工） |

---

## acceptance_ref

- **主验收**：`W2-1_imp_flow_and_artifacts.md` §4 in_scope 逐项 grep／只读 diff 对照。
- **Eng 证据**：`ART-ENG-EVD`（W2-1-ENG）— 含 stale 句清零命令与关键输出语义。
- **QA 收口**：`ART-QA-REV`（W2-1-QA-REL）— checker 只读；`verdict` ∈ {`accepted`, `accepted_with_gaps`}。
- **Release**：内部 doc-authority；`ART-REL-EXEC.target_audience_or_env` = `workflow_v2/10_governance/` 读者。

---

## scope_delta

相对 `01_art_pm_scope.md` v1：**无 scope 扩缩**；仅澄清 stale 句处理粒度与 Design review 豁免。

---

## ART-PM-GAPS（五轨缺口清单）

> 嵌入本 clarify 记录；满足 G7-3 `IMP-SPEC-CLARIFY` exit ②。

| track | artifact_id | missing_fields / 状态 | owner | target_ticket |
|-------|-------------|----------------------|-------|---------------|
| pm | ART-PM-OBS-PLAN | 未产出（`IMP-OBSERVING` entry 前） | W2-1-QA-REL | W2-1-QA-REL |
| design | ART-DES-REVIEW-PKG | **N/A**（trivial 票） | — | — |
| design | ART-DES-REV | **N/A**（trivial 票） | — | — |
| eng | ART-ENG-CTX | 全字段待 W2-1-ENG | W2-1-ENG | W2-1-ENG |
| eng | ART-ENG-WR／EVD／DOD | 待施工 | W2-1-ENG | W2-1-ENG |
| qa | ART-QA-REV | 待 Eng 完成后 | W2-1-QA-REL | W2-1-QA-REL |
| release | ART-REL-DEC／EXEC | 待 QA 通过后 | W2-1-QA-REL | W2-1-QA-REL |

| 字段 | 值 |
|------|-----|
| `all_tracks_addressed` | **true** |
| `notes` | 纯 CHG-GOV-DOC 文档票；Design peer review 标 N/A；Eng／QA／Release 缺口已派 W2-1-ENG／W2-1-QA-REL。 |
