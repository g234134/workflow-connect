# Ticket Memory — W5-A-K2-ROLLOUT-EXPANSION

> **用途**：在 W4-A「固定试点流 · minimal v1」完工基础上，规划 Wave 5 大票执行面；承接 prod rollout / CI 集成 / 多 cohort / 多 repo 扩面，**不**污染 W4-A 边界与 DONE 口径。  
> **本票当前切片**：`lane=planning` · `mode=planning`（仅 Ticket Memory + 控制面草案挂点；**无** runtime / CI / tools 变更）。  
> **控制面**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`  
> **模板**：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`

---

## ticket

- id: **W5-A-K2-ROLLOUT-EXPANSION**
- title: **K-2 rollout 扩展：prod / CI / multi-cohort / multi-repo**

## lane

- lane: **planning**

## priority

- priority: **P1**（未来主线增强；**不**阻塞 Wave 4 收口与 CHK-W4；须在 W4-A/B/C minimal v1 与 W4-X 控制面挂点稳定后再开 runtime 切片）

## mode

- mode: **planning**（本 Context Card 仅服务规划与 Ticket Memory；后续 runtime 切片另开 `mode=runtime-only` 子票或续卡）

## goal

将当前仅在单一试点流 **`W4-A-PILOT-RELEASE-STREAM-v0.1`** 上运行的 K-2×ask rollout（本地 helper + 案卷模拟，**不**改 prod CI）规划并升格为可在真实生产环境重复运作的 rollout 体系，具体包括：

1. **Prod / CI 集成**：至少一条真实 prod（或 prod-equivalent）CI / release 流水线嵌入 K-2 rollout 阶段（shadow → canary → 扩面 → 全量），与现有 eval / gov 观测链对齐，而非仅本地 `wf_k2_rollout_run.ps1` 触发。
2. **多 cohort 渐进交付**：支持分阶段流量策略（例如 Internal staff → 1% → 5% → 20% → 100%，或等价阶梯）；每阶具备进入/停留/退出条件与审计记录。
3. **多 repo / 多服务扩面**：在**明示授权**的前提下，将同一套 rollout 契约复制到额外 repo 或服务，每目标一次成功 rollout + 可索引 run 记录。
4. **保护机制**：每一阶段均具备可观测指标、自动/人工停止条件、rollback / fallback、pause 与 override（延续 W4-A allowlist + reason 语义，prod 级 SOP 化）。

**与 W4-A 分界**：W4-A 交付的是「主 case 上可重复 shadow + internal canary（5% 模拟）+ 最小 rollback/override」；**不等于**远端 prod 自动 rollout、多管道或多 cohort 策略。W5-A **承接** W4-A 产物为基线，**不 retro** 改写 W4-A DONE 口径或 `rollout_pipeline_config.json` v0.1 试点流定义。

## read_set

> 未来执行 W5-A（runtime / doc-sync 切片）时允许读取；未列出默认不读。暗部脚本 / 私密配置 **禁止**。

### W4-A 基线（试点流 · 必读）

