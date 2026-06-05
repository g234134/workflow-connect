# Wave 7 – CLEAN Orchestrator 输入映射规格（v0.1）

> **票号**：`CLEAN-ORCH-INPUT-MAPPING`  
> **性质**：spec / planning（**不写代码**）  
> **受众**：intake → orchestrator 转接器实现、Wave 7 runner 扩展、`build_runner_job_input` 调用方、HQ 派工  
> **前置**：`WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`、`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`、`WAVE6_CLEAN_INTAKE_SCRIPT_v0.1.md`、`WAVE6_CLEAN_INTAKE_ELIGIBILITY_v0.1.md`（准入规则）、`WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md`、`WAVE7_RUNNER_ENTRY_JOB_INPUT_v0.1.md`  
> **实现锚点**（只读对照）：暗部 `core/wave7_runner_entry_job_input.py` → `build_runner_job_input`；`core/wave6_intake_gate.py` → `run_intake_gate`；`core/schemas/wave6_intake_gate.py` → `IntakeGateRequest`  
> **状态**：**DRAFT-v0.1**

---

## 0. 文档目的

Wave 6 对话 intake 产出 **`intake_record`（JSON）**；Wave 7 runner 消费 **`job_record` + `raw_files[]`**，并可选调用 **`IntakeGateRequest`** 形态做 S0 闸道。

本文定义三层之间的 **唯一映射契约**：

1. **`intake_record`** — `WAVE6_CLEAN_INTAKE_SCRIPT` §3 顶层结构  
2. **`CleanJob`** — 编排器抽象工单（本稿新建，**仅 spec**，不落代码类型）  
3. **`job_record` / runner 入参** — `build_runner_job_input` 与 lifecycle 已实现的字段子集  

**不** 重定义 envelope/manifest/QA 规则；**不** 要求本稿实现转接器（留给后续 implementation 票）。

---

## 1. 抽象结构：`CleanJob`（v0.1）

`CleanJob` 是 orchestrator **S0–S5 全程**的逻辑工单视图；比 `job_record` 宽，比完整 `intake_record` 窄（去掉对话审计字段）。

### 1.1 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `clean_job_schema_version` | string | 固定 `"clean_job_v0.1"` |
| `job_id` | string | 全局 job 标识；可与 runner 生成规则对齐（§5.3） |
| `intake_id` | string | 来源 intake UUID；审计与商务对账 |
| `product_sku` | enum | `CLEAN-BASIC` \| `CLEAN-ENRICH`（v0.1 不含 `CLEAN-ENRICH-LLM` 进 runner） |
| `client_ref` | string | 客户/订单引用（非 secret） |
| `intake_status` | enum | `complete` \| `needs_clarification` — 仅 `complete` 可进 S0 job 构造 |
| `data_sources` | `DataSource[]` | 批次输入描述（逻辑路径，禁止绝对路径） |
| `schema_binding` | object | `schema_ref`、必填/PII 字段、record id |
| `cleaning_profile` | object | S2 锁定配置（可由 intake 预填，S2 可修订） |
| `target_outputs` | object | 期望交付物与格式 |
| `sla` | object | 时程与优先级 |
| `risk_flags` | `RiskFlag[]` | 合规模块与规模警示（驱动 gate / 人工） |
| `provenance` | object | 来源渠道、对话轮次、gate 决策摘要 |
| `extensions` | object | 前向兼容；未登记键不得被下游当必填 |

### 1.2 `DataSource`

| 字段 | 类型 | 说明 |
|------|------|------|
| `source_id` | string | 批次内稳定 ID（默认 `file_id` 或 manifest 序号） |
| `kind` | enum | `cleaned_full` \| `raw_inbound` \| `inline_queue` |
| `stored_logical_path` | string | 逻辑路径，如 `cleaned_full/acme-001.json` |
| `content_sha256` | string | 64 位 hex；runner **硬必填**（缺则 skip） |
| `file_format` | enum | `csv` \| `ndjson` \| `jsonl` \| `unknown` |
| `encoding` | string | 如 `utf-8` |
| `compression` | enum | `none` \| `gzip` \| `zstd` |
| `size_bytes` | int | 可选 |
| `row_count_estimate` | int | 可选；S1 预检可对账 |
| `inbound_path_hint` | string | **仅 gate 用**；不得写入 delivery 工件 |

