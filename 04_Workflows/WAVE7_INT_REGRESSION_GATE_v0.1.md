# Wave 7 – INT-REGRESSION-GATE（v0.1）

> **票号**：`INT-REGRESSION-GATE`  
> **性质**：implementation / governance ticket  
> **范围**：Wave 6/7 集成回归门禁定义 + 聚合入口  
> **依据**：现有 Wave 6/7 模块与装配层 unittest  
> **不做**：替代单元测试、全库跑测、M2/财务/bridge E2E、真实 Groq 或 Postgres

---

## 0. 背景

模块层单测通过不能防止装配层退化。本票定义 Wave 6/7 **集成回归门禁**：任何改动 envelope / manifest / QA / orchestrator / runner 时必须跑的一组测试与通过标准。

**聚合入口**（实现）：

| 项 | 路径 |
|----|------|
| CLI | `04_Workflows/_wave7_regression_gate.py` |
| 核心逻辑 | 暗部 `core/wave7_regression_gate.py` |
| 地图 runner | `Master_Map.json` → `runners.wave7_regression_gate` |

交叉引用：Gov Core smoke 索引见 `04_Workflows/Runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md`（不复制全文）。

---

## 1. 目标

- Tier-A：最小但充分的必跑集合，守护 Wave 6/7 装配不变量。
- Tier-B：更重集成场景（清单已列，模块待后续票增补）。
- 结构化回传：`{ok, suite, failed_tests[], ...}`；首个失败时 stderr 打印 `stage` / `job_id` / `first_qa_check_id`。

---

## 2. 推荐命令

### 2.1 本地开发者（最小门禁 · Tier-A）

从战车主舱或任意已激活 `gov_core_system` venv 的 shell：

```powershell
python .\04_Workflows\_wave7_regression_gate.py --tier A
```

等价（仅列 Tier-A 模块，不经过聚合器诊断行）：

```powershell
cd 01_Environments\python_venvs\gov_core_system
python -m unittest tests.test_envelope_v2 tests.test_wave6_manifest_writer tests.test_wave6_qa_manifest_m1 tests.test_wave6_e2e_smoke tests.test_wave6_intake_gate tests.test_wave7_runner_env_bootstrap tests.test_wave7_runner_entry_job_input tests.test_wave7_artifact_storage tests.test_wave7_orch_pipeline_wire tests.test_wave7_report_summary_producer tests.test_wave7_orch_job_lifecycle
```

### 2.2 Tier-B / ALL

```powershell
python .\04_Workflows\_wave7_regression_gate.py --tier B
python .\04_Workflows\_wave7_regression_gate.py --tier ALL
```

- `--tier B`：当前 **无已注册模块**，返回 `ok: true`、`tier_b_pending: true`（见 §6）。
- `--tier ALL`：Tier-A 全量（与 B 为空时等价于 A）。

### 2.3 选项

| 选项 | 说明 |
|------|------|
| `--tier A` \| `B` \| `ALL` | 选择门禁层级 |
| `-v` / `-vv` | 提高 unittest 控制台详细度 |
| `--pretty` | JSON 结果缩进打印 |

### 2.4 CI 接入建议

1. Job 使用 `gov_core_system` venv（与 `Master_Map.cabins.gov_core_system` 一致）。
2. 步骤：`python 04_Workflows/_wave7_regression_gate.py --tier A`（路径相对 CI checkout 根）。
3. 解析 stdout 末行 JSON：`ok` 必须为 `true`；失败时检查 stderr 的 `INT-REGRESSION-GATE first failure:` 行。
4. 退出码：`0` = 通过，`1` = 有用例失败，`2` = 门禁配置/加载错误。

---

## 3. 结构化输出格式

### 3.1 成功（stdout JSON）

```json
{
  "ok": true,
  "suite": "A",
  "tier": "A",
  "modules": ["tests.test_envelope_v2", "..."],
  "passed": 95,
  "failed": 0,
  "errors": 0,
  "tests_run": 95,
  "failed_tests": []
}
```

### 3.2 失败（stdout JSON + stderr 诊断）

```json
{
  "ok": false,
  "suite": "A",
  "failed_tests": [
    {
      "test_id": "tests.test_wave7_orch_pipeline_wire.TestWave7OrchPipelineWire.test_envelope_stage_failure_returns_stage_and_error_code",
      "kind": "failure",
      "message": "AssertionError: ...",
      "stage": "envelope",
      "job_id": "w7-pipe-bad-sku",
      "first_qa_check_id": null
    }
  ]
}
```

