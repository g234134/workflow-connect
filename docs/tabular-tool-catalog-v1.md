# Tabular Tool Catalog v1

> **Upstream contract（跨轨 SSOT）**：`docs/tool-catalog-and-selector-contract-v1.md` — 四轨分轨、`governed_by`、命名空间与 selector 形状以 contract 为准；本档为 **Tabular 实现附录**。  
> **Ticket**: W3-TL-T1 · Tabular Tool Catalog  
> **Machine SSOT**: `tools/tabular_tool_catalog_v1.json`  
> **Schema**: `tabular_tool_catalog_v1` · revision `2026-06-10`  
> **Trace authority**: `docs/mvp-standard-trace-path.md` §2.3  
> **Regression**: `docs/mvp-mainline-regression.md`

---

## 1. 目的与范围

本 Catalog 为 **Tabular MVP 工具层** 的单一权威（人读 spec + 机器 JSON 双轨），覆盖 MVP 主链：

```text
intake → gate (P2) → cleaning (P3) → bundle (P4) → E2E orchestration
```

以及只读索引、lookup、runbook planner、local UI 等辅助工具。

**In scope**

- `scripts/` 与 `notebooks/csv_cleaning/` 下 Tabular case 清洗相关 CLI / 库模块
- `app/local_ui.py`（本地 MVP UI 包装层）
- 主链回归包装 `scripts/run_mvp_mainline_regression.py`

**Out of scope（本 JSON 不包含；仅 §2 对照表引用）**

- Gov Tool Registry（`obs.*` / `kb.*`）→ 见 `docs/SKILL_CATALOG_OVERVIEW.md`
- Phase 8.8 编排 Tool Layer（`llm.*`、outbox replay 等）→ 见 `04_Workflows/tickets/W3-T1_state.md`–`W3-T4_state.md`
- Wave8 产品 SKU 卡（`skill-clean-*`）→ 见 `skills/cards/`

**工作目录**：repo 根（与 `scripts/`、`cases/` 同级）· **Python**：3.10+

---

## 2. 与其他 Catalog 的关系

| tool_family | SSOT 文档 / 位置 | ID 格式 | 与本 Catalog 关系 |
|-------------|------------------|---------|-------------------|
| **Tabular MVP** | 本档 + `tools/tabular_tool_catalog_v1.json` | `<action>.<target>` 或 `intake.*` / `validate.*` / `orchestrate.*` | **本票权威**；W3-TL-T2 Selector 消费 `tool_id` + `applicable_conditions` |
| **Gov Registry** | `docs/SKILL_CATALOG_OVERVIEW.md` · `skills/gov_cards/*.json` | `obs.*` / `kb.*` | **分轨**；`governed_by: gov_registry`；不入 tabular JSON |
| **Phase 8.8 编排** | `04_Workflows/SPEC_tool_catalog_and_selector_v1.md`（draft）· `W3-T1`–`T4` state | `llm.*` 等 | **分轨**；`governed_by: phase_8.8_spec`；暗部 orchestration，与本票 rename/合并禁止 |
| **Product skill cards** | `skills/cards/skill-clean-*.json` | `skill-clean-*` | **分轨**；对外产品 SKU；禁止与本 Catalog schema 混用 |

三套（及以上）Catalog **禁止**合并 JSON 或共用 `tool_id` 命名空间。

---

## 3. Tabular 工具清单（总览）

| tool_id | 类型 | module_path | 一句话说明 | 收录 JSON | 风险关键字 |
|---------|------|-------------|------------|-----------|------------|
| `intake.new_case` | intake | `scripts/new_cleaning_case.py` | 手工建案：`case_dir` + `intake.json` + 复制 raw | ✓ | `manual_intake`, `not_prod_dispatch` |
| `validate.eligibility` | validation | `scripts/check_case_eligibility.py` | P2 gate：eligibility 判定（exit 0/1/2） | ✓ | `review_needed`, `manual_mvp_gate` |
| `clean.phase_demo` | cleaning | `notebooks/csv_cleaning/clean_phase_demo.py` | Phase 表专用 demo 清洗（P3） | ✓ | `phase_like_only`, `demo_non_prod` |
| `export.delivery_bundle` | export | `scripts/build_case_delivery_bundle.py` | P4 交付包 + signoff + guard 侧车 | ✓ | `mvp_v0.1` |
| `validate.output_guard` | validation | `notebooks/csv_cleaning/output_guard.py` | 清洗输出行比例 guard（库模块） | ✓ | `sidecar_only`, `no_exit_block` |
| `orchestrate.e2e` | orchestration | `scripts/run_case_e2e_validation.py` | 一键 gate → clean → bundle | ✓ | `non_single_step`, `force_review` |
| `index.cases` | helper | `scripts/build_cases_index.py` | 刷新 `cases/index.json` | ✓ | `read_only_scan` |
| `lookup.history` | helper | `scripts/lookup_case_history.py` | 只读 case 历史查询 | ✓ | `needs_index` |
| `plan.cleaning_stages` | helper | `notebooks/csv_cleaning/run_tabular_cleaning_plan.py` | Runbook 阶段清单（不执行清洗） | ✓ | `not_prod_pipeline`, `planner_only` |
| `ui.local` | helper | `app/local_ui.py` | localhost Web UI 包装上述 CLI | ✓ | `NOT_PROD`, `localhost_only` |
| `orchestrate.mainline_regression` | orchestration | `scripts/run_mvp_mainline_regression.py` | demo_phase + sampleco 回归包装 | ✓ | `regression`, `non_single_step` |
| `case_eligibility`（库） | validation | `notebooks/csv_cleaning/case_eligibility.py` | gate 核心逻辑；由 `validate.eligibility` 调用 | ✗ | 见 §4.1；**不入 JSON**（无独立 CLI） |
| `case_delivery_bundle`（库） | export | `notebooks/csv_cleaning/case_delivery_bundle.py` | bundle 核心逻辑；由 `export.delivery_bundle` 调用 | ✗ | 见 §4.4 |
| `case_intake_loader`（库） | helper | `notebooks/csv_cleaning/case_intake_loader.py` | intake 加载；由 `clean.phase_demo` 调用 | ✗ | 内部库，Selector 应指向 CLI 层 |
| Gov `obs.*` / `kb.*` | — | `skills/gov_cards/` | Wave B 可观测 / KB CLI | ✗ | `governed_by: gov_registry` |
| Phase 8.8 `llm.*` | — | 暗部 draft | ask / 编排 Tool Layer | ✗ | `governed_by: phase_8.8_spec` |
| Wave8 `skill-clean-*` | — | `skills/cards/` | 产品 CLEAN SKU | ✗ | 禁止 ID 混用 |

