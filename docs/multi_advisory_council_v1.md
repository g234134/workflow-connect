# 多智囊團架構（Multi-Advisory Council）

> **版本**：v1.0 · 2026-07-24  
> **來源**：課程技術架構圖 OCR + 大唐三省六部現有四角色對齊  
> **目的**：定義六個專業智囊團的職責邊界、路由規則與與現有 Orchestrator/Implementer/Reviewer/Scribe 的整合方式

---

## §1 六大智囊團定義

| # | 智囊團 | 代號 | 核心模組 | 職責一句話 |
|---|--------|------|----------|-----------|
| 1 | **LangChain 智囊團** | `LC` | prompts, messages, runnable, output_parses, tools, memory, mcp, agents | prompt engineering、tool 接線、agent 行為設計 |
| 2 | **LangGraph 智囊團** | `LG` | graph, state, node, edge | workflow 編排、狀態機設計、graph 優化 |
| 3 | **MCP 智囊團** | `MCP` | stdio, sse, streamable_http, mcp市場 | MCP server/client 接線、協議選型、市場整合 |
| 4 | **Observability 智囊團** | `OBS` | LangSmith, Langfuse, tracing, metrics | 追蹤、評估、SLO 監控、shadow-advisory |
| 5 | **Tool 智囊團** | `TOOL` | Terminal, PowerShell, Chrome DevTools, DB, File | 基礎工具鏈、自動化腳本、外部系統整合 |
| 6 | **Model 智囊團** | `MOD` | 通義千問, DeepSeek, Claude 4, GPT-4, Ollama | 模型選型、路由策略、成本優化、本地部署 |

---

## §2 與現有角色映射

```
現有四角色（Phase 4 Contract）          六大智囊團（本檔）
─────────────────────────────          ─────────────────
Orchestrator (O)  ──路由──→  任何智囊團
Implementer (B)   ──施工──→  LC / LG / MCP / TOOL
Reviewer (C)      ──審查──→  OBS（評估指標）+ 原審查流程
Scribe (D)        ──記錄──→  全智囊團通用
```

**路由規則**：
- Orchestrator 依任務類型指派到對應智囊團
- 跨智囊團任務：Orchestrator 拆分 → 多智囊團並行 → 合流審查
- 智囊團內部可自行調用 subagent（依 `.cursor/agents/DISPATCH_GUIDE.md`）

---

## §3 各智囊團詳細定義

### 3.1 LangChain 智囊團 (LC)

**核心模組**：
- `prompts`：prompt template 設計、few-shot、chain-of-thought
- `messages`：message history 管理、system/user/assistant 角色
- `runnable`：Runnable sequence、parallel、branch 編排
- `output_parses`：JSON/Pydantic output parsing、structured output
- `tools`：tool definition、tool calling、tool selection
- `memory`：conversation memory、buffer memory、summary memory
- `mcp`：MCP tool integration via LangChain
- `agents`：agent type 選擇（ReAct, OpenAI Functions, etc.）

**進出項**：
- **輸入**：任務描述 + context payload
- **輸出**：prompt template / tool definition / agent config
- **交接**：→ LG（graph 編排）或 → MCP（外部工具接線）

**對應現有**：`core/coding_agent_router.py`、`core/ask_rag_selector.py`

---

### 3.2 LangGraph 智囊團 (LG)

**核心模組**：
- `graph`：StateGraph 建構、node 定義、edge 路由
- `state`：state schema 設計、state mutation、checkpointing
- `node`：node function 實作、error handling、retry logic
- `edge`：conditional edge、dynamic routing、human-in-the-loop

**進出項**：
- **輸入**：LC 的 agent config + 工具定義
- **輸出**：可執行的 LangGraph graph（`build_k1_graph()` / `build_k2_graph()`）
- **交接**：→ OBS（graph execution tracing）

**對應現有**：`core/langgraph_flow_k1.py`、`core/langgraph_flow_k2.py`、`core/monitoring_graph.py`

---

### 3.3 MCP 智囊團 (MCP)

**核心模組**：
- `stdio`：本地進程通訊、command-line tool 接線
- `sse`：Server-Sent Events、streaming response
- `streamable_http`：HTTP-based MCP transport
- `mcp市場`：community server discovery、registry integration

**進出項**：
- **輸入**：LC 的 tool definition + external system requirements
- **輸出**：MCP server config / client connection
- **交接**：→ TOOL（工具鏈整合）

**對應現有**：`01_Environments/config/mcp/_registry/`、`subagents/`

---

