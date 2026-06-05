# mcp / playwright

## 用途（尚書省 · 對外介面）

本目錄為 **Playwright MCP Server** 的總部登記位。實際執行透過 Cursor `mcpServers` 以 `npx @playwright/mcp@latest` 啟動；此處保存標準設定片段、瀏覽器依賴說明與驗收步驟。

## 禁則

**不得放暗部 venv 相關檔案**（含在 `gov_core_system` 內安裝 playwright、或將 MCP 執行檔指向暗部 `Scripts\python.exe`）。

## 未來可能放置的內容

- `mcp-config.snippet.json`：供複製至 Cursor MCP 設定的範本
- `INSTALL.md`：`npx playwright install` 等依賴步驟
- `verify.md`：在 Cursor 內驗證 Playwright MCP 可用性

---

## 安裝與掛載紀錄（Phase 6）

| 項目 | 內容 |
|------|------|
| **使用方式** | Cursor MCP（Model Context Protocol） |
| **啟動方式** | `npx @playwright/mcp@latest`（Windows 若相容性不佳可改 `cmd.exe /c npx -y @playwright/mcp@latest`） |
| **目的** | 提供 **web 自動化**、**UI 驗證**、**E2E 測試** 能力，供 Cursor Agent 透過 MCP 調用瀏覽器操作 |
| **Cursor 設定檔** | `%USERPROFILE%\.cursor\mcp.json` → `mcpServers.playwright` |
| **禁則** | **不得安裝進暗部 venv**（`python_venvs\gov_core_system`）；不得 `pip install playwright` 至暗部 `Scripts\`／`Lib\` |
| **瀏覽器依賴** | 屬總部層 Node／Playwright 二進位；必要時於本機執行 `npx playwright install`（非 Python venv 套件） |
| **驗證方式** | ① Cursor **Settings → MCP**（或 MCP 面板）確認 `playwright` server 狀態為已連線／已啟用；② 新 Agent 對話請 Agent 使用 Playwright 相關工具（例如開啟網頁、截圖）；③ 本目錄 `mcp-config.snippet.json` 與使用者層 `mcp.json` 內容一致 |
| **瀏覽器安裝（Phase 6 Step 3）** | 2026-05-16：本機 `ms-playwright` 快取為空，已執行 `npx playwright install chromium`（下載至 `%LOCALAPPDATA%\ms-playwright\chromium-1223` 等）；**非**暗部 Python 套件 |
