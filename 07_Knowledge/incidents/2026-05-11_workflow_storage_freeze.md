# 2026-05-11 Workflow Storage 首次封存戰報

## 1. 今日範圍

- 初始化目錄骨架：`04_Workflows/runs`、`04_Workflows/registry`、`04_Workflows/snapshots/*`、`07_Knowledge/*`。
- 建立首筆 run：`run_2026-05-11_0001`（接戰 → 初始化校準 dry-run）。
- 產出三份 JSON：`workflow_summary`、`execution_trace`、`department_flows`（後續已於頂層補 `run_id` / `schema_version`）。

## 2. 為什麼要做

- 之後每次 workflow run 共用同一套 **storage + index（runs_index.json）**，不必散落各處。
- 方便追溯、對照、示範；少依賴「只在聊天裡說過」的上下文。

## 3. 重要事實

- **Telegram listener lock**：封存當下磁碟上 **無** `.telegram_listener.lock`；僅記錄事實，**不**當作整體紅燈。
- **Status.json**：最後一波 migration 仍為 **Success**，本次校準 **未** 改寫該檔。
- **Chariot_Registry**：以 `register_explicit_paths` 登錄 **7** 筆 `workflow_freeze` 指紋；當時 **`registry_total_rows` 約 36422**（數字隨庫增長可能變動）。
- **根 `.gitignore`**：已追加 **Workflow Storage Ignore Rules**（大量原始 artifacts／debug dump 不入庫）。

## 4. 下次要注意什麼

- 每次 run 收尾：**更新** `04_Workflows/registry/runs_index.json`；規則變動時同步 **retention_policy.md**。
- **大型 trace** 依 retention 清理，避免 `runs/` 底下堆無用巨型檔。
- 正式批次／清洗類 run 請用 **tags / notes** 與 **dry-run** 區分，避免日後誤讀。