### 1.3 `schema_binding`

| 字段 | 类型 | 说明 |
|------|------|------|
| `schema_ref` | string | registry 或内嵌 schema 指针 |
| `schema_registry_id` | string | 可选 |
| `record_id_field` | string | 可选 |
| `required_fields` | string[] | 可选 |
| `pii_fields` | string[] | 与 `risk_flags` 联动 |

### 1.4 `cleaning_profile`（S2 锁定）

| 字段 | 类型 | BASIC | ENRICH |
|------|------|-------|--------|
| `output_format` | enum | 可选，默认与输入一致 | 同左 |
| `enrich_plan_ref` | string | **必须为空/省略** | **必填** |
| `enrich_apis` | string[] | 省略 | 建议填 |
| `fallback_policy` | enum | 省略 | `strict` \| `lenient` |
| `dedup_strategy` | enum | 可选 `none` | `exact` \| `fuzzy` \| `none` |
| `dedup_key_fields` | string[] | 可选 | 随 dedup |
| `rule_pack_version` | string | 可选 | 可选 |

### 1.5 `target_outputs`

| 字段 | 类型 | 说明 |
|------|------|------|
| `delivery_kinds` | string[] | 默认 `["envelope","manifest","report.json"]`；可选 `report.md` |
| `manifest_product_sku` | string | 与 `product_sku` 一致 |
| `report_template_version` | string | 可选，默认 `wave7_report_v1` |
| `artifact_ref_prefix` | string | 逻辑前缀，如 `w6://delivery/{job_id}/` |

### 1.6 `sla`

| 字段 | 类型 | 说明 |
|------|------|------|
| `deadline_utc` | ISO-8601 | 商务截止 |
| `priority` | enum | `standard` \| `expedite` |
| `estimated_processing_time` | string | 人读估计，非执行硬约束 |
| `queue_position_hint` | int | 可选 |

### 1.7 `RiskFlag`

| `code` | 触发来源（intake） | 编排器行为（v0.1） |
|--------|-------------------|-------------------|
| `PII_PRESENT` | `security_compliance.contains_pii=true` | S0：gate 可 accept；ENRICH 外发 API 须 `DPA_SIGNED` |
| `PII_WITHOUT_DPA` | PII + `dpa_signed=false` | S0：**defer** 或 **reject**（见 ELIGIBILITY） |
| `LARGE_FILE` | `file_size_bytes` > 1GB | S1 警告；可能 `size_policy` tag |
| `ENRICH_API_NOT_READY` | `api_key_status≠ready` | ENRICH：**reject** |
| `BUSINESS_RULES_DECLARED` | `business_rules[]` 非空 | S2 标注；BASIC 不承诺业务正确性 |
| `SCHEMA_INFERRED_LOW_CONF` | `inferred_flags.schema_ref.confidence<0.7` | S1：**补问** 或 defer |
| `ROW_COUNT_MISMATCH` | 预 job 扫描偏差 >20% | S0 后 **needs_clarification** |

### 1.8 `provenance`

| 字段 | 类型 | 说明 |
|------|------|------|
| `source_channel` | enum | 对齐 `IntakeGateRequest.source_channel` |
| `dialogue_turns` | int | 来自 intake |
| `gate_decision` | enum | `accept` \| `defer` \| `reject` |
| `gate_message` | string | `run_intake_gate` 回传摘要 |
| `intake_completed_at` | ISO-8601 | 来自 intake |

---

## 2. 字段映射总表

**图例**

- **S0\***：orchestrator S0（Intake & validation）必填  
- **S1\***：S1（Schema 分析 & 采样）必填（缺则 degrade，见 §3）  
- **R\***：runner `build_runner_job_input` 硬必填  
- **G\***：`IntakeGateRequest` / `run_intake_gate` 需要（转接器合成）  
- **—**：可选  