stderr（首个失败）：

```text
INT-REGRESSION-GATE first failure: test=... stage=envelope job_id=w7-pipe-bad-sku first_qa_check_id=M1-COUNT
```

字段从失败 traceback / assertion 文本中 **尽力解析**（`stage`、`job_id`、`check_id` 键名模式）。

---

## 4. Wave 8 测试纳管策略

Wave 8 新增 M2 抽样 QA 与 REPORT-MD 渲染模块。纳入策略如下：

| 模块 | 归属 | 理由 |
|------|------|------|
| `tests.test_wave8_m2_sampling_design` | **Tier-A** | M2 SamplingPlan 契约核心（样本量计算、确定性 seed、分层覆盖） |
| `tests.test_wave8_m2_execution_engine` | **Tier-A** | M2 `run_m2_checks` 行为定义（P0/P1 分级、skip 逻辑） |
| `tests.test_wave8_m2_report_integration` | **Tier-A** | M1+M2 合并后 `qa_status` / `overall_ok` 语义 |
| `tests.test_wave8_m2_orch_integration` | **Tier-B** | M2 在生命周期中的可选启用策略（`enable_m2` / `strict_m2`） |
| `tests.test_wave8_report_md_renderer` | **Tier-B** | Markdown 渲染器（双语输出、audience 切换、费用占位） |
| `tests.test_wave8_report_md_orch_integration` | **Tier-B** | `render_report_md` 标志在 orchestrator 中的集成 |

> **原则**：Tier-A 保持「小而精」，仅纳入 M2 核心契约与 M1+M2 合并语义；涉及 orchestrator 复杂组合与 Markdown 渲染的测试归入 Tier-B，避免默认门禁时间膨胀。

---

## 5. Tier-A 测试清单（必跑）

| 模块 | 守护不变量（摘要） |
|------|-------------------|
| `tests.test_envelope_v2` | ENVELOPE-V2：BASIC/ENRICH schema、`present` 规则、逻辑路径、禁止 billable / 原始路径泄漏 |
| `tests.test_wave6_manifest_writer` | MANIFEST-V2：去重、`accepted_units`、`billing_units` U/L、R-GROQ 计费排除 |
| `tests.test_wave6_qa_manifest_m1` | QA-M1：M1-KEYS / SHA / DEDUP / SKU-ENRICH / COUNT / OK-ONLY；不读 envelope/FS |
| `tests.test_wave6_e2e_smoke` | E2E：BASIC smoke、失败行聚合、`test_wave6_e2e_enrich_and_duplicates`（ENRICH/重复/tamper） |
| `tests.test_wave6_intake_gate` | INTAKE-GATE：accept/defer/reject、SKU 解析、禁止绝对路径 hint |
| `tests.test_wave7_runner_env_bootstrap` | env bootstrap：逻辑路径段、缺 map/schema 时 `ok: false` |
| `tests.test_wave7_runner_entry_job_input` | runner entry：`job_record`/`raw_files`、empty_batch/unknown_sku/intake mismatch 稳定 `error_code` |
| `tests.test_wave7_artifact_storage` | 落盘布局、幂等写入、I/O 失败回收、返回无绝对路径 |
| `tests.test_wave7_orch_pipeline_wire` | pipeline wire：ENRICH `present` 单 seam、与 E2E 等价、stage/error_code |
| `tests.test_wave7_report_summary_producer` | report：`accepted_units`/`billing_units`/`qa_status` 与 manifest + M1 一致 |
| `tests.test_wave7_orch_job_lifecycle` | lifecycle：happy/fail、checkpoint/retry、`completed_with_failures`、QA P0 |
| `tests.test_wave8_m2_sampling_design` | M2-SAMPLING：样本量边界（n<20 全采）、确定性 seed、分层覆盖（每扩展名至少 1 条） |
| `tests.test_wave8_m2_execution_engine` | M2-EXEC：P0 缺 envelope、P1 quality_score 漂移、skip 条件（n=0/M1 失败） |
| `tests.test_wave8_m2_report_integration` | M2-REPORT：`merge_m1_m2_results` 后 `overall_ok`、`qa_status` 三态映射、M2 跳过占位 |

### 4.1 Tier-A 逐条测试 → 不变量

#### `tests.test_envelope_v2`

