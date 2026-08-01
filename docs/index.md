# 大唐三省六部 — 文档总入口

> **版本**: Phase 1 Documentation Baseline  
> **更新**: 2026-06-05

---

## 快速导航

### 🚀 开始

| 文档 | 内容 |
|------|------|
| [`../README.md`](../README.md) | 项目总览、安装、启动 |
| [`../AGENTS.md`](../AGENTS.md) | 副官接战守则（必读） |
| [`../README_Refresher.md`](../README_Refresher.md) | 快速参考、点火 SOP |

### 📐 架构与治理

| 文档 | 内容 |
|------|------|
| [`architecture.md`](./architecture.md) | 系统架构、Mermaid 图、模块说明 |
| [`knowledge-layer.md`](./knowledge-layer.md) | **知识层 Phase 2**：PG+Qdrant 主方案、metadata、ingest/retrieve 入口 |
| [`phase2-knowledge-indexing-contract-v1.md`](./phase2-knowledge-indexing-contract-v1.md) | **Phase 2 收录契约 SSOT**：indexed/catalogued/excluded 三态、登记流程、Wave/Phase 标注 |
| [`phase2-index-contract-gap-audit-v1.md`](./phase2-index-contract-gap-audit-v1.md) | **Phase 2 gap 审计**（FP-G2-T2）：契约 vs 实际能力；审计 ≠ 已修复 |
| [`phase2-rag-e2e-answer-frame-v1.md`](./phase2-rag-e2e-answer-frame-v1.md) | **RAG E2E 问答 FRAME**（FP-G2-T3）：planning only；FRAME ≠ E2E 已验收 |
| [`phase2-graphrag-jobs-state-machine-v1.md`](./phase2-graphrag-jobs-state-machine-v1.md) | **graphrag_jobs 状态机设计**（FP-G2-T4）：设计 doc ≠ GraphRAG 主路／已验收 |
| [`phase6-release-sanity-runbook-v1.md`](./phase6-release-sanity-runbook-v1.md) | **P6 release-sanity 操作单页**（FP-G6-T2）：MP→MC→CI-SMOKE；≠ required CI／INT Tier-A／P6 closure |
| [`phase6-inspector-overclaim-spotcheck-v1.md`](./phase6-inspector-overclaim-spotcheck-v1.md) | **P6 inspector over-claim 抽样**（FP-G6-T4）：Reviewer 加速层；≠ 替代 wave-next-code-inspector |
| [`phase6-agent-lines-nightly-deferred-index-v1.md`](./phase6-agent-lines-nightly-deferred-index-v1.md) | **P6 agent-lines nightly deferred 索引**（FP-G6-T3）：Landed vs Deferred；≠ required CI／INT Tier-A |
| [`fleet-metrics-dashboard-operator-v1.md`](./fleet-metrics-dashboard-operator-v1.md) | **P5 fleet metrics operator 读法**（FP-G5-T1）：MC-METRICS／HTTP；≠ Grafana 已上线 |
| [`grafana-pg-soak-deferred-index-v1.md`](./grafana-pg-soak-deferred-index-v1.md) | **P5 Grafana／PG soak deferred 索引**（FP-G5-T2）：Landed vs Deferred；≠ soak 已跑 |
| [`lane-progress-append-template-v1.md`](./lane-progress-append-template-v1.md) | **Lane Progress 末尾模板**（FP-G5-T3）：evidence_tier／append-only；≠ 改历史／Phase% |
| [`governance-dual-unblock-checklist-v1.md`](./governance-dual-unblock-checklist-v1.md) | **governance_dual 五顶解阻 FRAME**（FP-G1-T1）：≠ Round-2 GO／批文已齐 |
| [`wc-pre-06-07-approval-tracker-v1.md`](./wc-pre-06-07-approval-tracker-v1.md) | **WC-PRE-06/07 批文追踪**（FP-G1-T2）：approved 仅 human |
| [`phase3-5-gate-crossref-index-v1.md`](./phase3-5-gate-crossref-index-v1.md) | **P3.5 eval-gate/K-2/ENF 交叉索引**（FP-G1-T4）：≠ blocking canary |
| [`progress-dashboard-append-protocol-v1.md`](./progress-dashboard-append-protocol-v1.md) | **Progress/Dashboard 写入边界**（FP-G1-T5）：append-only · 禁改 Phase% |
| [`evidence-tier-contract-v1.md`](./evidence-tier-contract-v1.md) | **Evidence tier SSOT**（FP-G3-T1）：L-local／CI-advisory／GA-remote |
| [`trace-canonical-schema-append-process-v1.md`](./trace-canonical-schema-append-process-v1.md) | **Trace Canonical append 流程**（FP-G3-T4）：禁 ad-hoc 字段 |
| [`langfuse-pg-alignment-deferred-index-v1.md`](./langfuse-pg-alignment-deferred-index-v1.md) | **Langfuse/PG deferred 索引**（FP-G3-T3）：≠ 真接 Langfuse |
| [`dual-cp-narrative-alignment-v1.md`](./dual-cp-narrative-alignment-v1.md) | **雙 CP 敘事對齊**（FP-G4-T1）：full-phase／wave-plan／W-ORCH |
| [`toolchain-runtime-gap-audit-v1.md`](./toolchain-runtime-gap-audit-v1.md) | **Toolchain runtime gap**（FP-G9-T1）：WB-T1–T3 · ≠ prod flip |
| [`tabular-vs-phase88-tool-layer-index-v1.md`](./tabular-vs-phase88-tool-layer-index-v1.md) | **W3-TL vs Phase 8.8 分軌**（FP-G9-T4）：禁止合併 |
| [`p9-prod-ledger-gap-index-v1.md`](./p9-prod-ledger-gap-index-v1.md) | **P9 prod ledger gap**（FP-G9-T3）：≠ provider flip |
| [`bridge-stub-vs-prod-browser-gap-index-v1.md`](./bridge-stub-vs-prod-browser-gap-index-v1.md) | **Bridge stub vs prod browser**（W4-P85-bridge-prod-gap）：≠ GA pass |
| [`automation-blueprint-gap-index-v1.md`](./automation-blueprint-gap-index-v1.md) | **Blueprint G8-1–10 缺口**（FP-G10-T3）：≠ S15 prod |
| [`wc-t6-t7-v2-mapping-frame-v1.md`](./wc-t6-t7-v2-mapping-frame-v1.md) | **WC-T6/T7 path_id FRAME**（FP-G10-T2）：planning · ≠ distill runtime |
| [`governance.md`](./governance.md) | 治理规范：分支/提交/ID/命名/错误 |