| intake JSON 路径 | CleanJob 字段 | Wave 7 `job_record` / runner | 备注 |
|------------------|---------------|------------------------------|------|
| `intake_id` | `intake_id` | `job_record.intake_id`（扩展，**当前实现未写**） | 建议写入 `job_record` 扩展或 `metadata` sidecar |
| `product_sku` | `product_sku` | `job_record.sku`；`build_runner_job_input(sku=…)` | 须与 gate 一致，否则 `sku_intake_mismatch` |
| — | `client_ref` | `job_record.client_ref`；runner **R\*** | intake 无顶栏时从 `provenance`/订单侧注入 |
| — | `job_id` | `job_record.job_id`；`job_id` override | 缺则 runner 生成 `w7-{basic\|enrich}-{slug}-{uuid8}` |
| `intake_status` | `intake_status` | — | 非 `complete` 不得调用 `build_runner_job_input` |
| `data_profile.*` + 上传清单 | `data_sources[]` | `raw_files[]` 逐文件 | 见 §2.1 |
| `schema_definition.schema_ref` | `schema_binding.schema_ref` | `cleaning_profile` / S1；**不进** `job_record` 核心四键 | S1/S2 sidecar |
| `schema_definition.required_fields` | `schema_binding.required_fields` | S1 预检 | — |
| `schema_definition.pii_fields` | `schema_binding.pii_fields` | `risk_flags` | — |
| `schema_definition.record_id_field` | `schema_binding.record_id_field` | — | — |
| `enrich_configuration.enrich_plan_ref` | `cleaning_profile.enrich_plan_ref` | ENRICH gate + S2 | BASIC 必须省略 |
| `enrich_configuration.*` | `cleaning_profile.*` | `raw_files[].enrichment`（已清洗 JSON） | 上游清洗已嵌入时 runner 只透传 |
| `scheduling.deadline_utc` | `sla.deadline_utc` | — | 调度侧车 |
| `scheduling.priority` | `sla.priority` | queue `priority`（可选） | — |
| `security_compliance.contains_pii` | `risk_flags` | `intake_request` 合成 `tags` | 见 §4.2 |
| `security_compliance.dpa_signed` | `risk_flags` | gate `tags` | — |
| `data_profile.file_format` | `data_sources[].file_format` | `raw_files[].original_type` / 扩展名 | 映射表 §2.2 |
| `data_profile.encoding` | `data_sources[].encoding` | `raw_files[].encoding` | — |
| `data_profile.row_count_estimate` | `data_sources[].row_count_estimate` | `batch_size_hint`（gate） | — |
| — | `target_outputs` | lifecycle 默认四件套 | 见 DELIVERABLE_TEMPLATES |
| `scheduling.*` | `sla` | — | — |
| `inferred_flags` | `provenance` + 低置信 `risk_flags` | — | 不直接进入 `job_record` |
| `user_explicit_answers` | `provenance` | — | 审计保留在 intake，不复制进 `job_record` |

### 2.1 `data_sources[]` → `raw_files[]`（runner）

| CleanJob `DataSource` | `raw_files[]` 字段 | 约束 |
|----------------------|-------------------|------|
| `source_id` | `file_id` | **R\*** |
| `content_sha256` | `content_sha256` | **R\***，无效则 `missing_content_sha256` |
| `stored_logical_path` | `stored_logical_path` | **R\***；禁止绝对路径泄漏 |
| `file_format` | `extension` / `original_type` | 如 `.csv` / `csv` |
| `encoding` | `encoding` | 可选 |
| `size_bytes` | `size_bytes` | 可选 |
| — | `clean_status` | 默认 `ok` |
| — | `content_summary` | 缺则空结构 |
| ENRICH 且已 enrich | `enrichment` | SKU=ENRICH 时必填或默认 stub |

**批次来源（三选一，与 runner 一致）**

| 来源 | intake / CleanJob | runner 参数 |
|------|-------------------|-------------|
| 目录扫描 | `data_sources[].kind=cleaned_full` | `cleaned_dir` |
| 批次 manifest | 多条 `stored_logical_path` | `manifest_path` |
| 队列 | `data_sources[].kind=inline_queue` | `queue_payload.files[]` |

### 2.2 `intake_request` 合成（`run_intake_gate`）

转接器将 `intake_record` + `CleanJob` 压平为 `IntakeGateRequest`（`wave6_intake_gate_v1`）：

