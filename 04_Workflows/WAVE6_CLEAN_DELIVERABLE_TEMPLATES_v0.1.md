# Wave 6 – CLEAN 产品交付物模板（v0.1）

> **票号**：`WAVE6-CLEAN-DELIVERABLE-TEMPLATES`  
> **性质**：spec / planning  
> **范围**：定义 CLEAN-BASIC / CLEAN-ENRICH 两产品标准交付物结构、报告章节、附件清单与 Done/Chargeable 判定标准  
> **前置**：W6-R1–R4 规格冻结；Wave 7 `report.json` 生产者已交付；Wave 8 Markdown 渲染规划中  
> **不做**：runner/orchestrator 实作、JSON Schema 落盘、财务牌价填数

---

## 0. 产品矩阵速查

| 产品代码 | 中文名 | 核心差异 | 适用场景 |
|----------|--------|----------|----------|
| `CLEAN-BASIC` | 基础清洗 | 仅 v2.0 信封、`groq_used=false`、无 `enrichment` 区块 | 格式标准化、去重、元数据提取 |
| `CLEAN-ENRICH` | 增强清洗 | 含 `enrichment_v0.1` 区块、允许 `groq_used=true`、计费增 LLM 触发项 | 语义标签、语言检测、质量评分 |

---

## 1. 报告结构（`report.json` + `report.md`）

### 1.1 顶层区块划分

```text
report
├── meta                    # 报告元数据
├── summary                 # 执行摘要与计费核心
├── stats                   # 统计明细
├── errors                  # 典型错误与分类
├── qa                      # M1/M2 质量检验
├── next_steps              # 建议与后续动作
└── attachments_index       # 附件清单（逻辑引用）
```

### 1.2 各章节字段定义

#### §1.2.1 Summary（执行摘要）

| 字段 | 类型 | 说明 | BASIC | ENRICH |
|------|------|------|-------|--------|
| `job_id` | string | 全局唯一作业 ID | ✓ | ✓ |
| `sku` | enum | `CLEAN-BASIC` / `CLEAN-ENRICH` | ✓ | ✓ |
| `accepted_units` | int | `clean_status=ok` 且符合 SKU 规则之列数 | ✓ | ✓ |
| `rejected_units` | int | 失败或不符合 SKU 规则之列数 | ✓ | ✓ |
| `total_rows` | int | intake 原始总行数（含重复） | ✓ | ✓ |
| `billing_units.U` | int | 计费成功单位 = accepted_units 去重后 | ✓ | ✓ |
| `billing_units.L` | int | LLM 触发次数（仅 ENRICH 非零） | ✗ (恒 0) | ✓ |
| `qa_status` | enum | `pass` / `pass_with_warnings` / `fail` | ✓ | ✓ |
| `completion_variant` | enum | `completed` / `completed_with_failures` | ✓ | ✓ |
| `cost` | object | 费用结构骨架（R2 §A.4） | ✓ | ✓ |
| `chargeable_hint` | bool | 结构就绪提示（非最终 Chargeable） | ✓ | ✓ |
| `enrichment_coverage_pct` | int | 含有效 enrichment 的 ok 列占比 | ✗ | ✓ |

#### §1.2.2 Stats（统计明细）

| 字段 | 类型 | 说明 | BASIC | ENRICH |
|------|------|------|-------|--------|
| `row_counts` | object | `intake` / `after_dedup` / `ok` / `rejected` | ✓ | ✓ |
| `field_coverage` | object | 各信封字段填充率（%） | ✓ | ✓ |
| `missing_value_stats` | array | 缺失值字段统计（前 10） | ✓ | ✓ |
| `by_extension` | array | 按扩展名分布：count / ok / rejected | ✓ | ✓ |
| `size_distribution` | object | 文件大小分桶（<1KB, 1-10KB, ...） | ✓ | ✓ |
| `groq_used_count` | int | LLM 触发次数（仅 ENRICH） | ✗ | ✓ |
| `language_distribution` | object | ISO 639-1 语言码分布（仅 ENRICH） | ✗ | ✓ |
| `quality_score_distribution` | object | quality_score 分桶（0-50/50-80/80-100） | ✗ | ✓ |
| `processing_time_ms` | int | 总处理耗时（不含 queue wait） | ✓ | ✓ |

