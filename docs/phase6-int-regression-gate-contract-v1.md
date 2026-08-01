# Phase 6 — INT-REGRESSION-GATE Contract v1

> **Ticket**: WA-T6 · `phase6-int-regression-gate-runbook-and-ci-integration-v1`  
> **Role**: Phase 6 SSOT — gate tiers, pass definition, CI boundaries, failure diagnostics  
> **Implementation appendix**: `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md` (Tier invariants, per-test tables)  
> **Code authority**: `core/wave7_regression_gate.py` → `TIER_A_MODULES` / `TIER_B_MODULES` (loaded via `04_Workflows/_wave7_regression_gate.py`)

---

## §1 Gate 层级总览

| 层级 | CLI | 范围 | 默认策略 |
|------|-----|------|----------|
| **Tier-A** | `--tier A` | Wave 6 模块 + Wave 7 装配 + Wave 8 M2 核心契约（14 个 `tests.test_*` 模块） | **本地 mandatory**（改 envelope/manifest/QA/orchestrator/runner 前必跑）；**PR CI 不跑** |
| **Tier-B** | `--tier B` | 更重集成（Wave 8 orchestrator + Markdown 渲染，3 模块） | **推荐** pre-release；**不**阻断 PR merge |
| **ALL** | `--tier ALL` | Tier-A ∪ Tier-B（去重保序） | 完整集成回归；本地 / release checklist |
| **PR smoke** | `_core_agent_smoke.py --tier PR` | 战車根 7 个 agent workflow 模块 | **PR CI mandatory**（`core-agent-smoke.yml`） |
| **P+ eval** | `eval-gate-ci.yml` | eval unittest + fixture + routing eval dry-run | **PR CI mandatory** |
| **Agent lines** | `run_agent_lines_ci_suite.py` | Tabular / Non-Tabular agent regression 合并 | **Optional**；见 W10-T1 |

**层级关系（Phase 6 测试金字塔）**

```text
                    ┌─────────────────────┐
                    │ Eval / shadow       │  eval-gate-ci (PR)
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Agent lines CI      │  optional (W10-T1)
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ INT Tier-A / ALL    │  local mandatory · NOT in PR CI
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ MVP mainline reg.   │  release checklist
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │ PR smoke (ROOT agent workflows) │  core-agent-smoke.yml
              └────────────────┬────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Unit (per module)   │
                    └─────────────────────┘
```

**Runner 索引**：`04_Workflows/Master_Map.json` → `runners.wave7_regression_gate` → `04_Workflows/_wave7_regression_gate.py`

---

## §2 「过 INT gate」定义

### 2.1 Authoritative 过 gate 命令（本地）

从战车主舱 checkout 根，在已激活 **`gov_core_system`** venv 的 shell 中：

```powershell
python 04_Workflows/_wave7_regression_gate.py --tier A
```

**过 gate 判定（唯一 authoritative）**

1. **Exit code** = `0`（exit code 0）
2. **stdout 末行 JSON**（或 `--pretty` 整段 JSON）满足：
   - `"ok": true`
   - `"failed_tests": []`（或空数组）
   - `"tier": "A"`（或 `"suite": "A"`）
3. **stderr** 无 `INT-REGRESSION-GATE first failure:` 行

可选可读输出：

```powershell
python 04_Workflows/_wave7_regression_gate.py --tier A --pretty
```

### 2.2 与 unit-only PR 的区别

| 场景 | 过 PR smoke | 过 INT Tier-A |
|------|-------------|---------------|
| 改 `core/context_entry.py` | PR smoke 足够 | INT **不必**跑（除非动 Wave 6/7 装配） |
| 改 envelope / manifest / QA-M1 / Wave 7 orch / runner | PR smoke **不覆盖** | **必须**跑 Tier-A |
| 模块层单测全绿、装配层退化 | PR 仍可能绿 | INT Tier-A **应红** |

**设计理由**：INT gate 存在正是因为「模块层绿、装配层红」—— Tier-A 串联 envelope → manifest → QA → pipeline wire → lifecycle。

### 2.3 Exit code 语义

| Code | 含义 | 是否算过 gate |
|------|------|---------------|
| `0` | 请求 tier 内测试全绿（或 Tier-B 空注册 + `tier_b_pending`） | **是**（见 §4） |
| `1` | 有用例 failure/error | **否** |
| `2` | 配置/加载错误（地图、venv、模块 import） | **否**（基础设施故障） |

---

## §3 Tier-A 清单与不变量

