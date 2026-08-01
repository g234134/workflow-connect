# Phase 3.5 Cost / Model / Risk Governance Contract v1

> **票號**：WA-T3 · `phase3-5-cost-and-model-governance-contract-v1`  
> **性质**：Gate 分类 **SSOT**（mandatory / optional / shadow-only）；**不**改 CI 门槛、**不**授权 prod canary。  
> **上位**：禁区与四域见 `04_Workflows/HARNESS_CONSTITUTION.md`；操作细节见各 runbook。  
> **完成度锚点**：Phase 3.5 **55% → 83%**（本票 codify 后）

---

## §1 范围与术语

### 1.1 本合同覆盖什么

| 在范围内 | 不在范围内 |
|----------|------------|
| PR / nightly / schedule 路径上 **现有** gate 的分类与主链影响 | 修改 `eval_ci_check` 门槛数值、`--max-needs-review-ratio` 默认、ENF blocking 旗标 |
| K-2 Phase 0–1 shadow 与 eval 对齐的 **文档索引** | 启用 K-2 Phase 2 canary 或 `GOV_ENF_BLOCKING_CANARY=1` |
| 成本／风险字段的 **已知 gap** 标注 | 统一 `daily_cost_summary` vs `task_runs` 双数据源（follow-up） |
| Wave B/C Agent 可假设的 PR 必过项、nightly shadow 项、logging-only 项 | 把 shadow nightly 升格为 PR blocking gate |

### 1.2 术语

| 术语 | 定义 |
|------|------|
| **mandatory** | PR 合并路径 **必须** 通过的 gate；失败 → workflow job fail → 阻塞合并（若 repo 设为 required check） |
| **optional** | 本地／发布 checklist **推荐**；**非** AC-3 所列 PR 硬门禁 trio；Wave B/C **不得** 假设其为 merge blocker |
| **shadow-only** | 仅 schedule／`workflow_dispatch` nightly 或内部 shadow 导出；`blocks_mainline=N`；**不**阻塞 MVP tabular 主链 |
| **blocks_mainline** | 该 gate 失败是否应阻断 Tabular MVP 主链（`run_mvp_mainline_regression.py`）或 outbox 写入：**Y**／**N**／**shadow** |
| **logging-only** | 步骤执行并产出 artifact／log，但 **不** 以 pass/fail 改变 job 结果（或 `continue-on-error: true`） |

### 1.3 权威位阶

```
尚書省批文 ＞ HARNESS_CONSTITUTION.md ＞ 本 contract ＞ 各 runbook 操作细节 ＞ brief/notes
```

本合同 **不** 取代 `docs/k2_deployment_governance.md` 的 Phase 进门批文；**不** 授权任何人自行开启 blocking canary。

---

## §2 Gate 分类总表

> **列定义**：`gate_id` · `class` · `workflow_or_runner` · `blocks_mainline` · `authority_doc`  
> **来源**：唯读对齐 `.github/workflows/eval-gate-ci.yml`、`.github/workflows/core-agent-smoke.yml`、`04_Workflows/_ops_cycle.py`（2026-06-10 快照）。

### 2.1 Mandatory（PR 必过）

| gate_id | class | workflow_or_runner | blocks_mainline | authority_doc |
|---------|-------|-------------------|-----------------|---------------|
| `MG-EVAL-UNIT` | mandatory | `.github/workflows/eval-gate-ci.yml` → job `eval-gate` → step `P+ eval unit tests`（含 `tests.test_eval_gate`） | Y | 本合同 §3 · `observability/eval_gate.py` |
| `MG-EVAL-CI-CHECK` | mandatory | `.github/workflows/eval-gate-ci.yml` → job `eval-gate` → `python -m observability.eval_ci_check`（PR 默认 `--max-needs-review-ratio 0.72`，`--fail-on-tags` 空） | Y | 本合同 §3 · `observability/eval_ci_check.py` |
| `MG-CORE-AGENT-SMOKE-PR` | mandatory | `.github/workflows/core-agent-smoke.yml` → job `agent-smoke-pr` → `python 04_Workflows/_core_agent_smoke.py --tier PR` | Y | `docs/testing.md` §5–§6 |
| `MG-OPS-EVAL-SUBSET` | mandatory | `python 04_Workflows/_ops_cycle.py checklist --mode full` → step `eval_gate_ci_subset`（fixture `tests/fixtures/eval/ibridge_records.jsonl`，ratio `0.9`） | Y | `docs/governance-constitution-v1.md` §3.4 · `docs/GOVERNANCE_ONBOARDING_v1.md` |

