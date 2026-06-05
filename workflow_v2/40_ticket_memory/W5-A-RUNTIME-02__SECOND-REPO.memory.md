# Ticket Memory — W5-A-RUNTIME-02

> **用途**：W5-A-K2-ROLLOUT-EXPANSION 第二条 **repo / 服务** runtime 子票；在与首条 prod CI（`W5-A-RUNTIME-01`）**不同**的目标上复用 / 调整 W5-A rollout 契约，完成一次可审计的 shadow → canary → promote rollout，并产出 rollback 证据。  
> **父票**：`workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`  
> **前置子票**：`workflow_v2/40_ticket_memory/W5-A-RUNTIME-01__FIRST-PROD-CI.memory.md`（**硬依赖**：首条 prod CI 验收通过后方可开工）  
> **控制面**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`（`lane=runtime` · Reviewer §1.4.1 · 须 governance-guard approve 后 merge）  
> **模板**：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`  
> **本文件产出切片**：planning（仅 Ticket Memory；**无** CI / runtime / tools 变更）

---

## ticket

- id: **W5-A-RUNTIME-02**
- title: **K-2 rollout 扩面：第二个 repo / 服务 · runtime-only**

## lane

- lane: **runtime**

## priority

- priority: **P1**（重要但低于首条 prod CI 的 `P0`；须在 `W5-A-RUNTIME-01` 与 **CHK-W4** 满足后方可开工）

## mode

- mode: **runtime-only**（Executor 在 `write_set` 内做第二条目标 workflow / rollout 配置增量；**不**在本 lane 改写 `00`/`90`/`99` 全局语义——属 **W5-A-DOCSYNC-02**）

## goal

在 **W5-A-K2-ROLLOUT-EXPANSION** 与 **W5-A-RUNTIME-01** 首条 prod CI 基线上，选定 **一个与首条目标不同** 的 repo / 服务（第二条 prod 或 prod-equivalent release 流水线），规划并实施 K-2 rollout 扩面，且满足：

1. **目标互斥**：第二条目标的 release workflow、服务名、`stream_id`、feature flag 命名空间 **均不得** 与 `W5-A-RUNTIME-01` Planning 续卡锁定的首条目标相同；若首条为 `service-X`，本票占位为 `service-Y`（Planning 续卡填实具体名）。
2. **契约复用 / 调整**：复用首条 prod CI 已验证的 rollout 阶段模型（shadow → canary → promote）、gate 引用方式（W4-B index + W4-C gov metrics）、pause/override/rollback 审计语义；允许针对第二条目标的 **traffic routing**、cohort 阶梯、环境变量或 flag 键做 **最小差异** 调整，调整须在 runbook 片段中 documented，**不得** silent 降低 gate 门槛。
3. **渐进交付**：延续父票 frozen_constraints——**禁止**一次性全量 K-2 主答案；须完成至少一次 **成功 rollout**（shadow → canary → promote 可索引）与至少一次 **rollback 演练或真实 rollback** 案例。
4. **指标 / gate 对齐**：第二条目标的 canary / promote 决策点须与首条 prod CI **同等级** 的 gate 行为（同一 playbook 阈值语义、同一 `gov-metrics-0.1` / index gate 引用模式）；偏差须书面说明并 Reviewer 批准。
5. **范围隔离**：改动 **仅** 落在票面 `write_set` 锁定的第二条 workflow 与对应 rollout config / runbook 片段；**不得** retro 改写 `W5-A-RUNTIME-01` 已 merge 部分、W4-A 试点流或历史 `run_records`。
6. **可审计**：产出第二条目标的 **CI workflow run id**（或等价）、`rollout_trace` / `rollback_record`（或等价）及与首条对齐的 checklist 勾选证据。

**开工前阻塞项（Planning 须先填）**：

- `read_set` / `write_set` 中 **「第二条 prod CI 目标 workflow」** 占位须替换为 **具体 repo 相对路径 + job 名 + step 锚点**，且须书面确认 **≠** `W5-A-RUNTIME-01` 的 `target_workflow_path`。
- **Depends on**：`W5-A-RUNTIME-01` 本子票 `done_definition` 全部勾选（或合规阻塞已关闭）+ **CHK-W4** PASS 或豁免留痕。

未满足前 **不得** 开工 runtime。

## read_set

> 未列出默认不读。暗部脚本 / venv / `.env` / 未授权 checkpoint **禁止**。

