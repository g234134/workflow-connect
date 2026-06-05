# Wave 7 – CLI / 日常开发 / QA Runbook（v0.1）

> **受众**：接盘工程师（运维、后端、QA）  
> **性质**：实战操作指南（非规格正文）  
> **范围**：Wave 6 DATA-CLEANING v1.0 + Wave 7 CLEAN-RUNNER/ORCH 已交付能力  
> **依据**：`WAVE7_CLEAN_RUNNER_ORCH_OVERVIEW_v0.1.md`、`WAVE7_INT_REGRESSION_GATE_v0.1.md`；暗部 `core/wave7_*`  
> **不做**：改代码、扩规格；**不覆盖** Wave 8（M2 抽样、Markdown 报告、invoice、bridge 等 — 见 §9）

---

## 0. 背景与边界

Wave 7 把 Wave 6 单模块能力装配成 **单 job 可重跑链**：环境引导 → job 构造 → pipeline（envelope/manifest）→ report summary → QA-M1 → 工件落盘。本 runbook 只说明 **如何在战车根用 CLI / Python 跑通一条真实 BASIC job**，以及如何读结果、跑最小回归门、挂 CI。

**真相层声明**：本 runbook **只消费** Wave 6/7 平台与 `Master_Map.json` 逻辑路径；**不修改** envelope / manifest / QA 规格或 R3/R4 裁定语义。

**与 Wave 8 分界**：`report.md` 渲染、`qa.sample_validation` 实跑、M2 抽样、`customer_ack` / invoice、bridge sidecar — **刻意留白**（§9）。

---

## 1. 建议章节结构（本文件目录）

| § | 主题 |
|---|------|
| 0 | 背景与边界 |
| 2 | 前置：venv、bootstrap、逻辑路径 |
| 3 | 跑一条真实 BASIC job（端到端） |
| 4 | 查看 job 结果（report / QA / 逻辑路径） |
| 5 | `completed_with_failures` 与 `qa_status` |
| 6 | 日常开发：Tier-A 最小门禁 |
| 7 | CI：INT-REGRESSION-GATE |
| 8 | FAQ（常见故障） |
| 9 | Wave 8 留白与延伸阅读 |

---

## 2. 前置：venv、bootstrap、逻辑路径

### 2.1 工作目录与 Python

- **工作目录**：战车根（含 `04_Workflows/Master_Map.json`、`00_master_plan.md`）。
- **解释器**：暗部 `gov_core_system` venv（与 `Master_Map.cabins.gov_core_system` 一致），**不是** `gov_main` / `gov_agency`。

```powershell
# 战车根下 — 建议先设别名（整篇复用）
$GovPy = ".\01_Environments\python_venvs\gov_core_system\Scripts\python.exe"
$GovPy -c "import core.wave7_orch_job_lifecycle; print('gov_core OK')"
```

战车主舱脚本 `Enter-Main.ps1` 激活的是 `gov_main`；Wave 7 **必须**用 `gov_core_system`（与 `04_Workflows/_wave7_*.py` 从地图注入 venv 的方式一致）。

### 2.2 环境自检（RUNNER-ENV-BOOTSTRAP）

```powershell
python .\04_Workflows\_wave7_runner_bootstrap.py --check --pretty
```

期望：stdout JSON 中 `"ok": true`；`paths_resolved` 含三键（逻辑段，非盘符绝对路径）：

| 键 | 地图来源 | 典型逻辑段（实例以本机 `gov_paths` 为准） |
|----|----------|------------------------------------------|
| `cleaned_full` | `wave7_paths.cleaned_full` | `05_Temp_Cache/cleaned_full` |
| `staging_root` | `wave7_paths.staging_root` | `05_Temp_Cache/staging/wave7` |
| `delivery_root` | `wave7_paths.delivery_root` | `06_Exports_Output/wave7/delivery` |

仅看路径、不跑 schema 检查：

```powershell
python .\04_Workflows\_wave7_runner_bootstrap.py --dry-run --pretty
```

### 2.3 逻辑交付引用（R4）

落盘成功后，API/编排回传中的 **artifact ref** 使用：

```text
w6://delivery/{job_id}/manifest
w6://delivery/{job_id}/report_json
w6://delivery/{job_id}/report_md      # Wave 7 可为占位
w6://delivery/{job_id}/deliverables   # per-file envelopes 目录语义
```

