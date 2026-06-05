# Wave 7 – CLEAN-Orchestrator 状态机规格（v0.1）

> **票号**：`CLEAN-ORCH-STATE-MACHINE`  
> **性质**：spec / planning（**不写代码**）  
> **受众**：多 job 调度、HQ 派工、Wave 8+ 编排扩展、尚書省裁定回退策略  
> **前置**：`WAVE7_ORCH_JOB_LIFECYCLE_v0.1.md`、`WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md`、`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`（R3 §G.6–G.7）  
> **实现锚点**（只读对照）：暗部 `core/wave7_orch_job_lifecycle.py`、`core/wave7_report_summary_producer.py`、`core/wave7_artifact_storage.py`  
> **状态**：**DRAFT-v0.1**

---

## 0. 文档目的

Wave 7 已实现 **单 job** 生命周期：`pending` → `running` → `done` | `failed` | `blocked`，并以 `completion_variant` / `report.summary.qa_status` 表达 **质量与交付形态**（与 **编排终态** 分层）。

本文将上述经验抽象为 **CLEAN-Orchestrator 通用状态机**（v0.1），供：

- 未来 **多 job 队列 / worker** 统一读写 `orch_status`；
- 与 Gov Core **DLQ / retry**（`error_taxonomy`、`dlq` 表）对齐升级路径；
- Agent／人 在失败时明确：**自动重试**、**阻塞待恢复**、**人工票**、**死信** 四选一。

**不** 在本稿重定义 Wave 6 envelope/manifest/QA 业务规则；**不** 要求 Wave 7 代码立即改名（映射表保证向后兼容）。

---

## 1. 状态集合（Orchestrator 层）

### 1.1 主状态（`orch_status`）

| 状态 | 语义 | 终态？ | Wave 7 等价 |
|------|------|--------|-------------|
| **PENDING** | 已接单／已创建，尚未进入执行段 | 否 | `job_record.status=pending`（runner 持久化时；内存 run 常直接从 RUNNING 起） |
| **RUNNING** | 至少一个 stage 在执行（S0–S5 任一） | 否 | `running` |
| **BLOCKED** | 可恢复阻塞：策略允许 **同 job** 修复后续跑，无需新 `job_id` | 否* | `blocked`（`p0_failure_policy=blocked` 等） |
| **DONE** | 编排成功结束；交付物可按政策 finalize | **是** | `done` |
| **FAILED** | 编排失败；默认 **不可** 对外 Chargeable finalize | **是** | `failed` |
| **NEED-HUMAN** | 自动重试／策略已耗尽；须人裁定（豁免、改 SKU、新批次、关单） | 否* | Wave 7 **无同名**；由 `blocked` + 侧车或映射升格 |

\* `BLOCKED` / `NEED-HUMAN` 在实现上可持久化为「非终态」；业务上若长期无人处理，可 **侧车** 写入 DLQ 并仍保留原 `orch_status` 供审计。

### 1.2 质量子类型（挂在 DONE / 报告层，非主状态）

| 字段 | 取值 | 层级 | 说明 |
|------|------|------|------|
| `completion_variant` | `completed` / `completed_with_failures` | job / `job_record` | R3 §G.7：manifest 有 rejected 行但 **M1 无 P0** |
| `qa_status` | `pass` / `pass_with_warnings` / `fail` | `report.summary` | 仅由 QA failures 严重度映射；**≠** `orch_status` |

**规则**：`orch_status=DONE` 时，`qa_status` 可为 `pass` 或 `pass_with_warnings`；`qa_status=fail` 时 Wave 7 实现 **不会** 进入 `done`（除非未来另开 policy 票）。

### 1.3 侧车道（非 `orch_status` 主状态）

