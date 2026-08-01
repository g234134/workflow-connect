# MVP Standard Trace Path

> **Repo SSOT**：`docs/TABULAR_MVP_SSOT.md` — 產品主線 landing doc；本檔為 L1 trace 對照 spec  
> **票号**：W1-T2-mvp-trace-path · Wave 1（治理 + 可观测 + 测试底座）  
> **性质**：**最小标准样本** · 非完整 trace 规格 · **非** prod SLA  
> **权威 E2E**：`docs/MVP_CASE_E2E_DoD_v0.1.md` · **叙事走查**：`docs/MVP_DEMO_WALKTHROUGH_v0.1.md`  
> **日期**：2026-06-10

---

## 1. 目的

为当前 **MVP 主链**（intake → gate → cleaning → bundle → E2E）定义一条可重跑、可对照的 **最小标准 trace 参考路径**：

- 指定 **1–2 条代表性样本**（`demo_phase` / `sampleco`）。
- 列出这些案例在 **L1 业务可观测**（CLI JSON + case 目录产物）中预期出现的关键节点。
- 标明 **L2 基础设施 trace**（Langfuse / Monitoring Graph）与 MVP 链的关系：**adjacent / 未接线**。
- 提供 **rerun 指令**与 **最小回归**步骤，供后续改动时做对照回归。

**本文件不是**：Langfuse span 命名规范、Monitoring Graph 接線设计、或 ask H 线完整可观测手册。未列出的 trace 信号 **不等于禁止**。

---

## 2. 范围

### 2.1 In scope

| 项 | 说明 |
|----|------|
| 主链阶段 | P2 gate · P3 cleaning · P4 bundle · Wave 3 E2E driver |
| 标准案例 | `cases/demo_phase`（最小 demo）· `cases/sampleco/2026-0001`（近真实客户） |
| L1 trace | 每步 CLI 结构化输出键 + `cases/<case>/reports/*` 落盘文件 |
| 业务状态节点 | uploaded → validated → gate_decision → processing → delivered |
| 最小回归 | 1–2 组可重跑指令序列 + 结果检查方式 |

### 2.2 Out of scope

| 项 | 说明 |
|----|------|
| Langfuse span / `workflow_name` 预定义 | 留待未来 trace 接線票；本 spec 仅标 `[待确认]` |
| Monitoring Graph L0+ 参与 MVP 决策 | MVP CLI 不触发 monitoring 路由 |
| PG `task_runs` / ask soak | 见 `docs/observability.md` §4.2.1（旧 W1-T2 PG ingest 票） |
| prod pipeline · 多案批量 · CI workflow | 见 `docs/MVP_CASE_E2E_DoD_v0.1.md` §7 |
| 修改 gate 规则 / 清洗逻辑 / bundle 结构 | 本票只定义对照路径，不改业务代码 |

### 2.3 主链 entrypoints（repo 实际）

| 阶段 | 脚本 | 角色 |
|------|------|------|
| Intake（新案） | `scripts/new_cleaning_case.py` | 建 `case_dir` + `intake.json`；demo 走查通常跳过 |
| Gate（P2） | `scripts/check_case_eligibility.py` | eligibility 判定 |
| Cleaning（P3） | `notebooks/csv_cleaning/clean_phase_demo.py` | tabular 清洗 |
| Bundle（P4） | `scripts/build_case_delivery_bundle.py` | 交付包 + output_guard |
| E2E | `scripts/run_case_e2e_validation.py` | 一键 gate → clean → bundle |
| Lookup（可选） | `scripts/build_cases_index.py` · `scripts/lookup_case_history.py` | 只读索引，非 hard gate |
| Local UI（可选） | `app/local_ui.py` | subprocess 包装上述 CLI；**NOT PROD** |

**工作目录**：repo 根（与 `scripts/`、`cases/` 同级）· **Python**：3.10+

---

## 3. 案例表

### 3.1 标准样本 A · `demo_phase`（最小 demo）

