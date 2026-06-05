# W3-A 试点案卷 — K-2 × ask Rollout / Canary

> **pilot_artifact_id**：`W3-A-K2-ASK-ROLLOUT-PILOT`  
> **总控**：`30_rollout/README.md` · `00_master_plan.md` §13.1  
> **IMP 轨**：可选；本试点以 **ART-REL** + run 记录为主（CHG-OBS-ONLY 精神）  
> **状态**：ORCH 骨架就绪；shadow／canary **未执行**

---

## 1. 案卷目标

在 **workflow_v2** 内完成 Wave 3 **W3-A** 最低 DoD（§13.4）：

1. **Phase 1 shadow**：≥7 日连续观测 + `shadow_run_*.md`  
2. **Phase 2 internal canary**：5–10% cohort ≥1 次 + `*_art_rel_*.json`  
3. **不宣称**远端 prod rollout 或 Phase 3+

---

## 2. 预期文件（施工后）

| 文件 | 票 | ART / 用途 |
|------|-----|------------|
| `W3-A_case.md` | 多票 | 案卷索引 + IMP 可选 |
| `shadow_run_01.md` … | W3-A-SHADOW-PILOT | 日／窗 run 记录 |
| `canary_env.md` | W3-A-REMOTE-ENV | cohort + env 逻辑名 |
| `canary_run_01.md` | W3-A-CANARY-PILOT | canary 窗记录 |
| `07_art_rel_dec.json` | W3-A-CANARY-PILOT | **ART-REL-DEC** |
| `08_art_rel_exec.json` | W3-A-CANARY-PILOT / REL-ARTIFACT | **ART-REL-EXEC** |
| `10_art_rel_obs.json` | W3-A-REL-ARTIFACT | **ART-REL-OBS**（可选） |

模板：`_TEMPLATE_art_rel_*.json` · schema → `30_rollout/artifact_schema_w3a.md`

---

## 3. 三张子票施工摘要

### W3-A-SHADOW-PILOT

| 项 | 内容 |
|----|------|
| **目标** | K-2×ask **shadow** 连续 **≥7 自然日**；每日指标可索引；对照 ask 主答案 |
| **DoD** | ≥1 份 `shadow_run_*.md`；spool/export/`eval_ci_check` 命令语义留痕；**不**改 user-facing 主路径 |
| **allowed_paths** | `30_rollout/`、`20_pilot/W3-A_case/`、observability 文档只读引用 |
| **禁区** | prod 主答案切换；merge adapter；secret |
| **软依赖** | `W3-B-INDEX-PIPELINE` 宜可查 index（ready/stale/missing） |
| **长上下文** | 否 |

### W3-A-REMOTE-ENV

| 项 | 内容 |
|----|------|
| **目标** | 规范 staging／远端等价 env 清单 + smoke/test 描述（零密钥） |
| **DoD** | `canary_env.md` + `30_rollout/env/env_matrix.md`（及可选 Runbook 一节） |
| **allowed_paths** | `30_rollout/env/`、`canary_env.md`、`04_Workflows/Runbooks/` 单节增补 |
| **禁区** | `.env` 原文；venv 树；远端 prod 自动 rollout |
| **长上下文** | 否 |

### W3-A-CANARY-PILOT

| 项 | 内容 |
|----|------|
| **目标** | 完成 **1 次** internal canary（**5–10%**）设计与执行案卷（ART-REL-DEC/EXEC） |
| **DoD** | `canary_run_*.md` + `07`/`08` art_rel JSON；rollback 演练勾 |
| **allowed_paths** | `30_rollout/`、`W3-A_case/*_art_rel_*.json`、`canary_run_*.md` |
| **禁区** | 远端 prod 自动 rollout；Phase 3+；改 adapter |
| **依赖** | `W3-A-SHADOW-PILOT` done；`W3-A-REMOTE-ENV` done |
| **软依赖** | `W3-C-CI-GATE-WIRE` nightly 至少一次 PASS |
| **长上下文** | 否 |

---

## 4. 索引

| 资源 | 路径 |
|------|------|
| Phase 映射 | `30_rollout/phase_map_k2_ask.md` |
| 链路边界 | `30_rollout/boundary_k2_ask.md` |
| W2-1 范式 | `20_pilot/W2-1_case/W2-1_case.md` |

---

## 5. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W3-A-ORCH 建案卷目录与施工摘要 |
