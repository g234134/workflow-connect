# Wave 7 – CLEAN-Orchestrator 工具整合接口草案（v0.1）

> **票号**：`CLEAN-ORCH-TOOL-INTEGRATION`  
> **性质**：spec / planning（**只定义工具接口；不写实现**）  
> **受众**：未来 Phase 8.6/8.7 Tool Catalog / Selector、CLEAN-Orchestrator 编排、HQ 协调整合  
> **前置**：`WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md`、`WAVE7_CLEAN_RUNNER_ORCH_OVERVIEW_v0.1.md`、`WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`、`SPEC_tool_layer_vnext_draft.md`  
> **实现锚点**（只读对照）：暗部 `core/wave6_*`、`core/envelope_writer.py`、`core/wave7_*`、`core/wave8_*`  
> **状态**：**DRAFT-v0.1**

---

## 0. 文档目的

Wave 6/7/8 已具备 envelope、manifest、M1/M2 QA、report、artifact store、job lifecycle 等**可运行模块**。将来 Phase 8.6/8.7 的 **Tool Catalog / Selector** 需要知道：CLEAN-Orchestrator **会 call 哪些工具类别**、每类的 **输入 / 返回 / 错误码**，以及与现有模块的 **映射关系**。

本文：

- **定义** orchestrator 侧工具清单与统一 `dict` 外形（`ok` / `payload` / `errors`）；
- **标注** 与 Wave 6/7/8 模块、逻辑阶段 S0–S5 的对应；
- **不** 实现 Catalog/Selector/Executor；**不** 新增 envelope/manifest/QA 业务规则。

---

## 1. 统一工具响应外形（Orchestrator 归一化层）

现有模块多直接返回 `{ok, message, error_code?, ...}`。Orchestrator（或未来 Executor）在对外暴露 Tool Catalog 时，**建议归一化**为：

```json
{
  "ok": true,
  "message": "human-readable summary",
  "error_code": null,
  "payload": {},
  "errors": [],
  "trace": {
    "tool_id": "CLEAN-QA-M1",
    "job_id": "w7-basic-acme-…",
    "stage": "S4",
    "runtime_stage": "qa",
    "started_at": "ISO-8601",
    "finished_at": "ISO-8601"
  }
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `ok` | 是 | 工具调用是否达到契约成功（**不**等同 job 终态 `done`） |
| `message` | 是 | 摘要；失败时含可操作语义 |
| `error_code` | 否 | 稳定机器码；成功时为 `null` |
| `payload` | 否 | 工具专有产物（见各节 `payload` 表） |
| `errors` | 否 | 结构化错误列表（可多行/多检查项） |
| `trace` | 否 | 可观测；对齐 `SPEC_tool_layer_vnext_draft` §3 `observability_fields` |

**`errors[]` 元素建议形状**（与 M1/M2 `failures[]` 对齐）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 稳定码（如 `M1-COUNT`、`schema_parse_failed`） |
| `severity` | string | `P0` / `P1` / `info`（QA 类必填） |
| `message` | string | 人读说明 |
| `row_ref` | string | 可选；manifest 行或文件逻辑 ref |
| `detail` | object | 可选；禁止绝对磁盘路径 |

**路径约束**：入参/出参中的路径均为 **逻辑路径**（`cleaned_full/…`、`w6://delivery/{job_id}/…`）或 **repo 相对名**；禁止泄漏本机绝对路径（继承工程合约 Rule 6）。

---

## 2. 工具清单总览

### 2.1 主清单（用户指定 + 编排必需邻接项）

