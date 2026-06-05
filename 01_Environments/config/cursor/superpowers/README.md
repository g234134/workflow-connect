# cursor / superpowers

## 用途（尚書省 · 環境對接）

本目錄為**總部級 Cursor Agent 插件（Superpowers）**的登記與說明位，隸屬 `01_Environments\config\cursor\`。實際插件由 Cursor 使用者層（`%USERPROFILE%\.cursor\plugins\`）載入；此處僅保存版本紀錄、安裝方式與驗收步驟，供三省六部治理查帳。

## 禁則

**不得放暗部 venv 相關檔案**（含 `Scripts\`、`Lib\`、`.venv`、`pyvenv.cfg`、或任何指向 `python_venvs\gov_core_system` 的依賴／啟動腳本）。

## 未來可能放置的內容

- `INSTALL.md`：安裝步驟（`/plugin-add superpowers` 等）
- `manifest.json`：插件版本與驗收紀錄
- `verify-checklist.md`：新 Agent session 驗證清單

---

## 安裝紀錄（Phase 3）

| 項目 | 內容 |
|------|------|
| **安裝日期** | 2026-05-16 |
| **使用方法** | ① 官方首選：在 Cursor Agent 對話輸入 `/add-plugin superpowers`（或 `/plugin-add superpowers`）。② 本機 Agent 無法代送上述 slash 指令，故採**官方倉庫手動落地**：`git clone https://github.com/obra/superpowers.git` 後複製至使用者插件目錄。 |
| **插件版本** | 5.1.0（來自 `.cursor-plugin/plugin.json`） |
| **寫入路徑（僅紀錄）** | `C:\Users\666LAG\.cursor\plugins\superpowers\`（含 `skills\`、`agents\`、`commands\`、`hooks\hooks-cursor.json`、`.cursor-plugin\plugin.json`） |
| **Cursor 使用者設定** | 本階段**未修改** `%APPDATA%\Cursor\User\settings.json`（仍僅 2 項一般設定） |
| **驗收（待你本機確認）** | 請重啟 Cursor（或重開 Agent），在新 Agent 對話問：`Do you have superpowers?` — 應能描述 brainstorming、TDD、debugging 等 skills。若未載入，請在 Agent 內執行 `/add-plugin superpowers` 讓市集覆寫／啟用。 |
| **暗部 venv** | **未碰** `python_venvs\gov_core_system\` |