### 2.2 Shadow-only（nightly / 内部对比；不阻塞主链）

| gate_id | class | workflow_or_runner | blocks_mainline | authority_doc |
|---------|-------|-------------------|-----------------|---------------|
| `SG-EVAL-SHADOW-NIGHTLY` | shadow-only | `.github/workflows/eval-gate-ci.yml` → job `eval-shadow-nightly`（cron UTC 06:00；`continue-on-error: true` on eval step） | N | 本合同 §4 · `docs/k2_deployment_governance.md` §4.2 |
| `SG-ENF-PREVIEW` | shadow-only | `eval-shadow-nightly` → `Enforcement Preview (Phase A)`；env **`GOV_ENF_BLOCKING_CANARY=0`**（shadow-only）；wrapper **exit 0** | N | `docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md` · `observability/enf_config.py` |
| `SG-K2-SHADOW-EXPORT` | shadow-only | `eval-shadow-nightly` → `python -m observability.ibridge_exporter --source shadow --profile shadow` → `artifacts/eval/shadow_ibridge_records.latest.jsonl` | shadow | `docs/k2_merge_strategy.md` · `core/k2_ask_shadow.py` |
| `SG-SHADOW-EVAL-CHECK` | shadow-only | `eval-shadow-nightly` → `eval_ci_check`（nightly 默认 ratio **0.60** + `--fail-on-tags infra_risk`；`continue-on-error: true`） | N | 本合同 §4 · `.github/workflows/eval-gate-ci.yml` |

### 2.3 Optional（推荐；非 PR 硬门禁 trio）

| gate_id | class | workflow_or_runner | blocks_mainline | authority_doc |
|---------|-------|-------------------|-----------------|---------------|
| `OG-AGENT-LINES-CI` | optional | `python scripts/run_agent_lines_ci_suite.py`（`--scope tabular\|non_tabular\|all`） | N | `docs/agent-lines-ci-suite-v1.md` · `04_Workflows/tickets/W10-T1-integrate-agent-lines-into-ci-v1_state.md` |
| `OG-ROUTING-EVAL-DRYRUN` | optional | `python -m unittest tests.test_routing_eval_runner` + `python scripts/run_routing_eval.py --dry-run --format json`（亦出现在 `eval-gate` PR job；**分类为 optional**：发布 checklist 推荐，**非** AC-3 mandatory trio） | N | `docs/routing-eval-runner-v1.md` · `04_Workflows/tickets/W4-T4-routing-ci-hooks_state.md` |
| `OG-SHADOW-SPOOL-SMOKE` | optional | `.github/workflows/eval-gate-ci.yml` → job `shadow-spool-smoke`（`scripts/build_shadow_spool.sh` fixture smoke） | N | 本合同 §3 · `scripts/build_shadow_spool.sh` |
| `OG-CORE-AGENT-SMOKE-DARK` | optional | `.github/workflows/core-agent-smoke.yml` → `agent-smoke-dark` / `agent-smoke-all`（`workflow_dispatch` only） | N | `docs/testing.md` §6 |
| `OG-WAVE7-REGRESSION-A` | optional | `python 04_Workflows/_wave7_regression_gate.py --tier A` | N | `docs/testing.md` §5.1 · `docs/tabular-mvp-release-checklist.md` |
| `OG-AGENT-LINES-METRICS` | optional | W10-T2 agent_lines metrics JSON（`outbox/agent_ci/` 汇总）；**mandatory PR gate 不依赖** metrics 存在 | N | `04_Workflows/tickets/W10-T2-agent-lines-metrics-and-monitoring-v1_state.md` |

