# W3-A 试点案 — K-2 × ask Rollout（索引）

> **artifact_id**：`W3-A-K2-ASK-ROLLOUT-PILOT`  
> **primary_change_class**：**CHG-OBS-ONLY**（rollout 观测；非 production code）  
> **imp_state**：*未启动*（可选；shadow 窗后可登记 `IMP-OBSERVING`）  
> **总控索引**：`30_rollout/README.md`

---

## 1. 任务描述

在 v2 导入工作流内，为 **K-2 × ask** 默认链完成 Wave 3 最低 rollout 观测：

- **Phase 1**：shadow ≥7 日 + run 案卷  
- **Phase 2**：internal canary 5–10% ≥1 次 + **ART-REL-DEC**／**ART-REL-EXEC**

**不做**：远端 prod 全自动；Phase 3+；改 merge adapter。

---

## 2. 当前状态

| 项 | 值 |
|----|-----|
| **W3-A-ORCH** | **DONE**（2026-05-27）— `30_rollout/` 骨架 |
| **W3-A-SHADOW-PILOT** | TODO |
| **W3-A-REMOTE-ENV** | TODO |
| **W3-A-CANARY-PILOT** | TODO |
| **W3-A-REL-ARTIFACT** | TODO |

---

## 3. 已完成的 ART-*

| ART ID | 路径 | 摘要 |
|--------|------|------|
| — | — | ORCH 阶段无 ART-REL；待 shadow／canary 子票 |

---

## 4. 案卷文件索引

| # | 文件 | 状态 |
|---|------|------|
| — | `README.md` | ✓ ORCH |
| — | `W3-A_case.md` | ✓ 本文件 |
| — | `shadow_run_*.md` | 待 SHADOW-PILOT |
| — | `canary_env.md` | 待 REMOTE-ENV |
| — | `canary_run_*.md` | 待 CANARY-PILOT |
| 07 | `07_art_rel_dec.json` | 待 CANARY-PILOT |
| 08 | `08_art_rel_exec.json` | 待 CANARY-PILOT |
| 10 | `10_art_rel_obs.json` | 待 REL-ARTIFACT（可选） |

---

## 5. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W3-A-ORCH 建案卷索引 |