| tool_id | 逻辑阶段 | 实现状态 | 暗部模块 / 入口（对照） |
|---------|----------|----------|-------------------------|
| `CLEAN-SAMPLE-ANALYZE` | S1 | **PLANNED**（S1 预检；无独立模块） | —；设计锚点：`wave8_m2_sampling_design`（计划子集） |
| `CLEAN-CSV-TRANSFORM` | S3 上游 | **PLANNED**（产品线 `clean_basic`/`clean_enrich`） | —；消费 `cleaned_full` 由 runner 间接接入 |
| `CLEAN-VALIDATE-SCHEMA` | S0–S3 | **PARTIAL** | `wave6_intake_gate`、`envelope_writer` / `build_envelope`、`wave8_m2_execution_engine`（M2 深检） |
| `CLEAN-QA-M1` | S4 | **DONE** | `wave6_qa_manifest_m1.run_m1_checks` |
| `CLEAN-QA-M2` | S4 | **DONE** | `wave8_m2_sampling_design` + `wave8_m2_execution_engine`；编排：`wave7_orch_pipeline_wire.execute_m2_checks` |
| `CLEAN-REPORT-RENDER` | S5 | **DONE**（MD）；JSON：**DONE** | `wave8_report_md_renderer`；`wave7_report_summary_producer.build_wave7_report` |
| `CLEAN-INTAKE-GATE` | S0 | **DONE** | `wave6_intake_gate.run_intake_gate` |
| `CLEAN-RUNNER-ENTRY` | S0 | **DONE** | `wave7_runner_entry_job_input.build_runner_job_input` |
| `CLEAN-ENVELOPE-WRITE` | S3 | **DONE** | `envelope_writer.write_envelopes` |
| `CLEAN-MANIFEST-WRITE` | S3 | **DONE** | `wave6_manifest_writer.write_manifest` |
| `CLEAN-PIPELINE-RUN` | S3–S4 | **DONE** | `wave7_orch_pipeline_wire.run_wave6_pipeline` |
| `CLEAN-REPORT-BUILD` | S5 | **DONE** | `wave7_report_summary_producer.build_wave7_report` |
| `CLEAN-ARTIFACT-STORE` | S5 | **DONE** | `wave7_artifact_storage.store_wave7_artifacts` |
| `CLEAN-JOB-RUN` | S0–S5 | **DONE** | `wave7_orch_job_lifecycle.run_wave7_job` |
| `CLEAN-M2-SAMPLING-PLAN` | S1 | **DONE** | `wave8_m2_sampling_design.build_sampling_plan` |

### 2.2 与 Tool Catalog vNext 的 tier 建议

| tool_id 前缀 | `tool_tier` | `intent_tags`（示例） |
|--------------|-------------|----------------------|
| `CLEAN-*` | `orchestration` | `data_cleaning`, `wave6`, `wave7`, `manifest`, `qa` |
| 上游 `CLEAN-CSV-TRANSFORM` | `orchestration` | `transform`, `clean_basic`, `clean_enrich` |

Selector（Phase 8.6/8.7）在 **intake accept** 之后，按 `job_record.sku`、阶段 `stage`、以及 `runtime_context` 中的 artifact 键（如 `manifest_ref`）过滤上表；**禁止** Selector 改写 Wave 6 冻结 QA 规则。

---

## 3. 工具接口规格

以下各节：**输入** = Catalog `input_schema` 逻辑字段；**payload** = 成功时 `payload` 内容；**典型错误码** = `error_code` 或 `errors[].code`。

---

### 3.1 `CLEAN-SAMPLE-ANALYZE`

**定位**：S1「Schema 分析 & 采样检查」— 对批次做**预检抽样**（结构、编码、字段覆盖率预览），并可选输出 M2 计划输入统计；**不**执行 M2 深检。

| 项 | 说明 |
|----|------|
| **逻辑阶段** | S1 |
| **模块映射** | **无独立实现**；计划子集见 `wave8_m2_sampling_design`（`N`、`per_extension_counts`）；预检语义见 `WAVE7_CLEAN_ORCH_TASK_MODEL` §S1 |
| **实现状态** | **PLANNED** |

**输入**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `job_id` | 是 | string | 作业 ID |
| `product_sku` | 是 | string | `CLEAN-BASIC` / `CLEAN-ENRICH` |
| `raw_files` | 是 | array | S0 产出的 `raw_files[]`（或逻辑路径列表 + 元数据） |
| `schema_ref` | 条件 | string | SKU 要求时必填（产品矩阵 §5.1） |
| `sample_limit` | 否 | int | 预检最大行数/文件数（默认小常数，如 5–20） |
| `schema_hint` | 否 | object | 内嵌 schema 片段或 registry 解析结果 |
| `enrich_plan_ref` | 条件 | string | ENRICH SKU 时必填 |

