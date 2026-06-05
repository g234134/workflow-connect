# W4-A — K-2 Rollout Integration Runbook（runtime-only v0.1）

> **票号**：`W4-A-K2-ROLLOUT-INTEGRATION`  
> **模式**：runtime-only（不改 `00`/`90`/`99`、不做 doc-sync）  
> **固定流 ID**：`W4-A-PILOT-RELEASE-STREAM-v0.1`（`rollout_pipeline_config.json`）  
> **邻接**：`30_rollout/README.md` · `phase_map_k2_ask.md` · `docs/k2_deployment_governance.md`（只读）  
> **案卷**：`workflow_v2/20_pilot/W3-A_case/` · Gate：`W3-A_case/W4-A_gate_checklist.md`

---

## 1. 固定试点 release 流（选定）

| 项 | 值 |
|----|-----|
| **流名称** | W4-A internal K-2×ask pilot stream |
| **范式锚点** | W2-1 内部 **ART-REL**（`20_pilot/W2-1_case/07–08_art_rel_*.json`） |
| **Shadow 观测锚** | `.github/workflows/eval-gate-ci.yml` → `eval-shadow-nightly` 语义（**本票不改该 workflow**） |
| **环境** | `staging-internal`（逻辑名；零密钥） |
| **入口** | `ask_api`（user-facing 主权不变） |
| **合流** | `ASK_MERGE_INTERFACE` / `merge_ask_and_k2`（**不改** adapter） |
| **配置** | `workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json` |
| **执行器** | `workflow_v2/tools/wf_k2_rollout_run.ps1` · `wf_k2_rollout_canary_sim.py` |

---

## 2. 端到端路径（输入 → shadow → canary → 输出）

```text
[触发] -Phase full | shadow | canary
    │
    ▼
[输入] rollout_pipeline_config.json
    │
    ├─► P1 SHADOW（primary_source=ask，用户无感）
    │     unittest (k2_merge + k2_ask_shadow)
    │     → ibridge_exporter --source shadow (fixture)
    │     → eval_ci_check (ratio≤0.6, fail_on_tags=infra_risk)
    │     → run_records/<run_id>/shadow_run_01.md + shadow_state.json
    │
    ├─► P2 INTERNAL CANARY（5% cohort 模拟）
    │     → canary_env.md（首次生成）
    │     → 07_art_rel_dec.json + 08_art_rel_exec.json
    │     → run_records/<run_id>/canary_run_01.md
    │
    └─► rollout_trace.jsonl（每步 NDJSON）

[回退] -Phase rollback  → 案卷 rollback_record.json
[覆盖] -Phase override -OverrideBy <role> -OverrideReason "…"
```

---

## 3. K2 shadow 步骤

| 项 | 说明 |
|----|------|
| **目的** | 对照 ask 主路径记录 K-2 侧车；**不**切换 prod 主答案 |
| **记录** | `run_records/<run_id>/shadow_run_01.md`、`eval/shadow_ibridge_records.latest.jsonl`、`shadow_state.json` |
| **门控** | unittest exit 0 **且** `eval_ci_check` exit 0 |
| **完成确认** | `VERDICT=OK step=shadow`；`shadow_state.json` → `"ok": true` |

---

## 4. Internal canary 步骤

| 项 | 说明 |
|----|------|
| **cohort** | `sha256(salt:task_id) % 100 < traffic_percent`（默认 **5%**） |
| **cohort 内** | 逻辑 `primary_source=k2`（**仅**案卷/state；非 prod 路由代码） |
| **cohort 外** | 100% ask |
| **完成确认** | `VERDICT=OK step=canary`；`07`/`08` JSON 存在 |
| **cohort 分流明细** | `08_art_rel_exec.json` → `execution_evidence.canary_assignments`；`run_records/<run_id>/canary_run_01.md` |
| **cohort 状态 sidecar** | `runs/<release_id>/canary_cohort_state.json`（v0.1 暂定落点；见 §5.2） |

---

