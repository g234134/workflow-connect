# MVP Case E2E DoD v0.1

> **适用范围**：低风险单表 CSV「单案」流程（Wave 2 P1–P4 · Wave 3 E2E 验收）。  
> **权威脚本**：`scripts/run_case_e2e_validation.py`  
> **代表案例**：`cases/demo_phase`

---

## 1. 适用范围

- 单个 `case_dir`，含 `intake.json`、`raw/`、`cleaned/`、`reports/`、`delivery_signoff.md`。
- 清洗 runner 为 `notebooks/csv_cleaning/clean_phase_demo.py`（Phase 表结构 demo）。
- 不包含：UI、邮件、dispatch 自动触发、prod pipeline。

---

## 2. 前置条件

| 项 | 要求 |
|----|------|
| case 目录结构 | 符合 `cases/_TEMPLATE_case/`（P1） |
| `intake.json` | 合法 JSON，含 `case_id`、`data_file`、`file_format` 等 P1 字段 |
| raw 数据文件 | `intake.json` 中 `data_file` 指向的文件存在 |
| P1–P4 脚本 | 当前 repo 版本中存在且可 import |
| Python | 3.10+；从 repo 根目录执行命令 |
| 工作目录 | **repo 根**（与 `scripts/`、`cases/` 同级） |
| 历史案例 lookup（推荐） | 处理新 case 前，建议先查 `cases/index.json` 是否已有相似案与 `known_limits`（如 `demo_phase` 仅适用于 Phase 每行一案、sampleco 为实验「勉强可用」样本）。示例：`python scripts/lookup_case_history.py --client-ref <ref>` 或 `--list-all`。只读索引，不替代 gate／清洗。详见 `cases/README.md` §查历史案例 |

---

## 3. 验收步骤

### 3.1 一键 E2E（推荐）

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
```

在 demo/internal 案例（例如 `cases/demo_phase`）下，E2E 驱动默认使用 `--force-review`：即便 gate 判定为 `review_needed`，仍会继续清洗与打包，用于内部验证。禁用该行为见 `--no-force-review`。

期望：stdout 打印 summary，`overall_ok: True`，进程 exit code `0`。

### 3.2 手动逐步（可复制）

```bash
# 1) 结构检查（人工目视或 ls）
#    cases/demo_phase/{intake.json, raw/, cleaned/, reports/, delivery_signoff.md}

# 2) Gate（P2）
python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json

# 3) Cleaning（P3）— gate 已单独跑过，用 --skip-eligibility
#    若 gate 为 review_needed，加 --force（见 §5 已知例外）
python notebooks/csv_cleaning/clean_phase_demo.py \
  --case-dir cases/demo_phase --skip-eligibility --force

# 4) Bundle（P4）
python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json
```

---

## 4. 验收项（全部为真则通过）

| # | 验收项 | 判定 |
|---|--------|------|
| 1 | Gate 脚本可运行并返回结构化 JSON | `ok: true`，`eligibility` 为 `accepted` / `review_needed` / `rejected` 之一；`review_needed` 时 gate 进程 exit code 为 `2`，仍计为 gate 步骤成功 |
| 1a | demo/internal 案例 E2E 整体通过（`demo_phase` 等） | 若 gate exit=`2`（`review_needed`）且 cleaning/bundle 均成功完成（含 cleaning `[forced]` 标记），整体 E2E 仍视为通过；**真实客户案例应优先要求 gate=`accepted` 后再执行清洗** |
| 2 | Cleaning 成功 | exit `0`，产出 `cleaned/*_cleaned.csv` |
| 3 | Cleaning 报告 | `reports/report.json`、`reports/report.md` 存在 |
| 4 | Bundle 成功 | `build_case_delivery_bundle` 返回 `ok: true` |
| 5 | 交付包齐全 | `reports/eligibility_result.json`、`delivery_signoff.md`、cleaned CSV 均存在 |
| 6 | 无 silent failure | 任一步失败时 CLI exit code 非 0，stderr/stdout 含可读错误 |

---

## 5. 已知例外

| 案例 | 例外 | 处理方式 |
|------|------|----------|
| `demo_phase` | 行数 < 100，gate 判 `review_needed`（`reason_code=rows<100`） | E2E 驱动默认 `--force-review`：cleaning 加 `--force` 继续；**生产流程须人工 review 后再清洗** |
| `demo_phase` | 文件 size < 1024 bytes | 同上，与 rows 一并触发 `review_needed` |

---

## 6. 相关票与脚本索引

| 阶段 | 票号 | 脚本 |
|------|------|------|
| P1 Case bootstrap | W-MVP-W2-P1 | `cases/_TEMPLATE_case/` |
| P2 Eligibility gate | W-MVP-W2-P2 | `scripts/check_case_eligibility.py` |
| P3 Cleaning runner | W-MVP-W2-P3 | `notebooks/csv_cleaning/clean_phase_demo.py` |
| P4 Delivery bundle | W-MVP-W2-P4 | `scripts/build_case_delivery_bundle.py` |
| E2E validation | W-MVP-W3-E2E-VALIDATION | `scripts/run_case_e2e_validation.py` |
| 历史案例 lookup | W-MVP-W4A-MEMO-LOOKUP | `scripts/lookup_case_history.py` · `scripts/build_cases_index.py` |

---

## 7. 未来扩展（本 DoD 不含）

- 多 case 批量 E2E（`cases/index.json` 遍历；lookup 已提供只读索引，批量 E2E 驱动仍属后续）
- CI workflow 集成（`.github/workflows/`）
- `accepted` 案例无需 `--force` 的 prod 路径文档化
- 异常分支：gate `rejected`、raw 缺失、intake 非法 JSON