#### §1.2.3 Errors（错误分析）

| 字段 | 类型 | 说明 | BASIC | ENRICH |
|------|------|------|-------|--------|
| `error_categories` | array | 错误类别分布：`{code, count, severity}` | ✓ | ✓ |
| `top_errors_sample` | array | 典型错误样本（脱敏）：最多 5 条 | ✓ | ✓ |
| `rejection_reasons` | array | 拒收原因占比图 | ✓ | ✓ |
| `remediation_summary` | object | 建议修复动作统计 | ✓ | ✓ |

**典型错误类别（`error_categories[].code`）**：

| 代码 | 含义 | 严重度 | 产品 |
|------|------|--------|------|
| `PARSE-FAIL` | 文件解析失败 | P0 | 共用 |
| `SCHEMA-VIOLATION` | 信封字段缺失/类型错误 | P0 | 共用 |
| `SKU-MISMATCH` | SKU 规则违规（如 BASIC 含 enrichment） | P0 | 共用 |
| `GROQ-BASIC-VIOLATION` | BASIC 却 `groq_used=true` | P0 | BASIC |
| `ENRICH-MISSING` | ENRICH 却缺 enrichment 区块 | P0 | ENRICH |
| `QUALITY-LOW` | quality_score < 50 | P1 | ENRICH |
| `PATH-LEAK` | 路径含磁盘根特征 | P1 | 共用 |
| `PREVIEW-LEN` | preview_lines > 10 | P2 | 共用 |

#### §1.2.4 QA（质量检验 M1/M2）

| 字段 | 类型 | 说明 | BASIC | ENRICH |
|------|------|------|-------|--------|
| `manifest_integrity` | object | M1 结果：`{ok, checked_rows, failed_rows, failed_checks}` | ✓ | ✓ |
| `sample_validation` | object | M2 结果：`{ok, N, sample_size, seed, failed_checks}` | ✓ | ✓ |
| `failures[]` | array | 详细失败记录（`qa_failure_record`，最多 100 条） | ✓ | ✓ |
| `overall_ok` | bool | `manifest_integrity.ok ∧ sample_validation.ok` | ✓ | ✓ |
| `m1_checks_summary` | array | M1 各检查项通过状态 | ✓ | ✓ |
| `m2_checks_summary` | array | M2 各检查项通过状态（抽样） | ✓ | ✓ |

**M1/M2 判定与红绿灯映射（R3 §G.6–G.7）**：

| M1 结果 | M2 结果 | `qa_status` | 信号灯 | Done 判定 | Chargeable 判定 |
|---------|---------|-------------|--------|-----------|-----------------|
| 无 P0 | 无 P0/P1 | `pass` | 绿灯 | ✓ | 视 C1–C5 |
| 无 P0 | 仅 P1 | `pass_with_warnings` | 黄灯 | ✓ | ✗（待修复/豁免） |
| 有 P0 | 任意 | `fail` | 红灯 | ✗ | ✗ |
| 任意 | 有 P0 | `fail` | 红灯 | ✗ | ✗ |

#### §1.2.5 Next Steps（建议与后续动作）

| 字段 | 类型 | 说明 | BASIC | ENRICH |
|------|------|------|-------|--------|
| `for_customer` | array | 给客户的建议（人读） | ✓ | ✓ |
| `for_internal` | array | 给 CS/运营的技术备注 | ✓ | ✓ |
| `recommended_actions` | array | 建议动作枚举：`{action, priority, reason}` | ✓ | ✓ |
| `upgrade_opportunity` | object | BASIC→ENRICH 升级建议（仅 BASIC 且质量允许） | ✓ | ✗ |
| `estimated_reprocess_time` | string | 预估重跑耗时（如有拒绝行） | ✓ | ✓ |

**推荐动作枚举**：