物理目录在 `{delivery_root}/{job_id}/` 下（`manifest.json`、`report.json`、`deliverables/envelopes/`、`.wave7_generation.json` 等）。**禁止**在日志或对外 JSON 中粘贴 `C:\...` 绝对路径。

---

## 3. 跑一条真实 BASIC job（端到端）

Wave 7 当前有两类入口：

| 步骤 | 能力 | CLI / API |
|------|------|-----------|
| A | 环境 + 路径 | `04_Workflows/_wave7_runner_bootstrap.py` |
| B | 构造 `job_record` + `raw_files[]` | 暗部 `core.wave7_runner_entry_job_input`（`-m` 或并入 C） |
| C | 单 job 全链路（bootstrap + entry + orchestrator） | `04_Workflows/_wave7_run_job.py`（`Master_Map.runners.wave7_run_job`） |

### 3.1 步骤 B：从真实批次构造 job（RUNNER-ENTRY）

**方式 1 — 扫描 cleaned 目录**（适合 `cleaned_full` / `cleaned_sample` 下已有 `*.json`）：

```powershell
& $GovPy -m core.wave7_runner_entry_job_input `
  --sku CLEAN-BASIC `
  --client-ref runbook-dev-001 `
  --cleaned-dir 05_Temp_Cache/cleaned_sample `
  --base-dir .
```

成功时打印两行 JSON：摘要（含 `job_id`）+ `raw_files_count`。失败时 exit code `1`，`error_code` 稳定（如 `empty_batch`、`unknown_sku`）。

**方式 2 — 队列 JSON**（更接近生产消息）：

```powershell
& $GovPy -m core.wave7_runner_entry_job_input `
  --sku CLEAN-BASIC `
  --client-ref runbook-queue-001 `
  --queue-json path\to\queue_minimal.json `
  --intake-json path\to\intake_accept.json `
  --base-dir .
```

`intake_request` 可选；`decision=accept` 才进入构造（见 Wave 6 intake gate）。

**方式 3 — 批次 manifest 路径**：加 `--manifest path\to\batch_manifest.json`。

> **注意**：仅跑 entry（步骤 B）时，`-m core.wave7_runner_entry_job_input` **默认不打印** `raw_files` 全文。端到端请用 §3.2 正式 runner。

### 3.2 步骤 C：跑一条 BASIC job（`_wave7_run_job.py`）

战车根执行（脚本从 `Master_Map.json` 注入 `gov_core_system`，与 bootstrap／regression gate 相同）：

```powershell
python .\04_Workflows\_wave7_run_job.py `
  --sku CLEAN-BASIC `
  --client-ref runbook-once `
  --cleaned-dir 05_Temp_Cache/cleaned_sample `
  --pretty
```

**队列 + intake**（与 `test_happy_path_intake_to_done` 同构）：

```powershell
python .\04_Workflows\_wave7_run_job.py `
  --sku CLEAN-BASIC `
  --client-ref runbook-queue-001 `
  --queue-json path\to\queue_minimal.json `
  --intake-json path\to\intake_accept.json `
  --pretty
```

可选：`--job-id`、`--manifest`、`--base-dir`（默认 repo 根）。

**stdout**：成功时 JSON 至少含 `ok`、`status`、`stage`、`artifacts`、`qa`、`completion_variant`、`message`、`error_code`；entry 失败时打印 entry 完整错误结构并 exit `1`；bootstrap 失败 exit `2`。

**保存结果**（PowerShell）：

```powershell
python .\04_Workflows\_wave7_run_job.py --sku CLEAN-BASIC --client-ref runbook-once `
  --cleaned-dir 05_Temp_Cache/cleaned_sample | Set-Content -Encoding utf8 .\result.json
```

### 3.3 成功时确认落盘

1. 看 `run_wave7_job` 回传 `artifacts`：`manifest_ref` / `report_ref` / `deliverables_ref` 应为 `w6://delivery/{job_id}/...`。
2. 在磁盘上打开 `{delivery_root}/{job_id}/`（`delivery_root` 来自 bootstrap 的 `paths_resolved`，默认地图指向 `06_Exports_Output/wave7/delivery`）。
3. 应存在至少：`manifest.json`、`report.json`、`deliverables/envelopes/*.json`、`.wave7_generation.json`（幂等指纹）。