### 3.4 Observability 智囊團 (OBS)

**核心模組**：
- `LangSmith`：trace logging、dataset management、evaluation
- `Langfuse`：open-source tracing、score tracking、prompt management
- `tracing`：span hierarchy、trace context propagation
- `metrics`：custom metrics、SLO tracking、alerting

**進出項**：
- **輸入**：LG graph execution results + tool execution logs
- **輸出**：trace data / evaluation scores / SLO reports
- **交接**：→ Orchestrator（决策依據）

**對應現有**：`core/monitoring_graph.py`（L0 observability）、`observability/`、`metrics/`

**三級治理**（沿用現有）：
- L0 observability（已啟用）
- L1 shadow-advisory（禁 — 需批文）
- L2 SLO gate（禁 — 需批文）

---

### 3.5 Tool 智囊團 (TOOL)

**核心模組**：
- `Terminal`：shell command execution、script automation
- `PowerShell`：Windows-specific automation、system administration
- `Chrome DevTools`：browser automation、web scraping、UI testing
- `DB`：database query、schema management、migration
- `File`：file system operations、knowledge base management

**進出項**：
- **輸入**：LC tool definition + MCP server config
- **輸出**：executed results / file artifacts / DB records
- **交接**：→ OBS（execution tracing）

**對應現有**：`core/infra_health.py`、`core/data_pipeline.py`、`runbooks/`

---

### 3.6 Model 智囊團 (MOD)

**核心模組**：
- `通義千問`：阿里雲百煉大模型、中文優化
- `DeepSeek`：開源模型、code generation
- `Claude 4`：Anthropic、長上下文、tool use
- `GPT-4`：OpenAI、multimodal
- `Ollama`：本地部署、privacy-first

**進出項**：
- **輸入**：LC prompt template + task requirements
- **輸出**：model response + confidence score + cost estimate
- **交接**：→ OBS（model performance tracking）

**路由策略**：
- 成本優先：Ollama → DeepSeek → 通義千問
- 品質優先：Claude 4 → GPT-4 → 通義千問
- 隱私優先：Ollama（本地）→ DeepSeek（開源）
- 中文優先：通義千問 → DeepSeek → Claude 4

**對應現有**：`core/coding_agent_router.py`（route agent vs cursor）

---

## §4 整合流程

```
尚書省指令
    ↓
Orchestrator (O)
    ↓ 分析任務類型
    ├─── LC (prompt/tool/agent 設計)
    │       ↓
    │    LG (graph 編排)
    │       ↓
    │    OBS (tracing + eval)
    │       ↓
    ├─── MCP (外部工具接線)
    │       ↓
    │    TOOL (執行)
    │       ↓
    │    OBS (execution log)
    │       ↓
    └─── MOD (model 選型 + inference)
            ↓
         OBS (performance tracking)
            ↓
         Orchestrator (合流決策)
            ↓
         Reviewer (C) 審查
            ↓
         Scribe (D) 記錄
            ↓
         尚書省收口
```

---

## §5 與現有系統對齊

| 現有組件 | 對應智囊團 | 整合方式 |
|----------|-----------|----------|
| `langgraph_flow_k1.py` | LG | K1 graph = LG 核心實作 |
| `langgraph_flow_k2.py` | LG | K2 graph = LG 升級版 |
| `monitoring_graph.py` | OBS | L0 observability graph |
| `coding_agent_router.py` | MOD + LC | model 選型 + agent routing |
| `infra_health_agent.py` | TOOL | 基礎設施健康檢查 |
| `data_pipeline_agent.py` | TOOL + LC | 資料管線 + tool 接線 |
| `rag_query_agent.py` | LC + MOD | RAG retrieval + model inference |
| `orchestrator_agent.py` | 全部 | Governance orchestrator |
| `k2_merge_adapter.py` | LG + OBS | shadow merge + eval |
| `k2_prod_shadow_worker.py` | OBS | prod shadow spool |

---

## §6 下一步

1. **驗證整合**：確認六大智囊團與現有四角色（O/B/C/D）的 routing 不衝突
2. **實作路由**：在 `core/` 下建 `advisory_council_router.py`，依任務類型分派
3. **Observability 升級**：L0 → L1 shadow-advisory（需尚書省批文）
4. **Model routing**：建 `model_router.py`，實現成本/品質/隱私三策略
5. **MCP 市場整合**：掃描 community MCP servers，自動 discover + register

---

*本檔為多智囊團架構 SSOT；個別智囊團實作細節見對應 `core/` 模組文檔。*
