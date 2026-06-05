# Wave 7 – CLEAN-Orchestrator 任务分解模型（v0.1）

> **票号**：`CLEAN-ORCH-TASK-MODEL`  
> **性质**：spec / planning（**不写代码**）  
> **受众**：未来 agent／工具协同、尚書省派工、Wave 7/8 编排扩展  
> **前置**：`WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`、`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`、`WAVE7_CLEAN_RUNNER_ORCH_OVERVIEW_v0.1.md`、`WAVE7_ORCH_JOB_LIFECYCLE_v0.1.md`、`WAVE8_OVERVIEW_v0.1.md`  
> **实现锚点**（只读对照）：暗部 `core/wave7_orch_job_lifecycle.py`、`core/wave7_orch_pipeline_wire.py`、`core/wave7_runner_entry_job_input.py`  
> **状态**：**DRAFT-v0.1**

---

## 0. 文档目的

Wave 7/8 已具备 **单 job 生命周期**、**pipeline 硬接线**、**QA-M1/M2**、**report.json / report.md** 等可运行实现。本文把「一张 CLEAN 工单」抽象为 **六段式任务分解模型（S0–S5）**，供：

- **人**：按阶段验收、裁定回退与豁免；
- **Agent**：按阶段领取子任务、读写约定 artifact、不越权改 Wave 6 冻结规则；
- **批处理脚本**：在固定 stage 边界调用 `dict` 契约 API（runner / lifecycle / store）。

本文 **不** 新增 envelope/manifest/QA 业务规则；规则权威仍在 Wave 6 R3/R4 与已冻结模块。

---

## 1. 模型总览

### 1.1 阶段列表（逻辑编排）

| 阶段 ID | 名称 | 一句话 |
|---------|------|--------|
| **S0** | Intake & validation | 接单、SKU/批次闸道、构造或拒绝 job |
| **S1** | Schema 分析 & 采样检查 | 解析 schema/enrich 计划、预检与（可选）M2 抽样设计 |
| **S2** | 清洗规则生成 / 配置 | 固化 `schema_ref`、清洗/enrich 配置与 SKU 对齐 |
| **S3** | 执行清洗（Wave 6 核心） | 产出 delivery 信封 + manifest（及上游 cleaned 输入） |
| **S4** | QA（M1 + M2） | 全量 manifest 完整性 + 抽样深检 |
| **S5** | 汇总与报告生成 | `report.json` + 可选 `report.md` + 交付落盘 |

### 1.2 与 Wave 7 runtime stage 的对照

Wave 7 代码内 stage 名与本文 **逻辑阶段** 并非一一同名，下表为 **推荐映射**（派工与日志用逻辑 ID，实现日志可带 runtime stage）：

| 逻辑阶段 | Wave 7 `JobRunContext.stage`（典型） | 主要模块 / 票 |
|----------|--------------------------------------|----------------|
| S0 | `intake` → `entry` | `wave6_intake_gate`、`wave7_runner_entry_job_input` |
| S1 | （多分布在 S0/S2；无独立 runtime stage） | intake 内 schema 校验；`wave8_m2_sampling_design`（M2 计划） |
| S2 | （配置产物写入 `job_record` / sidecar；多在 S0 前完成） | 产品线矩阵 §5.1；`enrich_plan_ref` 等 |
| S3 | `pipeline` | `envelope_writer`、`wave6_manifest_writer`、`wave7_orch_pipeline_wire` |
| S4 | `qa` | `wave6_qa_manifest_m1`、`wave8_m2_execution_engine`（`enable_m2`） |
| S5 | `report` → `storage` | `wave7_report_summary_producer`、`wave8_report_md_renderer`、`wave7_artifact_storage` |

**重要边界**：当前 Wave 7 runner **默认消费已产出的 `cleaned_full` JSON**（`raw_files[]`），即 **S3 的「行级清洗」常在上游批处理完成**；编排器内 S3 重点是 **信封化 + manifest 索引**。全链路「raw → clean」仍属产品线矩阵中的 `raw_load → clean_basic → [clean_enrich]`，可由独立 worker 在 S0 之前或并行完成。

---

