# 階段交接模板（HANDOFF_SUMMARY_TEMPLATE）

> 階段結束時由 **Cursor-Orchestrator** 複製填寫，覆寫或追加至 [`HANDOFF_SUMMARY.md`](./HANDOFF_SUMMARY.md)。  
> **必填四欄**：已完成、未完成、風險與約束更新、下一階段建議。

---

## 1. 空白模板（複製用）

```markdown
# 階段交接摘要（HANDOFF_SUMMARY）

> **階段名稱**：
> **交接日期**：YYYY-MM-DD
> **交接者**：Cursor-Orchestrator
> **上一階段 TASK_ID**：（例 T4）

---

## 已完成

- 

## 未完成

- 

## 風險與約束更新

- 

## 下一階段建議

- 

---

## 附錄（選填）

### 相關 SEGMENT 路徑

- 

### 相關 BRIEF / 文件

- 

### 需尚書省記住的決策

- 
```

---

## 2. 完整示例（可直接參考）

```markdown
# 階段交接摘要（HANDOFF_SUMMARY）

> **階段名稱**：用戶通知模組 v0.1 — 實作與測試  
> **交接日期**：2026-06-02  
> **交接者**：Cursor-Orchestrator  
> **上一階段 TASK_ID**：T4

---

## 已完成

- T4a：Hermes 產出 BRIEF（`docs/orchestration/briefs/T4_brief.md`）
- T4b-1：Worker 完成 notify API 骨架（seg1 SEGMENT 已存）
- 單元測試 12/12 通過（命令：`python -m pytest tests/test_notify.py`）
- TASK_BOARD 已更新 T4b-1 → 已完成

## 未完成

- T4b-2：整合測試尚未跑（依賴 staging 環境，目前不可用）
- T4c：操作文件未撰寫
- HANDOFF 尚未同步至 `04_Workflows/00_Agent_Work_Progress.md`（可選）

## 風險與約束更新

- **新增約束**：下一階段禁止改暗部 `core/orchestrator.py`（R6）
- **風險**：staging 環境本週維護，整合測試可能延到 2026-06-05
- **無變更**：仍禁止改 `.env`、force push（R2、R3）

## 下一階段建議

1. 開新任務 **T5**：僅做 T4c 文件 + 小龍蝦跑 smoke（白名單 runner）
2. T4b-2 整合測試等 staging 恢復後再開 **Worker 新 chat**（附本 HANDOFF）
3. 建議你確認：文件是否要先寫中文操作版，或僅 README 級

---

## 附錄（選填）

### 相關 SEGMENT 路徑

- `docs/orchestration/segments/T4b-1__seg1__2026-06-01.md`
- `docs/orchestration/segments/T4b-2__seg1__2026-06-02.md`

### 相關 BRIEF / 文件

- `docs/orchestration/briefs/T4_brief.md`

### 需尚書省記住的決策

- 2026-06-01 你確認：v0.1 不做 Telegram 推送，僅 HTTP API
```

---

## 3. 填寫規則

| 欄位 | 要求 |
|------|------|
| 已完成 | 列 TASK_ID + 可驗收證據（命令、檔案、SEGMENT 路徑） |
| 未完成 | 列阻塞原因與依賴 |
| 風險與約束更新 | **只寫變更**；繼承約束可寫「無變更」 |
| 下一階段建議 | 可執行、可派工；必要時標需你確認項 |

**頻率**：每階段結束必寫；長任務 major checkpoint 可寫 interim HANDOFF（檔名可改存 `handoffs/` 子目錄，並在 TASK_BOARD 備註連結）。