| `action` | 含义 | 触发条件 |
|----------|------|----------|
| `accept_deliverables` | 直接收交付物 | `qa_status=pass` |
| `review_warnings` | 人工复核警告项 | `qa_status=pass_with_warnings` |
| `fix_and_rerun` | 修复后重跑 | `qa_status=fail` 且可修复 |
| `upgrade_to_enrich` | 升级 ENRICH 补跑 | BASIC 完成，客户有语义需求 |
| `waive_with_approval` | 书面豁免后继续 | P1 失败但客户接受风险 |
| `contact_support` | 联系技术支持 | 系统性错误 |

---

## 2. 附件结构（Attachments）

### 2.1 标准附件清单

| 附件类型 | 文件名规范 | 格式 | 说明 | BASIC | ENRICH |
|----------|------------|------|------|-------|--------|
| **主数据文件** | `manifest.json` | JSON | 清洗后信封索引（去重后） | ✓ | ✓ |
| **交付物包** | `deliverables/` 目录 | 多文件 | 每行对应一个 `.json` 信封文件 | ✓ | ✓ |
| **统计附表** | `stats_detail.json` | JSON | Stats 区块完整数据 | ✓ | ✓ |
| **错误明细** | `errors_full.json` | JSON | Errors 完整列表（可能大） | ✓ | ✓ |
| **ENRICH 批次摘要** | `enrichment_batch_summary.json` | JSON | ENRICH 特有：语言分布、覆盖率等 | ✗ | ✓ |

### 2.2 Sidecar 元数据文件

| Sidecar 类型 | 文件名规范 | 格式 | 说明 | BASIC | ENRICH |
|--------------|------------|------|------|-------|--------|
| **Schema 描述** | `schema_manifest_v2.0.md` | Markdown | manifest.json 字段说明、类型约束 | ✓ | ✓ |
| **数据字典** | `data_dictionary.json` | JSON | 字段级语义说明、示例值 | ✓ | ✓ |
| **清洗规则说明** | `cleaning_rules_applied.md` | Markdown | 本作业应用的清洗规则摘要 | ✓ | ✓ |
| **QA 方法说明** | `qa_methodology.md` | Markdown | M1/M2 检查项详细说明 | ✓ | ✓ |
| **ENRICH 算法说明** | `enrichment_algorithms_v0.1.md` | Markdown | quality_score 算法、标签规则 | ✗ | ✓ |
| **计费说明** | `billing_note.md` | Markdown | U/L 计算说明、Q_min 提示 | ✓ | ✓ |

### 2.3 逻辑路径引用（`w6://` 协议）

所有附件统一通过 `w6://delivery/{job_id}/{kind}` 引用：

```
w6://delivery/{job_id}/manifest           → manifest.json
w6://delivery/{job_id}/deliverables       → deliverables/ 目录
w6://delivery/{job_id}/report_json        → report.json
w6://delivery/{job_id}/report_md          → report.md（人读报告）
w6://delivery/{job_id}/stats_detail       → stats_detail.json
w6://delivery/{job_id}/errors_full        → errors_full.json
w6://delivery/{job_id}/sidecars           → sidecars/ 目录（含 schema、数据字典等）
```

---

## 3. Done / Chargeable 判定标准

### 3.1 Done 完成态（技术交付）

| 条件编号 | 条件说明 | 必要/可选 | 验证来源 |
|----------|----------|-----------|----------|
| D-1 | `report.json` 已生成且通过 schema 校验 | 必要 | artifact store |
| D-2 | `qa.overall_ok=true` | 必要 | M1/M2 检查结果 |
| D-3 | `accepted_units > 0` | 必要 | manifest 计数 |
| D-4 | 所有 P0 失败已修复或 `waive_with_approval` | 必要 | `failures[].remediation_hint` |
| D-5 | `deliverables/` 目录与 manifest 行数一致 | 必要 | artifact store |
| D-6 | `enrichment_coverage_pct >= 95%`（仅 ENRICH） | 必要 | enrichment_batch_summary |
| D-7 | 四件套 artifact refs 可解析 | 必要 | `w6://` refs |

**`completed_with_failures` 特殊态**：