### 🤖 Agent 与编排

| 文档 | 内容 |
|------|------|
| [`orchestration/README.md`](./orchestration/README.md) | 多 Agent 调度使用说明 |
| [`orchestration/AGENT_RULES.md`](./orchestration/AGENT_RULES.md) | Agent 角色与规则 |
| [`orchestration/TASK_BOARD.md`](./orchestration/TASK_BOARD.md) | 活任务板 |

### 📊 计划与进度

| 文档 | 内容 |
|------|------|
| [`../00_master_plan.md`](../00_master_plan.md) | 企业化补强总蓝图 |
| [`../04_Workflows/00_Agent_Work_Progress.md`](../04_Workflows/00_Agent_Work_Progress.md) | 战报存档 |

---

## 模块文档索引

### Core（核心编排）

| 模块 | 文档 | 代码 |
|------|------|------|
| Context Entry | `core/context_entry_contract.md` | `core/context_entry.py` |
| LangGraph K-1 | - | `core/langgraph_flow_k1.py` |
| LangGraph K-2 | - | `core/langgraph_flow_k2.py` |

### Metrics & Observability（指标与观测）

| 模块 | 文档 | 代码 |
|------|------|------|
| **Observability baseline (Phase 3+5)** | [`observability.md`](./observability.md) | `observability/trace_schema.py` |
| Metrics Schema | `metrics/metric_definition.md` | `metrics/metrics_schema.json` |
| Metrics Collector | - | `metrics/metrics_collector.py` |
| Trace / HTTP middleware | `observability.md` §2–§3 | `observability/logging_adapter.py`, `trace_middleware.py` |
| Dashboard + alerts (config) | `observability.md` §4–§5 | `observability/dashboard/*.json`, `*.yaml` |
| Eval Gate | `observability/eval_pipeline.md` | `observability/eval_gate.py` |

### Skills（技能层）

| 模块 | 文档 | 代码 |
|------|------|------|
| Skills Contract | `skills/skills_contract.md` | `skills/*.py` |

### Workflows（工作流）

| 文档 | 内容 |
|------|------|
| `04_Workflows/HARNESS_CONSTITUTION.md` | 宪法/最高规范 |
| `04_Workflows/ENGINEERING_CONTRACT.md` | 工程合约 |

---

## 常用命令速查

```powershell
# 进入主舱
. .\04_Workflows\Enter-Main.ps1

# 进入副舱
. .\04_Workflows\Enter-Agency.ps1

# 密钥盲测
python .\04_Workflows\_smoke_test_keys.py

# 一键战路
.\04_Workflows\Launch-Warpath.ps1 -WaveN 100

# 体检
python .\04_Workflows\_doctor_main_cabin.py
```

---

## 文档更新记录

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-06-05 | 创建 Phase 1 治理文档基线 | Governance Architect |
| 2026-06-05 | 新增 `knowledge-layer.md`（Phase 2 知识层收尾） | Knowledge Layer Engineer |
| 2026-06-10 | 新增 `phase2-knowledge-indexing-contract-v1.md`（WA-T1 收录契约） | Implementer |
| 2026-07-10 | 新增 `phase2-graphrag-jobs-state-machine-v1.md`（FP-G2-T4 状态机设计） | Implementer |
| 2026-07-10 | 新增 `phase6-release-sanity-runbook-v1.md`（FP-G6-T2 release-sanity 操作单页） | Scribe |
| 2026-07-10 | 新增 `phase6-inspector-overclaim-spotcheck-v1.md`（FP-G6-T4 over-claim 抽样对照） | Scribe |
| 2026-07-10 | 新增 `phase6-agent-lines-nightly-deferred-index-v1.md`（FP-G6-T3 nightly／run-all-allowed deferred 索引） | Scribe |
| 2026-07-10 | 新增 G1 四档：governance-dual checklist · WC-PRE tracker · P3.5 crossref · Progress append protocol（FP-G1-T1/T2/T4/T5） | Scribe |
| 2026-07-10 | 新增 `fleet-metrics-dashboard-operator-v1.md`（FP-G5-T1 fleet operator 读法） | Implementer |
| 2026-07-10 | 新增 `grafana-pg-soak-deferred-index-v1.md`（FP-G5-T2 Grafana／PG soak deferred 索引） | Implementer |
| 2026-07-10 | 新增 `lane-progress-append-template-v1.md`（FP-G5-T3 Progress 末尾模板） | Implementer |
| 2026-07-10 | Batch-3：evidence-tier SSOT 升格 + 9 份 gap／process／FRAME doc（G3/G4/G9/G10/G8） | Implementer |