**开发期隔离**：若不想写入正式 `delivery_root`，可在脚本里 **仅用于本地** 覆盖 `paths_resolved`（单测做法）：把 `staging_root` / `delivery_root` 指到 `05_Temp_Cache/staging/wave7/_dev_run/...` 下的子目录；生产/CI 应使用 bootstrap 默认解析。

### 3.4 流水线阶段顺序（排障用）

```text
entry → pipeline (envelope + manifest) → report → QA-M1 → storage (finalize)
```

失败时看回传 `stage`（`entry` / `pipeline` / `report` / `qa` / `storage`）与 `error_code`（如 `unknown_sku`、`pipeline_stage_failed`、`qa_m1_p0_failed`）。

---

## 4. 查看 job 结果

### 4.1 `report.json` → `summary`

路径：`{delivery_root}/{job_id}/report.json`（或通过 `w6://delivery/{job_id}/report_json` 定位）。

| 字段 | 含义 |
|------|------|
| `summary.accepted_units` | manifest 中 `clean_status=ok` 行数；与 QA-M1 `M1-COUNT` 对账 |
| `summary.rejected_units` | 非 ok 行数 |
| `summary.billing_units.U` / `.L` | 计费单位（BASIC 通常主要看 `U`） |
| `summary.qa_status` | `pass` \| `pass_with_warnings` \| `fail`（R3 §G.6–G.7 映射，由 M1 失败推导） |
| `summary.cost.*` | 金额可为 `null`（表版本占位）；`chargeable_hint` 为提示非最终开票 |

示例（节选）：

```json
"summary": {
  "accepted_units": 1,
  "billing_units": { "U": 1, "L": 0 },
  "qa_status": "pass"
}
```

### 4.2 QA-M1 → `report.qa.manifest_integrity` 与 `failures`

| 字段 | 用途 |
|------|------|
| `qa.manifest_integrity.ok` | M1 聚合是否通过 |
| `qa.manifest_integrity.checked_rows` / `failed_rows` / `failed_checks` | 扫描规模与失败计数 |
| `qa.failures[]` | 逐条失败；每项含 `check_id`（如 `M1-COUNT`、`M1-SKU-ENRICH`、`M1-DEDUP`）、`severity`、`message`、行定位 |

M1 **只读 manifest**，不打开 `deliverables/` 内 envelope 文件（规格见 `WAVE6_IMPL_QA_M1_TICKET_v0.1.md`）。

`run_wave7_job` 回传里的 `qa` 键与写入 `report.json` 的 `qa` 区块同源（编排器内存结果）。

### 4.3 编排回传快速检查

```powershell
# 假设上一步将 stdout 存为 result.json
(Get-Content .\result.json | ConvertFrom-Json).ok
(Get-Content .\result.json | ConvertFrom-Json).status          # done | failed | blocked
(Get-Content .\result.json | ConvertFrom-Json).completion_variant
(Get-Content .\result.json | ConvertFrom-Json).artifacts
```

---

## 5. `completed_with_failures` 与 `qa_status`（R3 §G.7 简述）

二者 **不同层**，不要混用：

| 概念 | 位置 | 何时出现 |
|------|------|----------|
| `qa_status` | `report.summary` | 仅由 **QA-M1** 失败严重度映射：`pass`（无 P0/P1）、`pass_with_warnings`（仅 P1）、`fail`（任一 P0） |
| `completed_with_failures` | `job_record.completion_variant`（`status=done` 时） | manifest 存在 **rejected 行**，但 M1 **无 P0**；job 仍算跑完并落盘 |

Wave 7 实现要点（`wave7_orch_job_lifecycle.py`）：

- M1 有 P0 → 默认 `status=failed`，`qa_status=fail`，**不会** finalize（可配置 `p0_failure_policy=blocked`）。
- manifest 有 `clean_status!=ok` 行且 M1 通过 → `ok=true`、`status=done`、`completion_variant=completed_with_failures`。
- **Wave 8 才谈** M2 P1 与 chargeable 的完整 R3 表；本 runbook 不展开 M2 / invoice。

---

## 6. 日常开发：Tier-A 最小门禁