| 侧车 | 含义 | 何时设置 |
|------|------|----------|
| **DLQ** | 死信队列记录（持久化行 + 审计字段） | 自动重试耗尽、或 `non_retryable` 首次即入队（对齐 Gov Core `dlq` / `GET /monitoring/dlq`） |
| **NEW-TICKET** | 须 **新 job_id** 或新尚書省票才能继续 | SKU/规则/批次级错误、intake reject、schema 硬失败 |
| **CHECKPOINT** | `none` / `manifest` | Wave 7 `JobRunContext.checkpoint`；决定 S5 能否不重算 S3 |

---

## 2. 状态图（文字版）

### 2.1 主路径

```text
                         ┌──────────────────────────────────────┐
                         │            [外部触发]                 │
                         │  CLI / queue / HQ dispatch / resume   │
                         └──────────────────┬───────────────────┘
                                            ▼
                                    ┌───────────────┐
                                    │   PENDING     │
                                    └───────┬───────┘
                                            │ start / admit
                                            ▼
                                    ┌───────────────┐
              ┌────────────────────│   RUNNING     │────────────────────┐
              │                    └───────┬───────┘                    │
              │                            │                            │
   retryable  │                            │ stage OK                   │ terminal error
   same job   │                            ▼                            │ (non-retryable)
              │                    ┌───────────────┐                    │
              │                    │  checkpoint?  │                    │
              │                    │ manifest 可选  │                    │
              │                    └───────┬───────┘                    │
              │                            │                            │
              │              ┌─────────────┼─────────────┐              │
              │              ▼             ▼             ▼              ▼
              │        ┌──────────┐  ┌──────────┐  ┌──────────┐   ┌──────────┐
              │        │ QA/report│  │ storage  │  │ policy   │   │  FAILED  │
              │        │   fail   │  │ IO fail  │  │ blocked  │   │          │
              │        └────┬─────┘  └────┬─────┘  └────┬─────┘   └──────────┘
              │             │             │             │
              │             │             │ retries     │
              │             │             │ exhausted   │
              │             ▼             ▼             ▼
              │        ┌──────────┐  ┌──────────┐  ┌──────────────┐
              └───────▶│ BLOCKED  │  │ (retry   │  │ NEED-HUMAN   │
                       │          │  │  loop)   │  │ + DLQ 侧车   │
                       └────┬─────┘  └──────────┘  └──────┬───────┘
                            │ human resume                  │ new ticket / abandon
                            └──────────────┬────────────────┘
                                           ▼
                                    ┌───────────────┐
                                    │     DONE        │
                                    │  + completion_  │
                                    │    variant?     │
                                    │  + qa_status    │
                                    └───────────────┘
```

### 2.2 DONE 质量分支（与主状态正交）

```text
RUNNING ──(all stages ok, finalize ok)──▶ DONE
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                              ▼
         completion_variant = ∅ / completed          completion_variant =
         qa_status = pass (no P0/P1)                 completed_with_failures
         [标准交付]                                   qa_status = pass (M1 无 P0)
                                                    [黄灯：有 rejected 行]
```

### 2.3 升格为 NEED-HUMAN / DLQ / 新票（决策摘要）

```text
RUNNING ──error──▶ 可重试? ──是──▶ RUNNING（同 job，遵守 backoff）
                    │
                    否 ──▶ 同 job 可修? ──是──▶ BLOCKED ──超时/政策──▶ NEED-HUMAN + DLQ
                    │
                    否 ──▶ 须新 job / 新规则? ──是──▶ FAILED + NEW-TICKET
                    │
                    否 ──▶ 硬失败 ──▶ FAILED（可选 DLQ 仅审计）
```

---

## 3. Wave 7 → CLEAN-Orchestrator 映射表

### 3.1 `job_record.status` → `orch_status`

| `job_record.status` | `orch_status` | 备注 |
|---------------------|---------------|------|
| `pending` | **PENDING** | 队列持久化场景 |
| `running` | **RUNNING** | `run_wave7_job` 入口即设 |
| `blocked` | **BLOCKED** 或 **NEED-HUMAN** | 默认 **BLOCKED**；若 `blocked_ttl` 超时或 `escalate_on_blocked=true` → **NEED-HUMAN** |
| `done` | **DONE** | `ok=true` |
| `failed` | **FAILED** 或 **NEED-HUMAN** | 见 §3.3 `error_code` |

