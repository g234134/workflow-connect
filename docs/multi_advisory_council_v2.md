# 多智囊團 + 三工具協作架構 v2

> **決定**：以 Hermes Agent 為核心，協調 Cursor / OpenCode
>
> **核心原則**：
> - Hermes Agent = 指揮官（記憶 + 技能 + 自動化）
> - Cursor = 快速迭代工具（IDE + 自動補全）
> - OpenCode = PR review 工具（worktree 隔離）

---

## 架構圖

```
你（人類）
   │ 下指令
   ▼
┌─────────────────────────────────────────────────────────────┐
│  Hermes Agent（指揮官）                                      │
│  記憶 + 技能 + 自動化 + 跨平台 + 多 Agent 協作               │
└─────────────────────────────────────────────────────────────┘
   │ 自動路由
   ├──────────────────────┬──────────────────────┐
   ▼                      ▼                      ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Cursor      │   │  OpenCode    │   │  六大智囊團   │
│  快速迭代    │   │  PR review   │   │  LC/LG/MCP/  │
│  IDE + 補全  │   │  worktree    │   │  OBS/TOOL/MOD│
└──────────────┘   └──────────────┘   └──────────────┘
```

---

## Hermes Agent 的核心職責

| 職責 | 工具 / 技能 |
|------|------------|
| **記憶** | `memory` 工具（用戶偏好、環境設定） |
| **技能** | `skills` 系統（跨 session 學習） |
| **自動化** | `cron` / `webhook` / `delegate_task` |
| **跨平台** | 20+ 平台（Telegram、Discord、Slack...） |
| **協調** | `delegate_task` 呼叫 Cursor / OpenCode |
| **多智囊團路由** | `advisory_council_router.py` |

---

## 什麼時候呼叫 Cursor

| 條件 | 呼叫方式 |
|------|----------|
| 需要快速迭代程式碼 | `delegate_task` → `claude-code` 技能 |
| 需要視覺化除錯 | `delegate_task` → `claude-code` 技能 |
| 需要自動補全 | 用戶手動切換到 Cursor |

**示例**：

```python
# Hermes Agent 呼叫 Cursor（透過 claude-code 技能）
delegate_task(
    goal="Refactor the auth module to use JWT tokens",
    context="大唐三省六部專案",
    toolsets=["claude-code"]
)
```

---

## 什麼時候呼叫 OpenCode

| 條件 | 呼叫方式 |
|------|----------|
| 需要 PR Review | `delegate_task` → `opencode` 技能 |
| 需要長時間獨立編碼 | `delegate_task` → `opencode` 技能 |
| 需要 worktree 隔離 | `delegate_task` → `opencode` 技能 |

**示例**：

```python
# Hermes Agent 呼叫 OpenCode
delegate_task(
    goal="Review PR #42 for security issues",
    context="大唐三省六部專案",
    toolsets=["opencode"]
)
```

---

## 六大智囊團路由

### 智囊團清單

| 代碼 | 名稱 | 職責 |
|------|------|------|
| LC | LangChain | 應用層框架 |
| LG | LangGraph | 編排層圖結構 |
| MCP | MCP Servers | 外部工具整合 |
| OBS | Observability | LangSmith / LangFuse |
| TOOL | Tool Chain | Terminal / Browser |
| MOD | Model Router | 模型選型 |

### 路由邏輯

```python
# advisory_council_router.py

def route_to_advisory_council(task: str) -> str:
    """
    自動路由到對應智囊團
    """
    if "langchain" in task.lower():
        return "LC"
    elif "langgraph" in task.lower():
        return "LG"
    elif "mcp" in task.lower():
        return "MCP"
    elif "observability" in task.lower() or "langsmith" in task.lower():
        return "OBS"
    elif "terminal" in task.lower() or "browser" in task.lower():
        return "TOOL"
    elif "model" in task.lower() or "llm" in task.lower():
        return "MOD"
    else:
        return "auto"  # 自動判斷
```

---

## 典型工作流

### 工作流 1：快速迭代

```
你 → Hermes Agent → Cursor（快速迭代）→ 結果
```

### 工作流 2：PR Review

```
你 → Hermes Agent → OpenCode（PR review）→ 結果
```

### 工作流 3：多智囊團協作

```
你 → Hermes Agent → 六大智囊團（專業分工）→ 結果
```

### 工作流 4：混合模式

```
你 → Hermes Agent
    │
    ├── Cursor（快速迭代）
    │
    ├── OpenCode（PR review）
    │
    └── 六大智囊團（專業分工）
```

---

## 優勢

| 優勢 | 說明 |
|------|------|
| **持久記憶** | Hermes Agent 記住你的偏好、環境設定 |
| **技能系統** | 跨 session 學習、複用流程 |
| **自動化** | cron / webhook / delegate_task |
| **跨平台** | 20+ 平台 |
| **協調能力** | 呼叫 Cursor / OpenCode / 六大智囊團 |

---

## 成本分析

| 工具 | 成本 | 用量 |
|------|------|------|
| **Cursor** | 付費會員 | 高 |
| **Hermes Agent** | 免費（OmniRoute） | 中 |
| **OpenCode** | 待確認 | 低 |

---

## 相關文檔

- `D:/大唐三省六部/docs/tool_comparison_cursor_hermes_opencode.md` — 三工具對比
- `D:/大唐三省六部/core/advisory_council_router.py` — 智囊團路由實作
- `D:/大唐三省六部/tests/test_advisory_council_router.py` — 智囊團路由測試

---

*本架構決定於 2026-07-24*