| 项 | 值 |
|----|-----|
| 路径 | `cases/demo_phase/` |
| `client_ref` | `internal-demo` |
| `case_id` | `demo_phase` |
| 输入样本 | `raw/Phase.csv`（7 行 · Phase 表四列） |
| `intake.json` | `data_file`: `raw/Phase.csv` |
| 索引登记 | `cases/index.json` → `gate_status=review_needed` |
| 定位 | C2-D1 遗留锚点；最适合展示 gate 黄灯 + `--force` 清洗 |

### 3.2 标准样本 B · `sampleco/2026-0001`（近真实客户）

| 项 | 值 |
|----|-----|
| 路径 | `cases/sampleco/2026-0001/` |
| `client_ref` | `sampleco` |
| `case_id` | `2026-0001` |
| 输入样本 | `raw/sampleco_milestone_export.csv`（115 行 · 多 milestone / Sprint 模式） |
| `intake.json` | `data_file`: `raw/sampleco_milestone_export.csv` |
| 索引登记 | `cases/index.json` → `gate_status=accepted` |
| 定位 | gate 绿灯但 schema 歧义 + output_guard 黄灯对照案 |

### 3.3 案例对照摘要

| 信号 | `demo_phase` | `sampleco/2026-0001` |
|------|--------------|----------------------|
| Gate `eligibility` | `review_needed` | `accepted` |
| Gate exit code | `2` | `0` |
| Cleaning `--force` | **需要** | 不需要 |
| `input_rows` → `output_rows` | 7 → 5 | 115 → 8 |
| `output_guard.status` | `ok` | `warning` |
| E2E `overall_ok` | `true`（默认 `--force-review`） | `true` |

---

## 4. 状态节点

MVP 主链业务状态（与 ticket / case 生命周期对齐；非 Langfuse span）：

```text
uploaded
  └─ intake.json + raw/<data_file> 存在
       （P1 建案：scripts/new_cleaning_case.py；或沿用既有 case 目录）

validated
  └─ E2E steps.structure.ok = true
       （必备：intake.json、raw/）

gate_decision
  ├─ accepted       → exit 0  → 可直接清洗（sampleco）
  ├─ review_needed  → exit 2  → 人工 review 后须 --force 清洗（demo_phase）
  └─ rejected       → exit 1  → E2E 停止；不在本标准路径覆盖范围

processing
  └─ clean_phase_demo 执行；stdout JSON ok=true

delivered
  └─ build_case_delivery_bundle ok=true
       + reports/eligibility_result.json
       + reports/report.json · report.md
       + cleaned/*_cleaned.csv
       + delivery_signoff.md
```

**说明**

- `review_needed` 是 **gate 与 processing 之间的黄灯态**，不是终态；E2E 驱动默认 `--force-review` 仍可达 `delivered`（仅 demo/internal）。
- **真实客户案**应优先在 `accepted` 后再清洗；`review_needed` 路径仅作内部回归对照。

---

## 5. Trace 节点

### 5.1 分层定义

| 层 | 名称 | 来源 | MVP 主链今日 |
|----|------|------|--------------|
| **L1** | 业务 trace | CLI stdout JSON + case 目录 artifacts | **权威** · 本 spec 主体 |
| **L2** | 基础设施 trace | Langfuse · Monitoring Graph · gov-trace-v2 JSONL · PG `task_runs` | **adjacent / 未接线 `[待确认]`** |

L2 属于 **H 线 ask API** 可观测栈（见 `docs/observability.md` §2）。tabular MVP CLI **当前不写入** Langfuse / Monitoring Graph；未来接線应 **另开 trace 接線票**，不在本 spec 预定义 span name 或 `workflow_name`。

### 5.2 L1 trace 表 · `demo_phase`