## 5. Rollback（最小）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_k2_rollout_run.ps1 -Phase rollback
```

| 项 | 说明 |
|----|------|
| **动作** | `traffic_percent=0`；`primary_source=ask` |
| **产物** | `W3-A_case/rollback_record.json` + trace `step=rollback` |
| **谁执行** | engineering on-call（可先斩后奏，24h 内报备尚書省） |

### 5.1 Rollback path 现况（W4-A v0.1 · W4-A-FIX-02）

| 项 | 说明 |
|----|------|
| **已有** | 最小手动 rollback：`-Phase rollback` 写 `rollback_record.json`（`traffic_percent=0`、`primary_source=ask`）；DEC 含 `rollback_strategy_draft` |
| **未有** | 完整**自动** rollback 流程（cohort 状态机回写、远端 prod 切换、端到端验证脚本） |
| **`08_art_rel_exec.json` → `rollback_path_valid: false`** | 如实表示「无完整自动 rollback path」；**非** gate 失败时改填 `true` |
| **语义** | `true` = rollback 设计存在且 pilot 内已验证最小 happy-path；`false` = 仅文档/手动路径，本轮未自动化验证（sim 默认 `false`） |
| **后续** | 自动 rollback + 验证 → **W4-A-FIX-02.x** 或 Wave 5 结构票；届时 EXEC 可置 `true` |

> **勿误导**：v0.1 不得宣称 rollback path 已完整实作；checklist B6 见 `W4-A_gate_checklist.md` §F。

### 5.2 Cohort 状态现况（W4-A v0.1 · W4-A-FIX-03）

| 项 | 说明 |
|----|------|
| **文件** | `canary_cohort_state.json` |
| **v0.1 实际路径** | `20_pilot/W3-A_case/runs/<release_id>/canary_cohort_state.json`（当前样例：`runs/w4a-int-20260529-pilot/`）— **非**案卷根；设计上的暂定落点 |
| **产出时机** | 与 `runs/<release_id>/` run 目录并存（canary 窗相关 sidecar）；**非** `wf_k2_rollout_canary_sim.py` 写入。sim 在 canary 步写案卷根 `07_art_rel_dec.json`、`08_art_rel_exec.json`、`canary_env.md` 及 `run_records/<run_id>/canary_run_01.md` |
| **schema** | `schema_version=w4a-canary-cohort-v0.1` |
| **关键字段** | `active`（bool）· `traffic_percent`（int，如 5）· `primary_source`（cohort 内逻辑主源，如 `k2`）· `cohort_logical`（逻辑 cohort 名）· `release_id` · `recorded_at`（ISO8601） |
| **分流明细在哪** | **不在**本 JSON。per-task 结果见 EXEC `execution_evidence.canary_assignments`（`in_canary_cohort`、`would_primary_source`）与 `canary_run_01.md`；sim stdout 含 `cohort_in_count` / `sample_count` |
| **用途（v0.1）** | 协助人工 cross-check cohort 配置是否与 DEC/EXEC 一致；**不**构成完整自动治理证据 |
| **未有** | 将最终 cohort 决策**回写**案卷根或统一索引；rollback 时**不**更新本文件（`active` 可能仍为 `true`）— 归零证据见案卷根 `rollback_record.json` |
| **理想目标** | 统一 cohort 状态落点 + rollback 自动回写 + 与 trace/EXEC 一致 — 后续 **W4-A-FIX-03.x** 或 Wave 5；**不**承诺时间点 |
| **Gate** | checklist C1 / §G；schema → `30_rollout/artifact_schema_w3a.md` §5 |

> **勿误导**：不得以 `runs/.../canary_cohort_state.json` 的 `active=true` 单独证明 rollback 未完成或 canary 仍在运行；v0.1 须 dual-check `rollback_record.json` 或标 **accepted_with_gaps**。

---

## 6. Override（最小）

| 谁可 override | CLI | 记录 |
|---------------|-----|------|
| `release` · `hq_governance` · `engineering_oncall` | `-Phase override -OverrideBy release -OverrideReason "…"` | `override_record.json` |

---

## 7. 调用示例

```powershell
# 一次完整 shadow + canary
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_k2_rollout_run.ps1 -Phase full
```

### 成功样例（实测 2026-05-29）

```text
VERDICT=OK step=shadow run_dir=workflow_v2/20_pilot/W3-A_case/run_records/2026-05-29_111042
VERDICT=OK step=canary run_dir=workflow_v2/20_pilot/W3-A_case/run_records/2026-05-29_111042
PILOT_STREAM=W4-A-PILOT-RELEASE-STREAM-v0.1
RUN_ID=2026-05-29_111042
TRACE=workflow_v2/20_pilot/W3-A_case/run_records/2026-05-29_111042/rollout_trace.jsonl
```

### 失败样例（shadow gate）

```text
VERDICT=FAILED step=shadow
```

exit `1`；trace 中 `k2_shadow_unittest` 或 `eval_ci_check_shadow` 的 `exit_ok=false`。

---

## 8. Trace 契约（gate ↔ rollout_trace.jsonl ↔ ART-REL）

> **配置权威**：`rollout_pipeline_config.json` → `trace_contract`（W4-A-FIX-01）  
> **Gate 清单**：`W3-A_case/W4-A_gate_checklist.md` §0  
> **只读 helper**：`workflow_v2/tools/wf_k2_rollout_gate_trace.py`

### 8.1 两层 step 名（勿混用）

| 层 | 用途 | Shadow 例 | Canary 例 |
|----|------|-----------|-----------|
| **VERDICT stdout** | 人读 / CI 摘要 | `step=shadow` | `step=canary` |
| **trace 细步** | 可复盘子命令 | `k2_shadow_unittest`, `ibridge_exporter_shadow`, `eval_ci_check_shadow` | `internal_canary` |
| **trace phase 摘要** | Gate A6/B8 快捷行（v0.2+） | `step=shadow`, `kind=phase_summary` | `step=canary`, `kind=phase_summary` |
| **ART-REL DEC** | 案卷发布 phase | `k2_phase=shadow` | `k2_phase=internal_canary` |

### 8.2 Gate 对照命令

```powershell
python workflow_v2/tools/wf_k2_rollout_gate_trace.py `
  --config workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json `
  --trace workflow_v2/20_pilot/W3-A_case/run_records/<run_id>/rollout_trace.jsonl
```

成功时 stdout JSON 含 `"ok": true` 与 `checks.A6` / `checks.B8` 明细；**不**改 rollout exit code。

### 8.3 历史 run 说明

2026-05-29 及更早 `run_records/**` **不 retro 补写** phase 摘要行；helper 对旧 trace 用 `trace_sub_steps` + `phase` 字段回退判定。新跑 `-Phase full|shadow|canary` 会追加 phase 摘要行（仅新 run_dir）。

---

## 9. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-29 | W4-A-K2-ROLLOUT-INTEGRATION runtime-only v0.1 |
| 2026-05-31 | W4-A-FIX-01：trace_contract、gate §0 命名对照、phase 摘要 trace、gate_trace helper |
| 2026-05-31 | W4-A-FIX-02：`rollback_path_valid` v0.1 语义对齐（template / checklist §F / runbook §5.1）；实产仍为 false |
| 2026-05-31 | W4-A-FIX-03：`canary_cohort_state.json` 路径与 cohort 语义（checklist C1 / §G / runbook §5.2 / schema §5）；实产仍在 `runs/<release_id>/`，rollback 不回写 |