### 父票、首条 prod CI 与制度（必读）

| 路径 | 用途 |
|------|------|
| `workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md` | 父票 goal / frozen_constraints / 整票 DoD |
| `workflow_v2/40_ticket_memory/W5-A-RUNTIME-01__FIRST-PROD-CI.memory.md` | 首条 prod CI 契约、Planning 填空、`prod_stream_id`、gate 对齐范式（**只读**；本票不得改其已交付 workflow） |
| `workflow_v2/30_control_plane/W4-X_control_plane_mvp.md` | Lane 边界、Reviewer §1.4.1、governance-guard |
| `docs/k2_deployment_governance.md` | K-2 prod 流量切换角色矩阵与 Phase 门控（只读） |
| `docs/k2_merge_strategy.md` | 合流语义（只读；**不**改 merge adapter） |
| `AGENTS.md`、`04_Workflows/HARNESS_CONSTITUTION.md` | 工程红线与憲法 §7 禁区类型 |

### W4-A 试点流基线（只读 · 不 retro）

| 路径 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` | Shadow / canary / rollback / override 权威 |
| `workflow_v2/20_pilot/W3-A_case/W4-A_rollout_runbook.md` | 案卷侧索引 |
| `workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json` | 试点流 + 首条 prod 流（RUNTIME-01 新增段）只读 |
| `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` | Gate 勾选范式 |
| `workflow_v2/tools/wf_k2_rollout_run.ps1` | Helper 参考 |
| `workflow_v2/tools/wf_k2_rollout_canary_sim.py` | Cohort 逻辑参考 |
| `workflow_v2/20_pilot/W3-A_case/run_records/**` | W4-A 与 RUNTIME-01 历史证据（**禁止**篡改） |

### W4-B / W4-C gate（与首条对齐）

| 路径 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md` | Index / `IMP-AI-READY` gate |
| `workflow_v2/tools/wf_kb_index_gate.ps1` | Index allow/deny |
| `workflow_v2/20_pilot/W3-C/ci_gate_wire.md` | PR / nightly / manual 接线 |
| `workflow_v2/20_pilot/W3-C_metrics_schema.md` | `gov-metrics-0.1` schema |
| `workflow_v2/observability/gov_gate_metrics/*.jsonl` | 治理指标 |
| `workflow_v2/tools/wf_emit_gov_gate_metrics.ps1` | CI emitter |
| `.github/workflows/gov-gate-metrics.yml` | Gov 指标 CI |
| `.github/workflows/eval-gate-ci.yml` | Shadow nightly 语义（**不改**除非另票） |

### 首条 prod CI 已交付产物（只读 · 对齐用）

| 占位 | 说明 |
|------|------|
| `<RUNTIME-01_TARGET_WORKFLOW>` | 由 `W5-A-RUNTIME-01` Planning 续卡填入的首条 workflow 路径（本票 **禁止** 写入 `write_set`） |
| `<RUNTIME-01_PROD_STREAM_ID>` | 首条 prod 流 ID（例 `W5-A-PROD-RELEASE-STREAM-v0.1`） |
| `workflow_v2/20_pilot/W3-A/W5-A_first_prod_ci_runbook.md`（若 RUNTIME-01 已建） | 首条 SOP；本票可 fork 片段，不得覆盖首条正文 |

### 第二条目标 repo / 服务（占位 · Planning 开工前必填）

| 占位 | 说明 |
|------|------|
| `.github/workflows/service-Y-release.yml` | **第二条 prod CI 目标 workflow**（占位；替换为具体文件名；**须 ≠** RUNTIME-01 的 `target_workflow_path`） |
| `<TARGET_REPO_ROOT>` | 目标 repo 根（若第二条为 monorepo 外独立 repo，填相对路径或逻辑名） |
| `<TARGET_JOB_NAME>` | 嵌入 rollout 的 job 名（占位） |
| `<TARGET_STEP_ANCHOR>` | shadow / canary / promote 步骤锚点（占位） |
| `docs/<SERVICE-Y>-traffic-routing.md`（或等价） | **Traffic routing / cohort 配置** 文档占位（只读至 Planning 创建；Executor 可增补丁段） |
| `docs/<SERVICE-Y>-k2-rollout-config.md`（或等价） | 第二条服务 rollout 参数、flag 键、环境分层说明（占位） |

### 控制面挂点（Executor 只读；doc-sync 另票写）

| 路径 | 用途 |
|------|------|
| `workflow_v2/90_run_queue.md` | 本票 Status/Notes；核对 RUNTIME-01 = DONE |
| `workflow_v2/99_latest_status.md` | 阶段摘要对账 |
| `workflow_v2/00_master_plan.md`（§15.7） | W5-A 多 repo 挂点 |

## write_set

> **IMPORTANT**：下列为 **文字锁定范围**；具体文件名须在 **Planning lane 续卡** 中显式填入，且 **书面确认与 RUNTIME-01 目标互斥** 后，Executor 方可动档。

### 允许（runtime 切片 · 开工前须 Planning 填实）

1. **第二条 release workflow 文件（唯一）**  
   - 仅允许修改 **一条**、票面明示命名、且 **≠** `W5-A-RUNTIME-01` `target_workflow_path` 的 prod（或 prod-equivalent）release workflow（占位：`.github/workflows/service-Y-release.yml`）。  
   - 改动 **仅限** Planning 指定的 **job / step**（`<TARGET_JOB_NAME>` · `<TARGET_STEP_ANCHOR>`）内插入或调整 K-2 rollout 步骤（shadow、canary、promote、rollback hook、pause/override）。  
   - **禁止** 修改首条 workflow（RUNTIME-01 已交付路径）、**禁止** blanket 修改全部 `.github/workflows/*`、**禁止** 影响其他未列名服务。

2. **第二条 rollout 配置 / runbook 片段**  
   - 允许新增第二条 prod 流配置，例如新 `stream_id` **`W5-A-PROD-RELEASE-STREAM-v0.2-<SERVICE-Y>`**（或 Planning 指定名），存放于 `rollout_pipeline_config.json` 的并行段、或 `workflow_v2/20_pilot/W3-A/rollout_streams/<service-y>.json`。  
   - 允许新增或增补：`workflow_v2/20_pilot/W3-A/W5-A_second_repo_rollout_runbook.md`（或 `docs/<SERVICE-Y>-k2-rollout-config.md` 中 **仅** 第二条服务章节）。  
   - **禁止** 删除 / retro 改写 `W4-A-PILOT-RELEASE-STREAM-v0.1`、RUNTIME-01 已锁定的 prod 流定义与历史 `run_records/**`。

3. **Helpers（薄封装 · 可选 · 须向后兼容 RUNTIME-01）**  
   - `workflow_v2/tools/wf_k2_rollout_*` 扩展：须支持 `--stream-id` / `--target-service` 或等价参数化，**不得** 破坏首条 prod CI 已验收调用路径；结构化 `dict` 输出。  
   - **禁止** 改 `merge_ask_and_k2` / K-2 adapter。

4. **本票 run 证据（新增 · 不篡改历史）**  
   - `workflow_v2/20_pilot/W3-A_case/run_records/**` 下 **新** run id 目录（第二条服务专用前缀，例 `W5-A-R02-*`）。  
   - Traffic routing 文档：仅允许在 `docs/<SERVICE-Y>-traffic-routing.md`（或 Planning 锁定路径）增补与本服务相关的 cohort / 路由表。

### 禁止（除非尚書省 override + Progress/notes 末尾留痕）

- 暗部脚本 / venv 树 / `.env` / runtime checkpoints  
- `W5-A-RUNTIME-01` 已 merge 的 workflow、config、runbook 正文（**retro 禁止**）  
- W4-A 试点流定义与 W4-A / RUNTIME-01 历史 `run_records`  
- 未列名修改其他 `.github/workflows/*`（含 `eval-gate-ci.yml` / `gov-gate-metrics.yml` 语义变更，除非另票）  
- `00_master_plan.md` / `90_run_queue.md` / `99_latest_status.md` 全局语义（→ **W5-A-DOCSYNC-02**）  
- `merge_ask_and_k2`、adapter 实现、G7/G8 正文语义  
- 本 **planning 产出切片** 内写入任何 CI / tools / config（仅本文）

### Planning 续卡必填项（开工 gate）

| 字段 | 填法 |
|------|------|
| `target_workflow_path` | 例：`.github/workflows/service-Y-release.yml`；**须书面 ≠** RUNTIME-01 `target_workflow_path` |
| `target_job` | 例：`release` |
| `target_steps` | shadow / canary / promote / rollback 步骤名或 YAML 锚点列表 |
| `prod_stream_id` | 例：`W5-A-PROD-RELEASE-STREAM-v0.2-service-Y`；**须 ≠** RUNTIME-01 `prod_stream_id` |
| `feature_flag_keys` | 第二条服务专用 flag；不得与首条冲突 |
| `traffic_routing_doc` | 例：`docs/service-Y-traffic-routing.md` |
| `diff_from_runtime_01` | 与首条契约的差异表（cohort、环境、阈值是否相同及理由） |
| `runtime_01_done_ref` | RUNTIME-01 验收证据链接（workflow run id / PR / `90_run_queue` 行） |

## frozen_constraints

> 复用 **W5-A-K2-ROLLOUT-EXPANSION** §frozen_constraints（1–7）；下列为 **本子票追加**。

### 自 W5-A 父票继承（摘要 · 细则见父票）

1. **渐进交付**：禁止一次性全量 K-2 主答案；shadow → 有限 cohort canary → 扩面 → 全量。  
2. **每阶段保护**：可观测指标、自动/人工停止条件、rollback/fallback、pause/override（allowlist + `reason`）。  
3. **治理对齐**：G7/G8、`W4-B` index gate、`W4-C` gov metrics；遵从 `docs/k2_deployment_governance.md`；worker 不得自订 rollout 阈值覆盖 playbook。  
4. **扩面授权**：本票 **仅第二条** 目标；第三 repo/服务 → 后续子票（见 `pending_followups`）。  
5. **W4-A 边界**：不 retro W4-A DONE；试点流与历史 run **只读**。  
6. **控制面**：不实现 W4-X §0 Out of Scope。  
7. **憲法 §7 禁区**：暗部、venv、金鑰原文等见 `AGENTS.md`。

### 自 W5-A-RUNTIME-01 继承（本子票特有）

8. **CHK-W4 依赖**：**CHK-W4** PASS 或书面豁免（与 RUNTIME-01 相同硬门槛）。  
9. **RUNTIME-01 硬依赖**：**仅当** `W5-A-RUNTIME-01` 本子票 `done_definition` 全部满足（含 Review `approve`、Doc-sync 完成、至少一次成功 prod CI rollout + rollback 证据）后，方可开工本票 runtime；否则标阻塞。  
10. **首条不可改**：本票实施期间 **禁止** 修改 RUNTIME-01 已交付的 workflow / stream / runbook；若发现首条缺陷，开 **RUNTIME-01 补丁票**，不得在本票 `write_set` 内顺手修复。  
11. **目标互斥**：第二条 `target_workflow_path`、`prod_stream_id`、`feature_flag_keys` 命名空间须与 RUNTIME-01 Planning 填空 **无交集**；Reviewer 须核对 `diff_from_runtime_01`。  
12. **Gate 行为对齐**：第二条 canary/promote 的 gate 引用模式须与首条 **同级**；降低门槛须尚書省 override + 留痕。  
13. **Governance-guard / Reviewer**：diff 须经 **governance-guard** `allow` 且 **Reviewer** `approve` 后方可 merge。  
14. **无 flag / 无回滚 plan 禁止全量**：与 RUNTIME-01 同。  
15. **不改 merge adapter**：与 RUNTIME-01 同。

## done_definition

> 仅针对 **W5-A-RUNTIME-02**（第二条 repo / 服务）；父票整票 DoD 见 `W5-A-K2-ROLLOUT-EXPANSION.memory.md`。

### 本子票完成判定（全部满足或合规阻塞说明）

- [ ] **前置依赖**：**CHK-W4** PASS 或豁免留痕；**W5-A-RUNTIME-01** DONE（引用 `runtime_01_done_ref`）。  
- [ ] **Planning 填空**：`target_workflow_path` / `target_job` / `target_steps` / `prod_stream_id` / `feature_flag_keys` / `traffic_routing_doc` / `diff_from_runtime_01` 已写入本 Memory 或 Planning 续卡，且 **确认 ≠** RUNTIME-01 目标。  
- [ ] **至少一次成功 rollout（第二条目标）**：  
  - 提供第二条目标的 **workflow run id**（或等价 URL/编号）。  
  - Run 日志可索引 **shadow**、**canary**、**promote** 阶段。  
- [ ] **至少一次 rollback**：rollback drill（经批准）或真实 rollback——cohort 归零 / ask-only 恢复 + `rollback_record` 或 `rollout_trace` 审计行（第二条 run id 可区分）。  
- [ ] **Gate 对齐证据**：  
  - 与 RUNTIME-01 **同等级** 的 W4-B index gate + W4-C gov metrics 引用；`diff_from_runtime_01` 中若有差异，Reviewer 已 `approve` 理由。  
- [ ] **Pause / override**：第二条 prod CI 路径保留触发点；override 有 allowlist + `reason`。  
- [ ] **可重跑验证**：附可重跑命令或 `workflow_dispatch` 说明；关键输出含 `VERDICT=` / `ok` 语义。  
- [ ] **Review**：**W5-A-REVIEW-02** 产出 `approve`。  
- [ ] **Doc-sync**：**W5-A-DOCSYNC-02** 已回写 `00`/`90`/`99`，标明「第二条 repo / 服务」与首条 prod CI 并列，**未**夸大进度。

### 本 planning 产出切片（当前任务）

- [x] 本文 Ticket Memory 落盘，字段齐全  
- [x] 未修改 CI / runtime / tools / `rollout_pipeline_config.json` / 任何 `run_records`

## pending_followups

| 票号 | lane（预期） | 说明 |
|------|----------------|------|
| **W5-A-RUNTIME-03+** | `runtime` | 第三及更多 repo / 服务扩面；每目标单独 `write_set` 子票 |
| **W5-A-ROLLout-CONFIG-ABSTRACT** | `planning` → `runtime` | 统一 `rollout_streams/*.json` 或 schema 抽象，减少每 repo 重复 YAML（**不**默认在本票实施） |
| **W5-A-REVIEW-02** | `review` | 第二条目标 diff 的 Reviewer / governance-guard 结论 |
| **W5-A-DOCSYNC-02** | `doc-sync` | 回写 `00` §15.7 多 repo 挂点、`90` 本票 Status、`99` 第二条 rollout 战报 |
| **W5-A-K2-ROLLOUT-EXPANSION**（父票） | planning / 后续 | 多 cohort 全阶梯、Dashboard、Control Plane 集成等见父票 `pending_followups` |
| **W5-A-2 · Dashboard / Alert** | 占位 | 父票 pending；第二条服务 observability 面板可挂此票 |
| **CHK-W4** | — | 与 RUNTIME-01 相同开工前置（本票再次核对，不重复实施） |

---

## 附录 A — 与 RUNTIME-01 / W4-A 分界

| 维度 | W4-A（试点 minimal v1） | W5-A-RUNTIME-01（首条 prod CI） | 本票 W5-A-RUNTIME-02 |
|------|-------------------------|--------------------------------|----------------------|
| 流 ID | `W4-A-PILOT-RELEASE-STREAM-v0.1` | `W5-A-PROD-RELEASE-STREAM-v0.1`（建议） | 新 `stream_id`（如 `…-v0.2-service-Y`） |
| 目标 workflow | **不改** prod | `service-X-release.yml`（Planning 填） | `service-Y-release.yml`（**≠** 首条） |
| 依赖 | — | CHK-W4 | CHK-W4 + **RUNTIME-01 DONE** |
| 优先级 | — | P0 | **P1** |
| 证据 | 本地 `run_records` | 首条 CI run id | 第二条 CI run id + rollback |
| retro | 禁止改 W4-A | 本票 **禁止** 改 RUNTIME-01 已交付部分 |

---

## 附录 B — 本 planning 产出切片自检

| 检查 | 结果 |
|------|------|
| 未改 `.github/workflows/*`、`tools/*`、`rollout_pipeline_config.json`、任何 `run_records` | pass（仅本文） |
| 明确依赖 **W5-A-RUNTIME-01**、**CHK-W4**（frozen_constraints §8–9） | pass |
| 第二条目标与首条 **互斥**（goal §1、Planning 表 `target_workflow_path`） | pass |
| 继承 W5-A 父票 progressive delivery / gate / 授权 / 禁区 | pass（§frozen_constraints） |
| `write_set` 仅第二条 workflow + 对应 config/runbook；禁止 retro RUNTIME-01 | pass |
| `pending_followups` 含更多 repo 子票与 config 抽象化占位 | pass |
| 未宣称 W5-A-RUNTIME-02 已实施 | pass |

**规划切片签收**：Ticket Memory 落盘即视为本 **planning** 切片可交付；runtime 切片须待 RUNTIME-01 验收后另派工。