## 2. 阶段规格（S0–S5）

### S0 — Intake & validation

| 项 | 说明 |
|----|------|
| **阶段目的** | 把外部请求（订单/队列/CLI）转为 **可执行的 CLEAN job** 或 **明确拒绝/延期**；保证 SKU、客户引用、批次非空、无禁路径泄漏。 |
| **主要输入** | `intake_request`（或 bridge `intake.*` 等价字段）：`client_ref`、`product_sku`、`description`、`inbound_path_hint` 等；可选 `queue_payload`；批次 `manifest_path` / `cleaned_dir` 列表；可选 `job_id` override。 |
| **主要输出** | **接受路径**：`job_record`（`job_id`、`sku`、`client_ref`、`created_at`…）、`raw_files[]`（满足 `envelope_writer`）、`{ok, message, error_code, input_count, skipped[]}`；**拒绝路径**：`decision=reject/defer` + 稳定 `error_code`（如 `intake_rejected`、`intake_deferred`）。 |
| **执行角色** | **批处理脚本**：`build_runner_job_input` / CLI runner；**Agent**（可选）：补全 intake 字段、解释 reject 原因；**人**：裁定 defer、豁免、SKU 变更。 |

**子任务示例（可拆给 agent）**

1. 校验 `product_sku` ∈ `{CLEAN-BASIC, CLEAN-ENRICH, …}`  
2. 跑 `run_intake_gate` → 仅 `accept` 进入 job 构造  
3. 扫描批次 → 映射 `stored_logical_path`（禁止绝对路径落盘）  
4. 生成/确认 `job_id`，写入 lifecycle `pending`（若持久化）

**失败语义**：不创建 job；`job_record.status` 不进入 `running`（实现上直接 `failed` + intake 系 error code）。

---

### S1 — Schema 分析 & 采样检查

| 项 | 说明 |
|----|------|
| **阶段目的** | 确认 **schema 可解析**、字段与 SKU 匹配；对大批量 job **预建 M2 抽样计划**（N、seed、sample_size）；可选做 **预检抽样**（读少量 `raw_files` 行）避免整批进入 S3 后才发现结构灾难。 |
| **主要输入** | S0 的 `job_record`、`raw_files[]` 元数据；`schema_ref` / 内嵌 schema；ENRICH 时 `enrich_plan_ref`；`billing_table` 或 `billing_table_version`（M2 计划用）。 |
| **主要输出** | `schema_analysis`（建议结构，非强制文件名）：`{ok, schema_version, violations_preview[], field_coverage_preview?}`；`sampling_plan`（M2）：`{N, sample_size, seed, billing_table_version}`（见 `wave8_m2_sampling_design`）；可选 `preflight_sample` 报告。 |
| **执行角色** | **Agent**：读 schema registry、对比样例行、输出违规摘要；**批处理**：`build_sampling_plan`；**人**：裁定非标 schema、批准继续。 |

**与实现的关系**：M2 **执行**在 S4；S1 只 **设计计划** 与 **预检**。BASIC intake 校验见产品矩阵 §5.1（编码、格式、`schema_ref` 可解析）。

**失败语义**：schema 硬失败 → 回 S0/S2 或 `reject`；预检仅 warning 可带标进入 S3（产品政策由尚書省裁定）。

---

### S2 — 清洗规则生成 / 配置

| 项 | 说明 |
|----|------|
| **阶段目的** | 把业务要求固化为 **可重跑配置**：清洗规则、enrich 映射、输出格式、SKU 规则（BASIC 禁 enrichment、groq 等）；供 S3 与 QA 消费。 |
| **主要输入** | S1 的 schema 结论；订单行项 SKU；可选历史同类 job 的 `report.json`；`enrich_plan_ref` / 规则模板版本。 |
| **主要输出** | `cleaning_profile`（逻辑名，可落 sidecar 或写入 `job_record` 扩展字段）：`{schema_ref, output_format, enrich_plan_ref?, dedup_policy?, rule_pack_version}`；与 `job_record.sku` **一致** 的锁定配置；ENRICH 时 `enrichment_profile`。 |
| **执行角色** | **Agent**（主）：生成/修订规则草案、diff 说明；**人**：批准规则包、承担业务逻辑责任；**批处理**：加载已发布 `rule_pack_version`，禁止 agent 擅自改冻结 writer 逻辑。 |

