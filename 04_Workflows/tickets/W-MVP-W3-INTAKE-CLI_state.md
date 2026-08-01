# TICKET STATE · W-MVP-W3-INTAKE-CLI · 人工接案入口 CLI

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 · W-MVP — Intake CLI（**不做** UI、**不接** prod dispatch、**不触发**清洗/bundle）

---

## FRAME

- Goal: 为「人工接案」提供最薄 CLI，串联 case 创建 + intake 初稿 + 可选 P2 gate，供人类决策继续或拒绝。
- Scope:
  - `scripts/new_cleaning_case.py` CLI
  - 在 `cases/<client_ref>/<case_id>/` 落盘 `_TEMPLATE_case` 结构
  - 生成 `intake.json`（必要字段 + 可算 scale）
  - 可选 `--run-gate` 调用 `check_case_eligibility` 并打印 stdout
  - stdout 接案摘要（case_dir、gate_status 等）
  - 轻量 unittest
- NonScope:
  - 不移动用户原始文件（采用复制到 `raw/`）；不自动清洗、不 bundle
  - 不引入 UI；不接 W4 dispatch；不改清洗逻辑
  - 不强制写入 `reports/eligibility_result.json`（留给 P4）
- AllowedPaths:
  - `scripts/new_cleaning_case.py`
  - `tests/test_new_cleaning_case.py`
  - `04_Workflows/tickets/W-MVP-W3-INTAKE-CLI_state.md`
- BlockedPaths:
  - `core/*`、`dispatch_executor.py`、`scripts/run_dispatch_*`
  - `AGENTS.md`、`.cursor/rules/*`
  - 清洗引擎算法改动
- Dependencies:
  - P1 `W-MVP-W2-P1-CASE-BOOTSTRAP_state.md`（case 结构 + intake 模板）
  - P2 `scripts/check_case_eligibility.py` + `case_eligibility.py`
  - `cases/_TEMPLATE_case/*`
- AcceptanceCriteria:
  - 一条 CLI 可为给定 CSV 创建标准 case_dir + intake.json
  - `--run-gate` 可跑 gate 且结果在 stdout 可见
  - 结构与 P1 `cases/<client_ref>/<case_id>/` 约定兼容
  - B_REPORT 记录命名规则、字段、gate 行为

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 对照 AC 验收 CLI 与 gate 输出；Orchestrator 决定是否合并 gate 写盘到 P4
- last_updated: 2026-06-08 · implementer
- status_by_role:
  - orchestrator: pending
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

### changed_files

- `scripts/new_cleaning_case.py`（新建 · intake CLI）
- `tests/test_new_cleaning_case.py`（新建 · 创建 + CLI gate 轻测）
- `04_Workflows/tickets/W-MVP-W3-INTAKE-CLI_state.md`（本档）

### CLI 用法示例

```bash
# 仅建 case + intake
python scripts/new_cleaning_case.py \
  --client-ref ACME \
  --product-sku CLEAN-BASIC \
  --source-file cases/demo_phase/raw/Phase.csv

# 建 case 后立即跑 P2 gate（结果打印到 stdout，不写 eligibility_result.json）
python scripts/new_cleaning_case.py \
  --client-ref ACME \
  --product-sku CLEAN-BASIC \
  --source-file cases/demo_phase/raw/Phase.csv \
  --encoding utf-8-sig \
  --delimiter , \
  --file-format csv \
  --run-gate
```

stdout 末尾固定打印接案摘要块：

```
--- intake summary ---
case_dir: cases/acme/2026-0001
client_ref: acme
case_id: 2026-0001
product_sku: CLEAN-BASIC
source_file: raw/Phase.csv
gate_status: not_run | accepted | rejected | review_needed
----------------------
```

### case_dir 命名规则

| 段 | 规则 | 示例 |
|----|------|------|
| `client_ref` | 入参规范化：小写 `[a-z0-9-]`（非法字元 → `-`） | `ACME` → `acme` |
| `case_id` | UTC 当年 `YYYY-NNNN`，按 `cases/<client_ref>/` 下同年序号自增 | `2026-0001` |
| 完整路径 | `cases/<client_ref>/<case_id>/` | `cases/acme/2026-0001/` |

子结构对齐 `_TEMPLATE_case`：`intake.json`、`delivery_signoff.md`、`raw/`、`cleaned/`、`reports/`。

本 CLI 仅负责生成形如 `YYYY-NNNN` 的 `case_id`；例如 `demo_phase` 这类历史/示例 case 仍可使用手工指定的案号，只是不会由 CLI 自动创建。

### intake 初始字段（创建时填写）

**必填 / 自动填入：**

| 字段 | 来源 |
|------|------|
| `case_id` | 自增 `YYYY-NNNN` |
| `client_ref` | `--client-ref`（规范化） |
| `product_sku` | `--product-sku` |
| `data_file` | `raw/<源文件名>`（复制后相对路径） |
| `file_format` | `--file-format` 或源文件扩展名 |
| `encoding` | `--encoding`（默认 `utf-8`） |
| `delimiter` | `--delimiter`（默认 `,`） |
| `scale.row_count` | CSV 行数统计（含表头则减 1） |
| `scale.file_size_bytes` | 复制后 raw 文件大小 |