**返回 `payload`（成功）**

| 字段 | 说明 |
|------|------|
| `schema_analysis` | `{ok, schema_version, violations_preview[], field_coverage_preview?}` |
| `preflight_sample` | `{files_checked, rows_checked, extension_histogram?, warnings[]}` |
| `sampling_hints` | `{N_estimate, per_extension_counts?}` — 供 `CLEAN-M2-SAMPLING-PLAN` |

**典型错误码**

| code | 场景 |
|------|------|
| `sample_empty_batch` | `raw_files` 为空 |
| `schema_unresolvable` | `schema_ref` 无法解析 |
| `preflight_parse_failed` | 样例文件/行解析失败 |
| `sku_schema_mismatch` | 字段与 SKU 策略冲突 |

---

### 3.2 `CLEAN-CSV-TRANSFORM`

**定位**：产品线矩阵中的 **`raw_load → clean_basic → [clean_enrich]`**；将 CSV/NDJSON/结构化日志转为 **`cleaned_full` JSON**（runner 消费的 `raw_files` 上游形态）。

| 项 | 说明 |
|----|------|
| **逻辑阶段** | S3 上游（常在 S0 之前或并行） |
| **模块映射** | **无 Wave 6/7/8 冻结模块**；编排器当前默认 **已存在** `cleaned_full`（`wave7_runner_entry_job_input`） |
| **实现状态** | **PLANNED** |

**输入**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `job_id` | 是 | string | 作业 ID |
| `product_sku` | 是 | string | BASIC / ENRICH |
| `cleaning_profile` | 是 | object | S2 锁定配置：`schema_ref`, `output_format`, `rule_pack_version`, `enrich_plan_ref?` |
| `inbound_logical_paths` | 是 | string[] | 原始输入逻辑路径（非绝对路径） |
| `manifest_path` | 否 | string | 批次清单（逻辑或 repo 相对） |
| `dedup_policy` | 否 | object | ENRICH 去重策略 |

**返回 `payload`（成功）**

| 字段 | 说明 |
|------|------|
| `cleaned_records` | array | 行级清洗结果（将经 `map_cleaned_record_to_raw_file` 映射） |
| `transform_stats` | `{total_units, accepted_units, rejected_units, warning_units, schema_violations}` |
| `output_logical_dir` | string | 建议 `cleaned_full/{job_id}/` |

**典型错误码**

| code | 场景 |
|------|------|
| `transform_unsupported_format` | 非 CSV/NDJSON/结构化日志 |
| `transform_encoding_error` | 编码失败 |
| `transform_schema_violation` | 行级 schema 硬失败 |
| `transform_enrich_failed` | ENRICH 链路失败 |
| `transform_empty_output` | 零行产出 |

---

### 3.3 `CLEAN-VALIDATE-SCHEMA`

**定位**：跨阶段 **schema 校验** 统一工具面：intake 可解析性、envelope v2 模型、M2 抽样 envelope 深检中的 schema 类检查。

| 项 | 说明 |
|----|------|
| **逻辑阶段** | S0（intake）、S3（envelope）、S4（M2 子检查） |
| **模块映射** | `wave6_intake_gate`（请求模型校验）；`envelope_writer.build_envelope`（`EnvelopeV2`）；M2：`M2-SCHEMA-20` 等（`wave8_m2_execution_engine`） |
| **实现状态** | **PARTIAL**（分散在现有模块，无单一 `validate_schema()` 门面） |

**输入**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `validation_scope` | 是 | string | `intake` \| `envelope` \| `manifest_row` \| `m2_envelope` |
| `product_sku` | 是 | string | SKU 规则分支 |
| `payload` | 是 | object | 待验对象（`IntakeGateRequest` / raw_file / manifest row / envelope） |
| `schema_ref` | 条件 | string | scope 需要时 |
| `schema_hint` | 否 | object | 内嵌 schema |

**返回 `payload`（成功）**

| 字段 | 说明 |
|------|------|
| `valid` | bool | 是否通过 |
| `schema_version` | string | 如 `2.0` |
| `violations` | array | `{code, path, message}` |
| `gate_checks` | array | scope=`intake` 时对齐 `gate_checks[]` |