### 2.4 Logging-only（观测；不改变 merge 语义）

| gate_id | class | workflow_or_runner | blocks_mainline | authority_doc |
|---------|-------|-------------------|-----------------|---------------|
| `LG-ENF-FLAGS-AUDIT` | optional | `eval-gate` / `eval-shadow-nightly` → `python -m observability.enf_config`（non-fatal audit 行） | N | `observability/enf_config.py` |
| `LG-DRYRUN-GOV-LOG` | shadow-only | `eval-shadow-nightly` → `python -m tools.dryrun_ci_wrapper`（`continue-on-error: true`） | N | `observability/dryrun/README.md` |
| `LG-EVAL-OBS-ARTIFACTS` | optional | PR `eval-gate` → eval_report / wf_status_summary / trace correlate 上传 artifact | N | `docs/testing.md` §5 · `observability/eval_report.py` |

> **Wave B/C 假设**：仅 **§2.1 四行 mandatory** 为 PR 必过 SSOT；§2.2 均为 `blocks_mainline=N` 或 `shadow`；§2.3–§2.4 **不得** 误写为 mandatory 或自行升格 blocking canary。

---

## §3 PR 路径

### 3.1 触发与工作流

| Workflow | Job | 事件 | Required for merge |
|----------|-----|------|-------------------|
| `eval-gate-ci.yml` | `eval-gate` | `push` / `pull_request` / `workflow_dispatch`（非 schedule） | **Yes**（mandatory） |
| `core-agent-smoke.yml` | `agent-smoke-pr` | `push` / `pull_request`（paths-ignore 纯文档时不触发） | **Yes**（mandatory） |
| `eval-gate-ci.yml` | `shadow-spool-smoke` | 同上 | No（optional） |

### 3.2 `eval-gate` job 步骤顺序（摘要）

1. `GOV_ENF_ENABLE=1`，**`GOV_ENF_BLOCKING_CANARY=0`**（PR 亦 shadow preview 语义；见 `observability/enf_config.py`）  
2. P+ eval unit tests（含 `tests.test_eval_gate`、`tests.test_eval_ci_check` 等）  
3. Routing eval dry-run（W4-T4；**optional** 分类，见 §2.3）  
4. `observability.eval_ci_check` on `artifacts/eval/ibridge_records.latest.jsonl`（limit 50，ratio 0.72）  
5. Observability artifact 生成与上传（logging-only 语义，失败仍由前述 mandatory 步骤决定）

### 3.3 本地等价命令

```bash
python -m unittest tests.test_eval_gate tests.test_eval_ci_check -v
python -m observability.eval_ci_check tests/fixtures/eval/ibridge_records.jsonl --limit 50 --max-needs-review-ratio 0.72
python 04_Workflows/_core_agent_smoke.py --tier PR -v
python 04_Workflows/_ops_cycle.py checklist --mode full
```

---

## §4 Nightly/schedule 路径

### 4.1 `eval-shadow-nightly` job

| 项 | 值 |
|----|-----|
| 触发 | `schedule` cron `0 6 * * *` UTC；或 `workflow_dispatch` + `run_shadow_nightly=true` |
| ENF | `GOV_ENF_ENABLE=1`，**`GOV_ENF_BLOCKING_CANARY=0`**（prod 默认 shadow-only） |
| Shadow 输入 | `artifacts/eval/k2_shadow_spool.jsonl`；batch `artifacts/eval/shadow_batch_*.jsonl` |
| 导出 | `artifacts/eval/shadow_ibridge_records.latest.jsonl` |
| eval 门槛 | ratio **0.60** + `--fail-on-tags infra_risk`（**仅 shadow**；与 PR 0.72 不同） |
| Job 失败语义 | 核心 eval step 设 `continue-on-error: true` → **shadow-only，不阻塞 PR／主链** |

### 4.2 Artifact 与 log 路径