**默认值（可后续人工补全）：**

| 字段 | 默认 |
|------|------|
| `schema.field_count` / `primary_key` / `pii_fields` | `null` / `null` / `[]` |
| `provenance.source_type` / `data_owner` | `owned` / `<client_ref>` |
| `sensitivity` | `internal` |
| `structure` | `text_only` |
| `security_compliance` | `contains_pii: false`, `user_acknowledged_limitations: true` |
| `cleaning_goals` | `""` |

**留空 / 本票不填：** `eligibility_hint`、`schema` 列规则细节、`source.*` 嵌套形态（P1 README 形态；本票用 flat `data_file` 与 `demo_phase` / P2 解析器对齐）。

### 源文件策略（trade-off）

**选择：复制到 `raw/`**（`shutil.copy2`），不在 intake 记录外部绝对路径。

| 方案 | 优点 | 缺点 |
|------|------|------|
| **复制到 raw/**（采用） | case 自包含；P2/P3 无需外部路径；可移植、可归档 | 大文件占 repo 空间；需人工同步外部变更 |
| 仅记录 `external_source_path` | 不占 repo 空间 | gate/runner 依赖本机路径；不可移植；违反 P1「原始档入 raw」惯例 |

### gate 行为说明

| 场景 | 行为 |
|------|------|
| 默认（无 flag） | 仅创建 case_dir + intake；`gate_status: not_run` |
| `--run-gate` | 调用 `case_eligibility.check_case_eligibility(case_dir)`；打印一行 summary + 完整 JSON；**不写** `reports/eligibility_result.json` |
| gate 输入需求 | `intake.json` + 可解析 `data_file`；`file_format` / `encoding`；scale 可自文件补全；`provenance` / `sensitivity` / `structure` 有默认即可 |

本命令的进程 exit code 仅表示建案流程本身是否成功（成功恒为 `0`）；gate 裁决结果需通过 stdout 或 `--run-gate` 的 JSON 输出查看，请勿以 `$?` 作为业务判定依据。

**建议（deferred）：** 未来可在 P4 bundle 或本 CLI 增加 `--write-eligibility` 与 `build_case_delivery_bundle` 对齐。

### verification

- 命令：`python -m unittest tests.test_new_cleaning_case -v`
- 命令：`python scripts/new_cleaning_case.py --client-ref acme --product-sku CLEAN-BASIC --source-file cases/demo_phase/raw/Phase.csv --encoding utf-8-sig --run-gate`
- 预期：新目录 `cases/acme/<YYYY-NNNN>/` 含 template 结构；stdout 含 `eligibility=review_needed`（demo 行数 &lt; 100）与 `gate_status: review_needed`

### behavior_notes

- `client_ref` 入参大小写不敏感，落盘一律小写 slug。
- `case_id` 按客户分桶自增，不同 `client_ref` 同年可同为 `2026-0001`。
- CLI exit code：创建失败 → `1`；创建成功 → `0`（gate 结果不影响 exit code，仅打印）。

### deferred_items

- 更新 `cases/index.json` registry（可选 Scribe）
- `--write-eligibility` 写 `reports/eligibility_result.json`
- 从 intake 嵌套 `source.*` 形态与 P1 README 完全对齐（当前 flat 字段与 P2/P3 已兼容）

---

## C_REPORT

**Reviewer:** W-MVP-W3-INTAKE-CLI · 2026-06-08  
**P0 已读:** `engineering-contract.mdc` · 本票 FRAME/B_REPORT · P1 `W-MVP-W2-P1-CASE-BOOTSTRAP_state.md` · `scripts/new_cleaning_case.py` · `tests/test_new_cleaning_case.py` · `cases/_TEMPLATE_case/*` · `notebooks/csv_cleaning/case_eligibility.py`

### verdict

`accept_with_minor_edits`

实现与 AC 一致，可作为 v1 人工接案入口；建议仅补充说明层小修（B_REPORT / CLI help / Scribe 交叉引用），**不要求本票改脚本逻辑**。

### strengths

1. **命名与结构对齐 P1**：`client_ref` 小写 slug 规范化、`case_id` 按客户分桶 `YYYY-NNNN` 自增、落盘 `cases/<client_ref>/<case_id>/` 子结构与 `_TEMPLATE_case` 一致（`intake.json` · `delivery_signoff.md` · `raw/` · `cleaned/` · `reports/`）；`shutil.copy2` 复制源文件到 `raw/` 的理由在 B_REPORT「源文件策略」表已写清。
2. **intake 字段满足 P2 gate 最低需求**：创建时填入 `data_file` / `file_format` / `encoding` / `delimiter` / `scale` 及 `provenance` / `sensitivity` / `structure` 默认值；P2 `_resolve_*` 可消费 flat 形态（与 `demo_phase` / `acme/2026-0001` 一致）。
3. **Wave 6 默认调性合理**：`owned` / `internal` / `text_only` 落在 ACCEPT 区间，避免 `unknown` 触发 provenance `review_needed`；`security_compliance.contains_pii: false` 与空 `pii_fields` 为乐观默认，但 gate 仍会对列名启发式补 `possible_pii_columns`。
4. **Gate 行为可预期**：默认不跑 gate → 摘要 `gate_status: not_run`；`--run-gate` 调用 `check_case_eligibility` 并打印一行 summary + 完整 JSON；**未**写入 `reports/eligibility_result.json`（代码与 B_REPORT 一致）。
5. **人类安全细节**：创建失败 exit `1`；创建成功 exit `0`（gate 裁决不影响 CLI exit code）；stdout 固定 `--- intake summary ---` 块便于肉眼核对。
6. **验证证据**：`python -m unittest tests.test_new_cleaning_case -v` → 2 tests OK（Reviewer 复跑 2026-06-08）。

### gaps_or_ambiguities

1. **`cases/README.md` 与 CLI 案号规则未交叉引用**：README 仍写手动复制模板、`case_id` 示例为 `demo_phase` / `2026-q2-orders`；CLI 实际强制 UTC 年 `YYYY-NNNN` 自增。B_REPORT 已说明 CLI 规则，但新操作者若只读 README 可能混淆。**建议文案（可追加 B_REPORT「case_dir 命名规则」段末）：**  
   > 「本 CLI 的 `case_id` 仅采用 `YYYY-NNNN` 自动编号；`cases/README.md` 中 `demo_phase` 等遗留/手填案号仍合法，但不由本 CLI 生成。」

2. **P1 嵌套 `source.*` vs 本票 flat 字段**：B_REPORT 已标注 deferred；建议在 CLI `argparse` description 或模块 docstring 加一句「intake 采用 flat `data_file`（与 P2/P3 解析器兼容，非 P1 README 嵌套 `source.source_file` 形态）」——仅文档，不改 JSON 形状。

3. **Gate exit code 与 CLI exit code 分离未在 help 中强调**：`eligibility` 结果 JSON 含 `exit_code`（0/1/2），但 CLI 创建成功后恒返回 `0`。建议在 B_REPORT「gate 行为说明」或 `--run-gate` help 补一句：**「gate 裁决不改变本 CLI 进程 exit code；人工决策请读 stdout 摘要与 JSON，勿依赖 shell `$?` 判断 accept/reject。」**

### required_edits

| 目标 | 类型 | 内容 |
|------|------|------|
| B_REPORT | 追加 1 句 | 见 gaps #1 案号规则与 README 关系说明 |
| B_REPORT 或 CLI help | 追加 1 句 | 见 gaps #3 gate exit code 与 CLI exit code 分离 |
| `scripts/new_cleaning_case.py` docstring / `--help` | 可选文案 | 见 gaps #2 flat intake 说明；**不改参数、不改行为** |
| `cases/README.md` | Scribe 后续 | 「新建案件 Checklist」增加 `new_cleaning_case.py` 为推荐路径（本票 Reviewer 不改 README） |

**不要求：** 增加 `--write-eligibility`、对齐 P1 `schema_version` / 嵌套 `source.*`、修改 gate 或清洗逻辑。

### intake_cli_confidence

这版 CLI 足以作为 **MVP v1 人工接案入口**：一条命令可落标准 case 目录、填齐 gate 所需 intake 初稿，并可选用 `--run-gate` 即时获得 stdout 裁决摘要；结构与 P1 template 及现有 `acme/2026-0001` 样例一致。

### verification（Reviewer）

| 命令 | 结果 |
|------|------|
| `python -m unittest tests.test_new_cleaning_case -v` | 2 passed |
| 静态对照 `create_cleaning_case` / `main` / `case_eligibility.check_case_eligibility` | 与 B_REPORT gate 表一致 |
| `grep eligibility_result new_cleaning_case.py` | 无写盘逻辑 |

### next_steps（Orchestrator / Scribe）

| 角色 | 建议 |
|------|------|
| **Orchestrator** | `overall_status`: `in_progress` → `in_review` → **`done`**（采纳上述 minor edits 后关票）；`status_by_role.reviewer`: `done` |
| **Implementer** | 可选：按 `required_edits` 补 B_REPORT 两句 + CLI help 一句（仍属说明层，非逻辑变更） |
| **Scribe** | 更新 `cases/index.json` 登记 `acme/2026-0001` 或测试案为示例；`cases/README.md` Checklist 引用 `new_cleaning_case.py` |
| **P4 后续票** | `--write-eligibility` → `reports/eligibility_result.json`；与 bundle 对齐 |

**Scribe note（2026-06-08）：** 已按本 C_REPORT 的 `required_edits` 更新 B_REPORT 案号规则与 gate/CLI exit code 说明，并补充 `cases/README.md`「命名与工具」小节；未对任何脚本逻辑做改动，等待 Orchestrator 更新 STATE。

---

## D_REPORT

<!-- Scribe 填 -->