| 步骤 | L1 trace 名称 | 触发命令 | 预期信号（stdout / 落盘） |
|------|---------------|----------|---------------------------|
| 0 · 索引刷新 | `cases_index.refresh` | `python scripts/build_cases_index.py` | `ok=true`；`cases_written≥2` |
| 1 · Gate | `mvp.gate` | `python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json` | `eligibility=review_needed`；`exit_code=2`；`reason_code=rows<100`；`dimensions.schema.notes` 含 `phase_like`, `phase_demo` |
| 2 · Cleaning | `mvp.cleaning` | `python notebooks/csv_cleaning/clean_phase_demo.py --case-dir cases/demo_phase --skip-eligibility --force` | `ok=true`；`input_rows=7`；`output_rows=5`；`summary.qa_status=pass_with_warnings` |
| 3 · Bundle | `mvp.bundle` | `python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json` | `ok=true`；`output_guard.status=ok` |
| 4 · E2E | `mvp.e2e` | `python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json` | `ok=true`；`steps.cleaning.forced=true`；`message=e2e validation passed` |
| 落盘 · eligibility | `artifact.eligibility_result` | （gate 或 bundle refresh） | `reports/eligibility_result.json` → `status=review_needed` |
| 落盘 · report | `artifact.report` | （cleaning） | `reports/report.json` → `accepted_rows=5`；`meta.job_id=case-demo_phase` |
| 落盘 · cleaned | `artifact.cleaned_csv` | （cleaning） | `cleaned/Phase_cleaned.csv` |

### 5.3 L1 trace 表 · `sampleco/2026-0001`（与 demo 的差异）

| 步骤 | L1 trace 名称 | 预期差异 |
|------|---------------|----------|
| Gate · `mvp.gate` | `eligibility=accepted`；exit `0`；`dimensions.schema.notes` 含 `multi_row_export`, `schema_ambiguous`；`warnings` 含 `phase_like_headers_but_multi_row_or_sprint_pattern` |
| Cleaning · `mvp.cleaning` | 无 `--force`；`input_rows=115`；`output_rows=8`；`duplicate_rows_removed=106` |
| Bundle · `mvp.bundle` | `output_guard.status=warning`（ratio ≈ 8/115） |
| E2E · `mvp.e2e` | `steps.cleaning.forced=false`；其余 `ok=true` |

### 5.4 L2 trace 表（adjacent · 未接线）

| 系统 | 预期在 MVP 主链 | 对照参考 |
|------|-----------------|----------|
| Langfuse traces | **不出现** `[待确认]` | `docs/observability.md` §2 · ask `POST /api/ask` |
| Monitoring Graph | **不出现** `[待确认]` | `AGENTS.md` Monitoring Graph 节 · L0 only |
| gov-trace-v2 JSONL | **不出现** `[待确认]` | `observability/trace_query.py` · 默认 `runtime/task_traces.jsonl` |
| PG `task_runs` | **不出现** `[待确认]` | `docs/observability.md` §4.2.1 · `_phase5_pg_ingest_soak.py` |

---

## 6. Rerun 指令

### 6.1 一键 E2E（推荐 · 最小回归主入口）

```bash
# 样本 A
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json

# 样本 B
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
```

期望：进程 exit `0`；stdout `overall_ok: True`；JSON `ok=true`。

### 6.2 逐步 rerun · `demo_phase`

```bash
python scripts/build_cases_index.py

python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json

python notebooks/csv_cleaning/clean_phase_demo.py \
  --case-dir cases/demo_phase --skip-eligibility --force

python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json
```

### 6.3 逐步 rerun · `sampleco/2026-0001`

```bash
python scripts/check_case_eligibility.py --case-dir cases/sampleco/2026-0001 --json

python notebooks/csv_cleaning/clean_phase_demo.py \
  --case-dir cases/sampleco/2026-0001 --skip-eligibility

python scripts/build_case_delivery_bundle.py --case-dir cases/sampleco/2026-0001 --json
```

### 6.4 可选 · Lookup 对照

```bash
python scripts/lookup_case_history.py --list-all
python scripts/lookup_case_history.py --client-ref sampleco
```

---

## 7. 最小回归

### 7.1 何时跑

- 改动 `scripts/check_case_eligibility.py`、`notebooks/csv_cleaning/*`、`scripts/build_case_delivery_bundle.py`、`scripts/run_case_e2e_validation.py` 之后。
- 改动 `cases/demo_phase` 或 `cases/sampleco/2026-0001` 夹具数据之后。
- Wave 1 可观测 / MVP 文档票收尾前的 smoke 对照。