**漂移规则**：本表与 `WAVE7_INT_REGRESSION_GATE_v0.1.md` §5 应对齐；若与代码不一致，**以 `core/wave7_regression_gate.py` → `TIER_A_MODULES` 为准**，并更新本 contract + WAVE7 附录。

| # | 模块 | 守护不变量（摘要） |
|---|------|-------------------|
| 1 | `tests.test_envelope_v2` | ENVELOPE-V2：BASIC/ENRICH schema、`present` 规则、禁止 billable / 路径泄漏 |
| 2 | `tests.test_wave6_manifest_writer` | MANIFEST-V2：去重、`accepted_units`、`billing_units` U/L、R-GROQ 排除 |
| 3 | `tests.test_wave6_qa_manifest_m1` | QA-M1：M1-KEYS/SHA/DEDUP/SKU/COUNT；不读 envelope/FS |
| 4 | `tests.test_wave6_e2e_smoke` | E2E：BASIC smoke、ENRICH/重复/tamper 聚合 |
| 5 | `tests.test_wave6_intake_gate` | INTAKE-GATE：accept/defer/reject、SKU、禁止绝对路径 hint |
| 6 | `tests.test_wave7_runner_env_bootstrap` | env bootstrap：逻辑路径、缺 map/schema → `ok: false` |
| 7 | `tests.test_wave7_runner_entry_job_input` | runner entry：`job_record`/`raw_files`、稳定 `error_code` |
| 8 | `tests.test_wave7_artifact_storage` | 落盘布局、幂等、I/O 失败回收、无绝对路径 |
| 9 | `tests.test_wave7_orch_pipeline_wire` | pipeline wire：ENRICH `present` seam、stage/error_code |
| 10 | `tests.test_wave7_report_summary_producer` | report：`accepted_units`/`billing_units`/`qa_status` 与 manifest + M1 |
| 11 | `tests.test_wave7_orch_job_lifecycle` | lifecycle：happy/fail、checkpoint/retry、QA P0 |
| 12 | `tests.test_wave8_m2_sampling_design` | M2 SamplingPlan：样本量边界、确定性 seed、分层覆盖 |
| 13 | `tests.test_wave8_m2_execution_engine` | M2 `run_m2_checks`：P0/P1、skip 条件 |
| 14 | `tests.test_wave8_m2_report_integration` | M1+M2 合并：`overall_ok`、`qa_status` 三态 |

**Tier-A 不变量（contract 级）**

- **MUST** 在改动 envelope / manifest / QA-M1 / Wave 7 orchestrator / runner / artifact 路径治理前全绿。
- **MUST NOT** 用全库 `pytest discover` 或 PR smoke 代替 Tier-A。
- 逐测试 → 不变量明细见 implementation 附录 `WAVE7_INT_REGRESSION_GATE_v0.1.md` §5.1。

---

## §4 Tier-B / ALL / pending 语义

### 4.1 当前注册（代码）

`TIER_B_MODULES`（3 模块）：

| 模块 | 场景 |
|------|------|
| `tests.test_wave8_m2_orch_integration` | M2 在 lifecycle 中的 `enable_m2` / `strict_m2` |
| `tests.test_wave8_report_md_renderer` | Markdown 双语 / audience 切换 |
| `tests.test_wave8_report_md_orch_integration` | `render_report_md` 在 orchestrator 中的集成 |

`--tier B`：**运行上述模块**；失败时 `ok: false`，exit `1`。

`--tier ALL`：Tier-A 全量 + Tier-B Extras（与 A 去重后顺序：A 然后 B）。

### 4.2 `tier_b_pending` 语义（空注册时）

当 `TIER_B_MODULES` **为空元组**时，`run_regression_gate(tier="B")` 返回：

```json
{
  "ok": true,
  "tier": "B",
  "modules": [],
  "tier_b_pending": true,
  "message": "Tier-B modules not registered yet; see WAVE7_INT_REGRESSION_GATE_v0.1.md §6"
}
```

- **`ok: true` + `tier_b_pending: true`** = 「无 heavier 集成测试可跑」，**不是**「集成测试已全部覆盖」。
- **禁止**将 pending 解读为 Wave 6/7 装配已验收完毕。
- **禁止** Wave B/C 假设 Tier-B（即使已注册 M2 orch 模块）= 完整 M2 orchestrator 集成 / 生产 E2E 已覆盖；真实抽样数据 E2E、bridge、invoice 仍不在 INT gate 范围。

### 4.3 预留场景（未注册 · follow-up 票）

