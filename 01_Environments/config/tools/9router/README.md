# tools / 9router

## 用途（吏部 · 路由基建）

本目錄為 **9Router** 模型路由 CLI 的總部掛載位。優先以區域 `npm` 專案安裝（避免污染系統 PATH）；僅在確認後才考慮全域安裝。與暗部 `gov_core_system` 內正式 API／LangGraph 連線**分離**，本階段只驗證 CLI，不修改正式模型連線。

## 禁則

**不得放暗部 venv 相關檔案**（含 Python venv、指向 `python_venvs\gov_core_system` 的啟動腳本或依賴鎖檔）。

## 未來可能放置的內容

- `package.json` / `package-lock.json`：區域 Node 安裝
- `INSTALL.md`：安裝與 `9router --help` 驗證
- `cursor-bridge-notes.md`：未來接入 Cursor 的設定參考（不先啟用）

---

## 安裝紀錄（Phase 5）

| 項目 | 內容 |
|------|------|
| **安裝日期** | 2026-05-16 |
| **安裝方式** | **區域 npm 專案**（本目錄 `npm init -y` + `npm install 9router`）；未使用 `npm install -g` |
| **版本** | 9router **0.4.50**（`package.json` → `dependencies.9router`） |
| **執行方式** | `cd` 至本目錄後：`npx 9router --help` / `npx 9router --version` |
| **驗證摘要** | `npx 9router --help` 顯示 port 預設 20128、tray/log 等選項；`--version` → `0.4.50` |
| **Cursor 模型設定** | **本階段未修改**任何 Cursor 模型／路由設定 |
| **未來與 Cursor 對接（僅思路）** | 9Router 為本機 HTTP 代理（預設 `:20128`）。接入時可能需：① 在 Cursor 設定或環境變數指定 OpenAI-compatible `baseURL` 指向 `http://127.0.0.1:20128`；② 或透過 MCP／自訂 endpoint 文件登記於 `01_Environments\config\mcp\_registry\`。**現階段不實作。** |
| **暗部 venv** | **未碰** `python_venvs\gov_core_system\` |