**典型错误码**

| code | 场景 |
|------|------|
| `schema_validation_failed` | 存在违规 |
| `schema_unknown_scope` | 非法 `validation_scope` |
| `SCHEMA-VIOLATION` | 对齐交付模板 P0 类 |
| `absolute_path_forbidden` | intake 路径泄漏 |

---

### 3.4 `CLEAN-QA-M1`

**定位**：S4 全量 manifest 完整性检查（**仅 manifest 层**，不打开 envelope 做 BASIC 深检）。

| 项 | 说明 |
|----|------|
| **逻辑阶段** | S4 |
| **模块映射** | `core/wave6_qa_manifest_m1.py` → `run_m1_checks` |
| **实现状态** | **DONE** |

**输入**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `job_id` | 是 | string | |
| `job_record` | 是 | object | 至少 `job_id`, `sku` |
| `manifest` | 是 | object | `ManifestV20` 或 contract dict（含 `rows[]`） |
| `report_summary` | 是 | object | 至少 `accepted_units`（来自 report 或 `build_summary_for_m1_checks`） |

**返回 `payload`（成功）**

| 字段 | 说明 |
|------|------|
| `qa` | object | 模块原生：`{manifest_integrity, failures}` |
| `manifest_integrity` | `{ok, checked_rows, failed_rows, failed_checks}` |

**典型错误码 / `errors[].code`**

| code | severity | 场景 |
|------|----------|------|
| `M1-KEYS` | P0 | 缺必填 manifest 行键 |
| `M1-SHA` | P0 | `content_sha256` 非法 |
| `M1-SKU-BASIC` | P0 | BASIC 行含 `enrichment` |
| `M1-SKU-ENRICH` | P0 | ENRICH ok 行缺 `has_enrichment` |
| `M1-DEDUP` | P0 | 重复 sha |
| `M1-COUNT` | P0 | `accepted_units` 与 ok 行数不一致 |
| `M1-OK-ONLY` | P0 | accepted 含非 ok 行 |

工具级 `ok`：**建议** `ok = manifest_integrity.ok`（与模块一致）。

---

### 3.5 `CLEAN-QA-M2`

**定位**：S4 按 S1 抽样计划对 ok 行回读 envelope 做深检。

| 项 | 说明 |
|----|------|
| **逻辑阶段** | S4（计划 S1：`CLEAN-M2-SAMPLING-PLAN`） |
| **模块映射** | 计划：`wave8_m2_sampling_design.build_sampling_plan`；执行：`wave8_m2_execution_engine.run_m2_checks`；编排：`wave7_orch_pipeline_wire.execute_m2_checks` |
| **实现状态** | **DONE** |

**输入**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `job_id` | 是 | string | |
| `job_record` | 是 | object | |
| `manifest` | 是 | object | 全量 manifest |
| `envelopes` | 条件 | array | 内存 loader；或提供 `envelope_loader` 回调键 |
| `sampling_plan` | 是 | object | `{N, sample_size, seed, row_indexes, billing_table_version}` |
| `manifest_integrity_ok` | 是 | bool | M1 未 P0 时为 false 则跳过抽样 |
| `billing_table` | 否 | object \| string | 版本推导 |
| `strict_m2` | 否 | bool | 意外错误是否升格 job 失败（lifecycle） |

**返回 `payload`（成功）**

| 字段 | 说明 |
|------|------|
| `sample_validation` | `{ok, status, N, sample_size, seed, reason?}` |
| `failures` | M2 检查项列表 |
| `overall_ok` | bool | 用于合并进 `report.qa` |

**典型错误码 / `errors[].code`**

| code | severity | 场景 |
|------|----------|------|
| `M2-SCHEMA-20` | P0 | envelope schema 不合 |
| `M2-GROQ-BASIC` | P0 | BASIC 出现 groq |
| `M2-ENRICH-*` | P0/P1 | ENRICH 块违规 |
| `M2-QUALITY` | P1 | 质量分阈值 |
| `M2-PATH-LEAK` | P0 | 路径泄漏 |
| `M2-PREVIEW-LEN` | P1 | 预览长度 |
| `m2_skipped` | info | M1 失败或 `sample_size=0` |
| `m2_engine_error` | P0 | `strict_m2` 时意外异常 |

