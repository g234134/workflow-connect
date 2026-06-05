# Wave 6 – CLEAN 产品矩阵规格（v0.1）

> **轮次**：Wave 6 · **性质**：产品线规格（product matrix spec）  
> **定位**：CLEAN-BASIC / CLEAN-ENRICH 产品包定义，供 intake / orchestrator / 计费对齐  
> **状态**：**DRAFT-v0.1**（产品线规格，非实现票）  
> **前置**：Wave 6 R4 裁定已冻结（`WAVE6_DATA_CLEANING_R4_RATIFICATIONS_v0.1.md`）

---

## 1. 背景与范围

Wave 6/7/8 技术底座（清洗 core + orchestrator + QA + report）已就绪。本文档将清洗能力包装为清晰的 **CLEAN** 产品线，定义两个核心产品包：

- **CLEAN-BASIC**：结构化日志 / CSV 清洗 + 基本校验
- **CLEAN-ENRICH**：在 BASIC 之上增加外部 API enrich、去重、规范化

本文档为**产品线规格**，描述各产品的输入输出契约、前置依赖与不承诺边界，供后续 intake、orchestrator、计费模块对齐。不含具体实现代码。

---

## 2. 产品包定义

### 2.1 CLEAN-BASIC

结构化日志或 CSV 的基础清洗与校验服务。

**功能概述**：
- Schema 校验（字段存在性、类型检查）
- 基本规则校验（数值范围、字符串长度、必填项）
- 格式标准化（日期、时间戳、布尔值）
- 缺失值标记（不填充，仅标记）
- 生成清洗报告与 QA 指标

**输入规格**：

| 维度 | 规格 |
|------|------|
| 文件类型 | CSV（RFC 4180）、NDJSON（每行独立 JSON）、结构化日志（单行 JSON） |
| 编码 | UTF-8（BOM 可选）、ASCII（兼容模式） |
| 字段要求 | 必须提供 `schema_ref`（字符串，指向 schema registry 或内嵌 schema）；行数据必须含 `record_id` 或允许自动生成 UUID |
| 典型规模下限 | 1 行 / 1 KB（最小计费单位见 billing_table） |
| 典型规模上限 | 100 万行 / 1 GB 单文件（超过需走 batch partition） |
| 压缩支持 | gzip（`.gz`）、zstd（`.zst`）— 自动检测解压 |

**输出规格**：

| 维度 | 规格 |
|------|------|
| 清洗后数据 | CSV / JSON Lines（与输入格式保持一致或按 `output_format` 指定） |
| 报告文件 | `report.json`（结构化 QA 指标）、可选 `report.md`（人工可读摘要） |
| QA 指标 | `total_units`（总行数）、`accepted_units`（通过清洗）、`rejected_units`（失败）、`warning_units`（警告但通过）、`schema_violations`（schema 不符统计） |
| 元数据 | `manifest.json`（含 `job_id`、`content_sha256_list[]`、`product_sku=CLEAN-BASIC`） |

**前置依赖**：

| 依赖类型 | 说明 |
|----------|------|
| API Key | 无需外部 API Key（纯本地/容器内处理） |
| 内部 DB | PostgreSQL（job lifecycle 持久化）、可选 Qdrant（清洗日志检索，非必需） |
| 权限 | 读取 input 路径、写入 `delivery.artifact_refs[]` 指向的存储位置 |
| Schema Registry | 若使用 `schema_ref` 而非内嵌 schema，需可访问 schema registry 服务 |

**不承诺范围 / 风险边界**：

- ❌ **不做 OCR**：不包含图片、PDF 扫描件的文字识别
- ❌ **不做复杂 NLP**：不执行语义分析、情感分析、实体抽取
- ❌ **不保证业务逻辑正确性**：仅做格式与 schema 校验，不验证业务规则（如「订单金额必须大于 0」需由上游保证）
- ⚠️ **大文件风险**：超过 1 GB 单文件未经验证，可能触发内存限制或分区失败
- ⚠️ **编码 fallback**：非 UTF-8/ASCII 编码可能产生乱码，不承诺自动转码成功

