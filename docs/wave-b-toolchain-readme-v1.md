# Wave B Toolchain README — Bottom Layer Quick Entry

> **版本**：v1.0  
> **票号**：WB-T6 · `wave-b-bottom-layer-readme-and-phase-progress-alignment-v1`  
> **日期**：2026-06-11  
> **适用对象**：新合作者、Wave C（C1）服务引用方、复习 Toolchain contract 的 Agent  
> **阅读时间**：约 10 分钟（快速浏览）

---

## 系统现状一句话

**Toolchain Wave B（WB-T1–T7）** 已在 Tabular MVP（W3-TL）与 Agent Lines（W10–W12）实现之上，交付 **catalog/selector · executor/sandbox · outbox/feedback · toolchain health · audit spec · P6 smoke matrix YAML**；全部为 **plan_only / optional gate / investigation-only** 语义，**不改** MVP 主链默认行为。**WB-T6** 收口本 readme 与 Phase 索引；Observability Wave B（`WAVE-B-P*`）见 `docs/WAVE_B_EXECUTION_PLAN.md` — **不同轴**。

**Phase 完成度**：见 `docs/WAVE_PROGRESS_DASHBOARD.md`（**唯一 SSOT**）；本 readme 不重复百分比。

---

## 典型开发者流程

### 1. 接战校准（2 分钟）

1. 读 `docs/wave-b-toolchain-readme-v1.md`（本档）与 `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md`
2. 确认命名空间：Toolchain `WB-T*` ≠ Observability `WAVE-B-P*` ≠ Tabular `W3-TL-*`
3. 查票 state：`04_Workflows/tickets/WB-T*_state.md`

### 2. Contract 速查（5 分钟）

| 步骤 | 文档 | 验证 |
|------|------|------|
| Catalog + Selector | `docs/tool-catalog-and-selector-contract-v1.md` | `python -m unittest tests.test_tool_catalog_and_selector_contract_v1 -v` |
| Executor + Sandbox | `docs/tool-executor-and-sandbox-safety-contract-v1.md` | `python -m unittest tests.test_tool_executor_and_sandbox_contract_v1 -v` |
| Outbox + Feedback | `docs/outbox-and-feedback-layer-contract-v1.md` | `python -m unittest tests.test_outbox_and_feedback_layer_contract_v1 -v` |
| Health Dashboard | `docs/toolchain-health-dashboard-v1.md` | `python scripts/run_toolchain_health_dashboard.py --format json --dry-run` |
| Audit Quickview | `docs/audit-quickview-and-case-history-spec-v1.md` | `python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json` |
| P6 Smoke Matrix | `routing/toolchain_smoke_matrix_v1.yaml` | `python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v` |

### 3. 干跑一条 Tabular 路径（可选）

```bash
# plan_only：glue → selector → executor plan（不写 outbox）
python scripts/run_tabular_intake_tool_path.py \
  --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json

# 只读 outbox 检视
python -m tools.inspect_tabular_outbox --case-ref demo_phase --json
```

### 4. 离线健康摘要（可选 · 不阻塞 PR）

```bash
python scripts/run_toolchain_health_dashboard.py --format json --dry-run
# 输出 toolchain_health_v1；默认 gate_class=optional · blocks_mainline=false
```

### 5. 开 Multi-Chat 票时

- 角色边界：`docs/phase4-multi-agent-collaboration-contract-v1.md` §3–§5
- state 格式：`04_Workflows/tickets/README.md`
- **禁止**：Implementer 改 FRAME/STATE；自行新增里程碑编号

---

## 上位契约（AC-7 · Wave A 四份）

| Phase | Contract | 与 Toolchain 关系 |
|-------|----------|-------------------|
| **P2** 知识 / Indexing | `docs/phase2-knowledge-indexing-contract-v1.md` | Gov Registry 轨（`kb.*`）与 Tabular catalog **分轨**；WB-T3 `index_status` 侧车 |
| **P3.5** 成本 / Gate | `docs/phase3-5-cost-model-governance-contract-v1.md` | WB-T2 execute optional · WB-T4 dashboard **optional** · 不含 prod canary |
| **P4** Multi-Agent | `docs/phase4-multi-agent-collaboration-contract-v1.md` | Multi-Chat STATE 写入冻结；WB-T1 §5 对齐 Implementer 边界 |
| **P6** INT Regression | `docs/phase6-int-regression-gate-contract-v1.md` | 附录 A Tool-chain optional smoke matrix（WB-T4） |

