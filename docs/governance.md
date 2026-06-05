# 治理规范文档

> **版本**: Phase 1 Governance Baseline  
> **更新**: 2026-06-05  
> **权威**: `HARNESS_CONSTITUTION.md` > `ENGINEERING_CONTRACT.md` > 本文档

---

## 1. 代码管理规范

### 1.1 分支命名

```
<类型>/<简短描述>-<日期或序号>
```

| 类型 | 用途 | 示例 |
|------|------|------|
| `feature/` | 新功能 | `feature/k2-monitoring-graph-20260605` |
| `fix/` | Bug 修复 | `fix/retry-count-race-20260605` |
| `docs/` | 文档更新 | `docs/governance-phase1-20260605` |
| `refactor/` | 重构 | `refactor/skill-runner-cleanup-20260605` |
| `hotfix/` | 紧急修复 | `hotfix/api-timeout-20260605` |

**规则**:
- 使用小写字母和连字符
- 日期格式: `YYYYMMDD`
- 禁止直接推送 `main` 分支
- PR 必须通过 CI 检查（`eval-gate-ci.yml`）

### 1.2 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(metrics): add memory_hit_rate tracking` |
| `fix` | Bug 修复 | `fix(logging): trace_id propagation in nested spans` |
| `docs` | 文档更新 | `docs(arch): add mermaid diagrams` |
| `refactor` | 代码重构 | `refactor(skills): extract skill_runner base` |
| `test` | 测试相关 | `test(k2): add handoff node coverage` |
| `chore` | 构建/工具 | `chore(ci): add eval_gate workflow` |
| `gov` | 治理更新 | `gov(env): add staging env template` |

**范围 (Scope)**:
- `core` - 核心编排
- `agents` - Agent 层
- `skills` - 技能层
- `metrics` - 指标收集
- `obs` - 可观测性
- `docs` - 文档
- `gov` - 治理
- `infra` - 基础设施

**示例**:
```
feat(core): add K-2 monitoring graph (L0 only)

- Implement run_monitoring_graph() with summarize→analyze→recommend→finalize
- Add GOV_MONITORING_GRAPH_ENABLED env flag (default 0)
- Expose via ibridge_v0.monitoring_graph (observability only)

Refs: M-GOV-001
```

---

## 2. 环境分层

### 2.1 环境定义

| 环境 | 用途 | 数据来源 | 部署位置 |
|------|------|----------|----------|
| **local** | 本地开发 | Mock / 本地 DB | 开发者机器 |
| **dev** | 功能验证 | 脱敏样本 | 本地 Docker |
| **staging** | 集成测试 | 生产镜像 | 内网服务器 |
| **prod** | 生产运行 | 生产数据 | 生产集群 |

### 2.2 环境变量模板

```bash
# ========================================
# 基础配置 (所有环境)
# ========================================
# API Keys
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
TELEGRAM_BOT_TOKEN=...:...

# Database
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
QDRANT_URL=http://HOST:6333

# ========================================
# 功能包开关 (企业级补强)
# ========================================
# Package A - Observability (默认: false)
GOV_CORE_OBSERVABILITY_V2=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# Package B - Budget (默认: false)
GOV_CORE_BUDGET_ENABLED=false
GOV_CORE_DAILY_BUDGET_USD=50.0
GOV_CORE_WEEKLY_BUDGET_USD=200.0

# Package C - Structured Errors (默认: false)
GOV_CORE_STRUCTURED_ERRORS=false

# Package D - Retry/DLQ (默认: false)
GOV_CORE_RETRY_POLICY_ENABLED=false
GOV_CORE_RETRY_MAX_ATTEMPTS=3
GOV_CORE_DLQ_ENABLED=false

# ========================================
# 工作流配置
# ========================================
GOV_CORE_CHECKPOINTER=auto
GOV_CORE_JSON_MIRROR=1

# ========================================
# 开发环境专用 (dev only)
# ========================================
DEV_ALLOW_ALL_ORIGINS=true
ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500

# K-2 Monitoring Graph (默认: 0)
GOV_MONITORING_GRAPH_ENABLED=0

# API 观察闸门 (默认: 0)
GOV_CORE_API_EXPOSE_MONITORING_GRAPH=0
GOV_CORE_API_EXPOSE_IBRIDGE=0
```