---

### 3.6 `CLEAN-REPORT-RENDER`

**定位**：S5 将 **`report.json`** 渲染为客户可读 **`report.md`**（可选）；与 `CLEAN-REPORT-BUILD` 区分：后者产 JSON，本工具产 Markdown。

| 项 | 说明 |
|----|------|
| **逻辑阶段** | S5 |
| **模块映射** | `wave8_report_md_renderer.render_data_clean_report` / `render_report_md` |
| **实现状态** | **DONE**（MD）；依赖 `wave7_report_summary_producer` 产出 JSON |

**输入**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `job_id` | 是 | string | |
| `report` | 是 | object | 完整 `report.json` 契约 |
| `manifest_path` | 否 | string | 逻辑 ref；用于 artifact 节 cross-ref |
| `config` | 否 | object | `audience`, `include_appendix_internal`, `generated_at` |
| `display_context` | 否 | object | CS 展示上下文 |
| `artifact_refs` | 否 | object | `w6://delivery/…` 逻辑 ref 映射 |

**返回 `payload`（成功）**

| 字段 | 说明 |
|------|------|
| `markdown` | string | 完整 MD 正文 |
| `report_logical_ref` | string | 建议 `w6://delivery/{job_id}/report.md` |

**典型错误码**

| code | 场景 |
|------|------|
| `report_md_validation_failed` | 缺必填 report 块 |
| `report_md_render_failed` | 渲染异常 |
| `report_md_empty` | 成功但零长度（应视为失败） |

**隔离语义**：默认 `strict_report_md=false` 时，渲染失败 **不** rollback `report.json`（lifecycle 已文档化）。

---

## 4. 编排邻接工具（简表）

Orchestrator 单 job 链常用；接口细节见各 Wave 7 票，此处仅列 **映射** 与 **最小输入/错误码**。

### 4.1 `CLEAN-INTAKE-GATE`

| 项 | 值 |
|----|-----|
| 阶段 | S0 |
| 模块 | `wave6_intake_gate.run_intake_gate` |
| 输入 | `intake_request`（`client_ref`, `product_sku`, `inbound_path_hint`, …） |
| payload | `{decision, work_category, gate_checks, reasons, …}` |
| 错误码 | `intake_rejected`, `intake_deferred`, `absolute_path_forbidden` |

### 4.2 `CLEAN-RUNNER-ENTRY`

| 项 | 值 |
|----|-----|
| 阶段 | S0 |
| 模块 | `wave7_runner_entry_job_input.build_runner_job_input` |
| 输入 | `sku`, `client_ref`, `cleaned_dir?`, `manifest_path?`, `queue_payload?`, `intake_request?`, `job_id?` |
| payload | `{job_record, raw_files, input_count, skipped}` |
| 错误码 | `empty_batch`, `unknown_sku`, `intake_rejected`, `invalid_cleaned_json`, `manifest_empty`, `no_input_source` |

### 4.3 `CLEAN-ENVELOPE-WRITE`

| 项 | 值 |
|----|-----|
| 阶段 | S3 |
| 模块 | `envelope_writer.write_envelopes` |
| 输入 | `job_record`, `raw_files[]` |
| payload | `{envelopes[]}` |
| 错误码 | `envelope_stage_failed`（编排层）；`EnvelopeWriterError` 消息入 `errors` |

### 4.4 `CLEAN-MANIFEST-WRITE`

| 项 | 值 |
|----|-----|
| 阶段 | S3 |
| 模块 | `wave6_manifest_writer.write_manifest` |
| 输入 | `job_record`, `envelopes`（经 `normalize_manifest_inputs`）, `billing_table?` |
| payload | `{manifest}`（`ManifestV20`） |
| 错误码 | `manifest_stage_failed` |

### 4.5 `CLEAN-PIPELINE-RUN`

| 项 | 值 |
|----|-----|
| 阶段 | S3–S4（内存链） |
| 模块 | `wave7_orch_pipeline_wire.run_wave6_pipeline` |
| 输入 | `job_record`, `raw_files[]`, `enable_m2?`, `strict_m2?`, `billing_table?` |
| payload | `{envelopes, manifest, qa, report}` |
| 错误码 | `envelope_stage_failed`, `manifest_stage_failed`, `qa_stage_failed`；`stage` ∈ `{envelope, manifest, qa}` |