- 同一 `job_id` 多次 `run_wave7_job` 幂等
- 多 stage I/O 抖动 retry 矩阵
- 千行 manifest 批次性能

见 `WAVE7_INT_REGRESSION_GATE_v0.1.md` §6 预留表。

---

## §5 与 smoke / eval / agent-lines 关系矩阵

| Gate | 命令 / Workflow | when_required | blocks_merge |
|------|-----------------|---------------|--------------|
| **INT Tier-A** | `python 04_Workflows/_wave7_regression_gate.py --tier A` | 改 envelope/manifest/QA/orch/runner；**release checklist 推荐** | **否**（PR CI 未接入）；本地 **mandatory** |
| **core-agent-smoke PR** | `python 04_Workflows/_core_agent_smoke.py --tier PR` · `.github/workflows/core-agent-smoke.yml` | 每 PR（战車根 agent workflow） | **是**（required check） |
| **eval-gate-ci** | `.github/workflows/eval-gate-ci.yml` → job `eval-gate` | 每 PR（P+ eval + observability unittest） | **是** |
| **agent-lines-ci-suite** | `python scripts/run_agent_lines_ci_suite.py --scope all` | Tabular/NT agent 线变更；**optional** pre-release | **否**（helper；非 production workflow 硬门禁） |
| **mvp-mainline-regression** | `python scripts/run_mvp_mainline_regression.py -v` | Tabular MVP tag / demo 前 | **否**（release checklist **mandatory**） |
| **routing-eval dry-run** | `python scripts/run_routing_eval.py --dry-run --format json` · `tests.test_routing_eval_runner` | routing catalog/glue 变更；PR 内 eval-gate step | **是**（eval-gate 内 step；**无** `--execute`） |

**关键结论（AC-6）**

- `core-agent-smoke.yml` **绿** + `eval-gate-ci.yml` **绿** **≠** INT Tier-A **绿**。
- PR merge **不**要求 INT Tier-A；发布 / Wave 6–8 装配变更 **应**跑 Tier-A。
- **不**宣称 nightly INT gate 已在 CI 调度（本票不新增 production workflow）。

**Optional 扩展指标（W10-T2）**

- Agent lines 离线指标：`outbox/agent_metrics/*_ci_summary.json`（`passed`/`failed`/`duration_ms` 等）— **optional**，不替代 INT gate JSON。
- INT gate contract 级 metrics：`passed` / `failed` / `errors` / `tests_run` / `failed_tests[]`。

---

## §6 CI 集成指南

### 6.1 PR CI 现状

**PR CI 绿 ≠ INT Tier-A 绿**：`core-agent-smoke.yml` 与 `eval-gate-ci.yml` 通过不代表 `--tier A` 已跑过或已通过。

| Workflow | 跑什么 | 不跑什么 |
|----------|--------|----------|
| `core-agent-smoke.yml` | `_core_agent_smoke.py --tier PR` | Wave 7 Tier-A、暗部 107+ 全矩阵 |
| `eval-gate-ci.yml` | eval unittest + `eval_ci_check` fixture + routing eval dry-run | INT Tier-A、mainline regression、`--execute` |

**本票 NonScope**：不把 INT gate 硬塞进 `eval-gate-ci.yml`；不新增 production GHA workflow。

### 6.2 Local mandatory vs CI optional

| 检查 | Local | PR CI | Release |
|------|-------|-------|---------|
| INT Tier-A | **Mandatory**（装配变更） | Optional（未接入） | **Recommended** |
| INT Tier-B / ALL | Recommended | Optional | Recommended |
| PR smoke | Recommended | **Required** | Same |
| MVP mainline 6/6 | Recommended | No | **Required** |

### 6.3 未来 CI 接入（文档化建议 · 非本票交付）

```yaml
# 伪代码 — 需 gov_core_system venv；非当前 PR 必过
- name: Wave 6/7/8 integration regression (Tier-A)
  run: python 04_Workflows/_wave7_regression_gate.py --tier A
```

详见 `04_Workflows/WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md` §7。

### 6.4 venv 指针

INT Tier-A **必须**能 import 暗部 `core.wave7_*` 与 `gov_core_system/tests/*`。

- 激活：`04_Workflows/Enter-Agency.ps1` 或地图 `Master_Map.cabins.gov_core_system` 所指 venv。
- CLI 自动注入：`_wave7_regression_gate.py` 从 `Master_Map.json` 插入 venv 至 `sys.path`。

---

## §7 失败诊断

### 7.1 stderr 标准格式

首个失败时 CLI 打印（`format_first_failure_line`）：

