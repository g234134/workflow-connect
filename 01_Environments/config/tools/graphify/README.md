# tools / graphify

## 用途（吏部 · 總部工具）

本目錄為 **Graphify CLI** 的總部掛載位，用於程式碼／依賴圖譜分析與 Cursor 整合說明。工具應以 `uv tool install` 等**隔離方式**安裝，不寫入暗部執行環境。

## 禁則

**不得放暗部 venv 相關檔案**（含 `gov_core_system` 下之 `Scripts\`、`Lib\`、共用 `requirements.txt` 或在此目錄內建立指向暗部的 `.venv`）。

## 未來可能放置的內容

- `INSTALL.md`：`uv tool install graphifyy`、`graphify cursor install` 步驟
- `PATH-notes.md`：CLI 實際路徑與驗證指令
- `cursor-integration.md`：Graphify 寫入 Cursor 的設定摘要（唯讀備份）

---

## 安裝紀錄（Phase 4）

| 項目 | 內容 |
|------|------|
| **安裝日期** | 2026-05-16 |
| **安裝方式** | `uv tool install graphifyy`（成功；未使用 pipx／暗部 venv） |
| **套件版本** | graphifyy 0.8.5 |
| **CLI 執行檔** | `C:\Users\666LAG\.local\bin\graphify.exe` |
| **uv 工具環境** | `C:\Users\666LAG\AppData\Roaming\uv\tools\graphifyy\` |
| **安裝命令** | 於本目錄執行：`uv tool install graphifyy`；整合：`graphify cursor install` |
| **Cursor 整合寫入** | `D:\大唐三省六部\01_Environments\config\tools\graphify\.cursor\rules\graphify.mdc`（`alwaysApply: true`，引導讀取 `graphify-out/`） |
| **未修改** | `%APPDATA%\Cursor\User\settings.json`；使用者全域 `%USERPROFILE%\.cursor\rules\` 本階段未寫入 |
| **驗證** | `graphify --version` → `graphify 0.8.5`；`graphify update .` → `graphify-out\` 產生 5 nodes（本掛載位目錄） |
| **暗部 venv** | **未碰**；`gov_core_system\Lib\site-packages` 內無 graphifyy |
