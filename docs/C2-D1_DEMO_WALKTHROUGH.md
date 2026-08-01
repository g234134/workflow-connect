# C2-D1 Demo · 表格清洗與品質戰報導覽

> **票號**：C2-D1 · **產品基線**：`docs/PRODUCT_TABULAR_CLEANING.md`（C2-P1）  
> **性質**：**可帶客戶看的 demo**；人工確認點存在；**非**全自動、無人值守 production pipeline。

---

## 1. Demo 能展示什麼

本 demo 以匿名化 **產品路線 Phase 進度表** 示範 C2-P1 定義的四類清洗：

| 面向 | Demo 中的髒資料 | 處理方式 |
|------|-----------------|----------|
| **缺失** | 第 8 列 Phase 空白；Phase 5 的 `之前` 空白 | 關鍵欄缺失 → 刪列；非關鍵欄 → 保留空值 |
| **重複** | `Phase 2` 與 `phase 2` 兩列 | 正規化後依主鍵去重，保留較高 `現在（建議）` |
| **異常** | Phase 4 的 `現在（建議）`= 105% | 偵測 0–100 範圍外；**保留原值**並在報告標記 |
| **格式** | 大小寫、空白、`30%` 字串 | 正規化 Phase 名、trim、去除 `%` 轉數值 |

**交付物（可在 repo 內直接開給客戶看）**：

| 產物 | 路徑 |
|------|------|
| 原始樣本 | `cases/demo_phase/Phase.csv` |
| 清洗後檔案 | `cases/demo_phase/Phase_cleaned.csv` |
| 結構化品質報告 | `cases/demo_phase/report.json` |
| 可讀品質摘要 | `cases/demo_phase/report.md` |
| 詳細 case 戰報 | `docs/CASE_REPORTS/C2-D1_PHASE_CLEANING_REPORT.md` |
| 戰報模板樣例 | `docs/CASE_REPORTS/C2-D1_QUALITY_REPORT_SAMPLE.md` |

---

## 2. 清洗流程（五步 · 對齊 C2-P1 §5）

> 各步驟為 **人工驅動 + 可重現腳本輔助**；客戶不應理解為已上線的自助入口。

```text
Step 1 Intake     → 確認欄位說明、主鍵（Phase）、可缺失欄（之前）
Step 2 Profiling  → 統計列數、缺失率、重複、格式與範圍異常
Step 3 Cleaning   → 套用已確認規則（正規化、去重、刪列、轉格式）
Step 4 QC         → 對照剖析基線，確認指標改善與警告項
Step 5 Report     → 輸出清洗檔 + report.json / report.md + case 戰報
```

### 2.1 一鍵重跑（Implementer / 展示用）

```bash
python notebooks/csv_cleaning/clean_phase_demo.py
```

預期輸出：

```json
{"ok": true, "input_rows": 7, "output_rows": 5, "report_json": "cases/demo_phase/report.json"}
```

### 2.2 人工確認點（帶客戶時必講）

1. **去重策略**：本案以 `現在（建議）` 較大者為準；真實案可能改為「最後更新時間」。
2. **超範圍 105%**：demo 僅標記不截斷；需業務決定截斷、NULL 或豁免。
3. **缺失填補**：`之前` 空白不猜測填補；真實案需事先約定規則矩陣。

---

## 3. 品質指標對照（C2-P1 §3.1 ↔ Wave 6）

| C2-P1 `product_metrics` | Wave 6 `summary` / `stats` | Demo 位置 |
|-------------------------|----------------------------|-----------|
| `total_rows` | `summary.total_rows` / `stats.row_counts.intake` | `report.json` |
| `accepted_rows` | `summary.accepted_rows` / `stats.row_counts.ok` | `report.json` |
| `rejected_rows` | `summary.rejected_rows` / `stats.row_counts.rejected` | `report.json` |
| `duplicate_rows_found` | （產品層指標；dedup 前） | `product_metrics` |
| `duplicate_rows_removed` | 對應 ENRICH `dedup_removals` 語意 | `product_metrics` |
| `missing_rate_by_field` | `stats.missing_value_stats` | 兩者皆有 |
| `anomaly_count_by_rule` | `errors.error_categories` | `product_metrics` + `errors` |
| `format_fixes_applied` | （產品層；Wave 6 無同名欄） | `product_metrics` |

完整欄位定義見 `docs/CASE_REPORTS/C2-D1_QUALITY_REPORT_SAMPLE.md`。

---

## 4. 明確不屬本 Demo

對齊 C2-P1 §3.3、§4.3 — 展示時**勿暗示**已具備：

- 客戶自助上傳／一鍵自動 pipeline
- CLEAN-ENRICH 外部 API enrich
- OCR／PDF 表格
- SLA、7×24 託管、零錯誤保證
- 寫入客戶 production DB

---

## 5. 相關文件

| 文件 | 用途 |
|------|------|
| `docs/PRODUCT_TABULAR_CLEANING.md` | 對外 Product Spec v1 |
| `04_Workflows/WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md` | 機讀報告章節權威 |
| `04_Workflows/tickets/C2-D1_state.md` | 本票施工與驗收狀態 |

---

*C2-D1 Demo Walkthrough · v1 · 2026-06-07*
