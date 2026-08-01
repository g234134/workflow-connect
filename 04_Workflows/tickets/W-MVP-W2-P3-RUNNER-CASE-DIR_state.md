# TICKET STATE · W-MVP-W2-P3-RUNNER-CASE-DIR · 参数化清洗 runner（--case-dir）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 2 · P3 — 清洗 runner 泛化（**不改**清洗算法、**不接** prod dispatch）

---

## FRAME

- Goal: 清洗 runner 可针对任一 `case_dir` 运行，从 `intake.json` 读取 raw 路径与解析参数，产物写回标准 `cleaned/` + `reports/` 结构。
- Scope:
  - `--case-dir` CLI（默认 `cases/demo_phase`）
  - 从 `intake.json` 解析 `data_file` / `source.source_file`、`encoding`、`delimiter`、`file_format`
  - 清洗前调用 P2 `check_case_eligibility`（可 `--skip-eligibility`；`review_needed` 可用 `--force` 继续）
  - 输出：`cleaned/<stem>_cleaned.csv`、`reports/cleaning_stats.json`、`report.json`、`report.md`
  - `case_intake_loader.py` + 最小 unittest
- NonScope:
  - 不重写 Phase 清洗算法（列规则仍内嵌于 `clean_phase_demo.py`）
  - 不接入 W4-T1/T2 prod 链、dispatch/executor
  - 不引入新依赖；xlsx 解析留给 V2
  - 不更新 C2-D1/C2-P2 历史文档路径（Scribe）
- AllowedPaths:
  - `notebooks/csv_cleaning/clean_phase_demo.py`
  - `notebooks/csv_cleaning/case_intake_loader.py`（新建）
  - `tests/test_case_runner.py`（新建）
  - `04_Workflows/tickets/W-MVP-W2-P3-RUNNER-CASE-DIR_state.md`
- BlockedPaths:
  - `core/*`、`skills/*`、`dispatch_executor.py`、`scripts/run_dispatch_*`
  - `AGENTS.md`、`.cursor/rules/*`
- Dependencies:
  - P1 `W-MVP-W2-P1-CASE-BOOTSTRAP_state.md`（cases 结构 + intake）
  - P2 `case_eligibility.py` + `scripts/check_case_eligibility.py`
- AcceptanceCriteria:
  - `demo_phase` 上 `--case-dir` 流程跑通，产物齐全
  - 输入/输出路径由 `case_dir` + `intake.json` 决定，无硬编码 demo 路径
  - eligibility gate 可调用且可跳过
  - B_REPORT 记录 CLI、intake 契约、验证命令

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 对照 AC 验收 demo_phase 跑通与 gate 行为；Orchestrator 开 P4 delivery 票
- last_updated: 2026-06-08 · implementer
- status_by_role:
  - orchestrator: pending
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

### Step 0 — Module Reuse Check

**current_path_assumptions:**

- `clean_phase_demo.py`（改前）：`REPO_ROOT = parents[2]`，硬编码 `CASE_DIR = REPO_ROOT / "cases" / "demo_phase"`，以及 `INPUT_PATH`、`OUTPUT_PATH`、`REPORT_*` 常量；列名 `COLUMNS` / `PERCENT_COLUMNS` / `JOB_ID` 亦模块级写死。
- `run_tabular_cleaning_plan.py`：仅 runbook 步骤清单；`--case demo_phase` 时在 JSON 中附加 `demo_anchor` 路径提示，**不执行清洗**。

**intake_fields_needed_for_runner:**

- 路径：`data_file`（legacy）或 `source.source_file`（P1 README 形态）
- 解析：`file_format`（csv/tsv）、`encoding`、`delimiter`（可来自 `source.*` 或顶层）
- 标识：`case_id`（用于 `job_id` 默认 `case-{case_id}`）
- 可选 schema hint：`id_column` / `primary_key`、`required_columns`、`nullable_columns`、`date_columns`、`percent_columns`（本票 loader 已读取；Phase 清洗算法仍用内嵌列，未改规则引擎）
- P2 共用：`scale`、`provenance`、`sensitivity`、`structure`（eligibility gate 消费，runner 不重复解析）

**eligibility_call_contract:**

- 函数：`check_case_eligibility(case_dir: Path) -> dict`
- 返回键：`ok`、`eligibility`（`accepted` | `rejected` | `review_needed`）、`reason_code`、`human_readable`、`exit_code`（0/1/2）、`dimensions`、`review_reasons`、`reject_reasons`
- 技术错误（如无目录）：`eligibility=rejected`，`ok=False`
- 缺/坏 intake：`eligibility=review_needed`，`ok=False`
- 不抛异常；调用方读 `exit_code` 决定进程退出码

### CLI 形态（设计取捨）

**选择：扩展既有 `clean_phase_demo.py`**，不新建 `scripts/run_case_cleaning.py`。

理由：

- P1/P2 文档与 runbook 已指向该脚本为 demo 清洗入口；零教程断裂。
- P2 已有独立薄 CLI `scripts/check_case_eligibility.py`；清洗与 gate 分离符合职责。
- 新建第二入口会增加 Scribe 双轨维护成本。