**禁止**：在本阶段直接改 `manifest` 行或绕过 `envelope_writer` schema 校验（对齐 `WAVE7_ORCH_PIPELINE_WIRE`）。

**失败语义**：SKU 与规则冲突 → 停留 S2；不得进入 S3。

---

### S3 — 执行清洗（Wave 6 核心）

| 项 | 说明 |
|----|------|
| **阶段目的** | 产出 **delivery 级工件**：每文件 envelope + 作业级 `manifest.json`；统计 ok/rejected 行，为 QA 与报告提供事实源。 |
| **主要输入** | S0 `job_record` + `raw_files[]`（已清洗 JSON 或上游 raw，经 entry 映射）；S2 `cleaning_profile`（隐含在 raw 内容与 SKU 规则中）。 |
| **主要输出** | `envelopes[]`；`manifest`（`ManifestV20`，含 `rows[]`、`clean_status`）；**checkpoint**：`manifest` 可先行落 staging（`checkpoint=manifest`）。 |
| **执行角色** | **批处理脚本**（主）：`write_envelopes` → `normalize_manifest_inputs`（ENRICH `present` gate）→ `write_manifest`；**Agent**：仅诊断 envelope 错误、建议修 raw，**不**改 writer 规则；**人**：处理大规模 rejected 是否重跑。 |

**上游清洗（产品线矩阵）**：`clean_basic` / `clean_enrich` 若未在编排器内执行，则视为 S3 的 **输入准备子步骤**，产出 `cleaned_full` 再进入 runner。

**失败语义**：`envelope_stage_failed` / `manifest_stage_failed` → 通常 **不可从 S5 单独重试**；需回 S3 或更前。Manifest checkpoint 成功后，报告/QA 失败可 **不重算 envelope**（lifecycle 已文档化）。

---

### S4 — QA（M1 + M2）

| 项 | 说明 |
|----|------|
| **阶段目的** | **M1**：全量 manifest 完整性、SKU 规则、与 `report.summary.accepted_units` 对账；**M2**（Wave 8，可选）：按 S1 计划抽样回读 envelope 做深检。 |
| **主要输入** | S3 `manifest`；`job_record`（`job_id`、`sku`）；`build_summary_for_m1_checks` 的 summary slice；S1 `sampling_plan` + S3 `envelopes`（M2 loader）；`billing_table`。 |
| **主要输出** | `qa` 块：`manifest_integrity`（M1）、`sample_validation`（M2）、`failures[]`、`overall_ok`；驱动 `qa_status`（`pass` / `pass_with_warnings` / `fail`）。 |
| **执行角色** | **批处理**（主）：`run_m1_checks`、`execute_m2_checks`（`enable_m2`）；**Agent**：解读 failures、归类 P0/P1、建议回退目标；**人**：P1 豁免、Chargeable 裁定。 |

**P0 失败策略**（lifecycle）：默认 `job_record.status=failed`，可配置 `blocked`；**不 finalize** 完整交付（与 `WAVE7_ORCH_JOB_LIFECYCLE` 一致）。

**M2 非 strict 模式**：意外错误可落 `sample_validation.status=error` 而 job 仍可能 `done`（带 message 后缀），见实现 `strict_m2` 旗标。

---

### S5 — 汇总与报告生成

| 项 | 说明 |
|----|------|
| **阶段目的** | 聚合 S3/S4 事实，生成 **客户与计费可读** 的 `report.json`；可选渲染 `report.md`；**finalize** 工件至 delivery 区（四件套骨架 + 逻辑 ref）。 |
| **主要输入** | S3 `manifest`；S4 `qa`（含 M2 结果）；`job_record`；`billing_table`；artifact store 路径解析（`paths_resolved`）。 |
| **主要输出** | `report.json`（`meta`、`summary`、`stats`、`errors`、`qa`、`next_steps`、`attachments_index`）；可选 `report.md`；`w6://delivery/{job_id}/*` refs；终态 `job_record.status` ∈ `{done, failed, blocked}` 及 `completion_variant=completed_with_failures`（R3 §G.7）。 |
| **执行角色** | **批处理**：`build_wave7_report`、`store_wave7_artifacts`、`render_data_clean_report`（`render_report_md`）；**Agent**：撰写 `next_steps` 文案草稿（须人审）；**人**：对外交付、CS 解读。 |