| IntakeGateRequest 字段 | 来源（优先级高→低） |
|------------------------|---------------------|
| `product_sku` | `intake_record.product_sku` |
| `client_ref` | `CleanJob.client_ref` |
| `description` | 合成：SKU + `data_profile.data_source_type` + `row_count_estimate` |
| `tags` | `risk_flags` → tag；`scheduling.priority`；`size_policy:acknowledged` |
| `explicit_task_type` | 固定 `data_cleaning` 或 `clean.{basic\|enrich}` |
| `source_channel` | `provenance.source_channel` 或 `dialogue` |
| `file_extension_hints` | `data_profile.file_format` |
| `inbound_path_hint` | 首条 `data_sources[].inbound_path_hint`（**不得**落盘） |
| `batch_size_hint` | `sum(row_count_estimate)` 或首文件估计 |
| `enrichment_profile` | `enrich_configuration` 摘要对象（仅 ENRICH） |

Gate 至少需 **`description` \| `tags` \| `explicit_task_type` 之一**（schema 校验）。

---

## 3. 必填 / 可选与 degrade 策略

### 3.1 Orchestrator S0（Intake & validation）

| 层级 | 必填 | 缺失时 |
|------|------|--------|
| Intake 完成度 | `intake_status=complete` | **拒绝** job 构造；保持 `needs_clarification` |
| 身份 | `product_sku`、`client_ref` | `missing_product_sku` / `missing_required` |
| Gate | 合成 `IntakeGateRequest` 且 `decision=accept` | `defer` → `intake_deferred`；`reject` → `intake_rejected` |
| 批次 | ≥1 有效 `raw_files[]` | `empty_batch` |
| SKU 一致 | runner `sku` == intake `product_sku` | `sku_intake_mismatch` |
| ENRICH | `enrich_plan_ref`、`api_key_status=ready`（ELIGIBILITY） | **reject** |
| PII + ENRICH 外发 | `dpa_signed=true` | **defer** 默认 |

**S0 可选（有则写入 CleanJob / sidecar，无则不阻塞）**

| 字段 | degrade |
|------|---------|
| `job_id` override | runner 自动生成 |
| `inbound_path_hint` | 仅用 gate 文本信号，不影响 `stored_logical_path` |
| `dialogue_turns` / `inferred_flags` | 仅审计 |
| `queue_position_hint` | 忽略 |

### 3.2 Orchestrator S1（Schema 分析 & 采样）

| 层级 | 必填 | 缺失时 |
|------|------|--------|
| `schema_binding.schema_ref` | **S1\*** | **defer** 到人工；或 `needs_clarification`（intake 脚本 §6.3） |
| `data_sources[].content_sha256` | 已在 S0 硬要求 | — |
| `row_count_estimate` | S1 建议 | 跳过 M2 规模预估；`batch_size_hint` 省略 |
| `record_id_field` | 可选 | 信封层自动生成 UUID |
| M2 计划 | 可选 | Wave 8 `enable_m2` 时再补 `build_sampling_plan` |

**S1 可选 degrade**

| 字段 | degrade |
|------|---------|
| `required_fields` | S1 仅 warning；不阻塞 S3 |
| `pii_fields` 空但 `contains_pii=true` | 升 `risk_flags`；S4 加强抽检 |
| `language_distribution` | ENRICH：默认单语 `unknown` |
| `inferred_flags` 低置信 | 触发 `SCHEMA_INFERRED_LOW_CONF`；**补问** 不自动采用 |

### 3.3 Runner 硬必填（实现已存在）

`build_runner_job_input` 当前 **最小** `job_record`：

```json
{
  "job_id": "string",
  "sku": "CLEAN-BASIC | CLEAN-ENRICH",
  "client_ref": "string",
  "created_at": "ISO-8601 UTC"
}
```

| 参数 | 必填 | 缺失 |
|------|------|------|
| `sku` | **R\*** | `unknown_sku` |
| `client_ref` | **R\*** | `missing_required_field` |
| `cleaned_dir` \| `manifest_path` \| `queue_payload` | 至少其一 | `no_input_source` |
| `intake_request` | 可选 | 跳过 gate（**仅 dev/内测**；prod 应由制度要求必过） |

