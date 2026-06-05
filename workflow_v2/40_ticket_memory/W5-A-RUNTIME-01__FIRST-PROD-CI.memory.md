# Ticket Memory — W5-A-RUNTIME-01

> **用途**：W5-A-K2-ROLLOUT-EXPANSION 首条 **prod CI 集成** runtime 子票；在单一、明示命名的 prod（或 prod-equivalent）release workflow 中嵌入 K-2 rollout（shadow → canary → promote），范围可审计、可回滚。  
> **父票**：`workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`  
> **控制面**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`（`lane=runtime` · Reviewer §1.4.1 · 须 governance-guard approve 后 merge）  
> **模板**：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`  
> **本文件产出切片**：planning（仅 Ticket Memory；**无** CI / runtime / tools 变更）

---

## ticket

- id: **W5-A-RUNTIME-01**
- title: **K-2 rollout · 首条 prod CI 集成 · runtime-only**

## lane

- lane: **runtime**

## priority

- priority: **P0**（首条 prod CI 集成；触及 prod-equivalent 流水线，须高于 W5-A 父票 planning 的 P1，并优先于同 Wave 非阻塞子票）

## mode

- mode: **runtime-only**（Executor 在 `write_set` 内做 CI / rollout 配置增量；**不**在本 lane 改写 `00`/`90`/`99` 全局语义——属 W5-A-DOCSYNC-01）

## goal

在 **W5-A-K2-ROLLOUT-EXPANSION** 规划下，选定 **一条、命名明确** 的 prod（或 prod-equivalent）CI workflow（例如 `.github/workflows/<SERVICE>-release.yml` 中的单一 release job），将 K-2 rollout 阶段 **嵌入** 该流水线，且满足：

1. **阶段完整**：流水线须包含可索引的 **shadow → canary → promote**（或经批准的 **full rollout** 等价阶段）；每阶段有 documented 进入/退出条件与 CI 日志或 workflow run id 证据。
2. **渐进交付**：**禁止**一次性将全量用户流量切到 K-2 主答案；cohort 扩面须分阶（可与 W5-A 多 cohort 策略表对齐，首条流可先实现最小阶梯，但不得 skip 至 100% 而无中间 gate）。
3. **保护机制保留**：延续 W4-A allowlist + `reason` 语义——**rollback**、**pause**、**override** 在 prod CI 路径上仍可触发且可审计（`rollback_record` / trace 行 / 等价字段）。
4. **Gate 对齐**：canary / promote 决策点须可引用 **W4-B index gate**（`IMP-AI-READY` 前 `kb_index_*` 非 `missing`）与 **W4-C gov gate** 指标（`gov-metrics-0.1` JSONL / `gov-gate-metrics.yml` 输出）；不得绕过既有 gate「偷偷 release」。
5. **范围可审计**：改动仅落在票面 `write_set` 锁定的 **一条** workflow 文件与指定 job/step；新增 rollout 流使用 **新 `stream_id`**（建议 `W5-A-PROD-RELEASE-STREAM-v0.1`），与 W4-A 试点流 `W4-A-PILOT-RELEASE-STREAM-v0.1` **并存**，不 retro 改写 W4-A DONE 口径。

**开工前阻塞项（Planning 须先填）**：`read_set` / `write_set` 中的 **「首条 prod CI 目标 workflow」** 占位须由 Planning lane 或 Supervisor 替换为 **具体 repo 相对路径 + job 名 + step 锚点**（例：`.github/workflows/service-X-release.yml` · `job: release` · `step: k2-rollout-shadow`）。未替换前 **不得** 开工 runtime。

## read_set

> 未列出默认不读。暗部脚本 / venv / `.env` / 未授权 checkpoint **禁止**。

### 父票与制度（必读）

| 路径 | 用途 |
|------|------|
| `workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md` | 父票 goal / frozen_constraints / 整票 DoD；本票为其 **首条 prod CI** 切片 |
| `workflow_v2/30_control_plane/W4-X_control_plane_mvp.md` | Lane 边界、Reviewer §1.4.1、governance-guard 放行约定 |
| `docs/k2_deployment_governance.md` | K-2 prod 流量切换角色矩阵与 Phase 门控（只读） |
| `docs/k2_merge_strategy.md` | 合流语义（只读；**不**改 merge adapter） |
| `AGENTS.md`、`04_Workflows/HARNESS_CONSTITUTION.md` | 工程红线与憲法 §7 禁区类型 |

