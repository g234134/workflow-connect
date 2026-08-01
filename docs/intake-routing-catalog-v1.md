# Intake Routing Catalog v1

> **Ticket**: W2-T1 · Routing Catalog（Wave 2 · MVP Intake / Routing / Eval 基礎層）  
> **Machine SSOT**: `routing/intake_routing_catalog_v1.yaml`  
> **Date**: 2026-06-10  
> **Status**: catalog / rules only — **not** a routing engine implementation

---

## 1. 目的与范围

### 1.1 本文件是什么

本档是 **入口 / 技能 / 工具路由层** 的收敛视图（人读 spec），回答：

- Skill、Gov tool、Tabular 工具层、Product skill card 各是什么、边界在哪。
- 常见 **任务类型**（如 tabular cleaning、KB index、governance check、ask H 线）应优先走哪条 **Catalog family**、哪些 `tool_id`、哪个 CLI entrypoint。

机器可读清单见 `routing/intake_routing_catalog_v1.yaml`；Wave 2 **T2** 将以此写 routing / eval 测试样例。

### 1.2 In scope

| 项 | 说明 |
|----|------|
| 名词定义 | Skill / Gov tool / Tabular tool / Product skill card / Eval job / Route |
| 任务类型表 | 触发方、优先 family、典型 `tool_id`、entrypoint |
| 与既有 Catalog 关系 | `SKILL_CATALOG_OVERVIEW`、`tabular_tool_catalog_v1.json`、`routing_policy.yaml` |
| 挂钩点枚举 | 未来 routing engine / eval pipeline 的消费点（**不实现**） |

### 1.3 Out of scope（本票不做）