---

## 4. 转接流程（normative）

```text
intake_record (JSON)
    │  validate eligibility (WAVE6_CLEAN_INTAKE_ELIGIBILITY)
    ▼
map_to_clean_job()          ← 本 spec；实现票未来落地
    │  attach data_sources from upload manifest / scan
    ▼
CleanJob
    │  flatten → IntakeGateRequest
    ▼
run_intake_gate → accept?
    │ yes
    ▼
build_runner_job_input(
    sku=CleanJob.product_sku,
    client_ref=CleanJob.client_ref,
    job_id=CleanJob.job_id?,
    intake_request=<flattened>,
    cleaned_dir | manifest_path | queue_payload
)
    ▼
{ job_record, raw_files[], ok, ... }
    ▼
run_wave7_job / lifecycle S3–S5
```

### 4.1 `map_to_clean_job` 规则摘要

1. `product_sku` ← `intake_record.product_sku`（枚举校验）  
2. `client_ref` ← 调用方订单上下文（intake JSON **无顶栏** 时由 bridge 注入）  
3. `data_sources[]` ← 上传批次 manifest（每文件 `content_sha256` + 逻辑路径）  
4. `schema_binding` ← `intake_record.schema_definition`  
5. `cleaning_profile` ← `enrich_configuration` + SKU 缺省  
6. `risk_flags` ← `security_compliance` + `inferred_flags` 阈值规则  
7. `sla` ← `scheduling`  
8. `target_outputs` ← 产品矩阵默认四件套  

### 4.2 `risk_flags` → gate `tags`（示例）

| risk | tag |
|------|-----|
| `PII_PRESENT` | `pii:declared` |
| `LARGE_FILE` | `size:large`（需 ELIGIBILITY 的 `size_policy:acknowledged` 才 accept） |
| `ENRICH_API_NOT_READY` | —（直接 reject，不打 tag） |
| `priority=expedite` | `priority:expedite` |

---

## 5. 端到端示例

### 5.1 简化 `intake_record`（BASIC）

```json
{
  "intake_id": "c1b2a3d4-5678-90ab-cdef-1234567890ab",
  "product_sku": "CLEAN-BASIC",
  "intake_status": "complete",
  "completed_at": "2026-06-04T09:18:45Z",
  "data_profile": {
    "data_source_type": "log",
    "file_format": "csv",
    "encoding": "utf-8",
    "compression": "gzip",
    "file_size_bytes": 2411724,
    "row_count_estimate": 50000
  },
  "schema_definition": {
    "schema_ref": "auto_inferred://app_logs_standard",
    "record_id_field": "request_id",
    "required_fields": ["timestamp", "level", "message"],
    "pii_fields": []
  },
  "security_compliance": {
    "contains_pii": false,
    "dpa_signed": false,
    "user_acknowledged_limitations": true
  },
  "enrich_configuration": null,
  "scheduling": {
    "deadline_utc": "2026-06-07T23:59:59Z",
    "priority": "standard"
  }
}
```

**假设**：上传后批次扫描得到 1 个 cleaned 文件（逻辑路径 + sha256）。

### 5.2 对应 `CleanJob`

```json
{
  "clean_job_schema_version": "clean_job_v0.1",
  "job_id": "w7-basic-acme-logs-a1b2c3d4",
  "intake_id": "c1b2a3d4-5678-90ab-cdef-1234567890ab",
  "product_sku": "CLEAN-BASIC",
  "client_ref": "acme-corp-2026Q2",
  "intake_status": "complete",
  "data_sources": [
    {
      "source_id": "app-logs-202606",
      "kind": "cleaned_full",
      "stored_logical_path": "cleaned_full/app-logs-202606.json",
      "content_sha256": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
      "file_format": "csv",
      "encoding": "utf-8",
      "compression": "gzip",
      "size_bytes": 2411724,
      "row_count_estimate": 50000
    }
  ],
  "schema_binding": {
    "schema_ref": "auto_inferred://app_logs_standard",
    "record_id_field": "request_id",
    "required_fields": ["timestamp", "level", "message"],
    "pii_fields": []
  },
  "cleaning_profile": {
    "output_format": "csv",
    "dedup_strategy": "none"
  },
  "target_outputs": {
    "delivery_kinds": ["envelope", "manifest", "report.json"],
    "manifest_product_sku": "CLEAN-BASIC",
    "artifact_ref_prefix": "w6://delivery/w7-basic-acme-logs-a1b2c3d4/"
  },
  "sla": {
    "deadline_utc": "2026-06-07T23:59:59Z",
    "priority": "standard"
  },
  "risk_flags": [],
  "provenance": {
    "source_channel": "dialogue",
    "gate_decision": "accept",
    "intake_completed_at": "2026-06-04T09:18:45Z"
  }
}
```