- 允许条件：D-2 通过（无 P0）、D-3 满足（有成功行）、存在 P2 级失败
- 额外要求：必须在 `next_steps.for_customer` 中明确列出被拒收的文件数量与原因
- 禁止：`accepted_units=0` 时标记 `completed_with_failures`

### 3.2 Chargeable 可收费态（商务交付）

在 Done 基础上，额外满足：

| 条件编号 | 条件说明 | 必要/可选 | 验证来源 |
|----------|----------|-----------|----------|
| C-1 | `billing_units.U >= Q_min`（BASIC:100, ENRICH:50）或 `minimum_fee_applied=true` | 必要 | R2 §A.3 §A.5 |
| C-2 | `customer_ack` 非空（客户确认） | 必要 | Phase 6.5 `delivery` |
| C-3 | `billing_dispute_flag=false` | 必要 | report / bridge |
| C-4 | `job_record.sku` 与 `order.line_items[0].sku` 一致 | 必要 | intake / order |
| C-5 | `enrichment_coverage_pct >= 95%`（仅 ENRICH） | 必要 | R2 §A.7 C5 |

**`chargeable_hint` 与最终 Chargeable 区别**：

| 字段 | 含义 | 谁判定 |
|------|------|--------|
| `chargeable_hint` | 结构就绪，提示可进入商务流程 | 系统自动（结构检查） |
| `Chargeable`（商务） | 满足 C1–C5，可开票 | 财务/运营人工确认 |

---

## 4. 产品 → 报告章节对照表

| 报告章节 | 子区块/字段 | CLEAN-BASIC | CLEAN-ENRICH | 差异说明 |
|----------|-------------|-------------|--------------|----------|
| **meta** | `schema_version`, `job_id`, `generated_at` | ✓ | ✓ | 相同 |
| | `report_type` | `clean_basic_v0.1` | `clean_enrich_v0.1` | 区分标记 |
| **summary** | `job_id`, `sku` | ✓ | ✓ | 相同 |
| | `accepted_units`, `rejected_units` | ✓ | ✓ | 相同 |
| | `total_rows` | ✓ | ✓ | 相同 |
| | `billing_units.U` | ✓ | ✓ | 相同 |
| | `billing_units.L` | ✗ (恒 0) | ✓ | ENRICH 特有 |
| | `qa_status` | ✓ | ✓ | 相同 |
| | `completion_variant` | ✓ | ✓ | 相同 |
| | `cost` (skeleton) | ✓ | ✓ | 相同结构 |
| | `chargeable_hint` | ✓ | ✓ | 相同 |
| | `enrichment_coverage_pct` | ✗ | ✓ | ENRICH 特有 |
| **stats** | `row_counts`, `field_coverage` | ✓ | ✓ | 相同 |
| | `missing_value_stats` | ✓ | ✓ | 相同 |
| | `by_extension`, `size_distribution` | ✓ | ✓ | 相同 |
| | `processing_time_ms` | ✓ | ✓ | 相同 |
| | `groq_used_count` | ✗ | ✓ | ENRICH 特有 |
| | `language_distribution` | ✗ | ✓ | ENRICH 特有 |
| | `quality_score_distribution` | ✗ | ✓ | ENRICH 特有 |
| **errors** | `error_categories` | ✓ | ✓ | 类别集合不同 |
| | `top_errors_sample` | ✓ | ✓ | 相同 |
| | `rejection_reasons` | ✓ | ✓ | 相同 |
| | `remediation_summary` | ✓ | ✓ | 动作集合不同 |
| **qa** | `manifest_integrity` (M1) | ✓ | ✓ | 相同 |
| | `sample_validation` (M2) | ✓ | ✓ | 抽样范围不同 |
| | `failures[]` | ✓ | ✓ | 失败类型不同 |
| | `overall_ok` | ✓ | ✓ | 相同 |
| | `m1_checks_summary` | ✓ | ✓ | BASIC 检查 SKU-BASIC |
| | `m2_checks_summary` | ✓ | ✓ | ENRICH 检查 enrichment |
| **next_steps** | `for_customer` | ✓ | ✓ | 内容不同 |
| | `for_internal` | ✓ | ✓ | 内容不同 |
| | `recommended_actions` | ✓ | ✓ | BASIC 可建议 upgrade |
| | `upgrade_opportunity` | ✓ | ✗ | 仅 BASIC 有此字段 |
| | `estimated_reprocess_time` | ✓ | ✓ | 相同 |
| **attachments_index** | 全部字段 | ✓ | ✓ | 列表内容不同 |

