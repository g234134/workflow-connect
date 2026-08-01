# sandbox_client · sandbox-client · 品質戰報摘要（report.md）

> **case_id**: `sandbox_client` · **client_ref**: `sandbox-client` · **job_id**: `case-sandbox_client` · **sku**: `CLEAN-BASIC`
> **性質**：Demo 樣例；非 SLA、非全自動 pipeline。詳見 `docs/C2-D1_DEMO_WALKTHROUGH.md`。

## 数据概览

- 行数：intake `55` → accepted `8`（rejected `1`）
- 列数：`4`
- `qa_status`：`pass_with_warnings`

## 執行摘要

| 指標 | 清洗前 | 清洗後 |
|------|--------|--------|
| `total_rows` | 55 | — |
| `accepted_rows` | — | 8 |
| `rejected_rows` | — | 1 |
| `duplicate_rows_found` | 2 | — |
| `duplicate_rows_removed` | — | 46 |
| `qa_status` | — | pass_with_warnings |

## 缺失率（`missing_rate_by_field`）

| 欄位 | 清洗前 | 清洗後 |
|------|--------|--------|
| Phase | 1.8% | 0.0% |
| 名稱 | 0.0% | 0.0% |
| 之前 | 12.7% | 12.5% |
| 現在（建議） | 20.0% | 0.0% |

## 異常與格式

- **anomaly_count_by_rule**: {"percent_out_of_range_0_100": 11}
- **format_fixes_applied**: {"phase_name_normalized": 4, "name_trimmed": 0, "percent_symbol_removed": 42}

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