### 2.3 环境特定文件

| 文件 | local | dev | staging | prod |
|------|-------|-----|---------|------|
| `.env` | ✅ | ✅ | ✅ | ✅ |
| `DEV_ALLOW_ALL_ORIGINS` | `true` | `true` | `false` | `false` |
| `GOV_MONITORING_GRAPH_ENABLED` | `1` | `1` | `0` | `0` |
| `GOV_CORE_API_EXPOSE_*` | `1` | `1` | `0` | `0` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARN` | `WARN` |

---

## 3. API Key 管理规范

### 3.1 密钥来源

**唯一来源**: `01_Environments/.env`

```python
# 正确方式
from gov_paths import get_secret
api_key = get_secret("OPENAI_API_KEY")
```

### 3.2 使用禁令

| 禁令 | 违规示例 | 正确做法 |
|------|----------|----------|
| 禁止硬编码 | `API_KEY = "sk-..."` | 从 `.env` 读取 |
| 禁止打印原文 | `print(api_key)` | 打印 `[OK]`/`[FAILED]` |
| 禁止提交密钥 | `.env` 入 git | `.env` 在 `.gitignore` |
| 禁止日志泄露 | `logger.info(f"key={api_key}")` | 只记录 key 存在性 |

### 3.3 密钥验证

```powershell
# 标准验证脚本
python .\04_Workflows\_smoke_test_keys.py
```

**输出格式**:
```
[OK]    openai_api_key     HTTP 200
[OK]    groq_api_key       HTTP 200
[OK]    telegram_bot_token HTTP 200
```

### 3.4 密钥轮换

- **频率**: 建议每月一次
- **记录**: 更新 `secrets_status.rotated_at` in `Master_Map.json`
- **紧急**: 若怀疑泄露，立即撤销并重新生成

---

## 4. 日志规范

### 4.1 日志级别

| 级别 | 用途 | 目标环境 |
|------|------|----------|
| `DEBUG` | 开发调试、详细 trace | local/dev |
| `INFO` | 关键事件、业务里程碑 | all |
| `WARNING` | 非致命异常、降级 | all |
| `ERROR` | 可恢复错误、需关注 | all |
| `CRITICAL` | 系统故障、立即处理 | all |

### 4.2 结构化日志字段

**标准字段**:
```json
{
  "timestamp": "2026-06-05T12:34:56.789Z",
  "level": "INFO",
  "logger": "gov_core.observability",
  "event": "trace_start",
  "trace_schema_version": "agent-metrics-v1",
  "trace_id": "uuid-trace-id",
  "task_id": "uuid-task-id",
  "agent_name": "ask_pipeline",
  "message": "..."
}
```

**扩展字段** (依 event 类型):
- `trace_start`: `agent_run`, `metadata`
- `span_start/end`: `span_id`, `span_name`, `success`
- `log_metric`: `metric`, `value`, `unit`
- `error`: `error_type`, `message`

### 4.3 日志闸门

| 数据类型 | 允许记录 | 禁止记录 |
|----------|----------|----------|
| 任务 ID | ✅ | - |
| Trace ID | ✅ | - |
| Agent 名称 | ✅ | - |
| 步骤名称 | ✅ | - |
| Token 数量 | ✅ | - |
| API Key | ❌ | 任何部分 |
| 用户隐私数据 | ❌ | PII/PHI |
| 完整 Prompt | ⚠️ | 超过 1KB 需摘要 |

---

## 5. ID 命名规范

### 5.1 ID 类型定义

| ID 类型 | 格式 | 示例 | 生成方式 |
|---------|------|------|----------|
| **trace_id** | UUID v4 (hex) | `a1b2c3d4e5f6...` | `uuid.uuid4().hex` |
| **task_id** | UUID v4 (hex) | `f6e5d4c3b2a1...` | `uuid.uuid4().hex` |
| **session_id** | `sess_<timestamp>_<random>` | `sess_1717580096_a1b2` | `sess_{int(time)}_{4char}` |
| **run_id** | `run_<date>_<seq>` | `run_20260605_001` | 递增序列 |
| **span_id** | 12-char hex | `a1b2c3d4e5f6` | `uuid.uuid4().hex[:12]` |
| **job_id** | `job_<type>_<uuid>` | `job_wave_a1b2c3d4...` | `job_{type}_{uuid}` |

### 5.2 ID 使用场景

```python
# Trace ID - 跨全链路的调用链标识
with agent_run_trace("ask_pipeline", trace_id=trace_id) as ctx:
    # Span ID - 单个步骤/子 Agent 标识
    start_span(ctx, "retrieve")
    
