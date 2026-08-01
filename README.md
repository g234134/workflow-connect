# 大唐三省六部 — AI Workflow 治理基线

> **新接战副官**：先读下方 **Start Here** 四链，再执行 OPS 一键自检。

## Start Here

| 优先 | 文件 | 用途 |
|:----:|------|------|
| 1 | [`AGENTS.md`](./AGENTS.md) | 接战／封存口令与 §初始化校准（权威入口） |
| 2 | [`README_Refresher.md`](./README_Refresher.md) | 日常 SOP 与点火指令速查 |
| 3 | [`04_Workflows/_PORTABLE_CORE_INDEX.md`](./04_Workflows/_PORTABLE_CORE_INDEX.md) | W0 可移植核心 vs 实例锚点分流 |
| 4 | [`04_Workflows/Master_Map.json`](./04_Workflows/Master_Map.json) | 路径、runners、cabins 权威索引 |

**一键自检**：`python 04_Workflows/_ops_cycle.py checklist --mode full`  
**接战对照表**：[`docs/GOVERNANCE_ONBOARDING_v1.md`](./docs/GOVERNANCE_ONBOARDING_v1.md)

---

## 延伸阅读

> **版本**: Phase 1 Governance Baseline  
> **更新**: 2026-06-07  
> **宪章**: 详见 `AGENTS.md` 与 `HARNESS_CONSTITUTION.md`

---

## 1. 项目目的

**大唐三省六部**是企业级 AI Workflow 治理框架，目标是将多 Agent 协作从「能跑」升级到「可度量、可交接、可治理」。

核心能力覆盖五大维度（D1–D5）：

| 维度 | 语义 | 关键指标 |
|------|------|----------|
| **D1** | 长任务成功率与稳定性 | `retry_count`, `success_rate`, checkpoint 政策 |
| **D2** | 上下文工程与记忆 | `context_token_usage`, `memory_hit_rate` |
| **D3** | 多 Agent 协作与编排 | `handoff_count`, Agent 契约, LangGraph 桥接 |
| **D4** | 可观测性与评估 | trace 完整度, Langfuse 映射, eval gate |
| **D5** | 治理/安全/外部通道 | `error_type`, dev-only 透传闸门 |

---

## 2. 系统架构

详见 [`docs/architecture.md`](./docs/architecture.md) 完整架构图与模块说明。

```
┌─────────────────────────────────────────────────────────────┐
│                        User / Entry                          │
│              (CLI / API / Telegram / Cursor)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator Layer                       │
│              (LangGraph K-1/K-2, context_entry)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agents Layer                            │
│         (Planner → Executor → Reviewer + Handoffs)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Tool Layer  │ │Knowledge │ │ Observability│
│ (skills/run) │ │ (RAG/DB) │ │ (trace/eval) │
└──────────────┘ └──────────┘ └──────────────┘
```

---

## 3. 安装方式

### 3.1 环境要求

- Python 3.10+
- Windows / Linux / macOS
- PostgreSQL (可选，用于 Data Vault)
- Qdrant (可选，用于向量检索)

### 3.2 快速启动

```powershell
# 1. 进入项目目录（战車根；路径见 Master_Map.json）
cd <repo-root>

# 2. 复制环境变量模板
copy .env.example .env
# 编辑 .env 填入你的 API Keys

# 3. 进入主舱（监控/工厂主线）
. .\04_Workflows\Enter-Main.ps1

# 4. 运行密钥盲测
python .\04_Workflows\_smoke_test_keys.py
```

### 3.3 双舱结构

| 舱室 | 路径 | 用途 | 主要套件 |
|------|------|------|----------|
| **Main** | `01_Environments/python_venvs/gov_main` | 工厂主线、监控、Telegram | pydantic, PyYAML, watchdog, tenacity |
| **Agency** | `01_Environments/python_venvs/gov_agency` | CrewAI 任务、向量库、API | crewai, chromadb, fastapi, uvicorn |
| **Core** | `01_Environments/python_venvs/gov_core_system` | LangGraph 编排、企业级补强 | langgraph, langchain |

---

## 4. 启动方式

### 4.1 主舱常用指令

```powershell
# 一键战路（体检→登录→精炼→报告）
.\04_Workflows\Launch-Warpath.ps1 -WaveN 100

# 启动 Telegram 监听
.\04_Workflows\Start-TelegramListener.ps1

# 双舱体检
python .\04_Workflows\_doctor_main_cabin.py
python .\04_Workflows\_doctor_agency_cabin.py
```

### 4.2 API 模式

```powershell
# 进入 Core 舱
cd 01_Environments\python_venvs\gov_core_system
.\Scripts\activate

# 启动 FastAPI
python app_api.py
# 默认地址: http://127.0.0.1:8000
```

### 4.3 测试验证