**命令与参数：**

| 参数 | 默认 | 说明 |
|------|------|------|
| `--case-dir` | `cases/demo_phase`（须存在） | case 根目录 |
| `--skip-eligibility` | off | 跳过 P2 gate（dev/demo） |
| `--force` | off | `review_needed` 时仍继续（内部测试） |

**示例：**

```bash
# 默认 demo（等同显式指定 demo_phase，须带 skip 或 force 因 demo 行数 <100 → review_needed）
python notebooks/csv_cleaning/clean_phase_demo.py --skip-eligibility

python notebooks/csv_cleaning/clean_phase_demo.py --case-dir cases/demo_phase --skip-eligibility

python notebooks/csv_cleaning/clean_phase_demo.py --case-dir cases/demo_phase --force
```

**退出码：**

| 码 | 含义 |
|----|------|
| 0 | 清洗成功 |
| 1 | eligibility `rejected` 或 intake/路径技术错误 |
| 2 | eligibility `review_needed` 且未 `--force` |

### intake 读取契约（runner）

**必填（缺则 `gate=intake` 错误退出）：**

- `data_file` 或 `source.source_file` — 相对 `case_dir` 的 raw 路径
- 对应 raw 文件须存在
- `file_format` 须为 `csv`/`tsv`/`txt`（或可由后缀推断）；`xlsx` 明确拒绝

**有默认（缺省可用）：**

- `encoding` → `utf-8-sig`
- `delimiter` → `,`（csv）或 `\t`（tsv）

**可选（loader 暴露，算法本票未改）：**

- `schema.id_column` / `primary_key`
- `schema.required_columns`、`nullable_columns`、`date_columns`、`percent_columns`

**输出命名（无旧→新变更）：**

- `cleaned/{input_stem}_cleaned.csv`（demo：`Phase_cleaned.csv`）
- `reports/cleaning_stats.json`
- `reports/report.json`
- `reports/report.md`
- `job_id`：intake `job_id` 或 `case-{case_id}`（demo 由 `C2-D1-DEMO-PHASE` 改为 `case-demo_phase`）

### eligibility 集成

1. 默认（无 `--skip-eligibility`）：调用 `check_case_eligibility(case_dir)`
2. `rejected` → JSON 错误 + exit 1（业务拒绝，含 `reject_reasons`）
3. `review_needed` → 无 `--force` 时 JSON 提示 + exit 2；有 `--force` 时打印 warning JSON 后继续
4. `accepted` → 直接进入 intake 加载与清洗
5. `--skip-eligibility` → 完全跳过 gate（不推荐客户案）

`demo_phase` 因 `rows<100` 恒为 `review_needed`；教程跑通须 `--skip-eligibility` 或 `--force`。

### changed_files

- `notebooks/csv_cleaning/case_intake_loader.py`（新建）
- `notebooks/csv_cleaning/clean_phase_demo.py`（CLI + intake 路径 + eligibility 接点）
- `tests/test_case_runner.py`（新建）
- `04_Workflows/tickets/W-MVP-W2-P3-RUNNER-CASE-DIR_state.md`（本档）

### artifacts

- 无（demo_phase 报告由验证命令重写）

### verification

```bash
python notebooks/csv_cleaning/clean_phase_demo.py --case-dir cases/demo_phase --skip-eligibility
# {"ok": true, "case_id": "demo_phase", "input_rows": 7, "output_rows": 5, ...}

python -m unittest tests.test_case_runner -v
# TestCaseIntakeLoader + TestCaseRunnerCLI OK
```

### behavior_notes

- 清洗核心（Phase 列归一、去重、百分号解析）未改；仅路径/编码/delimiter/eligibility 参数化。
- intake 同时支持 P1 flat（`data_file`）与 nested（`source.source_file`）两种形态，与 P2 `_resolve_data_file` 对齐。
- 无 `--case-dir` 且 `cases/demo_phase` 不存在时明确报错，不静默失败。

### deferred_items

- V2：xlsx 加载、`schema.*` 驱动通用列清洗（非 Phase 专用）
- P4：读取 `reports/*` + eligibility 结果打包 `delivery_signoff.md`
- Scribe：更新 `docs/C2-D1_*`、`docs/C2-P2_RUNBOOK.md` CLI 示例与 `job_id` 变更说明

### integration_notes_for_P4

P4 delivery 可依赖：

- `case_dir/intake.json` — 案号、客户、SKU hint
- `case_dir/reports/report.json` — C2-P1 §3.1 `product_metrics` / `summary`
- `case_dir/reports/report.md` — 人读摘要
- `case_dir/reports/cleaning_stats.json` — before/after 剖析
- `case_dir/cleaned/*.csv` — 交付表
- eligibility：打包前可再跑 `scripts/check_case_eligibility.py --case-dir <case> --json`，将 `eligibility` + `dimensions` 写入 manifest 或 `delivery_signoff.md` 签核段

---

## C_REPORT

<!-- Reviewer 填 -->

---

## D_REPORT

<!-- Scribe 填 -->