```text
INT-REGRESSION-GATE first failure: test=<test_id> stage=<stage|-> job_id=<job_id|-> first_qa_check_id=<check_id|->
```

**工单粘贴模板**：复制整行 stderr；附 stdout JSON 中 `failed_tests[0]`。

### 7.2 JSON 字段

成功时 stdout JSON 含 contract 级 metrics 键：`passed` / `failed` / `errors` / `tests_run` / `modules` / `failed_tests`。

```json
{
  "ok": true,
  "suite": "A",
  "tier": "A",
  "modules": ["tests.test_envelope_v2", "..."],
  "passed": 95,
  "failed": 0,
  "errors": 0,
  "tests_run": 95,
  "failed_tests": []
}
```

| 字段 | 说明 |
|------|------|
| `test_id` | 完整 unittest id，如 `tests.test_wave7_orch_pipeline_wire.Test....test_envelope_stage_failure_*` |
| `kind` | `failure` 或 `error` |
| `message` | 首行 assertion / 错误摘要 |
| `stage` | 尽力从 traceback 解析（`envelope` / `manifest` / `qa` / …） |
| `job_id` | fixture job id（如 `w7-pipe-bad-sku`） |
| `first_qa_check_id` | 首个 QA check（如 `M1-COUNT`、`M2-SCHEMA-20`）；无则 `null` |

### 7.3 从 `job_id` 反查 envelope stage

1. 读 `failed_tests[0].test_id` → 定位模块（如 `test_wave7_orch_pipeline_wire`）。
2. 读 `stage` + `job_id` → 对照 `WAVE7_INT_REGRESSION_GATE_v0.1.md` §5.1 该模块不变量表。
3. Orchestrator lifecycle 语义：`tests.test_wave7_orch_job_lifecycle` 与 pipeline wire 测试共享 Wave 7 job 构造模式；stage 失败通常卡在 envelope/manifest 写回前。

**Exit code 分流**

- `1` → 回归失败：修测试或修装配逻辑后重跑 `--tier A`。
- `2` → 加载/地图/venv：修环境后重跑；**不要**当业务回归失败处理。

---

## §8 验证命令

### 8.1 Contract 结构（本票 · 无 gov_core venv）

```powershell
python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v
python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v
```

### 8.2 INT Tier-A 本地验收（需 gov_core venv）

```powershell
python 04_Workflows/_wave7_regression_gate.py --tier A --pretty
```

预期：`ok: true`，`modules` 长度 14，exit `0`。无 venv 时记 **blocked**，不冒充 done。

### 8.3 CLI help smoke

```powershell
python 04_Workflows/_wave7_regression_gate.py --help
```

### 8.4 交叉引用

| 文档 | 用途 |
|------|------|
| `docs/ci-design-p6-int-gate-v1.md` | **CI 接入设计**（三轨 PR optional / nightly / release · design-only · WF-P6-INT-UPLIFT；**非** live CI） |
| `docs/phase6-int-regression-verification-report-v1.md` | **Consolidated Tier-A verification report**（executed JSON · verdict · CI readiness · WF-P6-INT-GATE） |
| `docs/testing.md` | Phase 6 开发者入口 · 金字塔 · entry points |
| `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md` | Tier 逐测试不变量 · JSON 示例 |
| `04_Workflows/WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md` §7 | CI 挂接伪代码 · PowerShell JSON 解析 |
| `04_Workflows/WAVE7_CLEAN_RUNNER_ORCH_OVERVIEW_v0.1.md` §5–§6 | INT gate 在 Wave 7 装配链中的位置 |
| `docs/tabular-mvp-release-checklist.md` | Release 推荐 INT Tier-A 一行 |
| `docs/toolchain-health-dashboard-v1.md` | Tool-chain health dashboard（optional；WB-T4） |
| `routing/toolchain_smoke_matrix_v1.yaml` | Tool-chain smoke matrix SSOT（WB-T7） |

---

## 附录 A — Tool-chain smoke matrix（WB-T7 · YAML SSOT）

