# Wave 8 — CleanJob Submit CLI 运维手册附录（v0.1）

> **票号**：`W8-CLEAN-SUBMIT-APPENDIX`  
> **受众**：工程工程师、QA 工程师  
> **性质**：操作指南附录  
> **主文档**：`WAVE8_M2_RUNBOOK_v0.1.md`  
> **范围**：`04_Workflows/_wave8_submit_clean_job.py` 命令使用说明

---

## 1. 命令概览

`_wave8_submit_clean_job.py` 是 Wave 8 CleanJob 的工程/QA 提交入口，包装 `core.wave8_clean_submit_adapter`。

| 模式 | 命令标志 | 行为 |
|------|----------|------|
| **Preview** | `--dry-run` | 仅验证 intake → CleanJob → Wave7 inputs 映射链，不执行 lifecycle |
| **Submit** | (默认) | 执行完整映射并调用 Wave7 lifecycle，真正提交 job |

---

## 2. 前置要求

### 2.1 环境

- 工作目录：战车根（含 `04_Workflows/`）
- Python 解释器：暗部 `gov_core_system` venv

```powershell
# 快速检查 venv 可用
$GovPy = ".\01_Environments\python_venvs\gov_core_system\Scripts\python.exe"
$GovPy -c "from core.wave8_clean_submit_adapter import submit_intake_record; print('Adapter OK')"
```

### 2.2 Intake JSON 准备

参考 fixtures：
- `04_Workflows/fixtures/intake_basic_sample.json` — BASIC SKU 示例
- `04_Workflows/fixtures/intake_enrich_sample.json` — ENRICH SKU 示例

---

## 3. 命令详解

### 3.1 Preview 模式（推荐先跑）

验证 intake JSON 格式正确，且能完整映射到 CleanJob → Wave7 inputs：

```powershell
python .\04_Workflows\_wave8_submit_clean_job.py `
  --intake-json .\04_Workflows\fixtures\intake_basic_sample.json `
  --dry-run `
  --pretty
```

期望输出（成功）：

```json
{
  "ok": true,
  "stage": "preview",
  "clean_job": {
    "job_id": "w8-basic-...",
    "sku": "CLEAN-BASIC",
    "options": { ... }
  },
  "job_record": { ... },
  "raw_files": [ ... ],
  "raw_files_count": 1,
  "sidecar": { ... },
  "message": "preview: mapping and bridge complete",
  "run_result": null,
  "error_code": null,
  "schema_version": "wave8_clean_submit_adapter_v0.1"
}
```

### 3.2 Submit 模式（真正提 job）

确认 preview 通过后，去掉 `--dry-run` 提交：

```powershell
python .\04_Workflows\_wave8_submit_clean_job.py `
  --intake-json .\04_Workflows\fixtures\intake_basic_sample.json `
  --pretty
```

期望输出（成功）：

```json
{
  "ok": true,
  "stage": "submit",
  "clean_job": { ... },
  "job_record": { ... },
  "raw_files": [ ... ],
  "raw_files_count": 1,
  "sidecar": { ... },
  "run_result": {
    "ok": true,
    "job_id": "w8-basic-...",
    "status": "completed",
    "message": "Wave7 lifecycle completed"
  },
  "message": "Wave7 lifecycle finished",
  "error_code": null,
  "schema_version": "wave8_clean_submit_adapter_v0.1"
}
```

### 3.3 带详细日志

```powershell
python .\04_Workflows\_wave8_submit_clean_job.py `
  --intake-json .\path\to\intake.json `
  --pretty `
  --verbose
```

`--verbose` 会输出诊断信息到 stderr，不影响 stdout JSON 解析。

---

## 4. 提交 BASIC Job

### 4.1 完整流程

```powershell
# Step 1: Preview 验证
$preview = python .\04_Workflows\_wave8_submit_clean_job.py `
  --intake-json .\04_Workflows\fixtures\intake_basic_sample.json `
  --dry-run --pretty | ConvertFrom-Json

if (-not $preview.ok) {
  Write-Host "Preview failed: $($preview.message)" -ForegroundColor Red
  exit 1
}

# Step 2: Submit
python .\04_Workflows\_wave8_submit_clean_job.py `
  --intake-json .\04_Workflows\fixtures\intake_basic_sample.json `
  --pretty
```

### 4.2 预期字段映射

| Intake 字段 | CleanJob 字段 | 说明 |
|-------------|---------------|------|
| `intake_id` | `job_id` | 生成 Wave8 job ID |
| `product_sku` | `sku` | `CLEAN-BASIC` |
| `data_sources[]` | `raw_files` | 清洗后数据源 |
| `schema_definition` | `options.schema` | 字段定义 |
| `scheduling.deadline_utc` | `options.deadline` | 截止时间 |

---

## 5. 提交 ENRICH Job

### 5.1 ENRICH 与 BASIC 的差异

ENRICH SKU 需要额外字段：
- `enrich_configuration`：提示词、字段映射、输出格式
- `data_sources` 可能包含多个源（主表 + 辅表）

### 5.2 完整流程

```powershell
# Preview
python .\04_Workflows\_wave8_submit_clean_job.py `
  --intake-json .\04_Workflows\fixtures\intake_enrich_sample.json `
  --dry-run --pretty

# Submit
python .\04_Workflows\_wave8_submit_clean_job.py `
  --intake-json .\04_Workflows\fixtures\intake_enrich_sample.json `
  --pretty
```

### 5.3 ENRICH 特有选项