# Task ID - 单个任务的标识
collector.start_task(task_id, agent_name)

# Session ID - 用户会话标识
session_id = f"sess_{int(time.time())}_{uuid.uuid4().hex[:4]}"
```

### 5.3 ID 传递规范

```python
# HTTP Header 传递
X-Trace-Id: <trace_id>
X-Task-Id: <task_id>
X-Session-Id: <session_id>

# Context 传递
context = {
    "trace_id": trace_id,
    "task_id": task_id,
    "session_id": session_id,
}
```

---

## 6. Agent / Tool / Workflow 命名规范

### 6.1 Agent 命名

```
<领域>_<职责>_<版本>
```

| Agent | 命名 | 职责 |
|-------|------|------|
| 主 Planner | `core_planner_v1` | 任务分解 |
| 主 Executor | `core_executor_v1` | 执行检索/调用 |
| 主 Reviewer | `core_reviewer_v1` | 结果审核 |
| 监控执行器 | `monitoring_executor_v0` | 只读监控查询 |
| 代码清洗 | `code_cleaner_throttle_v2` | 代码精炼 |
| Groq 恢复 | `groq_hybrid_recovery_v1` | 配额管理 |

### 6.2 Tool/Skill 命名

```
skill_<动词>_<对象>[_<版本>]
run_<动作>_<目标>
```

| Skill | 命名 | 模式 |
|-------|------|------|
| 检索 | `skill_retrieve_v1` | `run_skill_retrieve()` |
| 回答 | `skill_answer_v1` | `run_skill_answer()` |
| 代码搜索 | `skill_code_search_v0` | `run_skill_code_search()` |

### 6.3 Workflow 命名

```
<线>-<编号>_<描述>_<版本>
```

| Workflow | 命名 | 说明 |
|----------|------|------|
| Ask 主线 | `ask-pipeline-v1` | I-line 主流程 |
| K-1 图 | `langgraph-k1-v1` | K-1 基础编排 |
| K-2 图 | `langgraph-k2-v0.2` | K-2 增强编排 |
| H 线入口 | `context-entry-v0.1` | 上下文入口合同 |
| J 线技能 | `skills-v0.1` | Metrics-aware skills |
| P+ 评估 | `eval-gate-v0` | 任务评估闸门 |

### 6.4 路由/子 Agent 命名

```python
# subagents/context_routing.py
ROUTE_ASK = "ask"                           # 标准问答
ROUTE_MONITORING = "monitoring"             # 监控查询
ROUTE_HUMAN_IN_THE_LOOP = "human-in-the-loop"  # 人工介入
```

---

## 7. Error Code / Exception 规范

### 7.1 Error Code 结构

```
<领域>_<具体错误>
```

| 领域 | 代码示例 | 说明 |
|------|----------|------|
| Health | `HEALTH_FAILED` | 健康检查失败 |
| Ingest | `INGEST_FAILED` | 数据摄入失败 |
| Verify | `VERIFY_FAILED` | 验证失败 |
| Retrieve | `RETRIEVE_FAILED` | 检索失败 |
| Answer | `ANSWER_FAILED` | 回答生成失败 |
| Pipeline | `PIPELINE_FAILED` | 管道执行失败 |
| Schema | `SCHEMA_VALIDATION_FAILED` | Schema 验证失败 |
| Business | `BUSINESS_VALIDATION_FAILED` | 业务规则验证失败 |
| JSON | `MALFORMED_JSON` | JSON 解析失败 |
| Empty | `EMPTY_PAYLOAD` | 空负载 |
| Human | `HUMAN_REJECTED` | 人工拒绝 |
| Unknown | `UNKNOWN` | 未知错误 |

### 7.2 结构化错误格式

```json
{
  "schema_version": "gov-core-error-v1",
  "code": "RETRIEVE_FAILED",
  "message": "Qdrant query timeout after 30s",
  "node": "retrieve_node",
  "retryable": true,
  "details": {
    "error_category": "infra",
    "error_code": "RETRIEVE_FAILED_INFRA",
    "latency_ms": 30000,
    "qdrant_status": "timeout"
  }
}
```

### 7.3 Error Taxonomy（分类）

| Category | 说明 | 自动处理 |
|----------|------|----------|
| `infra` | 基础设施错误（DB/API 故障） | 可重试 |
| `llm` | LLM 调用错误（Rate limit/内容过滤） | 可重试/降级 |
| `input` | 输入错误（格式/校验） | 不可重试 |
| `business` | 业务规则错误 | 不可重试 |
| `unknown` | 未知错误 | 人工介入 |

### 7.4 Exception 类层次

```python
# core/errors.py
class GovCoreError(Exception):
    """基础错误，携带结构化错误信息"""
    def __init__(self, structured_error: dict):
        self.structured_error = structured_error
        self.retryable = structured_error.get("retryable", False)

