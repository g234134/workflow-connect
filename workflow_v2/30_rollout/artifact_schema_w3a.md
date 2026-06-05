# W3-A 案卷 Schema — ART-REL（rollout / canary）

> **对齐**：G8-5 `50_release_owner.md` **字段语义**（不复制条文）  
> **范式**：`20_pilot/W2-1_case/07_art_rel_dec.json`、`08_art_rel_exec.json`  
> **落盘**：`20_pilot/W3-A_case/*_art_rel_*.json`（**W3-A-CANARY-PILOT**／**W3-A-REL-ARTIFACT**）

---

## 1. 适用 artifact

| ID | 施工票 | 必填时机 |
|----|--------|----------|
| **ART-REL-DEC** | W3-A-CANARY-PILOT（shadow 可用简化 dec 或 defer 至 canary） | canary 开窗前 |
| **ART-REL-EXEC** | W3-A-CANARY-PILOT · W3-A-REL-ARTIFACT | cohort 配置生效后 |
| **ART-REL-OBS** | W3-A-REL-ARTIFACT（可选） | 窗末观测收口 |

**pilot_artifact_id 建议**：`W3-A-K2-ASK-ROLLOUT-PILOT`

---

## 2. ART-REL-DEC 扩展（在 G8-5 §4.1 基础上）

| 字段 | 必填 | W3-A 说明 |
|------|:----:|-----------|
| `artifact_id` | ✓ | 固定 `ART-REL-DEC` |
| `pilot_artifact_id` | ✓ | `W3-A-K2-ASK-ROLLOUT-PILOT` |
| `ticket_id` | ✓ | 如 `W3-A-CANARY-PILOT` |
| `release_id` | ✓ | 稳定批次 ID，含 phase 后缀，如 `w3a-p2-canary-YYYYMMDD` |
| `decision` | ✓ | `approve` \| `deny` \| `defer` |
| `release_scope.summary` | ✓ | 如「internal canary 5% K-2×ask」 |
| `target_audience_or_env` | ✓ | 逻辑名：`staging-internal` · `remote-equiv-staging`（**无** host/secret） |
| `rollback_strategy_draft` | ✓ | ask-only 回退步骤或显式 forward-fix |
| `qa_verdict_ref` | ✓ | 指向 shadow 窗 **ART-QA-REV** 或 checker 留痕（若无可写 `defer` + 理由） |
| `p0_blockers` | ✓ | approve 时 `[]` |
| `k2_phase` | ✓ | `shadow` \| `internal_canary`（**v2 扩展**） |
| `traffic_percent` | 条件 | canary 时 `5`–`10` |
| `shadow_window_days` | 条件 | shadow dec 时 ≥ `7` |
| `neighbor_authority_ref` | 推荐 | 字符串：`root_plan_4.8` · `k2_deployment_governance`（**不**贴全文） |

**命名 alias（W4-A-FIX-01）**：DEC 字段 `k2_phase=internal_canary` 与 gate checklist「canary 门」、trace 细步 `internal_canary`、VERDICT stdout `step=canary` 为同一 P2 phase 的不同层命名；权威对照表 → `20_pilot/W3-A_case/W4-A_gate_checklist.md` §0 与 config `trace_contract`。

---

## 3. ART-REL-EXEC 扩展（在 G8-5 §4.2 基础上）

| 字段 | 必填 | W3-A 说明 |
|------|:----:|-----------|
| `decision_ref` | ✓ | 指向 `*_art_rel_dec.json` |
| `published_at` | ✓ | ISO8601 |
| `execution_evidence` | ✓ | 对象，见下表 |
| `rollback_path_valid` | ✓ | 是否演练回退 |
| `not_in_scope` | 推荐 | 显式「无远端 prod 自动 rollout」 |

### `execution_evidence` 推荐键

| 键 | 说明 |
|----|------|
| `env_logical` | 与 DEC 一致 |
| `entrypoint` | 固定 `ask_api` |
| `merge_interface` | `ASK_MERGE_INTERFACE` / `merge_ask_and_k2`（逻辑名） |
| `metrics_ref[]` | `eval_ci_check` run id、spool 路径索引、日期范围 |
| `commands_run[]` | `{ "cmd": "...", "exit_ok": true, "note": "..." }`（**无** env 值） |
| `canary_cohort_ref` | 指向 `canary_env.md` |
| `canary_assignments[]` | per-task 分流：`task_id`、`in_canary_cohort`、`would_primary_source`（sim 产出；**非** `canary_cohort_state.json`） |
| `shadow_run_ref` | 指向 `shadow_run_*.md` |
| `trace_ref` | 推荐：指向 `run_records/<run_id>/rollout_trace.jsonl`（gate A6/B8 证据；只读 helper `wf_k2_rollout_gate_trace.py`） |

---

## 4. 模板文件

| 文件 | 用途 |
|------|------|
| `20_pilot/W3-A_case/_TEMPLATE_art_rel_dec.json` | DEC 骨架 |
| `20_pilot/W3-A_case/_TEMPLATE_art_rel_exec.json` | EXEC 骨架 |

---

## 5. `canary_cohort_state.json`（W4-A v0.1 sidecar · W4-A-FIX-03）

> **与 EXEC 区别**：`execution_evidence.canary_assignments` 含 per-task 分流；本文件为 run 目录级 **minimal** cohort 配置快照，**非** sim.py 产出。

| 项 | 说明 |
|----|------|
| **schema_version** | 固定 `w4a-canary-cohort-v0.1` |
| **v0.1 落点** | `20_pilot/W3-A_case/runs/<release_id>/canary_cohort_state.json`（例：`runs/w4a-int-20260529-pilot/`）— 暂定；**非**案卷根 |
| **产出时机** | 与 `runs/<release_id>/` 目录并存；canary 相关 run sidecar |
| **未来目标** | 可能迁至案卷根或增加统一别名/索引；须另票，**不**承诺时间 |

### 必填字段（v0.1）

| 字段 | 类型 | 语义 |
|------|------|------|
| `schema_version` | string | `w4a-canary-cohort-v0.1` |
| `active` | bool | cohort 窗是否逻辑开启（v0.1 rollback **不**回写此字段） |
| `traffic_percent` | int | 当前 cohort 流量百分比（如 `5`） |
| `primary_source` | string | cohort 内逻辑主源（如 `k2`）；cohort 外仍为 ask |
| `cohort_logical` | string | 逻辑 cohort 名（如 `staging-internal-k2-cohort-v1`） |
| `release_id` | string | 与 `runs/<release_id>/` 目录名对齐 |
| `recorded_at` | string | ISO8601 记录时间 |

### v0.1 限制

- **无** per-task 明细 → 见 `08_art_rel_exec.json` → `execution_evidence.canary_assignments` 或 `canary_run_01.md`。
- **无** rollback 回写：`-Phase rollback` 仅写案卷根 `rollback_record.json`；本文件可能仍 `active=true`。
- **不构成**完整自动治理证据；gate C1 可 **accepted_with_gaps**（见 `W4-A_gate_checklist.md` §G）。

**交叉引用**：runbook §5.2 · checklist C1 / §G · EXEC `canary_cohort_ref` → `canary_env.md`（环境逻辑名，非本 JSON 路径）。

---

## 6. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W3-A-ORCH 初版 |
| 2026-05-31 | W4-A-FIX-01：`k2_phase` ↔ trace ↔ gate 命名 alias；`execution_evidence.trace_ref` |
| 2026-05-31 | W4-A-FIX-03：`canary_cohort_state.json` v0.1 路径（`runs/<release_id>/`）、字段语义与限制（§5）；`canary_assignments` 与 sidecar 分工 |
