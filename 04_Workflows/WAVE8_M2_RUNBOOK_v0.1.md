# Wave 8 – M2 抽样 QA 运维手册（v0.1）

> **票号**：`W8-M2-TOOLING-RUNBOOK`  
> **受众**：QA 工程师、运营、客户成功（CS）  
> **性质**：运维操作指南（非规格正文）  
> **范围**：M2 设计与执行引擎已交付后的工具使用说明  
> **不做**：改核心逻辑、实现 M2 引擎、财务开票流程

---

## 0. 背景与边界

M2（`qa.sample_validation`）是对 `deliverables/envelopes/*.json` 进行**抽样深检**的 QA 层，与 M1 的全量 manifest 扫描形成互补。

| 层级 | 扫描范围 | 检查深度 | 典型检查项 |
|------|----------|----------|------------|
| **M1** | manifest.json 全量 | 表层键值 | `M1-KEYS` / `M1-SHA` / `M1-DEDUP` / `M1-COUNT` |
| **M2** | envelope 文件抽样 | 内容语义 | `M2-ENVELOPE-EXIST` / `M2-SCHEMA` / `M2-CONTENT-INTEGRITY` / `M2-SEED-REPRO` |

**M2 与 M1 的关系**：
- M2 **依赖 M1 通过**（`manifest_integrity.ok=true`）才会执行
- M2 P0 失败同样阻断 `Done` / `Chargeable`
- `qa.overall_ok = M1.ok ∧ M2.ok`（当 M2 未执行时为 `null` 或仅反映 M1）

**Wave 7 vs Wave 8**：
- Wave 7：`sample_validation.status = "skipped"`（占位）
- Wave 8：M2 引擎实跑，支持分层抽样与种子重现

---

## 1. 手册目录

| § | 主题 |
|---|------|
| 0 | 背景与边界 |
| 2 | 前置：venv 与逻辑路径 |
| 3 | 从 job_id / report.json / manifest.json 重跑 M2 |
| 4 | 解读 `sample_validation` 段落 |
| 5 | M2 P0 / P1 / P2 严重度说明 |
| 6 | 分层抽样配置说明 |
| 7 | 常见故障排查 |
| 8 | 与 report.md / CS 解释对照 |
| 9 | 延伸阅读 |

---

## 2. 前置：venv 与逻辑路径

### 2.1 工作目录与 Python

- **工作目录**：战车根（含 `04_Workflows/Master_Map.json`）
- **解释器**：暗部 `gov_core_system` venv

```powershell
# 战车根下设置别名
$GovPy = ".\01_Environments\python_venvs\gov_core_system\Scripts\python.exe"
$GovPy -c "import core.wave8_m2_validator; print('M2 OK')"
```

### 2.2 M2 专属环境自检

```powershell
python .\04_Workflows\_wave8_m2_bootstrap.py --check --pretty
```

期望：stdout JSON 中 `"ok": true`；`paths_resolved` 含：

| 键 | 地图来源 | 说明 |
|----|----------|------|
| `delivery_root` | `wave7_paths.delivery_root` | 已完工 job 的 delivery 目录 |
| `m2_staging` | `wave8_paths.m2_staging` | M2 临时工作区（解包、展开） |
| `envelope_schema` | `wave8_bootstrap.schema_files.envelope_v2` | envelope 校验 schema |

### 2.3 逻辑路径引用（R4）

对已完工 job，artifact ref 格式：

```text
w6://delivery/{job_id}/manifest
w6://delivery/{job_id}/report_json
w6://delivery/{job_id}/deliverables
```

---

## 3. 从既有工件重跑 M2

### 3.1 场景 A：从 job_id 重跑（推荐）

已有完工 job，需要**补充执行**或**重跑** M2（例如调整抽样率）：

```powershell
python .\04_Workflows\_wave8_m2_rerun.py `
  --job-id w6-2024-001-basic `
  --sample-rate 0.1 `
  --stratify-by sku `
  --seed 42 `
  --pretty
```

参数说明：

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--job-id` | 是 | - | 目标 job ID |
| `--sample-rate` | 否 | 0.05 | 抽样比例（0.0–1.0） |
| `--stratify-by` | 否 | null | 分层字段（如 `sku` / `extension` / `quality_tier`） |
| `--seed` | 否 | 当前日期 | 重现种子 |
| `--force` | 否 | false | 覆盖既有 M2 结果 |