| 测试方法 | 不变量 |
|----------|--------|
| `test_basic_valid_no_enrichment_key` | BASIC 行无 `enrichment` 键 |
| `test_enrich_valid_present_true` | ENRICH OK 行须 `present: true` |
| `test_enrich_present_false_allowed_for_non_ok_row` | 非 OK 行允许 `present: false` |
| `test_enrich_ok_with_present_false_rejected` | OK+ENRICH 拒绝 `present: false` |
| `test_path_leak_rejected` | 拒绝盘符/URL 路径泄漏 |
| `test_billable_fields_rejected` | envelope 禁止 billable 字段 |
| `test_delivery_raw_path_fields_rejected` | 禁止 delivery/raw 绝对路径字段 |
| `test_write_envelopes_returns_dicts` | writer 返回稳定 dict |
| `test_schema_file_exists_and_declares_basic_enrich_branches` | schema 声明 BASIC/ENRICH 分支 |

#### `tests.test_wave6_manifest_writer`

| 测试方法 | 不变量 |
|----------|--------|
| `test_basic_pure_job_counts_accepted_and_billable_u` | BASIC 纯 job U 计数 |
| `test_basic_groq_violation_excludes_row_from_billable_u` | R-GROQ 违规不计费 U |
| `test_duplicate_sha_keeps_best_candidate_and_dedupes_output` | SHA 去重保留最优 |
| `test_enrich_normal_counts_u_and_l` | ENRICH U+L 计费 |
| `test_enrich_missing_enrichment_block_is_not_billable_u` | 缺 enrichment 不计 U |

#### `tests.test_wave6_qa_manifest_m1`

| 测试方法 | 不变量 |
|----------|--------|
| `test_m1_keys_pass_minimal_row` | M1-KEYS 最小行通过 |
| `test_m1_keys_fail_missing_required_key` | 缺键失败 |
| `test_m1_sha_pass_and_fail` | M1-SHA |
| `test_m1_ok_only_counts_only_exact_ok_rows` | M1-OK-ONLY |
| `test_m1_sku_basic_rejects_enrichment_key` | BASIC 禁 enrichment 键 |
| `test_m1_sku_enrich_requires_has_enrichment_true` | M1-SKU-ENRICH |
| `test_m1_dedup_flags_duplicate_sha_after_first_row` | M1-DEDUP |
| `test_m1_count_detects_aggregate_mismatch_without_failed_rows` | M1-COUNT |
| `test_manifest_integrity_counts_reconcile_distinct_rows` | manifest 完整性 |
| `test_output_never_emits_overall_ok` | 不输出 overall_ok |
| `test_billing_units_are_ignored` | QA 不读 billing_units 做裁决 |
| `test_m1_never_reads_envelope_or_filesystem` | M1 仅 manifest 真相 |

#### `tests.test_wave6_e2e_smoke`

| 测试方法 | 不变量 |
|----------|--------|
| `test_basic_envelope_manifest_qa_smoke_passes` | BASIC 全链路 smoke |
| `test_basic_smoke_failure_emits_row_and_aggregate_failures` | 失败行与聚合 failures |
| `test_wave6_e2e_enrich_and_duplicates` | ENRICH/重复/损坏 tamper E2E |

#### `tests.test_wave6_intake_gate`

| 测试方法 | 不变量 |
|----------|--------|
| `test_accept_*` / `test_defer_*` / `test_reject_*` | INTAKE 三分流与 SKU/路径红线 |
| `test_suggested_pipeline_not_used_as_billing_sku_on_accept` | accept 不用 suggested_pipeline 计费 |

#### `tests.test_wave7_runner_env_bootstrap`

| 测试方法 | 不变量 |
|----------|--------|
| `test_bootstrap_check_success` | 健康 bootstrap |
| `test_resolve_paths_logical_segments` | 逻辑路径段 |
| `test_missing_*` / `test_invalid_sub_type_ok_false` | 缺配置稳定失败 |
| `test_check_fails_when_schema_file_missing` | schema 可读性检查 |

#### `tests.test_wave7_runner_entry_job_input`

| 测试方法 | 不变量 |
|----------|--------|
| `test_logical_path_mapping` / `test_map_cleaned_record` | 逻辑路径映射 |
| `test_cli_cleaned_dir_scan_basic` | CLI 扫描构造 job |
| `test_empty_batch_fails` / `test_unknown_sku_fails` | 稳定 error_code |
| `test_intake_*` / `test_sku_intake_mismatch_rejected` | intake 与 job 构造 |

#### `tests.test_wave7_artifact_storage`