---

## 4. 工具详述（核心步骤）

行为信号以 `docs/mvp-standard-trace-path.md` §5 L1 表为准。

### 4.1 `validate.eligibility`（P2 Gate）

**前置条件**

- `--case-dir` 存在且含 `intake.json`
- `intake.json` 中 `data_file` 指向 `raw/` 下可读 CSV/TSV

**主要 CLI**

```bash
python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json
```

**典型行为**

- `demo_phase` → `eligibility=review_needed`，exit `2`，`reason_code=rows<100`
- `sampleco/2026-0001` → `eligibility=accepted`，exit `0`
- stdout JSON 含 `dimensions.schema.notes`（如 `phase_like`, `multi_row_export`）

**库模块**：`notebooks/csv_cleaning/case_eligibility.py`（`check_case_eligibility`）— 无独立 CLI，故不入 JSON。

### 4.2 `clean.phase_demo`（P3 Cleaning）

**前置条件**

- 同上；gate `accepted` 或人工确认后对 `review_needed` 使用 `--force`

**主要 CLI**

```bash
python notebooks/csv_cleaning/clean_phase_demo.py \
  --case-dir cases/demo_phase --skip-eligibility --force
```

**典型行为**

- 写入 `cleaned/*_cleaned.csv`、`reports/report.json`、`reports/cleaning_stats.json`
- **仅**支持 Phase 四列 schema；非通用清洗管线
- `demo_phase`：7 → 5 行；`sampleco`：115 → 8 行（无 `--force`）

### 4.3 `validate.output_guard`

**前置条件**

- 由 `export.delivery_bundle` 在 bundle 阶段调用
- 需要 `reports/report.json` 行数与可选 `eligibility_result.json`

**行为**

- 计算 `output_guard.status`：`ok` / `warning` / `unknown`
- **不**改变 cleaning / bundle / E2E 进程 exit code
- `sampleco` 预期 `warning`（115 → 8 行比例）

### 4.4 `export.delivery_bundle`（P4 Bundle）

**前置条件**

- `case_dir` 含 intake；建议已有 cleaning 产物（`reports/report.json`、`cleaned/`）

**主要 CLI**

```bash
python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json
```

**典型行为**

- 刷新或沿用 `reports/eligibility_result.json`
- 写入 / 更新 `delivery_signoff.md`
- 嵌入 `output_guard` 侧车摘要

**库模块**：`notebooks/csv_cleaning/case_delivery_bundle.py` — 由 CLI 包装，不入 JSON。

### 4.5 `orchestrate.e2e`

**前置条件**

- 完整 case 目录（`intake.json` + `raw/`）

**主要 CLI**

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
```

**典型行为**

- 顺序调用 gate → clean → bundle
- 默认 `--force-review`：`review_needed` 时仍可达 `delivered`（仅 demo/internal）
- **标注**：`non_single_step` 编排工具，非单步 Selector 目标

---

## 5. 注意事项与未来工作

1. **JSON 仅覆盖 Tabular MVP**；接入 Gov Registry、Phase 8.8 或产品 SKU 须另开票，禁止扩 scope 塞入本 JSON。
2. **主链守护**：合并本票前 Reviewer 须跑 `python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK（本票不改主链行为）。
3. **下游接口**：
   - **W3-TL-T2 Selector**：读取 `tool_id`、`type`、`applicable_conditions`、`enabled`
   - **W3-TL-T3 Executor**：读取 `module_path`、`entry_kind`、`cli_invocation`
4. **Loader（可选）**：`tools/tabular_tool_catalog_loader.py` 未在本票交付；T2/T3 可直接 `json.load` 本文件。
5. **[待确认]**：是否将 `case_eligibility` / `case_delivery_bundle` 以 `python_module` 条目纳入 JSON 供 Selector 细粒度路由——当前裁定为 CLI 层为准，库模块仅在本文档说明。

---

## 6. 验证命令

```bash
# Catalog 结构（本票交付）
python -m unittest tests.test_tabular_tool_catalog -v

# 主链回归（合并前 Reviewer；本票不执行即不宣称为本票 AC）
python scripts/run_mvp_mainline_regression.py -v
```

---

## 7. 相关文档

| 文档 | 用途 |
|------|------|
| `docs/mvp-standard-trace-path.md` | MVP 主链 entrypoints 与 L1 trace |
| `docs/mvp-mainline-regression.md` | 回归 runner 说明 |
| `docs/SKILL_CATALOG_OVERVIEW.md` | Gov Registry 对照 |
| `04_Workflows/tickets/W3-TL-T1-tabular-tool-catalog_state.md` | 本票 FRAME / AC |
| `04_Workflows/tickets/W3-TL-T2*` / `W3-TL-T3*` | Selector / Executor 下游 |
