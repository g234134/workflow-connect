# 2026-0001 · sampleco · 品質戰報摘要（report.md）

> **case_id**: `2026-0001` · **client_ref**: `sampleco` · **job_id**: `case-2026-0001` · **sku**: `CLEAN-BASIC`
> **性質**：Demo 樣例；非 SLA、非全自動 pipeline。詳見 `docs/C2-D1_DEMO_WALKTHROUGH.md`。

## 数据概览

- 行数：intake `115` → accepted `8`（rejected `1`）
- 列数：`4`
- `qa_status`：`pass_with_warnings`

## 執行摘要

| 指標 | 清洗前 | 清洗後 |
|------|--------|--------|
| `total_rows` | 115 | — |
| `accepted_rows` | — | 8 |
| `rejected_rows` | — | 1 |
| `duplicate_rows_found` | 2 | — |
| `duplicate_rows_removed` | — | 106 |
| `qa_status` | — | pass_with_warnings |

## 缺失率（`missing_rate_by_field`）

| 欄位 | 清洗前 | 清洗後 |
|------|--------|--------|
| Phase | 0.9% | 0.0% |
| 名稱 | 0.0% | 0.0% |
| 之前 | 14.8% | 12.5% |
| 現在（建議） | 20.0% | 0.0% |

## 異常與格式

- **anomaly_count_by_rule**: {"percent_out_of_range_0_100": 20}
- **format_fixes_applied**: {"phase_name_normalized": 7, "name_trimmed": 0, "percent_symbol_removed": 91}

## 清洗动作摘要

- `normalize_phase_name`: Phase N casing unified
- `dedup_by_phase`: Keep row with max 現在（建議）
- `drop_missing_phase`: Reject rows with empty Phase
- `parse_percent`: Strip % and store 0–100 numeric
- `flag_out_of_range`: Mark 0–100 violations; do not auto-truncate in demo

## 已知限制 / 注意事项

- Demo only; manual review required; not production SLA pipeline
- Review Phase 4 row: 現在（建議）=105 exceeds 0–100; decide truncate, NULL, or waive.
- Confirm dedup rule (keep highest 現在（建議）) matches business expectation.
- 异常样本：row 5 field `現在（建議）` value `105.0`
- 异常样本：row 7 field `現在（建議）` value `105.0`
- 异常样本：row 16 field `現在（建議）` value `105.0`
- 异常样本：row 17 field `現在（建議）` value `105.0`
- 异常样本：row 20 field `現在（建議）` value `105.0`

## 建議後續

- Review Phase 4 row: 現在（建議）=105 exceeds 0–100; decide truncate, NULL, or waive.
- Confirm dedup rule (keep highest 現在（建議）) matches business expectation.
