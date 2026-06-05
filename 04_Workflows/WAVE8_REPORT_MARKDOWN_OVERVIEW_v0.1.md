# Wave 8 – REPORT-MD · 总览（v0.1）

> **轮次**：Wave 8 · **性质**：planning / external delivery layer (first slice)  
> **前置**：Wave 7 已交付 `report.json` 真相层、artifact storage、`w6://delivery/{job_id}/report_md` 占位  
> **本波第一块**：仅 **Markdown 报告渲染**（`ART-DATA-CLEAN-REPORT`）；不改 `report.json` schema  
> **状态**：**PLANNED-v0.1**

---

## 1. 范围摘要

Wave 8 对外交付层的第一块：把 Wave 7 已落盘的 **`report.json`** 渲染为对人可读的 **Markdown**（文件名惯例 `report.md`，逻辑名 **`ART-DATA-CLEAN-REPORT`**，R4 `artifact_kind=report_md`）。

| 项 | 裁定 |
|----|------|
| **输入** | 固定为 `report.json`（+ 可选模板/配置 + 可选 **展示侧车** `display_context`，见 §5） |
| **输出** | UTF-8 Markdown 文本；后续可转 PDF/HTML（本波不做） |
| **原则** | **不计算新真相**；只做展示、解释、排版与免责声明 |
| **不做** | M2 实作、`customer_ack`、invoice、bridge sidecar、财务牌价填数、`report.json` 结构变更 |

路径与 ref 一律经 `Master_Map.json` / `gov_paths`；对外引用 `w6://delivery/{job_id}/{kind}`（R4 §3），**禁止**磁盘绝对路径。

---

## 2. 目标受众与内容块

### 2.1 受众

| 受众 | 用途 | 默认裁剪 |
|------|------|----------|
| **客户（customer）** | 交付验收、存档、商务对账前的「可读摘要」 | 隐藏内部 check_id 细表可选折叠；强调 QA 结论与计费单位；**不**暗示已开票 |
| **内部（internal）** | CS / 运营 / 工程排障 | 完整 failures 表、`remediation_hint`、schema 版本、与 `completion_variant` 对照说明 |

同一份 `report.json` 可通过配置 `audience=customer|internal` 切换章节深度（模板票定义）。

### 2.2 建议章节（`ART-DATA-CLEAN-REPORT`）

| § | 章节 ID | 标题（示例） | 主要数据源 |
|---|---------|--------------|------------|
| 0 | `meta` | 报告元数据 | `report.schema_version`、`report.job_id`、渲染时间（生成侧）、可选 `display_context.client_ref` |
| 1 | `executive_summary` | 执行摘要 | `summary.*`、`qa.overall_ok`、可选 `display_context.completion_variant` |
| 2 | `volume` | 处理量与计费单位 | `accepted_units`、`rejected_units`、`total_rows`、`billing_units` |
| 3 | `qa_m1` | 清单完整性（M1） | `qa.manifest_integrity` |
| 4 | `qa_m2` | 抽样校验（M2） | `qa.sample_validation`（Wave 7 常为 `skipped`） |
| 5 | `qa_failures` | 质量问题明细 | `qa.failures[]`（空则省略或写「无」） |
| 6 | `cost_skeleton` | 费用结构（未开票） | `summary.cost`、`chargeable_hint` |
| 7 | `artifacts` | 交付物索引 | 配置注入的 `w6://` refs（**非**从 report 重算路径） |
| 8 | `disclaimers` | 声明与下一步 | 固定文案 + 按 `qa_status` / M2 状态分支 |
| A | `appendix_internal` | 内部附录（可选） | `display_context`、原始 `qa_status` 映射说明 |

详细段落、表格列、可选图表占位 → `W8_REPORT_MD_TEMPLATE_AND_SECTIONS_v0.1.md`。

---

## 3. 与 `report.json` 的字段映射（只读）

Wave 7 生产者（`wave7_report_summary_producer`）当前形状：