### 3.2 场景 B：从 report.json + manifest.json 重跑

适用于**跨环境验证**或**report 已导出但需复现 M2 结论**：

```powershell
python .\04_Workflows\_wave8_m2_rerun.py `
  --report-json path\to\report.json `
  --manifest-json path\to\manifest.json `
  --deliverables-dir path\to\deliverables `
  --sample-rate 0.1 `
  --seed 42 `
  --pretty
```

### 3.3 场景 C：仅从 manifest.json 构造最小 M2 输入

用于**验证抽样算法**本身（不打开 envelope）：

```powershell
python .\04_Workflows\_wave8_m2_dry_run.py `
  --manifest-json path\to\manifest.json `
  --sample-rate 0.1 `
  --stratify-by extension `
  --seed 42 `
  --pretty
```

输出：被选中的 `file_id` 列表（ Dry run，不执行实际检查）

### 3.4 重跑后确认落盘

M2 结果会**追加**或**更新**原 report.json（根据 `--force`）：

```json
{
  "qa": {
    "manifest_integrity": { ... },
    "sample_validation": {
      "status": "completed",
      "ok": true,
      "seed": 42,
      "sample_rate": 0.1,
      "total_envelopes": 1000,
      "sampled_count": 50,
      "stratified_by": "extension",
      "strata_distribution": {
        "pdf": { "population": 600, "sampled": 30 },
        "docx": { "population": 400, "sampled": 20 }
      },
      "checked_at": "2024-01-15T10:30:00Z"
    },
    "failures": [ ... ]
  }
}
```

---

## 4. 解读 `sample_validation` 段落

### 4.1 状态字段速查

| 字段 | 类型 | 含义 |
|------|------|------|
| `status` | string | `skipped` / `pending` / `completed` / `failed` |
| `ok` | bool | `true` = 无 P0 失败；`false` = 存在 P0；`null` = 未执行 |
| `seed` | int | 抽样种子（重现用） |
| `sample_rate` | float | 实际抽样比例 |
| `total_envelopes` | int | 可选：母体大小 |
| `sampled_count` | int | 实际抽样检查数 |
| `stratified_by` | string/null | 分层字段 |
| `strata_distribution` | object | 各层母体/抽样数对照 |
| `checked_at` | ISO8601 | 执行时间戳 |

### 4.2 与 M1 结果的对照

```json
{
  "qa": {
    "manifest_integrity": {
      "ok": true,
      "checked_rows": 1000,
      "failed_rows": 0,
      "failed_checks": 0
    },
    "sample_validation": {
      "status": "completed",
      "ok": true,
      "sampled_count": 50
    },
    "overall_ok": true
  }
}
```

**解读**：
- M1 全量通过（1000 行全部 OK）
- M2 抽样 50 个 envelope 检查通过
- `overall_ok=true` 表示整包 QA 通过

### 4.3 CS 向客户解释模板

| 客户问题 | 标准解释 |
|----------|----------|
| "为什么 M2 显示 skipped？" | "M2 抽样 QA 在本版本中未执行，不影响 M1 清单校验结论。M1 已通过全量检查。" |
| "抽样 50 个能代表全部吗？" | "按统计学分层抽样，置信区间 95%，误差范围 ±5%。如需全检可申请定制 QA 流程。" |
| "seed 42 是什么意思？" | "抽样算法的随机种子，用于结果重现。相同 seed 下重跑会得到完全相同的抽样集合。" |

---

## 5. M2 P0 / P1 / P2 严重度说明

M2 失败同样使用 `severity` 字段，语义与 M1 一致：

| 严重度 | 阻断性 | 典型场景 | 处理建议 |
|--------|--------|----------|----------|
| **P0** | 阻断 Done / Chargeable | `M2-ENVELOPE-EXIST`（envelope 文件缺失）、`M2-SCHEMA`（envelope 结构损坏）、`M2-SEED-REPRO`（结果不可重现） | 立即排障，重跑 pipeline |
| **P1** | 不阻断，但需记录 | `M2-CONTENT-HINT`（内容质量警告）、`M2-METADATA-MISMATCH`（metadata 不一致但不影响可用性） | 记入报告，客户沟通 |
| **P2** | 仅内部记录 | `M2-PERFORMANCE-WARN`（检查耗时过长）、`M2-DEPRECATED-FIELD`（使用 deprecated 字段） | 技术债跟踪 |

### 5.1 M2 专属 check_id 列表

| check_id | 严重度 | 说明 |
|----------|--------|------|
| `M2-ENVELOPE-EXIST` | P0 | manifest 标记的 envelope 在 deliverables 目录不存在 |
| `M2-SCHEMA` | P0 | envelope JSON 不符合 schema |
| `M2-CONTENT-INTEGRITY` | P0 | envelope 内容 SHA 与 manifest 不一致 |
| `M2-SEED-REPRO` | P0 | 相同 seed 重跑得到不同抽样集合（算法非确定性） |
| `M2-STRATA-IMBALANCE` | P1 | 某层样本量低于统计要求（n<30） |
| `M2-COVERAGE-HINT` | P1 | 质量分数分布异常（如 90% 集中在低端） |
| `M2-PERFORMANCE-WARN` | P2 | 单个 envelope 检查耗时 >5s |

---

## 6. 分层抽样配置说明

### 6.1 何时使用分层抽样

当 envelope 群体存在**明显子群体**且各群体质量可能差异较大时：

| 分层字段 | 适用场景 | 示例 |
|----------|----------|------|
| `extension` | 多格式混合 | PDF vs DOCX 清洗质量可能不同 |
| `quality_tier` | 预分层 | intake 时已标记高质量/低质量 |
| `sku` | 多 SKU 混跑 | BASIC 与 ENRICH 可能分属不同 pipeline |

### 6.2 分层抽样公式

```
总体 N = Σ N_h（各层大小）
样本 n = N × sample_rate