class RetryExhaustedError(GovCoreError):
    """重试次数耗尽"""
    pass

class HumanRejectedError(GovCoreError):
    """人工拒绝"""
    pass
```

---

## 8. 配置管理

### 8.1 配置层级

```
默认值 → 环境变量 → 配置文件 → 代码参数
```

### 8.2 配置文件命名

| 文件 | 用途 | 格式 |
|------|------|------|
| `.env` | 密钥与环境 | Key=Value |
| `config.yaml` | 功能配置 | YAML |
| `model_registry.yaml` | 模型注册 | YAML |
| `factory_pipeline.yaml` | 工厂管道 | YAML |
| `metrics_schema.json` | 指标 Schema | JSON |

### 8.3 配置读取优先级

```python
# core/config_loader.py 示例
def get_config(key: str, default=None):
    # 1. 环境变量
    if env_val := os.getenv(key):
        return env_val
    # 2. 配置文件
    if config_val := _load_yaml().get(key):
        return config_val
    # 3. 默认值
    return default
```

---

## 9. 文档规范

### 9.1 文档目录结构

```
docs/
├── README.md                 # 文档总入口
├── architecture.md           # 架构文档
├── governance.md             # 治理规范 (本文档)
├── orchestration/            # 多 Agent 调度
│   ├── README.md
│   ├── AGENT_RULES.md
│   ├── TASK_BOARD.md
│   └── ...
└── api/                      # API 文档 (可选)
    └── openapi.yaml
```

### 9.2 文档模板

**新模块文档必须包含**:
1. 目的/场景
2. 接口定义
3. 使用示例
4. 配置说明
5. 相关文档链接

---

## 10. 合规检查清单

### 10.1 新增代码检查

- [ ] 分支命名符合规范
- [ ] 提交信息符合规范
- [ ] 未硬编码密钥或路径
- [ ] 使用 `build_rooted_context()` 入口
- [ ] Agent 使用 `agent_run_trace()` 包裹
- [ ] Skill 经过 `skill_runner` 执行
- [ ] 错误使用结构化格式
- [ ] ID 使用标准命名和格式
- [ ] 日志使用结构化输出
- [ ] 未打印密钥原文

### 10.2 新增 Agent 检查

- [ ] 命名符合 `<领域>_<职责>_<版本>`
- [ ] 声明服务的 D 维度
- [ ] 实现 `run()` 或 `invoke()` 方法
- [ ] 返回结构化 `dict` 含 `ok`, `message`
- [ ] 接入 `metrics_collector`
- [ ] 文档在 `docs/orchestration/` 或 `agents/README.md`

### 10.3 新增 Skill 检查

- [ ] 命名符合 `skill_<动词>_<对象>`
- [ ] 经过 `run_metrics_aware_skill()` 注册
- [ ] 自动挂钩 retry/metrics/trace
- [ ] 文档在 `skills/skills_contract.md`

---

## 11. 相关文档

- [`HARNESS_CONSTITUTION.md`](../HARNESS_CONSTITUTION.md) - 宪法/最高规范
- [`ENGINEERING_CONTRACT.md`](../04_Workflows/ENGINEERING_CONTRACT.md) - 工程合约
- [`AGENTS.md`](../AGENTS.md) - 副官接战守则
- [`docs/architecture.md`](./architecture.md) - 系统架构