---

### 2.2 CLEAN-ENRICH

在 BASIC 基础上增加外部数据 enrich、去重、规范化的高级清洗服务。

**功能概述**：
- 继承 CLEAN-BASIC 全部功能
- 外部 API enrich（地址标准化、公司名补全、手机号归属地等）
- 去重（基于 fuzzy match 或指定 key 的精确去重）
- 数据规范化（统一地名格式、货币单位换算、时间时区统一）
-  enrich 调用链路追踪与失败降级

**输入规格**：

| 维度 | 规格 |
|------|------|
| 文件类型 | 同 CLEAN-BASIC（CSV、NDJSON、结构化日志） |
| 编码 | UTF-8（必需，因 enrich API 返回多为 UTF-8） |
| 字段要求 | 必须提供 `schema_ref`；**额外要求** `enrich_plan_ref`（描述需调用的 enrich API 列表与字段映射） |
| 典型规模下限 | 1 行 / 1 KB（与 BASIC 一致） |
| 典型规模上限 | 10 万行 / 500 MB 单文件（enrich API 调用频次与速率限制考虑） |
| 压缩支持 | gzip、zstd（同 BASIC） |

**输出规格**：

| 维度 | 规格 |
|------|------|
| 清洗后数据 | CSV / JSON Lines（含 enrich 新增字段，如 `_enrich_address_std`） |
| 报告文件 | `report.json`（含 enrich 子指标）、可选 `report.md` |
| QA 指标 | 继承 BASIC 指标，**新增**：`enrich_attempted`（尝试 enrich 行数）、`enrich_succeeded`（成功行数）、`enrich_failed`（失败行数）、`enrich_fallback_applied`（降级行数）、`dedup_groups_found`（去重组数）、`dedup_removals`（去重删除行数） |
| 元数据 | `manifest.json`（`product_sku=CLEAN-ENRICH` 或 `CLEAN-ENRICH-LLM`，依 enrich 类型） |

**前置依赖**：

| 依赖类型 | 说明 |
|----------|------|
| API Key | **必需**： enrich API 密钥（地址服务、工商数据服务等），按 `enrich_plan_ref` 配置 |
| 内部 DB | PostgreSQL（job lifecycle）、Qdrant（可选，用于 enrich 缓存去重） |
| 权限 | 读取 input、写入 output、**外网访问**（enrich API 调用） |
| Enrich Plan Registry | 必须可解析 `enrich_plan_ref` 指向的 enrich 计划定义 |
| Rate Limit 配额 | 需预配置或动态获取各 enrich API 的速率限制参数 |

**不承诺范围 / 风险边界**：

- ❌ **不做 OCR / 复杂 NLP**：同 BASIC；注意 LLM-based enrich 为单独 SKU（`CLEAN-ENRICH-LLM`）
- ❌ **外部 API 可用性不保证**：enrich 服务故障时仅降级（留空 enrich 字段或标记 `_enrich_failed`），不承诺 100% enrich 成功率
- ❌ **去重精度不保证**：fuzzy match 存在假阳性/假阴性，关键业务去重需人工复核
- ⚠️ **数据隐私风险**：含 PII 字段（手机号、地址）外发 enrich API 需提前签署 DPA
- ⚠️ **成本波动**：enrich API 按调用计费，大文件可能产生意外费用，建议先抽样测试

---

## 3. 产品对比矩阵