| 产物 | 路径 |
|------|------|
| Shadow 导出 JSONL | `artifacts/eval/shadow_ibridge_records.latest.jsonl` |
| eval_export nightly | `artifacts/eval/eval_export_v1_shadow_nightly.latest.jsonl` |
| eval report | `artifacts/eval/eval_report.latest.{md,json}` |
| WF status | `artifacts/wf/wf_status_summary.latest.{md,json}` |
| ENF dry-run per-record | `observability/dryrun/<stamp>_per_record.jsonl` |
| ENF shadow summary | CI log 行 `[GOV-ENF-SHADOW-SUMMARY]`（JSON） |
| GHA artifact | `eval-gate-observability-nightly` |

### 4.3 ENF Preview 值班要点

- **`GOV_ENF_BLOCKING_CANARY=0`**：preview 仍执行，**不** fail pipeline；`would_block` 为观测值。  
- 任何 **`GOV_ENF_BLOCKING_CANARY=1`** 或 prod blocking 须尚書省 **BLOCKING-CRITERIA** 批文；本 contract **不包含** 该授权。  
- 操作细节：`docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md`。

### 4.4 Skip ≠ pass

Shadow batch 缺数据导致 seed／fixture fallback 时：

1. 查 log `[SHADOW-PIPELINE]` 与 `eval_ci_check` JSON 的 `reason`／`ok`  
2. **不得** 将 skip 或 `continue-on-error` 视为生产达标  
3. **不得** 据此自动升格为 PR blocking gate

---

## §5 模型/K-2 流量角色

### 5.1 Phase 矩阵（引用）

本合同 **索引** `docs/k2_deployment_governance.md` §4.1 矩阵，**不** 复制全文：

| Phase | 流量特征 | 本 contract 关系 |
|-------|----------|------------------|
| **0** | prod = ask-only；K-2 = dev/test | 当前默认；无 prod canary |
| **1** | Prod shadow（用户 100% ask） | `SG-K2-SHADOW-EXPORT` + `SG-EVAL-SHADOW-NIGHTLY` 对齐 |
| **2** | Internal canary 5–10% | **未授权**；本 contract **不包含** prod canary 批文 |
| **3** | Controlled expansion 10–30% | **未授权** |
| **4** | Primary switch | 远期；非本票范围 |

合流规则细节：`docs/k2_merge_strategy.md`（`infra_risk` → CI fail 对齐 nightly `--fail-on-tags`）。

### 5.2 Phase 3.5 contract 明确 **不包含**

- K-2 **Phase 2** internal canary 启用  
- `GOV_ENF_BLOCKING_CANARY=1` 或 ENF blocking 生产裁断  
- 修改 `ASK_MERGE_INTERFACE` 或 `/api/ask` 路由  
- 任何将 shadow nightly 升格为 **mandatory PR** gate 的操作

### 5.3 Severe eval 与 shadow 对齐

| 信号 | PR path | Nightly shadow |
|------|---------|----------------|
| `needs_review` ratio | fail if > **0.72** | observability at **0.60**（continue-on-error） |
| `infra_risk` tag | PR 默认 **不** fail-on-tags | **fail-on-tags** enabled（shadow signal） |
| 用户可见答案 | N/A（fixture） | 仍 100% ask（Phase 1） |

---

## §6 成本/风险字段

### 6.1 Eval record 最小字段（trace 交叉引用）

P+ eval 导出与 shadow 对比记录 **应** 含（与 `observability/eval_export_schema.md` 对齐）：

| 字段族 | 键（示例） | 用途 |
|--------|------------|------|
| 身份 | `task_id`, `trace_id`, `run_id` | 与 `observability/trace_schema.py` correlate |
| ibridge | `ibridge_v0` 或等价 pipeline 摘要 | selector／answer 侧车对照 |
| eval | `tags[]`, `gate_result`, `eval_gate` | P+ 规则输出 |
| K-2 shadow | `k2_summary`, `k2_merge` | shadow-only 对比 |
| 成本 proxy | `context_token_usage.total_tokens` | **非** 统一成本 SSOT |

本票 **不** 实现新 trace 字段；完整 spec 见 `docs/observability.md` 与 `observability/eval_trace_correlate.py`。

### 6.2 风险标签（eval_gate v0.1）