### 5.3 对应 `build_runner_job_input` 调用与 `job_record` 片段

**调用（概念）**

```python
build_runner_job_input(
    sku="CLEAN-BASIC",
    client_ref="acme-corp-2026Q2",
    job_id="w7-basic-acme-logs-a1b2c3d4",
    cleaned_dir="<logical_batch_root>",
    intake_request={
        "product_sku": "CLEAN-BASIC",
        "client_ref": "acme-corp-2026Q2",
        "description": "CLEAN-BASIC log csv gzip ~50000 rows",
        "explicit_task_type": "data_cleaning",
        "tags": ["pipeline:code_cleaning"],
        "file_extension_hints": ["csv"],
        "batch_size_hint": 50000,
    },
)
```

**成功回传中的 `job_record`（与当前实现对齐）**

```json
{
  "job_id": "w7-basic-acme-logs-a1b2c3d4",
  "sku": "CLEAN-BASIC",
  "client_ref": "acme-corp-2026Q2",
  "created_at": "2026-06-04T10:00:00+00:00"
}
```

**`raw_files[]` 单元素片段**

```json
{
  "file_id": "app-logs-202606",
  "content_sha256": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
  "stored_logical_path": "cleaned_full/app-logs-202606.json",
  "clean_status": "ok",
  "name": "app-logs-202606",
  "extension": ".csv",
  "original_type": "csv",
  "encoding": "utf-8",
  "content_summary": { "line_count": 0, "char_count": 0, "imports": [], "preview_lines": [] }
}
```

**lifecycle 入口**：`JobRunContext.job_record` 同上；`raw_files` 全长列表进入 S3 `write_envelopes`。

---

## 6. 与任务模型阶段对照

| 逻辑阶段 | CleanJob 消费字段 | Wave 7 产物 |
|----------|-------------------|-------------|
| S0 | 全文 + `data_sources` | `job_record`、`raw_files`、gate 结果 |
| S1 | `schema_binding`、`data_sources[].row_count_estimate` | `schema_analysis`、`sampling_plan`（sidecar） |
| S2 | `cleaning_profile` | 锁定 sidecar / 扩展 `job_record` |
| S3 | `raw_files`、`job_record.sku` | envelopes、manifest |
| S4 | manifest + sku | `qa` |
| S5 | `target_outputs` | report、artifact refs |

详见 `WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md` §2。

---

## 7. 版本与后续实现票

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始：`CleanJob` 抽象、三向映射表、S0/S1 必填与 degrade、E2E 示例 |

**预期下一版**

- `map_to_clean_job` / `intake_record_to_gate_request` 参考实现与单测 fixture  
- `job_record.intake_id` / `cleaning_profile` 扩展字段写入 lifecycle checkpoint  
- `CLEAN-ENRICH-LLM` SKU 与 runner `SUPPORTED_SKUS` 对齐表  
- 与 `WAVE6_CLEAN_INTAKE_ELIGIBILITY` 错误码一一对应表  

---

## 8. 占位 / 非目标（v0.1）

| 项 | 说明 |
|----|------|
| 转接器 Python 模块 | 本稿不交付代码 |
| Postgres jobs 表字段 | lifecycle 持久化另票 |
| 多 job 队列 payload | 仅单 job `CleanJob` |
| 绝对路径 / env 键 | 禁止出现在映射输出 |

---

*CLEAN-Orchestrator Input Mapping · `04_Workflows/WAVE7_CLEAN_ORCH_INPUT_MAPPING_v0.1.md`*
