# Cases — 低风险单表 CSV 清洗案落盘约定

> **SSOT**：本目录为 Wave 2 MVP 客户案档案根；P2 eligibility、P3 `--case-dir` runner、P4 delivery/signoff 均引用此处结构。  
> **产品边界**：`docs/PRODUCT_TABULAR_CLEANING.md` · **流程**：`docs/C2-P2_RUNBOOK.md` · **准入维度**：`04_Workflows/WAVE6_CLEAN_INTAKE_ELIGIBILITY_v0.1.md`

---

## 目录布局

### 模板（复制后改名）

```
cases/_TEMPLATE_case/
  intake.json              # 接案 intake 清单（Stage A SSOT）
  automation_state.json    # 自动化控制面 state（start/pause/stop；见 control-plane doc）
  delivery_signoff.md      # 交付签核占位（P4 填模板内容）
  raw/                     # 客户原始档（只读；清洗不覆盖）
  cleaned/                 # 清洗产物 CSV
  reports/                 # cleaning_stats.json · report.json · report.md
```

### 正式案件（推荐）

```
cases/<client_ref>/<case_id>/
  intake.json
  automation_state.json
  delivery_signoff.md
  raw/
  cleaned/
  reports/
```

| 段 | 命名规则 | 示例 |
|----|----------|------|
| `client_ref` | 小写 `[a-z0-9-]`，客户或项目简称 | `demo` · `acme-corp` |
| `case_id` | 小写 `[a-z0-9-]`，案号或批次 | `demo_phase` · `2026-q2-orders` |

**遗留 demo 锚点**：`cases/demo_phase/` 为 C2-D1 历史路径，内部结构已与 `_TEMPLATE_case` 对齐；P3 runner 以 `--case-dir cases/demo_phase` 为默认 demo 目标。

---

## 必备文件与子目录

| 路径 | 阶段 | 说明 |
|------|------|------|
| `intake.json` | A · Intake | 接案元数据；字段见 `_TEMPLATE_case/intake.json` 与下文 |
| `automation_state.json` | Control | start/pause/resume/stop 状态；见 `docs/tabular-cleaning-control-plane-v1.md` |
| `raw/<source_file>` | A | 原始 CSV/Excel（本 MVP 以 CSV 为主） |
| `cleaned/*.csv` | B · Cleaning | 清洗后交付表 |
| `reports/cleaning_stats.json` | B–C | 剖析 before/after |
| `reports/report.json` | C · Quality | C2-P1 §3.1 结构化品质报告 |
| `reports/report.md` | C | 人读摘要 |
| `delivery_signoff.md` | D · Delivery | 四签核点 #4 占位（P4 实作正文） |

可选（P4+）：`reports/delivery_manifest.md` · `notes.md`

---

## intake.json — 低风险单表 CSV 必要字段

结构版本：`gov-case-intake-v0.1`。本票**只落盘结构**，不做 eligibility 校验（P2）。

| 字段 | 用途 |
|------|------|
| `schema_version` | intake 契约版本 |
| `case_id` · `client_ref` | 案号与客户引用 |
| `product_sku` | 产品 SKU（如 `CLEAN-BASIC`） |
| `source.source_file` | 相对 case 根的 raw 路径 |
| `source.file_format` · `encoding` · `delimiter` | 解析参数 |
| `schema.id_column` · `required_columns` · `nullable_columns` | C2-P1 §2.1 主键与可缺失栏 |
| `schema.date_columns` · `percent_columns` | 格式规则 hint |
| `scale.expected_row_count` · `file_size_bytes` | Wave6 §3.1 规模 hint |
| `cleaning_goals` | 客户清洗目标（C2-P1 §2.1） |
| `provenance.source_type` · `data_owner` | Wave6 §3.2 来源 |
| `sensitivity.labels` · `contains_pii` | Wave6 §3.3 敏感度 |
| `structure.structure_type` | Wave6 §3.4（tabular MVP = `text_only`） |
| `eligibility_hint` | 人工预判 `accept` / `review` / `reject`（非自动判定） |

