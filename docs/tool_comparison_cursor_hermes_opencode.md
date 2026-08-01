# 三工具能力對比：Cursor / Hermes Agent / OpenCode

> **目的**：幫你理解三個工具的定位差異，決定何時用哪個

---

## 核心定位

| 工具 | 定位 | 最適合的場景 |
|------|------|--------------|
| **Cursor** | AI IDE（編輯器 + Copilot） | 寫程式、快速迭代、視覺化除錯 |
| **Hermes Agent** | 多平台 Agent Framework | 自動化、跨平台訊息、長時間任務、記憶 + 技能 |
| **OpenCode** | CLI 編碼代理 | PR review、長時間獨立編碼、worktree 隔離 |

---

## 能力對比表

| 能力 | Cursor | Hermes Agent | OpenCode |
|------|--------|--------------|----------|
| **程式碼編輯** | ✅ 核心（IDE + AI） | ⚠️ 透過 terminal/file 工具 | ✅ 核心（CLI + TUI） |
| **自動補全** | ✅ Tab 補全 | ❌ | ❌ |
| **多模型支援** | ✅ Claude / GPT / DeepSeek | ✅ 20+ providers | ✅ 多模型 |
| **Terminal 整合** | ✅ 內建 | ✅ 內建 | ✅ 內建 |
| **Git 整合** | ✅ 內建 | ⚠️ 透過 terminal | ✅ 內建 |
| **PR Review** | ⚠️ 手動 | ⚠️ 透過 gh CLI | ✅ 內建 `opencode pr` |
| **Web / Browser** | ❌ | ✅ browser 工具（Chromium、Camofox） | ❌ |
| **訊息平台** | ❌ | ✅ 20+ 平台（Telegram、Discord、Slack...） | ❌ |
| **持久記憶** | ❌（每 session 獨立） | ✅ memory + user profile | ❌ |
| **技能系統** | ⚠️ `.cursorrules` | ✅ skills（可跨 session 學習） | ❌ |
| **Cron 排程** | ❌ | ✅ cron 工具 | ❌ |
| **Webhook** | ❌ | ✅ webhook 工具 | ❌ |
| **MCP 客戶端** | ⚠️ 實驗性 | ✅ 內建 MCP 客戶端 | ⚠️ 有限 |
| **多 Agent 協作** | ⚠️ Composer 模式 | ✅ delegate_task + kanban | ❌ |
| **Worktree 隔離** | ❌ | ⚠️ 透過 terminal | ✅ 內建 |
| **TTY / PTY** | ❌（IDE 環境） | ✅ pty 模式 | ✅ TUI |
| **成本控制** | ⚠️ 訂閱制 | ✅ `--max-budget-usd` | ✅ `--max-budget-usd` |

---

## 實際使用場景

### 用 Cursor 當...

- 你需要**快速迭代**程式碼（改一行、跑測試、再改）
- 你需要**視覺化除錯**（斷點、變數監控）
- 你需要**自動補全**（Tab 補全省時間）
- 你在**探索新專案**（游標懸停看定義）

### 用 Hermes Agent 當...

- 你需要**自動化長時間任務**（cron、webhook）
- 你需要**跨平台訊息**（Telegram、Discord、Slack）
- 你需要**持久記憶**（記住用戶偏好、環境設定）
- 你需要**技能系統**（跨 session 學習、複用流程）
- 你需要**多 Agent 協作**（orchestrator + workers）
- 你需要**Web 自動化**（爬蟲、截圖、填表）

### 用 OpenCode 當...

- 你需要**PR Review**（`opencode pr 42`）
- 你需要**長時間獨立編碼**（背景執行、檢查進度）
- 你需要**Worktree 隔離**（多任務不衝突）
- 你喜歡**CLI / TUI** 體驗

---

## 在「多智囊團」架構中的角色

```
你（人類）
   │
   ├── Cursor ──────► 快速原型、視覺化除錯
   │
   ├── Hermes Agent ─► 自動化、跨平台、記憶 + 技能
   │                    （你現在這個）
   │
   └── OpenCode ────► PR review、長時間獨立編碼
```

### 智囊團路由建議

| 任務類型 | 建議工具 |
|----------|----------|
| `prompt_design` | Cursor（快速迭代） |
| `workflow_design` | Hermes Agent（LangGraph 整合） |
| `external_integration` | Hermes Agent（MCP + browser） |
| `tracing_setup` | Hermes Agent（observability） |
| `terminal_automation` | Hermes Agent（terminal 工具） |
| `model_selection` | 三者皆可（都有多模型支援） |
| `code_review` | OpenCode（`opencode pr`） |
| `end_to_end_pipeline` | Hermes Agent（協調多智囊團） |

---

## 典型協作模式

### 模式 1：Cursor → Hermes Agent → OpenCode

```
Cursor 快速原型
   ↓
Hermes Agent 整合自動化
   ↓
OpenCode PR review
```

### 模式 2：Hermes Agent 協調

```
Hermes Agent
   ├── delegate_task → OpenCode（編碼）
   ├── delegate_task → Cursor（快速迭代）
   └── cron / webhook（自動化）
```

### 模式 3：並行任務

```
Cursor ────► Task A（視覺化除錯）
Hermes ────► Task B（自動化 + 記憶）
OpenCode ──► Task C（PR review）
```

---

## 你目前的實際使用

| 工具 | 你拿來做什麼 |
|------|--------------|
| **Cursor** | 大唐三省六部專案開發、快速迭代 |
| **Hermes Agent** | Telegram 對話、知識庫查詢、自動化 |
| **OpenCode** | PR review、長時間編碼任務 |

---

## 建議：何時呼叫誰

| 你說... | 建議用 |
|---------|--------|
| 「幫我快速改一下這段 code」 | Cursor |
| 「幫我自動化這個流程」 | Hermes Agent |
| 「幫我 review 這個 PR」 | OpenCode |
| 「幫我記住這個設定」 | Hermes Agent |
| 「幫我排程每週跑一次」 | Hermes Agent |
| 「幫我在 Telegram 回覆」 | Hermes Agent |
| 「幫我隔離這個任務避免衝突」 | OpenCode |

---

*本對比基於 2026-07-24 的工具版本，可能隨時間變化。*