```text
report
├── schema_version          # wave7_report_v0.1
├── job_id
├── summary
│   ├── job_id, sku
│   ├── accepted_units, rejected_units, total_rows
│   ├── billing_units { U, L }
│   ├── qa_status         # pass | pass_with_warnings | fail
│   ├── cost              # R2 §A.4 skeleton（amount 可为 null）
│   └── chargeable_hint   # bool，非最终 Chargeable 裁定
└── qa
    ├── manifest_integrity  # { ok, checked_rows, failed_rows, failed_checks }
    ├── failures[]          # qa_failure_record（R3 §G.5）
    ├── sample_validation   # Wave 7: 常 status=skipped
    └── overall_ok          # M1 ok ∧ sample_validation.ok
```

Markdown 渲染器 **不得** 重算 `accepted_units`、`qa_status`、`overall_ok` 或 cost 金额；仅格式化与解释既有值。

---

## 4. 与 Wave 6/7 / 财务 / bridge 的边界

| 邻域 | 关系 |
|------|------|
| **Wave 7 `report.json`** | 唯一真相来源；Wave 8 单向依赖 |
| **Wave 7 artifact store** | 落盘 `report.md`、登记 `w6://.../report_md`；Wave 7 占位文案由 Wave 8 替换 |
| **M2 抽样 QA** | 属 Wave 8+ 独立票；本渲染票 **消费** `sample_validation` 各状态（含 `skipped`），不实现 M2 |
| **`customer_ack`** | R2 §A.6 / R3 §H.3；**不在** Markdown 中写入或推断；可声明「客户确认未记录」 |
| **invoice / Chargeable** | R2 §A.7–A.8；Markdown **显式标注「未开票／非发票」**；`chargeable_hint` 仅作提示 |
| **bridge sidecar** | R3 §H 为 SPEC-ONLY；本波不写 `bridge_result.wave6.report.*` |
| **job lifecycle** | `completion_variant`（如 `completed_with_failures`）在 **`job_record`**，不在 `report.json`；经 **展示侧车** 传入（见 §5） |

---

## 5. 单向依赖与「展示侧车」

### 5.1 单向依赖（硬规则）

```text
manifest + QA-M1  →  report.json  →  Markdown (ART-DATA-CLEAN-REPORT)
                         ↑
                    禁止反向：Markdown 不得回写或修补 report.json
```

- 渲染失败 **不得** 修改 QA 结果或 summary 数字。  
- 若 `report.json` 缺失字段，渲染器应 **降级展示**（标 N/A）或 `ok: false` 回传，**不得** 用 manifest 重算补洞（补洞属 Wave 7 生产者职责）。

### 5.2 可选 `display_context`（非真相）

以下字段 **不在** 当前 `report.json` 内，可由编排集成票在渲染时注入，**仅用于排版与说明**：

| 键 | 来源 | 用途 |
|----|------|------|
| `completion_variant` | `run_wave7_job` → `job_record` | 解释「已完成但有拒收行」 |
| `client_ref` | intake / job_record | 报告抬头 |
| `artifact_refs` | storage 回传 | §7 交付物索引表 |
| `generated_at` | 渲染时刻 ISO8601 | 页眉 |
| `run_status` | lifecycle `status` | 与 `qa_status` 对照脚注 |

**禁止** 把 `display_context` 写成客户可当作合同的 Chargeable／Done 依据。

### 5.3 QA 状态呈现（M1 / M2）

| 层级 | 字段 | Markdown 呈现要点 |
|------|------|-------------------|
| **汇总** | `summary.qa_status` | 醒目标签：`通过` / `通过（有警告）` / `未通过`；映射 R3 §G.6 |
| **M1** | `qa.manifest_integrity` | 表格：checked / failed rows / failed_checks + `ok` 徽章 |
| **M2** | `qa.sample_validation` | `status=skipped` → 固定说明：「抽样 QA 未在本版本执行，不影响 M1 结论展示」；`ok=false` 时红色提示；**不** 假装已抽样 |
| **聚合** | `qa.overall_ok` | 与 `qa_status` 并列；注明 Wave 7 下 `overall_ok` 主要反映 M1 |
| **明细** | `qa.failures[]` | 按 `layer`（M1/M2）、`severity` 排序表格；P0/P1/P2 徽章；`remediation_hint` 人类可读枚举 |