| 测试方法 | 不变量 |
|----------|--------|
| `test_create_success` | 落盘布局与 w6 ref |
| `test_idempotent_rerun_same_inputs` | 幂等写入 |
| `test_io_error_recovery_failed_and_quarantine` | 失败回收 |
| `test_return_structure_has_no_absolute_path_leak` | 无绝对路径泄漏 |

#### `tests.test_wave7_orch_pipeline_wire`

| 测试方法 | 不变量 |
|----------|--------|
| `test_present_true_strips_present_key` / `test_present_false_drops_enrichment` | ENRICH present 单 seam |
| `test_basic_happy_path_matches_e2e_smoke` | 与 E2E smoke 等价 |
| `test_enrich_present_true_false_normalization_via_pipeline` | present 规范化 |
| `test_basic_duplicate_sha_behavior_matches_e2e` | 去重与 E2E 一致 |
| `test_qa_stub_bridge_m1_count_mismatch_surfaces_in_qa_not_stage_fail` | M1-COUNT 在 QA 层 |
| `test_envelope_stage_failure_*` / `test_manifest_stage_failure_*` | stage + error_code |
| `test_corrupted_manifest_qa_failures_match_e2e` | tamper 与 E2E QA 一致 |

#### `tests.test_wave7_report_summary_producer`

| 测试方法 | 不变量 |
|----------|--------|
| `test_basic_summary_matches_manifest_and_m1_count_passes` | summary 与 manifest/M1 |
| `test_enrich_e2e_fixture_summary_and_pipeline_report` | ENRICH E2E report |
| `test_m1_fail_maps_qa_status_fail` | qa_status 映射 |
| `test_basic_dedup_billing_units_locked` | 去重后 billing 锁定 |

#### `tests.test_wave7_orch_job_lifecycle`

| 测试方法 | 不变量 |
|----------|--------|
| `test_happy_path_intake_to_done` / `test_happy_path_direct_job_record` | 成功 DONE |
| `test_completed_with_failures_when_rejected_rows_and_m1_ok` | completed_with_failures |
| `test_qa_p0_failure_default_failed_not_retryable` | QA P0 → FAILED |
| `test_qa_p0_failure_blocked_policy` | blocked 策略 |
| `test_storage_io_retry_skips_envelope_recompute` | checkpoint + retry |

#### `tests.test_wave8_m2_sampling_design`

| 测试方法 | 不变量 |
|----------|--------|
| `test_n_zero` / `test_n_below_20_full_sample` | 样本量边界：N=0 返回 0；N<20 全采样 |
| `test_n_100_typical` | N=100 时样本量为 20（20% 或上限约束） |
| `test_deterministic_repeated_calls` | 相同输入产生相同 `SamplingPlan`（含 seed、row_indexes） |
| `test_n_gt_500_strata_at_least_one_per_extension` | 分层保证：每扩展名至少采 1 条（当 N>500 时） |
| `test_billing_version_affects_seed` | billing_table_version 参与 seed 派生，版本不同则 seed 不同 |

#### `tests.test_wave8_m2_execution_engine`

| 测试方法 | 不变量 |
|----------|--------|
| `test_basic_sample_all_pass` | 正常样本全部通过时 `ok: true`、`failed_checks: 0` |
| `test_missing_envelope_is_p0` | 缺失 envelope → P0 失败、`layer: M2`、`check_id: M2-SCHEMA-20` |
| `test_enrich_quality_mismatch_is_p1` | quality_score 漂移 → P1 失败、`check_id: M2-QUALITY` |
| `test_n_zero_skipped_no_io` | N=0 时跳过采样、无 IO、返回 `status: skipped`、`reason: no_sample` |
| `test_m1_failed_skipped_no_io` | M1 失败时 M2 跳过、无 IO、返回 `status: skipped`、`reason: m1_failed` |

#### `tests.test_wave8_m2_report_integration`

| 测试方法 | 不变量 |
|----------|--------|
| `test_without_m2_uses_skipped_sample_validation` | 无 M2 时 `sample_validation.status=skipped`、`overall_ok` 仅看 M1 |
| `test_m2_p1_merges_failures_and_sets_overall_ok_false` | M2 P1 失败合并入 `failures[]` 且 `overall_ok: false` |
| `test_m1_pass_m2_p1_pass_with_warnings` | M1 通过+M2 P1 → `qa_status: pass_with_warnings`、`chargeable_hint: false` |
| `test_m1_pass_m2_p0_fail` | M2 P0 → `qa_status: fail`、 severities 包含 P0 |
| `test_m1_fail_m2_skipped` | M1 失败时 M2 跳过、`qa_status: fail`、M1 失败保留在 failures |