| 路径 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` | 权威 runbook（shadow / canary / rollback / override 端到端） |
| `workflow_v2/20_pilot/W3-A_case/W4-A_rollout_runbook.md` | 案卷侧索引 |
| `workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json` | 试点流配置（`W4-A-PILOT-RELEASE-STREAM-v0.1`） |
| `workflow_v2/20_pilot/W3-A_case/W4-A_release_stream.json` | 流指针 → canonical config |
| `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` | Shadow / Canary / Rollback gate |
| `workflow_v2/tools/wf_k2_rollout_run.ps1` | 当前本地执行入口（扩面时参考，非最终 prod 唯一入口） |
| `workflow_v2/tools/wf_k2_rollout_canary_sim.py` | Cohort 模拟逻辑参考 |
| `workflow_v2/20_pilot/W3-A_case/run_records/**` | 既有 shadow+canary 证据（只读；例 `rollout_trace.jsonl`、`shadow_state.json`） |
| `workflow_v2/20_pilot/W3-A_case/07_art_rel_dec.json`、`08_art_rel_exec.json`（若存在） | ART-REL 风格发布记录样例 |
| `workflow_v2/30_rollout/**` | Phase 地图与 rollout 制度邻接 |
| 战车根 `docs/k2_deployment_governance.md`、`docs/k2_merge_strategy.md` | K-2 prod 流量切换治理（只读） |

### CI / Release（占位 · 扩面时对齐）

| 占位 | 说明 |
|------|------|
| `.github/workflows/eval-gate-ci.yml` | W4-A 锚定的 shadow nightly 语义（`eval-shadow-nightly`）；W5 集成时 **须** 评估是否新增 job 而非 silent 改 prod release |
| `.github/workflows/<SERVICE>-release.yml` | **占位**：目标服务的 prod / staging release workflow（票内指定具体文件名后再读） |
| `.github/workflows/gov-gate-metrics.yml` | W4-C 已落地的 gov 指标 CI |
| `workflow_v2/20_pilot/W2-1_case/07–08_art_rel_*.json` | ART-REL 范式锚点 |

### W4-B / W4-C 决策指标（rollout gate 依赖）

| 路径 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md` | Index / `IMP-AI-READY` gate；canary 前宜 `kb_index_*` 非 `missing` |
| `workflow_v2/tools/wf_kb_index_gate.ps1` | Index allow/deny 行为参考 |
| `workflow_v2/20_pilot/W3-C/ci_gate_wire.md` | PR / nightly / manual 接线 |
| `workflow_v2/20_pilot/W3-C_metrics_schema.md` | `gov-metrics-0.1` schema |
| `workflow_v2/observability/gov_gate_metrics/*.jsonl` | 治理指标时间序列 |
| `workflow_v2/tools/wf_emit_gov_gate_metrics.ps1` | CI → JSONL emitter |

### 控制面与规划挂点

| 路径 | 用途 |
|------|------|
| `workflow_v2/00_master_plan.md`（§15、§15.7） | Wave 4/5 分界 |
| `workflow_v2/90_run_queue.md` | 票状态 |
| `workflow_v2/99_latest_status.md` | 阶段摘要 |
| `workflow_v2/30_control_plane/W4-X_control_plane_mvp.md` | Lane / Reviewer 边界 |
| `AGENTS.md`、`04_Workflows/HARNESS_CONSTITUTION.md`（禁区类型） | 工程红线与 §7 禁区 |
| `04_Workflows/ENGINEERING_CONTRACT.md` | 四流派 / 12-rule |

## write_set

> 未来 W5-A **runtime** 切片允许触及的范围（文字描述；具体路径在开工前由 Planning lane 续卡锁定）。**本 planning 切片**仅允许写：`40_ticket_memory/`、以及 `00`/`90`/`99` 的**草案级**挂点。

### 未来 runtime 切片（预期）

- **CI workflows**：针对**票内明示**的单一或少数服务 / repo 的 rollout job（shadow / canary / promote）；禁止未列名 blanket 修改所有 `.github/workflows/*`。
- **Rollout 配置**：`rollout_pipeline_config.json` 的 v0.2+ 或并行 `rollout_streams/*.json`（多 cohort、多 `pilot_stream_id` / `prod_stream_id`）；**不**删除或 retro 改写 v0.1 试点流定义。
- **Runbook / SOP**：prod 级 `W5-A_rollout_runbook.md`（或升格 W4-A runbook 的 v0.2 节）、prod gate checklist、cohort 策略表。
- **Helpers**：`workflow_v2/tools/wf_k2_rollout_*` 扩展或新增薄封装（调用链可观测、结构化 `dict` 输出）；**不**改 `merge_ask_and_k2` / adapter 实现（除非另开 adapter 票）。
- **观测**：rollout 专用 metrics JSONL / dashboard 配置占位、`run_records/**` 新 run id（**不**篡改 W4-A 历史 run）。
- **文档**：`00` §15.7、`90` W5-A 行 Status、`99` 战报（doc-sync lane）。

### 本 planning 切片（当前）

- `workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`（本文）
- `workflow_v2/00_master_plan.md`（仅 §15.7 草案挂点）
- `workflow_v2/90_run_queue.md`（W5-A 行 · Status=`FUTURE`/`IDEA`）
- `workflow_v2/99_latest_status.md`（可选 · 「Wave 5 展望」草案段）

### 明确禁止（任何切片，除非尚書省 override + 留痕）

- 暗部脚本 / venv 树 / `.env` / runtime checkpoints
- 未授权修改 **全部** prod release workflows
- 本 planning 切片内写入 `tools/*`、`.github/workflows/*`、`rollout_pipeline_config.json`、`run_records/**`

## frozen_constraints

1. **渐进交付（Progressive delivery）**  
   - **禁止**一次性将全量用户流量切到 K-2 主答案；必须分阶段 rollout（shadow → 有限 cohort canary → 逐步扩面 → 全量）。  
   - 每阶段须有 documented 进入条件与最短观察窗口（参考 W4-A shadow `min_window_days` 语义，prod 由 W5 runbook 具体化）。

2. **每阶段最低保护**  
   - **可观测**：错误率、延迟、p95/p99、shadow 对照差异、关键业务 KPI（票内清单化）；对接 W4-C `gov-metrics-0.1` 与 eval shadow 链。  
   - **停止条件**：自动阈值（例：错误率 > X%、`eval_ci_check` fail、`infra_risk` tag）与人工 on-call 叫停；须写入 gate checklist。  
   - **Rollback / fallback**：每阶段可一键回退至 ask-only 或上一 cohort 比例；须产生 `rollback_record` / trace 行（延续 W4-A 案卷模式）。  
   - **Pause / override**：仅 allowlist 角色 + 必填 `reason`；override 不得绕过 audit。

3. **治理对齐（不得偷跑 release）**  
   - 必须与 **G7/G8** 治理文档、`W4-B` index gate（`IMP-AI-READY` 前 `missing` 硬阻断）、`W4-C` gov gate 指标对齐；扩面决策须可引用 JSONL / gate 输出。  
   - **禁止**绕过既有 gate 体系「偷偷 release」；fail-on-deny 全 PR 默认仍属 Wave 5+ 治理议题，须尚書省分阶段批文。  
   - 遵从 `docs/k2_deployment_governance.md` 角色矩阵与 Phase 门控；worker 不得自订 rollout 阈值覆盖 playbook。

4. **扩面授权**  
   - **禁止**在未经明示同意前将 rollout 自动扩展到**所有** repo / **所有**服务；每新增目标须单独列 `write_set` 子范围或子票。  
   - **禁止**修改 `merge_ask_and_k2` / K-2 adapter 实现作为本票默认范围（属独立票）。  
   - **禁止**宣称完成「远端 prod Phase 3+」除非 DoD 证据满足且 doc-sync 已回写。

5. **W4-A 边界保护**  
   - 不 retro 改写 W4-A **DONE（minimal v1）** 口径；不删除 `W4-A-PILOT-RELEASE-STREAM-v0.1` 配置与历史 `run_records`。  
   - W5 新流使用新 `stream_id`（建议 `W5-A-PROD-RELEASE-STREAM-v0.1` 或票内指定），与试点流并存。

6. **控制面与自动化**  
   - W5-A **不**默认实现 W4-X §0 Out of Scope：自动开 chat、自动并行调度、自动 merge、deny engine runtime、复杂 reviewer pipeline。  
   - Control Plane 深度集成（按 metrics 自动推进/停止）→ `pending_followups`。

7. **禁区（憲法 §7 类型）**  
   - 不触碰暗部脚本、venv 树、未授权 checkpoint、金鑰原文输出；双 Telegram 监听等见 `AGENTS.md` 红线。

## done_definition

> W5-A **整票**（含 planning + runtime + review + doc-sync）完成判定；当前 planning 切片**仅**完成「Ticket Memory + 草案挂点」子集。

### Planning 切片（当前票 · 已完成即勾选）

- [x] 本文 Ticket Memory 落盘，字段齐全（goal / read_set / write_set / frozen_constraints / done_definition / pending_followups）
- [x] `00_master_plan.md` §15.7 草案挂点（标明 **草案 / 未实施**）
- [x] `90_run_queue.md` W5-A 行 Status=`FUTURE` 或 `IDEA`
- [x] `99_latest_status.md`「Wave 5 展望」草案段

### Runtime 切片（未来 · 整票 DoD）

- [ ] **至少一条真实 prod CI 流程**已集成 K-2 rollout：  
  - 部署流水线含明确 **shadow / canary / promote（或 full）** 阶段；  
  - 每阶段有指标门槛与自动/人工决策点（文档 + 一次成功 run 链接或 workflow run id）。  
- [ ] **至少一套多 cohort 策略**在真实（或 prod-equivalent）环境执行完毕：  
  - 例：Internal → 1% → 5% → 20% → 100%（或等价）；  
  - 各阶段有 `rollout_trace` 或 CI 日志可索引。  
- [ ] **至少一次真实 rollback**（或经批准的模拟 drill）：cohort 归零 / ask-only 恢复 + `rollback_record` 或等价审计。  
- [ ] **至少一个额外 repo / 服务**按 W5 策略完成一次成功 rollout（非仅 `W3-A_case`）。  
- [ ] **Gate 对齐证据**：W4-B index gate 与 W4-C gov metrics 在 canary 决策点被引用（checklist 勾选或 JSONL 引用）。  
- [ ] **doc-sync**：`00` / `90` / `99` 已区分 W4-A（试点 minimal v1）与 W5-A（prod/CI/扩面），**未**夸大进度。  
- [ ] **Review lane**：`approve`（Reviewer §1.4.1 清单通过）。  
- [ ] **验证命令**：可重跑（例：workflow_dispatch、helper CLI、或 CI re-run）附关键 `VERDICT=` / `ok` 语义。

## pending_followups

| 候选票 / 主题 | 说明 |
|---------------|------|
| **W5-A-2 · Dashboard / Alert** | Rollout 专用 Grafana/告警、on-call 路由、SLO 面板（占位） |
| **W5-A-3 · Owner 交接** | Release 值班 runbook、override 审批链、尚書省 sign-off 模板 |
| **W5-B · Control Plane 集成** | 按 `gov-metrics` / eval 指标自动建议 pause/promote（**不**默认自动执行，除非另批文） |
| **W5-C · fail-on-deny 分阶段** | 与 W4-C 分立；须治理批文，非 W5-A 默认范围 |
| **K-2 Phase 3–4** | 根 plan §4.8 后续 Phase；可能与 W5-A 并行但单独票号 |
| **Adapter / merge 变更** | 若 prod 路由逻辑变更，单开 `merge_ask_and_k2` 票，不混入 W5-A |
| **CHK-W4** | Wave 4 出口盘点；W5-A runtime **依赖** W4-A/B/C minimal v1 与 CHK 结论 |

---

## 附录 A — W4-A vs W5-A 对照（规划用）

| 维度 | W4-A（DONE · minimal v1） | W5-A（规划 → 未来实装） |
|------|---------------------------|-------------------------|
| 流 ID | `W4-A-PILOT-RELEASE-STREAM-v0.1` | 新 prod 流（待命名，如 `W5-A-PROD-…`） |
| 环境 | `staging-internal` 逻辑名；案卷模拟 | Prod / prod-equivalent CI |
| Cohort | 固定 5% internal hash 模拟 | 多阶梯（1%→…→100%） |
| CI | **不改** prod workflow；本地 helper | **接入**至少一条真实 release CI |
| 范围 | 主 case `W3-A_case` | + 至少 1 repo/服务 |
| 证据 | `run_records/**` 本地 | CI run id + 远端可观测 |

---

## 附录 B — 本 planning 切片验证

| 检查 | 结果 |
|------|------|
| 未改 `tools/*`、`.github/workflows/*`、`rollout_pipeline_config.json`、`run_records/**` | 预期 pass（仅本文 + 00/90/99 草案） |
| 未宣称 W5-A 已实施 | 预期 pass |
| W4-A DONE 口径未 retro | 预期 pass |

**规划切片签收**：Ticket Memory 落盘即视为本 **planning** 切片可交付；runtime 切片另派工。