按比例分配：n_h = n × (N_h / N)

最小样本约束：若 n_h < 30，提升为 30 或整层全检（N_h < 30 时）
```

### 6.3 CLI 示例：多维度分层

```powershell
python .\04_Workflows\_wave8_m2_rerun.py `
  --job-id w6-2024-001-mixed `
  --sample-rate 0.1 `
  --stratify-by extension,quality_tier `
  --seed 20240115 `
  --pretty
```

输出 `strata_distribution` 示例：

```json
{
  "strata_distribution": {
    "pdf:high": { "population": 300, "sampled": 30 },
    "pdf:low": { "population": 200, "sampled": 30 },
    "docx:high": { "population": 400, "sampled": 40 },
    "docx:low": { "population": 100, "sampled": 30, "note": "n<30 enforced" }
  }
}
```

---

## 7. 常见故障排查

### 7.1 envelope 缺失（`M2-ENVELOPE-EXIST`）

**现象**：`M2-ENVELOPE-EXIST` P0 失败，message 形如：

```json
{
  "layer": "M2",
  "check_id": "M2-ENVELOPE-EXIST",
  "severity": "P0",
  "file_id": "doc_001",
  "content_sha256": "abc123...",
  "stored_logical_path": "w6://delivery/w6-001/deliverables/envelopes/doc_001.json",
  "message": "Envelope file not found at expected path",
  "remediation_hint": "check_artifact_storage"
}
```

**排查步骤**：

1. 确认物理路径：`{delivery_root}/{job_id}/deliverables/envelopes/{file_id}.json` 是否存在
2. 检查 manifest 与 deliverables 版本是否一致（可能为旧 manifest 指向新 delivery）
3. 确认 artifact storage 未发生部分删除或迁移
4. 如使用逻辑路径，确认 `gov_paths` 解析正确

**CLI 验证**：

```powershell
# 列出该 job 实际存在的 envelope 文件
python .\04_Workflows\_wave8_m2_rerun.py `
  --job-id w6-2024-001 `
  --dry-run `
  --list-existing
```

### 7.2 seed 重现失败（`M2-SEED-REPRO`）

**现象**：相同 `--seed` 重跑 M2，抽样集合不一致，触发 `M2-SEED-REPRO` P0。

**排查步骤**：

1. 确认 manifest 内容**完全一致**（无新增/删除行）
2. 确认 `--stratify-by` 参数完全一致
3. 确认 Python 版本与 `gov_core_system` 依赖版本一致（`numpy.random` 版本差异）
4. 检查是否有**并发修改**（另一进程同时改动 deliverables）

**修复**：

```powershell
# 强制固定种子算法版本（确定论模式）
python .\04_Workflows\_wave8_m2_rerun.py `
  --job-id w6-2024-001 `
  --seed 42 `
  --deterministic-mode `
  --pretty