### 3.2 `completion_variant`（仅当 `status=done`）

| `job_record.status` | `completion_variant` | `orch_status` | 建议展示 |
|---------------------|------------------------|---------------|----------|
| `done` | （缺省 / `completed`） | **DONE** | 标准完成 |
| `done` | `completed_with_failures` | **DONE** + `quality=partial` | R3 §G.7 黄灯；**不** 降级 `orch_status` |

### 3.3 `report.summary.qa_status`（报告层，非主状态）

| `qa_status` | 典型 `job_record.status` | `orch_status` | 说明 |
|-------------|--------------------------|---------------|------|
| `pass` | `done` | **DONE** | 无 P0/P1 |
| `pass_with_warnings` | `done`（Wave 8+ M2 P1） | **DONE** | 仅 P1；Wave 7 无 M2 时少见 |
| `fail` | `failed` 或 `blocked` | **FAILED** / **BLOCKED** | M1 P0；Wave 7 默认 **不** `done` |
| `fail` | （无 report） | **FAILED** | QA 前即失败 |

**禁止映射**：`qa_status=fail` → `orch_status=DONE`（除非未来尚書省 explicit policy 票）。

### 3.4 组合真值表（实施对照）

| status | completion_variant | qa_status | `orch_status` | Chargeable（R3 缺省） |
|--------|-------------------|-----------|---------------|------------------------|
| `done` | — | `pass` | DONE | 允许 |
| `done` | `completed_with_failures` | `pass` | DONE (partial) | 允许 + CS 复核 |
| `done` | — | `pass_with_warnings` | DONE | 允许 + 警告 |
| `failed` | — | `fail` / N/A | FAILED | 禁止 |
| `blocked` | — | `fail` / N/A | BLOCKED | 禁止 |
| `running` | — | — | RUNNING | — |
| `pending` | — | — | PENDING | — |

### 3.5 `run_wave7_job` 回传字段 → 侧车

| 回传字段 | 映射 |
|----------|------|
| `retryable=true` | 允许同 job 重试；`orch_status` 保持 **RUNNING** 或回到 **PENDING**（调度器实现） |
| `retryable=false` | 禁止自动重试；视 `error_code` 进 **FAILED** / **BLOCKED** / **NEED-HUMAN** |
| `checkpoint=manifest` | **CHECKPOINT=manifest**；S5/S4 可 resume |
| `storage_attempts` | IO 重试计数；≥ `max_retries` → **FAILED** + DLQ 侧车 |
| `error_code` | 见 §4 错误类别表 |

---

## 4. 错误类别处理规则

### 4.1 分类与目标状态（总表）

