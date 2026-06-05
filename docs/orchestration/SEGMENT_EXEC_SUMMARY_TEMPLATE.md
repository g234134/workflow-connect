# 段執行摘要模板（SEGMENT_EXEC_SUMMARY）

> **使用者**：Cursor-Worker、小龍蝦  
> **時機**：長任務**每一段**結束，或 Orchestrator 明确要求時  
> **存放**：`docs/orchestration/segments/{TASK_ID}__seg{N}__{YYYY-MM-DD}.md`

---

## 1. 必填欄位

| 欄位 | 說明 |
|------|------|
| **任務** | TASK_ID + 本段目標一句話 |
| **執行結果** | 成功 / 部分成功 / 失敗 + 一行摘要 |
| **已完成** | 本段交付項清單 |
| **未完成 / 問題** | 阻塞、待下段、需確認 |
| **關鍵檔案或輸出** | 改動路徑、命令、log 摘要（**禁** secret） |
| **下一步建議** | 給 Orchestrator 或下一段 Worker |

---

## 2. 空白模板（複製用）

```markdown
# 段執行摘要（SEGMENT）

> **TASK_ID**：
> **段號**：seg-
> **執行者**：Cursor-Worker | 小龍蝦
> **日期**：YYYY-MM-DD
> **對應 chat**：（Worker chat 標題或簡述，選填）

---

## 任務

（本段要做什麼）

## 執行結果

**結果**：成功 | 部分成功 | 失敗  
**摘要**：（一行）

## 已完成

- 

## 未完成 / 問題

- 

## 關鍵檔案或輸出

| 類型 | 路徑或命令 | 說明 |
|------|------------|------|
| 改檔 | | |
| 命令 | | |
| 產物 | | |

## 下一步建議

- 
```

---

## 3. 完整示例 — Cursor-Worker

```markdown
# 段執行摘要（SEGMENT）

> **TASK_ID**：T4b-1  
> **段號**：seg-1  
> **執行者**：Cursor-Worker  
> **日期**：2026-06-01  
> **對應 chat**：Worker — notify API seg1

---

## 任務

依 BRIEF 完成 notify 模組 HTTP 路由與 handler 骨架，不含整合測試。

## 執行結果

**結果**：成功  
**摘要**：新增 3 個檔案，本地 import 檢查通過，尚未跑全量 pytest。

## 已完成

- 新增 `core/notify/router.py`（路由定義）
- 新增 `core/notify/handlers.py`（POST /notify stub）
- 新增 `tests/test_notify_router.py`（2 個 smoke case）
- 執行 `python -m pytest tests/test_notify_router.py -q` → 2 passed

## 未完成 / 問題

- handler 尚未接真實 queue（留 T4b-2）
- 未改暗部 core，符合 R6

## 關鍵檔案或輸出

| 類型 | 路徑或命令 | 說明 |
|------|------------|------|
| 改檔 | `core/notify/router.py` | 新增 |
| 改檔 | `core/notify/handlers.py` | 新增 |
| 改檔 | `tests/test_notify_router.py` | 新增 |
| 命令 | `python -m pytest tests/test_notify_router.py -q` | 2 passed |

## 下一步建議

- Orchestrator 開 **T4b-2 新 Worker chat**，目標：接 queue + 補齊 tests
- 新 chat 首則附本 SEGMENT 路徑與 BRIEF 連結
```

---

## 4. 完整示例 — 小龍蝦

```markdown
# 段執行摘要（SEGMENT）

> **TASK_ID**：T4c  
> **段號**：seg-1  
> **執行者**：小龍蝦  
> **日期**：2026-06-02  
> **對應 chat**：小龍蝦 — smoke batch

---

## 任務

跑白名單 smoke：`python 04_Workflows/_smoke_test_keys.py`（Orchestrator 指定，只讀 keys 狀態）。

## 執行結果

**結果**：成功  
**摘要**：三鑰盲測均 [OK]，無 FAILED。

## 已完成

- 執行 `_smoke_test_keys.py` 一次
- 輸出已存 `06_Exports_Output/smoke_2026-06-02.txt`（無 secret 原文）

## 未完成 / 問題

- 無

## 關鍵檔案或輸出

| 類型 | 路徑或命令 | 說明 |
|------|------------|------|
| 命令 | `python 04_Workflows/_smoke_test_keys.py` | 全 [OK] |
| 產物 | `06_Exports_Output/smoke_2026-06-02.txt` | 摘要 log |

## 下一步建議

- Orchestrator 更新 HANDOFF，T4c smoke 標已完成
- 若需整合測試，**不在**小龍蝦白名單，須另派 Worker 或請你確認
```

---

## 5. 命名與存放規則

```
docs/orchestration/segments/
  {TASK_ID}__seg{N}__{YYYY-MM-DD}.md
```

示例：

- `T4b-1__seg1__2026-06-01.md`
- `T4c__seg1__2026-06-02.md`

Orchestrator 派工時應指定檔名；執行者填完後在 TASK_BOARD 備註欄連結。

---

## 6. 禁止事項

- 不得在此貼 `.env`、token、完整連線字串
- 不得把 SEGMENT 當階段總 HANDOFF（總交接仍用 `HANDOFF_SUMMARY.md`）
- 失敗時不得標成功；須寫清阻塞與建議
