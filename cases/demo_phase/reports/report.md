# demo_phase · internal-demo · 品質戰報摘要（report.md）

> **case_id**: `demo_phase` · **client_ref**: `internal-demo` · **job_id**: `case-demo_phase` · **sku**: `CLEAN-BASIC`
> **性質**：Demo 樣例；非 SLA、非全自動 pipeline。詳見 `docs/C2-D1_DEMO_WALKTHROUGH.md`。

## 数据概览

- 行数：intake `7` → accepted `5`（rejected `1`）
- 列数：`4`
- `qa_status`：`pass_with_warnings`

## 執行摘要

| 指標 | 清洗前 | 清洗後 |
|------|--------|--------|
| `total_rows` | 7 | — |
| `accepted_rows` | — | 5 |
| `rejected_rows` | — | 1 |
| `duplicate_rows_found` | 2 | — |
| `duplicate_rows_removed` | — | 1 |
| `qa_status` | — | pass_with_warnings |

## 缺失率（`missing_rate_by_field`）

| 欄位 | 清洗前 | 清洗後 |
|------|--------|--------|
| Phase | 14.3% | 0.0% |
| 名稱 | 0.0% | 0.0% |
| 之前 | 14.3% | 20.0% |
| 現在（建議） | 0.0% | 0.0% |

## 異常與格式

- **anomaly_count_by_rule**: {"percent_out_of_range_0_100": 1}
- **format_fixes_applied**: {"phase_name_normalized": 1, "name_trimmed": 1, "percent_symbol_removed": 13}

## 清洗动作摘要

- `normalize_phase_name`: normalize phase name
- `dedup_by_phase`: dedup by phase
- `drop_missing_phase`: drop missing phase
- `parse_percent`: parse percent
- `flag_out_of_range`: flag out of range

## 已知限制 / 注意事项

- Demo only; manual review required; not production SLA pipeline
- Review Phase 4 row: 現在（建議）=105 exceeds 0–100; decide truncate, NULL, or waive.
- Confirm dedup rule (keep highest 現在（建議）) matches business expectation.
- 异常样本：row 6 field `現在（建議）` value `105.0`

## 建議後續

- Review Phase 4 row: 現在（建議）=105 exceeds 0–100; decide truncate, NULL, or waive.
- Confirm dedup rule (keep highest 現在（建議）) matches business expectation.