完整样例：`_TEMPLATE_case/intake.json` · `demo_phase/intake.json` · 索引 `index.json`。

---

## 与 demo / runner 的关系

- **清洗引擎**：仍用 `notebooks/csv_cleaning/clean_phase_demo.py`（P3 参数化 `--case-dir`）。
- **步骤清单**：`run_tabular_cleaning_plan.py --stage intake --case demo_phase`（P2+ 可输出 intake checklist）。
- **不建第二套引擎**；prod 链（W4-T1/T2）不在本 MVP 硬依赖内。

---

## 命名与工具

- `demo_phase` 等示例案可能采用手工案号或特别名称（遗留路径，合法但非 CLI 产物）。
- 正式 case 推荐使用 `scripts/new_cleaning_case.py` 生成标准路径 `cases/<client_ref>/<case_id>/`，其中 `case_id` 为 UTC 年 `YYYY-NNNN` 自增编号。
- gate 裁决由 `scripts/check_case_eligibility.py` 负责；建案 CLI 只创建目录与 `intake.json`，不做业务裁决。
- **自动化控制面**：`scripts/manage_tabular_automation_state.py`（start/pause/resume/stop/status）；state 落盘 `automation_state.json`。
- **运营查现况**：运营查询 Tabular 案件现况，请用 `scripts/tabular_ops_summary.py`（`--case-id` / `--client-ref` / `--all` · 表格或 `--format json`）。
- **历史案例索引**：`cases/index.json`（由 `scripts/build_cases_index.py` 刷新）；只读查询见下文「查历史案例（lookup）」。

---

## 查历史案例（lookup）

**接案默认动作**：新建 case 或跑 gate／清洗前，建议先查是否已有相似历史案与已知限制（如 Phase demo 的「每 Phase 一行」假设、sampleco 实验案的 gate／QA 备注）。lookup 是**只读历史案例索引**，不触发 gate、清洗或 bundle，也不做策略推荐。

```bash
# 刷新索引（登记 demo_phase + sampleco/2026-0001 等已配置案）
python scripts/build_cases_index.py

# 列出所有已登记 case
python scripts/lookup_case_history.py --list-all

# 按客户 slug 查找（大小写不敏感）
python scripts/lookup_case_history.py --client-ref SAMPLECO
```

可选过滤：`--product-sku CLEAN-BASIC`、`--schema-headers Phase,名稱`（表头子集匹配）。详见 `scripts/lookup_case_history.py --help`。

**stdout 形状**（单一 JSON，可供后续工具消费）：

| 键 | 说明 |
|----|------|
| `ok` | 查询是否成功 |
| `matches[]` | 命中 case 摘要（`case_dir`、`client_ref`、`gate_status`、`known_limits[]` 等） |
| `notes[]` | 索引覆盖范围、只读声明等非 case 级提示 |

交叉引用：`docs/MVP_CASE_E2E_DoD_v0.1.md` §2 · `docs/C2-P2_RUNBOOK.md` §7.1 · **`docs/case-history-lookup-spec-v0.1.md`**（W4-MEM-01 字段 SSOT）。

---

## 新建案件 Checklist

0. **推荐**：`python scripts/lookup_case_history.py --client-ref <ref>` 或 `--schema-headers <h1,h2,...>` 查历史；无匹配再建案
1. **推荐**：`python scripts/new_cleaning_case.py --client-ref <ref> --product-sku <sku> --source-file <path>`（可选 `--run-gate`）；或手动复制 `cases/_TEMPLATE_case/` → `cases/<client_ref>/<case_id>/`
2. 将原始 CSV 放入 `raw/`，更新 `intake.json` 中 `source` 与 `schema`
3. Stage A 签核后跑清洗（demo：`clean_phase_demo.py`，P3：`--case-dir`）
4. 确认 `reports/report.json` 与 C2-P1 §3.1 指标一致
5. P4 填写 `delivery_signoff.md` 并完成交付签核
