# 数据清洗交付报告 · w8-m2-orch-054232bbee

## 报告元数据

| 字段 | 值 |
| --- | --- |
| schema_version | `wave7_report_v0.1` |
| job_id | `w8-m2-orch-054232bbee` |
| rendered_at | `2026-06-04T16:56:24Z` |
| renderer | `wave8_report_md_v0.1` |

## 执行摘要

- **QA 结论（qa_status）**：通过 (`pass`)
- **overall_ok**：是
- **SKU**：`CLEAN-BASIC`
- **accepted_units**：1
- **billing_units**：U=1, L=0

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

**结论**：✅ 通过

| 指标 | 值 |
| --- | --- |
| status | `completed` |
| ok | True |
| sample_size | 1 |
| failed_checks | 0 |

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
| report.json | `w6://delivery/w8-m2-orch-054232bbee/report` |
| report.md | `w6://delivery/w8-m2-orch-054232bbee/report_md` |
| manifest | `w6://delivery/w8-m2-orch-054232bbee/manifest` |

## 声明与下一步

<!-- DISCLAIMER-NOT-INVOICE -->
<!-- DISCLAIMER-CUSTOMER-ACK-NOT-RECORDED -->

- 本 Markdown 由 `report.json` 只读渲染，不构成发票或正式计费承诺。
- 客户确认（customer_ack）与开票状态未在本报告中记录或推断。

- QA 清单校验通过：可进入交付存档与后续 customer_ack / 财务流程。
