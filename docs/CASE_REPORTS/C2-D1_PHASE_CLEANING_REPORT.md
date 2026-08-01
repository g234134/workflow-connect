# C2-D1 · Phase 表格清洗與品質報告

> **票號**：C2-D1  
> **案件類型**：Demo · 產品路線 Phase 進度表（對齊 `docs/PRODUCT_TABULAR_CLEANING.md` §1.1 四面向）  
> **資料來源**：`cases/demo_phase/Phase.csv`  
> **清洗產物**：`cases/demo_phase/Phase_cleaned.csv`  
> **品質報告**：`cases/demo_phase/report.json` · `cases/demo_phase/report.md`  
> **執行腳本**：`notebooks/csv_cleaning/clean_phase_demo.py`（**demo scope**；非 production pipeline）  
> **導覽**：`docs/C2-D1_DEMO_WALKTHROUGH.md` · 模板樣例 `docs/CASE_REPORTS/C2-D1_QUALITY_REPORT_SAMPLE.md`  
> **對內 runbook**：`docs/C2-P2_RUNBOOK.md`（四階段執行步驟；附錄 B 以本案為 demo 錨點）

---

## 1. 案件描述

本 demo 模擬客戶交付的 **產品開發 Phase 進度表**：每列代表一個開發階段，欄位含階段代號（`Phase`）、階段名稱（`名稱`）、歷史完成度（`之前`）與建議目標完成度（`現在（建議）`）。百分比欄位以字串形式混用 `30%`、帶空白、以及未規範大小寫的 Phase 名稱，用以驗證標準化清洗流程。

---

## 2. 原始資料概況

| 指標 | 數值 |
|------|------|
| 列數 | 7 |
| 欄位數 | 4（`Phase`、`名稱`、`之前`、`現在（建議）`） |

### 2.1 缺失率（清洗前）

| 欄位 | 缺失筆數 | 缺失率 |
|------|----------|--------|
| Phase | 1 | 14.3% |
| 名稱 | 0 | 0% |
| 之前 | 1 | 14.3% |
| 現在（建議） | 0 | 0% |

### 2.2 重複列

| 類型 | 數量 | 說明 |
|------|------|------|
| 完整列重複 | 0 | 無完全相同列 |
| Phase 名稱重複（正規化前） | 1 組 | `Phase 2` 與 `phase 2` 為同一階段之大小寫變體 |
| Phase 名稱重複（正規化後） | 1 組 | 正規化後皆為 `Phase 2`，需去重 |

### 2.3 格式異常

| 類型 | 筆數 | 範例 |
|------|------|------|
| Phase 缺失 | 1 | 第 8 列：`名稱=空白階段`，Phase 為空 |
| Phase 命名不一致 | 1 | `phase 2`（小寫） |
| 名稱前後空白 | 1 | ` 資料整合 ` |
| 百分比含 `%` 符號 | 多筆 | `30%`、`25%` 等（預期，需轉數值） |
| 百分比前後空白 | 2 | ` 45%`、` 90%` |

### 2.4 數值範圍異常

| 列 | Phase | 欄位 | 值 | 說明 |
|----|-------|------|-----|------|
| 6 | Phase 4 | 現在（建議） | 105 | 超出合理範圍 0–100 |

---

## 3. 清洗策略

| 問題類型 | 處理方式 | 本案結果 |
|----------|----------|----------|
| **缺失 Phase** | 刪除列並記錄於報告 | 刪除 1 列（`空白階段`） |
| **缺失百分比（之前）** | 保留空值，不填補 | Phase 5 之 `之前` 維持空白 |
| **Phase 命名** | 正規化為 `Phase N`（大小寫統一） | `phase 2` → `Phase 2` |
| **名稱空白** | `strip()` 去除前後空白 | ` 資料整合 ` → `資料整合` |
| **重複 Phase** | 保留 `現在（建議）` 較高者 | 保留補丁列（35%），捨棄舊列（30%） |
| **百分比格式** | 去除 `%`，轉為 0–100 數值（小數） | 例：`30%` → `30.0` |
| **超出範圍** | 保留原值並標記 `_flags: out_of_range` | Phase 4 之 105% 保留並標記 |

---

## 4. 清洗後統計

### 4.1 C2-P1 §3.1 核心指標

| 指標 | 清洗前 | 清洗後 |
|------|--------|--------|
| `total_rows` | 7 | — |
| `accepted_rows` | — | 5 |
| `rejected_rows` | — | 1 |
| `duplicate_rows_found` | 2 | — |
| `duplicate_rows_removed` | — | 1 |
| `anomaly_count_by_rule`（`percent_out_of_range_0_100`） | 1 | 1 |

完整 JSON 見 `cases/demo_phase/report.json` → `product_metrics`；欄位對照表見 `C2-D1_QUALITY_REPORT_SAMPLE.md`。

### 4.2 剖析摘要

| 指標 | 清洗前 | 清洗後 |
|------|--------|--------|
| 列數 | 7 | 5 |
| Phase 缺失 | 1 | 0 |
| 之前 缺失 | 1 | 1（刻意保留） |
| 完整列重複 | 0 | 0 |
| Phase 重複 | 1 組（正規化後） | 0 |
| 格式異常（Phase 命名） | 2 | 0 |
| 範圍異常（>100） | 1 | 1（已標記，未刪除） |

### 清洗後資料摘要

```
Phase 1 · 基礎建設        之前 30.0  → 現在 45.0
Phase 2 · 資料整合（補丁） 之前 20.0  → 現在 35.0  （去重後保留）
Phase 3 · 分析模組        之前 80.0  → 現在 90.0
Phase 4 · 上線準備        之前 100.0 → 現在 105.0 ⚠ 超出範圍
Phase 5 · 維運監控        之前 (空)  → 現在 50.0
```

---

## 5. 本案局限與建議

1. **欄位單薄**：真實客戶表可能含負責人、起訖日、依賴關係、備註等欄位；本案僅 4 欄，後續 C2-Px 應擴充欄位字典與型別推斷。
2. **缺失填補**：本案對 `之前` 缺失採「保留空值」；真實案子需依業務規則決定是否用 0、前值或人工補登。
3. **超出範圍**：105% 僅標記未修正；生產流程可改為截斷至 100、改為 NULL，或進人工覆核佇列。
4. **去重策略**：本案以 `現在（建議）` 最大者為準；若客戶以「最後更新時間」為準，需另備 metadata 欄。
5. **異常外顯**：105% 標記在 `report.json`／`cleaning_stats.json` 內部；交付 CSV 無 `_flags` 欄（真實案應加 sidecar 或附加欄）。
6. **自動化邊界**：腳本為 **demo 輔助**；C2-P2 才詳化 runbook。不暗示客戶可自助上傳或無人值守 pipeline（見 C2-P1 §1.3、§4.3）。
7. **產品對齊**：本案已對照 `docs/PRODUCT_TABULAR_CLEANING.md`（C2-P1）四面向與 §3.1 指標；Wave 6 章節骨架見 `report.json`。

---

## 6. 驗證方法

- 執行 `python notebooks/csv_cleaning/clean_phase_demo.py`，確認 `ok: true`、輸入 7 列 → 輸出 5 列、`report_json` 路徑正確。
- 比對 `cases/demo_phase/cleaning_stats.json` 與 `report.json` 之 `product_metrics` 與本報告 §4.1 一致。
- 目視檢查 `Phase_cleaned.csv`：百分比已為數值、Phase 命名統一、重複 Phase 2 僅剩一列。
- 人讀摘要：`cases/demo_phase/report.md` 可單獨展示給客戶。