### 5.4 `completed_with_failures` 与 `qa_status` 分栏

二者 **不同层**（对齐 `WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md` §5）：

| 概念 | 数据位置 | Markdown 处理 |
|------|----------|---------------|
| `qa_status` | `report.summary` | §1 摘要 + §3 QA 主结论 |
| `completed_with_failures` | `display_context.completion_variant` | §1 单独「作业完成形态」说明：「流水线已结束，部分输入行未纳入交付；QA 清单校验无 P0」 |

**禁止** 在客户版报告中把 `completed_with_failures` 写成 `qa_status=pass` 的同义句而不加解释。

### 5.5 Cost skeleton（未开票）

| 元素 | 呈现规则 |
|------|----------|
| 章节标题 | 必须含 **「费用结构（预估 · 未开票）」** 或等价措辞 |
| `line_items[]` | 表格：SKU、unit、quantity；`unit_price` / `amount` 为 `null` 时显示「待财务表」 |
| `amount_*` | 全部为 null 时汇总行写「—」 |
| `chargeable_hint` | `false` → 脚注：「牌价未配置或不可计费，非最终 Chargeable 裁定」；`true` → 仍注明「需 customer_ack 与 invoice 后方为正式收费」 |
| 禁止用语 | 不得出现「发票」「已开票」「应付金额」作为确定值（除非未来独立票扩展且改 schema） |

---

## 6. 票面索引

| 票名 | 文件 | 一句话 |
|------|------|--------|
| `REPORT-MD-TEMPLATE` | `W8_REPORT_MD_TEMPLATE_AND_SECTIONS_v0.1.md` | Markdown 结构、段落、表格与可选图表占位 |
| `REPORT-MD-RENDER` | `W8_REPORT_MD_RENDER_ENGINE_v0.1.md` | `report.json` → Markdown 纯函数 + CLI |
| `REPORT-MD-ORCH` | `W8_REPORT_MD_ORCH_INTEGRATION_v0.1.md` | Wave 7 lifecycle 之后可选生成 `report.md` |
| `REPORT-MD-RUNBOOK` | `W8_REPORT_MD_RUNBOOK_v0.1.md` | CS/运营「怎么看报告」说明书 |

### 6.1 建议实施顺序

```text
TEMPLATE → RENDER → ORCH-INTEGRATION → RUNBOOK
```

- 模板与渲染可并行定稿，但 **先锁章节契约** 再写渲染器。  
- 编排集成依赖渲染器 CLI/API 稳定。  
- Runbook 在首版样例 Markdown 冻结后撰写。

---

## 7. Wave 8 本切片 Done（规划级）

- [ ] 从真实 Wave 7 `report.json` 样例生成客户版 + 内部版 Markdown 各 1 份（快照测试）。  
- [ ] `report.md` 替换 artifact store 占位；`w6://delivery/{job_id}/report_md` 可解析。  
- [ ] 文档明确：不改 `report.json`、不写 invoice/ack/bridge。  
- [ ] Runbook 覆盖 `qa_status` / `skipped` M2 / `completed_with_failures` / cost skeleton 读法。

---

## 8. 占位 / 后续 Wave 8 票（不在本切片）

| 项 | 说明 |
|----|------|
| M2 抽样 QA 实作 | 独立票；本切片只渲染其输出 |
| PDF/HTML 导出 | 下游工具链 |
| `customer_ack` / invoice | Phase 6.5 / 财务波 |
| bridge `wave6.report.*` 写入 | SPEC-ONLY 扩展 |
| 多语言 i18n | v0.1 仅 zh-CN 正文 |

---

*Wave 8 planning overview · `04_Workflows/WAVE8_REPORT_MARKDOWN_OVERVIEW_v0.1.md`*
