# Wave 7 – REPORT-SUMMARY-PRODUCER（v0.1）

> **票号**：`REPORT-SUMMARY-PRODUCER`  
> **性质**：implementation ticket  
> **范围**：正式 `report.json` 生产者，尤其 `report.summary.*` 与 QA 区块骨架  
> **依据**：R2 §A.4；R3 §G.6–G.7  
> **不做**：M2 抽样校验、Markdown 报告、`customer_ack` / invoice、财务牌价数字

---

## 0. 背景

QA-M1 的 `M1-COUNT` 依赖 `report.summary.accepted_units`，但现有测试里用 `_qa_report()` stub，**尚无正式 report 生产者**。本票实现 **正式 `report.json` 生产者**。

---

## 1. 目标

实现 **正式 `report.json` 生产者**，尤其 `report.summary.*` 与 QA 区块骨架，使 QA-M1 的 `M1-COUNT` 读真实 summary 而非测试 stub。

---

## 2. 输入 / 输出

### 2.1 输入

| 输入 | 说明 |
|------|------|
| `job_record` | job 元数据 |
| post-dedup `manifest`（或 contract dict） | 去重后 manifest |
| QA-M1 结果 | M1 检查输出 |
| 可选 `billing_table` 结构 | R2 §A.4，价格可为 null |

### 2.2 输出

完整 `report.json` dict + 结构化回传：

```text
{ok, report, summary_fields_computed[]}
```

供 artifact store 落盘。

---

## 3. Done 条件（checklist）

- [ ] `report.summary` 至少含：`job_id`、`sku`、`accepted_units`、`rejected_units`、`total_rows`、`billing_units.{U,L}`、`qa_status`（由 M1 结果映射 R3 §G.6–G.7）。
- [ ] `accepted_units` **严格等于** manifest ok 行数；与 `billing_units.U` 关系符合 R2 去重规则并单测锁定。
- [ ] `report.qa.manifest_integrity` 嵌入 QA-M1 输出；`overall_ok` = M1 ok（Wave 7 不含 M2 时 `sample_validation` 可 skeleton 标 `skipped`）。
- [ ] `report.summary.cost` 或等价字段：**结构就绪**（币种、line_items 占位、amount 公式引用 R2 §A.4.3）；价格为 null 时 `chargeable_hint=false`，不假装可开票。
- [ ] 集成测：接 E2E smoke 数据 → 生产 report → 喂 QA-M1 → `M1-COUNT` 通过。

---

## 4. 边界（明确不做）

- 不实现 M2 抽样校验逻辑
- 不生成 `ART-DATA-CLEAN-REPORT` Markdown
- 不写 `customer_ack` / invoice
- 不填财务牌价数字

---

## 5. 依赖 / 前置

- post-dedup manifest（来自 `ORCH-PIPELINE-WIRE` 或等价上游）
- R2 §A.4、R3 §G.6–G.7

---

*Wave 7 implementation ticket · `04_Workflows/WAVE7_REPORT_SUMMARY_PRODUCER_v0.1.md`*
