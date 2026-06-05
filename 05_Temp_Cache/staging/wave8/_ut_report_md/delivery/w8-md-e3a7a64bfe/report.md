# 数据清洗交付报告 · w8-md-e3a7a64bfe

## 报告元数据

| 字段 | 值 |
| --- | --- |
| schema_version | `wave7_report_v0.1` |
| job_id | `w8-md-e3a7a64bfe` |
| rendered_at | `2026-06-04T03:11:58Z` |
| renderer | `wave8_report_md_v0.1` |

## 执行摘要

- **QA 结论（qa_status）**：通过 (`pass`)
- **overall_ok**：是
- **SKU**：`CLEAN-BASIC`
- **accepted_units**：1
- **billing_units**：U=1, L=0

> **M2 说明**：本版未执行 M2 抽样 QA（sample validation skipped）；下方 `overall_ok` 主要反映 M1 清单完整性结论。

## 处理量与计费单位

| 指标 | 值 |
| --- | --- |
| accepted_units | 1 |
| rejected_units | 0 |
| total_rows | 1 |
| billing_units.U | 1 |
| billing_units.L | 0 |

## 清单完整性（M1）

**结论**：✅ 通过

| 指标 | 值 |
| --- | --- |
| ok | True |
| checked_rows | 1 |
| failed_rows | 0 |
| failed_checks | 0 |

## 抽样校验（M2）

> **本版未执行 M2 抽样 QA**（`sample_validation.status=skipped`）。
> This release did **not** run M2 sample QA; the result must **not** be read as a pass.

- **status**：`skipped`
- **reason**：Wave 7: M2 sample_validation deferred to Wave 8
- **sample_validation.ok**：True（skipped 时不代表抽样通过）

<!-- DISCLAIMER-M2-SKIPPED -->

## 质量问题明细

无 recorded QA failures。

## 费用结构（预估 · 未开票）

> 本节为 R2 cost skeleton 展示，**非发票**；金额未填时仅为结构预留。
> <!-- DISCLAIMER-NOT-INVOICE -->

- **currency**：USD
- **billing_table_version**：w6_billing_v0.1
- **chargeable_hint**：False

| SKU | unit | quantity | unit_price | amount | formula_ref |
| --- | --- | --- | --- | --- | --- |
| CLEAN-BASIC | U | 1 | 待财务表 | 待财务表 | `R2_A4_3_amount_basic_or_enrich_u` |

| 汇总项 | 值 |
| --- | --- |
| amount_basic | — |
| amount_enrich | — |
| amount_total | — |
| minimum_fee_adjustment | — |

<!-- DISCLAIMER-CHARGEABLE-HINT-FALSE -->

_牌价未配置或不可计费，非最终 Chargeable 裁定。_

## 交付物索引

逻辑引用（w6://）；非磁盘路径。

| 交付物 | w6 ref |
| --- | --- |
| report.json | `w6://delivery/w8-md-e3a7a64bfe/report` |
| report.md | `w6://delivery/w8-md-e3a7a64bfe/report_md` |
| manifest | `w6://delivery/w8-md-e3a7a64bfe/manifest` |

## 声明与下一步

<!-- DISCLAIMER-NOT-INVOICE -->
<!-- DISCLAIMER-CUSTOMER-ACK-NOT-RECORDED -->

- 本 Markdown 由 `report.json` 只读渲染，不构成发票或正式计费承诺。
- 客户确认（customer_ack）与开票状态未在本报告中记录或推断。

- M2 抽样 QA 未执行：请勿将本报告理解为已完成抽样验收。
- QA 清单校验通过：可进入交付存档与后续 customer_ack / 财务流程。
