# C2-D1 · 品質戰報模板樣例（對齊 C2-P1 §3.1 + Wave 6）

> **用途**：供 Reviewer／對外展示參考的 **報表樣式**；欄位命名以 C2-P1 §3.1 為準，章節骨架參考 `WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`。  
> **實例資料**：`cases/demo_phase/report.json`（由 `clean_phase_demo.py` 產生）。

---

## 0. 報告性質聲明

- 本樣例為 **C2-D1 demo**，非 production job 的 `w6://delivery/{job_id}/...` 交付。
- `chargeable_hint: false` — 不代表可開票或 SLA 達標。
- 含 **人工確認點**；異常列可能保留原值僅標記。

---

## 1. 執行摘要（↔ Wave 6 `summary`）

| 欄位 | 本案值 | 說明 |
|------|--------|------|
| `job_id` | `C2-D1-DEMO-PHASE` | Demo 作業 ID |
| `sku` | `CLEAN-BASIC` | 對齊 Wave 6 BASIC 線 |
| `total_rows` | 7 | intake 原始列數 |
| `accepted_rows` | 5 | 納入交付檔之列數 |
| `rejected_rows` | 1 | 刪除／隔離列（缺失 Phase） |
| `qa_status` | `pass_with_warnings` | 有範圍異常但未阻斷交付 |
| `completion_variant` | `completed_with_failures` | 有 P2 級警告 |

---

## 2. 產品核心指標（C2-P1 §3.1 `product_metrics`）

### 2.1 列數與去重

| 指標 | 清洗前 | 清洗後 | 說明 |
|------|--------|--------|------|
| `total_rows` | 7 | — | 原始列數 |
| `accepted_rows` | — | 5 | 通過清洗納入交付 |
| `rejected_rows` | — | 1 | 拒絕列（空白階段） |
| `duplicate_rows_found` | 2 | — | 正規化前屬同一 Phase 2 的列數 |
| `duplicate_rows_removed` | — | 1 | 去重捨棄之列 |

### 2.2 `missing_rate_by_field`

| 欄位 | 清洗前 | 清洗後 |
|------|--------|--------|
| Phase | 14.3% | 0% |
| 名稱 | 0% | 0% |
| 之前 | 14.3% | 20.0% |
| 現在（建議） | 0% | 0% |

> 清洗後 `之前` 缺失率上升是因為分母由 7 列變 5 列，Phase 5 仍刻意留空。

### 2.3 `anomaly_count_by_rule`

| 規則 | 次數 |
|------|------|
| `percent_out_of_range_0_100` | 1 |

### 2.4 `format_fixes_applied`

| 規則類別 | 次數 |
|----------|------|
| `phase_name_normalized` | 1 |
| `name_trimmed` | 1 |
| `percent_symbol_removed` | 13 |

---

## 3. 統計明細（↔ Wave 6 `stats`）

### 3.1 `row_counts`

```json
{
  "intake": 7,
  "after_dedup": 6,
  "ok": 5,
  "rejected": 1
}
```

### 3.2 `missing_value_stats`（節錄）

| field | missing_before | missing_after | rate_before | rate_after |
|-------|----------------|---------------|-------------|------------|
| Phase | 1 | 0 | 0.1429 | 0.0 |
| 之前 | 1 | 1 | 0.1429 | 0.2 |

---

## 4. 錯誤與警告（↔ Wave 6 `errors`）

| code | count | severity | 說明 |
|------|-------|----------|------|
| `MISSING-KEY` | 1 | P1 | Phase 主鍵缺失 |
| `RANGE-ANOMALY` | 1 | P2 | 現在（建議）> 100 |

**典型樣本**：

| Phase | 欄位 | 值 |
|-------|------|-----|
| Phase 4 | 現在（建議） | 105.0 |

---

## 5. 建議後續（↔ Wave 6 `next_steps`）

**給客戶**：

1. 覆核 Phase 4 之 105% 是否為真實進度或輸入錯誤。
2. 確認去重規則（保留較高 `現在（建議）`）是否符合業務。

**建議動作**：

| action | priority | reason |
|--------|----------|--------|
| `review_warnings` | medium | 範圍異常保留未截斷 |

---

## 6. 清洗規則紀錄（↔ sidecar `cleaning_rules_applied.md`）

| rule | description |
|------|-------------|
| `normalize_phase_name` | Phase N 大小寫統一 |
| `dedup_by_phase` | 同 Phase 保留 `現在（建議）` 較大列 |
| `drop_missing_phase` | Phase 空白則拒絕列 |
| `parse_percent` | 去除 `%`，儲存 0–100 數值 |
| `flag_out_of_range` | 標記超範圍；demo 不自動截斷 |

---

## 7. 與完整 case 戰報的關係

| 文件 | 側重 |
|------|------|
| 本檔 | **模板樣式** + 欄位對照表（給 PM／Reviewer） |
| `C2-D1_PHASE_CLEANING_REPORT.md` | **逐案敘事**（原始概況、策略表、逐列摘要） |
| `cases/demo_phase/report.json` | **機讀權威**（腳本產出，可 diff） |
| `cases/demo_phase/report.md` | **精簡人讀摘要**（腳本產出） |

---

*品質戰報模板樣例 · C2-D1 · 2026-06-07*