| 错误类别 | 典型 `error_code` / 征象 | 目标 `orch_status` | 自动重试 | 退避策略 | 升级 NEED-HUMAN | 升级 DLQ | 新票 |
|----------|-------------------------|-------------------|----------|----------|-----------------|----------|------|
| **A. Schema / 契约** | `invalid_job_input`、`invalid_cleaned_json`、`envelope_stage_failed`、`manifest_stage_failed`、PARSE-FAIL | **FAILED** | **否** | — | 批次重复失败 ≥1 | 可选（审计） | **是**（修 raw/schema） |
| **B. 数据规模 / 批次** | `empty_batch`、`manifest_empty`、超 `max_files`/`max_bytes`（政策） | **FAILED** | **否** | — | 超限需豁免 | 否 | **是**（拆批） |
| **C. Intake / 入口** | `intake_rejected`、`intake_deferred`、`unknown_sku`、`sku_intake_mismatch` | **FAILED** / **PENDING** | defer：**是**（定时） | 固定间隔 | reject：**是** | defer 多次：**是** | reject：**是** |
| **D. 外部 API** | 上游 Groq/LLM timeout、rate limit（清洗阶段） | **RUNNING**→**FAILED** | **是**（若 `retryable`） | 指数退避 2^n × 30s，上限 15m | 耗尽 | **是** | 否（同 job） |
| **E. QA P0** | `qa_m1_p0_failed`、M2 strict P0 | **FAILED** 或 **BLOCKED** | **否** | — | `policy=blocked` → **BLOCKED**；否则 **FAILED** + 人审 | 否 | 数据问题 → **是** |
| **F. QA P1 only** | M2 P1、`pass_with_warnings` | **DONE** | **否** | — | 商务豁免 | 否 | 否 |
| **G. Report 构建** | `report_build_failed` | **RUNNING**（checkpoint） | **是**（同 job） | 立即 3 次 | 3 次失败 | 可选 | 否 |
| **H. Storage IO** | `io_error`、`storage_failed` | **RUNNING**→**FAILED** | **是** | 指数退避 2^n × 5s | `max_retries` 耗尽 | **是** | 否 |
| **I. M2 非 strict** | `m2_checks_failed`（sample error） | **DONE** | **否** | — | 可选（运维） | 否 | 否 |
| **J. 路径 / 安全** | `path_leak`、`bootstrap_failed` | **FAILED** | **否** | — | **是** | **是** | **是**（配置票） |

### 4.2 重试参数（v0.1 缺省；Wave 7 已实现部分）

| 场景 | `max_retries` | 间隔 / 退避 | 幂等要求 | Wave 7 实现 |
|------|---------------|-------------|----------|-------------|
| Storage finalize | **3**（`DEFAULT_MAX_RETRIES`） | 实现为 **紧循环**；规格建议 **2^n × 5s**，cap 60s | `store_wave7_artifacts` 同 fingerprint skip | **已实现** 次数；退避 **未实现** |
| Manifest checkpoint store | 同 storage | 同左 | `overwrite_stage` | 失败即返回，**无**内层循环 |
| Report build | **3**（建议） | 立即 / 5s 固定 | checkpoint=manifest 时不重算 envelope | **建议**；当前单次失败即停 |
| External API（上游） | **5**（建议） | 2^n × 30s，cap 900s | 清洗输出 hash 不变则 skip | **未在** lifecycle 内 |
| Intake defer | **∞**（队列级） | 业务 `defer_until` | 新请求 | intake gate |

**不可重试集合**（与 `NON_RETRYABLE_CODES` 对齐）：  
`entry_failed`、`envelope_stage_failed`、`manifest_stage_failed`、`pipeline_stage_failed`、`report_build_failed`、`m2_checks_failed`、`qa_m1_p0_failed`、`invalid_job_input`、`intake_*`、`unknown_sku`、`sku_intake_mismatch`、`empty_batch`、`invalid_cleaned_json`。

**可重试**：仅 **`io_error`**（`ERR_IO`）在 lifecycle 内显式 `retryable=True`。

### 4.3 升级为 NEED-HUMAN 的触发条件

满足 **任一** 即应将 `orch_status` 设为 **NEED-HUMAN**（或 `blocked` + `human_required=true` 侧车）：

1. **同 job** 自动重试已达 `max_retries` 且 `error_category` 仍为 `retryable`（IO、外部 API）。  
2. `p0_failure_policy=blocked` 且 QA P0，待人豁免或改 manifest。  
3. `intake_deferred` 超过 **N** 次（建议 N=3）或超过 `defer_until` 仍无法 accept。  
4. `completed_with_failures` + 客户争议 / 商务裁定（**非自动**；事件驱动）。  
5. BLOCKED 状态持续 **> TTL**（建议 24h staging、72h prod）无操作。  
6. 重复 **同类** `error_code` 在同一 `client_ref` 下 **≥2** job（防刷）。

**人需动作**：豁免 P0、批准非标 schema、拆批、改 SKU、签发新 `job_id`、或明确 abandon。