### 6.1 命令

战车根（脚本自行注入 `gov_core_system`）：

```powershell
python .\04_Workflows\_wave7_regression_gate.py --tier A
```

更详细日志：

```powershell
python .\04_Workflows\_wave7_regression_gate.py --tier A -vv --pretty
```

### 6.2 输出 JSON 字段

| 字段 | 含义 |
|------|------|
| `ok` | **合并门槛**：`true` 才可合入（与 exit code 0 一致） |
| `suite` / `tier` | 当前为 `A` |
| `tests_run` | 运行的测试用例数 |
| `passed` / `failed` / `errors` | unittest 统计 |
| `failed_tests[]` | 失败列表；项内可含 `test_id`、`stage`、`job_id`、`first_qa_check_id`（从断言文本解析） |
| `tier_b_pending` | 仅 `--tier B` 时出现；当前 Tier-B **无模块**，为 `true` 时仍 `ok: true` |

失败时 stderr 另有首条诊断行，形如：

```text
INT-REGRESSION-GATE first failure: test=... stage=envelope job_id=... first_qa_check_id=M1-COUNT
```

### 6.3 什么算「可以合并」

- Exit code **`0`** 且 stdout JSON **`"ok": true`** 且 **`failed_tests` 为空**。
- 改动了 envelope / manifest / QA-M1 / Wave 7 orchestrator / runner / artifact 路径治理时，**必须**跑 Tier-A；不要改用全库 `pytest` 代替（范围见 `WAVE7_INT_REGRESSION_GATE_v0.1.md` §4）。
- Tier-B / ALL：当前 B 为空集；`--tier ALL` 在 B 未注册时等价于 A。

---

## 7. CI：挂 INT-REGRESSION-GATE

### 7.1 Runner 索引

| 键 | 脚本 |
|----|------|
| `runners.wave7_run_job` | `04_Workflows/_wave7_run_job.py` |
| `runners.wave7_runner_bootstrap` | `04_Workflows/_wave7_runner_bootstrap.py` |
| `runners.wave7_regression_gate` | `04_Workflows/_wave7_regression_gate.py` |

### 7.2 推荐 Job 步骤（GitHub Actions / Azure Pipelines 等）

```yaml
# 伪代码 — 工作目录 = 仓库 checkout 根
- name: Wave 6/7 integration regression (Tier-A)
  run: python 04_Workflows/_wave7_regression_gate.py --tier A
  shell: pwsh   # 或 bash；Python 需能加载 gov_core_system（地图相对 venv）
```

- **只跑** Tier-A 登记的 11 个 `tests.test_*` 模块（Wave 6/7），**不**跑全库。
- 使用与本地相同的 `gov_core_system` venv（CI 镜像需预装或 bootstrap 暗部 venv）。

### 7.3 失败处理建议

1. 步骤 exit code **`1`** → 阻断合并。
2. 解析 **stdout 最后一行 JSON**（或整段 JSON）的 `ok`。
3. 若 `ok: false`，打印 `failed_tests[0]` 的：
   - `test_id`
   - `stage`（如 `envelope`、`qa`）
   - `job_id`
   - `first_qa_check_id`（如 `M1-COUNT`、`M1-SKU-ENRICH`）
4. 同时抓取 **stderr** 中 `INT-REGRESSION-GATE first failure:` 行便于工单粘贴。
5. Exit code **`2`** → 配置/加载错误（地图、venv、模块 import），按基础设施故障处理，非单测回归。

PowerShell 解析示例：

```powershell
$json = python .\04_Workflows\_wave7_regression_gate.py --tier A | Select-Object -Last 1 | ConvertFrom-Json
if (-not $json.ok) {
  $f = $json.failed_tests[0]
  Write-Error "gate failed: $($f.test_id) stage=$($f.stage) job_id=$($f.job_id) qa=$($f.first_qa_check_id)"
  exit 1
}
```

---

## 8. FAQ（常见故障）

### 8.1 `bootstrap` 失败：缺 `Master_Map` 键或 schema

**现象**：`_wave7_runner_bootstrap.py` 退出码 `2`，JSON `ok: false`，`message` 含 `wave7_paths[...]` 或 `schema_files`。

**排查**：