### W4-A 试点流基线（只读 · 不 retro）

| 路径 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` | Shadow / canary / rollback / override 端到端权威 |
| `workflow_v2/20_pilot/W3-A_case/W4-A_rollout_runbook.md` | 案卷侧索引 |
| `workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json` | `W4-A-PILOT-RELEASE-STREAM-v0.1`（**只读**；本票新建 prod 流配置） |
| `workflow_v2/20_pilot/W3-A_case/W4-A_release_stream.json` | 流指针 |
| `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` | Shadow / Canary / Rollback gate 勾选范式 |
| `workflow_v2/tools/wf_k2_rollout_run.ps1` | 本地 helper 参考（prod CI 可薄封装调用，非唯一入口） |
| `workflow_v2/tools/wf_k2_rollout_canary_sim.py` | Cohort 逻辑参考 |
| `workflow_v2/20_pilot/W3-A_case/run_records/**` | W4-A 历史证据（**禁止**篡改） |

### W4-B / W4-C gate（canary / promote 决策依赖）

| 路径 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md` | Index / `IMP-AI-READY` gate |
| `workflow_v2/tools/wf_kb_index_gate.ps1` | Index allow/deny 行为 |
| `workflow_v2/20_pilot/W3-C/ci_gate_wire.md` | PR / nightly / manual 接线 |
| `workflow_v2/20_pilot/W3-C_metrics_schema.md` | `gov-metrics-0.1` schema |
| `workflow_v2/observability/gov_gate_metrics/*.jsonl` | 治理指标时间序列 |
| `workflow_v2/tools/wf_emit_gov_gate_metrics.ps1` | CI → JSONL emitter |
| `.github/workflows/gov-gate-metrics.yml` | W4-C 已落地 gov 指标 CI |
| `.github/workflows/eval-gate-ci.yml` | W4-A 锚定 shadow nightly（`eval-shadow-nightly`）；集成时评估 **新增 job** vs 改既有 release |

### 首条 prod CI 目标（占位 · Planning 开工前必填）

| 占位 | 说明 |
|------|------|
| `.github/workflows/<SERVICE>-release.yml` | **首条 prod CI 目标 workflow**（占位；替换为具体文件名，如 `service-X-release.yml`） |
| `<TARGET_JOB_NAME>` | 嵌入 rollout 的 job 名（占位） |
| `<TARGET_STEP_ANCHOR>` | shadow / canary / promote 步骤锚点或 step id 前缀（占位） |

### 控制面挂点（Executor 只读；doc-sync 另票写）

| 路径 | 用途 |
|------|------|
| `workflow_v2/90_run_queue.md` | 本票 Status/Notes 对账 |
| `workflow_v2/99_latest_status.md` | 阶段摘要对账 |
| `workflow_v2/00_master_plan.md`（§15.7） | W5-A 能力挂点 |

## write_set

> **IMPORTANT**：下列为 **文字锁定范围**；具体文件名须在 **Planning lane 续卡** 中显式填入后，Executor 方可动档。当前 Memory **不写** 具体 service 名。

### 允许（runtime 切片 · 开工前须 Planning 填实）

1. **单一 release workflow 文件**  
   - 仅允许修改 **一条**、票面明示命名的 prod（或 prod-equivalent）release workflow（占位：`.github/workflows/<SERVICE>-release.yml`）。  
   - 改动 **仅限** 该文件中 Planning 指定的 **job / step**（占位：`<TARGET_JOB_NAME>` · `<TARGET_STEP_ANCHOR>`）内插入或调整与 K-2 rollout 相关的步骤（shadow、canary、promote、rollback hook、pause/override 触发点）。  
   - **禁止** 修改其他 service 的 release workflow、**禁止** blanket 修改全部 `.github/workflows/*`。

2. **Rollout 配置（新增或扩展 · 不删 v0.1 试点流）**  
   - 允许新增并行 prod 流配置，例如新 `stream_id` **`W5-A-PROD-RELEASE-STREAM-v0.1`**（或 Planning 指定名），存放于 `rollout_pipeline_config.json` 的 v0.2+ 段、或 `workflow_v2/20_pilot/W3-A/rollout_streams/*.json`（路径以 Planning 锁定为准）。  
   - **禁止** 删除或 retro 改写 `W4-A-PILOT-RELEASE-STREAM-v0.1` 定义与 W4-A 历史 `run_records/**`。

3. **Helpers（薄封装 · 可选）**  
   - `workflow_v2/tools/wf_k2_rollout_*` 扩展：须结构化 `dict` 输出、可观测；**禁止** 改 `merge_ask_and_k2` / K-2 adapter（另开 adapter 票）。

4. **本票 run 证据（新增 · 不篡改 W4-A 历史）**  
   - `workflow_v2/20_pilot/W3-A_case/run_records/**` 下 **新** run id 目录（CI run id 索引、trace、rollback 记录）。  
   - 可选：`workflow_v2/20_pilot/W3-A/W5-A_first_prod_ci_runbook.md`（首条 prod CI SOP 片段；若与父票 runbook 合并须 doc-sync 票同步）。

### 禁止（除非尚書省 override + Progress/notes 末尾留痕）

- 暗部脚本 / venv 树 / `.env` / runtime checkpoints  
- 未列名修改 **其他** `.github/workflows/*`（含未授权的 eval / gov workflow 语义变更）  
- `00_master_plan.md` / `90_run_queue.md` / `99_latest_status.md` 全局语义（→ **W5-A-DOCSYNC-01**）  
- `merge_ask_and_k2`、adapter 实现、G7/G8 正文语义  
- 本 **planning 产出切片** 内写入任何 CI / tools / config（仅本文）

### Planning 续卡必填项（开工 gate）

| 字段 | 填法 |
|------|------|
| `target_workflow_path` | 例：`.github/workflows/service-X-release.yml` |
| `target_job` | 例：`release` |
| `target_steps` | shadow / canary / promote / rollback 步骤名或 YAML 锚点列表 |
| `prod_stream_id` | 例：`W5-A-PROD-RELEASE-STREAM-v0.1` |
| `feature_flag_keys` | prod 开关与回滚 plan 引用（不得为空） |

## frozen_constraints

> 复用 **W5-A-K2-ROLLOUT-EXPANSION** §frozen_constraints（1–7）；下列为 **本子票追加**。

### 自 W5-A 父票继承（摘要 · 细则见父票）

1. **渐进交付**：禁止一次性全量 K-2 主答案；shadow → 有限 cohort canary → 扩面 → 全量。  
2. **每阶段保护**：可观测指标、自动/人工停止条件、rollback/fallback、pause/override（allowlist + `reason`）。  
3. **治理对齐**：G7/G8、`W4-B` index gate、`W4-C` gov metrics；遵从 `docs/k2_deployment_governance.md`；worker 不得自订 rollout 阈值覆盖 playbook。  
4. **扩面授权**：本票 **仅一条** workflow；第二 repo/服务 → **W5-A-RUNTIME-02**。  
5. **W4-A 边界**：不 retro W4-A DONE；试点流与历史 run **只读**。  
6. **控制面**：不实现 W4-X §0 Out of Scope（自动开 chat、自动 merge、deny engine runtime 等）。  
7. **憲法 §7 禁区**：暗部、venv、金鑰原文、双 Telegram 监听等见 `AGENTS.md`。

### 本子票追加

8. **CHK-W4 依赖**：**CHK-W4**（Wave 4 出口盘点）结论为 **PASS** 或书面豁免后，方可开工本票 runtime；否则标阻塞、不得 merge prod CI 变更。  
9. **Governance-guard / Reviewer**：CI / config diff 须经 **governance-guard** `allow` 且 **Reviewer** `approve`（W4-X §1.4.1 清单全绿）后方可 merge；`stop_work` / `block` 时不得推进。  
10. **无 flag / 无回滚 plan 禁止全量**：禁止在无 **feature flag**（或等价 prod 开关）与 **documented 回滚 plan** 情况下直接全量 rollout 或 skip canary；override 不得绕过 audit。  
11. **不改 merge adapter**：prod 路由逻辑变更须另开 adapter 票，**不**混入本票。  
12. **首条流唯一**：本票完成前，**不得** 并行修改第二条 prod release workflow（第二条 → W5-A-RUNTIME-02）。

## done_definition

> 仅针对 **W5-A-RUNTIME-01**（首条 prod CI）；父票整票 DoD 见 `W5-A-K2-ROLLOUT-EXPANSION.memory.md`。

### 本子票完成判定（全部满足或合规阻塞说明）

- [ ] **Planning 填空**：`target_workflow_path` / `target_job` / `target_steps` / `prod_stream_id` / `feature_flag_keys` 已写入本 Memory 或链接的 Planning 续卡，且与 `write_set` 一致。  
- [ ] **CHK-W4**：已完成或豁免留痕（引用 `90_run_queue.md` / CHK 记录）。  
- [ ] **至少一次成功 CI run**：  
  - 提供 **workflow run id**（或等价 URL/编号），对应票面锁定的 **唯一** release workflow。  
  - Run 日志可索引 **shadow**、**canary**、**promote**（或经批准的 **full rollout**）阶段。  
- [ ] **Gate 决策依据**：  
  - Canary / promote 前引用了 **W4-B** index gate 输出（非 `missing` 硬阻断场景有 documented 处理）。  
  - 引用了 **W4-C** gov metrics（JSONL 行或 `gov-gate-metrics.yml` job 产物）；checklist 或 PR 评论可追溯到具体文件/行。  
- [ ] **Rollback 证据**：至少一次 **rollback drill**（经批准）或 **真实 rollback** 案例——cohort 归零 / ask-only 恢复 + `rollback_record` 或 `rollout_trace` 等价审计行。  
- [ ] **Pause / override**：prod CI 路径上保留触发点；若使用 override，须有 allowlist + `reason` 记录。  
- [ ] **可重跑验证**：附可重跑命令或 `workflow_dispatch` 说明；关键输出含 `VERDICT=` / `ok` 语义（不贴金鑰）。  
- [ ] **Review**：**W5-A-REVIEW-01** 产出 `approve`（非本票 Executor 自签）。  
- [ ] **Doc-sync**：**W5-A-DOCSYNC-01** 已回写 `00`/`90`/`99`，区分 W4-A minimal v1 与本首条 prod CI，**未**夸大进度。

### 本 planning 产出切片（当前任务）

- [x] 本文 Ticket Memory 落盘，字段齐全  
- [x] 未修改 CI / runtime / tools / `rollout_pipeline_config.json` / W4-A `run_records`

## pending_followups

| 票号 | lane（预期） | 说明 |
|------|----------------|------|
| **W5-A-RUNTIME-02** | `runtime` | 第二条 prod release workflow / 第二 repo·服务；须单独 `write_set`，不得与本票并行改档 |
| **W5-A-REVIEW-01** | `review` | 首条 prod CI diff 的 Reviewer / governance-guard 清单与 `approve`/`request_changes` 结论 |
| **W5-A-DOCSYNC-01** | `doc-sync` | 回写 `00` §15.7、`90` 本票 Status、`99` 战报；与 W4-A DONE 口径对齐 |
| **W5-A-K2-ROLLOUT-EXPANSION**（父票） | planning / 后续切片 | 多 cohort 全阶梯、额外 repo、Dashboard 等见父票 `pending_followups` |
| **CHK-W4** | — | 开工前置；非本票实施范围，但为硬依赖 |

---

## 附录 A — 与父票 / W4-A 分界

| 维度 | W4-A（DONE · minimal v1） | 本票 W5-A-RUNTIME-01 |
|------|---------------------------|----------------------|
| 流 ID | `W4-A-PILOT-RELEASE-STREAM-v0.1` | 新 prod 流（Planning 填，建议 `W5-A-PROD-RELEASE-STREAM-v0.1`） |
| CI | **不改** prod workflow | **改一条** 明示 release workflow |
| 环境 | 案卷 / staging-internal 逻辑 | Prod / prod-equivalent CI |
| 证据 | 本地 `run_records` | **CI run id** + 新 run_records |
| 范围 | 主 case | 首条 prod 流 only |

---

## 附录 B — 本 planning 产出切片自检

| 检查 | 结果 |
|------|------|
| 未改 `.github/workflows/*`、`tools/*`、`rollout_pipeline_config.json`、W4-A 历史 `run_records` | pass（仅本文） |
| 明确引用 W5-A 父票 frozen_constraints（§frozen_constraints 继承 + 追加） | pass |
| `write_set` 锁定单 workflow、Planning 必填占位 | pass |
| CHK-W4 / governance-guard / 无 flag 全量禁止 | pass（frozen_constraints §8–10） |
| `pending_followups` 含 RUNTIME-02 / REVIEW-01 / DOCSYNC-01 | pass |
