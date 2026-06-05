# services / agentmemory

## 用途（尚書省 · 獨立服務）

本目錄為 **Agentmemory** 記憶服務的 Docker 部署位。以 `docker compose` 獨立運行，與暗部 FastAPI／LangGraph 進程分離。健康檢查通過後，方可考慮以 MCP URL（如 `http://127.0.0.1:8081/mcp`）對接 Cursor——**正式工作流啟用前僅預留參考**。

## 禁則

**不得放暗部 venv 相關檔案**（含 `gov_core_system` 的 Python 依賴、venv、或修改暗部內既有 `docker-compose.yml`）。

## 未來可能放置的內容

- `docker-compose.yml` / `.env.example`
- `INSTALL.md`：`docker compose up -d` 與健康檢查
- `mcp-config.snippet.json`：Cursor 接入參考（不先啟用至正式專案）

---

## 部署紀錄（Phase 7）

| 項目 | 內容 |
|------|------|
| **用途** | 提供 AI agent **長期記憶**、**語意搜尋**、**知識圖譜**、**MCP 接口**（22 個 MCP tools） |
| **部署方式** | `docker compose up -d`（官方來源：[tonyzorin/agentmemory](https://github.com/tonyzorin/agentmemory) / [agentmemory.md](https://agentmemory.md)） |
| **服務定位** | 總部 **sidecar／記憶服務**，與暗部 `gov_core_system` FastAPI／LangGraph **分離** |
| **禁則** | **不得安裝進暗部 venv**；不得修改暗部 `requirements`／`pyproject`／`Lib`／`Scripts` |
| **未來接入** | Cursor 透過 MCP URL（本機預設見下方實際 port）接入；**不在此 Phase 寫入專案 rules** |
| **原始碼目錄** | `repo\`（git clone 官方倉庫，僅供 compose build） |

### Phase 7 部署結果（2026-05-16）

| 項目 | 值 |
|------|-----|
| **compose 檔** | `repo\docker-compose.yml` + `repo\docker-compose.override.yml`（總部 volume 命名） |
| **MCP 對外 port** | **8006**（官方 compose 映射 `127.0.0.1:8006→8006`；文件常見 8081 為 Tailscale 轉發範例，本機直連請用 8006） |
| **MCP URL** | `http://127.0.0.1:8006/mcp` |
| **容器** | `agentmemory-app`、`agentmemory-postgres`、`agentmemory-redis` |
| **Cursor 預留** | `%USERPROFILE%\.cursor\mcp.json` 已合併 `agentmemory`（保留 `playwright`） |
| **驗證** | `docker compose ps` 三服務 healthy；app log 顯示 FastMCP on `8006/mcp` |