```

### 7.3 分层抽样说明不清

**现象**：`strata_distribution` 显示某层 `sampled` 数与预期比例不符。

**原因说明**：

| 现象 | 解释 |
|------|------|
| 某层 `sampled = population` | 该层总数 < 最小样本约束（30），执行整层全检 |
| 实际抽样率 > 设定值 | 因最小样本约束提升，总体抽样率会略高于设定值 |
| `stratified_by` 字段缺失 | manifest 中部分行缺少分层字段，被归入 `__missing__` 层 |

**CLI 查看详细分层报告**：

```powershell
python .\04_Workflows\_wave8_m2_rerun.py `
  --job-id w6-2024-001 `
  --stratify-by extension `
  --detailed-strata-report `
  --pretty
```

### 7.4 M2 结果与 M1 冲突

**现象**：M1 报告 `ok=true`，但 M2 发现内容损坏。

**解释**：
- M1 只检查 manifest 表层，不打开 envelope
- M2 发现的是**内容级**损坏（如 JSON parse 失败、SHA 不匹配）
- 这是 M2 存在的价值——发现 M1 无法捕获的深度缺陷

**处理**：

```powershell
# 仅重算 M2（不触发完整 pipeline）
python .\04_Workflows\_wave8_m2_rerun.py `
  --job-id w6-2024-001 `
  --m2-only `
  --force
```

---

## 8. 与 report.md / CS 解释对照

### 8.1 Markdown 报告中的 M2 段落

客户版 `report.md` §4（qa_m2）呈现：

```markdown
## 4. 抽样校验（M2）

- **执行状态**：已完成
- **抽样方法**：分层抽样（按文件类型）
- **样本量**：50 / 1000（5%）
- **随机种子**：42（可重现）
- **结果**：✅ 通过

### 分层分布

| 类型 | 母体数量 | 抽样数量 | 状态 |
|------|----------|----------|------|
| PDF | 600 | 30 | ✅ |
| DOCX | 400 | 20 | ✅ |

*注：抽样 QA 已按统计学方法执行，置信水平 95%，误差范围 ±5%。*
```

### 8.2 红灯/黄灯/绿灯判定卡

| 信号 | M2 条件 | CS 话术 |
|------|---------|---------|
| 🟢 绿灯 | `status=completed` + `ok=true` + 无 P0 | "抽样 QA 通过，整包质量符合交付标准。" |
| 🟡 黄灯 | `status=completed` + `ok=true` + 存在 P1 | "抽样 QA 通过，发现轻微质量提示，建议内部关注但不影响交付。" |
| 🔴 红灯 | `status=failed` 或 `ok=false` | "抽样 QA 发现严重问题，建议暂停交付并联系工程排障。" |
| ⚪ 灰灯 | `status=skipped` | "本版本未执行抽样 QA，以清单校验（M1）结论为准。" |

### 8.3 升级路径

| 场景 | 操作 |
|------|------|
| M2 P0 失败需紧急处理 | 联系工程团队，提供 `job_id` 与 `failures[]` 完整 JSON |
| 客户要求全检代替抽样 | 记录需求，转交 PM 评估定制 QA 流程 |
| 对抽样结果有疑问 | 使用相同 `--seed` 重跑验证，保存两份结果对比 |

---

## 9. 延伸阅读

| 文档 | 内容 |
|------|------|
| `WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md` | Wave 7 CLI 基础、M1 解读、artifact 路径 |
| `WAVE8_REPORT_MARKDOWN_OVERVIEW_v0.1.md` | Markdown 报告渲染总览 |
| `WAVE8_REPORT_MD_RUNBOOK_v0.1.md` | CS 阅读 Markdown 报告指南 |
| `WAVE6_IMPL_QA_M1_TICKET_v0.1.md` | M1 实现规格（对比参考） |
| `WAVE6_DATA_CLEANING_R3_APPENDICES_v0.1.md` | R3 §G.6–G.7 QA 严重度定义 |

---

*Wave 8 M2 运维手册 · `04_Workflows/WAVE8_M2_RUNBOOK_v0.1.md` · v0.1*