### 4.4 升级为 DLQ 的触发条件

DLQ 为 **Gov Core 持久化侧车**（见 Progress Wave 3 记述），CLEAN job 建议对齐：

| 条件 | `dlq_reason`（建议） | 是否仍保留 job 行 |
|------|----------------------|-------------------|
| `non_retryable` 首次失败 | `non_retryable` | 是，`orch_status=FAILED` |
| 重试 + auto-recovery 耗尽 | `max_retries_exhausted` | 是 |
| NEED-HUMAN 超时 | `human_ttl_exceeded` | 是 |
| 人工拒绝继续 | `human_rejected` | 是 |

**不进 DLQ**：`intake_rejected`（无 job）、`WorkflowInterrupted` 类人工中断（Gov Core 另轨）。

**出 DLQ**：`POST /api/dlq/retry/{task_id}` 或尚書省新票 → 新 run / 新 `job_id`。

### 4.5 新票（NEW-TICKET）触发条件

| 条件 | 原因 |
|------|------|
| Schema/规则/SKU 硬失败 | 修配置非单 job resume |
| `unknown_sku` / `sku_intake_mismatch` | 产品矩阵变更 |
| 整批 `empty_batch` / 路径错误 | 新 inbound |
| BASIC→ENRICH 升级 | Wave 8+ 另票 |
| FAILED 且 `completion_variant` 不适用 | 需新 `job_id` 重跑 S0–S5 |

---

## 5. 与逻辑阶段（S0–S5）的交叉索引

| 阶段 | 常见错误类别 | 首选 `orch_status` | checkpoint |
|------|--------------|-------------------|------------|
| S0 | C | FAILED / PENDING(defer) | none |
| S1 | A | FAILED | none |
| S2 | A, B | FAILED | none |
| S3 | A, B, D | FAILED | none |
| S4 | E, F, I | FAILED / BLOCKED / DONE | manifest |
| S5 | G, H | FAILED / DONE | manifest |

**回退**（与 `WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md` §4.3 一致）：manifest checkpoint 成立后，S4/S5 失败 **不得** 默认重算 S3；须显式 `force_repipeline=true` 新 run。

---

## 6. 结构化回传（未来统一契约）

建议在 `run_wave7_job` / 队列 worker 回传中增加 **编排层** 字段（v0.2 实现票）：

```json
{
  "ok": true,
  "orch_status": "DONE",
  "orch_status_detail": {
    "completion_variant": "completed_with_failures",
    "qa_status": "pass",
    "checkpoint": "manifest",
    "human_required": false,
    "dlq_enqueued": false
  },
  "status": "done",
  "job_record": { "status": "done", "completion_variant": "completed_with_failures" },
  "retryable": false,
  "error_code": null,
  "retry_policy": { "attempt": 1, "max_attempts": 4, "next_backoff_sec": 0 }
}
```

**向后兼容**：保留现有 `status` / `completion_variant` / `qa`；`orch_status` 为超集视图。

---

## 7. 非目标（v0.1）

| 项 | 说明 |
|----|------|
| 修改 Wave 7 常量名 | 仅文档映射；代码另票 |
| 多 job 调度 / 锁 | 不在本稿 |
| Phase 6.5 `delivery.status` | 不在本稿 |
| 完整 DLQ schema | 引用 Gov Core 既有表；不复制 SQL |
| M2 P1 → Chargeable 全表 | 见 R3 / Wave 8 runbook |

---

## 8. 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草稿：六态 + 侧车、Wave 7 映射、错误矩阵、文字状态图 |

**下一版预期**：`orch_status` 写入 Postgres jobs 表；与 `TASK_ROUTING.md` / `error_taxonomy` 联合矩阵；退避在 lifecycle 内实现。

---

*CLEAN-Orchestrator State Machine · `04_Workflows/WAVE7_CLEAN_ORCH_STATE_MACHINE_v0.1.md`*