1. 确认在 **战车根** 执行（能找到 `04_Workflows/Master_Map.json`）。
2. 打开地图 → `wave7_paths` 三键是否各有 `department` + `sub_type`；`gov_paths` 能否解析对应部门目录。
3. `--check` 时核对 `wave7_bootstrap.schema_files.envelope_v2` 相对路径在仓库内存在。
4. 代码入口：`core/wave7_runner_env_bootstrap.py`（`resolve_wave7_logical_paths`、`run_bootstrap_check`）。

### 8.2 Runner entry：`unknown_sku` / `sku_intake_mismatch`

| `error_code` | 常见原因 | 处理 |
|--------------|----------|------|
| `unknown_sku` | `--sku` 不是 `CLEAN-BASIC` / `CLEAN-ENRICH` | 修正 SKU 字面量（大小写不敏感，会 normalize） |
| `sku_intake_mismatch` | `intake_request.product_sku` 与 runner `sku` 不一致 | 对齐 intake JSON 与 CLI `--sku` |
| `intake_rejected` / `intake_deferred` | intake gate 未 accept | 修 intake 描述/标签或走无 intake 的直连 `job_record` 路径 |
| `empty_batch` | 目录无合法 `*.json` 或队列无有效 files | 检查 `cleaned_dir` / `queue_payload.files` |

代码入口：`core/wave7_runner_entry_job_input.py`（`build_runner_job_input`、`_evaluate_intake`）。

### 8.3 INT-REGRESSION-GATE：`M1-COUNT` 失败

**含义**：`report.summary.accepted_units` 与 manifest 中 `clean_status=ok` 行数不一致。

**排查**：`core/wave7_report_summary_producer.py`（summary 计数）与 `core/wave6_manifest_writer.py`（manifest 行状态）；对照失败用例里的 `job_id` 在 `tests.test_wave7_report_summary_producer` / `tests.test_wave6_qa_manifest_m1`。

### 8.4 INT-REGRESSION-GATE：ENRICH `present` 相关失败

**含义**：ENRICH 流水线在 **唯一 seam** 剥离/规范化 `enrichment.present`（BASIC 不得残留 `enrichment` 键）。

**排查**：

- `core/wave7_orch_pipeline_wire.py`（`normalize_manifest_inputs` / pipeline wire）
- `core/envelope_writer.py` + `tests.test_wave7_orch_pipeline_wire`（`test_enrich_present_*`）
- 若仅 BASIC job 失败，先确认未误用 `CLEAN-ENRICH` 或 raw 行带 `enrichment`。

### 8.5 Job `ok: true` 但 `qa_status=fail` 或无法落盘

- `qa_status=fail`：M1 P0 失败，通常 `status=failed` 且 **无** 完整 delivery 四件套。
- `storage` / `io_error`：看重试字段 `retryable`；检查 `delivery_root` 可写；失败树可能在 `{job_id}/failed/` 与 `staging/.../quarantine/{job_id}/recovery_audit.json`（`core/wave7_artifact_storage.py`）。

---

## 9. Wave 8 留白与延伸阅读

| 主题 | 状态 |
|------|------|
| M2 抽样 QA（`qa.sample_validation` 实跑） | Wave 8 |
| `report.md` / 客户可读 Markdown | Wave 8 |
| `customer_ack`、invoice、bridge sidecar | Wave 8 |
| Tier-B 更重集成（同 job 幂等重跑等） | 清单在 `WAVE7_INT_REGRESSION_GATE_v0.1.md` §6，模块待注册 |

**规格与票证（不重复条文）**：

- 总览：`WAVE7_CLEAN_RUNNER_ORCH_OVERVIEW_v0.1.md`
- 环境票：`WAVE7_RUNNER_ENV_BOOTSTRAP_v0.1.md`
- 入口票：`WAVE7_RUNNER_ENTRY_JOB_INPUT_v0.1.md`
- 门禁票：`WAVE7_INT_REGRESSION_GATE_v0.1.md`
- Wave 6 QA-M1：`WAVE6_IMPL_QA_M1_TICKET_v0.1.md`
- R3 §G.6–G.7：`WAVE6_DATA_CLEANING_R3_APPENDICES_v0.1.md`

---

*Wave 7 operator runbook · `04_Workflows/WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md` · v0.1*