### 4.6 `CLEAN-REPORT-BUILD`

| 项 | 值 |
|----|-----|
| 阶段 | S5 |
| 模块 | `wave7_report_summary_producer.build_wave7_report` |
| 输入 | `job_record`, `manifest`, `qa_m1_result`, `billing_table?`, `m2_result?` |
| payload | `{report}` |
| 错误码 | `report_build_failed` |

### 4.7 `CLEAN-ARTIFACT-STORE`

| 项 | 值 |
|----|-----|
| 阶段 | S5 |
| 模块 | `wave7_artifact_storage.store_wave7_artifacts` |
| 输入 | `job_id`, `sku`, `envelopes?`, `manifest?`, `report?`, `mode`, `paths_resolved?` |
| payload | `{artifact_refs, paths_logical, idempotent_hit}` |
| 错误码 | `invalid_job_id`, `artifact_io_failed`, `bootstrap_failed` |

### 4.8 `CLEAN-M2-SAMPLING-PLAN`

| 项 | 值 |
|----|-----|
| 阶段 | S1 |
| 模块 | `wave8_m2_sampling_design.build_sampling_plan` |
| 输入 | `n`（ok 行数 N）, `billing_table_version?`, `per_extension_counts?` |
| payload | `{sampling_plan}` |
| 错误码 | `invalid_sample_n`, `invalid_extension_counts` |

### 4.9 `CLEAN-JOB-RUN`（组合工具）

| 项 | 值 |
|----|-----|
| 阶段 | S0–S5 |
| 模块 | `wave7_orch_job_lifecycle.run_wave7_job` |
| 输入 | runner 参数或 `{job_record, raw_files}`；`enable_m2`, `render_report_md`, `resume_context?`, … |
| payload | `{status, stage, artifacts, qa, completion_variant, artifact_refs}` |
| 错误码 | 各子阶段码 + `storage_failed`, `qa_p0_blocked` |

---

## 5. 编排调用顺序（参考）

与 `WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1` 对齐的 **默认工具链**（单 job）：

```text
CLEAN-INTAKE-GATE? ──▶ CLEAN-RUNNER-ENTRY
        │
        ▼
CLEAN-SAMPLE-ANALYZE? ──▶ CLEAN-M2-SAMPLING-PLAN?
        │                      (S1 可选)
CLEAN-CSV-TRANSFORM? ──▶ (产出 cleaned_full / raw_files)
        │
        ▼
CLEAN-ENVELOPE-WRITE ──▶ CLEAN-MANIFEST-WRITE
   (或 CLEAN-PIPELINE-RUN 一次调用)
        │
        ▼
CLEAN-REPORT-BUILD ──▶ CLEAN-QA-M1 ──▶ CLEAN-QA-M2?
        │                    ▲              (enable_m2)
        └────────────────────┘
        ▼
CLEAN-ARTIFACT-STORE ──▶ CLEAN-REPORT-RENDER?
        │
        ▼
CLEAN-JOB-RUN  （对外单一入口，内嵌上述步骤）
```

**Checkpoint 重试**（lifecycle）：`manifest` 已落盘后，可跳过 envelope/manifest 重跑 `CLEAN-QA-M1`、`CLEAN-REPORT-BUILD`、`CLEAN-REPORT-RENDER`、`CLEAN-ARTIFACT-STORE`。

---

## 6. Wave 6/7/8 模块对照矩阵