### 7.2 回归序列 A（快速 · 约 2 分钟）

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
```

**通过条件**

| 检查项 | `demo_phase` | `sampleco` |
|--------|--------------|------------|
| 进程 exit code | `0` | `0` |
| JSON `ok` | `true` | `true` |
| `eligibility` | `review_needed` | `accepted` |
| `steps.cleaning.forced` | `true` | `false` |
| `artifacts.cleaned_csv` | 非空路径 | 非空路径 |

### 7.3 回归序列 B（逐步 · 用于定位失败步骤）

对失败案例，按 §6.2 / §6.3 逐步执行，逐步核对 §5.2 / §5.3 L1 表中的 **预期信号**。

### 7.4 结果检查方式（今日无 Langfuse UI 需求）

1. **终端**：summary 行 `overall_ok` / 各 step `ok`；JSON 键与 §5 表一致。
2. **落盘**：`cases/<case>/reports/eligibility_result.json`、`report.json` 字段与上次回归一致（允许 `generated_at` / `checked_at` 时间戳变化）。
3. **索引（可选）**：`python scripts/lookup_case_history.py --client-ref <ref>` → `gate_status` 与 §3 表一致。
4. **Local UI（可选）**：`python app/local_ui.py` → 浏览器触发 E2E，对照同样 JSON 信号。

**不检查**：Langfuse 项目、PG `task_runs`、Monitoring Graph 输出（L2 未接线）。

---

## 8. 注意事项

1. **最小标准样本**：仅覆盖 `demo_phase` 与 `sampleco/2026-0001`；其他客户案须另建对照或扩展本 spec。
2. **非完整规格**：未列出的 CLI 日志行、guard 细项、或未来 L2 span **不等于禁止**；回归以 §5 L1 表 **关键节点** 为准。
3. **L2 未接线**：若发现 Langfuse / JSONL 已有 MVP 相关 trace，标为 **漂移** 或 **接線进展**，应更新本 spec 或另开接線票；本 spec 不预定义 span 名。
4. **`review_needed` 语义**：demo 路径允许 `--force`；生产客户流应 gate `accepted` 后再清洗（见 `docs/MVP_CASE_E2E_DoD_v0.1.md` §4–§5）。
5. **票号区分**：`04_Workflows/tickets/W1-T2_state.md` 为 **Monitoring PG Ingest**（done）；本 spec 票为 **`W1-T2-mvp-trace-path`**，勿混淆。
6. **trace 配置 bug**：若 L1 信号与 §5 表系统性不符，在本 spec 或票 state 标 `[待确认]`，由业务或 trace 接線票处理，不在本票改 gate/清洗逻辑。

---

## 9. 相关文档

| 文档 | 用途 |
|------|------|
| `docs/MVP_CASE_E2E_DoD_v0.1.md` | E2E 验收权威 |
| `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` | 两案逐步叙事与信号表 |
| `cases/README.md` | case 目录约定 |
| `docs/observability.md` | H 线 trace / PG ingest（L2 对照） |
| `04_Workflows/tickets/W1-T2-mvp-trace-path_state.md` | 本 spec 施工票 state |

---

## 附录 A · `demo_phase` 步骤 → L1 trace 节点（一览）

```text
build_cases_index.py
  └─ cases_index.refresh          ok=true, cases_written≥2

check_case_eligibility.py --json
  └─ mvp.gate                     eligibility=review_needed, exit=2, reason=rows<100
  └─ artifact.eligibility_result  reports/eligibility_result.json

clean_phase_demo.py --force
  └─ mvp.cleaning                 ok=true, 7→5 rows, qa_status=pass_with_warnings
  └─ artifact.report              reports/report.json
  └─ artifact.cleaned_csv         cleaned/Phase_cleaned.csv

build_case_delivery_bundle.py --json
  └─ mvp.bundle                   ok=true, output_guard.status=ok

run_case_e2e_validation.py --json
  └─ mvp.e2e                      ok=true, cleaning.forced=true

[L2 Langfuse / Monitoring Graph / PG]   未出现 [待确认]
```