| Tag | 含义 | PR 默认 | Nightly shadow |
|-----|------|---------|----------------|
| `infra_risk` | 基础设施／超时类 | 不 fail（`--fail-on-tags` 空） | fail-on-tags |
| `high_retry` | 高重试 | observability | shadow spool retain |
| `context_heavy` | 上下文过重 | observability | observability |
| `observability_gap` |  trace 不完整 | observability | observability |

### 6.3 Known gap — 双数据源成本（follow-up）

| 数据源 | 现状 | 决策可用性 |
|--------|------|------------|
| `daily_cost_summary` (DCS) | 与 `task_runs` 同日口径可矛盾 | **不可用** 于 gate 门槛 |
| `task_runs` / Langfuse usage | 低样本；`total_cost_usd` 多为 0 | **partial**（见 `docs/WAVE1-3_HISTORY_STATUS.md` §3.2） |

**Follow-up 占位**：统一成本口径票（未开）；本合同 **不** 假装已统一。

---

## §7 失败处置与 rollback 指针

### 7.1 Mandatory gate 失败

| gate_id | 处置 | rollback |
|---------|------|----------|
| `MG-EVAL-CI-CHECK` | 修 exporter／fixture 或 eval 回归；查 `needs_review` ratio 与 tags | 回滚引入 eval 回归的 commit；重跑 `eval_ci_check` |
| `MG-CORE-AGENT-SMOKE-PR` | 查 `smoke_ci_summary.json` → `failed_modules[]` | 回滚 agent workflow 变更；`--tier PR -v` 本地复现 |
| `MG-OPS-EVAL-SUBSET` | 与 PR eval 子集对齐；查 fixture 是否漂移 | 见 `docs/GOVERNANCE_ONBOARDING_v1.md` Step 10 |

### 7.2 Shadow-only 失败

- **不** 阻塞 merge；须查 nightly artifact 与 `[GOV-ENF-SHADOW-SUMMARY]`  
- `infra_risk` 升高 → 对照 `docs/k2_deployment_governance.md` §7 回退条件；**不** 自行开 canary  
- ENF `would_block` spike → `docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md` §5 escalation；**不开** `GOV_ENF_BLOCKING_CANARY=1`

### 7.3 K-2 紧急回退

工程 on-call 可先执行 **ask-only** 回退（`docs/k2_deployment_governance.md` §2.1）；24h 内尚書省报备。本 contract 不定义 runbook 逐步命令。

### 7.4 手动打开 blocking 的治理

若 ops 将 `GOV_ENF_BLOCKING_CANARY=1` 写入 prod CI env：

- 视为 **未经授权** 的 Phase 升格尝试  
- 须立即还原 `GOV_ENF_BLOCKING_CANARY=0` 并开 governance 票留痕

---

## §8 验证命令

### 8.1 本票 unittest（AC-7 / AC-8）

```bash
python -m unittest tests.test_phase3_5_governance_contract_v1 tests.test_eval_gate -v
```

### 8.2 OPS 全量 checklist（文档引用；失败记 blocked，不冒充 done）

```bash
python 04_Workflows/_ops_cycle.py checklist --mode full
```

### 8.3 Contract 结构自检

```bash
python -m unittest tests.test_phase3_5_governance_contract_v1 -v
```

### 8.4 相关索引

| 文档 | 关系 |
|------|------|
| `docs/testing.md` §5–§6 | PR smoke 与 eval 交叉引用 |
| `docs/k2_deployment_governance.md` | K-2 Phase 审批矩阵 |
| `docs/k2_merge_strategy.md` | 合流与 severe eval |
| `docs/governance-constitution-v1.md` §3.4 | OPS checklist |
| `docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md` | ENF shadow 值班 |
| `04_Workflows/WORKFLOW_INDEX.md` | 工作流索引 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | WA-T3 进度 |
| `docs/WAVE_A_EXECUTION_PLAN.md` §0 | P3.5 完成度 |

---

*Phase 3.5 governance contract v1 · WA-T3 · doc-only SSOT · 2026-06-10*
