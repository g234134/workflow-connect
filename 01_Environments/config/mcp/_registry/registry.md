# 總部工具與 MCP 登記總表（HQ-Tooling-Worker · 2026-05-17）

> 本檔為 **唯讀盤點產物**，集中索引 `D:\大唐三省六部\01_Environments\config\` 下 services／tools／mcp 掛載位。  
> **禁則：** 不得將任何條目指向暗部 venv（`D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Scripts\` 等）。  
> Cursor 使用者層 MCP 合併檔：`%USERPROFILE%\.cursor\mcp.json`（不在 repo 內）。

## 專案根與設定層

| 項目 | 完整路徑 |
|------|----------|
| 專案根 | `D:\大唐三省六部\` |
| 總部設定層 | `D:\大唐三省六部\01_Environments\config\` |
| 模型註冊 | `D:\大唐三省六部\01_Environments\config\model_registry.yaml` |
| 工廠管線 | `D:\大唐三省六部\01_Environments\config\factory_pipeline.yaml` |
| MCP 單檔（預期） | `D:\大唐三省六部\01_Environments\config\mcp.json` — **不存在**；改為目錄化 snippet |

---

## MCP Servers（`config\mcp\`）

| 名稱 | 登記目錄 | Snippet | 啟動／接入 | 驗證方式 | 狀態 |
|------|----------|---------|------------|----------|------|
| playwright | `D:\大唐三省六部\01_Environments\config\mcp\playwright\` | `mcp-config.snippet.json` | `npx -y @playwright/mcp@latest` | Cursor MCP 面板；`npx playwright install chromium`（總部 Node，非暗部 pip） | 已登記（Phase 6） |
| agentmemory | `D:\大唐三省六部\01_Environments\config\services\agentmemory\` | `mcp-config.snippet.json` | `http://127.0.0.1:8006/mcp`（Docker compose） | `docker compose ps` 三服務 healthy；app log FastMCP on 8006 | 已部署（Phase 7） |

### Cursor `mcp.json` 合併參考

- Playwright snippet：`D:\大唐三省六部\01_Environments\config\mcp\playwright\mcp-config.snippet.json`
- Agentmemory snippet：`D:\大唐三省六部\01_Environments\config\services\agentmemory\mcp-config.snippet.json`
- 詳細步驟：各目錄 `README.md`

---

## Services（`config\services\`）

| 名稱 | 目錄 | 用途 | 驗證／備註 |
|------|------|------|------------|
| agentmemory | `D:\大唐三省六部\01_Environments\config\services\agentmemory\` | 長期記憶 sidecar（Docker）；MCP 22 tools | Compose：`repo\docker-compose.yml` + `repo\docker-compose.override.yml`；port **8006** |
| agentmemory 原始碼 | `D:\大唐三省六部\01_Environments\config\services\agentmemory\repo\` | 官方 clone，僅供 build | 勿與暗部 `docker-compose.yml` 混用 |

---

## Tools（`config\tools\`）

| 名稱 | 目錄 | 安裝方式（總部層） | 驗證命令 | 暗部 venv |
|------|------|-------------------|----------|-----------|
| 9router | `D:\大唐三省六部\01_Environments\config\tools\9router\` | 區域 `npm install`（`package.json` 已存在） | `cd` 至目錄後 `npx 9router --version` | **未碰** |
| graphify | `D:\大唐三省六部\01_Environments\config\tools\graphify\` | `uv tool install graphifyy`（隔離，非 repo 內 venv） | `graphify --version`；產出 `graphify-out\` | **未碰** |
| spec-kit | `D:\大唐三省六部\01_Environments\config\tools\spec-kit\` | 預留；獨立 `.venv` 或 `uvx`（Phase 8） | `specify --help`（待建環境） | **未碰** |

---

## Cursor 插件（`config\cursor\`）

| 名稱 | 目錄 | 說明 |
|------|------|------|
| superpowers | `D:\大唐三省六部\01_Environments\config\cursor\superpowers\` | 插件登記；實體於 `%USERPROFILE%\.cursor\plugins\superpowers\`（v5.1.0） |

---

## 第一階段施工邊界（2026-05-17）

- **允許：** 本檔與各子目錄 `README.md` 之文檔補齊（唯讀盤點衍生）。
- **禁止：** 任何 `npm install`／`pip`／`uv pip` 於暗部根；修改 `9router\node_modules\` 大量內容；建立 `config\mcp.json`（除非尚書省另票）。
- **暗部：** `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\` — **Blocked**。

---

## Changelog

- **2026-05-17**：HQ-Tooling-Worker 初版總表（唯讀盤點，無套件變更）。