| 项 | 说明 |
|----|------|
| 改现有实现 | 不动 `tools/`、`scripts/`、`skills/` 内程式、`core/*` router |
| 改治理母本 | 不动 `HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`AGENTS.md` |
| LLM / eval prompt 内容 | 只做结构；`eval_profile` 字段留给 T2 |
| 真正的 routing engine | 不改 `core/routing_policy_loader.py`、`ask_rag_selector`、Tabular selector/executor |
| Catalog 合并 | **禁止** 把 Gov / Tabular / Product card / Phase 8.8 塞进同一 JSON 命名空间 |

---

## 2. 名词表

| 术语 | 定义 | SSOT / 位置 | ID 格式 |
|------|------|-------------|---------|
| **Skill（广义）** | 可被 Agent 引用的能力描述；本 repo 分 **四套** 平行 Catalog，不可混用 schema | 见 §4 | 依 family 而异 |
| **Gov tool** | Wave B 可观测 / KB CLI 登记项；供 routing policy、ops、eval gate 引用 | `skills/gov_cards/*.json` · `docs/SKILL_CATALOG_OVERVIEW.md` | `obs.*` · `kb.*` · `route.*`（保留） |
| **Tabular tool** | Tabular MVP 主链（intake → gate → clean → bundle → E2E）及辅助 CLI | `tools/tabular_tool_catalog_v1.json` · `docs/tabular-tool-catalog-v1.md` | `intake.*` · `validate.*` · `clean.*` · `export.*` · `orchestrate.*` 等 |
| **Product skill card** | Wave8 对外 CLEAN 产品 SKU；客户叙事用 | `skills/cards/skill-clean-*.json` | `skill-clean-*` |
| **Phase 8.8 编排层** | 暗部 ask / orchestration Tool Layer（draft）；与 Tabular MVP **分轨** | `04_Workflows/SPEC_tool_catalog_and_selector_v1.md`（draft）· `W3-T1`–`T4` state | `llm.*` 等 |
| **Eval job** | 对 ask / workflow 输出的离线评测与 CI gate；消费 Gov `obs.eval.*` 工具族 | `observability/eval_*.py` · `config/routing_policy.yaml` route `wave_b.eval_report` | 无独立 `tool_id`；路由到 `obs.eval.export` 等 |
| **Route（本 Catalog）** | 一条 **任务类型 → family + tool_ids + entrypoint** 的映射记录 | `routing/intake_routing_catalog_v1.yaml` → `routes[]` | `task_type` 字符串（本 Catalog 命名空间） |
| **HQ task_type** | 尚書省派工到 HQ/Dark worker 的类型（**另一套**命名空间） | `04_Workflows/TASK_ROUTING.md` · `task_routing_table.json` | `hq.*` · `chariot.*` · `dark.*` |
| **Routing Policy route** | Wave B Gov 工具 **编排顺序**（config 层） | `config/routing_policy.yaml` | `route_id` 如 `wave_b.eval_report` |

**关键区分**：本 Catalog 的 `task_type`（例 `tabular.cleaning.mvp`）描述 **业务任务应走哪套工具**；HQ 的 `task_type`（例 `hq.governance`）描述 **派给哪个 worker**。二者可并存、通过 `hq_task_type` 字段交叉引用，但 **禁止** 混为同一 ID 命名空间。

---

## 3. 入口 / 任务类型表

下表列出 **今天真的在用** 的主线。Agent / 人类接战时应先对号入座，再查对应 Catalog SSOT 取 `tool_id` 与 CLI。

| task_type | 谁触发 | 优先 tool family | 典型 entrypoint | 典型 tool_ids | eval_profile |
|-----------|--------|------------------|-----------------|---------------|--------------|
| `tabular.cleaning.mvp` | Agent / CLI / Local UI | **tabular_mvp** | `scripts/run_case_e2e_validation.py` | `validate.eligibility` → `clean.phase_demo` → `export.delivery_bundle`（或一步 `orchestrate.e2e`） | `none`（T2 填） |
| `tabular.cleaning.regression` | CI / Reviewer | **tabular_mvp** | `scripts/run_mvp_mainline_regression.py` | `orchestrate.mainline_regression`（包装 `orchestrate.e2e`） | `none` |
| `tabular.intake.new_case` | Agent / CLI | **tabular_mvp** | `scripts/new_cleaning_case.py` | `intake.new_case` | `none` |
| `gov.observability.eval` | CI / Agent | **gov_registry** | `observability/eval_exporter.py` 等 | `obs.eval.export` · `obs.eval.report` · `obs.wf.status_summary` | `eval_gate_v1`（T2 填） |
| `gov.observability.trace_triage` | Agent / ops | **gov_registry** | `observability/eval_trace_correlate.py` | `obs.eval.correlate` · `obs.trace.query`（**非** composite `obs.eval.triage` 作 prod step） | `none` |
| `kb.index.bootstrap` | Agent / CI | **gov_registry** | `workflow_v2/kb/repo_index_bootstrap.py` | `kb.index.bootstrap` · `kb.index.rag_smoke` | `none` |
| `governance.check.full` | Agent 接战 | **hq_ops**（非 tool Catalog） | `04_Workflows/_ops_cycle.py checklist --mode full` | N/A（runner 非 `tool_id`） | `none` |
| `governance.route.resolve` | Orchestrator | **hq_routing**（非 tool Catalog） | `04_Workflows/_route_task.py` | N/A；读 `task_routing_table.json` | `none` |
| `ask.h_line.context` | ask API / LangGraph | **h_line_context**（非 B-F1 Catalog） | `core/context_entry.py` → `build_rooted_context` | N/A；契约见 `context/context_entry_contract.md` | `none` |
| `ask.h_line.monitoring_sidecar` | ask 流程（signal_only） | **h_line_subagent** | `subagents/monitoring_executor.py` | N/A；**非** HQ `_route_task` | `none` |

### 3.1 Tabular MVP 主链（最常用）

```text
intake.new_case (可选)
  → validate.eligibility (P2 gate)
  → clean.phase_demo (P3)
  → export.delivery_bundle (P4)
  → 或一键 orchestrate.e2e
```

- **标准样本**：`cases/demo_phase` · `cases/sampleco/2026-0001`（见 `docs/mvp-standard-trace-path.md`）。
- **Local UI**：`ui.local` 包装上述 CLI；**NOT PROD**。
- **Selector / Executor**（W3-TL-T2/T3）：读 Tabular JSON Catalog；本 Intake Catalog 的 `tabular.*` 路由与之对齐，但 **不替代** selector 实现。

### 3.2 Gov / Eval 主线

- **Eval 编排**：`config/routing_policy.yaml` → `route_id: wave_b.eval_report` 顺序为 export → report → wf status。
- **CI**：`eval-gate-ci.yml` + `obs.eval.ci_check`；PR smoke 另跑 `tests.test_eval_gate`（见 `docs/testing.md` §5）。
- **Composite 注意**：`obs.eval.triage` 无独立模块；路由 steps 应展开为 `obs.eval.correlate` + `obs.trace.query`。

### 3.3 KB index 主线

- Bootstrap + smoke：`route_id: wave_b.kb_index_bootstrap`（policy）= `kb.index.bootstrap` → `kb.index.rag_smoke`。
- **Skeleton**：`kb.index.selector_gate` 仅 catalog 参考；**不得** 出现在 prod route steps（Wave C 专票）。

### 3.4 Governance / HQ 派工（非 tool_id 层）

| 场景 | 入口 | 说明 |
|------|------|------|
| 接战自检 | `_ops_cycle.py checklist --mode full` | 含 `routing_policy_validate` · `eval_gate_ci_subset` · `darkops_route_gate` |
| 派工路由 | `_route_task.py --type hq.governance` | `assignable: false`（DarkOps blocked）时 **不假绿** |
| 治理快照 | `docs/governance-constitution-v1.md` | 禁区类型引用母本 §7 |

### 3.5 ask H 线（与 Catalog 平行）

- **必须** `build_rooted_context`；禁止手写 context 包（`governance-constitution-v1.md` §3.5）。
- Monitoring subagent：**不** 新增 HQ `task_type`；走 `subagents/context_routing.py` 信号（见 `TASK_ROUTING.md` §3.4）。

---

## 4. 与现有 Catalog 的关系与边界

### 4.1 四层平行 Catalog（禁止合并）

```text
┌─────────────────────┐  ┌──────────────────────┐
│ Gov Tool Registry   │  │ Tabular Tool Catalog │
│ skills/gov_cards/   │  │ tools/tabular_*.json │
│ obs.* / kb.*        │  │ validate.* / clean.* │
└─────────┬───────────┘  └──────────┬───────────┘
          │                         │
          │    ┌────────────────────┴────────────────────┐
          │    │  intake_routing_catalog_v1.yaml       │
          └───►│  task_type → family + tool_ids         │◄─── 本票
               │  (跨 family 索引，不复制 tool 定义)      │
               └────────────────────────────────────────┘
          ┌─────────────────────┐  ┌──────────────────────┐
          │ Product skill cards │  │ Phase 8.8 (draft)    │
          │ skill-clean-*       │  │ llm.*                │
          │ 对外 SKU 叙事        │  │ 暗部 orchestration   │
          └─────────────────────┘  └──────────────────────┘
```

| Catalog | 文档 | 机器 SSOT | 本 Intake Catalog 如何引用 |
|---------|------|-----------|---------------------------|
| Gov Registry | `docs/SKILL_CATALOG_OVERVIEW.md` | `skills/gov_cards/*.json` | `preferred_tool_family: gov_registry` + `obs.*`/`kb.*` tool_ids |
| Tabular MVP | `docs/tabular-tool-catalog-v1.md` | `tools/tabular_tool_catalog_v1.json` | `preferred_tool_family: tabular_mvp` + tabular tool_ids |
| Routing Policy | `docs/ROUTING_POLICY_GUIDE.md` | `config/routing_policy.yaml` | `policy_route_id` 交叉引用 Gov 编排 |
| Product cards | `skills/cards/` | `skill_card_v0.1` | **仅叙事**；路由 **禁止** 用 `skill-clean-*` 作 `tool_ids` |
| Phase 8.8 | `W3-T1`–`T4` state | draft spec | `governed_by: phase_8.8_spec`；本 v1 routes **不列** `llm.*` |

### 4.2 Gov Catalog vs Wave8 Product cards

| 维度 | Gov Tool Catalog | Product skill cards |
|------|------------------|---------------------|
| 目录 | `skills/gov_cards/` | `skills/cards/skill-clean-*.json` |
| Schema | `gov_tool_card_v1` | `skill_card_v0.1` |
| 用途 | ops / eval / KB CLI routing | 客户 CLEAN SKU |
| B-F3 policy | **必须** 用 Gov `tool_id` | **禁止** 混入 policy steps |

### 4.3 Tabular vs Gov（分轨示例）

- Tabular E2E **不** 触发 `obs.eval.export` 或 monitoring graph（见 `mvp-standard-trace-path.md` §2.2）。
- Gov eval **不** 引用 `clean.phase_demo` 或 case 目录语义。
- 若任务同时需要「清洗一案」与「eval gate」，应拆为两条 `task_type` 或显式多步计划，**不得** 发明跨 family 的混合 `tool_id`。

---

## 5. 未来 routing engine / eval 挂钩点（非本票）

以下仅供 Wave 2 T2 及后续票参考；**本票不实现**。

| 挂钩点 | 现状 | 未来消费方 |
|--------|------|------------|
| `routing/intake_routing_catalog_v1.yaml` | 新建；task_type → family | T2 routing 测试；文档化 Agent 决策树 |
| `config/routing_policy.yaml` | Gov 工具编排 validate/resolve | Wave C prod selector 接線（专票） |
| `core/routing_policy_loader.py` | validate · resolve-route | 可扩展读 intake catalog（**未接**） |
| `tools/tabular_tool_catalog_v1.json` | W3-TL-T1 SSOT | W3-TL-T2 Selector · T3 Executor |
| `04_Workflows/_route_task.py` | HQ worker 派工 | 与 intake catalog 的 `hq_task_type` 对齐测试 |
| `tests.test_hq_task_routing_smoke` | PR smoke 子集 | T2 可增 intake catalog 结构测试 |
| `eval_profile` 字段（YAML） | 占位 `none` | T2 填 `eval_gate_v1` 等 profile id |
| `obs.eval.ci_check` | CI gate | T2 eval routing 样例 |

**边界重申**：Intake Catalog = **规则与索引**；Routing Policy = **Gov 工具顺序**；Tabular Selector = **case 级工具推荐**；HQ route_task = **派工**；四者并存、各司其职。

---

## 6. 验证

```bash
# 本票结构测试（可选 AC）
python -m unittest tests.test_intake_routing_catalog -v

# 下游 Catalog 健康（只读对照，非本票改码）
python -m skills.gov_tool_registry validate
python -m core.routing_policy_loader validate
python -m unittest tests.test_tabular_tool_catalog -v
```

---

## 7. 相关文档

| 文档 | 用途 |
|------|------|
| `routing/intake_routing_catalog_v1.yaml` | 机器可读 routes |
| `docs/SKILL_CATALOG_OVERVIEW.md` | Gov tool 索引 |
| `docs/tabular-tool-catalog-v1.md` | Tabular 工具索引 |
| `docs/ROUTING_POLICY_GUIDE.md` | Gov routing policy |
| `docs/mvp-standard-trace-path.md` | Tabular MVP trace |
| `04_Workflows/TASK_ROUTING.md` | HQ 派工 task_type |
| `04_Workflows/tickets/W2-T1-intake-routing-catalog_state.md` | 本票 FRAME / AC |

---

## 附录 A：10 分钟速读路径（新工程师）

1. 读 §2 名词表 → 记住 **四套 Catalog 不可混 ID**。
2. 读 §3 表 → 找到自己的任务类型（tabular / gov eval / kb / governance / ask）。
3. 打开 `routing/intake_routing_catalog_v1.yaml` → 查 `task_type` 对应 `tool_ids` 与 `entrypoint`。
4. 深入时跳 SSOT：`SKILL_CATALOG_OVERVIEW` 或 `tabular-tool-catalog-v1.md`。
5. 记住 §1.3：**本档不替你做路由执行**；真正跑 CLI 仍用各工具既有 entrypoint。