| tool_id | 暗部 Python 模块 | 主要符号 | Wave |
|---------|------------------|----------|------|
| `CLEAN-INTAKE-GATE` | `wave6_intake_gate` | `run_intake_gate` | 6 |
| `CLEAN-RUNNER-ENTRY` | `wave7_runner_entry_job_input` | `build_runner_job_input` | 7 |
| `CLEAN-VALIDATE-SCHEMA` | `wave6_intake_gate`, `envelope_writer`, `wave8_m2_execution_engine` | 分散校验 | 6/8 |
| `CLEAN-SAMPLE-ANALYZE` | — | — | PLANNED |
| `CLEAN-CSV-TRANSFORM` | — | — | PLANNED |
| `CLEAN-ENVELOPE-WRITE` | `envelope_writer` | `write_envelopes` | 6 |
| `CLEAN-MANIFEST-WRITE` | `wave6_manifest_writer` | `write_manifest` | 6 |
| `CLEAN-PIPELINE-RUN` | `wave7_orch_pipeline_wire` | `run_wave6_pipeline` | 7 |
| `CLEAN-QA-M1` | `wave6_qa_manifest_m1` | `run_m1_checks` | 6 |
| `CLEAN-M2-SAMPLING-PLAN` | `wave8_m2_sampling_design` | `build_sampling_plan` | 8 |
| `CLEAN-QA-M2` | `wave8_m2_execution_engine` | `run_m2_checks` | 8 |
| `CLEAN-REPORT-BUILD` | `wave7_report_summary_producer` | `build_wave7_report` | 7 |
| `CLEAN-REPORT-RENDER` | `wave8_report_md_renderer` | `render_data_clean_report` | 8 |
| `CLEAN-ARTIFACT-STORE` | `wave7_artifact_storage` | `store_wave7_artifacts` | 7 |
| `CLEAN-JOB-RUN` | `wave7_orch_job_lifecycle` | `run_wave7_job` | 7 |

**Schema 权威**：`schemas/wave6_manifest.py`、`schemas/envelope_v2.py`、`schemas/wave6_intake_gate.py`；交付字段见 `WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`。

---

## 7. Phase 8.6/8.7 Selector 挂钩（草案）

| Selector 输入 | 用途 |
|---------------|------|
| `runtime_context.stage` | `S0`…`S5` 过滤候选工具 |
| `runtime_context.job_record.sku` | BASIC/ENRICH 分支 |
| `runtime_context.artifact.manifest_ref` | 已有 manifest 时跳过 S3 写工具 |
| `runtime_context.flags.enable_m2` | 是否挂载 `CLEAN-QA-M2` |
| `runtime_context.flags.render_report_md` | 是否挂载 `CLEAN-REPORT-RENDER` |
| `request_type` / `intent` | 与 `SPEC_tool_layer_vnext_draft` `selection_key` 对齐 |

**Preconditions 示例**（Catalog 级，非实现）：

| tool_id | precondition kind | key |
|---------|-------------------|-----|
| `CLEAN-QA-M1` | `artifact` | `manifest` |
| `CLEAN-QA-M2` | `artifact` | `manifest` + `envelopes` |
| `CLEAN-REPORT-RENDER` | `artifact` | `report.json` |
| `CLEAN-CSV-TRANSFORM` | `artifact` | `inbound_logical_paths` |

**decision_id / trace_id**：每次 Selector 决策与工具执行结果应写入 ops cycle 战报 JSON（对齐 Phase 8.7 outbox 语义）；字段见 `SPEC_tool_layer_vnext_draft` §1.3。

---

## 8. 占位 / 非目标（v0.1）

| 项 | 说明 |
|----|------|
| Tool Catalog JSON 落盘 | Phase 8.6/8.7 另票 |
| Selector 规则表 / Executor registry | 本文仅接口；不定义 S1–S12 规则 |
| `CLEAN-SAMPLE-ANALYZE` / `CLEAN-CSV-TRANSFORM` 实现 | 待上游清洗票 |
| Invoice / bridge 工具 | Wave 8 PLANNED；不在 CLEAN 编排 S0–S5 |
| 修改 M1/M2 检查规则 | 禁止；治理见 Wave 6 冻结票 |

---

## 9. 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草稿：工具清单、统一响应、主工具接口、模块映射、Selector 挂钩 |

**下一版预期**：各工具 `input_schema` / `output_schema` JSON Schema 落盘；与 `TASK_ROUTING.md` `task_type` 映射；`CLEAN-SAMPLE-ANALYZE` / `CLEAN-CSV-TRANSFORM` 实现票对齐。

---

*CLEAN-Orchestrator Tool Integration · `04_Workflows/WAVE7_CLEAN_ORCH_TOOL_INTEGRATION_v0.1.md`*