> **SSOT**：`routing/toolchain_smoke_matrix_v1.yaml`（`schema_version=toolchain_smoke_matrix_v1`）  
> **分类**：与 `docs/phase3-5-cost-model-governance-contract-v1.md` §2 对齐（`mandatory` / `optional` / `shadow`）；本矩阵 **不含** PR mandatory trio 升格。  
> **MP/MC/CI release sanity**：`docs/smoke-and-regression-contract-v1.md`（`TS-MP-SMOKE` · `TS-MC-SMOKE` · `TS-CI-SMOKE` 矩阵条目）。  
> **用途**：Wave C Agent 读取 P6 时知悉 local recommended / optional CI / release-only 工具链验证；与 `docs/toolchain-health-dashboard-v1.md` 命令表单向同步（**YAML 为准**）。  
> **执行**：本地 optional runner `python scripts/run_toolchain_smoke_matrix.py`（**不**进 PR CI）；亦可仍用既有 scripts / unittest 逐条执行。  
> **验证**：`python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v`

### A.1 INT Tier vs Toolchain smoke（分表）

| 表 | SSOT | 范围 |
|----|------|------|
| **INT Tier-A/B** | `core/wave7_regression_gate.py` · 本 contract §3–§4 | Wave 6/7/8 装配回归；**非** tool-chain smoke |
| **Toolchain smoke** | `routing/toolchain_smoke_matrix_v1.yaml` | Agent lines · routing eval · W3-TL · dashboard · MVP mainline（release-only） |

### A.2 矩阵摘要（完整列见 YAML）

| smoke_id | tier | gate_class | blocks_mainline | 摘要 |
|----------|------|------------|-----------------|------|
| `TS-W3TL-UNIT` | local_recommended | optional | N | W3-TL 四件套 unittest |
| `TS-ROUTING-EVAL-*` | optional_ci | optional | N | routing eval runner + dry-run（W4-T2/T4） |
| `TS-AGENT-LINES-CI` | local_recommended | **optional** | N | W10-T1；**非** PR mandatory（AC-8） |
| `TS-AGENT-LINES-METRICS` | local_recommended | optional | N | W10-T2 metrics scan |
| `TS-AGENT-LINES-AUDIT` | local_recommended | optional | N | W10-T3 audit quickview |
| `TS-AGENT-LINES-MONTHLY` | local_recommended | optional | N | W11-T3 monthly head |
| `TS-TOOLCHAIN-DASHBOARD-*` | local_recommended | optional | N | WB-T4 dashboard dry-run + contract unittest |
| `TS-WF-STATUS-HELP` | local_recommended | optional | N | wf_status `--help` only |
| `TS-MVP-MAINLINE` | **release_only** | optional | **Y** | release checklist mandatory；**不**进 PR CI |
| `TS-INT-TIER-A` | **local_mandatory** | **mandatory** | N | INT Tier-A assembly regression；**非** PR CI（`blocks_pr_ci: false`） |
| `TS-MP-SMOKE` / `TS-MC-SMOKE` / `TS-CI-SMOKE` | local_recommended | optional | N | release sanity · 见 `smoke-and-regression-contract-v1.md` |

**Pass semantics（本附录）**

- Toolchain matrix 条目 **默认** `gate_class=optional` · `blocks_mainline=false`（MVP mainline 例外：`tier=release_only` · `blocks_mainline=true`）。
- `TS-TOOLCHAIN-DASHBOARD-DRYRUN` + `TS-TOOLCHAIN-DASHBOARD-UNIT` 绿 = WB-T4 observability contract OK。
- `TS-AGENT-LINES-CI` 失败 **不** 阻塞 PR merge（W10-T1 optional class）。

**Forbidden（本附录边界）**

- Do **not** add matrix steps to `eval-gate-ci.yml` or `core-agent-smoke.yml` as **new** required checks。
- Do **not** treat `aggregated_health_score` or matrix `estimated_seconds` as SLA / SLO gate。
- Do **not** 将 tool-chain smoke 升格为 INT Tier-A 或 PR mandatory trio（违 WA-T3）。

**WB-T4 dashboard 命令对齐（YAML 覆盖）**

以下命令必须出现在 YAML `entries[].command`（machine-checked by `tests.test_phase6_toolchain_smoke_matrix_v1`）：

1. `python scripts/run_toolchain_health_dashboard.py --format json --dry-run --no-write`
2. `python -m unittest tests.test_toolchain_health_dashboard_v1 -v`
3. `python scripts/run_agent_lines_ci_suite.py --scope all --format json --no-ci-summary`
4. `python scripts/analyze_agent_lines_metrics.py --format json --no-write`
5. `python scripts/generate_agent_lines_monthly_report.py --no-write --format json`
6. `python -m observability.wf_status_summary --help`

---

*附录 A 机器可读 SSOT · WB-T7 · 取代 WB-T4 inline-only 表*

---

*Phase 6 contract v1 · WA-T6 · authoritative over WAVE7 gate doc for tier/CI semantics*