---

## 5. 产品 → 附件清单对照表

| 附件类别 | 具体文件 | CLEAN-BASIC | CLEAN-ENRICH | 说明 |
|----------|----------|-------------|--------------|------|
| **主数据文件** | `manifest.json` | ✓ | ✓ | 都必须 |
| | `deliverables/*.json` | ✓ | ✓ | 每行一个信封 |
| **统计明细** | `stats_detail.json` | ✓ | ✓ | 完整 Stats 区块 |
| | `enrichment_batch_summary.json` | ✗ | ✓ | 仅 ENRICH |
| **错误明细** | `errors_full.json` | 可选 | 可选 | 大文件时可选 |
| **人读报告** | `report.md` | ✓ | ✓ | Wave 8 交付 |
| **Sidecar** | `schema_manifest_v2.0.md` | ✓ | ✓ | 通用 |
| | `data_dictionary.json` | ✓ | ✓ | 通用 |
| | `cleaning_rules_applied.md` | ✓ | ✓ | 通用 |
| | `qa_methodology.md` | ✓ | ✓ | M1 相同，M2 不同 |
| | `enrichment_algorithms_v0.1.md` | ✗ | ✓ | 仅 ENRICH |
| | `billing_note.md` | ✓ | ✓ | U/L 计算说明 |

---

## 6. 交付物目录结构示例

```
{delivery_root}/{job_id}/
├── manifest.json                     # 主索引
├── report.json                       # 机读报告（本模板定义）
├── report.md                         # 人读报告（Wave 8 渲染）
├── stats_detail.json                 # 统计明细
├── errors_full.json                  # 错误完整列表（可选）
├── deliverables/                     # 清洗后信封包
│   ├── {file_id_1}.json
│   ├── {file_id_2}.json
│   └── ...
├── sidecars/                         # 元数据与说明文档
│   ├── schema_manifest_v2.0.md
│   ├── data_dictionary.json
│   ├── cleaning_rules_applied.md
│   ├── qa_methodology.md
│   ├── enrichment_algorithms_v0.1.md   # 仅 ENRICH
│   └── billing_note.md
└── enrichment_batch_summary.json     # 仅 ENRICH
```

---

## 7. 下游消费指引（简要）

| 消费方 | 关注区块 | 关键字段 |
|--------|----------|----------|
| **客户（人读）** | `summary`, `next_steps.for_customer`, `report.md` | `qa_status`, `accepted_units`, `recommended_actions` |
| **客户（系统对接）** | `manifest.json`, `deliverables/` | `content_sha256`, `stored_logical_path` |
| **CS/运营** | `errors`, `qa`, `next_steps.for_internal` | `failures[]`, `remediation_hint` |
| **财务/开票** | `summary.billing_units`, `billing_note.md` | `U`, `L` (ENRICH), `Q_min` |
| **审计/合规** | `qa`, `sidecars/qa_methodology.md` | `m1_checks_summary`, `m2_checks_summary` |
| **上游系统（bridge）** | `report.json` 整体 | `bridge_result.wave6.*` 映射（R3 §H） |

---

## 8. 版本与演进

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草案：BASIC/ENRICH 交付物结构、报告章节、附件清单、Done/Chargeable 标准 |

**后续 Wave 潜在扩展**（本版不实现）：

- M2 抽样 QA 实装后更新 `sample_validation` 字段示例
- Markdown 模板冻结后补充 `report.md` 段落映射
- `customer_ack` / `invoice` 实装后更新 Chargeable 判定流程
- `bridge_result.wave6.*` 实装后补充键名对照附录

---

*Wave 6 CLEAN Deliverable Templates · `04_Workflows/WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`*