| 对比维度 | CLEAN-BASIC | CLEAN-ENRICH |
|----------|-------------|--------------|
| **输入格式** | CSV / NDJSON / 结构化日志 | 同 BASIC |
| **编码支持** | UTF-8、ASCII、BOM 可选 | UTF-8（必需） |
| **必需 schema** | `schema_ref` | `schema_ref` + `enrich_plan_ref` |
| **规模上限** | 100 万行 / 1 GB | 10 万行 / 500 MB（enrich API 限制） |
| **输出格式** | CSV / JSON Lines | CSV / JSON Lines（含 enrich 字段） |
| **QA 深度** | schema + 基本规则 | schema + 基本规则 + enrich 链路 + 去重 |
| **是否含 M2 抽样** | ❌ 否（仅 M1 全量检查） | ❌ 否（M2 为 Wave 8 能力） |
| **是否生成 report.md** | ✅ 可选 | ✅ 可选 |
| **外部依赖** | 无外部 API | enrich API 密钥 + 网络访问 |
| **计费 SKU** | `CLEAN-BASIC` | `CLEAN-ENRICH` / `CLEAN-ENRICH-LLM` |
| **典型场景** | 日志格式统一、CSV 基础校验 | 地址清洗、客户数据补全、去重合并 |

---

## 4. 计费与交付对齐

### 4.1 SKU 映射

| 产品包 | SKU（`product_sku`） | 计费单位（U） | 说明 |
|--------|----------------------|--------------|------|
| CLEAN-BASIC | `CLEAN-BASIC` | `accepted_units` 行数 | 按通过清洗的行数计费 |
| CLEAN-ENRICH | `CLEAN-ENRICH` | `accepted_units` 行数 | 非 LLM enrich（地址标准化等） |
| CLEAN-ENRICH-LLM | `CLEAN-ENRICH-LLM` | `accepted_units` 行数 | 含 LLM 调用（更高单价） |

### 4.2 交付物 URI 格式

遵循 R4 裁定 #H-2，逻辑 URI 格式固定为：

```
w6://delivery/{job_id}/{artifact_kind}
```

- `job_id`：本次交付的 job_record.job_id（UUID）
- `artifact_kind`：`manifest`、`report_json`、`report_md`、`deliverables`

### 4.3 upgrade 场景（BASIC → ENRICH）

遵循 R4 裁定 #I-1：

| JOB-B 状态 | JOB-E 发票行为 |
|------------|----------------|
| 已开票 | JOB-E 仅含 ENRICH 行项 |
| 未开票且无豁免 | 允许单张合并发票（`basic_unbilled_merge`） |
| 未开票但有豁免 | JOB-E 仅含 ENRICH 行项 |

---

## 5.  intake / orchestrator 对齐要点

### 5.1 intake 校验

- **BASIC**：校验文件编码、格式、schema_ref 可解析
- **ENRICH**：额外校验 enrich_plan_ref 存在、API Key 有效、网络可达

### 5.2 orchestrator 阶段映射

```text
intake → raw_load → clean_basic → [clean_enrich] → qa_m1 → report_summary → finalize
```

- `clean_enrich` 阶段仅在 product_sku 为 ENRICH/ENRICH-LLM 时启用
- 各阶段失败语义见 `WAVE7_ORCH_JOB_LIFECYCLE_v0.1.md`

### 5.3 与 Wave 7/8 的边界

| 能力 | 所在 Wave | 说明 |
|------|-----------|------|
| M2 抽样 QA | Wave 8 | 本规格仅定义 M1 全量检查 |
| Markdown 报告渲染 | Wave 8 | `report.md` 为占位，渲染引擎在 W8 |
| BASIC→ENRICH upgrade job | Wave 8 | 本规格定义 upgrade 计费规则，实现不在 W6 |
| bridge sidecar | Wave 8 | 本规格不涉及 |

---

## 6. 版本与演进

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草案：BASIC / ENRICH 双产品定义、输入输出规格、计费对齐 |

**下一版预期内容**（需尚书省裁定）：
- 增加 `CLEAN-ENTERPRISE`（含 PII mask、KMS 加密、SLA 承诺）
- M2 抽样 QA 规格（Wave 8 落地后回填）
- 多语言编码自动检测规格

---

*Wave 6 CLEAN Product Matrix · `04_Workflows/WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`*
