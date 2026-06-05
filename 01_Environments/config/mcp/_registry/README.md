# mcp / _registry

## 用途（尚書省 · MCP 總冊）

本目錄為總部 **MCP Server 架構登記總表**，集中列出各 MCP 子目錄（如 `playwright\`）、啟動方式、驗收狀態與 Cursor 設定檔位置。各 server 實作細節放在同級子資料夾，此處只做索引與治理。

## 禁則

**不得放暗部 venv 相關檔案**（含任何需暗部 Python 執行的 MCP 二進位、venv、或指向 `gov_core_system` 的 command 預設值）。

## 未來可能放置的內容

- `registry.md`：MCP 清單（名稱、路徑、狀態、驗證方式）
- `cursor-mcp-location.md`：使用者層 `mcp.json` 預期位置說明
- 各 `<server-name>\` 子目錄之交叉連結
