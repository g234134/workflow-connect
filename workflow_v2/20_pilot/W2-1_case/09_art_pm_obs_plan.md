# ART-PM-OBS-PLAN — W2-1 轻量观测计划

> **artifact_id**：`W2-1-G8-RECON-PILOT`  
> **ticket_id**：`W2-1-QA-REL`  
> **G8 契约**：`10_governance/G8_artifact_contract/10_pm.md` §4.4  
> **release_ref**：`08_art_rel_exec.json` · `release_id`: `W2-1-G8-RECON-PILOT-doc-auth-20260527`

---

## 字段

| 字段 | 值 |
|------|-----|
| `artifact_id` | `W2-1-G8-RECON-PILOT` |
| `release_ref` | **ART-REL-EXEC**（`08_art_rel_exec.json`） |
| `observation_window` | **7 日历日**（自 2026-05-27 发布日起至 2026-06-03） |
| `exit_observation_condition` | 窗口内无 P0 交叉引用回归；或 orchestrator 轻量 spot-check 通过 |

---

## signals[]

| # | 信号 | 检查方式 | P0 条件 |
|---|------|----------|---------|
| S1 | 旧路径 `10_states.md` 被误引用 | `rg "10_states" workflow_v2/10_governance/` | 新 doc 引用错误路径且无勘误 |
| S2 | `ART-REL-RECORD` 回流 | `rg "ART-REL-RECORD" workflow_v2/10_governance/G7_state_machine/` | 占位 ID 重新出现 |
| S3 | stale「待 G8-」占位回流 | `rg "待 G8-" workflow_v2/10_governance/G7_state_machine/` | 未替换占位句重现 |
| S4 | G7 exit 误读（跳关） | 人工：读者反馈 IMP 迁移与 G7-3 §2.1 矛盾 | 制度误用导致错误派工 |

---

## 指标

| 项 | 值 |
|----|-----|
| 基线指标 | **无自动化指标**（doc-authority 票；W2-2 再议 imp_state tooling） |
| 无指标声明 | 本票 CHG-GOV-DOC 仅依赖 grep spot-check + 读者反馈 |

---

## 确认

| 项 | 值 |
|----|-----|
| owner | `pm`（W2-1-QA-REL release 轨代登记观测计划） |
| 登记日期 | 2026-05-27 |
