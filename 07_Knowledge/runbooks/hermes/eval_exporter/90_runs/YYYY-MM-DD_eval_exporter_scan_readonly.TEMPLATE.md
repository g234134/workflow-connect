# Run Note TEMPLATE — eval_exporter Readonly Scan

> 本文件為空白模板。實際執行 scan 時複製此檔案，用實際日期替換 `YYYY-MM-DD`，填入實際內容。

---

> **任務**：eval_exporter 第一次只讀衛生檢查
> **執行者**：（Hermes Agent）
> **日期**：YYYY-MM-DD
> **模式**：read-only | 未修改任何 repo 原始碼
> **前提**：discovery 已完成（`90_runs/YYYY-MM-DD_eval_exporter_discovery.md`）；DEBT_LOG.md 為空表

---

## 1. Scope / Non-Scope

### Scope（本輪涵蓋）

| 類別 | 檔案 | 重點 |
|------|------|------|
| 核心 | `observability/eval_exporter.py`（?? 行） | CLI, export logic |
| （其他） | — | — |

### Non-Scope（明確排除）

| 元件 | 排除原因 |
|------|----------|
| （待設定） | — |

---

## 2. 結構與依賴檢查

（待填入 — 檔案分層、import 依賴、耦合點）

---

## 3. Hygiene 逐項檢查

### 3.1 合約檢查（Contract）

| 項目 | 狀態 | 備註 |
|------|:----:|------|
| 公開函數 docstring | ✅ / ⚠️ / ❌ | — |
| docstring 包含 Args/Returns/Raises | ✅ / ⚠️ / ❌ | — |
| 回傳型別註記 | ✅ / ⚠️ / ❌ | — |

### 3.2 錯誤處理（Error Handling）

| 項目 | 狀態 | 備註 |
|------|:----:|------|
| bare except | ✅ / ⚠️ / ❌ | — |
| 例外類型具體 | ✅ / ⚠️ / ❌ | — |
| I/O 路徑保護 | ✅ / ⚠️ / ❌ | — |

### 3.3 型別與介面（Type & Interface）

| 項目 | 狀態 | 備註 |
|------|:----:|------|
| 參數有 type hint | ✅ / ⚠️ / ❌ | — |
| 回傳值與 docstring 一致 | ✅ / ⚠️ / ❌ | — |
| Any 濫用 | ✅ / ⚠️ / ❌ | — |

### 3.4 日誌與可觀測性（Logging & Observability）

| 項目 | 狀態 | 備註 |
|------|:----:|------|
| 關鍵決策點有 INFO 日誌 | ✅ / ⚠️ / ❌ | — |
| 錯誤路徑有 WARNING/ERROR 日誌 | ✅ / ⚠️ / ❌ | — |
| 結構化欄位一致 | ✅ / ⚠️ / ❌ | — |

### 3.5 測試穩定性（Test Hygiene）

| 項目 | 狀態 | 備註 |
|------|:----:|------|
| 測試檔案存在 | ✅ / ⚠️ / ❌ | — |
| 外部服務 mock | ✅ / ⚠️ / ❌ | — |
| fixture 過時 | ✅ / ⚠️ / ❌ | — |

### 3.6 技術債（Debt Tracking）

| 項目 | 狀態 | 備註 |
|------|:----:|------|
| TODO/FIXME 對應 DEBT_LOG | ✅ / ⚠️ / ❌ | — |

---

## 4. 問題總表（引用 DEBT_LOG）

| Debt ID | 檔案:行號 | 嚴重度 | 摘要 |
|---------|-----------|:-----:|------|
| （待填入） | — | — | — |

---

## 5. 限制與免責聲明

- （待根據實際執行環境補充）