从 `enrich_configuration` 映射到 `clean_job.options`：

```json
{
  "options": {
    "enrich_prompt": "...",
    "field_mapping": { ... },
    "output_format": "jsonl",
    "enable_m2": true,
    "render_report_md": true
  }
}
```

---

## 6. 故障排查

### 6.1 Exit Code 1 + intake_load_failed

**现象**：`"error_code": "intake_load_failed"`

**排查**：
1. 确认文件路径正确：`Test-Path .\path\to\intake.json`
2. 确认 JSON 格式有效：`Get-Content .\path\to\intake.json | ConvertFrom-Json`
3. 确认文件非空

### 6.2 core_path_not_found

**现象**：找不到 `gov_core_system` 核心路径

**排查**：
1. 确认工作目录是战车根（含 `01_Environments/` 和 `04_Workflows/`）
2. 确认 venv 已初始化：`Test-Path .\01_Environments\python_venvs\gov_core_system\core`

### 6.3 import_error

**现象**：无法导入 `submit_intake_record`

**排查**：
1. 确认 adapter 存在：`Test-Path .\01_Environments\python_venvs\gov_core_system\core\wave8_clean_submit_adapter.py`
2. 确认依赖已安装：`pip list | findstr wave8`

### 6.4 映射阶段失败

**现象**：`"stage": "intake_mapping"` 且 `ok: false`

**常见原因**：
- `intake_id` 缺失或格式错误
- `product_sku` 不在允许列表（`CLEAN-BASIC`, `CLEAN-ENRICH`, ...）
- `data_sources` 为空或格式错误
- `schema_definition` 缺少必需字段

**修复**：对照 `fixtures/intake_*.json` 修正 intake JSON。

### 6.5 Bridge 阶段失败

**现象**：`"stage": "job_bridge"` 且 `ok: false`

**常见原因**：
- CleanJob 结构不满足 Wave7 输入要求
- `raw_files` 解析失败

### 6.6 Submit 阶段失败

**现象**：`"stage": "submit"` 且 `ok: false`

**排查**：查看 `run_result.message` 和 `run_result.error_code`：

```powershell
$result = python .\04_Workflows\_wave8_submit_clean_job.py ... | ConvertFrom-Json
$result.run_result | Format-List
```

---

## 7. 自动化脚本示例

### 7.1 CI Pipeline 集成

```powershell
# CI 步骤：提交 intake 并检查结果
$ErrorActionPreference = "Stop"

$result = python .\04_Workflows\_wave8_submit_clean_job.py `
  --intake-json $env:INTAKE_JSON_PATH `
  --pretty | ConvertFrom-Json

if (-not $result.ok) {
  Write-Error "CleanJob submit failed: $($result.message)"
  exit 1
}

$jobId = $result.clean_job.job_id
Write-Host "Job submitted successfully: $jobId"

# 后续步骤可使用 $jobId 查询状态
```

### 7.2 批量 Preview（非批量 submit）

注意：本 CLI 不支持多 job 批处理。如需批量 preview，用 shell loop：

```powershell
$intakeFiles = Get-ChildItem .\fixtures\intake_*.json
foreach ($file in $intakeFiles) {
  Write-Host "Previewing: $($file.Name)"
  $result = python .\04_Workflows\_wave8_submit_clean_job.py `
    --intake-json $file.FullName `
    --dry-run | ConvertFrom-Json

  if ($result.ok) {
    Write-Host "  OK: $($result.clean_job.job_id)" -ForegroundColor Green
  } else {
    Write-Host "  FAILED: $($result.message)" -ForegroundColor Red
  }
}
```

---

## 8. 字段速查表

### 8.1 CLI 参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--intake-json` | 是 | - | Intake JSON 文件路径 |
| `--dry-run` | 否 | false | Preview 模式，仅验证不提交 |
| `--pretty` | 否 | false | 美化输出 JSON |
| `--verbose` | 否 | false | 详细日志到 stderr |

### 8.2 输出字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 操作是否成功 |
| `stage` | string | 执行到的阶段：`preview` / `submit` / `intake_mapping` / `job_bridge` |
| `clean_job` | object | 映射后的 CleanJob 对象 |
| `job_record` | object | Wave7 job_record |
| `raw_files` | array | 原始文件列表 |
| `raw_files_count` | int | 文件数量 |
| `sidecar` | object | Bridge 产生的 sidecar 元数据 |
| `run_result` | object | Wave7 lifecycle 执行结果（submit 模式且执行后） |
| `message` | string | 人类可读状态信息 |
| `error_code` | string | 错误代码（`ok=false` 时） |
| `validation_errors` | array | 验证错误详情（映射失败时） |
| `schema_version` | string | Schema 版本标识 |

---

## 9. 与其他命令的关系

| 命令 | 用途 | 与本命令关系 |
|------|------|--------------|
| `_wave8_preview_clean_job_mapping.py` | 仅验证映射链 | 本命令 `--dry-run` 等效但更轻量 |
| `_wave8_m2_rerun.py` | M2 抽样 QA | 对已完工 job 执行 QA，非提交 |
| `_wave8_m2_bootstrap.py` | M2 环境自检 | 提交前可跑确认环境就绪 |
| `_factory_wave_01.py` | 批量发起 Wave | 面向运营场景，非工程提交 |

---

*Wave 8 CleanJob Submit CLI 运维手册附录 · `04_Workflows/WAVE8_CLEAN_JOB_SUBMIT_RUNBOOK_APPENDIX_v0.1.md` · v0.1*