---

## 6. Tier-B 清单（补充场景 · Wave 8 已注册）

| 模块 | 场景 | 目标不变量 |
|------|------|------------|
| `tests.test_wave8_m2_orch_integration` | M2 在生命周期中的可选启用 | `enable_m2=False` 时跳过 M2；`enable_m2=True` 时执行采样；`strict_m2` 决定异常时是否 FAILED |
| `tests.test_wave8_report_md_renderer` | Markdown 渲染器双语/audience 切换 | `audience=external` 隐藏 remediation；`audience=internal` 显示内部附录；费用占位符（未开票） |
| `tests.test_wave8_report_md_orch_integration` | `render_report_md` 标志在 orchestrator 中的集成 | `render_report_md=True` 生成实际 Markdown；`False` 保留 placeholder；失败隔离（strict_report_md） |
| *预留* | 同一 `job_id` 多次 `run_wave7_job` | artifact 幂等 + lifecycle 状态一致 |
| *预留* | 多 stage I/O 抖动组合 | retry 边界、不重复 envelope 计算 |
| *预留* | 千行 manifest 批次 | 内存/耗时上限（无 OOM） |

> Tier-B 跑测命令：`python .\04_Workflows\_wave7_regression_gate.py --tier B`

---

## 7. Done 条件（checklist）

### Tier-A（必跑）

- [x] `test_envelope_v2`、`test_wave6_manifest_writer`、`test_wave6_qa_manifest_m1`、`test_wave6_e2e_smoke`、`test_wave6_intake_gate` 纳入门禁。
- [x] Wave 7：`runner env`、`runner entry`、`artifact storage`、`pipeline wire`、`report producer`、`job lifecycle` 纳入门禁。
- [x] **Wave 8 Tier-A**：`test_wave8_m2_sampling_design`、`test_wave8_m2_execution_engine`、`test_wave8_m2_report_integration` 纳入门禁。
- [x] 聚合入口 `_wave7_regression_gate.py` + `core/wave7_regression_gate.py`。

### Tier-B

- [x] 清单文档化（§6）。
- [x] **Wave 8 Tier-B**：`test_wave8_m2_orch_integration`、`test_wave8_report_md_renderer`、`test_wave8_report_md_orch_integration` 已注册 `TIER_B_MODULES`。
- [ ] 预留场景：同一 job_id 多次运行、多 stage I/O 抖动、千行 manifest 批次（后续票）。

### 文档与诊断

- [x] 每条测试 → 不变量表（§5.1）。
- [x] Wave 8 新增不变量已入表：M2 SamplingPlan 契约、M2 `run_m2_checks` 行为、M1+M2 合并语义。
- [x] 失败打印 stage + job_id + 首个 QA check_id（尽力解析）。
- [x] GOV_CORE smoke runbook 交叉引用（§0）。

---

## 8. 推荐命令示例

### Tier-A（默认 · Wave 6/7/8 核心）

```powershell
python .\04_Workflows\_wave7_regression_gate.py --tier A
```

等价显式模块列表：

```powershell
cd 01_Environments\python_venvs\gov_core_system
python -m unittest `
  tests.test_envelope_v2 `
  tests.test_wave6_manifest_writer `
  tests.test_wave6_qa_manifest_m1 `
  tests.test_wave6_e2e_smoke `
  tests.test_wave6_intake_gate `
  tests.test_wave7_runner_env_bootstrap `
  tests.test_wave7_runner_entry_job_input `
  tests.test_wave7_artifact_storage `
  tests.test_wave7_orch_pipeline_wire `
  tests.test_wave7_report_summary_producer `
  tests.test_wave7_orch_job_lifecycle `
  tests.test_wave8_m2_sampling_design `
  tests.test_wave8_m2_execution_engine `
  tests.test_wave8_m2_report_integration
```

### Tier-B（Wave 8 orchestrator + Markdown 场景）

```powershell
python .\04_Workflows\_wave7_regression_gate.py --tier B
```

### ALL（完整回归）

```powershell
python .\04_Workflows\_wave7_regression_gate.py --tier ALL
```

---

## 9. 边界（明确不做）

- 不替代单元测试
- 不跑全库
- 不纳入 M2/财务/bridge E2E（Wave 8 M2 仅含 contract/execution/report 集成，不含真实抽样数据 E2E）
- 不要求真实 Groq 或 Postgres
- 不修改 Wave 6/7/8 业务规则或 QA 规则

---

*Wave 7/8 integration ticket · `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`*