**报告 MD**：默认 **隔离失败**（不 rollback `report.json`），除非 `strict_report_md=true`。

---

## 3. 工件与数据流（跨阶段）

```text
[intake_request / queue / CLI]
        │
        ▼
   S0 ─ job_record, raw_files[]
        │
        ▼
   S1 ─ schema_analysis, sampling_plan (optional)
        │
        ▼
   S2 ─ cleaning_profile (config lock)
        │
        ▼
   S3 ─ envelopes[], manifest  ──checkpoint──▶ staging/manifest.json
        │
        ▼
   S4 ─ qa{M1,M2}, overall_ok, qa_status
        │
        ▼
   S5 ─ report.json, report.md?, artifact_refs, job status
```

**下游依赖速查**

| 产出 | 消费阶段 |
|------|----------|
| `job_record` | S1–S5 全程 |
| `raw_files[]` | S1 预检、S3 envelope |
| `cleaning_profile` | S3 规则、S4 SKU 检查 |
| `manifest` | S4 M1/M2、S5 report |
| `envelopes` | S4 M2 回读 |
| `qa` | S5 `report.qa`、Done/Chargeable |
| `report.json` | S5 `report.md`、财务/bridge（Wave 8+） |

---

## 4. 状态流转与回退

### 4.1 Job 级状态（lifecycle）

| 状态 | 含义 | 典型进入阶段 |
|------|------|----------------|
| `pending` | 已创建未跑 | S0 后 |
| `running` | 编排中 | S3 起 |
| `done` | 成功 finalize | S5 末 |
| `failed` | 不可交付或 P0 QA | S0–S5 任一 |
| `blocked` | 可恢复阻塞（策略可选） | 多為 S4 P0 |

`done` + `completion_variant=completed_with_failures`：manifest 有 rejected 行但 **M1 无 P0**（R3 §G.7）。

### 4.2 阶段顺序与回退（ASCII）

```text
                    ┌──────────────┐
                    │     S0       │
                    │   intake     │
                    └──────┬───────┘
                           │ reject/defer ──▶ [STOP]
                           ▼
                    ┌──────────────┐
         ┌─────────│     S1       │─────────┐
         │         │ schema/sample│         │
         │         └──────┬───────┘         │
         │ schema hard fail                 │ preflight warn only
         ▼                ▼                 │
    ┌─────────┐    ┌──────────────┐        │
    │  S0/S2  │◀───│     S2       │        │
    │  修订   │    │ rules/config │        │
    └─────────┘    └──────┬───────┘        │
                            ▼                │
                    ┌──────────────┐       │
                    │     S3       │◀──────┘
                    │ clean+env+mf │
                    └──────┬───────┘
                           │ envelope/manifest fail
                           ├──────────────────▶ S2 (规则) / S0 (换批次)
                           ▼
                    ┌──────────────┐
                    │     S4       │
                    │  QA M1+M2    │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │ M1 P0         │ M2 P0       │ P1 only
           ▼               ▼               ▼
      ┌─────────┐    ┌─────────┐    ┌──────────────┐
      │ failed/ │    │ S3 重跑 │    │  S5 继续     │
      │ blocked │    │ 或 S2   │    │ pass_with_   │
      └─────────┘    └─────────┘    │ warnings     │
           │               │         └──────┬───────┘
           │               │                ▼
           │               │         ┌──────────────┐
           │               └────────▶│     S5       │
           │                         │ report+store │
           │                         └──────┬───────┘
           │                                │
           │         report IO fail         │ storage retry
           │         (checkpoint manifest)  │ (幂等)
           └────────────────────────────────┤
                                            ▼
                                      [done | failed]
```

### 4.3 回退决策表

