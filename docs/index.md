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