验证（上位契约 smoke）：

```bash
python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 \
  tests.test_phase3_5_governance_contract_v1 \
  tests.test_phase4_multi_agent_contract_v1 \
  tests.test_phase6_int_regression_gate_contract_v1 -v
```

---

## Wave C 可假设能力

> 细则见 `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` §5 与 `docs/tool-catalog-and-selector-contract-v1.md` §6。

### 可假设（contract 已交付）

- 四轨 `tool_id` 命名与 `governed_by` 边界可读
- Selector 输出 `plan_only: true` 的 `candidate_tools[]` / `planned_tools[]`
- Executor 四级 `execution_mode` 与 case allowlist 矩阵有 SSOT
- 战車根 `outbox/` 六命名空间、`schema_id`、feedback 语义可 join `cases/index.json`
- `toolchain_health_v1` 可离线聚合 agent CI / metrics / catalog health
- Audit quickview `sections[]` / `timeline[]` / `gaps[]` 形状（WB-T5）
- P6 `toolchain_smoke_matrix_v1.yaml` 可读 tier / `gate_class` / `blocks_mainline`（WB-T7）
- Trace 建议键：`case_ref` + `task_type` + `selector_rule_id`

### 禁止假设（除非另票）

- Selector 已接 prod blocking INT gate 或 delivery gate
- Tabular E2E 默认驱动 selector（须专票 + feature flag）
- Non-Tabular stub 已接 heavy processor
- Toolchain dashboard 为 PR required check 或 SLA 字段
- `orchestration_bridge_outbox` 与战車根 outbox 已合并

**Wave C 服务入口（唯读）**：`docs/WAVE_C_EXECUTION_PLAN.md` — C1 调试/健检走 Observability 轴；引用 Toolchain 能力须显式标注 `WB-T*` contract 版本。

---

## Observability 逻辑路径

| 产物 | 逻辑路径 | 说明 |
|------|----------|------|
| Agent metrics 摘要 | `outbox/agent_metrics/metrics_summary.json` | W10-T2 产出；WB-T4 消费 |
| Toolchain health JSON | `artifacts/toolchain/toolchain_health.latest.json` | WB-T4 CLI 写入 |
| Toolchain health MD | `artifacts/toolchain/toolchain_health.latest.md` | 人读摘要 |
| WF status（可选） | `artifacts/wf/wf_status_summary.latest.json` | Observability 轴；`--include-wf-status` |

---

## case_ref 范例 fixture 表（traces）

| case_ref | maturity | stop_at（实验线） | 用途 |
|----------|----------|-------------------|------|
| `demo_phase` | stable | bundle | Tabular 锚点 · 主链回归 |
| `sampleco/2026-0001` | stable | checkpoint_b | 大表 + human review |
| `additional_demo` | controlled_experimental | checkpoint_b / sandbox e2e | W12-T1 sandbox 交付 |
| `sandbox_client` | controlled_experimental | cleaning_preview | gate-only 实验 |

**输入 maturity 范例（唯读 · 不改内容）**：`cases/demo_phase/raw/Phase.csv` — Tabular 清洗输入样例（7 行 milestones）；**不是** Phase 完成度 SSOT。

---

## 命名空间对照（勿混淆）

| 名称 | 票号 | 入口 |
|------|------|------|
| Observability Wave B | `WAVE-B-P*` | `docs/WAVE_B_EXECUTION_PLAN.md` |
| **Toolchain Wave B** | **`WB-T*`** | `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` |
| Tabular Tool Layer | `W3-TL-*` | `docs/tabular-tool-catalog-v1.md` |

---

## 索引

| 资源 | 路径 |
|------|------|
| 执行计划 | `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` |
| 进度 Dashboard（Phase% SSOT） | `docs/WAVE_PROGRESS_DASHBOARD.md` §Toolchain Wave B |
| 工作流索引 | `04_Workflows/WORKFLOW_INDEX.md` §1.26 |
| 票务索引 | `04_Workflows/tickets/README.md` §Wave B Toolchain |
| Agent Lines 总览 | `docs/agent-and-non-tabular-lines-readme-v2.md` |

---

*WAVE-B-TOOLCHAIN-README-v1 · WB-T6 · 2026-06-11*