| 失败征象 | 建议回退目标 | 是否可 checkpoint 重试 | 典型执行者 |
|----------|--------------|------------------------|------------|
| intake reject/defer | S0（新请求） | — | 人/商务 |
| SKU/schema 不明 | S2 或 S0 | — | Agent + 人 |
| envelope 批量 PARSE-FAIL | S3（修 raw）或上游清洗 | 否（重算 envelope） | 批处理 |
| manifest 结构错误 | S3 | 否 | 批处理 |
| M1 P0（KEYS/COUNT/SKU） | S3；若规则错 → S2 | manifest 已存时可只重跑 S4/S5 | 批处理 + Agent 诊断 |
| M2 P0 抽样失败 | S3（数据问题）或 S2（规则） | 同上 | 批处理 |
| M2 仅 P1 | 不回退；S5 `pass_with_warnings` | 是 | 人裁定豁免 |
| report build 失败 | S5 | **是**（不重算 manifest） | 批处理 |
| storage IO 失败 | S5 | **是**（`max_retries`） | 批处理 |

---

## 5. 角色分工矩阵

| 阶段 | 人 | Agent | 批处理脚本 |
|------|----|-------|------------|
| S0 | 裁定 defer/豁免、SKU 变更 | 补 intake、解释 reject | `run_intake_gate`、`build_runner_job_input` |
| S1 | 批准非标 schema | schema 差异分析、抽样建议 | `build_sampling_plan` |
| S2 | 批准规则包 | 起草 `cleaning_profile` | 加载发布版 rule pack |
| S3 | 大规模 rejected 决策 | 诊断行级错误 | `write_envelopes`、`write_manifest` |
| S4 | P1 豁免、Chargeable | failures 归类与回退建议 | `run_m1_checks`、`execute_m2_checks` |
| S5 | 对外交付 | `next_steps` 草稿 | `build_wave7_report`、store、render MD |

**Agent 红线**（继承工程合约）：不改 Wave 6 冻结 writer/QA 规则；不输出 env/密钥；路径仅逻辑名 / `w6://` ref。

---

## 6. 子任务 ID 与派工约定（供未来工具）

建议子任务命名：`{job_id}/{stage}/{seq}-{slug}`，例如 `w7-basic-acme/S4/01-m1-rerun`。

| 前缀 | 含义 |
|------|------|
| `S0-*` | intake/entry |
| `S1-*` | schema/sample |
| `S2-*` | rules/config |
| `S3-*` | envelope/manifest |
| `S4-*` | qa-m1 / qa-m2 |
| `S5-*` | report-json / report-md / finalize |

每个子任务完成应回传 **结构化 `dict`**（至少 `ok`、`message`、可选 `error_code`、`stage`），与 `run_wave7_job` 回传形状对齐，便于 HQ 协调整合。

---

## 7. 与 Wave 8 / 产品交付的衔接

| 能力 | 阶段 | 说明 |
|------|------|------|
| M2 抽样执行 | S4 | `enable_m2=true`；计划来自 S1 |
| `report.md` | S5 | `render_report_md=true`；模板见 `WAVE8_REPORT_MARKDOWN_OVERVIEW` |
| `customer_ack` / invoice / bridge | S5 之后 | **不在**本模型 S0–S5 内；Wave 8 PLANNED |

交付物目录与 Done/Chargeable 判定见 `WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md` §D/C。

---

## 8. 占位 / 非目标（v0.1）

| 项 | 说明 |
|----|------|
| 多 job 队列调度 | 不在此模型；单 job 假设 |
| BASIC→ENRICH 升级链 | Wave 8+ 另票 |
| Agent 自动改 envelope 规则 | 禁止；仅诊断与配置草案 |
| 分布式锁 / Postgres jobs 表 | Wave 7 lifecycle 票界外 |
| 远程 object store | 不在 v0.1 |

---

## 9. 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草稿：S0–S5 分解、I/O、角色、状态回退图 |

**下一版预期**：子任务 JSON Schema；与 `TASK_ROUTING.md` 的 `task_type` 映射；M2/invoice 升格后的回退表增量。

---

*CLEAN-Orchestrator Task Model · `04_Workflows/WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md`*
