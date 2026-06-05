# W3-A — Allowed Paths & 禁区（子票）

> **票号**：W3-A-ORCH  
> **用途**：派工 guard／worker 路径白名单；**不**替代 G6 ACT 表

---

## 全局禁区（W3-A 全线）

- 修改 `10_governance/G6_*`／`G7_*`／`G8_*`／`G10_*` **正文语义**
- 修改 `core/k2_merge_adapter.py`、`gov_core_system` production deploy、merge adapter 逻辑
- 远端 **prod** 全自动 rollout；K-2 Phase **3+**
- `.env` 原文、venv 树、密钥、完整连接字串
- 可执行 canary／shadow **自动化脚本**（仅 runbook／案卷／schema）

---

## W3-A-SHADOW-PILOT

| 类 | 路径 |
|----|------|
| **允许** | `workflow_v2/30_rollout/**`（只读引用 + 本票可写 `shadow` 索引节） |
| **允许** | `workflow_v2/20_pilot/W3-A_case/shadow_run_*.md`、`W3-A_case.md` |
| **允许** | observability **只读**引用（`docs/k2_deployment_governance.md`、根 plan §4.8 摘要写入案卷） |
| **禁止** | prod 流量切换；改 merge adapter；写 deploy 脚本 |
| **DoD** | ≥7 日 shadow 连续观测 + ≥1 份可回溯 `shadow_run_*.md`；指标指向 spool/export（名称） |

**长上下文**：否

---

## W3-A-REMOTE-ENV

| 类 | 路径 |
|----|------|
| **允许** | `workflow_v2/30_rollout/env/**` |
| **允许** | `workflow_v2/20_pilot/W3-A_case/canary_env.md` |
| **允许** | `04_Workflows/Runbooks/` **补一节**（仅 env 清单／smoke 步骤描述；须单票注明文件名） |
| **禁止** | `.env`、venv、secret、硬编码磁盘路径 |
| **DoD** | env 逻辑名表 + cohort 定义 + smoke/test **步骤**（命令占位符用 `<RUNNER>`，无密钥） |

**长上下文**：否

---

## W3-A-CANARY-PILOT

| 类 | 路径 |
|----|------|
| **允许** | `workflow_v2/30_rollout/**` |
| **允许** | `workflow_v2/20_pilot/W3-A_case/canary_run_*.md`、`*_art_rel_*.json` |
| **禁止** | 远端 prod 自动 rollout；Phase 3+；改 adapter |
| **DoD** | 1 次 internal 5–10% canary 设计与执行案卷；**ART-REL-DEC** + **ART-REL-EXEC** |
| **软依赖** | `W3-C-CI-GATE-WIRE` nightly PASS 留痕；`W3-A-REMOTE-ENV` done |

**长上下文**：否

---

## W3-A-REL-ARTIFACT（索引）

| 类 | 路径 |
|----|------|
| **允许** | `20_pilot/W3-A_case/` 内 ART-REL 与 obs 块 |
| **DoD** | 对齐 G8-5；shadow+canary 观测链可索引 |

---

## 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W3-A-ORCH 初版 |