```powershell
# 核心单元测试
python -m pytest tests/test_context_entry.py -v
python -m pytest tests/test_langgraph_flow_k1.py -v
python -m pytest tests/test_eval_gate.py -v
```

---

## 5. 环境变量说明

复制 `.env.example` 为 `.env` 并配置：

### 5.1 必填项（业务 Happy Path）

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 连接 | `postgresql://user:pass@localhost:5432/db` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-...` |

### 5.2 基础设施（选填）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `QDRANT_URL` | 向量数据库地址 | `http://127.0.0.1:6333` |
| `OPENAI_EMBED_MODEL` | 嵌入模型 | `text-embedding-3-small` |

### 5.3 功能包开关（企业级补强）

| 变量 | 功能 | 默认 |
|------|------|------|
| `GOV_CORE_OBSERVABILITY_V2` | Package A - 可观测性 | `false` |
| `GOV_CORE_BUDGET_ENABLED` | Package B - 预算控制 | `false` |
| `GOV_CORE_STRUCTURED_ERRORS` | Package C - 结构化错误 | `false` |
| `GOV_CORE_RETRY_POLICY_ENABLED` | Package D - 重试/DLQ | `false` |

详见 [`docs/governance.md`](./docs/governance.md) §2 完整环境分层规范。

---

## 6. 主要模块说明

### 6.1 核心编排层

| 模块 | 路径 | 职责 |
|------|------|------|
| `context_entry` | `core/context_entry.py` | H-line 上下文入口合同 |
| `langgraph_flow_k1` | `core/langgraph_flow_k1.py` | K-1 基础编排图 |
| `langgraph_flow_k2` | `core/langgraph_flow_k2.py` | K-2 增强编排（含 handoff/retry） |

### 6.2 观测与评估层

| 模块 | 路径 | 职责 |
|------|------|------|
| `metrics_collector` | `metrics/metrics_collector.py` | D1-D5 指标收集 |
| `logging_adapter` | `observability/logging_adapter.py` | Trace/Span 结构化日志 |
| `eval_gate` | `observability/eval_gate.py` | P+ 评估闸门 |

### 6.3 技能层（J-line）

| 模块 | 路径 | 职责 |
|------|------|------|
| `skill_retrieve` | `skills/example_skill_retrieve.py` | Metrics-aware 检索技能 |
| `skill_answer` | `skills/example_skill_answer.py` | Metrics-aware 回答技能 |

### 6.4 多 Agent 调度

| 模块 | 路径 | 职责 |
|------|------|------|
| `base_agent` | `agents/base_agent.py` | Agent 基础类与角色定义 |
| `orchestration` | `docs/orchestration/` | Cursor-Orchestrator 工作流 |

---

## 7. 可观测性 / 测试 / 索引入口

### 7.1 可观测性

| 入口 | 说明 |
|------|------|
| `observability/logging_adapter.py` | Trace/Span 结构化日志 API |
| `observability/eval_gate.py` | 任务记录评估闸门 |
| `metrics/metrics_schema.json` | 指标 Schema 定义 |

### 7.2 测试

| 测试集 | 命令 |
|--------|------|
| **PR smoke（推荐）** | `python 04_Workflows/_core_agent_smoke.py --tier PR` |
| 测试制度全文 | [`docs/testing.md`](./docs/testing.md) |
| Context Entry | `python -m unittest tests.test_context_entry -v` |
| LangGraph K-1 | `python -m unittest tests.test_langgraph_flow_k1 -v` |
| Eval Gate | `python -m unittest tests.test_eval_gate -v` |
| Skills | `python -m unittest tests.test_skills_metrics -v` |

### 7.3 文档索引

| 文档 | 内容 |
|------|------|
| [`docs/architecture.md`](./docs/architecture.md) | 系统架构与 Mermaid 图 |
| [`docs/governance.md`](./docs/governance.md) | 治理规范（分支/提交/日志/命名） |
| [`docs/orchestration/README.md`](./docs/orchestration/README.md) | 多 Agent 调度使用说明 |
| [`AGENTS.md`](./AGENTS.md) | 副官接战守则 |
| [`00_master_plan.md`](./00_master_plan.md) | 企业化补强总蓝图 |

---

## 8. 快速链接

- **主计划**: [`00_master_plan.md`](./00_master_plan.md)
- **接战守则**: [`AGENTS.md`](./AGENTS.md)
- **任务看板**: [`docs/orchestration/TASK_BOARD.md`](./docs/orchestration/TASK_BOARD.md)
- **架构文档**: [`docs/architecture.md`](./docs/architecture.md)
- **治理规范**: [`docs/governance.md`](./docs/governance.md)

---

## 9. 许可证

内部治理框架 - 按 `HARNESS_CONSTITUTION.md` 与 `ENGINEERING_CONTRACT.md` 执行。

---

> **致新接战的副官**: 先读 `AGENTS.md` §初始化校准，再读 `docs/orchestration/README.md` 了解多 Agent 调度流程。
