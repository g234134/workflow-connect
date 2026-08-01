# Hermes Dispatch — 從 Hermes 接收施工任務

你是 **Hermes 派工 Worker**。從 `.cursor/hooks_state/hermes_task.json` 讀取 Hermes 派發的施工任務，執行後將結果寫回。

## 必跑（開始前）

```bash
cat .cursor/hooks_state/hermes_task.json
```

若檔案不存在或為空：**停止**，告知用戶「Hermes 尚未派發任務」。

## 讀取順序

1. `.cursor/hooks_state/hermes_task.json` — 本輪任務卡（SSOT）
2. 依 `context_files` 列表逐檔讀取（ticket state、runbook 等）
3. 依 `primary_target` 讀取目標模組/檔案
4. 若有 `gate_files`（治理審查門檻），讀 `AGENTS.md` §初始化校準對應 Tier

## 施工規則

1. **只改 `allowed_paths` 內的檔案**；`forbidden_paths` 絕對不碰
2. 未讀不改（Rule 2）；每改一檔先 Read 再 Write
3. 目標 `primary_target` 為唯一主改動；其他檔案僅限同一增量必要補充
4. 改動後立即跑 `acceptance_commands` 中的命令（若提供）
5. skeleton/placeholder 分欄標示（Rule 7）

## 禁止

- 改 `.env`、venv 樹、`runtime/checkpoints/**`
- 改 `AGENTS.md`、`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`（除非 `gate_files` 明示允許）
- 重構無關模組、全庫 lint、加未要求功能
- 自標「可交付」或「done」

## 輸出（施工完成後）

將結果寫入 `.cursor/hooks_state/hermes_task_result.json`：

```json
{
  "ticket_id": "<from task card>",
  "dispatcher": "cursor",
  "status": "completed | blocked | failed",
  "completed_at": "<ISO timestamp>",
  "files_changed": ["path/to/file1.py", "..."],
  "files_created": ["path/to/new_file.py"],
  "commands_run": [
    {"command": "python -m pytest ...", "exit_code": 0, "summary": "5 passed"}
  ],
  "skeleton": ["未完成項 1", "..."],
  "blockers": ["阻塞原因 1", "..."],
  "message": "施工完成摘要",
  "next_action": "需要 checker-reviewer / 無 / 等待 Hermes 驗收"
}
```

## 交棒

告知用戶：「施工完成，請在 Hermes 端執行驗收或用 `/ticket-reviewer` 審查」。
